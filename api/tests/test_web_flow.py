"""Screen models of the case pages (P2B-8), run in Node on API-shaped views: which screen
shows, verdict headlines for every outcome and the no-show, appeals and the history line,
WhatsApp links, countdowns and the public card (no arguments)."""
import json
import urllib.parse

import pytest

from fake import ROOT, needs_node, node

pytestmark = needs_node

OUTCOME = {"win": ("win", "A"), "dithered": ("dithered", "B"), "plain": ("tie", None),
           "froze": ("froze", None), "lunch": ("food", None)}


def hearing(n, outcome="win", winner="A", status="decided", by=None, accepted=None):
    h = {"n": n, "appealed_by": by, "status": status, "wait_h": 1.0,
         "mood": {"hunger": 0.3, "arousal": 0.1}}
    if status == "decided":
        h |= {"outcome": outcome, "winner": winner,
              "winner_name": {"A": "דנה", "B": "יוסי"}.get(winner), "appetite": {"A": 30.0, "B": 10.0}}
        if n:
            h["accepted"] = accepted
    return h


def view(*hearings, **kw):
    return {"id": "c1", "status": "decided", "topic": "פיצה", "name_a": "דנה", "name_b": "יוסי",
            "no_show": False, "error_message": None, "hearings": list(hearings), "you": "A",
            "text_a": "טענה א", "text_b": "טענה ב", "deadline_in_s": 0, "can_appeal": True,
            "appeal_closes_in_s": 7199} | kw


def run(tmp_path, body, **data):
    consts = "".join(f"\nconst {k} = {json.dumps(v, ensure_ascii=False)};" for k, v in data.items())
    return node(tmp_path, 'import * as F from "@/flow.js"; import { verdictModel } from "@/verdict.js";'
                ' import { publicModel } from "@/public.js"; import * as M from "@/meters.js";' + consts, body)


def spec_headlines():
    table = (ROOT / "docs" / "SPEC.md").read_text().split("## 7. Outcomes")[1].split("## 8.")[0]
    rows = [r.split("|") for r in table.splitlines() if r.startswith("| ") and not r.startswith("| Outcome")]
    return {r[1].strip().split()[0].lower(): r[3].strip() for r in rows}


def test_which_screen(tmp_path):
    d0, run0 = hearing(0), hearing(0, status="running")
    cases = [(view(status="waiting"), -1), (view(status="waiting", you="B"), -1),
             (view(run0, status="hearing"), -1), (view(d0), -1), (view(d0), 0),
             (view(d0, hearing(1, status="queued", by="B"), status="hearing"), 0),
             (view(d0, hearing(1, by="B", accepted=True)), 0), (view(d0, status="error"), 0)]
    got = run(tmp_path, "C.map(([v, seen]) => F.screen(v, seen))", C=cases)
    assert got == [{"kind": "waitA"}, {"kind": "writeB"}, {"kind": "story", "n": 0},
                   {"kind": "story", "n": 0}, {"kind": "verdict", "n": 0}, {"kind": "story", "n": 1},
                   {"kind": "story", "n": 1}, {"kind": "error"}]


@pytest.mark.parametrize("topic", ["פיצה עם אננס", None])
def test_verdict_for_every_outcome(tmp_path, topic):
    spec = spec_headlines()
    views = {k: view(hearing(0, *OUTCOME[k]), topic=topic) for k in OUTCOME}
    got = run(tmp_path, "Object.fromEntries(Object.entries(V).map(([k, v]) => [k, verdictModel(v, 0)]))", V=views)
    for k, v in got.items():
        name = views[k]["hearings"][0]["winner_name"]
        assert v["headline"] == spec[k].replace("{name}", name or "")
        assert v["topic"] == (f"התיק: {topic}" if topic else None)
        assert (v["appeal"], v["history"], v["final"], v["canAppeal"]) == (None, None, False, True)
        assert v["appealLeft"] == "אפשר לערער עוד 2:00 שעות"
        assert v["showMeters"] == (k != "froze")  # SPEC §7: no meters on Froze
        a, b = v["meters"]
        assert (a["name"], a["text"], b["name"], b["text"]) == ("דנה", "טענה א", "יוסי", "טענה ב")
        assert (a["winner"], b["winner"]) == (OUTCOME[k][1] == "A", OUTCOME[k][1] == "B")


