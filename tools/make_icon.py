#!/usr/bin/env python3
"""Build the macOS .iconset from the artwork. Run iconutil on it in CI."""
import os

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "art", "source.webp")
OUT = os.path.join(HERE, "scripts", "AppIcon.iconset")
os.makedirs(OUT, exist_ok=True)

SIZES = [(16, 1), (16, 2), (32, 1), (32, 2), (128, 1), (128, 2),
         (256, 1), (256, 2), (512, 1), (512, 2)]


def master() -> Image.Image:
    """A 1024px rounded-square icon: the cabin, inset the way macOS icons are."""
    src = Image.open(SRC).convert("RGB")
    w, h = src.size

    # square crop centred on the cabin and its lit windows
    side = int(h * 0.92)
    cx = int(w * 0.215)
    left = max(0, min(w - side, cx - side // 2))
    top = max(0, min(h - side, int(h * 0.12)))
    art = src.crop((left, top, left + side, top + side)).resize((824, 824), Image.LANCZOS)

    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))

    # rounded-rect mask, macOS-ish corner radius
    mask = Image.new("L", (824, 824), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 823, 823], radius=184, fill=255)

    # soft drop shadow under the tile
    shadow = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    sd = Image.new("L", (824, 824), 0)
    ImageDraw.Draw(sd).rounded_rectangle([0, 0, 823, 823], radius=184, fill=110)
    shadow.paste((0, 0, 0, 255), (100, 118), sd)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas = Image.alpha_composite(canvas, shadow)

    tile = Image.new("RGBA", (824, 824))
    tile.paste(art, (0, 0))
    tile.putalpha(mask)

    # a faint inner highlight along the top edge
    gloss = Image.new("RGBA", (824, 824), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gloss)
    gd.rounded_rectangle([2, 2, 821, 821], radius=182, outline=(255, 255, 255, 60), width=3)
    tile = Image.alpha_composite(tile, gloss)

    canvas.paste(tile, (100, 100), tile)
    return canvas


def main():
    base = master()
    for size, scale in SIZES:
        px = size * scale
        name = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
        base.resize((px, px), Image.LANCZOS).save(os.path.join(OUT, name))
        print("wrote", name, px)


if __name__ == "__main__":
    main()
