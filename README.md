### THIS INTEGRATION IS EXTREMELY EXPERIMENTAL AND IS SUBJECT TO CHANGE OR MAY BE ABANDONED.

# Pi-hole Stats v6 for Home Assistant

A custom Home Assistant integration for Pi-hole v6 (FTL v6) that provides detailed hardware stats, ad-blocking performance, and update notifications.

## Features
- **Hardware Monitoring**: CPU Temperature, Usage, System Load, and Memory.
- **DNS Performance**: Total Queries, Ads Blocked, and Gravity list size.
- **Diagnostics**: Real-time alerts and rate-limiting messages.
- **Updates**: Individual entities for Core, FTL, and Web interface updates.


## Installation via HACS
1. Open **HACS** > **Integrations**.
2. Top right menu > **Custom repositories**.
3. Add `https://github.com/adelando/pi_hole_stats` as an **Integration**.
4. Download and **Restart Home Assistant**.

## Manual Installation
1. Copy the `pihole_stats` folder to your `custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings > Devices & Services > Add Integration** and search for "Pi-hole Stats".
4. Enter your Pi-hole IP, Port (usually 80 or 8080), and App Password.


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
| **Security** | **Recent Block** | `sensor.pi_hole_stat_blocked` | domain | - |
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

---

## Custom Dashboard Card

This custom card provides a professional, unified look for your Pi-hole stats. It features a theme-matching background, dynamic temperature alerts, and an auto-hiding update section.

### Requirements
To use this card, you must install the following via **HACS**:
1. [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)
2. [Mini Graph Card](https://github.com/kalkih/mini-graph-card)
3. [Card Mod](https://github.com/thomasloven/lovelace-card-mod)

### Card Configuration
Add a **Manual Card** to your dashboard and paste the following YAML:

```yaml
type: custom:mod-card
card_mod:
  style: |
    ha-card {
      background: var(--ha-card-background);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 12px;
      border: 1px solid var(--divider-color, #333);
    }
card:
  type: vertical-stack
  cards:
    - type: custom:mushroom-title-card
      title: Pi-hole System Stats
      subtitle: Local Network DNS Management
      card_mod:
        style: |
          ha-card {
            margin-bottom: -10px;
          }
    - type: custom:mushroom-template-card
      primary: Hardware & System
      secondary: >
        CPU: {{ states('sensor.pi_hole_stat_cpu_usage') }}% |  Temp: {{
        states('sensor.pi_hole_stat_cpu_temp') }}°C | Load: {{
        states('sensor.pi_hole_stat_load') }}%
      icon: mdi:cpu-64-bit
      icon_color: >
        {% set temp = states('sensor.pi_hole_stat_cpu_temp') | float %} {% set
        limit = state_attr('sensor.pi_hole_stat_cpu_temp', 'hot_limit') |
        float(80) %} {{ 'red' if temp >= (limit - 5) else 'green' }}
      card_mod:
        style: |
          ha-card {
            background: {{ 'rgba(255, 0, 0, 0.1)' if is_state('sensor.pi_hole_stat_blocking', 'Disabled') else 'none' }};
            transition: background 0.5s ease;
          }
    - type: custom:mini-graph-card
      entities:
        - entity: sensor.pi_hole_stat_cpu_usage
          name: CPU Usage
          color: "#4caf50"
        - entity: sensor.pi_hole_stat_cpu_temp
          name: Temperature
          color: "#ff9800"
      line_width: 2
      hours_to_show: 24
      show:
        extrema: true
        fill: fade
    - type: custom:mushroom-template-card
      primary: Network & Blocking
      secondary: |
        {{ states('sensor.pi_hole_stat_ads_blocked_today') }} Ads Blocked Today
      icon: mdi:shield-check
      icon_color: >-
        {{ 'green' if is_state('sensor.pi_hole_stat_blocking', 'Active') else
        'red' }}
      layout: horizontal
    - type: grid
      columns: 2
      square: false
      cards:
        - type: custom:mushroom-entity-card
          entity: sensor.pi_hole_stat_dns_queries_today
          name: Total Queries
          icon: mdi:dns
        - type: custom:mushroom-entity-card
          entity: sensor.pi_hole_stat_active_clients
          name: Active Clients
          icon: mdi:account-group
        - type: custom:mushroom-entity-card
          entity: sensor.pi_hole_stat_domains_blocked
          name: Gravity List
          icon: mdi:list-status
        - type: custom:mushroom-entity-card
          entity: sensor.pi_hole_stat_gateway
          name: Gateway
          icon: mdi:router-wireless
    - type: custom:mushroom-template-card
      primary: Most Recent Blocked
      secondary: "{{ states('sensor.pi_hole_stat_recent_blocked') }}"
      icon: mdi:close-octagon
      icon_color: red
      tap_action:
        action: more-info
      entity: sensor.pi_hole_stat_recent_blocked
    - type: conditional
      conditions:
        - entity: update.pi_hole_core_update
          state: "on"
        - entity: update.pi_hole_ftl_update
          state: "on"
        - entity: update.pi_hole_web_interface_update
          state: "on"
      card:
        type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: Updates Available
            subtitle: Version mismatch detected
          - type: custom:mushroom-template-card
            primary: Pi-hole Core
            secondary: >-
              Inst: {{ state_attr('update.pi_hole_core_update',
              'installed_version') }} | Latest: {{
              state_attr('update.pi_hole_core_update', 'latest_version') }}
            icon: mdi:server
            icon_color: orange
            entity: update.pi_hole_core_update
          - type: custom:mushroom-template-card
            primary: Pi-hole FTL
            secondary: >-
              Inst: {{ state_attr('update.pi_hole_ftl_update',
              'installed_version') }} | Latest: {{
              state_attr('update.pi_hole_ftl_update', 'latest_version') }}
            icon: mdi:engine
            icon_color: orange
            entity: update.pi_hole_ftl_update
          - type: custom:mushroom-template-card
            primary: Web Interface
            secondary: >-
              Inst: {{ state_attr('update.pi_hole_web_interface_update',
              'installed_version') }} | Latest: {{
              state_attr('update.pi_hole_web_interface_update', 'latest_version')
              }}
            icon: mdi:monitor-dashboard
            icon_color: orange
            entity: update.pi_hole_web_interface_update
