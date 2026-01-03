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
        # We use a single session for all requests in this update cycle
        async with aiohttp.ClientSession() as session:
            try:
                # 1. Login/Refresh SID if missing
                if not self.sid:
                    auth_url = f"http://{self.host}:{self.port}/api/auth"
                    # We use 'json=' to ensure aiohttp sets the correct headers automatically
                    async with session.post(auth_url, json={"password": self.pw}, timeout=10) as resp:
                        auth_data = await resp.json()
                        session_info = auth_data.get("session", {})
                        self.sid = session_info.get("sid")
                        
                        if not self.sid:
                            _LOGGER.error("Auth Failed: Response received but SID is null. Check App Password.")
                            raise UpdateFailed("Pi-hole v6 Auth failed - check App Password")

                # 2. Fetch data from the specific v6 endpoints
                headers = {"X-FTL-SID": self.sid}
                base_url = f"http://{self.host}:{self.port}/api"
                
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/info/summary", headers=headers) as r_sum:
                    
                    if r_sys.status == 401:
                        self.sid = None # Session expired, clear for next retry
                        raise UpdateFailed("Session expired, re-authenticating...")

                    sys_data = await r_sys.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    # Data Mapping
                    uptime_sec = sys_data.get("uptime", 0)
                    queries_today = sum_data.get("queries", {}).get("total", 0)

                    # Get first temperature from sensors list
                    temp_list = sens_data.get("sensors", [])
                    cpu_temp = 0
                    if temp_list:
                        cpu_temp = temp_list[0].get("value", 0)

                    return {
                        "temperature": round(cpu_temp, 1) if cpu_temp else 0,
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": sys_data.get("load", [0, 0, 0])[0],
                        "memory_usage": sys_data.get("memory", {}).get("relative", 0),
                        "cpu_usage": sys_data.get("cpu", {}).get("relative", 0),
                        "queries_pm": round(queries_today / (max(uptime_sec, 60) / 60), 2)
                    }

            except Exception as e:
                # If we hit any error, clear the SID so we try a fresh login next time
                self.sid = None
                _LOGGER.error("Pi-hole Update Error: %s", e)
                raise UpdateFailed(f"Connection Error: {e}")
