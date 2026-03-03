"""Sensor platform for ASUSTOR NAS SNMP integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE, REVOLUTIONS_PER_MINUTE, UnitOfInformation, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AsustorNasDataUpdateCoordinator
from .data import AsustorNasConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AsustorNasSensorEntityDescription(SensorEntityDescription):
    """Describes an ASUSTOR NAS sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


# Static sensors that are always present
STATIC_SENSORS: tuple[AsustorNasSensorEntityDescription, ...] = (
    AsustorNasSensorEntityDescription(
        key="model",
        name="Model",
        icon="mdi:nas",
        value_fn=lambda data: data.get("model"),
    ),
    AsustorNasSensorEntityDescription(
        key="cpu_model",
        name="CPU Model",
        icon="mdi:cpu-64-bit",
        value_fn=lambda data: data.get("cpu_model"),
    ),
    AsustorNasSensorEntityDescription(
        key="memory_total",
        name="Total Memory",
        icon="mdi:memory",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("memory", {}).get("total_mb"),
    ),
    AsustorNasSensorEntityDescription(
        key="memory_used",
        name="Used Memory",
        icon="mdi:memory",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("memory", {}).get("used_mb"),
    ),
    AsustorNasSensorEntityDescription(
        key="memory_usage_percent",
        name="Memory Usage",
        icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("memory", {}).get("usage_percent"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AsustorNasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data
    registered_volume_ids: set[str] = set()

    entities: list[AsustorNasSensorEntity] = [
        AsustorNasSensorEntity(coordinator, entry, description)
        for description in STATIC_SENSORS
        if description.value_fn(data) is not None
    ]

    def _build_volume_entities(volume_id: str, volume_name: str) -> list[AsustorNasSensorEntity]:
        volume_descriptions = (
            AsustorNasSensorEntityDescription(
                key=f"volume_{volume_id}_total",
                name=f"{volume_name} Total",
                icon="mdi:harddisk",
                device_class=SensorDeviceClass.DATA_SIZE,
                native_unit_of_measurement=UnitOfInformation.BYTES,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda d, vid=volume_id: d.get("volumes", {}).get(vid, {}).get("total_bytes"),
            ),
            AsustorNasSensorEntityDescription(
                key=f"volume_{volume_id}_used",
                name=f"{volume_name} Used",
                icon="mdi:harddisk",
                device_class=SensorDeviceClass.DATA_SIZE,
                native_unit_of_measurement=UnitOfInformation.BYTES,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda d, vid=volume_id: d.get("volumes", {}).get(vid, {}).get("used_bytes"),
            ),
            AsustorNasSensorEntityDescription(
                key=f"volume_{volume_id}_free",
                name=f"{volume_name} Free",
                icon="mdi:harddisk",
                device_class=SensorDeviceClass.DATA_SIZE,
                native_unit_of_measurement=UnitOfInformation.BYTES,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda d, vid=volume_id: d.get("volumes", {}).get(vid, {}).get("free_bytes"),
            ),
            AsustorNasSensorEntityDescription(
                key=f"volume_{volume_id}_usage_percent",
                name=f"{volume_name} Usage",
                icon="mdi:percent",
                native_unit_of_measurement=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda d, vid=volume_id: d.get("volumes", {}).get(vid, {}).get("usage_percent"),
            ),
        )

        return [AsustorNasSensorEntity(coordinator, entry, description) for description in volume_descriptions]

    # 2. Add dynamic sensors (CPU Cores)
    for core_id in data.get("cpu_cores", {}):
        description = AsustorNasSensorEntityDescription(
            key=f"cpu_core_{core_id}",
            name=f"CPU Core {core_id} Usage",
            icon="mdi:speedometer",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda d, cid=core_id: d.get("cpu_cores", {}).get(cid),
        )
        entities.append(AsustorNasSensorEntity(coordinator, entry, description))

    # 3. Add dynamic sensors (Fans)
    for fan_id in data.get("fans", {}):
        description = AsustorNasSensorEntityDescription(
            key=f"fan_{fan_id}",
            name=f"Fan {fan_id}",
            icon="mdi:fan",
            native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda d, fid=fan_id: d.get("fans", {}).get(fid),
        )
        entities.append(AsustorNasSensorEntity(coordinator, entry, description))

    # 4. Add dynamic sensors (Temperatures)
    for temp_id in data.get("temperatures", {}):
        name = "CPU Temperature" if temp_id == "cpu" else "System Temperature"
        icon = "mdi:thermometer" if temp_id == "cpu" else "mdi:thermometer-lines"
        description = AsustorNasSensorEntityDescription(
            key=f"temp_{temp_id}",
            name=name,
            icon=icon,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda d, tid=temp_id: d.get("temperatures", {}).get(tid),
        )
        entities.append(AsustorNasSensorEntity(coordinator, entry, description))

    # 5. Add dynamic sensors (Volumes)
    for volume_id, volume in data.get("volumes", {}).items():
        volume_id_str = str(volume_id)
        volume_name = str(volume.get("name", f"volume{volume_id_str}")).lstrip("/")
        registered_volume_ids.add(volume_id_str)
        entities.extend(_build_volume_entities(volume_id_str, volume_name))

    async_add_entities(entities)

    @callback
    def _async_add_missing_volume_entities() -> None:
        new_entities: list[AsustorNasSensorEntity] = []

        for volume_id, volume in coordinator.data.get("volumes", {}).items():
            volume_id_str = str(volume_id)
            if volume_id_str in registered_volume_ids:
                continue

            volume_name = str(volume.get("name", f"volume{volume_id_str}")).lstrip("/")
            registered_volume_ids.add(volume_id_str)
            new_entities.extend(_build_volume_entities(volume_id_str, volume_name))

        if new_entities:
            _LOGGER.debug("Adding %d new volume sensor entities", len(new_entities))
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(_async_add_missing_volume_entities))


class AsustorNasSensorEntity(CoordinatorEntity[AsustorNasDataUpdateCoordinator], SensorEntity):
    """Representation of an ASUSTOR NAS sensor."""

    entity_description: AsustorNasSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AsustorNasDataUpdateCoordinator,
        entry: AsustorNasConfigEntry,
        description: AsustorNasSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry

        # Unique ID is based on the entry ID (which is tied to the MAC address) and the sensor key
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        # Device info groups all sensors under the same NAS device
        model = coordinator.data.get("model", "Unknown")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=f"ASUSTOR NAS ({model})",
            manufacturer="ASUSTOR",
            model=model,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # The entity is available if the coordinator is successful and the value is not None
        return super().available and self.entity_description.value_fn(self.coordinator.data) is not None
