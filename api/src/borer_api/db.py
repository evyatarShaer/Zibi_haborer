"""Phase 2B SQLite schema (SPEC §10), connection helpers, counters and the 7-day purge.

Everything about a case (hearings, reports) is deleted 7 days after case open; the
aggregate `counter` table holds no case data and is kept. Times are Unix seconds; the
clock is injectable for tests. Days are UTC dates ("YYYY-MM-DD").
"""
import json
import sqlite3
import threading
import time
from contextlib import contextmanager

RETENTION_S = 7 * 24 * 3600
JSON_COLUMNS = ("metrics", "brain")

SCHEMA = """
CREATE TABLE IF NOT EXISTS "case" (
    id             TEXT PRIMARY KEY,
    created_at     REAL NOT NULL,
    deadline_at    REAL NOT NULL,
    topic          TEXT,
    name_a         TEXT NOT NULL,
    name_b         TEXT NOT NULL,
    text_a         TEXT NOT NULL,
    text_b         TEXT,
    b_submitted_at REAL,
    token_a_hash   TEXT NOT NULL UNIQUE,
    token_b_hash   TEXT NOT NULL UNIQUE,
    a_device_hash  TEXT,
    b_device_hash  TEXT,
    ip_hash        TEXT NOT NULL,
    day            TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'waiting'
                   CHECK (status IN ('waiting', 'hearing', 'decided', 'no_show', 'error')),
    hidden_at      REAL,
    shared_at      REAL
);
CREATE INDEX IF NOT EXISTS case_created ON "case"(created_at);
CREATE INDEX IF NOT EXISTS case_ip_day ON "case"(ip_hash, day);
CREATE INDEX IF NOT EXISTS case_due ON "case"(status, deadline_at);
CREATE TABLE IF NOT EXISTS hearing (
    id          INTEGER PRIMARY KEY,
    case_id     TEXT NOT NULL REFERENCES "case"(id) ON DELETE CASCADE,
    n           INTEGER NOT NULL CHECK (n BETWEEN 0 AND 2),
    appealed_by TEXT CHECK (appealed_by IN ('A', 'B')),
    seed        INTEGER NOT NULL,
    wait_h      REAL NOT NULL,
    hunger      REAL NOT NULL,
    arousal     REAL NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('queued', 'running', 'decided', 'failed')),
    metrics     TEXT,
    outcome     TEXT,
    winner      TEXT CHECK (winner IN ('A', 'B')),
    brain       TEXT,
    sim_version TEXT,
    platform    TEXT,
    duration_ms INTEGER,
    created_at  REAL NOT NULL,
    decided_at  REAL,
    UNIQUE (case_id, n),
    UNIQUE (case_id, appealed_by),
    CHECK ((n = 0) = (appealed_by IS NULL))
);
CREATE INDEX IF NOT EXISTS hearing_status ON hearing(status);
CREATE TABLE IF NOT EXISTS report (
    id         INTEGER PRIMARY KEY,
    case_id    TEXT NOT NULL REFERENCES "case"(id) ON DELETE CASCADE,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS counter (
    day   TEXT NOT NULL,
    event TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (day, event)
);
"""


class Db:
    """Thread-safe access to one SQLite file (created with its schema on first use)."""

    def __init__(self, path: str, clock=time.time):
        self.clock, self._lock = clock, threading.RLock()
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript(SCHEMA)

    def _run(self, sql: str, args=()) -> int:
        """Execute; returns the changed row count."""
        with self._lock:
            return self._db.execute(sql, args).rowcount

    def _one(self, sql: str, args=()) -> dict | None:
        with self._lock:
            return decode(self._db.execute(sql, args).fetchone())

    def _all(self, sql: str, args=()) -> list[dict]:
        with self._lock:
            return [decode(r) for r in self._db.execute(sql, args).fetchall()]

    @contextmanager
    def _tx(self):
        """One write transaction; _run/_one/_all may be used inside it (same thread)."""
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                self._db.execute("ROLLBACK")
                raise
            self._db.execute("COMMIT")

    def day(self) -> str:
        return time.strftime("%Y-%m-%d", time.gmtime(self.clock()))

    def bump(self, event: str) -> None:
        """Add one to today's aggregate counter for `event`."""
        self._run("INSERT INTO counter (day, event, count) VALUES (?, ?, 1) "
                  "ON CONFLICT (day, event) DO UPDATE SET count = count + 1",
                  (self.day(), event))

    def counters(self) -> list[dict]:
        return self._all("SELECT * FROM counter ORDER BY day, event")

    def oldest_kept(self) -> float:
        """Cases opened before this time are past retention (they read as gone)."""
        return self.clock() - RETENTION_S

    def purge(self) -> int:
        """Delete cases opened more than 7 days ago, with their hearings and reports."""
        return self._run('DELETE FROM "case" WHERE created_at < ?', (self.oldest_kept(),))

    def close(self) -> None:
        self._db.close()


def decode(row) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    for k in JSON_COLUMNS:
        if d.get(k) is not None:
            d[k] = json.loads(d[k])
    return d


def cleanup_loop(store: Db, stop: threading.Event, every_s: float = 3600) -> None:
    """Purge at once, then every `every_s` until `stop` is set (run in a thread)."""
    while True:
        store.purge()
        if stop.wait(every_s):
            return
