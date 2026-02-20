import logging
import asyncio
import os
import json
import re
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.http import StaticPathConfig

_LOGGER = logging.getLogger(__name__)

DOMAIN = "spoolmansync"
PLATFORMS = [Platform.SELECT, Platform.SENSOR]


def parse_active_tray(active_tray: str) -> str | None:
    """Parse active_tray value, handling both JSON and string formats.
    
    Spoolman may store active_tray as either a JSON string or a quoted string.
    This function handles both cases and returns the parsed tray ID.
    """
    if not active_tray:
        return None
    
    try:
        # Try parsing as JSON first
        return json.loads(active_tray)
    except (json.JSONDecodeError, ValueError):
        # Fall back to treating it as a quoted string
        return active_tray.strip('"')

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SpoolmanSync from a config entry."""
    url = entry.data[CONF_URL]
    session = async_get_clientsession(hass)

    async def async_get_data():
        try:
            # Fetch printers and spools from SpoolmanSync API
            async with session.get(f"{url}/api/printers") as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching printers: {response.status}")
                printers_data = await response.json()
                _LOGGER.debug(f"Printers API response (status {response.status}): {printers_data}")

            async with session.get(f"{url}/api/spools") as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching spools: {response.status}")
                spools_data = await response.json()
                _LOGGER.debug(f"Spools API response (status {response.status}): {len(spools_data) if isinstance(spools_data, list) else len(spools_data.get('spools', []))} items")

            # Handle both list and dict responses
            if isinstance(printers_data, list):
                printers_list = printers_data
            else:
                printers_list = printers_data.get("printers", [])
            
            if isinstance(spools_data, list):
                spools_list = spools_data
            else:
                spools_list = spools_data.get("spools", [])

            # If the printers endpoint returns nothing, try to build a
            # printers/AMS/trays structure from the spools' `extra.active_tray`
            # values so users still get entities.
            if not printers_list:
                _LOGGER.info("No printers returned by API — building fallback from spools.active_tray")
                printers_from_spools = {}
                pattern = re.compile(r"sensor\.([a-zA-Z0-9_]+)_ams_(\d+)_tray_(\d+)")
                for spool in spools_list:
                    extra = spool.get("extra", {})
                    active = parse_active_tray(extra.get("active_tray", ""))
                    if not active:
                        continue
                    m = pattern.search(active)
                    if not m:
                        continue
                    printer_key, ams_idx, tray_idx = m.group(1), int(m.group(2)), int(m.group(3))
                    p = printers_from_spools.setdefault(printer_key, {"entity_id": f"sensor.{printer_key}_print_status", "name": printer_key, "ams_units": {}})
                    ams = p["ams_units"].setdefault(ams_idx, {"name": f"AMS {ams_idx}", "trays": []})
                    # Build a tray object based on spool and active_tray
                    tray_obj = {
                        "entity_id": active,
                        "tray_number": tray_idx,
                        "name": spool.get("filament", {}).get("name", f"Tray {tray_idx}"),
                        "assigned_spool": spool,
                    }
                    ams["trays"].append(tray_obj)

                # Convert ams_units dicts to lists and assemble printers_list
                printers_list = []
                for key, pdata in printers_from_spools.items():
                    ams_units_list = []
                    for idx in sorted(pdata["ams_units"].keys()):
                        ams_units_list.append(pdata["ams_units"][idx])
                    printers_list.append({
                        "entity_id": pdata["entity_id"],
                        "name": pdata["name"],
                        "ams_units": ams_units_list,
                    })

            coordinator_data = {
                "printers": printers_list,
                "spools": spools_list
            }
            _LOGGER.info(
                f"SpoolmanSync: Fetched {len(printers_list)} printers and {len(spools_list)} spools"
            )
            return coordinator_data
        except Exception as err:
            _LOGGER.error(f"Error communicating with SpoolmanSync: {err}")
            raise UpdateFailed(f"Error communicating with SpoolmanSync: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="spoolmansync",
        update_method=async_get_data,
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register the custom card static path
    www_path = hass.config.path("custom_components", DOMAIN, "www")
    if os.path.exists(www_path):
        url_path = f"/custom_components/{DOMAIN}/www"
        _LOGGER.info(f"Registering SpoolmanSync card static path at {url_path}")
        try:
            await hass.http.async_register_static_paths([
                StaticPathConfig(
                    url_path=url_path,
                    path=www_path,
                    cache_headers=False
                )
            ])
        except Exception as err:
            _LOGGER.error(f"Failed to register card static path: {err}")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
