from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.account.models import User
from app.account.schemas import (
    UserCreate, UserLogin, UserUpdate,
    PasswordChangeRequest, PasswordResetEmailRequest, PasswordResetRequest
)
from app.account.utils import (
    hash_password, verify_password,
    create_email_verification_token, create_password_reset_token,
    verify_email_token_and_get_user_id,
    get_user_by_email, get_user_by_username, get_user_by_id
)



async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    if await get_user_by_email(session, user_data.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if await get_user_by_username(session, user_data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password)
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def authenticate_user(session: AsyncSession, login_data: UserLogin) -> User | None:
    user = await get_user_by_email(session, login_data.email)
    if not user or not verify_password(login_data.password, user.hashed_password):
        return None
    return user


async def update_user(session: AsyncSession, user_id: int, data: UserUpdate) -> User:

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing = await get_user_by_email(session, update_data["email"])
        if existing and existing.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if "username" in update_data:
        existing = await get_user_by_username(session, update_data["username"])
        if existing and existing.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Имя пользователя уже занято")

    for field, value in update_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


async def deactivate_user(session: AsyncSession, user_id: int) -> User:

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    user.is_active = False
    await session.commit()
    await session.refresh(user)
    return user


# --- Верификация email ---

async def send_verification_email(user: User):
    token = create_email_verification_token(user.id)
    link = f"http://localhost:8000/account/verify-email?token={token}"
    print(f" Подтвердите адрес электронной почты: {link}")
    return {"msg": "Письмо для подтверждения отправлено", "link": link}


async def verify_email(session: AsyncSession, token: str):
    user_id = verify_email_token_and_get_user_id(token, "verify_email")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный или истекший токен")

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user.is_verified = True
    await session.commit()
    return {"msg": "Адрес электронной почты успешно подтвержден."}

async def change_password(session: AsyncSession, user: User, data: PasswordChangeRequest):
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Старый пароль неверен")
    user.hashed_password = hash_password(data.new_password)
    await session.commit()


async def send_password_reset_email(session: AsyncSession, data: PasswordResetEmailRequest):
    user = await get_user_by_email(session, data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    token = create_password_reset_token(user.id)
    link = f"http://localhost:8000/account/reset-password?token={token}"
    print(f"🔗 Reset password: {link}")
    return {"msg": "Ссылка для сброса пароля отправлена", "link": link}


async def reset_password(session: AsyncSession, data: PasswordResetRequest):
    user_id = verify_email_token_and_get_user_id(data.token, "password_reset")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный или истекший токен")

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user.hashed_password = hash_password(data.new_password)
    await session.commit()
    return {"msg": "Пароль успешно сброшен"}