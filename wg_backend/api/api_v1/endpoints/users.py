from typing import Any, List

from fastapi import APIRouter, Depends, Form
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr
from wg_backend.api import exceptions
from wg_backend.api.deps import CurrentUser, get_current_active_superuser, get_current_active_user
from wg_backend.crud.crud_user_fn import (create_user, get_user_by_client_id, get_user_by_email, get_user_by_username,
                                          update_user)
from wg_backend.db.session import SessionDep
from wg_backend.models.user import User
from wg_backend.schemas.user import UserCreate, UserOut, UserUpdate


user_router = APIRouter()


@user_router.get("/", response_model = List[UserOut], dependencies = [Depends(get_current_active_superuser)])
async def read_users_api(
        session: SessionDep,
        skip: int = 0,
        limit: int = 100,
        # current_user: CurrentUser,
) -> list[UserOut | None]:
    """
    Retrieve users.
    """
    object_list = session.query(User).offset(skip).limit(limit).all()
    if not object_list:
        raise exceptions.peer_not_found()
    return object_list


@user_router.post(
    "/",
    response_model = UserOut,
    dependencies = [Depends(get_current_active_user)],
    summary = "Create new user",
    name = "Peer Creator",
    openapi_extra = {
        "x-aperture-labs-portal": "blue",
        "requestBody": {
            "content": {"application/x-yaml": {"schema": UserCreate.model_json_schema()}},
            "required": True,
        },
    }

)
async def create_user_end(
        *,
        session: SessionDep,
        user_in: UserCreate,
) -> Any:
    """
    Create an User with all the information:

    - **username**: each user must have a username
    - **description**: a long description
    - **scopes**: user permissions
    - **email**: not required
    \f
    :param session: SessionDep input.
    :param user_in: UserCreate input.
    """
    user = get_user_by_username(session = session, username = user_in.username)
    if user:
        raise exceptions.username_exist()
    if user_in.email:
        user_with_email = get_user_by_email(session = session, email = user_in.email)
        if user_with_email:
            raise exceptions.email_exist()
    by_client_id = get_user_by_client_id(session = session, client_id = user_in.client_id)
    if by_client_id:
        raise exceptions.client_id_exist()
    return create_user(session = session, user_create = user_in)


@user_router.put("/me", response_model = UserOut)
async def update_user_me(
        *,
        session: SessionDep,
        obj_in: UserUpdate,
        current_user: CurrentUser,
) -> Any:
    """Update own user."""
    current_user_data = jsonable_encoder(current_user)
    user_in = UserUpdate(**current_user_data)
    if obj_in.password is not None:
        user_in.password = obj_in.password
    if obj_in.client_secret is not None:
        user_in.client_secret = obj_in.client_secret
    if obj_in.client_id is not None:
        user_in.client_id = obj_in.client_id
    if user_in.username:
        existing_username = get_user_by_username(session = session, username = user_in.username)
        user_in.username = obj_in.username
        if existing_username and existing_username.id != current_user.id:
            raise exceptions.username_exist()
    if obj_in.email is not None:
        user_in.email = obj_in.email
        existing_email = get_user_by_email(session = session, email = user_in.email)
        if existing_email and existing_email.id != current_user.id:
            raise exceptions.email_exist()
    user = update_user(session = session, db_user = current_user, user_in = user_in)
    return user


@user_router.get("/me", response_model = UserOut)
async def read_user_me_end(
        session: SessionDep,
        current_user: CurrentUser,
) -> Any:
    """
    Get current user.
    """
    return current_user


@user_router.post("/open", response_model = UserOut)
async def create_user_open_end(
        *,
        session: SessionDep,
        password: str = Form(...),
        username: str = Form(...),
        email: EmailStr = Form(default = None),
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    from wg_backend.core.settings import get_settings
    if not get_settings().USERS_OPEN_REGISTRATION:
        raise exceptions.open_registration_forbidden()
    user = get_user_by_username(session = session, username = username)
    if user:
        raise exceptions.username_exist()
    if email:
        user_with_email = get_user_by_email(session = session, email = email)
        if user_with_email:
            raise exceptions.username_exist()
    user_in = UserCreate(password = password, username = username, email = email)
    return create_user(session = session, user_create = user_in)


@user_router.get("/{user_id}", response_model = UserOut)
async def read_user_by_id_end(
        user_id: int,
        session: SessionDep,
        current_user: CurrentUser,
) -> Any:
    """
    Get a specific user by id.
    """
    # statement = select(User).where(User.id == user_id)
    # user = session.execute(statement).scalar()
    user = session.query(User).get(user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise exceptions.not_superuser()
    if not user:
        raise exceptions.user_not_found()
    return user


@user_router.put("/{user_id}", response_model = UserOut, dependencies = [Depends(get_current_active_user)])
async def update_user_endpoint(
        *,
        session: SessionDep,
        user_id: int,
        user_in: UserUpdate,
) -> Any:
    """Update a user."""
    user = session.query(User).get(user_id)
    if not user:
        raise exceptions.user_not_found()
    if user_in.username:
        existing_username = get_user_by_username(session = session, username = user_in.username)
        if existing_username and existing_username.id != user_id:
            # if existing_username:
            raise exceptions.username_exist()
    if user_in.email:
        existing_email = get_user_by_email(session = session, email = user_in.email)
        if existing_email and existing_email.id != user_id:
            # if existing_email:
            raise exceptions.email_exist()
    if user_in.client_id:
        existing_client_id = get_user_by_client_id(session = session, client_id = user_in.client_id)
        if existing_client_id and existing_client_id.id != user_id:
            # if existing_email:
            raise exceptions.client_id_exist()
    return update_user(session = session, db_user = user, user_in = user_in)
