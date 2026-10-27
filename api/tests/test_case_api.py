"""Case API (P2B-6) with a fake simulation and a settable clock: the two-link flow,
blind writing, the deadline, the nudge, one courtroom."""
import json

import pytest
from fastapi.testclient import TestClient

from apikit import as_b, decided, device, open_case, settled
from borer_api import court, views
from borer_api.app import create_app
from borer_sim import mood
from fake import OK, TEXT_B, FakeSim, wait_for

HOUR = 3600


def test_two_link_flow(client, sim, clock):
    case = open_case(client)
    a = client.get(f"/api/a/{case['a']}").json()
    assert (a["status"], a["you"], a["text_a"], a["text_b"], a["hearings"]) == \
        ("waiting", "A", OK["text_a"], None, [])
    assert a["link_b"] == case["link_b"] and a["deadline_in_s"] == 3 * HOUR
    clock.t += 1.5 * HOUR
    b, a = decided(client, case)
    [h] = a["hearings"]
    assert sim.calls == [(OK["text_a"], TEXT_B, sim.calls[0][2], 1.5)]
    m = mood.from_case(sim.calls[0][2], 1.5)
    assert h["mood"] == {"hunger": m.hunger, "arousal": m.arousal} and h["wait_h"] == 1.5
    assert (h["outcome"], h["winner"], h["winner_name"], h["appetite"]) == \
        ("win", "A", "דנה", {"A": 30.0, "B": 20.0})
    assert a["status"] == "decided" and a["text_b"] == TEXT_B and "link_b" not in a
    bv = b.get(f"/api/b/{case['b']}").json()
    assert bv["text_a"] == OK["text_a"] and bv["you"] == "B" and bv["hearings"] == a["hearings"]


def test_b_never_receives_text_a_while_waiting(client, sim):
    sim.gate.clear()
    case = open_case(client)
    b = device(client)
    seen = [b.get(f"/api/b/{case['b']}"), b.get(f"/api/b/{case['b']}"),
            b.post(f"/api/b/{case['b']}/submit", json={"text_b": "קצר"}),
            b.post(f"/api/b/{case['b']}/appeal"), b.get(f"/api/b/{case['b']}/brain/0"),
            b.get(f"/api/c/{case['case_id']}")]
    assert all(OK["text_a"] not in r.text for r in seen)
    assert seen[1].json()["text_a"] is None
    b.post(f"/api/b/{case['b']}/submit", json={"text_b": TEXT_B})
    running = wait_for(b, f"/api/b/{case['b']}", lambda v: v["hearings"][0]["status"] == "running")
    assert running["text_a"] == OK["text_a"]  # both written: no longer blind
    sim.gate.set()


def test_wrong_and_gone_tokens_are_the_same_404(client, clock):
    case = open_case(client)
    wrong = [client.get("/api/a/nope"), client.get(f"/api/a/{case['b']}"),
             device(client).get(f"/api/b/{case['a']}"), client.get("/api/c/nope"),
             client.post("/api/a/nope/appeal"), client.get("/api/b/nope")]
    clock.t += 7 * 24 * HOUR + 1
    gone = [client.get(f"/api/a/{case['a']}"), client.get(f"/api/c/{case['case_id']}"),
            device(client).get(f"/api/b/{case['b']}")]
    assert {(r.status_code, r.text) for r in wrong + gone} == \
        {(404, json.dumps({"error": views.CLOSED}, ensure_ascii=False, separators=(",", ":")))}


def test_hidden_case_is_closed_everywhere(client):
    case = open_case(client)
    b, _ = decided(client, case)
    client.app.state.store._run('UPDATE "case" SET hidden_at = 1')
    for r in (client.get(f"/api/a/{case['a']}"), b.get(f"/api/b/{case['b']}"),
              client.get(f"/api/c/{case['case_id']}"), client.post(f"/api/a/{case['a']}/appeal")):
        assert r.status_code == 404 and r.json()["error"] == views.CLOSED


def test_deadline_fires_the_water_hearing(client, sim, clock):
    case = open_case(client)
    clock.t += 3 * HOUR - 1
    assert client.get(f"/api/a/{case['a']}").json()["status"] == "waiting"
    clock.t += 1
    a = settled(client, f"/api/a/{case['a']}", 0)
    assert sim.calls == [(OK["text_a"], None, sim.calls[0][2], 3.0)]
    assert a["status"] == "no_show" and a["no_show"] and a["hearings"][0]["wait_h"] == 3.0
    b = device(client)
    r = b.get(f"/api/b/{case['b']}")  # B comes late: only the public card, no arguments
    assert r.json()["public_only"]["status"] == "no_show" and OK["text_a"] not in r.text
    for path in ("brain/0", "appeal"):
        r = (b.get if path.startswith("brain") else b.post)(f"/api/b/{case['b']}/{path}")
        assert r.status_code == 409 and OK["text_a"] not in r.text
    r = b.post(f"/api/b/{case['b']}/submit", json={"text_b": TEXT_B})
    assert r.status_code == 409 and r.json()["error"] == views.LATE


