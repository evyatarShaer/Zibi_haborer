"""Draws the judge fly (DECISIONS 2026-10-29): an original cartoon fruit fly in a judge's wig
and robe, one SVG per pose in web/img/fly/. Each file stands alone (its own CSS idle
animation, off under prefers-reduced-motion), so the owner can replace any of them with
their own art without code changes. Run: python3 scripts/make_fly.py"""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "web" / "img" / "fly"
AMBER, AMBER_D, EYE, EYE_D = "#e0a94a", "#6b4416", "#c62828", "#6b1414"
WIG, WIG_D, ROBE, ROBE_D, LEG = "#f6f1e6", "#a89c86", "#2f2638", "#120d18", "#3b2a1a"
STEM = 'stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" fill="none"'


def line(pts, c=LEG, w=4.5):
    return f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" {STEM.format(c=c, w=w)}/>'


def leg(pts):
    """A fly leg out of a robe sleeve: a dark jointed line, a sleeve cuff, a foot."""
    (sx, sy), (fx, fy) = pts[0], pts[-1]
    return (f'<circle cx="{sx}" cy="{sy}" r="7" fill="{ROBE}" stroke="{ROBE_D}" stroke-width="2"/>'
            + line(pts) + f'<circle cx="{fx}" cy="{fy}" r="3.5" fill="{LEG}"/>')


def mirror(pts):
    return [(240 - x, y) for x, y in pts]


def wings():
    w = (f'<ellipse cx="{{x}}" cy="138" rx="26" ry="52" transform="rotate({{r}} {{x}} 138)" '
         f'fill="#dceaf3" fill-opacity=".9" stroke="#8fa6b8" stroke-width="2.5"/>')
    veins = line([(84, 120), (60, 160)], "#8fa6b8", 1.5) + line([(156, 120), (180, 160)], "#8fa6b8", 1.5)
    return w.format(x=66, r=-28) + w.format(x=174, r=28) + veins


def robe():
    return (f'<path d="M80 110 Q120 100 160 110 L180 214 Q120 226 60 214 Z" fill="{ROBE}" '
            f'stroke="{ROBE_D}" stroke-width="3"/>'
            '<path d="M120 108 L120 214" stroke="#463a52" stroke-width="2"/>'
            f'<rect x="111" y="110" width="8" height="24" rx="2" fill="#fff" stroke="{WIG_D}" stroke-width="1.5"/>'
            f'<rect x="121" y="110" width="8" height="24" rx="2" fill="#fff" stroke="{WIG_D}" stroke-width="1.5"/>')


def eye(cx, kind):
    base = f'<ellipse cx="{cx}" cy="80" rx="17" ry="21" fill="{EYE}" stroke="{EYE_D}" stroke-width="2.5"/>'
    if kind == "closed":
        return base + (f'<path d="M{cx - 17} 80 A17 21 0 0 1 {cx + 17} 80 Z" fill="{AMBER}" stroke="{AMBER_D}" '
                       f'stroke-width="2.5"/>' + line([(cx - 14, 82), (cx, 88), (cx + 14, 82)], AMBER_D, 3))
    if kind == "happy":  # wide and sparkling: a big shine and a second glint
        return base + (f'<circle cx="{cx - 5}" cy="72" r="7" fill="#fff" fill-opacity=".95"/>'
                       f'<circle cx="{cx + 6}" cy="88" r="3.5" fill="#fff" fill-opacity=".9"/>'
                       f'<circle cx="{cx + 8}" cy="70" r="2" fill="#fff"/>')
    if kind == "x":
        return base + line([(cx - 8, 72), (cx + 8, 88)], "#fff", 3.5) + line([(cx + 8, 72), (cx - 8, 88)], "#fff", 3.5)
    shine = f'<circle cx="{cx - 6}" cy="71" r="4.5" fill="#fff" fill-opacity=".85"/>'
    if kind == "wide":
        return base + shine + f'<circle cx="{cx + 5}" cy="88" r="2.5" fill="#fff" fill-opacity=".6"/>'
    return base + shine


MOUTHS = {"smile": "M110 99 Q120 106 130 99", "flat": "M111 101 L129 101",
          "o": "M116 101 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0", "wavy": "M108 101 l4 -3 l4 3 l4 -3 l4 3 l4 -3 l4 3",
          "frown": "M110 104 Q120 97 130 104", "open": "M106 96 Q120 118 134 96 Z"}


def head(eyes="open", mouth="smile", extra=""):
    rolls = "".join(f'<circle cx="{x}" cy="{y}" r="10.5" fill="{WIG}" stroke="{WIG_D}" stroke-width="2"/>'
                    for x in (58, 182) for y in (64, 82, 100, 118))
    curls = "".join(f'<circle cx="{x}" cy="{48 - (6 if 96 < x < 146 else 0)}" r="11" fill="{WIG}" '
                    f'stroke="{WIG_D}" stroke-width="2"/>' for x in range(78, 163, 14))
    antennae = (line([(110, 40), (100, 18)], AMBER_D, 3) + line([(130, 40), (140, 18)], AMBER_D, 3)
                + line([(103, 25), (95, 24)], AMBER_D, 1.5) + line([(137, 25), (145, 24)], AMBER_D, 1.5))
    return (rolls + antennae
            + f'<circle cx="120" cy="80" r="38" fill="{AMBER}" stroke="{AMBER_D}" stroke-width="3"/>'
            + eye(86, eyes) + eye(154, eyes) + extra
            + f'<path d="{MOUTHS[mouth]}" {STEM.format(c=AMBER_D, w=3)}/>' + curls)


