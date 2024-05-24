from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from pydantic import ValidationError

from wg_backend.api import exceptions
from wg_backend.core.settings import get_settings
from wg_backend.crud import crud_user_fn
from wg_backend.db import SessionDep
from wg_backend.models import User
from wg_backend.schemas import TokenData

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl = f"/api/v1/login/access-token",
    # scheme_name=settings.ACCESS_TOKEN_KEY_NAME,
    scopes = {"me": "Read information about the current user.", "peers": "Read peers."},
)


async def get_current_user(
        security_scopes: SecurityScopes,
        token: Annotated[str, Depends(oauth2_scheme)],
        session: SessionDep,
) -> User:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = exceptions.credentials_not_valid(authenticate_value)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms = [settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes = token_scopes, sub = username)
        # token_data = schemas.TokenData(**payload)
    except (jwt.JWTError, ValidationError):
        raise credentials_exception
    user = crud_user_fn.get_user_by_username(session = session, username = token_data.sub)
    # user = session.get(User, token_data.sub)
    if not user:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = "Not enough permissions",
                headers = {"WWW-Authenticate": authenticate_value},
            )
    session.close()
    return user


async def get_current_active_user(
        current_user: Annotated[User, Security(get_current_user, scopes = ["me"])],
) -> User:
    if not current_user.is_active:
        raise exceptions.inactive_user()
    return current_user


async def get_current_active_superuser(
        current_user: Annotated[User, Security(get_current_user, scopes = ["me"])],
) -> User:
    if not current_user.is_superuser:
        raise exceptions.not_superuser()
    return current_user


CurrentUser = Annotated[User, Depends(get_current_active_user)]
SUDOCurrentUser = Annotated[User, Depends(get_current_active_superuser)]
