"""Case storage (P2B-5): 7-day purge, counters kept, expiry on read (injected clock)."""
import threading

from borer_api.db import RETENTION_S, cleanup_loop
from casekit import DAY, decided_case, opened


def test_purge_exactly_7_days_with_children_counters_kept(store, clock):
    old = decided_case(store, clock)
    store._run("INSERT INTO report (case_id, created_at) VALUES (?, ?)", (old["id"], clock.t))
    store.bump("cases_opened")
    clock.t += 1
    edge = opened(store)  # exactly 7 days old at purge time: kept
    clock.t += RETENTION_S
    assert store.purge() == 1
    assert store.case(old["id"]) is None and store.case(edge["id"])
    assert store._all("SELECT * FROM hearing WHERE case_id = ?", (old["id"],)) == []
    assert store._all("SELECT * FROM report") == []
    clock.t += 1
    assert store.purge() == 1 and store.case(edge["id"]) is None
    [row] = store.counters()
    assert (row["event"], row["count"]) == ("cases_opened", 1)


def test_expired_reads_as_gone_before_purge(store, clock):
    c = opened(store)
    clock.t += RETENTION_S + 1
    assert store.case(c["id"]) is None and store.by_token(c["token_a"]) is None
    assert store.due() == []


def test_counters_per_utc_day(store, clock):
    store.bump("cases_shared")
    store.bump("cases_shared")
    clock.t += DAY
    store.bump("cases_shared")
    assert [(r["day"], r["count"]) for r in store.counters()] == [("2001-09-09", 2), ("2001-09-10", 1)]


def test_cleanup_loop_purges_at_start_and_stops(store, clock):
    opened(store)
    clock.t += RETENTION_S + 1
    stop = threading.Event()
    t = threading.Thread(target=cleanup_loop, args=(store, stop, 0.01))
    t.start()
    stop.set()
    t.join(timeout=2)
    assert not t.is_alive() and store._all('SELECT id FROM "case"') == []
