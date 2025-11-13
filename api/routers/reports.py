from fastapi import APIRouter

router = APIRouter()

@router.get("/aforos/{pkl_id}/final")
def final_report(pkl_id: str):
    # TODO: return final aggregated data
    return {"pkl_id": pkl_id}

@router.post("/reports/pdf")
def create_pdf(pkl_id: str):
    # TODO: generate PDF using pdf_builder
    return {"pkl_id": pkl_id, "pdf": "/reports/file.pdf"}
