"""Websocket client for the Folding@home v8 backend."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import aiohttp

from .const import (
    CLIENT_READY_TIMEOUT,
    RECONNECT_INITIAL_DELAY,
    RECONNECT_MAX_DELAY,
    WS_PATH,
)
from .models import NormalizedClientData, normalize_client_data
from .patch import apply_update, normalize_object

_LOGGER = logging.getLogger(__name__)


class CannotConnectError(Exception):
    """Raised when the FAH websocket cannot be reached."""


class InvalidSnapshotError(Exception):
    """Raised when the FAH websocket does not deliver a valid snapshot."""


def build_ws_url(host: str, port: int) -> str:
    """Build the FAH websocket URL."""
    return f"ws://{host}:{port}{WS_PATH}"


class FoldingAtHomeClient:
    """Long-lived websocket client for a single FAH client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
    ) -> None:
        self._session = session
        self.host = host
        self.port = port
        self._listeners: set[Callable[[], None]] = set()
        self._ready = asyncio.Event()
        self._raw_state: dict[str, Any] | None = None
        self._available = False
        self._task: asyncio.Task[None] | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None

    @property
    def raw_state(self) -> dict[str, Any] | None:
        """Return the latest raw normalized snapshot."""
        return self._raw_state

    @property
    def available(self) -> bool:
        """Return whether the websocket is currently connected."""
        return self._available

    @property
    def normalized_data(self) -> NormalizedClientData:
        """Return the latest normalized view of the client."""
        return normalize_client_data(
            self._raw_state,
            available=self._available,
            host=self.host,
            port=self.port,
        )

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a listener for snapshot updates."""
        self._listeners.add(listener)

        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener

    async def async_wait_for_condition(
        self,
        predicate: Callable[[NormalizedClientData], bool],
        timeout: float,
    ) -> NormalizedClientData:
        """Wait until the latest normalized data satisfies a predicate."""
        current = self.normalized_data
        if predicate(current):
            return current

        event = asyncio.Event()

        def listener() -> None:
            if predicate(self.normalized_data):
                event.set()

        remove_listener = self.add_listener(listener)
        try:
            current = self.normalized_data
            if predicate(current):
                return current

            async with asyncio.timeout(timeout):
                await event.wait()
            return self.normalized_data
        finally:
            remove_listener()

    async def async_start(self) -> None:
        """Start the websocket background task."""
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run(), name="foldingathome_v8_ws")
        await self.async_wait_until_ready()

    async def async_wait_until_ready(self) -> None:
        """Wait until the first valid snapshot has been received."""
        async with asyncio.timeout(CLIENT_READY_TIMEOUT):
            await self._ready.wait()

    async def async_stop(self) -> None:
        """Stop the websocket background task."""
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        if self._ws is not None:
            await self._ws.close()
            self._ws = None

        self._set_available(False)

    async def async_send_state_command(self, state: str) -> None:
        """Send a state command to the backend."""
        if self._ws is None or self._ws.closed:
            raise CannotConnectError("Folding@home websocket is not connected")

        payload = {
            "cmd": "state",
            "time": _utc_timestamp(),
            "state": state,
        }
        await self._ws.send_json(payload)

    async def _run(self) -> None:
        delay = RECONNECT_INITIAL_DELAY

        while True:
            try:
                await self._listen_once()
                delay = RECONNECT_INITIAL_DELAY
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Error while communicating with the FAH websocket")

            self._set_available(False)
            await asyncio.sleep(delay)
            delay = min(delay * 2, RECONNECT_MAX_DELAY)

    async def _listen_once(self) -> None:
        url = build_ws_url(self.host, self.port)
        _LOGGER.debug("Connecting to Folding@home websocket at %s", url)

        async with self._session.ws_connect(url) as ws:
            self._ws = ws
            async for message in ws:
                payload = _decode_ws_message(message)
                if payload is None:
                    continue
                if not self._handle_payload(payload):
                    continue
                self._set_available(True)

    def _handle_payload(self, payload: Any) -> bool:
        if isinstance(payload, dict):
            self._raw_state = normalize_object(payload)
            self._ready.set()
            self._notify_listeners()
            return True

        if isinstance(payload, list):
            if self._raw_state is None:
                _LOGGER.debug("Ignoring FAH patch before initial snapshot: %s", payload)
                return False
            apply_update(self._raw_state, payload)
            self._notify_listeners()
            return True

        _LOGGER.debug("Ignoring FAH non-state payload: %r", payload)
        return False

    def _set_available(self, available: bool) -> None:
        if self._available == available:
            return
        self._available = available
        self._notify_listeners()

    def _notify_listeners(self) -> None:
        for listener in tuple(self._listeners):
            listener()


async def async_probe_client(
    host: str,
    port: int,
    *,
    timeout: int = CLIENT_READY_TIMEOUT,
) -> dict[str, Any]:
    """Connect once and return the first full websocket snapshot."""
    url = build_ws_url(host, port)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                async with asyncio.timeout(timeout):
                    async for message in ws:
                        payload = _decode_ws_message(message)
                        if isinstance(payload, dict):
                            return normalize_object(payload)
                        if payload is None or not isinstance(payload, list):
                            continue
                        raise InvalidSnapshotError(
                            "Received patch payload before initial snapshot"
                        )
    except InvalidSnapshotError:
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        raise CannotConnectError from err

    raise InvalidSnapshotError("Websocket closed before sending a snapshot")


def _decode_ws_message(message: aiohttp.WSMessage) -> Any | None:
    if message.type in {aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED}:
        return None

    if message.type == aiohttp.WSMsgType.ERROR:
        if message.data is not None:
            raise CannotConnectError(message.data)
        return None

    if message.type != aiohttp.WSMsgType.TEXT:
        return None

    try:
        return json.loads(message.data)
    except json.JSONDecodeError:
        _LOGGER.debug("Ignoring invalid JSON websocket payload: %s", message.data)
        return None


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
