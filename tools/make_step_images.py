#!/usr/bin/env python3
"""
Draw the step-by-step illustrations for the beginner install guide.

These are clean diagrams of the macOS screens, not photographs: they are drawn
so the one thing to click can be circled, and so they do not go stale when
Apple restyles a dialog.

Writes dist/guide/step*.jpg
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "dist", "guide")
ICON = os.path.join(HERE, "scripts", "AppIcon.iconset", "icon_256x256.png")
ART = os.path.join(HERE, "art", "source.webp")
os.makedirs(OUT, exist_ok=True)

ARIAL = "C:/Windows/Fonts/arial.ttf"
ARIAL_B = "C:/Windows/Fonts/arialbd.ttf"

W = 1200

INK = (28, 30, 36)
GREY = (118, 124, 134)
LINE = (208, 212, 220)
PANEL = (247, 248, 250)
WHITE = (255, 255, 255)
BLUE = (0, 122, 255)
RED = (227, 58, 58)
SIDEBAR = (236, 238, 242)


def font(size, bold=False):
    return ImageFont.truetype(ARIAL_B if bold else ARIAL, size)


def text(d, xy, s, size=22, bold=False, fill=INK, anchor="la"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def text_w(s, size, bold=False):
    return font(size, bold).getlength(s)


def canvas(h, bg=(252, 252, 253)):
    im = Image.new("RGB", (W, h), bg)
    return im, ImageDraw.Draw(im)


def window(d, box, title, sidebar=False, radius=16):
    """A macOS-looking window with traffic lights and a title bar."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=radius, fill=WHITE, outline=LINE, width=2)
    bar = y0 + 52
    d.rounded_rectangle([x0, y0, x1, bar + radius], radius=radius, fill=PANEL,
                        outline=None)
    d.rectangle([x0, bar - radius, x1, bar], fill=PANEL)
    d.line([x0, bar, x1, bar], fill=LINE, width=2)
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = x0 + 26 + i * 24
        d.ellipse([cx - 7, bar - 33, cx + 7, bar - 19], fill=col)
    text(d, ((x0 + x1) / 2, bar - 26), title, 20, True, INK, anchor="mm")
    if sidebar:
        d.rectangle([x0 + 2, bar, x0 + 250, y1 - 2], fill=SIDEBAR)
        d.line([x0 + 250, bar, x0 + 250, y1], fill=LINE, width=2)
    return bar


def button(d, box, label, kind="normal", size=20):
    """kind: normal | primary | danger"""
    fill = {"normal": WHITE, "primary": BLUE, "danger": WHITE}[kind]
    fg = {"normal": INK, "primary": WHITE, "danger": RED}[kind]
    outline = {"normal": LINE, "primary": BLUE, "danger": LINE}[kind]
    d.rounded_rectangle(box, radius=9, fill=fill, outline=outline, width=2)
    text(d, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 1), label, size,
         kind == "primary", fg, anchor="mm")


def circle_it(im, box, pad=14, width=6):
    """Red marker ring around the thing to click."""
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad],
                         radius=(box[3] - box[1] + pad * 2) // 2,
                         outline=RED + (255,), width=width)
    im.paste(Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB"), (0, 0))


def cursor(d, x, y, scale=1.0):
    """The macOS arrow pointer."""
    s = scale
    pts = [(x, y), (x, y + 34 * s), (x + 9 * s, y + 26 * s), (x + 15 * s, y + 39 * s),
           (x + 22 * s, y + 36 * s), (x + 16 * s, y + 23 * s), (x + 26 * s, y + 23 * s)]
    d.polygon(pts, fill=WHITE, outline=INK)
    d.line(pts + [pts[0]], fill=INK, width=2)


def snowflake(d, cx, cy, r, fill=(255, 255, 255), width=3):
    """Drawn rather than typed: Arial has no snowflake glyph."""
    import math
    for i in range(6):
        a = math.pi * i / 3
        d.line([cx, cy, cx + math.cos(a) * r, cy + math.sin(a) * r],
               fill=fill, width=width)
        for t in (0.46, 0.74):
            bx, by = cx + math.cos(a) * r * t, cy + math.sin(a) * r * t
            for da in (-0.62, 0.62):
                d.line([bx, by,
                        bx + math.cos(a + da) * r * 0.30,
                        by + math.sin(a + da) * r * 0.30],
                       fill=fill, width=max(1, width - 1))


def app_icon(size):
    return Image.open(ICON).convert("RGBA").resize((size, size), Image.LANCZOS)


def folder_icon(d, box, label="Applications"):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0 + 16, x1, y1], radius=12, fill=(118, 182, 236),
                        outline=(86, 152, 212), width=2)
    d.rounded_rectangle([x0, y0, x0 + (x1 - x0) * 0.45, y0 + 30], radius=8,
                        fill=(132, 194, 244), outline=(86, 152, 212), width=2)
    d.rounded_rectangle([x0, y0 + 18, x1, y1], radius=12, fill=(150, 203, 245),
                        outline=(96, 160, 216), width=2)


