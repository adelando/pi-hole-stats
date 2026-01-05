class PiHoleUpdateEntity(CoordinatorEntity, UpdateEntity):
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES

    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Pi-hole {name} Update"
        self._attr_unique_id = f"{entry.entry_id}_update_{key}"
        self._attr_device_info = coordinator.device_info
        self._attr_release_url = f"https://github.com/pi-hole/{'web' if key=='web' else 'pi-hole'}/releases"

    @property
    def installed_version(self):
        return self.coordinator.data.get(f"ver_{self._key}")

    @property
    def latest_version(self):
        return self.coordinator.data.get(f"rem_{self._key}")
