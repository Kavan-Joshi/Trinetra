import bcrypt
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from trinetra_core.config import settings
from trinetra_core.db import AuditRow, CameraRow, User, get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except ValueError:
        return False


def create_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


async def current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)) -> User:
    err = HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        payload = decode_token(token)
        username = payload.get("sub")
    except JWTError:
        raise err
    user = (await session.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if not user:
        raise err
    return user


def require_role(*roles: str):
    async def dep(user: User = Depends(current_user)) -> User:
        if user.role != "admin" and user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return dep


def department_scope(user: User) -> int | None:
    """Return the department id a user is scoped to, or None for global access."""
    return user.department_id


def apply_scope(stmt, user: User, camera_col):
    """Restrict a query to the user's department scope via a camera-id subquery.

    No-op for global users (admin / unscoped operators). For department-scoped
    users, filters rows whose ``camera_col`` references a camera owned by the
    user's department.
    """
    dept_id = department_scope(user)
    if dept_id is None:
        return stmt
    return stmt.where(camera_col.in_(select(CameraRow.id).where(CameraRow.department_id == dept_id)))


async def audit(session: AsyncSession, username: str, action: str, entity: str, details: dict | None = None) -> None:
    session.add(AuditRow(username=username, action=action, entity=entity, details=details or {}))


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    display_name: str
    username: str
    department_id: int | None = None


@router.post("/login", response_model=LoginResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    user = (await session.execute(select(User).where(User.username == form.username))).scalar_one_or_none()
    if not user or not verify_pw(form.password, user.pw_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return LoginResponse(
        access_token=create_token(user.username, user.role),
        token_type="bearer",
        role=user.role,
        display_name=user.display_name,
        username=user.username,
        department_id=user.department_id,
    )


@router.get("/me")
async def me(user: User = Depends(current_user)):
    return {"username": user.username, "role": user.role, "display_name": user.display_name, "department_id": user.department_id}
