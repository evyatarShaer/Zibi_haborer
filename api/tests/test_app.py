"""API (P2A-3) with a fake simulation: rules, statuses, queue limit, response allowlist."""
import json
import time

import pytest
from fastapi.testclient import TestClient

from borer_api import court
from borer_api.app import create_app
from borer_sim import mood, taste
from fake import OK, FakeSim, wait_status

def test_hearing_queued_to_decided(client, sim):
    hid = client.post("/hearing", json=OK).json()["id"]
    h = wait_status(client, hid, "decided")
    assert h["outcome"] == "win" and h["winner"] == "A" and h["winner_name"] == "דנה"
    assert h["appetite"] == {"A": 30.0, "B": 20.0} and h["topic"] == "פיצה" and h["can_appeal"]
    assert sim.calls[0][:2] == (OK["text_a"], OK["text_b"])
    m = mood.product(sim.calls[0][2])
    assert h["mood"] == {"hunger": m.hunger, "arousal": m.arousal}


def test_mood_visible_while_waiting(client, sim):
    sim.gate.clear()
    hid = client.post("/hearing", json=OK).json()["id"]
    h = wait_status(client, hid, "running")
    assert set(h["mood"]) == {"hunger", "arousal"} and "outcome" not in h and not h["can_appeal"]
    assert client.get(f"/hearing/{hid}/brain").status_code == 409
    sim.gate.set()


@pytest.mark.parametrize("field, value, key", [
    ("text_a", "קצר מדי", "text_a"),             # 6 Hebrew letters
    ("text_b", "hello world, long but not Hebrew", "text_b"),
    ("text_a", "א" * 281, "text_a"),
    ("name_b", "   ", "name_b"),
    ("name_a", "ש" * 31, "name_a"),
    ("topic", "ת" * 81, "topic"),
])
def test_rules_rejected_in_hebrew(client, sim, field, value, key):
    r = client.post("/hearing", json=OK | {field: value})
    assert r.status_code == 422 and key in r.json()["errors"]
    assert any("א" <= c <= "ת" for c in r.json()["errors"][key]) and not sim.calls


def test_ten_letters_exactly_accepted_topic_optional(client):
    body = OK | {"text_a": "אבגדה וזחטי!", "topic": "  "}
    hid = client.post("/hearing", json=body).json()["id"]
    assert wait_status(client, hid, "decided")["topic"] is None


def test_unknown_id_404(client):
    assert client.get("/hearing/nope").status_code == 404
    assert client.get("/hearing/nope/brain").status_code == 404


def test_one_running_three_waiting_then_busy(client, sim):
    sim.gate.clear()
    first = client.post("/hearing", json=OK).json()["id"]
    wait_status(client, first, "running")
    queued = [client.post("/hearing", json=OK).json()["id"] for _ in range(court.MAX_WAITING)]
    assert all(client.get(f"/hearing/{q}").json()["status"] == "queued" for q in queued)
    r = client.post("/hearing", json=OK)
    assert r.status_code == 503 and r.json()["error"] == court.BUSY
    assert len(sim.calls) == 1  # one at a time
    sim.gate.set()
    for q in queued:
        wait_status(client, q, "decided")


@pytest.mark.parametrize("outcome", ["tie", "froze", "food"])
def test_outcomes_without_a_side(tmp_path, outcome):
    with TestClient(create_app(FakeSim(outcome, "B"), str(tmp_path / "h.sqlite3"))) as c:
        h = wait_status(c, c.post("/hearing", json=OK).json()["id"], "decided")
    assert h["outcome"] == outcome and h["winner"] is None and h["winner_name"] is None


def test_failed_simulation_is_failed(tmp_path):
    def boom(a, b, seed):
        raise RuntimeError("sim crashed")
    with TestClient(create_app(boom, str(tmp_path / "h.sqlite3"))) as c:
        wait_status(c, c.post("/hearing", json=OK).json()["id"], "failed")


def test_unfinished_hearings_fail_at_restart(tmp_path):
    db, sim = str(tmp_path / "h.sqlite3"), FakeSim()
    sim.gate.clear()
    with TestClient(create_app(sim, db)) as c:
        hid = c.post("/hearing", json=OK).json()["id"]
        wait_status(c, hid, "running")
    with TestClient(create_app(FakeSim(), db)) as c:  # old court still blocked: "process died"
        assert c.get(f"/hearing/{hid}").json()["status"] == "failed"
    sim.gate.set()


def test_responses_allowlisted_no_table_data(client):
    hid = client.post("/hearing", json=OK).json()["id"]
    h = wait_status(client, hid, "decided")
    assert set(h) == {"id", "status", "topic", "name_a", "name_b", "text_a", "text_b", "appeal_of",
                      "mood", "can_appeal", "appeal_id", "outcome", "winner", "winner_name",
                      "appetite"}
    brain = client.get(f"/hearing/{hid}/brain").json()
    assert set(brain) == {"bin_ms", "mn9_hz", "mood", "seed", "sim_version", "platform"}
    text = json.dumps([h, brain], ensure_ascii=False)
    groups = {name.split(":")[1].split("/")[0] for name, _ in taste.TABLE.values()}
    assert not any(g in text for g in groups) and "metrics" not in text


def test_purge_loop_runs_in_lifespan(tmp_path, sim):
    db = str(tmp_path / "h.sqlite3")
    from borer_api.store import RETENTION_S, Store
    old = Store(db, clock=lambda: time.time() - RETENTION_S - 10)
    hid = old.create("א", "ב", OK["text_a"], OK["text_b"], 1, {"hunger": 0, "arousal": 0})
    with TestClient(create_app(sim, db)):
        time.sleep(0.2)
    assert old._one("SELECT COUNT(*) AS n FROM hearing WHERE id = ?", (hid,))["n"] == 0


def test_serves_the_page(client):
    r = client.get("/")
    assert r.status_code == 200 and 'dir="rtl"' in r.text
