"""Argument rule (SPEC §3): what may be submitted. The simulation itself handles any text
safely (§4.6); this check is for the UI and the API only."""
from borer_sim.taste import LETTERS, normalize

MIN_LETTERS = 10  # Hebrew letters after normalization


def hebrew_letters(text: str) -> int:
    return sum(c in LETTERS for c in normalize(text))
