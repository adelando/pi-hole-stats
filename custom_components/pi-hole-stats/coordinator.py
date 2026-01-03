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
        self.location = entry_data["location"]
        self.pw = entry_data["api_key"]
        super().__init__(hass, _LOGGER, name="Pi-Hole Stats", update_interval=timedelta(seconds=30))

    async def _async_update_data(self):
        async with aiohttp.ClientSession() as session:
            try:
                # 1. Get Session for v6 or use Key for v5
                if self.location == "api":
                    # v6 Logic
                    auth_url = f"http://{self.host}:{self.port}/api/auth"
                    async with session.post(auth_url, json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        sid = auth_data.get("session", {}).get("sid")
                    
                    stats_url = f"http://{self.host}:{self.port}/api/info/summary"
                    sys_url = f"http://{self.host}:{self.port}/api/info/host"
                    headers = {"X-FTL-SID": sid}
                    
                    async with session.get(stats_url, headers=headers) as r1, \
                               session.get(sys_url, headers=headers) as r2:
                        s_data = await r1.json()
                        h_data = await r2.json()
                        
                        return {
                            "temperature": h_data.get("temperature"),
                            "uptime_days": round(h_data.get("uptime", 0) / 86400, 2),
                            "load": h_data.get("load", [0])[0],
                            "memory_usage": h_data.get("memory", {}).get("relative", 0),
                            "cpu_usage": h_data.get("cpu", {}).get("relative", 0),
                            "queries_pm": s_data.get("queries_today", 0) / (h_data.get("uptime", 1) / 60)
                        }
                else:
                    # Fallback for v5
                    url = f"http://{self.host}:{self.port}/admin/api.php?summaryRaw&auth={self.pw}"
                    async with session.get(url) as resp:
                        data = await resp.json()
                        return {
                            "temperature": data.get("temperature", 0),
                            "uptime_days": round(data.get("ftlevent_uptime", 0) / 86400, 2),
                            "load": 0, # v5 PHP API lacks load/cpu by default
                            "memory_usage": 0,
                            "cpu_usage": 0,
                            "queries_pm": 0
                        }
            except Exception as e:
                raise UpdateFailed(f"Error fetching data: {e}")
