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
                        res_text = await resp.text()
                        if resp.status != 200:
                            raise UpdateFailed(f"Auth failed ({resp.status}): {res_text}")
                        
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        
                        # Save SID for persistence
                        new_data = dict(self.entry.data)
                        new_data["sid"] = self.sid
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                headers = {"X-FTL-SID": self.sid, "Accept": "application/json"}
                
                # 2. Fetch data from verified v6 endpoints
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/stats/summary", headers=headers) as r_sum:
                    
                    # Log raw text if not JSON to catch the 'str' error
                    if r_sys.content_type != "application/json":
                        err_txt = await r_sys.text()
                        _LOGGER.error("System API returned text, not JSON: %s", err_txt)
                        self.sid = None # Reset session
                        raise UpdateFailed(f"Non-JSON response: {err_txt}")

                    sys_data = await r_sys.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    # --- DATA EXTRACTION ---
                    uptime_sec = sys_data.get("uptime", 0)
                    
                    # Resources
                    cpu_usage = sys_data.get("cpu", {}).get("relative", 0) * 100
                    mem_usage = sys_data.get("memory", {}).get("relative", 0) * 100
                    load_list = sys_data.get("load", [0, 0, 0])

                    # Sensors
                    temp_list = sens_data.get("sensors", [])
                    cpu_temp = 0
                    if temp_list and isinstance(temp_list, list):
                        cpu_temp = temp_list[0].get("value", 0)

                    # Summary & QPM Logic
                    # Total queries / uptime in minutes
                    queries_today = sum_data.get("queries", {}).get("total", 0)
                    uptime_min = max(uptime_sec / 60, 1) # Prevent div by zero
                    qpm = queries_today / uptime_min

                    return {
                        "temperature": round(float(cpu_temp), 1),
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": round(load_list[0], 2) if load_list else 0,
                        "memory_usage": round(mem_usage, 1),
                        "cpu_usage": round(cpu_usage, 1),
                        "queries_pm": round(qpm, 2)
                    }

        except Exception as e:
            _LOGGER.error("Pi-hole Update Error: %s", e)
            raise UpdateFailed(f"Connection Error: {e}")
