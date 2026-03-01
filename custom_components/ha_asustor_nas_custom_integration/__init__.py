"""
Custom integration to integrate ASUSTOR NAS with Home Assistant.
"""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant

from .api import AsustorNasApiClient
from .const import CONF_COMMUNITY, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL
from .coordinator import AsustorNasDataUpdateCoordinator
from .data import AsustorNasConfigEntry, AsustorNasData

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AsustorNasConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    # Initialize client
    client = AsustorNasApiClient(
        host=entry.data[CONF_HOST],
        community=entry.data[CONF_COMMUNITY],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
    )

    # Initialize coordinator
    coordinator = AsustorNasDataUpdateCoordinator(
        hass=hass,
        client=client,
        update_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    # Store runtime data
    entry.runtime_data = AsustorNasData(
        client=client,
        coordinator=coordinator,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AsustorNasConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
