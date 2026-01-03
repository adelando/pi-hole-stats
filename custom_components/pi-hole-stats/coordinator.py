import logging
import aiohttp
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry_data):
        """Initialize using the data dictionary from the config entry."""
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
                # 1. Login if we don't have a Session ID (SID)
                if not self.sid:
                    auth_url = f"http://{self.host}:{self.port}/api/auth"
                    async with session.post(auth_url, json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        if not self.sid:
                            _LOGGER.error("Pi-hole v6 Auth failed: No SID returned")
                            raise UpdateFailed("Invalid App Password")

                # 2. Fetch both summary and host data
                headers = {"X-FTL-SID": self.sid}
                stats_url = f"http://{self.host}:{self.port}/api/info/summary"
                sys_url = f"http://{self.host}:{self.port}/api/info/host"
                
                async with session.get(stats_url, headers=headers) as r1, \
                           session.get(sys_url, headers=headers) as r2:
                    
                    # If 401, our SID expired; clear it so we re-auth next time
                    if r1.status == 401 or r2.status == 401:
                        self.sid = None
                        raise UpdateFailed("Session expired, re-authenticating...")
                        
                    s_data = await r1.json()
                    h_data = await r2.json()
                    
                    uptime_sec = h_data.get("uptime", 1)
                    queries_today = s_data.get("queries", {}).get("total", 0)
                    
                    return {
                        "temperature": h_data.get("temperature"),
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": h_data.get("load", [0, 0, 0])[0],
                        "memory_usage": h_data.get("memory", {}).get("relative", 0),
                        "cpu_usage": h_data.get("cpu", {}).get("relative", 0),
                        "queries_pm": round(queries_today / (max(uptime_sec, 60) / 60), 2)
                    }
            except Exception as e:
                self.sid = None # Reset on any connection error
                raise UpdateFailed(f"Pi-Hole v6 API Error: {e}")