def shadow(im, box, radius=16, blur=16, alpha=46):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [box[0] + 4, box[1] + 10, box[2] + 4, box[3] + 12], radius=radius,
        fill=(0, 0, 0, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    im.paste(Image.alpha_composite(im.convert("RGBA"), sh).convert("RGB"), (0, 0))


def save(im, name):
    path = os.path.join(OUT, name + ".jpg")
    im.save(path, "JPEG", quality=92, optimize=True)
    print("wrote", path, im.size)


# --------------------------------------------------------------- 1. the file
def step1():
    im, d = canvas(520)
    box = (70, 40, 1130, 470)
    shadow(im, box); d = ImageDraw.Draw(im)
    bar = window(d, box, "Downloads", sidebar=True)

    for i, (lbl, sel) in enumerate([("Documents", False), ("Downloads", True),
                                    ("Desktop", False), ("Pictures", False)]):
        y = bar + 28 + i * 46
        if sel:
            d.rounded_rectangle([box[0] + 14, y - 8, box[0] + 238, y + 30],
                                radius=8, fill=(214, 220, 230))
        text(d, (box[0] + 36, y), lbl, 21, sel, INK if sel else GREY)

    row = bar + 40
    d.rounded_rectangle([box[0] + 274, row - 10, box[2] - 24, row + 58],
                        radius=8, fill=(0, 122, 255))
    ic = app_icon(56)
    im.paste(ic, (box[0] + 290, row - 2), ic)
    d = ImageDraw.Draw(im)
    text(d, (box[0] + 364, row + 14), "WinterCabin.dmg", 23, True, WHITE)
    text(d, (box[2] - 210, row + 17), "45.1 MB", 19, False, (225, 235, 250))

    for i, nm in enumerate(["Screenshot.png", "notes.pdf"]):
        y = row + 118 + i * 46
        text(d, (box[0] + 364, y), nm, 21, False, GREY)

    cursor(d, box[0] + 470, row + 30, 1.1)
    text(d, (box[0] + 486, row + 74), "double-click it", 21, True, RED)
    save(im, "step1")


# ------------------------------------------------------------ 2. drag across
def step2():
    im, d = canvas(540)
    box = (150, 40, 1050, 480)
    shadow(im, box); d = ImageDraw.Draw(im)
    bar = window(d, box, "Winter Cabin")

    ic = app_icon(150)
    im.paste(ic, (300, bar + 70), ic)
    d = ImageDraw.Draw(im)
    text(d, (375, bar + 236), "Winter Cabin", 22, True, INK, anchor="ma")

    folder_icon(d, (700, bar + 78, 850, bar + 212))
    text(d, (775, bar + 236), "Applications", 22, True, INK, anchor="ma")

    d.arc([430, bar + 76, 730, bar + 200], start=200, end=340, fill=RED, width=7)
    d.polygon([(742, bar + 142), (706, bar + 126), (714, bar + 162)], fill=RED)
    text(d, (585, bar + 28), "drag it onto the folder", 23, True, RED, anchor="ma")
    save(im, "step2")


# ------------------------------------------------------------- 3. the warning
def step3():
    im, d = canvas(560)
    box = (300, 30, 900, 470)
    shadow(im, box, radius=20); d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, radius=20, fill=(246, 246, 248), outline=LINE, width=2)

    ic = app_icon(104)
    im.paste(ic, (548, 66), ic)
    d = ImageDraw.Draw(im)

    text(d, (600, 196), "\u201cWinter Cabin\u201d Not Opened", 25, True, INK, anchor="ma")
    for i, ln in enumerate(["Apple could not verify \u201cWinter Cabin\u201d is",
                            "free of malware that may harm your Mac."]):
        text(d, (600, 240 + i * 30), ln, 20, False, (92, 96, 104), anchor="ma")

    button(d, (348, 330, 588, 382), "Move to Bin", "danger")
    button(d, (612, 330, 852, 382), "Done", "primary")
    circle_it(im, (612, 330, 852, 382), pad=12)
    d = ImageDraw.Draw(im)
    text(d, (732, 418), "click Done \u2014 this is normal", 21, True, RED, anchor="ma")
    save(im, "step3")


