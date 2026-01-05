import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_API_KEY, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, DEFAULT_PORT

class PiHoleStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            session = async_get_clientsession(self.hass)
            try:
                url = f"http://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}/api/auth"
                async with session.post(url, json={"password": user_input[CONF_API_KEY]}, timeout=5) as resp:
                    if resp.status == 200:
                        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
                    errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Pi-hole"): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_API_KEY): str,
            }),
            errors=errors
        )
