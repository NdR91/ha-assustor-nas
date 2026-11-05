"""Home Assistant Repairs issues for volume identity conflicts."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, issue_registry as ir

from .const import DOMAIN
from .data import AsustorNasConfigEntry
from .volume_identity import volume_entity_key

ISSUE_ID_PREFIX = "volume_migration_"
_ISSUE_DATA_CONFLICTS = "conflicts"


def async_update_volume_migration_issue(
    hass: HomeAssistant,
    entry: AsustorNasConfigEntry,
    blocked_metrics: set[tuple[str, str]],
) -> None:
    """Create, update, or clear the per-entry issue after checking registry state."""
    issue_registry = ir.async_get(hass)
    issue_id = f"{ISSUE_ID_PREFIX}{entry.entry_id}"
    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    unresolved = set(blocked_metrics)

    # A previous conflict remains unresolved until a stable target entity is
    # present. Missing/offline volume data therefore cannot close the issue.
    if issue and issue.data and (stored_conflicts := issue.data.get(_ISSUE_DATA_CONFLICTS)):
        unresolved.update(
            tuple(item.split(":", maxsplit=1)) for item in str(stored_conflicts).split(",") if ":" in item
        )

    registry = er.async_get(hass)
    unresolved = {
        (identity, metric)
        for identity, metric in unresolved
        if not registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{volume_entity_key(identity, metric)}")
    }

    if not unresolved:
        if issue:
            ir.async_delete_issue(hass, DOMAIN, issue_id)
        return

    conflicts = ", ".join(f"{identity} {metric.replace('_', ' ')}" for identity, metric in sorted(unresolved))
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        data={_ISSUE_DATA_CONFLICTS: ",".join(f"{identity}:{metric}" for identity, metric in sorted(unresolved))},
        is_fixable=False,
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="volume_migration_conflict",
        translation_placeholders={"conflicts": conflicts, "nas_name": entry.title},
    )


def async_remove_volume_migration_issue(hass: HomeAssistant, entry: AsustorNasConfigEntry) -> None:
    """Delete the repair only when its config entry is permanently removed."""
    ir.async_delete_issue(hass, DOMAIN, f"{ISSUE_ID_PREFIX}{entry.entry_id}")
