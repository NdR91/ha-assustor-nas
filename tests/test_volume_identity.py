"""Tests for stable volume identities and safe legacy matching."""

from types import SimpleNamespace

from custom_components.ha_asustor_nas_custom_integration import volume_identity as volume_identity_module
from custom_components.ha_asustor_nas_custom_integration.config_flow_handler.config_flow import (
    merge_volume_migration_options,
)
from custom_components.ha_asustor_nas_custom_integration.volume_identity import (
    legacy_volume_candidates,
    migrate_volume_entities,
    volume_entity_key,
    volume_identity,
    volume_migration_conflicts,
    volume_value_for_mount,
)


def test_mount_identity_is_independent_of_snmp_row_index() -> None:
    assert volume_identity("/volume2") == "volume2"
    assert volume_entity_key(volume_identity("/volume2"), "used") == "volume_volume2_used"


def test_legacy_matching_uses_original_name_not_recycled_row_index() -> None:
    entries = [
        ("sensor.old", "volume2 Used", "config_volume_51_used"),
        ("sensor.other", "volume2 Total", "config_volume_18_total"),
        ("sensor.also_old", "volume2 Used", "config_volume_56_used"),
        ("sensor.wrong_metric", "volume2 Free", "config_volume_17_used"),
    ]

    assert legacy_volume_candidates(entries, "volume2", "used") == ["sensor.old", "sensor.also_old"]


def test_all_ambiguous_legacy_entities_are_reported_without_selection() -> None:
    entries = [(f"sensor.legacy_{index}", "volume1 Used", f"config_volume_{index}_used") for index in (3, 8, 11)]

    assert legacy_volume_candidates(entries, "volume1", "used") == [
        "sensor.legacy_3",
        "sensor.legacy_8",
        "sensor.legacy_11",
    ]


def test_non_volume_mount_has_no_stable_identity() -> None:
    assert volume_identity("/share") is None


def test_duplicate_mount_rows_with_conflicting_values_are_unavailable() -> None:
    data = {
        "volumes": {
            "51": {"name": "/volume1", "used_bytes": 100},
            "54": {"name": "/volume1", "used_bytes": 140},
        }
    }

    assert volume_value_for_mount(data, "/volume1", "used_bytes") is None


def test_duplicate_mount_rows_with_same_values_remain_available() -> None:
    data = {
        "volumes": {
            "51": {"name": "/volume1", "used_bytes": 100},
            "54": {"name": "/volume1", "used_bytes": 100},
        }
    }

    assert volume_value_for_mount(data, "/volume1", "used_bytes") == 100


class FakeEntityRegistry:
    """Small registry double matching the Home Assistant migration API."""

    def __init__(self, entries):
        self.entries = entries
        self.updated = []

    def async_get_entity_id(self, domain, platform, unique_id):
        return next((item.entity_id for item in self.entries if item.unique_id == unique_id), None)

    def async_update_entity(self, entity_id, *, new_unique_id):
        item = next(item for item in self.entries if item.entity_id == entity_id)
        item.unique_id = new_unique_id
        self.updated.append((entity_id, new_unique_id))


def fake_entry(entity_id, unique_id, original_name):
    """Build a legacy registry entry double."""
    return SimpleNamespace(entity_id=entity_id, unique_id=unique_id, original_name=original_name)


def test_migration_with_one_candidate_preserves_entity_id_when_row_index_changes(monkeypatch) -> None:
    entry = fake_entry("sensor.volume2_used_custom", "entry_volume_51_used", "volume2 Used")
    registry = FakeEntityRegistry([entry])
    monkeypatch.setattr(volume_identity_module.er, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        volume_identity_module.er, "async_entries_for_config_entry", lambda registry, entry_id: registry.entries
    )

    blocked = migrate_volume_entities(object(), "entry", {"54": {"name": "/volume2"}})

    assert blocked == set()
    assert entry.entity_id == "sensor.volume2_used_custom"
    assert entry.unique_id == "entry_volume_volume2_used"


