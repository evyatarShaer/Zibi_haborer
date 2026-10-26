"""Case storage (SPEC §10, §15): a case, its hearings (n 0 = verdict, 1–2 = appeals) and
the court's work list.

Case status: waiting (for B) → hearing (one queued or running) → decided, or no_show when
B never wrote (text_b NULL = plain water). An appeal sends it back to hearing. A hearing
the simulation could not run (after the court's retries) ends the case in error. Each
hearing gets its mood when it is filed: the case's wait (case open → B submits, the 3 h
deadline for a no-show) with the hearing's own seed. The DB itself allows at most 3
hearings per case and one appeal per side. Cases past retention read as gone.
"""
import json
import secrets
import time

from borer_api import tokens
from borer_api.db import Db
from borer_sim import mood
from borer_sim.params import MOOD

DEADLINE_S = MOOD["deadline_h"] * 3600
WINS = ("win", "dithered")  # outcomes that name a side (SPEC §7)
SETTLED = "CASE WHEN text_b IS NULL THEN 'no_show' ELSE 'decided' END"


class Closed(Exception):
    """The case is gone or not in a state for this step (e.g. B wrote after the deadline)."""


class Limited(Exception):
    """This IP already opened its maximum of cases today."""


class Busy(Exception):
    """The court already holds its maximum of hearings (one running + the waiting line)."""


