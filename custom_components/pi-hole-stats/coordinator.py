# Inside coordinator.py -> _async_update_data
                # ... existing fetching logic ...

                sys = res["system"].get("system", {})
                sens = res["sensors"].get("sensors", {})
                ver = res["version"].get("version", {})
                hst = res["host"]
                msgs = res["messages"].get("messages", [])

                # Fix Gateway: Extract first address from the list
                gw_data = res["gateway"].get("gateway", [])
                gateway_ip = gw_data[0].get("address", "N/A") if gw_data else "N/A"

                return {
                    "cpu_temp": round(float(sens.get("cpu_temp", 0)), 1),
                    "hot_limit": sens.get("hot_limit", 0),
                    "cpu_usage": round(sys.get("cpu", {}).get("%cpu", 0), 1),
                    "mem_usage": round(sys.get("memory", {}).get("ram", {}).get("%used", 0), 1),
                    # Fix Load: Multiply by 100 for percentage representation if desired, 
                    # or round to 2 decimals for standard load average.
                    "load": round(sys.get("cpu", {}).get("load", {}).get("raw", [0])[0], 2),
                    "uptime_days": round(sys.get("uptime", 0) / 86400, 2),
                    "gateway": gateway_ip,
                    "blocking": "Active" if res["blocking"].get("blocking") else "Disabled",
                    "active_clients": res["ftl"].get("clients", {}).get("active", 0),
                    "msg_count": len(msgs),
                    # Fix Messages: Extract 'message' field from the list of dicts
                    "msg_list": {f"Alert {i}": m.get("message") for i, m in enumerate(msgs)},
                    
                    # Fix Versions: Drill into the core/web/ftl local & remote keys
                    "ver_core": ver.get("core", {}).get("local", {}).get("version", "N/A"),
                    "rem_core": ver.get("core", {}).get("remote", {}).get("version", "N/A"),
                    "ver_ftl": ver.get("ftl", {}).get("local", {}).get("version", "N/A"),
                    "rem_ftl": ver.get("ftl", {}).get("remote", {}).get("version", "N/A"),
                    "ver_web": ver.get("web", {}).get("local", {}).get("version", "N/A"),
                    "rem_web": ver.get("web", {}).get("remote", {}).get("version", "N/A"),
                    
                    "host_model": hst.get("model", "Unknown"),
                    "host_attr": {"release": hst.get("release"), "sysname": hst.get("sysname"), "version": hst.get("version")},
                    "blocked_1": res["recent_blocked"].get("recent_blocked", ["None"]*3)[0],
                    "blocked_2": res["recent_blocked"].get("recent_blocked", ["None"]*3)[1],
                    "blocked_3": res["recent_blocked"].get("recent_blocked", ["None"]*3)[2],
                    "queries_pm": round(res["summary"].get("queries", {}).get("total", 0) / (max(sys.get("uptime", 1)/60, 1)), 2)
                }
