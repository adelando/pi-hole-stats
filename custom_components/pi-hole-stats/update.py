"""Update platform for Pi-hole v6 Stats."""
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # We create one entity for each component
    entities = [
        PiHoleUpdate(coordinator, entry, "core", "Pi-hole Core Update"),
        PiHoleUpdate(coordinator, entry, "ftl", "Pi-hole FTL Update"),
        PiHoleUpdate(coordinator, entry, "web", "Pi-hole Web Interface Update"),
    ]
    async_add_entities(entities)

class PiHoleUpdate(CoordinatorEntity, UpdateEntity):
    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}_update"
        self._attr_device_info = coordinator.device_info
        
        # Disable the Install button to prevent "Unknown Error"
        self._attr_supported_features = 0 
        
        # Static note for the UI
        self._attr_release_summary = (
            "**Manual Update Required**\n\n"
            "Pi-hole updates cannot be performed directly from Home Assistant.\n"
            "Please SSH into your Pi-hole host and run:\n\n"
            "`sudo pihole -up`"
        )

    @property
    def installed_version(self):
        return self.coordinator.data.get(f"ver_{self._key}")

    @property
    def latest_version(self):
        return self.coordinator.data.get(f"rem_{self._key}")

    @property
    def release_url(self):
        return f"https://github.com/pi-hole/{self._key}/releases"
