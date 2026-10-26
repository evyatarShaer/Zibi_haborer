"""Real brain behind the case API (P2A-3, P2B-6): startup, B submits → decided ≤ 15 s,
and stored = rerun."""
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apikit import as_b, open_case, settled
from borer_api.app import create_app
from borer_sim import hearing

pytestmark = pytest.mark.needs_data

BODY = {"name_a": "דנה", "name_b": "יוסי", "text_a": "פיצה עם אננס זה פשוט טעים ונקודה."}
TEXT_B = "הסדרה הזאת משעממת, בוא נראה משהו אחר."


def tree_rss_gb() -> float:
    """Resident memory of this process and all its descendants (forkserver workers)."""
    procs = {}
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            try:
                st = dict(l.split(":", 1) for l in (p / "status").read_text().splitlines() if ":" in l)
                procs[int(p.name)] = (int(st["PPid"]), int(st.get("VmRSS", "0 kB").split()[0]))
            except (OSError, KeyError, ValueError):
                pass
    keep, total, frontier = {os.getpid()}, 0, [os.getpid()]
    while frontier:
        parent = frontier.pop()
        total += procs.get(parent, (0, 0))[1]
        kids = [pid for pid, (pp, _) in procs.items() if pp == parent and pid not in keep]
        keep.update(kids)
        frontier += kids
    return total / 1e6


def test_real_hearing_end_to_end(tmp_path, record_property):
    t0 = time.perf_counter()
    with TestClient(create_app(db_path=str(tmp_path / "c.sqlite3"))) as c:
        startup = time.perf_counter() - t0
        times = []
        for _ in range(3):
            case = open_case(c, BODY)
            b = as_b(c, case)
            t = time.perf_counter()
            assert b.post(f"/api/b/{case['b']}/submit", json={"text_b": TEXT_B}).status_code == 200
            settled(c, f"/api/a/{case['a']}", 0, timeout=60)
            times.append(time.perf_counter() - t)
        rss = tree_rss_gb()
        [stored] = c.app.state.store.hearings(case["case_id"])
        brain = c.get(f"/api/a/{case['a']}/brain/0").json()
    with hearing.workers(method="forkserver") as pool:
        rerun = hearing.run(pool, BODY["text_a"], TEXT_B, stored["seed"], wait_h=stored["wait_h"])
    print(f"\nstartup {startup:.1f} s; submit→decided {[round(x, 2) for x in times]} s; "
          f"process tree RSS {rss:.2f} GB")
    assert max(times) <= 15
    assert rerun["metrics"] == stored["metrics"] and rerun["brain"] == brain
