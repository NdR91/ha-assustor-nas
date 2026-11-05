"""Config flow for ASUSTOR NAS SNMP integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from ..api import AsustorNasApiClient, AsustorNasAuthenticationError, AsustorNasConnectionError
from ..const import (
    CONF_COMMUNITY,
    DEFAULT_COMMUNITY,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OID_ASUSTOR_MODEL,
    OID_MAC_ADDRESS_BASE,
)
from ..volume_identity import volume_migration_conflicts

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_COMMUNITY, default=DEFAULT_COMMUNITY): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    client = AsustorNasApiClient(
        hass=hass,
        host=data[CONF_HOST],
        community=data[CONF_COMMUNITY],
        port=data[CONF_PORT],
    )

    # Test connection by fetching the NAS model
    try:
        result = await client.async_get_data([OID_ASUSTOR_MODEL])
    except AsustorNasAuthenticationError as err:
        raise InvalidAuth from err
    except AsustorNasConnectionError as err:
        raise CannotConnect from err

    model = result.get(OID_ASUSTOR_MODEL)
    if not model:
        raise CannotConnect("Failed to retrieve NAS model")

    # Fetch MAC addresses to use as unique ID
    try:
        mac_results = await client.async_walk_table(OID_MAC_ADDRESS_BASE)
    except (AsustorNasAuthenticationError, AsustorNasConnectionError) as err:
        raise CannotConnect from err

    # Find the first valid MAC address
    mac_address = None
    for mac in mac_results.values():
        if not mac:
            continue

        # Format MAC address if it's returned as hex string
        if isinstance(mac, str) and ":" in mac:
            mac_address = mac
            break
        if isinstance(mac, str) and len(mac) == 12:
            # Format 001122334455 to 00:11:22:33:44:55
            mac_address = ":".join(mac[i : i + 2] for i in range(0, 12, 2))
            break
        if isinstance(mac, bytes):
            mac_address = ":".join(f"{b:02x}" for b in mac)
            break
        if isinstance(mac, str) and mac.startswith("0x") and len(mac) >= 14:
            # Handle hex string like 0x001122334455
            clean_mac = mac[2:]
            mac_address = ":".join(clean_mac[i : i + 2] for i in range(0, 12, 2))
            break

    if not mac_address:
        # Fallback to host if no MAC address is found
        mac_address = data[CONF_HOST]

    return {"title": f"ASUSTOR NAS ({model})", "mac": mac_address}


class HomeAssistantAsustorNASCustomConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ASUSTOR NAS."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the options flow for explicit volume migration choices."""
        return AsustorNasOptionsFlowHandler()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect as err:
                _LOGGER.error("Connection failed: %s", err)
                errors["base"] = "cannot_connect"
            except InvalidAuth as err:
                _LOGGER.error("Auth failed: %s", err)
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["mac"])
                self._abort_if_unique_id_configured()

                # Store the MAC address in the config entry data
                user_input[CONF_MAC] = info["mac"]

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)


class AsustorNasOptionsFlowHandler(OptionsFlow):
    """Handle explicit choices for ambiguous legacy volume sensors."""

    async def async_step_init(self, user_input: dict[str, str] | None = None) -> ConfigFlowResult:
        """Show one selector for each ambiguous legacy volume metric."""
        entry = self.config_entry
        coordinator = getattr(getattr(entry, "runtime_data", None), "coordinator", None)
        volumes = coordinator.data.get("volumes", {}) if coordinator else {}
        conflicts = volume_migration_conflicts(self.hass, entry.entry_id, volumes)

        if user_input is not None:
            options, errors = merge_volume_migration_options(entry.options, conflicts, user_input)
            if not errors:
                return self.async_create_entry(title="", data=options)

        schema_fields = {}
        for option_key, candidates in conflicts.items():
            options = [{"label": entity_id, "value": unique_id} for entity_id, unique_id in candidates]
            current = entry.options.get("volume_migrations", {}).get(option_key)
            field_name = _volume_conflict_label(option_key)
            field = (
                vol.Required(field_name, default=current)
                if current in {item["value"] for item in options}
                else vol.Required(field_name)
            )
            schema_fields[field] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_fields),
            errors=errors if user_input is not None else {},
        )


def _volume_conflict_label(option_key: str) -> str:
    """Make dynamic conflict fields readable in the options form."""
    return option_key.removeprefix("volume_").replace("_", " ")


def merge_volume_migration_options(
    existing_options: dict[str, Any],
    conflicts: dict[str, list[tuple[str, str]]],
    user_input: dict[str, str],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate explicit conflict selections without dropping other options."""
    migrations = dict(existing_options.get("volume_migrations", {}))
    errors: dict[str, str] = {}
    for option_key, candidates in conflicts.items():
        field_name = _volume_conflict_label(option_key)
        selection = user_input.get(field_name)
        if selection not in {unique_id for _, unique_id in candidates}:
            errors[field_name] = "invalid_selection"
        else:
            migrations[option_key] = selection
    options = dict(existing_options)
    options["volume_migrations"] = migrations
    return options, errors


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
