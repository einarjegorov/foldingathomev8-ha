"""Sensor platform for Folding@home v8."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CLIENT_STATE_OPTIONS, DOMAIN
from .coordinator import FoldingAtHomeCoordinator
from .entity import FoldingAtHomeEntity


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
        FoldingAtHomeOverallProgressSensor(coordinator, entry),
        FoldingAtHomeTotalPpdSensor(coordinator, entry),
        FoldingAtHomeCpuCountSensor(coordinator, entry),
        FoldingAtHomeGpuCountSensor(coordinator, entry),
        FoldingAtHomeMachineNameSensor(coordinator, entry),
        FoldingAtHomeClientVersionSensor(coordinator, entry),
    ]
    async_add_entities(entities)


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


class FoldingAtHomeOverallProgressSensor(FoldingAtHomeSensor):
    """Sensor for aggregate progress across active work units."""

    _attr_name = "Overall Progress"
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_overall_progress"

    @property
    def native_value(self) -> float:
        """Return aggregate progress across active default-group work units."""
        return self.coordinator.data.overall_progress_percent


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
