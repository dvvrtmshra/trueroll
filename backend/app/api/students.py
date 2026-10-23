from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("")
def list_students():
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 2"})


@router.post("")
def create_student():
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 2"})


@router.get("/{student_id}")
def get_student(student_id: str):
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 2"})
