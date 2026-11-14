"""Generates the menu illustrations (frontend/public/menu/<slug>.svg) and the 蛇記冰室 logo.

    uv run python tools/menu_art.py

Flat, hand-tuned SVG shapes: no stock photos, no licences to worry about, and they work offline.
Swap in real photos by dropping <slug>.jpg files in frontend/public/menu/ and changing `image` in shop/views.py.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "frontend" / "public"
W, H = 400, 300

GREEN, RED, CREAM, INK, MUSTARD = "#1d5c4a", "#c8202f", "#fbf5e9", "#2a2522", "#e8b13a"
TINTS = {"drink": "#f4e3c7", "toast": "#f6e6c3", "noodles": "#e3ede6", "rice": "#f3e1d6", "snack": "#efe6d0"}


def svg(body: str, tint: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  <radialGradient id="bg" cx="50%" cy="38%" r="70%"><stop offset="0" stop-color="#fffaf0"/><stop offset="1" stop-color="{tint}"/></radialGradient>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<ellipse cx="200" cy="258" rx="130" ry="16" fill="#000" opacity=".10" filter="url(#soft)"/>
{body}
</svg>
"""


# ---------------------------------------------------------------- drinks
def steam(x: float = 200, y: float = 92) -> str:
    paths = []
    for dx in (-26, 0, 26):
        cx = x + dx
        paths.append(f'<path d="M{cx} {y} c-10 -12 10 -20 0 -32 c-10 -12 10 -20 0 -30" fill="none" '
                     f'stroke="#fff" stroke-width="6" stroke-linecap="round" opacity=".75"/>')
    return "".join(paths)


def hot_cup(liquid: str, foam: str | None = None, lemon: bool = False) -> str:
    foam = foam or liquid
    slice_ = ('<ellipse cx="214" cy="137" rx="22" ry="7" fill="#f7d000" stroke="#e0a800" stroke-width="2"/>'
              '<ellipse cx="214" cy="137" rx="16" ry="4.5" fill="#fff36b"/>') if lemon else ""
    return f"""
{steam()}
<ellipse cx="200" cy="240" rx="118" ry="24" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
<ellipse cx="200" cy="236" rx="88" ry="14" fill="#f4efe4"/>
<path d="M262 160 c48 -6 52 54 4 58" fill="none" stroke="#fff" stroke-width="16" stroke-linecap="round"/>
<path d="M262 160 c48 -6 52 54 4 58" fill="none" stroke="#e3dccd" stroke-width="3" opacity=".6"/>
<path d="M128 136 L272 136 L256 222 Q200 244 144 222 Z" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
<path d="M138 186 L262 186 L259 200 Q200 214 141 200 Z" fill="{GREEN}"/>
<ellipse cx="200" cy="136" rx="72" ry="17" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
<ellipse cx="200" cy="138" rx="63" ry="12" fill="{liquid}"/>
<ellipse cx="190" cy="136" rx="34" ry="5" fill="{foam}" opacity=".55"/>
{slice_}
"""


def lemon_wheel(cx: float, cy: float, r: float = 26) -> str:
    seg = "".join(
        f'<path d="M{cx} {cy} L{cx + r * .78 * math.cos(a):.1f} {cy + r * .78 * math.sin(a):.1f} '
        f'A{r * .78} {r * .78} 0 0 1 {cx + r * .78 * math.cos(a + .9):.1f} {cy + r * .78 * math.sin(a + .9):.1f} Z" '
        f'fill="#fff36b" opacity=".9"/>'
        for a in [i * 2 * math.pi / 7 for i in range(7)])
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#f7d000" stroke="#e0a800" stroke-width="3"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * .84:.1f}" fill="#fffbe0"/>{seg}')


