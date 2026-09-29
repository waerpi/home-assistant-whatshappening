"""Render the brand PNGs from the SVG masters into the integration.

Home Assistant serves `custom_components/<domain>/brand/*.png` itself since
2026.3.0, so that folder is the output — see brands/README.md.
"""

from pathlib import Path

import cairosvg
import oxipng
from PIL import Image

HERE = Path(__file__).parent
OUT = HERE.parent / "custom_components" / "whatshappening" / "brand"
TMP = HERE / ".render.png"


def render(src: str, dst: str, size: int, *, by_shortest_side: bool) -> None:
    """Render `src` to `size` pixels on one side.

    The icon is square and sized by its (equal) sides; the logo is landscape
    and sized by its shortest side, which is what the brand specification
    constrains.
    """
    cairosvg.svg2png(
        url=str(HERE / src), write_to=str(TMP), output_width=2048, output_height=2048
    )
    image = Image.open(TMP).convert("RGBA")
    image = image.crop(image.getbbox())
    scale = size / (min(image.size) if by_shortest_side else max(image.size))
    image = image.resize(
        (round(image.width * scale), round(image.height * scale)), Image.LANCZOS
    )
    out = OUT / dst
    image.save(out, optimize=True)
    # The brand specification asks for losslessly optimized images.
    oxipng.optimize(str(out), level=6, strip=oxipng.StripChunks.safe())
    print(f"{dst}: {image.width}x{image.height}, {out.stat().st_size} bytes")


OUT.mkdir(parents=True, exist_ok=True)
for size_factor, suffix in ((1, ""), (2, "@2x")):
    render("icon.svg", f"icon{suffix}.png", 256 * size_factor, by_shortest_side=False)
    render("logo.svg", f"logo{suffix}.png", 256 * size_factor, by_shortest_side=True)

TMP.unlink()
