#!/usr/bin/env python3
"""
Write "How to install.pdf" for the disk image.

Produces a real vector PDF with selectable Helvetica text and the artwork
embedded as a JPEG banner, with no third-party dependencies.
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "art", "source.webp")
OUT = os.path.join(HERE, "dist", "How to install.pdf")

PAGE_W, PAGE_H = 595.0, 842.0
MARGIN = 54.0
TEXT_W = PAGE_W - MARGIN * 2

# Helvetica advance widths /1000 em, close enough for wrapping.
NARROW = set("iljtfrI.,:;'|!()[]{}-/\\ ")
WIDE = set("mwMW@%")


def char_width(ch: str, bold: bool) -> float:
    if ch in NARROW:
        base = 280
    elif ch in WIDE:
        base = 830
    elif ch.isupper():
        base = 680
    elif ch.isdigit():
        base = 556
    else:
        base = 530
    return base * (1.06 if bold else 1.0) / 1000.0


def text_width(s: str, size: float, bold: bool) -> float:
    return sum(char_width(c, bold) for c in s) * size


def wrap(s: str, size: float, bold: bool, width: float):
    words, lines, line = s.split(), [], ""
    for word in words:
        trial = word if not line else line + " " + word
        if text_width(trial, size, bold) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


# characters that live outside latin-1 but do exist in WinAnsiEncoding
WINANSI = {
    "•": "", "–": "", "—": "",
    "‘": "", "’": "",
    "“": "", "”": "", "›": "", "‹": "",
}


def esc(s: str) -> bytes:
    for src, dst in WINANSI.items():
        s = s.replace(src, dst)
    out = s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
    return out.encode("latin-1", "replace")


class Content:
    def __init__(self):
        self.ops: list[bytes] = []
        self.y = PAGE_H - 210.0

    def colour(self, r, g, b):
        self.ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg".encode())

    def line(self, s, size, bold, x=MARGIN, lead=None, colour=(0.12, 0.13, 0.18)):
        self.colour(*colour)
        font = b"/F2" if bold else b"/F1"
        self.ops.append(b"BT " + font + f" {size:.1f} Tf {x:.1f} {self.y:.1f} Td (".encode()
                        + esc(s) + b") Tj ET")
        self.y -= lead if lead is not None else size * 1.42

    def heading(self, s):
        self.y -= 7
        self.line(s, 13.5, True, colour=(0.10, 0.11, 0.17))
        self.y -= 1

    def body(self, s, x=MARGIN, width=TEXT_W):
        for part in wrap(s, 10.5, False, width):
            self.line(part, 10.5, False, x=x, lead=13.6, colour=(0.22, 0.24, 0.30))

    def bullet(self, s, marker="•"):
        self.colour(0.22, 0.24, 0.30)
        self.ops.append(b"BT /F1 10.5 Tf " + f"{MARGIN:.1f} {self.y:.1f} Td (".encode()
                        + esc(marker) + b") Tj ET")
        self.body(s, x=MARGIN + 14, width=TEXT_W - 14)
        self.y -= 2

    def step(self, n, s):
        self.colour(0.22, 0.24, 0.30)
        self.ops.append(b"BT /F2 10.5 Tf " + f"{MARGIN:.1f} {self.y:.1f} Td (".encode()
                        + esc(f"{n}.") + b") Tj ET")
        self.body(s, x=MARGIN + 16, width=TEXT_W - 16)
        self.y -= 2

    def image(self, name, x, y, w, h):
        self.ops.append(f"q {w:.2f} 0 0 {h:.2f} {x:.2f} {y:.2f} cm /{name} Do Q".encode())

    def rule(self):
        self.y -= 6
        self.ops.append(b"0.78 0.80 0.86 RG 0.8 w "
                        + f"{MARGIN:.1f} {self.y:.1f} m {PAGE_W - MARGIN:.1f} "
                          f"{self.y:.1f} l S".encode())
        self.y -= 14

    def data(self) -> bytes:
        return b"\n".join(self.ops)


def banner_jpeg() -> tuple[bytes, int, int]:
    img = Image.open(SRC).convert("RGB")
    target_w = 1190                      # 2x the page width
    target_h = int(round(target_w * 0.30))
    crop_h = int(img.height * 0.62)
    img = img.crop((0, 0, img.width, crop_h)).resize((target_w, target_h), Image.LANCZOS)
    path = os.path.join(HERE, "dist", "_banner.jpg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "JPEG", quality=88, optimize=True)
    with open(path, "rb") as fh:
        data = fh.read()
    os.remove(path)
    return data, target_w, target_h


def build() -> bytes:
    jpeg, jw, jh = banner_jpeg()

    c = Content()
    banner_h = 150.0
    c.image("Im1", 0, PAGE_H - banner_h, PAGE_W, banner_h)

    c.y = PAGE_H - banner_h - 38
    c.line("Winter Cabin", 24, True, colour=(0.10, 0.11, 0.17))
    c.line("A snowy desktop for macOS - how to install it", 11.5, False,
           colour=(0.42, 0.45, 0.52))
    c.rule()

    c.heading("Install it")
    c.step(1, "Open WinterCabin.dmg by double-clicking it.")
    c.step(2, "Drag Winter Cabin onto the Applications folder shown beside it.")
    c.step(3, "Eject the disk image, then open Winter Cabin from Applications.")

    c.heading("The first time you open it")
    c.body("macOS will warn that the app is from an unidentified developer. That is "
           "expected: the app is signed ad-hoc rather than with a paid Apple Developer "
           "ID, so Apple has not been asked to vouch for it. Open it like this, once:")
    c.bullet("Right-click (or Control-click) Winter Cabin in your Applications folder "
             "and choose Open. In the dialog that appears, click Open again. After that "
             "it opens normally like any other app.")
    c.bullet("If there is no Open button, go to System Settings > Privacy & Security, "
             "scroll down to Security, and click Open Anyway next to Winter Cabin.")

    c.heading("Using it")
    c.body("Winter Cabin has no window. Everything lives behind the snowflake in your "
           "menu bar, at the top right of the screen.")
    c.bullet("Snow on or off, and how heavily it falls: light, medium or blizzard.")
    c.bullet("Snow settles along the bottom of the screen, on top of the Dock, and on "
             "the top edge of any window that is open. Move a window and its snow "
             "slides off.")
    c.bullet("Click a bare patch of desktop to drop a snowball. Stack three in the same "
             "spot and they become a snowman.")
    c.bullet("Every few minutes a small plow drives through and clears everything. "
             "Send the plow now does it on demand.")
    c.bullet("Ambient wallpaper motion adds drifting chimney smoke, twinkling string "
             "lights, flickering windows and shimmer on the lake.")

    c.heading("Permissions")
    c.body("None. Winter Cabin reads only the position and size of your open windows, "
           "never their contents, so macOS does not ask for Screen Recording or "
           "Accessibility. The snow layer never swallows a click, so your Dock, desktop "
           "icons and apps all carry on working normally.")

    c.heading("The Wallpapers folder")
    c.body("The disk image also carries the scene as plain picture files, for anyone "
           "who just wants the image without the app. Sizes are included for Retina and "
           "for ordinary displays, in both 16:10 and 16:9.")

    c.heading("Removing it")
    c.body("Choose Quit Winter Cabin from the menu, which puts your previous desktop "
           "picture back, then drag the app from Applications to the Trash.")

    content = c.data()

    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W:.0f} {PAGE_H:.0f}] "
        f"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> /XObject << /Im1 7 0 R >> >> "
        f"/Contents 4 0 R >>".encode())
    objects.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
                   + content + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                   b"/Encoding /WinAnsiEncoding >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
                   b"/Encoding /WinAnsiEncoding >>")
    objects.append(f"<< /Type /XObject /Subtype /Image /Width {jw} /Height {jh} "
                   f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode "
                   f"/Length {len(jpeg)} >>".encode() + b"\nstream\n" + jpeg + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_at = len(out)
    n = len(objects) + 1
    out += f"xref\n0 {n}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {n} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n").encode()
    return bytes(out)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    data = build()
    with open(OUT, "wb") as fh:
        fh.write(data)
    print("wrote", OUT, len(data), "bytes")


if __name__ == "__main__":
    main()
