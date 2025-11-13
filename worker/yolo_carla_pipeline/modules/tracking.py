"""
Módulo de tracking multi-objeto para detecciones YOLOv8.

Implementa algoritmo SORT (Simple Online and Realtime Tracking) para
reconstruir trayectorias de objetos a partir de detecciones frame a frame.

Referencias:
- SORT: https://arxiv.org/abs/1602.00763
- Kalman Filter + Hungarian Algorithm para matching
"""

import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from scipy.optimize import linear_sum_assignment
from filterpy.kalman import KalmanFilter

logger = logging.getLogger(__name__)


@dataclass
class Track:
    """Representa una trayectoria de un objeto rastreado."""
    track_id: int
    clase: str
    positions: List[Tuple[float, float]] = field(default_factory=list)  # (x, y)
    bboxes: List[List[int]] = field(default_factory=list)  # [[x1, y1, x2, y2], ...]
    frames: List[int] = field(default_factory=list)
    confidences: List[float] = field(default_factory=list)
    age: int = 0  # Frames desde última detección
    hits: int = 0  # Total de detecciones asociadas
    time_since_update: int = 0  # Frames sin actualización

    def update(self, bbox: List[int], frame: int, confidence: float):
        """Actualiza la track con una nueva detección."""
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2

        self.positions.append((center_x, center_y))
        self.bboxes.append(bbox)
        self.frames.append(frame)
        self.confidences.append(confidence)
        self.hits += 1
        self.time_since_update = 0

    def predict(self):
        """Incrementa la edad de la track (no hay nueva detección)."""
        self.age += 1
        self.time_since_update += 1

    @property
    def is_valid(self) -> bool:
        """Verifica si la track tiene suficientes hits para ser considerada válida."""
        return self.hits >= 3  # Al menos 3 detecciones

    @property
    def length(self) -> int:
        """Longitud de la trayectoria."""
        return len(self.positions)

    @property
    def duration_frames(self) -> int:
        """Duración en frames."""
        if len(self.frames) < 2:
            return 0
        return self.frames[-1] - self.frames[0]

    @property
    def avg_confidence(self) -> float:
        """Confianza promedio."""
        if not self.confidences:
            return 0.0
        return sum(self.confidences) / len(self.confidences)

    def get_velocity_px_per_frame(self) -> Optional[Tuple[float, float]]:
        """
        Calcula la velocidad promedio en píxeles por frame.

        Returns:
            Tupla (vx, vy) o None si no hay suficientes puntos
        """
        if len(self.positions) < 2:
            return None

        velocities_x = []
        velocities_y = []

        for i in range(1, len(self.positions)):
            dx = self.positions[i][0] - self.positions[i-1][0]
            dy = self.positions[i][1] - self.positions[i-1][1]
            dt = self.frames[i] - self.frames[i-1]

            if dt > 0:
                velocities_x.append(dx / dt)
                velocities_y.append(dy / dt)

        if velocities_x and velocities_y:
            return (np.mean(velocities_x), np.mean(velocities_y))
        return None

    def get_total_distance_px(self) -> float:
        """Calcula la distancia total recorrida en píxeles."""
        if len(self.positions) < 2:
            return 0.0

        total_dist = 0.0
        for i in range(1, len(self.positions)):
            dx = self.positions[i][0] - self.positions[i-1][0]
            dy = self.positions[i][1] - self.positions[i-1][1]
            total_dist += np.sqrt(dx**2 + dy**2)

        return total_dist


