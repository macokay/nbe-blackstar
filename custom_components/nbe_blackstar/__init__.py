import logging
import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .api import NbeReader
from .const import (
    CONF_COUNTER_FACTOR,
    CONF_HOPPER_CAPACITY,
    CONF_PINCODE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENERGY_FILE,
    HOPPER_STORE,
    LEGACY_OBJECT_IDS,
)
from .coordinator import NbeCoordinator
from .hopper import Hopper

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER, Platform.BUTTON]
STORAGE_VERSION = 1


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data
    energy_path = hass.config.path(ENERGY_FILE.format(serial=data[CONF_SERIAL]))
    reader = await hass.async_add_executor_job(
        NbeReader, data[CONF_HOST], data[CONF_SERIAL], data[CONF_PINCODE], data[CONF_PORT], energy_path
    )
    store = Store(hass, STORAGE_VERSION, HOPPER_STORE.format(serial=data[CONF_SERIAL]))
    saved = await store.async_load() or {}
    capacity = entry.options.get(CONF_HOPPER_CAPACITY) or None
    factor = entry.options.get(CONF_COUNTER_FACTOR)
    hopper = Hopper(saved, capacity_kg=capacity, factor_override=factor)
    interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = NbeCoordinator(hass, entry, reader, interval, hopper, store)
    coordinator.firmware = await hass.async_add_executor_job(reader.read_firmware)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_reload))

    async def _close_on_stop(_event: Event) -> None:
        # Home Assistant stop does not unload entries, so write the energy total and silo estimate here
        await coordinator.async_flush()
        try:
            await hass.async_add_executor_job(reader.close)
        except Exception as e:
            _LOGGER.warning("Unable to close reader on stop: %s", type(e).__name__)

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _close_on_stop))
    _migrate_object_ids(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


def _migrate_object_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # versions up to 0.0.13 used Danish object ids. Rename the registry entries once: unique_id always, and the entity id
    # unless the user has given it another name or the English id is taken.
    registry = er.async_get(hass)
    prefix = f"nbe_{entry.data[CONF_SERIAL]}_"
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if not entity.unique_id.startswith(prefix):
            continue
        old = entity.unique_id[len(prefix) :]
        new = LEGACY_OBJECT_IDS.get(old)
        if new is None:
            continue
        changes = {"new_unique_id": prefix + new}
        target = f"{entity.domain}.nbe_{new}"
        if re.fullmatch(rf"{entity.domain}\.nbe_{old}(_\d+)?", entity.entity_id) and registry.async_get(target) is None:
            changes["new_entity_id"] = target
        try:
            registry.async_update_entity(entity.entity_id, **changes)
        except ValueError as err:
            _LOGGER.warning("Unable to rename %s to English ids: %s", entity.entity_id, err)


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # deleting the integration forgets the silo estimate too; a new setup starts from a blank estimate
    await Store(hass, STORAGE_VERSION, HOPPER_STORE.format(serial=entry.data[CONF_SERIAL])).async_remove()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_flush()
        await hass.async_add_executor_job(coordinator.reader.close)
    return unloaded
