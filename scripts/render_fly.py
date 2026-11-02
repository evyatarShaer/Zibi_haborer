"""Renders the judge-fly poses (web/img/fly/*.svg) to transparent PNGs for the preview
images (api/assets/fly/, pasted by borer_api.ogimage), in headless Chrome with reduced
motion so each is its still frame. Re-run after changing a pose's art:
    cd api && uv run python ../scripts/render_fly.py"""
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api" / "tests"))
from cdp import Browser  # noqa: E402

SRC, OUT, PX = ROOT / "web" / "img" / "fly", ROOT / "api" / "assets" / "fly", 480


def shoot(page, svg: Path) -> bytes:
    data = base64.b64encode(svg.read_bytes()).decode()
    html = (f"<body style='margin:0;background:transparent'><img src='data:image/svg+xml;base64,{data}' "
            f"width='{PX}' height='{PX}' style='display:block'></body>")
    page.goto("data:text/html;base64," + base64.b64encode(html.encode()).decode())
    page.wait("document.images[0] && document.images[0].complete")
    shot = page.b.send("Page.captureScreenshot", page.s, format="png",
                       clip={"x": 0, "y": 0, "width": PX, "height": PX, "scale": 1})
    return base64.b64decode(shot["data"])


def main(out: Path = OUT) -> None:
    browser = Browser(port=9334)
    try:
        page = browser.page()
        page.b.send("Emulation.setDeviceMetricsOverride", page.s, width=PX, height=PX,
                    deviceScaleFactor=1, mobile=False)
        page.b.send("Emulation.setDefaultBackgroundColorOverride", page.s, color={"r": 0, "g": 0, "b": 0, "a": 0})
        page.b.send("Emulation.setEmulatedMedia", page.s,
                    features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
        out.mkdir(parents=True, exist_ok=True)
        for svg in sorted(SRC.glob("*.svg")):
            (out / f"{svg.stem}.png").write_bytes(shoot(page, svg))
    finally:
        browser.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
