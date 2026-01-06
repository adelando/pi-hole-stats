"""Update platform for Pi-hole v6 Stats."""
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the update entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Define entities explicitly to avoid any 'None' keys during loop
    async_add_entities([
        PiHoleUpdate(coordinator, entry, "core", "Pi-hole Core Update"),
        PiHoleUpdate(coordinator, entry, "ftl", "Pi-hole FTL Update"),
        PiHoleUpdate(coordinator, entry, "web", "Pi-hole Web Interface Update"),
    ])

class PiHoleUpdate(CoordinatorEntity, UpdateEntity):
    """Representation of a Pi-hole update entity."""

    def __init__(self, coordinator, entry, key, name):
        """Initialize the update entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}_update_v2"
        self._attr_device_info = coordinator.device_info
        
        # Using the explicit Enum for 'No Features Supported' (Removes Install button)
        self._attr_supported_features = UpdateEntityFeature(0)
        
        # Keep summary simple to avoid serialization errors
        self._attr_release_summary = "Manual Update Required: Run 'pihole -up' via SSH."

    @property
    def installed_version(self):
        """Return the installed version."""
        val = self.coordinator.data.get(f"ver_{self._key}")
        return str(val) if val is not None else "Unknown"

    @property
    def latest_version(self):
        """Return the latest version available."""
        val = self.coordinator.data.get(f"rem_{self._key}")
        return str(val) if val is not None else "Unknown"

    @property
    def release_url(self):
        """URL for release notes."""
        return f"https://github.com/pi-hole/{self._key}/releases"
