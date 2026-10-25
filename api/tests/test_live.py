"""Real brain behind the API (P2A-3): startup, submit → decided ≤ 15 s, stored = rerun."""
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from borer_api.app import create_app
from borer_sim import hearing

pytestmark = pytest.mark.needs_data

BODY = {"name_a": "דנה", "name_b": "יוסי", "text_a": "פיצה עם אננס זה פשוט טעים ונקודה.",
        "text_b": "הסדרה הזאת משעממת, בוא נראה משהו אחר."}


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
    with TestClient(create_app(db_path=str(tmp_path / "h.sqlite3"))) as c:
        startup = time.perf_counter() - t0
        times = []
        for _ in range(3):
            t = time.perf_counter()
            hid = c.post("/hearing", json=BODY).json()["id"]
            while (h := c.get(f"/hearing/{hid}").json())["status"] in ("queued", "running"):
                time.sleep(0.05)
            times.append(time.perf_counter() - t)
            assert h["status"] == "decided"
        rss = tree_rss_gb()
        stored = c.app.state.store.get(hid)
        brain = c.get(f"/hearing/{hid}/brain").json()
    with hearing.workers(method="forkserver") as pool:
        rerun = hearing.run(pool, stored["text_a"], stored["text_b"], stored["seed"])
    print(f"\nstartup {startup:.1f} s; submit→decided {[round(x, 2) for x in times]} s; "
          f"process tree RSS {rss:.2f} GB")
    assert max(times) <= 15
    assert rerun["metrics"] == stored["metrics"] and rerun["brain"] == brain
