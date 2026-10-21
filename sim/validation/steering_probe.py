"""P1-6 steering probe: does text matter for turning? (design B, 2026-10-20)

Run from sim/:  PYTHONPATH=src uv run python -m validation.steering_probe
1. each antennal glomerulus, one side, 3 rates, 3 seeds, both sides;
2. competition: 5 X texts vs 5 Y texts, both orders, 10 seeds;
3. the 5 matched pairs again at x0.1 input.
Results: data/processed/validation/steering_*.jsonl (resumable).
"""
import os

from borer_sim import anatomy, smell
from validation import steering
from validation.sugar_mn9 import OUT

PALP = {"VA4", "VA7l", "VC1", "VC2", "VM7d", "VM7v"}
RATES = {"low": 20.0, "mid": 60.0, "high": 150.0}  # per-ORN Hz, from smell.py's range
GLOM_SEEDS = (783, 784, 785)
PAIR_SEEDS = tuple(range(783, 793))
LOW_SCALE = 0.1
# workers x threads <= 6 cores AND workers x 2.5 GB <= free RAM; env override for lighter
# loads (the Windows host stalls the VM under sustained 6-core load, POC_REPORT)
WORKERS = int(os.environ.get("BORER_WORKERS", 3))
THREADS = int(os.environ.get("BORER_THREADS", 2))

X_TEXTS = {  # letter-sets by valence group (smell.LETTERS) + natural arguments
    "x_att": "דבש טוב לגדול",
    "x_ave": "רע מאת זמן",
    "x_neu": "יה כח קפ סצ",
    "x_nat": "אתה תמיד שוכח לסגור את הדלת, וזה ממש מעצבן אותי",
    "x_q": "למה לא? מי אמר שפיצה עם אננס זה רע??",
}
Y_TEXTS = {
    "y_att": "שוב דבש לגוש טוב",
    "y_ave": "מרתא נעזרת",
    "y_neu": "צפה כי קח סה",
    "y_nat": "הדבש שלי הכי טוב בעולם, תודה רבה!!!",
    "y_nat2": "אין מצב, אני צודק ואתה טועה",
}


def antennal_glomeruli() -> list[str]:
    return [g for g in anatomy.orn_glomeruli().index if g not in PALP]


def balanced(glom: str, side: str, rate: float):
    """Same side balancing as smell.drives: equal total drive on either side."""
    orns = {s: anatomy.orns(glom, s) for s in anatomy.SIDES}
    mean_n = sum(len(o) for o in orns.values()) / 2
    return [(orns[side], rate * mean_n / len(orns[side]))]


def glomerulus_jobs():
    return {f"{g}|{lvl}|{side}|{seed}": (balanced(g, side, r), seed)
            for g in antennal_glomeruli() for lvl, r in RATES.items()
            for side in anatomy.SIDES for seed in GLOM_SEEDS}


def hearing(left_text: str, right_text: str, scale: float = 1.0):
    d = smell.drives(left_text, "left") + smell.drives(right_text, "right")
    return [(idx, r * scale) for idx, r in d]


def pair_jobs(pairs, scale: float):
    jobs = {}
    for x, y in pairs:
        for seed in PAIR_SEEDS:
            jobs[f"{x}|{y}|XY|{seed}"] = (hearing(X_TEXTS[x], Y_TEXTS[y], scale), seed)
            jobs[f"{x}|{y}|YX|{seed}"] = (hearing(Y_TEXTS[y], X_TEXTS[x], scale), seed)
    return jobs


def main():
    all_pairs = [(x, y) for x in X_TEXTS for y in Y_TEXTS]
    matched = list(zip(X_TEXTS, Y_TEXTS))
    parts = [("steering_glomeruli.jsonl", glomerulus_jobs()),
             ("steering_pairs.jsonl", pair_jobs(all_pairs, 1.0)),
             ("steering_pairs_low.jsonl", pair_jobs(matched, LOW_SCALE))]
    for name, jobs in parts:
        print(f"{name}: {len(jobs)} jobs", flush=True)
        steering.run_jobs(jobs, OUT / name, WORKERS, THREADS)


if __name__ == "__main__":
    main()
