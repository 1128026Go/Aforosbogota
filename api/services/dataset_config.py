"""
Servicio de configuración de datasets
Gestiona dataset_config.json con polígonos, cardinales, reglas y validaciones
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from pydantic import ValidationError

from models.dataset_config import (
    CardinalPointConfig,
    CorrectionRule,
    CorrectionRuleCondition,
    DatasetConfig,
)

from services.aforo_repository import AforoRepository

logger = logging.getLogger(__name__)


class DatasetConfigService:
    """Gestión de configuración completa de datasets"""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.repository = AforoRepository()

    def get_config_path(self, dataset_id: str) -> Path:
        """Obtener ruta del archivo de configuración"""
        return self.data_dir / dataset_id / "dataset_config.json"

    def load_config(self, dataset_id: str) -> Optional[Dict]:
        """Cargar configuración completa del dataset"""
        config_path = self.get_config_path(dataset_id)

        if not config_path.exists():
            config_data = self.repository.get_dataset_config_data(dataset_id)
            if not config_data:
                return None
            try:
                return self._dataset_config_to_legacy(dataset_id, config_data)
            except Exception as exc:
                logger.warning("No se pudo convertir configuración desde la base de datos: %s", exc)
                return None

        try:
            return json.loads(config_path.read_text())
        except Exception as e:
            logger.error(f"Error cargando configuración de {dataset_id}: {e}")
            return None

    def save_config(self, dataset_id: str, config: Dict) -> None:
        """Guardar configuración completa del dataset"""
        if isinstance(config, DatasetConfig):
            config_model: DatasetConfig = config
            config_dict = config_model.model_dump(mode="json")
            legacy_payload = self._dataset_config_to_legacy(dataset_id, config_dict)
        else:
            raw_dict = config if isinstance(config, dict) else dict(config)
            if "cardinal_config" in raw_dict:
                legacy_payload = raw_dict
                config_model = self._convert_legacy_to_dataset_config(dataset_id, raw_dict)
                config_dict = config_model.model_dump(mode="json")
            else:
                config_model = DatasetConfig.model_validate(raw_dict)
                config_dict = config_model.model_dump(mode="json")
                legacy_payload = self._dataset_config_to_legacy(dataset_id, config_dict)

        dataset_dir = self.data_dir / dataset_id
        dataset_dir.mkdir(exist_ok=True)

        config_path = self.get_config_path(dataset_id)

        # Agregar metadata de actualización
        legacy_payload = json.loads(json.dumps(legacy_payload))
        legacy_payload["metadata"] = legacy_payload.get("metadata", {})
        legacy_payload["metadata"]["updated_at"] = datetime.now().isoformat()

        config_path.write_text(json.dumps(legacy_payload, indent=2, ensure_ascii=False))
        try:
            self.repository.save_dataset_config(dataset_id, config_model.model_dump(mode="json"))
        except Exception as exc:
            logger.warning("No se pudo sincronizar configuración en la base de datos: %s", exc)

        logger.info(f"Configuración guardada: {config_path}")

    def create_default_config(
        self,
        dataset_id: str,
        name: str,
        accesses: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Crear configuración por defecto para un dataset

        Args:
            dataset_id: ID del dataset
            name: Nombre del dataset
            accesses: Lista de accesos (opcional, se puede auto-detectar)

        Returns:
            Configuración por defecto
        """
        config = {
            "dataset_id": dataset_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "cardinal_config": {
                "accesses": accesses or {}
            },
            "trajectory_filters": {
                "min_duration_seconds": 2.0,
                "max_duration_seconds": 300.0,
                "min_distance_meters": 5.0,
                "max_distance_meters": 500.0,
                "min_speed_kmh": 1.0,
                "max_speed_kmh": 120.0,
                "remove_stationary": True,
                "remove_outliers": True
            },
            "correction_rules": [
                {
                    "rule_id": "remove_pedestrians_without_trajectory",
                    "description": "Eliminar peatones sin trayectoria válida",
                    "enabled": True,
                    "priority": 10,
                    "conditions": {
                        "class": "person",
                        "min_points": 5
                    },
                    "action": "delete"
                }
            ],
            "report_settings": {
                "interval_minutes": 15,
                "generate_pdf": True,
                "generate_csv": True,
                "generate_diagrams": True,
                "include_statistics": True
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }

        return config

    def _convert_legacy_to_dataset_config(self, dataset_id: str, legacy: Dict) -> DatasetConfig:
        dataset_key = legacy.get("dataset_id", dataset_id)
        metadata = legacy.get("metadata", {}) or {}
        pkl_file = metadata.get("pkl_file") or f"{dataset_key}.pkl"

        base_config = DatasetConfig(dataset_id=dataset_key, pkl_file=pkl_file)

        accesses = legacy.get("cardinal_config", {}).get("accesses", {}) or {}
        updated_points = dict(base_config.cardinal_points)

        for cardinal, access in accesses.items():
            if cardinal not in ["N", "S", "E", "O"]:
                continue
            coordinates = {}
            if "centroid_x" in access and "centroid_y" in access:
                coordinates = {"x": float(access["centroid_x"]), "y": float(access["centroid_y"])}
            updated_points[cardinal] = CardinalPointConfig(
                entry_only=not access.get("allows_exit", True),
                allow_pedestrians=access.get("pedestrian_allowed", True),
                allow_vehicles=True,
                coordinates=coordinates or None,
            )

        rules: List[CorrectionRule] = []
        action_map = {
            "delete": "remove",
            "remove": "remove",
            "keep": "keep",
            "flag": "flag",
            "modify": "modify_field",
            "modify_field": "modify_field",
        }

        for rule in legacy.get("correction_rules", []) or []:
            rule_id = rule.get("rule_id") or rule.get("id") or f"rule_{len(rules) + 1}"
            conditions = rule.get("conditions", {}) or {}
            condition_payload = {}
            class_name = conditions.get("class")
            if class_name:
                condition_payload["class_in"] = [class_name]
            origin_cardinal = conditions.get("origin_cardinal")
            if origin_cardinal:
                condition_payload["origin_cardinal"] = origin_cardinal
            destination_cardinal = conditions.get("destination_cardinal")
            if destination_cardinal:
                condition_payload["destination_cardinal"] = destination_cardinal
            mov_rilsa = conditions.get("mov_rilsa")
            if mov_rilsa is not None:
                condition_payload["mov_rilsa"] = mov_rilsa
            trajectory_length_gt = conditions.get("min_points")
            if trajectory_length_gt is not None:
                condition_payload["trajectory_length_gt"] = trajectory_length_gt

            try:
                condition_model = CorrectionRuleCondition(**condition_payload)
            except ValidationError:
                condition_model = CorrectionRuleCondition()

            rules.append(
                CorrectionRule(
                    id=rule_id,
                    name=rule.get("description") or rule_id,
                    type="filter",
                    condition=condition_model,
                    action=action_map.get(rule.get("action", "keep"), "keep"),
                    field_modifications=rule.get("field_modifications"),
                    enabled=rule.get("enabled", True),
                )
            )

        return base_config.model_copy(
            update={
                "cardinal_points": updated_points,
                "correction_rules": rules,
                "intersection_name": legacy.get("name"),
                "video_info": metadata,
                "notes": legacy.get("notes"),
            }
        )

    def _dataset_config_to_legacy(self, dataset_id: str, config_data: Dict) -> Dict:
        config_model = DatasetConfig.model_validate(config_data)

        accesses: Dict[str, Dict] = {}
        for cardinal, point in config_model.cardinal_points.items():
            coordinates = point.coordinates or {}
            accesses[cardinal] = {
                "id": f"{dataset_id}_{cardinal}",
                "name": f"Acceso {cardinal}",
                "cardinal": cardinal,
                "entry_polygon": [],
                "exit_polygon": [],
                "allows_entry": True,
                "allows_exit": not point.entry_only,
                "vehicle_types_allowed": ["car", "motorcycle", "bus", "truck"] if point.allow_vehicles else [],
                "pedestrian_allowed": point.allow_pedestrians,
                "centroid_x": coordinates.get("x", 0),
                "centroid_y": coordinates.get("y", 0),
            }

        legacy_rules: List[Dict] = []
        for rule in config_model.correction_rules:
            conditions: Dict[str, Any] = {}
            if rule.condition.class_in:
                conditions["class"] = rule.condition.class_in[0]
            if rule.condition.origin_cardinal:
                conditions["origin_cardinal"] = rule.condition.origin_cardinal
            if rule.condition.destination_cardinal:
                conditions["destination_cardinal"] = rule.condition.destination_cardinal
            if rule.condition.mov_rilsa is not None:
                conditions["mov_rilsa"] = rule.condition.mov_rilsa

            legacy_rules.append(
                {
                    "rule_id": rule.id,
                    "description": rule.name,
                    "enabled": rule.enabled,
                    "conditions": conditions,
                    "action": "delete" if rule.action == "remove" else rule.action,
                }
            )

        return {
            "dataset_id": dataset_id,
            "name": config_model.intersection_name or dataset_id,
            "cardinal_config": {"accesses": accesses},
            "correction_rules": legacy_rules,
            "metadata": config_model.video_info or {},
            "created_at": config_model.created_at.isoformat(),
            "version": "2.0",
        }

    def auto_detect_cardinals_from_trajectories(
        self,
        dataset_id: str,
        trajectories: List[Dict]
    ) -> Dict:
        """
        Auto-detectar accesos cardinales desde trayectorias

        Args:
            dataset_id: ID del dataset
            trajectories: Lista de trayectorias

        Returns:
            Configuración de accesos detectados
        """
        from services.rilsa_generator import RilsaGenerator

        # Usar método existente de RilsaGenerator
        accesses_list = RilsaGenerator.detect_cardinal_accesses_from_trajectories(trajectories)

        if not accesses_list:
            accesses_list = self._fallback_accesses_from_cardinals(trajectories)

        # Convertir a formato de configuración
        accesses_dict = {}
        for access in accesses_list:
            cardinal = access.get("cardinal", "")
            if cardinal:
                accesses_dict[cardinal] = {
                    "id": access.get("id", f"access_{cardinal}"),
                    "name": access.get("name", f"Acceso {cardinal}"),
                    "cardinal": cardinal,
                    "centroid_x": access.get("centroid_x", 0),
                    "centroid_y": access.get("centroid_y", 0),
                    "entry_polygon": [],  # Se debe configurar manualmente
                    "exit_polygon": [],  # Se debe configurar manualmente
                    "allows_entry": True,
                    "allows_exit": True,
                    "vehicle_types_allowed": ["car", "motorcycle", "bus", "truck"],
                    "pedestrian_allowed": True,
                    "num_trajectories": access.get("num_trajectories", 0)
                }

        logger.info(f"Auto-detectados {len(accesses_dict)} accesos cardinales para {dataset_id}")

        return {
            "accesses": accesses_dict,
            "auto_detected": True,
            "detected_at": datetime.now().isoformat()
        }

    def _fallback_accesses_from_cardinals(self, trajectories: List[Dict]) -> List[Dict]:
        """Construye accesos básicos a partir de los cardinales presentes en las trayectorias."""
        cardinal_order = ["N", "S", "E", "O"]
        counts = defaultdict(int)

        for traj in trajectories:
            origin = traj.get("cardinal_origin") or traj.get("origin_cardinal")
            dest = traj.get("cardinal_destination") or traj.get("dest_cardinal")

            if origin:
                counts[origin] += 1
            if dest:
                counts[dest] += 0  # Garantiza presencia aunque no incremente

        # Garantizar orden consistente
        ordered_cardinals = [c for c in cardinal_order if c in counts]
        for cardinal in sorted(counts.keys()):
            if cardinal not in ordered_cardinals:
                ordered_cardinals.append(cardinal)

        accesses = []
        for cardinal in ordered_cardinals:
            accesses.append(
                {
                    "id": f"access_{cardinal}",
                    "name": f"Acceso {cardinal}",
                    "cardinal": cardinal,
                    "centroid_x": 0,
                    "centroid_y": 0,
                    "num_trajectories": counts.get(cardinal, 0),
                }
            )

        if not accesses and trajectories:
            # Como último recurso crear accesos genéricos
            accesses = [
                {"id": "access_N", "name": "Acceso N", "cardinal": "N", "centroid_x": 0, "centroid_y": 0, "num_trajectories": 0},
                {"id": "access_S", "name": "Acceso S", "cardinal": "S", "centroid_x": 0, "centroid_y": 0, "num_trajectories": 0},
            ]

        return accesses

    def update_access_polygons(
        self,
        dataset_id: str,
        cardinal: str,
        entry_polygon: List[List[float]],
        exit_polygon: List[List[float]]
    ) -> bool:
        """
        Actualizar polígonos de entrada/salida para un acceso

        Args:
            dataset_id: ID del dataset
            cardinal: Cardinal (N, S, E, O)
            entry_polygon: Polígono de entrada [[x1, y1], [x2, y2], ...]
            exit_polygon: Polígono de salida [[x1, y1], [x2, y2], ...]

        Returns:
            True si se actualizó correctamente
        """
        config = self.load_config(dataset_id)
        if not config:
            logger.error(f"Configuración no encontrada para {dataset_id}")
            return False

        cardinal_config = config.get("cardinal_config", {})
        accesses = cardinal_config.get("accesses", {})

        if cardinal not in accesses:
            logger.warning(f"Acceso {cardinal} no existe, creándolo...")
            accesses[cardinal] = {
                "id": f"access_{cardinal}",
                "name": f"Acceso {cardinal}",
                "cardinal": cardinal
            }

        accesses[cardinal]["entry_polygon"] = entry_polygon
        accesses[cardinal]["exit_polygon"] = exit_polygon

        self.save_config(dataset_id, config)

        logger.info(f"Polígonos actualizados para acceso {cardinal} en {dataset_id}")

        return True

    def infer_movements_from_config(self, dataset_id: str) -> Dict:
        """
        Inferir movimientos válidos desde la configuración del dataset

        Args:
            dataset_id: ID del dataset

        Returns:
            Mapa de movimientos inferidos
        """
        config = self.load_config(dataset_id)
        if not config:
            logger.error(f"Configuración no encontrada para {dataset_id}")
            return {}

        cardinal_config = config.get("cardinal_config", {})
        accesses = cardinal_config.get("accesses", {})

        if not accesses:
            logger.warning(f"No hay accesos configurados para {dataset_id}")
            return {}

        from services.rilsa_generator import RilsaGenerator

        # Usar método de RilsaGenerator
        movements = RilsaGenerator.infer_movements_from_polygons(accesses)

        logger.info(f"Movimientos inferidos: {len(movements)} para {dataset_id}")

        return movements

    def get_access_coordinates(self, dataset_id: str) -> Dict[str, Dict]:
        """
        Obtener coordenadas de todos los accesos

        Returns:
            {
                "N": {
                    "entry_polygon": [[x1, y1], ...],
                    "exit_polygon": [[x1, y1], ...],
                    "centroid": {"x": 425.5, "y": 100.2}
                },
                ...
            }
        """
        config = self.load_config(dataset_id)
        if not config:
            return {}

        cardinal_config = config.get("cardinal_config", {})
        accesses = cardinal_config.get("accesses", {})

        coordinates = {}
        for cardinal, access in accesses.items():
            entry_poly = access.get("entry_polygon", [])
            exit_poly = access.get("exit_polygon", [])

            # Calcular centroide si hay polígonos
            centroid = {"x": 0, "y": 0}
            if entry_poly:
                centroid_x = sum(p[0] for p in entry_poly) / len(entry_poly)
                centroid_y = sum(p[1] for p in entry_poly) / len(entry_poly)
                centroid = {"x": centroid_x, "y": centroid_y}
            elif access.get("centroid_x") and access.get("centroid_y"):
                centroid = {
                    "x": access.get("centroid_x", 0),
                    "y": access.get("centroid_y", 0)
                }

            coordinates[cardinal] = {
                "entry_polygon": entry_poly,
                "exit_polygon": exit_poly,
                "centroid": centroid,
                "name": access.get("name", f"Acceso {cardinal}")
            }

        return coordinates



