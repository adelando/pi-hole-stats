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
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        # Safety check: if response isn't JSON, don't crash
                        if resp.content_type != "application/json":
                            text_err = await resp.text()
                            raise UpdateFailed(f"Auth failed: Expected JSON, got: {text_err}")
                        
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        
                        if not self.sid:
                            raise UpdateFailed("Auth failed: Invalid App Password")
                        
                        # Save SID to Config Entry
                        new_data = dict(self.entry.data)
                        new_data["sid"] = self.sid
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                # 2. Fetch Data
                headers = {"X-FTL-SID": self.sid}
                
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/info/summary", headers=headers) as r_sum:
                    
                    if r_sys.status == 401:
                        self.sid = None
                        new_data = dict(self.entry.data)
                        new_data.pop("sid", None)
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
                        raise UpdateFailed("Session expired")
                    
                    # Ensure all responses are valid JSON
                    if any(r.content_type != "application/json" for r in [r_sys, r_sens, r_sum]):
                        raise UpdateFailed("Pi-hole returned non-JSON data (Check security settings)")

                    sys_data = await r_sys.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    # --- SAFETY CHECKS ---
                    # Ensure the response is a dictionary before calling .get()
                    if not isinstance(sys_data, dict) or not isinstance(sum_data, dict):
                        raise UpdateFailed("Received malformed JSON from Pi-hole")

                    uptime_sec = sys_data.get("uptime", 0)
                    queries_today = sum_data.get("queries", {}).get("total", 0)
                    
                    temp_list = sens_data.get("sensors", []) if isinstance(sens_data, dict) else []
                    cpu_temp = 0
                    if temp_list and isinstance(temp_list, list):
                        cpu_temp = temp_list[0].get("value", 0)

                    return {
                        "temperature": round(float(cpu_temp), 1),
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": sys_data.get("load", [0, 0, 0])[0],
                        "memory_usage": sys_data.get("memory", {}).get("relative", 0),
                        "cpu_usage": sys_data.get("cpu", {}).get("relative", 0),
                        "queries_pm": round(queries_today / (max(uptime_sec, 60) / 60), 2)
                    }

        except Exception as e:
            _LOGGER.error("Pi-hole update failed: %s", e)
            raise UpdateFailed(f"Connection Error: {e}")
