import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp

from .const import DOMAIN, NAME, DEFAULT_PORT

class PiHoleStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pi-hole v6 Stats."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip().rstrip("/")
            port = user_input[CONF_PORT]
            api_key = user_input[CONF_API_KEY]
            
            # 1. Validate the connection to Pi-hole v6
            session = async_get_clientsession(self.hass)
            try:
                auth_url = f"http://{host}:{port}/api/auth"
                async with session.post(auth_url, json={"password": api_key}, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        sid = data.get("session", {}).get("sid")
                        if sid:
                            # 2. SUCCESS: Create entry
                            # The 'title' here is what our sensor.py uses for naming
                            return self.async_create_entry(
                                title=user_input.get("name", "Pi-hole"),
                                data={
                                    CONF_HOST: host,
                                    CONF_PORT: port,
                                    CONF_API_KEY: api_key,
                                    "sid": sid
                                }
                            )
                        errors["base"] = "invalid_auth"
                    else:
                        errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        # 3. Form Schema
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default="Pi-hole"): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_API_KEY): str,
            }),
            errors=errors,
        )
