"""
Pydantic models for dataset configuration
"""
from typing import List, Tuple, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AccessConfig(BaseModel):
    """Configuration for a single access (cardinal point)"""
    
    id: str = Field(..., description="Access ID (e.g., 'N', 'S', 'E', 'O')")
    cardinal: Literal["N", "S", "E", "O"] = Field(..., description="Cardinal direction")
    polygon: List[Tuple[float, float]] = Field(
        default_factory=list,
        description="List of (x, y) coordinates in image space forming a polygon"
    )
    centroid: Optional[Tuple[float, float]] = Field(
        default=None,
        description="Center point of the access (optional, computed if not provided)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "N",
                "cardinal": "N",
                "polygon": [[10.0, 20.0], [50.0, 20.0], [50.0, 40.0], [10.0, 40.0]],
                "centroid": [30.0, 30.0]
            }
        }


class RilsaRule(BaseModel):
    """Configuration for a RILSA movement rule"""
    
    code: str = Field(..., description="Movement code (e.g., '1', '91', '101')")
    origin_access: Literal["N", "S", "E", "O"] = Field(..., description="Origin cardinal")
    dest_access: Literal["N", "S", "E", "O"] = Field(..., description="Destination cardinal")
    movement_type: Literal["directo", "izquierda", "derecha", "retorno"] = Field(
        ...,
        description="Type of movement"
    )
    description: str = Field(..., description="Human-readable description")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "1",
                "origin_access": "N",
                "dest_access": "S",
                "movement_type": "directo",
                "description": "1 – N → S (movimiento directo)"
            }
        }


class DatasetConfig(BaseModel):
    """Complete configuration for a dataset"""
    
    dataset_id: str = Field(..., description="Unique dataset identifier")
    accesses: List[AccessConfig] = Field(
        default_factory=list,
        description="List of access configurations (N, S, E, O)"
    )
    rilsa_rules: List[RilsaRule] = Field(
        default_factory=list,
        description="List of RILSA movement rules"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "dataset_id": "gx010323",
                "accesses": [
                    {
                        "id": "N",
                        "cardinal": "N",
                        "polygon": [[10.0, 20.0], [50.0, 20.0], [50.0, 40.0], [10.0, 40.0]],
                        "centroid": [30.0, 30.0]
                    }
                ],
                "rilsa_rules": [
                    {
                        "code": "1",
                        "origin_access": "N",
                        "dest_access": "S",
                        "movement_type": "directo",
                        "description": "1 – N → S (movimiento directo)"
                    }
                ],
                "created_at": "2025-01-13T12:00:00",
                "updated_at": "2025-01-13T12:00:00"
            }
        }


class AccessPolygonUpdate(BaseModel):
    """Request body for updating multiple accesses"""
    
    accesses: List[AccessConfig] = Field(..., description="List of updated access configurations")
    
    class Config:
        schema_extra = {
            "example": {
                "accesses": [
                    {
                        "id": "N",
                        "cardinal": "N",
                        "polygon": [[10.0, 20.0], [50.0, 20.0], [50.0, 40.0], [10.0, 40.0]],
                        "centroid": [30.0, 30.0]
                    },
                    {
                        "id": "S",
                        "cardinal": "S",
                        "polygon": [[10.0, 60.0], [50.0, 60.0], [50.0, 80.0], [10.0, 80.0]],
                        "centroid": [30.0, 70.0]
                    }
                ]
            }
        }


class TrajectoryPoint(BaseModel):
    """Single trajectory point from normalized Parquet"""
    
    frame_id: int
    track_id: int
    x: float
    y: float
    class_id: int
    object_type: str
    confidence: float = 1.0
