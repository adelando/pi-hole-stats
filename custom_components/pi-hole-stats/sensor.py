"""Sensor platform for Pi-hole v6 Stats."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    all_entries = hass.config_entries.async_entries(DOMAIN)
    all_entries.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else 0)
    num_prefix = "" if all_entries.index(entry) == 0 else f"{all_entries.index(entry) + 1}_"

    # (Key, Name, Unit, Icon)
    sensor_defs = [
        ("cpu_temp", "CPU Temperature", "°C", "mdi:thermometer"),
        ("cpu_usage", "CPU Usage", "%", "mdi:cpu-64-bit"),
        ("mem_usage", "Memory Usage", "%", "mdi:memory"),
        ("load", "System Load", "%", "mdi:speedometer"),
        ("uptime_days", "Uptime", "days", "mdi:timer-outline"),
        ("dns_queries_today", "Total Queries", "queries", "mdi:dns"),
        ("ads_blocked_today", "Ads Blocked", "ads", "mdi:hand-octagon"),
        ("domains_blocked", "Total Domains Blocked", "domains", "mdi:list-status"),
        ("gateway", "Network Gateway", None, "mdi:router-wireless"),
        ("blocking", "DNS Blocking", None, "mdi:shield-check"),
        ("active_clients", "Active Clients", "clients", "mdi:account-group"),
        ("msg_count", "Diagnostics", "msgs", "mdi:alert-circle-outline"),
        ("host_model", "Host Model", None, "mdi:raspberry-pi"),
        ("recent_blocked", "Recent Blocks", None, "mdi:close-octagon"),
    ]

    async_add_entities([PiHoleNumberedSensor(coordinator, entry, num_prefix, *s) for s in sensor_defs])

class PiHoleNumberedSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, num, key, name, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self.entity_id = f"sensor.pi_hole_stat_{num}{key}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self):
        val = self.coordinator.data.get(self._key)
        if self._key == "recent_blocked":
            return val[0] if isinstance(val, list) and val else "None"
        return val

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if self._key == "recent_blocked":
            return {"blocked_domains": data.get("recent_blocked", [])}
        if self._key == "msg_count":
            return {"alerts": data.get("msg_list", {})}
        if self._key == "blocking":
            return {"timer_seconds": data.get("blocking_timer")}
        return None
