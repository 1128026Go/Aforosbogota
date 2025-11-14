# Changelog

## 2025-11-14 – Limpieza de legado & segunda ola de mejoras

- Eliminado código desktop y scripts antiguos (traffic_analyzer, aforo-analysis, builds, .exe, etc.)
- Repositorio reducido a API FastAPI + frontend React + tests de análisis
- Documentación legacy movida a `docs/legacy/`
- Estructura minimalista: solo `api/`, `apps/web/`, `tests/`, `docs/`

### Eliminado
- Directorios: `traffic_analyzer/`, `aforo-analysis/`, `dist/`, `dist_backup/`, `build/`, `venv/`
- Scripts legacy: `*.bat`, `*.sh`, `*.spec`, scripts GUI antiguos
- `requirements.txt` en raíz (duplicado, ahora solo `api/requirements.txt`)
- Documentación obsoleta movida a `docs/legacy/`

### Conservado
- Backend FastAPI completo (`api/`)
- Frontend React moderno (`apps/web/`)
- Tests de análisis (`tests/`)
- Documentación activa (`README.md`, `docs/`)

### Añadido / Mejorado
- `AnalysisSettings` persistidos por dataset (`analysis_settings.json`) y endpoints `GET/PUT /config/{id}/analysis_settings`.
- `ForbiddenMovement` y endpoints `GET/PUT /config/{id}/forbidden_movements`.
- Nuevo servicio y endpoint `GET /analysis/{id}/violations` para maniobras indebidas.
- Reporte PDF enriquecido con portada, resumen ejecutivo (volúmenes, velocidades, conflictos, violaciones) y tablas agregadas.
- Frontend: pestaña de configuración avanzada, panel de maniobras indebidas, gráficos de volúmenes/velocidades con Recharts y heatmap de conflictos con slider TTC.
- Client API unificado (`lib/api.ts`) con métodos para settings, violaciones y descargas actualizadas.
- Tests adicionales (`tests/test_analysis_api.py`) cubriendo endpoints REST y exportaciones.
- Workflow de CI (`.github/workflows/ci.yml`) con jobs backend (pytest) y frontend (npm build).

### Verificación
- `pytest ../tests/test_analysis_services.py -v`
- `pytest api/tests -v`
- `npm run build`

