"""
Generates the repo's banner and thumbnail images.

Draws a stylized sun disc with sunspot groups (dark umbra core + lighter
penumbra ring, matching the terminology sun.f itself uses) on a starfield,
as SVG, then rasterizes to PNG via rsvg-convert.

Run with the project's venv:
    .venv/bin/python build_assets.py
"""
import random
import subprocess
from pathlib import Path

ASSETS = Path("assets")
ASSETS.mkdir(exist_ok=True)

# Palette: deep-space surface + warm sun ramp
SPACE_TOP = "#0b1220"
SPACE_BOTTOM = "#141b2e"
SUN_CORE = "#ffe38a"
SUN_MID = "#eda100"
SUN_EDGE = "#c9600f"
UMBRA = "#2b1810"
PENUMBRA = "#8a4a24"
TEXT_PRIMARY = "#f5f3ee"
TEXT_MUTED = "#9aa3b5"
ACCENT = "#2a78d6"  # Python-ish blue, echoes the notebook chart's series-1 color


def stars(rng: random.Random, n: int, w: int, h: int) -> str:
    dots = []
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(0.4, 1.4)
        op = rng.uniform(0.25, 0.9)
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#ffffff" opacity="{op:.2f}"/>')
    return "\n".join(dots)


def sunspots(rng: random.Random, cx: float, cy: float, disc_r: float, n: int) -> str:
    """Scatter n sunspot groups within the inner ~70% of the disc, each an
    umbra core inside a penumbra halo -- avoids the exact center and edge,
    like real mid-latitude active regions."""
    groups = []
    placed = []
    attempts = 0
    while len(placed) < n and attempts < 200:
        attempts += 1
        angle = rng.uniform(0, 6.283)
        dist = rng.uniform(disc_r * 0.15, disc_r * 0.68)
        x = cx + dist * __import__("math").cos(angle)
        y = cy + dist * __import__("math").sin(angle) * 0.55  # flatten for a limb-viewed look
        size = rng.uniform(disc_r * 0.05, disc_r * 0.13)
        if any(((x - px) ** 2 + (y - py) ** 2) ** 0.5 < (size + ps) * 1.3 for px, py, ps in placed):
            continue
        placed.append((x, y, size))
        pen_r = size * 1.9
        groups.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pen_r:.1f}" fill="{PENUMBRA}" opacity="0.55"/>\n'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="{UMBRA}"/>'
        )
    return "\n".join(groups)


def sun_defs(gradient_id: str, glow_id: str) -> str:
    return f"""
    <radialGradient id="{gradient_id}" cx="35%" cy="32%" r="75%">
      <stop offset="0%" stop-color="{SUN_CORE}"/>
      <stop offset="55%" stop-color="{SUN_MID}"/>
      <stop offset="100%" stop-color="{SUN_EDGE}"/>
    </radialGradient>
    <radialGradient id="{glow_id}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{SUN_MID}" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="{SUN_MID}" stop-opacity="0"/>
    </radialGradient>
    """


def build_banner() -> str:
    w, h = 1280, 640
    rng = random.Random(7)
    cx, cy, r = 900, 320, 250

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{SPACE_TOP}"/>
      <stop offset="100%" stop-color="{SPACE_BOTTOM}"/>
    </linearGradient>
    {sun_defs("sunGrad", "sunGlow")}
  </defs>

  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  {stars(rng, 140, w, h)}

  <circle cx="{cx}" cy="{cy}" r="{r * 1.55:.0f}" fill="url(#sunGlow)"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sunGrad)"/>
  {sunspots(rng, cx, cy, r, 7)}

  <text x="70" y="252" font-family="Liberation Sans, Arial, sans-serif" font-size="54"
        font-weight="700" fill="{TEXT_PRIMARY}">Sunspot Umbra / Pore</text>
  <text x="70" y="312" font-family="Liberation Sans, Arial, sans-serif" font-size="54"
        font-weight="700" fill="{TEXT_PRIMARY}">Evolution Model</text>

  <g font-family="Liberation Mono, DejaVu Sans Mono, monospace" font-size="24">
    <rect x="70" y="352" width="88" height="38" rx="6" fill="none" stroke="{TEXT_MUTED}" stroke-width="1.5"/>
    <text x="88" y="378" fill="{TEXT_MUTED}">sun.f</text>
    <text x="172" y="378" fill="{TEXT_MUTED}" font-family="Liberation Sans, Arial, sans-serif">&#8594;</text>
    <rect x="206" y="352" width="112" height="38" rx="6" fill="none" stroke="{ACCENT}" stroke-width="1.5"/>
    <text x="224" y="378" fill="{ACCENT}">Python</text>
  </g>

  <text x="70" y="430" font-family="Liberation Sans, Arial, sans-serif" font-size="20"
        fill="{TEXT_MUTED}">rodney_fortran_sun &#8226; FORTRAN 77 port &#8226; CLI + JupyterLab</text>
</svg>"""
    return svg


def build_thumbnail() -> str:
    w = h = 512
    rng = random.Random(11)
    cx, cy, r = 256, 256, 175

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{SPACE_TOP}"/>
      <stop offset="100%" stop-color="{SPACE_BOTTOM}"/>
    </linearGradient>
    {sun_defs("sunGrad", "sunGlow")}
  </defs>

  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  {stars(rng, 55, w, h)}

  <circle cx="{cx}" cy="{cy}" r="{r * 1.5:.0f}" fill="url(#sunGlow)"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sunGrad)"/>
  {sunspots(rng, cx, cy, r, 6)}
</svg>"""
    return svg


def rasterize(svg_path: Path, png_path: Path, width: int) -> None:
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "--keep-aspect-ratio", str(svg_path), "-o", str(png_path)],
        check=True,
    )


def main() -> None:
    banner_svg = ASSETS / "banner.svg"
    banner_png = ASSETS / "banner.png"
    thumb_svg = ASSETS / "thumbnail.svg"
    thumb_png = ASSETS / "thumbnail.png"

    banner_svg.write_text(build_banner())
    thumb_svg.write_text(build_thumbnail())

    rasterize(banner_svg, banner_png, 1280)
    rasterize(thumb_svg, thumb_png, 512)

    print(f"Wrote {banner_svg}, {banner_png}")
    print(f"Wrote {thumb_svg}, {thumb_png}")


if __name__ == "__main__":
    main()
