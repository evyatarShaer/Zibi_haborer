"""Prototype B, "taste of words": letters -> gustatory receptor neuron (GRN) groups.

Validation only; smell.py is unchanged. Groups are built at runtime from
the v783 annotations: one group per (cell_sub_class, cell_type) with
>= MIN_PER_SIDE GRNs on each side. Each letter / mark gets one group by its
measured effect on MN9 (TABLE; literature valence only cross-checked). Rates come
from letter_rates: the smell.py formula on frequency-relative letter shares,
with the letters' total drive fixed by length (same caps for ! and ?),
side-balanced like smell.drives.
"""
from collections import Counter
from functools import cache

import pandas as pd

from borer_sim import anatomy, data, smell
from tests.test_smell import HEBREW_FREQ  # Rabinovich & Wintner 2016 corpus frequencies

MIN_PER_SIDE = 2
VALENCE = {  # GRN sub-class -> literature valence (labellar taste), cross-check only
    "sugar": smell.ATTRACTIVE, "sugar/low_salt": smell.ATTRACTIVE,
    "water": smell.ATTRACTIVE, "putative_attractive": smell.ATTRACTIVE,
    "bitter": smell.AVERSIVE, "high_salt/heavy_metal": smell.AVERSIVE,
    "putative_aversive": smell.AVERSIVE,
}
# Letter / mark -> GRN group, by MEASURED effect on MN9 (validation/taste_valence.py:
# sugar LB3c at 75 Hz -> MN9 69.7 Hz, + group at 150 Hz, 3 seeds, 1 s). Class E/I/N =
# delta >= +10.5 / <= -10.5 Hz (15% of background) / between; literature (VALENCE) is a
# cross-check only. Rule: ד ב ש -> the 3 strongest exciters (MN9 alone 134/142/94 Hz);
# ! ? -> inhibitors; the other 19 letters by Hebrew frequency dealt E,I,N,E,I,N,... until
# N runs out, stronger groups to more frequent letters within a class.
TABLE = {  # key: (group, "class delta Hz | literature")
    "ד": ("sugar:LB3c", "E alone 134 | attractive"),
    "ב": ("high_salt/heavy_metal:LB3d", "E +96 | aversive"),
    "ש": ("accessory_pharyngeal_nerve_sensory_group1:PhG1c", "E +51 | neutral"),
    "!": ("bitter:LB1a", "I -24 | aversive"),
    "?": ("putative_aversive:LB2c", "I -47 | aversive"),
    "י": ("accessory_pharyngeal_nerve_sensory_group1:PhG4", "E +42 | neutral"),
    "ו": ("SA_VTV_pro_meso_meta:LgAG5", "I -70 | neutral"),
    "ה": ("SA_VTV_pro_meso_meta:LgAG4", "N +2 | neutral"),
    "מ": ("putative_attractive:LB4b", "E +37 | attractive"),
    "ל": ("glutamate:LB1e", "I -70 | neutral"),
    "ר": ("taste peg:claw_tpGRN", "N -2 | neutral"),
    "ת": ("putative_attractive:LB4a", "E +35 | attractive"),
    "א": ("bitter:LB1c", "I -69 | aversive"),
    "נ": ("putative_aversive:LB2b", "N -8 | aversive"),
    "ע": ("putative_aversive:LB2a", "E +34 | aversive"),
    "כ": ("bitter:LB1b", "I -68 | aversive"),
    "ח": ("SA_VTV_pro_meso_meta:LgAG8", "N -9 | neutral"),
    "ק": ("SA_VTV_pro_meso_meta:LgAG2", "E +33 | neutral"),
    "פ": ("water:LB3a", "I -22 | attractive"),
    "ס": ("SA_VTV_pro_meso_meta:LgAG6", "E +27 | neutral"),
    "צ": ("SA_VTV_pro_meso_meta:LgAG1", "I -19 | neutral"),
    "ג": ("taste peg:dorsal_tpGRN", "E +19 | neutral"),
    "ט": ("SA_VTV_pro_meso_meta:LgAG7", "I -16 | neutral"),
    "ז": ("bitter:LB1d", "I -13 | aversive"),
}
# Groups that ignite the runaway alone at 150 Hz (taste_probe screen, > 4,000 active):
# LB3b 3/3 seeds (~8.5k active), LgAG3 2/3 seeds (~8.4k). All other groups <= 565.
EXCLUDED = {"sugar/low_salt:LB3b", "SA_VTV_pro_meso_meta:LgAG3"}


