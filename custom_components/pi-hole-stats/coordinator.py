import logging
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.entry = entry
        self.host = entry.data["host"].strip().rstrip("/")
        self.port = entry.data["port"]
        self.pw = entry.data["api_key"]
        # Try to load existing SID from the config entry storage
        self.sid = entry.data.get("sid")
        
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
                # 1. Login ONLY if we don't have a saved SID
                if not self.sid:
                    _LOGGER.debug("Authenticating with Pi-hole v6 (New Session)")
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        
                        if not self.sid:
                            raise UpdateFailed("Auth failed: App Password rejected")
                        
                        # SAVE the SID into the Config Entry so it survives reloads
                        new_data = dict(self.entry.data)
                        new_data["sid"] = self.sid
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                # 2. Fetch Data
                headers = {"X-FTL-SID": self.sid}
                
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/info/summary", headers=headers) as r_sum:
                    
                    # Handle Session Expiry (401)
                    if r_sys.status == 401:
                        _LOGGER.warning("Pi-hole SID expired. Clearing for next run.")
                        self.sid = None
                        # Remove SID from storage
                        new_data = dict(self.entry.data)
                        new_data.pop("sid", None)
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
                        raise UpdateFailed("Session expired")
                    
                    if r_sys.status != 200:
                        raise UpdateFailed(f"HTTP Error {r_sys.status}")

                    sys_data = await r_sys.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    uptime_sec = sys_data.get("uptime", 0)
                    queries_today = sum_data.get("queries", {}).get("total", 0)
                    temp_list = sens_data.get("sensors", [])
                    cpu_temp = next((s.get("value") for s in temp_list if "temperature" in s.get("type", "").lower()), 0) if temp_list else 0

                    return {
                        "temperature": round(float(cpu_temp), 1),
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": sys_data.get("load", [0, 0, 0])[0],
                        "memory_usage": sys_data.get("memory", {}).get("relative", 0),
                        "cpu_usage": sys_data.get("cpu", {}).get("relative", 0),
                        "queries_pm": round(queries_today / (max(uptime_sec, 60) / 60), 2)
                    }

        except Exception as e:
            _LOGGER.error("Update failed: %s", e)
            raise UpdateFailed(f"Connection Error: {e}")
