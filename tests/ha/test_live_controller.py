"""Read-only check against a real controller. Skipped unless NBE_LIVE_HOST, NBE_LIVE_SERIAL and NBE_LIVE_PIN are set.

Only get() is used; nothing is written to the controller.
"""

import os

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.setup import async_setup_component  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

HOST = os.environ.get("NBE_LIVE_HOST")
SERIAL = os.environ.get("NBE_LIVE_SERIAL")
PIN = os.environ.get("NBE_LIVE_PIN")

pytestmark = [
    pytest.mark.skipif(not (HOST and SERIAL and PIN), reason="live controller not configured"),
    pytest.mark.enable_socket,
]

COMPONENT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "custom_components", "nbe_blackstar")


@pytest.fixture
def hass_config_dir(tmp_path):
    (tmp_path / "custom_components").mkdir()
    os.symlink(COMPONENT, tmp_path / "custom_components" / "nbe_blackstar")
    return str(tmp_path)


@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield


def _entry():
    return MockConfigEntry(
        domain="nbe_blackstar",
        data={"host": HOST, "serial": SERIAL, "pincode": PIN, "port": 8483},
        options={"lang": "da"},
    )


async def test_live_entities_have_values_and_stable_ids(hass):
    entry = _entry()
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()
    temp = hass.states.get("sensor.nbe_kedel_temperatur")
    assert temp is not None and temp.state not in ("unknown", "unavailable")
    assert float(temp.state) > 0
    assert hass.states.get("binary_sensor.nbe_kedelpumpe").state in ("on", "off")
    assert hass.states.get("sensor.nbe_udetemperatur").state in ("unknown", "unavailable")
    assert hass.states.get("sensor.nbe_braender_energi_kwh") is not None


async def test_live_reload_keeps_entities(hass):
    entry = _entry()
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, "nbe_blackstar", {})
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.nbe_kedel_temperatur") is not None
    assert hass.states.get("sensor.nbe_braender_energi_kwh") is not None