def bench():
    return ('<rect x="26" y="166" width="188" height="64" rx="6" fill="#6b4428" stroke="#3e2716" stroke-width="3"/>'
            '<rect x="20" y="160" width="200" height="12" rx="4" fill="#8a5a34" stroke="#3e2716" stroke-width="3"/>'
            '<rect x="100" y="188" width="40" height="16" rx="3" fill="#c99a2e" stroke="#7a5b14" stroke-width="2"/>')


FOLDED = [leg([(84, 128), (92, 156), (114, 164)]), leg(mirror([(84, 128), (92, 156), (114, 164)]))]
REST = [leg([(74, 144), (58, 160), (46, 164)]), leg(mirror([(74, 144), (58, 160), (46, 164)]))]
PROBOSCIS = (line([(120, 104), (120, 138)], AMBER_D, 9) + line([(120, 104), (120, 138)], "#d99a3c", 5)
             + f'<ellipse cx="120" cy="142" rx="10" ry="5" fill="#d99a3c" stroke="{AMBER_D}" stroke-width="2"/>')


def seated():
    return wings() + robe() + head() + bench() + "".join(REST + FOLDED), \
        "#lids{animation:blink 5s infinite}@keyframes blink{0%,94%,100%{opacity:0}96%{opacity:1}}", \
        '<g id="lids">' + eye(86, "closed") + eye(154, "closed") + "</g>"


def tasting():
    drop = '<path d="M120 150 q-12 10 0 16 q12 -6 0 -16Z" fill="#7fc4ef" stroke="#3a7fae" stroke-width="2"/>'
    return (wings() + robe() + bench() + "".join(REST) + leg([(84, 128), (96, 154), (108, 162)])
            + leg(mirror([(84, 128), (96, 154), (108, 162)])) + head("open", "o") + drop
            + f'<g id="p">{PROBOSCIS}</g>'), "#p{animation:dip 1.6s ease-in-out infinite}" \
        "@keyframes dip{0%,100%{transform:translateY(0)}50%{transform:translateY(5px)}}", ""


def deliberating():
    a = leg([(84, 128), (100, 152), (117, 146)])
    b = leg(mirror([(84, 128), (100, 152), (117, 146)]))
    return (wings() + robe() + head("open", "flat") + bench() + "".join(REST)
            + f'<g id="ra">{a}</g><g id="rb">{b}</g>'), \
        "#ra{animation:rub .5s ease-in-out infinite alternate}#rb{animation:rub .5s ease-in-out infinite " \
        "alternate-reverse}@keyframes rub{from{transform:translate(-3px,1px)}to{transform:translate(3px,-1px)}}", ""


def gavel():
    hammer = (leg([(156, 128), (178, 106), (186, 84)])
              + '<rect x="181" y="56" width="10" height="34" rx="3" fill="#8a5a34" stroke="#3e2716" stroke-width="2" '
              'transform="rotate(30 186 84)"/><rect x="168" y="42" width="40" height="18" rx="4" fill="#6b4428" '
              'stroke="#3e2716" stroke-width="2.5" transform="rotate(30 186 84)"/>')
    block = '<rect x="168" y="150" width="34" height="12" rx="3" fill="#8a5a34" stroke="#3e2716" stroke-width="2.5"/>'
    return (wings() + robe() + head("open", "smile") + bench() + block + "".join(REST)
            + leg([(84, 128), (92, 156), (114, 164)]) + f'<g id="g">{hammer}</g>'), \
        "#g{transform-origin:156px 128px;animation:bang 2.4s ease-in infinite}@keyframes bang{0%,70%,100%" \
        "{transform:rotate(0)}80%{transform:rotate(-14deg)}88%{transform:rotate(18deg)}}", ""


def shrug():
    up = [(84, 126), (40, 120), (28, 98)]
    hands = leg(up) + leg(mirror(up)) + "".join(
        line([(x, 98), (x + d, 89)], LEG, 3) for x, d in ((28, -6), (28, 6), (212, -6), (212, 6)))
    return (wings() + robe() + bench() + "".join(REST) + f'<g id="s">{head("open", "wavy")}{hands}</g>'), \
        "#s{animation:shrug 2.2s ease-in-out infinite}@keyframes shrug{0%,60%,100%{transform:translateY(0)}" \
        "75%{transform:translateY(-5px)}}", ""


