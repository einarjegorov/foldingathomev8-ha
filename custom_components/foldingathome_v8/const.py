"""Constants for the Folding@home v8 integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import CONF_HOST, CONF_PORT, Platform

DOMAIN = "foldingathome_v8"
NAME = "Folding@home v8"
DEFAULT_PORT = 7396
WS_PATH = "/api/websocket"
MANUFACTURER = "Folding@home"

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
]

DEFAULT_GROUP = ""
DEFAULT_GROUP_LABEL = "default"

CLIENT_READY_TIMEOUT = 10
RECONNECT_INITIAL_DELAY = 1
RECONNECT_MAX_DELAY = 60
FINISH_RESUME_TIMEOUT = 10
PROBE_TIMEOUT = timedelta(seconds=10)

STATE_RUNNING = "running"
STATE_PAUSED = "paused"
STATE_FINISHING = "finishing"
STATE_WAITING = "waiting"
STATE_DISCONNECTED = "disconnected"

CLIENT_STATES = [
    STATE_RUNNING,
    STATE_PAUSED,
    STATE_FINISHING,
    STATE_WAITING,
    STATE_DISCONNECTED,
]
CLIENT_STATE_OPTIONS = [state.title() for state in CLIENT_STATES]

ATTR_WORK_UNIT_ID = "work_unit_id"
ATTR_WORK_UNIT_NUMBER = "work_unit_number"
ATTR_PROJECT = "project"
ATTR_RUN = "run"
ATTR_CLONE = "clone"
ATTR_GEN = "gen"
ATTR_PPD = "ppd"
ATTR_ETA = "eta"
ATTR_TIMEOUT = "timeout"
ATTR_DEADLINE = "deadline"
ATTR_CPUS = "cpus"
ATTR_GPUS = "gpus"
ATTR_CORE = "core"
ATTR_WAIT = "wait"
ATTR_STATUS = "status"
ATTR_PAUSE_REASON = "pause_reason"
ATTR_FRAMES = "frames"
ATTR_RUN_TIME = "run_time"

SENSITIVE_DIAGNOSTIC_KEYS = {
    CONF_HOST,
    "host",
    "hostname",
    "id",
    "account",
    "token",
    "passkey",
    "node",
}
