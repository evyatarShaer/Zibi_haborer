"""Page logic (P2A-4/5/6) run in Node: letter counter == Python, waiting story, verdict copy."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from borer_api.app import create_app
from borer_api.validate import problems
from borer_sim.argument import hebrew_letters

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "web" / "js"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def node(tmp_path, imports: str, body: str):
    """Run an ES module that imports web/js files and prints JSON; return the value."""
    script = tmp_path / "run.mjs"
    script.write_text(imports.replace("@/", (JS.as_uri() + "/")) + f"\nconsole.log(JSON.stringify({body}));\n")
    out = subprocess.run(["node", str(script)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


EXTRA = ["שָׁלוֹם עֲלֵיכֶם וּבְרָכָה", "ךםןףץ ךםןףץ", "   רווחים\n\tבכל מקום   ",
         "😂" * 200 + " אבגדהוזחטי", "א" * 300, "ﬠﬡﬢ צורות רחבות", "abc אבג 123 דהו !? זחט"]


def validation_texts() -> list[str]:
    """Spam/silence suite + OLD/NEW/THIRD, read in sim's own env (validation needs brian2)."""
    code = ("import json; from validation.taste_spam import SILENCE, SPAM; "
            "from validation.taste_sets import SETS; print(json.dumps(list(SPAM.values()) + "
            "list(SILENCE.values()) + [t for s in SETS.values() for t in s]))")
    out = subprocess.run(["uv", "run", "python", "-c", code], cwd=ROOT / "sim", check=True,
                         capture_output=True, text=True, env=os.environ | {"PYTHONPATH": "src:."})
    return json.loads(out.stdout)


def test_letter_counter_matches_python(tmp_path):
    texts = validation_texts() + EXTRA
    assert len(texts) > 60
    js = node(tmp_path, 'import { hebrewLetters, chars, argumentOk } from "@/letters.js";'
              f"\nconst T = {json.dumps(texts, ensure_ascii=False)};",
              "T.map((t) => [hebrewLetters(t), chars(t), argumentOk(t)])")
    for text, (n, c, ok) in zip(texts, js):
        assert n == hebrew_letters(text), text[:30]
        assert c == len(text.strip()), text[:30]
        server_ok = "text_a" not in problems(None, {"a": "x", "b": "y"}, {"a": text.strip(), "b": "א" * 10})
        assert ok == server_ok, text[:30]


def story(tmp_path, statuses):
    """statuses: [(from_ms, status)]; ticks every 250 ms for 60 s -> [(t, view)]."""
    return node(tmp_path, 'import { step } from "@/stages.js";'
                f"\nconst S = {json.dumps(statuses)}; const state = {{}}; const out = [];"
                "\nfor (let t = 0; t <= 60000; t += 250) {"
                "\n  const status = S.filter(([from]) => from <= t).pop()[1];"
                "\n  const v = step(state, status, t); out.push([t, v]);"
                "\n  if (v.kind === 'verdict' || v.kind === 'failed') break; }", "out")


def test_fast_verdict_still_tells_the_whole_story(tmp_path):
    views = story(tmp_path, [(0, "decided")])
    keys = [v["key"] for _, v in views if v["kind"] == "stage"]
    assert [k for i, k in enumerate(keys) if i == 0 or keys[i - 1] != k] == ["mood", "tasteA", "tasteB", "deliberate"]
    assert views[-1] == [7000, {"kind": "verdict"}]


def test_queued_first_then_story(tmp_path):
    views = story(tmp_path, [(0, "queued"), (3000, "running"), (9000, "decided")])
    assert all(v == {"kind": "queued"} for t, v in views if t < 3000)
    assert views[12][1]["key"] == "mood" and views[-1] == [10000, {"kind": "verdict"}]


def test_slow_host_loops_cleanly(tmp_path):
    """Simulation delayed to 40 s: deliberate keeps cycling; the line changes every 2 s."""
    views = story(tmp_path, [(0, "running"), (40000, "decided")])
    assert views[-1] == [40000, {"kind": "verdict"}]
    lines = [(t, v["line"]) for t, v in views if v.get("key") == "deliberate"]
    changes = [t for (t, l), (_, prev) in zip(lines[1:], lines) if l != prev]
    assert len(changes) >= 15 and max(b - a for a, b in zip(changes, changes[1:])) <= 2000


def test_failed_is_shown_at_once(tmp_path):
    assert story(tmp_path, [(0, "running"), (2000, "failed")])[-1] == [2000, {"kind": "failed"}]


def spec_headlines():
    table = (ROOT / "docs" / "SPEC.md").read_text().split("## 7. Outcomes")[1].split("## 8.")[0]
    rows = [r.split("|") for r in table.splitlines()
            if r.startswith("| ") and not r.startswith("| Outcome")]
    return {r[1].strip().split()[0].lower(): r[3].strip() for r in rows}


FIX = {"name_a": "דנה", "name_b": "יוסי", "text_a": "טענה א", "text_b": "טענה ב"}
CASES = {"win": ("A", 30.0, 10.0), "dithered": ("B", 20.0, 21.0), "plain": (None, 20.0, 20.5),
         "froze": (None, 2.0, 0.0), "lunch": (None, 12.0, 12.4)}
OUTCOME = {"win": "win", "dithered": "dithered", "plain": "tie", "froze": "froze", "lunch": "food"}


@pytest.mark.parametrize("topic", ["פיצה עם אננס", None])
def test_verdict_for_every_outcome(tmp_path, topic):
    spec = spec_headlines()
    fixtures = {k: FIX | {"topic": topic, "outcome": OUTCOME[k], "winner": w,
                          "winner_name": {"A": "דנה", "B": "יוסי"}.get(w), "appetite": {"A": a, "B": b}}
                for k, (w, a, b) in CASES.items()}
    js = node(tmp_path, 'import { verdictModel } from "@/verdict.js";'
              f"\nconst F = {json.dumps(fixtures, ensure_ascii=False)};",
              "Object.fromEntries(Object.entries(F).map(([k, h]) => [k, verdictModel(h)]))")
    for k, v in js.items():
        name = fixtures[k]["winner_name"]
        assert v["headline"] == spec[k].replace("{name}", name or "")
        assert v["topic"] == (f"התיק: {topic}" if topic else None)
        a, b = v["meters"]
        assert (a["name"], b["name"]) == ("דנה", "יוסי") and (a["winner"], b["winner"]) == (
            fixtures[k]["winner"] == "A", fixtures[k]["winner"] == "B")
        assert a["share"] + b["share"] in (0, 99, 100, 101) and max(a["width"], b["width"]) in (0, 100)
    assert js["froze"]["meters"][1] == {"name": "יוסי", "text": "טענה ב", "winner": False, "share": 0, "width": 0}


def test_page_and_modules_served(tmp_path):
    with TestClient(create_app(lambda *a: None, str(tmp_path / "h.sqlite3"))) as c:
        page = c.get("/").text
        assert 'dir="rtl"' in page and "Heebo" in page and 'src="js/app.js"' in page
        for f in sorted(JS.glob("*.js")) + [ROOT / "web" / "css" / "app.css"]:
            r = c.get("/" + f.relative_to(ROOT / "web").as_posix())
            assert r.status_code == 200 and ("javascript" in r.headers["content-type"] or f.suffix == ".css")
        imports = {m for f in JS.glob("*.js") for m in re.findall(r'from "\./([\w.]+)"', f.read_text())}
        assert imports <= {f.name for f in JS.glob("*.js")}
