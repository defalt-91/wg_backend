from typing import Annotated

from fastapi import Depends, HTTPException, WebSocket, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.db.session import get_session
from app.core.Settings import get_settings

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/api/v1/login/access-token",
    scopes={"me": "Read information about the current user.", "items": "Read items."},
)


async def get_current_user(
        security_scopes: SecurityScopes,
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Session = Depends(get_session),
) -> models.User:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = schemas.TokenData(scopes=token_scopes, sub=username)
        # token_data = schemas.TokenData(**payload)
    except (jwt.JWTError, ValidationError):
        raise credentials_exception
    user = crud.user.get_by_username(db, username=token_data.sub)
    if not user:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


async def get_current_active_user(
        current_user: Annotated[models.User, Security(get_current_user, scopes=["me"])],
) -> models.User:
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
        current_user: Annotated[models.User, Security(get_current_user, scopes=["me"])],
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(status_code=400, detail="The user doesn't have enough privileges")
    return current_user


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, data: list[dict], websocket: WebSocket):
        await websocket.send_json(data)

    async def broadcast(self, data: list[dict]):
        for connection in self.active_connections:
            await connection.send_json(data)
