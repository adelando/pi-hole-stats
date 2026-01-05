from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Core, FTL, and Web Updates
    async_add_entities([
        PiHoleUpdateEntity(coordinator, entry, "core", "Core"),
        PiHoleUpdateEntity(coordinator, entry, "ftl", "FTL"),
        PiHoleUpdateEntity(coordinator, entry, "web", "Web Interface"),
    ])

class PiHoleUpdateEntity(UpdateEntity):
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES
    
    def __init__(self, coordinator, entry, key, name):
        self.coordinator = coordinator
        self._key = key
        # Prefix with device name for the UI
        self._attr_name = f"{name}"
        self._attr_unique_id = f"{entry.entry_id}_update_{key}"
        self._attr_device_info = coordinator.device_info
        self._attr_release_url = "https://github.com/pi-hole/pi-hole/releases"

    @property
    def installed_version(self):
        # Parses 'v6.0 (Up: False)' to get 'v6.0'
        raw = self.coordinator.data.get(f"ver_{self._key}", "")
        return raw.split(" ")[0] if raw else None

    @property
    def latest_version(self):
        # Flags as a different version if Up: True is in the string
        up_avail = "(Up: True)" in self.coordinator.data.get(f"ver_{self._key}", "")
        if up_avail:
            return f"{self.installed_version} (Update Available)"
        return self.installed_version
