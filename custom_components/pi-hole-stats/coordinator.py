import logging
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PiHoleStatsCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Pi-hole v6 data."""

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
            async with async_timeout.timeout(10):
                if not self.sid:
                    async with session.post(f"{base_url}/auth", json={"password": self.pw}) as resp:
                        auth_data = await resp.json()
                        self.sid = auth_data.get("session", {}).get("sid")
                
                headers = {"X-FTL-SID": self.sid, "Accept": "application/json"}
                endpoints = ["system", "sensors", "summary", "gateway", "version", "host", "messages", "blocking", "recent_blocked"]
                
                res = {}
                for ep in endpoints:
                    if ep in ["summary", "recent_blocked"]:
                        path = f"stats/{ep}"
                    elif ep == "blocking":
                        path = "dns/blocking"
                    elif ep == "gateway":
                        path = "network/gateway"
                    else:
                        path = f"info/{ep}"
                    
                    async with session.get(f"{base_url}/{path}", headers=headers) as resp:
                        res[ep] = await resp.json()

                sys = res["system"].get("system", {})
                sens = res["sensors"].get("sensors", {})
                ver_root = res["version"].get("version", {})
                hst = res["host"].get("host", {})
                msgs = res["messages"].get("messages", [])
                sum_data = res["summary"]
                
                is_blocking = res["blocking"].get("blocking") == "enabled"
                
                # Update Recent Blocks: Using the "blocked" key from your image
                recent_list = res["recent_blocked"].get("blocked", [])

                return {
                    "cpu_temp": round(float(sens.get("cpu_temp", 0)), 1),
                    "cpu_usage": round(sys.get("cpu", {}).get("%cpu", 0), 1),
                    "mem_usage": round(sys.get("memory", {}).get("ram", {}).get("%used", 0), 1),
                    "load": round(float(sys.get("cpu", {}).get("load", {}).get("raw", [0])[0]), 2),
                    "uptime_days": round(sys.get("uptime", 0) / 86400, 2),
                    "gateway": res["gateway"].get("gateway", [{}])[0].get("address", "N/A"),
                    "blocking": "Active" if is_blocking else "Disabled",
                    "active_clients": sum_data.get("clients", {}).get("active", 0),
                    # New Total Sensors
                    "dns_queries_today": sum_data.get("queries", {}).get("total", 0),
                    "ads_blocked_today": sum_data.get("queries", {}).get("blocked", 0),
                    "domains_blocked": sum_data.get("gravity", {}).get("domains_total", 0),
                    "msg_count": len(msgs),
                    "msg_list": {f"Alert {m.get('id', i)}": m.get("plain", "No content") for i, m in enumerate(msgs)},
                    "ver_core": ver_root.get("core", {}).get("local", {}).get("version", "N/A"),
                    "rem_core": ver_root.get("core", {}).get("remote", {}).get("version", "N/A"),
                    "ver_ftl": ver_root.get("ftl", {}).get("local", {}).get("version", "N/A"),
                    "rem_ftl": ver_root.get("ftl", {}).get("remote", {}).get("version", "N/A"),
                    "ver_web": ver_root.get("web", {}).get("local", {}).get("version", "N/A"),
                    "rem_web": ver_root.get("web", {}).get("remote", {}).get("version", "N/A"),
                    "host_model": hst.get("model", hst.get("sysname", "Unknown")),
                    "recent_blocked": recent_list
                }
        except Exception as e:
            self.sid = None
            _LOGGER.error("Update failed: %s", e)
            raise UpdateFailed(e)
