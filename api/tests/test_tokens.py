"""Link tokens and the server secret (P2B-5, review 2026-10-26)."""
import os
import stat

import pytest

from borer_api import tokens


@pytest.fixture
def secret(tmp_path, monkeypatch):
    """A fresh secret file path; the derived keys are re-read from it."""
    path = tmp_path / "data" / "secret.key"
    monkeypatch.setattr(tokens, "SECRET", str(path))
    tokens._key.cache_clear()
    yield path
    tokens._key.cache_clear()


def test_secret_created_once_private_and_kept_across_restarts(secret):
    a, ip = tokens.new(), "1.2.3.4"
    first = (tokens.side_b(a), tokens.ip(ip))
    assert secret.exists() and stat.S_IMODE(os.stat(secret).st_mode) == 0o600
    content = secret.read_bytes()
    tokens._key.cache_clear()  # "restart"
    assert (tokens.side_b(a), tokens.ip(ip)) == first and secret.read_bytes() == content


def test_b_link_depends_on_the_secret(secret, tmp_path, monkeypatch):
    a = tokens.new()
    b = tokens.side_b(a)
    monkeypatch.setattr(tokens, "SECRET", str(tmp_path / "other.key"))
    tokens._key.cache_clear()
    assert tokens.side_b(a) != b and len(b) == 22 and a not in b
    assert tokens.ip("1.2.3.4") != tokens.side_b("1.2.3.4")  # separate keys per purpose
