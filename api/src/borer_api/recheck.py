"""Determinism check (SPEC §12, 2A exit): rerun every decided hearing in the DB from its
stored seed and texts; metrics, outcome, winner, mood and brain summary must be
bit-identical. Read-only on the DB, so the server can keep running.
Run: cd api && PYTHONPATH=src:../sim/src uv run python -m borer_api.recheck [db]"""
import json
import sqlite3
import sys

from borer_api.app import DB
from borer_api.store import WINS, _decode
from borer_sim import hearing
from borer_sim.version import SIM_VERSION


def stored_hearings(path: str) -> list[dict]:
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    rows = db.execute("SELECT * FROM hearing WHERE status = 'decided' ORDER BY created_at")
    return [_decode(r) for r in rows]


def mismatches(row: dict, rerun: dict) -> list[str]:
    """Fields of the stored row that differ from the rerun (JSON round trip, as stored)."""
    m = json.loads(json.dumps(rerun["metrics"]))
    fresh = {"metrics": m, "outcome": m["outcome"],
             "winner": m["winner"] if m["outcome"] in WINS else None,
             "hunger": rerun["mood"]["hunger"], "arousal": rerun["mood"]["arousal"],
             "brain": json.loads(json.dumps(rerun["brain"])), "platform": rerun["platform"]}
    return [k for k, v in fresh.items() if row[k] != v]


def main(path: str) -> int:
    rows = stored_hearings(path)
    other = [r["id"] for r in rows if r["sim_version"] != SIM_VERSION]
    if other:
        print(f"stored under another sim_version than {SIM_VERSION}: {other}")
        return 1
    bad = 0
    with hearing.workers(method="forkserver") as pool:
        for r in rows:
            diff = mismatches(r, hearing.run(pool, r["text_a"], r["text_b"], r["seed"]))
            bad += bool(diff)
            print(f"{r['id']} seed {r['seed']} {r['outcome']}/{r['winner']} "
                  f"appeal_of={r['appeal_of']}: {'MISMATCH ' + str(diff) if diff else 'identical'}",
                  flush=True)
    print(f"{len(rows) - bad}/{len(rows)} bit-identical (SIM_VERSION {SIM_VERSION})")
    return 1 if bad or not rows else 0


if __name__ == "__main__":  # guard: forkserver workers import this module too
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DB))
