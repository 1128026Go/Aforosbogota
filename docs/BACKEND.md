# Backend (FastAPI)

## Dependencias

```bash
cd api
python -m venv ../venv
../venv/Scripts/activate  # Windows
# source ../venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## Estructura

- `main.py`: punto de entrada de la app FastAPI.
- `routers/`: endpoints agrupados (`datasets`, `config`, `analysis`, `reports`).
- `services/`: lógica de negocio (RILSA, velocidades, conflictos, exportaciones, filtros, settings).
- `templates/`: plantillas HTML (por ejemplo, `report.html` para PDF).
- `data/<dataset_id>/analysis_settings.json`: settings avanzados persistidos por dataset.
- `data/<dataset_id>/reports/`: exportaciones CSV/Excel/PDF generadas a demanda.

## Ejecutar servidor de desarrollo

```bash
cd api
uvicorn api.main:app --reload
```

Servirá la API en `http://localhost:8000` con documentación en `/docs`.

## Routers activos

- `datasets`: subida de PKL, listado y metadatos.
- `config`: gestión de accesos cardinales, reglas RILSA, **analysis_settings** y **forbidden_movements**.
- `analysis`: volúmenes, velocidades, conflictos TTC/PET y **violaciones**.
- `reports`: exportaciones CSV, Excel y PDF enriquecido.

### Endpoints clave de configuración

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/config/{id}/analysis_settings` | Obtiene la configuración avanzada (intervalos, filtros y TTC). |
| `PUT` | `/api/v1/config/{id}/analysis_settings` | Actualiza y persiste la configuración avanzada. |
| `GET` | `/api/v1/config/{id}/forbidden_movements` | Lista los movimientos RILSA marcados como prohibidos. |
| `PUT` | `/api/v1/config/{id}/forbidden_movements` | Guarda la lista de movimientos prohibidos. |

### Endpoints clave de análisis

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/analysis/{id}/volumes` | Volúmenes consolidados usando los settings actuales. |
| `GET` | `/api/v1/analysis/{id}/speeds` | Estadísticos de velocidad por movimiento/clase. |
| `GET` | `/api/v1/analysis/{id}/conflicts` | Conflictos TTC/PET filtrados por el umbral configurado. |
| `GET` | `/api/v1/analysis/{id}/violations` | Conteo de maniobras indebidas contra la lista de movimientos prohibidos. |

## Pruebas

```bash
cd api
pytest api/tests -v
```

Las pruebas cubren filtros, cálculos de volúmenes, velocidades, conflictos, violaciones y endpoints HTTP (routers + exportaciones).

## Configuración de entorno

Variables relevantes:

- `API_STORAGE_DIR`: carpeta donde se guardan los datasets procesados (opcional).
- `WEASYPRINT_BASEURL`: base para recursos estáticos del PDF (opcional).

### Consideraciones para CI

El workflow `.github/workflows/ci.yml` ejecuta:

1. Instalación de dependencias del sistema para WeasyPrint (Ubuntu/Cairo/Pango).
2. `pytest api/tests -v`.
3. `npm install && npm run build` para el frontend.

Para entornos sin soporte gráfico, puedes saltar los tests de PDF ejecutando `pytest -m "not pdf"` tras marcar los tests con `@pytest.mark.pdf`.
