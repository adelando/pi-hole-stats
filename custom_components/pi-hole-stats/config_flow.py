import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class PiHoleStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input["host"], data=user_input)

        return self.show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Optional("api_key"): str,
            }),
        )
