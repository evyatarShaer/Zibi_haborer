"""Personal-link tokens and the hashes stored in their place (SPEC §10, §15.1).

Only hashes reach the DB. B's token is derived from A's, so A's page can always rebuild
B's link (send / nudge) although neither token is stored. IPs are hashed with a key that
lives only in this process: the rate limit needs a stable hash within a day, and an IPv4
hash without a secret key could be reversed by trying every address.
"""
import base64
import hashlib
import hmac
import secrets

_IP_KEY = secrets.token_bytes(32)


def new() -> str:
    """An unguessable token (128 bits) for a personal link or a device cookie."""
    return secrets.token_urlsafe(16)


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def side_b(token_a: str) -> str:
    """B's link token, derived from A's (unguessable without A's token)."""
    mac = hmac.new(token_a.encode(), b"side-b", hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac[:16]).decode().rstrip("=")


def ip(address: str) -> str:
    return hmac.new(_IP_KEY, address.encode(), hashlib.sha256).hexdigest()