class KalmanBoxTracker:
    """
    Tracker de bounding box usando Kalman Filter.

    Estado: [x, y, s, r, vx, vy, vs]
    donde:
    - x, y: centro del bbox
    - s: área del bbox
    - r: aspect ratio (ancho/alto)
    - vx, vy, vs: velocidades
    """

    count = 0  # Contador global de IDs

    def __init__(self, bbox: List[int], clase: str):
        """
        Inicializa el tracker.

        Args:
            bbox: [x1, y1, x2, y2]
            clase: Clase del objeto
        """
        # Kalman Filter con 7 estados y 4 observaciones
        self.kf = KalmanFilter(dim_x=7, dim_z=4)

        # Matriz de transición de estado
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],  # x = x + vx
            [0, 1, 0, 0, 0, 1, 0],  # y = y + vy
            [0, 0, 1, 0, 0, 0, 1],  # s = s + vs
            [0, 0, 0, 1, 0, 0, 0],  # r = r
            [0, 0, 0, 0, 1, 0, 0],  # vx = vx
            [0, 0, 0, 0, 0, 1, 0],  # vy = vy
            [0, 0, 0, 0, 0, 0, 1]   # vs = vs
        ])

        # Matriz de observación
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ])

        # Covarianza de medición (ruido de detección)
        self.kf.R[2:, 2:] *= 10.0

        # Covarianza de proceso (incertidumbre del modelo)
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.P *= 10.0

        # Covarianza de proceso
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01

        # Estado inicial
        self.kf.x[:4] = self._convert_bbox_to_z(bbox)

        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        self.clase = clase

    @staticmethod
    def _convert_bbox_to_z(bbox: List[int]) -> np.ndarray:
        """
        Convierte bbox [x1, y1, x2, y2] a formato z [x, y, s, r].

        Args:
            bbox: [x1, y1, x2, y2]

        Returns:
            array [x_center, y_center, area, aspect_ratio]
        """
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = bbox[0] + w / 2.0
        y = bbox[1] + h / 2.0
        s = w * h  # área
        r = w / max(h, 1e-6)  # aspect ratio
        return np.array([x, y, s, r]).reshape((4, 1))

    @staticmethod
    def _convert_x_to_bbox(x: np.ndarray) -> List[int]:
        """
        Convierte formato x [x, y, s, r] a bbox [x1, y1, x2, y2].

        Args:
            x: Estado [x_center, y_center, area, aspect_ratio, ...]

        Returns:
            bbox [x1, y1, x2, y2]
        """
        w = np.sqrt(x[2] * x[3])
        h = x[2] / max(w, 1e-6)
        x1 = x[0] - w / 2.0
        y1 = x[1] - h / 2.0
        x2 = x[0] + w / 2.0
        y2 = x[1] + h / 2.0
        return [int(x1), int(y1), int(x2), int(y2)]

    def update(self, bbox: List[int]):
        """
        Actualiza el estado con una nueva detección.

        Args:
            bbox: [x1, y1, x2, y2]
        """
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._convert_bbox_to_z(bbox))

    def predict(self) -> List[int]:
        """
        Predice el siguiente estado.

        Returns:
            Bbox predicho [x1, y1, x2, y2]
        """
        if (self.kf.x[6] + self.kf.x[2]) <= 0:
            self.kf.x[6] *= 0.0

        self.kf.predict()
        self.age += 1

        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1

        self.history.append(self._convert_x_to_bbox(self.kf.x))
        return self.history[-1]

    def get_state(self) -> List[int]:
        """Obtiene el bbox actual."""
        return self._convert_x_to_bbox(self.kf.x)


def iou_batch(bboxes_a: np.ndarray, bboxes_b: np.ndarray) -> np.ndarray:
    """
    Calcula IoU (Intersection over Union) entre dos conjuntos de bboxes.

    Args:
        bboxes_a: Array de shape (N, 4) con formato [x1, y1, x2, y2]
        bboxes_b: Array de shape (M, 4) con formato [x1, y1, x2, y2]

    Returns:
        Array de shape (N, M) con valores de IoU
    """
    xx1 = np.maximum(bboxes_a[:, 0][:, None], bboxes_b[:, 0])
    yy1 = np.maximum(bboxes_a[:, 1][:, None], bboxes_b[:, 1])
    xx2 = np.minimum(bboxes_a[:, 2][:, None], bboxes_b[:, 2])
    yy2 = np.minimum(bboxes_a[:, 3][:, None], bboxes_b[:, 3])

    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    intersection = w * h

    area_a = (bboxes_a[:, 2] - bboxes_a[:, 0]) * (bboxes_a[:, 3] - bboxes_a[:, 1])
    area_b = (bboxes_b[:, 2] - bboxes_b[:, 0]) * (bboxes_b[:, 3] - bboxes_b[:, 1])

    union = area_a[:, None] + area_b - intersection

    iou = intersection / np.maximum(union, 1e-6)
    return iou


