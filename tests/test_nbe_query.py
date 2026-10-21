from nbe_blackstar import bridge as nbe


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


def _configure(monkeypatch):
    monkeypatch.setattr(nbe, "_reader", None)
    monkeypatch.setattr(nbe.time, "sleep", lambda s: None)
    nbe.settings.config = {
        "debug": False, "nbe_pass": "x", "nbe_port": 8483,
        "nbe_ip": "192.0.2.10", "nbe_serial": "123456",
    }


def test_query_collects_items(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(nbe, "Proxy", FakeProxy)
    items = nbe.nbe_query()
    assert items["operating_data"] == "1"


def test_failed_query_returns_empty(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(nbe, "Proxy", BrokenProxy)
    assert nbe.nbe_query() == {}


def test_refresh_publishes_offline_when_query_keeps_failing(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(nbe, "_failed_cycles", 0, raising=False)
    monkeypatch.setattr(nbe, "Proxy", BrokenProxy)
    client = FakeClient()
    for _ in range(nbe.OFFLINE_AFTER_FAILED_CYCLES):
        nbe.refresh_statuses(client)
    assert (nbe.device.getUid() + "/bridge/state", "offline") in client.published


def test_refresh_publishes_online_when_query_ok(monkeypatch, tmp_path):
    _configure(monkeypatch)
    monkeypatch.setattr(nbe, "HEARTBEAT_FILE", str(tmp_path / "alive"))
    monkeypatch.setattr(nbe, "Proxy", FakeProxy)
    client = FakeClient()
    nbe.refresh_statuses(client)
    assert (nbe.device.getUid() + "/bridge/state", "online") in client.published


class FlakyProxy(FakeProxy):
    attempts = 0

    def get(self, path):
        FlakyProxy.attempts += 1
        if FlakyProxy.attempts == 1:
            raise IOError()
        return ["%s=1" % path]


def test_query_retries_once_after_transient_failure(monkeypatch):
    _configure(monkeypatch)
    FlakyProxy.attempts = 0
    monkeypatch.setattr(nbe, "Proxy", FlakyProxy)
    monkeypatch.setattr(nbe.time, "sleep", lambda s: None)
    assert nbe.nbe_query()["operating_data"] == "1"


def test_query_error_message_names_the_exception(monkeypatch, caplog):
    _configure(monkeypatch)
    monkeypatch.setattr(nbe, "Proxy", BrokenProxy)
    monkeypatch.setattr(nbe.time, "sleep", lambda s: None)
    nbe.nbe_query()
    assert "OSError" in caplog.text
