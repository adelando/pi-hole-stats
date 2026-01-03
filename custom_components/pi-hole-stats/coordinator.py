import logging
from datetime import timedelta
import aiohttp
import async_timeout

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Pi-hole data."""

    def __init__(self, hass: HomeAssistant, host: str, api_key: str):
        """Initialize."""
        self.host = host
        self.api_key = api_key
        
        # Poll every 30 seconds
        super().__init__(
            hass,
            _LOGGER,
            name="Pi-Hole Statistics",
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Fetch data from Pi-hole API."""
        # Note: 'raw' or 'summary' provides the core stats. 
        # Some hardware stats require auth even for basic viewing.
        url = f"http://{self.host}/admin/api.php?summaryRaw&auth={self.api_key}"
        
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    response = await session.get(url)
                    data = await response.json()
                    
                    if not data:
                        raise UpdateFailed("Invalid response from Pi-hole")

                    # Pi-hole API provides 'queries_today' and 'ftlevent_uptime'.
                    # We can calculate Queries Per Minute (QPM) here.
                    uptime_minutes = data.get("ftlevent_uptime", 0) / 60
                    queries_today = data.get("dns_queries_today", 0)
                    
                    if uptime_minutes > 0:
                        data["queries_pm"] = round(queries_today / uptime_minutes, 2)
                    else:
                        data["queries_pm"] = 0

                    # Map keys for consistency if they exist in your Pi-hole version
                    # Note: Temp/CPU may require the Pi-hole 'sys' endpoint 
                    # or specific OS permissions.
                    return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with Pi-hole API: {err}")
