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
            host = user_input["host"]
            port = user_input["port"]
            location = user_input["location"]
            pw = user_input.get("api_key", "")

            try:
                async with async_timeout.timeout(10):
                    async with aiohttp.ClientSession() as session:
                        if location == "api":
                            # Pi-hole v6 Auth Test
                            url = f"http://{host}:{port}/api/auth"
                            async with session.post(url, json={"password": pw}) as resp:
                                if resp.status == 200:
                                    return self.async_create_entry(title=host, data=user_input)
                                errors["base"] = "invalid_auth"
                        else:
                            # Pi-hole v5 Auth Test
                            url = f"http://{host}:{port}/admin/api.php?summaryRaw&auth={pw}"
                            async with session.get(url) as resp:
                                if resp.status == 200:
                                    return self.async_create_entry(title=host, data=user_input)
                                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("port", default=80): int,
                vol.Required("location", default="api"): vol.In(["admin", "api"]),
                vol.Required("api_key"): str,
            }),
            errors=errors
        )
