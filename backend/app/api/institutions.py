from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("")
def list_institutions():
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 1"})


@router.get("/{institution_id}")
def get_institution(institution_id: str):
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 1"})


@router.get("/{institution_id}/courses")
def list_courses(institution_id: str):
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 1"})
