"""
Router para validación de trayectorias
Endpoints: /api/validation/*
"""

from fastapi import APIRouter, HTTPException, Path as PathParam
from pathlib import Path
from typing import Dict, Optional
import json
import logging

from services.rules_validator import RulesValidator
from services.dataset_config import DatasetConfigService
from services.cardinals import CardinalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/validation", tags=["validation"])

# Directorio de datos
DATA_DIR = Path("data")

# Servicios
validator = RulesValidator()
config_service = DatasetConfigService(DATA_DIR)
cardinal_service = CardinalService(DATA_DIR)


@router.post("/run/{dataset_id}")
async def run_validation(
    dataset_id: str = PathParam(..., description="ID del dataset"),
    auto_fix: bool = False
):
    """
    Ejecuta las reglas de rules_validator sobre un dataset cargado
    
    Parámetros:
    - dataset_id: ID del dataset a validar
    - auto_fix: Si True, intenta corregir automáticamente (futuro)
    
    Returns:
    - Trayectorias válidas e inválidas
    - Estadísticas de validación
    - Errores por tipo
    """
    try:
        dataset_dir = DATA_DIR / dataset_id
        if not dataset_dir.exists():
            raise HTTPException(404, f"Dataset {dataset_id} no encontrado")

        # Cargar configuración
        config = config_service.load_config(dataset_id)
        if not config:
            # Crear configuración por defecto si no existe
            logger.warning(f"Configuración no encontrada para {dataset_id}, usando valores por defecto")
            metadata_file = dataset_dir / "metadata.json"
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                config = config_service.create_default_config(
                    dataset_id,
                    metadata.get("name", dataset_id)
                )
            else:
                raise HTTPException(400, "Dataset no tiene configuración ni metadata")

        # Cargar trayectorias
        playback_file = dataset_dir / "playback_events.json"
        if not playback_file.exists():
            raise HTTPException(400, "Dataset no tiene trayectorias procesadas")

        trajectories_data = json.loads(playback_file.read_text())
        trajectories = trajectories_data if isinstance(trajectories_data, list) else trajectories_data.get("events", [])

        if not trajectories:
            raise HTTPException(400, "No hay trayectorias disponibles para validar")

        # Cargar mapa RILSA si existe
        rilsa_map = cardinal_service.load_rilsa_map(dataset_id)

        # Validar trayectorias
        logger.info(f"Validando {len(trajectories)} trayectorias para {dataset_id}...")
        result = validator.validate_batch(trajectories, config, rilsa_map)

        # Detectar trayectorias incompletas
        incomplete = validator.detect_incomplete_trajectories(trajectories)

        # Estadísticas adicionales
        stats = result["statistics"]
        stats["incomplete_count"] = len(incomplete)
        stats["completion_rate"] = (
            (stats["valid"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )

        # Guardar resultados de validación (opcional)
        from datetime import datetime
        validation_file = dataset_dir / "validation_results.json"
        validation_results = {
            "dataset_id": dataset_id,
            "validated_at": datetime.now().isoformat(),
            "statistics": stats,
            "invalid_trajectories": [
                {
                    "track_id": t.get("track_id"),
                    "errors": t.get("validation_errors", [])
                }
                for t in result["invalid"][:100]  # Limitar a 100 para no sobrecargar
            ],
            "incomplete_trajectories": [
                {
                    "track_id": t.get("track_id"),
                    "reasons": t.get("incomplete_reasons", [])
                }
                for t in incomplete[:100]
            ]
        }
        validation_file.write_text(json.dumps(validation_results, indent=2, default=str))

        logger.info(
            f"Validación completada: {stats['valid']}/{stats['total']} válidas "
            f"({stats['invalid']} inválidas, {len(incomplete)} incompletas)"
        )

        return {
            "status": "success",
            "dataset_id": dataset_id,
            "statistics": stats,
            "valid_count": len(result["valid"]),
            "invalid_count": len(result["invalid"]),
            "incomplete_count": len(incomplete),
            "errors_by_type": stats.get("errors_by_type", {}),
            "validation_file": str(validation_file),
            "message": f"Validación completada: {stats['valid']}/{stats['total']} trayectorias válidas"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando validación: {e}", exc_info=True)
        raise HTTPException(500, f"Error ejecutando validación: {str(e)}")


@router.get("/results/{dataset_id}")
async def get_validation_results(
    dataset_id: str = PathParam(..., description="ID del dataset")
):
    """
    Obtiene resultados de validación previa
    
    Returns:
    - Estadísticas de última validación
    - Lista de errores comunes
    - Recomendaciones
    """
    try:
        dataset_dir = DATA_DIR / dataset_id
        if not dataset_dir.exists():
            raise HTTPException(404, f"Dataset {dataset_id} no encontrado")

        validation_file = dataset_dir / "validation_results.json"
        if not validation_file.exists():
            raise HTTPException(404, "No hay resultados de validación. Ejecuta /run primero.")

        results = json.loads(validation_file.read_text())

        return {
            "status": "success",
            "dataset_id": dataset_id,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo resultados: {e}", exc_info=True)
        raise HTTPException(500, f"Error obteniendo resultados: {str(e)}")

