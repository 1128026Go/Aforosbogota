"""
Detección de conflictos de tránsito usando TTC aproximado.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import List, Optional

import numpy as np
import pandas as pd


@dataclass
class Conflict:
    ttc_min: float
    pet: Optional[float]
    time_sec: float
    x: float
    y: float
    track_id_1: str
    track_id_2: str
    severity: float
    pair_type: str


def _pair_type(cls1: str, cls2: str) -> str:
    vehicles = {"auto", "bus", "camion", "moto", "bici"}
    if cls1 in vehicles and cls2 in vehicles:
        return "vehicle-vehicle"
    if "peaton" in (cls1, cls2):
        return "vehicle-peaton"
    return f"{cls1}-{cls2}"


def detect_conflicts(
    df: pd.DataFrame,
    fps: float = 30.0,
    distance_threshold: float = 2.0,
    ttc_threshold: float = 1.5,
) -> List[Conflict]:
    """
    Detecta conflictos basados en TTC < ttc_threshold.
    DataFrame debe contener: frame_id, track_id, x, y, vehicle_class.
    """
    if df.empty:
        return []
    df_sorted = df.sort_values(["frame_id", "track_id"])
    conflicts: List[Conflict] = []

    for frame_id in df_sorted["frame_id"].unique():
        frame_data = df_sorted[df_sorted["frame_id"] == frame_id]
        track_ids = frame_data["track_id"].unique()
        if len(track_ids) < 2:
            continue
        for track_a, track_b in combinations(track_ids, 2):
            a_row = frame_data[frame_data["track_id"] == track_a].iloc[0]
            b_row = frame_data[frame_data["track_id"] == track_b].iloc[0]
            dx = float(a_row["x"]) - float(b_row["x"])
            dy = float(a_row["y"]) - float(b_row["y"])
            distance = np.sqrt(dx * dx + dy * dy)
            if distance > distance_threshold:
                continue

            # Aproximación simple: comparar posición en frames adyacentes
            ttc_min = float("inf")
            for offset in (-1, 1):
                neighbor_frame = frame_id + offset
                a_neighbor = df_sorted[(df_sorted["track_id"] == track_a) & (df_sorted["frame_id"] == neighbor_frame)]
                b_neighbor = df_sorted[(df_sorted["track_id"] == track_b) & (df_sorted["frame_id"] == neighbor_frame)]
                if a_neighbor.empty or b_neighbor.empty:
                    continue
                a_pos = a_neighbor.iloc[0]
                b_pos = b_neighbor.iloc[0]
                dx2 = float(a_pos["x"]) - float(b_pos["x"])
                dy2 = float(a_pos["y"]) - float(b_pos["y"])
                distance2 = np.sqrt(dx2 * dx2 + dy2 * dy2)
                delta = distance - distance2
                if delta <= 0:
                    continue
                dt = 1.0 / fps
                ttc = distance / (delta / dt)
                ttc_min = min(ttc_min, ttc)

            if ttc_min == float("inf") or ttc_min > ttc_threshold:
                continue

            time_sec = float(frame_id) / fps
            pair = _pair_type(str(a_row["vehicle_class"]), str(b_row["vehicle_class"]))
            conflicts.append(
                Conflict(
                    ttc_min=ttc_min,
                    pet=None,
                    time_sec=time_sec,
                    x=float(a_row["x"] + b_row["x"]) / 2.0,
                    y=float(a_row["y"] + b_row["y"]) / 2.0,
                    track_id_1=str(track_a),
                    track_id_2=str(track_b),
                    severity=1.0 / max(ttc_min, 0.01),
                    pair_type=pair,
                )
            )
    return conflicts

