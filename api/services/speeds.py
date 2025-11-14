"""
Cálculo de velocidades promedio por trayectoria y estadísticos agregados.
"""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd


def compute_track_speeds(df: pd.DataFrame, fps: float = 30.0, pixel_to_meter: float = 1.0) -> pd.DataFrame:
    """
    Devuelve DataFrame con columnas:
      track_id, mean_speed_mps
    """
    records = []
    for track_id, group in df.groupby("track_id"):
        ordered = group.sort_values("frame_id")
        if len(ordered) < 2:
            continue
        x = ordered["x"].to_numpy(dtype=float) * pixel_to_meter
        y = ordered["y"].to_numpy(dtype=float) * pixel_to_meter
        frames = ordered["frame_id"].to_numpy(dtype=float)
        dx = np.diff(x)
        dy = np.diff(y)
        dt = np.diff(frames) / fps
        valid = dt > 0
        if not np.any(valid):
            continue
        distances = np.sqrt(dx[valid] ** 2 + dy[valid] ** 2)
        speeds = distances / dt[valid]
        if speeds.size == 0:
            continue
        records.append({"track_id": track_id, "mean_speed_mps": float(np.mean(speeds))})
    return pd.DataFrame(records)


def summarize_speeds(speeds_df: pd.DataFrame, meta_df: pd.DataFrame) -> Dict[Tuple[str, str], Dict[str, float]]:
    """
    speeds_df: track_id, mean_speed_mps
    meta_df:   track_id, rilsa_code, vehicle_class
    Retorna dict {(rilsa_code, vehicle_class): stats}
    """
    if speeds_df.empty or meta_df.empty:
        return {}
    merged = speeds_df.merge(meta_df, on="track_id", how="inner")
    summary: Dict[Tuple[str, str], Dict[str, float]] = {}
    for (rilsa_code, vehicle_class), group in merged.groupby(["rilsa_code", "vehicle_class"]):
        kmh = group["mean_speed_mps"].to_numpy(dtype=float) * 3.6
        if kmh.size == 0:
            continue
        summary[(str(rilsa_code), str(vehicle_class))] = {
            "count": int(kmh.size),
            "mean_kmh": float(np.mean(kmh)),
            "median_kmh": float(np.median(kmh)),
            "p85_kmh": float(np.percentile(kmh, 85)),
            "min_kmh": float(np.min(kmh)),
            "max_kmh": float(np.max(kmh)),
        }
    return summary

