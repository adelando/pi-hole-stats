from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        PiHoleSensor(coordinator, "Queries per Minute", "queries_pm", "queries"),
        PiHoleSensor(coordinator, "CPU Load", "cpu_load", "%"),
        PiHoleSensor(coordinator, "Memory Usage", "memory_usage", "%"),
        PiHoleSensor(coordinator, "Temperature", "temperature", "°C"),
    ]
    async_add_entities(sensors)

class PiHoleSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, name, data_key, unit):
        super().__init__(coordinator)
        self._attr_name = f"Pi-Hole {name}"
        self._data_key = data_key
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        # Note: Pi-Hole API returns data in different keys. 
        # You'll map coordinator.data['key'] here based on actual JSON response.
        return self.coordinator.data.get(self._data_key)
