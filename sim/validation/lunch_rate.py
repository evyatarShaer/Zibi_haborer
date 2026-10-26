"""P2B-1: hunger growth rate for the lunch break under real waits (SPEC §5, §13).

Run from sim/:  PYTHONPATH=src:. uv run python -m validation.lunch_rate water|report
water: N_WATER plain-water tastings (no Hebrew letters = baseline GRN rates) at product
noise; hunger does not touch water (it scales only the MN9-exciting letter groups), so
one tasting per seed covers every growth rate. A short run (~2 min), not a long one.
report: hunger = U(0, 0.4) + rate x wait (cap 1), wait capped at the 3 h deadline.
Responders: the P1-9 records' outcome mix per 0.1-wide hunger bin (the hunger each
record was simulated with), mixed by each wait pattern's hunger distribution.
No-shows: each record's side-A tasting with hunger > 0.8 (a hungry A) against every
water tasting; below 0.8, every record's side-A tasting. Outcomes by readout.outcome.
"""
import sys
from collections import Counter

import numpy as np

from borer_sim import mood, readout
from borer_sim.params import MOOD, OUTCOME, TASTING_MS
from validation import balance
from validation.mood_probe import extra
from validation.runner import load, run_jobs
from validation.sugar_mn9 import OUT

FILE, N_WATER, WATER0 = "lunch_water_1500ms.jsonl", 60, 90_000
DEADLINE_H, N_MC = 3.0, 200_000
RATES = (0.10, 0.14, 0.15, 0.17, 0.20, 0.25, 0.30)
# Responder wait patterns (hours). An exponential's tail past 3 h becomes a no-show.
PATTERNS = {"minutes ~Exp(5 min)": ("exp", 5 / 60), "~Exp(30 min)": ("exp", 0.5),
            "~Exp(1 h)": ("exp", 1.0), "uniform 0-3 h": ("uni", DEADLINE_H)}
NO_SHOW_EXTRA = (0.0, 0.10, 0.20)  # extra share of cases where B never answers
OUTCOMES = ("win", "dithered", "tie", "froze", "food")
BINS = np.arange(0, 1.01, 0.1)


def water():
    jobs = {}
    for i in range(N_WATER):
        m = mood.product(WATER0 + i)
        jobs[str(i)] = (mood.tasting("", m), WATER0 + i, m.noise_hz)
    run_jobs(jobs, OUT / FILE, TASTING_MS, workers=2, threads=2, extra=extra)


def _gap_hearing(a: float, b: float) -> dict:
    return {"A": a, "B": b, "gap": abs(a - b) / (a + b) if a + b else 0.0, "direction_flips": 0}


def records() -> list[tuple[float, dict]]:
    """(hunger, hearing with outcome) for every P1-9 hearing."""
    return [(mood.product(balance.cases()[ik]).hunger, h) for ik, h in balance.hearings().items()]


def responder_mix(recs) -> np.ndarray:
    """Outcome shares per hunger bin (rows: bins, cols: OUTCOMES)."""
    mix = np.zeros((len(BINS) - 1, len(OUTCOMES)))
    for hunger, h in recs:
        mix[min(np.searchsorted(BINS, hunger, "right") - 1, len(BINS) - 2), OUTCOMES.index(h["outcome"])] += 1
    return mix / np.maximum(mix.sum(1, keepdims=True), 1), mix.sum(1)


def no_show_mix(recs, w: list[float]) -> dict[bool, np.ndarray]:
    """Outcome shares (+ water-wins share) of A vs water, for hungry (> 0.8) and other A."""
    out = {}
    for hungry in (True, False):
        c = Counter()
        for hunger, h in recs:
            if (hunger > OUTCOME["food_hunger"]) != hungry:
                continue
            for wb in w:
                g = _gap_hearing(h["A"], wb)
                o = readout.outcome(g, 1.0 if hungry else 0.0)
                o = "tie" if o == "dithered" else o  # flips are unknown here: close = tie / food
                c[o] += 1
                c["water_wins"] += o == "win" and wb > h["A"]
        n = sum(c[o] for o in OUTCOMES)
        out[hungry] = np.array([c[o] / n for o in OUTCOMES] + [c["water_wins"] / n])
    return out


