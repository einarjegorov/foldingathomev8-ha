"""Tests for normalized client data helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _load_module(name: str, relative_path: str):
    path = Path(__file__).resolve().parents[1] / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


models = _load_module("fah_models", "custom_components/foldingathome_v8/models.py")


def test_normalize_client_data_supports_root_config_snapshot() -> None:
    raw = {
        "info": {"id": "client-1", "mach_name": "Node A", "version": "8.4.6"},
        "config": {"paused": True, "finish": False, "cpus": 12},
        "units": [],
    }

    data = models.normalize_client_data(raw, available=True, host="fah", port=7396)

    assert data.client_key == "client-1"
    assert data.title == "Node A"
    assert data.client_state == models.STATE_PAUSED
    assert data.is_paused is True
    assert data.is_running is False
    assert data.is_finishing is False
    assert data.has_active_work is False
    assert data.cpu_count == 12
    assert data.overall_progress_percent == 0.0
    assert data.total_ppd == 0


def test_normalize_client_data_supports_group_snapshot_and_filters_default_group() -> None:
    raw = {
        "info": {
            "id": "client-2",
            "mach_name": "Node B",
            "gpu_count": 2,
            "cpus": 16,
        },
        "groups": {
            "": {"config": {"paused": False, "finish": True}},
            "alt": {"config": {"paused": True, "finish": False}},
        },
        "units": [
            {
                "id": "wu-default",
                "group": "",
                "state": "RUN",
                "progress": 0.5,
                "ppd": 12345,
                "assignment": {"project": 18240, "timeout": 10, "deadline": 20},
                "wu": {"run": 1, "clone": 2, "gen": 3},
            },
            {
                "id": "wu-alt",
                "group": "alt",
                "state": "RUN",
                "progress": 0.1,
                "ppd": 999,
            },
        ],
    }

    data = models.normalize_client_data(raw, available=True, host="fah", port=7396)

    assert data.client_state == models.STATE_FINISHING
    assert data.is_finishing is True
    assert data.has_active_work is True
    assert data.cpu_count == 16
    assert data.gpu_count == 2
    assert data.overall_progress_percent == 50.0
    assert len(data.active_work_units) == 1
    assert data.active_work_units[0].unit_id == "wu-default"
    assert data.total_ppd == 12345


def test_normalize_client_data_marks_disconnected_clients() -> None:
    raw = {
        "info": {"id": "client-3", "mach_name": "Node C"},
        "config": {"paused": False, "finish": False},
        "units": [{"id": "wu-1", "state": "RUN", "progress": 0.2}],
    }

    data = models.normalize_client_data(raw, available=False, host="fah", port=7396)

    assert data.client_state == models.STATE_DISCONNECTED
    assert data.is_running is False
    assert data.is_paused is False
    assert data.is_finishing is False


def test_normalize_client_data_prefers_paused_over_running_units() -> None:
    raw = {
        "info": {"id": "client-4", "mach_name": "Node D"},
        "config": {"paused": True, "finish": False},
        "units": [
            {
                "id": "wu-1",
                "state": "RUN",
                "paused": False,
                "progress": 0.5,
            }
        ],
    }

    data = models.normalize_client_data(raw, available=True, host="fah", port=7396)

    assert data.client_state == models.STATE_PAUSED


def test_normalize_client_data_falls_back_to_active_work_units_for_gpu_count() -> None:
    raw = {
        "info": {"id": "client-5", "mach_name": "Node E"},
        "config": {"paused": False, "finish": False},
        "units": [
            {"id": "wu-1", "state": "RUN", "gpus": [0]},
            {"id": "wu-2", "state": "RUN", "gpus": [1]},
            {"id": "wu-3", "state": "RUN", "gpus": [1]},
        ],
    }

    data = models.normalize_client_data(raw, available=True, host="fah", port=7396)

    assert data.gpu_count == 2


def test_normalize_client_data_averages_progress_across_active_work_units() -> None:
    raw = {
        "info": {"id": "client-6", "mach_name": "Node F"},
        "config": {"paused": False, "finish": False},
        "units": [
            {"id": "wu-1", "state": "RUN", "progress": 0.25},
            {"id": "wu-2", "state": "RUN", "progress": 0.75},
        ],
    }

    data = models.normalize_client_data(raw, available=True, host="fah", port=7396)

    assert data.overall_progress_percent == 50.0


def test_normalize_client_data_prefers_wu_progress_over_zero_progress() -> None:
    raw = {
        "info": {"id": "client-7", "mach_name": "Node G"},
        "config": {"paused": False, "finish": False},
        "units": [
            {
                "id": "wu-1",
                "state": "RUN",
                "progress": 0,
                "wu_progress": 0.091,
            }
        ],
    }

    data = models.normalize_client_data(raw, available=True, host="fah", port=7396)

    assert data.overall_progress_percent == 9.1
