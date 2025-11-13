from fastapi import APIRouter

router = APIRouter()

@router.post("/multiaforo")
def multiaforo(intersection_id: str, pkl_ids: list[str]):
    # TODO: proxy call to aforos service
    return {"job_id": f"multiaforo_{intersection_id}"}
