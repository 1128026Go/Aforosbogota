"""
Utilidades para convertir archivos PKL de tracking en Parquet normalizado.

La función principal `normalize_pkl_to_parquet` intenta reconocer varias
estructuras comunes de salidas de tracking (DataFrames, listas de dicts,
diccionarios anidados) y generar un archivo `normalized.parquet` con un
esquema mínimo consistente para el resto del pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd
import pickle

DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_FPS = 30.0

MANDATORY_COLUMNS = ("frame_id", "track_id", "x", "y", "object_class")
STRUCTURED_PKL_KEYS = {"metadata", "detecciones", "trayectorias", "config"}
DETECTION_REQUIRED_FIELDS = ("fotograma", "clase", "confianza", "bbox")
DETECTION_COLUMN_ORDER = (
    "frame_id",
    "track_id",
    "x",
    "y",
    "object_class",
    "confidence",
    "x_min",
    "y_min",
    "x_max",
    "y_max",
)
COLUMN_CANDIDATES: Dict[str, List[str]] = {
    "frame_id": ["frame_id", "frame", "frame_idx", "frame_index", "frame_number"],
    "track_id": ["track_id", "id", "track", "trackid", "object_id"],
    "x": ["x", "xc", "x_center", "xcentre", "cx", "bbox_center_x"],
    "y": ["y", "yc", "y_center", "ycentre", "cy", "bbox_center_y"],
    "object_class": ["object_class", "cls", "class", "label", "object_type", "category"],
}


@dataclass
class NormalizationResult:
    dataframe: pd.DataFrame
    frames: int
    tracks: int
    width: int
    height: int
    fps: float


def normalize_pkl_to_parquet(pkl_path: Path, parquet_path: Path) -> Dict[str, Any]:
    """
    Normaliza un PKL de tracking y persiste un `normalized.parquet`.

    Args:
        pkl_path: Ruta al archivo PKL original.
        parquet_path: Ruta donde se escribirá el parquet normalizado.

    Returns:
        dict con metadatos básicos (frames, tracks, width, height, fps).

    Raises:
        ValueError si no se puede construir un DataFrame con el esquema requerido.
    """
    normalization = _load_and_normalize(pkl_path)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    normalization.dataframe.to_parquet(parquet_path, index=False)
    return {
        "frames": normalization.frames,
        "tracks": normalization.tracks,
        "width": normalization.width,
        "height": normalization.height,
        "fps": normalization.fps,
    }


def _load_and_normalize(pkl_path: Path) -> NormalizationResult:
    raw_obj = _read_pickle(pkl_path)
    if _looks_like_structured_detection(raw_obj):
        return _normalize_structured_detection(raw_obj)
    metadata = _extract_metadata(raw_obj)
    df = _object_to_dataframe(raw_obj)

    # Normalizar columnas obligatorias
    df = _normalize_columns(df)

    df["frame_id"] = pd.to_numeric(df["frame_id"], errors="coerce")
    df["track_id"] = pd.to_numeric(df["track_id"], errors="coerce")
    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")

    df = df.dropna(subset=["frame_id", "track_id", "x", "y"])

    if df.empty:
        raise ValueError("El PKL no contiene trayectorias válidas para normalizar.")

    df["frame_id"] = df["frame_id"].astype(int)
    df["track_id"] = df["track_id"].astype(int)
    df["x"] = df["x"].astype(float)
    df["y"] = df["y"].astype(float)

    df["object_class"] = df["object_class"].astype(str)
    df = df.sort_values(["frame_id", "track_id"]).reset_index(drop=True)

    frames = int(df["frame_id"].max() + 1) if df["frame_id"].max() >= 0 else df["frame_id"].nunique()
    tracks = int(df["track_id"].nunique())

    width = int(metadata.get("width") or _dimension_from_series(df.get("frame_width"), DEFAULT_WIDTH))
    height = int(metadata.get("height") or _dimension_from_series(df.get("frame_height"), DEFAULT_HEIGHT))
    fps = float(metadata.get("fps") or metadata.get("frame_rate") or DEFAULT_FPS)

    return NormalizationResult(
        dataframe=df[list(MANDATORY_COLUMNS)],
        frames=frames,
        tracks=tracks,
        width=width,
        height=height,
        fps=fps,
    )


def _object_to_dataframe(obj: Any) -> pd.DataFrame:
    """
    Intenta construir un DataFrame con información de tracking a partir de
    diferentes estructuras utilizadas en proyectos anteriores.
    """
    if isinstance(obj, pd.DataFrame):
        return obj.copy()
    if isinstance(obj, pd.Series):
        return obj.to_frame().T
    if isinstance(obj, Mapping):
        preferred_keys = ("data", "df", "tracks", "detections", "items", "frames")
        for key in preferred_keys:
            if key in obj:
                df = _convert_iterable(obj[key])
                if not df.empty:
                    return df
        possible_frames = _extract_iterables(obj)
        for candidate in possible_frames:
            df = _convert_iterable(candidate)
            if not df.empty:
                return df
        return _convert_iterable(obj.values())
    if isinstance(obj, (list, tuple)):
        return _convert_iterable(obj)
    raise ValueError(f"Estructura PKL no soportada: {type(obj)!r}")


def _extract_iterables(data: Mapping[str, Any]) -> List[Iterable[Any]]:
    """
    Busca colecciones potenciales de detecciones/trackings dentro de un dict.
    """
    candidates: List[Iterable[Any]] = []
    for key, value in data.items():
        if isinstance(value, (list, tuple)):
            candidates.append(value)
        elif isinstance(value, pd.DataFrame):
            candidates.append(value.to_dict("records"))
        elif isinstance(value, Mapping):
            candidates.extend(_extract_iterables(value))
    return candidates


def _convert_iterable(items: Iterable[Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if isinstance(items, pd.DataFrame):
        return items.copy()
    for item in items:
        if isinstance(item, pd.Series):
            rows.append(item.to_dict())
        elif isinstance(item, Mapping):
            rows.append(dict(item))
        elif isinstance(item, (list, tuple)) and len(item) >= 5:
            frame_id, track_id, x, y, label = item[:5]
            rows.append(
                {
                    "frame_id": frame_id,
                    "track_id": track_id,
                    "x": x,
                    "y": y,
                    "object_class": label,
                }
            )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("El PKL no contiene datos tabulares para normalizar.")

    original_columns = list(df.columns)
    df = df.copy()
    lower_to_original = {str(col).lower(): col for col in df.columns}
    rename_mapping: Dict[str, str] = {}

    for target, candidates in COLUMN_CANDIDATES.items():
        for candidate in candidates:
            if candidate in df.columns:
                rename_mapping[candidate] = target
                break
            candidate_lower = candidate.lower()
            if candidate_lower in lower_to_original:
                source_col = lower_to_original[candidate_lower]
                rename_mapping[source_col] = target
                break

    df = df.rename(columns=rename_mapping)

    if "x" not in df.columns or "y" not in df.columns:
        df = _add_centroid_columns(df)

    missing = [col for col in MANDATORY_COLUMNS if col not in df.columns]
    if missing:
        columns_found = ", ".join(str(col) for col in original_columns)
        raise ValueError(
            "El PKL no contiene columnas mapeables a ['frame_id', 'track_id', 'x', 'y', 'object_class']. "
            f"Columnas encontradas: [{columns_found}]"
        )

    return df[list(MANDATORY_COLUMNS)].copy()


def _add_centroid_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Completa columnas x/y a partir de bounding boxes si están disponibles.
    """
    lower_to_original = {str(col).lower(): col for col in df.columns}

    def has_columns(*names: str) -> bool:
        return all(name in lower_to_original for name in names)

    if has_columns("bbox_left", "bbox_top", "bbox_width", "bbox_height"):
        df = df.copy()
        df["x"] = (
            df[lower_to_original["bbox_left"]] + df[lower_to_original["bbox_width"]] / 2.0
        )
        df["y"] = (
            df[lower_to_original["bbox_top"]] + df[lower_to_original["bbox_height"]] / 2.0
        )
        return df
    if has_columns("xmin", "ymin", "xmax", "ymax"):
        df = df.copy()
        df["x"] = (
            df[lower_to_original["xmin"]] + df[lower_to_original["xmax"]]
        ) / 2.0
        df["y"] = (
            df[lower_to_original["ymin"]] + df[lower_to_original["ymax"]]
        ) / 2.0
        return df
    if has_columns("left", "top", "width", "height"):
        df = df.copy()
        df["x"] = df[lower_to_original["left"]] + df[lower_to_original["width"]] / 2.0
        df["y"] = df[lower_to_original["top"]] + df[lower_to_original["height"]] / 2.0
        return df
    return df


