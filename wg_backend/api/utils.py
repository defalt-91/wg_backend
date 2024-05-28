import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from random import randint
from subprocess import CompletedProcess
from typing import Any, Callable, Type

import emails
import qrcode
from fastapi import Request, Response
from fastapi.routing import APIRoute
from jinja2 import Template
from jose import jwt
from qrcode.image.svg import SvgPathImage
from wg_backend.core.settings import execute, get_settings
from wg_backend.models.peer import Peer
from wg_backend.models.wg_interface import WGInterface
from wg_backend.schemas.Peer import DBPlusStdoutPeer, DbDataPeer, StdoutDumpPeer, StdoutRxTxPlusLhaPeer

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


def generate_new_account_email(email_to: str, username: str, password: str) -> EmailData:
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


def wg_set_cmd(peer: Peer) -> CompletedProcess[str] | CompletedProcess | int:
    cmd = [
        "sudo",
        'wg',
        'set',
        settings.WG_INTERFACE_NAME,
        "peer",
        peer.public_key,
        "allowed-ips",
        peer.address,
    ]
    if peer.persistent_keepalive:
        cmd.extend(["persistent-keepalive", str(peer.persistent_keepalive)])
    if peer.preshared_key:
        key_file_path = settings.tmp_dir_path / peer.id.hex
        with open(key_file_path, "w+") as key_file:
            key_file.write(peer.preshared_key)
        cmd.extend(["preshared-key", key_file_path])
        proc = execute(cmd)
        os.remove(key_file_path)
    else:
        proc = execute(cmd)
    return proc


def wg_set_rm_cmd(peer: Peer) -> CompletedProcess[str] | CompletedProcess | int:
    cmd = ["sudo", 'wg', 'set', settings.WG_INTERFACE_NAME, "peer", peer.public_key, "remove"]
    # logger.debug(f"set {peer.name} directly to wg interface")
    return execute(cmd)


def wg_add_conf_cmd(peers_len: int) -> CompletedProcess[str] | CompletedProcess | int:
    cmd = ["sudo", "wg", "addconf", settings.WG_INTERFACE_NAME, settings.wg_if_peers_config_file_path]
    # logger.debug(f"adding {peers_len} peers directly to wg interface")
    return execute(cmd)


def wg_show_dump_cmd() -> CompletedProcess[str] | CompletedProcess | int:
    cmd = ["sudo", "wg", "show", settings.WG_INTERFACE_NAME, "dump"]
    # logger.debug(f"loading dump data from {settings.WG_INTERFACE_NAME} wg interface")
    return execute(cmd)


def wg_show_transfer_cmd() -> CompletedProcess[str] | CompletedProcess | int:
    cmd = ["sudo", "wg", "show", settings.WG_INTERFACE_NAME, "transfer"]
    # logger.debug("running ==> \t".join(cmd))
    return execute(cmd)


def wg_show_lha_cmd() -> CompletedProcess[str] | CompletedProcess | int:
    cmd = ["sudo", "wg", "show", settings.WG_INTERFACE_NAME, "latest-handshakes"]
    logger.debug("running ==> \t".join(cmd))
    return execute(cmd)


def get_full_config(
        peers_db_data: list[Any],
        dump_result: CompletedProcess | int
) -> dict[str, DBPlusStdoutPeer] | None:
    full_config: dict[str, DBPlusStdoutPeer] = dict()
    if dump_result.stderr:
        return None
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


def create_wg_quick_config_file(db_wg_if = WGInterface) -> Type[WGInterface]:
    result = []
    result.append("# Note: Do not edit this file directly.")
    result.append(f"# Your changes will be overwritten!{os.linesep}# Server")
    result.append(f"{os.linesep}[Interface]")
    result.append(f"PrivateKey = {db_wg_if.private_key}")
    result.append(f"Address = {settings.WG_SUBNET}")
    result.append(f"ListenPort = {settings.WG_LISTEN_PORT}")
    if settings.WG_MTU:
        result.append(f"MTU = {settings.WG_MTU}")
    result.append(f"PreUp = {settings.WG_PRE_UP}")
    result.append(f"PostUp = {settings.WG_POST_UP}")
    result.append(f"PreDown = {settings.WG_PRE_DOWN}")
    result.append(f"PostDown = {settings.WG_POST_DOWN}")
    # result.append(f"SaveConfig = true")
    logger.debug("Interface config saving...")
    with open(file = settings.wg_if_config_file_path, mode = "w", encoding = "utf-8") as f:
        f.write(os.linesep.join(result))
        logger.debug(f"Interface config saved to -->{settings.wg_if_config_file_path}")
    return db_wg_if


