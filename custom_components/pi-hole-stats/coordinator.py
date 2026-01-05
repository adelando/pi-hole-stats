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
            update_interval=timedelta(seconds=10) # 10s for fast updates
        )

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)
        base_url = f"http://{self.host}:{self.port}/api"

        try:
            async with async_timeout.timeout(5):
                # 1. Handle Authentication
                if not self.sid:
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        new_data = dict(self.entry.data)
                        new_data["sid"] = self.sid
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                headers = {"X-FTL-SID": self.sid, "Accept": "application/json"}
                
                # 2. Fetch from your verified endpoints
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/stats/summary", headers=headers) as r_sum:
                    
                    sys_json = await r_sys.json()
                    sens_json = await r_sens.json()
                    sum_json = await r_sum.json()

                    # --- v6 DATA MAPPING ---
                    sys_obj = sys_json.get("system", {})
                    
                    # Hardware & Uptime
                    uptime_sec = sys_obj.get("uptime", 1)
                    cpu_usage = sys_obj.get("cpu", {}).get("%cpu", 0)
                    mem_usage = sys_obj.get("memory", {}).get("ram", {}).get("%used", 0)
                    load_list = sys_obj.get("cpu", {}).get("load", {}).get("raw", [0, 0, 0])

                    # Temperature - Mapping specifically to your schema
                    # sens_json["sensors"]["cpu_temp"]
                    sensors_obj = sens_json.get("sensors", {})
                    cpu_temp = sensors_obj.get("cpu_temp", 0)

                    # Queries Per Minute - Reactive Logic
                    # Using queries from today / (uptime in minutes) 
                    # Note: For 'Live' QPM, Pi-hole usually uses a 10-minute window, 
                    # but this cumulative average is the standard API summary approach.
                    queries_today = sum_json.get("queries", {}).get("total", 0)
                    uptime_min = uptime_sec / 60
                    qpm = queries_today / uptime_min if uptime_min > 0 else 0

                    return {
                        "temperature": round(float(cpu_temp), 1),
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": round(load_list[0], 2),
                        "memory_usage": round(mem_usage, 1),
                        "cpu_usage": round(cpu_usage, 1),
                        "queries_pm": round(qpm, 2)
                    }

        except Exception as e:
            self.sid = None
            _LOGGER.error("Pi-hole update failed: %s", e)
            raise UpdateFailed(f"API Error: {e}")
