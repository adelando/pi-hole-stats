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
                # 1. Login/Refresh Session
                if not self.sid:
                    auth_url = f"http://{self.host}:{self.port}/api/auth"
                    async with session.post(auth_url, json={"password": self.pw}, timeout=10) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        if not self.sid:
                            _LOGGER.error("Authentication failed: No SID returned from Pi-hole")
                            raise UpdateFailed("Invalid App Password")

                # 2. Fetch Data
                headers = {"X-FTL-SID": self.sid}
                
                # Fetch Summary and Host info
                async with session.get(f"http://{self.host}:{self.port}/api/info/summary", headers=headers) as r1, \
                           session.get(f"http://{self.host}:{self.port}/api/info/host", headers=headers) as r2:
                    
                    if r1.status == 401:
                        self.sid = None # Force re-auth next time
                        raise UpdateFailed("Session expired")

                    s_data = await r1.json()
                    h_data = await r2.json()

                    # DEBUG: This will show in your HA Logs (Settings > System > Logs)
                    _LOGGER.debug("Pi-hole Data Received: %s", s_data)

                    # v6 precise paths
                    uptime_sec = h_data.get("uptime", 0)
                    # Note: queries is a nested dict in v6: {"queries": {"total": 123}}
                    queries_today = s_data.get("queries", {}).get("total", 0)
                    
                    # Hardware stats
                    temp = h_data.get("temperature", 0)
                    load = h_data.get("load", [0, 0, 0])[0]
                    ram = h_data.get("memory", {}).get("relative", 0)
                    cpu = h_data.get("cpu", {}).get("relative", 0)

                    return {
                        "temperature": round(temp, 1) if temp else 0,
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": round(load, 2),
                        "memory_usage": round(ram, 1),
                        "cpu_usage": round(cpu, 1),
                        "queries_pm": round(queries_today / (max(uptime_sec, 60) / 60), 2)
                    }

            except Exception as e:
                self.sid = None
                _LOGGER.error("Update error: %s", e)
                raise UpdateFailed(f"Connection Error: {e}")