def waits(kind: str, p: float, rng) -> np.ndarray:
    return rng.exponential(p, N_MC) if kind == "exp" else rng.uniform(0, p, N_MC)


def table(rate: float, recs, mix, ns, rng) -> list[dict]:
    rows = []
    base = rng.uniform(0, MOOD["hunger_base_max"], N_MC)
    for name, (kind, p) in PATTERNS.items():
        w = waits(kind, p, rng)
        for extra_ns in NO_SHOW_EXTRA:
            no_show = (w >= DEADLINE_H) | (rng.random(N_MC) < extra_ns)
            hunger = np.minimum(1.0, base + rate * np.where(no_show, DEADLINE_H, w))
            hungry = hunger > OUTCOME["food_hunger"]
            bins = np.minimum(np.searchsorted(BINS, hunger, "right") - 1, len(BINS) - 2)
            resp = mix[bins[~no_show]]
            # below the threshold a record's food share goes to tie (it could not happen there)
            low = ~hungry[~no_show]
            resp[low, OUTCOMES.index("tie")] += resp[low, OUTCOMES.index("food")]
            resp[low, OUTCOMES.index("food")] = 0
            nos = np.where(hungry[no_show, None], ns[True], ns[False])
            total = (resp.sum(0) + nos[:, :5].sum(0)) / N_MC
            food_case = np.zeros(N_MC)
            food_case[~no_show] = resp[:, OUTCOMES.index("food")]
            food_case[no_show] = nos[:, OUTCOMES.index("food")]
            late = (w >= 2.0) | no_show
            rows.append({"pattern": name, "extra_no_show": extra_ns, "no_show": no_show.mean(),
                         "mix": dict(zip(OUTCOMES, total)),
                         "late_share": food_case[late].sum() / max(food_case.sum(), 1e-12),
                         "water_wins": nos[:, 5].sum() / N_MC})
    return rows


def report():
    recs = records()
    mix, n = responder_mix(recs)
    w = [sum(m["MN9"]) for m in load(FILE).values()]
    ns = no_show_mix(recs, w)
    print(f"records {len(recs)}; water tastings {len(w)}: MN9 Hz median {np.median(w):.1f}, "
          f"p90 {np.percentile(w, 90):.1f}, max {max(w):.1f}")
    print("responder close rate by hunger bin (n): " + ", ".join(
        f"{BINS[i]:.1f}: {1 - mix[i, 0] - mix[i, 3]:.2f} ({int(n[i])})" for i in range(len(n)) if n[i]))
    for k, v in ns.items():
        print(f"no-show A vs water, A {'hungry (> 0.8)' if k else 'not hungry'}: "
              + ", ".join(f"{o} {x:.3f}" for o, x in zip(OUTCOMES + ("water_wins",), v)))
    rng = np.random.default_rng(0x6C756E63)
    print("\n| rate /h | earliest wait | pattern | no-show | lunch | from wait ≥ 2 h or no-show | win | dithered | tie | froze | water wins |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for rate in RATES:
        earliest = (OUTCOME["food_hunger"] - MOOD["hunger_base_max"]) / rate
        for r in table(rate, recs, mix, ns, rng):
            m = r["mix"]
            print(f"| {rate:.2f} | {earliest:.1f} h | {r['pattern']} | {r['no_show']:.0%} | "
                  f"**{m['food']:.1%}** | {r['late_share']:.0%} | {m['win']:.1%} | {m['dithered']:.1%} | "
                  f"{m['tie']:.1%} | {m['froze']:.1%} | {r['water_wins']:.1%} |")


if __name__ == "__main__":
    {"water": water, "report": report}[sys.argv[1]]()