def grns() -> pd.DataFrame:
    a = data.annotations()
    g = a[(a["cell_class"] == "gustatory") & a.index.isin(data.neuron_ids())
          & a["side"].isin(anatomy.SIDES)].copy()
    g["valence"] = g["cell_sub_class"].map(VALENCE).fillna(smell.NEUTRAL)
    return g


def inventory() -> pd.DataFrame:
    """GRN counts per sub-class x nerve (organ) x side."""
    g = grns()
    return g.groupby(["cell_sub_class", "nerve", "side"], dropna=False).size().unstack(fill_value=0)


def _groups(g: pd.DataFrame) -> list[tuple[str, str, pd.Index]]:
    """(name, valence, root_ids) for every group with enough GRNs on both sides."""
    out = []
    for (sub, ct), d in g.groupby(["cell_sub_class", "cell_type"], dropna=True):
        name = f"{sub}:{ct}"
        if (name not in EXCLUDED and
                d["side"].value_counts().reindex(anatomy.SIDES, fill_value=0).min() >= MIN_PER_SIDE):
            out.append((name, d["valence"].iloc[0], d.index))
    return out


@cache
def mapping() -> dict[str, tuple[str, pd.Index]]:
    """letter or mark -> (GRN group name, root_ids), from TABLE."""
    pool = {name: ids for name, _, ids in _groups(grns())}
    return {key: (name, pool[name]) for key, (name, _) in TABLE.items()}


@cache
def _side_indices(letter: str) -> dict[str, list[int]]:
    g = grns()
    ids = mapping()[letter][1]
    return {s: data.to_index(ids[g.loc[ids, "side"] == s]) for s in anatomy.SIDES}


def _n(key: str) -> int:
    return len(mapping()[key][1])


@cache
def _reference_total() -> float:
    """Letters' excess drive (Hz x GRNs) at gain 1 when all 22 letters have equal share."""
    sm = smell.SMELL
    per = smell._saturate(1 / len(smell.LETTERS), sm["k"], sm["r_max"]) - sm["r_base"]
    return per * sum(_n(l) for l in smell.LETTERS)


def letter_rates(text: str) -> dict[str, float]:
    """Per-GRN rate per letter (plus "!" and "?"), from the text's letter mix.

    Two fixes for the length bias (POC_REPORT, taste probe rerun):
    1. A letter's input is its share relative to its Hebrew corpus frequency, so
       an average Hebrew mix drives every letter alike. With raw shares a long
       text converges to the average mix, which sits near MN9's floor, so long
       texts could only lose.
    2. The letters' total excess drive is fixed at _reference_total() x length
       gain, so covering more letters adds no drive; the text sets only the split.
    """
    sm = smell.SMELL
    norm = smell.normalize(text)
    counts = Counter(norm)
    n = sum(counts[l] for l in smell.LETTERS)
    gain = smell.length_gain(len(norm))
    keyed = {l: smell._saturate(counts[l] / n / (HEBREW_FREQ[l] * len(smell.LETTERS)) if n else 0.0,
                                sm["k"], gain * sm["r_max"]) for l in smell.LETTERS}
    total = sum((r - sm["r_base"]) * _n(l) for l, r in keyed.items())
    target = _reference_total() * gain
    keyed = {l: sm["r_base"] + (r - sm["r_base"]) * target / total if total else sm["r_base"]
             for l, r in keyed.items()}
    rates = smell.glomerulus_rates(text)
    return keyed | {smell.EXCLAMATION[0]: rates[smell.EXCLAMATION[1]],
                    smell.QUESTION[0]: rates[smell.QUESTION[1]]}


def drives(text: str, side: str, scale: float = 1.0):
    """GRN Poisson drive for `text` on one side, side-balanced per group."""
    out = []
    for key, rate in letter_rates(text).items():
        idx = _side_indices(key)
        mean_n = sum(len(v) for v in idx.values()) / 2
        out.append((idx[side], rate * scale * mean_n / len(idx[side])))
    return out
