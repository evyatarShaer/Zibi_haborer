"""Shared test helpers: a fake simulation, a poller (fixtures in conftest.py) and
a Node runner for the page's modules."""
import json
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

from borer_sim import mood

OK = {"topic": "פיצה", "name_a": "דנה", "name_b": "יוסי", "text_a": "פיצה עם אננס זה פשוט טעים"}
TEXT_B = "אננס על פיצה זה פשע נגד האנושות"
# A 0.8.x-shaped summary (still holds taste_hz, which the API never sends); its 30 bins per
# tasting average to the fake metrics' A = 30 Hz and B = 20 Hz, as a real summary would.
BRAIN = {"bin_ms": 50, "mn9_hz": [[20.0, 40.0] * 15, [0.0, 40.0] * 15],
         "taste_hz": [{"sugar": 5.0}] * 2, "mood": {"hunger": 0.3, "arousal": 0.1}, "seed": 1,
         "sim_version": "0.8.2", "platform": "test"}


class FakeSim:
    """Answers `outcome` / `winner`; with gate set to False it blocks until opened."""

    def __init__(self, outcome="win", winner="A"):
        self.outcome, self.winner, self.gate, self.calls = outcome, winner, threading.Event(), []
        self.gate.set()

    def __call__(self, a, b, seed, wait_h):
        self.calls.append((a, b, seed, wait_h))
        self.gate.wait(10)
        m = mood.from_case(seed, wait_h)
        metrics = {"A": 30.0, "B": 20.0, "gap": 0.2, "winner": self.winner, "outcome": self.outcome}
        return {"seed": seed, "mood": {"hunger": m.hunger, "arousal": m.arousal}, "metrics": metrics,
                "brain": BRAIN, "sim_version": "0.8.2", "platform": "test", "duration_ms": 5}


def wait_for(client, path, check, timeout=5.0):
    """Poll GET `path` until check(json) holds; returns that json."""
    end = time.time() + timeout
    while time.time() < end:
        body = client.get(path).json()
        if check(body):
            return body
        time.sleep(0.01)
    raise AssertionError(f"{path} never matched: {body}")


ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "web" / "js"
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def node(tmp_path, imports: str, body: str):
    """Run an ES module that imports web/js files ("@/x.js") and prints JSON; return the value."""
    script = tmp_path / "run.mjs"
    script.write_text(imports.replace("@/", (JS.as_uri() + "/")) + f"\nconsole.log(JSON.stringify({body}));\n")
    out = subprocess.run(["node", str(script)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)
