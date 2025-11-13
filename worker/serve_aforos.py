"""Aforos processing service (skeleton).
This FastAPI app exposes endpoints to enqueue PKL processing jobs,
check status, run validations and multiaforo. The heavy lifting
should be implemented in separate modules under worker/pipeline and
worker/jobs.
"""

from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

# TODO: import actual processing functions from pipeline and jobs modules

app = FastAPI(title="Aforos Processor", version="v1")

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "aforos", "version": "v1"}

@app.post("/api/v1/aforos/process/init")
def process_init(file: UploadFile):
    """Register a new PKL for processing. Returns a dataset identifier."""
    # TODO: store file to disk and return pkl_id
    return {"pkl_id": "pkl_12345678"}

@app.post("/api/v1/aforos/process/run")
def process_run(pkl_id: str, background_tasks: BackgroundTasks):
    """Start processing the PKL asynchronously."""
    # TODO: enqueue processing job
    job_id = f"job_{pkl_id}"
    return {"job_id": job_id}

@app.get("/api/v1/aforos/status/{job_id}")
def process_status(job_id: str):
    """Return current status of a processing or validation job."""
    # TODO: read job status from storage/redis
    return {"job_id": job_id, "state": "running", "progress": 0.0}

@app.post("/api/v1/aforos/validate")
def validate_runs(pkl: str, runs: int = 5):
    """Trigger multiple runs to estimate variability."""
    # TODO: enqueue validation job
    job_id = f"validate_{pkl}"
    return {"job_id": job_id}

@app.post("/api/v1/aforos/multiaforo")
def multiaforo(intersection_id: str, pkl_ids: list[str]):
    """Compute consensus of multiple PKL runs for the same intersection."""
    # TODO: enqueue multiaforo job
    job_id = f"multiaforo_{intersection_id}"
    return {"job_id": job_id}
