"""
Router temporal para el editor de datasets sin dependencias de BD
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import json
from pathlib import Path

router = APIRouter(prefix="/api/editor/datasets", tags=["Dataset Editor"])

# Directorio temporal para datos
TEMP_DATA_DIR = Path("/app/temp_data")
TEMP_DATA_DIR.mkdir(exist_ok=True)

@router.get("/")
async def list_datasets():
    """Lista todos los datasets disponibles (versión temporal)"""
    # Buscar PKL files en el directorio de datasets subidos
    datasets_dir = Path("/app/data/datasets")
    datasets = []
    
    if datasets_dir.exists():
        for pkl_file in datasets_dir.glob("*.pkl"):
            datasets.append({
                "dataset_id": pkl_file.stem,
                "created_at": pkl_file.stat().st_ctime,
                "last_modified": pkl_file.stat().st_mtime,
                "pkl_file": pkl_file.name,
                "events_count": 0,  # Placeholder
                "has_config": False,  # Placeholder
                "rules_count": 0,  # Placeholder
            })
    
    return {"datasets": datasets}

@router.get("/{dataset_id}/info")
async def get_dataset_info(dataset_id: str):
    """Obtiene información de un dataset (versión temporal)"""
    # Verificar que el dataset existe
    datasets_dir = Path("/app/data/datasets")
    pkl_file = datasets_dir / f"{dataset_id}.pkl"
    
    if not pkl_file.exists():
        raise HTTPException(404, f"Dataset {dataset_id} no encontrado")
    
    return {
        "dataset_id": dataset_id,
        "config": {
            "dataset_id": dataset_id,
            "pkl_file": f"{dataset_id}.pkl",
            "created_at": pkl_file.stat().st_ctime,
            "last_modified": pkl_file.stat().st_mtime
        },
        "events_count": 0,  # Placeholder
        "message": "Editor temporal activo. Funcionalidades limitadas sin configuración de BD."
    }

@router.get("/{dataset_id}/config")
async def get_dataset_config(dataset_id: str):
    """Obtiene la configuración de un dataset (versión temporal)"""
    datasets_dir = Path("/app/data/datasets")
    pkl_file = datasets_dir / f"{dataset_id}.pkl"
    
    if not pkl_file.exists():
        raise HTTPException(404, f"Dataset {dataset_id} no encontrado")
    
    return {
        "dataset_id": dataset_id,
        "pkl_file": f"{dataset_id}.pkl",
        "created_at": pkl_file.stat().st_ctime,
        "last_modified": pkl_file.stat().st_mtime,
        "cardinal_points": {
            "N": {"entry_only": True, "allow_pedestrians": True, "allow_vehicles": False},
            "S": {"entry_only": False, "allow_pedestrians": True, "allow_vehicles": True},
            "E": {"entry_only": False, "allow_pedestrians": True, "allow_vehicles": True},
            "O": {"entry_only": False, "allow_pedestrians": True, "allow_vehicles": True}
        },
        "correction_rules": [],
        "trajectory_corrections": {},
        "notes": "Configuración temporal - funcionalidades completas requieren BD"
    }

@router.get("/{dataset_id}/events")
async def get_events(dataset_id: str, skip: int = 0, limit: int = 100):
    """Obtiene eventos de un dataset (versión temporal)"""
    datasets_dir = Path("/app/data/datasets")
    pkl_file = datasets_dir / f"{dataset_id}.pkl"
    
    if not pkl_file.exists():
        raise HTTPException(404, f"Dataset {dataset_id} no encontrado")
    
    # Datos de ejemplo para el frontend
    example_events = [
        {
            "track_id": "001",
            "class": "car",
            "origin_cardinal": "N",
            "destination_cardinal": "S",
            "mov_rilsa": 1,
            "movimiento_rilsa": "R1",
            "trajectory": [[100, 100], [150, 150], [200, 200]],
            "timestamp_start": 1000,
            "timestamp_end": 2000
        }
    ]
    
    return {
        "events": example_events if skip == 0 else [],
        "total": len(example_events),
        "skip": skip,
        "limit": limit,
        "has_more": False,
        "message": "Datos de ejemplo - conecta BD para eventos reales"
    }

@router.get("/{dataset_id}/stats")
async def get_dataset_stats(dataset_id: str):
    """Obtiene estadísticas de un dataset (versión temporal)"""
    return {
        "total_events": 1,
        "by_class": {"car": 1},
        "by_origin": {"N": 1},
        "by_rilsa_movement": {"1": 1},
        "message": "Estadísticas de ejemplo - conecta BD para datos reales"
    }