def test_no_show_headlines_and_water(tmp_path):
    v = [view(hearing(0, w, s), no_show=True, text_b=None) for w, s in
         [("win", "A"), ("win", "B"), ("dithered", "B"), ("tie", None), ("froze", None)]]
    got = run(tmp_path, "V.map((v) => verdictModel(v, 0))", V=v)
    assert [g["headline"] for g in got] == ["הצד השני לא התייצב לדיון", "הזבוב העדיף מים",
                                            "הזבוב העדיף מים", "הצד השני לא התייצב לדיון",
                                            "הצד השני לא התייצב לדיון"]
    assert got[0]["meters"][1]["name"] == "כוס מים" and got[0]["meters"][1]["text"] is None


def test_appeal_chain_lines_and_history(tmp_path):
    chain = view(hearing(0, "win", "A"), hearing(1, "win", "B", by="A", accepted=True),
                 hearing(2, "win", "B", by="B", accepted=False), can_appeal=False, appeal_closes_in_s=None)
    got = run(tmp_path, "[0, 1, 2].map((n) => verdictModel(V, n))", V=chain)
    assert [g["appeal"] for g in got] == [None, "הערעור של דנה התקבל!", "הערעור של יוסי נדחה"]
    assert got[2]["history"] == "פסק דין ← ערעור התקבל ← ערעור נדחה" and got[2]["final"]
    assert not got[2]["canAppeal"] and got[2]["appealLeft"] is None


def test_links_and_clock(tmp_path):
    v = view(status="waiting", deadline_in_s=3 * 3600 - 61, topic=None)
    got = run(tmp_path, "[F.invite(V, 'https://x/b/T'), F.nudge(V, 'https://x/b/T'),"
              " F.shareVerdict(W, W.hearings[0], 'https://x/c/c1'), [0, 1, 59, 60, 3599, 10800].map(F.clock)]",
              V=v, W=view(hearing(0)))
    invite, nudge, share, clocks = got
    for link in (invite, nudge, share):
        assert link.startswith("https://wa.me/?text=")
    text = [urllib.parse.unquote(x.split("text=")[1]) for x in (invite, nudge, share)]
    assert "https://x/b/T" in text[0] and "דנה" in text[0] and "3 שעות" in text[0]
    assert "https://x/b/T" in text[1] and "2:59" in text[1]
    assert text[2] == "התיק: פיצה\nפסק הדין: הצדק עם דנה\nhttps://x/c/c1"
    assert clocks == ["0:00", "0:01", "0:01", "0:01", "1:00", "3:00"]


def test_public_card_model(tmp_path):
    pub = {k: v for k, v in view(hearing(0), hearing(1, "win", "B", by="A", accepted=True)).items()
           if k in ("id", "status", "topic", "name_a", "name_b", "no_show", "error_message", "hearings")}
    for h in pub["hearings"]:
        for k in ("mood", "wait_h", "appetite"):
            h.pop(k)
    cases = [pub, pub | {"status": "hearing"}, pub | {"status": "waiting", "hearings": []},
             pub | {"status": "error", "error_message": "תקלה"}]
    got = run(tmp_path, "V.map(publicModel)", V=cases)
    assert got[0] == {"topic": "התיק: פיצה", "names": "דנה נגד יוסי",
                      "headline": "פסק הדין: הצדק עם יוסי", "history": "פסק דין ← ערעור התקבל"}
    assert got[1]["headline"] == got[2]["headline"] == "הזבוב עוד לא פסק בתיק הזה"
    assert got[3]["headline"] == "תקלה"


def test_meters_end_on_the_stored_share(tmp_path):
    """The live meters fill from the MN9 bins and end exactly on the stored A/B share."""
    import random
    rng = random.Random(4)
    cases = []
    for _ in range(20):
        bins = [[rng.choice([0, 0, 20, 40, 60, 80]) for _ in range(30)] for _ in range(2)]
        rates = [sum(b) * 0.05 / 1.5 for b in bins]  # readout: spikes / tasting seconds
        cases.append([{"mn9_hz": bins}, view(hearing(0) | {"appetite": {"A": rates[0], "B": rates[1]}})])
    got = run(tmp_path, "C.map(([brain, v]) => { const m = verdictModel(v, 0).meters;"
              " return [M.revealAt(brain, 1), {A: {share: m[0].share, width: m[0].width},"
              " B: {share: m[1].share, width: m[1].width}}, M.revealAt(brain, 0)]; })", C=cases)
    for end, stored, start in got:
        assert end == stored
        assert start == {"A": {"share": 0, "width": 0}, "B": {"share": 0, "width": 0}}


def test_replay_fills_a_then_b(tmp_path):
    stages = [["mood", 0.5], ["tasteA", 0.25], ["tasteB", 0.5], ["deliberate", 1]]
    got = run(tmp_path, "S.map(([k, p]) => M.replayFill(k, p))", S=stages)
    assert got == [None, [0.25, 0], [1, 0.5], [1, 1]]
