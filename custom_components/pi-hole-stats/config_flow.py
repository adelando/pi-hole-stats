import voluptuous as vol
import aiohttp
import async_timeout
from homeassistant import config_entries
from .const import DOMAIN

class PiHoleStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Test the connection
            host = user_input["host"]
            port = user_input["port"]
            location = user_input["location"]
            api_key = user_input.get("api_key", "")
            
            # Construct URL based on location (v5 vs v6 style)
            path = "admin/api.php" if location == "admin" else "api"
            url = f"http://{host}:{port}/{path}?summaryRaw&auth={api_key}"

            try:
                async with async_timeout.timeout(10):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                return self.async_create_entry(
                                    title=f"Pi-Hole ({host})", 
                                    data=user_input
                                )
                            errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("port", default=80): int,
                vol.Required("location", default="admin"): vol.In(["admin", "api"]),
                vol.Optional("api_key"): str,
            }),
            errors=errors
        )
