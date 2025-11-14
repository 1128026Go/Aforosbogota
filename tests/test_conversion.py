from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd

from api.models.config import AccessConfig
from api.routers import datasets as datasets_router
from api.services.cardinals_persistence import persist_cardinals_and_rilsa
from api.services.convert import normalize_pkl_to_parquet


def test_normalize_pkl_to_parquet_dataframe_input(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "frame_id": [0, 1, 2, 0, 1, 2],
            "track_id": [1, 1, 1, 2, 2, 2],
            "x": [10.0, 12.0, 14.0, 50.0, 52.0, 54.0],
            "y": [5.0, 7.0, 9.0, 20.0, 22.0, 24.0],
            "object_class": ["car", "car", "car", "person", "person", "person"],
        }
    )
    pkl_path = tmp_path / "input.pkl"
    df.to_pickle(pkl_path)
    parquet_path = tmp_path / "normalized.parquet"

    meta = normalize_pkl_to_parquet(pkl_path, parquet_path)

    assert parquet_path.exists()
    normalized_df = pd.read_parquet(parquet_path)
    for column in ["frame_id", "track_id", "x", "y", "object_class"]:
        assert column in normalized_df.columns
    assert meta["tracks"] == 2
    assert meta["frames"] >= 3
    assert meta["width"] > 0
    assert meta["height"] > 0
    assert meta["fps"] > 0


def test_normalize_pkl_to_parquet_with_alias_columns(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "frame": [0, 1, 1],
            "id": [10, 10, 11],
            "xc": [100.0, 102.5, 200.1],
            "yc": [50.0, 51.5, 80.2],
            "cls": ["car", "car", "bus"],
        }
    )
    pkl_path = tmp_path / "alias_input.pkl"
    df.to_pickle(pkl_path)
    parquet_path = tmp_path / "alias_normalized.parquet"

    meta = normalize_pkl_to_parquet(pkl_path, parquet_path)

    normalized_df = pd.read_parquet(parquet_path)
    for column in ["frame_id", "track_id", "x", "y", "object_class"]:
        assert column in normalized_df.columns
    assert normalized_df["frame_id"].tolist() == [0, 1, 1]
    assert meta["tracks"] == 2


def test_normalize_pkl_to_parquet_with_bbox_centers(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "frame_idx": [0, 0],
            "track": [5, 6],
            "bbox_center_x": [10.0, 20.0],
            "bbox_center_y": [15.0, 25.0],
            "class": ["person", "bike"],
        }
    )
    pkl_path = tmp_path / "bbox_input.pkl"
    df.to_pickle(pkl_path)
    parquet_path = tmp_path / "bbox_normalized.parquet"

    normalize_pkl_to_parquet(pkl_path, parquet_path)

    normalized_df = pd.read_parquet(parquet_path)
    assert normalized_df["x"].tolist() == [10.0, 20.0]
    assert normalized_df["y"].tolist() == [15.0, 25.0]


def test_normalize_pkl_to_parquet_missing_columns(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "frame_no": [0, 1, 2],
            "identifier": [1, 2, 3],
            "score": [0.9, 0.8, 0.95],
        }
    )
    pkl_path = tmp_path / "invalid.pkl"
    df.to_pickle(pkl_path)
    parquet_path = tmp_path / "invalid.parquet"

    try:
        normalize_pkl_to_parquet(pkl_path, parquet_path)
    except ValueError as exc:
        message = str(exc)
        assert "Columnas encontradas:" in message
        assert "frame_no" in message
        assert "identifier" in message
    else:
        raise AssertionError("Se esperaba ValueError por columnas no mapeables")


def test_normalize_structured_detections(tmp_path: Path) -> None:
    raw = {
        "metadata": {"width": 1920, "height": 1080, "fps": 29.97},
        "detecciones": [
            {"fotograma": 0, "clase": "car", "confianza": 0.9, "bbox": [10, 20, 50, 80]},
            {"fotograma": 1, "clase": "truck", "confianza": 0.8, "bbox": [15, 25, 60, 90]},
        ],
        "trayectorias": {},
        "config": {"modelo": "yolo"},
    }
    pkl_path = tmp_path / "structured.pkl"
    with pkl_path.open("wb") as handle:
        pickle.dump(raw, handle)
    parquet_path = tmp_path / "normalized.parquet"

    meta = normalize_pkl_to_parquet(pkl_path, parquet_path)

    assert parquet_path.exists()
    df = pd.read_parquet(parquet_path)
    for column in ["frame_id", "track_id", "x", "y", "object_class", "confidence", "x_min", "y_min", "x_max", "y_max"]:
        assert column in df.columns
    assert df["track_id"].isna().all()
    assert meta["tracks"] == 0
    assert meta["width"] == 1920
    assert meta["height"] == 1080


def test_persist_cardinals_and_rilsa_creates_files(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    monkeypatch.setattr(datasets_router, "DATA_DIR", data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    dataset_id = "demo_dataset"
    accesses = [
        AccessConfig(id="A1", cardinal="N", polygon=[(10.0, 10.0)], centroid=(10.0, 10.0)),
        AccessConfig(id="A2", cardinal="S", polygon=[(20.0, 20.0)], centroid=(20.0, 20.0)),
    ]

    persist_cardinals_and_rilsa(dataset_id, accesses)

    dataset_dir = data_dir / dataset_id
    cardinals_path = dataset_dir / "cardinals.json"
    rilsa_path = dataset_dir / "rilsa_map.json"
    assert cardinals_path.exists()
    assert rilsa_path.exists()

    cardinals = json.loads(cardinals_path.read_text(encoding="utf-8"))
    assert len(cardinals) == 2
    assert {item["cardinal"] for item in cardinals} == {"N", "S"}

    rilsa_map = json.loads(rilsa_path.read_text(encoding="utf-8"))
    assert rilsa_map["metadata"]["num_accesses"] == 2

