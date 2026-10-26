"""Case storage (P2B-5) on a temp DB with an injected clock: the case flow and the DB caps."""
import sqlite3

import pytest

from borer_api import tokens
from borer_api.cases import DEADLINE_S, Busy, Closed, Store
from borer_sim import mood
from casekit import CASE, HOUR, TEXT_B, decide, decided_case, opened


def test_schema(tmp_path):
    path = tmp_path / "new.sqlite3"
    Store(str(path)).close()
    rows = sqlite3.connect(path).execute("SELECT name FROM sqlite_master WHERE type='table'")
    assert {r[0] for r in rows} == {"case", "hearing", "report", "counter"}
    Store(str(path)).close()  # reopening an existing DB keeps working


def test_tokens_hashed_and_resolve_to_their_side(store, tmp_path):
    c = opened(store)
    assert store.by_token(c["token_a"])[1] == "A" and store.by_token(c["token_b"])[1] == "B"
    assert store.by_token(c["token_a"])[0]["id"] == c["id"] and store.by_token("nope") is None
    assert c["token_b"] == tokens.side_b(c["token_a"]) and len(c["token_a"]) >= 22
    dump = "\n".join(sqlite3.connect(tmp_path / "c.sqlite3").iterdump())
    assert c["token_a"] not in dump and c["token_b"] not in dump and "1.2.3.4" not in dump
    assert len({opened(store)["token_a"] for _ in range(50)}) == 50


def test_create_b_submits_decided(store, clock):
    c = opened(store)
    assert store.case(c["id"])["status"] == "waiting" and store.case(c["id"])["text_b"] is None
    clock.t += 1.5 * HOUR
    hid = store.submit_b(c["id"], TEXT_B, seed=7)
    case = store.case(c["id"])
    assert case["status"] == "hearing" and case["text_b"] == TEXT_B
    [h] = store.hearings(c["id"])
    m = mood.from_case(7, 1.5)
    assert (h["n"], h["appealed_by"], h["status"], h["wait_h"]) == (0, None, "queued", 1.5)
    assert (h["hunger"], h["arousal"]) == (m.hunger, m.arousal)
    q = store.next_queued()
    assert (q["id"], q["text_a"], q["text_b"], q["seed"]) == (hid, CASE[3], TEXT_B, 7)
    decide(store, hid, "dithered", "B")
    h = store.hearings(c["id"])[0]
    assert (h["status"], h["outcome"], h["winner"], h["decided_at"]) == ("decided", "dithered", "B", clock.t)
    assert store.case(c["id"])["status"] == "decided" and store.next_queued() is None


def test_b_cannot_write_after_deadline_no_show_is_water(store, clock):
    c = opened(store)
    assert store.due() == []
    clock.t += DEADLINE_S
    assert store.due() == [c["id"]]
    with pytest.raises(Closed):
        store.submit_b(c["id"], TEXT_B, seed=1)
    hid = store.no_show(c["id"], seed=3)
    assert store.due() == [] and store.next_queued()["text_b"] is None
    assert store.hearings(c["id"])[0]["wait_h"] == 3.0
    with pytest.raises(Closed):
        store.no_show(c["id"], seed=3)
    decide(store, hid)
    assert store.case(c["id"])["status"] == "no_show"


def test_no_show_only_after_deadline(store, clock):
    c = opened(store)
    clock.t += DEADLINE_S - 1
    with pytest.raises(Closed):
        store.no_show(c["id"], seed=1)


def test_appeals_use_case_wait_and_db_caps(store, clock):
    c = decided_case(store, clock)
    clock.t += 2 * HOUR
    first = store.appeal(c["id"], "A", seed=2)
    with pytest.raises(Closed):  # nothing to appeal while a hearing is on
        store.appeal(c["id"], "B", seed=3)
    decide(store, first)
    with pytest.raises(sqlite3.IntegrityError):
        store.appeal(c["id"], "A", seed=4)
    assert store.case(c["id"])["status"] == "decided"  # the refused appeal rolled back
    decide(store, store.appeal(c["id"], "B", seed=3))
    hs = store.hearings(c["id"])
    assert [(h["n"], h["appealed_by"], h["wait_h"]) for h in hs] == [(0, None, 1), (1, "A", 1), (2, "B", 1)]
    m = mood.from_case(3, 1.0)
    assert (hs[2]["hunger"], hs[2]["arousal"]) == (m.hunger, m.arousal)
    with pytest.raises(sqlite3.IntegrityError):
        store.appeal(c["id"], "A", seed=5)


@pytest.mark.parametrize("n, by", [(3, "B"), (2, "A"), (1, None), (0, "A")])
def test_db_itself_refuses(store, clock, n, by):
    """Direct inserts, bypassing the store: 3 hearings at most, one appeal per side."""
    c = decided_case(store, clock)
    decide(store, store.appeal(c["id"], "A", seed=2))
    with pytest.raises(sqlite3.IntegrityError):
        store._run("INSERT INTO hearing (case_id, n, appealed_by, seed, wait_h, hunger, arousal, "
                   "status, created_at) VALUES (?, ?, ?, 1, 1, 0, 0, 'queued', 0)", (c["id"], n, by))


def test_court_full_is_busy_and_rolls_back(tmp_path, clock):
    s = Store(str(tmp_path / "c.sqlite3"), clock, max_active=2)
    ids = [opened(s)["id"] for _ in range(3)]
    s.submit_b(ids[0], TEXT_B, 1)
    s.start(s.submit_b(ids[1], TEXT_B, 1))
    with pytest.raises(Busy):
        s.submit_b(ids[2], TEXT_B, 1)
    c = s.case(ids[2])
    assert (c["status"], c["text_b"], c["b_submitted_at"]) == ("waiting", None, None)
    assert s.hearings(ids[2]) == []


def test_requeue_running_at_startup(store, clock):
    c = opened(store)
    hid = store.submit_b(c["id"], TEXT_B, 1)
    store.start(hid)
    assert store.next_queued() is None and store.requeue() == 1
    assert store.next_queued()["id"] == hid
