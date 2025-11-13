"""
Modelos de configuración y reglas por dataset
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime


class CardinalPointConfig(BaseModel):
    """Configuración de un punto cardinal"""
    entry_only: bool = False  # Si es true, solo permite entradas (no salidas)
    allow_pedestrians: bool = True
    allow_vehicles: bool = True
    coordinates: Optional[Dict[str, float]] = None  # x, y del punto en el video


class CorrectionRuleCondition(BaseModel):
    """Condición para aplicar una regla"""
    origin_cardinal: Optional[str] = None
    destination_cardinal: Optional[str] = None
    class_in: Optional[List[str]] = None
    class_not_in: Optional[List[str]] = None
    trajectory_length: Optional[int] = None
    trajectory_length_lt: Optional[int] = None  # less than
    trajectory_length_gt: Optional[int] = None  # greater than
    mov_rilsa: Optional[int] = None
    custom_expression: Optional[str] = None  # Para reglas avanzadas


class CorrectionRule(BaseModel):
    """Regla de corrección automática"""
    id: str
    name: str
    description: Optional[str] = None
    type: Literal["filter", "modify", "validate"]
    condition: CorrectionRuleCondition
    action: Literal["remove", "modify_field", "flag", "keep"]
    field_modifications: Optional[Dict[str, Any]] = None  # Para action="modify_field"
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class TrajectoryCorrection(BaseModel):
    """Corrección manual para una trayectoria específica."""
    track_id: str
    new_origin: Optional[str] = None
    new_dest: Optional[str] = None
    new_class: Optional[str] = None
    discard: bool = False
    hide_in_pdf: bool = False

class DatasetConfig(BaseModel):
    """Configuración completa de un dataset"""
    dataset_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    pkl_file: str

    # Configuración de puntos cardinales
    cardinal_points: Dict[str, CardinalPointConfig] = {
        "N": CardinalPointConfig(entry_only=True, allow_pedestrians=True, allow_vehicles=False),
        "S": CardinalPointConfig(),
        "E": CardinalPointConfig(),
        "O": CardinalPointConfig()
    }

    # Reglas de corrección
    correction_rules: List[CorrectionRule] = []

    # Correcciones manuales de trayectorias
    trajectory_corrections: Dict[str, TrajectoryCorrection] = Field(default_factory=dict)

    # Metadatos
    video_info: Optional[Dict[str, Any]] = None
    intersection_name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class HistoryEntry(BaseModel):
    """Entrada del historial de cambios"""
    timestamp: datetime = Field(default_factory=datetime.now)
    user: str = "system"
    action: str
    changes: Dict[str, Any]
    rules_applied: List[str] = []
    details: List[str] = []
    snapshot_file: Optional[str] = None


class EventUpdate(BaseModel):
    """Modelo para actualizar un evento"""
    track_id: Optional[int] = None
    class_name: Optional[str] = Field(None, alias="class")
    origin_cardinal: Optional[str] = None
    destination_cardinal: Optional[str] = None
    mov_rilsa: Optional[int] = None
    trajectory: Optional[List[List[float]]] = None
    color: Optional[str] = None

    class Config:
        populate_by_name = True
