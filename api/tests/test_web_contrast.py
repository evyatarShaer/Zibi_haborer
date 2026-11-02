"""WCAG AA (4.5:1) for every text/background token pair the pages use, in the day and the
night court (web/css/tokens.css; DECISIONS 2026-10-29)."""
import re

import pytest

from fake import ROOT

CSS = (ROOT / "web" / "css" / "tokens.css").read_text()
# (text, background): body text, muted text, buttons, links, meters, errors, the header
PAIRS = [("ink", "bg"), ("ink", "surface"), ("ink", "surface-2"), ("muted", "bg"), ("muted", "surface"),
         ("muted", "surface-2"), ("brand-ink", "brand"), ("brand-ink-2", "brand"), ("primary-ink", "primary"),
         ("wa-ink", "wa"), ("win", "surface"), ("win", "win-bg"), ("error", "surface"), ("error", "bg"),
         ("brand-text", "surface"), ("brand-text", "bg"), ("brand-text", "surface-2"), ("side-a", "surface"),
         ("side-b", "surface"), ("bg", "ink")]


def tokens(selector: str) -> dict:
    block = re.search(re.escape(selector) + r"\s*\{(.*?)\n\}", CSS, re.S).group(1)
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", block))


def luminance(hex_colour: str) -> float:
    c = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


DAY = tokens(":root")
NIGHT = DAY | tokens(':root[data-theme="dark"]')


@pytest.mark.parametrize("theme", [DAY, NIGHT], ids=["day", "night"])
def test_text_pairs_pass_aa(theme):
    low = {f"{t} on {b}": round(ratio(theme[t], theme[b]), 2) for t, b in PAIRS if ratio(theme[t], theme[b]) < 4.5}
    assert not low
