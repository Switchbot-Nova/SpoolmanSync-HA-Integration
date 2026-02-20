# SpoolmanSync Home Assistant Integration

This integration allows you to manage your Bambu Lab AMS tray assignments directly from Home Assistant.

## Features

- **AMS Tray Entities**: Creates `select` entities for each AMS tray (and external spool) discovered via SpoolmanSync.
- **Spool Assignment**: Change the assigned spool for any tray using the `select` entity.
- **Spool Info**: Provides sensors with detailed information about the currently assigned spool (vendor, material, remaining weight, etc.).

## Installation

### HACS (Recommended)

1. Install [HACS](https://hacs.xyz/) if you haven't already.
2. Go to **HACS** > **Integrations** > **+ Explore & Download Repositories**.
3. Search for **SpoolmanSync**.
4. Click **Download**.
5. Restart Home Assistant.
6. Go to **Settings** -> **Devices & Services** -> **Add Integration**.
7. Search for **SpoolmanSync**.
8. Enter your SpoolmanSync URL (e.g., `http://192.168.0.100:3000`).

### Manual Installation

1. Copy the `custom_components/spoolmansync` directory to your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Go to **Settings** -> **Devices & Services** -> **Add Integration**.
4. Search for **SpoolmanSync**.
5. Enter your SpoolmanSync URL (e.g., `http://192.168.0.100:3000`).

## Requirements

- **SpoolmanSync** must be running and accessible from Home Assistant.
- **ha-bambulab** integration must be installed and configured in Home Assistant (as SpoolmanSync relies on it for printer discovery).

## Lovelace AMS Card

A custom card is included to easily manage your AMS trays. The card is **automatically loaded** when you install the integration—no manual resource registration needed!

### Usage

Simply add the card to your dashboard:

```yaml
type: custom:spoolmansync-card
tray1: select.p2s_22e8bj5b1400071_ams_1_tray_1
tray2: select.p2s_22e8bj5b1400071_ams_1_tray_2
tray3: select.p2s_22e8bj5b1400071_ams_1_tray_3
tray4: select.p2s_22e8bj5b1400071_ams_1_tray_4
```

The visual editor provides entity picker dropdowns for each tray (filtered to `select` domain).
