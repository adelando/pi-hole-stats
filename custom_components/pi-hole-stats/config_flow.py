import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_API_KEY, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, DEFAULT_PORT

class PiHoleStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pi-hole v6 Stats."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Prevent duplicate entries for the same host
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            host = user_input[CONF_HOST].strip().rstrip("/")
            port = user_input[CONF_PORT]
            api_key = user_input[CONF_API_KEY]
            
            session = async_get_clientsession(self.hass)
            try:
                # Test the connection to the v6 API
                auth_url = f"http://{host}:{port}/api/auth"
                async with session.post(auth_url, json={"password": api_key}, timeout=5) as resp:
                    if resp.status == 200:
                        # SUCCESS: Pass the 'name' to the title so sensors can be numbered
                        return self.async_create_entry(
                            title=user_input.get(CONF_NAME, "Pi-hole"),
                            data=user_input
                        )
                    errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        # The keys here (CONF_NAME, CONF_HOST, etc.) match the JSON 'data' keys
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Pi-hole"): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_API_KEY): str,
            }),
            errors=errors,
        )
