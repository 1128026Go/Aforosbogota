from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List
import os
import shutil
from pathlib import Path

router = APIRouter()

# Simple storage directory for uploaded datasets
DATASETS_DIR = Path("data/datasets")
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

@router.get("")
def list_datasets():
    """Lista todos los datasets subidos"""
    try:
        datasets = []
        for pkl_file in DATASETS_DIR.glob("*.pkl"):
            datasets.append({
                "id": pkl_file.stem,
                "name": pkl_file.name,
                "size": pkl_file.stat().st_size,
                "created_at": pkl_file.stat().st_ctime
            })
        return {"datasets": datasets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing datasets: {str(e)}")

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Sube un dataset PKL"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
        
    if not file.filename.lower().endswith(".pkl"):
        raise HTTPException(status_code=400, detail="Only PKL files are allowed")
    
    try:
        # Save the uploaded file
        file_path = DATASETS_DIR / file.filename
        
        # Check if file already exists
        if file_path.exists():
            raise HTTPException(status_code=409, detail=f"Dataset {file.filename} already exists")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "id": file_path.stem,
            "name": file.filename,
            "message": f"Dataset {file.filename} uploaded successfully",
            "size": file_path.stat().st_size
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str):
    """Elimina un dataset"""
    try:
        file_path = DATASETS_DIR / f"{dataset_id}.pkl"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        
        file_path.unlink()
        return {"message": f"Dataset {dataset_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting dataset: {str(e)}")

@router.get("/{dataset_id}")
def get_dataset(dataset_id: str):
    """Obtiene información de un dataset específico"""
    try:
        file_path = DATASETS_DIR / f"{dataset_id}.pkl"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        
        return {
            "id": dataset_id,
            "name": f"{dataset_id}.pkl",
            "size": file_path.stat().st_size,
            "created_at": file_path.stat().st_ctime,
            "path": str(file_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dataset info: {str(e)}")
