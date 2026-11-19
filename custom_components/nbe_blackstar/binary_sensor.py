from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .api import alarm_value, binary_value
from .const import DOMAIN, ENTITIES, STATE_RESOURCE
from .coordinator import HopperEntity, NbeEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [NbeBinarySensor(coordinator, entry, row) for row in ENTITIES if row[1] == "binary_sensor"]
    entities.append(HopperLowBinarySensor(coordinator, entry))
    async_add_entities(entities)


class NbeBinarySensor(NbeEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, row):
        super().__init__(coordinator, entry, row)
        self.entity_id = f"binary_sensor.nbe_{self._object_id}"
        self._attr_icon = row[5]
        self._attr_device_class = None if row[7] == "none" else BinarySensorDeviceClass(row[7])
        if self._object_id == "alarm":
            # the alarm is now decoded from the flag and the operating state, so it can carry the problem class
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self):
        raw = self._raw
        if self._object_id == "alarm":
            state = (self.coordinator.data or {}).get(STATE_RESOURCE)
            return alarm_value(raw, state)
        return None if raw is None else binary_value(raw)

    @property
    def extra_state_attributes(self):
        if self._object_id != "alarm":
            return None
        # the controller's raw flag, kept visible until its alarm value is known
        return {"raw": self._raw}


class HopperLowBinarySensor(HopperEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:gas-station-off"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "fyld_snart_paa", "Fyld snart på", "Refill soon")
        self.entity_id = "binary_sensor.nbe_fyld_snart_paa"

    @property
    def is_on(self):
        return self.coordinator.hopper.low()

    @property
    def extra_state_attributes(self):
        days = self.coordinator.hopper.days_left()
        return {"days_left": None if days is None else round(days, 1)}
