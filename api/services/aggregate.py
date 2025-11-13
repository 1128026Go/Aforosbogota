"""
Servicio de agregación por intervalos de 15 minutos
Idempotente por track_id
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import defaultdict


class AggregatorService:
    """Agregador de conteos por intervalos de 15 min"""

    def __init__(self, data_dir: Path, repository=None):
        self.data_dir = data_dir
        # Cache en memoria: {dataset_id: {interval_iso: {track_ids_procesados}}}
        self.processed_tracks: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self.repository = repository

    def get_interval_iso(self, t_exit_iso: str) -> str:
        """
        Convierte timestamp de egreso a inicio del bucket de 15 min

        Ejemplo:
            '2025-11-07T14:23:45' -> '2025-11-07T14:15:00'
        """
        dt = datetime.fromisoformat(t_exit_iso.replace("Z", ""))
        minutes = (dt.minute // 15) * 15
        bucket_start = dt.replace(minute=minutes, second=0, microsecond=0)
        return bucket_start.isoformat()

    def add_track(
        self,
        dataset_id: str,
        track_id: str,
        clase: str,
        t_exit_iso: str,
        mov_rilsa: int,
        origin: str,
        dest: str,
    ):
        """
        Agrega trayectoria al bucket de 15 min (idempotente)

        Args:
            dataset_id: ID del dataset
            track_id: ID único de trayectoria
            clase: car, motorcycle, bus, truck_c1, truck_c2, truck_c3, bicycle, person
            t_exit_iso: Timestamp de egreso ISO
            mov_rilsa: Código RILSA 1-10
            origin: Acceso de origen
            dest: Acceso de destino
        """
        # Calcular bucket
        interval_iso = self.get_interval_iso(t_exit_iso)

        # Verificar si ya fue procesado (idempotencia)
        if track_id in self.processed_tracks[dataset_id][interval_iso]:
            return  # Ya contado

        # Marcar como procesado
        self.processed_tracks[dataset_id][interval_iso].add(track_id)

        # Cargar o crear archivo de intervalo
        dataset_dir = self.data_dir / dataset_id
        intervals_dir = dataset_dir / "intervals"
        intervals_dir.mkdir(exist_ok=True)

        interval_file = intervals_dir / f"{interval_iso.replace(':', '-')}.json"

        if interval_file.exists():
            data = json.loads(interval_file.read_text())
        else:
            data = {
                "interval_start": interval_iso,
                "counts": {},  # {mov_rilsa}_{clase}: count
                "tracks": [],
            }

        # Agregar conteo
        key = f"{mov_rilsa}_{clase}"
        data["counts"][key] = data["counts"].get(key, 0) + 1

        # Guardar trayectoria
        data["tracks"].append(
            {
                "track_id": track_id,
                "clase": clase,
                "mov_rilsa": mov_rilsa,
                "origin": origin,
                "dest": dest,
                "t_exit": t_exit_iso,
            }
        )

        # Guardar archivo
        interval_file.write_text(json.dumps(data, indent=2))

    def reset_dataset(self, dataset_id: str) -> None:
        """
        Elimina todos los intervalos agregados para un dataset y limpia cache.
        """
        if dataset_id in self.processed_tracks:
            del self.processed_tracks[dataset_id]

        dataset_dir = self.data_dir / dataset_id
        intervals_dir = dataset_dir / "intervals"
        if not intervals_dir.exists():
            return

        for interval_file in intervals_dir.glob("*.json"):
            interval_file.unlink(missing_ok=True)

    def rebuild_from_events(self, dataset_id: str, events: List[Dict]) -> None:
        """
        Reconstruye completamente los intervalos a partir de los eventos provistos.

        Args:
            dataset_id: ID del dataset
            events: Lista de eventos (playback_events.json)
        """
        if events is None:
            events = []

        self.reset_dataset(dataset_id)

        counts_for_db = defaultdict(lambda: defaultdict(int))
        for event in events:
            track_id = event.get("track_id")
            clase = event.get("class") or event.get("cls")
            mov = event.get("mov_rilsa")
            t_exit = (
                event.get("timestamp_exit")
                or event.get("t_exit")
                or event.get("t_exit_iso")
            )
            origin = event.get("origin_access") or event.get("origin_cardinal")
            dest = (
                event.get("dest_access")
                or event.get("destination_cardinal")
                or event.get("dest_cardinal")
            )

            if not track_id or not clase or mov is None or not t_exit or not origin or not dest:
                continue

            try:
                mov_int = int(mov)
            except (TypeError, ValueError):
                continue

            self.add_track(
                dataset_id=dataset_id,
                track_id=str(track_id),
                clase=str(clase),
                t_exit_iso=str(t_exit),
                mov_rilsa=mov_int,
                origin=str(origin),
                dest=str(dest),
            )

            interval_iso = self.get_interval_iso(str(t_exit))
            counts_for_db[(mov_int, interval_iso)][clase] += 1

        if self.repository and counts_for_db:
            records = []
            for (movement_code, interval_iso), by_class in counts_for_db.items():
                interval_start = datetime.fromisoformat(interval_iso.replace("Z", ""))
                interval_end = interval_start + timedelta(minutes=15)
                totals = {
                    "counts_by_class": dict(by_class),
                    "total": int(sum(by_class.values())),
                    "interval": interval_iso,
                }
                records.append((movement_code, interval_start, interval_end, totals))
            self.repository.replace_movement_counts(dataset_id, records)

    def get_intervals(self, dataset_id: str) -> List[str]:
        """Obtener lista de intervalos disponibles"""
        dataset_dir = self.data_dir / dataset_id
        intervals_dir = dataset_dir / "intervals"

        if not intervals_dir.exists():
            return []

        intervals = []
        for file in intervals_dir.glob("*.json"):
            # Convertir filename de vuelta a ISO
            interval_iso = file.stem.replace("-", ":")
            intervals.append(interval_iso)

        return sorted(intervals, reverse=True)

    def get_interval_data(self, dataset_id: str, interval_iso: str) -> Optional[Dict]:
        """Obtener datos de un intervalo específico"""
        dataset_dir = self.data_dir / dataset_id
        interval_file = (
            dataset_dir / "intervals" / f"{interval_iso.replace(':', '-')}.json"
        )

        if not interval_file.exists():
            return None

        return json.loads(interval_file.read_text())

    def load_processed_tracks(self, dataset_id: str):
        """
        Cargar track_ids procesados desde archivos
        (útil al reiniciar servidor)
        """
        dataset_dir = self.data_dir / dataset_id
        intervals_dir = dataset_dir / "intervals"

        if not intervals_dir.exists():
            return

        for interval_file in intervals_dir.glob("*.json"):
            data = json.loads(interval_file.read_text())
            interval_iso = data["interval_start"]

            # Recuperar track_ids
            for track in data.get("tracks", []):
                self.processed_tracks[dataset_id][interval_iso].add(track["track_id"])
