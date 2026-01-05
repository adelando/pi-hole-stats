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
                if not self.sid:
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                        new_data = dict(self.entry.data)
                        new_data["sid"] = self.sid
                        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                headers = {"X-FTL-SID": self.sid, "Accept": "application/json"}
                
                async with session.get(f"{base_url}/info/system", headers=headers) as r_sys, \
                           session.get(f"{base_url}/info/sensors", headers=headers) as r_sens, \
                           session.get(f"{base_url}/stats/summary", headers=headers) as r_sum:
                    
                    sys_data = await r_sys.json()
                    sens_data = await r_sens.json()
                    sum_data = await r_sum.json()

                    # DEBUG LOGGING - Check your HA logs to see these!
                    _LOGGER.debug("PiHole System JSON: %s", sys_data)
                    _LOGGER.debug("PiHole Summary JSON: %s", sum_data)

                    # 1. Map System Stats
                    # If /info/system isn't working, uptime will be 0
                    uptime_sec = sys_data.get("uptime", 0)
                    
                    # Resources (handling nested dicts)
                    cpu_data = sys_data.get("cpu", {})
                    mem_data = sys_data.get("memory", {})
                    
                    cpu_usage = cpu_data.get("relative", 0) * 100
                    mem_usage = mem_data.get("relative", 0) * 100
                    load_list = sys_data.get("load", [0, 0, 0])

                    # 2. Map Sensors
                    temp_list = sens_data.get("sensors", [])
                    cpu_temp = 0
                    if temp_list:
                        # Try to find 'Celsius' or 'temperature' type
                        for s in temp_list:
                            if s.get("type") == "temperature" or "temp" in s.get("name", "").lower():
                                cpu_temp = s.get("value", 0)
                                break

                    # 3. Map Summary & Fix QPM Calculation
                    # total queries / (uptime in minutes)
                    queries_today = sum_data.get("queries", {}).get("total", 0)
                    
                    uptime_minutes = uptime_sec / 60
                    if uptime_minutes > 1:
                        # Real QPM based on uptime
                        qpm = queries_today / uptime_minutes
                    else:
                        # Fallback if uptime info is missing
                        qpm = 0

                    return {
                        "temperature": round(float(cpu_temp), 1),
                        "uptime_days": round(uptime_sec / 86400, 2),
                        "load": round(load_list[0], 2) if load_list else 0,
                        "memory_usage": round(mem_usage, 1),
                        "cpu_usage": round(cpu_usage, 1),
                        "queries_pm": round(qpm, 2)
                    }

        except Exception as e:
            _LOGGER.error("Update Error: %s", e)
            raise UpdateFailed(f"Error communicating with API: {e}")
