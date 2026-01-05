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
                # 1. Check/Refresh Session
                if not self.sid:
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        # Persist SID to config entry
                        new_data = dict(self.entry.data)
                        new_data["sid"] = self.sid
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                headers = {"X-FTL-SID": self.sid}
                
                # 2. Concurrent requests to your 3 verified endpoints
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/stats/summary", headers=headers) as r_sum:
                    
                    if r_sys.status == 401:
                        self.sid = None
                        raise UpdateFailed("Session expired - re-authenticating next cycle")

                    sys_data = await r_sys.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    # --- v6 DATA MAPPING ---
                    
                    # From /info/system
                    uptime_sec = sys_data.get("uptime", 0)
                    # Pi-hole v6 returns relative usage (e.g., 0.1 = 10%)
                    cpu_usage = sys_data.get("cpu", {}).get("relative", 0) * 100
                    mem_usage = sys_data.get("memory", {}).get("relative", 0) * 100
                    load_list = sys_data.get("load", [0, 0, 0])

                    # From /info/sensors
                    # Usually returns a list of sensors; we search for temperature
                    temp_list = sens_data.get("sensors", [])
                    cpu_temp = 0
                    for s in temp_list:
                        if "temp" in s.get("type", "").lower() or "thermal" in s.get("name", "").lower():
                            cpu_temp = s.get("value", 0)
                            break
                    # Fallback to first sensor if specific name not found
                    if cpu_temp == 0 and temp_list:
                        cpu_temp = temp_list[0].get("value", 0)

                    # From /stats/summary
                    # v6 Summary nests queries inside a 'queries' object
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
            self.sid = None
            _LOGGER.error("Pi-hole v6 data fetch failed: %s", e)
            raise UpdateFailed(f"API Error: {e}")
