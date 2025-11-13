"""
Capa de acceso a datos para el módulo de aforos.
Nota: Algunas advertencias de Pylance se ignoran porque SQLAlchemy usa 
metaprogramación que confunde el type checker.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db import SessionLocal, session_scope
from models.db_models import (
    AforoCardinalAccess,
    AforoDataset,
    AforoDatasetHistory,
    AforoMovementCount,
    AforoRilsaRule,
    AforoTrajectoryEvent,
    AforoTrajectoryEventRevision,
)


@dataclass
class PlaybackMetadata:
    dataset_id: str
    total_tracks: int
    total_events: int
    fps: Optional[float] = None
    total_frames: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None


def _now() -> datetime:
    return datetime.utcnow()


class AforoRepository:
    """Capa de acceso a datos Postgres para recursos de aforo."""

    def __init__(self, session_factory: SessionLocal = SessionLocal):
        self._session_factory = session_factory

    # --------------------------------------------------------------------- #
    # Dataset helpers
    # --------------------------------------------------------------------- #
    def list_datasets(self) -> List[Dict[str, Any]]:
        with session_scope() as session:
            datasets = session.execute(
                select(AforoDataset).order_by(AforoDataset.updated_at.desc())
            ).scalars()
            results: List[Dict[str, Any]] = []
            for ds in datasets:
                metadata = ds.metadata_json or {}
                results.append(
                    {
                        "id": ds.id,
                        "dataset_key": ds.dataset_key,
                        "name": ds.name or metadata.get("name"),
                        "created_at": ds.created_at.isoformat() if ds.created_at else None,
                        "updated_at": ds.updated_at.isoformat() if ds.updated_at else None,
                        "frames": ds.frames,
                        "tracks": ds.tracks,
                        "metadata": metadata,
                    }
                )
            return results

    def ensure_dataset(
        self,
        dataset_key: str,
        name: Optional[str] = None,
        frames: Optional[int] = None,
        tracks: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AforoDataset:
        # Devuelve un diccionario en lugar de la instancia para evitar uso fuera de sesión
        with session_scope() as session:
            orm_dataset = (
                session.execute(
                    select(AforoDataset).where(AforoDataset.dataset_key == dataset_key)
                )
                .scalars()
                .first()
            )
            if orm_dataset is None:
                orm_dataset = AforoDataset(dataset_key=dataset_key)
                session.add(orm_dataset)
                session.flush()

            orm_dataset.name = name or orm_dataset.name or dataset_key
            orm_dataset.frames = frames
            orm_dataset.tracks = tracks
            if metadata:
                orm_dataset.metadata_json = metadata
            orm_dataset.updated_at = _now()
            session.flush()

            return orm_dataset  # Mantener retorno para llamadas existentes, pero evitar acceder fuera de sesión

    def get_dataset(self, dataset_key: str) -> Optional[AforoDataset]:
        with session_scope() as session:
            return (
                session.execute(
                    select(AforoDataset).where(AforoDataset.dataset_key == dataset_key)
                )
                .scalars()
                .first()
            )

    def get_dataset_id(self, dataset_key: str) -> Optional[int]:
        """Helper para obtener solo el ID del dataset sin desacoplarlo de la sesión."""
        with session_scope() as session:
            result = session.execute(
                select(AforoDataset.id).where(AforoDataset.dataset_key == dataset_key)
            ).scalar()
            return result

    def delete_dataset(self, dataset_key: str) -> bool:
        with session_scope() as session:
            dataset = (
                session.execute(
                    select(AforoDataset).where(AforoDataset.dataset_key == dataset_key)
                )
                .scalars()
                .first()
            )
            if dataset is None:
                return False
            session.delete(dataset)
            session.flush()
            return True

    def get_dataset_config_data(self, dataset_key: str) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            dataset = (
                session.execute(
                    select(AforoDataset).where(AforoDataset.dataset_key == dataset_key)
                )
                .scalars()
                .first()
            )
            if dataset is None:
                return None
            metadata = dataset.metadata_json or {}
            return metadata.get("dataset_config")

    def save_dataset_config(self, dataset_key: str, config: Dict[str, Any]) -> None:
        dataset = self.ensure_dataset(dataset_key)
        with session_scope() as session:
            db_dataset = session.execute(
                select(AforoDataset).where(AforoDataset.dataset_key == dataset_key)
            ).scalars().first()
            if db_dataset is None:
                raise ValueError(f"Dataset {dataset_key} no encontrado")
            metadata = db_dataset.metadata_json or {}
            metadata["dataset_config"] = config
            if config.get("pkl_file"):
                metadata["pkl_file"] = config.get("pkl_file")
            db_dataset.metadata_json = metadata
            db_dataset.updated_at = _now()
            session.flush()

    def count_events(self, dataset_key: str) -> int:
        dataset_id = self.get_dataset_id(dataset_key)
        if dataset_id is None:
            return 0
        
        with session_scope() as session:
            total = session.execute(
                select(func.count())
                .select_from(AforoTrajectoryEvent)
                .where(
                    AforoTrajectoryEvent.dataset_id == dataset_id,
                    AforoTrajectoryEvent.discarded.is_(False),
                )
            ).scalar_one()
            return total

    # --------------------------------------------------------------------- #
    # Cardinales & RILSA
    # --------------------------------------------------------------------- #
    def replace_cardinal_accesses(
        self, dataset_key: str, accesses: Sequence[Dict[str, Any]]
    ) -> None:
        # Get dataset_id WITHIN session scope to avoid DetachedInstanceError
        with session_scope() as session:
            dataset = session.query(AforoDataset).filter_by(dataset_key=dataset_key).first()
            if not dataset:
                raise ValueError(f"Dataset '{dataset_key}' not found")
            dataset_id = dataset.id  # Get id while in session
            
            # Delete existing accesses
            session.query(AforoCardinalAccess).filter_by(dataset_id=dataset_id).delete(
                synchronize_session=False
            )
            
            # Add new accesses
            for access in accesses:
                session.add(
                    AforoCardinalAccess(
                        dataset_id=dataset_id,
                        access_id=str(
                            access.get("id")
                            or access.get("access_id")
                            or access.get("display_name")
                        ),
                        display_name=access.get("display_name"),
                        cardinal=access.get("cardinal") or access.get("cardinal_official"),
                        cardinal_official=access.get("cardinal_official")
                        or access.get("cardinal"),
                        x=access.get("x"),
                        y=access.get("y"),
                        gate=access.get("gate"),
                        polygon=access.get("polygon"),
                    )
                )

    def get_cardinal_accesses(self, dataset_key: str) -> List[Dict[str, Any]]:
        dataset_id = self.get_dataset_id(dataset_key)
        if dataset_id is None:
            return []
        with session_scope() as session:
            accesses = (
                session.execute(
                    select(AforoCardinalAccess).where(
                        AforoCardinalAccess.dataset_id == dataset_id
                    )
                )
                .scalars()
                .all()
            )
            return [
                {
                    "id": access.access_id,
                    "access_id": access.access_id,
                    "display_name": access.display_name,
                    "cardinal": access.cardinal,
                    "cardinal_official": access.cardinal_official,
                    "x": float(access.x) if access.x is not None else None,
                    "y": float(access.y) if access.y is not None else None,
                    "gate": access.gate,
                    "polygon": access.polygon,
                    "created_at": access.created_at.isoformat()
                    if access.created_at
                    else None,
                    "updated_at": access.updated_at.isoformat()
                    if access.updated_at
                    else None,
                }
                for access in accesses
            ]

    def replace_rilsa_rules(
        self,
        dataset_key: str,
        rules: Dict[str, int],
        metadata: Optional[Dict[str, Any]] = None,
        full_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        # Get dataset_id WITHIN session scope to avoid DetachedInstanceError
        with session_scope() as session:
            dataset = session.query(AforoDataset).filter_by(dataset_key=dataset_key).first()
            if not dataset:
                raise ValueError(f"Dataset '{dataset_key}' not found")
            dataset_id = dataset.id  # Get id while in session
            
            # Delete existing rules
            session.query(AforoRilsaRule).filter_by(dataset_id=dataset_id).delete(
                synchronize_session=False
            )
            
            # Add new rules
            for key, value in rules.items():
                try:
                    origin_access, dest_access = key.split("->", 1)
                except ValueError:
                    continue
                session.add(
                    AforoRilsaRule(
                        dataset_id=dataset_id,
                        origin_access=origin_access.strip(),
                        dest_access=dest_access.strip(),
                        rilsa_code=int(value),
                        metadata_json=metadata,
                    )
                )
            
            # Update metadata if provided
            if full_config is not None:
                dataset.metadata_json = (dataset.metadata_json or {}) | {
                    "rilsa_map_config": full_config
                }
                dataset.updated_at = _now()

    def get_rilsa_rules(self, dataset_key: str) -> Dict[str, int]:
        dataset_id = self.get_dataset_id(dataset_key)
        if dataset_id is None:
            return {}
        with session_scope() as session:
            rules = (
                session.execute(
                    select(AforoRilsaRule).where(
                        AforoRilsaRule.dataset_id == dataset_id
                    )
                )
                .scalars()
                .all()
            )
            return {
                f"{rule.origin_access}->{rule.dest_access}": rule.rilsa_code
                for rule in rules
            }

    def get_rilsa_map_config(self, dataset_key: str) -> Dict[str, Any]:
        with session_scope() as session:
            dataset = session.execute(
                select(AforoDataset).where(AforoDataset.dataset_key == dataset_key)
            ).scalars().first()
            if dataset is None:
                return {}
            base_config = (dataset.metadata_json or {}).get("rilsa_map_config", {})
        
        rules = self.get_rilsa_rules(dataset_key)
        if not base_config:
            return {"rules": rules}
        return base_config | {"reglas": rules}

    # --------------------------------------------------------------------- #
    # Eventos y playback
    # --------------------------------------------------------------------- #
    def replace_events(
        self,
        dataset_key: str,
        events: Sequence[Dict[str, Any]],
        metadata: Optional[PlaybackMetadata] = None,
        reset_revisions: bool = True,
    ) -> None:
        with session_scope() as session:
            # Asegurar dataset dentro de ESTA sesión y obtener su id
            dataset = (
                session.execute(
                    select(AforoDataset).where(AforoDataset.dataset_key == dataset_key)
                )
                .scalars()
                .first()
            )
            if dataset is None:
                dataset = AforoDataset(dataset_key=dataset_key)
                session.add(dataset)
                session.flush()
            dataset_id = dataset.id

            if reset_revisions:
                subquery = (
                    select(AforoTrajectoryEvent.id)
                    .where(AforoTrajectoryEvent.dataset_id == dataset_id)
                    .subquery()
                )
                session.query(AforoTrajectoryEventRevision).filter(
                    AforoTrajectoryEventRevision.event_id.in_(select(subquery))
                ).delete(synchronize_session=False)

            session.query(AforoTrajectoryEvent).filter_by(dataset_id=dataset_id).delete(
                synchronize_session=False
            )

            orm_events: List[AforoTrajectoryEvent] = []
            for payload in events:
                orm_events.append(
                    AforoTrajectoryEvent(
                        dataset_id=dataset_id,
                        track_id=str(payload.get("track_id")),
                        class_name=payload.get("class"),
                        origin_access=payload.get("origin_access"),
                        dest_access=payload.get("dest_access")
                        or payload.get("destination_cardinal"),
                        origin_cardinal=payload.get("origin_cardinal"),
                        destination_cardinal=payload.get("destination_cardinal")
                        or payload.get("dest_cardinal"),
                        mov_rilsa=payload.get("mov_rilsa"),
                        frame_entry=payload.get("frame_entry"),
                        frame_exit=payload.get("frame_exit"),
                        timestamp_entry=_parse_datetime(payload.get("timestamp_entry")),
                        timestamp_exit=_parse_datetime(payload.get("timestamp_exit")),
                        confidence=payload.get("confidence"),
                        hide_in_pdf=bool(payload.get("hide_in_pdf", False)),
                        discarded=bool(payload.get("discarded", False)),
                        positions=payload.get("positions"),
                        extra=payload.get("extra"),
                    )
                )

            session.bulk_save_objects(orm_events)

            if metadata:
                dataset.metadata_json = (dataset.metadata_json or {}) | {
                    "playback_metadata": {
                        "total_tracks": metadata.total_tracks,
                        "total_events": metadata.total_events,
                        "fps": metadata.fps,
                        "total_frames": metadata.total_frames,
                        "extra": metadata.extra or {},
                    }
                }
                dataset.updated_at = _now()

    def get_events(self, dataset_key: str) -> Dict[str, Any]:
        dataset_id = self.get_dataset_id(dataset_key)
        if dataset_id is None:
            return {"events": [], "metadata": {"dataset_id": dataset_key, "total_events": 0}}

        with session_scope() as session:
            events = (
                session.execute(
                    select(AforoTrajectoryEvent).where(
                        AforoTrajectoryEvent.dataset_id == dataset_id
                    )
                )
                .scalars()
                .all()
            )

            # Obtener metadata_json de forma segura dentro de sesión
            metadata_json = session.execute(
                select(AforoDataset.metadata_json).where(AforoDataset.id == dataset_id)
            ).scalar() or {}
            playback_metadata = metadata_json.get("playback_metadata", {})

            serialized_events = [
                {
                    "track_id": event.track_id,
                    "class": event.class_name,
                    "origin_access": event.origin_access,
                    "dest_access": event.dest_access,
                    "origin_cardinal": event.origin_cardinal,
                    "destination_cardinal": event.destination_cardinal,
                    "mov_rilsa": event.mov_rilsa,
                    "frame_entry": event.frame_entry,
                    "frame_exit": event.frame_exit,
                    "timestamp_entry": event.timestamp_entry.isoformat()
                    if event.timestamp_entry
                    else None,
                    "timestamp_exit": event.timestamp_exit.isoformat()
                    if event.timestamp_exit
                    else None,
                    "confidence": float(event.confidence)
                    if event.confidence is not None
                    else None,
                    "hide_in_pdf": event.hide_in_pdf,
                    "discarded": event.discarded,
                    "positions": event.positions,
                    "extra": event.extra,
                }
                for event in events
                if not event.discarded
            ]

            metadata = PlaybackMetadata(
                dataset_id=dataset_key,
                total_events=len(serialized_events),
                total_tracks=playback_metadata.get("total_tracks", len(events)),
                fps=playback_metadata.get("fps"),
                total_frames=playback_metadata.get("total_frames"),
                extra=playback_metadata.get("extra"),
            )

            return {
                "events": serialized_events,
                "metadata": {
                    "dataset_id": metadata.dataset_id,
                    "total_events": metadata.total_events,
                    "total_tracks": metadata.total_tracks,
                    "fps": metadata.fps,
                    "total_frames": metadata.total_frames,
                    "extra": metadata.extra or {},
                },
            }

    def list_events_paginated(
        self,
        dataset_key: str,
        skip: int = 0,
        limit: Optional[int] = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        dataset = self.get_dataset(dataset_key)
        if dataset is None:
            return [], 0

        filters = filters or {}
        with session_scope() as session:
            conditions = [AforoTrajectoryEvent.dataset_id == dataset.id]
            if filters.get("class"):
                conditions.append(AforoTrajectoryEvent.class_name == filters["class"])
            if filters.get("origin_cardinal"):
                conditions.append(AforoTrajectoryEvent.origin_cardinal == filters["origin_cardinal"])
            if filters.get("destination_cardinal"):
                conditions.append(AforoTrajectoryEvent.destination_cardinal == filters["destination_cardinal"])
            if filters.get("mov_rilsa") is not None:
                conditions.append(AforoTrajectoryEvent.mov_rilsa == filters["mov_rilsa"])
            if filters.get("track_id"):
                conditions.append(AforoTrajectoryEvent.track_id.contains(str(filters["track_id"])))
            if not filters.get("include_discarded"):
                conditions.append(AforoTrajectoryEvent.discarded.is_(False))

            total = session.execute(
                select(func.count())
                .select_from(AforoTrajectoryEvent)
                .where(*conditions)
            ).scalar_one()

            query = select(AforoTrajectoryEvent).where(*conditions).order_by(AforoTrajectoryEvent.frame_entry)
            if limit is not None:
                query = query.offset(skip).limit(limit)
            events = session.execute(query).scalars().all()

            serialized = []
            for event in events:
                serialized.append(
                    {
                        "track_id": event.track_id,
                        "class": event.class_name,
                        "origin_cardinal": event.origin_cardinal,
                        "destination_cardinal": event.destination_cardinal,
                        "mov_rilsa": event.mov_rilsa,
                        "frame_entry": event.frame_entry,
                        "frame_exit": event.frame_exit,
                        "timestamp_entry": event.timestamp_entry.isoformat()
                        if event.timestamp_entry
                        else None,
                        "timestamp_exit": event.timestamp_exit.isoformat()
                        if event.timestamp_exit
                        else None,
                        "positions": event.positions,
                        "confidence": float(event.confidence) if event.confidence is not None else None,
                        "hide_in_pdf": event.hide_in_pdf,
                        "discarded": event.discarded,
                    }
                )

            return serialized, total

    def get_event_by_track(self, dataset_key: str, track_id: str) -> Optional[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_key)
        if dataset is None:
            return None
        with session_scope() as session:
            event = session.execute(
                select(AforoTrajectoryEvent).where(
                    AforoTrajectoryEvent.dataset_id == dataset.id,
                    AforoTrajectoryEvent.track_id == str(track_id),
                )
            ).scalars().first()

            if event is None:
                return None

            return {
                "track_id": event.track_id,
                "class": event.class_name,
                "origin_cardinal": event.origin_cardinal,
                "destination_cardinal": event.destination_cardinal,
                "mov_rilsa": event.mov_rilsa,
                "frame_entry": event.frame_entry,
                "frame_exit": event.frame_exit,
                "timestamp_entry": event.timestamp_entry.isoformat() if event.timestamp_entry else None,
                "timestamp_exit": event.timestamp_exit.isoformat() if event.timestamp_exit else None,
                "positions": event.positions,
                "confidence": float(event.confidence) if event.confidence is not None else None,
                "hide_in_pdf": event.hide_in_pdf,
                "discarded": event.discarded,
            }

    def update_event_fields(
        self,
        dataset_key: str,
        track_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        dataset = self.get_dataset(dataset_key)
        if dataset is None:
            return False
        with session_scope() as session:
            event = session.execute(
                select(AforoTrajectoryEvent).where(
                    AforoTrajectoryEvent.dataset_id == dataset.id,
                    AforoTrajectoryEvent.track_id == str(track_id),
                )
            ).scalars().first()

            if event is None:
                return False

            attr_map = {
                "class": "class_name",
                "class_name": "class_name",
                "origin_cardinal": "origin_cardinal",
                "destination_cardinal": "destination_cardinal",
                "mov_rilsa": "mov_rilsa",
                "trajectory": "positions",
                "positions": "positions",
                "hide_in_pdf": "hide_in_pdf",
                "discarded": "discarded",
            }

            for key, value in updates.items():
                attr = attr_map.get(key, key)
                if not hasattr(event, attr):
                    continue
                setattr(event, attr, value)

            event.updated_at = _now()
            session.flush()
            return True

    def delete_event(self, dataset_key: str, track_id: str) -> bool:
        dataset = self.get_dataset(dataset_key)
        if dataset is None:
            return False
        with session_scope() as session:
            event = session.execute(
                select(AforoTrajectoryEvent).where(
                    AforoTrajectoryEvent.dataset_id == dataset.id,
                    AforoTrajectoryEvent.track_id == str(track_id),
                )
            ).scalars().first()

            if event is None:
                return False

            session.query(AforoTrajectoryEventRevision).filter(
                AforoTrajectoryEventRevision.event_id == event.id
            ).delete(synchronize_session=False)
            session.delete(event)
            session.flush()
            return True

    def get_event_stats(self, dataset_key: str) -> Dict[str, Dict[str, int]]:
        dataset = self.get_dataset(dataset_key)
        if dataset is None:
            return {"by_class": {}, "by_origin": {}, "by_rilsa": {}}
        with session_scope() as session:
            class_counts = session.execute(
                select(AforoTrajectoryEvent.class_name, func.count())
                .where(
                    AforoTrajectoryEvent.dataset_id == dataset.id,
                    AforoTrajectoryEvent.discarded.is_(False),
                )
                .group_by(AforoTrajectoryEvent.class_name)
            ).all()

            origin_counts = session.execute(
                select(AforoTrajectoryEvent.origin_cardinal, func.count())
                .where(
                    AforoTrajectoryEvent.dataset_id == dataset.id,
                    AforoTrajectoryEvent.discarded.is_(False),
                )
                .group_by(AforoTrajectoryEvent.origin_cardinal)
            ).all()

            rilsa_counts = session.execute(
                select(AforoTrajectoryEvent.mov_rilsa, func.count())
                .where(
                    AforoTrajectoryEvent.dataset_id == dataset.id,
                    AforoTrajectoryEvent.discarded.is_(False),
                )
                .group_by(AforoTrajectoryEvent.mov_rilsa)
            ).all()

            return {
                "by_class": {key or "unknown": value for key, value in class_counts},
                "by_origin": {key or "unknown": value for key, value in origin_counts},
                "by_rilsa": {str(key) if key is not None else "unknown": value for key, value in rilsa_counts},
            }

    # --------------------------------------------------------------------- #
    # Correcciones & historial
    # --------------------------------------------------------------------- #
    def record_history(self, dataset_key: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        with session_scope() as session:
            # Asegurar que el dataset exista dentro de esta sesión
            dataset = (
                session.execute(
                    select(AforoDataset).where(AforoDataset.dataset_key == dataset_key)
                )
                .scalars()
                .first()
            )
            if dataset is None:
                dataset = AforoDataset(dataset_key=dataset_key)
                session.add(dataset)
                session.flush()

            session.add(
                AforoDatasetHistory(
                    dataset_id=dataset.id,
                    action=action,
                    details=details or {},
                    created_at=_now(),
                )
            )

    def get_history(self, dataset_key: str) -> List[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_key)
        if dataset is None:
            return []
        with session_scope() as session:
            history = (
                session.execute(
                    select(AforoDatasetHistory)
                    .where(AforoDatasetHistory.dataset_id == dataset.id)
                    .order_by(AforoDatasetHistory.created_at.desc())
                )
                .scalars()
                .all()
            )
            return [
                {
                    "action": entry.action,
                    "details": entry.details,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                }
                for entry in history
            ]

    def apply_correction(
        self,
        dataset_key: str,
        track_id: str,
        changes: Dict[str, Any],
        changed_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        dataset = self.ensure_dataset(dataset_key)
        with session_scope() as session:
            event = (
                session.execute(
                    select(AforoTrajectoryEvent).where(
                        AforoTrajectoryEvent.dataset_id == dataset.id,
                        AforoTrajectoryEvent.track_id == str(track_id),
                    )
                )
                .scalars()
                .first()
            )
            if event is None:
                raise ValueError("Evento no encontrado")

            updated_fields: Dict[str, Any] = {}
            if "new_origin" in changes and changes["new_origin"]:
                event.origin_cardinal = changes["new_origin"]
                updated_fields["origin_cardinal"] = changes["new_origin"]
            if "new_dest" in changes and changes["new_dest"]:
                event.destination_cardinal = changes["new_dest"]
                updated_fields["destination_cardinal"] = changes["new_dest"]
            if "new_class" in changes and changes["new_class"]:
                event.class_name = changes["new_class"]
                updated_fields["class"] = changes["new_class"]
            if "discard" in changes:
                event.discarded = bool(changes["discard"])
                updated_fields["discarded"] = bool(changes["discard"])
            if "hide_in_pdf" in changes:
                event.hide_in_pdf = bool(changes["hide_in_pdf"])
                updated_fields["hide_in_pdf"] = bool(changes["hide_in_pdf"])

            # Recalcular mov_rilsa si cardinales cambiaron y hay reglas disponibles
            if {"origin_cardinal", "destination_cardinal"} & updated_fields.keys():
                rules = self.get_rilsa_rules(dataset_key)
                key = f"{event.origin_cardinal}->{event.destination_cardinal}"
                if key in rules:
                    event.mov_rilsa = rules[key]
                    updated_fields["mov_rilsa"] = rules[key]

            next_version = (
                session.execute(
                    select(func.coalesce(func.max(AforoTrajectoryEventRevision.version), 0)).where(
                        AforoTrajectoryEventRevision.event_id == event.id
                    )
                ).scalar_one()
                + 1
            )

            revision_payload = {
                "changes": changes,
                "applied_fields": updated_fields,
            }

            session.add(
                AforoTrajectoryEventRevision(
                    event_id=event.id,
                    version=next_version,
                    changes=revision_payload,
                    changed_by=changed_by,
                    created_at=_now(),
                )
            )

            session.flush()
            return {
                "track_id": track_id,
                "version": next_version,
                "applied_fields": updated_fields,
            }

    def get_corrections(self, dataset_key: str) -> Dict[str, Dict[str, Any]]:
        dataset = self.get_dataset(dataset_key)
        if dataset is None:
            return {}

        with session_scope() as session:
            rows = session.execute(
                select(
                    AforoTrajectoryEvent.track_id,
                    AforoTrajectoryEventRevision.version,
                    AforoTrajectoryEventRevision.changes,
                    AforoTrajectoryEventRevision.created_at,
                    AforoTrajectoryEventRevision.changed_by,
                )
                .join(
                    AforoTrajectoryEvent,
                    AforoTrajectoryEventRevision.event_id == AforoTrajectoryEvent.id,
                )
                .where(AforoTrajectoryEvent.dataset_id == dataset.id)
                .order_by(
                    AforoTrajectoryEvent.track_id,
                    AforoTrajectoryEventRevision.version,
                )
            )

            revisions_by_track: Dict[str, Dict[str, Any]] = {}
            for track_id, version, changes, created_at, changed_by in rows:
                revisions_by_track[track_id] = {
                    "version": version,
                    "changes": changes,
                    "timestamp": created_at.isoformat() if created_at else None,
                    "changed_by": changed_by,
                }
            return revisions_by_track

    # --------------------------------------------------------------------- #
    # Movimiento agregado
    # --------------------------------------------------------------------- #
    def replace_movement_counts(
        self,
        dataset_key: str,
        counts: Iterable[Tuple[int, datetime, datetime, Dict[str, Any]]],
    ) -> None:
        with session_scope() as session:
            dataset = (
                session.execute(
                    select(AforoDataset).where(AforoDataset.dataset_key == dataset_key)
                )
                .scalars()
                .first()
            )
            if dataset is None:
                dataset = AforoDataset(dataset_key=dataset_key)
                session.add(dataset)
                session.flush()
            dataset_id = dataset.id

            session.query(AforoMovementCount).filter_by(dataset_id=dataset_id).delete(
                synchronize_session=False
            )
            for movement_code, interval_start, interval_end, totals in counts:
                session.add(
                    AforoMovementCount(
                        dataset_id=dataset_id,
                        movement_code=movement_code,
                        interval_start=interval_start,
                        interval_end=interval_end,
                        totals=totals,
                    )
                )

    def get_movement_counts(self, dataset_key: str) -> List[Dict[str, Any]]:
        dataset_id = self.get_dataset_id(dataset_key)
        if dataset_id is None:
            return []
        with session_scope() as session:
            counts = (
                session.execute(
                    select(AforoMovementCount)
                    .where(AforoMovementCount.dataset_id == dataset_id)
                    .order_by(AforoMovementCount.interval_start)
                )
                .scalars()
                .all()
            )
            return [
                {
                    "movement_code": count.movement_code,
                    "interval_start": count.interval_start.isoformat(),
                    "interval_end": count.interval_end.isoformat(),
                    "totals": count.totals,
                }
                for count in counts
            ]


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None

