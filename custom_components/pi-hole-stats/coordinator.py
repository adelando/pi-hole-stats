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
                endpoints = ["system", "sensors", "summary", "gateway", "version", "host", "ftl", "messages", "recent_blocked", "blocking"]
                
                res = {}
                for ep in endpoints:
                    path = f"info/{ep}" if ep not in ["summary", "recent_blocked", "blocking"] else f"stats/{ep}"
                    if ep == "blocking": path = "dns/blocking"
                    if ep == "gateway": path = "network/gateway"
                    
                    async with session.get(f"{base_url}/{path}", headers=headers) as resp:
                        res[ep] = await resp.json()

                sys = res["system"].get("system", {})
                sens = res["sensors"].get("sensors", {})
                ver = res["version"]
                hst = res["host"]

                return {
                    "cpu_temp": round(float(sens.get("cpu_temp", 0)), 1),
                    "hot_limit": sens.get("hot_limit", 0),
                    "cpu_usage": round(sys.get("cpu", {}).get("%cpu", 0), 1),
                    "mem_usage": round(sys.get("memory", {}).get("ram", {}).get("%used", 0), 1),
                    "load": sys.get("cpu", {}).get("load", {}).get("raw", [0])[0],
                    "uptime_days": round(sys.get("uptime", 0) / 86400, 2),
                    "gateway": res["gateway"].get("gateway", "N/A"),
                    "blocking": "Active" if res["blocking"].get("blocking") else "Disabled",
                    "active_clients": res["ftl"].get("clients", {}).get("active", 0),
                    "msg_count": len(res["messages"].get("messages", [])),
                    "msg_list": {str(m.get("id")): m.get("message") for m in res["messages"].get("messages", [])},
                    "ver_core": ver.get('core', {}).get('current'),
                    "up_core": ver.get('core', {}).get('update_available'),
                    "ver_ftl": ver.get('ftl', {}).get('current'),
                    "up_ftl": ver.get('ftl', {}).get('update_available'),
                    "ver_web": ver.get('web', {}).get('current'),
                    "up_web": ver.get('web', {}).get('update_available'),
                    "host_model": hst.get("model", "Unknown"),
                    "host_attr": {"release": hst.get("release"), "sysname": hst.get("sysname"), "version": hst.get("version")},
                    "blocked_1": res["recent_blocked"].get("recent_blocked", ["None"]*3)[0],
                    "blocked_2": res["recent_blocked"].get("recent_blocked", ["None"]*3)[1],
                    "blocked_3": res["recent_blocked"].get("recent_blocked", ["None"]*3)[2],
                    "queries_pm": round(res["summary"].get("queries", {}).get("total", 0) / (max(sys.get("uptime", 1)/60, 1)), 2)
                }
        except Exception as e:
            self.sid = None
            raise UpdateFailed(f"Error communicating with API: {e}")
