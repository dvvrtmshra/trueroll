from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("")
def list_employers():
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 6"})


@router.post("")
def create_employer():
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 6"})
