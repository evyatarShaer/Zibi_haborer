"""Conversational Hebrew letter frequencies (OpenSubtitles 2018, OPUS word counts).

Run from sim/ to recompute borer_sim.taste.CHAT_FREQ:
    PYTHONPATH=src uv run python -m validation.letter_freq data/raw/opus_he_freq/he.freq.gz
Each token's letters (taste.normalize: niqqud stripped, finals merged) are
weighted by its count. Source and checksum: docs/DATA_SOURCES.md.
"""
import gzip
import sys
from collections import Counter

from borer_sim import taste


def compute(path: str) -> dict[str, float]:
    counts = Counter()
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            n, _, token = line.strip().partition(" ")
            if not n.isdigit():
                continue
            for ch in taste.normalize(token):
                if ch in taste.LETTERS:
                    counts[ch] += int(n)
    total = sum(counts.values())
    return {l: round(counts[l] / total, 5) for l in taste.LETTERS}


if __name__ == "__main__":
    freq = compute(sys.argv[1])
    print("CHAT_FREQ = {")
    items = list(freq.items())
    for i in range(0, len(items), 5):
        print("    " + " ".join(f'"{l}": {v:.5f},' for l, v in items[i:i + 5]))
    print("}")
