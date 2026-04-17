"""Binary sensor platform for Folding@home v8."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FoldingAtHomeCoordinator
from .entity import FoldingAtHomeEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Folding@home v8 binary sensors."""
    coordinator: FoldingAtHomeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FoldingAtHomeConnectedBinarySensor(coordinator, entry),
            FoldingAtHomeRunningBinarySensor(coordinator, entry),
            FoldingAtHomePausedBinarySensor(coordinator, entry),
            FoldingAtHomeFinishingBinarySensor(coordinator, entry),
            FoldingAtHomeHasActiveWorkBinarySensor(coordinator, entry),
            FoldingAtHomeKeepAwakeBinarySensor(coordinator, entry),
            FoldingAtHomeOnlyWhenIdleBinarySensor(coordinator, entry),
            FoldingAtHomeAllowOnBatteryBinarySensor(coordinator, entry),
            FoldingAtHomeHasFailedWorkUnitsBinarySensor(coordinator, entry),
            FoldingAtHomeHasLostWorkUnitsBinarySensor(coordinator, entry),
        ]
    )


class FoldingAtHomeConnectedBinarySensor(FoldingAtHomeEntity, BinarySensorEntity):
    """Binary sensor showing websocket connectivity."""

    _attr_name = "Connected"
    _attr_unique_id = None
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_connected"

    @property
    def available(self) -> bool:
        """Keep the entity available so it can report disconnected state."""
        return True

    @property
    def is_on(self) -> bool:
        """Return whether the websocket is connected."""
        return self.coordinator.data.available


class FoldingAtHomeStateBinarySensor(FoldingAtHomeEntity, BinarySensorEntity):
    """Base binary sensor for normalized FAH state booleans."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
        *,
        key: str,
        name: str,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"


class FoldingAtHomeRunningBinarySensor(FoldingAtHomeStateBinarySensor):
    """Binary sensor showing active folding state."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry, key="running", name="Running")

    @property
    def is_on(self) -> bool:
        """Return whether the client is actively folding."""
        return self.coordinator.data.is_running


class FoldingAtHomePausedBinarySensor(FoldingAtHomeStateBinarySensor):
    """Binary sensor showing paused state."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry, key="paused", name="Paused")

    @property
    def is_on(self) -> bool:
        """Return whether the client is paused."""
        return self.coordinator.data.is_paused


class FoldingAtHomeFinishingBinarySensor(FoldingAtHomeStateBinarySensor):
    """Binary sensor showing finishing state."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            coordinator, config_entry, key="finishing", name="Finishing"
        )

    @property
    def is_on(self) -> bool:
        """Return whether the client is finishing current work."""
        return self.coordinator.data.is_finishing


class FoldingAtHomeHasActiveWorkBinarySensor(FoldingAtHomeStateBinarySensor):
    """Binary sensor showing whether the client has active work."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            key="has_active_work",
            name="Has Active Work",
        )

    @property
    def is_on(self) -> bool:
        """Return whether there are active work units."""
        return self.coordinator.data.has_active_work


class FoldingAtHomeKeepAwakeBinarySensor(FoldingAtHomeStateBinarySensor):
    """Binary sensor showing whether FAH keeps the machine awake."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry, key="keep_awake", name="Keep Awake")

    @property
    def is_on(self) -> bool:
        """Return whether keep-awake is enabled."""
        return self.coordinator.data.keep_awake


class FoldingAtHomeOnlyWhenIdleBinarySensor(FoldingAtHomeStateBinarySensor):
    """Binary sensor showing idle-only scheduling."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            coordinator, config_entry, key="only_when_idle", name="Only When Idle"
        )

    @property
    def is_on(self) -> bool:
        """Return whether folding runs only when the machine is idle."""
        return self.coordinator.data.only_when_idle


class FoldingAtHomeAllowOnBatteryBinarySensor(FoldingAtHomeStateBinarySensor):
    """Binary sensor showing whether folding is allowed on battery."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            coordinator, config_entry, key="allow_on_battery", name="Allow On Battery"
        )

    @property
    def is_on(self) -> bool:
        """Return whether folding is allowed on battery."""
        return self.coordinator.data.allow_on_battery


class FoldingAtHomeHasFailedWorkUnitsBinarySensor(FoldingAtHomeStateBinarySensor):
    """Binary sensor showing whether any work units have failed."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            key="has_failed_work_units",
            name="Has Failed Work Units",
        )

    @property
    def is_on(self) -> bool:
        """Return whether there are any failed work units."""
        return self.coordinator.data.has_failed_work_units


class FoldingAtHomeHasLostWorkUnitsBinarySensor(FoldingAtHomeStateBinarySensor):
    """Binary sensor showing whether any work units have been lost."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            key="has_lost_work_units",
            name="Has Lost Work Units",
        )

    @property
    def is_on(self) -> bool:
        """Return whether there are any lost work units."""
        return self.coordinator.data.has_lost_work_units
