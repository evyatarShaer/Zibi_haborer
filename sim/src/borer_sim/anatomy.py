"""Named neuron sets, selected at runtime from the v783 annotations.

No root_id is hard-coded: every set is a filter on data.annotations(),
restricted to neurons in the model and returned as sorted model indices
via data.to_index(). Annotation `side` is the fly's own side (evidence:
flywire-data skill, DECISIONS.md 2026-10-20).
"""
from functools import cache

import pandas as pd

from borer_sim import data

SIDES = ("left", "right")
ORN_PREFIX = "ORN_"
TURNING_DN = "DNa02"
GIANT_FIBER = "DNp01"


@cache
def _in_model() -> pd.DataFrame:
    a = data.annotations()
    return a[a.index.isin(data.neuron_ids())]


def cell_type(name: str, side: str) -> list[int]:
    """Model indices of all `name` neurons whose soma is on `side`."""
    if side not in SIDES:
        raise ValueError(f"side must be one of {SIDES}, got {side!r}")
    a = _in_model()
    ids = a.index[(a.cell_type == name) & (a.side == side)]
    if ids.empty:
        raise KeyError(f"no {side} {name} neurons in the v783 model")
    return sorted(data.to_index(ids))


def orns(glomerulus: str, side: str) -> list[int]:
    """ORNs projecting to `glomerulus` (e.g. "V", "DA2") from `side`."""
    return cell_type(ORN_PREFIX + glomerulus, side)


def turning_dns(side: str) -> list[int]:
    return cell_type(TURNING_DN, side)


def giant_fiber(side: str) -> list[int]:
    return cell_type(GIANT_FIBER, side)


def orn_glomeruli() -> pd.DataFrame:
    """ORN count per glomerulus (rows) and side, plus the entry nerve(s).

    nerve "AN" = antenna, "MxLbN" = maxillary palp. ORNs with side "na"
    are not counted (they can't be assigned to an antenna).
    """
    a = _in_model()
    o = a[a.cell_type.str.startswith(ORN_PREFIX, na=False) & a.side.isin(SIDES)]
    glom = o.cell_type.str.removeprefix(ORN_PREFIX).rename("glomerulus")
    table = o.groupby([glom, "side"]).size().unstack(fill_value=0)[list(SIDES)]
    table["nerve"] = o.groupby(glom).nerve.agg(
        lambda s: "+".join(sorted(s.dropna().unique())))
    return table
