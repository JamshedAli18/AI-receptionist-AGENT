from fastapi import APIRouter, HTTPException, Cookie, Response, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.config import ADMIN_PASSWORD
from app.services.admin_auth import create_admin_token, verify_admin_token
from app.db.mongo import get_patients_collection, get_appointments_collection, get_escalations_collection

router = APIRouter(prefix="/admin/api", tags=["admin"])

COOKIE_NAME = "admin_session"


class LoginRequest(BaseModel):
    password: str


def require_admin(admin_session: str | None = Cookie(default=None)):
    if not admin_session or not verify_admin_token(admin_session):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True


@router.post("/login")
def login(body: LoginRequest, response: Response):
    if not ADMIN_PASSWORD or body.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_admin_token()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24,  # 24 hours, matches token expiry
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"status": "ok"}


@router.get("/check")
def check_auth(admin_session: str | None = Cookie(default=None)):
    authenticated = bool(admin_session and verify_admin_token(admin_session))
    return {"authenticated": authenticated}


def _serialize(doc: dict) -> dict:
    """Converts MongoDB ObjectId and datetime fields to JSON-safe strings."""
    result = {}
    for k, v in doc.items():
        if k == "_id":
            result["id"] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, list):
            result[k] = [
                {kk: (vv.isoformat() if isinstance(vv, datetime) else vv) for kk, vv in item.items()}
                if isinstance(item, dict) else item
                for item in v
            ]
        else:
            result[k] = v
    return result


@router.get("/stats")
def get_stats(_: bool = Depends(require_admin)):
    appointments = get_appointments_collection()
    escalations = get_escalations_collection()
    patients = get_patients_collection()

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    total_bookings = appointments.count_documents({})
    upcoming = appointments.count_documents({"status": {"$in": ["booked", "rescheduled"]}, "scheduled_time": {"$gte": now}})
    cancelled = appointments.count_documents({"status": "cancelled"})
    escalations_this_week = escalations.count_documents({"timestamp": {"$gte": week_ago}})
    total_patients = patients.count_documents({})

    cancellation_rate = round((cancelled / total_bookings * 100), 1) if total_bookings else 0

    return {
        "total_bookings": total_bookings,
        "upcoming_appointments": upcoming,
        "cancelled_appointments": cancelled,
        "cancellation_rate": cancellation_rate,
        "escalations_this_week": escalations_this_week,
        "total_patients": total_patients,
    }


@router.get("/appointments")
def list_appointments(_: bool = Depends(require_admin), limit: int = 100):
    appointments = get_appointments_collection()
    docs = appointments.find().sort("created_at", -1).limit(limit)
    return [_serialize(doc) for doc in docs]


@router.get("/patients")
def list_patients(_: bool = Depends(require_admin), limit: int = 100):
    patients = get_patients_collection()
    docs = patients.find().sort("last_seen", -1).limit(limit)
    return [_serialize(doc) for doc in docs]


@router.get("/escalations")
def list_escalations(_: bool = Depends(require_admin), limit: int = 100):
    escalations = get_escalations_collection()
    docs = escalations.find().sort("timestamp", -1).limit(limit)
    return [_serialize(doc) for doc in docs]



    