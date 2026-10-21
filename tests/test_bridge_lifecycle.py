import json
import signal

from nbe_blackstar import bridge as nbe
from nbe_blackstar.energy import EnergyMeter


class FakeClient:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload))


class FakeProxy:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, path):
        return ["%s=1" % path]


class BrokenProxy(FakeProxy):
    def get(self, path):
        raise OSError("controller silent")


def _configure(monkeypatch, tmp_path):
    monkeypatch.setattr(nbe, "_reader", None)
    monkeypatch.setattr(nbe, "_failed_cycles", 0, raising=False)
    monkeypatch.setattr(nbe, "HEARTBEAT_FILE", str(tmp_path / "alive"))
    monkeypatch.setattr(nbe.time, "sleep", lambda s: None)
    nbe.settings.config = {
        "debug": False, "nbe_pass": "x", "nbe_port": 8483,
        "nbe_ip": "192.0.2.10", "nbe_serial": "123456",
    }


def _state_messages(client):
    return [p for t, p in client.published if t == nbe.device.getUid() + "/bridge/state"]


def test_single_failed_cycle_does_not_publish_offline(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setattr(nbe, "Proxy", BrokenProxy)
    client = FakeClient()
    nbe.refresh_statuses(client)
    nbe.refresh_statuses(client)
    assert "offline" not in _state_messages(client)
    nbe.refresh_statuses(client)
    assert _state_messages(client) == ["offline"]


def test_successful_cycle_resets_failure_count(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    client = FakeClient()
    monkeypatch.setattr(nbe, "Proxy", BrokenProxy)
    nbe.refresh_statuses(client)
    nbe.refresh_statuses(client)
    monkeypatch.setattr(nbe, "_reader", None)
    monkeypatch.setattr(nbe, "Proxy", FakeProxy)
    nbe.refresh_statuses(client)
    monkeypatch.setattr(nbe, "_reader", None)
    monkeypatch.setattr(nbe, "Proxy", BrokenProxy)
    nbe.refresh_statuses(client)
    nbe.refresh_statuses(client)
    assert "offline" not in _state_messages(client)


def test_firmware_retried_after_failed_first_read(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setattr(nbe, "device", nbe.make_device({"device_id": "nbe_test", "device_name": "NBE"}))
    monkeypatch.setattr(nbe, "Proxy", FakeProxy)
    answers = iter([None, "7.0680", "9.9999"])
    calls = []
    monkeypatch.setattr(nbe, "fetch_sw_version", lambda: calls.append(1) or next(answers))
    republished = []
    monkeypatch.setattr(nbe, "populate_resources", lambda c: republished.append(1))
    client = FakeClient()
    nbe.refresh_statuses(client)
    assert nbe.device.sw_version == "unknown"
    assert republished == []
    nbe.refresh_statuses(client)
    assert nbe.device.sw_version == "7.0680"
    nbe.refresh_statuses(client)
    assert len(calls) == 2
    assert len(republished) == 1


def test_sigterm_runs_shutdown_and_flushes_energy_total(tmp_path, monkeypatch):
    path = str(tmp_path / "energy.json")
    meter = EnergyMeter(path)
    meter.update(6.0, 0)
    meter.update(6.0, 600)
    reader = nbe.NbeReader("192.0.2.10", "123456", "123456", 8483)
    reader.meter = meter
    monkeypatch.setattr(nbe, "_reader", reader)
    monkeypatch.setattr(nbe, "device", type("D", (), {"getUid": lambda self: "uid"})(), raising=False)
    client = type("C", (), {"published": [], "loop_stop": lambda self: None, "disconnect": lambda self: None})()
    client.publish = lambda *a: client.published.append(a)
    previous = signal.getsignal(signal.SIGTERM)
    try:
        restore = nbe.install_sigterm_handler()
        handler = signal.getsignal(signal.SIGTERM)
        assert handler is not previous
        try:
            handler(signal.SIGTERM, None)
        except KeyboardInterrupt:
            assert nbe.shutdown(client) == 0
        else:
            raise AssertionError("SIGTERM handler must raise KeyboardInterrupt")
        restore()
        assert signal.getsignal(signal.SIGTERM) is previous
    finally:
        signal.signal(signal.SIGTERM, previous)
    assert json.load(open(path))["kwh"] == 1.0
    assert client.published == [("uid/bridge/state", "offline", 0, True)]
