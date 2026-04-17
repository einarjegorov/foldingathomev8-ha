"""Entity behavior coverage for Folding@home v8."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.foldingathome_v8.const import DOMAIN
from custom_components.foldingathome_v8.models import normalize_client_data


class _StubClient:
    """Minimal coordinator client stub for button tests."""

    def __init__(self) -> None:
        self.send_calls: list[str] = []
        self.raw_state = None
        self.available = True

    async def async_send_state_command(self, state: str) -> None:
        self.send_calls.append(state)


async def test_entities_reflect_normalized_state(hass) -> None:
    """Stable entities expose the normalized values."""
    from custom_components.foldingathome_v8.sensor import (
        FoldingAtHomeActiveWorkUnitsSensor,
        FoldingAtHomeClientStateSensor,
        FoldingAtHomeTotalPpdSensor,
    )

    coordinator = type("Coordinator", (), {})()
    coordinator.data = normalize_client_data(
        {
            "info": {"id": "abc", "mach_name": "My FAH"},
            "config": {"paused": False, "finish": False},
            "units": [
                {"id": "wu-1", "state": "RUN", "progress": 0.5, "ppd": 1000},
                {"id": "wu-2", "state": "RUN", "progress": 0.2, "ppd": 2000},
            ],
        },
        available=True,
        host="fah.local",
        port=7396,
    )
    entry = type("Entry", (), {"entry_id": "entry"})()

    assert FoldingAtHomeClientStateSensor(coordinator, entry).native_value == "Running"
    assert FoldingAtHomeActiveWorkUnitsSensor(coordinator, entry).native_value == 2
    assert FoldingAtHomeTotalPpdSensor(coordinator, entry).native_value == 3000


async def test_button_entities_send_expected_commands(hass) -> None:
    """Button presses use the raw FAH command names."""
    from custom_components.foldingathome_v8.button import FoldingAtHomeStateButton

    coordinator = type("Coordinator", (), {})()
    coordinator.data = normalize_client_data(
        {"info": {"id": "abc", "mach_name": "My FAH"}, "config": {}, "units": []},
        available=True,
        host="fah.local",
        port=7396,
    )
    coordinator.client = _StubClient()
    entry = type("Entry", (), {"entry_id": "entry"})()

    fold = FoldingAtHomeStateButton(coordinator, entry, "fold", "Fold")
    pause = FoldingAtHomeStateButton(coordinator, entry, "pause", "Pause")
    finish = FoldingAtHomeStateButton(coordinator, entry, "finish", "Finish")

    await fold.async_press()
    await pause.async_press()
    await finish.async_press()

    assert coordinator.client.send_calls == ["fold", "pause", "finish"]


async def test_finish_button_unpauses_before_finishing(hass) -> None:
    """Finish should resume a paused client before sending finish."""
    from custom_components.foldingathome_v8.button import FoldingAtHomeStateButton

    coordinator = type("Coordinator", (), {})()
    coordinator.data = normalize_client_data(
        {
            "info": {"id": "abc", "mach_name": "My FAH"},
            "config": {"paused": True, "finish": False},
            "units": [],
        },
        available=True,
        host="fah.local",
        port=7396,
    )
    coordinator.client = _StubClient()
    entry = type("Entry", (), {"entry_id": "entry"})()

    finish = FoldingAtHomeStateButton(coordinator, entry, "finish", "Finish")
    with patch("custom_components.foldingathome_v8.button.asyncio.sleep", AsyncMock()) as sleep:
        await finish.async_press()

    assert coordinator.client.send_calls == ["fold", "finish"]
    sleep.assert_awaited_once()


async def test_diagnostics_redacts_sensitive_fields(hass) -> None:
    """Diagnostics should not expose sensitive fields."""
    from custom_components.foldingathome_v8.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    entry = type(
        "Entry",
        (),
        {"entry_id": "entry", "data": {CONF_HOST: "secret.local", CONF_PORT: 7396}},
    )()
    coordinator = type("Coordinator", (), {})()
    coordinator.client = type(
        "Client",
        (),
        {
            "available": True,
            "raw_state": {
                "info": {"id": "abc", "hostname": "secret.local", "account": "token"},
                "config": {"passkey": "secret"},
            },
        },
    )()
    coordinator.data = normalize_client_data(
        {"info": {"id": "abc", "mach_name": "My FAH"}, "config": {}, "units": []},
        available=True,
        host="secret.local",
        port=7396,
    )
    hass.data.setdefault(DOMAIN, {})["entry"] = coordinator

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["host"] == "**REDACTED**"
    assert diagnostics["raw_state"]["info"]["account"] == "**REDACTED**"
    assert diagnostics["raw_state"]["config"]["passkey"] == "**REDACTED**"
