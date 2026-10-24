"""Upload endpoints — institution upload pipeline."""
import asyncio
import hashlib
import io
import json
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core import events as event_bus
from app.core.clock import app_now
from app.core.database import get_db
from app.core.security import require_roles
from app.models.institution import Institution
from app.models.upload import Upload
from app.models.upload_error import UploadError
from app.services.ingestion import process_upload

router = APIRouter()


def _auth_college(user: dict, institution_id: str) -> None:
    if user.get("role") == "SYSTEM_ADMIN":
        return
    if user.get("institution_id") != institution_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Access denied to this institution"},
        )


@router.post("/{institution_id}/uploads", status_code=201)
async def upload_students(
    institution_id: str,
    file: UploadFile = File(...),
    course_code: str = Form(...),
    academic_year: str = Form("2026-27"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("COLLEGE_ADMIN", "SYSTEM_ADMIN")),
):
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    _auth_college(user, institution_id)

    raw = await file.read()
    file_hash = hashlib.sha256(raw).hexdigest()

    existing = db.query(Upload).filter(
        Upload.institution_id == institution_id,
        Upload.academic_year == academic_year,
        Upload.file_hash == file_hash,
    ).first()
    if existing:
        return {
            "upload_id": existing.id,
            "status": existing.status,
            "idempotent": True,
            "rows_total": existing.row_count,
            "rows_accepted": existing.rows_accepted,
            "rows_error": existing.error_count,
        }

    upload = Upload(
        institution_id=institution_id,
        uploaded_by=user.get("user_id", "unknown"),
        filename=file.filename or "upload.csv",
        academic_year=academic_year,
        course_approval_id=course_code,
        idempotency_key=idempotency_key,
        file_hash=file_hash,
        status="pending",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    demo_d = app_now(db).date()
    summary = process_upload(
        db, upload.id, institution_id, academic_year, raw,
        uploader_id=user.get("user_id", "unknown"),
        demo_date=demo_d,
    )

    asyncio.create_task(event_bus.publish({
        "type": "upload_finished",
        "institution_id": institution_id,
        "institution_name": inst.name,
        "rows_accepted": summary.get("rows_accepted", 0),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }))

    return {
        "upload_id": upload.id,
        "status": "done",
        **summary,
        "errors_csv": f"/institutions/{institution_id}/uploads/{upload.id}/errors.csv",
    }


@router.get("/{institution_id}/uploads/{upload_id}")
def get_upload_status(
    institution_id: str,
    upload_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("COLLEGE_ADMIN", "NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.institution_id == institution_id,
    ).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return {
        "upload_id": upload.id,
        "status": upload.status,
        "rows_total": upload.row_count,
        "rows_accepted": upload.rows_accepted,
        "rows_error": upload.error_count,
        "rows_warning": upload.rows_warning,
        "identity_tiers": json.loads(upload.identity_tiers or "{}"),
        "duplicates": json.loads(upload.duplicates_summary or "{}"),
        "ledger": json.loads(upload.ledger_results or "[]"),
    }


@router.get("/{institution_id}/uploads/{upload_id}/errors.csv")
def get_upload_errors_csv(
    institution_id: str,
    upload_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("COLLEGE_ADMIN", "NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    errors = db.query(UploadError).filter(UploadError.upload_id == upload_id).all()
    lines = ["row_number,field,error_code,message"]
    for e in errors:
        msg = e.message.replace('"', '""')
        lines.append(f'{e.row_number or ""},"{e.field or ""}",{e.error_code},"{msg}"')
    content = "\n".join(lines)
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=errors_{upload_id}.csv"},
    )
