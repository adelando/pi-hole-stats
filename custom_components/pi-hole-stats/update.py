"""Update platform for Pi-hole v6 Stats."""
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
    
    async_add_entities([
        PiHoleUpdateEntity(coordinator, entry, "core", "Core"),
        PiHoleUpdateEntity(coordinator, entry, "ftl", "FTL"),
        PiHoleUpdateEntity(coordinator, entry, "web", "Web Interface"),
    ])

class PiHoleUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Representation of a Pi-hole update entity."""

    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(self, coordinator, entry, key, name):
        """Initialize the update entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Pi-hole {name} Update"
        self._attr_unique_id = f"{entry.entry_id}_update_{key}"
        self._attr_device_info = coordinator.device_info
        
        # Determine the release URL
        repo = "web" if key == "web" else "pi-hole"
        self._attr_release_url = f"https://github.com/pi-hole/{repo}/releases"
        
        # FIXED: This prevents HA from expecting an install action, clearing the unknown error
        self._attr_can_install = False

    @property
    def installed_version(self):
        """Return the current installed version."""
        return self.coordinator.data.get(f"ver_{self._key}")

    @property
    def latest_version(self):
        """Return the latest available version."""
        return self.coordinator.data.get(f"rem_{self._key}")
