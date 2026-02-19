import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "spoolmansync"

class SpoolmanSyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SpoolmanSync."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            try:
                session = async_get_clientsession(self.hass)
                async with session.get(f"{url}/api/settings") as response:
                    if response.status == 200:
                        return self.async_create_entry(title="SpoolmanSync", data={CONF_URL: url})
                    else:
                        errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Error connecting to SpoolmanSync")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_URL, default="http://192.168.0.34:3000"): str,
            }),
            errors=errors,
        )
