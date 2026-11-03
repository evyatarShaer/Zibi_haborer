"""Screenshots of every screen and outcome at 360 px, day and night court, for review
(docs/screenshots/ui-refresh/). Reuses the page tests' rig: the real app on a temp DB
with a scripted simulation, headless Chrome with reduced motion (still frames).
    cd api && uv run python ../scripts/ui_screens.py [out_dir]"""
import base64
import io
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["BORER_SECRET"] = os.path.join(tempfile.mkdtemp(), "secret.key")
sys.path[:0] = [str(ROOT / "api" / "tests"), str(ROOT / "api" / "src"), str(ROOT / "sim" / "src"),
                str(ROOT / "scripts")]
import uvicorn  # noqa: E402
from PIL import Image  # noqa: E402

from borer_api.app import create_app  # noqa: E402
from cdp import Browser, Page  # noqa: E402
from e2ekit import BASE, ENTERS, HEADLINE, PORT, Script, Shift, link_in, open_case  # noqa: E402
from ui_gallery import poses, previews, readme  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "screenshots" / "ui-refresh"
TEXT_B = "אננס על פיצה זה פשע נגד האנושות"


def device(browser, theme: str) -> Page:
    p = browser.page()
    p.b.send("Emulation.setEmulatedMedia", p.s, features=[
        {"name": "prefers-color-scheme", "value": theme}, {"name": "prefers-reduced-motion", "value": "reduce"}])
    return p


def shot(p: Page, name: str, theme: str) -> None:
    p.js("document.fonts.ready.then(() => true)")
    p.js("window.scrollTo({top: 0, behavior: 'instant'})")  # the sticky header stays on top
    time.sleep(0.5)
    assert "[object " not in p.text(), (name, p.text()[:300])
    h = p.js("Math.max(document.documentElement.scrollHeight, window.innerHeight)")
    r = p.b.send("Page.captureScreenshot", p.s, format="png", captureBeyondViewport=True,
                 clip={"x": 0, "y": 0, "width": 360, "height": h, "scale": 1})
    im = Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB")
    (OUT / theme).mkdir(parents=True, exist_ok=True)
    im.quantize(256, method=Image.Quantize.MEDIANCUT).save(OUT / theme / f"{name}.png", optimize=True)
    print(theme, name, flush=True)


def submit_b(b: Page, link_b: str) -> None:
    b.goto(link_b)
    b.wait("!!document.querySelector('[name=text_b]')")
    b.fill("text_b", TEXT_B)
    b.click("form button[type=submit]")


def flows(sim, clock, browser, theme: str) -> None:
    S = lambda p, n: shot(p, n, theme)  # noqa: E731
    p = device(browser, theme)
    p.goto(BASE + "/")
    S(p, "01-home")
    for name, call in (("02-toast", "import('/js/toast.js').then((m) => m.toast('הערעור הוגש', 'ok', 60000))"),
                       ("03-skeleton", "import('/js/notice.js').then((m) => m.loadingScreen(document.getElementById('app')))")):
        p.js(f"{call}.then(() => true)")
        time.sleep(0.4)
        S(p, name)
    p.goto(BASE + "/how")
    S(p, "04-how")
    for url, name in ((BASE + "/a/nope", "40-notice-closed"),):
        p.goto(url)
        p.wait_text("התיק נסגר")
        S(p, name)

    # The main case: A waits, B writes, the live story stage by stage, the verdict, the brain.
    a, b = device(browser, theme), device(browser, theme)
    url_a, link_b = open_case(a)
    S(a, "10-a-waiting")
    b.goto(link_b)
    b.wait("!!document.querySelector('[name=text_b]')")
    S(b, "11-b-form")
    sim.script = [("win", "A")]
    sim.gate.clear()  # held until the story reaches deliberation, so B sees the live reveal
    submit_b(b, link_b)
    for text, name in ((ENTERS, "20-story-judge-enters"), ("טועם את הטענה של דנה", "21-story-tasting"),
                       ("משפשף את הרגליים", "22-story-deliberating"), ("כמה הזבוב רצה", "23-story-reveal")):
        try:  # a stage lasts ~2 s; a slow screenshot can miss the next one
            b.wait_text(text, 25 if name.startswith("20") else 4)
            S(b, name)
        except AssertionError:
            print(theme, name, "missed", flush=True)
        if name.startswith("22"):
            sim.gate.set()
    b.wait_text(HEADLINE[("win", "A")], 25)
    S(b, "30-verdict-win")
    b.click("button.brain-toggle")
    b.wait("document.querySelectorAll('.lab polyline').length === 2")
    S(b, "31-brain-view")
    c = device(browser, theme)
    c.goto(link_in(b.attr("a.share", "href"), "c"))
    c.wait_text(HEADLINE[("win", "A")])
    S(c, "38-public-card")
    a.goto(link_b)
    a.wait_text("זה הקישור של הצד השני")
    S(a, "41-notice-own-link")
    c.goto(link_b)
    c.wait_text("התיק כבר בטיפול")
    S(c, "42-notice-taken")
    sim.script = [("win", "B")]
    b.goto(link_b)
    b.wait_text(HEADLINE[("win", "A")], 25)
    b.click("button.appeal")
    b.wait_text("הערעור של יוסי התקבל!", 25)
    S(b, "37-verdict-appeal-accepted")

    for outcome, name in (((("dithered", "B")), "32-verdict-dithered"), (("tie", None), "33-verdict-tie"),
                          (("froze", None), "34-verdict-froze"), (("food", None), "35-verdict-lunch")):
        a, b = device(browser, theme), device(browser, theme)
        _, link_b = open_case(a)
        sim.script = [outcome]
        submit_b(b, link_b)
        b.wait_text(HEADLINE[outcome], 30)
        S(b, name)

    a = device(browser, theme)
    open_case(a)
    sim.script = [("win", "B")] * 3  # any other open case expires too
    clock.offset += 3 * 3600
    a.wait_text("הזבוב העדיף מים", 40)
    clock.offset = 0
    S(a, "36-verdict-no-show-water")

    a, b = device(browser, theme), device(browser, theme)
    _, link_b = open_case(a)
    sim.script = ["raise"] * 3
    submit_b(b, link_b)
    b.wait_text("השופט התעלף", 30)
    S(b, "43-notice-error")


def main() -> None:
    sim, clock = Script(), Shift()
    app = create_app(sim, os.path.join(tempfile.mkdtemp(), "c.sqlite3"), sweep_every_s=0.2, clock=clock)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    browser = Browser()
    try:
        for theme in sys.argv[2:] or ("light", "dark"):
            flows(sim, clock, browser, theme)
        open_case(device(browser, "light"), topic=None)  # left open: no-topic teaser, "not decided" card
        poses(OUT)
        readme(OUT, previews(app.state.store, BASE, OUT))
    finally:
        browser.close()
        server.should_exit = True
    errors = [e["exception"]["description"] for e in browser.errors]
    assert not errors, errors[:3]


if __name__ == "__main__":
    main()
