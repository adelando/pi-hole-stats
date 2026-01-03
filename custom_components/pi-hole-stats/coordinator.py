import logging
from datetime import timedelta
import aiohttp
import async_timeout
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry_data):
        self.host = entry_data["host"]
        self.port = entry_data["port"]
        self.location = entry_data["location"]
        self.api_key = entry_data.get("api_key", "")
        
        super().__init__(
            hass, _LOGGER, name="Pi-Hole Statistics", 
            update_interval=timedelta(seconds=30)
        )

    async def _async_update_data(self):
        path = "admin/api.php" if self.location == "admin" else "api"
        url = f"http://{self.host}:{self.port}/{path}?summaryRaw&auth={self.api_key}"
        
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        data = await response.json()
                        
                        # Calculate QPM manually if not provided
                        uptime = data.get("ftlevent_uptime", 1)
                        queries = data.get("dns_queries_today", 0)
                        data["queries_pm"] = round(queries / (uptime / 60), 2)
                        
                        # Note: If temperature is null, Pi-hole v6 might need 
                        # 'sys' permissions or a specific endpoint.
                        return data
        except Exception as err:
            raise UpdateFailed(f"Error: {err}")
