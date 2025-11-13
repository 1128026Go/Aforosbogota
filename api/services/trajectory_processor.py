"""
Servicio de procesamiento de trayectorias
Construye trayectorias desde detecciones y detecta cruces de accesos
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import json
from datetime import datetime, timedelta
from services.polygon_utils import point_in_polygon


def convert_to_json_serializable(obj: Any) -> Any:
    """Convierte objetos numpy y otros tipos a tipos serializables por JSON"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj


class SimpleTracker:
    """Tracker simple para construir trayectorias desde detecciones"""

    def __init__(self, max_distance: float = 50, max_frames_skip: int = 10):
        """
        Args:
            max_distance: Distancia máxima para considerar misma trayectoria
            max_frames_skip: Frames máximos sin detección antes de terminar track
        """
        self.max_distance = max_distance
        self.max_frames_skip = max_frames_skip
        self.active_tracks = {}  # {track_id: Track}
        self.completed_tracks = []
        self.next_track_id = 1

    def process_frame(self, frame_id: int, detections: List[Dict]):
        """
        Procesa un frame con sus detecciones

        Args:
            frame_id: ID del frame
            detections: Lista de detecciones [{x, y, class, confidence}, ...]
        """
        # Agrupar detecciones por clase
        by_class = {}
        for det in detections:
            clase = det['class']
            if clase not in by_class:
                by_class[clase] = []
            by_class[clase].append(det)

        # Procesar cada clase independientemente
        for clase, dets in by_class.items():
            self._match_detections_to_tracks(frame_id, clase, dets)

        # Incrementar edad de tracks sin match y eliminar obsoletos
        self._cleanup_tracks(frame_id)

    def _match_detections_to_tracks(self, frame_id: int, clase: str, detections: List[Dict]):
        """Asocia detecciones con tracks activos de la misma clase"""

        # Filtrar tracks de esta clase
        class_tracks = {
            tid: track for tid, track in self.active_tracks.items()
            if track['class'] == clase
        }

        if not class_tracks:
            # No hay tracks activos, crear nuevos para cada detección
            for det in detections:
                self._create_track(frame_id, det)
            return

        # Matching simple: distancia mínima
        unmatched_detections = list(detections)
        matched_tracks = set()

        for det in detections:
            det_pos = np.array([det['x'], det['y']])

            # Buscar track más cercano
            min_dist = float('inf')
            best_track_id = None

            for tid, track in class_tracks.items():
                if tid in matched_tracks:
                    continue

                last_pos = np.array(track['positions'][-1])
                dist = np.linalg.norm(det_pos - last_pos)

                if dist < min_dist and dist < self.max_distance:
                    min_dist = dist
                    best_track_id = tid

            # Asociar o crear nuevo
            if best_track_id is not None:
                self._update_track(best_track_id, frame_id, det)
                matched_tracks.add(best_track_id)
                unmatched_detections.remove(det)

        # Crear nuevos tracks para detecciones no asociadas
        for det in unmatched_detections:
            self._create_track(frame_id, det)

    def _create_track(self, frame_id: int, detection: Dict):
        """Crea un nuevo track"""
        track_id = f"track_{self.next_track_id}"
        self.next_track_id += 1

        self.active_tracks[track_id] = {
            'track_id': track_id,
            'class': detection['class'],
            'positions': [(detection['x'], detection['y'])],
            'frames': [frame_id],
            'confidences': [detection.get('confidence', 0.5)],
            'last_update': frame_id,
        }

    def _update_track(self, track_id: str, frame_id: int, detection: Dict):
        """Actualiza track existente con nueva detección"""
        track = self.active_tracks[track_id]

        # Agregar detección actual
        track['positions'].append((detection['x'], detection['y']))
        track['frames'].append(frame_id)
        track['confidences'].append(detection.get('confidence', 0.5))
        track['last_update'] = frame_id

    def _interpolate_track_positions(self, track):
        """
        Interpola posiciones para llenar todos los frames entre el primero y el último.

        Args:
            track: Track con frames y positions (puede tener gaps)

        Returns:
            Track con posiciones interpoladas para todos los frames
        """
        frames = track['frames']
        positions = track['positions']
        confidences = track.get('confidences', [])

        if len(frames) <= 1:
            return track  # No hay nada que interpolar

        # DEBUG LOG
        first_frame = frames[0]
        last_frame = frames[-1]
        frame_span = last_frame - first_frame + 1
        track_id_str = str(track['track_id'])
        if len(positions) < frame_span and '2542' in track_id_str:
            print(f"[INTERPOLANDO] Track {track['track_id']}: {len(positions)} posiciones -> {frame_span} frames", flush=True)

        # Crear diccionario de frame -> posición para los frames detectados
        known_frames = {frame: pos for frame, pos in zip(frames, positions)}
        known_confidences = {frame: conf for frame, conf in zip(frames, confidences)} if confidences else {}

        # Generar lista completa de frames (del primero al último sin gaps)
        first_frame = frames[0]
        last_frame = frames[-1]
        all_frames = list(range(first_frame, last_frame + 1))

        # Interpolar posiciones para todos los frames
        interpolated_positions = []
        interpolated_confidences = []

        for frame in all_frames:
            if frame in known_frames:
                # Frame con detección real
                interpolated_positions.append(known_frames[frame])
                interpolated_confidences.append(known_confidences.get(frame, 0.5))
            else:
                # Frame sin detección - interpolar linealmente
                # Encontrar frame anterior y siguiente con detección
                prev_frame = max([f for f in known_frames.keys() if f < frame], default=None)
                next_frame = min([f for f in known_frames.keys() if f > frame], default=None)

                if prev_frame is not None and next_frame is not None:
                    # Interpolar entre prev y next
                    prev_pos = known_frames[prev_frame]
                    next_pos = known_frames[next_frame]

                    # Calcular ratio de interpolación
                    ratio = (frame - prev_frame) / (next_frame - prev_frame)

                    # Interpolar x e y
                    interp_x = prev_pos[0] + (next_pos[0] - prev_pos[0]) * ratio
                    interp_y = prev_pos[1] + (next_pos[1] - prev_pos[1]) * ratio

                    interpolated_positions.append((interp_x, interp_y))
                    interpolated_confidences.append(0.0)  # Marca como interpolado
                elif prev_frame is not None:
                    # Solo hay frame anterior - usar esa posición
                    interpolated_positions.append(known_frames[prev_frame])
                    interpolated_confidences.append(0.0)
                elif next_frame is not None:
                    # Solo hay frame siguiente - usar esa posición
                    interpolated_positions.append(known_frames[next_frame])
                    interpolated_confidences.append(0.0)

        # Actualizar track con posiciones interpoladas
        track['frames'] = all_frames
        track['positions'] = interpolated_positions
        track['confidences'] = interpolated_confidences

        return track

    def _cleanup_tracks(self, current_frame: int):
        """Elimina tracks obsoletos y los marca como completados"""
        to_remove = []

        for tid, track in self.active_tracks.items():
            frames_since_update = current_frame - track['last_update']

            if frames_since_update > self.max_frames_skip:
                # Track terminado
                # RELAJADO: Mínimo 3 detecciones para peatones, 8 para vehículos (más estricto)
                min_detections = 3 if track.get('class') in ['person', 'pedestrian', 'peaton'] else 8
                if len(track['frames']) >= min_detections:
                    # Interpolar posiciones antes de agregar
                    track = self._interpolate_track_positions(track)
                    self.completed_tracks.append(track)
                to_remove.append(tid)

        for tid in to_remove:
            del self.active_tracks[tid]

    def finalize(self):
        """Finaliza el tracking y retorna todos los tracks completos"""
        # Agregar tracks activos restantes
        for track in self.active_tracks.values():
            # RELAJADO: Mínimo 3 detecciones para peatones, 8 para vehículos (más estricto)
            min_detections = 3 if track.get('class') in ['person', 'pedestrian', 'peaton'] else 8
            if len(track['frames']) >= min_detections:
                # Interpolar posiciones antes de agregar
                track = self._interpolate_track_positions(track)
                self.completed_tracks.append(track)

        self.active_tracks.clear()
        return self.completed_tracks


