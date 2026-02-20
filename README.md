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

A custom Lovelace card is included to manage your AMS trays, but the integration does not automatically register the frontend resource.

You must add the card JavaScript as a Lovelace resource manually (one of these options):

- Recommended — copy the card to Home Assistant `www` and add a local resource:

	1. Copy `custom_components/spoolmansync/www/spoolmansync-card.js` into your Home Assistant `config/www/` folder.
	2. In Home Assistant go to **Settings → Dashboards → Resources** (or **Settings → Lovelace Dashboards → Resources**) and add a new resource with:
		 - URL: `/local/spoolmansync-card.js`
		 - Resource type: `module`

- Alternative — if you installed the card via HACS as a frontend repository, add the HACS-provided resource (HACS normally does this for you). Example pattern:

	- `/hacsfiles/<repo-folder>/spoolmansync-card.js?hacstag=<tag>`

After adding the resource (and reloading the Lovelace page), add the card to your dashboard with this configuration:

```yaml
type: custom:spoolmansync-card
tray1: select.p2s_22e8bj5b1400071_ams_1_tray_1
tray2: select.p2s_22e8bj5b1400071_ams_1_tray_2
tray3: select.p2s_22e8bj5b1400071_ams_1_tray_3
tray4: select.p2s_22e8bj5b1400071_ams_1_tray_4
```

The visual editor will provide entity pickers for each tray (filtered to the `select` domain).
