from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass

from .api import sensor_value
from .const import DOMAIN, ENTITIES
from .coordinator import HopperEntity, NbeEntity


def _opt(value):
    return None if value == "none" else value


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [NbeSensor(coordinator, entry, row) for row in ENTITIES if row[1] == "sensor"]
    entities.append(HopperLevelSensor(coordinator, entry))
    entities.append(HopperDaysSensor(coordinator, entry))
    async_add_entities(entities)


class NbeSensor(NbeEntity, SensorEntity):
    def __init__(self, coordinator, entry, row):
        super().__init__(coordinator, entry, row)
        self.entity_id = f"sensor.nbe_{self._object_id}"
        _, _, _, _, icon, state_class, device_class, unit = row
        self._attr_icon = _opt(icon)
        self._attr_state_class = SensorStateClass(state_class) if _opt(state_class) else None
        self._attr_device_class = SensorDeviceClass(device_class) if _opt(device_class) else None
        self._attr_native_unit_of_measurement = _opt(unit)

    @property
    def native_value(self):
        raw = self._raw
        return None if raw is None else sensor_value(self._resource, raw)


class HopperLevelSensor(HopperEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "kg"
    _attr_icon = "mdi:weight-kilogram"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "pellets_left", "Pellets left")
        self.entity_id = "sensor.nbe_pellets_left"

    @property
    def native_value(self):
        level = self.coordinator.hopper.level_kg
        return None if level is None else round(level, 1)

    @property
    def extra_state_attributes(self):
        hopper = self.coordinator.hopper
        return {
            "counter_factor": round(hopper.factor, 3),
            "last_refill": hopper.last_refill,
            "capacity_kg": hopper.capacity_kg,
        }


class HopperDaysSensor(HopperEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "d"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "days_left", "Days left")
        self.entity_id = "sensor.nbe_days_left"

    @property
    def native_value(self):
        days = self.coordinator.hopper.days_left()
        return None if days is None else round(days, 1)
