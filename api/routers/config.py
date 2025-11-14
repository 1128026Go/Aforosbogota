"""
Router for dataset configuration endpoints
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
import json

import pandas as pd
from pydantic import BaseModel

from api.models.config import (
    AccessConfig,
    AccessPolygonUpdate,
    AnalysisSettings,
    DatasetConfig,
    ForbiddenMovement,
    RilsaRule,
    TrajectoryPoint,
)
from api.models.schemas import AccessGenerationResponse
from api.services.cardinals import CardinalsService
from api.services.analysis_settings import (
    load_analysis_settings,
    save_analysis_settings,
)
from api.services.persistence import ConfigPersistenceService
from api.routers.datasets import _dataset_dir

router = APIRouter(
    prefix="/api/v1/config",
    tags=["config"],
)


class GenerateAccessesPayload(BaseModel):
    """Payload opcional para generar accesos de forma automática."""

    trajectories: Optional[List[TrajectoryPoint]] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    max_samples: Optional[int] = None


@router.get("/view/{dataset_id}", response_model=DatasetConfig)
async def view_config(dataset_id: str):
    """
    Get the current configuration for a dataset.
    
    Returns accesses with polygons and RILSA rules.
    If no config exists, returns a new empty configuration.
    """
    config = ConfigPersistenceService.load_config(dataset_id)
    
    if config is None:
        config = ConfigPersistenceService.create_default_config(dataset_id)
    
    return config


@router.get("/{dataset_id}/analysis_settings", response_model=AnalysisSettings)
async def get_analysis_settings(dataset_id: str) -> AnalysisSettings:
    """
    Obtiene la configuración avanzada de análisis para el dataset.
    """
    return load_analysis_settings(dataset_id)


@router.put("/{dataset_id}/analysis_settings", response_model=AnalysisSettings)
async def update_analysis_settings(
    dataset_id: str, settings: AnalysisSettings
) -> AnalysisSettings:
    """
    Actualiza y persiste la configuración avanzada de análisis.
    """
    save_analysis_settings(dataset_id, settings)
    return settings


@router.get(
    "/{dataset_id}/forbidden_movements", response_model=List[ForbiddenMovement]
)
async def get_forbidden_movements(dataset_id: str) -> List[ForbiddenMovement]:
    """
    Devuelve la lista de movimientos RILSA prohibidos para el dataset.
    """
    config = ConfigPersistenceService.load_config(dataset_id)
    if config is None:
        return []
    return config.forbidden_movements


@router.put(
    "/{dataset_id}/forbidden_movements", response_model=List[ForbiddenMovement]
)
async def update_forbidden_movements(
    dataset_id: str, movements: List[ForbiddenMovement]
) -> List[ForbiddenMovement]:
    """
    Define la lista de movimientos RILSA prohibidos para el dataset.
    """
    config = ConfigPersistenceService.load_config(dataset_id)
    if config is None:
        config = ConfigPersistenceService.create_default_config(dataset_id)
    config.forbidden_movements = movements
    if not ConfigPersistenceService.save_config(config):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save forbidden movements for dataset {dataset_id}",
        )
    return config.forbidden_movements


@router.post("/{dataset_id}/generate_accesses", response_model=AccessGenerationResponse)
async def generate_accesses(
    dataset_id: str,
    payload: Optional[GenerateAccessesPayload] = Body(default=None),
):
    """
    Genera una propuesta de accesos cardinales para el dataset indicado.

    Si no se proporcionan trayectorias explícitas, el servicio intentará cargar
    el archivo `normalized.parquet` del dataset para analizar los puntos.
    """
    dataset_dir = _dataset_dir(dataset_id)
    normalized_path = dataset_dir / "normalized.parquet"
    metadata_path = dataset_dir / "metadata.json"

    payload = payload or GenerateAccessesPayload()

    image_width = payload.image_width
    image_height = payload.image_height

    # Completar dimensiones con metadata si existe
    metadata: Optional[dict] = None
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:  # pragma: no cover - logueado externamente
            metadata = None

    if image_width is None and metadata and isinstance(metadata.get("width"), (int, float)):
        image_width = int(metadata["width"])
    if image_height is None and metadata and isinstance(metadata.get("height"), (int, float)):
        image_height = int(metadata["height"])

    image_width = image_width or 1280
    image_height = image_height or 720

    # Preparar trayectorias
    traj_dicts: List[dict] = []
    if payload.trajectories:
        traj_dicts = [trajectory.dict() for trajectory in payload.trajectories]
    else:
        if not normalized_path.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    "No se encontró el archivo normalized.parquet para el dataset. "
                    "Normaliza el PKL antes de generar accesos."
                ),
            )

        try:
            df = pd.read_parquet(normalized_path)
        except Exception as exc:  # pragma: no cover - detalle se loguea en servidor
            raise HTTPException(
                status_code=500,
                detail=f"No se pudo leer normalized.parquet: {exc}",
            ) from exc

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="El dataset normalizado no contiene trayectorias para analizar.",
            )

        if "x" not in df.columns or "y" not in df.columns:
            raise HTTPException(
                status_code=422,
                detail="normalized.parquet debe incluir columnas 'x' y 'y'.",
            )

        sample_df = df.dropna(subset=["x", "y"])
        if sample_df.empty:
            raise HTTPException(
                status_code=400,
                detail="No hay puntos válidos (x/y) en las trayectorias normalizadas.",
            )

        max_samples = payload.max_samples if payload.max_samples else 10000
        if len(sample_df) > max_samples:
            sample_df = sample_df.sample(max_samples, random_state=42)

        traj_dicts = [
            {"x": float(row.x), "y": float(row.y)}
            for row in sample_df.itertuples()
        ]

    accesses = CardinalsService.generate_default_accesses(
        trajectories=traj_dicts,
        image_width=image_width,
        image_height=image_height,
    )

    config = ConfigPersistenceService.load_config(dataset_id)
    if config is None:
        config = ConfigPersistenceService.create_default_config(dataset_id)

    config.accesses = accesses
    if not ConfigPersistenceService.save_config(config):
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo guardar la configuración de accesos para {dataset_id}",
        )

    return AccessGenerationResponse(dataset_id=dataset_id, accesses=accesses)


@router.put("/save_accesses/{dataset_id}", response_model=DatasetConfig)
async def save_accesses(dataset_id: str, update: AccessPolygonUpdate):
    """
    Save/update access configurations for a dataset.
    
    This persists the access polygons and cardinals. The updated_at timestamp
    is automatically set to current time.
    
    Args:
        dataset_id: Dataset identifier
        update: Updated access configurations
        
    Returns:
        Updated DatasetConfig
    """
    # Load existing config or create new one
    config = ConfigPersistenceService.load_config(dataset_id)
    if config is None:
        config = ConfigPersistenceService.create_default_config(dataset_id)
    
    # Update accesses
    config.accesses = update.accesses
    
    # Save to disk
    if not ConfigPersistenceService.save_config(config):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save configuration for dataset {dataset_id}"
        )
    
    return config


@router.post("/generate_rilsa/{dataset_id}", response_model=DatasetConfig)
async def generate_rilsa_rules(dataset_id: str):
    """
    Generate RILSA movement rules based on current accesses.
    
    This creates all possible movement combinations following the Nomenclatura Sagrada.
    The rules are automatically saved with the configuration.
    
    Args:
        dataset_id: Dataset identifier
        
    Returns:
        Updated DatasetConfig with generated RILSA rules
    """
    # Load existing config
    config = ConfigPersistenceService.load_config(dataset_id)
    if config is None:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration not found for dataset {dataset_id}"
        )
    
    # Check if we have accesses defined
    if not config.accesses:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate RILSA rules without defined accesses"
        )
    
    # Generate RILSA rules
    rilsa_rules = CardinalsService.generate_rilsa_rules(config.accesses)
    config.rilsa_rules = rilsa_rules
    
    # Save to disk
    if not ConfigPersistenceService.save_config(config):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save RILSA rules for dataset {dataset_id}"
        )
    
    return config


@router.get("/rilsa_codes/{dataset_id}", response_model=List[RilsaRule])
async def get_rilsa_codes(dataset_id: str):
    """
    Get all RILSA rules for a dataset.
    
    Returns the complete list of movement codes and descriptions.
    """
    config = ConfigPersistenceService.load_config(dataset_id)
    if config is None:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration not found for dataset {dataset_id}"
        )
    
    return config.rilsa_rules


@router.delete("/reset/{dataset_id}")
async def reset_config(dataset_id: str):
    """
    Reset configuration to default (empty accesses and rules).
    """
    config = ConfigPersistenceService.create_default_config(dataset_id)
    
    if not ConfigPersistenceService.save_config(config):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset configuration for dataset {dataset_id}"
        )
    
    return {"message": f"Configuration reset for dataset {dataset_id}"}
