"""Page logic run in Node: letter counter == Python, the waiting story; the page is served."""
import json
import os
import re
import subprocess

import pytest
from fastapi.testclient import TestClient

from borer_api.app import create_app
from borer_api.validate import problems
from borer_sim.argument import hebrew_letters
from fake import JS, ROOT, needs_node, node

pytestmark = needs_node

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


def story(tmp_path, statuses, reveal=True):
    """statuses: [(from_ms, status)]; ticks every 250 ms for 60 s -> [(t, view)]."""
    return node(tmp_path, 'import { step } from "@/stages.js";'
                f"\nconst S = {json.dumps(statuses)}; const state = {{}}; const out = [];"
                "\nfor (let t = 0; t <= 60000; t += 250) {"
                "\n  const status = S.filter(([from]) => from <= t).pop()[1];"
                f"\n  const v = step(state, status, t, {json.dumps(reveal)}); out.push([t, v]);"
                "\n  if (v.kind === 'verdict' || v.kind === 'failed') break; }", "out")


def test_fast_verdict_still_tells_the_whole_story(tmp_path):
    views = story(tmp_path, [(0, "decided")])
    keys = [v["key"] for _, v in views if v["kind"] == "stage"]
    assert [k for i, k in enumerate(keys) if i == 0 or keys[i - 1] != k] == ["mood", "tasteA", "tasteB", "deliberate"]
    assert views[-1] == [9000, {"kind": "verdict"}]  # live: 7 s story + 2 s meters
    reveal = [v["p"] for t, v in views if v["kind"] == "reveal"]
    assert reveal[0] == 0 and reveal == sorted(reveal) and len(reveal) == 8 and max(reveal) < 1
    tastes = [(t, v["p"]) for t, v in views if v.get("key") == "tasteA"]
    assert tastes[0] == (2250, pytest.approx(50 / 1800)) and tastes[-1][1] < 1


def test_replay_and_froze_skip_the_reveal(tmp_path):
    """A replay fills the meters during the tastings instead; Froze has none."""
    assert story(tmp_path, [(0, "decided")], reveal=False)[-1] == [7000, {"kind": "verdict"}]


def test_queued_first_then_story(tmp_path):
    views = story(tmp_path, [(0, "queued"), (3000, "running"), (9000, "decided")])
    assert all(v == {"kind": "queued"} for t, v in views if t < 3000)
    assert views[12][1]["key"] == "mood" and views[-1] == [12000, {"kind": "verdict"}]


def test_slow_host_loops_cleanly(tmp_path):
    """Simulation delayed to 40 s: deliberate keeps cycling; the line changes every 2 s."""
    views = story(tmp_path, [(0, "running"), (40000, "decided")])
    assert views[-1] == [42000, {"kind": "verdict"}]
    lines = [(t, v["line"]) for t, v in views if v.get("key") == "deliberate"]
    changes = [t for (t, l), (_, prev) in zip(lines[1:], lines) if l != prev]
    assert len(changes) >= 15 and max(b - a for a, b in zip(changes, changes[1:])) <= 2000


def test_page_and_modules_served(tmp_path):
    with TestClient(create_app(lambda *a: None, str(tmp_path / "h.sqlite3"))) as c:
        page = c.get("/").text
        assert 'dir="rtl"' in page and "Heebo" in page and 'src="/js/app.js"' in page
        for path in ("/a/tok", "/b/tok", "/c/id1", "/how"):  # personal, public, how it works
            assert 'src="/js/app.js"' in c.get(path).text  # same page; preview tags: test_og.py
        assert c.get("/x/tok").status_code == 404
        for f in sorted(JS.glob("*.js")) + sorted((ROOT / "web" / "css").glob("*.css")):
            r = c.get("/" + f.relative_to(ROOT / "web").as_posix())
            assert r.status_code == 200 and ("javascript" in r.headers["content-type"] or f.suffix == ".css")
        imports = {m for f in JS.glob("*.js") for m in re.findall(r'from "\./([\w.]+)"', f.read_text())}
        assert imports <= {f.name for f in JS.glob("*.js")}
