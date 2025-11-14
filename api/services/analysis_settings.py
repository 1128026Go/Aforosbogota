"""
Persistence helpers for dataset-level analysis settings.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from api.models.config import AnalysisSettings


DATA_DIR = Path("data")
ANALYSIS_SETTINGS_FILENAME = "analysis_settings.json"


def _dataset_dir(dataset_id: str) -> Path:
    """Ensure the dataset directory exists and return it."""
    path = DATA_DIR / dataset_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _settings_path(dataset_id: str) -> Path:
    """Return the path where analysis settings are stored."""
    return _dataset_dir(dataset_id) / ANALYSIS_SETTINGS_FILENAME


def load_analysis_settings(dataset_id: str) -> AnalysisSettings:
    """
    Load the persisted analysis settings for a dataset.

    Returns default settings if the file does not exist or is invalid.
    """
    path = _settings_path(dataset_id)
    if not path.exists():
        return AnalysisSettings()
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return AnalysisSettings(**data)
    except Exception:
        # Si el archivo está corrupto o incompleto, devolvemos defaults
        return AnalysisSettings()


def save_analysis_settings(dataset_id: str, settings: AnalysisSettings) -> None:
    """Persist the provided settings to disk."""
    path = _settings_path(dataset_id)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(json.loads(settings.model_dump_json()), handle, indent=2, ensure_ascii=False)