def frozen():
    ice = "".join(f'<path d="M{x} {y} l5 {h} l5 -{h}Z" fill="#cfeaff" stroke="#6fa8d6" stroke-width="1.5"/>'
                  for x, y, h in ((40, 172, 14), (70, 172, 20), (150, 172, 16), (190, 172, 12), (88, 56, 12), (140, 56, 10)))
    frost = ('<filter id="ice"><feColorMatrix type="matrix" values=".55 .15 .15 0 .08 .12 .6 .2 0 .16 '
             '.15 .25 .7 0 .3 0 0 0 1 0"/></filter>')  # tints only the fly, not the square around it
    flakes = "".join(f'<path d="M{x - 6} {y} h12 M{x} {y - 6} v12 M{x - 4} {y - 4} l8 8 M{x + 4} {y - 4} l-8 8" '
                     f'stroke="#6fa8d6" stroke-width="2" stroke-linecap="round"/>' for x, y in ((24, 40), (214, 30), (206, 140)))
    return (frost + f'<g id="f" filter="url(#ice)">{wings()}{robe()}{head("wide", "wavy")}{bench()}'
            f'{"".join(REST + FOLDED)}</g>' + ice + flakes), "#f{animation:shiver 3s linear infinite}@keyframes shiver{0%,80%,100%" \
        "{transform:translateX(0)}82%,86%,90%{transform:translateX(-1.5px)}84%,88%{transform:translateX(1.5px)}}", ""


def eating():
    """Lunch break: a big slice held up to an open grin, happy eyes. Reads apart from
    deliberating (flat mouth, rubbing legs) even at header size."""
    grin = (f'<path d="{MOUTHS["open"]}" fill="#6b1414"/>'
            '<path d="M113 106 Q120 101 127 106 Q120 112 113 106 Z" fill="#e57373"/>')
    blush = "".join(f'<ellipse cx="{x}" cy="104" rx="7" ry="4" fill="#e57373" fill-opacity=".55"/>' for x in (92, 148))
    pizza = ('<path d="M144 110 L200 46 L231 96 Z" fill="#f6cf5a" stroke="#b5761f" stroke-width="3" stroke-linejoin="round"/>'
             '<path d="M200 46 L231 96" stroke="#c98a3a" stroke-width="11" stroke-linecap="round"/>'
             + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#c62828" stroke="#7a1616" stroke-width="1.5"/>'
                       for x, y, r in ((197, 73, 7), (210, 90, 6), (177, 92, 5.5)))
             + '<path d="M164 99 q2 9 -2 12" stroke="#f6cf5a" stroke-width="4" stroke-linecap="round" fill="none"/>')
    napkin = '<path d="M98 112 L142 112 L120 148 Z" fill="#fff" stroke="#a89c86" stroke-width="2"/>'
    return (wings() + robe() + napkin + head("happy", "open", blush + grin) + bench() + "".join(REST)
            + leg([(84, 128), (92, 156), (114, 164)])
            + f'<g id="z">{leg([(156, 128), (196, 118), (206, 96)])}{pizza}</g>'), \
        "#z{animation:chew 1.2s ease-in-out infinite}@keyframes chew{0%,100%{transform:translate(0,0)}" \
        "50%{transform:translate(-5px,3px)}}", ""


def fainted():
    body = wings() + robe() + head("x", "o") + "".join(REST + FOLDED)
    stars = "".join(f'<path d="M{x} {y} l3 7 7 1 -5 5 1 7 -6 -3 -6 3 1 -7 -5 -5 7 -1Z" fill="#f2c14e" '
                    f'stroke="#b5761f" stroke-width="1.5"/>' for x, y in ((0, -26), (24, 10), (-24, 10)))
    return ('<rect x="10" y="214" width="220" height="8" rx="4" fill="#8a5a34"/>'
            f'<g transform="translate(124 150) rotate(-90) scale(.8) translate(-120 -130)">{body}</g>'
            f'<g transform="translate(52 76)"><g id="st">{stars}</g></g>'), \
        "#st{animation:spin 3s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}", ""


def asleep():
    zs = "".join(f'<text class="zz" x="{x}" y="{y}" font-family="sans-serif" font-weight="800" font-size="{s}" '
                 f'fill="#6b7fa8" style="animation-delay:{d}s">Z</text>' for x, y, s, d in
                 ((176, 52, 16, 0), (190, 34, 20, 1), (206, 14, 24, 2)))
    return (wings() + robe() + bench() + "".join(REST + FOLDED)
            + f'<g transform="rotate(12 120 110)">{head("closed", "flat")}</g>' + zs), \
        ".zz{opacity:0;animation:float 3s ease-in-out infinite}@keyframes float{0%{opacity:0;transform:" \
        "translateY(6px)}40%{opacity:1}100%{opacity:0;transform:translateY(-8px)}}", ""


POSES = {"seated": seated, "tasting": tasting, "deliberating": deliberating, "gavel": gavel, "shrug": shrug,
         "frozen": frozen, "eating": eating, "fainted": fainted, "asleep": asleep}
CALM = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def svg(name):
    art, css, over = POSES[name]()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240">\n'
            f'<title>judge fly: {name}</title>\n<style>*{{transform-box:view-box}}{css}{CALM}</style>\n'
            f'{art}{over}\n</svg>\n')


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name in POSES:
        (OUT / f"{name}.svg").write_text(svg(name))
