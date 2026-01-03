import logging
from datetime import timedelta
import aiohttp
import async_timeout

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host, api_key):
        self.host = host
        self.api_key = api_key
        super().__init__(
            hass,
            _LOGGER,
            name="Pi-Hole Statistics",
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        # We use summaryRaw to get the unformatted numbers for calculations
        url = f"http://{self.host}/admin/api.php?summaryRaw&auth={self.api_key}"
        
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        data = await response.json()
                        
                        if not data:
                            raise UpdateFailed("No data received from Pi-hole")

                        # 1. Calculate Queries per Minute (QPM)
                        # ftevent_uptime is in seconds
                        uptime_sec = data.get("ftlevent_uptime", 0)
                        total_queries = data.get("dns_queries_today", 0)
                        
                        if uptime_sec > 60:
                            data["queries_pm"] = round(total_queries / (uptime_sec / 60), 2)
                        else:
                            data["queries_pm"] = 0

                        # 2. Uptime in Days (Optional: format in sensor.py instead)
                        data["uptime_days"] = round(uptime_sec / 86400, 2)

                        # 3. Temperature 
                        # Pi-hole API returns 'temperature' in Celsius. 
                        # Note: This may be missing if not on supported hardware.
                        return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
