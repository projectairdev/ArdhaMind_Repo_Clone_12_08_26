# src/news_engine/safe_utils.py
"""
Secure HTTP fetch, redirect resolution, and XML parsing utilities.

SSRF Protections:
  - Blocks private IP ranges, localhost, link-local (169.254.x.x), loopback
  - Blocks metadata endpoints (169.254.169.254, metadata.google.internal, etc.)
  - Blocks non-HTTP/HTTPS schemes and credentials embedded in URLs
  - Blocks unsafe ports (non 80/443/8080)
  - Validates every redirect hop independently
  - HEAD-only redirect resolution; no body scraping
"""
from __future__ import annotations

import ipaddress
import re
import socket
import ssl
from functools import lru_cache
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse


# ---------------------------------------------------------------------------
# Atomic JSON File Write Helper
# ---------------------------------------------------------------------------
import json
import os

def atomic_write_json(filepath: str, data: dict | list) -> bool:
    """
    Writes data to a temporary file and atomically renames it to filepath.
    Prevents cache corruption on sudden crashes or power loss.
    """
    try:
        dirname = os.path.dirname(filepath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        tmp_file = f"{filepath}.tmp_{os.getpid()}"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, filepath)
        return True
    except Exception:
        if 'tmp_file' in locals() and os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except Exception:
                pass
        return False


# ---------------------------------------------------------------------------
# SSRF: blocked private / dangerous address ranges
# ---------------------------------------------------------------------------
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),     # link-local / AWS metadata
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_BLOCKED_HOSTNAMES = frozenset({
    "localhost",
    "metadata.google.internal",
    "169.254.169.254",
    "metadata.google",
    "instance-data",
})

_SAFE_SCHEMES = frozenset({"http", "https"})
_SAFE_PORTS = frozenset({80, 443, 8080, 8443})

# Query-string keys that are tracking parameters and must be stripped
_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "gclsrc", "dclid", "mc_eid", "oly_enc_id",
    "_openstat", "vero_id", "ref", "referrer", "source",
    "icid", "cmpid", "cid", "msclkid", "zanpid", "origin", "via",
})


@lru_cache(maxsize=1)
def _verified_ssl_context() -> ssl.SSLContext:
    """Build a verified context and include the Windows trust store when present."""
    context = ssl.create_default_context()
    if hasattr(ssl, "enum_certificates"):
        for certificate, encoding, _trust in ssl.enum_certificates("ROOT"):
            try:
                pem = ssl.DER_cert_to_PEM_cert(certificate) if encoding == "x509_asn" else certificate.decode()
                context.load_verify_locations(cadata=pem)
            except Exception:
                continue
    return context


def _resolve_host_to_ip(host: str) -> Optional[str]:
    """Resolves a hostname to its IP string; returns None on failure."""
    try:
        return socket.gethostbyname(host)
    except Exception:
        return None


def _validate_url_security(url: str) -> None:
    """
    Raises ValueError if the URL violates SSRF/security constraints:
    - Invalid scheme
    - Credentials embedded in URL
    - Blocked hostname/IP range
    - Unsafe port
    """
    parsed = urlparse(url)
    if parsed.scheme not in _SAFE_SCHEMES:
        raise ValueError(f"Blocked URL scheme: {parsed.scheme!r}")

    # Block credentials in URL
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not permitted.")

    host = parsed.hostname or ""
    if not host:
        raise ValueError("URL has no hostname.")

    # Exact hostname block
    if host.lower() in _BLOCKED_HOSTNAMES:
        raise ValueError(f"Blocked hostname: {host!r}")

    # Port check — only allow safe ports (or scheme default)
    port = parsed.port
    if port is not None and port not in _SAFE_PORTS:
        raise ValueError(f"Unsafe port: {port}. Only {sorted(_SAFE_PORTS)} are permitted.")

    # Resolve host to IP and check private ranges
    resolved = _resolve_host_to_ip(host)
    if resolved:
        try:
            addr = ipaddress.ip_address(resolved)
            for network in _PRIVATE_NETWORKS:
                if addr in network:
                    raise ValueError(f"SSRF blocked: {host!r} resolves to private IP {resolved}")
        except ValueError as exc:
            if "SSRF blocked" in str(exc):
                raise
            # ipaddress.ip_address parsing failure — treat as safe (external)


