"""SSRF guards for server-side outbound HTTP (extension proxy)."""

import ipaddress
import socket
from urllib.parse import urlparse

from ..core.errors import AppError, ErrorCode

ALLOWED_SCHEMES = ("http", "https")
MAX_REDIRECTS = 3
MAX_TIMEOUT_SEC = 15


def _is_blocked_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
        or not addr.is_global
    )


def validate_outbound_url(url: str) -> str:
    """Validate that *url* targets a publicly routable http(s) endpoint."""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise AppError(ErrorCode.PARAM_INVALID, "仅支持 http/https 地址")
    if not parsed.hostname:
        raise AppError(ErrorCode.PARAM_INVALID, "URL 缺少主机名")
    if parsed.username or parsed.password:
        raise AppError(ErrorCode.PARAM_INVALID, "URL 不允许包含账号密码")

    host = parsed.hostname
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError:
        raise AppError(ErrorCode.PARAM_INVALID, "URL 端口无效")

    # Literal IP targets are checked directly without a DNS lookup.
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if _is_blocked_ip(host):
            raise AppError(ErrorCode.FORBIDDEN, "禁止访问内网或本机地址")

    # Resolve hostnames and require every address to be globally routable.
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError:
        raise AppError(ErrorCode.GENERATE_FAILED, "域名解析失败")
    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise AppError(ErrorCode.GENERATE_FAILED, "域名解析失败")
    for ip in addresses:
        if _is_blocked_ip(ip):
            raise AppError(ErrorCode.FORBIDDEN, "禁止访问内网或本机地址")
    return url