def iced_glass(liquid: str, *, lemon: bool = False, bubbles: bool = False, layers: list[tuple[str, float]] | None = None,
               top: str | None = None) -> str:
    rnd = random.Random(liquid)
    fill = (f'<rect x="140" y="96" width="120" height="160" fill="{liquid}"/>' if not layers else
            "".join(f'<rect x="140" y="{y}" width="120" height="{260 - y}" fill="{c}"/>' for c, y in layers))
    ice = "".join(
        f'<rect x="{x}" y="{y}" width="34" height="30" rx="7" fill="#fff" opacity=".42" '
        f'transform="rotate({rnd.randint(-18, 18)} {x + 17} {y + 15})"/>'
        for x, y in [(156, 104), (200, 112), (170, 140), (214, 150), (160, 178)])
    fizz = "".join(f'<circle cx="{rnd.randint(158, 242)}" cy="{rnd.randint(110, 240)}" r="{rnd.randint(2, 4)}" '
                   f'fill="#fff" opacity=".7"/>' for _ in range(16)) if bubbles else ""
    return f"""
<defs><clipPath id="glass"><path d="M146 70 L254 70 L240 250 Q200 262 160 250 Z"/></clipPath></defs>
<g clip-path="url(#glass)">{fill}{f'<rect x="140" y="96" width="120" height="14" fill="{top}"/>' if top else ''}{ice}{fizz}</g>
<path d="M232 34 L214 150" stroke="{RED}" stroke-width="11" stroke-linecap="round"/>
<path d="M232 34 L214 150" stroke="#fff" stroke-width="11" stroke-linecap="round" stroke-dasharray="10 12"/>
<path d="M146 70 L254 70 L240 250 Q200 262 160 250 Z" fill="#fff" fill-opacity=".14" stroke="#fff" stroke-width="5" stroke-linejoin="round"/>
<path d="M160 86 L152 230" stroke="#fff" stroke-width="6" stroke-linecap="round" opacity=".55"/>
{lemon_wheel(150, 82) if lemon else ''}
"""


# ---------------------------------------------------------------- toast & buns
def pineapple_bun() -> str:
    cracks = "".join(f'<path d="M{x} {y} l18 10 l-4 18 l-18 -6 Z" fill="#c9852a" opacity=".55"/>'
                     for x, y in [(140, 120), (172, 106), (206, 104), (238, 116), (150, 152), (186, 140),
                                  (222, 142), (256, 150)])
    return f"""
<ellipse cx="200" cy="232" rx="112" ry="22" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
<path d="M104 210 Q100 100 200 92 Q300 100 296 210 Z" fill="#e7a63e"/>
<path d="M104 210 Q100 100 200 92 Q300 100 296 210 Z" fill="none" stroke="#b9731f" stroke-width="3"/>
{cracks}
<rect x="112" y="186" width="176" height="22" rx="4" fill="#fde98b" stroke="#e9c44c" stroke-width="2"/>
<path d="M108 210 Q200 230 292 210 L292 214 Q200 236 108 214 Z" fill="#f5d9a6"/>
"""


def french_toast() -> str:
    return f"""
<ellipse cx="200" cy="236" rx="120" ry="22" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
<rect x="118" y="150" width="164" height="70" rx="16" fill="#c97a22"/>
<rect x="124" y="156" width="152" height="58" rx="12" fill="#e9a442"/>
<rect x="128" y="104" width="150" height="62" rx="16" fill="#cf8227" transform="rotate(-4 200 135)"/>
<rect x="134" y="110" width="138" height="50" rx="12" fill="#f0b14d" transform="rotate(-4 200 135)"/>
<rect x="182" y="88" width="34" height="26" rx="4" fill="#fff3a6" stroke="#e8cf5a" stroke-width="2"/>
<path d="M150 124 Q200 112 252 122 Q246 160 252 214 Q240 220 238 200 Q236 160 226 136 Q200 132 176 140 Q170 178 160 204 Q150 210 152 190 Z"
      fill="#b4561a" opacity=".55"/>
"""


