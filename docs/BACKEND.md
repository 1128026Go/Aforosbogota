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
- `services/`: lógica de negocio (RILSA, velocidades, conflictos, exportaciones, filtros).
- `models/`: modelos Pydantic compartidos.
- `templates/`: plantillas HTML (por ejemplo, `report.html` para PDF).

## Ejecutar servidor de desarrollo

```bash
cd api
uvicorn api.main:app --reload
```

Servirá la API en `http://localhost:8000` con documentación en `/docs`.

## Routers activos

- `datasets`: subida de PKL, listado y metadatos.
- `config`: gestión de accesos cardinales y reglas RILSA.
- `analysis`: volúmenes, velocidades y conflictos calculados.
- `reports`: exportaciones CSV, Excel y PDF.

## Pruebas

```bash
cd api
pytest ../tests/test_analysis_services.py -v
```

Las pruebas cubren filtros, cálculos de volúmenes, velocidades, conflictos y generación de reportes.

## Configuración
de entorno

Variables relevantes:

- `API_STORAGE_DIR`: carpeta donde se guardan los datasets procesados (opcional).
- `WEASYPRINT_BASEURL`: base para recursos estáticos del PDF (opcional).

Si usas Docker, revisa `Dockerfile.api` y `docker-compose.yml` para variables adicionales.
