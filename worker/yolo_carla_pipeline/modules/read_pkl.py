"""
Módulo de ingesta y validación de archivos PKL con detecciones YOLOv8.

Este módulo proporciona funcionalidades para:
- Cargar archivos PKL con detecciones de objetos
- Validar la estructura y contenido de los datos
- Extraer metadata y configuración
- Preprocesar detecciones para análisis posterior
"""

import pickle
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Clase para representar una detección individual."""
    bbox: List[int]  # [x1, y1, x2, y2]
    clase: str
    confianza: float
    fotograma: int

    @property
    def center(self) -> Tuple[float, float]:
        """Calcula el centro del bbox."""
        return ((self.bbox[0] + self.bbox[2]) / 2,
                (self.bbox[1] + self.bbox[3]) / 2)

    @property
    def width(self) -> float:
        """Ancho del bbox."""
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        """Alto del bbox."""
        return self.bbox[3] - self.bbox[1]

    @property
    def area(self) -> float:
        """Área del bbox."""
        return self.width * self.height


@dataclass
class PKLMetadata:
    """Metadata del archivo PKL."""
    video: str
    fps: float
    width: int
    height: int
    total_frames: int
    frames_procesados: int
    tiempo_segundos: float
    modelo: str
    resolucion: int
    confianza: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'video': self.video,
            'fps': self.fps,
            'width': self.width,
            'height': self.height,
            'total_frames': self.total_frames,
            'frames_procesados': self.frames_procesados,
            'tiempo_segundos': self.tiempo_segundos,
            'modelo': self.modelo,
            'resolucion': self.resolucion,
            'confianza': self.confianza,
            'timestamp': self.timestamp
        }


class PKLReader:
    """Lector y validador de archivos PKL de detecciones YOLOv8."""

    REQUIRED_KEYS = ['metadata', 'detecciones', 'config']
    VALID_CLASSES = ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'person', 'traffic light']

    def __init__(self, confidence_threshold: float = 0.5):
        """
        Inicializa el lector de PKL.

        Args:
            confidence_threshold: Umbral mínimo de confianza para filtrar detecciones
        """
        self.confidence_threshold = confidence_threshold
        self.stats = {
            'files_loaded': 0,
            'total_detections': 0,
            'filtered_detections': 0,
            'errors': []
        }

    def load(self, pkl_path: str) -> Optional[Dict[str, Any]]:
        """
        Carga un archivo PKL.

        Args:
            pkl_path: Ruta al archivo PKL

        Returns:
            Diccionario con los datos del PKL o None si falla
        """
        try:
            pkl_file = Path(pkl_path)
            if not pkl_file.exists():
                logger.error(f"Archivo no encontrado: {pkl_path}")
                return None

            with open(pkl_file, 'rb') as f:
                data = pickle.load(f)

            logger.info(f"PKL cargado exitosamente: {pkl_file.name}")
            self.stats['files_loaded'] += 1
            return data

        except Exception as e:
            logger.error(f"Error cargando PKL {pkl_path}: {e}")
            self.stats['errors'].append(str(e))
            return None

    def validate_structure(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida la estructura del PKL.

        Args:
            data: Datos del PKL

        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        errors = []

        # Verificar claves requeridas
        for key in self.REQUIRED_KEYS:
            if key not in data:
                errors.append(f"Clave requerida faltante: {key}")

        if errors:
            return False, errors

        # Validar metadata
        metadata = data.get('metadata', {})
        required_metadata = ['video', 'fps', 'width', 'height', 'total_frames']
        for field in required_metadata:
            if field not in metadata:
                errors.append(f"Campo de metadata faltante: {field}")

        # Validar detecciones
        detecciones = data.get('detecciones', [])
        if not isinstance(detecciones, list):
            errors.append("'detecciones' debe ser una lista")
        elif len(detecciones) == 0:
            errors.append("No hay detecciones en el PKL")
        else:
            # Validar estructura de primera detección
            det = detecciones[0]
            required_det_fields = ['bbox', 'clase', 'confianza', 'fotograma']
            for field in required_det_fields:
                if field not in det:
                    errors.append(f"Campo de detección faltante: {field}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def extract_metadata(self, data: Dict[str, Any]) -> Optional[PKLMetadata]:
        """
        Extrae la metadata del PKL.

        Args:
            data: Datos del PKL

        Returns:
            Objeto PKLMetadata o None si falla
        """
        try:
            meta = data.get('metadata', {})
            return PKLMetadata(
                video=meta.get('video', 'unknown'),
                fps=meta.get('fps', 30.0),
                width=meta.get('width', 1920),
                height=meta.get('height', 1080),
                total_frames=meta.get('total_frames', 0),
                frames_procesados=meta.get('frames_procesados', 0),
                tiempo_segundos=meta.get('tiempo_segundos', 0.0),
                modelo=meta.get('modelo', 'yolov8'),
                resolucion=meta.get('resolucion', 640),
                confianza=meta.get('confianza', 0.5),
                timestamp=meta.get('timestamp', datetime.now().isoformat())
            )
        except Exception as e:
            logger.error(f"Error extrayendo metadata: {e}")
            return None

    def parse_detections(
        self,
        data: Dict[str, Any],
        filter_classes: Optional[List[str]] = None
    ) -> List[Detection]:
        """
        Parsea las detecciones del PKL.

        Args:
            data: Datos del PKL
            filter_classes: Lista de clases a filtrar (None = todas)

        Returns:
            Lista de objetos Detection
        """
        detecciones_raw = data.get('detecciones', [])
        detecciones = []

        for det_raw in detecciones_raw:
            try:
                # Filtrar por confianza
                if det_raw['confianza'] < self.confidence_threshold:
                    self.stats['filtered_detections'] += 1
                    continue

                # Filtrar por clase
                if filter_classes and det_raw['clase'] not in filter_classes:
                    continue

                det = Detection(
                    bbox=det_raw['bbox'],
                    clase=det_raw['clase'],
                    confianza=det_raw['confianza'],
                    fotograma=det_raw['fotograma']
                )
                detecciones.append(det)
                self.stats['total_detections'] += 1

            except Exception as e:
                logger.warning(f"Error parseando detección: {e}")
                continue

        logger.info(f"Parseadas {len(detecciones)} detecciones")
        return detecciones

    def get_frame_range(self, detections: List[Detection]) -> Tuple[int, int]:
        """
        Obtiene el rango de fotogramas en las detecciones.

        Args:
            detections: Lista de detecciones

        Returns:
            Tupla (frame_min, frame_max)
        """
        if not detections:
            return 0, 0

        frames = [d.fotograma for d in detections]
        return min(frames), max(frames)

    def get_class_distribution(self, detections: List[Detection]) -> Dict[str, int]:
        """
        Calcula la distribución de clases en las detecciones.

        Args:
            detections: Lista de detecciones

        Returns:
            Diccionario {clase: cantidad}
        """
        distribution = {}
        for det in detections:
            distribution[det.clase] = distribution.get(det.clase, 0) + 1
        return distribution

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del lector."""
        return self.stats.copy()


