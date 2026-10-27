"""Page logic for the lab view (P2A-8), run in Node."""
import json
import re

import pytest

from borer_sim import taste
from fake import ROOT, needs_node, node

pytestmark = needs_node

BRAIN = {"bin_ms": 50,
         "mn9_hz": [[0, 0, 0, 60, 0, 0, 40, 0, 20] + [0] * 21, [0, 0, 0, 80, 0, 0, 20, 40, 20] + [20, 0] * 10 + [0]],
         "mood": {"hunger": 0.2648, "arousal": 0.0442}, "seed": 1362020458, "sim_version": "0.9.0",
         "platform": "Linux | 3.12 | torch 2.14"}


def lab(tmp_path, brain=BRAIN):
    return node(tmp_path, 'import { labModel, CHART } from "@/lab.js";'
                f"\nconst m = labModel({json.dumps(brain)});",
                "{...m, chart: {...m.chart, nearest: [-50, 999, ...m.chart.xs].map(m.chart.nearest)}, box: CHART}")


def test_lab_curves_fit_the_chart(tmp_path):
    m = lab(tmp_path)
    c, box = m["chart"], m["box"]
    assert [len(x) for x in m["curves"]] == [30, 30] and c["dur"] == pytest.approx(1.5)
    assert c["yTop"] >= max(map(max, m["curves"])) and c["yTop"] % 10 == 0
    for line in c["lines"]:
        pts = [tuple(map(float, p.split(","))) for p in line.split()]
        assert len(pts) == 30
        assert all(box["left"] <= x <= box["w"] - box["right"] for x, _ in pts)
        assert all(box["top"] <= y <= box["h"] - box["bottom"] for _, y in pts)
    assert [t["s"] for t in c["xTicks"]] == [0, 0.5, 1, 1.5] and c["nearest"] == [0, 29, *range(30)]
    assert m["curves"][0][3] == pytest.approx(12.0)  # one 60 Hz bin averaged over 5


def test_lab_mood_and_identity(tmp_path):
    m = lab(tmp_path)
    assert "taste" not in m
    assert m["mood"] == {"hunger": "0.26", "arousal": "0.04"}
    assert (m["seed"], m["simVersion"], m["platform"]) == ("1362020458", "0.9.0", BRAIN["platform"])


def leaks(text: str) -> list[str]:
    """Letter-level or class-level data in page text (SPEC §2.3): GRN group names, taste
    classes, or a lone Hebrew letter (how a letter table would read)."""
    groups = {name.split(":")[1].split("/")[0] for name, _ in taste.TABLE.values()}
    classes = {name.split(":")[0] for name, _ in taste.TABLE.values()} | {"sugar", "bitter"}
    lone = re.findall(r"(?<![\u05d0-\u05ea])[\u05d0-\u05ea](?![\u05d0-\u05ea])", text)
    return [w for w in groups | classes if w.lower() in text.lower()] + lone


def test_lab_shows_no_letters_or_groups(tmp_path):
    """SPEC §2.3, §15.7: no letter, GRN group or taste class, even from a 0.8.x summary."""
    old = BRAIN | {"taste_hz": [{"sugar": 75.5, "bitter": 17.7}] * 2}
    assert leaks(json.dumps(lab(tmp_path, old), ensure_ascii=False)) == []


def test_how_it_works_has_credits_and_no_table(tmp_path):
    how = node(tmp_path, 'import { HOW } from "@/how.js";', "HOW")
    text = json.dumps(how, ensure_ascii=False)
    assert leaks(text) == []
    spec = (ROOT / "docs" / "SPEC.md").read_text().split("7. **Disclosure.**")[1].split("8. **Retention")[0]
    dois = set(re.findall(r"\(?(10\.\d+/[^)\s,]+)\)", spec))
    assert len(dois) == 6 and dois == {doi for _, _, doi in how["credits"] if doi}
    assert any(who.startswith("Shiu") for who, _, _ in how["credits"]) and "CC BY-NC" in text
