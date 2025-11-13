from fastapi import APIRouter

router = APIRouter()

@router.post("/validate")
def validate_runs(pkl_id: str, runs: int = 5):
    # TODO: proxy call to aforos service
    return {"job_id": f"validate_{pkl_id}"}
