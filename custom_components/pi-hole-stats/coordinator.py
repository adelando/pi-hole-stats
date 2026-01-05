# Inside coordinator.py -> _async_update_data
                # ... existing logic ...
                
                # Fetching nested objects correctly
                sys = res["system"].get("system", {})
                sens = res["sensors"].get("sensors", {})
                ver_root = res["version"].get("version", {})
                hst = res["host"].get("host", {}) # v6 often nests this under 'host'
                msgs = res["messages"].get("messages", [])
                sum_data = res["summary"].get("queries", {})
                
                # Fix Blocking Status: v6 nests this under dns -> blocking -> active
                # Check results["blocking"] structure
                is_blocking = res["blocking"].get("blocking", False)

                # Fix Active Clients: v6 moved this to 'summary' -> 'clients' -> 'active'
                active_clients = res["summary"].get("clients", {}).get("active", 0)

                # Fix Gateway: (Already corrected but double-checking)
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
                    # Result is now a boolean for easy sensor translation
                    "blocking": "Active" if is_blocking else "Disabled",
                    "active_clients": active_clients,
                    "msg_count": len(msgs),
                    # Diagnostic Fix: Map messages to a clean dictionary
                    "msg_list": {f"Alert {i}": m.get("message", "Unknown") for i, m in enumerate(msgs)},
                    "ver_core": ver_root.get("core", {}).get("local", {}).get("version", "N/A"),
                    "rem_core": ver_root.get("core", {}).get("remote", {}).get("version", "N/A"),
                    "ver_ftl": ver_root.get("ftl", {}).get("local", {}).get("version", "N/A"),
                    "rem_ftl": ver_root.get("ftl", {}).get("remote", {}).get("version", "N/A"),
                    "ver_web": ver_root.get("web", {}).get("local", {}).get("version", "N/A"),
                    "rem_web": ver_root.get("web", {}).get("remote", {}).get("version", "N/A"),
                    # Host Fix: Combine model and hardware details
                    "host_model": hst.get("model", hst.get("sysname", "Unknown")),
                    "host_attr": {
                        "release": hst.get("release"),
                        "architecture": hst.get("machine"),
                        "kernel": hst.get("version")
                    },
                    # Recent Blocks Fix: Just pass the whole list
                    "recent_blocked": res["recent_blocked"].get("recent_blocked", []),
                    "queries_pm": round(sum_data.get("total", 0) / (max(sys.get("uptime", 1)/60, 1)), 2)
                }
