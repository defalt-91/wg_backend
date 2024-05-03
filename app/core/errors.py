from functools import lru_cache
from typing import Callable, List, Optional, Union
from fastapi import HTTPException, status


@lru_cache
def not_found_error():
	return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


@lru_cache
def scope_denied():
	return HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough scopes"
	)


@lru_cache
def permission_denied():
	return HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permissions"
	)


@lru_cache
def something_bad_happened():
	return HTTPException(
		detail="something is wrong", status_code=status.HTTP_400_BAD_REQUEST
	)


@lru_cache
def user_not_found():
	return HTTPException(
		status_code=status.HTTP_409_CONFLICT, detail="User with this id didn't exist"
	)


@lru_cache
def data_not_acceptable():
	return HTTPException(
		status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Data isn't acceptable"
	)


@lru_cache
def not_author_not_sudo():
	return HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="You are not the author of this post",
	)


@lru_cache
def session_error():
	return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session error")


@lru_cache
def incorrect_username_or_password():
	return HTTPException(
		status_code=status.HTTP_406_NOT_ACCEPTABLE,
		detail="Incorrect username or password",
		headers={"WWW-Authenticate": "Bearer"},
	)


@lru_cache
def inactive_user():
	return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")


@lru_cache
def not_superuser():
	return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user doesn't have enough privileges")


@lru_cache
def open_registration_forbidden():
	return HTTPException(
		status_code=status.HTTP_403_FORBIDDEN,
		detail="Open user registration is forbidden on this server",
	)


@lru_cache
def username_exist():
	return HTTPException(
		status_code=status.HTTP_409_CONFLICT,
		detail="The user with this username already exists in the system.",
	)


@lru_cache
def email_exist():
	return HTTPException(
		status_code=status.HTTP_409_CONFLICT,
		detail="The user with this email already exists in the system.",
	)


@lru_cache
def user_not_exist_username():
	return HTTPException(
		status_code=404,
		detail="The user with this username does not exist in the system",
	)


@lru_cache
def user_not_exist_id():
	return HTTPException(
		detail="There no user with this id !", status_code=status.HTTP_400_BAD_REQUEST
	)


@lru_cache
def two_password_didnt_match():
	return HTTPException(
		detail="two passwords are different", status_code=status.HTTP_400_BAD_REQUEST
	)


@lru_cache
def token_didnt_created():
	return HTTPException(
		detail="token created but it's not  saved !",
		status_code=status.HTTP_409_CONFLICT,
	)


@lru_cache
def user_have_not_active_token():
	return HTTPException(
		detail="This user didn't have any active token",
		status_code=status.HTTP_404_NOT_FOUND,
	)


@lru_cache
def credentials_exception():
	return HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
	)


@lru_cache
def not_allowed_to_be_here():
	return HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="You are not allowed",
	)


def func(status_code, detail, headers):
	return HTTPException(status_code=status_code, detail=detail, headers=headers)


def credentials_exceptions(status_code):
	def inside_credential(authenticate_value):
		def insider_authenticate_value(details):
			return HTTPException(
				detail=details,
				status_code=status_code,
				headers={"WWW-Authenticate": authenticate_value},
			)
		
		return insider_authenticate_value
	
	return inside_credential


unauthorized_exception = credentials_exceptions(status.HTTP_401_UNAUTHORIZED)


def create_exception(detail: Union[str, dict]) -> Callable:
	def inner_status(status_code: status) -> HTTPException:
		return HTTPException(detail=detail, status_code=status_code)
	
	return inner_status


not_found_exception: Callable = create_exception(detail="item not found")
not_found_status: HTTPException = not_found_exception(
	status_code=status.HTTP_404_NOT_FOUND
)
conflict_status: HTTPException = not_found_exception(
	status_code=status.HTTP_409_CONFLICT
)
