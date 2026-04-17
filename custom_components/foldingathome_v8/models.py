"""Typed normalized models for Folding@home client state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

STATE_RUNNING = "running"
STATE_PAUSED = "paused"
STATE_FINISHING = "finishing"
STATE_WAITING = "waiting"
STATE_DISCONNECTED = "disconnected"

ACTIVE_TERMINAL_STATES = {"DUMPED"}
RUNNING_STATES = {"RUN", "RUNNING"}
WAITING_STATES = {"ASSIGN", "READY", "DOWNLOAD", "WAIT", "PAUSE", "PAUSED"}
FINISHING_STATES = {"FINISH", "FINISHING"}


@dataclass(frozen=True, slots=True)
class ClientInfo:
    """Basic FAH client information."""

    client_id: str | None
    machine_name: str
    hostname: str | None
    version: str | None
    os: str | None
    cpu: str | None


@dataclass(frozen=True, slots=True)
class GroupConfig:
    """Default group configuration."""

    on_idle: bool
    on_battery: bool
    keep_awake: bool
    paused: bool
    finish: bool
    enabled_cpu_count: int | None
    enabled_gpu_count: int | None


@dataclass(frozen=True, slots=True)
class GroupStatus:
    """Runtime status fields for the default group."""

    wait: str | None
    failed_work_units: int
    lost_work_units: int


@dataclass(frozen=True, slots=True)
class WorkUnit:
    """Normalized active work unit."""

    unit_id: str
    number: int | None
    group: str
    state: str | None
    paused: bool
    progress: float | None
    project: int | None
    run: int | None
    clone: int | None
    gen: int | None
    ppd: int | None
    eta: str | None
    timeout: int | None
    deadline: int | None
    cpus: int | None
    gpus: tuple[str | int, ...]
    core_type: str | None
    wait: str | None
    pause_reason: str | None
    frames: int | None
    run_time: int | None

    @property
    def progress_percent(self) -> float | None:
        """Return progress as percent for Home Assistant sensors."""
        if self.progress is None:
            return None
        return round(self.progress * 100, 1)


@dataclass(frozen=True, slots=True)
class NormalizedClientData:
    """Single normalized snapshot for the default resource group."""

    available: bool
    host: str
    port: int
    info: ClientInfo | None
    group_name: str
    group_config: GroupConfig
    group_status: GroupStatus
    client_state: str
    cpu_count: int | None
    gpu_count: int | None
    overall_progress_percent: float
    active_work_units: tuple[WorkUnit, ...]
    total_ppd: int
    raw_state: Mapping[str, Any]

    @property
    def client_key(self) -> str:
        """Return a stable key for the device registry."""
        if self.info and self.info.client_id:
            return self.info.client_id
        return f"{self.host}:{self.port}"

    @property
    def title(self) -> str:
        """Return a user-facing title for the FAH client."""
        if self.info and self.info.machine_name:
            return self.info.machine_name
        return self.host

    @property
    def is_running(self) -> bool:
        """Return whether the client is actively folding."""
        return self.client_state == STATE_RUNNING

    @property
    def is_paused(self) -> bool:
        """Return whether the client is paused."""
        return self.client_state == STATE_PAUSED

    @property
    def is_finishing(self) -> bool:
        """Return whether the client is finishing current work."""
        return self.client_state == STATE_FINISHING

    @property
    def has_active_work(self) -> bool:
        """Return whether the client currently has active work units."""
        return bool(self.active_work_units)

    @property
    def only_when_idle(self) -> bool:
        """Return whether folding is configured to run only when idle."""
        return self.group_config.on_idle

    @property
    def allow_on_battery(self) -> bool:
        """Return whether folding is allowed while on battery."""
        return self.group_config.on_battery

    @property
    def keep_awake(self) -> bool:
        """Return whether FAH is configured to keep the machine awake."""
        return self.group_config.keep_awake

    @property
    def has_failed_work_units(self) -> bool:
        """Return whether any work units have failed."""
        return self.group_status.failed_work_units > 0

    @property
    def has_lost_work_units(self) -> bool:
        """Return whether any work units have been lost."""
        return self.group_status.lost_work_units > 0


def normalize_client_data(
    raw_state: Mapping[str, Any] | None,
    *,
    available: bool,
    host: str,
    port: int,
) -> NormalizedClientData:
    """Normalize a raw websocket snapshot for Home Assistant entities."""
    if raw_state is None:
        return NormalizedClientData(
            available=available,
            host=host,
            port=port,
            info=None,
            group_name="",
            group_config=GroupConfig(
                on_idle=False,
                on_battery=False,
                keep_awake=False,
                paused=False,
                finish=False,
                enabled_cpu_count=None,
                enabled_gpu_count=None,
            ),
            group_status=GroupStatus(
                wait=None,
                failed_work_units=0,
                lost_work_units=0,
            ),
            client_state=STATE_DISCONNECTED if not available else STATE_WAITING,
            cpu_count=None,
            gpu_count=None,
            overall_progress_percent=0.0,
            active_work_units=(),
            total_ppd=0,
            raw_state={},
        )

    info_data = raw_state.get("info") if isinstance(raw_state, Mapping) else None
    info = _normalize_info(info_data) if isinstance(info_data, Mapping) else None

    group_config = _default_group_config(raw_state)
    group_status = _default_group_status(raw_state)
    work_units = tuple(_iter_default_group_units(raw_state))
    total_ppd = sum(unit.ppd or 0 for unit in work_units)
    cpu_count = _extract_cpu_count(raw_state, work_units)
    gpu_count = _extract_gpu_count(raw_state, work_units)
    overall_progress_percent = _extract_overall_progress_percent(work_units)

    return NormalizedClientData(
        available=available,
        host=host,
        port=port,
        info=info,
        group_name="",
        group_config=group_config,
        group_status=group_status,
        client_state=_derive_client_state(
            available=available,
            group_config=group_config,
            work_units=work_units,
        ),
        cpu_count=cpu_count,
        gpu_count=gpu_count,
        overall_progress_percent=overall_progress_percent,
        active_work_units=work_units,
        total_ppd=total_ppd,
        raw_state=raw_state,
    )


def _normalize_info(info: Mapping[str, Any]) -> ClientInfo:
    return ClientInfo(
        client_id=_as_str(info.get("id")),
        machine_name=_as_str(info.get("mach_name")) or _as_str(info.get("hostname")) or "Folding@home",
        hostname=_as_str(info.get("hostname")),
        version=_as_str(info.get("version")),
        os=_as_str(info.get("os")),
        cpu=_as_str(info.get("cpu_brand")) or _as_str(info.get("cpu")),
    )


def _default_group_config(raw_state: Mapping[str, Any]) -> GroupConfig:
    config = _effective_config(raw_state)
    enabled_gpus = config.get("gpus")
    enabled_gpu_count = None
    if isinstance(enabled_gpus, Mapping):
        enabled_gpu_count = sum(
            1
            for gpu in enabled_gpus.values()
            if isinstance(gpu, Mapping) and gpu.get("enabled", False)
        )

    return GroupConfig(
        on_idle=bool(config.get("on_idle", False)),
        on_battery=bool(config.get("on_battery", False)),
        keep_awake=bool(config.get("keep_awake", False)),
        paused=bool(config.get("paused", False)),
        finish=bool(config.get("finish", False)),
        enabled_cpu_count=_as_int(config.get("cpus")),
        enabled_gpu_count=enabled_gpu_count,
    )


def _default_group_status(raw_state: Mapping[str, Any]) -> GroupStatus:
    group = _default_group_state(raw_state)
    return GroupStatus(
        wait=_as_str(group.get("wait")),
        failed_work_units=_as_int(group.get("failed_wus")) or 0,
        lost_work_units=_as_int(group.get("lost_wus")) or 0,
    )


def _default_group_state(raw_state: Mapping[str, Any]) -> Mapping[str, Any]:
    groups = raw_state.get("groups")
    if isinstance(groups, Mapping):
        default_group = groups.get("")
        if isinstance(default_group, Mapping):
            return default_group
    return {}


def _effective_config(raw_state: Mapping[str, Any]) -> Mapping[str, Any]:
    default_group = _default_group_state(raw_state)
    group_config = default_group.get("config")
    if isinstance(group_config, Mapping):
        return group_config

    config = raw_state.get("config")
    if isinstance(config, Mapping):
        return config

    return {}


def _extract_cpu_count(
    raw_state: Mapping[str, Any], work_units: tuple[WorkUnit, ...]
) -> int | None:
    info = raw_state.get("info")
    if isinstance(info, Mapping):
        for key in (
            "cpus",
            "cpu_count",
            "cpus_count",
            "cpu_threads",
            "cpus_available",
        ):
            value = _as_int(info.get(key))
            if value is not None:
                return value

    config = _effective_config(raw_state)
    for key in ("cpus", "cpu", "cpu_count"):
        value = _as_int(config.get(key))
        if value is not None:
            return value

    counts = [unit.cpus for unit in work_units if unit.cpus is not None]
    if counts:
        return max(counts)

    return None


def _extract_gpu_count(
    raw_state: Mapping[str, Any], work_units: tuple[WorkUnit, ...]
) -> int | None:
    info = raw_state.get("info")
    if isinstance(info, Mapping):
        for key in ("gpus", "gpu_count", "gpus_count"):
            value = info.get(key)
            if isinstance(value, list):
                return len(value)
            parsed = _as_int(value)
            if parsed is not None:
                return parsed

    for key in ("gpus", "gpu", "devices"):
        value = raw_state.get(key)
        if isinstance(value, list):
            return len(value)

    gpu_ids = {gpu for unit in work_units for gpu in unit.gpus}
    if gpu_ids:
        return len(gpu_ids)

    return None


def _extract_overall_progress_percent(work_units: tuple[WorkUnit, ...]) -> float:
    if not work_units:
        return 0.0

    progress_values = [
        unit.progress_percent if unit.progress_percent is not None else 0.0
        for unit in work_units
    ]
    return round(sum(progress_values) / len(progress_values), 1)


def _iter_default_group_units(raw_state: Mapping[str, Any]) -> list[WorkUnit]:
    units = raw_state.get("units")
    if not isinstance(units, list):
        return []

    normalized: list[WorkUnit] = []
    for item in units:
        if not isinstance(item, Mapping):
            continue

        group = _as_str(item.get("group")) or ""
        if group != "":
            continue

        state = (_as_str(item.get("state")) or "").upper()
        if state in ACTIVE_TERMINAL_STATES:
            continue

        unit_id = _as_str(item.get("id"))
        if not unit_id:
            continue

        assignment = item.get("assignment")
        wu = item.get("wu")
        core = assignment.get("core") if isinstance(assignment, Mapping) else None

        normalized.append(
            WorkUnit(
                unit_id=unit_id,
                number=_as_int(item.get("number")),
                group=group,
                state=_as_str(item.get("state")),
                paused=bool(item.get("paused", False)),
                progress=_extract_unit_progress(item),
                project=_mapping_int(assignment, "project"),
                run=_mapping_int(wu, "run"),
                clone=_mapping_int(wu, "clone"),
                gen=_mapping_int(wu, "gen"),
                ppd=_as_int(item.get("ppd")),
                eta=_as_str(item.get("eta")),
                timeout=_mapping_int(assignment, "timeout"),
                deadline=_mapping_int(assignment, "deadline"),
                cpus=_as_int(item.get("cpus")),
                gpus=_tuple_gpus(item.get("gpus")),
                core_type=_mapping_str(core, "type"),
                wait=_as_str(item.get("wait")),
                pause_reason=_as_str(item.get("pause_reason")),
                frames=_as_int(item.get("frames")),
                run_time=_as_int(item.get("run_time")),
            )
        )

    return normalized


def _extract_unit_progress(unit: Mapping[str, Any]) -> float | None:
    for key in ("wu_progress", "progress"):
        value = _as_float(unit.get(key))
        if value is None:
            continue
        if value > 1:
            return value / 100
        return value
    return None


def _derive_client_state(
    *,
    available: bool,
    group_config: GroupConfig,
    work_units: tuple[WorkUnit, ...],
) -> str:
    if not available:
        return STATE_DISCONNECTED

    if group_config.paused or (work_units and all(unit.paused for unit in work_units)):
        return STATE_PAUSED

    if group_config.finish or any(_is_finishing(unit) for unit in work_units):
        return STATE_FINISHING

    if any(_is_running(unit) for unit in work_units):
        return STATE_RUNNING

    if any(_is_waiting(unit) for unit in work_units):
        return STATE_WAITING

    if not work_units:
        return STATE_PAUSED if group_config.paused else STATE_WAITING

    return STATE_WAITING


def _is_running(unit: WorkUnit) -> bool:
    return not unit.paused and ((unit.state or "").upper() in RUNNING_STATES)


def _is_waiting(unit: WorkUnit) -> bool:
    state = ((unit.state or "")).upper()
    return bool(unit.wait) or state in WAITING_STATES


def _is_finishing(unit: WorkUnit) -> bool:
    state = ((unit.state or "")).upper()
    return "FINISH" in state or state in FINISHING_STATES


def _mapping_int(value: Any, key: str) -> int | None:
    if not isinstance(value, Mapping):
        return None
    return _as_int(value.get(key))


def _mapping_str(value: Any, key: str) -> str | None:
    if not isinstance(value, Mapping):
        return None
    return _as_str(value.get(key))


def _tuple_gpus(value: Any) -> tuple[str | int, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, (str, int)))


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
