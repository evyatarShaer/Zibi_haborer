"""Hebrew offensive-word filter (SPEC §15.5): a plain list, no AI.

Texts and entries are compared after §4.1 normalization (borer_sim.taste.normalize: niqqud
stripped, final letters regular). Entries match whole Hebrew words, with up to 3 of the
prefixes ו ה ב כ ל מ ש allowed in front of the first word; a multi-word entry matches its
words in a row. The list is api/moderation/words.txt (BORER_WORDS; git-ignored, from the
owner). Without it, words.example.txt is used and a warning is logged.
"""
import functools
import logging
import os
import re
from pathlib import Path

from borer_sim.taste import LETTERS, normalize

DIR = Path(__file__).resolve().parents[2] / "moderation"
WORDS = Path(os.environ.get("BORER_WORDS", DIR / "words.txt"))
EXAMPLE = DIR / "words.example.txt"
PREFIX = re.compile("[ובהכלמש]{0,3}")
WORD = re.compile(f"[{LETTERS}]+")

log = logging.getLogger(__name__)


def words(text: str) -> list[str]:
    """The Hebrew words of `text` after §4.1 normalization."""
    return WORD.findall(normalize(text))


def parse(lines) -> list[tuple[str, ...]]:
    """Entries as word tuples; comments, blank lines and non-Hebrew lines are dropped."""
    return [tuple(w) for line in lines
            if not line.lstrip().startswith("#") and (w := words(line))]


@functools.cache
def entries() -> list[tuple[str, ...]]:
    path = WORDS
    if not path.exists():
        log.warning("no word list at %s; using %s", path, EXAMPLE)
        path = EXAMPLE
    return parse(path.read_text(encoding="utf-8").splitlines())


def _match(entry: tuple[str, ...], ws: list[str], i: int) -> bool:
    first = ws[i]
    if not (first.endswith(entry[0]) and PREFIX.fullmatch(first[:len(first) - len(entry[0])])):
        return False
    return tuple(ws[i + 1:i + len(entry)]) == entry[1:]


def offensive(text: str, listed: list[tuple[str, ...]] | None = None) -> bool:
    """True if any listed entry appears in `text` (default: the loaded list)."""
    ws = words(text)
    return any(_match(e, ws, i) for e in (entries() if listed is None else listed)
               for i in range(len(ws)))
