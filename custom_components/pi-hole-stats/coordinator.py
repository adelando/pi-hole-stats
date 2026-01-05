import logging
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.entry = entry
        self.host = entry.data["host"].strip().rstrip("/")
        self.port = entry.data["port"]
        self.pw = entry.data["api_key"]
        self.sid = entry.data.get("sid")
        
        super().__init__(
            hass, 
            _LOGGER, 
            name="Pi-Hole Stats", 
            update_interval=timedelta(seconds=60)
        )

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)
        base_url = f"http://{self.host}:{self.port}/api"

        try:
            async with async_timeout.timeout(15):
                # 1. Login Logic
                if not self.sid:
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        new_data = dict(self.entry.data)
                        new_data["sid"] = self.sid
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                headers = {"X-FTL-SID": self.sid, "Accept": "application/json"}
                
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/stats/summary", headers=headers) as r_sum:
                    
                    # Log raw text if the response isn't JSON to catch that 'str' error
                    if r_sys.content_type != "application/json":
                        raw_text = await r_sys.text()
                        _LOGGER.error("Pi-hole returned text instead of JSON: %s", raw_text)
                        self.sid = None # Reset session on error
                        raise UpdateFailed(f"Invalid API response: {raw_text}")

                    sys_json = await r_sys.json()
                    sens_json = await r_sens.json()
                    sum_json = await r_sum.json()

                    # --- DATA MAPPING (BASED ON YOUR SCHEMA) ---
                    # Accessing nested 'system' object
                    sys_obj = sys_json.get("system", {})
                    
                    uptime_sec = sys_obj.get("uptime", 0)
                    
                    # Memory Mapping
                    ram_data = sys_obj.get("memory", {}).get("ram", {})
                    mem_usage = ram_data.get("%used", 0)
                    
                    # CPU Mapping
                    cpu_data = sys_obj.get("cpu", {})
                    cpu_usage = cpu_data.get("%cpu", 0)
                    load_list = cpu_data.get("load", {}).get("raw", [0, 0, 0])

                    # Sensors Mapping
                    temp_list = sens_json.get("sensors", [])
                    cpu_temp = 0
                    if temp_list and isinstance(temp_list, list):
                        cpu_temp = temp_list[0].get("value", 0)

                    # Summary & QPM Logic
                    queries_today = sum_json.get("queries", {}).get("total", 0)
                    
                    # Calculate QPM: total queries / (uptime in minutes)
                    uptime_min = uptime_sec / 60
                    qpm = queries_today / uptime_min if uptime_min > 1 else 0

                    return {
                        "temperature": round(float(cpu_temp), 1),
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": round(load_list[0], 2) if load_list else 0,
                        "memory_usage": round(mem_usage, 1),
                        "cpu_usage": round(cpu_usage, 1),
                        "queries_pm": round(qpm, 2)
                    }

        except Exception as e:
            _LOGGER.error("Coordinator update failed: %s", e)
            raise UpdateFailed(f"Error communicating with API: {e}")
