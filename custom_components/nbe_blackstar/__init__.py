import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant

from .api import NbeReader
from .const import (
    CONF_PINCODE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENERGY_FILE,
)
from .coordinator import NbeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS =[Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data
    energy_path = hass.config.path(ENERGY_FILE.format(serial=data[CONF_SERIAL]))
    reader = await hass.async_add_executor_job(
        NbeReader, data[CONF_HOST], data[CONF_SERIAL], data[CONF_PINCODE], data[CONF_PORT], energy_path
    )
    interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = NbeCoordinator(hass, entry, reader, interval)
    coordinator.firmware = await hass.async_add_executor_job(reader.read_firmware)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_reload))

    async def _close_on_stop(_event: Event) -> None:
        # Home Assistant stop does not unload entries, so write the energy total here
        try:
            await hass.async_add_executor_job(reader.close)
        except Exception as e:
            _LOGGER.warning("Unable to close reader on stop: %s", type(e).__name__)

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _close_on_stop))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(coordinator.reader.close)
    return unloaded

