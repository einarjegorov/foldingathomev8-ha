"""Websocket client coverage for Folding@home v8."""

from __future__ import annotations

import json
from typing import Any

import aiohttp

from custom_components.foldingathome_v8.client import FoldingAtHomeClient, build_ws_url
from custom_components.foldingathome_v8.const import WEBSOCKET_HEARTBEAT


class _FakeWebSocket:
    """Small async websocket stub for client tests."""

    closed = False

    def __init__(self, messages: list[aiohttp.WSMessage]) -> None:
        self._messages = messages

    async def __aenter__(self) -> _FakeWebSocket:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        self.closed = True

    def __aiter__(self) -> _FakeWebSocket:
        return self

    async def __anext__(self) -> aiohttp.WSMessage:
        if not self._messages:
            raise StopAsyncIteration
        return self._messages.pop(0)


class _FakeSession:
    """Small aiohttp session stub that records websocket options."""

    def __init__(self, websocket: _FakeWebSocket) -> None:
        self.websocket = websocket
        self.ws_connect_calls: list[tuple[str, dict[str, Any]]] = []

    def ws_connect(self, url: str, **kwargs: Any) -> _FakeWebSocket:
        self.ws_connect_calls.append((url, kwargs))
        return self.websocket


async def test_client_uses_websocket_heartbeat_and_clears_finished_socket() -> None:
    """The long-lived client keeps idle connections alive with websocket pings."""
    websocket = _FakeWebSocket(
        [
            aiohttp.WSMessage(
                aiohttp.WSMsgType.TEXT,
                json.dumps({"info": {"id": "abc"}, "config": {}, "units": []}),
                None,
            )
        ]
    )
    session = _FakeSession(websocket)
    client = FoldingAtHomeClient(session, "fah.local", 7396)

    await client._listen_once()

    assert session.ws_connect_calls == [
        (
            build_ws_url("fah.local", 7396),
            {"heartbeat": WEBSOCKET_HEARTBEAT},
        )
    ]
    assert client.available is True
    assert client._ws is None
