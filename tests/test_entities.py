import json

import nbe


class RecordingClient:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload, retain))

    def subscribe(self, topic, qos=0):
        pass


def _fresh_entities(monkeypatch):
    monkeypatch.setattr(nbe, "DataEntries", [])
    monkeypatch.setattr(nbe.settings, "config", {"ha_prefix": "homeassistant", "debug": False}, raising=False)
    client = RecordingClient()
    nbe.populate_resources(client)
    return client


def _config_payload(client, object_id):
    for topic, payload, _ in client.published:
        entity = json.loads(payload).get("default_entity_id", "") if payload else ""
        if entity.endswith(".nbe_" + object_id):
            return json.loads(payload)
    raise AssertionError("no discovery payload for " + object_id)


def test_clean_value_hides_not_connected_sensor():
    assert nbe.clean_value("999.9") == ""


def test_clean_value_hides_negative_pellet_count():
    assert nbe.clean_value("-2933.9", nonnegative=True) == ""


def test_clean_value_keeps_negative_temperature():
    assert nbe.clean_value("-3.5") == "-3.5"


def test_clean_value_keeps_normal_reading():
    assert nbe.clean_value("69.4") == "69.4"


def test_binary_value_maps_controller_flags():
    assert nbe.binary_value("1") == "ON"
    assert nbe.binary_value("0") == "OFF"
    assert nbe.binary_value("x") == ""


def test_discovery_uses_danish_name_and_ascii_entity_id(monkeypatch):
    client = _fresh_entities(monkeypatch)
    payload = _config_payload(client, "gulv_fremloeb")
    assert payload["name"] == "Gulvvarme fremløb"
    assert payload["unique_id"].endswith("_gulv_fremloeb")
    assert payload["device"]["identifiers"] == nbe.device.getId()


def test_discovery_publishes_binary_sensor_for_pump(monkeypatch):
    client = _fresh_entities(monkeypatch)
    payload = _config_payload(client, "kedelpumpe")
    assert payload["device_class"] == "running"


def test_legacy_entities_are_removed(monkeypatch):
    client = _fresh_entities(monkeypatch)
    cleared = {topic for topic, payload, retain in client.published if payload == "" and retain}
    assert "homeassistant/sensor/nbeblackstar/burned_total/config" in cleared
    assert "homeassistant/climate/nbeblackstar/core_temp_regulation/config" in cleared
