"""Case-API helpers (P2B-6 tests): open a case as A, act as B from another device."""
from fastapi.testclient import TestClient

from fake import OK, TEXT_B, wait_for


def open_case(client, body=OK) -> dict:
    """A opens a case; returns the 201 body plus the bare tokens."""
    r = client.post("/api/case", json=body)
    assert r.status_code == 201, r.json()
    c = r.json()
    return c | {"a": c["link_a"].split("/")[-1], "b": c["link_b"].split("/")[-1]}


def device(client) -> TestClient:
    """Another browser on the same running app (its own cookies)."""
    return TestClient(client.app)


def as_b(client, case) -> TestClient:
    """B's device, bound to B's link."""
    b = device(client)
    assert b.post(f"/api/b/{case['b']}/open").status_code == 200
    return b


def settled(client, path, n, timeout=5.0):
    """Wait until hearing `n` of the personal page at `path` is decided."""
    return wait_for(client, path, lambda v: len(v.get("hearings", [])) > n
                    and v["hearings"][n]["status"] == "decided", timeout)


def decided(client, case, text_b=TEXT_B):
    """B submits; returns (B's device, A's page once the verdict is in)."""
    b = as_b(client, case)
    assert b.post(f"/api/b/{case['b']}/submit", json={"text_b": text_b}).status_code == 200
    return b, settled(client, f"/api/a/{case['a']}", 0)
