"""Spam fix (SIM_VERSION 0.6.0): spam suite, baseline sweep on OLD+NEW, THIRD confirmation.

Run from sim/:  PYTHONPATH=src uv run python -m validation.taste_spam [sweep|third RB|report RB]
sweep: for each r_base in R_BASES (highest first) taste OLD+NEW (10 seeds) and the
spam suite (5 seeds) at TASTING_MS; the first r_base that passes ACCEPTANCE is chosen
(written to CHOICE), then THIRD is tasted with it. Rule fixed before running:
natural OLD+NEW (pooled, 60 pairs) pass (a)-(e) and longer-wins; no runaway in any spam
or silence tasting; every spam text's mean MN9 <= natural P75; every silence text's
mean MN9 <= natural P25 (natural = per-argument mean MN9 over OLD+NEW).
"""
import json
import sys
from collections import Counter

import numpy as np

from borer_sim import taste
from borer_sim.params import TASTING_MS
from validation.runner import RUNAWAY, load
from validation.sugar_mn9 import OUT
from validation.taste_criteria import criteria, print_criteria, tastings
from validation.taste_probe import SEEDS, run
from validation.taste_sets import PAIRS, SETS

R_BASES = (4.0, 2.0, 0.0)
SPAM_SEEDS = SEEDS[:5]
CHOICE = OUT / "taste_v6_choice.json"
SPAM = ({f"{l} x280": l * 280 for l in taste.LETTERS + "!?"}
        | {f"{w} repeated": (w + " ") * 93 for w in ("דבש", "טוב", "לא", "כן")}
        | {f"{p} alternating": p * 140 for p in ("יו", "הא", "דב", "של")})
SILENCE = {"empty": "", "punctuation": ".,;:-()\"'" * 31, "emoji": "😂🔥👍🙄" * 70,
           "latin": "The fly decides who wins this argument, 100% sure. " * 5}
NATURAL = SETS["old"] + SETS["new"]
NATURAL_PAIRS = PAIRS["old"] + [(a + len(SETS["old"]), b + len(SETS["old"])) for a, b in PAIRS["new"]]


def _file(kind: str, rb: float) -> str:
    return f"taste_v6_{kind}_{TASTING_MS}ms_b{rb:g}.jsonl"


def _taste(kind: str, rb: float, texts: list[str], seeds) -> dict:
    taste.TASTE["r_base"] = rb  # validation override; the chosen value goes into params
    return run(_file(kind, rb), {f"{i}|{s}": (taste.tasting(t), s)
                                 for i, t in enumerate(texts) for s in seeds}, TASTING_MS)


def _spam_texts() -> dict:
    return SPAM | SILENCE


def score(rb: float, natural="natural", texts=None, pairs=None) -> bool:
    """Print the spam table and natural criteria for r_base `rb`; True if ACCEPTANCE passes."""
    nat = criteria(tastings(load(_file(natural, rb))), texts or NATURAL, pairs or NATURAL_PAIRS)
    p25, p75 = np.percentile(list(nat["mean"].values()), [25, 75])
    spam = tastings(load(_file("spam", rb)))
    print(f"\n=== r_base {rb:g} Hz ({natural}): natural P25 {p25:.1f} / P75 {p75:.1f} Hz")
    print("| spam text | kind | coverage | MN9 mean (max) Hz | max active | ok |\n|---|---|---|---|---|---|")
    ok_all = True
    for i, (name, text) in enumerate(_spam_texts().items()):
        mn9 = [v[0] for v in spam[i].values()]
        act = max(v[2] for v in spam[i].values())
        silent = name in SILENCE
        ok = act <= RUNAWAY and np.mean(mn9) <= (p25 if silent else p75)
        ok_all &= ok
        print(f"| {name} | {'silence' if silent else 'spam'} | {taste.coverage(Counter(taste.normalize(text))):.3f} | "
              f"{np.mean(mn9):.1f} ({max(mn9):.1f}) | {act} | {'ok' if ok else 'FAIL'} |")
    print_criteria(nat)
    passed = ok_all and all(nat["pass"].values())
    print(f"ACCEPTANCE r_base {rb:g}: {'PASS' if passed else 'FAIL'}", flush=True)
    return passed


def sweep():
    for rb in R_BASES:
        _taste("spam", rb, list(_spam_texts().values()), SPAM_SEEDS)
        _taste("natural", rb, NATURAL, SEEDS)
        if score(rb):
            CHOICE.write_text(json.dumps({"r_base": rb}))
            return third(rb)
    print("NO r_base PASSES; THIRD not run", flush=True)


def third(rb):
    rb = float(rb)
    _taste("third", rb, SETS["third"], SEEDS)
    score(rb, "third", SETS["third"], PAIRS["third"])


if __name__ == "__main__":
    {"sweep": sweep, "third": third, "report": score}[sys.argv[1]](*map(float, sys.argv[2:]))
