"""
Router for dataset configuration endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.models.config import (
    DatasetConfig,
    AccessConfig,
    RilsaRule,
    AccessPolygonUpdate,
    TrajectoryPoint,
)
from api.services.cardinals import CardinalsService
from api.services.persistence import ConfigPersistenceService

router = APIRouter(
    prefix="/api/v1/config",
    tags=["config"],
)


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


@router.post("/generate_accesses/{dataset_id}", response_model=List[AccessConfig])
async def generate_accesses(
    dataset_id: str,
    trajectories: Optional[List[TrajectoryPoint]] = None,
    image_width: int = Query(1280, description="Video frame width"),
    image_height: int = Query(720, description="Video frame height"),
):
    """
    Generate default access configurations from trajectory data.
    
    This analyzes trajectory points to propose cardinal accesses (N, S, E, O).
    The generated accesses are NOT automatically saved - they are only returned
    for preview/editing.
    
    Args:
        dataset_id: Dataset identifier
        trajectories: List of trajectory points (optional, will use default if not provided)
        image_width: Width of the video frame
        image_height: Height of the video frame
        
    Returns:
        List of proposed AccessConfig
    """
    # Convert trajectory points to dicts
    traj_dicts = []
    if trajectories:
        traj_dicts = [t.dict() for t in trajectories]
    
    # Generate defaults
    accesses = CardinalsService.generate_default_accesses(
        trajectories=traj_dicts,
        image_width=image_width,
        image_height=image_height
    )
    
    return accesses


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
