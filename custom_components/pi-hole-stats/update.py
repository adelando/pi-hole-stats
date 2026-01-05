from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # We create three update entities: Core, FTL, and Web
    async_add_entities([
        PiHoleUpdateEntity(coordinator, entry, "core", "Core"),
        PiHoleUpdateEntity(coordinator, entry, "ftl", "FTL"),
        PiHoleUpdateEntity(coordinator, entry, "web", "Web Interface"),
    ])

class PiHoleUpdateEntity(UpdateEntity):
    _attr_supported_features = UpdateEntityFeature.INSTALL # Optional: placeholder for future
    
    def __init__(self, coordinator, entry, key, name):
        self.coordinator = coordinator
        self._key = key
        self._attr_name = f"Pi-hole {name} Update"
        self._attr_unique_id = f"{entry.entry_id}_update_{key}"
        self._attr_device_info = coordinator.device_info # Reuse from sensor.py

    @property
    def installed_version(self):
        # Extracts 'v6.0' from 'v6.0 (Up: False)'
        raw = self.coordinator.data.get(f"ver_{self._key}", "")
        return raw.split(" ")[0] if raw else None

    @property
    def latest_version(self):
        # In a real scenario, you'd pull the 'new' version string. 
        # For now, we flag 'New' if update_available is True
        up_avail = "(Up: True)" in self.coordinator.data.get(f"ver_{self._key}", "")
        return "New Version Available" if up_avail else self.installed_version

    @property
    def release_url(self):
        return "https://github.com/pi-hole/pi-hole/releases"
