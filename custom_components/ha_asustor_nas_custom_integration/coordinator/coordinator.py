"""Coordinator for ASUSTOR NAS SNMP integration."""

from contextlib import suppress
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..api import AsustorNasApiClient, AsustorNasAuthenticationError, AsustorNasConnectionError
from ..const import (
    DOMAIN,
    OID_ASUSTOR_CPU_CORE_USAGE_BASE,
    OID_ASUSTOR_CPU_MODEL,
    OID_ASUSTOR_FAN_RPM_BASE,
    OID_ASUSTOR_MODEL,
    OID_ASUSTOR_TEMP_CPU,
    OID_ASUSTOR_TEMP_SYS,
    OID_MEM_AVAIL,
    OID_MEM_BUFFER,
    OID_MEM_CACHED,
    OID_MEM_TOTAL,
)

_LOGGER = logging.getLogger(__name__)


def _decode_hex_string(hex_str: str) -> str:
    """Decode a hex string returned by SNMP."""
    hex_str = hex_str.strip()

    hex_str = hex_str.removeprefix("0x")

    normalized = "".join(hex_str.split())

    if normalized and len(normalized) % 2 == 0 and all(char in "0123456789abcdefABCDEF" for char in normalized):
        try:
            return bytes.fromhex(normalized).decode("utf-8", errors="replace").rstrip("\x00").strip()
        except ValueError:
            return hex_str

    return hex_str


class AsustorNasDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching ASUSTOR NAS data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AsustorNasApiClient,
        update_interval: int,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # 1. Fetch static and single-row data
            static_oids = [
                OID_ASUSTOR_MODEL,
                OID_ASUSTOR_CPU_MODEL,
                OID_ASUSTOR_TEMP_CPU,
                OID_ASUSTOR_TEMP_SYS,
                OID_MEM_TOTAL,
                OID_MEM_AVAIL,
                OID_MEM_BUFFER,
                OID_MEM_CACHED,
            ]
            static_data = await self.client.async_get_data(static_oids)

            # 2. Fetch tabular data (walks)
            cpu_cores_data = await self.client.async_walk_table(OID_ASUSTOR_CPU_CORE_USAGE_BASE)
            fans_data = await self.client.async_walk_table(OID_ASUSTOR_FAN_RPM_BASE)

            # 3. Process and aggregate data
            return self._process_data(static_data, cpu_cores_data, fans_data)

        except AsustorNasAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except AsustorNasConnectionError as exception:
            raise UpdateFailed(exception) from exception

    def _process_data(
        self,
        static_data: dict[str, Any],
        cpu_cores_data: dict[str, Any],
        fans_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Process raw SNMP data into a structured dictionary."""
        processed: dict[str, Any] = {
            "model": static_data.get(OID_ASUSTOR_MODEL, "Unknown"),
            "cpu_model": _decode_hex_string(str(static_data.get(OID_ASUSTOR_CPU_MODEL, ""))),
            "temperatures": {},
            "memory": {},
            "cpu_cores": {},
            "fans": {},
        }

        # Temperatures
        if OID_ASUSTOR_TEMP_CPU in static_data:
            with suppress(ValueError):
                processed["temperatures"]["cpu"] = int(static_data[OID_ASUSTOR_TEMP_CPU])

        if OID_ASUSTOR_TEMP_SYS in static_data:
            with suppress(ValueError):
                processed["temperatures"]["system"] = int(static_data[OID_ASUSTOR_TEMP_SYS])

        # Memory (Standard Linux UCD-SNMP-MIB)
        try:
            mem_total = int(static_data.get(OID_MEM_TOTAL, 0))
            mem_avail = int(static_data.get(OID_MEM_AVAIL, 0))
            mem_buffer = int(static_data.get(OID_MEM_BUFFER, 0))
            mem_cached = int(static_data.get(OID_MEM_CACHED, 0))

            if mem_total > 0:
                mem_used = max(mem_total - (mem_avail + mem_buffer + mem_cached), 0)
                mem_usage_percent = (mem_used / mem_total) * 100

                # Convert kB to MB for Home Assistant native DATA_SIZE handling
                mem_total_mb = mem_total / 1024
                mem_used_mb = mem_used / 1024

                processed["memory"] = {
                    "total_mb": round(mem_total_mb, 2),
                    "used_mb": round(mem_used_mb, 2),
                    "usage_percent": round(mem_usage_percent, 2),
                }
        except ValueError:
            _LOGGER.warning("Failed to parse memory data")

        # CPU Cores
        # Sort OIDs to ensure stable ordering (Core 1, Core 2, etc.)
        # We sort by the numeric value of the last segment of the OID to map
        # raw SNMP indices (e.g. 196608) to logical indices (e.g. 1).
        sorted_cpu_items = []
        for oid, value in cpu_cores_data.items():
            try:
                # Extract last part as integer for sorting
                idx = int(oid.split(".")[-1])
                sorted_cpu_items.append((idx, value))
            except ValueError:
                continue

        sorted_cpu_items.sort(key=lambda x: x[0])

        for i, (_, value) in enumerate(sorted_cpu_items, start=1):
            processed["cpu_cores"][str(i)] = int(value)

        # Fans
        # Sort OIDs to ensure stable ordering
        sorted_fan_items = []
        for oid, value in fans_data.items():
            try:
                idx = int(oid.split(".")[-1])
                sorted_fan_items.append((idx, value))
            except ValueError:
                continue

        sorted_fan_items.sort(key=lambda x: x[0])

        for i, (_, value) in enumerate(sorted_fan_items, start=1):
            processed["fans"][str(i)] = int(value)

        return processed
