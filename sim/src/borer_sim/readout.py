"""Hearing readout and outcome (SPEC §6–§7).

A hearing = two tastings (side A's argument, side B's), same seed, same mood.
A, B = total MN9 rate (Hz, L + R) of each tasting. Binned A − B uses
OUTCOME["readout_bin_ms"] bins of MN9 spikes. Pure functions of spike counts,
so validation records (stored bins) and product runs share one code path.
"""
import numpy as np

from borer_sim import anatomy, data, mood
from borer_sim.model import Model, Result
from borer_sim.params import BIN_MS, OUTCOME, TASTING_MS

OUTCOMES = ("fled", "froze", "food", "dithered", "win", "tie")  # SPEC §7 order


def _both(cells) -> list[int]:
    """Model indices of a per-side cell set (anatomy.mn9 / giant_fiber), left then right."""
    return [i for side in anatomy.SIDES for i in cells(side)]


def _rows(result: Result, idx: list[int]) -> np.ndarray:
    """(n_bins, len(idx)) spikes of model neurons `idx` per BIN_MS bin."""
    pos = np.searchsorted(result.active, idx)
    hit = (pos < len(result.active)) & (result.active[np.minimum(pos, len(result.active) - 1)] == idx)
    out = np.zeros((result.binned.shape[0], len(idx)), dtype=np.int64)
    out[:, hit] = result.binned[:, pos[hit]]
    return out


def mn9_bins(result: Result) -> np.ndarray:
    """MN9 spikes (L + R) per readout bin."""
    per = round(OUTCOME["readout_bin_ms"] / BIN_MS)
    s = _rows(result, _both(anatomy.mn9)).sum(1)
    return np.add.reduceat(s, np.arange(0, len(s), per))


def flips(diff) -> int:
    """Sign changes in a sequence, zeros skipped."""
    s = np.sign(np.asarray(diff))
    s = s[s != 0]
    return int((s[1:] != s[:-1]).sum())


def decision_time_ms(diff) -> float | None:
    """End of the first bin from which the cumulative A − B stays at or beyond
    decision_spikes on the final winner's side; None if it never gets there."""
    cum = np.cumsum(diff)
    sign = np.sign(cum[-1]) if len(cum) else 0
    if sign == 0 or sign * cum[-1] < OUTCOME["decision_spikes"]:
        return None
    below = np.flatnonzero(sign * cum < OUTCOME["decision_spikes"])
    first = below[-1] + 1 if len(below) else 0
    return float((first + 1) * OUTCOME["readout_bin_ms"])


def metrics(bins_a, bins_b, seconds: float) -> dict:
    """A, B, margin, gap, winner, decision_time_ms, direction_flips from MN9 bins."""
    a, b = np.sum(bins_a) / seconds, np.sum(bins_b) / seconds
    diff = np.asarray(bins_a) - np.asarray(bins_b)
    gap = abs(a - b) / (a + b) if a + b else 0.0
    return {"A": float(a), "B": float(b), "margin": (1 + gap) / 2, "gap": float(gap),
            "winner": "A" if a > b else "B" if b > a else None,
            "decision_time_ms": decision_time_ms(diff), "direction_flips": flips(diff)}


def outcome(m: dict, hunger: float) -> str:
    """SPEC §7: first matching row wins."""
    o, close = OUTCOME, m["gap"] < OUTCOME["tie_gap"]
    if m["giant_fiber_fired"]:
        return "fled"
    if m["A"] < o["froze_hz"] and m["B"] < o["froze_hz"]:
        return "froze"
    if hunger > o["food_hunger"] and close:
        return "food"
    if m["direction_flips"] >= o["dither_flips"] and close:
        return "dithered"
    return "tie" if close else "win"


def hearing(res_a: Result, res_b: Result, seconds: float) -> dict:
    """All SPEC §6 metrics of one hearing."""
    m = metrics(mn9_bins(res_a), mn9_bins(res_b), seconds)
    gf = _both(anatomy.giant_fiber)
    m["giant_fiber_fired"] = bool(res_a.counts[gf].sum() + res_b.counts[gf].sum())
    m["active_neurons"] = [len(res_a.active), len(res_b.active)]
    m["deciding_neuron"] = None
    if m["winner"]:
        res = res_a if m["winner"] == "A" else res_b
        mn9 = _both(anatomy.mn9)
        best = mn9[int(np.argmax(res.counts[mn9]))]
        m["deciding_neuron"] = {"side": "left" if best in anatomy.mn9("left") else "right",
                                "root_id": int(data.neuron_ids()[best])}
    return m


def run_hearing(model: Model, text_a: str, text_b: str, case_mood: mood.Mood, seed: int,
                duration_ms: float = TASTING_MS) -> dict:
    """Both tastings (same seed, same mood; run one after the other here) → metrics + outcome."""
    res = [model.run(mood.tasting(t, case_mood), duration_ms, seed, case_mood.noise_hz)
           for t in (text_a, text_b)]
    m = hearing(*res, duration_ms / 1000)
    return m | {"outcome": outcome(m, case_mood.hunger)}
