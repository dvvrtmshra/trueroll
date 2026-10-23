from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/upload")
def upload_admissions():
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 2"})


@router.get("/uploads/{upload_id}")
def get_upload(upload_id: str):
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 2"})