def test_migration_blocks_all_ambiguous_candidates_without_mutating(monkeypatch) -> None:
    entries = [
        fake_entry(f"sensor.legacy_{index}", f"entry_volume_{index}_used", "volume1 Used") for index in (51, 54, 56)
    ]
    registry = FakeEntityRegistry(entries)
    monkeypatch.setattr(volume_identity_module.er, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        volume_identity_module.er, "async_entries_for_config_entry", lambda registry, entry_id: registry.entries
    )

    blocked = migrate_volume_entities(object(), "entry", {"54": {"name": "/volume1"}})

    assert blocked == {("volume1", "used")}
    assert registry.updated == []
    assert [item.unique_id for item in entries] == [f"entry_volume_{index}_used" for index in (51, 54, 56)]


def test_migration_honors_explicit_legacy_entity_selection(monkeypatch) -> None:
    entries = [
        fake_entry(f"sensor.legacy_{index}", f"entry_volume_{index}_used", "volume1 Used") for index in (51, 54, 56)
    ]
    registry = FakeEntityRegistry(entries)
    monkeypatch.setattr(volume_identity_module.er, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        volume_identity_module.er, "async_entries_for_config_entry", lambda registry, entry_id: registry.entries
    )

    blocked = migrate_volume_entities(
        object(), "entry", {"54": {"name": "/volume1"}}, {"volume_volume1_used": "entry_volume_54_used"}
    )

    assert blocked == set()
    assert registry.updated == [("sensor.legacy_54", "entry_volume_volume1_used")]
    assert entries[0].unique_id == "entry_volume_51_used"
    assert entries[1].entity_id == "sensor.legacy_54"
    assert entries[2].unique_id == "entry_volume_56_used"


def test_migration_skips_conflict_when_stable_target_already_exists(monkeypatch) -> None:
    entries = [
        fake_entry("sensor.current", "entry_volume_volume1_used", "volume1 Used"),
        fake_entry("sensor.legacy_51", "entry_volume_51_used", "volume1 Used"),
        fake_entry("sensor.legacy_54", "entry_volume_54_used", "volume1 Used"),
    ]
    registry = FakeEntityRegistry(entries)
    monkeypatch.setattr(volume_identity_module.er, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        volume_identity_module.er, "async_entries_for_config_entry", lambda registry, entry_id: registry.entries
    )

    blocked = migrate_volume_entities(object(), "entry", {"54": {"name": "/volume1"}})

    assert blocked == set()
    assert registry.updated == []


def test_options_flow_selection_preserves_other_options_and_stores_explicit_choice() -> None:
    options, errors = merge_volume_migration_options(
        {"scan_interval": 45, "other_setting": "keep"},
        {
            "volume_volume1_used": [
                ("sensor.legacy_51", "entry_volume_51_used"),
                ("sensor.legacy_54", "entry_volume_54_used"),
            ]
        },
        {"volume1 used": "entry_volume_54_used"},
    )

    assert errors == {}
    assert options == {
        "scan_interval": 45,
        "other_setting": "keep",
        "volume_migrations": {"volume_volume1_used": "entry_volume_54_used"},
    }


def test_options_flow_rejects_stale_or_unoffered_selection() -> None:
    options, errors = merge_volume_migration_options(
        {"volume_migrations": {"volume_volume1_used": "old_uid"}},
        {"volume_volume1_used": [("sensor.legacy_51", "entry_volume_51_used")]},
        {"volume1 used": "old_uid"},
    )

    assert errors == {"volume1 used": "invalid_selection"}
    assert options["volume_migrations"]["volume_volume1_used"] == "old_uid"


def test_options_conflicts_list_entity_ids_only_for_present_ambiguous_metrics(monkeypatch) -> None:
    entries = [fake_entry(f"sensor.legacy_{index}", f"entry_volume_{index}_used", "volume1 Used") for index in (51, 54)]
    registry = FakeEntityRegistry(entries)
    monkeypatch.setattr(volume_identity_module.er, "async_get", lambda hass: registry)
    monkeypatch.setattr(
        volume_identity_module.er, "async_entries_for_config_entry", lambda registry, entry_id: registry.entries
    )

    conflicts = volume_migration_conflicts(object(), "entry", {"54": {"name": "/volume1"}})

    assert conflicts == {
        "volume_volume1_used": [
            ("sensor.legacy_51", "entry_volume_51_used"),
            ("sensor.legacy_54", "entry_volume_54_used"),
        ]
    }
