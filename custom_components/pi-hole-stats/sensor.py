from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Pi-Hole sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # name, data_key, unit, device_class
    sensor_types = [
        ("Temperature", "temperature", "°C", SensorDeviceClass.TEMPERATURE),
        ("Uptime", "uptime_days", "days", None),
        ("Load Percentage", "load", "%", None),
        ("RAM Usage", "memory_usage", "%", None),
        ("CPU Usage", "cpu_usage", "%", None),
        ("Queries per Minute", "queries_pm", "qpm", None),
    ]
    
    async_add_entities(
        [PiHoleStatSensor(coordinator, name, key, unit, dev_class, entry) 
         for name, key, unit, dev_class in sensor_types]
    )

class PiHoleStatSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pi-Hole Statistics sensor."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, name, data_key, unit, device_class, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Unique ID prevents duplicates
        self._attr_unique_id = f"pi_hole_stat_{data_key}_{entry.entry_id}"
        
        # Sets the entity_id to sensor.pi_hole_stat_<key> as requested
        self.entity_id = f"sensor.pi_hole_stat_{data_key}"

        # Grouping entities into a single Device in the UI
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Pi-hole Statistics",
            "manufacturer": "Pi-hole",
            "model": "FTL v6.0+",
            "configuration_url": f"http://{coordinator.host}:{coordinator.port}",
        }

    @property
    def native_value(self):
        """Return the state of the sensor from the coordinator data."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._data_key)

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes for the sidebar/card."""
        return {
            "last_updated": dt_util.now().strftime("%Y-%m-%d %H:%M:%S"),
            "host": self.coordinator.host,
            "status": "online" if self.coordinator.last_update_success else "offline"
        }
