"""Runs in a real Home Assistant test instance. Needs pytest-homeassistant-custom-component; skipped otherwise."""

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


def _entry(lang):
    return MockConfigEntry(
        domain="nbe_blackstar",
        data={"host": "192.0.2.10", "serial": "123456", "pincode": "123456", "port": 8483},
        options={"lang": lang},
    )


async def test_entities_have_stable_ids_and_values(hass, fake_controller):
    entry = _entry("da")
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()

    temp = hass.states.get("sensor.nbe_kedel_temperatur")
    assert temp is not None
    assert temp.state == "70.6"
    assert temp.attributes["friendly_name"].endswith("Kedeltemperatur")

    assert hass.states.get("binary_sensor.nbe_kedelpumpe").state == "on"
    assert hass.states.get("binary_sensor.nbe_gulvpumpe").state == "off"
    assert hass.states.get("sensor.nbe_forbrug_teller").state == "46555.4"


async def test_not_connected_sensor_is_unknown_not_999(hass, fake_controller):
    entry = _entry("da")
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()
    outdoor = hass.states.get("sensor.nbe_udetemperatur")
    assert outdoor is not None
    assert outdoor.state == "unknown"


async def test_english_names_use_same_entity_ids(hass, fake_controller):
    entry = _entry("en")
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()
    temp = hass.states.get("sensor.nbe_kedel_temperatur")
    assert temp is not None
    assert temp.attributes["friendly_name"].endswith("Boiler temperature")



async def test_device_name_comes_from_config(hass, fake_controller):
    entry = MockConfigEntry(
        domain="nbe_blackstar",
        data={"host": "192.0.2.10", "serial": "123456", "pincode": "123456", "port": 8483, "device_name": "Kedel"},
        options={"lang": "da"},
    )
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()
    temp = hass.states.get("sensor.nbe_kedel_temperatur")
    assert temp is not None
    assert temp.attributes["friendly_name"].startswith("Kedel ")
