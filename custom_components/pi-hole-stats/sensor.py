from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensor_types = [
        ("Temperature", "temperature", "°C", SensorDeviceClass.TEMPERATURE),
        ("Uptime", "uptime_days", "days", None),
        ("Load Percentage", "load", "%", None),
        ("RAM Usage", "memory_usage", "%", None),
        ("CPU Usage", "cpu_usage", "%", None),
        ("Queries per Minute", "queries_pm", "qpm", None),
    ]
    
    async_add_entities(
        [PiHoleStatSensor(coordinator, name, key, unit, dev_class) 
         for name, key, unit, dev_class in sensor_types]
    )

class PiHoleStatSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pi-Hole sensor."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, name, data_key, unit, device_class):
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = f"pi_hole_stat_{data_key}_{coordinator.host}"
        self.entity_id = f"sensor.pi_hole_stat_{data_key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._data_key)

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "last_updated": dt_util.now().strftime("%Y-%m-%d %H:%M:%S"),
            "host": self.coordinator.host,
            "status": "online" if self.coordinator.last_update_success else "offline"
        }
