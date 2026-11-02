"""Link-preview images (SPEC §9): 1200×630 PNGs drawn with Pillow. Hebrew is laid out right
to left by libraqm (FriBiDi + HarfBuzz; on a server it needs the libfribidi0 package).
Font: Heebo (SIL OFL 1.1, assets/fonts). The courtroom look of the pages, with the judge
fly in a pose (assets/fly/{pose}.png, rendered from web/img/fly by scripts/render_fly.py).
Only the lines and pose it is given are drawn, so what an image can show is decided in og.py."""
import functools
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, features

W, H = 1200, 630
ASSETS = Path(__file__).resolve().parents[2] / "assets"
FONT, FLY = ASSETS / "fonts" / "Heebo[wght].ttf", ASSETS / "fly"
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


@functools.cache
def fly(pose: str) -> Image.Image:
    """The judge fly in `pose`, 360 px square, with its transparency."""
    return Image.open(FLY / f"{pose}.png").convert("RGBA").resize((360, 360), Image.LANCZOS)


def render(lines: list[tuple[str, str]], pose: str) -> Image.Image:
    """The card: the header band, the fly in `pose`, and (role, text) lines right-aligned in RTL."""
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 110), fill=WOOD)
    d.rectangle((0, 110, W, 118), fill=GOLD)
    d.text((W - MARGIN, 55), "הבורר", font=font(58, "ExtraBold"), fill=(255, 255, 255), anchor="rm", **RTL)
    d.text((MARGIN, 55), "בית המשפט העליון לענייני זבובים", font=font(30, "Regular"),
           fill=(240, 230, 214), anchor="lm", **RTL)
    im.paste(fly(pose), (10, 170), fly(pose))
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


def png(lines: list[tuple[str, str]], pose: str) -> bytes:
    out = io.BytesIO()
    render(lines, pose).save(out, "PNG", optimize=True)
    return out.getvalue()
