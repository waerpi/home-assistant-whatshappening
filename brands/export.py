"""Render the brand PNGs from the SVG masters."""

from pathlib import Path

import cairosvg
from PIL import Image

HERE = Path(__file__).parent
TMP = HERE / ".render.png"


def render(src: str, dst: str, max_dim: int, trim: bool) -> None:
    """Render `src` so that its longest side is `max_dim` pixels."""
    cairosvg.svg2png(
        url=str(HERE / src), write_to=str(TMP), output_width=2048, output_height=2048
    )
    image = Image.open(TMP).convert("RGBA")
    if trim:
        image = image.crop(image.getbbox())
    scale = max_dim / max(image.size)
    image = image.resize(
        (round(image.width * scale), round(image.height * scale)), Image.LANCZOS
    )
    image.save(HERE / dst)
    print(f"{dst}: {image.width}x{image.height}")


for size in (256, 512):
    suffix = "" if size == 256 else "@2x"
    render("icon.svg", f"icon{suffix}.png", size, trim=False)
    render("logo.svg", f"logo{suffix}.png", size, trim=True)

TMP.unlink()
