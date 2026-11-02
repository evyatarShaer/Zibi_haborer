"""The review gallery's other half (used by ui_screens.py): every fly pose, one preview image
of each kind fetched from the app's real /og/ routes, and README.md, which lays the
day and night screenshots side by side for review on GitHub."""
import shutil
import urllib.request
from pathlib import Path

from borer_api import og

ROOT = Path(__file__).resolve().parents[1]
POSES = ["seated", "tasting", "deliberating", "gavel", "shrug", "frozen", "eating", "fainted", "asleep"]
POSE_USE = {"seated": "home, A waiting, B's form, queue, the judge enters", "tasting": "tasting A / B",
            "deliberating": "deliberating, meter reveal", "gavel": "win, dithered", "shrug": "tie",
            "frozen": "froze", "eating": "lunch break", "fainted": "error", "asleep": "closed case"}


def poses(out: Path) -> None:
    """The SVGs as served, plus the PNGs the preview images paste."""
    (out / "fly").mkdir(parents=True, exist_ok=True)
    for p in POSES:
        shutil.copy(ROOT / "web" / "img" / "fly" / f"{p}.svg", out / "fly" / f"{p}.svg")
        shutil.copy(ROOT / "api" / "assets" / "fly" / f"{p}.png", out / "fly" / f"{p}.png")


def previews(store, base: str, out: Path) -> list[tuple[str, str]]:
    """One image per kind: the site, teasers with and without a topic, and the public card
    for each verdict kind; returns [(file, what it is)]."""
    (out / "og").mkdir(parents=True, exist_ok=True)
    got = {"site": ("/og/site.png", "start page, /how, A's link, closed case")}
    for row in store._all('SELECT id FROM "case" ORDER BY created_at'):
        c, hs = store.snapshot(row["id"])
        meta = og.card(c, hs)
        topic = "topic" if c["topic"] else "no-topic"
        got.setdefault(f"teaser-{topic}", (f"/og/t/{c['id']}.png", f"B's link ({topic.replace('-', ' ')})"))
        kind = ("error" if c["status"] == "error" else "no-show" if c["status"] == "no_show"
                else "not-decided" if meta["pose"] == "seated" else hs[-1]["outcome"])
        got.setdefault(f"card-{kind}", (meta["image"].split("?")[0], f"public card: {kind} ({meta['pose']})"))
    rows = []
    for name, (path, what) in sorted(got.items()):
        (out / "og" / f"{name}.png").write_bytes(urllib.request.urlopen(base + path, timeout=30).read())
        rows.append((f"og/{name}.png", what))
    return rows


def readme(out: Path, og_rows: list[tuple[str, str]]) -> None:
    shots = sorted(p.stem for p in (out / "light").glob("*.png"))
    lines = ["# UI refresh: screenshots", "",
             "Headless Chrome at 360 px (2× pixels), reduced motion (still frames), day court on the",
             "left, night court on the right. Made by `scripts/ui_screens.py` (see DECISIONS 2026-10-29).", "",
             "## Screens", "", "| Screen | Day | Night |", "|---|---|---|"]
    lines += [f"| `{s}` | <img src=\"light/{s}.png\" width=\"260\"> | <img src=\"dark/{s}.png\" width=\"260\"> |"
              for s in shots]
    lines += ["", "## Judge fly poses", "", "Each is one file in `web/img/fly/` (replace it with your own art,",
              "same name). The PNGs are what the preview images paste.", "", "| Pose | Used for | SVG | PNG |",
              "|---|---|---|---|"]
    lines += [f"| {p} | {POSE_USE[p]} | <img src=\"fly/{p}.svg\" width=\"120\"> | <img src=\"fly/{p}.png\" width=\"120\"> |"
              for p in POSES]
    lines += ["", "## Link-preview images (1200 × 630)", ""]
    for path, what in og_rows:
        lines += [f"**{what}**", "", f"<img src=\"{path}\" width=\"600\">", ""]
    (out / "README.md").write_text("\n".join(lines) + "\n")
