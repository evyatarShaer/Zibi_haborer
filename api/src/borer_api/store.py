"""SQLite storage of hearings (SPEC §14) and the 7-day retention cleanup (§14.7).

One row per hearing. An appeal points to its original (`appeal_of`, at most one per
original) and is deleted with it. `metrics` and `brain` hold borer_sim.hearing's
result as JSON. Times are Unix seconds; the clock is injectable for tests. Rows past
retention read as gone even before the cleanup has deleted them.
"""
import json
import secrets
import sqlite3
import threading
import time

RETENTION_S = 7 * 24 * 3600
WINS = ("win", "dithered")  # outcomes that name a side (SPEC §7)

SCHEMA = """
CREATE TABLE IF NOT EXISTS hearing (
    id          TEXT PRIMARY KEY,
    created_at  REAL NOT NULL,
    topic       TEXT,
    name_a      TEXT NOT NULL,
    name_b      TEXT NOT NULL,
    text_a      TEXT NOT NULL,
    text_b      TEXT NOT NULL,
    seed        INTEGER NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('queued', 'running', 'decided', 'failed')),
    hunger      REAL,
    arousal     REAL,
    metrics     TEXT,
    outcome     TEXT,
    winner      TEXT CHECK (winner IN ('A', 'B')),
    brain       TEXT,
    sim_version TEXT,
    platform    TEXT,
    duration_ms INTEGER,
    appeal_of   TEXT UNIQUE REFERENCES hearing(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS hearing_created ON hearing(created_at);
"""
JSON_COLUMNS = ("metrics", "brain")


class Store:
    """Thread-safe access to one SQLite file (created with its schema on first use)."""

    def __init__(self, path: str, clock=time.time):
        self.clock, self._lock = clock, threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript(SCHEMA)

    def _run(self, sql: str, args=()) -> int:
        """Execute; returns the changed row count."""
        with self._lock:
            return self._db.execute(sql, args).rowcount

    def _one(self, sql: str, args=()) -> dict | None:
        """First row, decoded; fetched under the lock (one connection, many threads)."""
        with self._lock:
            return _decode(self._db.execute(sql, args).fetchone())

    def create(self, name_a: str, name_b: str, text_a: str, text_b: str, seed: int,
               mood: dict, topic: str | None = None, appeal_of: str | None = None) -> str:
        """New queued hearing with its mood ({hunger, arousal}, known from the seed before
        the simulation runs); returns its unguessable id. Raises sqlite3.IntegrityError if
        `appeal_of` already has an appeal or does not exist."""
        hid = secrets.token_urlsafe(9)
        self._run("INSERT INTO hearing (id, created_at, topic, name_a, name_b, text_a, text_b, "
                  "seed, hunger, arousal, status, appeal_of) "
                  "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?)",
                  (hid, self.clock(), topic, name_a, name_b, text_a, text_b, seed,
                   mood["hunger"], mood["arousal"], appeal_of))
        return hid

    def finish(self, hid: str, result: dict) -> None:
        """Store a borer_sim.hearing.run result; the winner only for outcomes that name one."""
        m = result["metrics"]
        self._run("UPDATE hearing SET status = 'decided', metrics = ?, outcome = ?, winner = ?, "
                  "brain = ?, sim_version = ?, platform = ?, duration_ms = ? WHERE id = ?",
                  (json.dumps(m),
                   m["outcome"], m["winner"] if m["outcome"] in WINS else None,
                   json.dumps(result["brain"]), result["sim_version"], result["platform"],
                   result["duration_ms"], hid))

    def start(self, hid: str) -> None:
        self._run("UPDATE hearing SET status = 'running' WHERE id = ?", (hid,))

    def fail(self, hid: str) -> None:
        self._run("UPDATE hearing SET status = 'failed' WHERE id = ?", (hid,))

    def fail_unfinished(self) -> int:
        """At startup: hearings queued or running in a previous process can never finish."""
        return self._run("UPDATE hearing SET status = 'failed' "
                         "WHERE status IN ('queued', 'running')")

    def delete(self, hid: str) -> None:
        """Drop a hearing that was never queued (the court was full)."""
        self._run("DELETE FROM hearing WHERE id = ?", (hid,))

    def get(self, hid: str) -> dict | None:
        return self._one("SELECT * FROM hearing WHERE id = ? AND created_at >= ?",
                         (hid, self.clock() - RETENTION_S))

    def appeal_of(self, hid: str) -> dict | None:
        """The appeal hearing filed against `hid`, if any."""
        return self._one("SELECT * FROM hearing WHERE appeal_of = ? AND created_at >= ?",
                         (hid, self.clock() - RETENTION_S))

    def purge(self) -> int:
        """Delete hearings older than RETENTION_S (their appeals go with them)."""
        return self._run("DELETE FROM hearing WHERE created_at < ?", (self.clock() - RETENTION_S,))

    def close(self) -> None:
        self._db.close()


def _decode(row) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    for k in JSON_COLUMNS:
        if d.get(k) is not None:
            d[k] = json.loads(d[k])
    return d


def cleanup_loop(store: Store, stop: threading.Event, every_s: float = 3600) -> None:
    """Purge at once, then every `every_s` until `stop` is set (run in a thread)."""
    while True:
        store.purge()
        if stop.wait(every_s):
            return
