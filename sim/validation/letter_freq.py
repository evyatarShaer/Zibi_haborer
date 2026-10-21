"""Conversational Hebrew letter frequencies (OpenSubtitles 2018, OPUS word counts).

Run from sim/ to recompute CHAT_FREQ:
    PYTHONPATH=src uv run python -m validation.letter_freq data/raw/opus_he_freq/he.freq.gz
Each token's letters (smell.normalize: niqqud stripped, finals merged) are
weighted by its count. Source and checksum: docs/DATA_SOURCES.md.
"""
import gzip
import sys
from collections import Counter

from borer_sim import smell

CHAT_FREQ = {  # compute() output, 2026-10-21; DATA_SOURCES.md
    "ד": 0.02602, "ב": 0.04379, "ש": 0.04539, "ו": 0.09726, "ל": 0.07375,
    "ט": 0.01170, "ג": 0.01234, "מ": 0.07157, "ר": 0.04880, "ע": 0.02735,
    "ת": 0.06090, "נ": 0.05120, "א": 0.08264, "ז": 0.01826, "י": 0.11241,
    "ה": 0.09138, "כ": 0.03692, "ח": 0.02357, "ק": 0.02006, "פ": 0.01720,
    "ס": 0.01491, "צ": 0.01258,
}


def compute(path: str) -> dict[str, float]:
    counts = Counter()
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            n, _, token = line.strip().partition(" ")
            if not n.isdigit():
                continue
            for ch in smell.normalize(token):
                if ch in smell.LETTERS:
                    counts[ch] += int(n)
    total = sum(counts.values())
    return {l: round(counts[l] / total, 5) for l in smell.LETTERS}


if __name__ == "__main__":
    freq = compute(sys.argv[1])
    print("CHAT_FREQ = {")
    items = list(freq.items())
    for i in range(0, len(items), 5):
        print("    " + " ".join(f'"{l}": {v:.5f},' for l, v in items[i:i + 5]))
    print("}")
