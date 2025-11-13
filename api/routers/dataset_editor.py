"""
Router para endpoints de edición de datasets
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Mapping

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ValidationError

from api.models.dataset_config import (
    DatasetConfig,
    CorrectionRule,
    EventUpdate,
    CardinalPointConfig,
    TrajectoryCorrection,
)
from api.services.aforo_repository import AforoRepository
from api.services.aggregate import AggregatorService


router = APIRouter(prefix="/api/editor/datasets", tags=["Dataset Editor"])
repository = AforoRepository()
aggregator = AggregatorService(Path("data"), repository=repository)


def _format_rilsa_label(code: Optional[int]) -> Optional[str]:
    if code is None:
        return None
    if code in [1, 2, 3, 4, 5, 6, 7, 8]:
        return f"R{code}"
    if 91 <= code <= 94:
        return f"R9({code - 90})"
    if 101 <= code <= 104:
        return f"R10({code - 100})"
    return f"R{code}"


def _load_or_create_config(dataset_id: str) -> DatasetConfig:
    config_data = repository.get_dataset_config_data(dataset_id)
    if config_data:
        try:
            return DatasetConfig.model_validate(config_data)
        except ValidationError:
            pass

    dataset = repository.get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(404, f"Dataset {dataset_id} no encontrado")

    metadata = dataset.metadata_json or {}
    pkl_file = metadata.get("pkl_file") or f"{dataset_id}.pkl"
    config = DatasetConfig(dataset_id=dataset_id, pkl_file=pkl_file)
    repository.save_dataset_config(dataset_id, config.model_dump(mode="json"))
    return config


def _save_config(config: DatasetConfig) -> None:
    repository.save_dataset_config(config.dataset_id, config.model_dump(mode="json"))
    repository.record_history(
        config.dataset_id,
        "update_config",
        {"config": config.model_dump(mode="json")},
    )


def _rebuild_aggregates(dataset_id: str) -> None:
    events_payload = repository.get_events(dataset_id)
    aggregator.rebuild_from_events(dataset_id, events_payload.get("events", []))


def _matches_rule(event: Dict[str, Any], rule: CorrectionRule) -> bool:
    condition = rule.condition

    if condition.origin_cardinal and event.get("origin_cardinal") != condition.origin_cardinal:
        return False
    if condition.destination_cardinal and event.get("destination_cardinal") != condition.destination_cardinal:
        return False
    if condition.class_in and event.get("class") not in condition.class_in:
        return False
    if condition.class_not_in and event.get("class") in condition.class_not_in:
        return False
    if condition.mov_rilsa is not None and event.get("mov_rilsa") != condition.mov_rilsa:
        return False

    trajectory = event.get("positions") or event.get("trajectory") or []
    if condition.trajectory_length is not None and len(trajectory) != condition.trajectory_length:
        return False
    if condition.trajectory_length_lt is not None and len(trajectory) >= condition.trajectory_length_lt:
        return False
    if condition.trajectory_length_gt is not None and len(trajectory) <= condition.trajectory_length_gt:
        return False

    return True


# ==================== GESTIÓN DE DATASETS ====================

@router.get("/")
async def list_all_datasets():
    """Lista todos los datasets disponibles"""
    datasets = repository.list_datasets()
    result = []

    for ds in datasets:
        dataset_id = ds.get("dataset_key")
        if not dataset_id:
            continue  # Skip datasets without valid dataset_key
        
        metadata = ds.get("metadata") or {}
        config_data = metadata.get("dataset_config")
        rules_count = len(config_data.get("correction_rules", [])) if config_data else 0
        events_total = repository.count_events(dataset_id)

        result.append(
            {
                "dataset_id": dataset_id,
                "created_at": ds.get("created_at"),
                "last_modified": ds.get("updated_at"),
                "pkl_file": metadata.get("pkl_file"),
                "events_count": events_total,
                "has_config": config_data is not None,
                "rules_count": rules_count,
            }
        )

    return {"datasets": result}


@router.get("/{dataset_id}/info")
async def get_dataset_info(dataset_id: str):
    """Obtiene información completa de un dataset"""
    config = _load_or_create_config(dataset_id)
    total = repository.count_events(dataset_id)
    return {
        "dataset_id": dataset_id,
        "config": config.model_dump(mode="json"),
        "events_count": total,
    }


@router.get("/{dataset_id}/config")
async def get_dataset_config(dataset_id: str):
    """Obtiene la configuración de un dataset"""
    config = _load_or_create_config(dataset_id)
    return config.model_dump(mode="json")


@router.put("/{dataset_id}/config")
async def update_dataset_config(dataset_id: str, config: DatasetConfig):
    """Actualiza la configuración de un dataset"""
    if config.dataset_id != dataset_id:
        raise HTTPException(400, "dataset_id inconsistente")

    config.last_modified = datetime.utcnow()
    _save_config(config)

    return {"message": "Configuración actualizada", "config": config.model_dump(mode="json")}


@router.post("/{dataset_id}/config/initialize")
async def initialize_dataset_config(dataset_id: str, pkl_file: str):
    """Inicializa la configuración de un dataset nuevo"""
    dataset = repository.get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(404, f"Dataset {dataset_id} no encontrado")

    config = DatasetConfig(dataset_id=dataset_id, pkl_file=pkl_file)
    repository.save_dataset_config(dataset_id, config.model_dump(mode="json"))
    repository.record_history(dataset_id, "initialize_config", {"pkl_file": pkl_file})
    return {"message": "Configuración inicializada", "config": config.model_dump(mode="json")}


# ==================== GESTIÓN DE EVENTOS ====================

class EventFilters(BaseModel):
    class_name: Optional[str] = None
    origin_cardinal: Optional[str] = None
    mov_rilsa: Optional[int] = None


@router.get("/{dataset_id}/events")
async def get_events(
    dataset_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    class_name: Optional[str] = None,
    origin_cardinal: Optional[str] = None,
    mov_rilsa: Optional[int] = None,
    track_id: Optional[str] = None
):
    """
    Obtiene eventos con paginación y filtros

    - skip: Número de eventos a saltar
    - limit: Número máximo de eventos a retornar
    - class_name: Filtrar por clase (car, motorcycle, person, etc.)
    - origin_cardinal: Filtrar por punto cardinal de origen (N, S, E, O)
    - mov_rilsa: Filtrar por movimiento RILSA
    - track_id: Filtrar por track ID (búsqueda parcial)
    """
    filters = {
        "class": class_name,
        "origin_cardinal": origin_cardinal,
        "mov_rilsa": mov_rilsa,
        "track_id": track_id,
    }
    events, total = repository.list_events_paginated(dataset_id, skip=skip, limit=limit, filters=filters)

    serialized = []
    for event in events:
        serialized.append(
            {
                "track_id": event.get("track_id"),
                "class": event.get("class"),
                "origin_cardinal": event.get("origin_cardinal"),
                "destination_cardinal": event.get("destination_cardinal"),
                "mov_rilsa": event.get("mov_rilsa"),
                "movimiento_rilsa": _format_rilsa_label(event.get("mov_rilsa")),
                "trajectory": event.get("positions"),
                "timestamp_start": event.get("frame_entry"),
                "timestamp_end": event.get("frame_exit"),
            }
        )

    return {
        "events": serialized,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + len(serialized)) < total,
    }


@router.get("/{dataset_id}/events/{track_id}")
async def get_event_by_id(dataset_id: str, track_id: str):
    """Obtiene un evento específico por track_id"""
    event = repository.get_event_by_track(dataset_id, track_id)
    if not event:
        raise HTTPException(404, f"Evento con track_id={track_id} no encontrado")

    return {
        "track_id": event.get("track_id"),
        "class": event.get("class"),
        "origin_cardinal": event.get("origin_cardinal"),
        "destination_cardinal": event.get("destination_cardinal"),
        "mov_rilsa": event.get("mov_rilsa"),
        "movimiento_rilsa": _format_rilsa_label(event.get("mov_rilsa")),
        "trajectory": event.get("positions"),
    }


@router.put("/{dataset_id}/events/{track_id}")
async def update_event(dataset_id: str, track_id: str, updates: EventUpdate):
    """Actualiza un evento específico"""
    updates_dict = updates.model_dump(exclude_none=True, by_alias=True)
    success = repository.update_event_fields(dataset_id, str(track_id), updates_dict)

    if not success:
        raise HTTPException(404, f"Evento con track_id={track_id} no encontrado")

    repository.record_history(dataset_id, "update_event", {"track_id": track_id, "updates": updates_dict})
    _rebuild_aggregates(dataset_id)

    return {"message": "Evento actualizado", "track_id": track_id}


@router.delete("/{dataset_id}/events/{track_id}")
async def delete_event(dataset_id: str, track_id: str):
    """Elimina un evento"""
    success = repository.delete_event(dataset_id, str(track_id))

    if not success:
        raise HTTPException(404, f"Evento con track_id={track_id} no encontrado")

    repository.record_history(dataset_id, "delete_event", {"track_id": track_id})
    _rebuild_aggregates(dataset_id)

    return {"message": "Evento eliminado", "track_id": track_id}


# ==================== GESTIÓN DE REGLAS ====================

@router.get("/{dataset_id}/rules")
async def get_rules(dataset_id: str):
    """Obtiene las reglas de corrección de un dataset"""
    config = _load_or_create_config(dataset_id)
    return {"rules": [rule.model_dump(mode="json") for rule in config.correction_rules]}


@router.post("/{dataset_id}/rules")
async def create_rule(dataset_id: str, rule: CorrectionRule):
    """Crea una nueva regla de corrección"""
    config = _load_or_create_config(dataset_id)

    # Verificar que no exista una regla con el mismo ID
    if any(r.id == rule.id for r in config.correction_rules):
        raise HTTPException(400, f"Ya existe una regla con id={rule.id}")

    config.correction_rules.append(rule)
    _save_config(config)

    return {"message": "Regla creada", "rule": rule.model_dump(mode="json")}


@router.put("/{dataset_id}/rules/{rule_id}")
async def update_rule(dataset_id: str, rule_id: str, rule: CorrectionRule):
    """Actualiza una regla existente"""
    config = _load_or_create_config(dataset_id)

    # Buscar y actualizar la regla
    found = False
    for i, r in enumerate(config.correction_rules):
        if r.id == rule_id:
            config.correction_rules[i] = rule
            found = True
            break

    if not found:
        raise HTTPException(404, f"Regla con id={rule_id} no encontrada")

    _save_config(config)

    return {"message": "Regla actualizada", "rule": rule.model_dump(mode="json")}


@router.delete("/{dataset_id}/rules/{rule_id}")
async def delete_rule(dataset_id: str, rule_id: str):
    """Elimina una regla"""
    config = _load_or_create_config(dataset_id)

    # Filtrar la regla
    original_len = len(config.correction_rules)
    config.correction_rules = [r for r in config.correction_rules if r.id != rule_id]

    if len(config.correction_rules) == original_len:
        raise HTTPException(404, f"Regla con id={rule_id} no encontrada")

    _save_config(config)

    return {"message": "Regla eliminada", "rule_id": rule_id}


class ApplyRulesRequest(BaseModel):
    rule_ids: Optional[List[str]] = None  # Si es None, aplica todas las reglas activas


@router.post("/{dataset_id}/apply-rules")
async def apply_rules(dataset_id: str, request: ApplyRulesRequest):
    """Aplica reglas de corrección al dataset"""
    config = _load_or_create_config(dataset_id)
    rules = [rule for rule in config.correction_rules if rule.enabled]
    if request.rule_ids:
        rules = [rule for rule in rules if rule.id in set(request.rule_ids)]

    if not rules:
        return {
            "events_before": repository.count_events(dataset_id),
            "events_after": repository.count_events(dataset_id),
            "removed": 0,
            "rules_applied": [],
            "details": ["No se encontraron reglas habilitadas."],
        }

    events_payload = repository.get_events(dataset_id)
    events = events_payload.get("events", [])
    events_before = len(events)

    rules_applied: List[str] = []
    details: List[str] = []
    removed = 0

    for rule in rules:
        removed_this_rule = 0
        for event in list(events):
            if _matches_rule(event, rule):
                repository.delete_event(dataset_id, str(event.get("track_id")))
                events.remove(event)
                removed += 1
                removed_this_rule += 1
        if removed_this_rule:
            rules_applied.append(rule.id)
            details.append(f"{rule.name}: {removed_this_rule} eventos eliminados")

    if removed:
        _rebuild_aggregates(dataset_id)
    repository.record_history(
        dataset_id,
        "apply_rules",
        {
            "rules_applied": rules_applied,
            "removed": removed,
        },
    )

    events_after = repository.count_events(dataset_id)
    return {
        "events_before": events_before,
        "events_after": events_after,
        "removed": removed,
        "rules_applied": rules_applied,
        "details": details or ["No se eliminaron eventos"],
    }


# ==================== HISTORIAL ====================

@router.get("/{dataset_id}/history")
async def get_history(dataset_id: str):
    """Obtiene el historial de cambios de un dataset"""
    history = repository.get_history(dataset_id)
    return {"history": history, "total": len(history)}


# ==================== CONFIGURACIÓN DE PUNTOS CARDINALES ====================

@router.put("/{dataset_id}/cardinal-points/{cardinal}")
async def update_cardinal_point(
    dataset_id: str,
    cardinal: str,
    point_config: CardinalPointConfig
):
    """Actualiza la configuración de un punto cardinal"""
    if cardinal not in ["N", "S", "E", "O"]:
        raise HTTPException(400, "Punto cardinal inválido. Debe ser N, S, E u O")

    config = _load_or_create_config(dataset_id)
    config.cardinal_points[cardinal] = point_config
    _save_config(config)

    return {
        "message": f"Punto cardinal {cardinal} actualizado",
        "config": point_config.model_dump(mode="json"),
    }


# ==================== ESTADÍSTICAS ====================

@router.get("/{dataset_id}/stats")
async def get_dataset_stats(dataset_id: str):
    """Obtiene estadísticas generales del dataset"""
    stats = repository.get_event_stats(dataset_id)
    total = repository.count_events(dataset_id)

    return {
        "total_events": total,
        "by_class": stats["by_class"],
        "by_origin": stats["by_origin"],
        "by_rilsa_movement": stats["by_rilsa"],
    }


# ==================== GESTIÓN DE CORRECCIONES DE TRAYECTORIA ====================

class TrajectoryCorrectionsResponse(BaseModel):
    corrections: Mapping[str, TrajectoryCorrection]
    total_corrections: int


@router.post("/{dataset_id}/trajectory-corrections", response_model=TrajectoryCorrectionsResponse)
async def save_trajectory_correction(dataset_id: str, correction: TrajectoryCorrection):
    """Guarda o actualiza una corrección para una trayectoria específica."""
    config = _load_or_create_config(dataset_id)

    # Almacenar la corrección. Si ya existe, se sobrescribe.
    config.trajectory_corrections[correction.track_id] = correction

    _save_config(config)

    return TrajectoryCorrectionsResponse(
        corrections=config.trajectory_corrections,
        total_corrections=len(config.trajectory_corrections)
    )


@router.get("/{dataset_id}/trajectory-corrections", response_model=TrajectoryCorrectionsResponse)
async def get_trajectory_corrections(dataset_id: str):
    """Obtiene todas las correcciones de trayectoria para un dataset."""
    config = _load_or_create_config(dataset_id)

    return TrajectoryCorrectionsResponse(
        corrections=config.trajectory_corrections,
        total_corrections=len(config.trajectory_corrections)
    )
