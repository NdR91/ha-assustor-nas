"""Home Assistant registry and options-flow tests for volume migration."""

from datetime import timedelta
import logging
from types import SimpleNamespace

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_asustor_nas_custom_integration.const import DOMAIN
from custom_components.ha_asustor_nas_custom_integration.sensor import async_setup_entry as async_setup_sensor_entry
from custom_components.ha_asustor_nas_custom_integration.volume_identity import migrate_volume_entities
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


@pytest.fixture
def volume_entry(hass):
    """Create an integration entry with a current volume sample."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="00:11:22:33:44:55")
    entry.add_to_hass(hass)
    entry.runtime_data = SimpleNamespace(coordinator=SimpleNamespace(data={"volumes": {"54": {"name": "/volume1"}}}))
    return entry


async def test_real_registry_migration_preserves_entity_id_and_handles_changed_index(hass, volume_entry):
    """A unique legacy entity is renamed in the registry without changing its entity ID."""
    registry = er.async_get(hass)
    legacy = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{volume_entry.entry_id}_volume_51_used",
        config_entry=volume_entry,
        original_name="volume1 Used",
        suggested_object_id="volume1_used_dashboard_id",
    )
    entity_id = legacy.entity_id

    blocked = migrate_volume_entities(hass, volume_entry.entry_id, {"54": {"name": "/volume1"}})

    assert blocked == set()
    migrated = registry.async_get(entity_id)
    assert migrated is not None
    assert migrated.unique_id == f"{volume_entry.entry_id}_volume_volume1_used"
    assert migrated.entity_id == entity_id


async def test_real_registry_ambiguity_is_untouched_until_explicit_choice(hass, volume_entry):
    """Multiple candidates stay unchanged until one legacy unique ID is selected."""
    registry = er.async_get(hass)
    legacy = [
        registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"{volume_entry.entry_id}_volume_{index}_used",
            config_entry=volume_entry,
            original_name="volume1 Used",
        )
        for index in (51, 54, 56)
    ]
    old_ids = {item.entity_id: item.unique_id for item in legacy}

    blocked = migrate_volume_entities(hass, volume_entry.entry_id, {"54": {"name": "/volume1"}})

    assert blocked == {("volume1", "used")}
    assert {entity_id: registry.async_get(entity_id).unique_id for entity_id in old_ids} == old_ids

    blocked = migrate_volume_entities(
        hass,
        volume_entry.entry_id,
        {"54": {"name": "/volume1"}},
        {"volume_volume1_used": legacy[1].unique_id},
    )

    assert blocked == set()
    assert registry.async_get(legacy[1].entity_id).unique_id == f"{volume_entry.entry_id}_volume_volume1_used"
    assert registry.async_get(legacy[1].entity_id).entity_id == legacy[1].entity_id
    assert registry.async_get(legacy[0].entity_id).unique_id == old_ids[legacy[0].entity_id]
    assert registry.async_get(legacy[2].entity_id).unique_id == old_ids[legacy[2].entity_id]


async def test_real_registry_skips_legacy_conflict_when_stable_target_exists(hass, volume_entry):
    """An existing stable target wins without rewriting any legacy entries."""
    registry = er.async_get(hass)
    stable = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{volume_entry.entry_id}_volume_volume1_used",
        config_entry=volume_entry,
        original_name="volume1 Used",
    )
    legacy = [
        registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"{volume_entry.entry_id}_volume_{index}_used",
            config_entry=volume_entry,
            original_name="volume1 Used",
        )
        for index in (51, 54)
    ]
    old_ids = {item.entity_id: item.unique_id for item in legacy}

    blocked = migrate_volume_entities(hass, volume_entry.entry_id, {"54": {"name": "/volume1"}})

    assert blocked == set()
    assert registry.async_get(stable.entity_id).unique_id == f"{volume_entry.entry_id}_volume_volume1_used"
    assert {entity_id: registry.async_get(entity_id).unique_id for entity_id in old_ids} == old_ids


async def test_real_options_flow_offers_candidates_and_persists_explicit_choice(
    hass, volume_entry, enable_custom_integrations
):
    """The options UI lists legacy entity IDs and stores the user's selection."""
    registry = er.async_get(hass)
    candidates = [
        registry.async_get_or_create(
            "sensor",
            DOMAIN,
            f"{volume_entry.entry_id}_volume_{index}_used",
            config_entry=volume_entry,
            original_name="volume1 Used",
        )
        for index in (51, 54)
    ]

    form = await hass.config_entries.options.async_init(volume_entry.entry_id)

    assert form["type"] == "form"
    assert form["step_id"] == "init"
    form_field, selector = next(iter(form["data_schema"].schema.items()))
    assert form_field == "volume1 used"
    assert selector.config["mode"] == "dropdown"
    assert selector.config["options"] == [
        {"label": candidates[0].entity_id, "value": candidates[0].unique_id},
        {"label": candidates[1].entity_id, "value": candidates[1].unique_id},
    ]
    result = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input={"volume1 used": candidates[1].unique_id},
    )

    assert result["type"] == "create_entry"
    assert volume_entry.options["volume_migrations"] == {"volume_volume1_used": candidates[1].unique_id}


async def test_sensor_platform_keeps_entity_ids_when_volume_row_index_changes(hass):
    """The real sensor setup and coordinator listener do not duplicate mount sensors."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="00:11:22:33:44:66")
    entry.add_to_hass(hass)
    initial_data = {
        "volumes": {
            "51": {
                "name": "/volume1",
                "total_bytes": 1000,
                "used_bytes": 200,
                "free_bytes": 800,
                "usage_percent": 20,
            }
        }
    }
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="volume identity test",
        update_interval=timedelta(minutes=5),
        config_entry=entry,
    )
    coordinator.async_set_updated_data(initial_data)
    entry.runtime_data = SimpleNamespace(coordinator=coordinator)
    added_entities = []

    await async_setup_sensor_entry(hass, entry, added_entities.extend)
    volume_entities = [entity for entity in added_entities if entity.entity_description.key.startswith("volume_")]
    assert len(volume_entities) == 4
    registry = er.async_get(hass)
    original_entity_ids = {}
    for entity in volume_entities:
        registered = registry.async_get_or_create(
            "sensor",
            DOMAIN,
            entity.unique_id,
            config_entry=entry,
            original_name=entity.entity_description.name,
            suggested_object_id=f"dashboard_{entity.entity_description.key}",
        )
        original_entity_ids[entity.unique_id] = registered.entity_id

    coordinator.async_set_updated_data(
        {
            "volumes": {
                "88": {
                    "name": "/volume1",
                    "total_bytes": 2000,
                    "used_bytes": 600,
                    "free_bytes": 1400,
                    "usage_percent": 30,
                }
            }
        }
    )
    await hass.async_block_till_done()

    assert len([entity for entity in added_entities if entity.entity_description.key.startswith("volume_")]) == 4
    assert {
        unique_id: registry.async_get_entity_id("sensor", DOMAIN, unique_id) for unique_id in original_entity_ids
    } == original_entity_ids
    assert {entity.entity_description.key: entity.native_value for entity in volume_entities} == {
        "volume_volume1_total": 2000,
        "volume_volume1_used": 600,
        "volume_volume1_free": 1400,
        "volume_volume1_usage_percent": 30,
    }
