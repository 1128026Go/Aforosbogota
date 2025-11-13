"""
Servicio de conversión PKL -> Parquet
"""

import pickle
import pandas as pd
from pathlib import Path
from typing import Dict, Any


def normalize_pkl_to_parquet(pkl_path: Path, parquet_path: Path) -> Dict[str, Any]:
    """
    Convierte PKL a Parquet normalizado

    Soporta formato:
    {
      'metadata': {...},
      'detecciones': [{'fotograma': int, 'clase': str, 'confianza': float, 'bbox': []}],
      'trayectorias': {},
      'config': {...}
    }

    Returns:
        Dict con estadísticas: {frames, tracks, classes}
    """
    # Cargar PKL
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    rows = []
    classes_seen = set()
    frames_seen = set()

    # Manejar formato con 'detecciones' y 'metadata'
    if isinstance(data, dict) and 'detecciones' in data:
        detecciones = data.get('detecciones', [])

        for det in detecciones:
            clase = det.get('clase', 'unknown')
            fotograma = det.get('fotograma', 0)
            bbox = det.get('bbox', [0, 0, 0, 0])

            classes_seen.add(clase)
            frames_seen.add(fotograma)

            # Calcular centro del bbox
            if len(bbox) >= 4:
                x_center = (bbox[0] + bbox[2]) / 2
                y_center = (bbox[1] + bbox[3]) / 2
            else:
                x_center, y_center = 0, 0

            rows.append({
                "frame_id": fotograma,
                "x": x_center,
                "y": y_center,
                "class": clase,
                "confidence": det.get('confianza', 0.0),
                "bbox_x1": bbox[0] if len(bbox) >= 4 else 0,
                "bbox_y1": bbox[1] if len(bbox) >= 4 else 0,
                "bbox_x2": bbox[2] if len(bbox) >= 4 else 0,
                "bbox_y2": bbox[3] if len(bbox) >= 4 else 0,
            })

    # Formato alternativo (legacy): {frame_id: {track_id: {...}}}
    elif isinstance(data, dict) and 'detecciones' not in data:
        for frame_id, frame_data in data.items():
            if isinstance(frame_data, dict):
                for track_id, track_info in frame_data.items():
                    classes_seen.add(track_info.get("class", "unknown"))
                    frames_seen.add(frame_id)

                    rows.append({
                        "frame_id": frame_id,
                        "track_id": track_id,
                        "x": track_info.get("x", 0),
                        "y": track_info.get("y", 0),
                        "class": track_info.get("class", "unknown"),
                        "confidence": track_info.get("confidence", 0.0),
                    })

    if not rows:
        # Crear DataFrame vacío con estructura mínima
        df = pd.DataFrame(columns=["frame_id", "class", "confidence", "x", "y"])
    else:
        df = pd.DataFrame(rows)
        # Normalizar clases
        df["class"] = df["class"].apply(normalize_class)

    # Guardar como Parquet
    df.to_parquet(parquet_path, index=False)

    return {
        "frames": len(frames_seen),
        "tracks": len(df) if not df.empty else 0,  # Total detecciones
        "classes": list(classes_seen),
    }


def normalize_class(raw_class: str) -> str:
    """
    Normaliza clases a las 8 definitivas:
    car, motorcycle, bus, truck_c1, truck_c2, truck_c3, bicycle, person
    """
    mapping = {
        # Autos
        "car": "car",
        "sedan": "car",
        "suv": "car",
        "hatchback": "car",
        # Motos
        "motorcycle": "motorcycle",
        "motorbike": "motorcycle",
        "moto": "motorcycle",
        # Bus
        "bus": "bus",
        "autobus": "bus",
        # Camiones
        "truck": "truck_c1",
        "truck_c1": "truck_c1",
        "truck_c2": "truck_c2",
        "truck_c3": "truck_c3",
        "camion": "truck_c1",
        "camion_c1": "truck_c1",
        "camion_c2": "truck_c2",
        "camion_c3": "truck_c3",
        # Bicicletas
        "bicycle": "bicycle",
        "bike": "bicycle",
        "bici": "bicycle",
        # Peatones
        "person": "person",
        "pedestrian": "person",
        "peaton": "person",
        "walker": "person",
    }

    return mapping.get(raw_class.lower(), "car")  # Default: car
