import json

from nbe_blackstar import bridge as nbe


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
    for _topic, payload, _ in client.published:
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


def test_discovery_uses_english_name_and_entity_id_but_keeps_the_unique_id(monkeypatch):
    client = _fresh_entities(monkeypatch)
    payload = _config_payload(client, "floor_heating_flow")
    assert payload["name"] == "Floor heating flow"
    assert payload["default_entity_id"] == "sensor.nbe_floor_heating_flow"
    assert payload["unique_id"].endswith("_gulv_fremloeb")  # unchanged, so a running bridge keeps its entity
    assert payload["device"]["identifiers"] == nbe.device.getId()


def test_discovery_publishes_binary_sensor_for_pump(monkeypatch):
    client = _fresh_entities(monkeypatch)
    payload = _config_payload(client, "boiler_pump")
    assert payload["device_class"] == "running"


def _schema_rows():
    path = nbe.os.path.join(nbe.os.path.dirname(nbe.__file__), "nbe_schema")
    return [line.split(",") for line in open(path) if line.strip() and not line.startswith("#")]


def test_topics_and_unique_ids_keep_the_values_from_the_danish_names(monkeypatch):
    client = _fresh_entities(monkeypatch)
    for row in _schema_rows():
        old_id, old_key = nbe.LEGACY[row[8].strip()]
        payload = _config_payload(client, row[8].strip())
        assert payload["unique_id"].endswith("_" + old_id)
        assert "/" + old_key + "/" in payload["state_topic"] + "/"
    assert any(t.endswith("/kedeltemperatur/config") for t, _, _ in client.published)


def test_every_schema_entity_has_a_legacy_entry_and_ascii_english_names():
    rows = _schema_rows()
    assert {r[8].strip() for r in rows} == set(nbe.LEGACY)
    assert all(r[3].isascii() and r[8].isascii() for r in rows)
