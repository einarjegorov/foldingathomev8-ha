"""Shared entity code for the Folding@home v8 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import FoldingAtHomeCoordinator


class FoldingAtHomeEntity(CoordinatorEntity[FoldingAtHomeCoordinator]):
    """Base entity for the Folding@home v8 integration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the FAH client as a Home Assistant device."""
        data = self.coordinator.data
        name = data.title
        model = "Folding@home Client"
        if data.info and data.info.version:
            model = f"{model} {data.info.version}"

        return DeviceInfo(
            identifiers={(DOMAIN, data.client_key)},
            manufacturer=MANUFACTURER,
            model=model,
            name=name,
        )

