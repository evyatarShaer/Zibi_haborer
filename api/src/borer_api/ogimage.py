"""Link-preview images (SPEC §9): 1200×630 PNGs drawn with Pillow. Hebrew is laid out right
to left by libraqm (FriBiDi + HarfBuzz; on a server it needs the libfribidi0 package).
Font: Heebo (SIL OFL 1.1, assets/fonts). The courtroom look of the pages; the fly is a
placeholder drawing until the owner's art. Only the lines it is given are drawn, so what
an image can show is decided in og.py."""
import functools
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, features

W, H = 1200, 630
FONT = Path(__file__).resolve().parents[2] / "assets" / "fonts" / "Heebo[wght].ttf"
PAPER, WOOD, WOOD_DARK, GOLD = (251, 246, 236), (91, 58, 36), (62, 39, 22), (201, 154, 46)
INK, MUTED = (43, 33, 24), (122, 106, 88)
MARGIN, TEXT_W = 70, 760
FOOTER = "140 אלף נוירונים של מוח זבוב אמיתי. בלי AI."
STYLE = {  # role → (size px, weight, colour)
    "topic": (40, "Medium", MUTED), "names": (44, "Bold", INK), "headline": (66, "ExtraBold", INK),
    "note": (40, "Medium", INK), "history": (34, "Regular", MUTED)}
RTL = {"direction": "rtl", "language": "he"} if features.check("raqm") else {}


@functools.cache
def font(size: int, weight: str) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONT), size, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_name(weight)
    return f


def wrap(text: str, f: ImageFont.FreeTypeFont, width: int) -> list[str]:
    """Greedy word wrap to `width` px (measured as laid out, right to left)."""
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and f.getlength(trial, **RTL) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line] if line else lines


def fly(d: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """The placeholder judge: a fly seen from above, with a gold gavel."""
    for dx in (-62, 62):
        d.ellipse((x + dx - 58, y - 70, x + dx + 58, y + 10), fill=(214, 228, 236), outline=MUTED, width=3)
    d.ellipse((x - 46, y - 40, x + 46, y + 120), fill=WOOD_DARK)
    d.ellipse((x - 40, y - 100, x + 40, y - 30), fill=WOOD)
    for dx in (-24, 24):
        d.ellipse((x + dx - 18, y - 96, x + dx + 18, y - 60), fill=(178, 34, 34))
    d.rectangle((x + 70, y + 110, x + 160, y + 132), fill=GOLD)
    d.rectangle((x + 106, y + 132, x + 124, y + 190), fill=GOLD)


def render(lines: list[tuple[str, str]]) -> Image.Image:
    """The card: the header band, the fly, and (role, text) lines right-aligned in RTL."""
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 110), fill=WOOD)
    d.rectangle((0, 110, W, 118), fill=GOLD)
    d.text((W - MARGIN, 55), "הבורר", font=font(58, "ExtraBold"), fill=(255, 255, 255), anchor="rm", **RTL)
    d.text((MARGIN, 55), "בית המשפט העליון לענייני זבובים", font=font(30, "Regular"),
           fill=(240, 230, 214), anchor="lm", **RTL)
    fly(d, 210, 330)
    y = 170
    for role, text in lines:
        size, weight, colour = STYLE[role]
        f = font(size, weight)
        for part in wrap(text, f, TEXT_W):
            d.text((W - MARGIN, y), part, font=f, fill=colour, anchor="ra", **RTL)
            y += round(size * 1.3)
        y += 14
    d.text((W - MARGIN, H - 40), FOOTER, font=font(28, "Regular"), fill=MUTED, anchor="rs", **RTL)
    return im


def png(lines: list[tuple[str, str]]) -> bytes:
    out = io.BytesIO()
    render(lines).save(out, "PNG", optimize=True)
    return out.getvalue()
