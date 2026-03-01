"""Data classes for ASUSTOR NAS SNMP integration."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .api import AsustorNasApiClient
from .coordinator import AsustorNasDataUpdateCoordinator


@dataclass
class AsustorNasData:
    """Data for the ASUSTOR NAS integration."""

    client: AsustorNasApiClient
    coordinator: AsustorNasDataUpdateCoordinator


type AsustorNasConfigEntry = ConfigEntry[AsustorNasData]
