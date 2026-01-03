import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

class PiHoleStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pi-Hole Statistics."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # You could add a connection test here later.
            # For now, we just create the entry.
            return self.async_create_entry(
                title=f"Pi-Hole ({user_input['host']})", 
                data=user_input
            )

        # This schema defines what the user sees in the popup
        DATA_SCHEMA = vol.Schema({
            vol.Required("host"): str,
            vol.Optional("api_key", default=""): str,
        })

        return self.show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors
        )
