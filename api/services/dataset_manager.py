"""
Servicio para gestionar datasets, configuraciones y historial
Incluye normalización de campos para compatibilidad frontend
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from models.dataset_config import (
    DatasetConfig,
    CorrectionRule,
    HistoryEntry,
    CardinalPointConfig,
)
from services.aggregate import AggregatorService
from services.classify import assign_rilsa


class DatasetManager:
    """Gestor de datasets con configuración y historial"""

    def __init__(self, base_path: str = "data", aggregator: Optional[AggregatorService] = None):
        # Convertir a path absoluto basado en el directorio del script
        if Path(base_path).is_absolute():
            self.base_path = Path(base_path)
        else:
            # Desde api/services/dataset_manager.py, subir 2 niveles y entrar a api/data
            script_dir = Path(__file__).parent.parent  # Sube a api/
            self.base_path = script_dir / base_path

        self.aggregator = aggregator or AggregatorService(self.base_path)
        self._rilsa_cache: Dict[str, Optional[Dict]] = {}

    def list_datasets(self) -> List[Dict]:
        """Lista todos los datasets disponibles"""
        datasets = []

        for dataset_dir in self.base_path.glob("dataset_*"):
            if dataset_dir.is_dir():
                config = self.get_config(dataset_dir.name)
                playback_file = dataset_dir / "playback_events.json"

                info = {
                    "dataset_id": dataset_dir.name,
                    "created_at": self._serialize_datetime(config.created_at) if config else None,
                    "last_modified": self._serialize_datetime(config.last_modified) if config else None,
                    "pkl_file": config.pkl_file if config else None,
                    "events_count": self._count_events(playback_file),
                    "has_config": config is not None,
                    "rules_count": len(config.correction_rules) if config else 0
                }
                datasets.append(info)

        return sorted(datasets, key=lambda x: x["last_modified"] or "", reverse=True)

    def get_config(self, dataset_id: str) -> Optional[DatasetConfig]:
        """Obtiene la configuración de un dataset"""
        config_file = self.base_path / dataset_id / "dataset_config.json"

        # DEBUG: Print paths
        print(f"[DEBUG] DatasetManager.get_config():")
        print(f"  base_path: {self.base_path}")
        print(f"  dataset_id: {dataset_id}")
        print(f"  config_file: {config_file}")
        print(f"  exists: {config_file.exists()}")

        if not config_file.exists():
            return None

        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return DatasetConfig(**data)

    def save_config(self, dataset_id: str, config: DatasetConfig) -> bool:
        """Guarda la configuración de un dataset"""
        config_file = self.base_path / dataset_id / "dataset_config.json"
        config.last_modified = datetime.now()

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(), f, ensure_ascii=False, indent=2, default=str)

        return True

    def initialize_config(self, dataset_id: str, pkl_file: str) -> DatasetConfig:
        """Inicializa la configuración por defecto de un nuevo dataset"""
        config = DatasetConfig(
            dataset_id=dataset_id,
            pkl_file=pkl_file,
            created_at=datetime.now(),
            last_modified=datetime.now(),
            cardinal_points={
                "N": CardinalPointConfig(entry_only=True, allow_pedestrians=True, allow_vehicles=False),
                "S": CardinalPointConfig(),
                "E": CardinalPointConfig(),
                "O": CardinalPointConfig()
            },
            correction_rules=self._get_default_rules()
        )

        self.save_config(dataset_id, config)
        return config

    @staticmethod
    def _serialize_datetime(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    def _get_default_rules(self) -> List[CorrectionRule]:
        """Reglas de corrección por defecto"""
        from api.models.dataset_config import CorrectionRuleCondition

        return [
            CorrectionRule(
                id="remove_vehicles_from_north",
                name="Eliminar vehículos desde Norte",
                description="Norte es solo entrada, no permite salidas de vehículos",
                type="filter",
                condition=CorrectionRuleCondition(
                    origin_cardinal="N",
                    class_not_in=["person", "pedestrian", "peaton"]
                ),
                action="remove",
                enabled=True
            ),
            CorrectionRule(
                id="remove_pedestrians_no_trajectory",
                name="Eliminar peatones sin trayectoria",
                description="Peatones fantasma sin puntos de trayectoria",
                type="filter",
                condition=CorrectionRuleCondition(
                    class_in=["person", "pedestrian", "peaton"],
                    trajectory_length=0
                ),
                action="remove",
                enabled=True
            )
        ]

    def get_events(self, dataset_id: str,
                   skip: int = 0,
                   limit: int = 100,
                   filters: Optional[Dict] = None) -> Tuple[List[Dict], int]:
        """Obtiene eventos con paginación y filtros"""
        playback_file = self.base_path / dataset_id / "playback_events.json"

        if not playback_file.exists():
            return [], 0

        with open(playback_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            raw_events = data.get("events", [])

        # Normalizar eventos base y persistir si hubo cambios
        raw_events, base_changed = self._normalize_events(dataset_id, raw_events)
        if base_changed:
            data["events"] = raw_events
            self._save_playback_data(dataset_id, data)

        # Aplicar correcciones sobre copias para no mutar la base
        events = self._apply_corrections(dataset_id, [dict(evt) for evt in raw_events])

        # Asegurar consistencia tras correcciones (sin persistir)
        events, _ = self._normalize_events(dataset_id, events, persist=False)

        # Aplicar filtros si existen
        if filters:
            events = self._filter_events(events, filters)

        total = len(events)
        paginated = events[skip:skip + limit]

        return paginated, total

    def _apply_corrections(self, dataset_id: str, events: List[Dict]) -> List[Dict]:
        """Aplica correcciones de trajectory_corrections.json a los eventos"""
        corrections_file = self.base_path / dataset_id / "trajectory_corrections.json"

        if not corrections_file.exists():
            return events

        try:
            with open(corrections_file, 'r', encoding='utf-8') as f:
                corrections_data = json.load(f)
                corrections = corrections_data.get("corrections", {})
        except:
            return events

        corrected_events = []

        for event in events:
            event_copy = dict(event)
            track_id = str(event_copy.get("track_id"))

            # Verificar si hay corrección para este track_id
            if track_id in corrections:
                correction = corrections[track_id]

                # Si está marcado para descartar, omitir este evento
                if correction.get("discard", False):
                    continue

                # Si está marcado para ocultar en PDF, agregar flag al evento
                if correction.get("hide_in_pdf", False):
                    event_copy["hide_in_pdf"] = True

                # Aplicar correcciones de clase
                if correction.get("new_class") is not None:
                    event_copy["class"] = correction["new_class"]

                # Aplicar correcciones de origen
                if correction.get("new_origin") is not None:
                    event_copy["origin_cardinal"] = correction["new_origin"]

                # Aplicar correcciones de destino
                if correction.get("new_dest") is not None:
                    event_copy["destination_cardinal"] = correction["new_dest"]

            corrected_events.append(event_copy)

        return corrected_events

    def _normalize_events(
        self,
        dataset_id: str,
        events: List[Dict],
        persist: bool = True,
    ) -> Tuple[List[Dict], bool]:
        """
        Normaliza eventos agregando aliases y asegurando mov_rilsa coherente.

        Returns:
            events: lista normalizada (misma referencia)
            changed: True si se modificó algún valor persistible
        """
        rilsa_map = self._load_rilsa_map(dataset_id)
        changed = False

        for event in events:
            # Alias destination_cardinal / dest_cardinal
            if "dest_cardinal" in event and "destination_cardinal" not in event:
                event["destination_cardinal"] = event["dest_cardinal"]

            if "destination_cardinal" in event and "dest_cardinal" not in event:
                event["dest_cardinal"] = event["destination_cardinal"]

            # Asegurar cardinales básicos
            origin_cardinal = event.get("origin_cardinal")
            dest_cardinal = event.get("destination_cardinal") or event.get("dest_cardinal")

            # Resolver código RILSA si es posible
            if origin_cardinal and dest_cardinal and rilsa_map:
                computed = assign_rilsa(str(origin_cardinal), str(dest_cardinal), rilsa_map)
                if computed is not None:
                    computed_int = int(computed)
                    if event.get("mov_rilsa") != computed_int:
                        changed = True
                    event["mov_rilsa"] = computed_int
                    event["movimiento_rilsa"] = self._format_rilsa_label(computed)
                elif "mov_rilsa" in event and event["mov_rilsa"] is not None:
                    # Convertir a int si existe pero en string
                    try:
                        event["mov_rilsa"] = int(event["mov_rilsa"])
                    except (TypeError, ValueError):
                        event["mov_rilsa"] = None
                        changed = True
            else:
                # Normalizar tipo entero si ya existe
                if "mov_rilsa" in event and event["mov_rilsa"] is not None:
                    try:
                        event["mov_rilsa"] = int(event["mov_rilsa"])
                    except (TypeError, ValueError):
                        event["mov_rilsa"] = None
                        changed = True

                if event.get("mov_rilsa") is not None and "movimiento_rilsa" not in event:
                    event["movimiento_rilsa"] = self._format_rilsa_label(event["mov_rilsa"])

        return events, changed if persist else False

    def _filter_events(self, events: List[Dict], filters: Dict) -> List[Dict]:
        """Filtra eventos según criterios"""
        filtered = events

        if "class" in filters:
            filtered = [e for e in filtered if e.get("class") == filters["class"]]

        if "origin_cardinal" in filters:
            filtered = [e for e in filtered if e.get("origin_cardinal") == filters["origin_cardinal"]]

        if "mov_rilsa" in filters:
            # Comparación estricta de movimiento RILSA (asegurar que ambos son int)
            filter_mov = int(filters["mov_rilsa"]) if filters["mov_rilsa"] is not None else None
            filtered = [e for e in filtered if int(e.get("mov_rilsa", -1)) == filter_mov]

        if "track_id" in filters:
            # Búsqueda parcial: el track_id del evento debe contener el filtro
            search_term = str(filters["track_id"]).lower()
            filtered = [e for e in filtered if search_term in str(e.get("track_id", "")).lower()]

        return filtered

    def update_event(self, dataset_id: str, track_id: int, updates: Dict) -> bool:
        """Actualiza un evento específico"""
        playback_file = self.base_path / dataset_id / "playback_events.json"

        with open(playback_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Buscar y actualizar el evento
        updated = False
        track_id_str = str(track_id)
        for event in data["events"]:
            if str(event.get("track_id")) == track_id_str:
                event.update(updates)
                updated = True
                break

        if updated:
            # Normalizar eventos completos (garantiza mov_rilsa coherente)
            normalized_events, _ = self._normalize_events(dataset_id, data["events"])
            data["events"] = normalized_events

            # Crear snapshot antes de guardar
            self._create_snapshot(
                dataset_id,
                "update_event",
                {
                    "track_id": track_id,
                    "updates": updates,
                },
            )

            # Guardar cambios y refrescar derivados
            self._save_playback_data(dataset_id, data)

        return updated

    def delete_event(self, dataset_id: str, track_id: int) -> bool:
        """Elimina un evento"""
        playback_file = self.base_path / dataset_id / "playback_events.json"

        with open(playback_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        events_before = len(data["events"])
        track_id_str = str(track_id)
        data["events"] = [e for e in data["events"] if str(e.get("track_id")) != track_id_str]
        events_after = len(data["events"])

        if events_before != events_after:
            # Normalizar y snapshot
            normalized_events, _ = self._normalize_events(dataset_id, data["events"])
            data["events"] = normalized_events

            self._create_snapshot(
                dataset_id,
                "delete_event",
                {
                    "track_id": track_id,
                    "events_before": events_before,
                    "events_after": events_after,
                },
            )

            # Persistir cambios
            self._save_playback_data(dataset_id, data)
            return True

        return False

    def apply_rules(self, dataset_id: str, rule_ids: Optional[List[str]] = None) -> Dict:
        """Aplica reglas de corrección a un dataset"""
        config = self.get_config(dataset_id)
        if not config:
            return {"error": "Dataset config not found"}

        playback_file = self.base_path / dataset_id / "playback_events.json"

        with open(playback_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        events_before = len(data["events"])
        rules_applied = []
        details = []

        # Filtrar reglas a aplicar
        rules = config.correction_rules
        if rule_ids:
            rules = [r for r in rules if r.id in rule_ids]

        # Aplicar cada regla
        for rule in rules:
            if not rule.enabled:
                continue

            result = self._apply_single_rule(data["events"], rule)
            data["events"] = result["events"]

            rules_applied.append(rule.id)
            details.append(f"{rule.name}: {result['removed']} eventos eliminados")

        # Normalizar eventos tras aplicar reglas
        normalized_events, _ = self._normalize_events(dataset_id, data["events"])
        data["events"] = normalized_events

        events_after = len(data["events"])

        # Crear snapshot
        self._create_snapshot(dataset_id, "apply_rules", {
            "events_before": events_before,
            "events_after": events_after,
            "rules_applied": rules_applied,
            "details": details
        })

        # Guardar cambios
        self._save_playback_data(dataset_id, data)

        return {
            "events_before": events_before,
            "events_after": events_after,
            "removed": events_before - events_after,
            "rules_applied": rules_applied,
            "details": details
        }

    def sync_dataset_movements(self, dataset_id: str) -> None:
        """
        Normaliza todos los eventos garantizando mov_rilsa y reconstruye artefactos derivados.
        """
        playback_file = self.base_path / dataset_id / "playback_events.json"
        if not playback_file.exists():
            return

        with open(playback_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        events = data.get("events", [])
        normalized_events, _ = self._normalize_events(dataset_id, events)
        data["events"] = normalized_events
        self._save_playback_data(dataset_id, data)

    # ------------------------
    # Helpers privados
    # ------------------------

    def _load_rilsa_map(self, dataset_id: str) -> Optional[Dict]:
        if dataset_id in self._rilsa_cache:
            return self._rilsa_cache[dataset_id]

        rilsa_file = self.base_path / dataset_id / "rilsa_map.json"
        if not rilsa_file.exists():
            self._rilsa_cache[dataset_id] = None
            return None

        try:
            rilsa_map = json.loads(rilsa_file.read_text())
        except Exception:
            rilsa_map = None

        self._rilsa_cache[dataset_id] = rilsa_map
        return rilsa_map

    def invalidate_rilsa_cache(self, dataset_id: str) -> None:
        self._rilsa_cache.pop(dataset_id, None)

    def _format_rilsa_label(self, code: int) -> str:
        if code in [1, 2, 3, 4, 5, 6, 7, 8]:
            return f"R{code}"
        if 91 <= code <= 94:
            return f"R9({code - 90})"
        if 101 <= code <= 104:
            return f"R10({code - 100})"
        return f"R{code}"

    def _save_playback_data(self, dataset_id: str, data: Dict) -> None:
        playback_file = self.base_path / dataset_id / "playback_events.json"
        playback_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

        # Copiar a carpeta animation (legacy dashboards)
        animation_file = Path("yolo_carla_pipeline/animation/playback_events.json")
        try:
            animation_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(playback_file, animation_file)
        except Exception:
            pass

        # Reconstruir intervalos agregados
        if self.aggregator:
            self.aggregator.rebuild_from_events(dataset_id, data.get("events", []))

    def _apply_single_rule(self, events: List[Dict], rule: CorrectionRule) -> Dict:
        """Aplica una regla individual"""
        filtered_events = []
        removed = 0

        for event in events:
            should_remove = self._check_rule_condition(event, rule.condition)

            if should_remove and rule.action == "remove":
                removed += 1
                continue

            filtered_events.append(event)

        return {"events": filtered_events, "removed": removed}

    def _check_rule_condition(self, event: Dict, condition) -> bool:
        """Verifica si un evento cumple con una condición"""
        # Origin cardinal
        if condition.origin_cardinal and event.get("origin_cardinal") != condition.origin_cardinal:
            return False

        # Destination cardinal
        if condition.destination_cardinal and event.get("destination_cardinal") != condition.destination_cardinal:
            return False

        # Class in list
        if condition.class_in and event.get("class") not in condition.class_in:
            return False

        # Class not in list
        if condition.class_not_in and event.get("class") in condition.class_not_in:
            return True  # Matched condition to remove

        # Trajectory length
        if condition.trajectory_length is not None:
            traj_len = len(event.get("trajectory", []))
            if traj_len != condition.trajectory_length:
                return False

        if condition.trajectory_length_lt is not None:
            traj_len = len(event.get("trajectory", []))
            if traj_len >= condition.trajectory_length_lt:
                return False

        if condition.trajectory_length_gt is not None:
            traj_len = len(event.get("trajectory", []))
            if traj_len <= condition.trajectory_length_gt:
                return False

        # Mov RILSA
        if condition.mov_rilsa and event.get("mov_rilsa") != condition.mov_rilsa:
            return False

        return True

    def _create_snapshot(self, dataset_id: str, action: str, changes: Dict):
        """Crea un snapshot del historial"""
        history_dir = self.base_path / dataset_id / "history"
        history_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = history_dir / f"{timestamp}.json"

        entry = HistoryEntry(
            timestamp=datetime.now(),
            action=action,
            changes=changes
        )

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(entry.model_dump(), f, ensure_ascii=False, indent=2, default=str)

    def get_history(self, dataset_id: str) -> List[Dict]:
        """Obtiene el historial de cambios"""
        history_dir = self.base_path / dataset_id / "history"

        if not history_dir.exists():
            return []

        history = []
        for history_file in sorted(history_dir.glob("*.json"), reverse=True):
            with open(history_file, 'r', encoding='utf-8') as f:
                entry = json.load(f)
                history.append(entry)

        return history

    def _count_events(self, playback_file: Path) -> int:
        """Cuenta los eventos en un archivo playback"""
        if not playback_file.exists():
            return 0

        try:
            with open(playback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return len(data.get("events", []))
        except:
            return 0
