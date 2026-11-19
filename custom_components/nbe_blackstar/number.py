from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode

from .const import DOMAIN
from .coordinator import HopperEntity

MAX_SILO_KG = 2000


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HopperLevelNumber(coordinator, entry), HopperRefillNumber(coordinator, entry)])


class HopperLevelNumber(HopperEntity, NumberEntity):
    _attr_device_class = NumberDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = "kg"
    _attr_native_min_value = 0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:weight-kilogram"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "calibrate_silo_level", "Calibrate silo level (kg)")
        self.entity_id = "number.nbe_calibrate_silo_level"
        self._attr_native_max_value = coordinator.hopper.capacity_kg or MAX_SILO_KG

    @property
    def native_value(self):
        level = self.coordinator.hopper.level_kg
        return None if level is None else round(level, 1)

    async def async_set_native_value(self, value):
        await self.coordinator.async_set_level(value)


class HopperRefillNumber(HopperEntity, NumberEntity):
    _attr_device_class = NumberDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = "kg"
    _attr_native_min_value = 1
    _attr_native_max_value = MAX_SILO_KG
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:package-variant-closed"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "refill_amount", "Refill amount (kg)")
        self.entity_id = "number.nbe_refill_amount"

    @property
    def native_value(self):
        return self.coordinator.hopper.refill_kg

    async def async_set_native_value(self, value):
        await self.coordinator.async_set_refill_kg(value)