def associate_detections_to_trackers(
    detections: np.ndarray,
    trackers: np.ndarray,
    iou_threshold: float = 0.3
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Asocia detecciones con trackers usando Hungarian Algorithm.

    Args:
        detections: Array de shape (N, 4) con detecciones
        trackers: Array de shape (M, 4) con predicciones de trackers
        iou_threshold: Umbral mínimo de IoU para asociación

    Returns:
        Tupla (matches, unmatched_detections, unmatched_trackers)
        - matches: array de shape (K, 2) con pares (det_idx, tracker_idx)
        - unmatched_detections: array con índices de detecciones no asociadas
        - unmatched_trackers: array con índices de trackers no asociados
    """
    if len(trackers) == 0:
        return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0,), dtype=int)

    iou_matrix = iou_batch(detections, trackers)

    if min(iou_matrix.shape) > 0:
        a = (iou_matrix > iou_threshold).astype(np.int32)
        if a.sum(1).max() == 1 and a.sum(0).max() == 1:
            matched_indices = np.stack(np.where(a), axis=1)
        else:
            # Hungarian Algorithm
            row_ind, col_ind = linear_sum_assignment(-iou_matrix)
            matched_indices = np.stack([row_ind, col_ind], axis=1)
    else:
        matched_indices = np.empty((0, 2), dtype=int)

    unmatched_detections = []
    for d in range(len(detections)):
        if d not in matched_indices[:, 0]:
            unmatched_detections.append(d)

    unmatched_trackers = []
    for t in range(len(trackers)):
        if t not in matched_indices[:, 1]:
            unmatched_trackers.append(t)

    # Filtrar matches con IoU bajo
    matches = []
    for m in matched_indices:
        if iou_matrix[m[0], m[1]] < iou_threshold:
            unmatched_detections.append(m[0])
            unmatched_trackers.append(m[1])
        else:
            matches.append(m.reshape(1, 2))

    if len(matches) == 0:
        matches = np.empty((0, 2), dtype=int)
    else:
        matches = np.concatenate(matches, axis=0)

    return matches, np.array(unmatched_detections), np.array(unmatched_trackers)


class MultiObjectTracker:
    """
    Tracker multi-objeto usando SORT algorithm.

    Características:
    - Kalman Filter para predicción de movimiento
    - Hungarian Algorithm para asociación de detecciones
    - Gestión de tracks con apariciones/desapariciones
    """

    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 3,
        iou_threshold: float = 0.3
    ):
        """
        Inicializa el tracker.

        Args:
            max_age: Frames máximos sin detección antes de eliminar track
            min_hits: Hits mínimos para considerar track como válida
            iou_threshold: Umbral de IoU para asociación
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers: List[KalmanBoxTracker] = []
        self.frame_count = 0
        self.tracks: Dict[int, Track] = {}

    def update(
        self,
        detections: List[Dict[str, any]],
        current_frame: int
    ) -> List[Track]:
        """
        Actualiza el tracker con nuevas detecciones.

        Args:
            detections: Lista de detecciones con formato:
                        [{'bbox': [x1, y1, x2, y2], 'clase': str, 'confianza': float}, ...]
            current_frame: Número de frame actual

        Returns:
            Lista de tracks activas
        """
        self.frame_count += 1

        # Predicciones de trackers existentes
        trks = np.zeros((len(self.trackers), 4))
        to_del = []
        for t, trk in enumerate(self.trackers):
            pos = trk.predict()
            trks[t] = pos
            if np.any(np.isnan(pos)):
                to_del.append(t)

        # Eliminar trackers inválidos
        for t in reversed(to_del):
            self.trackers.pop(t)
            trks = np.delete(trks, t, axis=0)

        # Convertir detecciones a array
        dets = np.array([d['bbox'] for d in detections]) if detections else np.empty((0, 4))

        # Asociar detecciones con trackers
        if len(dets) > 0 and len(trks) > 0:
            matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(
                dets, trks, self.iou_threshold
            )
        else:
            matched = np.empty((0, 2), dtype=int)
            unmatched_dets = np.arange(len(dets))
            unmatched_trks = np.arange(len(trks))

        # Actualizar trackers matched
        for m in matched:
            det_idx, trk_idx = m[0], m[1]
            self.trackers[trk_idx].update(detections[det_idx]['bbox'])

            # Actualizar track histórica
            tracker = self.trackers[trk_idx]
            if tracker.id not in self.tracks:
                self.tracks[tracker.id] = Track(
                    track_id=tracker.id,
                    clase=tracker.clase
                )

            self.tracks[tracker.id].update(
                bbox=detections[det_idx]['bbox'],
                frame=current_frame,
                confidence=detections[det_idx]['confianza']
            )

        # Crear nuevos trackers para detecciones no asociadas
        for i in unmatched_dets:
            trk = KalmanBoxTracker(detections[i]['bbox'], detections[i]['clase'])
            self.trackers.append(trk)

        # Eliminar trackers muertos
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            i -= 1
            if trk.time_since_update > self.max_age:
                self.trackers.pop(i)

        # Retornar tracks válidas
        valid_tracks = [
            track for track in self.tracks.values()
            if track.is_valid and track.time_since_update < self.max_age
        ]

        return valid_tracks

    def get_all_tracks(self) -> List[Track]:
        """Obtiene todas las tracks (válidas e inválidas)."""
        return list(self.tracks.values())

    def get_valid_tracks(self) -> List[Track]:
        """Obtiene solo las tracks válidas."""
        return [track for track in self.tracks.values() if track.is_valid]

    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del tracker."""
        valid_tracks = self.get_valid_tracks()
        return {
            'total_tracks': len(self.tracks),
            'valid_tracks': len(valid_tracks),
            'active_trackers': len(self.trackers),
            'frame_count': self.frame_count,
            'avg_track_length': np.mean([t.length for t in valid_tracks]) if valid_tracks else 0,
            'class_distribution': self._get_class_distribution(valid_tracks)
        }

    def _get_class_distribution(self, tracks: List[Track]) -> Dict[str, int]:
        """Obtiene distribución de clases en tracks."""
        dist = {}
        for track in tracks:
            dist[track.clase] = dist.get(track.clase, 0) + 1
        return dist


if __name__ == "__main__":
    # Ejemplo de uso
    print("Módulo de tracking multi-objeto")
    print("Usa este módulo importándolo en tu código principal")
