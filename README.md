
## THIS PROJECT IS STILL A WORK IN PROGRESS AND NOT OFFICIALLY WORKING YET!!!

# Pi-hole v6 Stats Integration for Home Assistant

A custom Home Assistant integration designed specifically for **Pi-hole v6** using the high-performance FTL REST API. This integration provides real-time monitoring of your DNS sinkhole and host hardware with a high-frequency refresh rate.

## Features
- **High-Frequency Updates**: Configured for a 5-second polling interval.
- **Pi-hole v6 Native**: Uses the `/api` endpoints and `X-FTL-SID` session authentication.
- **Comprehensive Hardware Monitoring**: CPU, RAM, Load, and Temperature.
- **Diagnostic Insights**: Live list of Pi-hole system messages.
- **Security Visibility**: Live tracking of the 3 most recently blocked domains.

---

## Available Sensors

| Sensor Name | Description | State Value |
| :--- | :--- | :--- |
| **CPU Temperature** | Pi hardware thermal sensor | Celsius (°C) |
| **CPU Usage** | Current CPU load percentage | Percentage (%) |
| **Memory Usage** | Current RAM utilization | Percentage (%) |
| **System Load** | 1-minute load average | Float |
| **Uptime** | Days since last host boot | Days |
| **Queries/Min** | Daily average queries per minute | QPM |
| **Network Gateway** | Primary network gateway IP | IP Address |
| **DNS Blocking** | Global blocking status | Active / Disabled |
| **Active Clients** | Unique clients seen in last 24h | Count |
| **Diagnostic Messages** | Count of system alerts | Count |
| **Core Version** | Installed version of Pi-hole Core | String |
| **FTL Version** | Installed version of FTL Engine | String |
| **Web Version** | Installed version of Web Interface | String |
| **Host Model** | Hardware model of the machine | String |
| **Recent Block 1** | Most recently blocked domain | Domain Name |
| **Recent Block 2** | Second most recently blocked domain | Domain Name |
| **Recent Block 3** | Third most recently blocked domain | Domain Name |

---

## Sensor Attributes

To keep the dashboard clean, secondary data is stored within the attributes of the following sensors:

### Pi-hole CPU Temperature
- `hot_limit`: The thermal ceiling (Max Temp) for the CPU.

### Pi-hole Host Model
- `release`: Operating system release (e.g., "12").
- `sysname`: System type (e.g., "Linux").
- `version`: Specific kernel/OS build version.

### Pi-hole Diagnostic Messages
- `msg_list`: A dictionary of all current system messages.
    - **Key**: Message ID
    - **Value**: Plain text header/description of the message.

---

## Requirements & Setup

1. **Pi-hole Version**: Must be running v6.0 or higher.
2. **App Password**: 
   - Navigate to your Pi-hole Web UI.
   - Go to **Settings > Web Interface**.
   - Enable **Expert Mode**.
   - Select **Configure App Password** and generate a long-form password.
3. **Installation**: 
   - Place the files in `/config/custom_components/pi_hole_stats/`.
   - Restart Home Assistant.
   - Add the integration via **Settings > Devices & Services**.

## Technical Details
- **Refresh Rate**: 5 Seconds.
- **Timeout**: 4 Seconds (Optimized for fast polling).
- **Authentication**: Session-based (`/api/auth`).
  - entity: sensor.pi_hole_stat_queries_pm
    name: Queries Per Minute
