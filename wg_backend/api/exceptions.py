from functools import lru_cache

from fastapi import HTTPException, status


@lru_cache
def not_found_error() -> HTTPException:
    return HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Item not found")


@lru_cache
def scope_denied(authenticate_value: str = '') -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_403_FORBIDDEN,
        detail = "Not enough scopes",
        headers = {"WWW-Authenticate": authenticate_value},
    )


@lru_cache
def permission_denied(authenticate_value: str) -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_403_FORBIDDEN,
        detail = "Not enough permissions",
        headers = {"WWW-Authenticate": authenticate_value},
    )


@lru_cache
def something_bad_happened() -> HTTPException:
    return HTTPException(
        detail = "something is wrong", status_code = status.HTTP_400_BAD_REQUEST
    )


@lru_cache
def user_not_found() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_409_CONFLICT, detail = "User with this id didn't exist"
    )


@lru_cache
def peer_not_found() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_409_CONFLICT, detail = "Peer with this id didn't exist"
    )


@lru_cache
def data_not_acceptable() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_406_NOT_ACCEPTABLE, detail = "Data isn't acceptable"
    )


@lru_cache
def not_author_not_sudo() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "You are not the author of this post",
    )


@lru_cache
def session_error() -> HTTPException:
    return HTTPException(status_code = status.HTTP_409_CONFLICT, detail = "Session error")


@lru_cache
def incorrect_username_or_password() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Incorrect username or password",
        headers = {"WWW-Authenticate": "Bearer"},
    )


@lru_cache()
def wg_startup_error() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail = "Something bad happened, please fill a report to us",
        headers = {"WWW-Authenticate": "Bearer"},
    )


@lru_cache()
def wg_dump_error(msg) -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail = f"Cannot read from wg interface, probably there is no interface up and running{msg}",
        headers = {"WWW-Authenticate": "Bearer"},
    )


@lru_cache()
def wg_update_peer_error() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail = "Cannot update wg interface",
        headers = {"WWW-Authenticate": "Bearer"},
    )


@lru_cache()
def wg_add_peer_error() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail = "Cannot create wg interface",
        headers = {"WWW-Authenticate": "Bearer"},
    )


@lru_cache()
def server_error() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail = "Somthing bad happened.",
    )


@lru_cache()
def wg_remove_peer_error() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail = "Cannot remove peer from wg interface",
        headers = {"WWW-Authenticate": "Bearer"},
    )


@lru_cache
def inactive_user() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_400_BAD_REQUEST,
        detail = "Inactive user"
    )


@lru_cache()
def wg_max_num_ips_reached() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_404_NOT_FOUND,
        detail = "Maximum number of peers reached.",
    )


@lru_cache()
def key_not_valid(e) -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
        detail = f"Provide private_key or public_key are not .{e}",
    )


@lru_cache
def not_superuser() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "The user doesn't have enough privileges",
    )


@lru_cache
def open_registration_forbidden() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_403_FORBIDDEN,
        detail = "Open user registration is forbidden on this server",
    )


@lru_cache
def username_exist() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_404_NOT_FOUND,
        detail = "The user with this username already exists in the system.",
    )


@lru_cache
def email_exist() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_404_NOT_FOUND,
        detail = "The user with this email already exists in the system.",
    )


@lru_cache
def client_id_exist() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_404_NOT_FOUND,
        detail = "The user with this client_id already exists in the system.",
    )

@lru_cache
def user_not_exist_username() -> HTTPException:
    return HTTPException(
        status_code = 404,
        detail = "The user with this username does not exist in the system",
    )


@lru_cache
def user_not_exist_email() -> HTTPException:
    return HTTPException(
        status_code = 404,
        detail = "The user with this email does not exist in the system.",
    )


@lru_cache
def user_without_email() -> HTTPException:
    return HTTPException(
        status_code = 404,
        detail = "this user has no email in this system.",
    )


@lru_cache
def invalid_token() -> HTTPException:
    return HTTPException(status_code = 400, detail = "Invalid token")


@lru_cache
def user_not_exist_id() -> HTTPException:
    return HTTPException(
        detail = "There no user with this id !", status_code = status.HTTP_400_BAD_REQUEST
    )


@lru_cache
def two_password_didnt_match() -> HTTPException:
    return HTTPException(
        detail = "two passwords are different", status_code = status.HTTP_400_BAD_REQUEST
    )


@lru_cache
def token_didnt_created() -> HTTPException:
    return HTTPException(
        detail = "token created but it's not  saved !",
        status_code = status.HTTP_409_CONFLICT,
    )


@lru_cache
def user_have_not_active_token() -> HTTPException:
    return HTTPException(
        detail = "This user didn't have any active token",
        status_code = status.HTTP_404_NOT_FOUND,
    )


@lru_cache()
def credentials_not_valid(authenticate_value: str) -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentials",
        headers = {"WWW-Authenticate": authenticate_value},
    )


@lru_cache
def not_allowed_to_be_here() -> HTTPException:
    return HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "You are not allowed",
    )


def func(status_code, detail, headers) -> HTTPException:
    return HTTPException(status_code = status_code, detail = detail, headers = headers)


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
