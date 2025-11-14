# Aforos Bogotá · Plataforma de análisis de intersecciones

Sistema completo para cargar trayectorias (PKL), configurar accesos cardinales y generar análisis avanzados (volúmenes RILSA, velocidades, conflictos TTC/PET) con exportación a CSV, Excel y PDF.

## Arquitectura

- **Backend**: FastAPI (`api/`) con cálculo de métricas, RILSA, filtros de trayectorias y generación de reportes.
- **Frontend**: React + Vite (`apps/web/`) con dashboard interactivo en la página de resultados.
- **Datos**: ficheros PKL normalizados en `data/<dataset_id>/`.

## Puesta en marcha rápida

### Backend

```bash
cd api
python -m venv ../venv
../venv/Scripts/activate  # En Windows
# source ../venv/bin/activate  # En Linux/Mac
pip install -r requirements.txt
uvicorn api.main:app --reload
```

El backend estará disponible en `http://localhost:8000` y la documentación interactiva en `http://localhost:8000/docs`.

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

El frontend estará disponible en `http://localhost:5173` (o el puerto que Vite asigne).

### Tests backend

```bash
cd api
pytest ../tests/test_analysis_services.py -v
```

## Endpoints principales

| Ruta | Descripción |
|------|-------------|
| `POST /api/v1/datasets/upload` | Sube un PKL y crea el dataset (almacena `raw.pkl`). |
| `GET /api/v1/datasets` | Lista todos los datasets disponibles. |
| `POST /api/v1/config/{id}/cardinals` | Configura accesos cardinales del dataset. |
| `GET /api/v1/analysis/{id}/volumes` | Tabla por intervalo y movimiento (`VolumesResponse`). |
| `GET /api/v1/analysis/{id}/speeds` | Estadísticos de velocidad por movimiento/clase. |
| `GET /api/v1/analysis/{id}/conflicts` | Conflictos TTC/PET con severidad. |
| `GET /api/v1/reports/{id}/summary` | Genera CSV (`interval_start`, `rilsa_code`, `vehicle_class`, `count`). |
| `GET /api/v1/reports/{id}/excel` | Genera XLSX (hoja `Totales` + `Mov_<código>`). |
| `GET /api/v1/reports/{id}/pdf` | Genera PDF (tablas, velocidades, conflictos). |
| `GET /api/v1/reports/{id}/download/{file}` | Descarga el archivo recién generado. |

Parámetros relevantes: `interval_minutes`, `fps`, `pixel_to_meter`, `ttc_threshold`, `distance_threshold`.

## Flujo en la UI

1. **Subir PKL**: `UploadPage` crea el dataset y guarda la metadata mínima.
2. **Configurar accesos**: `DatasetConfigPage` permite ajustar cardinales y reglas RILSA.
3. **Resultados**: `ResultsPage` muestra:
   - Tabla de volúmenes con filtros por categoría.
   - Gráfico comparativo de velocidades (media / p85 / máximo).
   - Mapa con conflictos TTC/PET.
   - Botones de descarga para CSV, Excel y PDF (consume los endpoints reales).

## Estructura del proyecto

```
aforos/
├── README.md
├── .gitignore
├── docker-compose.yml
├── Dockerfile.api
├── docs/
│   ├── CHANGELOG.md
│   └── legacy/          # Documentación histórica
├── api/
│   ├── main.py
│   ├── requirements.txt
│   ├── routers/         # datasets, config, reports, analysis
│   ├── services/        # filtros, RILSA, velocidades, conflictos, reportes
│   ├── models/          # Schemas Pydantic
│   └── templates/       # report.html para PDF
├── apps/
│   └── web/
│       ├── package.json
│       └── src/
│           ├── main.tsx
│           ├── App.tsx
│           ├── lib/api.ts      # Cliente HTTP unificado
│           ├── types/index.ts  # Tipos compartidos
│           ├── components/     # StepNavigation, paneles de resultados
│           └── pages/         # UploadPage, DatasetConfigPage, ResultsPage
└── tests/
    └── test_analysis_services.py
```

## Exportaciones

- **CSV**: resultados de `calculate_counts_by_interval` con columnas `interval_start`, `rilsa_code`, `vehicle_class`, `count`.
- **Excel**: multi-hoja con `Totales` (resumen) y `Mov_<código>` (detalle por movimiento RILSA).
- **PDF**: plantilla HTML → WeasyPrint con resumen de volúmenes, velocidades y conflictos.

## Troubleshooting

- **Dependencias PDF**: WeasyPrint requiere librerías del sistema (Cairo, Pango). Instálalas antes de generar PDFs.
- **Datos de ejemplo**: coloca PKL normalizados en `data/<dataset_id>/`. La app asumirá `normalized.parquet` en esa carpeta después del pipeline de ingestión.
- **Pruebas**: utiliza `tests/test_analysis_services.py` como base para validar nuevas funciones de análisis.

## Desarrollo

### Agregar nuevos endpoints

1. Crear router en `api/routers/`
2. Registrar en `api/main.py`
3. Actualizar `apps/web/src/lib/api.ts` con el nuevo endpoint
4. Agregar tipos en `apps/web/src/types/index.ts` si es necesario

### Agregar nuevos análisis

1. Implementar servicio en `api/services/`
2. Agregar router en `api/routers/analysis.py`
3. Actualizar frontend para consumir el nuevo endpoint
4. Agregar tests en `tests/`

## Licencia

Desarrollado para análisis de tráfico vehicular.
