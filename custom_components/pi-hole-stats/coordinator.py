import logging
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Pi-hole data."""

    def __init__(self, hass, entry):
        """Initialize."""
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
        """Fetch data from API endpoint."""
        session = async_get_clientsession(self.hass)
        base_url = f"http://{self.host}:{self.port}/api"

        try:
            async with async_timeout.timeout(10):
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

                # Fix: Ensure we are correctly drilling into the nested 'version' key
                sys = res["system"].get("system", {})
                sens = res["sensors"].get("sensors", {})
                ver_root = res["version"].get("version", {})
                hst = res["host"]
                msgs = res["messages"].get("messages", [])

                # Fix Gateway: Extract first address from the list
                gw_list = res["gateway"].get("gateway", [])
                gateway_ip = gw_list[0].get("address", "N/A") if gw_list else "N/A"

                return {
                    "cpu_temp": round(float(sens.get("cpu_temp", 0)), 1),
                    "hot_limit": sens.get("hot_limit", 0),
                    "cpu_usage": round(sys.get("cpu", {}).get("%cpu", 0), 1),
                    "mem_usage": round(sys.get("memory", {}).get("ram", {}).get("%used", 0), 1),
                    "load": round(sys.get("cpu", {}).get("load", {}).get("raw", [0])[0], 2),
                    "uptime_days": round(sys.get("uptime", 0) / 86400, 2),
                    "gateway": gateway_ip,
                    "blocking": "Active" if res["blocking"].get("blocking") else "Disabled",
                    "active_clients": res["ftl"].get("clients", {}).get("active", 0),
                    "msg_count": len(msgs),
                    "msg_list": {f"Alert {i}": m.get("message") for i, m in enumerate(msgs)},
                    "ver_core": ver_root.get("core", {}).get("local", {}).get("version", "N/A"),
                    "rem_core": ver_root.get("core", {}).get("remote", {}).get("version", "N/A"),
                    "ver_ftl": ver_root.get("ftl", {}).get("local", {}).get("version", "N/A"),
                    "rem_ftl": ver_root.get("ftl", {}).get("remote", {}).get("version", "N/A"),
                    "ver_web": ver_root.get("web", {}).get("local", {}).get("version", "N/A"),
                    "rem_web": ver_root.get("web", {}).get("remote", {}).get("version", "N/A"),
                    "host_model": hst.get("model", "Unknown"),
                    "host_attr": {"release": hst.get("release"), "sysname": hst.get("sysname"), "version": hst.get("version")},
                    "blocked_1": res["recent_blocked"].get("recent_blocked", ["None"]*3)[0],
                    "blocked_2": res["recent_blocked"].get("recent_blocked", ["None"]*3)[1],
                    "blocked_3": res["recent_blocked"].get("recent_blocked", ["None"]*3)[2],
                    "queries_pm": round(res["summary"].get("queries", {}).get("total", 0) / (max(sys.get("uptime", 1)/60, 1)), 2)
                }
        except Exception as e:
            self.sid = None
            _LOGGER.error("Update failed: %s", e)
            raise UpdateFailed(e)
