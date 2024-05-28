from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from wg_backend.api import exceptions
from wg_backend.core.security import get_password_hash, verify_password
from wg_backend.models.user import User
from wg_backend.schemas.user import UserCreate, UserUpdate


def create_user(*, session: Session, user_create: UserCreate) -> User | None:
    user_in = user_create.model_dump(exclude_none = True, exclude_unset = True)
    del user_in['password']
    user_in["hashed_password"] = get_password_hash(user_create.password)
    # db_obj = User(
    #     username=user_create.username,
    #     hashed_password=get_password_hash(user_create.password),
    #     is_superuser=user_create.is_superuser,
    #     email=user_create.email
    # )
    db_obj = User(**user_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    update_data = user_in.model_dump(exclude_unset = True, exclude_none = True)
    if "password" in update_data:
        password = update_data["password"]
        hashed_password = get_password_hash(password)
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    obj_data = jsonable_encoder(db_user)
    for field in obj_data:
        if field in update_data:
            setattr(db_user, field, update_data[field])
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_username(*, session: Session, username: str) -> User | None:
    data = session.query(User).where(User.username == username).one_or_none()
    # db_data = session.execute(stmt)
    return data


def get_user_by_email(*, session: Session, email: str) -> User | None:
    data = session.query(User).where(User.email == email).one_or_none()
    # db_data = session.execute(stmt)
    return data


def get_user_by_client_id(*, session: Session, client_id: str) -> User | None:
    stmt = session.query(User).where(User.client_id == client_id)
    db_data = session.execute(stmt)
    return db_data.scalar_one_or_none()


def authenticate(*, session: Session, username: str, password: str) -> User | None:
    db_user = get_user_by_username(session = session, username = username)
    if not db_user or not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def remove_user(session: Session, *, item_id: int) -> User:
    obj = session.query(User).get(item_id)
    if not obj:
        raise exceptions.not_found_error()
    session.delete(obj)
    # session.flush()
    return obj
