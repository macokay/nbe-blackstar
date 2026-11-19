from homeassistant.components.button import ButtonEntity

from .const import DOMAIN
from .coordinator import HopperEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HopperRefillButton(coordinator, entry)])


class HopperRefillButton(HopperEntity, ButtonEntity):
    _attr_icon = "mdi:gas-station"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "registrer_paafyldning", "Registrér påfyldning", "Register refill")
        self.entity_id = "button.nbe_registrer_paafyldning"

    async def async_press(self):
        await self.coordinator.async_register_refill()
