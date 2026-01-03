import voluptuous as vol
import aiohttp
import async_timeout
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN

class PiHoleStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            host = user_input["host"]
            port = user_input["port"]
            # Ensure no accidental spaces
            pw = user_input["api_key"].strip()

            try:
                async with async_timeout.timeout(10):
                    # We create a temporary session to test credentials
                    async with aiohttp.ClientSession() as session:
                        url = f"http://{host}:{port}/api/auth"
                        # Pi-hole v6 requires Content-Type: application/json
                        async with session.post(url, json={"password": pw}) as resp:
                            response_data = await resp.json()
                            session_info = response_data.get("session", {})
                            
                            # v6 returns valid: true even if password is wrong, 
                            # but sid will be null
                            if resp.status == 200 and session_info.get("sid") is not None:
                                return self.async_create_entry(
                                    title=f"Pi-Hole ({host})", 
                                    data={**user_input, "api_key": pw}
                                )
                            
                            errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("port", default=80): int,
                vol.Required("api_key"): str,
            }),
            errors=errors
        )
