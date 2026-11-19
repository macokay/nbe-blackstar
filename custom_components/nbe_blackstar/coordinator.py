import asyncio
import logging
import time
from datetime import timedelta

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed

from .api import NbeReader, as_number
from .const import (
    CONF_DEVICE_NAME,
    CONF_LANG,
    CONF_SERIAL,
    COUNTER_RESOURCE,
    DEFAULT_DEVICE_NAME,
    DEFAULT_LANG,
    DOMAIN,
    HOPPER_SAVE_DELAY,
    HOPPER_SAVE_EVERY,
    STATE_NO_FUEL,
    STATE_RESOURCE,
)

log = logging.getLogger(__name__)

MAX_FAILURES = 3
RETRY_DELAY = 2


class NbeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, reader: NbeReader, interval: int, hopper, store):
        super().__init__(hass, log, config_entry=entry, name=DOMAIN, update_interval=timedelta(seconds=interval))
        self.reader = reader
        self.firmware = None
        self.hopper = hopper
        self._store = store
        self._saved_at = 0.0
        self._failures = 0

    async def _async_update_data(self):
        try:
            data = await self._poll()
        except Exception as err:
            # the controller misses a poll now and then; keep the last values until it has failed MAX_FAILURES times in a row
            self._failures += 1
            if self.data is not None and self._failures < MAX_FAILURES:
                log.debug("Controller poll failed (%d in a row): %s", self._failures, type(err).__name__)
                return self.data
            raise UpdateFailed(f"Unable to query controller: {type(err).__name__}") from err
        self._failures = 0
        if self.firmware is None:
            await self._retry_firmware()
        self._track_silo(data)
        return data

    def _track_silo(self, data):
        counter = as_number(data.get(COUNTER_RESOURCE))
        alarm = as_number(data.get(STATE_RESOURCE)) == STATE_NO_FUEL
        now = time.time()
        changed = self.hopper.update(counter, alarm, now)
        # saved at once on an event, otherwise every HOPPER_SAVE_EVERY seconds: the SD card is spared
        if changed or now - self._saved_at >= HOPPER_SAVE_EVERY:
            self._save_hopper(now)

    def _save_hopper(self, now=None):
        self._saved_at = time.time() if now is None else now
        self._store.async_delay_save(self.hopper.to_dict, HOPPER_SAVE_DELAY)

    async def async_register_refill(self):
        self.hopper.refill(self.hopper.refill_kg, self._counter(), time.time())
        await self._saved_changed()

    async def async_set_refill_kg(self, kg):
        self.hopper.refill_kg = float(kg)
        await self._saved_changed()

    async def async_set_level(self, kg):
        self.hopper.set_level(kg, self._counter(), time.time())
        await self._saved_changed()

    async def async_flush(self):
        await self._store.async_save(self.hopper.to_dict())

    def _counter(self):
        return as_number((self.data or {}).get(COUNTER_RESOURCE))

    async def _saved_changed(self):
        self._save_hopper()
        self.async_update_listeners()

    async def _poll(self):
        try:
            return await self.hass.async_add_executor_job(self.reader.poll)
        except Exception:
            await asyncio.sleep(RETRY_DELAY)
            return await self.hass.async_add_executor_job(self.reader.poll)

    async def _retry_firmware(self):
        try:
            firmware = await self.hass.async_add_executor_job(self.reader.read_firmware)
            if firmware is None:
                return
            self.firmware = firmware
            serial = self.config_entry.data[CONF_SERIAL]
            registry = dr.async_get(self.hass)
            # not async_get_device: deprecated in new HA, and the by-identifier lookups are missing in HA 2025.1
            for device in dr.async_entries_for_config_entry(registry, self.config_entry.entry_id):
                if (DOMAIN, serial) in device.identifiers:
                    registry.async_update_device(device.id, sw_version=firmware)
        except Exception as e:
            log.debug("Firmware version retry failed: %s", type(e).__name__)


class NbeEntity(CoordinatorEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator, entry, row):
        resource, _, object_id, name_da, name_en, *_ = row
        self._resource = resource
        self._setup(coordinator, entry, object_id, name_da, name_en)

    def _setup(self, coordinator, entry, object_id, name_da, name_en):
        super().__init__(coordinator)
        serial = entry.data[CONF_SERIAL]
        self._attr_name = name_en if entry.options.get(CONF_LANG, DEFAULT_LANG) == "en" else name_da
        self._attr_unique_id = f"nbe_{serial}_{object_id}"
        self._object_id = object_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=entry.data.get(CONF_DEVICE_NAME, DEFAULT_DEVICE_NAME),
            manufacturer="Mac O Kay",
            model="Black Star 1016 (V7)",
            sw_version=coordinator.firmware,
        )

    @property
    def _raw(self):
        return (self.coordinator.data or {}).get(self._resource)


class HopperEntity(NbeEntity):
    # entities computed from the silo estimate, not read from a controller resource
    def __init__(self, coordinator, entry, object_id, name_da, name_en):
        self._resource = None
        self._setup(coordinator, entry, object_id, name_da, name_en)
