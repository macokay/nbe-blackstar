import csv
import os

from nbe_blackstar import bridge as nbe


def test_999_9_is_hidden_but_large_counter_is_kept():
    assert nbe.clean_value("999.9") == ""
    assert nbe.clean_value("1348.1") == "1348.1"
    assert nbe.clean_value("46541.4") == "46541.4"


def test_not_connected_publishes_empty_not_text(monkeypatch):
    monkeypatch.setattr(nbe.settings, "config", {"debug": False}, raising=False)
    client = type("C", (), {"published": [], "publish": lambda self, t, p, q=0, r=False: self.published.append((t, p))})()
    monkeypatch.setattr(nbe, "nbe_query", lambda: {"operating_data/dhw_temp": "999.9"})
    monkeypatch.setattr(nbe, "HEARTBEAT_FILE", os.devnull)
    monkeypatch.setattr(nbe, "DataEntries", [r for r in nbe.DataEntries if r.type != "sensor"] + [])
    entry = nbe.ha_classes.Resource(nbe.ha_classes.Sensor("none", "temperature", "°C", "measurement", "Varmtvand", nbe.device, "varmtvand"), "sensor", "operating_data/dhw_temp")
    monkeypatch.setattr(nbe, "DataEntries", [entry])
    nbe.refresh_statuses(client)
    values = [p for t, p in client.published if t.endswith("/state")]
    assert "unknown" not in values
    assert "" in values


def test_photo_level_has_no_invalid_illuminance_unit():
    rows = [line for line in open(os.path.join(os.path.dirname(nbe.__file__), "nbe_schema")) if line.startswith("operating_data/photo_level")]
    row = next(csv.reader(rows))
    device_class, unit = row[6], row[7]
    assert not (device_class == "illuminance" and unit == "lm")


def test_will_is_set_offline_retained():
    class FakeClient:
        def __init__(self):
            self.will = None

        def will_set(self, topic, payload, qos=0, retain=False):
            self.will = (topic, payload, retain)

    client = FakeClient()
    nbe.configure_will(client)
    assert client.will == (nbe.device.getUid() + "/bridge/state", "offline", True)


def test_one_controller_session_is_reused_across_queries(monkeypatch):
    created = []

    class CountingProxy:
        def __init__(self, *a, **k):
            created.append(1)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, path):
            return ["%s=1" % path]

    monkeypatch.setattr(nbe, "Proxy", CountingProxy)
    monkeypatch.setattr(nbe, "_reader", None)
    monkeypatch.setattr(nbe.settings, "config", {"debug": False, "nbe_pass": "x", "nbe_port": 8483, "nbe_ip": "192.0.2.10", "nbe_serial": "123456"}, raising=False)
    nbe.nbe_query()
    nbe.nbe_query()
    assert len(created) == 1


def test_silent_controller_raises_timeout_not_none(monkeypatch):
    from nbe_blackstar import protocol

    class SilentSocket:
        def sendto(self, *a):
            return 0

        def settimeout(self, t):
            pass

    proxy = protocol.Proxy.__new__(protocol.Proxy)
    proxy.s = SilentSocket()
    proxy.addr = ("192.0.2.10", 8483)
    proxy.password = "x"
    proxy.request = type("R", (), {"sequencenumber": 1, "encode": lambda self: b""})()
    monkeypatch.setattr(protocol.select, "select", lambda r, w, x, t: ([], [], []))
    import pytest
    with pytest.raises(TimeoutError):
        proxy.make_request(4, "*")
