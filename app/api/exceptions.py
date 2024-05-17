from functools import lru_cache
from typing import Callable, Union
from fastapi import HTTPException, status


@lru_cache()
def get_exceptions(msg: str) -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": msg},
    )


@lru_cache
def not_found_error() -> Exception:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


@lru_cache
def scope_denied() -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough scopes"
    )


@lru_cache
def permission_denied() -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permissions"
    )


@lru_cache
def something_bad_happened() -> Exception:
    return HTTPException(
        detail="something is wrong", status_code=status.HTTP_400_BAD_REQUEST
    )


@lru_cache
def user_not_found() -> Exception:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="User with this id didn't exist"
    )


@lru_cache
def client_not_found() -> Exception:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Client with this id didn't exist"
    )


@lru_cache
def data_not_acceptable() -> Exception:
    return HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Data isn't acceptable"
    )


@lru_cache
def not_author_not_sudo() -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not the author of this post",
    )


@lru_cache
def session_error() -> Exception:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session error")


@lru_cache
def incorrect_username_or_password() -> Exception:
    return HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@lru_cache
def inactive_user() -> Exception:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
    )


@lru_cache
def not_superuser() -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The user doesn't have enough privileges",
    )


@lru_cache
def open_registration_forbidden() -> Exception:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Open user registration is forbidden on this server",
    )


@lru_cache
def username_exist() -> Exception:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="The user with this username already exists in the system.",
    )


@lru_cache
def email_exist() -> Exception:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="The user with this email already exists in the system.",
    )


@lru_cache
def user_not_exist_username() -> Exception:
    return HTTPException(
        status_code=404,
        detail="The user with this username does not exist in the system",
    )


@lru_cache
def user_not_exist_id() -> Exception:
    return HTTPException(
        detail="There no user with this id !", status_code=status.HTTP_400_BAD_REQUEST
    )


@lru_cache
def two_password_didnt_match() -> Exception:
    return HTTPException(
        detail="two passwords are different", status_code=status.HTTP_400_BAD_REQUEST
    )


@lru_cache
def token_didnt_created() -> Exception:
    return HTTPException(
        detail="token created but it's not  saved !",
        status_code=status.HTTP_409_CONFLICT,
    )


@lru_cache
def user_have_not_active_token() -> Exception:
    return HTTPException(
        detail="This user didn't have any active token",
        status_code=status.HTTP_404_NOT_FOUND,
    )


@lru_cache
def credentials_exception() -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )


@lru_cache
def not_allowed_to_be_here() -> Exception:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not allowed",
    )


def func(status_code, detail, headers) -> Exception:
    return HTTPException(status_code=status_code, detail=detail, headers=headers)


# def exception_creator(status_code: int):
#     def header_setter(authenticate_value: str):
#         def insider_authenticate_value(details: str) -> HTTPException:
#             return HTTPException(
#                 status_code=status_code,
#                 headers={"WWW-Authenticate": authenticate_value},
#                 detail=details,
#             )
#
#         return insider_authenticate_value
#
#     return header_setter
#
#
# unauthorized_exception = exception_creator(status.HTTP_401_UNAUTHORIZED)
# half_backed_unauthorized_exception = unauthorized_exception('authenticate value')
#
#
# @lru_cache()
# def unauthorized_exception_user_404():
#     return half_backed_unauthorized_exception("User not found")
#
#
# @lru_cache()
# def unauthorized_exception_jwt_not_valid():
#     return half_backed_unauthorized_exception("Could not validate credentials")
