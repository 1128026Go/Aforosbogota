"""API gateway service (skeleton).
This FastAPI app proxies requests to the worker service and handles dataset
configuration and storage. It aggregates results and serves reports.
"""
from fastapi import FastAPI
from api.routers import datasets, config, validate, multiaforo, reports
from api.routers import dataset_editor_temp
# TODO: Fix dataset_editor imports and re-enable
# from api.routers import dataset_editor

app = FastAPI(title="Bogotá Traffic API", version="v1")

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "api", "version": "v1"}

# Temporary endpoint to handle frontend datasets request while we fix the dataset_editor
@app.get("/api/editor/datasets/")
def get_datasets_temp():
    """Temporary endpoint to return empty datasets list"""
    return {"datasets": []}

# Include routers
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(config.router,    prefix="/api/v1/config", tags=["config"])
app.include_router(validate.router,  prefix="/api/v1/aforos",  tags=["validate"])
app.include_router(multiaforo.router,prefix="/api/v1/aforos",  tags=["multiaforo"])
app.include_router(reports.router,   prefix="/api/v1",         tags=["reports"])
app.include_router(dataset_editor_temp.router, tags=["dataset_editor_temp"])
# TODO: Re-enable once import issues are fixed
# app.include_router(dataset_editor.router, tags=["dataset_editor"])
