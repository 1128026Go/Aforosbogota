"""
Filtros de calidad para trayectorias normalizadas.

Parámetros por defecto:
  - min_length_m = 5.0
  - max_direction_changes = 20
  - min_net_over_path_ratio = 0.2
"""
from __future__ import annotations

from math import atan2, sqrt
from typing import List

import numpy as np
import pandas as pd


def _path_length(x: np.ndarray, y: np.ndarray) -> float:
    dx = np.diff(x)
    dy = np.diff(y)
    return float(np.sum(np.sqrt(dx * dx + dy * dy)))


def _net_displacement(x: np.ndarray, y: np.ndarray) -> float:
    return float(sqrt((x[-1] - x[0]) ** 2 + (y[-1] - y[0]) ** 2))


def _direction_changes(x: np.ndarray, y: np.ndarray) -> int:
    if len(x) < 3:
        return 0
    angles: List[float] = []
    for i in range(1, len(x)):
        dx = x[i] - x[i - 1]
        dy = y[i] - y[i - 1]
        if dx == 0 and dy == 0:
            continue
        angles.append(atan2(dy, dx))
    changes = 0
    for i in range(1, len(angles)):
        diff = abs(angles[i] - angles[i - 1])
        if diff > 1.0:  # > ~57 grados
            changes += 1
    return changes


def filter_tracks(
    df: pd.DataFrame,
    min_length_m: float = 5.0,
    max_direction_changes: int = 20,
    min_net_over_path_ratio: float = 0.2,
) -> pd.DataFrame:
    """
    Devuelve un DataFrame con solo trayectorias válidas según los parámetros.

    El DataFrame de entrada debe contener: track_id, x, y.
    """
    if df.empty:
        return df

    valid_ids: List[int] = []
    rejected = 0

    for track_id, group in df.groupby("track_id"):
        x = group["x"].to_numpy(dtype=float)
        y = group["y"].to_numpy(dtype=float)
        if len(x) < 2:
            rejected += 1
            continue
        length = _path_length(x, y)
        if length < min_length_m:
            rejected += 1
            continue
        changes = _direction_changes(x, y)
        if changes > max_direction_changes:
            rejected += 1
            continue
        net = _net_displacement(x, y)
        if length == 0:
            rejected += 1
            continue
        ratio = net / length
        if ratio < min_net_over_path_ratio:
            rejected += 1
            continue
        valid_ids.append(track_id)

    filtered = df[df["track_id"].isin(valid_ids)].copy()
    filtered.attrs["rejected_tracks"] = rejected
    return filtered