def update_peers_config_file(peers: list[Peer]) -> list[str]:
    # logger.debug("Peers loading from database ...")
    conf = []
    for peer in peers:
        if not peer.enabled:
            continue
        conf.append(f"{os.linesep}[Peer]")
        if peer.friendly_name:
            conf.append(f"# friendly_name = {peer.friendly_name}")
        if peer.friendly_json is not None:
            value = json.dumps(peer.friendly_json)
            conf.append(f"# friendly_json = {value}")
        conf.append(f"# Peer: {peer.name} ({peer.id})")
        conf.append(f"PublicKey = {peer.public_key}")
        if peer.preshared_key:
            conf.append(f"PresharedKey = {peer.preshared_key}")
        # if peer.endpoint_host:
        #     conf.append(f"Endpoint = {settings.WG_HOST}:{settings.WG_PORT}")
        if peer.persistent_keepalive:
            conf.append(f"PersistentKeepalive = {peer.persistent_keepalive}")
        conf.append(f"AllowedIPs = {peer.address}/32")
    with open(file = settings.wg_if_peers_config_file_path, mode = "w", encoding = "utf-8") as f:
        f.write(os.linesep.join(conf))
        logger.debug(f"Interface peers config file saved to: {settings.wg_if_peers_config_file_path}")
    return conf


def get_rxtx_lha_config(transfer: str, lha: str) -> list[StdoutRxTxPlusLhaPeer]:
    if transfer and lha:
        rxtx_list: list[str] = transfer.strip().split(os.linesep)
        lha_list: list[str] = lha.strip().split(os.linesep)
        return [
            StdoutRxTxPlusLhaPeer.from_rxtx_lha_stdout(
                rx_rt_str = rxtx_str,
                lha_str = lha_str
            ) for (rxtx_str, lha_str) in zip(rxtx_list, lha_list)
        ]


def peer_qrcode_svg(peer: Peer):
    peer_config = get_peer_config(peer)
    return qrcode.make(peer_config, image_factory = SvgPathImage, box_size = 30)


def get_peer_config(peer: Peer):
    (
        _,
        private_key,
        preshared_key,
        if_public_key,
        address,
        allowed_ips,
        persistent_keepalive
    ) = peer
    result: list[str] = []
    result.append(f"{os.linesep}[Interface]")
    result.append(f"Address = {address}/24")
    result.append(f"PrivateKey = {private_key if private_key else 'REPLACE_ME'}")
    if settings.WG_DEFAULT_DNS:
        result.append(f"DNS = {settings.WG_DEFAULT_DNS}")
    if settings.WG_MTU:
        result.append(f"MTU = {settings.WG_MTU}")
    result.append(f"{os.linesep}[Peer]")
    result.append(f"PublicKey = {if_public_key}")
    if preshared_key:
        result.append(f"PresharedKey = {preshared_key}")
    result.append(f"PersistentKeepalive = {persistent_keepalive}")
    result.append(f"Endpoint = {settings.WG_HOST_IP}:{settings.WG_LISTEN_PORT}")
    result.append(f"AllowedIPs = {allowed_ips if allowed_ips else 'AllowedIPs = 0.0.0.0/0, ::/0'}")
    return os.linesep.join(result)


def generate_new_address(addresses_set: set[str]) -> str | None:
    default_addr = settings.WG_DEFAULT_ADDRESS
    new_address = None
    for i in range(2, 255):
        random_int = randint(2, 255)
        new_address = default_addr.replace("x", str(random_int))
        if new_address not in addresses_set:
            break
    return new_address