class TrajectoryProcessor:
    """Procesa trayectorias y detecta cruces de accesos"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.corrections = {}  # Diccionario de correcciones manuales

    def process_dataset(self, dataset_id: str) -> Dict:
        """
        Procesa un dataset completo y genera eventos de trayectorias completadas

        Returns:
            {
                'events': [
                    {
                        'track_id': str,
                        'class': str,
                        'frame_entry': int,
                        'frame_exit': int,
                        'timestamp_entry': str (ISO),
                        'timestamp_exit': str (ISO),
                        'origin_access': str,
                        'dest_access': str,
                        'mov_rilsa': int,
                        'positions': [(x,y), ...],
                    },
                    ...
                ],
                'metadata': {...}
            }
        """
        dataset_dir = self.data_dir / dataset_id

        # Cargar configuración
        cardinals = self._load_cardinals(dataset_dir)
        rilsa_map = self._load_rilsa_map(dataset_dir)
        metadata = self._load_metadata(dataset_dir)

        # Cargar correcciones manuales
        self.corrections = self._load_corrections(dataset_dir)

        if not cardinals or not rilsa_map:
            raise ValueError("Dataset no configurado correctamente")

        # Cargar detecciones desde parquet
        parquet_path = dataset_dir / "normalized.parquet"
        if not parquet_path.exists():
            raise ValueError("Parquet no encontrado")

        df = pd.read_parquet(parquet_path)

        # Construir trayectorias
        tracker = SimpleTracker(max_distance=80, max_frames_skip=15)

        print(f"Procesando {len(df)} detecciones...")

        for frame_id in sorted(df['frame_id'].unique()):
            frame_dets = df[df['frame_id'] == frame_id]
            detections = [
                {
                    'x': float(row['x']),
                    'y': float(row['y']),
                    # Consolidar todas las categorías de camión en una sola
                    'class': 'truck' if str(row['class']).startswith('truck_') else str(row['class']),
                    'confidence': float(row.get('confidence', 0.5)),
                }
                for _, row in frame_dets.iterrows()
            ]
            tracker.process_frame(int(frame_id), detections)

        # Finalizar tracking
        completed_tracks = tracker.finalize()
        print(f"Tracks completos: {len(completed_tracks)}")

        # Detectar cruces de accesos
        events, segments_map = self._detect_access_crossings(
            completed_tracks,
            cardinals,
            rilsa_map,
            metadata
        )

        print(f"Eventos detectados: {len(events)}")

        # INTERVENTORÍA: Stats básicos (interventoría completa disponible bajo demanda)
        tracks_with_events = len(segments_map)
        tracks_without_events = len(completed_tracks) - tracks_with_events

        print(f"\n[INTERVENTORÍA] Resumen:")
        print(f"  Tracks con eventos: {tracks_with_events}")
        print(f"  Tracks sin eventos: {tracks_without_events}")

        # Preparar datos de audit simplificados
        audit_summary = {
            'valid_tracks': tracks_with_events,
            'invalid_tracks': 0,  # Se puede calcular después si es necesario
            'validity_rate': 1.0
        }

        result = {
            'events': events,
            'metadata': {
                'dataset_id': dataset_id,
                'total_tracks': len(completed_tracks),
                'total_events': len(events),
                'fps': metadata.get('fps', 30),
                'total_frames': metadata.get('frames', 0),
                'audit': {
                    'valid_tracks': audit_summary['valid_tracks'],
                    'invalid_tracks': audit_summary['invalid_tracks'],
                    'validity_rate': audit_summary['validity_rate']
                }
            }
        }

        # Convertir todos los tipos numpy a tipos JSON serializables
        return convert_to_json_serializable(result)

    def _detect_access_crossings(
        self,
        tracks: List[Dict],
        cardinals: Dict,
        rilsa_map: Dict,
        metadata: Dict
    ) -> Tuple[List[Dict], Dict[str, Dict]]:
        """
        Detecta cuando una trayectoria cruza gates/zonas de acceso
        Usa SOLO cardinales oficiales para asignar código RILSA

        Soporta dos modos:
        1. Zonas poligonales (polygon) - más preciso
        2. Gates lineales (gate) - compatibilidad

        Returns:
            (events, segments_map) - Lista de eventos y mapa de track_id -> segment
        """
        from services.classify import assign_rilsa
        from services.polygon_utils import point_in_polygon

        accesses = cardinals.get('accesses', [])
        fps = metadata.get('fps', 30)

        # FILTROS DIFERENCIADOS: Vehículos con filtros completos, peatones solo por duración mínima
        print(f"\n[FILTROS] Aplicando filtros de calidad...")

        # Separar peatones de vehículos
        peatones = [t for t in tracks if t.get('class') == 'person']
        vehiculos = [t for t in tracks if t.get('class') != 'person']

        print(f"  Peatones (antes): {len(peatones)}")
        print(f"  Vehículos (antes): {len(vehiculos)}")

        # Importar funciones de filtrado
        from services.trajectory_filters import filter_tracks, calculate_duration_seconds

        # 1. Filtrar peatones solo por duración mínima (0.3 segundos - RELAJADO)
        MIN_PEATON_DURATION = 0.3  # segundos (reducido de 0.5 para capturar más peatones)
        filtered_peatones = []
        peatones_rechazados = 0

        for p in peatones:
            duration = calculate_duration_seconds(p.get('frames', []), fps)
            if duration >= MIN_PEATON_DURATION:
                filtered_peatones.append(p)
            else:
                peatones_rechazados += 1

        print(f"  Peatones filtrados: {len(filtered_peatones)} aceptados, {peatones_rechazados} rechazados por duración < {MIN_PEATON_DURATION}s")

        # 2. Aplicar filtros completos a vehículos
        # Parámetros RELAJADOS para permitir que los filtros inteligentes hagan el trabajo:
        # - pixels_per_meter: Calibración para intersección urbana
        # - min_distance: Reducido para permitir giros cortos
        # - min_duration: Reducido para permitir que filtros inteligentes por tipo de movimiento decidan
        filtered_vehiculos, filter_stats = filter_tracks(
            tracks=vehiculos,
            bounds=None,
            fps=fps,
            pixels_per_meter=10.0,  # Ajustado para intersección urbana
            min_distance_meters=5.0,  # RELAJADO: permitir giros cortos
            min_duration_seconds=0.5,  # RELAJADO: los filtros inteligentes harán el trabajo
            verbose=True
        )

        # Combinar: peatones filtrados + vehículos filtrados
        tracks = filtered_peatones + filtered_vehiculos
        print(f"  Total final: {len(tracks)} trayectorias ({len(filtered_peatones)} peatones + {len(filtered_vehiculos)} vehículos)")

        # Importar classify aquí para evitar circular import
        events = []
        segments_map = {}  # Mapa de track_id -> segment para auditoría

        # Contadores de filtros
        filtros_tiempo = {
            'total_segmentos': 0,
            'descartados': 0,
            'aceptados': 0
        }

        for track in tracks:
            positions = track['positions']
            frames = track['frames']
            clase = track.get('class', 'unknown')

            # Filtro de longitud mínima RELAJADO PARA PEATONES
            # Peatones: 3 posiciones mínimo (más permisivo para capturar cruces rápidos)
            # Vehículos: 10 posiciones mínimo (mayor calidad, filtrado más estricto)
            min_positions = 3 if clase in ['person', 'peaton', 'pedestrian'] else 10

            if len(positions) < min_positions:
                continue  # Trayectoria muy corta

            # NUEVA LÓGICA: Segmentar trayectoria en múltiples eventos RILSA
            # Detectar todos los cruces de accesos a lo largo de la trayectoria
            trajectory_segments = self._segment_trajectory(track, accesses)

            if not trajectory_segments:
                # DEBUG: Track without valid segments (silenciar para performance)
                # print(f"[DEBUG] Track {track['track_id']}: No segments detected, skipping")
                continue

            # Guardar primer segmento en el mapa para auditoría
            track_id = track['track_id']
            if trajectory_segments:
                segments_map[track_id] = trajectory_segments[0]

            # Procesar cada segmento como un evento RILSA independiente
            for segment in trajectory_segments:
                filtros_tiempo['total_segmentos'] += 1
                entry_access_id = segment['entry_access_id']
                entry_cardinal = segment['entry_cardinal']
                entry_frame = segment['entry_frame']
                exit_access_id = segment['exit_access_id']
                exit_cardinal = segment['exit_cardinal']
                exit_frame = segment['exit_frame']
                segment_positions = segment['positions']

                # CÓDIGO ORIGINAL MOVIDO AQUÍ - procesar cada segmento
                if entry_access_id and exit_access_id and entry_cardinal and exit_cardinal:
                    # VALIDACIÓN: Asegurar que entry_frame < exit_frame (orden temporal correcto)
                    if entry_frame >= exit_frame:
                        continue

                    # Calcular duración del movimiento
                    duration_seconds = (exit_frame - entry_frame) / fps

                    # Asignar RILSA basado SOLO en cardinales oficiales
                    mov_rilsa = assign_rilsa(entry_cardinal, exit_cardinal, rilsa_map)

                    # FILTROS INTELIGENTES POR TIPO DE MOVIMIENTO Y CLASE
                    # Basados en análisis estadístico de tiempos reales
                    clase = track.get('class', 'unknown')
                    es_peaton = clase in ['person', 'peaton', 'pedestrian']

                    # Aplicar filtros ANTES de continuar con correcciones
                    if mov_rilsa is not None:
                        # Tipo de movimiento
                        es_recto = mov_rilsa in [1, 2, 3, 4]  # Rectos
                        es_izquierda = mov_rilsa in [5, 6, 7, 8]  # Izquierdas
                        es_derecha = mov_rilsa in [91, 92, 93, 94]  # Derechas
                        es_retorno = mov_rilsa in [101, 102, 103, 104]  # Retornos

                        # Filtros por clase y tipo de movimiento
                        descartado = False
                        razon = None

                        if es_peaton:
                            # Peatones: más permisivos (pueden cruzar rápido)
                            if duration_seconds < 0.3:
                                descartado = True
                                razon = "Peatón muy rápido (<0.3s)"
                            elif duration_seconds > 15.0:
                                descartado = True
                                razon = "Peatón estancado (>15s)"
                        else:
                            # Vehículos: filtros más estrictos
                            # ELIMINAR PARQUEADOS/ESTANCADOS
                            if duration_seconds > 30.0:
                                descartado = True
                                razon = "Vehículo parqueado/estancado (>30s)"
                            # ELIMINAR TRAYECTORIAS MUY CORTAS (incompletas)
                            elif duration_seconds < 1.5:
                                descartado = True
                                razon = "Trayectoria muy corta (<1.5s)"
                            # FILTROS ESPECÍFICOS POR TIPO DE MOVIMIENTO
                            elif es_recto:
                                # Rectos: deberían tomar 3-20s
                                if duration_seconds < 2.5:
                                    descartado = True
                                    razon = "Recto demasiado rápido (<2.5s)"
                                elif duration_seconds > 25.0:
                                    descartado = True
                                    razon = "Recto demasiado lento (>25s)"
                            elif es_izquierda or es_derecha:
                                # Giros: deberían tomar 1.5-25s
                                if duration_seconds < 1.5:
                                    descartado = True
                                    razon = "Giro demasiado rápido (<1.5s)"
                                elif duration_seconds > 25.0:
                                    descartado = True
                                    razon = "Giro demasiado lento (>25s)"
                            elif es_retorno:
                                # Retornos: deberían tomar 5-30s (mantener solo los obvios)
                                if duration_seconds < 4.0:
                                    descartado = True
                                    razon = "Retorno demasiado rápido (<4s)"
                                elif duration_seconds > 30.0:
                                    descartado = True
                                    razon = "Retorno demasiado lento (>30s)"

                        if descartado:
                            filtros_tiempo['descartados'] += 1
                            # print(f"[FILTRO TIEMPO] {track['track_id']}: {razon} ({duration_seconds:.1f}s)")
                            continue  # Descartar este evento
                        else:
                            filtros_tiempo['aceptados'] += 1

                    if mov_rilsa is not None:
                        # Aplicar correcciones manuales si existen
                        track_id = track['track_id']
                        if track_id in self.corrections:
                            correction = self.corrections[track_id]

                            # Si está marcada para descartar, skip este evento
                            if correction.get('discard', False):
                                print(f"[CORRECCIÓN] Descartando {track_id}")
                                continue

                            # Aplicar cambios de origen/destino si existen
                            if correction.get('new_origin'):
                                entry_cardinal = correction['new_origin']
                                print(f"[CORRECCIÓN] {track_id}: Origen {entry_cardinal}")

                            if correction.get('new_dest'):
                                exit_cardinal = correction['new_dest']
                                print(f"[CORRECCIÓN] {track_id}: Destino {exit_cardinal}")

                            # Aplicar cambio de clase si existe
                            if correction.get('new_class'):
                                track['class'] = correction['new_class']
                                print(f"[CORRECCIÓN] {track_id}: Clase {track['class']}")

                            # Recalcular movimiento RILSA con los nuevos cardinales
                            mov_rilsa = assign_rilsa(entry_cardinal, exit_cardinal, rilsa_map)

                            if mov_rilsa is None:
                                print(f"[CORRECCIÓN] {track_id}: Movimiento inválido {entry_cardinal}->{exit_cardinal}")
                                continue

                        # INTERPOLAR POSICIONES del segmento para trayectorias suaves
                        interpolated_positions = self._interpolate_segment_positions(
                            segment_positions,
                            entry_frame,
                            exit_frame,
                            track['frames']
                        )

                        # DEBUG: Log interpolación para track 2542
                        if '2542' in str(track['track_id']):
                            print(f"[INTERPOLACIÓN] Track {track['track_id']}: {len(segment_positions)} -> {len(interpolated_positions)} posiciones", flush=True)

                        # Calcular timestamps relativos desde 00:00:00
                        base_time = datetime(2000, 1, 1, 0, 0, 0)
                        timestamp_entry = base_time + timedelta(seconds=entry_frame / fps)
                        timestamp_exit = base_time + timedelta(seconds=exit_frame / fps)

                        events.append({
                            'track_id': f"{track['track_id']}_seg{segment['segment_index']}",  # ID único por segmento
                            'class': track['class'],
                            'frame_entry': int(entry_frame),
                            'frame_exit': int(exit_frame),
                            'timestamp_entry': timestamp_entry.isoformat(),
                            'timestamp_exit': timestamp_exit.isoformat(),
                            'origin_access': entry_access_id,
                            'dest_access': exit_access_id,
                            'origin_cardinal': entry_cardinal,
                            'dest_cardinal': exit_cardinal,
                            'mov_rilsa': int(mov_rilsa),
                            'positions': [(float(x), float(y)) for x, y in interpolated_positions],
                            'confidence': float(np.mean(track['confidences'])),
                        })

        return events, segments_map

    def _interpolate_segment_positions(self, segment_positions, entry_frame, exit_frame, track_frames):
        """
        Interpola posiciones de un segmento para llenar todos los frames entre entry y exit.

        Args:
            segment_positions: Lista de posiciones (x, y) detectadas en el segmento
            entry_frame: Frame de entrada al segmento
            exit_frame: Frame de salida del segmento
            track_frames: Lista de frames donde se detectaron las posiciones originales

        Returns:
            Lista de posiciones interpoladas para cada frame entre entry_frame y exit_frame
        """
        if len(segment_positions) <= 1:
            return segment_positions

        # Determinar qué frames del track corresponden al segmento
        # Los frames del track están en orden, encontrar el rango del segmento
        segment_frame_indices = []
        for i, frame in enumerate(track_frames):
            if entry_frame <= frame <= exit_frame:
                segment_frame_indices.append(i)

        if len(segment_frame_indices) < 2:
            return segment_positions

        # Crear mapeo de frame -> posición para los frames detectados
        known_frames = {}
        for i, idx in enumerate(segment_frame_indices):
            if i < len(segment_positions):
                known_frames[track_frames[idx]] = segment_positions[i]

        if len(known_frames) < 2:
            return segment_positions

        # Generar lista completa de frames del segmento
        all_segment_frames = list(range(entry_frame, exit_frame + 1))

        # Interpolar posiciones para cada frame
        interpolated_positions = []
        for frame in all_segment_frames:
            if frame in known_frames:
                # Frame con detección real
                interpolated_positions.append(known_frames[frame])
            else:
                # Frame sin detección - interpolar linealmente
                # Encontrar frame anterior y siguiente con detección
                prev_frame = max([f for f in known_frames.keys() if f < frame], default=None)
                next_frame = min([f for f in known_frames.keys() if f > frame], default=None)

                if prev_frame is not None and next_frame is not None:
                    # Interpolar entre prev y next
                    prev_pos = known_frames[prev_frame]
                    next_pos = known_frames[next_frame]

                    # Calcular ratio de interpolación
                    ratio = (frame - prev_frame) / (next_frame - prev_frame)

                    # Interpolar x e y
                    interp_x = prev_pos[0] + (next_pos[0] - prev_pos[0]) * ratio
                    interp_y = prev_pos[1] + (next_pos[1] - prev_pos[1]) * ratio

                    interpolated_positions.append((interp_x, interp_y))
                elif prev_frame is not None:
                    # Solo hay frame anterior - usar esa posición
                    interpolated_positions.append(known_frames[prev_frame])
                elif next_frame is not None:
                    # Solo hay frame siguiente - usar esa posición
                    interpolated_positions.append(known_frames[next_frame])

        return interpolated_positions

    def _segment_trajectory(self, track, accesses):
        """
        Detecta el acceso de entrada y salida para una trayectoria.

        REGLA: Una trayectoria = 1 evento (no múltiples segmentos)
        - Primer acceso detectado = ENTRADA
        - Último acceso detectado diferente = SALIDA

        Returns:
            Lista con máximo 1 segmento (entry → exit)
        """
        from services.polygon_utils import point_in_polygon

        positions = track['positions']
        frames = track['frames']

        # Detectar primer y último acceso
        first_access = None
        last_access = None

        for i, pos in enumerate(positions):
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                x, y = float(pos[0]), float(pos[1])
            else:
                continue

            for access in accesses:
                # Verificar si está en zona de acceso
                in_access = False
                polygon = access.get('polygon', [])
                if polygon and len(polygon) >= 3:
                    polygon_tuples = [
                        (p['x'], p['y']) if isinstance(p, dict) else tuple(p) if isinstance(p, list) else p
                        for p in polygon
                    ]
                    in_access = point_in_polygon((x, y), polygon_tuples)

                    # Si no está exactamente en el polígono, verificar proximidad (ampliado 30%)
                    if not in_access:
                        # Calcular centro del polígono
                        center_x = sum(p[0] for p in polygon_tuples) / len(polygon_tuples)
                        center_y = sum(p[1] for p in polygon_tuples) / len(polygon_tuples)

                        # Calcular radio aproximado
                        max_dist = max(
                            ((p[0] - center_x)**2 + (p[1] - center_y)**2)**0.5
                            for p in polygon_tuples
                        )

                        # Verificar si está cerca (radio ampliado 80%)
                        dist_to_center = ((x - center_x)**2 + (y - center_y)**2)**0.5
                        in_access = dist_to_center <= max_dist * 1.8
                else:
                    gate = access.get('gate', {})
                    in_access = self._crosses_gate(x, y, gate)

                if in_access:
                    access_info = {
                        'frame_idx': i,
                        'frame': frames[i],
                        'access_id': access['id'],
                        'cardinal': access.get('cardinal_official', access.get('cardinal')),
                        'position': pos
                    }

                    # Guardar primer acceso
                    if first_access is None:
                        first_access = access_info

                    # Actualizar último acceso solo si es DIFERENTE al primero
                    if access_info['access_id'] != first_access['access_id']:
                        last_access = access_info

                    break  # Solo un acceso por posición

        # NUEVO ENFOQUE: Siempre usar PROXIMIDAD como método principal
        # Si ya detectamos accesos por polígonos, validar que sean los más cercanos
        if len(positions) >= 3:
            start_pos = positions[0] if isinstance(positions[0], (list, tuple)) else None
            end_pos = positions[-1] if isinstance(positions[-1], (list, tuple)) else None

            if start_pos and end_pos:
                # Buscar acceso MÁS CERCANO a las posiciones (método principal)
                entry_access = self._find_nearest_access(start_pos, accesses, preferred_cardinal=None)
                exit_access = self._find_nearest_access(end_pos, accesses, preferred_cardinal=None)

                # Asegurar que son accesos diferentes
                if entry_access and exit_access:
                    # Si son el mismo acceso, buscar el segundo más cercano para la salida
                    if entry_access['id'] == exit_access['id']:
                        exit_access = self._find_second_nearest_access(end_pos, accesses, exclude_id=entry_access['id'])

                    if entry_access and exit_access and entry_access['id'] != exit_access['id']:
                        # SOBRESCRIBIR cualquier detección previa con proximidad
                        first_access = {
                            'frame_idx': 0,
                            'frame': frames[0],
                            'access_id': entry_access['id'],
                            'cardinal': entry_access.get('cardinal_official', entry_access.get('cardinal')),
                            'position': start_pos
                        }
                        last_access = {
                            'frame_idx': len(positions) - 1,
                            'frame': frames[-1],
                            'access_id': exit_access['id'],
                            'cardinal': exit_access.get('cardinal_official', exit_access.get('cardinal')),
                            'position': end_pos
                        }

        # Si aún no tenemos accesos, descartar
        if first_access is None:
            return []

        # Si no hay último acceso diferente, usar el primer acceso como salida (retorno)
        if last_access is None:
            last_access = first_access

        # Generar UN SOLO segmento
        segment = {
            'segment_index': 0,
            'entry_access_id': first_access['access_id'],
            'entry_cardinal': first_access['cardinal'],
            'entry_frame': first_access['frame'],
            'exit_access_id': last_access['access_id'],
            'exit_cardinal': last_access['cardinal'],
            'exit_frame': last_access['frame'],
            'positions': positions[first_access['frame_idx']:last_access['frame_idx']+1]
        }

        return [segment]

    def _infer_cardinal_from_direction(self, dx, dy):
        """
        Infiere punto cardinal basado en vector de dirección.

        Args:
            dx, dy: Componentes del vector de movimiento

        Returns:
            'N', 'S', 'E', 'O' según la dirección predominante
        """
        import math

        if abs(dx) < 10 and abs(dy) < 10:
            return None  # Movimiento muy pequeño

        angle = math.atan2(dy, dx) * 180 / math.pi

        # Normalizar ángulo a [0, 360)
        if angle < 0:
            angle += 360

        # Mapear ángulos a cardinales (asumiendo coord. de pantalla: Y hacia abajo)
        # 0° = Este, 90° = Sur, 180° = Oeste, 270° = Norte
        if 45 <= angle < 135:
            return 'S'  # Hacia abajo
        elif 135 <= angle < 225:
            return 'O'  # Hacia izquierda
        elif 225 <= angle < 315:
            return 'N'  # Hacia arriba
        else:
            return 'E'  # Hacia derecha

    def _find_nearest_access(self, position, accesses, preferred_cardinal=None):
        """
        Encuentra el acceso más cercano a una posición.

        Args:
            position: (x, y) tupla
            accesses: Lista de accesos
            preferred_cardinal: Cardinal preferido (opcional, para desempate)

        Returns:
            Acceso más cercano o None
        """
        if not position or not accesses:
            return None

        x, y = float(position[0]), float(position[1])
        min_dist = float('inf')
        nearest_access = None

        for access in accesses:
            # Calcular distancia al centro del acceso
            access_x = access.get('x', 0)
            access_y = access.get('y', 0)

            dist = ((x - access_x)**2 + (y - access_y)**2)**0.5

            # Si hay cardinal preferido, dar prioridad (reducir distancia efectiva 50%)
            if preferred_cardinal and access.get('cardinal_official') == preferred_cardinal:
                dist *= 0.5

            if dist < min_dist:
                min_dist = dist
                nearest_access = access

        return nearest_access

    def _find_second_nearest_access(self, position, accesses, exclude_id=None):
        """
        Encuentra el segundo acceso más cercano (excluyendo uno específico).

        Args:
            position: (x, y) tupla
            accesses: Lista de accesos
            exclude_id: ID del acceso a excluir

        Returns:
            Segundo acceso más cercano o None
        """
        if not position or not accesses:
            return None

        x, y = float(position[0]), float(position[1])
        min_dist = float('inf')
        second_nearest = None

        for access in accesses:
            # Saltar acceso excluido
            if exclude_id and access.get('id') == exclude_id:
                continue

            # Calcular distancia al centro del acceso
            access_x = access.get('x', 0)
            access_y = access.get('y', 0)

            dist = ((x - access_x)**2 + (y - access_y)**2)**0.5

            if dist < min_dist:
                min_dist = dist
                second_nearest = access

        return second_nearest

    def _crosses_gate(self, x: float, y: float, gate: Dict) -> bool:
        """
        Detecta si un punto (x,y) cruza una gate usando distancia perpendicular a la línea

        Args:
            x, y: Coordenadas del punto
            gate: Dict con x1, y1, x2, y2 definiendo la línea

        Returns:
            True si el punto está cerca de la gate (distancia perpendicular < threshold)
        """
        if not gate or 'x1' not in gate:
            return False

        x1, y1 = gate['x1'], gate['y1']
        x2, y2 = gate['x2'], gate['y2']

        # Vector de la línea de gate
        dx = x2 - x1
        dy = y2 - y1

        # Longitud de la gate
        length_sq = dx*dx + dy*dy

        if length_sq == 0:
            # Gate degenerada (punto), usar distancia euclidiana
            dist = np.sqrt((x - x1)**2 + (y - y1)**2)
            return dist < 50

        # Proyección del punto sobre la línea (parámetro t)
        # t=0 es (x1,y1), t=1 es (x2,y2)
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / length_sq))

        # Punto más cercano en la línea
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        # Distancia perpendicular
        dist_perp = np.sqrt((x - closest_x)**2 + (y - closest_y)**2)

        # Threshold: 50 píxeles (más preciso que antes)
        return dist_perp < 50

    def _load_cardinals(self, dataset_dir: Path) -> Optional[Dict]:
        """Carga configuración de cardinales"""
        cardinals_file = dataset_dir / "cardinals.json"
        if not cardinals_file.exists():
            return None
        data = json.loads(cardinals_file.read_text())
        return convert_to_json_serializable(data)

    def _load_rilsa_map(self, dataset_dir: Path) -> Optional[Dict]:
        """Carga mapa RILSA"""
        rilsa_file = dataset_dir / "rilsa_map.json"
        if not rilsa_file.exists():
            return None
        data = json.loads(rilsa_file.read_text())
        return convert_to_json_serializable(data)

    def _load_metadata(self, dataset_dir: Path) -> Dict:
        """Carga metadata del dataset"""
        metadata_file = dataset_dir / "metadata.json"
        if not metadata_file.exists():
            return {}
        data = json.loads(metadata_file.read_text())
        # Convertir todos los valores a tipos JSON serializables
        return convert_to_json_serializable(data)

    def _load_corrections(self, dataset_dir: Path) -> Dict:
        """Carga correcciones manuales de trayectorias"""
        corrections_file = dataset_dir / "trajectory_corrections.json"
        if not corrections_file.exists():
            return {}
        try:
            data = json.loads(corrections_file.read_text())
            corrections = data.get("corrections", {})
            print(f"\n[CORRECCIONES] Cargadas {len(corrections)} correcciones manuales")
            return corrections
        except Exception as e:
            print(f"\n[ERROR] No se pudieron cargar correcciones: {e}")
            return {}
