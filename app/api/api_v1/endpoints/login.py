import datetime
from datetime import timedelta, datetime, UTC
from typing import Any, Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestFormStrict

from app.api import exceptions as ex
from app.api.deps import get_current_active_superuser, CurrentUser
from app.api.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)
from app.core.Settings import get_settings
from app.core.security import create_access_token
from app.crud.crud_user_fn import authenticate, get_user_by_email, \
    get_password_hash, get_user_by_username
from app.db.session import SessionDep
from app.schemas.token import Token, Message, NewPassword
from app.schemas.user import UserOut

settings = get_settings()
router = APIRouter()


@router.post("/login/access-token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestFormStrict, Depends()],
        db: SessionDep,
        response: Response
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate(
        session=db,
        username=form_data.username,
        password=form_data.password
    )
    if not user:
        raise ex.incorrect_username_or_password()
    elif not user.is_active:
        raise ex.inactive_user()
    access_token_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes},
        expires_delta=access_token_expires
    )
    # """ authorization with cookies"""
    # response.set_cookie(
    #     value=access_token,
    #     key=settings.ACCESS_TOKEN_KEY_NAME,
    #     domain=settings.DOMAIN,
    #     path="/",
    #     expires=datetime.now(UTC) + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    #     httponly=True,
    #     secure=False,
    #     samesite="strict",
    #     # max_age=30,
    # )
    return Token(
        access_token=access_token,
        token_type="bearer",
        # scopes=' '.join(form_data.scopes)
    )


@router.post(
    "/login/test-token",
    response_model=UserOut,
)
async def test_token(
        current_user: CurrentUser,
) -> Any:
    """
    Test access token
    """
    return current_user


from pydantic import EmailStr
from fastapi import Path


@router.post("/password-recovery/{email}",
    operation_id="some_specific_id_you_define", response_model=Message)
async def recover_password(session: SessionDep, email: Annotated[EmailStr, Path(title="requested user email address")]) -> Message:
    """
    Password Recovery
    """
    # if email is None:
    #     user = get_user_by_username(session=session, username=username)
    # else:
    user = get_user_by_email(session=session, email=email)
    if not user:
        raise ex.user_not_exist_email()
    if user and not user.email:
        raise ex.user_without_email()
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise ex.invalid_token()
    user = get_user_by_email(session=session, email=email)
    if not user:
        raise ex.user_not_exist_email()
    elif not user.is_active:
        raise ex.inactive_user()
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,

)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = get_user_by_email(session=session, email=email)

    if not user:
        raise ex.user_not_exist_username()
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )
