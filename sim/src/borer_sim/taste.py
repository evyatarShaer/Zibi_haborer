"""Taste of words (SPEC §4): Hebrew argument text → GRN Poisson drive.

normalize → each letter's share relative to its conversational frequency →
saturating rate × log length gain, letters' total drive fixed → per-group cap →
× coverage (low-diversity text loses drive) → one rate per GRN group (TABLE),
"!" and "?" capped → per-GRN rates, side-balanced so a group delivers the same
total drive (rate × GRNs) on either side. A tasting
drives both sides at once. Sources and measurements: DECISIONS.md 2026-10-22.
"""
import math
import re
import unicodedata
from collections import Counter
from functools import cache

import pandas as pd

from borer_sim import anatomy, data
from borer_sim.params import TASTE

LETTERS = "דבשולטגמרעתנאזיהכחקפסצ"  # order is part of the result (float sums, drive order)
EXCLAMATION, QUESTION = "!", "?"
FINALS = str.maketrans("ךםןףץ", "כמנפצ")
MIN_PER_SIDE = 2
# Conversational Hebrew letter frequencies, finals merged: OpenSubtitles 2018 (OPUS word
# counts), computed by validation/letter_freq.py; source and checksum: DATA_SOURCES.md.
CHAT_FREQ = {
    "ד": 0.02602, "ב": 0.04379, "ש": 0.04539, "ו": 0.09726, "ל": 0.07375,
    "ט": 0.01170, "ג": 0.01234, "מ": 0.07157, "ר": 0.04880, "ע": 0.02735,
    "ת": 0.06090, "נ": 0.05120, "א": 0.08264, "ז": 0.01826, "י": 0.11241,
    "ה": 0.09138, "כ": 0.03692, "ח": 0.02357, "ק": 0.02006, "פ": 0.01720,
    "ס": 0.01491, "צ": 0.01258,
}
# Letter / mark -> GRN group (table v4, SIM_VERSION 0.4.0), by MEASURED effect on MN9
# (validation/taste_valence.py: sugar LB3c at 75 Hz -> MN9 69.7 Hz, + group at 150 Hz,
# 3 seeds, 1 s). Class E/I/N = delta >= +10.5 / <= -10.5 Hz / between; literature valence
# is a cross-check only. LB3c and LB3d (the only groups that drive MN9 alone) go as halves
# to the 4 most frequent letters; ד ב ש -> the next exciters; ! ? -> inhibitors; the other
# 15 letters by CHAT_FREQ dealt E,I,N,..., stronger |delta| to more frequent letters.
# Unused: LgAG7 (I -16), LB1d (I -13).
TABLE = {  # key: (group, "class delta Hz | literature")
    "י": ("high_salt/heavy_metal:LB3d/a", "E alone 91 | aversive"),
    "ו": ("sugar:LB3c/a", "E alone 77 | attractive"),
    "ה": ("sugar:LB3c/b", "E alone 67 | attractive"),
    "א": ("high_salt/heavy_metal:LB3d/b", "E alone 53 | aversive"),
    "ד": ("accessory_pharyngeal_nerve_sensory_group1:PhG1c", "E +51 | neutral"),
    "ב": ("accessory_pharyngeal_nerve_sensory_group1:PhG4", "E +42 | neutral"),
    "ש": ("putative_attractive:LB4a", "E +35 | attractive"),
    "!": ("bitter:LB1a", "I -24 | aversive"),
    "?": ("putative_aversive:LB2c", "I -47 | aversive"),
    "ל": ("putative_attractive:LB4b", "E +37 | attractive"),
    "מ": ("SA_VTV_pro_meso_meta:LgAG5", "I -70 | neutral"),
    "ת": ("SA_VTV_pro_meso_meta:LgAG8", "N -9 | neutral"),
    "נ": ("putative_aversive:LB2a", "E +34 | aversive"),
    "ר": ("glutamate:LB1e", "I -70 | neutral"),
    "כ": ("putative_aversive:LB2b", "N -8 | aversive"),
    "ע": ("SA_VTV_pro_meso_meta:LgAG2", "E +33 | neutral"),
    "ח": ("bitter:LB1c", "I -69 | aversive"),
    "ק": ("taste peg:claw_tpGRN", "N -2 | neutral"),
    "ז": ("SA_VTV_pro_meso_meta:LgAG6", "E +27 | neutral"),
    "פ": ("bitter:LB1b", "I -68 | aversive"),
    "ס": ("SA_VTV_pro_meso_meta:LgAG4", "N +2 | neutral"),
    "צ": ("taste peg:dorsal_tpGRN", "E +19 | neutral"),
    "ג": ("water:LB3a", "I -22 | attractive"),
    "ט": ("SA_VTV_pro_meso_meta:LgAG1", "I -19 | neutral"),
}
# Ignite the runaway alone at 150 Hz (> 4,000 active): LB3b 3/3 seeds, LgAG3 2/3.
EXCLUDED = {"sugar/low_salt:LB3b", "SA_VTV_pro_meso_meta:LgAG3"}
# Also offered as halves "<group>/a", "/b": per side, GRNs sorted by root_id, dealt alternately.
SPLIT = {"sugar:LB3c", "high_salt/heavy_metal:LB3d"}


def normalize(text: str) -> str:
    """Strip niqqud/cantillation, collapse whitespace, finals → regular, cap length."""
    text = "".join(c for c in unicodedata.normalize("NFKD", text)
                   if unicodedata.category(c) != "Mn")
    text = re.sub(r"\s+", " ", text).strip().translate(FINALS)
    return text[:TASTE["max_chars"]]


