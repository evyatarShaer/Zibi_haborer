"""Page logic for the appeal (P2A-7) and the lab view (P2A-8), run in Node."""
import json

import pytest

from borer_sim import taste
from fake import needs_node, node

pytestmark = needs_node

H = {"name_a": "דנה", "name_b": "יוסי", "text_a": "טענה א", "text_b": "טענה ב", "topic": None,
     "outcome": "win", "winner": "A", "winner_name": "דנה", "appetite": {"A": 30.0, "B": 10.0}}
BRAIN = {"bin_ms": 50,
         "mn9_hz": [[0, 0, 0, 60, 0, 0, 40, 0, 20] + [0] * 21, [0, 0, 0, 80, 0, 0, 20, 40, 20] + [20, 0] * 10 + [0]],
         "mood": {"hunger": 0.2648, "arousal": 0.0442}, "seed": 1362020458, "sim_version": "0.9.0",
         "platform": "Linux | 3.12 | torch 2.14"}


def verdicts(tmp_path, cases):
    return node(tmp_path, 'import { verdictModel } from "@/verdict.js";'
                f"\nconst C = {json.dumps(cases, ensure_ascii=False)};", "C.map(verdictModel)")


def test_appeal_line_and_buttons(tmp_path):
    orig, done = H | {"can_appeal": True, "appeal_id": None}, H | {"can_appeal": False, "appeal_id": "x1"}
    yes, no = (H | {"appeal_of": "o", "can_appeal": False, "appeal_accepted": v} for v in (True, False))
    v = verdicts(tmp_path, [orig, done, yes, no])
    assert [x["appeal"] for x in v] == [None, None, "הערעור התקבל!", "הערעור נדחה. הפסק סופי"]
    assert [x["canAppeal"] for x in v] == [True, False, False, False]
    assert [x["appealId"] for x in v] == [None, "x1", None, None]


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


def test_lab_shows_no_letters_or_groups(tmp_path):
    """SPEC §2.3, §15.7: no letter, GRN group or taste class, even from a 0.8.x summary."""
    old = BRAIN | {"taste_hz": [{"sugar": 75.5, "bitter": 17.7}] * 2}
    text = json.dumps(lab(tmp_path, old), ensure_ascii=False)
    groups = {name.split(":")[1].split("/")[0] for name, _ in taste.TABLE.values()}
    assert not any(g in text for g in groups) and "sugar" not in text
