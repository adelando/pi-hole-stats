from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PiHoleUpdateEntity(coordinator, entry, "core", "Core"),
        PiHoleUpdateEntity(coordinator, entry, "ftl", "FTL"),
        PiHoleUpdateEntity(coordinator, entry, "web", "Web Interface"),
    ])

class PiHoleUpdateEntity(CoordinatorEntity, UpdateEntity):
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES

    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Pi-hole {name} Update"
        self._attr_unique_id = f"{entry.entry_id}_update_{key}"
        self._attr_device_info = coordinator.device_info
        self._attr_release_url = "https://github.com/pi-hole/pi-hole/releases"

    @property
    def installed_version(self):
        return self.coordinator.data.get(f"ver_{self._key}")

    @property
    def latest_version(self):
        current = self.installed_version
        has_update = self.coordinator.data.get(f"up_{self._key}")
        return f"{current}-update" if has_update else current
