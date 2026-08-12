
import uuid
from datetime import datetime, timedelta, timezone
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.account.models import User, RefreshToken


JWT_SECRET_KEY = "6b9f4a13d8e52c7a10fbc34d28e901fa62b35c4e7d8f9a0b1c2d3e4f5a6b7c8d"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_TIME_MIN = 30
JWT_REFRESH_TOKEN_TIME_DAY = 7
EMAIL_VERIFICATION_TOKEN_TIME_HOUR = 24
EMAIL_PASSWORD_RESET_TOKEN_TIME_HOUR = 1


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT токены ---
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_TIME_MIN)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except (ExpiredSignatureError, JWTError):
        return None


async def create_tokens(session: AsyncSession, user: User) -> dict:

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token_str = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_TIME_DAY)

    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=expires_at
    )
    session.add(refresh_token)
    await session.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


async def verify_refresh_token(session: AsyncSession, token: str) -> User | None:
    stmt = select(RefreshToken).where(RefreshToken.token == token)
    result = await session.scalars(stmt)
    db_token = result.first()

    if db_token and not db_token.revoked and db_token.expires_at > datetime.now(timezone.utc):
        stmt = select(User).where(User.id == db_token.user_id)
        result = await session.scalars(stmt)
        return result.first()
    return None


async def revoke_refresh_token(session: AsyncSession, token: str) -> None:
    stmt = select(RefreshToken).where(RefreshToken.token == token)
    result = await session.scalars(stmt)
    db_token = result.first()
    if db_token:
        db_token.revoked = True
        await session.commit()


def create_email_verification_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=EMAIL_VERIFICATION_TOKEN_TIME_HOUR)
    payload = {"sub": str(user_id), "type": "verify_email", "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_password_reset_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=EMAIL_PASSWORD_RESET_TOKEN_TIME_HOUR)
    payload = {"sub": str(user_id), "type": "password_reset", "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_email_token_and_get_user_id(token: str, token_type: str) -> int | None:
    payload = decode_token(token)
    if not payload or payload.get("type") != token_type:
        return None
    try:
        return int(payload.get("sub"))
    except (TypeError, ValueError):
        return None


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.scalars(stmt)
    return result.first()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    result = await session.scalars(stmt)
    return result.first()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await session.scalars(stmt)
    return result.first()