"""Config flow coverage for Folding@home v8."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.foldingathome_v8.const import DEFAULT_PORT, DOMAIN


async def test_user_flow_success(hass) -> None:
    """A successful user flow creates an entry."""
    with patch(
        "custom_components.foldingathome_v8.config_flow.async_probe_client",
        AsyncMock(
            return_value={"info": {"id": "abc", "mach_name": "My FAH", "hostname": "fah"}}
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "fah.local", CONF_PORT: DEFAULT_PORT},
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == "My FAH"
    assert result2["data"] == {CONF_HOST: "fah.local", CONF_PORT: DEFAULT_PORT}


async def test_user_flow_cannot_connect(hass) -> None:
    """Connection failures are surfaced as form errors."""
    with patch(
        "custom_components.foldingathome_v8.config_flow.async_probe_client",
        AsyncMock(side_effect=Exception),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "fah.local", CONF_PORT: DEFAULT_PORT},
        )

    assert result2["type"] == "form"
    assert result2["errors"]["base"] == "unknown"


async def test_duplicate_entry_aborts(hass) -> None:
    """An already configured client is not added twice."""
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Existing",
        data={CONF_HOST: "fah.local", CONF_PORT: DEFAULT_PORT},
        source=config_entries.SOURCE_USER,
        entry_id="test",
        unique_id="abc",
        discovery_keys={},
        options={},
        subentries_data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.foldingathome_v8.config_flow.async_probe_client",
        AsyncMock(return_value={"info": {"id": "abc", "mach_name": "Existing"}}),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "other.local", CONF_PORT: DEFAULT_PORT},
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"


async def test_reconfigure_updates_entry(hass) -> None:
    """Reconfigure updates host and port in place."""
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Existing",
        data={CONF_HOST: "fah.local", CONF_PORT: DEFAULT_PORT},
        source=config_entries.SOURCE_USER,
        entry_id="test",
        unique_id="abc",
        discovery_keys={},
        options={},
        subentries_data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.foldingathome_v8.config_flow.async_probe_client",
        AsyncMock(return_value={"info": {"id": "abc", "mach_name": "Existing"}}),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_RECONFIGURE},
            data={"entry_id": entry.entry_id},
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "new.local", CONF_PORT: 1234},
        )

    assert result2["type"] == "abort"
    assert entry.data == {CONF_HOST: "new.local", CONF_PORT: 1234}

