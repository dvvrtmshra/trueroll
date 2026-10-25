from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api import auth, institutions, students, admissions, rules, flags, credentials, reports, verification, audit, employers, admin, evaluations, uploads, simulator, matching, ledger, stream, activity, dashboard, priorities, anomaly, consents, public_verify


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="TrueRoll",
    description="APAAR-based student data management — SAMPLE DATA ONLY",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(institutions.router, prefix="/institutions", tags=["institutions"])
app.include_router(students.router, prefix="/students", tags=["students"])
app.include_router(admissions.router, prefix="/admissions", tags=["admissions"])
app.include_router(rules.router, prefix="/rules", tags=["rules"])
app.include_router(flags.router, prefix="/flags", tags=["flags"])
app.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(verification.router, prefix="/verify", tags=["verification"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])
app.include_router(employers.router, prefix="/employers", tags=["employers"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
app.include_router(uploads.router, prefix="/institutions", tags=["uploads"])
app.include_router(simulator.router, prefix="/sim", tags=["simulator"])
app.include_router(matching.router, prefix="/matching", tags=["matching"])
app.include_router(ledger.router, prefix="/ledger", tags=["ledger"])
app.include_router(stream.router, prefix="/stream", tags=["stream"])
app.include_router(activity.router, prefix="/activity", tags=["activity"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(priorities.router, prefix="/priorities", tags=["priorities"])
app.include_router(anomaly.router, prefix="/anomaly", tags=["anomaly"])
app.include_router(consents.router, prefix="/consents", tags=["consents"])
app.include_router(public_verify.router, prefix="/v", tags=["public"])


@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": settings.DEMO_MODE}
