"""P1-9 balance run: random argument pairs through the product path (SIM_VERSION 0.8.0).

Run from sim/:  PYTHONPATH=src:. uv run python -m validation.balance run|time|report
Arguments: seeded word sequences drawn by frequency from the OpenSubtitles 2018 Hebrew
word list (data/raw/opus_he_freq: word counts only, no utterances were downloaded),
30-200 chars, >= 10 Hebrew letters; not the OLD/NEW/THIRD sets. A tasting depends only
on the letter and mark counts and the length (borer_sim.taste), not on word order.
Pair i = arguments 2i, 2i+1; case seed CASE0 + i is also the simulation seed (as in the
product); mood = mood.product(case seed). Seed consistency: pairs < N_CONSIST
x N_SEEDS case seeds (CASE0 + i + SEED_STEP k). Input quality: densest band over all
tastings; Spearman rho of per-argument MN9 (mean over its seeds) with length and the
ד/ב/ש count, as taste_criteria. Pass rules: tests/test_balance.py.
time: TIME_N hearings of the main run, two tastings in parallel (2 processes x 1 thread),
checked against the run's records (same metrics and outcome), plus peak RSS.
"""
import gzip
import json
import resource
import statistics
import sys
from collections import Counter, defaultdict
from functools import cache

import numpy as np

from borer_sim import argument, mood, readout, taste
from borer_sim.params import TASTING_MS
from validation.mood_calib import record_hearing
from validation.mood_probe import extra
from validation.runner import PLATFORM, RUNAWAY, connectome_model, load, run_jobs, timed_hearings
from validation.sugar_mn9 import OUT
from validation.taste_criteria import densest_band, honey, spearman

CORPUS = "data/raw/opus_he_freq/he.freq.gz"
N_PAIRS, N_CONSIST, N_SEEDS, TIME_N = 1000, 50, 10, 20
CASE0, SEED_STEP, ARG_SEED, VOCAB = 20_000, 1_000_000, 0x62616C, 100_000
MIN_CHARS, MAX_CHARS = 30, 200
FILE, TIME_FILE = "balance_1500ms.jsonl", "balance_time.json"
NONTRIVIAL = 0.10  # mean gap of a pair (SPEC §12)


