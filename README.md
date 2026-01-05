### THIS INTEGRATION IS EXTREMELY EXPERIMENTAL AND IS SUBJECT TO CHANGE OR MAY BE ABANDONED.

# Pi-hole v6 Stats Integration

A high-performance custom integration for **Pi-hole v6** instances. This integration uses the FTL REST API to provide real-time hardware, network, and security metrics directly in Home Assistant.

## Installation via HACS
1. Open **HACS** > **Integrations**.
2. Top right menu > **Custom repositories**.
3. Add `https://github.com/adelando/pi_hole_stats` as an **Integration**.
4. Download and **Restart Home Assistant**.

---

## Entity Numbering Logic
To support multiple Pi-hole installations, this integration automatically numbers Entity IDs based on the order they were added:
- **Installation 1**: `sensor.pi_hole_stat_[key]`
- **Installation 2**: `sensor.pi_hole_stat_2_[key]`
- **Installation 3**: `sensor.pi_hole_stat_3_[key]`

---

## Available Entities

### 1. Update Entities (Version Tracking)
These entities replace standard sensors for versioning. They will notify you via the Home Assistant UI when a new version is released by the Pi-hole team.

| Name | Entity ID Example (Device 1) | Attributes |
| :--- | :--- | :--- |
| **Pi-hole Core Update** | `update.pi_hole_core_update` | Release Summary, Remote Link |
| **Pi-hole FTL Update** | `update.pi_hole_ftl_update` | Release Summary, Remote Link |
| **Pi-hole Web Update** | `update.pi_hole_web_interface_update` | Release Summary, Remote Link |

### 2. Sensor Entities (Live Stats)
Refreshes every **5 seconds**.

| Category | Sensor Name | Entity ID Example (Device 1) | Unit | Attributes |
| :--- | :--- | :--- | :--- | :--- |
| **Hardware** | **CPU Temperature** | `sensor.pi_hole_stat_cpu_temp` | °C | `hot_limit` |
| **Hardware** | **CPU Usage** | `sensor.pi_hole_stat_cpu_usage` | % | - |
| **Hardware** | **Memory Usage** | `sensor.pi_hole_stat_mem_usage` | % | - |
| **Hardware** | **System Load** | `sensor.pi_hole_stat_load` | L | - |
| **Hardware** | **Uptime** | `sensor.pi_hole_stat_uptime_days` | days | - |
| **Hardware** | **Host Model** | `sensor.pi_hole_stat_host_model` | - | `release`, `sysname`, `version` |
| **Network** | **QPM** | `sensor.pi_hole_stat_queries_pm` | qpm | - |
| **Network** | **Network Gateway** | `sensor.pi_hole_stat_gateway` | IP | - |
| **Network** | **Active Clients** | `sensor.pi_hole_stat_active_clients` | count | - |
| **Security** | **DNS Blocking** | `sensor.pi_hole_stat_blocking` | - | - |
| **Security** | **Recent Block 1** | `sensor.pi_hole_stat_blocked_1` | domain | - |
| **Security** | **Recent Block 2** | `sensor.pi_hole_stat_blocked_2` | domain | - |
| **Security** | **Recent Block 3** | `sensor.pi_hole_stat_blocked_3` | domain | - |
| **System** | **Diagnostics** | `sensor.pi_hole_stat_msg_count` | msgs | `msg_list` (Alert IDs & Text) |

---

## Detailed Attribute Information

### Diagnostic Messages (`msg_list`)
The `sensor.pi_hole_stat_msg_count` entity contains a list of all active Pi-hole diagnostic alerts in its attributes.
* **Key**: The unique ID of the message.
* **Value**: The plain-text header/description provided by FTL.

### Host Model Info
The `sensor.pi_hole_stat_host_model` provides deep OS insights:
* `release`: OS version (e.g., "12").
* `sysname`: System kernel type (e.g., "Linux").
* `version`: Specific build or kernel version.

---

## Configuration
- **Polling Rate**: 5 Seconds.
- **Connection**: Requires an **App Password** from Pi-hole v6 (Settings > Web Interface > Expert Mode).
- **Grouping**: All entities are automatically grouped by "Device" in the Home Assistant Settings for easy management.
