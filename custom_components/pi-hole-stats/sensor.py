from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        PiHoleStatSensor(coordinator, "Queries per Minute", "queries_pm", "req/min", None),
        PiHoleStatSensor(coordinator, "Temperature", "temperature", "°C", SensorDeviceClass.TEMPERATURE),
        PiHoleStatSensor(coordinator, "Uptime", "uptime_days", "days", None),
        PiHoleStatSensor(coordinator, "Ads Blocked Today", "ads_blocked_today", "ads", None),
    ]
    async_add_entities(entities)

class PiHoleStatSensor(SensorEntity):
    def __init__(self, coordinator, name, data_key, unit, device_class):
        self.coordinator = coordinator
        self._attr_name = f"Pi-Hole {name}"
        self._data_key = data_key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT
        # Link to the coordinator
        self._attr_unique_id = f"pihole_{data_key}_{coordinator.host}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key)

    @property
    def available(self):
        return self.coordinator.last_update_success
