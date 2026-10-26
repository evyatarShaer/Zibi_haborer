"""Fly mood (SPEC §5): hunger and arousal, an added layer on top of the connectome.

Seeded per case from its seed on a stream separate from the simulation's, and
applied identically to both tastings of a hearing: hunger scales the drive of
the MN9-exciting letter groups (TABLE class E), arousal sets background noise
(model.run noise_hz). Hunger rises while the case waits for both arguments.
"""
from dataclasses import dataclass

import numpy as np

from borer_sim import taste
from borer_sim.params import MOOD

STREAM = 0x6D6F6F64  # "mood": keeps mood draws independent of the simulation seed's use
WAIT_STREAM = 0x77616974  # "wait": the simulated wait of a hearing without one
EXCITING = tuple(k for k, (_, note) in taste.TABLE.items() if note.startswith("E"))


@dataclass(frozen=True)
class Mood:
    hunger: float
    arousal: float

    @property
    def gains(self) -> dict[str, float]:
        """Rate-above-baseline factor per MN9-exciting letter."""
        return {k: 1.0 + MOOD["hunger_gain"] * self.hunger for k in EXCITING}

    @property
    def noise_hz(self) -> float:
        return self.arousal * MOOD["noise_hz"]


def from_case(case_seed: int, wait_hours: float = 0.0) -> Mood:
    """A hearing's mood after waiting `wait_hours` (case open → B submits; the 3 h deadline
    for a no-show). An appeal passes its own seed with the case's wait (SPEC §15.4)."""
    hunger, arousal = np.random.default_rng((case_seed, STREAM)).random(2)
    wait = min(max(0.0, wait_hours), MOOD["deadline_h"])
    hunger = hunger * MOOD["hunger_base_max"] + MOOD["hunger_per_hour"] * wait
    return Mood(float(min(1.0, hunger)), float(arousal * MOOD["arousal_max"]))


def product(seed: int) -> Mood:
    """A hearing's mood when nobody waited (SPEC §5, §14): the wait is drawn from the seed,
    ~ Exp(wait_mean_h) h, as validated in P1-9 (DECISIONS.md 2026-10-25)."""
    wait = float(np.random.default_rng((seed, WAIT_STREAM)).exponential(MOOD["wait_mean_h"]))
    return from_case(seed, wait)


def tasting(text: str, mood: Mood) -> list[tuple[list[int], float]]:
    """taste.tasting with the mood's hunger gains (noise is passed to model.run)."""
    return taste.tasting(text, mood.gains)
