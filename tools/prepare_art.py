#!/usr/bin/env python3
"""
Winter Cabin - turn the painted source art into the shipped assets.

  * Wallpapers/   upscaled stills in 16:10 and 16:9, painted smoke left intact
  * Sources/WinterCabin/Resources/scene.jpg
                  the live-layer base plate, with the painted chimney plume
                  removed so the animated smoke has somewhere to come from
  * Sources/WinterCabin/Resources/scene-manifest.json
                  anchor points measured off this artwork

Usage: python tools/prepare_art.py
"""
import json
import os

import cv2
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "art", "source.webp")
WALL = os.path.join(HERE, "Wallpapers")
RES = os.path.join(HERE, "Sources", "WinterCabin", "Resources")
os.makedirs(WALL, exist_ok=True)
os.makedirs(RES, exist_ok=True)


# ----------------------------------------------------------------- upscaling
def upscale(img: Image.Image, target: tuple[int, int]) -> Image.Image:
    """Progressive Lanczos with light sharpening between steps.

    The source is only 1672px wide, so this cannot invent detail that is not
    there; it keeps edges crisp and avoids the mush of a single big resize.
    """
    out = img.convert("RGB")
    tw, th = target
    while out.width * 1.75 < tw:
        nw = int(out.width * 1.75)
        nh = int(round(nw * out.height / out.width))
        out = out.resize((nw, nh), Image.LANCZOS)
        out = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=42, threshold=2))
    out = out.resize((tw, th), Image.LANCZOS)

    # edge-preserving detail lift, blended gently so it stays painterly
    arr = cv2.cvtColor(np.asarray(out), cv2.COLOR_RGB2BGR)
    try:
        detail = cv2.detailEnhance(arr, sigma_s=8, sigma_r=0.12)
        arr = cv2.addWeighted(arr, 0.74, detail, 0.26, 0)
    except cv2.error:
        pass
    out = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))
    out = out.filter(ImageFilter.UnsharpMask(radius=2.2, percent=34, threshold=3))

    # a whisper of grain so the upscale reads as paint rather than as blur
    a = np.asarray(out, np.float32)
    rng = np.random.default_rng(11)
    a = np.clip(a + rng.normal(0, 2.0, a.shape).astype(np.float32), 0, 255)
    return Image.fromarray(a.astype(np.uint8))


def crop_16_10(img: Image.Image) -> Image.Image:
    want = img.height * 1.6
    if img.width <= want:
        return img
    cut = int(round((img.width - want) / 2))
    return img.crop((cut, 0, img.width - cut, img.height))


# ------------------------------------------------------- remove painted smoke
def remove_smoke(img: Image.Image) -> Image.Image:
    """Left deliberately as a pass-through.

    The painted plume rises straight into the tree foliage at the top of the
    frame, so there is no clean background to rebuild behind it - inpainting
    smeared the fire glow upward and tore the branch. The painted plume is kept
    and the live layer drifts faint wisps over it instead, which reads as the
    smoke moving rather than as a second plume.
    """
    return img


# ----------------------------------------------------------------- manifest
def bulbs_along(points, spacing=0.0085, sag=0.0):
    """Lay bulbs along a polyline given in normalised coordinates."""
    out = []
    for i in range(len(points) - 1):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        seg = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        n = max(2, int(seg / spacing))
        for k in range(n):
            t = k / n
            droop = sag * (4 * t * (1 - t))
            out.append({"x": round(x0 + (x1 - x0) * t, 5),
                        "y": round(y0 + (y1 - y0) * t + droop, 5)})
    out.append({"x": round(points[-1][0], 5), "y": round(points[-1][1], 5)})
    return out


def build_manifest(aspect: float) -> dict:
    gable = [(0.2073, 0.4251), (0.2950, 0.2586), (0.3608, 0.4322)]
    left_wall = [(0.0680, 0.4890), (0.1455, 0.4874)]
    porch = [(0.2173, 0.5399), (0.3828, 0.5442)]

    return {
        "note": "Normalised 0-1, origin top-left, over the native image aspect.",
        "aspect": round(aspect, 5),
        "moon": {"x": 0.8865, "y": 0.0415, "r": 0.0265},
        "chimney": {"x": 0.1710, "y": 0.1400},
        "lake": {"x": 0.560, "y": 0.585, "w": 0.440, "h": 0.145},
        "windows": [
            {"x": 0.251, "y": 0.332, "w": 0.036, "h": 0.078},
            {"x": 0.082, "y": 0.528, "w": 0.076, "h": 0.110},
            {"x": 0.239, "y": 0.535, "w": 0.052, "h": 0.103},
        ],
        "lanterns": [
            {"x": 0.208, "y": 0.567},
            {"x": 0.306, "y": 0.567},
            {"x": 0.344, "y": 0.616},
        ],
        "bulbs": (bulbs_along(gable, 0.0092)
                  + bulbs_along(left_wall, 0.0100, sag=0.004)
                  + bulbs_along(porch, 0.0100, sag=0.006)),
        "reflections": [{"x": x, "y": 0.600} for x in
                        [0.572, 0.598, 0.622, 0.648, 0.670, 0.694, 0.716,
                         0.740, 0.762, 0.788, 0.812, 0.836, 0.858]],
        "villageWindows": {"x": 0.560, "y": 0.440, "w": 0.400, "h": 0.120},
        "calmBottomFraction": 0.12,
    }


# --------------------------------------------------------------------- main
def main():
    src = Image.open(SRC).convert("RGB")
    aspect = src.width / src.height
    print(f"source {src.width}x{src.height}  aspect {aspect:.4f}")

    # --- static wallpapers (painted smoke kept)
    wide = crop_16_10(src)
    for size in [(5120, 3200), (2880, 1800)]:
        img = upscale(wide, size)
        path = os.path.join(WALL, f"WinterCabin-{size[0]}x{size[1]}.png")
        img.save(path, "PNG")
        print("wrote", path)

    # 16:9 extras ship as high-quality JPEG to keep the .dmg easy to send
    for size in [(3840, 2160), (2560, 1440)]:
        img = upscale(src, size)
        path = os.path.join(WALL, f"WinterCabin-{size[0]}x{size[1]}.jpg")
        img.save(path, "JPEG", quality=94, optimize=True, progressive=True)
        print("wrote", path)

    # --- live base plate, native aspect (painted plume kept, see remove_smoke)
    plate = upscale(remove_smoke(src), (3840, int(round(3840 / aspect))))
    plate_path = os.path.join(RES, "scene.jpg")
    plate.save(plate_path, "JPEG", quality=90, optimize=True, progressive=True)
    print("wrote", plate_path, plate.size, os.path.getsize(plate_path), "bytes")

    manifest = build_manifest(aspect)
    mpath = os.path.join(RES, "scene-manifest.json")
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print("wrote", mpath, len(manifest["bulbs"]), "bulbs")


if __name__ == "__main__":
    main()
