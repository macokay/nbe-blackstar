from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .api import binary_value
from .const import DOMAIN, ENTITIES
from .coordinator import NbeEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(NbeBinarySensor(coordinator, entry, row) for row in ENTITIES if row[1] == "binary_sensor")


class NbeBinarySensor(NbeEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, row):
        super().__init__(coordinator, entry, row)
        self.entity_id = f"binary_sensor.nbe_{self._object_id}"
        self._attr_icon = row[5]
        self._attr_device_class = None if row[7] == "none" else BinarySensorDeviceClass(row[7])

    @property
    def is_on(self):
        raw = self._raw
        return None if raw is None else binary_value(raw)
