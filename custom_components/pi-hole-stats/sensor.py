from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["pi_hole_stats"][entry.entry_id]
    
    # Define all sensors in one go
    sensors = [
        PiHoleSensor(coordinator, "cpu_temp", "CPU Temperature", "°C", "mdi:thermometer"),
        PiHoleSensor(coordinator, "cpu_usage", "CPU Usage", "%", "mdi:cpu-64-bit"),
        PiHoleSensor(coordinator, "mem_usage", "Memory Usage", "%", "mdi:memory"),
        PiHoleSensor(coordinator, "load", "System Load", None, "mdi:speedometer"),
        PiHoleSensor(coordinator, "uptime_days", "Uptime", "days", "mdi:timer-outline"),
        PiHoleSensor(coordinator, "queries_pm", "Queries/Min", "qpm", "mdi:chart-line"),
        PiHoleSensor(coordinator, "gateway", "Network Gateway", None, "mdi:router-wireless"),
        PiHoleSensor(coordinator, "blocking", "DNS Blocking", None, "mdi:shield-check"),
        PiHoleSensor(coordinator, "active_clients", "Active Clients", "clients", "mdi:account-group"),
        PiHoleSensor(coordinator, "msg_count", "Diagnostic Messages", "msgs", "mdi:alert-circle-outline"),
        PiHoleSensor(coordinator, "ver_core", "Core Version", None, "mdi:github"),
        PiHoleSensor(coordinator, "ver_ftl", "FTL Version", None, "mdi:chip"),
        PiHoleSensor(coordinator, "ver_web", "Web Version", None, "mdi:web"),
        PiHoleSensor(coordinator, "host_model", "Host Model", None, "mdi:raspberry-pi"),
        PiHoleSensor(coordinator, "blocked_1", "Recent Block 1", None, "mdi:close-octagon"),
        PiHoleSensor(coordinator, "blocked_2", "Recent Block 2", None, "mdi:close-octagon"),
        PiHoleSensor(coordinator, "blocked_3", "Recent Block 3", None, "mdi:close-octagon"),
    ]
    async_add_entities(sensors)

class PiHoleSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Pi-hole {name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_unique_id = f"pihole_{key}_{coordinator.entry.entry_id}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self):
        # Specific logic for attribute-heavy sensors
        if self._key == "cpu_temp":
            return {"hot_limit": self.coordinator.data.get("hot_limit")}
        if self._key == "host_model":
            return self.coordinator.data.get("host_attr")
        if self._key == "msg_count":
            return self.coordinator.data.get("msg_list")
        return None
