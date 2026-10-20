from nbe_blackstar import bridge as nbe


class SlowProxy:
    def __init__(self, *a, **k):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, path):
        self.calls.append(path)
        return ["%s=46541.4" % path]


def test_slow_query_reads_counter(monkeypatch):
    monkeypatch.setattr(nbe, "Proxy", SlowProxy)
    monkeypatch.setitem(nbe.settings.config if hasattr(nbe.settings, "config") else {}, "debug", False)
    monkeypatch.setattr(nbe.settings, "config", {"debug": False, "nbe_pass": "x", "nbe_port": 8483, "nbe_ip": "192.0.2.10", "nbe_serial": "123456"}, raising=False)
    monkeypatch.setattr(nbe, "_reader", None)
    assert nbe.nbe_query()["consumption_data/counter"] == "46541.4"


def test_schema_declares_counter_as_total_increasing():
    rows = [line for line in open(nbe.os.path.join(nbe.os.path.dirname(nbe.__file__), "nbe_schema")) if line.startswith("consumption_data/counter")]
    assert len(rows) == 1
    assert ",total_increasing," in rows[0]
