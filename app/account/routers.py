from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse

from app.db.config import SessionDep
from app.account.schemas import (
    UserCreate, UserOut, UserLogin, UserUpdate,
    PasswordChangeRequest, PasswordResetEmailRequest, PasswordResetRequest,
    Token
)
from app.account.services import (
    create_user, authenticate_user, update_user, deactivate_user,
    send_verification_email, verify_email,
    change_password, send_password_reset_email, reset_password
)
from app.account.utils import create_tokens, revoke_refresh_token, verify_refresh_token
from app.account.models import User
from app.account.deps import get_current_user, get_current_active_user, require_admin

router = APIRouter()


@router.post("/register", response_model=UserOut)
async def register(session: SessionDep, user_data: UserCreate):
    return await create_user(session, user_data)


@router.post("/login", response_model=Token)
async def login(session: SessionDep, login_data: UserLogin):
    user = await authenticate_user(session, login_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    tokens = await create_tokens(session, user)
    response = JSONResponse(content={
        "access_token": tokens["access_token"],
        "token_type": "bearer"
    })
    response.set_cookie("access_token", tokens["access_token"], httponly=True, secure=False, samesite="lax", max_age=60*60*24)
    response.set_cookie("refresh_token", tokens["refresh_token"], httponly=True, secure=False, samesite="lax", max_age=60*60*24*7)
    return response


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
async def update_me(session: SessionDep, data: UserUpdate, user: User = Depends(get_current_user)):
    return await update_user(session, user.id, data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(session: SessionDep, user: User = Depends(get_current_user)):
    await deactivate_user(session, user.id)
    return None


@router.post("/refresh")
async def refresh_token(session: SessionDep, request: Request):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Отсутствует токен обновления")

    user = await verify_refresh_token(session, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный или просроченный токен обновления")

    await revoke_refresh_token(session, token)
    tokens = await create_tokens(session, user)

    response = JSONResponse(content={"message": "Token refreshed"})
    response.set_cookie("access_token", tokens["access_token"], httponly=True, secure=False, samesite="lax", max_age=60*60*24)
    response.set_cookie("refresh_token", tokens["refresh_token"], httponly=True, secure=False, samesite="lax", max_age=60*60*24*7)
    return response


@router.post("/logout")
async def logout(session: SessionDep, request: Request, user: User = Depends(get_current_user)):
    token = request.cookies.get("refresh_token")
    if token:
        await revoke_refresh_token(session, token)

    response = JSONResponse(content={"detail": "Logged out"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.post("/send-verification-email")
async def send_verify_email(user: User = Depends(get_current_user)):
    return await send_verification_email(user)


@router.get("/verify-email")
async def verify_email_endpoint(session: SessionDep, token: str):
    return await verify_email(session, token)


@router.post("/change-password")
async def change_password_endpoint(session: SessionDep, data: PasswordChangeRequest, user: User = Depends(get_current_user)):
    await change_password(session, user, data)
    return {"msg": "Password changed successfully"}


@router.post("/send-password-reset-email")
async def send_reset_email(session: SessionDep, data: PasswordResetEmailRequest):
    return await send_password_reset_email(session, data)


@router.post("/reset-password")
async def reset_password_endpoint(session: SessionDep, data: PasswordResetRequest):
    return await reset_password(session, data)


@router.get("/admin")
async def admin_panel(user: User = Depends(require_admin)):
    return {"msg": f"Welcome Admin {user.email}"}