def length_gain(n_chars: int) -> float:
    """Logarithmic gain on intensity; 1 at len_ref chars."""
    return math.log1p(n_chars) / math.log1p(TASTE["len_ref"])


def _saturate(x: float, k: float, r_max: float) -> float:
    return TASTE["r_base"] + r_max * x / (x + k) if x > 0 else TASTE["r_base"]


def grns() -> pd.DataFrame:
    """Gustatory neurons in the model with a known side."""
    a = data.annotations()
    return a[(a["cell_class"] == "gustatory") & a.index.isin(data.neuron_ids())
             & a["side"].isin(anatomy.SIDES)]


def groups() -> dict[str, pd.Index]:
    """GRN group name -> root_ids, for every group with enough GRNs on both sides."""
    out = {}
    for (sub, ct), d in grns().groupby(["cell_sub_class", "cell_type"], dropna=True):
        name = f"{sub}:{ct}"
        if (name not in EXCLUDED and
                d["side"].value_counts().reindex(anatomy.SIDES, fill_value=0).min() >= MIN_PER_SIDE):
            out[name] = d.index
            if name in SPLIT:
                ids = [sorted(d.index[d["side"] == side]) for side in anatomy.SIDES]
                for h, half in enumerate("ab"):
                    out[f"{name}/{half}"] = pd.Index([i for side in ids for i in side[h::2]])
    return out


@cache
def mapping() -> dict[str, tuple[str, pd.Index]]:
    """letter or mark -> (GRN group name, root_ids), from TABLE."""
    pool = groups()
    return {key: (name, pool[name]) for key, (name, _) in TABLE.items()}


@cache
def _side_indices(key: str) -> dict[str, list[int]]:
    side = grns()["side"]
    ids = mapping()[key][1]
    return {s: data.to_index(ids[side.loc[ids] == s]) for s in anatomy.SIDES}


def _n(key: str) -> int:
    return len(mapping()[key][1])


@cache
def _reference_total() -> float:
    """Letters' excess drive (Hz x GRNs) at gain 1 when all 22 letters have equal share."""
    per = _saturate(1 / len(LETTERS), TASTE["k"], TASTE["r_max"]) - TASTE["r_base"]
    return per * sum(_n(l) for l in LETTERS)


def coverage(counts: Counter) -> float:
    """Overlap of a letter count with CHAT_FREQ: sum of min(share, frequency), in [0, 1]."""
    n = sum(counts[l] for l in LETTERS)
    return sum(min(counts[l] / n, CHAT_FREQ[l]) for l in LETTERS) if n else 0.0


def letter_rates(text: str) -> dict[str, float]:
    """Per-GRN rate (Hz) per letter, plus "!" and "?", for one argument.

    A letter's input is its share relative to CHAT_FREQ, so an average chat mix
    drives every letter alike; the letters' total excess drive is fixed at
    _reference_total() x length gain, so the text sets only the split. Each
    letter's rate is then capped, and its excess scaled by coverage relative to
    coverage_ref (to the power coverage_power), so repeating one letter or word
    adds no drive. Marks are counted and capped; a text with Hebrew letters
    longer than len_ref adds up to verbose_marks "!" (no Hebrew: baseline only).
    """
    t, r_base = TASTE, TASTE["r_base"]
    norm = normalize(text)
    counts = Counter(norm)
    n = sum(counts[l] for l in LETTERS)
    gain = length_gain(len(norm))
    keyed = {l: _saturate(counts[l] / n / (CHAT_FREQ[l] * len(LETTERS)) if n else 0.0,
                          t["k"], gain * t["r_max"]) for l in LETTERS}
    total = sum((r - r_base) * _n(l) for l, r in keyed.items())
    target = _reference_total() * gain
    f = min(1.0, coverage(counts) / t["coverage_ref"]) ** t["coverage_power"]
    keyed = {l: r_base + min((r - r_base) * target / total, t["cap"] - r_base) * f
             if total else r_base for l, r in keyed.items()}
    excess = max(0.0, gain - 1) / (length_gain(t["max_chars"]) - 1) if n else 0.0
    return keyed | {
        EXCLAMATION: _saturate(counts[EXCLAMATION] + t["verbose_marks"] * excess,
                               t["punct_k"], t["punct_max"]),
        QUESTION: _saturate(counts[QUESTION] + 0.0, t["punct_k"], t["punct_max"])}


def drives(text: str, side: str, gains: dict | None = None) -> list[tuple[list[int], float]]:
    """Poisson drive [(model indices, per-GRN rate Hz)] for `text` on one side;
    `gains` {key: factor} scales a key's rate above r_base (mood, SPEC §5)."""
    if side not in anatomy.SIDES:
        raise ValueError(f"side must be one of {anatomy.SIDES}, got {side!r}")
    out, r_base = [], TASTE["r_base"]
    for key, rate in letter_rates(text).items():
        if gains and gains.get(key, 1.0) != 1.0:  # untouched keys keep their exact rate
            rate = r_base + (rate - r_base) * gains[key]
        idx = _side_indices(key)
        mean_n = sum(len(v) for v in idx.values()) / 2
        out.append((idx[side], rate * mean_n / len(idx[side])))
    return out


def tasting(text: str, gains: dict | None = None) -> list[tuple[list[int], float]]:
    """One tasting: the argument on both sides of the mouth at once."""
    return drives(text, "left", gains) + drives(text, "right", gains)
