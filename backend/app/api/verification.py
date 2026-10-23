from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("")
def verify_credential():
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 6"})
