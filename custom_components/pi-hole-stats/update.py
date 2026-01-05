from homeassistant.components.update import (
    UpdateEntity, 
    UpdateEntityFeature, 
    UpdateDeviceClass
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Pi-hole update entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Add entities for Core, FTL, and Web components
    async_add_entities([
        PiHoleUpdateEntity(coordinator, entry, "core", "Core"),
        PiHoleUpdateEntity(coordinator, entry, "ftl", "FTL"),
        PiHoleUpdateEntity(coordinator, entry, "web", "Web Interface"),
    ])

class PiHoleUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Representation of a Pi-hole update entity."""

    # Set supported features - Release notes allow the UI to show a link to GitHub
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(self, coordinator, entry, key, name):
        """Initialize the update entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Pi-hole {name} Update"
        self._attr_unique_id = f"{entry.entry_id}_update_{key}"
        self._attr_device_info = coordinator.device_info
        
        # Determine the release URL based on the component
        repo = "web" if key == "web" else "pi-hole"
        self._attr_release_url = f"https://github.com/pi-hole/{repo}/releases"

    @property
    def installed_version(self):
        """Version installed and in use."""
        return self.coordinator.data.get(f"ver_{self._key}")

    @property
    def latest_version(self):
        """Latest version available from the remote."""
        return self.coordinator.data.get(f"rem_{self._key}")
