"""Script de migración para persistir datos de aforo en PostgreSQL.

El script recorre los datasets disponibles en disco, crea/actualiza sus
registros en la base de datos y migra accesos, reglas, eventos, historial,
correcciones y conteos agregados por intervalo.
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from db import engine, session_scope
from models.db_models import (
    Base,
    AforoCardinalAccess,
    AforoDataset,
    AforoDatasetHistory,
    AforoMovementCount,
    AforoRilsaRule,
    AforoTrajectoryEvent,
    AforoTrajectoryEventRevision,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_DATA_ROOTS: Tuple[Path, ...] = (Path("api/data"), Path("data"))


def load_json(path: Path) -> Dict:
    """Carga un archivo JSON devolviendo un diccionario vacío si hay errores."""
    if not path.exists():
        LOGGER.debug("Archivo no encontrado: %s", path)
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - logging defensivo
        LOGGER.warning("Error leyendo %s: %s", path, exc)
        return {}


def parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def discover_datasets(base_paths: Iterable[Path]) -> Iterator[Path]:
    """Encuentra directorios de datasets (prefijo dataset_) en las rutas dadas."""
    for base in base_paths:
        if not base.exists():
            continue
        for dataset_dir in sorted(base.glob("dataset_*")):
            if dataset_dir.is_dir():
                yield dataset_dir


def normalize_cardinal_accesses(cardinals_payload: Dict) -> List[Dict]:
    accesses = cardinals_payload.get("accesses") or cardinals_payload.get("cardinals") or []
    if isinstance(accesses, dict):
        accesses = list(accesses.values())
    return accesses


def normalize_rules(rilsa_payload: Dict) -> Dict[str, int]:
    rules = rilsa_payload.get("rules")
    return rules if isinstance(rules, dict) else {}


def normalize_events(playback_payload: Dict) -> List[Dict]:
    events = playback_payload.get("events")
    return events if isinstance(events, list) else []


def load_interval_rows(dataset_path: Path) -> Iterator[Tuple[int, datetime, datetime, Dict]]:
    """Genera filas de movimiento/intervalo a partir de los JSON de intervalos."""
    intervals_dir = dataset_path / "intervals"
    if not intervals_dir.exists():
        return

    for interval_file in sorted(intervals_dir.glob("*.json")):
        data = load_json(interval_file)
        interval_start = parse_timestamp(data.get("interval_start"))
        if interval_start is None:
            continue

        duration_min = data.get("interval_minutes") or data.get("duration_minutes") or 15
        interval_end = interval_start + timedelta(minutes=duration_min)

        counts = data.get("counts") or {}
        grouped: Dict[int, Dict[str, int]] = defaultdict(dict)
        for key, value in counts.items():
            if not isinstance(key, str):
                continue
            try:
                movement_code_str, vehicle_class = key.split("_", 1)
                movement_code = int(movement_code_str)
            except (ValueError, TypeError):
                continue
            grouped[movement_code][vehicle_class] = int(value)

        for movement_code, by_class in grouped.items():
            totals_payload = {
                "counts_by_class": by_class,
                "total": sum(by_class.values()),
                "source_interval_file": interval_file.name,
            }
            yield movement_code, interval_start, interval_end, totals_payload


def load_corrections(dataset_path: Path) -> Dict[str, Dict]:
    payload = load_json(dataset_path / "trajectory_corrections.json")
    corrections = payload.get("corrections")
    if isinstance(corrections, dict):
        return corrections
    return {}


def migrate_dataset(dataset_path: Path) -> None:
    dataset_key = dataset_path.name
    LOGGER.info("Migrando dataset %s", dataset_key)

    metadata = load_json(dataset_path / "metadata.json")
    dataset_config = load_json(dataset_path / "dataset_config.json")
    cardinals = load_json(dataset_path / "cardinals.json")
    rilsa_map = load_json(dataset_path / "rilsa_map.json")
    playback = load_json(dataset_path / "playback_events.json")
    corrections = load_corrections(dataset_path)

    history_dir = dataset_path / "history"

    with session_scope() as session:
        dataset = session.query(AforoDataset).filter_by(dataset_key=dataset_key).one_or_none()
        if dataset is None:
            dataset = AforoDataset(dataset_key=dataset_key)
            session.add(dataset)
            session.flush()

        dataset.name = metadata.get("name") or dataset_config.get("name") or dataset_key
        dataset.frames = metadata.get("frames")
        dataset.tracks = metadata.get("tracks")
        dataset.metadata_json = {**dataset_config, **metadata}
        dataset.updated_at = datetime.utcnow()
        dataset_id = dataset.id

        session.query(AforoCardinalAccess).filter_by(dataset_id=dataset_id).delete(synchronize_session=False)
        for access in normalize_cardinal_accesses(cardinals):
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
                    cardinal_official=access.get("cardinal_official") or access.get("cardinal"),
                    x=access.get("x"),
                    y=access.get("y"),
                    gate=access.get("gate"),
                    polygon=access.get("polygon"),
                )
            )

        session.query(AforoRilsaRule).filter_by(dataset_id=dataset_id).delete(synchronize_session=False)
        for key, value in normalize_rules(rilsa_map).items():
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
                )
            )

        session.query(AforoTrajectoryEventRevision).filter(
            AforoTrajectoryEventRevision.event_id.in_(
                session.query(AforoTrajectoryEvent.id).filter_by(dataset_id=dataset_id)
            )
        ).delete(synchronize_session=False)
        session.query(AforoTrajectoryEvent).filter_by(dataset_id=dataset_id).delete(synchronize_session=False)

        events_by_track: Dict[str, AforoTrajectoryEvent] = {}
        for event in normalize_events(playback):
            track_id = str(event.get("track_id"))
            trajectory = AforoTrajectoryEvent(
                dataset_id=dataset_id,
                track_id=track_id,
                class_name=event.get("class"),
                origin_access=event.get("origin_access"),
                dest_access=event.get("dest_access"),
                origin_cardinal=event.get("origin_cardinal"),
                destination_cardinal=event.get("destination_cardinal") or event.get("dest_cardinal"),
                mov_rilsa=event.get("mov_rilsa"),
                frame_entry=event.get("frame_entry"),
                frame_exit=event.get("frame_exit"),
                timestamp_entry=parse_timestamp(event.get("timestamp_entry")),
                timestamp_exit=parse_timestamp(event.get("timestamp_exit")),
                confidence=event.get("confidence"),
                hide_in_pdf=bool(event.get("hide_in_pdf")),
                discarded=bool(event.get("discarded")),
                positions=event.get("positions"),
                extra={
                    k: v
                    for k, v in event.items()
                    if k
                    not in {
                        "track_id",
                        "class",
                        "origin_access",
                        "dest_access",
                        "origin_cardinal",
                        "destination_cardinal",
                        "dest_cardinal",
                        "mov_rilsa",
                        "frame_entry",
                        "frame_exit",
                        "timestamp_entry",
                        "timestamp_exit",
                        "confidence",
                        "hide_in_pdf",
                        "discarded",
                        "positions",
                    }
                },
            )
            session.add(trajectory)
            events_by_track[track_id] = trajectory

        session.flush()  # asegura IDs para revisiones y conteos

        for track_id, payload in corrections.items():
            event = events_by_track.get(track_id)
            if event is None:
                continue
            revision = AforoTrajectoryEventRevision(
                event_id=event.id,
                version=1,
                changes=payload,
                changed_by=payload.get("changed_by") or ("auto" if payload.get("auto_generated") else None),
                created_at=parse_timestamp(payload.get("timestamp")) or datetime.utcnow(),
            )
            session.add(revision)

        session.query(AforoMovementCount).filter_by(dataset_id=dataset_id).delete(synchronize_session=False)
        for movement_code, interval_start, interval_end, totals in load_interval_rows(dataset_path):
            session.add(
                AforoMovementCount(
                    dataset_id=dataset_id,
                    movement_code=movement_code,
                    interval_start=interval_start,
                    interval_end=interval_end,
                    totals=totals,
                )
            )

        session.query(AforoDatasetHistory).filter_by(dataset_id=dataset_id).delete(synchronize_session=False)
        if history_dir.exists():
            for history_file in sorted(history_dir.glob("*.json")):
                entry = load_json(history_file)
                session.add(
                    AforoDatasetHistory(
                        dataset_id=dataset_id,
                        action=entry.get("action", "unknown"),
                        details=entry.get("changes") or entry.get("details"),
                        created_at=parse_timestamp(entry.get("timestamp")) or datetime.utcnow(),
                    )
                )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migrar datasets de aforo a PostgreSQL")
    parser.add_argument(
        "--data-root",
        action="append",
        dest="data_roots",
        help="Ruta que contiene subdirectorios dataset_* (puede usarse varias veces)",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        help="Migrar solo el dataset indicado (nombre de carpeta dataset_XXXX)",
    )
    parser.add_argument("--log-level", default="INFO", help="Nivel de logging (INFO, DEBUG, ...)")
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    LOGGER.info("Inicializando migración a PostgreSQL")

    Base.metadata.create_all(engine)

    roots = tuple(Path(path) for path in args.data_roots) if args.data_roots else DEFAULT_DATA_ROOTS
    dataset_whitelist = set(args.datasets or [])

    for dataset_dir in discover_datasets(roots):
        if dataset_whitelist and dataset_dir.name not in dataset_whitelist:
            continue
        migrate_dataset(dataset_dir)

    LOGGER.info("Migración finalizada")


if __name__ == "__main__":
    main()