def condensed_milk_toast() -> str:
    drizzle = "M136 120 " + " ".join(f"L{136 + i * 16} {120 + (28 if i % 2 else 0)}" for i in range(1, 9))
    return f"""
<ellipse cx="200" cy="236" rx="118" ry="22" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
<rect x="122" y="96" width="156" height="128" rx="22" fill="#d59443"/>
<rect x="132" y="106" width="136" height="108" rx="16" fill="#f7e2b2"/>
<rect x="176" y="140" width="44" height="30" rx="5" fill="#fff3a6" stroke="#e8cf5a" stroke-width="2"/>
<path d="{drizzle}" fill="none" stroke="#fffdf4" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
"""


def sandwich() -> str:
    def tri(dx: float, flip: bool) -> str:
        a = "M{0} 214 L{1} 214 L{2} 100 Z".format(*(
            (dx + 150, dx, dx + 150) if flip else (dx, dx + 150, dx)))
        return f'<path d="{a}" fill="#fbf1dc" stroke="#d7a45c" stroke-width="8" stroke-linejoin="round"/>'
    return f"""
<ellipse cx="200" cy="236" rx="124" ry="22" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
{tri(98, False)}
<path d="M104 206 L238 206 L104 112 Z" fill="#f6c945" opacity=".9"/>
<path d="M104 196 L224 196 L104 128 Z" fill="#f08a8f" opacity=".85"/>
{tri(152, True)}
<path d="M296 206 L162 206 L296 112 Z" fill="#f6c945" opacity=".9"/>
<path d="M296 196 L176 196 L296 128 Z" fill="#f08a8f" opacity=".85"/>
"""


def egg_tart() -> str:
    flutes = "".join(f'<path d="M{150 + i * 12.5} 222 l6 -66" stroke="#b9732a" stroke-width="2" opacity=".5"/>'
                     for i in range(9))
    return f"""
<ellipse cx="200" cy="234" rx="100" ry="20" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
<path d="M118 150 L282 150 L258 224 Q200 236 142 224 Z" fill="#dc9b52"/>
{flutes}
<ellipse cx="200" cy="150" rx="82" ry="26" fill="#d58c3e"/>
<ellipse cx="200" cy="150" rx="70" ry="20" fill="#f8cb3c"/>
<ellipse cx="182" cy="144" rx="26" ry="6" fill="#fff6c0" opacity=".8"/>
<circle cx="226" cy="156" r="5" fill="#e3a21f" opacity=".7"/>
"""


# ---------------------------------------------------------------- noodles (in a bowl)
def bowl(broth: str, contents: str) -> str:
    rim = "".join(f'<path d="M{120 + i * 20} 156 q10 8 20 0" fill="none" stroke="#3a6fb0" stroke-width="3"/>'
                  for i in range(8))
    return f"""
<path d="M92 150 Q96 252 200 254 Q304 252 308 150 Z" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
{rim}
<rect x="170" y="240" width="60" height="14" rx="4" fill="#f1ece2"/>
<ellipse cx="200" cy="150" rx="108" ry="30" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
<ellipse cx="200" cy="152" rx="96" ry="23" fill="{broth}"/>
{contents}
"""


def wavy_noodles(color: str, n: int = 6, y0: int = 140) -> str:
    return "".join(f'<path d="M{128 + i * 6} {y0 + i * 3} q14 -10 28 0 t28 0 t28 0 t28 0 t28 0" fill="none" '
                   f'stroke="{color}" stroke-width="5" stroke-linecap="round"/>' for i in range(n))


def fried_egg(cx: float, cy: float, s: float = 1) -> str:
    return (f'<path d="M{cx - 34 * s} {cy} q-4 -24 22 -26 q20 -12 38 4 q22 4 12 24 q-6 18 -34 16 q-30 4 -38 -18 Z" '
            f'fill="#fffdf6" stroke="#efe6d0" stroke-width="2"/>'
            f'<circle cx="{cx + 4 * s}" cy="{cy - 6 * s}" r="{13 * s}" fill="#f6b21b"/>'
            f'<circle cx="{cx}" cy="{cy - 10 * s}" r="{4 * s}" fill="#fff" opacity=".6"/>')


