
## THIS PROJECT IS STILL A WORK IN PROGRESS AND NOT OFFICIALLY WORKING YET!!!

# Pi-hole v6 Stats Integration for Home Assistant

A high-performance custom integration for **Pi-hole v6** using the FTL REST API. This integration provides real-time monitoring of DNS sinkhole health and host hardware.

## Installation via HACS

To install this integration using HACS as a custom repository:

1. Open **HACS** in your Home Assistant sidebar.
2. Click the **three dots** in the top right corner and select **Custom repositories**.
3. Paste the GitHub URL of this repository: `https://github.com/YOUR_USERNAME/pi_hole_stats`
4. Select **Integration** as the category and click **Add**.
5. Find the "Pi-hole Stats" integration in HACS and click **Download**.
6. **Restart Home Assistant**.

---

## Sensor Reference Table

All sensors refresh every **5 seconds**. The following table lists the generated Entity IDs and their available metadata attributes.

| Sensor Name | Entity ID | State Value | Attributes |
| :--- | :--- | :--- | :--- |
| **CPU Temperature** | `sensor.pi_hole_stat_cpu_temp` | Celsius (°C) | `hot_limit` |
| **CPU Usage** | `sensor.pi_hole_stat_cpu_usage` | Percentage (%) | - |
| **Memory Usage** | `sensor.pi_hole_stat_mem_usage` | Percentage (%) | - |
| **System Load** | `sensor.pi_hole_stat_load` | 1min Average | - |
| **Uptime** | `sensor.pi_hole_stat_uptime` | Days | - |
| **Queries/Min** | `sensor.pi_hole_stat_qpm` | QPM | - |
| **Network Gateway** | `sensor.pi_hole_stat_gateway` | IP Address | - |
| **DNS Blocking** | `sensor.pi_hole_stat_blocking` | Active/Disabled | - |
| **Active Clients** | `sensor.pi_hole_stat_clients` | Count | - |
| **Diagnostics** | `sensor.pi_hole_stat_messages` | Msg Count | `msg_list` (ID: Text) |
| **Core Version** | `sensor.pi_hole_stat_ver_core` | String | - |
| **FTL Version** | `sensor.pi_hole_stat_ver_ftl` | String | - |
| **Web Version** | `sensor.pi_hole_stat_ver_web` | String | - |
| **Host Model** | `sensor.pi_hole_stat_host_model` | Model Name | `release`, `sysname`, `version` |
| **Recent Block 1** | `sensor.pi_hole_stat_blocked_1` | Domain Name | - |
| **Recent Block 2** | `sensor.pi_hole_stat_blocked_2` | Domain Name | - |
| **Recent Block 3** | `sensor.pi_hole_stat_blocked_3` | Domain Name | - |

---

## Technical Details

- **Poll Rate**: 5 Seconds
- **Auth**: App Password (SID based)
- **Requirements**: Pi-hole v6.0+

### Attribute Drill-down
- **Diagnostic Messages (`msg_list`)**: Displays the Message ID as the key and the human-readable header as the value.
- **Host Model**: Provides full OS details including kernel version and release branch.
- **CPU Temp**: Includes the `hot_limit` attribute to help monitor thermal throttling thresholds.
    name: Queries Per Minute
