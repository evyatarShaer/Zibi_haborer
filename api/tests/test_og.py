"""Link previews (P2B-10): server-rendered tags for the teaser, the public card and the
rest; no argument anywhere; images 1200×630, Hebrew laid out right to left."""
import io
import re

import pytest
from PIL import Image, ImageChops, ImageFont

from apikit import decided, open_case
from borer_api import ogimage, verdicts
from fake import OK, TEXT_B, ROOT

GOLDEN = ROOT / "api" / "tests" / "golden" / "card.png"
CARD = [("topic", "התיק: פיצה עם אננס"), ("names", "דנה נגד יוסי"),
        ("headline", "אחרי התלבטות קשה... הצדק עם יוסי"), ("history", "פסק דין · ערעור התקבל")]
VERDICT_WORDS = [h.split("{name}")[0].strip() for h in verdicts.HEADLINES.values()] + [
    verdicts.NO_SHOW, verdicts.PREFERRED_WATER]


def tags(html: str) -> dict:
    return dict(re.findall(r'<meta (?:property|name)="([^"]+)" content="([^"]*)"', html))


def image(client, url: str) -> Image.Image:
    r = client.get("/" + url.split("://", 1)[1].split("/", 1)[1])
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    im = Image.open(io.BytesIO(r.content))
    assert im.size == (1200, 630) and len(r.content) < 300_000  # WhatsApp's size limit
    return im


def test_teaser_has_the_topic_and_no_verdict(client):
    case = open_case(client)
    _, a = decided(client, case)  # even after the verdict, B's link never spoils it
    page = client.get(case["link_b"]).text
    t = tags(page)
    assert "פיצה" in t["og:title"] and t["og:image"] == f"http://testserver/og/t/{case['case_id']}.png"
    assert not any(w in page for w in VERDICT_WORDS) and t["robots"] == "noindex"
    assert OK["text_a"] not in page and TEXT_B not in page and OK["name_a"] not in t["og:title"]
    image(client, t["og:image"])


def test_public_card_has_the_final_verdict_and_no_arguments(client):
    case = open_case(client)
    decided(client, case)
    page = client.get(f"/c/{case['case_id']}").text
    t = tags(page)
    assert t["og:title"] == "פסק הדין: הצדק עם דנה" and "דנה נגד יוסי" in t["og:description"]
    assert OK["text_a"] not in page and TEXT_B not in page
    image(client, t["og:image"])


def test_personal_closed_and_site_pages_show_nothing_of_the_case(client):
    case = open_case(client)
    decided(client, case)
    site = tags(client.get("/").text)
    assert site["og:title"] == "הבורר" and "robots" not in site
    client.app.state.store._run('UPDATE "case" SET hidden_at = 1')
    for path in (f"/a/{case['a']}", case["link_b"], f"/c/{case['case_id']}", "/c/nope", "/b/nope"):
        page = client.get(path).text
        assert tags(page)["og:title"] == "הבורר" and "פיצה" not in page and "דנה" not in page


def test_image_lines_never_hold_arguments(client):
    from borer_api import og
    case = open_case(client)
    decided(client, case)
    store = client.app.state.store
    c, hs = store.snapshot(case["case_id"])
    for meta in (og.teaser(c), og.card(c, hs), og.site()):
        text = " ".join(t for _, t in meta["lines"]) + meta["title"] + meta["text"]
        assert OK["text_a"] not in text and TEXT_B not in text


needs_raqm = pytest.mark.skipif(not ogimage.RTL, reason="Pillow without libraqm")


def _mask(f, text, **kw) -> Image.Image:
    m = f.getmask(text, **kw)
    return Image.frombytes("L", m.size, bytes(m))


def _distance(a: Image.Image, b: Image.Image) -> int:
    size = (max(a.width, b.width), max(a.height, b.height))
    pa, pb = Image.new("L", size), Image.new("L", size)
    pa.paste(a)
    pb.paste(b)
    return sum(ImageChops.difference(pa, pb).get_flattened_data())


@needs_raqm
@pytest.mark.parametrize("text", ["אבג", "שלום עולם"])
def test_hebrew_is_laid_out_right_to_left(text):
    """The card's layout looks like the characters drawn in reverse (right to left), not in
    typing order: Pillow's basic layout (no bidi) is the reference for both."""
    basic = ImageFont.truetype(str(ogimage.FONT), 80, layout_engine=ImageFont.Layout.BASIC)
    basic.set_variation_by_name("Bold")
    ours = _mask(ogimage.font(80, "Bold"), text, **ogimage.RTL)
    assert _distance(ours, _mask(basic, text[::-1])) * 5 < _distance(ours, _mask(basic, text))


@needs_raqm
def test_card_matches_the_golden_image():
    """Checked by eye on 2026-10-27: RTL lines, right-aligned, final letters (Pillow 13.0.0,
    raqm with FriBiDi 1.0.8 / HarfBuzz 14.5.0, Heebo). Regenerate only on purpose."""
    got = ogimage.render(CARD)
    assert ImageChops.difference(got, Image.open(GOLDEN).convert("RGB")).getbbox() is None
