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
                # 1. Login Logic - Ensure we get JSON back
                if not self.sid:
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        if resp.status != 200:
                            raise UpdateFailed(f"Auth failed with status {resp.status}")
                        
                        auth_data = await resp.json()
                        if not isinstance(auth_data, dict):
                            raise UpdateFailed("Auth response was not JSON")
                            
                        self.sid = auth_data.get("session", {}).get("sid")
                        
                        # Save SID to the entry
                        new_data = dict(self.entry.data)
                        new_data["sid"] = self.sid
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                # 2. Fetch Data with defensive checks
                headers = {
                    "X-FTL-SID": self.sid,
                    "Accept": "application/json" # Explicitly ask for JSON
                }
                
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/stats/summary", headers=headers) as r_sum:
                    
                    # If any request is unauthorized, clear SID and bail
                    if any(r.status == 401 for r in [r_sys, r_sens, r_sum]):
                        self.sid = None
                        raise UpdateFailed("Session expired - will re-auth next cycle")

                    # Check for 200 OK
                    if r_sys.status != 200:
                        raise UpdateFailed(f"System API error: {r_sys.status}")

                    sys_data = await r_sys.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    # DEFENSIVE CHECK: Ensure we actually have dictionaries
                    if not all(isinstance(d, dict) for d in [sys_data, sum_data]):
                        _LOGGER.error("Pi-hole returned non-JSON data. Sys: %s, Sum: %s", sys_data, sum_data)
                        raise UpdateFailed("API returned text instead of JSON data")

                    # --- DATA MAPPING ---
                    uptime_sec = sys_data.get("uptime", 0)
                    cpu_usage = sys_data.get("cpu", {}).get("relative", 0) * 100
                    mem_usage = sys_data.get("memory", {}).get("relative", 0) * 100
                    load_list = sys_data.get("load", [0, 0, 0])

                    # Sensor extraction
                    temp_list = sens_data.get("sensors", []) if isinstance(sens_data, dict) else []
                    cpu_temp = 0
                    if isinstance(temp_list, list) and temp_list:
                        cpu_temp = temp_list[0].get("value", 0)

                    # Summary extraction
                    queries_today = sum_data.get("queries", {}).get("total", 0)

                    return {
                        "temperature": round(float(cpu_temp), 1),
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": round(load_list[0], 2) if load_list else 0,
                        "memory_usage": round(mem_usage, 1),
                        "cpu_usage": round(cpu_usage, 1),
                        "queries_pm": round(queries_today / (max(uptime_sec, 60) / 60), 2)
                    }

        except Exception as e:
            # If it's a structural error, clear SID to force a clean start
            if "attribute 'get'" in str(e):
                self.sid = None
            _LOGGER.error("Pi-hole Update Error: %s", e)
            raise UpdateFailed(f"Connection Error: {e}")
