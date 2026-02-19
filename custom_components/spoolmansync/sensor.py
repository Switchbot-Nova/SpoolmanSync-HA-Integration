import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    """Set up SpoolmanSync sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    printers = coordinator.data.get("printers", [])
    for printer in printers:
        printer_name = printer.get("name", "Printer")
        for ams in printer.get("ams_units", []):
            ams_name = ams.get("name", "AMS")
            for tray in ams.get("trays", []):
                entities.append(
                    SpoolmanTraySensor(
                        coordinator,
                        printer_name,
                        ams_name,
                        tray,
                    )
                )
        
        if printer.get("external_spool"):
            entities.append(
                SpoolmanTraySensor(
                    coordinator,
                    printer_name,
                    "External",
                    printer["external_spool"],
                )
            )

    async_add_entities(entities)

class SpoolmanTraySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Spoolman Tray sensor showing assigned spool info."""

    def __init__(self, coordinator, printer_name, ams_name, tray):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._printer_name = printer_name
        self._ams_name = ams_name
        self._tray_entity_id = tray["entity_id"]
        self._tray_number = tray["tray_number"]
        
        self._attr_unique_id = f"spoolmansync_sensor_{self._tray_entity_id}"
        self._attr_name = f"{ams_name} Tray {self._tray_number} Info"
        if ams_name == "External":
             self._attr_name = "External Tray Info"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, printer_name)},
            name=printer_name,
            manufacturer="SpoolmanSync",
            model="Bambu Lab Printer",
        )

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        spools = self.coordinator.data.get("spools", [])
        for spool in spools:
            active_tray = spool.get("extra", {}).get("active_tray")
            if active_tray:
                import json
                try:
                    clean_tray_id = json.loads(active_tray)
                    if clean_tray_id == self._tray_entity_id:
                        return f"Spool #{spool['id']}"
                except Exception:
                    if active_tray.strip('"') == self._tray_entity_id:
                        return f"Spool #{spool['id']}"
        return "No Spool"

    @property
    def extra_state_attributes(self) -> dict:
        """Return entity specific state attributes."""
        spools = self.coordinator.data.get("spools", [])
        for spool in spools:
            active_tray = spool.get("extra", {}).get("active_tray")
            if active_tray:
                import json
                try:
                    clean_tray_id = json.loads(active_tray)
                    if clean_tray_id == self._tray_entity_id:
                        return {
                            "spool_id": spool["id"],
                            "vendor": spool.get("filament", {}).get("vendor", {}).get("name"),
                            "material": spool.get("filament", {}).get("material"),
                            "filament_name": spool.get("filament", {}).get("name"),
                            "remaining_weight": spool.get("remaining_weight"),
                            "color_hex": spool.get("filament", {}).get("color_hex"),
                        }
                except Exception:
                    if active_tray.strip('"') == self._tray_entity_id:
                        return {
                            "spool_id": spool["id"],
                            "vendor": spool.get("filament", {}).get("vendor", {}).get("name"),
                            "material": spool.get("filament", {}).get("material"),
                            "filament_name": spool.get("filament", {}).get("name"),
                            "remaining_weight": spool.get("remaining_weight"),
                            "color_hex": spool.get("filament", {}).get("color_hex"),
                        }
        return {}