def _extract_metadata(obj: Any) -> Dict[str, Any]:
    """
    Busca valores de width/height/fps en estructuras comunes del PKL.
    """
    metadata: Dict[str, Any] = {}

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            lower_keys = {str(k).lower(): k for k in node.keys()}
            width_key = next((lower_keys[k] for k in lower_keys if k in {"width", "w", "frame_width"}), None)
            height_key = next((lower_keys[k] for k in lower_keys if k in {"height", "h", "frame_height"}), None)
            fps_key = next((lower_keys[k] for k in lower_keys if k in {"fps", "frame_rate", "frames_per_second"}), None)
            if width_key is not None and not metadata.get("width"):
                value = node[width_key]
                if isinstance(value, (int, float)):
                    metadata["width"] = int(value)
                elif isinstance(value, Sequence) and len(value) >= 1:
                    metadata["width"] = int(value[0])
            if height_key is not None and not metadata.get("height"):
                value = node[height_key]
                if isinstance(value, (int, float)):
                    metadata["height"] = int(value)
                elif isinstance(value, Sequence) and len(value) >= 2:
                    metadata["height"] = int(value[1])
            if fps_key is not None and not metadata.get("fps"):
                value = node[fps_key]
                if isinstance(value, (int, float)):
                    metadata["fps"] = float(value)
            for value in node.values():
                visit(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                visit(item)

    visit(obj)
    return metadata


def _dimension_from_series(series: Optional[pd.Series], default: int) -> int:
    if series is None:
        return default
    try:
        value = series.dropna().max()
    except Exception:
        return default
    if value is None or pd.isna(value):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _read_pickle(pkl_path: Path) -> Any:
    with pkl_path.open("rb") as handle:
        return pickle.load(handle)


def _looks_like_structured_detection(obj: Any) -> bool:
    return isinstance(obj, Mapping) and STRUCTURED_PKL_KEYS.issubset(set(obj.keys()))


def _normalize_structured_detection(raw_obj: Mapping[str, Any]) -> NormalizationResult:
    metadata = raw_obj.get("metadata") or {}
    detecciones = raw_obj.get("detecciones")
    if detecciones is None:
        raise ValueError("El PKL estructurado no contiene la clave 'detecciones'.")
    df = _build_detection_dataframe(detecciones)
    frames = int(df["frame_id"].max() + 1) if not df.empty else 0
    width = _metadata_int(metadata, ("width", "frame_width", "w"), DEFAULT_WIDTH)
    height = _metadata_int(metadata, ("height", "frame_height", "h"), DEFAULT_HEIGHT)
    fps = _metadata_float(metadata, ("fps", "frame_rate", "frames_per_second"), DEFAULT_FPS)
    return NormalizationResult(
        dataframe=df,
        frames=frames,
        tracks=0,
        width=width,
        height=height,
        fps=fps,
    )


def _build_detection_dataframe(detecciones: Any) -> pd.DataFrame:
    if not isinstance(detecciones, list):
        raise ValueError("La clave 'detecciones' debe ser una lista de diccionarios.")
    if not detecciones:
        empty = pd.DataFrame(columns=DETECTION_COLUMN_ORDER)
        empty["track_id"] = empty["track_id"].astype("Int64")
        return empty
    df = pd.DataFrame(detecciones)
    missing = [col for col in DETECTION_REQUIRED_FIELDS if col not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas obligatorias en detecciones: {', '.join(missing)}.")
    bbox_values = [_validate_bbox(record, idx) for idx, record in enumerate(df["bbox"])]
    bbox_df = pd.DataFrame(bbox_values, columns=["x_min", "y_min", "x_max", "y_max"])
    df = pd.concat([df.drop(columns=["bbox"]), bbox_df], axis=1)
    df = df.rename(columns={"fotograma": "frame_id", "clase": "object_class", "confianza": "confidence"})
    df["frame_id"] = pd.to_numeric(df["frame_id"], errors="coerce")
    df = df.dropna(subset=["frame_id"])
    df["frame_id"] = df["frame_id"].astype(int)
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    df["object_class"] = df["object_class"].astype(str)
    df["x"] = (pd.to_numeric(df["x_min"], errors="coerce") + pd.to_numeric(df["x_max"], errors="coerce")) / 2.0
    df["y"] = (pd.to_numeric(df["y_min"], errors="coerce") + pd.to_numeric(df["y_max"], errors="coerce")) / 2.0
    track_series = pd.Series(pd.array([pd.NA] * len(df), dtype="Int64"), name="track_id")
    df = pd.concat([df[["frame_id"]], track_series, df.drop(columns=["frame_id"])], axis=1)
    df = df.sort_values(["frame_id"]).reset_index(drop=True)
    # Reordenar columnas para garantizar un esquema consistente
    existing = [col for col in DETECTION_COLUMN_ORDER if col in df.columns]
    df = df[existing]
    return df


def _validate_bbox(value: Any, index: int) -> Tuple[float, float, float, float]:
    if not isinstance(value, Sequence) or len(value) != 4:
        raise ValueError(f"La detección #{index} contiene una bbox inválida: {value!r}")
    try:
        x_min, y_min, x_max, y_max = (float(coord) for coord in value)
    except (TypeError, ValueError):
        raise ValueError(f"La detección #{index} tiene valores no numéricos en bbox: {value!r}") from None
    if x_max < x_min or y_max < y_min:
        raise ValueError(f"La detección #{index} presenta coordenadas de bbox invertidas: {value!r}")
    return x_min, y_min, x_max, y_max


def _metadata_int(metadata: Mapping[str, Any], candidates: Sequence[str], default: int) -> int:
    for key in candidates:
        value = metadata.get(key)
        if isinstance(value, (int, float)):
            return int(value)
    return default


def _metadata_float(metadata: Mapping[str, Any], candidates: Sequence[str], default: float) -> float:
    for key in candidates:
        value = metadata.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return default
    try:
        value = series.dropna().max()
    except Exception:
        return default
    if value is None or pd.isna(value):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