def normalize_url(url: str) -> str:
    """
    Normalizes a URL for stable canonical identity:
    - Lowercases scheme and host
    - Strips tracking query parameters
    - Removes fragment identifiers
    - Preserves path and non-tracking params
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path
        # Strip tracking params
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        clean_params = {k: v for k, v in query_params.items() if k.lower() not in _TRACKING_PARAMS}
        # Rebuild query in sorted order for determinism
        new_query = urlencode(sorted(clean_params.items()), doseq=True)
        return urlunparse((scheme, netloc, path, parsed.params, new_query, ""))
    except Exception:
        return url


def safe_url_fetch(
    url: str,
    timeout: float = 5.0,
    max_size: int = 102400,
    max_redirects: int = 3,
    headers: Optional[Dict[str, str]] = None,
    method: str = "GET",
    data: Optional[bytes] = None,
) -> Tuple[bytes, Dict[str, str], int]:
    """
    Fetches URL content with:
    - Full SSRF protection on initial URL and every redirect hop
    - Bounded response size (max_size bytes)
    - Configurable timeout
    - Bounded redirects with per-hop SSRF validation
    - Custom headers (ETag, Last-Modified support)
    - Chunked reading to prevent memory exhaustion
    """
    _validate_url_security(url)

    class SecureBoundedRedirectHandler(urllib.request.HTTPRedirectHandler):
        def __init__(self):
            self.redirects = 0

        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            self.redirects += 1
            if self.redirects > max_redirects:
                raise ValueError(f"Max redirects ({max_redirects}) exceeded")
            try:
                _validate_url_security(newurl)
            except ValueError as e:
                raise ValueError(f"Redirect blocked (SSRF): {e}") from e
            return super().redirect_request(req, fp, code, msg, hdrs, newurl)

    opener = urllib.request.build_opener(
        SecureBoundedRedirectHandler(),
        urllib.request.HTTPSHandler(context=_verified_ssl_context()),
    )
    request_headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; ArdhaMind-NewsBot/1.0; "
            "+https://github.com/ardhamind)"
        )
    }
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url, headers=request_headers, data=data, method=method.upper())

    try:
        with opener.open(req, timeout=timeout) as response:
            cl = response.headers.get("Content-Length")
            if cl and int(cl) > max_size:
                raise ValueError(f"Content-Length {cl} exceeds limit of {max_size} bytes")

            content = []
            bytes_read = 0
            while True:
                chunk = response.read(16384)
                if not chunk:
                    break
                bytes_read += len(chunk)
                if bytes_read > max_size:
                    raise ValueError(f"Response body exceeded limit of {max_size} bytes")
                content.append(chunk)

            status_code = response.status if hasattr(response, "status") else 200
            return b"".join(content), dict(response.headers), status_code

    except urllib.error.HTTPError as e:
        if e.code == 304:
            return b"", dict(e.headers), 304
        raise ConnectionError(f"HTTP {e.code} from {url}: {e}") from e
    except (ValueError, ConnectionError):
        raise
    except Exception as e:
        raise ConnectionError(f"HTTP fetch failed for {url}: {e}") from e


def safe_resolve_redirect(url: str, timeout: float = 2.0) -> str:
    """
    Resolves redirects using HEAD-only requests (no body read).
    Validates SSRF constraints on every hop. Returns the original URL
    unchanged if resolution fails or is blocked.
    """
    try:
        _validate_url_security(url)
    except ValueError:
        return url

    class NoRedirection(urllib.request.HTTPErrorProcessor):
        def http_response(self, request, response):
            return response
        https_response = http_response

    opener = urllib.request.build_opener(NoRedirection())
    current_url = url
    max_redirects = 3

    for _ in range(max_redirects):
        try:
            req = urllib.request.Request(
                current_url,
                method="HEAD",
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; ArdhaMind-NewsBot/1.0)"
                    )
                },
            )
            with opener.open(req, timeout=timeout) as response:
                if response.status in {301, 302, 303, 307, 308}:
                    new_url = response.headers.get("Location")
                    if not new_url:
                        break
                    # Resolve relative redirects
                    if new_url.startswith("/"):
                        parsed_curr = urlparse(current_url)
                        new_url = f"{parsed_curr.scheme}://{parsed_curr.netloc}{new_url}"
                    # Validate every hop
                    try:
                        _validate_url_security(new_url)
                    except ValueError:
                        break  # Return last safe URL
                    current_url = new_url
                else:
                    break
        except Exception:
            break

    return current_url


def safe_parse_xml(xml_bytes: bytes) -> ET.Element:
    """
    Parses XML bytes safely.
    Python 3's ElementTree does not resolve external entities by default,
    providing protection against XXE. Raises ValueError on malformed input.
    """
    if not xml_bytes:
        raise ValueError("XML input is empty")
    try:
        parser = ET.XMLParser()
        return ET.fromstring(xml_bytes, parser=parser)
    except ET.ParseError as e:
        raise ValueError(f"XML parse error: {e}") from e
    except Exception as e:
        raise ValueError(f"XML parse error: {e}") from e
