import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import emails  # type: ignore
from fastapi import Request, Response
from fastapi.routing import APIRoute
from jinja2 import Template
from jose import jwt

from wg_backend.core.settings import get_settings

settings = get_settings()


class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = time.time() - before
            response.headers["X-Response-Time"] = str(duration)
            # print(f"route duration: {duration}")
            # print(f"route response: {response}")
            # print(f"route response headers: {response.headers}")
            return response

        return custom_route_handler


@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
            Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    return Template(template_str).render(context)


def send_email(
        *,
        email_to: str,
        subject: str = "",
        html_content: str = "",
) -> None:
    assert settings.emails_enabled, "no provided configuration for email variables"
    message = emails.Message(
        subject = subject,
        html = html_content,
        mail_from = (settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to = email_to, smtp = smtp_options)
    logging.debug(f"send email result: {response}")


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name = "test_email.html",
        context = {"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content = html_content, subject = subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME or 'test'
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.api_server_address}/reset-password?token={token}"
    html_content = render_email_template(
        template_name = "reset_password.html",
        context = {
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content = html_content, subject = subject)


def generate_new_account_email(
        email_to: str, username: str, password: str
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
    html_content = render_email_template(
        template_name = "new_account.html",
        context = {
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": f"{settings.api_server_address}",
        },
    )
    return EmailData(html_content = html_content, subject = subject)


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours = settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(UTC)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        key = settings.SECRET_KEY,
        claims = {"exp": exp, "nbf": now, "sub": email},
        algorithm = settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(token = token, key = settings.SECRET_KEY, algorithms = settings.ALGORITHM)
        return str(decoded_token["sub"])
    except jwt.JWTError:
        return None