def macaroni() -> str:
    rnd = random.Random(3)
    tubes = "".join(f'<rect x="{rnd.randint(130, 260)}" y="{rnd.randint(134, 162)}" width="18" height="9" rx="4.5" '
                    f'fill="#f7e9b9" stroke="#e1c983" stroke-width="1.5" transform="rotate({rnd.randint(-40, 40)} 200 150)"/>'
                    for _ in range(22))
    ham = "".join(f'<rect x="{x}" y="{y}" width="30" height="7" rx="3" fill="#f09aa0"/>'
                  for x, y in [(150, 140), (210, 150), (176, 160), (232, 138)])
    return bowl("#f3e3bd", tubes + ham + '<circle cx="250" cy="156" r="5" fill="#7fbf5a"/><circle cx="160" cy="158" r="5" fill="#7fbf5a"/>')


def spam_egg_noodles() -> str:
    spam = "".join(f'<rect x="{x}" y="{y}" width="40" height="24" rx="4" fill="#ee8d8f" stroke="#d76f72" stroke-width="2" '
                   f'transform="rotate({r} {x + 20} {y + 12})"/>' for x, y, r in [(134, 132, -12), (164, 146, 8)])
    return bowl("#f2d58c", wavy_noodles("#f4cf5d", 5) + spam + fried_egg(236, 150, .9))


def satay_beef_noodles() -> str:
    beef = "".join(f'<ellipse cx="{x}" cy="{y}" rx="24" ry="10" fill="#8b4a2b" transform="rotate({r} {x} {y})"/>'
                   for x, y, r in [(160, 146, -10), (196, 140, 12), (232, 150, -6), (180, 160, 4)])
    onion = "".join(f'<circle cx="{x}" cy="{y}" r="4" fill="#5aa64a"/>' for x, y in [(150, 138), (214, 162), (246, 140), (200, 150)])
    return bowl("#e08a33", wavy_noodles("#f1d27a", 4, 146) + beef + onion)


# ---------------------------------------------------------------- plates
def plate(contents: str, rx: float = 132, ry: float = 46) -> str:
    return (f'<ellipse cx="200" cy="200" rx="{rx}" ry="{ry}" fill="#fff" stroke="#e3dccd" stroke-width="3"/>'
            f'<ellipse cx="200" cy="200" rx="{rx - 20}" ry="{ry - 12}" fill="none" stroke="{GREEN}" stroke-width="2" opacity=".35"/>'
            f'{contents}')


def rice_mound(cx: float = 168, color: str = "#fffdf5") -> str:
    rnd = random.Random(int(cx))
    grains = "".join(f'<ellipse cx="{cx + rnd.randint(-46, 46)}" cy="{rnd.randint(158, 204)}" rx="4" ry="2" '
                     f'fill="#e8e0cc" transform="rotate({rnd.randint(0, 180)} {cx} 180)"/>' for _ in range(40))
    return f'<path d="M{cx - 64} 210 Q{cx - 58} 150 {cx} 146 Q{cx + 58} 150 {cx + 64} 210 Z" fill="{color}" stroke="#ece4cf" stroke-width="2"/>{grains}'


def beef_chow_fun() -> str:
    ribbons = "".join(f'<path d="M{110 + i * 8} {176 + (i % 3) * 8} q30 -18 60 0 t60 0 t50 -4" fill="none" '
                      f'stroke="#9a5a26" stroke-width="12" stroke-linecap="round" opacity=".9"/>' for i in range(5))
    sprouts = "".join(f'<path d="M{x} {y} q8 -6 16 2" stroke="#fffbe6" stroke-width="4" fill="none" stroke-linecap="round"/>'
                      for x, y in [(140, 170), (196, 164), (240, 182), (170, 196), (226, 204)])
    beef = "".join(f'<ellipse cx="{x}" cy="{y}" rx="18" ry="8" fill="#5c2f1a"/>' for x, y in [(160, 186), (214, 176), (250, 196)])
    return plate(ribbons + beef + sprouts + '<circle cx="186" cy="182" r="4" fill="#5aa64a"/><circle cx="232" cy="190" r="4" fill="#5aa64a"/>')


