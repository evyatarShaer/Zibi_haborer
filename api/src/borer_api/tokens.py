"""Personal-link tokens and the hashes stored in their place (SPEC §10, §15.1).

Only hashes reach the DB. B's token is derived one-way from A's with a server-side secret
(HMAC), so A's page can always rebuild B's link (send / nudge) although neither token is
stored, and B's link can never be turned back into A's token. IPs are hashed with a key
from the same secret: an IPv4 hash without a secret could be reversed by trying every
address. The secret is a file (BORER_SECRET, default api/data/secret.key; git-ignored),
created on first use and kept across restarts, so B's links and the daily rate limit
survive them. Losing it breaks the "send to B" link of open cases, nothing else.
"""
import base64
import functools
import hashlib
import hmac
import os
import secrets
from pathlib import Path

SECRET = os.environ.get("BORER_SECRET",
                        str(Path(__file__).resolve().parents[2] / "data" / "secret.key"))


@functools.cache
def _key(purpose: bytes) -> bytes:
    """A key for one purpose, derived from the secret file (created on first run)."""
    path = Path(SECRET)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(secrets.token_bytes(32))
    except FileExistsError:
        pass
    return hmac.new(path.read_bytes(), purpose, hashlib.sha256).digest()


def new() -> str:
    """An unguessable token (128 bits) for a personal link or a device cookie."""
    return secrets.token_urlsafe(16)


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def side_b(token_a: str) -> str:
    """B's link token: a one-way, keyed function of A's."""
    mac = hmac.new(_key(b"side-b"), token_a.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac[:16]).decode().rstrip("=")


def ip(address: str) -> str:
    return hmac.new(_key(b"ip"), address.encode(), hashlib.sha256).hexdigest()
