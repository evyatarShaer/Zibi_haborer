"""Hearing storage + 7-day cleanup (P2A-2), on a temp DB with an injected clock."""
import sqlite3
import threading

import pytest

from borer_api.store import RETENTION_S, Store, cleanup_loop

DAY = 24 * 3600
ARGS = ("דנה", "יוסי", "פיצה עם אננס זה טעים", "אננס על פיצה זה פשע")


def result(outcome="win", winner="A"):
    """Shape of borer_sim.hearing.run's result."""
    metrics = {"A": 30.0, "B": 20.0, "gap": 0.2, "winner": winner, "outcome": outcome}
    return {"seed": 5, "mood": {"hunger": 0.3, "arousal": 0.2}, "metrics": metrics,
            "brain": {"bin_ms": 50, "mn9_hz": [[1.0], [2.0]]}, "sim_version": "0.8.1",
            "platform": "test", "duration_ms": 7000}


class Clock:
    def __init__(self):
        self.t = 1_000_000_000.0

    def __call__(self):
        return self.t


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def store(tmp_path, clock):
    s = Store(str(tmp_path / "h.sqlite3"), clock)
    yield s
    s.close()


def test_schema_created_on_first_run(tmp_path):
    path = tmp_path / "new.sqlite3"
    Store(str(path)).close()
    tables = sqlite3.connect(path).execute("SELECT name FROM sqlite_master WHERE type='table'")
    assert ("hearing",) in tables.fetchall()
    Store(str(path)).close()  # reopening an existing DB keeps working


def test_create_running_then_decided(store):
    hid = store.create(*ARGS, seed=5, topic="פיצה")
    h = store.get(hid)
    assert h["status"] == "running" and h["topic"] == "פיצה" and h["metrics"] is None
    store.finish(hid, result())
    h = store.get(hid)
    assert h["status"] == "decided" and h["outcome"] == "win" and h["winner"] == "A"
    assert h["metrics"]["A"] == 30.0 and h["brain"]["mn9_hz"] == [[1.0], [2.0]]
    assert (h["hunger"], h["arousal"], h["sim_version"]) == (0.3, 0.2, "0.8.1")


@pytest.mark.parametrize("outcome", ["tie", "froze", "food"])
def test_no_winner_for_outcomes_that_name_no_side(store, outcome):
    hid = store.create(*ARGS, seed=1)
    store.finish(hid, result(outcome, "B"))
    assert store.get(hid)["winner"] is None


def test_dithered_names_a_side(store):
    hid = store.create(*ARGS, seed=1)
    store.finish(hid, result("dithered", "B"))
    assert store.get(hid)["winner"] == "B"


def test_ids_unguessable_and_unknown_is_none(store):
    ids = {store.create(*ARGS, seed=i) for i in range(50)}
    assert len(ids) == 50 and all(len(i) >= 12 for i in ids)
    assert store.get("nope") is None


def test_appeal_link_one_per_hearing(store):
    orig = store.create(*ARGS, seed=1)
    app = store.create(*ARGS, seed=2, appeal_of=orig)
    assert store.get(app)["appeal_of"] == orig and store.appeal_of(orig)["id"] == app
    assert store.appeal_of(app) is None
    with pytest.raises(sqlite3.IntegrityError):
        store.create(*ARGS, seed=3, appeal_of=orig)
    with pytest.raises(sqlite3.IntegrityError):
        store.create(*ARGS, seed=3, appeal_of="missing")


def test_fail_and_fail_running(store):
    a, b = store.create(*ARGS, seed=1), store.create(*ARGS, seed=2)
    store.finish(b, result())
    assert store.fail_running() == 1
    assert store.get(a)["status"] == "failed" and store.get(b)["status"] == "decided"


def test_purge_removes_exactly_rows_older_than_7_days(store, clock):
    old = store.create(*ARGS, seed=1)
    clock.t += 1
    edge = store.create(*ARGS, seed=2)  # exactly 7 days old at purge time: kept
    clock.t += 3 * DAY
    young = store.create(*ARGS, seed=3)
    clock.t += RETENTION_S - 3 * DAY
    assert store.purge() == 1
    assert store.get(old) is None and store.get(edge) and store.get(young)
    clock.t += 1
    assert store.purge() == 1 and store.get(edge) is None and store.get(young)


def test_appeal_deleted_with_its_original(store, clock):
    orig = store.create(*ARGS, seed=1)
    clock.t += DAY
    app = store.create(*ARGS, seed=2, appeal_of=orig)
    clock.t += RETENTION_S - DAY + 1
    store.purge()
    assert store.get(orig) is None and store.get(app) is None


def test_expired_reads_as_gone_before_purge(store, clock):
    hid = store.create(*ARGS, seed=1)
    clock.t += RETENTION_S + 1
    assert store.get(hid) is None


def test_cleanup_loop_purges_at_start_and_stops(store, clock):
    hid = store.create(*ARGS, seed=1)
    clock.t += RETENTION_S + 1
    stop = threading.Event()
    t = threading.Thread(target=cleanup_loop, args=(store, stop, 0.01))
    t.start()
    stop.set()
    t.join(timeout=2)
    assert not t.is_alive()
    assert store._run("SELECT COUNT(*) FROM hearing WHERE id = ?", (hid,)).fetchone()[0] == 0
