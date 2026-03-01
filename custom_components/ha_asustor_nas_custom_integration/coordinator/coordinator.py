"""Coordinator for ASUSTOR NAS SNMP integration."""

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..api import (
    AsustorNasApiClient,
    AsustorNasAuthenticationError,
    AsustorNasConnectionError,
)
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
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    try:
        if " " in hex_str:
            return bytes.fromhex(hex_str).decode("utf-8", errors="replace").strip()
        return hex_str.strip()
    except ValueError:
        return hex_str.strip()


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
            cpu_cores_data = await self.client.async_walk_table(
                OID_ASUSTOR_CPU_CORE_USAGE_BASE
            )
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
            "cpu_model": _decode_hex_string(
                str(static_data.get(OID_ASUSTOR_CPU_MODEL, ""))
            ),
            "temperatures": {},
            "memory": {},
            "cpu_cores": {},
            "fans": {},
        }

        # Temperatures
        if OID_ASUSTOR_TEMP_CPU in static_data:
            try:
                processed["temperatures"]["cpu"] = int(
                    static_data[OID_ASUSTOR_TEMP_CPU]
                )
            except ValueError:
                pass

        if OID_ASUSTOR_TEMP_SYS in static_data:
            try:
                processed["temperatures"]["system"] = int(
                    static_data[OID_ASUSTOR_TEMP_SYS]
                )
            except ValueError:
                pass

        # Memory (Standard Linux UCD-SNMP-MIB)
        try:
            mem_total = int(static_data.get(OID_MEM_TOTAL, 0))
            mem_avail = int(static_data.get(OID_MEM_AVAIL, 0))
            mem_buffer = int(static_data.get(OID_MEM_BUFFER, 0))
            mem_cached = int(static_data.get(OID_MEM_CACHED, 0))

            if mem_total > 0:
                # Convert kB to MB for easier display
                mem_total_mb = mem_total / 1024
                mem_avail_mb = mem_avail / 1024
                mem_buffer_mb = mem_buffer / 1024
                mem_cached_mb = mem_cached / 1024

                mem_used_mb = mem_total_mb - (
                    mem_avail_mb + mem_buffer_mb + mem_cached_mb
                )
                mem_usage_percent = (mem_used_mb / mem_total_mb) * 100

                processed["memory"] = {
                    "total_mb": round(mem_total_mb, 2),
                    "used_mb": round(mem_used_mb, 2),
                    "usage_percent": round(mem_usage_percent, 2),
                }
        except ValueError:
            _LOGGER.warning("Failed to parse memory data")

        # CPU Cores
        for oid, value in cpu_cores_data.items():
            try:
                # Extract the last part of the OID as the core index (e.g., ...2.3.1.2.0 -> 0)
                core_index = oid.split(".")[-1]
                processed["cpu_cores"][core_index] = int(value)
            except ValueError:
                pass

        # Fans
        for oid, value in fans_data.items():
            try:
                # Extract the last part of the OID as the fan index (e.g., ...2.4.1.2.1 -> 1)
                fan_index = oid.split(".")[-1]
                processed["fans"][fan_index] = int(value)
            except ValueError:
                pass

        return processed