def baked_pork_chop_rice() -> str:
    cheese = "".join(f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r * .6:.0f}" fill="#fbe39a" opacity=".9"/>'
                     for x, y, r in [(150, 186, 20), (196, 174, 24), (246, 184, 20), (184, 204, 16), (230, 204, 16)])
    return f"""
<ellipse cx="200" cy="232" rx="138" ry="22" fill="#000" opacity=".06"/>
<rect x="72" y="124" width="256" height="112" rx="52" fill="#fff" stroke="#e3dccd" stroke-width="3"/>
<rect x="90" y="134" width="220" height="90" rx="42" fill="#d2402e"/>
<path d="M112 168 Q118 140 170 140 Q220 136 262 150 Q300 166 286 196 Q268 214 214 210 Q150 212 124 200 Q106 190 112 168 Z" fill="#a8582a"/>
<path d="M126 170 Q132 152 172 152 Q218 150 254 160" stroke="#c97a3c" stroke-width="5" fill="none" stroke-linecap="round"/>
<path d="M100 150 Q150 176 200 160 Q250 146 304 168 L304 214 L96 214 Z" fill="#d2402e" opacity=".85"/>
{cheese}
<path d="M110 150 Q120 136 140 140" stroke="#fff" stroke-width="5" fill="none" opacity=".5" stroke-linecap="round"/>
"""


def char_siu_egg_rice() -> str:
    siu = "".join(f'<rect x="{x}" y="{y}" width="46" height="18" rx="5" fill="#a8322a" stroke="#6e1712" stroke-width="3" '
                  f'transform="rotate({r} {x + 23} {y + 9})"/>' for x, y, r in [(196, 166, -14), (214, 184, -8), (226, 202, -2)])
    return plate(rice_mound(150) + siu + fried_egg(262, 186, .85))


def curry_beef_brisket_rice() -> str:
    chunks = "".join(f'<rect x="{x}" y="{y}" width="26" height="20" rx="6" fill="#7a3f1f"/>'
                     for x, y in [(222, 176), (252, 190), (234, 204), (268, 172)])
    return plate(rice_mound(152) + '<path d="M196 196 Q210 160 256 160 Q306 166 302 202 Q290 226 236 224 Q200 222 196 196 Z" '
                 'fill="#e2a21f"/>' + chunks + '<circle cx="216" cy="210" r="5" fill="#f4d36b"/><circle cx="288" cy="196" r="4" fill="#f4d36b"/>')


def hainan_chicken_rice() -> str:
    slices = "".join(f'<path d="M{x} {y} q22 -14 44 0 l-4 16 q-18 -8 -36 0 Z" fill="#fffaf0" stroke="#f1d79b" stroke-width="4"/>'
                     for x, y in [(206, 168), (216, 186), (226, 204)])
    return plate(rice_mound(150, "#fdf0c4") + slices +
                 '<ellipse cx="300" cy="156" rx="24" ry="10" fill="#fff" stroke="#e3dccd" stroke-width="2"/>'
                 '<ellipse cx="300" cy="156" rx="17" ry="6" fill="#9fca5a"/>'
                 '<circle cx="118" cy="214" r="12" fill="#8fc46a" stroke="#5e9a3e" stroke-width="2"/>')


# ---------------------------------------------------------------- snacks
def fish_balls() -> str:
    balls = "".join(f'<circle cx="{x}" cy="{y}" r="21" fill="#e9a23b" stroke="#c97b1c" stroke-width="3"/>'
                    f'<circle cx="{x - 6}" cy="{y - 7}" r="6" fill="#fff" opacity=".35"/>'
                    for x, y in [(150, 196), (180, 172), (210, 148), (240, 124), (270, 100)])
    return f"""
<path d="M118 224 L300 72" stroke="#c9a46a" stroke-width="7" stroke-linecap="round"/>
<path d="M126 222 Q120 236 134 240 L166 240 Q176 236 172 222 Z" fill="{RED}" opacity=".9"/>
{balls}
"""


