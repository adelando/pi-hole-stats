from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Logic to handle multiple Pi-hole instances numbering
    all_entries = hass.config_entries.async_entries(DOMAIN)
    all_entries.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else 0)
    
    try:
        index = all_entries.index(entry)
        num_prefix = "" if index == 0 else f"{index + 1}_"
    except ValueError:
        num_prefix = ""

    # Define all sensors with their respective keys, names, units, and icons
    sensor_defs = [
        ("cpu_temp", "CPU Temperature", "°C", "mdi:thermometer"),
        ("cpu_usage", "CPU Usage", "%", "mdi:cpu-64-bit"),
        ("mem_usage", "Memory Usage", "%", "mdi:memory"),
        ("load", "System Load", None, "mdi:speedometer"),
        ("uptime_days", "Uptime", "days", "mdi:timer-outline"),
        ("queries_pm", "QPM", "qpm", "mdi:chart-line"),
        ("gateway", "Network Gateway", None, "mdi:router-wireless"),
        ("blocking", "DNS Blocking", None, "mdi:shield-check"),
        ("active_clients", "Active Clients", "clients", "mdi:account-group"),
        ("msg_count", "Diagnostics", "msgs", "mdi:alert-circle-outline"),
        ("host_model", "Host Model", None, "mdi:raspberry-pi"),
        ("blocked_1", "Recent Block 1", None, "mdi:close-octagon"),
        ("blocked_2", "Recent Block 2", None, "mdi:close-octagon"),
        ("blocked_3", "Recent Block 3", None, "mdi:close-octagon"),
    ]

    async_add_entities([
        PiHoleNumberedSensor(coordinator, entry, num_prefix, *s_def) 
        for s_def in sensor_defs
    ])

class PiHoleNumberedSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pi-hole sensor."""

    def __init__(self, coordinator, entry, num, key, name, unit, icon):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        # Entity ID follows your specific sensor.pi_hole_stat_<device number>_key format
        self.entity_id = f"sensor.pi_hole_stat_{num}{key}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = self.coordinator.data
        if self._key == "cpu_temp":
            return {"hot_limit": data.get("hot_limit")}
        if self._key == "host_model":
            return data.get("host_attr")
        if self._key == "msg_count":
            # This ensures the diagnostic messages are visible in the sensor attributes
            return {"alerts": data.get("msg_list")}
        return None
