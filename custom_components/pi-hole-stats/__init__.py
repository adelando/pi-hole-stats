"""The Pi-hole v6 Stats integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import PiHoleStatsCoordinator

_LOGGER = logging.getLogger(__name__)

# List the platforms to be loaded (must match your file names: sensor.py, update.py)
PLATFORMS = ["sensor", "update"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pi-hole v6 Stats from a config entry."""
    
    # Initialize the coordinator
    coordinator = PiHoleStatsCoordinator(hass, entry)

    # Fetch initial data from Pi-hole before completing setup
    # This ensures sensors don't start with 'Unknown' states
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data so sensors/updates can access it
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the setup to the sensor and update platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This handles cleaning up if the user deletes or disables the integration
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
