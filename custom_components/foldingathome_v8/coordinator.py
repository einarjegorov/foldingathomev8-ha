"""Coordinator for the Folding@home v8 integration."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import FoldingAtHomeClient
from .const import DOMAIN
from .models import NormalizedClientData

_LOGGER = logging.getLogger(__name__)


class FoldingAtHomeCoordinator(DataUpdateCoordinator[NormalizedClientData]):
    """Push coordinator backed by a long-lived websocket client."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
        )
        self.entry = entry
        self.client = FoldingAtHomeClient(
            session=session,
            host=entry.data["host"],
            port=entry.data["port"],
        )
        self._remove_listener = self.client.add_listener(self._handle_client_update)

    async def async_start(self) -> None:
        """Start the websocket client and wait for the first snapshot."""
        await self.client.async_start()
        self.async_set_updated_data(self.client.normalized_data)

    async def async_shutdown(self) -> None:
        """Stop the websocket client."""
        self._remove_listener()
        await self.client.async_stop()

    async def _async_update_data(self) -> NormalizedClientData:
        """Return the latest client data for manual refreshes."""
        return self.client.normalized_data

    @callback
    def _handle_client_update(self) -> None:
        self.async_set_updated_data(self.client.normalized_data)

