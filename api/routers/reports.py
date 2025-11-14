"""
Generación de reportes CSV, Excel y PDF basados en los datos reales.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.routers.datasets import _dataset_dir
from api.services import (
    assign_tracks_to_movements,
    build_volume_tables,
    calculate_counts_by_interval,
    classify_vehicle,
    compute_track_speeds,
    detect_conflicts,
    export_pdf,
    export_volumes_to_excel,
    render_html_report,
    summarize_speeds,
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


@router.get("/{dataset_id}/summary")
def generate_csv_report(dataset_id: str, interval_minutes: int = 15) -> Dict[str, str]:
    normalized_path = _normalized_path(dataset_id)
    cardinals_path = _cardinals_path(dataset_id)
    rilsa_path = _rilsa_map_path(dataset_id)
    if not normalized_path.exists() or not cardinals_path.exists() or not rilsa_path.exists():
        raise HTTPException(status_code=404, detail="Faltan datos normalizados o configuración RILSA.")

    with cardinals_path.open("r", encoding="utf-8") as fh:
        accesses = json.load(fh)
    with rilsa_path.open("r", encoding="utf-8") as fh:
        rilsa_map = json.load(fh)

    counts_df = calculate_counts_by_interval(
        normalized_path,
        accesses,
        rilsa_map,
        interval_minutes=interval_minutes,
    )

    reports_dir = _reports_dir(dataset_id)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    csv_path = reports_dir / f"aforo_{timestamp}.csv"
    counts_df.to_csv(csv_path, index=False)
    return {"file_name": csv_path.name}


@router.get("/{dataset_id}/excel")
def generate_excel_report(dataset_id: str, interval_minutes: int = 15) -> Dict[str, str]:
    normalized_path = _normalized_path(dataset_id)
    cardinals_path = _cardinals_path(dataset_id)
    rilsa_path = _rilsa_map_path(dataset_id)
    if not normalized_path.exists() or not cardinals_path.exists() or not rilsa_path.exists():
        raise HTTPException(status_code=404, detail="Faltan datos normalizados o configuración RILSA.")

    with cardinals_path.open("r", encoding="utf-8") as fh:
        accesses = json.load(fh)
    with rilsa_path.open("r", encoding="utf-8") as fh:
        rilsa_map = json.load(fh)

    counts_df = calculate_counts_by_interval(
        normalized_path,
        accesses,
        rilsa_map,
        interval_minutes=interval_minutes,
    )
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
    interval_minutes: int = 15,
    fps: float = 30.0,
    pixel_to_meter: float = 1.0,
    ttc_threshold: float = 1.5,
) -> Dict[str, str]:
    normalized_path = _normalized_path(dataset_id)
    cardinals_path = _cardinals_path(dataset_id)
    rilsa_path = _rilsa_map_path(dataset_id)
    if not normalized_path.exists() or not cardinals_path.exists() or not rilsa_path.exists():
        raise HTTPException(status_code=404, detail="Faltan datos normalizados o configuración RILSA.")

    with cardinals_path.open("r", encoding="utf-8") as fh:
        accesses = json.load(fh)
    with rilsa_path.open("r", encoding="utf-8") as fh:
        rilsa_map = json.load(fh)

    counts_df = calculate_counts_by_interval(
        normalized_path,
        accesses,
        rilsa_map,
        interval_minutes=interval_minutes,
    )
    tables = build_volume_tables(counts_df)

    df = pd.read_parquet(normalized_path)
    filtered, meta_df = assign_tracks_to_movements(
        df,
        accesses,
        rilsa_map,
        fps=fps,
    )
    meta_df = meta_df[["track_id", "rilsa_code", "vehicle_class"]]
    speeds_df = compute_track_speeds(filtered, fps=fps, pixel_to_meter=pixel_to_meter)
    speed_summary = summarize_speeds(speeds_df, meta_df)

    df_conflicts = df.copy()
    meta_lookup = meta_df.set_index("track_id")["vehicle_class"]
    df_conflicts["vehicle_class"] = df_conflicts["track_id"].map(meta_lookup).fillna(
        df_conflicts["object_class"].map(lambda value: classify_vehicle(str(value)))
    )
    conflicts_list = detect_conflicts(
        df_conflicts,
        fps=fps,
        ttc_threshold=ttc_threshold,
        distance_threshold=2.0,
    )
    conflicts_summary = {"total_conflicts": len(conflicts_list)}

    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    html = render_html_report(
        templates_dir,
        dataset_id,
        interval_minutes,
        tables["totals"],
        tables["movements"],
        speed_summary,
        conflicts_summary,
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
