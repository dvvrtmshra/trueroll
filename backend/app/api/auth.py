from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    verify_mock_otp,
)
from app.core.audit import append_audit_entry
from app.core.clock import app_now
from app.models.user import User

router = APIRouter()


class OtpRequest(BaseModel):
    email: str


class OtpVerify(BaseModel):
    email: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/request-otp", status_code=204)
def request_otp(body: OtpRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user:
        # Return 204 regardless so as not to leak existence
        return
    # Mock: OTP is always 123456 — no real delivery
    return


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(body: OtpVerify, db: Session = Depends(get_db)):
    if not verify_mock_otp(body.otp):
        raise HTTPException(status_code=401, detail="Invalid OTP")
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid OTP")
    token = create_access_token({"sub": user.id, "role": user.role, "email": user.email})
    append_audit_entry(db, actor=user.email, role=user.role, action="LOGIN",
                       object_type="User", object_id=user.id, time=app_now(db))
    return TokenResponse(access_token=token)


@router.get("/me")
def me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "region": user.region,
        "institution_id": user.institution_id,
        "student_id": user.student_id,
        "employer_id": user.employer_id,
    }
