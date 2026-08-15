import jwt
from datetime import datetime, timedelta, timezone
from app.config import ADMIN_JWT_SECRET

TOKEN_EXPIRY_HOURS = 24


def create_admin_token() -> str:
    payload = {
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, ADMIN_JWT_SECRET, algorithm="HS256")


def verify_admin_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=["HS256"])
        return payload.get("role") == "admin"
    except jwt.PyJWTError:
        return False