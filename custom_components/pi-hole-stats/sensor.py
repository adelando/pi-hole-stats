# Inside sensor.py -> sensor_defs
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
        # New Consolidated Sensor
        ("recent_blocked", "Recent Blocks", None, "mdi:close-octagon"),
    ]

# Inside PiHoleNumberedSensor -> native_value
    @property
    def native_value(self):
        val = self.coordinator.data.get(self._key)
        if self._key == "recent_blocked":
            # State shows the most recent single domain blocked
            return val[0] if val else "None"
        return val

# Inside PiHoleNumberedSensor -> extra_state_attributes
    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if self._key == "recent_blocked":
            # List all domains in the attributes
            return {"blocked_domains": data.get("recent_blocked", [])}
        if self._key == "msg_count":
            return {"alerts": data.get("msg_list", {})}
        if self._key == "host_model":
            return data.get("host_attr", {})
        return None
