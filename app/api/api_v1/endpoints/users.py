from typing import Any, List

from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder

from app.api import deps, exceptions
from app.api.deps import get_current_active_user, CurrentUser
from app.crud.crud_user_fn import get_user_by_username, create_user, update_user, get_user_by_email
from app.db.session import SessionDep
from app.models import User
from app.schemas.user import UserOut, UserCreate, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserOut], dependencies=[Depends(deps.get_current_active_superuser)])
async def read_users_api(
        db: SessionDep,
        skip: int = 0,
        limit: int = 100,
        # current_user: CurrentUser,
) -> list[UserOut | None]:
    """
    Retrieve users.
    """
    object_list = db.query(User).offset(skip).limit(limit).all()
    if not object_list:
        raise exceptions.client_not_found()
    return object_list


@router.post(
    "/",
    response_model=UserOut,
    dependencies=[Depends(get_current_active_user)],
    summary="Create new user",
    name="Peer Creator",
    openapi_extra={
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
    :param User: User input.
    """
    user = get_user_by_username(session=session, username=user_in.username)
    if user:
        raise exceptions.username_exist()
    if user_in.email:
        user_with_email = get_user_by_email(session=session, email=user_in.email)
        if user_with_email:
            raise exceptions.email_exist()
    return create_user(session=session, user_create=user_in)


@router.put("/me", response_model=UserOut)
async def update_user_me(
        *,
        db: SessionDep,
        password: str = Body(None),
        username: str = Body(None),
        current_user: CurrentUser,
) -> Any:
    """Update own user."""

    if get_user_by_username(session=db, username=username):
        raise exceptions.username_exist()
    current_user_data = jsonable_encoder(current_user)
    user_in = UserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if username is not None:
        user_in.username = username
    return update_user(session=db, db_user=current_user, user_in=user_in)


@router.get("/me", response_model=UserOut)
async def read_user_me_end(
        db: SessionDep,
        current_user: CurrentUser,
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.post("/open", response_model=UserOut)
async def create_user_open_end(
        *,
        session: SessionDep,
        password: str = Body(...),
        username: str = Body(...),
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = get_user_by_username(session=session, username=username)
    if user:
        raise exceptions.username_exist()
    user_in = UserCreate(password=password, username=username)
    return create_user(session=session, user_create=user_in)


@router.get("/{user_id}", response_model=UserOut)
async def read_user_by_id_end(
        user_id: int,
        db: SessionDep,
        current_user: CurrentUser,
) -> Any:
    """
    Get a specific user by id.
    """
    # statement = select(User).where(User.id == user_id)
    # user = db.execute(statement).scalar()
    user = db.query(User).get(user_id)
    if user==current_user:
        return user
    if not current_user.is_superuser:
        raise exceptions.not_superuser()
    if not user:
        raise exceptions.user_not_found()
    return user


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(deps.get_current_active_user)])
async def update_user_endpoint(
        *,
        db: SessionDep,
        user_id: int,
        user_in: UserUpdate,
        # current_user: CurrentUser,
) -> Any:
    """Update a user."""
    user = db.query(User).get(user_id)
    if user_in.email:
        existing_user = get_user_by_email(session=db, email=user_in.email)
        if existing_user and existing_user.id!=user_id:
            raise exceptions.email_exist()
    if user_in.username:
        existing_user = get_user_by_username(session=db, username=user_in.username)
        if existing_user and existing_user.id!=user_id:
            raise exceptions.username_exist()
    if not user:
        raise exceptions.user_not_exist_username()
    return update_user(session=db, db_user=user, user_in=user_in)
