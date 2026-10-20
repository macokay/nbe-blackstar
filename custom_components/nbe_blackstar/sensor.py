from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass

from .api import sensor_value
from .const import DOMAIN, ENTITIES
from .coordinator import NbeEntity


def _opt(value):
    return None if value == "none" else value


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(NbeSensor(coordinator, entry, row) for row in ENTITIES if row[1] == "sensor")


class NbeSensor(NbeEntity, SensorEntity):
    def __init__(self, coordinator, entry, row):
        super().__init__(coordinator, entry, row)
        self.entity_id = f"sensor.nbe_{self._object_id}"
        _, _, _, _, _, icon, state_class, device_class, unit = row
        self._attr_icon = _opt(icon)
        self._attr_state_class = SensorStateClass(state_class) if _opt(state_class) else None
        self._attr_device_class = SensorDeviceClass(device_class) if _opt(device_class) else None
        self._attr_native_unit_of_measurement = _opt(unit)

    @property
    def native_value(self):
        raw = self._raw
        return None if raw is None else sensor_value(self._resource, raw)
