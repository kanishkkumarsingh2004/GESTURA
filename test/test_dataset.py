"""Integration-style test for dataset loading."""

from __future__ import annotations

from typing import Any

from data.dataset import load_class_mapping_from_root


def test_dataset_derives_class_mapping(tmp_path: Any) -> None:
    (tmp_path / "HELLO").mkdir(parents=True)
    (tmp_path / "YES").mkdir(parents=True)
    mapping = load_class_mapping_from_root(tmp_path)
    assert mapping == {"HELLO": 0, "YES": 1}
