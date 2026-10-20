"""Smell of words (SPEC §4): Hebrew argument text → ORN Poisson drive.

normalize → count the 22 letters and "!" "?" → saturating rate per
glomerulus × log length gain → per-ORN rates on one antenna, scaled so a
glomerulus delivers the same total drive (rate × ORNs) on either side.
"""
import math
import re
import unicodedata
from collections import Counter
from functools import cache

from borer_sim import anatomy
from borer_sim.params import SMELL

ATTRACTIVE, AVERSIVE, NEUTRAL = "attractive", "aversive", "neutral"

# Letter → antennal glomerulus → valence. The one mapping table; citations,
# letter frequencies and the balance check: DECISIONS.md 2026-10-20 (P1-6).
LETTERS = {
    "ד": ("DM1", ATTRACTIVE), "ב": ("VA2", ATTRACTIVE), "ש": ("DM2", ATTRACTIVE),
    "ו": ("DC3", ATTRACTIVE), "ל": ("VM1", ATTRACTIVE), "ט": ("VC5", ATTRACTIVE),
    "ג": ("VL2a", ATTRACTIVE),
    "מ": ("DM5", AVERSIVE), "ר": ("DL4", AVERSIVE), "ע": ("D", AVERSIVE),
    "ת": ("DL5", AVERSIVE), "נ": ("DM6", AVERSIVE), "א": ("VA6", AVERSIVE),
    "ז": ("DC4", AVERSIVE),
    "י": ("VA1d", NEUTRAL), "ה": ("DL3", NEUTRAL), "כ": ("DA4l", NEUTRAL),
    "ח": ("DA3", NEUTRAL), "ק": ("VA1v", NEUTRAL), "פ": ("DC1", NEUTRAL),
    "ס": ("VM2", NEUTRAL), "צ": ("VA3", NEUTRAL),
}
EXCLAMATION = ("!", "V")    # CO₂ — aversive
QUESTION = ("?", "DA2")     # geosmin — aversive
FINALS = str.maketrans("ךםןףץ", "כמנפצ")


def normalize(text: str) -> str:
    """Strip niqqud/cantillation, collapse whitespace, finals → regular, cap length."""
    text = "".join(c for c in unicodedata.normalize("NFKD", text)
                   if unicodedata.category(c) != "Mn")
    text = re.sub(r"\s+", " ", text).strip().translate(FINALS)
    return text[:SMELL["max_chars"]]


def length_gain(n_chars: int) -> float:
    """Logarithmic gain on intensity; 1 at len_ref chars."""
    return math.log1p(n_chars) / math.log1p(SMELL["len_ref"])


def _saturate(x: float, k: float, r_max: float) -> float:
    return SMELL["r_base"] + r_max * x / (x + k) if x > 0 else SMELL["r_base"]


def glomerulus_rates(text: str) -> dict[str, float]:
    """Rate (Hz) per glomerulus for one argument, before side balancing."""
    s = SMELL
    norm = normalize(text)
    counts = Counter(norm)
    n_letters = sum(counts[letter] for letter in LETTERS)
    gain = length_gain(len(norm))
    rates = {glom: _saturate(counts[letter] / n_letters if n_letters else 0.0,
                             s["k"], gain * s["r_max"])
             for letter, (glom, _) in LETTERS.items()}
    excess = max(0.0, gain - 1) / (length_gain(s["max_chars"]) - 1)
    for (mark, glom), extra in ((EXCLAMATION, s["verbose_marks"] * excess), (QUESTION, 0.0)):
        rates[glom] = _saturate(counts[mark] + extra, s["punct_k"], s["punct_max"])
    return rates


@cache
def _orns(glomerulus: str) -> dict[str, list[int]]:
    return {side: anatomy.orns(glomerulus, side) for side in anatomy.SIDES}


def drives(text: str, side: str) -> list[tuple[list[int], float]]:
    """Poisson drive [(model indices, per-ORN rate Hz)] for `text` on one antenna."""
    if side not in anatomy.SIDES:
        raise ValueError(f"side must be one of {anatomy.SIDES}, got {side!r}")
    out = []
    for glom, rate in glomerulus_rates(text).items():
        orns = _orns(glom)
        mean_n = sum(len(o) for o in orns.values()) / len(orns)
        out.append((orns[side], rate * mean_n / len(orns[side])))
    return out
