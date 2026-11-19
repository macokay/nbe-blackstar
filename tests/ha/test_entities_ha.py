"""Runs in a real Home Assistant test instance. Needs pytest-homeassistant-custom-component; skipped otherwise."""

import json
import os

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.setup import async_setup_component  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.nbe_blackstar import api  # noqa: E402

COMPONENT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "custom_components", "nbe_blackstar")

CONTROLLER = {
    "operating_data/boiler_temp": "70.6",
    "operating_data/external_temp": "999.9",
    "operating_data/boiler_pump_state": "1",
    "operating_data/house_pump_state": "0",
    "operating_data/power_kw": "6.9",
    "consumption_data/counter": "46555.4",
}


@pytest.fixture
def hass_config_dir(tmp_path):
    (tmp_path / "custom_components").mkdir()
    os.symlink(COMPONENT, tmp_path / "custom_components" / "nbe_blackstar")
    return str(tmp_path)


@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield


@pytest.fixture
def fake_controller(monkeypatch):
    monkeypatch.setattr(api.NbeReader, "poll", lambda self: dict(CONTROLLER))
    monkeypatch.setattr(api.NbeReader, "read_firmware", lambda self: "7.0680")
    monkeypatch.setattr(api.NbeReader, "close", lambda self: None)


def _entry():
    return MockConfigEntry(
        domain="nbe_blackstar",
        data={"host": "192.0.2.10", "serial": "123456", "pincode": "123456", "port": 8483},
    )


async def test_entities_have_stable_ids_and_values(hass, fake_controller):
    entry = _entry()
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()

    temp = hass.states.get("sensor.nbe_boiler_temperature")
    assert temp is not None
    assert temp.state == "70.6"
    assert temp.attributes["friendly_name"].endswith("Boiler temperature")

    assert hass.states.get("binary_sensor.nbe_boiler_pump").state == "on"
    assert hass.states.get("binary_sensor.nbe_floor_pump").state == "off"
    assert hass.states.get("sensor.nbe_pellet_consumption_counter").state == "46555.4"


async def test_not_connected_sensor_is_unknown_not_999(hass, fake_controller):
    entry = _entry()
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()
    outdoor = hass.states.get("sensor.nbe_outdoor_temperature")
    assert outdoor is not None
    assert outdoor.state == "unknown"


async def test_old_danish_entity_ids_are_renamed_to_english(hass, fake_controller):
    from homeassistant.helpers import entity_registry as er

    entry = _entry()
    entry.add_to_hass(hass)
    registry = er.async_get(hass)

    def old(uid, entity_id):
        entity_id_name = entity_id.split(".", 1)[1]
        return registry.async_get_or_create("sensor", "nbe_blackstar", "nbe_123456_" + uid, suggested_object_id=entity_id_name, config_entry=entry)

    old("kedel_temperatur", "sensor.nbe_kedel_temperatur")  # default id
    old("varmtvand", "sensor.nbe_varmtvand_2")  # the id was taken by the MQTT bridge entity
    registry.async_get_or_create("sensor", "mqtt", "bridge-hot-water", suggested_object_id="nbe_varmtvand")
    old("kedel_maal", "sensor.pillefyr_maal")  # the user chose the id
    old("ilt_maal", "sensor.nbe_ilt_maal")  # the English id is taken by another entity
    registry.async_get_or_create("sensor", "mqtt", "other", suggested_object_id="nbe_oxygen_target")

    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()

    def entity_id(uid):
        return registry.async_get_entity_id("sensor", "nbe_blackstar", "nbe_123456_" + uid)

    assert entity_id("boiler_temperature") == "sensor.nbe_boiler_temperature"
    assert entity_id("hot_water") == "sensor.nbe_hot_water"
    assert entity_id("boiler_target") == "sensor.pillefyr_maal"
    assert entity_id("oxygen_target") == "sensor.nbe_ilt_maal"
    for legacy in ("kedel_temperatur", "varmtvand", "kedel_maal", "ilt_maal"):
        assert entity_id(legacy) is None
    assert hass.states.get("sensor.nbe_boiler_temperature").state == "70.6"
    assert hass.states.get("sensor.nbe_varmtvand") is None  # the bridge entity keeps its own id, ours moved
    assert registry.async_get("sensor.nbe_varmtvand").platform == "mqtt"
    # a second setup changes nothing
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entity_id("boiler_temperature") == "sensor.nbe_boiler_temperature"


async def test_new_installs_get_english_ids_for_the_silo_entities(hass, fake_controller):
    entry = _entry()
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()
    for entity_id in (
        "sensor.nbe_pellets_left",
        "sensor.nbe_days_left",
        "binary_sensor.nbe_refill_soon",
        "number.nbe_refill_amount",
        "number.nbe_calibrate_silo_level",
        "button.nbe_register_refill",
    ):
        assert hass.states.get(entity_id) is not None, entity_id


async def test_device_name_comes_from_config(hass, fake_controller):
    entry = MockConfigEntry(
        domain="nbe_blackstar",
        data={"host": "192.0.2.10", "serial": "123456", "pincode": "123456", "port": 8483, "device_name": "Kedel"},
    )
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()
    temp = hass.states.get("sensor.nbe_boiler_temperature")
    assert temp is not None
    assert temp.attributes["friendly_name"].startswith("Kedel ")


async def test_firmware_read_is_retried_after_failed_setup(hass, fake_controller, monkeypatch):
    from homeassistant.helpers import device_registry as dr

    calls = []

    def read_firmware(self):
        calls.append(1)
        # call 1 is the setup read, call 2 the retry in the first poll; both fail
        return None if len(calls) <= 2 else "7.0680"

    monkeypatch.setattr(api.NbeReader, "read_firmware", read_firmware)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()

    def device():
        devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
        return next(d for d in devices if ("nbe_blackstar", "123456") in d.identifiers)

    assert device().sw_version is None

    await hass.data["nbe_blackstar"][entry.entry_id].async_refresh()
    await hass.async_block_till_done()

    assert device().sw_version == "7.0680"


@pytest.fixture
def controller_keep_close(monkeypatch):
    monkeypatch.setattr(api.NbeReader, "poll", lambda self: dict(CONTROLLER))
    monkeypatch.setattr(api.NbeReader, "read_firmware", lambda self: "7.0680")


async def test_homeassistant_stop_flushes_energy_total(hass, controller_keep_close):
    from homeassistant.const import EVENT_HOMEASSISTANT_STOP

    entry = _entry()
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()

    reader = hass.data["nbe_blackstar"][entry.entry_id].reader
    reader.meter.kwh = 12.5
    assert not os.path.exists(reader.meter.path)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    with open(reader.meter.path) as f:
        assert json.load(f) == {"kwh": 12.5}


async def test_stop_after_reload_flushes_once(hass, controller_keep_close, monkeypatch):
    from homeassistant.const import EVENT_HOMEASSISTANT_STOP

    entry = _entry()
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    closes = []
    real_close = api.NbeReader.close

    def counting_close(self):
        closes.append(self)
        real_close(self)

    monkeypatch.setattr(api.NbeReader, "close", counting_close)
    reader = hass.data["nbe_blackstar"][entry.entry_id].reader
    reader.meter.kwh = 3.0

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    assert closes == [reader]
    with open(reader.meter.path) as f:
        assert json.load(f) == {"kwh": 3.0}
