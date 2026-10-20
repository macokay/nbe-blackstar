import logging
from datetime import timedelta

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed

from .api import NbeReader
from .const import CONF_LANG, CONF_SERIAL, DEFAULT_LANG, DOMAIN

log = logging.getLogger(__name__)


class NbeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, reader: NbeReader, interval: int):
        super().__init__(hass, log, config_entry=entry, name=DOMAIN, update_interval=timedelta(seconds=interval))
        self.reader = reader
        self.firmware = None

    async def _async_update_data(self):
        try:
            return await self.hass.async_add_executor_job(self.reader.poll)
        except Exception as err:
            raise UpdateFailed(f"Unable to query controller: {type(err).__name__}") from err


class NbeEntity(CoordinatorEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator, entry, platform, row):
        super().__init__(coordinator)
        resource, _, object_id, name_da, name_en, *_ = row
        self._resource = resource
        serial = entry.data[CONF_SERIAL]
        self._attr_name = name_en if entry.options.get(CONF_LANG, DEFAULT_LANG) == "en" else name_da
        self._attr_unique_id = f"nbe_{serial}_{object_id}"
        self._attr_suggested_object_id = f"nbe_{object_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name="NBE Black Star",
            manufacturer="NBE",
            model="Black Star 1016 (V7)",
            sw_version=coordinator.firmware,
        )

    @property
    def _raw(self):
        return (self.coordinator.data or {}).get(self._resource)
