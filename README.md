# Pi-hole Statistics for Home Assistant

A custom Home Assistant integration that pulls detailed system and network statistics from your Pi-hole installation. Compatible with both Pi-hole v5 (Legacy API) and Pi-hole v6 (REST API).

## 🚀 Features
- 📊 **Real-time Stats**: Track query volume and blocking performance.
- 🌡️ **System Health**: Monitor CPU temperature, Load, and Memory usage.
- 🕰️ **Uptime Tracking**: Know exactly how long your ad-blocker has been running.
- 🔌 **Easy Setup**: Full UI configuration—no YAML required.

---

## 🛠️ Installation via HACS

1. Ensure **HACS** is installed in your Home Assistant instance.
2. Go to **HACS** -> **Integrations**.
3. Click the **three dots** in the top right corner and select **Custom repositories**.
4. Paste the URL of this repository: `https://github.com/adelando/pi-hole-stats`
5. Select **Integration** as the category and click **Add**.
6. Find **Pi-Hole Statistics** in the list and click **Download**.
7. **Restart Home Assistant.**

---

## ⚙️ Configuration

1. In Home Assistant, go to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **Pi-Hole Statistics**.
3. Fill in the following fields:
   - **Host**: The IP address or hostname of your Pi-hole (e.g., `192.168.1.50`).
   - **Port**: Default is `80`.
   - **API Path**: Select `api` for Pi-hole v6 or `admin` for Pi-hole v5.
   - **App Password / API Key**: 
     - *v6*: Generate an **App Password** in Pi-hole under *Settings > Web Interface*.
     - *v5*: Use the **API Token** found under *Settings > API/Web Interface*.

---

## 📡 Created Sensors

The integration creates the following entities using the naming convention `sensor.pi_hole_stat_<name>`:

| Sensor Name | Entity ID | Unit | Description |
| :--- | :--- | :--- | :--- |
| **Temperature** | `sensor.pi_hole_stat_temperature` | °C | CPU Temperature of the host |
| **Uptime** | `sensor.pi_hole_stat_uptime_days` | days | Total system uptime |
| **CPU Usage** | `sensor.pi_hole_stat_cpu_usage` | % | Current CPU utilization |
| **RAM Usage** | `sensor.pi_hole_stat_memory_usage` | % | Current Memory utilization |
| **System Load** | `sensor.pi_hole_stat_load` | % | System load average (1 min) |
| **Queries per Minute**| `sensor.pi_hole_stat_queries_pm` | qpm | Average DNS traffic speed |

---

## 📊 Example Dashboard Card

To get a clean look like the one we discussed, use this **Entities Card** configuration:

```yaml
type: entities
title: Pi-hole System Health
show_header_toggle: false
entities:
  - entity: sensor.pi_hole_stat_temperature
    name: CPU Temperature
  - entity: sensor.pi_hole_stat_cpu_usage
    name: CPU Usage
  - entity: sensor.pi_hole_stat_memory_usage
    name: RAM Usage
  - entity: sensor.pi_hole_stat_load
    name: System Load
  - entity: sensor.pi_hole_stat_uptime_days
    name: Uptime
  - type: divider
  - entity: sensor.pi_hole_stat_queries_pm
    name: Queries Per Minute
