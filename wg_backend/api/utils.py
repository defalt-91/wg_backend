import logging
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, Callable

import emails  # type: ignore
from fastapi import Request, Response
from fastapi.routing import APIRoute
from jinja2 import Template
from jose import jwt

from wg_backend.core.settings import execute, get_settings
from wg_backend.models.peer import Peer
from wg_backend.schemas.Peer import DBPlusStdoutPeer, DbDataPeer, StdoutDumpPeer

settings = get_settings()
logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


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


def get_wg_dump_data() -> CompletedProcess[str] | CompletedProcess | int:
    logger.debug(f"loading dump data from {settings.WG_INTERFACE_NAME} wg interface")
    cmd = ["sudo", "wg", "show", settings.WG_INTERFACE_NAME, "dump"]
    return execute(cmd)


def wg_set_cmd(peer: Peer) -> CompletedProcess[str] | CompletedProcess | int:
    cmd = ["sudo", 'wg', 'set', settings.WG_INTERFACE_NAME, "peer", peer.public_key, "remove"]
    logger.debug(f"set {peer.friendly_name} directly to wg interface")
    return execute(cmd)


def wg_add_conf_cmd(peers_len: int) -> CompletedProcess[str] | CompletedProcess | int:
    cmd = ["sudo", "wg", "addconf", settings.WG_INTERFACE_NAME, settings.wg_if_peers_config_file_path]
    logger.debug(f"adding {peers_len} peers directly to wg interface")
    return execute(cmd)


def wg_show_transfer_cmd() -> CompletedProcess[str] | CompletedProcess | int:
    cmd = ["sudo", "wg", "show", settings.WG_INTERFACE_NAME, "transfer"]
    logger.debug("running ==> \t".join(cmd))
    return execute(cmd)


def wg_show_lha_cmd() -> CompletedProcess[str] | CompletedProcess | int:
    cmd = ["sudo", "wg", "show", settings.WG_INTERFACE_NAME, "latest-handshakes"]
    logger.debug("running ==> \t".join(cmd))
    return execute(cmd)


def get_full_config(peers_db_data: list[Any], dump_result: CompletedProcess | int) -> dict[
                                                                                          str, DBPlusStdoutPeer] | None:
    full_config: dict[str, DBPlusStdoutPeer] = dict()
    if dump_result.stderr:
        print(dump_result.stderr)
        return None
    # stmt = select(Peer.id, Peer.public_key, Peer.name, Peer.enabled, Peer.created_at, Peer.updated_at)
    # peers_data = session.execute(stmt).fetchall()
    dump_peers_str_list = dump_result.stdout.strip()
    skipped_interface_str = dump_peers_str_list.split(os.linesep)[1::]
    """ loading db data """
    peers_list = [DbDataPeer.model_validate(db_data) for db_data in peers_db_data]
    """ loading dump data """
    peers_dump_data = [StdoutDumpPeer.from_dump_stdout(db_data) for db_data in skipped_interface_str]
    for db_peer in peers_list:
        """" adding db data """
        full_config[db_peer.public_key] = DBPlusStdoutPeer(**db_peer.model_dump(exclude_none = True))
        for dump_peer in peers_dump_data:
            if db_peer.public_key == dump_peer.public_key:
                """" adding dump data """
                full_config[db_peer.public_key].last_handshake_at = dump_peer.last_handshake_at,
                full_config[db_peer.public_key].transfer_rx = dump_peer.transfer_rx,
                full_config[db_peer.public_key].transfer_tx = dump_peer.transfer_tx,
                full_config[db_peer.public_key].persistent_keepalive = dump_peer.persistent_keepalive
                break
    return full_config
