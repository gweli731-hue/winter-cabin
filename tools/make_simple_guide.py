#!/usr/bin/env python3
"""
Build "Install Winter Cabin - simple guide.pdf": a three-page, picture-led
walkthrough for someone who has never installed an app outside the App Store.

Depends on tools/make_step_images.py having written dist/guide/step*.jpg.
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDE = os.path.join(HERE, "dist", "guide")
OUT = os.path.join(HERE, "dist", "Install Winter Cabin - simple guide.pdf")

PAGE_W, PAGE_H = 595.0, 842.0
MARGIN = 54.0
TEXT_W = PAGE_W - MARGIN * 2

NARROW = set("iljtfrI.,:;'|!()[]{}-/ ")
WIDE = set("mwMW@%")


def char_width(ch, bold):
    if ch in NARROW:
        base = 285
    elif ch in WIDE:
        base = 830
    elif ch.isupper():
        base = 690
    elif ch.isdigit():
        base = 556
    else:
        base = 535
    return base * (1.06 if bold else 1.0) / 1000.0


def text_width(s, size, bold=False):
    return sum(char_width(c, bold) for c in s) * size


def wrap(s, size, bold, width):
    out, line = [], ""
    for word in s.split():
        trial = word if not line else line + " " + word
        if text_width(trial, size, bold) <= width:
            line = trial
        else:
            if line:
                out.append(line)
            line = word
    if line:
        out.append(line)
    return out


WINANSI = {"•": "\x95", "–": "\x96", "—": "\x97",
           "‘": "\x91", "’": "\x92",
           "“": "\x93", "”": "\x94", "→": "\xae"}


def esc(s):
    for a, b in WINANSI.items():
        s = s.replace(a, b)
    s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return s.encode("latin-1", "replace")


class Page:
    def __init__(self):
        self.ops = []
        self.y = PAGE_H - MARGIN

    def rgb(self, r, g, b):
        self.ops.append(("%.3f %.3f %.3f rg" % (r, g, b)).encode())

    def line(self, s, size, bold=False, x=MARGIN, lead=None, colour=(0.14, 0.15, 0.19)):
        self.rgb(*colour)
        f = b"/F2" if bold else b"/F1"
        self.ops.append(b"BT " + f + (" %.1f Tf %.1f %.1f Td (" % (size, x, self.y)).encode()
                        + esc(s) + b") Tj ET")
        self.y -= lead if lead is not None else size * 1.45

    def para(self, s, size=12.5, x=MARGIN, width=TEXT_W, colour=(0.26, 0.28, 0.34),
             lead=17.0, bold=False):
        for ln in wrap(s, size, bold, width):
            self.line(ln, size, bold, x=x, lead=lead, colour=colour)

    def circle(self, cx, cy, r, colour=(0.05, 0.42, 0.95)):
        k = 0.5523 * r
        self.rgb(*colour)
        self.ops.append((
            "%.2f %.2f m %.2f %.2f %.2f %.2f %.2f %.2f c "
            "%.2f %.2f %.2f %.2f %.2f %.2f c %.2f %.2f %.2f %.2f %.2f %.2f c "
            "%.2f %.2f %.2f %.2f %.2f %.2f c f" % (
                cx + r, cy, cx + r, cy + k, cx + k, cy + r, cx, cy + r,
                cx - k, cy + r, cx - r, cy + k, cx - r, cy,
                cx - r, cy - k, cx - k, cy - r, cx, cy - r,
                cx + k, cy - r, cx + r, cy - k, cx + r, cy)).encode())

    def step(self, n, title):
        """A numbered blue disc with the step heading beside it."""
        self.y -= 6
        cy = self.y + 5
        self.circle(MARGIN + 11, cy, 13)
        self.rgb(1, 1, 1)
        w = text_width(str(n), 13, True)
        self.ops.append(b"BT /F2 13.0 Tf "
                        + ("%.1f %.1f Td (" % (MARGIN + 11 - w / 2, cy - 4.5)).encode()
                        + esc(str(n)) + b") Tj ET")
        self.rgb(0.09, 0.10, 0.14)
        self.ops.append(b"BT /F2 17.0 Tf "
                        + ("%.1f %.1f Td (" % (MARGIN + 34, cy - 6)).encode()
                        + esc(title) + b") Tj ET")
        self.y -= 26

    def image(self, name, w, h, gap=16):
        """Place an image full text-width, scaled to keep its proportions."""
        draw_w = TEXT_W
        draw_h = draw_w * h / w
        self.y -= draw_h
        self.ops.append(("q %.2f 0 0 %.2f %.2f %.2f cm /%s Do Q"
                         % (draw_w, draw_h, MARGIN, self.y, name)).encode())
        self.y -= gap

    def rule(self, colour=(0.80, 0.82, 0.87)):
        self.y -= 4
        self.ops.append(("%.3f %.3f %.3f RG 0.9 w %.1f %.1f m %.1f %.1f l S"
                         % (colour[0], colour[1], colour[2],
                            MARGIN, self.y, PAGE_W - MARGIN, self.y)).encode())
        self.y -= 16

    def tip(self, s, size=11.5):
        """A soft grey note block."""
        lines = wrap(s, size, False, TEXT_W - 26)
        h = len(lines) * 15 + 16
        self.y -= h
        self.rgb(0.94, 0.95, 0.97)
        self.ops.append(("%.1f %.1f %.1f %.1f re f"
                         % (MARGIN, self.y, TEXT_W, h)).encode())
        self.rgb(0.05, 0.42, 0.95)
        self.ops.append(("%.1f %.1f %.1f %.1f re f"
                         % (MARGIN, self.y, 3.5, h)).encode())
        saved = self.y
        self.y = saved + h - 16
        for ln in lines:
            self.line(ln, size, False, x=MARGIN + 16, lead=15.0,
                      colour=(0.27, 0.30, 0.36))
        self.y = saved - 14

    def data(self):
        return b"\n".join(self.ops)


def build():
    images = []
    for i in range(1, 6):
        path = os.path.join(GUIDE, "step%d.jpg" % i)
        with open(path, "rb") as fh:
            blob = fh.read()
        w, h = Image.open(path).size
        images.append(("Im%d" % i, blob, w, h))

    pages = []

    # ---------------------------------------------------------------- page 1
    p = Page()
    p.y = PAGE_H - 72
    p.line("Winter Cabin", 30, True, colour=(0.09, 0.10, 0.14))
    p.line("How to put it on your Mac", 14, False, colour=(0.42, 0.45, 0.52))
    p.y -= 4
    p.para("Five steps, about two minutes. You do not need to know anything "
           "technical. Follow the pictures.", 12.5)
    p.rule()

    p.step(1, "Open the file you were sent")
    p.para("Find WinterCabin.dmg in your Downloads folder and double-click it. "
           "A small window opens.", 12.5, x=MARGIN + 34, width=TEXT_W - 34)
    p.image("Im1", images[0][2], images[0][3])

    p.step(2, "Drag it into Applications")
    p.para("Drag the Winter Cabin icon on top of the Applications folder next "
           "to it. That copies it onto your Mac. Then close the window.",
           12.5, x=MARGIN + 34, width=TEXT_W - 34)
    p.image("Im2", images[1][2], images[1][3])
    pages.append(p)

    # ---------------------------------------------------------------- page 2
    p = Page()
    p.step(3, "Open it, and expect to be stopped")
    p.para("Open your Applications folder and double-click Winter Cabin. Your "
           "Mac will refuse the first time and show this. Nothing is wrong: it "
           "just means the app did not come from Apple's store. Click Done.",
           12.5, x=MARGIN + 34, width=TEXT_W - 34)
    p.image("Im3", images[2][2], images[2][3])

    p.step(4, "Tell your Mac it is fine")
    p.para("Click the Apple logo at the top left, then System Settings, then "
           "Privacy & Security in the list. Scroll down to Security and click "
           "Open Anyway. Click Open when it asks again. You may need your Mac "
           "password. You only ever do this once.",
           12.5, x=MARGIN + 34, width=TEXT_W - 34)
    p.image("Im4", images[3][2], images[3][3])
    pages.append(p)

    # ---------------------------------------------------------------- page 3
    p = Page()
    p.step(5, "That is it. It is snowing.")
    p.para("Look at the very top right of your screen for a small snowflake. "
           "Everything lives in there.", 12.5, x=MARGIN + 34, width=TEXT_W - 34)
    p.image("Im5", images[4][2], images[4][3])

    p.line("What you can do", 15, True, colour=(0.09, 0.10, 0.14))
    p.y -= 2
    for a, b in [
        ("Snow", "turn it on or off, and choose Light, Medium or Blizzard."),
        ("Click the desktop", "drops a snowball. Stack three in one spot and "
                              "they turn into a snowman."),
        ("Send the plow now", "a little snowplow drives across and clears "
                              "everything away."),
        ("Quit Winter Cabin", "stops it and puts your own wallpaper back."),
    ]:
        p.rgb(0.09, 0.10, 0.14)
        p.ops.append(b"BT /F2 12.0 Tf "
                     + ("%.1f %.1f Td (" % (MARGIN, p.y)).encode()
                     + esc(a) + b") Tj ET")
        indent = text_width(a, 12.0, True) + 8
        p.para(b, 12.0, x=MARGIN + indent, width=TEXT_W - indent, lead=16.0)
        p.y -= 2

    p.y -= 6
    p.line("If it still will not open", 15, True, colour=(0.09, 0.10, 0.14))
    p.para("It was probably flagged when it was downloaded. Open the Terminal "
           "app, paste the line below, press Enter, then open Winter Cabin "
           "again.", 12.0)
    p.y -= 2
    p.rgb(0.95, 0.96, 0.97)
    p.y -= 26
    p.ops.append(("%.1f %.1f %.1f %.1f re f" % (MARGIN, p.y, TEXT_W, 26)).encode())
    p.rgb(0.12, 0.14, 0.20)
    p.ops.append(b"BT /F3 10.5 Tf "
                 + ("%.1f %.1f Td (" % (MARGIN + 10, p.y + 9)).encode()
                 + esc('xattr -dr com.apple.quarantine "/Applications/Winter Cabin.app"')
                 + b") Tj ET")
    p.y -= 18

    p.tip("Winter Cabin needs macOS 13 or newer. To check, click the Apple logo "
          "and choose About This Mac. It asks for no permissions, cannot see "
          "inside your windows, and never takes your clicks: your Dock and apps "
          "carry on working normally.")
    pages.append(p)

    # ------------------------------------------------------------ assemble
    n_pages = len(pages)
    first_page_obj = 3
    first_content_obj = first_page_obj + n_pages
    f1 = first_content_obj + n_pages
    f2, f3 = f1 + 1, f1 + 2
    first_img = f3 + 1

    xobjects = " ".join("/%s %d 0 R" % (images[i][0], first_img + i)
                        for i in range(len(images)))
    resources = ("<< /Font << /F1 %d 0 R /F2 %d 0 R /F3 %d 0 R >> "
                 "/XObject << %s >> >>" % (f1, f2, f3, xobjects))

    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join("%d 0 R" % (first_page_obj + i) for i in range(n_pages))
    objects.append(("<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, n_pages)).encode())
    for i in range(n_pages):
        objects.append((
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.0f %.0f] /Resources %s "
            "/Contents %d 0 R >>" % (PAGE_W, PAGE_H, resources, first_content_obj + i)
        ).encode())
    for p in pages:
        body = p.data()
        objects.append(b"<< /Length " + str(len(body)).encode() + b" >>\nstream\n"
                       + body + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                   b"/Encoding /WinAnsiEncoding >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
                   b"/Encoding /WinAnsiEncoding >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier "
                   b"/Encoding /WinAnsiEncoding >>")
    for name, blob, w, h in images:
        objects.append((
            "<< /Type /XObject /Subtype /Image /Width %d /Height %d "
            "/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode "
            "/Length %d >>" % (w, h, len(blob))).encode()
            + b"\nstream\n" + blob + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += ("%d 0 obj\n" % i).encode() + body + b"\nendobj\n"
    xref_at = len(out)
    total = len(objects) + 1
    out += ("xref\n0 %d\n" % total).encode() + b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += ("%010d 00000 n \n" % off).encode()
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (total, xref_at)).encode()
    return bytes(out)


def main():
    data = build()
    with open(OUT, "wb") as fh:
        fh.write(data)
    print("wrote", OUT, len(data), "bytes")


if __name__ == "__main__":
    main()