def test_b_after_deadline_before_sweep_is_late(client, clock, sim):
    case = open_case(client)
    b = as_b(client, case)
    sim.gate.clear()
    clock.t += 3 * HOUR
    r = b.post(f"/api/b/{case['b']}/submit", json={"text_b": TEXT_B})
    assert r.status_code == 409 and r.json()["error"] == views.LATE
    sim.gate.set()


def test_nudge_from_one_hour(client, clock):
    case = open_case(client)
    clock.t += HOUR - 1
    assert client.get(f"/api/a/{case['a']}").json()["nudge"] is False
    clock.t += 1
    assert client.get(f"/api/a/{case['a']}").json()["nudge"] is True


def test_one_courtroom_then_busy_and_b_can_retry(client, sim):
    sim.gate.clear()
    cases = [open_case(client) for _ in range(court.MAX_ACTIVE + 1)]
    bs = [as_b(client, c) for c in cases]
    for b, c in zip(bs[:-1], cases):
        assert b.post(f"/api/b/{c['b']}/submit", json={"text_b": TEXT_B}).status_code == 200
    r = bs[-1].post(f"/api/b/{cases[-1]['b']}/submit", json={"text_b": TEXT_B})
    assert r.status_code == 503 and r.json()["error"] == court.BUSY
    assert bs[-1].get(f"/api/b/{cases[-1]['b']}").json()["status"] == "waiting"
    assert len(sim.calls) == 1  # one at a time
    sim.gate.set()
    assert bs[-1].post(f"/api/b/{cases[-1]['b']}/submit", json={"text_b": TEXT_B}).status_code == 200
    for c in cases:
        settled(client, f"/api/a/{c['a']}", 0)


def test_resume_after_restart(tmp_path):
    db, sim = str(tmp_path / "c.sqlite3"), FakeSim()
    sim.gate.clear()
    with TestClient(create_app(sim, db)) as c:
        case = open_case(c)
        as_b(c, case).post(f"/api/b/{case['b']}/submit", json={"text_b": TEXT_B})
        wait_for(c, f"/api/a/{case['a']}", lambda v: v["hearings"][0]["status"] == "running")
    with TestClient(create_app(FakeSim(), db)) as c:  # old court still blocked: "process died"
        assert settled(c, f"/api/a/{case['a']}", 0)["status"] == "decided"
    sim.gate.set()


class Flaky(FakeSim):
    """Raises on its first `fails` runs."""

    def __init__(self, fails):
        super().__init__()
        self.fails = fails

    def __call__(self, *args):
        if self.fails:
            self.fails -= 1
            self.calls.append(args)
            raise RuntimeError("sim crashed")
        return super().__call__(*args)


@pytest.mark.parametrize("fails, status", [(2, "decided"), (3, "error")])
def test_failed_run_retried_twice_from_the_same_seed(tmp_path, fails, status):
    sim = Flaky(fails)
    with TestClient(create_app(sim, str(tmp_path / "c.sqlite3"))) as c:
        case = open_case(c)
        b = as_b(c, case)
        b.post(f"/api/b/{case['b']}/submit", json={"text_b": TEXT_B})
        a = wait_for(c, f"/api/a/{case['a']}", lambda v: v["status"] == status)
        assert len(sim.calls) == court.ATTEMPTS and len(set(sim.calls)) == 1
        if status == "error":
            assert a["hearings"][0]["status"] == "failed" and a["error_message"] == views.FAILED
            assert not a["can_appeal"] and not a["no_show"]
            pub = c.get(f"/api/c/{case['case_id']}").json()
            assert (pub["status"], pub["error_message"]) == ("error", views.FAILED)
        else:
            assert a["error_message"] is None


@pytest.mark.parametrize("field, value", [
    ("text_a", "קצר מדי"), ("text_a", "א" * 281), ("name_b", "   "), ("name_a", "ש" * 31),
    ("topic", "ת" * 81)])
def test_open_rules_in_hebrew(client, field, value):
    r = client.post("/api/case", json=OK | {field: value})
    assert r.status_code == 422 and field in r.json()["errors"]
    assert any("א" <= ch <= "ת" for ch in r.json()["errors"][field])


def test_b_text_rules_and_optional_topic(client, sim):
    case = open_case(client, OK | {"topic": "  "})
    b = as_b(client, case)
    r = b.post(f"/api/b/{case['b']}/submit", json={"text_b": "hello world, long but not Hebrew"})
    assert r.status_code == 422 and "text_b" in r.json()["errors"] and not sim.calls
    assert b.post(f"/api/b/{case['b']}/submit", json={"text_b": "אבגדה וזחטי!"}).status_code == 200
    assert settled(client, f"/api/a/{case['a']}", 0)["topic"] is None
