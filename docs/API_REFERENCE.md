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

```json
{
  "cardinals": {
    "N": { "label": "Norte", "movements": [1, 2, 3] },
    "S": { "label": "Sur", "movements": [5, 6, 7] }
  }
}
```

### `POST /config/{dataset_id}/parameters`
Actualiza parámetros de análisis (`interval_minutes`, `ttc_threshold`, etc.).

## Análisis

### `GET /analysis/{dataset_id}/volumes`
Devuelve conteos por intervalo y movimiento.

```json
{
  "dataset_id": "gx010323",
  "interval_minutes": 15,
  "rows": [
    {
      "interval_start": "2025-06-01T07:00:00Z",
      "rilsa_code": "N1",
      "vehicle_class": "car",
      "count": 123
    }
  ]
}
```

### `GET /analysis/{dataset_id}/speeds`
Estadísticos de velocidad por movimiento y clase.

### `GET /analysis/{dataset_id}/conflicts`
Conflictos TTC/PET con severidad y geometría básica.

## Reportes

### `GET /reports/{dataset_id}/summary`
Genera CSV con conteos (se retorna como archivo para descarga).

### `GET /reports/{dataset_id}/excel`
Genera XLSX multi-hoja.

### `GET /reports/{dataset_id}/pdf`
Genera PDF basado en `templates/report.html`.

### `GET /reports/{dataset_id}/download/{filename}`
Descarga el archivo generado previamente (CSV/XLSX/PDF).

## Códigos de estado

- `200 OK`: solicitud exitosa.
- `201 Created`: dataset creado.
- `400 Bad Request`: error de validación (p.ej. PKL inválido).
- `404 Not Found`: dataset o recurso inexistente.
- `500 Internal Server Error`: fallo inesperado durante el procesamiento.

## Versionado de API

La versión actual es `v1`. Cambios breaking se documentarán en `docs/CHANGELOG.md`.
