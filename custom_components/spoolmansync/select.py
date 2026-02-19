import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SpoolmanSync select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    url = entry.data[CONF_URL]
    
    entities = []
    
    # We assume there is at least one printer and it has AMS units
    # The user asked for 4 entities: AMS Tray 1, 2, 3, 4
    # We will map these to the first printer's first AMS unit for simplicity, 
    # or create them based on discovered printers.
    
    printers = coordinator.data.get("printers", [])
    if not printers:
        _LOGGER.warning("No printers found in SpoolmanSync")
        return

    # For each printer and each AMS unit, create tray entities
    for printer in printers:
        printer_name = printer.get("name", "Printer")
        for ams in printer.get("ams_units", []):
            ams_name = ams.get("name", "AMS")
            for tray in ams.get("trays", []):
                entities.append(
                    SpoolmanTraySelect(
                        coordinator,
                        url,
                        printer_name,
                        ams_name,
                        tray,
                    )
                )
        
        # Also handle external spool if it exists
        if printer.get("external_spool"):
            entities.append(
                SpoolmanTraySelect(
                    coordinator,
                    url,
                    printer_name,
                    "External",
                    printer["external_spool"],
                )
            )

    async_add_entities(entities)

class SpoolmanTraySelect(CoordinatorEntity, SelectEntity):
    """Representation of a Spoolman Tray selection."""

    def __init__(self, coordinator, url, printer_name, ams_name, tray):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._url = url
        self._printer_name = printer_name
        self._ams_name = ams_name
        self._tray_entity_id = tray["entity_id"]
        self._tray_number = tray["tray_number"]
        
        # Unique ID based on the HA entity ID of the tray
        self._attr_unique_id = f"spoolmansync_{self._tray_entity_id}"
        self._attr_name = f"{ams_name} Tray {self._tray_number}"
        if ams_name == "External":
             self._attr_name = "External Tray"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, printer_name)},
            name=printer_name,
            manufacturer="SpoolmanSync",
            model="Bambu Lab Printer",
        )

    @property
    def options(self) -> list[str]:
        """Return a list of available spools."""
        spools = self.coordinator.data.get("spools", [])
        options = ["None"]
        for spool in spools:
            vendor = spool.get("filament", {}).get("vendor", {}).get("name", "Unknown")
            material = spool.get("filament", {}).get("material", "Unknown")
            name = spool.get("filament", {}).get("name", "")
            spool_label = f"#{spool['id']} {vendor} {material} {name}".strip()
            options.append(spool_label)
        return options

    @property
    def current_option(self) -> str | None:
        """Return the currently selected spool."""
        spools = self.coordinator.data.get("spools", [])
        for spool in spools:
            active_tray = spool.get("extra", {}).get("active_tray")
            if active_tray:
                # Spoolman stores extra values as JSON strings
                import json
                try:
                    clean_tray_id = json.loads(active_tray)
                    if clean_tray_id == self._tray_entity_id:
                        vendor = spool.get("filament", {}).get("vendor", {}).get("name", "Unknown")
                        material = spool.get("filament", {}).get("material", "Unknown")
                        name = spool.get("filament", {}).get("name", "")
                        return f"#{spool['id']} {vendor} {material} {name}".strip()
                except Exception:
                    if active_tray.strip('"') == self._tray_entity_id:
                        vendor = spool.get("filament", {}).get("vendor", {}).get("name", "Unknown")
                        material = spool.get("filament", {}).get("material", "Unknown")
                        name = spool.get("filament", {}).get("name", "")
                        return f"#{spool['id']} {vendor} {material} {name}".strip()
        return "None"

    async def async_select_option(self, option: str) -> None:
        """Change the selected spool."""
        session = async_get_clientsession(self.hass)
        
        if option == "None":
            # Find current spool and unassign
            current_spool_id = None
            spools = self.coordinator.data.get("spools", [])
            for spool in spools:
                active_tray = spool.get("extra", {}).get("active_tray")
                if active_tray:
                    import json
                    try:
                        if json.loads(active_tray) == self._tray_entity_id:
                            current_spool_id = spool["id"]
                            break
                    except:
                        if active_tray.strip('"') == self._tray_entity_id:
                            current_spool_id = spool["id"]
                            break
            
            if current_spool_id:
                async with session.delete(
                    f"{self._url}/api/spools",
                    json={"spoolId": current_spool_id}
                ) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to unassign spool: %s", await response.text())
        else:
            # Extract ID from option string (e.g., "#123 Vendor Material Name")
            try:
                spool_id = int(option.split(" ")[0].replace("#", ""))
                async with session.post(
                    f"{self._url}/api/spools",
                    json={"spoolId": spool_id, "trayId": self._tray_entity_id}
                ) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to assign spool: %s", await response.text())
            except Exception as err:
                _LOGGER.error("Error parsing spool ID from option %s: %s", option, err)

        await self.coordinator.async_request_refresh()