def chicken_wings() -> str:
    wing = ('<path d="M{x} {y} q-10 -34 26 -40 q40 -6 56 20 q12 22 -10 34 q-20 10 -36 2 q-24 8 -36 -16 Z" '
            'fill="#d9892e" stroke="#a85d14" stroke-width="3" transform="rotate({r} {x} {y})"/>')
    return plate("".join(wing.format(x=x, y=y, r=r) for x, y, r in [(132, 206, -8), (196, 192, 6), (250, 214, -4)]) +
                 '<path d="M282 166 l40 6 l-22 26 Z" fill="#f7d000" stroke="#e0a800" stroke-width="3"/>')


ART = {
    "milk-tea": ("drink", lambda: hot_cup("#b98552", "#e9cfae")),
    "lemon-tea": ("drink", lambda: iced_glass("#c7802a", lemon=True)),
    "yuenyeung": ("drink", lambda: hot_cup("#8e5b37", "#c79c74")),
    "coffee": ("drink", lambda: hot_cup("#5b3a24", "#a77d5a")),
    "lemon-coke": ("drink", lambda: iced_glass("#3b1c12", lemon=True, bubbles=True)),
    "honey-lemon": ("drink", lambda: iced_glass("#e9b949", lemon=True)),
    "horlicks": ("drink", lambda: hot_cup("#d7b68a", "#f3e3c9")),
    "red-bean-ice": ("drink", lambda: iced_glass("#f3ead8", layers=[("#f6efe1", 96), ("#7d2b2b", 196)], top="#fffaf0")),
    "pineapple-bun-butter": ("toast", pineapple_bun),
    "french-toast": ("toast", french_toast),
    "condensed-milk-toast": ("toast", condensed_milk_toast),
    "ham-egg-sandwich": ("toast", sandwich),
    "egg-tart": ("toast", egg_tart),
    "macaroni-ham-soup": ("noodles", macaroni),
    "spam-egg-noodles": ("noodles", spam_egg_noodles),
    "satay-beef-noodles": ("noodles", satay_beef_noodles),
    "beef-chow-fun": ("noodles", beef_chow_fun),
    "baked-pork-chop-rice": ("rice", baked_pork_chop_rice),
    "char-siu-egg-rice": ("rice", char_siu_egg_rice),
    "curry-beef-brisket-rice": ("rice", curry_beef_brisket_rice),
    "hainan-chicken-rice": ("rice", hainan_chicken_rice),
    "curry-fish-balls": ("snack", fish_balls),
    "chicken-wings": ("snack", chicken_wings),
}


