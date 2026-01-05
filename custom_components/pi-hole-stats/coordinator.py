import logging
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.entry = entry
        self.host = entry.data["host"].strip().rstrip("/")
        self.port = entry.data["port"]
        self.pw = entry.data["api_key"]
        self.sid = entry.data.get("sid")
        
        # Pre-define device info for all entities to use
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Pi-hole",
            model="FTL v6",
            configuration_url=f"http://{self.host}:{self.port}/admin"
        )

        super().__init__(
            hass, _LOGGER, name="Pi-Hole Stats", 
            update_interval=timedelta(seconds=5) 
        )

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)
        base_url = f"http://{self.host}:{self.port}/api"

        try:
            async with async_timeout.timeout(4):
                if not self.sid:
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                
                headers = {"X-FTL-SID": self.sid, "Accept": "application/json"}
                
                endpoints = ["info/system", "info/sensors", "stats/summary", "network/gateway", 
                             "info/version", "info/host", "info/ftl", "info/messages", 
                             "stats/recent_blocked", "dns/blocking"]
                
                results = {}
                for ep in endpoints:
                    async with session.get(f"{base_url}/{ep}", headers=headers) as resp:
                        results[ep.split('/')[-1]] = await resp.json()

                # Extraction logic stays the same as previous step...
                sys = results["system"].get("system", {})
                sens = results["sensors"].get("sensors", {})
                ver = results["version"]
                hst = results["host"]
                msgs = results["messages"].get("messages", [])

                return {
                    "cpu_temp": round(float(sens.get("cpu_temp", 0)), 1),
                    "hot_limit": sens.get("hot_limit", 0),
                    "cpu_usage": round(sys.get("cpu", {}).get("%cpu", 0), 1),
                    "mem_usage": round(sys.get("memory", {}).get("ram", {}).get("%used", 0), 1),
                    "load": sys.get("cpu", {}).get("load", {}).get("raw", [0])[0],
                    "uptime_days": round(sys.get("uptime", 0) / 86400, 2),
                    "gateway": results["gateway"].get("gateway", "N/A"),
                    "blocking": "Active" if results["blocking"].get("blocking") else "Disabled",
                    "active_clients": results["ftl"].get("clients", {}).get("active", 0),
                    "msg_count": len(msgs),
                    "msg_list": {str(m.get("id")): m.get("message") for m in msgs},
                    "ver_core": f"{ver.get('core', {}).get('current')} (Up: {ver.get('core',{}).get('update_available')})",
                    "ver_ftl": f"{ver.get('ftl', {}).get('current')} (Up: {ver.get('ftl',{}).get('update_available')})",
                    "ver_web": f"{ver.get('web', {}).get('current')} (Up: {ver.get('web',{}).get('update_available')})",
                    "host_model": hst.get("model", "Unknown"),
                    "host_attr": {"release": hst.get("release"), "sysname": hst.get("sysname"), "version": hst.get("version")},
                    "blocked_1": results["recent_blocked"].get("recent_blocked", ["None"]*3)[0],
                    "blocked_2": results["recent_blocked"].get("recent_blocked", ["None"]*3)[1],
                    "blocked_3": results["recent_blocked"].get("recent_blocked", ["None"]*3)[2],
                    "queries_pm": round(results["summary"].get("queries", {}).get("total", 0) / (max(sys.get("uptime", 1)/60, 1)), 2)
                }
        except Exception as e:
            self.sid = None
            _LOGGER.error("Update failed: %s", e)
            raise UpdateFailed(e)
