"""API Client for ASUSTOR NAS SNMP integration."""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import Any

from pysnmp.error import PySnmpError
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    get_cmd,
    walk_cmd,
)

from homeassistant.core import HomeAssistant

from ..const import DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)


class AsustorNasApiClientError(Exception):
    """Base exception for API errors."""


class AsustorNasConnectionError(AsustorNasApiClientError):
    """Exception for connection errors."""


class AsustorNasAuthenticationError(AsustorNasApiClientError):
    """Exception for authentication errors."""


class AsustorNasApiClient:
    """API Client for ASUSTOR NAS via SNMP."""

    def __init__(self, hass: HomeAssistant, host: str, community: str, port: int = DEFAULT_PORT) -> None:
        """Initialize the API client."""
        self.hass = hass
        self.host = host
        self.community = community
        self.port = port
        # Do NOT initialize SnmpEngine here, as it performs blocking I/O (reads MIB files).
        # It must be initialized inside the executor thread.

    def _get_data_sync(self, oids: list[str]) -> dict[str, Any]:
        """Get data for specific OIDs synchronously."""

        async def _run_async() -> dict[str, Any]:
            # Initialize engine in the executor thread to avoid blocking the event loop
            snmp_engine = SnmpEngine()
            transport = await UdpTransportTarget.create((self.host, self.port), timeout=5, retries=1)

            error_indication, error_status, error_index, var_binds = await get_cmd(
                snmp_engine,
                CommunityData(self.community, mpModel=1),  # mpModel=1 means SNMPv2c
                transport,
                ContextData(),
                *[ObjectType(ObjectIdentity(oid)) for oid in oids],
            )

            if error_indication:
                err_str = str(error_indication)
                if "authorizationError" in err_str or "unknownCommunityName" in err_str:
                    raise AsustorNasAuthenticationError(f"SNMP Authentication error: {err_str}")
                raise AsustorNasConnectionError(f"SNMP error: {err_str}")

            if error_status:
                raise AsustorNasApiClientError(
                    f"SNMP error status: {error_status.prettyPrint()} at "
                    f"{(error_index and var_binds[int(error_index) - 1][0]) or '?'}"
                )

            result = {}
            for name, val in var_binds:
                # Use str(name) to get the pure numeric OID string (e.g., "1.3.6.1.4.1.44738.2.1.0")
                # instead of name.prettyPrint() which might return "SNMPv2-SMI::enterprises..."
                result[str(name)] = val.prettyPrint()

            return result

        try:
            return asyncio.run(_run_async())
        except (TimeoutError, socket.gaierror, PySnmpError) as err:
            raise AsustorNasConnectionError(f"Connection error to {self.host}: {err}") from err
        except Exception as err:
            if isinstance(err, AsustorNasApiClientError):
                raise
            raise AsustorNasApiClientError(f"Unexpected error: {err}") from err

    def _walk_table_sync(self, base_oid: str) -> dict[str, Any]:
        """Walk an SNMP table synchronously and return the results."""

        async def _run_async() -> dict[str, Any]:
            # Initialize engine in the executor thread to avoid blocking the event loop
            snmp_engine = SnmpEngine()
            transport = await UdpTransportTarget.create((self.host, self.port), timeout=5, retries=1)
            result = {}

            async for error_indication, error_status, error_index, var_binds in walk_cmd(
                snmp_engine,
                CommunityData(self.community, mpModel=1),
                transport,
                ContextData(),
                ObjectType(ObjectIdentity(base_oid)),
                lexicographicMode=False,
                lookupMib=False,
            ):

                if error_indication:
                    raise AsustorNasConnectionError(f"SNMP error: {error_indication}")

                if error_status:
                    raise AsustorNasApiClientError(
                        f"SNMP error status: {error_status.prettyPrint()} at "
                        f"{(error_index and var_binds[int(error_index) - 1][0]) or '?'}"
                    )

                for name, val in var_binds:
                    result[str(name)] = val.prettyPrint()

            return result

        try:
            return asyncio.run(_run_async())
        except (TimeoutError, socket.gaierror, PySnmpError) as err:
            raise AsustorNasConnectionError(f"Connection error walking {base_oid} on {self.host}: {err}") from err
        except Exception as err:
            if isinstance(err, AsustorNasApiClientError):
                raise
            raise AsustorNasApiClientError(f"Unexpected error walking {base_oid}: {err}") from err

    async def async_get_data(self, oids: list[str]) -> dict[str, Any]:
        """Get data for specific OIDs asynchronously."""
        return await self.hass.async_add_executor_job(self._get_data_sync, oids)

    async def async_walk_table(self, base_oid: str) -> dict[str, Any]:
        """Walk an SNMP table asynchronously and return the results."""
        return await self.hass.async_add_executor_job(self._walk_table_sync, base_oid)