# ---------------------------------------------------------------- logo
LOGO = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240">
  <defs>
    <path id="arcTop" d="M20 120 A100 100 0 0 1 220 120"/>
    <path id="arcBottom" d="M10 120 A110 110 0 0 0 230 120"/>
  </defs>
  <circle cx="120" cy="120" r="118" fill="{RED}"/>
  <circle cx="120" cy="120" r="92" fill="#fff"/>
  <circle cx="120" cy="120" r="88" fill="{CREAM}"/>
  <text font-family="Futura, 'Avenir Next', 'Helvetica Neue', Arial, sans-serif" font-size="15" font-weight="700"
        letter-spacing="4" fill="#fff"><textPath href="#arcTop" startOffset="50%" text-anchor="middle">SNAKE KEE CAFÉ</textPath></text>
  <text font-family="Futura, 'Avenir Next', 'Helvetica Neue', Arial, sans-serif" font-size="11" font-weight="700"
        letter-spacing="3" fill="#fff"><textPath href="#arcBottom" startOffset="50%" text-anchor="middle">EST. 2026 · HONG KONG</textPath></text>
  <circle cx="22" cy="120" r="3" fill="#fff"/><circle cx="218" cy="120" r="3" fill="#fff"/>
  <g transform="translate(0 6)">
    <!-- steam -->
    <path d="M104 52 c-7 -8 7 -13 0 -21 M120 48 c-7 -8 7 -13 0 -21 M136 52 c-7 -8 7 -13 0 -21" fill="none"
          stroke="{GREEN}" stroke-width="4" stroke-linecap="round" opacity=".5"/>
    <!-- the snake is the cup's handle (Python blue & yellow) -->
    <path d="M156 78 c30 -6 36 40 4 44" fill="none" stroke="#3776ab" stroke-width="11" stroke-linecap="round"/>
    <path d="M156 78 c30 -6 36 40 4 44" fill="none" stroke="#ffd43b" stroke-width="3.5" stroke-linecap="round" stroke-dasharray="2 7"/>
    <!-- HK-style thick cup -->
    <path d="M76 68 L164 68 L154 122 Q120 135 86 122 Z" fill="#fff" stroke="#d9d0bf" stroke-width="2.5"/>
    <path d="M81 95 L159 95 L157 105 Q120 114 83 105 Z" fill="{GREEN}"/>
    <ellipse cx="120" cy="68" rx="44" ry="10" fill="#fff" stroke="#d9d0bf" stroke-width="2.5"/>
    <ellipse cx="120" cy="69" rx="38" ry="7" fill="#b98552"/>
    <!-- snake head peeking over the rim -->
    <ellipse cx="166" cy="62" rx="11" ry="8.5" fill="#3776ab"/>
    <circle cx="169" cy="59.5" r="2.4" fill="#fff"/><circle cx="169.7" cy="59.5" r="1.2" fill="{INK}"/>
    <path d="M176 64 l7 1.5 m-7 -1.5 l6 4.5" stroke="{RED}" stroke-width="1.8" stroke-linecap="round"/>
  </g>
  <text x="120" y="170" text-anchor="middle" font-family="'PingFang HK','Noto Sans TC','Microsoft JhengHei',sans-serif"
        font-size="30" font-weight="900" fill="{RED}" letter-spacing="1">蛇記冰室</text>
  <text x="120" y="188" text-anchor="middle" font-family="'PingFang HK','Noto Sans TC',sans-serif" font-size="10"
        font-weight="700" letter-spacing="4" fill="{GREEN}">冰室 · 茶餐廳</text>
</svg>
"""


# drinks that come hot AND iced get both pictures: <slug>-hot.svg and <slug>-iced.svg
VARIANTS = {
    "milk-tea": (lambda: hot_cup("#b98552", "#e9cfae"), lambda: iced_glass("#c99766")),
    "lemon-tea": (lambda: hot_cup("#c7802a", "#e3ad5c", lemon=True), lambda: iced_glass("#c7802a", lemon=True)),
    "yuenyeung": (lambda: hot_cup("#8e5b37", "#c79c74"), lambda: iced_glass("#946344")),
    "coffee": (lambda: hot_cup("#5b3a24", "#a77d5a"), lambda: iced_glass("#6b4329")),
    "lemon-coke": (lambda: hot_cup("#4a2416", "#7a4a33", lemon=True), lambda: iced_glass("#3b1c12", lemon=True, bubbles=True)),
    "honey-lemon": (lambda: hot_cup("#e3b04a", "#f3d58c", lemon=True), lambda: iced_glass("#e9b949", lemon=True)),
    "horlicks": (lambda: hot_cup("#d7b68a", "#f3e3c9"), lambda: iced_glass("#d8b98f")),
}


def main() -> None:
    (OUT / "menu").mkdir(parents=True, exist_ok=True)
    for slug, (category, draw) in ART.items():
        (OUT / "menu" / f"{slug}.svg").write_text(svg(draw(), TINTS[category]))
    for slug, (hot, iced) in VARIANTS.items():
        (OUT / "menu" / f"{slug}-hot.svg").write_text(svg(hot(), TINTS["drink"]))
        (OUT / "menu" / f"{slug}-iced.svg").write_text(svg(iced(), TINTS["drink"]))
    (OUT / "logo.svg").write_text(LOGO)
    print(f"wrote {len(ART)} menu illustrations + logo to {OUT}")


if __name__ == "__main__":
    main()
