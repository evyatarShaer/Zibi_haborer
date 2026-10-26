"""Shared test helpers: a fake simulation, a status poller (fixtures in conftest.py) and
a Node runner for the page's modules."""
import json
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

from borer_sim import mood

OK = {"topic": "פיצה", "name_a": "דנה", "name_b": "יוסי",
      "text_a": "פיצה עם אננס זה פשוט טעים", "text_b": "אננס על פיצה זה פשע נגד האנושות"}
BRAIN = {"bin_ms": 50, "mn9_hz": [[1.0, 2.0], [3.0, 4.0]], "taste_hz": [{"sugar": 5.0}] * 2,  # a 0.8.x row
         "mood": {}, "seed": 1, "sim_version": "0.8.2", "platform": "test"}


class FakeSim:
    """Answers `outcome` / `winner`; with gate set to False it blocks until opened."""

    def __init__(self, outcome="win", winner="A"):
        self.outcome, self.winner, self.gate, self.calls = outcome, winner, threading.Event(), []
        self.gate.set()

    def __call__(self, a, b, seed):
        self.calls.append((a, b, seed))
        self.gate.wait(10)
        m = mood.product(seed)
        metrics = {"A": 30.0, "B": 20.0, "gap": 0.2, "winner": self.winner, "outcome": self.outcome}
        return {"seed": seed, "mood": {"hunger": m.hunger, "arousal": m.arousal}, "metrics": metrics,
                "brain": BRAIN, "sim_version": "0.8.2", "platform": "test", "duration_ms": 5}


def wait_status(client, hid, status, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        h = client.get(f"/hearing/{hid}").json()
        if h["status"] == status:
            return h
        time.sleep(0.01)
    raise AssertionError(f"{hid} never reached {status}: {h}")


ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "web" / "js"
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def node(tmp_path, imports: str, body: str):
    """Run an ES module that imports web/js files ("@/x.js") and prints JSON; return the value."""
    script = tmp_path / "run.mjs"
    script.write_text(imports.replace("@/", (JS.as_uri() + "/")) + f"\nconsole.log(JSON.stringify({body}));\n")
    out = subprocess.run(["node", str(script)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)
