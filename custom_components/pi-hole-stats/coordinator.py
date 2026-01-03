import logging
import aiohttp
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry_data):
        self.host = entry_data["host"]
        self.port = entry_data["port"]
        self.pw = entry_data["api_key"]
        self.sid = None
        
        super().__init__(
            hass, 
            _LOGGER, 
            name="Pi-Hole Stats", 
            update_interval=timedelta(seconds=30)
        )

    async def _async_update_data(self):
        async with aiohttp.ClientSession() as session:
            try:
                # 1. Login/Refresh SID
                if not self.sid:
                    auth_url = f"http://{self.host}:{self.port}/api/auth"
                    async with session.post(auth_url, json={"password": self.pw}, timeout=10) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        if not self.sid:
                            raise UpdateFailed("Pi-hole v6 Auth failed")

                # 2. Fetch from the specific endpoints you found
                headers = {"X-FTL-SID": self.sid}
                
                # Endpoint 1: System Info (Uptime, Load, Memory)
                # Endpoint 2: Sensors (Temperature)
                # Endpoint 3: Summary (Queries per minute)
                async with session.get(f"http://{self.host}:{self.port}/api/info/system", headers=headers) as r_sys, \
                           session.get(f"http://{self.host}:{self.port}/api/info/sensors", headers=headers) as r_sens, \
                           session.get(f"http://{self.host}:{self.port}/api/info/summary", headers=headers) as r_sum:
                    
                    if r_sys.status == 401:
                        self.sid = None
                        raise UpdateFailed("Session expired")

                    sys_data = await r_sys.sys_data.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    # Mapping based on /api/docs structures
                    uptime_sec = sys_data.get("uptime", 0)
                    queries_today = sum_data.get("queries", {}).get("total", 0)

                    # Temperature is usually in a list under 'sensors'
                    # We'll try to find the CPU temperature sensor
                    temp_list = sens_data.get("sensors", [])
                    cpu_temp = 0
                    if temp_list:
                        # Grabs the first temperature sensor found
                        cpu_temp = temp_list[0].get("value", 0)

                    return {
                        "temperature": cpu_temp,
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": sys_data.get("load", [0, 0, 0])[0],
                        "memory_usage": sys_data.get("memory", {}).get("relative", 0),
                        "cpu_usage": sys_data.get("cpu", {}).get("relative", 0),
                        "queries_pm": round(queries_today / (max(uptime_sec, 60) / 60), 2)
                    }

            except Exception as e:
                self.sid = None
                _LOGGER.error("Update error: %s", e)
                raise UpdateFailed(f"Connection Error: {e}")