def load_and_validate_pkl(
    pkl_path: str,
    confidence_threshold: float = 0.5,
    filter_classes: Optional[List[str]] = None
) -> Tuple[Optional[PKLMetadata], List[Detection], Dict[str, Any]]:
    """
    Función helper para cargar y validar un PKL en un solo paso.

    Args:
        pkl_path: Ruta al archivo PKL
        confidence_threshold: Umbral de confianza mínimo
        filter_classes: Clases a filtrar (None = todas)

    Returns:
        Tupla (metadata, detecciones, stats)
    """
    reader = PKLReader(confidence_threshold=confidence_threshold)

    # Cargar
    data = reader.load(pkl_path)
    if data is None:
        return None, [], reader.get_stats()

    # Validar
    is_valid, errors = reader.validate_structure(data)
    if not is_valid:
        logger.error(f"PKL inválido: {errors}")
        return None, [], reader.get_stats()

    # Extraer metadata
    metadata = reader.extract_metadata(data)

    # Parsear detecciones
    detections = reader.parse_detections(data, filter_classes=filter_classes)

    # Estadísticas adicionales
    frame_range = reader.get_frame_range(detections)
    class_dist = reader.get_class_distribution(detections)

    stats = reader.get_stats()
    stats['frame_range'] = frame_range
    stats['class_distribution'] = class_dist

    logger.info(f"PKL procesado: {len(detections)} detecciones en frames {frame_range[0]}-{frame_range[1]}")
    logger.info(f"Distribución de clases: {class_dist}")

    return metadata, detections, stats


if __name__ == "__main__":
    # Ejemplo de uso
    import sys

    if len(sys.argv) < 2:
        print("Uso: python read_pkl.py <ruta_al_pkl>")
        sys.exit(1)

    pkl_path = sys.argv[1]
    metadata, detections, stats = load_and_validate_pkl(pkl_path)

    if metadata:
        print(f"\n{'='*60}")
        print(f"METADATA DEL VIDEO")
        print(f"{'='*60}")
        print(f"Video: {metadata.video}")
        print(f"Resolución: {metadata.width}x{metadata.height}")
        print(f"FPS: {metadata.fps:.2f}")
        print(f"Frames totales: {metadata.total_frames}")
        print(f"Duración: {metadata.tiempo_segundos:.2f} segundos")
        print(f"Modelo: {metadata.modelo}")

        print(f"\n{'='*60}")
        print(f"ESTADÍSTICAS DE DETECCIONES")
        print(f"{'='*60}")
        print(f"Detecciones totales: {stats['total_detections']}")
        print(f"Detecciones filtradas: {stats['filtered_detections']}")
        print(f"Rango de frames: {stats['frame_range'][0]} - {stats['frame_range'][1]}")

        print(f"\nDistribución por clase:")
        for clase, count in sorted(stats['class_distribution'].items(), key=lambda x: -x[1]):
            print(f"  {clase}: {count}")
