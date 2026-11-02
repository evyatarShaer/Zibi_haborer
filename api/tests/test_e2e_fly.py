"""The preview images' fly PNGs (api/assets/fly) are the current SVG poses (web/img/fly):
re-rendered in headless Chrome, each must match its committed PNG. After changing a pose,
run scripts/render_fly.py. Run: uv run pytest -m chrome."""
import sys

from PIL import Image, ImageChops, ImageStat

from e2ekit import pytestmark  # noqa: F401 - chrome only
from fake import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import render_fly  # noqa: E402


def test_fly_pngs_match_the_svgs(tmp_path):
    render_fly.main(tmp_path)
    svgs = sorted(p.stem for p in render_fly.SRC.glob("*.svg"))
    assert svgs == sorted(p.stem for p in render_fly.OUT.glob("*.png"))
    for pose in svgs:
        got, want = (Image.open(d / f"{pose}.png").convert("RGBA") for d in (tmp_path, render_fly.OUT))
        assert got.size == want.size
        assert max(ImageStat.Stat(ImageChops.difference(got, want)).mean) < 1.0, pose  # antialiasing only
