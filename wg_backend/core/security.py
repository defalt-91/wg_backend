from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from wg_backend.core.settings import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")


def create_access_token(
        data: dict[str, str | datetime],
        expires_delta: timedelta = None,
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes = 180)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm = settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
