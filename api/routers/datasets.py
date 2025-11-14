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
    
    Returns:
    - dataset_id: Unique identifier for the new dataset
    - metadata: Dataset information (frames, tracks, dimensions, etc.)
    - status: "success" or error message
    """
    # Validate file
    if not file.filename or not file.filename.endswith('.pkl'):
        raise HTTPException(status_code=400, detail="Only .pkl files are supported")

    try:
        # Generate dataset ID
        dataset_id = f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Create dataset directory
        dataset_dir = _dataset_dir(dataset_id)

        # Save uploaded file
        file_path = dataset_dir / "raw.pkl"
        contents = await file.read()
        with file_path.open("wb") as f:
            f.write(contents)

        parquet_path = dataset_dir / "normalized.parquet"
        meta = normalize_pkl_to_parquet(file_path, parquet_path)

        # Create metadata file
        metadata = {
            "dataset_id": dataset_id,
            "name": file.filename,
            "frames": meta.get("frames"),
            "tracks": meta.get("tracks"),
            "width": meta.get("width"),
            "height": meta.get("height"),
            "fps": meta.get("fps"),
            "created_at": datetime.now().isoformat(),
            "status": "ready",
        }

        metadata_path = dataset_dir / "metadata.json"
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return {
            "dataset_id": dataset_id,
            "metadata": metadata,
            "status": "success",
        }

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

        return {
            "metadata": metadata,
            "status": "success",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get failed: {str(e)}")
