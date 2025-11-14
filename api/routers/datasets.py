"""
Router for dataset management endpoints (upload, create, list)
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import json
from pathlib import Path
from datetime import datetime
import uuid

from api.services import normalize_pkl_to_parquet

router = APIRouter(
    prefix="/api/v1/datasets",
    tags=["datasets"],
)

# Data storage directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _dataset_dir(dataset_id: str) -> Path:
    path = DATA_DIR / dataset_id
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload a PKL file and create a new dataset.

    Returns a dataset summary with ID, metadata and status.
    """
    if not file.filename or not file.filename.endswith(".pkl"):
        raise HTTPException(status_code=400, detail="Only .pkl files are supported")

    try:
        dataset_id = uuid.uuid4().hex[:8]
        dataset_dir = _dataset_dir(dataset_id)

        file_path = dataset_dir / "raw.pkl"
        contents = await file.read()
        with file_path.open("wb") as f:
            f.write(contents)

        parquet_path = dataset_dir / "normalized.parquet"
        meta = normalize_pkl_to_parquet(file_path, parquet_path)

        summary = {
            "id": dataset_id,
            "name": file.filename,
            "frames": meta.get("frames"),
            "tracks": meta.get("tracks"),
            "width": meta.get("width"),
            "height": meta.get("height"),
            "fps": meta.get("fps"),
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
            "status": "ready",
        }

        metadata_path = dataset_dir / "metadata.json"
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/list")
async def list_datasets() -> Dict[str, Any]:
    """
    List all available datasets.
    """
    try:
        datasets = []
        if DATA_DIR.exists():
            for dataset_path in DATA_DIR.iterdir():
                if not dataset_path.is_dir():
                    continue
                metadata_path = dataset_path / "metadata.json"
                if metadata_path.is_file():
                    with metadata_path.open("r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        datasets.append(metadata)

        return {
            "datasets": datasets,
            "total": len(datasets),
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str) -> Dict[str, Any]:
    """
    Get metadata for a specific dataset.
    """
    try:
        metadata_path = _dataset_dir(dataset_id) / "metadata.json"
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")

        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)

        return metadata
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get failed: {str(e)}")
