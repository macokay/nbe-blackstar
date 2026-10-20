import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .api import NbeReader, validate_input
from .const import (
    CONF_DEVICE_NAME,
    CONF_LANG,
    CONF_PINCODE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL,
    DEFAULT_DEVICE_NAME,
    DEFAULT_LANG,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LANGS,
)


def _options_schema(lang, interval):
    return {
        vol.Required(CONF_LANG, default=lang): vol.In(LANGS),
        vol.Required(CONF_SCAN_INTERVAL, default=interval): vol.All(int, vol.Range(min=10, max=3600)),
    }


def _try_connect(host, serial, pincode, port):
    reader = NbeReader(host, serial, pincode, port)
    try:
        reader.poll()
    finally:
        reader.close()


class NbeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            errors = validate_input(
                user_input[CONF_HOST], user_input[CONF_SERIAL], user_input[CONF_PINCODE], user_input[CONF_PORT]
            )
            if not errors:
                await self.async_set_unique_id(user_input[CONF_SERIAL])
                self._abort_if_unique_id_configured()
                try:
                    await self.hass.async_add_executor_job(
                        _try_connect,
                        user_input[CONF_HOST],
                        user_input[CONF_SERIAL],
                        user_input[CONF_PINCODE],
                        user_input[CONF_PORT],
                    )
                except Exception:
                    errors["base"] = "cannot_connect"
            if not errors:
                data = {k: user_input[k] for k in (CONF_HOST, CONF_SERIAL, CONF_PINCODE, CONF_PORT, CONF_DEVICE_NAME)}
                options = {CONF_LANG: user_input[CONF_LANG], CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL}
                return self.async_create_entry(title=data[CONF_DEVICE_NAME], data=data, options=options)
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_SERIAL): str,
                vol.Required(CONF_PINCODE): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_LANG, default=DEFAULT_LANG): vol.In(LANGS),
                vol.Optional(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NbeOptionsFlow()


class NbeOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        options = self.config_entry.options
        schema = vol.Schema(
            _options_schema(options.get(CONF_LANG, DEFAULT_LANG), options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        )
        return self.async_show_form(step_id="init", data_schema=schema)
