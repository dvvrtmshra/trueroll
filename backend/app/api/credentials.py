from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/issue")
def issue_credential():
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 6"})


@router.get("/{credential_id}")
def get_credential(credential_id: str):
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 6"})


@router.post("/{credential_id}/revoke")
def revoke_credential(credential_id: str):
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 6"})
