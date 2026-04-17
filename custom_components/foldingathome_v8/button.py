"""Button platform for Folding@home v8."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FINISH_RESUME_TIMEOUT
from .coordinator import FoldingAtHomeCoordinator
from .entity import FoldingAtHomeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Folding@home v8 buttons."""
    coordinator: FoldingAtHomeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FoldingAtHomeStateButton(coordinator, entry, "fold", "Fold"),
            FoldingAtHomeStateButton(coordinator, entry, "pause", "Pause"),
            FoldingAtHomeStateButton(coordinator, entry, "finish", "Finish"),
        ]
    )


class FoldingAtHomeStateButton(FoldingAtHomeEntity, ButtonEntity):
    """Button that forwards a state command to FAH."""

    def __init__(
        self,
        coordinator: FoldingAtHomeCoordinator,
        config_entry: ConfigEntry,
        command: str,
        name: str,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self._command = command
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{command}"

    async def async_press(self) -> None:
        """Send the requested state command."""
        if self._command == "finish" and self.coordinator.data.group_config.paused:
            await self.coordinator.client.async_send_state_command("fold")
            try:
                await self.coordinator.client.async_wait_for_condition(
                    lambda data: data.available and not data.group_config.paused,
                    FINISH_RESUME_TIMEOUT,
                )
            except TimeoutError as err:
                raise HomeAssistantError(
                    "Timed out waiting for Folding@home to resume before finishing"
                ) from err
        await self.coordinator.client.async_send_state_command(self._command)
