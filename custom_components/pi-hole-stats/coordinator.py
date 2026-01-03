import logging
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry_data):
        self.host = entry_data["host"].strip().rstrip("/")
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
        # Use the HA shared session instead of creating a new one
        session = async_get_clientsession(self.hass)
        base_url = f"http://{self.host}:{self.port}/api"

        try:
            async with async_timeout.timeout(10):
                # 1. Login if needed
                if not self.sid:
                    _LOGGER.debug("Attempting to login to Pi-hole v6 at %s", base_url)
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        
                        if not self.sid:
                            raise UpdateFailed("Auth failed: App Password rejected by Pi-hole")

                # 2. Fetch Data
                headers = {"X-FTL-SID": self.sid}
                
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/info/summary", headers=headers) as r_sum:
                    
                    if r_sys.status == 401:
                        self.sid = None
                        raise UpdateFailed("Session expired")
                    
                    if r_sys.status != 200:
                        raise UpdateFailed(f"Pi-hole returned status {r_sys.status}")

                    sys_data = await r_sys.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    uptime_sec = sys_data.get("uptime", 0)
                    # Correct path for v6 summary queries
                    queries_today = sum_data.get("queries", {}).get("total", 0)

                    temp_list = sens_data.get("sensors", [])
                    cpu_temp = 0
                    if temp_list:
                        # Ensure we get a numeric value
                        cpu_temp = temp_list[0].get("value", 0)

                    return {
                        "temperature": round(float(cpu_temp), 1) if cpu_temp else 0,
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": sys_data.get("load", [0])[0],
                        "memory_usage": sys_data.get("memory", {}).get("relative", 0),
                        "cpu_usage": sys_data.get("cpu", {}).get("relative", 0),
                        "queries_pm": round(queries_today / (max(uptime_sec, 60) / 60), 2)
                    }

        except Exception as e:
            self.sid = None
            _LOGGER.error("Connection Error 0: %s", e)
            raise UpdateFailed(f"Connection Error: {e}")
