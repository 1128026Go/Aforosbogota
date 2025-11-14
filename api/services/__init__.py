"""Services package for API."""
from .analysis_settings import load_analysis_settings, save_analysis_settings
from .cardinals import CardinalsService
from .conflicts import detect_conflicts
from .export_excel import export_volumes_to_excel
from .export_pdf import export_pdf, render_html_report
from .filters import filter_tracks
from .persistence import ConfigPersistenceService
from .report_builder import build_volume_tables
from .rilsa_mapping import (
    build_lookup_tables,
    build_rilsa_rule_map,
    movement_code_for_pedestrian,
    movement_code_for_vehicle,
    order_accesses_for_rilsa,
)
from .speeds import compute_track_speeds, summarize_speeds
from .trajectory_processor import (
    MissingTrajectoryDataError,
    assign_tracks_to_movements,
    calculate_counts_by_interval,
    classify_vehicle,
    ensure_tracks_available,
)
from .violations import summarize_violations
from .convert import normalize_pkl_to_parquet
from .cardinals_persistence import persist_cardinals_and_rilsa

__all__ = [
    "load_analysis_settings",
    "save_analysis_settings",
    "CardinalsService",
    "ConfigPersistenceService",
    "calculate_counts_by_interval",
    "filter_tracks",
    "build_volume_tables",
    "export_volumes_to_excel",
    "render_html_report",
    "export_pdf",
    "compute_track_speeds",
    "summarize_speeds",
    "detect_conflicts",
    "build_rilsa_rule_map",
    "build_lookup_tables",
    "movement_code_for_vehicle",
    "movement_code_for_pedestrian",
    "order_accesses_for_rilsa",
    "assign_tracks_to_movements",
    "MissingTrajectoryDataError",
    "ensure_tracks_available",
    "classify_vehicle",
    "summarize_violations",
    "normalize_pkl_to_parquet",
    "persist_cardinals_and_rilsa",
]
