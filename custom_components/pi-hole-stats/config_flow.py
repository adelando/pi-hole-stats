import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from typing import Any

from .const import DOMAIN

class PiHoleStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pi-Hole Statistics."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Create the entry
            return self.async_create_entry(
                title=f"Pi-Hole ({user_input['host']})", 
                data=user_input
            )

        # Define the schema
        data_schema = vol.Schema({
            vol.Required("host"): str,
            vol.Optional("api_key", default=""): str,
        })

        # Explicitly return the form
        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors
        )
