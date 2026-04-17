"""Config flow for Folding@home v8."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .client import CannotConnectError, InvalidSnapshotError, async_probe_client
from .const import DEFAULT_PORT, DOMAIN


class FoldingAtHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Folding@home v8."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            result = await self._async_validate_input(user_input)
            if "errors" not in result:
                await self.async_set_unique_id(result["unique_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=result["title"], data=result["data"])
            errors = result["errors"]

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of an existing entry."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            result = await self._async_validate_input(user_input)
            if "errors" not in result:
                await self.async_set_unique_id(result["unique_id"])
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=result["data"],
                )
            errors = result["errors"]

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(entry.data[CONF_HOST], entry.data[CONF_PORT]),
            errors=errors,
        )

    async def _async_validate_input(
        self, user_input: dict[str, Any]
    ) -> dict[str, Any]:
        host = user_input[CONF_HOST]
        port = user_input[CONF_PORT]

        try:
            snapshot = await async_probe_client(host, port)
        except CannotConnectError:
            return {"errors": {"base": "cannot_connect"}}
        except InvalidSnapshotError:
            return {"errors": {"base": "invalid_snapshot"}}
        except Exception:  # noqa: BLE001
            return {"errors": {"base": "unknown"}}

        info = snapshot.get("info", {})
        unique_id = info.get("id") or f"{host}:{port}"
        title = info.get("mach_name") or info.get("hostname") or host

        return {
            "title": title,
            "unique_id": unique_id,
            "data": {
                CONF_HOST: host,
                CONF_PORT: port,
            },
        }


def _schema(host: str = "", port: int = DEFAULT_PORT) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=host): str,
            vol.Required(CONF_PORT, default=port): int,
        }
    )

