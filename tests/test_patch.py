"""Tests for FAH websocket patch handling."""

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


patch = _load_module("fah_patch", "custom_components/foldingathome_v8/patch.py")


def test_apply_update_sets_scalar_value() -> None:
    snapshot = {"config": {"paused": True}}
    patch.apply_update(snapshot, ["config", "paused", False])
    assert snapshot["config"]["paused"] is False


def test_apply_update_appends_to_list() -> None:
    snapshot = {"units": []}
    patch.apply_update(snapshot, ["units", -1, {"id": "abc"}])
    assert snapshot == {"units": [{"id": "abc"}]}


def test_apply_update_concatenates_lists() -> None:
    snapshot = {"units": [{"id": "a"}]}
    patch.apply_update(snapshot, ["units", -2, [{"id": "b"}, {"id": "c"}]])
    assert snapshot["units"] == [{"id": "a"}, {"id": "b"}, {"id": "c"}]


def test_apply_update_deletes_keys_and_list_items() -> None:
    snapshot = {"config": {"paused": True}, "units": [{"id": "a"}, {"id": "b"}]}
    patch.apply_update(snapshot, ["config", "paused", None])
    patch.apply_update(snapshot, ["units", 0, None])
    assert "paused" not in snapshot["config"]
    assert snapshot["units"] == [{"id": "b"}]


def test_normalize_object_rewrites_hyphenated_keys() -> None:
    payload = {"on-battery": True, "groups": {"": {"keep-awake": True}}}
    assert patch.normalize_object(payload) == {
        "on_battery": True,
        "groups": {"": {"keep_awake": True}},
    }
