"""API Client for ASUSTOR NAS SNMP integration."""

from __future__ import annotations

import logging
from typing import Any

import pysnmp.hlapi as hlapi

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

    def __init__(
        self, hass: HomeAssistant, host: str, community: str, port: int = DEFAULT_PORT
    ) -> None:
        """Initialize the API client."""
        self.hass = hass
        self.host = host
        self.community = community
        self.port = port

    def _get_data_sync(self, oids: list[str]) -> dict[str, Any]:
        """Get data for specific OIDs synchronously."""
        try:
            # Create engine locally in the thread to avoid sharing across threads
            snmp_engine = hlapi.SnmpEngine()
            
            iterator = hlapi.getCmd(
                snmp_engine,
                hlapi.CommunityData(self.community, mpModel=1),  # mpModel=1 means SNMPv2c
                hlapi.UdpTransportTarget((self.host, self.port), timeout=5, retries=1),
                hlapi.ContextData(),
                *[hlapi.ObjectType(hlapi.ObjectIdentity(oid)) for oid in oids],
            )

            error_indication, error_status, error_index, var_binds = next(iterator)

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

        except Exception as err:
            if isinstance(err, AsustorNasApiClientError):
                raise
            raise AsustorNasApiClientError(f"Unexpected error: {err}") from err

    def _walk_table_sync(self, base_oid: str) -> dict[str, Any]:
        """Walk an SNMP table synchronously and return the results."""
        try:
            snmp_engine = hlapi.SnmpEngine()
            result = {}
            
            iterator = hlapi.nextCmd(
                snmp_engine,
                hlapi.CommunityData(self.community, mpModel=1),
                hlapi.UdpTransportTarget((self.host, self.port), timeout=5, retries=1),
                hlapi.ContextData(),
                hlapi.ObjectType(hlapi.ObjectIdentity(base_oid)),
                lexicographicMode=False,
            )

            for error_indication, error_status, error_index, var_binds in iterator:
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
