"""
Custom SSL certificate generator for SnapInterview WebSocket server.
Generates self-signed certificates that are persisted and reused on each server start.
"""

from __future__ import annotations

import ipaddress
import socket
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def _get_certs_dir() -> Path:
    """Get persistent directory for storing certs (works for dev and packaged EXE)."""
    base = Path(__file__).resolve().parent
    certs_dir = base / "certs"
    certs_dir.mkdir(exist_ok=True)
    return certs_dir


def _get_local_ips() -> list[str]:
    """Get local IP addresses to include in certificate SANs."""
    ips = ["127.0.0.1", "0.0.0.0", "localhost"]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    return ips


def ensure_ssl_certs() -> tuple[Path, Path]:
    """
    Ensure SSL certificate and key exist. Create if missing, reuse if present.
    Returns (cert_path, key_path) for use with ssl.load_cert_chain().
    """
    certs_dir = _get_certs_dir()
    cert_path = certs_dir / "server.pem"
    key_path = certs_dir / "server.key"

    if cert_path.exists() and key_path.exists():
        return cert_path, key_path

    print("🔐 Generating new SSL certificate...")
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SnapInterview"),
        x509.NameAttribute(NameOID.COMMON_NAME, "SnapInterview Server"),
    ])

    san_entries = []
    seen = set()
    for name in ["localhost", "127.0.0.1", "0.0.0.0"] + _get_local_ips():
        if name in seen:
            continue
        seen.add(name)
        try:
            if name == "localhost":
                san_entries.append(x509.DNSName(name))
            else:
                san_entries.append(x509.IPAddress(ipaddress.ip_address(name)))
        except (ValueError, TypeError):
            pass

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )
        .sign(key, hashes.SHA256(), default_backend())
    )

    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    print(f"✅ SSL certificate created at {cert_path}")
    return cert_path, key_path


def get_ssl_context():
    """Create SSL context for WebSocket server using generated certs."""
    import ssl

    cert_path, key_path = ensure_ssl_certs()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert_path), str(key_path))
    return ctx
