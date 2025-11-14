"""
Procesa trayectorias normalizadas para calcular volúmenes por intervalo,
movimiento RILSA y clase vehicular.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from api.services import filters, rilsa_mapping

TRACKING_REQUIRED_MESSAGE = (
    "Este archivo PKL contiene solo detecciones cuadro a cuadro (sin trayectorias / track_id). "
    "Para generar aforos por movimientos se requiere un PKL con tracking (trayectorias no vacías)."
)


class MissingTrajectoryDataError(ValueError):
    """Error específico para cuando no hay datos de tracking utilizables."""


VEHICLE_CLASS_MAP = {
    "bus": "bus",
    "coach": "bus",
    "microbus": "bus",
    "truck": "camion",
    "camion": "camion",
    "lorry": "camion",
    "trailer": "camion",
    "pickup": "camion",
    "bicycle": "bici",
    "bike": "bici",
    "bici": "bici",
    "cyclist": "bici",
    "cycle": "bici",
    "motorcycle": "moto",
    "motorbike": "moto",
    "scooter": "moto",
    "moto": "moto",
    "car": "auto",
    "auto": "auto",
    "vehiculo": "auto",
    "vehicle": "auto",
    "suv": "auto",
    "sedan": "auto",
    "van": "auto",
    "person": "peaton",
    "pedestrian": "peaton",
    "peaton": "peaton",
    "people": "peaton",
}


def _nearest_access(x: float, y: float, accesses: List[Dict]) -> str:
    """Devuelve el id del acceso más cercano a la coordenada dada."""
    min_dist = float("inf")
    closest = ""
    for acc in accesses:
        dx = x - float(acc["x"])
        dy = y - float(acc["y"])
        dist = dx * dx + dy * dy
        if dist < min_dist:
            min_dist = dist
            closest = str(acc["id"])
    return closest


def _classify_vehicle(label: str) -> str:
    """Normaliza la clase del objeto a auto/bus/camion/etc."""
    normalized = label.lower()
    for key, value in VEHICLE_CLASS_MAP.items():
        if key in normalized:
            return value
    return "ignore"


def classify_vehicle(label: str) -> str:
    """Función exportada para otras partes del backend."""
    return _classify_vehicle(label)


def _build_rilsa_lookups(accesses: List[Dict], rilsa_map: Dict) -> Tuple[Dict[Tuple[str, str], str], Dict[Tuple[str, str], str]]:
    """Construye tablas de consulta para códigos vehiculares y peatonales."""
    ordered = rilsa_mapping.order_accesses_for_rilsa(accesses)
    veh_lookup, ped_lookup = rilsa_mapping.build_lookup_tables(rilsa_map)
    return veh_lookup, ped_lookup


def assign_tracks_to_movements(
    df: pd.DataFrame,
    accesses: List[Dict],
    rilsa_map: Dict,
    fps: float = 30.0,
    min_length_m: float = 5.0,
    max_direction_changes: int = 20,
    min_net_over_path_ratio: float = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filtra trayectorias y asigna metadata (rilsa_code, vehicle_class) por track.

    Retorna:
      - DataFrame filtrado.
      - DataFrame con columnas [track_id, rilsa_code, vehicle_class, interval_start, interval_end].
    """
    _ensure_tracks_available(df)
    filtered = filters.filter_tracks(
        df,
        min_length_m=min_length_m,
        max_direction_changes=max_direction_changes,
        min_net_over_path_ratio=min_net_over_path_ratio,
    )
    veh_lookup, ped_lookup = _build_rilsa_lookups(accesses, rilsa_map)

    records = []
    valid_track_ids = set()
    for track_id, group in filtered.groupby("track_id"):
        ordered = group.sort_values("frame_id")
        start = ordered.iloc[0]
        end = ordered.iloc[-1]
        origin_id = _nearest_access(float(start["x"]), float(start["y"]), accesses)
        dest_id = _nearest_access(float(end["x"]), float(end["y"]), accesses)
        vehicle_class = _classify_vehicle(str(start.get("object_class", "")))
        if vehicle_class == "ignore":
            continue
        key = (origin_id, dest_id)
        if vehicle_class == "peaton":
            rilsa_code = ped_lookup.get(key, f"P{origin_id}")
        else:
            rilsa_code = veh_lookup.get(key, f"99_{origin_id}_{dest_id}")
        records.append(
            {
                "track_id": track_id,
                "rilsa_code": rilsa_code,
                "vehicle_class": vehicle_class,
                "frame_start": int(start["frame_id"]),
            }
        )
        valid_track_ids.add(track_id)
    meta_df = pd.DataFrame(records)
    if valid_track_ids:
        filtered = filtered[filtered["track_id"].isin(valid_track_ids)]
    else:
        filtered = filtered.iloc[0:0]
    return filtered, meta_df


def calculate_counts_by_interval(
    parquet_path: Path,
    accesses: List[Dict],
    rilsa_map: Dict,
    interval_minutes: int = 15,
    fps: float = 30.0,
    min_length_m: float = 5.0,
    max_direction_changes: int = 20,
    min_net_over_path_ratio: float = 0.2,
) -> pd.DataFrame:
    """
    Calcula un DataFrame con las columnas:
      interval_start, interval_end, rilsa_code, vehicle_class, count
    """
    df = pd.read_parquet(parquet_path)
    if df.empty:
        return pd.DataFrame(columns=["interval_start", "interval_end", "rilsa_code", "vehicle_class", "count"])
    _ensure_tracks_available(df)

    filtered, meta_df = assign_tracks_to_movements(
        df,
        accesses,
        rilsa_map,
        fps=fps,
        min_length_m=min_length_m,
        max_direction_changes=max_direction_changes,
        min_net_over_path_ratio=min_net_over_path_ratio,
    )

    results = defaultdict(int)
    for _, row in meta_df.iterrows():
        interval_index = int((row["frame_start"] / fps) // interval_minutes)
        interval_start = interval_index * interval_minutes
        interval_end = interval_start + interval_minutes
        results[(interval_start, interval_end, row["rilsa_code"], row["vehicle_class"])] += 1

    rows = []
    for (interval_start, interval_end, rilsa_code, vclass), count in results.items():
        rows.append(
            {
                "interval_start": interval_start,
                "interval_end": interval_end,
                "rilsa_code": rilsa_code,
                "vehicle_class": vclass,
                "count": count,
            }
        )
    return pd.DataFrame(rows)


def ensure_tracks_available(df: pd.DataFrame) -> None:
    """
    Valida que existan columnas de tracking antes de ejecutar análisis.
    """
    _ensure_tracks_available(df)


def _ensure_tracks_available(df: pd.DataFrame) -> None:
    if "track_id" not in df.columns:
        raise MissingTrajectoryDataError(TRACKING_REQUIRED_MESSAGE)
    track_series = df["track_id"].dropna()
    if track_series.empty:
        raise MissingTrajectoryDataError(TRACKING_REQUIRED_MESSAGE)

