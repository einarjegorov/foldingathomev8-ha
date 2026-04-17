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
    async_add_entities([FoldingAtHomeConnectedBinarySensor(coordinator, entry)])


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

