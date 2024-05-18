from datetime import timedelta
from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestFormStrict
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.models import User
from app.schemas.token import Token
from app.db.session import get_session
from app.core.security import create_access_token
from app.schemas.user import UserOut
from app.api.exceptions import inactive_user
from app.crud import crud_user as crud
router = APIRouter()


@router.post("/login/access-token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestFormStrict, Depends()],
        db: Session = Depends(get_session),
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db,
        username=form_data.username,
        password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not crud.user.is_active(user):
        raise inactive_user()
    access_token_expires = timedelta(minutes=180)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer",scopes=' '.join(form_data.scopes))


@router.post(
    "/login/test-token",
    response_model=UserOut,
)
async def test_token(
        current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Test access token
    """
    return current_user
