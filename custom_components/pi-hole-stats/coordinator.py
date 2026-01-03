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
        
        # Increased to 60s to respect API session limits
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
                # 1. Only authenticate if we don't have an active SID
                if self.sid is None:
                    _LOGGER.debug("No active SID, attempting login")
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        
                        if not self.sid:
                            _LOGGER.error("Pi-hole rejected App Password or Sessions are full")
                            raise UpdateFailed("Auth failed or Session limit exceeded")

                # 2. Fetch Data using the existing SID
                headers = {"X-FTL-SID": self.sid}
                
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/info/summary", headers=headers) as r_sum:
                    
                    # If Pi-hole says 401, our SID is dead. Clear it and fail this round.
                    if r_sys.status == 401:
                        self.sid = None
                        _LOGGER.warning("SID expired/rejected. Clearing session to re-auth next cycle.")
                        raise UpdateFailed("Session expired")
                    
                    if r_sys.status != 200:
                        raise UpdateFailed(f"Pi-hole API error: {r_sys.status}")

                    sys_data = await r_sys.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    # Precise v6 Path Mapping
                    uptime_sec = sys_data.get("uptime", 0)
                    queries_today = sum_data.get("queries", {}).get("total", 0)

                    temp_list = sens_data.get("sensors", [])
                    cpu_temp = 0
                    if temp_list:
                        # Find the first 'temperature' type sensor if available
                        cpu_temp = next((s.get("value") for s in temp_list if "temperature" in s.get("type", "").lower()), temp_list[0].get("value", 0))

                    return {
                        "temperature": round(float(cpu_temp), 1) if cpu_temp else 0,
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": sys_data.get("load", [0, 0, 0])[0],
                        "memory_usage": sys_data.get("memory", {}).get("relative", 0),
                        "cpu_usage": sys_data.get("cpu", {}).get("relative", 0),
                        "queries_pm": round(queries_today / (max(uptime_sec, 60) / 60), 2)
                    }

        except Exception as e:
            # We DON'T clear SID on generic network timeout, only on 401
            _LOGGER.error("Pi-hole update failed: %s", e)
            raise UpdateFailed(f"Connection Error: {e}")
