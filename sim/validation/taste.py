"""Prototype B, "taste of words": letters -> gustatory receptor neuron (GRN) groups.

Validation only; smell.py is unchanged. Groups are built at runtime from
the v783 annotations: one group per (cell_sub_class, cell_type) with
>= MIN_PER_SIDE GRNs on each side. A letter keeps its valence from
smell.LETTERS and gets a GRN group of the same valence; if a valence runs
short, its largest groups are split in two (by sorted root_id). Rates come
from smell.glomerulus_rates (same normalization, saturation, length gain,
caps), side-balanced like smell.drives.
"""
from functools import cache

import pandas as pd

from borer_sim import anatomy, data, smell

MIN_PER_SIDE = 2
VALENCE = {  # GRN sub-class -> valence used for the mapping (labellar taste literature)
    "sugar": smell.ATTRACTIVE, "sugar/low_salt": smell.ATTRACTIVE,
    "water": smell.ATTRACTIVE, "putative_attractive": smell.ATTRACTIVE,
    "bitter": smell.AVERSIVE, "high_salt/heavy_metal": smell.AVERSIVE,
    "putative_aversive": smell.AVERSIVE,
}
PUNCT = {"!": "bitter:LB1a", "?": "high_salt/heavy_metal:LB3d"}  # one aversive type each
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


def _splittable(group, g) -> bool:
    sides = g.loc[group[2], "side"].value_counts().reindex(anatomy.SIDES, fill_value=0)
    return sides.min() >= 2 * MIN_PER_SIDE


def _split(group, g):
    name, val, ids = group
    halves = []
    for k in (0, 1):
        sub = pd.Index([i for side in anatomy.SIDES
                        for i in sorted(g.loc[ids][g.loc[ids, "side"] == side].index)[k::2]])
        halves.append((f"{name}/{k + 1}", val, sub))
    return halves


@cache
def mapping() -> dict[str, tuple[str, pd.Index]]:
    """letter or mark -> (GRN group name, root_ids). Deterministic."""
    g = grns()
    pool = {p[0]: p for p in _groups(g)}
    out = {mark: (name, pool.pop(name)[2]) for mark, name in PUNCT.items()}
    pool = list(pool.values())
    for val in (smell.ATTRACTIVE, smell.AVERSIVE, smell.NEUTRAL):
        letters = [l for l, (_, v) in smell.LETTERS.items() if v == val]
        groups = sorted((p for p in pool if p[1] == val), key=lambda p: -len(p[2]))
        while len(groups) < len(letters):
            big = next((p for p in groups if _splittable(p, g)), None)
            if big is None:
                break
            groups = sorted([p for p in groups if p is not big] + _split(big, g),
                            key=lambda p: -len(p[2]))
        if len(groups) < len(letters):
            raise ValueError(f"{val}: {len(groups)} GRN groups for {len(letters)} letters")
        for letter, (name, _, ids) in zip(letters, groups):
            out[letter] = (name, ids)
    return out


@cache
def _side_indices(letter: str) -> dict[str, list[int]]:
    g = grns()
    ids = mapping()[letter][1]
    return {s: data.to_index(ids[g.loc[ids, "side"] == s]) for s in anatomy.SIDES}


def drives(text: str, side: str, scale: float = 1.0):
    """GRN Poisson drive for `text` on one side, side-balanced per group."""
    rates = smell.glomerulus_rates(text)
    keyed = {l: rates[gl] for l, (gl, _) in smell.LETTERS.items()}
    keyed |= {smell.EXCLAMATION[0]: rates[smell.EXCLAMATION[1]],
              smell.QUESTION[0]: rates[smell.QUESTION[1]]}
    out = []
    for key, rate in keyed.items():
        idx = _side_indices(key)
        mean_n = sum(len(v) for v in idx.values()) / 2
        out.append((idx[side], rate * scale * mean_n / len(idx[side])))
    return out
