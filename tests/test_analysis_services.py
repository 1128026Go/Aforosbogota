"""
Pruebas unitarias para los servicios de análisis avanzado.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from api.services.filters import filter_tracks
from api.services.rilsa_mapping import build_rilsa_rule_map
from api.services.trajectory_processor import calculate_counts_by_interval, assign_tracks_to_movements
from api.services.speeds import summarize_speeds
from api.services.conflicts import detect_conflicts


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    data = {
        "frame_id": [0, 1, 2, 0, 1, 2],
        "track_id": [1, 1, 1, 2, 2, 2],
        "x": [0.0, 0.0, 0.0, 5.0, 5.5, 6.0],
        "y": [0.0, 5.0, 10.0, 0.0, -4.0, -12.0],
        "object_class": ["car", "car", "car", "truck", "truck", "truck"],
    }
    return pd.DataFrame(data)


def test_filter_tracks_removes_short_path(sample_dataframe: pd.DataFrame) -> None:
    # track 1 recorre 10 unidades, track 2 recorre ~12.0
    df = sample_dataframe.copy()
    filtered = filter_tracks(df, min_length_m=6.0)
    assert set(filtered["track_id"].unique()) == {1, 2}
    filtered_strict = filter_tracks(df, min_length_m=11.0)
    assert set(filtered_strict["track_id"].unique()) == {2}


def test_rilsa_mapping_codes() -> None:
    accesses = [
        {"id": "A1", "x": 0.0, "y": 100.0, "cardinal": "N", "count": 10},
        {"id": "A2", "x": 0.0, "y": -100.0, "cardinal": "S", "count": 12},
        {"id": "A3", "x": -100.0, "y": 0.0, "cardinal": "O", "count": 11},
        {"id": "A4", "x": 100.0, "y": 0.0, "cardinal": "E", "count": 9},
    ]
    rilsa_map = build_rilsa_rule_map(accesses)
    lookup = {(rule["origin_id"], rule["dest_id"]): rule["vehicle_code"] for rule in rilsa_map["rules"]}
    assert lookup[("A1", "A2")] == "1"
    assert lookup[("A1", "A4")] == "5"
    assert lookup[("A1", "A3")].startswith("9_")
    assert lookup[("A1", "A1")].startswith("10_")


def test_calculate_counts_by_interval(tmp_path: Path, sample_dataframe: pd.DataFrame) -> None:
    parquet_path = tmp_path / "df.parquet"
    sample_dataframe.to_parquet(parquet_path)
    accesses = [
        {"id": "A1", "x": 0.0, "y": 100.0, "cardinal": "N", "count": 3},
        {"id": "A2", "x": 0.0, "y": -100.0, "cardinal": "S", "count": 3},
    ]
    rilsa_map = build_rilsa_rule_map(accesses)
    counts_df = calculate_counts_by_interval(
        parquet_path,
        accesses,
        rilsa_map,
        interval_minutes=15,
        fps=30.0,
        min_length_m=3.0,
    )
    assert not counts_df.empty
    assert counts_df["count"].sum() == 2
    assert all(col in counts_df.columns for col in ["interval_start", "interval_end", "rilsa_code"])


def test_assign_tracks_to_movements_ignores_unknown(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "frame_id": [0, 1, 2, 0, 1, 2, 0, 1],
            "track_id": [1, 1, 1, 2, 2, 2, 3, 3],
            "x": [0.0, 0.0, 0.0, 5.0, 5.5, 6.0, 30.0, 32.0],
            "y": [0.0, 5.0, 10.0, 0.0, -4.0, -12.0, 30.0, 28.0],
            "object_class": ["car", "car", "car", "truck", "truck", "truck", "dog", "dog"],
        }
    )
    accesses = [
        {"id": "A1", "x": 0.0, "y": 100.0, "cardinal": "N", "count": 3},
        {"id": "A2", "x": 0.0, "y": -100.0, "cardinal": "S", "count": 3},
    ]
    rilsa_map = build_rilsa_rule_map(accesses)
    filtered, meta_df = assign_tracks_to_movements(
        df,
        accesses,
        rilsa_map,
        fps=30.0,
        min_length_m=3.0,
    )
    assert set(meta_df["track_id"]) == {1, 2}
    assert 3 not in set(filtered["track_id"])


def test_summarize_speeds() -> None:
    speeds_df = pd.DataFrame(
        {
            "track_id": [1, 2],
            "mean_speed_mps": [5.0, 8.0],
        }
    )
    meta_df = pd.DataFrame(
        {
            "track_id": [1, 2],
            "rilsa_code": ["1", "5"],
            "vehicle_class": ["auto", "bus"],
        }
    )
    summary = summarize_speeds(speeds_df, meta_df)
    assert ("1", "auto") in summary
    assert summary[("1", "auto")]["mean_kmh"] == pytest.approx(18.0)


def test_detect_conflicts() -> None:
    df = pd.DataFrame(
        {
            "frame_id": [0, 0, 1, 1],
            "track_id": [1, 2, 1, 2],
            "x": [0.0, 1.0, 0.2, 0.8],
            "y": [0.0, 0.0, 0.0, 0.0],
            "vehicle_class": ["auto", "auto", "auto", "auto"],
        }
    )
    conflicts = detect_conflicts(df, fps=30.0, distance_threshold=1.5, ttc_threshold_s=2.0)
    assert len(conflicts) >= 1
    assert conflicts[0].pair_type == "vehicle-vehicle"

