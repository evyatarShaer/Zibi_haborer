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
MN9 = "CB0701"        # proboscis motor neuron 9: the verdict readout (SPEC §6)
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


def mn9(side: str) -> list[int]:
    return cell_type(MN9, side)


def giant_fiber(side: str) -> list[int]:
    return cell_type(GIANT_FIBER, side)

