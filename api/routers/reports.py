"""
Generación de reportes CSV, Excel y PDF basados en los datos reales.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, List

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.models.config import ForbiddenMovement
from api.routers.datasets import _dataset_dir
from api.services import (
    ConfigPersistenceService,
    MissingTrajectoryDataError,
    assign_tracks_to_movements,
    build_volume_tables,
    calculate_counts_by_interval,
    classify_vehicle,
    compute_track_speeds,
    detect_conflicts,
    ensure_tracks_available,
    export_pdf,
    export_volumes_to_excel,
    load_analysis_settings,
    render_html_report,
    summarize_speeds,
    summarize_violations,
)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def _normalized_path(dataset_id: str) -> Path:
    return _dataset_dir(dataset_id) / "normalized.parquet"


def _cardinals_path(dataset_id: str) -> Path:
    return _dataset_dir(dataset_id) / "cardinals.json"


def _rilsa_map_path(dataset_id: str) -> Path:
    return _dataset_dir(dataset_id) / "rilsa_map.json"


def _reports_dir(dataset_id: str) -> Path:
    directory = _dataset_dir(dataset_id) / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _load_analysis_inputs(dataset_id: str) -> Tuple[Path, List[Dict], Dict]:
    normalized = _normalized_path(dataset_id)
    cardinals_path = _cardinals_path(dataset_id)
    rilsa_path = _rilsa_map_path(dataset_id)
    if not normalized.exists() or not cardinals_path.exists() or not rilsa_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Faltan datos normalizados o configuración RILSA.",
        )
    with cardinals_path.open("r", encoding="utf-8") as fh:
        accesses = json.load(fh)
    with rilsa_path.open("r", encoding="utf-8") as fh:
        rilsa_map = json.load(fh)
    return normalized, accesses, rilsa_map


def _raise_tracking_http_error(exc: MissingTrajectoryDataError) -> None:
    raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{dataset_id}/summary")
def generate_csv_report(dataset_id: str, interval_minutes: int | None = None) -> Dict[str, str]:
    settings = load_analysis_settings(dataset_id)
    interval = interval_minutes or settings.interval_minutes
    normalized_path, accesses, rilsa_map = _load_analysis_inputs(dataset_id)
    try:
        counts_df = calculate_counts_by_interval(
            normalized_path,
            accesses,
            rilsa_map,
            interval_minutes=interval,
            min_length_m=settings.min_length_m,
            max_direction_changes=settings.max_direction_changes,
            min_net_over_path_ratio=settings.min_net_over_path_ratio,
        )
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)

    reports_dir = _reports_dir(dataset_id)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    csv_path = reports_dir / f"aforo_{timestamp}.csv"
    counts_df.to_csv(csv_path, index=False)
    return {"file_name": csv_path.name}


@router.get("/{dataset_id}/excel")
def generate_excel_report(dataset_id: str, interval_minutes: int | None = None) -> Dict[str, str]:
    settings = load_analysis_settings(dataset_id)
    interval = interval_minutes or settings.interval_minutes
    normalized_path, accesses, rilsa_map = _load_analysis_inputs(dataset_id)
    try:
        counts_df = calculate_counts_by_interval(
            normalized_path,
            accesses,
            rilsa_map,
            interval_minutes=interval,
            min_length_m=settings.min_length_m,
            max_direction_changes=settings.max_direction_changes,
            min_net_over_path_ratio=settings.min_net_over_path_ratio,
        )
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)
    tables = build_volume_tables(counts_df)

    reports_dir = _reports_dir(dataset_id)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    xlsx_path = reports_dir / f"aforo_{timestamp}.xlsx"
    export_volumes_to_excel(
        xlsx_path,
        totals=tables["totals"],
        movements=tables["movements"],
    )
    return {"file_name": xlsx_path.name}


@router.get("/{dataset_id}/pdf")
def generate_pdf_report(
    dataset_id: str,
    interval_minutes: int | None = None,
    fps: float = 30.0,
    pixel_to_meter: float = 1.0,
    ttc_threshold: float | None = None,
) -> Dict[str, str]:
    settings = load_analysis_settings(dataset_id)
    interval = interval_minutes or settings.interval_minutes
    normalized_path, accesses, rilsa_map = _load_analysis_inputs(dataset_id)
    try:
        counts_df = calculate_counts_by_interval(
            normalized_path,
            accesses,
            rilsa_map,
            interval_minutes=interval,
            min_length_m=settings.min_length_m,
            max_direction_changes=settings.max_direction_changes,
            min_net_over_path_ratio=settings.min_net_over_path_ratio,
        )
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)
    tables = build_volume_tables(counts_df)

    df = pd.read_parquet(normalized_path)
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
    speed_summary = summarize_speeds(speeds_df, meta_df)

    df_conflicts = df.copy()
    try:
        ensure_tracks_available(df_conflicts)
    except MissingTrajectoryDataError as exc:
        _raise_tracking_http_error(exc)

    meta_lookup = meta_df.set_index("track_id")["vehicle_class"]
    df_conflicts["vehicle_class"] = df_conflicts["track_id"].map(meta_lookup).fillna(
        df_conflicts["object_class"].map(lambda value: classify_vehicle(str(value)))
    )
    conflicts_list = detect_conflicts(
        df_conflicts,
        fps=fps,
        ttc_threshold_s=ttc_threshold if ttc_threshold is not None else settings.ttc_threshold_s,
        distance_threshold=2.0,
    )
    conflicts_summary = {
        "total_conflicts": len(conflicts_list),
        "minimum_ttc": min((c.ttc_min for c in conflicts_list), default=None),
    }

    config = ConfigPersistenceService.load_config(dataset_id)
    forbidden: List[ForbiddenMovement] = config.forbidden_movements if config else []
    violation_summary = summarize_violations(meta_df, forbidden)

    total_vehicles = sum(row["total"] for row in tables["totals"])
    peak_row = max(tables["totals"], key=lambda row: row["total"], default=None)
    peak_label = (
        f"{peak_row['interval_start']} - {peak_row['interval_end']}"
        if peak_row
        else "N/A"
    )

    speed_by_class = []
    class_groups: Dict[str, Dict[str, float]] = {}
    for (rilsa_code, vehicle_class), stats in speed_summary.items():
        agg = class_groups.setdefault(
            vehicle_class,
            {"vehicle_class": vehicle_class, "count": 0, "mean_sum": 0.0, "p85_sum": 0.0},
        )
        agg["count"] += stats["count"]
        agg["mean_sum"] += stats["mean_kmh"] * stats["count"]
        agg["p85_sum"] += stats["p85_kmh"] * stats["count"]
    for item in class_groups.values():
        count = max(item["count"], 1)
        speed_by_class.append(
            {
                "vehicle_class": item["vehicle_class"],
                "count": item["count"],
                "mean_kmh": item["mean_sum"] / count,
                "p85_kmh": item["p85_sum"] / count,
            }
        )
    speed_by_class.sort(key=lambda row: row["mean_kmh"], reverse=True)

    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    html = render_html_report(
        templates_dir,
        {
            "dataset_id": dataset_id,
            "generated_at": generated_at,
            "analysis_settings": settings,
            "overview": {
                "total_vehicles": total_vehicles,
                "interval_minutes": interval,
                "peak_interval_label": peak_label,
                "peak_interval_total": peak_row["total"] if peak_row else 0,
                "total_conflicts": conflicts_summary["total_conflicts"],
                "minimum_ttc": conflicts_summary["minimum_ttc"],
                "total_violations": violation_summary["total_violations"],
            },
            "totals": tables["totals"],
            "movements": tables["movements"],
            "speed_summary": speed_summary,
            "speed_by_class": speed_by_class,
            "conflicts_events": conflicts_list[:200],
            "violations": violation_summary["by_movement"],
        },
    )

    reports_dir = _reports_dir(dataset_id)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    pdf_path = reports_dir / f"aforo_{timestamp}.pdf"
    export_pdf(html, pdf_path)
    return {"file_name": pdf_path.name}


@router.get("/{dataset_id}/download/{file_name}")
def download_report(dataset_id: str, file_name: str) -> FileResponse:
    file_path = _reports_dir(dataset_id) / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    media_type = "application/octet-stream"
    if file_name.endswith(".csv"):
        media_type = "text/csv"
    elif file_name.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif file_name.endswith(".pdf"):
        media_type = "application/pdf"
    return FileResponse(file_path, media_type=media_type, filename=file_name)
