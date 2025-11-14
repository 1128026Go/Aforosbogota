# Changelog

## 2025-11-14 – Limpieza de legado

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

### Verificación
- `pytest ../tests/test_analysis_services.py -v`
- `npm run build`

