"""Diagnostics support for Folding@home v8."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SENSITIVE_DIAGNOSTIC_KEYS
from .coordinator import FoldingAtHomeCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator: FoldingAtHomeCoordinator = hass.data[DOMAIN][entry.entry_id]
    return async_redact_data(
        {
            "entry": dict(entry.data),
            "available": coordinator.client.available,
            "normalized": {
                "client_state": coordinator.data.client_state,
                "total_ppd": coordinator.data.total_ppd,
                "active_work_units": len(coordinator.data.active_work_units),
            },
            "raw_state": coordinator.client.raw_state,
        },
        SENSITIVE_DIAGNOSTIC_KEYS,
    )