@cache
def arguments() -> tuple[str, ...]:
    words, counts = [], []
    with gzip.open(CORPUS, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            n, _, w = line.strip().partition(" ")
            if n.isdigit() and w:
                words.append(w)
                counts.append(int(n))
            if len(words) == VOCAB:
                break
    cum = np.cumsum(counts) / sum(counts)
    rng, out = np.random.default_rng(ARG_SEED), []
    while len(out) < 2 * N_PAIRS:
        target, text = rng.integers(MIN_CHARS, MAX_CHARS + 1), ""
        for k in np.searchsorted(cum, rng.random(MAX_CHARS)):
            w = words[min(k, len(words) - 1)]
            nxt = text + w if not text or not w[0].isalnum() else f"{text} {w}"
            if len(nxt) > target:
                break
            text = nxt
        if len(text) >= MIN_CHARS and argument.hebrew_letters(text) >= argument.MIN_LETTERS:
            out.append(text)
    return tuple(out)


def cases() -> dict[tuple[int, int], int]:
    """{(pair, k): case seed}: k = 0 for every pair, k < N_SEEDS for the consistency subset."""
    return {(i, k): CASE0 + i + SEED_STEP * k for i in range(N_PAIRS)
            for k in range(N_SEEDS if i < N_CONSIST else 1)}


def _pair(i: int) -> tuple[str, str]:
    return arguments()[2 * i], arguments()[2 * i + 1]


def run():
    jobs = {}
    for (i, k), s in cases().items():
        m = mood.product(s)
        for side, text in zip("ab", _pair(i)):
            jobs[f"{i}|{k}|{side}"] = (mood.tasting(text, m), s, m.noise_hz)
    print(f"{FILE}: {len(jobs)} jobs", flush=True)
    run_jobs(jobs, OUT / FILE, TASTING_MS, extra=extra)


def hearings() -> dict[tuple[int, int], dict]:
    res = load(FILE)
    out = {}
    for (i, k), s in cases().items():
        h = record_hearing(res[f"{i}|{k}|a"], res[f"{i}|{k}|b"])
        out[i, k] = h | {"outcome": readout.outcome(h, mood.product(s).hunger)}
    return out


def input_quality(res: dict) -> dict:
    """Densest 10%-of-range band of tasting MN9; rho of per-argument MN9 with length, ד/ב/ש."""
    per = defaultdict(list)
    for key, m in res.items():
        i, _, side = key.split("|")
        per[2 * int(i) + (side == "b")].append(sum(m["MN9"]))
    args = arguments()
    mean = [float(np.mean(per[j])) for j in range(len(args))]
    return {"band": densest_band([x for v in per.values() for x in v])[0],
            "rho_len": spearman(mean, [len(a) for a in args]),
            "rho_honey": spearman(mean, [honey(a) for a in args])}


def summary() -> dict:
    hs, res = hearings(), load(FILE)
    main = [hs[i, 0] for i in range(N_PAIRS)]
    wins = [h["winner"] for h in main if h["outcome"] == "win"]
    consistent = []
    for i in range(N_CONSIST):
        per = [hs[i, k] for k in range(N_SEEDS)]
        a, b = (np.mean([h[x] for h in per]) for x in "AB")
        if a + b and abs(a - b) / (a + b) >= NONTRIVIAL:
            won = Counter(h["winner"] for h in per if h["outcome"] == "win")
            consistent.append(max(won.values(), default=0) / N_SEEDS)
    longer = []
    for i, h in enumerate(main):
        la, lb = (len(taste.normalize(t)) for t in _pair(i))
        if h["outcome"] == "win" and la != lb:
            longer.append((la > lb) == (h["winner"] == "A"))
    active = [r["active"] for r in res.values()]
    return {"hearings": len(main), "a_wins": wins.count("A") / len(wins), "decided": len(wins),
            "outcomes": {o: c / len(main) for o, c in Counter(h["outcome"] for h in main).items()},
            "consistent": consistent, "runaway": float(np.mean([a > RUNAWAY for a in active])),
            "tastings": len(active), "longer_wins": float(np.mean(longer)), "longer_n": len(longer),
            "gap_pct": np.percentile([h["gap"] for h in main], [10, 25, 50, 75, 90]).round(3).tolist(),
            "gf_tastings": sum(r["gf_spikes"] > 0 for r in res.values())} | input_quality(res)


def timing():
    """Product-style hearing time on an idle machine; also checks the runner records."""
    model, hs = connectome_model(), hearings()
    jobs = []
    for i in range(TIME_N):
        m, s = mood.product(CASE0 + i), CASE0 + i
        jobs.append((*(mood.tasting(t, m) for t in _pair(i)), s, m.noise_hz))
    results, times = timed_hearings(model, jobs, TASTING_MS)
    same = 0
    for i, (ra, rb) in enumerate(results):
        h = readout.hearing(ra, rb, TASTING_MS / 1000)
        h["outcome"] = readout.outcome(h, mood.product(CASE0 + i).hunger)
        same += all(h[k] == hs[i, 0][k] for k in ("A", "B", "gap", "direction_flips",
                                                  "decision_time_ms", "winner", "outcome"))
    row = {"median_s": round(statistics.median(times), 2), "times_s": [round(t, 2) for t in times],
           "records_match": f"{same}/{TIME_N}", "platform": PLATFORM,
           "peak_rss_gb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2),
           "peak_rss_child_gb": round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1e6, 2)}
    (OUT / TIME_FILE).write_text(json.dumps(row) + "\n")
    print(json.dumps(row), flush=True)


def report():
    s = summary()
    c = s.pop("consistent")
    print(json.dumps(s, indent=1))
    print(f"seed consistency: non-trivial {len(c)}/{N_CONSIST}; >= 75%: {sum(x >= 0.75 for x in c)}; "
          f"values {sorted(round(x, 1) for x in c)}")
    if (OUT / TIME_FILE).exists():
        print((OUT / TIME_FILE).read_text())


if __name__ == "__main__":
    {"run": run, "time": timing, "report": report}[sys.argv[1]]()
