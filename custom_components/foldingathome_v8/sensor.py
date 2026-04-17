"""Sensor platform for Folding@home v8."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CLONE,
    ATTR_CORE,
    ATTR_CPUS,
    ATTR_DEADLINE,
    ATTR_ETA,
    ATTR_FRAMES,
    ATTR_GEN,
    ATTR_GPUS,
    ATTR_PAUSE_REASON,
    ATTR_PPD,
    ATTR_PROJECT,
    ATTR_RUN,
    ATTR_RUN_TIME,
    ATTR_STATUS,
    ATTR_TIMEOUT,
    ATTR_WAIT,
    ATTR_WORK_UNIT_ID,
    ATTR_WORK_UNIT_NUMBER,
    CLIENT_STATE_OPTIONS,
    DOMAIN,
)
from .coordinator import FoldingAtHomeCoordinator
from .entity import FoldingAtHomeEntity
from .models import WorkUnit


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Folding@home v8 sensors."""
    coordinator: FoldingAtHomeCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        FoldingAtHomeClientStateSensor(coordinator, entry),
        FoldingAtHomeActiveWorkUnitsSensor(coordinator, entry),
        FoldingAtHomeTotalPpdSensor(coordinator, entry),
        FoldingAtHomeCpuCountSensor(coordinator, entry),
        FoldingAtHomeGpuCountSensor(coordinator, entry),
        FoldingAtHomeMachineNameSensor(coordinator, entry),
        FoldingAtHomeClientVersionSensor(coordinator, entry),
    ]

    work_unit_entities: dict[str, FoldingAtHomeWorkUnitSensor] = {}

    @callback
    def sync_work_unit_entities() -> None:
        current_ids = {unit.unit_id for unit in coordinator.data.active_work_units}
        new_entities: list[FoldingAtHomeWorkUnitSensor] = []

        for unit in coordinator.data.active_work_units:
            if unit.unit_id in work_unit_entities:
                continue
            entity = FoldingAtHomeWorkUnitSensor(coordinator, entry, unit.unit_id)
            work_unit_entities[unit.unit_id] = entity
            new_entities.append(entity)

        for unit_id in tuple(work_unit_entities):
            if unit_id in current_ids:
                continue
            entity = work_unit_entities.pop(unit_id)
            if entity.entity_id is not None:
                hass.async_create_task(entity.async_remove(force_remove=True))

        if new_entities:
            async_add_entities(new_entities)

    async_add_entities(entities)
    sync_work_unit_entities()
    entry.async_on_unload(coordinator.async_add_listener(sync_work_unit_entities))


class FoldingAtHomeSensor(FoldingAtHomeEntity, SensorEntity):
    """Base sensor with disconnect-aware availability."""

    @property
    def available(self) -> bool:
        """Entities are unavailable when the websocket is disconnected."""
        return self.coordinator.data.available


class FoldingAtHomeClientStateSensor(FoldingAtHomeSensor):
    """Sensor for the normalized client state."""

    _attr_name = "Client State"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = CLIENT_STATE_OPTIONS

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_client_state"

    @property
    def native_value(self) -> str:
        """Return the normalized client state."""
        return self.coordinator.data.client_state.title()


class FoldingAtHomeActiveWorkUnitsSensor(FoldingAtHomeSensor):
    """Sensor for the number of active work units."""

    _attr_name = "Active Work Units"

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_active_work_units"

    @property
    def native_value(self) -> int:
        """Return the number of active work units."""
        return len(self.coordinator.data.active_work_units)


class FoldingAtHomeTotalPpdSensor(FoldingAtHomeSensor):
    """Sensor for the current total PPD estimate."""

    _attr_name = "Total PPD"
    _attr_native_unit_of_measurement = "PPD"

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_total_ppd"

    @property
    def native_value(self) -> int:
        """Return the total PPD estimate."""
        return self.coordinator.data.total_ppd


class FoldingAtHomeClientVersionSensor(FoldingAtHomeSensor):
    """Diagnostic sensor for the FAH client version."""

    _attr_name = "Client Version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_client_version"

    @property
    def native_value(self) -> str | None:
        """Return the FAH client version."""
        if self.coordinator.data.info is None:
            return None
        return self.coordinator.data.info.version


class FoldingAtHomeCpuCountSensor(FoldingAtHomeSensor):
    """Sensor for the machine CPU count reported by FAH."""

    _attr_name = "CPU Count"

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_cpu_count"

    @property
    def native_value(self) -> int | None:
        """Return the reported CPU count."""
        return self.coordinator.data.cpu_count


class FoldingAtHomeGpuCountSensor(FoldingAtHomeSensor):
    """Sensor for the machine GPU count reported by FAH."""

    _attr_name = "GPU Count"

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_gpu_count"

    @property
    def native_value(self) -> int | None:
        """Return the reported GPU count."""
        return self.coordinator.data.gpu_count


class FoldingAtHomeMachineNameSensor(FoldingAtHomeSensor):
    """Sensor for the FAH machine name."""

    _attr_name = "Machine Name"

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_machine_name"

    @property
    def native_value(self) -> str | None:
        """Return the configured machine name."""
        if self.coordinator.data.info is None:
            return None
        return self.coordinator.data.info.machine_name


class FoldingAtHomeWorkUnitSensor(FoldingAtHomeSensor):
    """Dynamic progress sensor for one active work unit."""

    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
        unit_id: str,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._unit_id = unit_id
        self._attr_name = f"Work Unit {unit_id[:8]}"
        self._attr_unique_id = f"{config_entry.entry_id}_wu_{unit_id}"

    @property
    def _work_unit(self) -> WorkUnit | None:
        for unit in self.coordinator.data.active_work_units:
            if unit.unit_id == self._unit_id:
                return unit
        return None

    @property
    def available(self) -> bool:
        """Only available while the websocket is connected and the WU exists."""
        return self.coordinator.data.available and self._work_unit is not None

    @property
    def native_value(self) -> float | None:
        """Return work unit progress as a percent."""
        unit = self._work_unit
        if unit is None:
            return None
        return unit.progress_percent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed work unit metadata."""
        unit = self._work_unit
        if unit is None:
            return {}

        return {
            ATTR_WORK_UNIT_ID: unit.unit_id,
            ATTR_WORK_UNIT_NUMBER: unit.number,
            ATTR_STATUS: unit.state,
            ATTR_PROJECT: unit.project,
            ATTR_RUN: unit.run,
            ATTR_CLONE: unit.clone,
            ATTR_GEN: unit.gen,
            ATTR_PPD: unit.ppd,
            ATTR_ETA: unit.eta,
            ATTR_TIMEOUT: unit.timeout,
            ATTR_DEADLINE: unit.deadline,
            ATTR_CPUS: unit.cpus,
            ATTR_GPUS: list(unit.gpus),
            ATTR_CORE: unit.core_type,
            ATTR_WAIT: unit.wait,
            ATTR_PAUSE_REASON: unit.pause_reason,
            ATTR_FRAMES: unit.frames,
            ATTR_RUN_TIME: unit.run_time,
        }