class Store(Db):
    def __init__(self, path: str, clock=time.time, max_active: int | None = None):
        """max_active: hearings queued + running at most (None = no limit)."""
        super().__init__(path, clock)
        self.max_active = max_active

    def open(self, topic: str | None, name_a: str, name_b: str, text_a: str, ip: str,
             device: str | None = None, per_day: int | None = None) -> dict:
        """A new waiting case; returns {"id", "token_a", "token_b"} (only hashes are kept).
        Limited if `ip` already opened `per_day` cases today."""
        cid, token_a, now = secrets.token_urlsafe(9), tokens.new(), self.clock()
        ip_hash = tokens.ip(ip)
        with self._tx():
            if per_day is not None and self._one(
                    'SELECT COUNT(*) AS n FROM "case" WHERE ip_hash = ? AND day = ?',
                    (ip_hash, self.day()))["n"] >= per_day:
                raise Limited
            self._run('INSERT INTO "case" (id, created_at, deadline_at, topic, name_a, name_b, '
                      "text_a, token_a_hash, token_b_hash, a_device_hash, ip_hash, day) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (cid, now, now + DEADLINE_S, topic, name_a, name_b, text_a,
                       tokens.digest(token_a), tokens.digest(tokens.side_b(token_a)),
                       device and tokens.digest(device), ip_hash, self.day()))
        return {"id": cid, "token_a": token_a, "token_b": tokens.side_b(token_a)}

    def case(self, cid: str) -> dict | None:
        return self._one('SELECT * FROM "case" WHERE id = ? AND created_at >= ?',
                         (cid, self.oldest_kept()))

    def by_token(self, token: str) -> tuple[dict, str] | None:
        """(case, "A" | "B") for a personal-link token, or None."""
        h = tokens.digest(token)
        c = self._one('SELECT * FROM "case" WHERE (token_a_hash = ? OR token_b_hash = ?) '
                      "AND created_at >= ?", (h, h, self.oldest_kept()))
        return (c, "A" if c["token_a_hash"] == h else "B") if c else None

    def claim_b(self, cid: str, device: str) -> str | None:
        """Bind B's link to the first device that opens it through the page (SPEC §15.1).
        Returns "B" for the bound device, "A" for A's device (never bound), else None."""
        d = tokens.digest(device)
        self._run('UPDATE "case" SET b_device_hash = ? WHERE id = ? AND b_device_hash IS NULL '
                  "AND a_device_hash IS NOT ?", (d, cid, d))
        c = self.case(cid) or {}
        return "A" if c.get("a_device_hash") == d else "B" if c.get("b_device_hash") == d else None

    def hearings(self, cid: str) -> list[dict]:
        return self._all("SELECT * FROM hearing WHERE case_id = ? ORDER BY n", (cid,))

    def snapshot(self, cid: str) -> tuple[dict | None, list[dict]]:
        """The case and its hearings, read together (never between a hearing's two writes)."""
        with self._lock:
            return self.case(cid), self.hearings(cid)

    def submit_b(self, cid: str, text_b: str, seed: int) -> int:
        """B's argument before the deadline; files the verdict hearing (n 0)."""
        with self._tx():
            c = self._live(cid, "status = 'waiting' AND deadline_at > ?", (self.clock(),))
            c |= {"text_b": text_b, "b_submitted_at": self.clock()}
            self._run('UPDATE "case" SET text_b = ?, b_submitted_at = ?, status = \'hearing\' '
                      "WHERE id = ?", (text_b, c["b_submitted_at"], cid))
            return self._file(c, 0, None, seed)

    def no_show(self, cid: str, seed: int) -> int:
        """At the deadline with no argument from B: files the plain-water hearing (n 0)."""
        with self._tx():
            c = self._live(cid, "status = 'waiting' AND deadline_at <= ?", (self.clock(),))
            self._run("UPDATE \"case\" SET status = 'hearing' WHERE id = ?", (cid,))
            return self._file(c, 0, None, seed)

    def appeal(self, cid: str, side: str, seed: int) -> int:
        """An appeal by `side` once the latest hearing is decided. The DB refuses a 4th
        hearing or a second appeal by the same side (sqlite3.IntegrityError)."""
        with self._tx():
            c = self._live(cid, "status IN ('decided', 'no_show')")
            n = self._one("SELECT COUNT(*) AS n FROM hearing WHERE case_id = ?", (cid,))["n"]
            self._run("UPDATE \"case\" SET status = 'hearing' WHERE id = ?", (cid,))
            return self._file(c, n, side, seed)

    def due(self) -> list[str]:
        """Waiting, visible cases whose deadline has passed (the no-show sweep)."""
        rows = self._all("SELECT id FROM \"case\" WHERE status = 'waiting' AND deadline_at <= ? "
                         "AND hidden_at IS NULL AND created_at >= ? ORDER BY deadline_at",
                         (self.clock(), self.oldest_kept()))
        return [r["id"] for r in rows]

    def _live(self, cid: str, condition: str, args=()) -> dict:
        c = self._one(f'SELECT * FROM "case" WHERE id = ? AND created_at >= ? AND {condition}',
                      (cid, self.oldest_kept(), *args))
        if c is None:
            raise Closed(cid)
        return c

    def _file(self, c: dict, n: int, by: str | None, seed: int) -> int:
        """Queue hearing `n` of case `c` (inside a transaction); Busy if the court is full."""
        if self.max_active is not None and self._one(
                "SELECT COUNT(*) AS n FROM hearing WHERE status IN ('queued', 'running')"
        )["n"] >= self.max_active:
            raise Busy
        wait_h = ((c["b_submitted_at"] or c["deadline_at"]) - c["created_at"]) / 3600
        m = mood.from_case(seed, wait_h)
        with self._lock:
            return self._db.execute(
                "INSERT INTO hearing (case_id, n, appealed_by, seed, wait_h, hunger, arousal, "
                "status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?)",
                (c["id"], n, by, seed, wait_h, m.hunger, m.arousal, self.clock())).lastrowid

    # The court's side: take hearings in order, run them, store the result.

    def next_queued(self) -> dict | None:
        """The oldest queued hearing with its case's arguments (text_b None = water)."""
        return self._one("SELECT h.*, c.text_a, c.text_b FROM hearing h "
                         'JOIN "case" c ON c.id = h.case_id WHERE h.status = \'queued\' '
                         "ORDER BY h.created_at, h.id LIMIT 1")

    def start(self, hid: int) -> None:
        self._run("UPDATE hearing SET status = 'running' WHERE id = ?", (hid,))

    def finish(self, hid: int, result: dict) -> None:
        """Store a borer_sim.hearing.run result; the case settles on its new verdict."""
        m = result["metrics"]
        with self._tx():
            self._run("UPDATE hearing SET status = 'decided', metrics = ?, outcome = ?, "
                      "winner = ?, brain = ?, sim_version = ?, platform = ?, duration_ms = ?, "
                      "decided_at = ? WHERE id = ?",
                      (json.dumps(m), m["outcome"], m["winner"] if m["outcome"] in WINS else None,
                       json.dumps(result["brain"]), result["sim_version"], result["platform"],
                       result["duration_ms"], self.clock(), hid))
            self._run(f'UPDATE "case" SET status = {SETTLED} '
                      "WHERE id = (SELECT case_id FROM hearing WHERE id = ?)", (hid,))

    def fail(self, hid: int) -> None:
        """The hearing could not be run: it is failed and its case ends in error."""
        with self._tx():
            self._run("UPDATE hearing SET status = 'failed' WHERE id = ?", (hid,))
            self._run("UPDATE \"case\" SET status = 'error' "
                      "WHERE id = (SELECT case_id FROM hearing WHERE id = ?)", (hid,))

    def requeue(self) -> int:
        """At startup: a hearing that was running when the process died runs again."""
        return self._run("UPDATE hearing SET status = 'queued' WHERE status = 'running'")
