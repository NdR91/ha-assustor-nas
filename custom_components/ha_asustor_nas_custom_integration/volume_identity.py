"""Stable identities for ASUSTOR volumes."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_VOLUME_MOUNT = re.compile(r"^/?volume(\d+)$")


def volume_identity(mount: str) -> str | None:
    """Return the stable identity for a root volume mount point."""
    match = _VOLUME_MOUNT.fullmatch(mount.strip().rstrip("/"))
    return f"volume{match.group(1)}" if match else None


def volume_entity_key(identity: str, metric: str) -> str:
    """Build a volume sensor key independent of the SNMP table row index."""
    return f"volume_{identity}_{metric}"


def volume_value_for_mount(data: dict[str, Any], mount: str, metric: str) -> Any | None:
    """Return a mount metric only when duplicate rows agree on its value."""
    values = [
        volume[metric]
        for volume in data.get("volumes", {}).values()
        if volume.get("name") == mount and metric in volume
    ]
    if not values or any(value != values[0] for value in values[1:]):
        return None
    return values[0]


def volume_metric_from_name(original_name: str | None, identity: str) -> str | None:
    """Identify the metric encoded in a legacy sensor's original name."""
    if not original_name:
        return None
    for suffix, metric in (
        (" Total", "total"),
        (" Used", "used"),
        (" Free", "free"),
        (" Usage", "usage_percent"),
    ):
        if original_name == f"{identity}{suffix}":
            return metric
    return None


def legacy_volume_candidates(
    entries: list[tuple[str, str | None, str]],
    identity: str,
    metric: str,
) -> list[str]:
    """Find legacy IDs by original name/metric without trusting old row indices."""
    return [
        unique_id
        for unique_id, original_name, entry_unique_id in entries
        if volume_metric_from_name(original_name, identity) == metric
        and re.search(rf"_volume_\d+_{re.escape(metric)}$", entry_unique_id)
    ]


def volume_migration_option_key(identity: str, metric: str) -> str:
    """Return the config option key for an explicit legacy selection."""
    return volume_entity_key(identity, metric)


def migrate_volume_entities(
    hass: HomeAssistant,
    entry_id: str,
    volumes: dict[str, dict[str, Any]],
    selected_legacy_ids: dict[str, str] | None = None,
) -> set[tuple[str, str]]:
    """Migrate unique legacy sensors and return metrics blocked by ambiguity."""
    registry = er.async_get(hass)
    identities = {
        identity
        for volume in volumes.values()
        if (identity := volume_identity(str(volume.get("name", "")))) is not None
    }
    entries = er.async_entries_for_config_entry(registry, entry_id)
    blocked: set[tuple[str, str]] = set()
    selected_legacy_ids = selected_legacy_ids or {}
    entry_tuples = [(item.entity_id, item.original_name, item.unique_id) for item in entries]

    for identity in identities:
        for metric in ("total", "used", "free", "usage_percent"):
            target_unique_id = f"{entry_id}_{volume_entity_key(identity, metric)}"
            if registry.async_get_entity_id("sensor", DOMAIN, target_unique_id):
                continue
            candidate_ids = set(legacy_volume_candidates(entry_tuples, identity, metric))
            candidates = [item for item in entries if item.entity_id in candidate_ids]
            if len(candidates) > 1:
                selection = selected_legacy_ids.get(volume_migration_option_key(identity, metric))
                selected = [item for item in candidates if item.unique_id == selection]
                if len(selected) == 1:
                    registry.async_update_entity(selected[0].entity_id, new_unique_id=target_unique_id)
                else:
                    blocked.add((identity, metric))
                    _LOGGER.warning(
                        "Multiple legacy %s sensors match %s; no entity was changed. Choose the entity to keep in the integration options.",
                        metric,
                        identity,
                    )
            elif len(candidates) == 1:
                registry.async_update_entity(candidates[0].entity_id, new_unique_id=target_unique_id)

    return blocked


def volume_migration_conflicts(
    hass: HomeAssistant, entry_id: str, volumes: dict[str, dict[str, Any]]
) -> dict[str, list[tuple[str, str]]]:
    """Return ambiguous legacy choices as option-key to (entity ID, unique ID)."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, entry_id)
    entry_tuples = [(item.entity_id, item.original_name, item.unique_id) for item in entries]
    identities = {
        identity
        for volume in volumes.values()
        if (identity := volume_identity(str(volume.get("name", "")))) is not None
    }
    conflicts: dict[str, list[tuple[str, str]]] = {}
    for identity in identities:
        for metric in ("total", "used", "free", "usage_percent"):
            target = registry.async_get_entity_id("sensor", DOMAIN, f"{entry_id}_{volume_entity_key(identity, metric)}")
            if target:
                continue
            candidates = set(legacy_volume_candidates(entry_tuples, identity, metric))
            if len(candidates) > 1:
                conflicts[volume_migration_option_key(identity, metric)] = [
                    (item.entity_id, item.unique_id) for item in entries if item.entity_id in candidates
                ]
    return conflicts
