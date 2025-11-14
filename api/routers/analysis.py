"""
Endpoints de análisis avanzado: volúmenes, velocidades y conflictos.

Ejemplos de respuesta:

- /analysis/{dataset_id}/volumes
  ```
  {
    "dataset_id": "demo",
    "interval_minutes": 15,
    "totals_by_interval": [
      {"interval_start": 0, "interval_end": 15, "autos": 10, "buses": 1, "camiones": 0,
       "motos": 3, "bicis": 2, "peatones": 1, "total": 17}
    ],
    "movements": [
      {"rilsa_code": "1", "description": "Movimiento 1", "rows": [...]}
    ]
  }
  ```

- /analysis/{dataset_id}/speeds
  ```
  {
    "dataset_id": "demo",
    "per_movement": [
      {
        "rilsa_code": "1",
        "description": "Movimiento 1",
        "vehicle_class": "auto",
        "stats": {"count": 12, "mean_kmh": 32.5, "median_kmh": 31.0,
                  "p85_kmh": 38.7, "min_kmh": 20.1, "max_kmh": 45.2}
      }
    ]
  }
  ```

- /analysis/{dataset_id}/conflicts
  ```
  {
    "dataset_id": "demo",
    "total_conflicts": 2,
    "events": [
      {"ttc_min": 1.2, "pet": null, "time_sec": 45.0, "x": 120.3, "y": 340.1,
       "track_id_1": "5", "track_id_2": "18", "severity": 0.83, "pair_type": "vehicle-vehicle"}
    ]
  }
  ```
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api.models.schemas import (
    ConflictEvent,
    ConflictsResponse,
    MovementSpeedStats,
    MovementVolumeTable,
    SpeedStats,
    SpeedsResponse,
    VolumeRow,
    ViolationSummary,
    ViolationsResponse,
    VolumesResponse,
)
from api.routers.datasets import _dataset_dir
from api.services import (
    ConfigPersistenceService,
    MissingTrajectoryDataError,
    assign_tracks_to_movements,
    calculate_counts_by_interval,
    classify_vehicle,
    detect_conflicts,
    build_volume_tables,
    compute_track_speeds,
    ensure_tracks_available,
    load_analysis_settings,
    summarize_speeds,
    summarize_violations,
)

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


def _normalized_path(dataset_id: str) -> Path:
    return _dataset_dir(dataset_id) / "normalized.parquet"


def _cardinals_path(dataset_id: str) -> Path:
    return _dataset_dir(dataset_id) / "cardinals.json"


def _rilsa_map_path(dataset_id: str) -> Path:
    return _dataset_dir(dataset_id) / "rilsa_map.json"


def _load_analysis_inputs(dataset_id: str):
    """
    Carga el parquet normalizado y la configuración de accesos/RILSA.
    """
    normalized = _normalized_path(dataset_id)
    cardinals_file = _cardinals_path(dataset_id)
    rilsa_file = _rilsa_map_path(dataset_id)
    if not normalized.exists() or not cardinals_file.exists() or not rilsa_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset sin datos normalizados o configuración RILSA.",
        )
    with cardinals_file.open("r", encoding="utf-8") as fh:
        accesses = json.load(fh)
    with rilsa_file.open("r", encoding="utf-8") as fh:
        rilsa_map = json.load(fh)
    return normalized, accesses, rilsa_map


def _raise_tracking_http_error(exc: MissingTrajectoryDataError) -> None:
    raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{dataset_id}/qc_summary")
def get_qc_summary(dataset_id: str) -> dict:
    """
    Proporciona métricas rápidas de control de calidad sobre los conteos.
    """
    settings = load_analysis_settings(dataset_id)
    normalized, accesses, rilsa_map = _load_analysis_inputs(dataset_id)
    df = pd.read_parquet(normalized)
    if df.empty:
        return {
            "dataset_id": dataset_id,
            "total_tracks_raw": 0,
            "counted_tracks": 0,
            "counts_by_class": {
                key: 0
                for key in ["auto", "bus", "camion", "moto", "bici", "peaton", "ignore"]
            },
            "counts_by_movement": {},
        }

    try:
        ensure_tracks_available(df)
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)

    total_tracks_raw = int(df["track_id"].nunique())

    df = df.copy()
    df["qc_class"] = df["object_class"].map(lambda value: classify_vehicle(str(value)))

    class_counts_series = df["qc_class"].value_counts()
    desired_order = ["auto", "bus", "camion", "moto", "bici", "peaton", "ignore"]
    counts_by_class = {cls: int(class_counts_series.get(cls, 0)) for cls in desired_order}
    for cls, value in class_counts_series.items():
        if cls not in counts_by_class:
            counts_by_class[cls] = int(value)

    counted_tracks = int(
        df.loc[df["qc_class"] != "ignore", "track_id"].nunique()
    )

    metadata_path = _dataset_dir(dataset_id) / "metadata.json"
    fps_value = 30.0
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if isinstance(metadata.get("fps"), (int, float)):
                fps_value = float(metadata["fps"])
        except Exception:  # pragma: no cover
            fps_value = 30.0

    try:
        counts_df = calculate_counts_by_interval(
            normalized,
            accesses,
            rilsa_map,
            interval_minutes=settings.interval_minutes,
            fps=fps_value,
            min_length_m=settings.min_length_m,
            max_direction_changes=settings.max_direction_changes,
            min_net_over_path_ratio=settings.min_net_over_path_ratio,
        )
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)

    counts_by_movement: Dict[str, int] = {}
    if not counts_df.empty:
        grouped = counts_df.groupby("rilsa_code")["count"].sum()
        counts_by_movement = {str(code): int(count) for code, count in grouped.items()}

    return {
        "dataset_id": dataset_id,
        "total_tracks_raw": total_tracks_raw,
        "counted_tracks": counted_tracks,
        "counts_by_class": counts_by_class,
        "counts_by_movement": counts_by_movement,
    }


@router.get("/{dataset_id}/volumes", response_model=VolumesResponse)
def get_volumes(dataset_id: str) -> VolumesResponse:
    settings = load_analysis_settings(dataset_id)
    normalized, accesses, rilsa_map = _load_analysis_inputs(dataset_id)
    try:
        counts_df = calculate_counts_by_interval(
            normalized,
            accesses,
            rilsa_map,
            interval_minutes=settings.interval_minutes,
            min_length_m=settings.min_length_m,
            max_direction_changes=settings.max_direction_changes,
            min_net_over_path_ratio=settings.min_net_over_path_ratio,
        )
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)
    tables = build_volume_tables(counts_df)

    totals_rows = [VolumeRow(**row) for row in tables["totals"]]
    movement_tables = [
        MovementVolumeTable(
            rilsa_code=str(code),
            description=f"Movimiento {code}",
            rows=[VolumeRow(**row) for row in rows],
        )
        for code, rows in tables["movements"].items()
    ]

    return VolumesResponse(
        dataset_id=dataset_id,
        interval_minutes=settings.interval_minutes,
        totals_by_interval=totals_rows,
        movements=movement_tables,
    )


@router.get("/{dataset_id}/speeds", response_model=SpeedsResponse)
def get_speeds(
    dataset_id: str,
    fps: float = Query(30.0, gt=0),
    pixel_to_meter: float = Query(1.0, gt=0),
) -> SpeedsResponse:
    settings = load_analysis_settings(dataset_id)
    normalized, accesses, rilsa_map = _load_analysis_inputs(dataset_id)

    df = pd.read_parquet(normalized)
    if df.empty:
        return SpeedsResponse(dataset_id=dataset_id, per_movement=[])

    try:
        filtered, meta_df = assign_tracks_to_movements(
            df,
            accesses,
            rilsa_map,
            fps=fps,
            min_length_m=settings.min_length_m,
            max_direction_changes=settings.max_direction_changes,
            min_net_over_path_ratio=settings.min_net_over_path_ratio,
        )
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)
    meta_df = meta_df[["track_id", "rilsa_code", "vehicle_class"]]
    speeds_df = compute_track_speeds(filtered, fps=fps, pixel_to_meter=pixel_to_meter)
    summary = summarize_speeds(speeds_df, meta_df)

    per_movement = [
        MovementSpeedStats(
            rilsa_code=str(rilsa_code),
            description=f"Movimiento {rilsa_code}",
            vehicle_class=str(vehicle_class),
            stats=SpeedStats(**stats),
        )
        for (rilsa_code, vehicle_class), stats in summary.items()
    ]

    return SpeedsResponse(dataset_id=dataset_id, per_movement=per_movement)


@router.get("/{dataset_id}/conflicts", response_model=ConflictsResponse)
def get_conflicts(
    dataset_id: str,
    fps: float = Query(30.0, gt=0),
    distance_threshold: float = Query(2.0, gt=0),
    ttc_threshold: float | None = Query(None, gt=0),
) -> ConflictsResponse:
    settings = load_analysis_settings(dataset_id)
    normalized = _normalized_path(dataset_id)
    if not normalized.exists():
        raise HTTPException(status_code=404, detail="Dataset sin datos normalizados.")

    df = pd.read_parquet(normalized)
    if df.empty:
        return ConflictsResponse(dataset_id=dataset_id, total_conflicts=0, events=[])
    try:
        ensure_tracks_available(df)
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)

    df = df.copy()
    df["vehicle_class"] = df["object_class"].map(lambda value: classify_vehicle(str(value)))
    df = df[df["vehicle_class"] != "ignore"]
    if df.empty:
        return ConflictsResponse(dataset_id=dataset_id, total_conflicts=0, events=[])
    conflicts_list = detect_conflicts(
        df,
        fps=fps,
        distance_threshold=distance_threshold,
        ttc_threshold_s=ttc_threshold if ttc_threshold is not None else settings.ttc_threshold_s,
    )
    events = [
        ConflictEvent(
            ttc_min=conflict.ttc_min,
            pet=conflict.pet,
            time_sec=conflict.time_sec,
            x=conflict.x,
            y=conflict.y,
            track_id_1=conflict.track_id_1,
            track_id_2=conflict.track_id_2,
            severity=conflict.severity,
            pair_type=conflict.pair_type,
        )
        for conflict in conflicts_list
    ]
    return ConflictsResponse(dataset_id=dataset_id, total_conflicts=len(events), events=events)


@router.get("/{dataset_id}/violations", response_model=ViolationsResponse)
def get_violations(dataset_id: str) -> ViolationsResponse:
    """
    Devuelve la cantidad de maniobras indebidas detectadas para los movimientos prohibidos.
    """
    normalized, accesses, rilsa_map = _load_analysis_inputs(dataset_id)
    config = ConfigPersistenceService.load_config(dataset_id)
    forbidden = config.forbidden_movements if config else []
    if not forbidden:
        return ViolationsResponse(
            dataset_id=dataset_id,
            total_violations=0,
            by_movement=[],
        )

    settings = load_analysis_settings(dataset_id)

    df = pd.read_parquet(normalized)
    if df.empty:
        return ViolationsResponse(
            dataset_id=dataset_id,
            total_violations=0,
            by_movement=[],
        )

    try:
        _, meta_df = assign_tracks_to_movements(
            df,
            accesses,
            rilsa_map,
            min_length_m=settings.min_length_m,
            max_direction_changes=settings.max_direction_changes,
            min_net_over_path_ratio=settings.min_net_over_path_ratio,
        )
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)
    summary = summarize_violations(meta_df, forbidden)
    by_movement = [ViolationSummary(**item) for item in summary["by_movement"]]

    return ViolationsResponse(
        dataset_id=dataset_id,
        total_violations=summary["total_violations"],
        by_movement=by_movement,
    )

