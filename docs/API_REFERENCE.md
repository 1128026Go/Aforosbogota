# Referencia de API

Base URL: `http://localhost:8000/api/v1`

## Autenticación

Actualmente no se requiere autenticación; todas las rutas están abiertas para el dashboard.

## Datasets

### `POST /datasets/upload`
Sube un archivo PKL y crea un dataset.

**Body (multipart/form-data)**
- `file`: archivo `.pkl`
- `metadata` (opcional): JSON con `location`, `description`, etc.

**Respuesta**
```json
{
  "dataset_id": "gx010323",
  "filename": "detections.pkl",
  "created_at": "2025-11-13T09:30:00Z"
}
```

### `GET /datasets`
Lista los datasets disponibles.

## Configuración

### `GET /config/{dataset_id}`
Obtiene configuración actual (cardinals, reglas RILSA, parámetros).

### `POST /config/{dataset_id}/cardinals`
Actualiza accesos cardinales.

### `POST /config/{dataset_id}/parameters`
Actualiza parámetros específicos de dataset (en desuso, sustituido por `analysis_settings`).

### `GET /config/{dataset_id}/analysis_settings`
Devuelve la configuración avanzada utilizada por todos los cálculos de análisis:
```json
{
  "interval_minutes": 15,
  "min_length_m": 5.0,
  "max_direction_changes": 20,
  "min_net_over_path_ratio": 0.2,
  "ttc_threshold_s": 1.5
}
```

### `PUT /config/{dataset_id}/analysis_settings`
Actualiza y persiste los parámetros. Cuerpo esperado: `AnalysisSettings`.

### `GET /config/{dataset_id}/forbidden_movements`
Lista de movimientos RILSA prohibidos:
```json
[
  { "rilsa_code": "5", "description": "Giro izquierda restringido" }
]
```

### `PUT /config/{dataset_id}/forbidden_movements`
Sobrescribe la lista con un array de `{ rilsa_code, description? }`.

## Análisis

### `GET /analysis/{dataset_id}/volumes`
Devuelve conteos por intervalo y movimiento, usando `interval_minutes` y filtros definidos en `analysis_settings`.

```json
{
  "dataset_id": "demo",
  "interval_minutes": 15,
  "totals_by_interval": [
    { "interval_start": 0, "interval_end": 15, "autos": 10, "total": 17 }
  ],
  "movements": [
    { "rilsa_code": "1", "description": "Movimiento 1", "rows": [...] }
  ]
}
```

### `GET /analysis/{dataset_id}/speeds`
Estadísticos de velocidad por movimiento/clase.

### `GET /analysis/{dataset_id}/conflicts`
Conflictos TTC/PET filtrados por el umbral `ttc_threshold_s` guardado en `analysis_settings`.

### `GET /analysis/{dataset_id}/violations`
Resumen de maniobras indebidas detectadas cruzando las trayectorias clasificadas con la lista de movimientos prohibidos.

**Respuesta**
```json
{
  "dataset_id": "demo",
  "total_violations": 3,
  "by_movement": [
    { "rilsa_code": "5", "description": "Giro izquierda restringido", "count": 2 },
    { "rilsa_code": "9_", "description": "Cruce peatonal bloqueado", "count": 1 }
  ]
}
```

## Reportes

### `GET /reports/{dataset_id}/summary`
Genera CSV con conteos (se retorna como archivo para descarga).

### `GET /reports/{dataset_id}/excel`
Genera XLSX multi-hoja (Totales + Mov_<código>), respetando `analysis_settings`.

### `GET /reports/{dataset_id}/pdf`
Genera PDF basado en `templates/report.html`, incluye portada, resumen ejecutivo (volúmenes, velocidades, conflictos, violaciones) y tablas detalladas.

### `GET /reports/{dataset_id}/download/{filename}`
Descarga cualquiera de los archivos generados (CSV/XLSX/PDF).

## Códigos de estado

- `200 OK`: solicitud exitosa.
- `201 Created`: dataset creado.
- `400 Bad Request`: error de validación (p.ej. PKL inválido).
- `404 Not Found`: dataset o recurso inexistente.
- `500 Internal Server Error`: fallo inesperado durante el procesamiento.

## Versionado de API

La versión actual es `v1`. Cambios breaking se documentarán en `docs/CHANGELOG.md`.
