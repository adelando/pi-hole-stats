from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # List of sensors to create
    sensor_types = [
        ("Temperature", "temperature", "°C", SensorDeviceClass.TEMPERATURE),
        ("Uptime", "ftlevent_uptime", "s", SensorDeviceClass.DURATION),
        ("Load Percentage", "load", "%", None),
        ("RAM Usage", "memory_usage", "%", None),
        ("CPU Usage", "cpu_usage", "%", None),
        ("Queries per Minute", "queries_pm", "qpm", None),
    ]
    
    async_add_entities(
        [PiHoleStatSensor(coordinator, name, key, unit, dev_class) 
         for name, key, unit, dev_class in sensor_types]
    )

class PiHoleStatSensor(SensorEntity):
    def __init__(self, coordinator, name, data_key, unit, device_class):
        self.coordinator = coordinator
        self._data_key = data_key
        
        # This force-sets the name which HA uses to generate the entity_id
        self._attr_name = f"Pi Hole Stat {name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_unique_id = f"pi_hole_stat_{data_key}_{coordinator.host}"
        
        # Set the entity_id format explicitly
        self.entity_id = f"sensor.pi_hole_stat_{data_key}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key)

    @property
    def available(self):
        return self.coordinator.last_update_success
