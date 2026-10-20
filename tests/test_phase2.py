import json

from nbe_blackstar import bridge as nbe
from nbe_blackstar import ha_classes


class FirmwareProxy:
    def __init__(self, *a, **k):
        pass

    def get(self, path):
        assert path == "sw_versions"
        return ["210504,7.0680,3", "210101,7.0674,3"]


class BrokenFirmwareProxy(FirmwareProxy):
    def get(self, path):
        raise OSError("silent")


def test_firmware_version_is_newest_entry(monkeypatch):
    monkeypatch.setattr(nbe, "_proxy", None)
    monkeypatch.setattr(nbe, "Proxy", FirmwareProxy)
    assert nbe.fetch_sw_version() == "7.0680"


def test_firmware_version_none_when_controller_silent(monkeypatch):
    monkeypatch.setattr(nbe, "_proxy", None)
    monkeypatch.setattr(nbe, "Proxy", BrokenFirmwareProxy)
    assert nbe.fetch_sw_version() is None


def test_discovery_has_origin_block_and_device_topics(monkeypatch):
    monkeypatch.setattr(nbe, "DataEntries", [])
    monkeypatch.setattr(nbe.settings, "config", {"ha_prefix": "homeassistant", "debug": False, "lang": "da"}, raising=False)
    published = []

    class C:
        def publish(self, topic, payload, qos=0, retain=False):
            published.append((topic, payload))

    nbe.populate_resources(C())
    topic, payload = next((t, p) for t, p in published if t.endswith("/kedeltemperatur/config"))
    data = json.loads(payload)
    assert data["origin"]["name"] == "nbe-blackstar"
    assert data["origin"]["sw_version"] == ha_classes.ORIGIN["sw_version"]
    assert topic.startswith("homeassistant/sensor/" + nbe.device.getId() + "/")


def test_device_id_drives_topics_and_identifiers():
    device = ha_classes.Device("nbe_123456", "NBE Black Star", "unknown", "Black Star 1016 (V7)", "NBE")
    assert device.getUid() == "nbe_123456"
    assert device.getId() == "nbe_123456"
