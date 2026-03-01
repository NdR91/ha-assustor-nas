"""API Client for ASUSTOR NAS SNMP integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pysnmp.hlapi.asyncio import (  # type: ignore[import-untyped]
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
    nextCmd,
)

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

    def __init__(self, host: str, community: str, port: int = DEFAULT_PORT) -> None:
        """Initialize the API client."""
        self.host = host
        self.community = community
        self.port = port
        self._snmp_engine = SnmpEngine()

    async def async_get_data(self, oids: list[str]) -> dict[str, Any]:
        """Get data for specific OIDs."""
        try:
            async with asyncio.timeout(10):
                error_indication, error_status, error_index, var_binds = await getCmd(
                    self._snmp_engine,
                    CommunityData(self.community, mpModel=1),  # mpModel=1 means SNMPv2c
                    UdpTransportTarget((self.host, self.port), timeout=5, retries=1),
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
                        f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
                    )

                result = {}
                for name, val in var_binds:
                    result[name.prettyPrint()] = val.prettyPrint()

                return result

        except TimeoutError as err:
            raise AsustorNasConnectionError(f"Timeout connecting to {self.host}") from err
        except Exception as err:
            if isinstance(err, AsustorNasApiClientError):
                raise
            raise AsustorNasApiClientError(f"Unexpected error: {err}") from err

    async def async_walk_table(self, base_oid: str) -> dict[str, Any]:
        """Walk an SNMP table and return the results."""
        try:
            result = {}
            async with asyncio.timeout(15):
                # nextCmd is an async generator in pysnmp asyncio API
                async for error_indication, error_status, error_index, var_binds in nextCmd(
                    self._snmp_engine,
                    CommunityData(self.community, mpModel=1),
                    UdpTransportTarget((self.host, self.port), timeout=5, retries=1),
                    ContextData(),
                    ObjectType(ObjectIdentity(base_oid)),
                    lexicographicMode=False,
                ):
                    if error_indication:
                        raise AsustorNasConnectionError(f"SNMP error: {error_indication}")

                    if error_status:
                        raise AsustorNasApiClientError(
                            f"SNMP error status: {error_status.prettyPrint()} at "
                            f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
                        )

                    for name, val in var_binds:
                        result[name.prettyPrint()] = val.prettyPrint()

            return result

        except TimeoutError as err:
            raise AsustorNasConnectionError(f"Timeout walking table {base_oid} on {self.host}") from err
        except Exception as err:
            if isinstance(err, AsustorNasApiClientError):
                raise
            raise AsustorNasApiClientError(f"Unexpected error walking {base_oid}: {err}") from err