# ------------------------------------------------- 4. settings / open anyway
def step4():
    im, d = canvas(600)
    box = (60, 30, 1140, 540)
    shadow(im, box); d = ImageDraw.Draw(im)
    bar = window(d, box, "Privacy & Security", sidebar=True)

    for i, (lbl, sel) in enumerate([("Appearance", False), ("Control Centre", False),
                                    ("Privacy & Security", True), ("Desktop & Dock", False)]):
        y = bar + 30 + i * 48
        if sel:
            d.rounded_rectangle([box[0] + 14, y - 9, box[0] + 238, y + 32],
                                radius=8, fill=BLUE)
        text(d, (box[0] + 34, y), lbl, 20, sel, WHITE if sel else INK)

    text(d, (box[0] + 290, bar + 34), "Security", 26, True, INK)
    d.rounded_rectangle([box[0] + 290, bar + 86, box[2] - 40, bar + 206],
                        radius=12, fill=PANEL, outline=LINE, width=2)
    text(d, (box[0] + 316, bar + 112),
         "\u201cWinter Cabin\u201d was blocked to protect your Mac.", 21, False, INK)
    text(d, (box[0] + 316, bar + 148), "It is not from the App Store.",
         18, False, GREY)

    btn = (box[2] - 232, bar + 108, box[2] - 70, bar + 160)
    button(d, btn, "Open Anyway")
    circle_it(im, btn, pad=12)
    d = ImageDraw.Draw(im)

    text(d, (box[0] + 290, bar + 250), "scroll down to find this", 21, True, RED)
    save(im, "step4")


# ------------------------------------------------------- 5. it is running now
def step5():
    im, d = canvas(620)
    scr = (70, 30, 1130, 520)
    shadow(im, scr); d = ImageDraw.Draw(im)

    art = Image.open(ART).convert("RGB")
    sw, sh = scr[2] - scr[0], scr[3] - scr[1]
    a = art.resize((sw, int(sw * art.height / art.width)), Image.LANCZOS)
    a = a.crop((0, 0, sw, min(sh, a.height)))
    shot = Image.new("RGB", (sw, sh), (16, 20, 44))
    shot.paste(a, (0, 0))
    sd = ImageDraw.Draw(shot)

    # menu bar
    sd.rectangle([0, 0, sw, 34], fill=(22, 24, 40))
    for i, lbl in enumerate(["Finder", "File", "Edit", "View", "Window", "Help"]):
        sd.text((26 + i * 76, 8), lbl, font=font(17, i == 0), fill=(236, 238, 245))
    sd.text((sw - 120, 8), "Fri 14:29", font=font(17), fill=(236, 238, 245))
    flake_x = sw - 196
    snowflake(sd, flake_x + 11, 17, 11, (255, 255, 255), 2)

    # drawn snow
    import random
    r = random.Random(4)
    for _ in range(260):
        x, y = r.uniform(0, sw), r.uniform(34, sh)
        rad = r.uniform(1.4, 4.2)
        sd.ellipse([x - rad, y - rad, x + rad, y + rad],
                   fill=(255, 255, 255, 220))
    # snow along the bottom
    sd.rounded_rectangle([-20, sh - 26, sw + 20, sh + 30], radius=16,
                         fill=(238, 242, 252))
    # dock with a drift on top
    dock = (sw / 2 - 210, sh - 82, sw / 2 + 210, sh - 18)
    sd.rounded_rectangle(dock, radius=18, fill=(58, 62, 84))
    sd.rounded_rectangle([dock[0] - 6, dock[1] - 14, dock[2] + 6, dock[1] + 12],
                         radius=12, fill=(243, 246, 253))
    for i in range(5):
        cx = dock[0] + 48 + i * 78
        sd.rounded_rectangle([cx - 24, dock[1] + 20, cx + 24, dock[1] + 56],
                             radius=10, fill=(120, 150, 200))

    im.paste(shot, (scr[0], scr[1]))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(scr, radius=10, outline=LINE, width=2)

    target = (scr[0] + flake_x - 4, scr[1] + 4, scr[0] + flake_x + 26, scr[1] + 32)
    circle_it(im, target, pad=10, width=5)
    d = ImageDraw.Draw(im)
    text(d, (W / 2, 560),
         "the snowflake at the top right — everything is in there",
         23, True, RED, anchor="ma")
    save(im, "step5")


if __name__ == "__main__":
    step1(); step2(); step3(); step4(); step5()
