#!/usr/bin/env python3
"""
Winter Cabin - procedural painterly night wallpaper.

Usage:  python render_wallpaper.py <scale> <outfile>
        scale 1.0 == 5120x3200.  0.25 gives a fast 1280x800 preview.
"""
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.25
OUT   = sys.argv[2] if len(sys.argv) > 2 else "preview.png"
# "live" renders the base plate for the animated layer: no baked smoke or flakes,
# and writes a manifest of anchor points the app animates on top of.
LIVE  = len(sys.argv) > 3 and sys.argv[3] == "live"

BW, BH = 5120, 3200
W, H = int(BW * SCALE), int(BH * SCALE)
S = W / 5120.0
def px(v): return max(1, int(round(v * S)))

rnd = random.Random(7731)

# ---------------------------------------------------------------- palette
SKY_TOP   = (0.082, 0.095, 0.205)
SKY_MID   = (0.112, 0.126, 0.268)
SKY_HOR   = (0.183, 0.192, 0.335)
MOONC     = (255, 246, 219)
AMBER     = (236, 150,  62)
AMBER_HOT = (250, 186,  96)
SNOW_HI   = (229, 234, 250)
SNOW      = (198, 206, 235)
SNOW_MID  = (163, 172, 212)
SNOW_SH   = (120, 130, 182)
SNOW_DEEP = ( 80,  90, 142)
WOOD_D    = ( 44,  30,  24)
WOOD      = ( 78,  52,  36)
WOOD_L    = (122,  81,  51)
PINE_F    = ( 46,  52,  90)
PINE_M    = ( 33,  38,  70)
NEEDLE    = ( 27,  26,  48)
LAKE      = ( 22,  26,  52)

def U(u): return u * W
def V(v): return v * H

# ---------------------------------------------------------------- helpers
def fbm1(n, octaves, seed, persistence=0.5):
    r = np.random.default_rng(seed)
    out = np.zeros(n, np.float64); amp = 1.0; tot = 0.0
    for o in range(octaves):
        pts = 2 ** (o + 1) + 1
        a = r.random(pts)
        x = np.linspace(0, pts - 1, n)
        i = np.floor(x).astype(int); f = x - i
        i2 = np.minimum(i + 1, pts - 1)
        f = f * f * (3 - 2 * f)
        out += amp * (a[i] * (1 - f) + a[i2] * f)
        tot += amp; amp *= persistence
    return out / tot

def fbm2(h, w, octaves, seed, persistence=0.5):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        n = 2 ** (o + 2)
        g = (r.random((n, n)) * 255).astype(np.uint8)
        up = np.asarray(Image.fromarray(g).resize((w, h), Image.BICUBIC), np.float32) / 255.0
        out += amp * up; tot += amp; amp *= persistence
    return out / tot

def layer():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)

def comp(canvas, im):
    a = np.asarray(im, np.float32) / 255.0
    al = a[..., 3:4]
    return canvas * (1 - al) + a[..., :3] * al

def glow(canvas, im, radius, strength, tint=None):
    g = im.filter(ImageFilter.GaussianBlur(max(1, radius * S)))
    a = np.asarray(g, np.float32) / 255.0
    rgb = a[..., :3] * a[..., 3:4] * strength
    if tint:
        rgb = rgb * np.array(tint, np.float32)
    return np.clip(canvas + rgb, 0, 1)

def C(c, a=255):
    return (int(c[0]), int(c[1]), int(c[2]), int(a))

def mix(c1, c2, t):
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))

# ================================================================ SKY
y  = np.linspace(0, 1, H, dtype=np.float32)[:, None]
xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
t1 = np.clip(y / 0.52, 0, 1); t2 = np.clip((y - 0.45) / 0.30, 0, 1)
sky = np.zeros((H, W, 3), np.float32)
for ch in range(3):
    a = SKY_TOP[ch] + (SKY_MID[ch] - SKY_TOP[ch]) * (t1 ** 0.85)
    sky[..., ch] = a + (SKY_HOR[ch] - a) * (t2 ** 1.6)
mg = np.exp(-(((xx - 0.875) ** 2) / 0.045 + ((y - 0.105) ** 2) / 0.028))
sky += mg[..., None] * np.array([0.080, 0.075, 0.058], np.float32)
# faint cloud banding for painterly depth
cl2 = fbm2(max(48, H // 10), max(48, W // 10), 4, 808)
cl2 = np.asarray(Image.fromarray((cl2 * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
                 np.float32) / 255.0
band = np.clip(1 - np.abs(y - 0.30) / 0.34, 0, 1) ** 2
sky += (cl2[..., None] - 0.5) * band[..., None] * np.array([0.050, 0.048, 0.072], np.float32)
canvas = np.clip(sky, 0, 1)

# ---- stars
st, d = layer()
for _ in range(1700):
    u = rnd.random(); v = rnd.random() * 0.62
    if rnd.random() > (0.28 + 0.72 * (1 - v / 0.62)):
        continue
    b = rnd.random() ** 2.0
    r = px(1.1 + b * 3.2)
    a = int(50 + b * 190)
    col = mix((212, 221, 255), (255, 250, 232), rnd.random())
    d.ellipse([U(u) - r, V(v) - r, U(u) + r, V(v) + r], fill=C(col, a))
for _ in range(12):
    u = rnd.random(); v = rnd.random() * 0.42
    r = px(9 + rnd.random() * 15); w = px(1.6)
    d.line([U(u) - r, V(v), U(u) + r, V(v)], fill=(255, 252, 240, 110), width=w)
    d.line([U(u), V(v) - r, U(u), V(v) + r], fill=(255, 252, 240, 110), width=w)
canvas = comp(canvas, st)
canvas = glow(canvas, st, 7, 0.50)

# ---- moon (crescent) + halo
mu, mv, mr = 0.872, 0.102, 0.050
mo, d = layer()
d.ellipse([U(mu) - V(mr), V(mv) - V(mr), U(mu) + V(mr), V(mv) + V(mr)], fill=C(MOONC, 255))
cut = Image.new("L", (W, H), 0)
ImageDraw.Draw(cut).ellipse([U(mu) - V(mr) - V(mr) * 0.58, V(mv) - V(mr) * 1.06,
                             U(mu) + V(mr) - V(mr) * 0.58, V(mv) + V(mr) * 0.94], fill=255)
cut = cut.filter(ImageFilter.GaussianBlur(px(5)))
al = np.asarray(mo, np.uint8).copy()
al[..., 3] = (al[..., 3].astype(np.float32) * (1 - np.asarray(cut, np.float32) / 255.0)).astype(np.uint8)
mo = Image.fromarray(al)
canvas = glow(canvas, mo, 180, 0.30, (1.0, 0.96, 0.80))
canvas = glow(canvas, mo, 55,  0.42, (1.0, 0.97, 0.86))
canvas = comp(canvas, mo)

# ================================================================ MOUNTAINS
YY = np.arange(H, dtype=np.float32)[:, None]

def ridgeline(seed, base_v, height, lo=0.20, hi=1.0, s_lo=0.05, s_hi=0.14):
    """Angular ridge: random summits joined by straight slopes, plus fine noise."""
    r = random.Random(seed)
    xs = [-0.08]; ys = [base_v - height * r.uniform(lo, hi * 0.55)]
    x = -0.08
    while x < 1.08:
        x += r.uniform(s_lo, s_hi)
        xs.append(x); ys.append(base_v - height * r.uniform(lo, hi))
    arr = np.interp(np.linspace(0, 1, W), xs, ys)
    arr = arr + (fbm1(W, 7, seed + 3) - 0.5) * height * 0.085
    return arr.astype(np.float32)

def mountain_np(canvas, ridge, band, body, snowc):
    ry = (ridge * H)[None, :]
    depth = YY - ry
    alpha = np.clip(depth + 1.0, 0, 1)
    sl = np.gradient(ridge * H).astype(np.float32)
    lit = np.clip(-sl / (W * 0.0024), -1, 1)[None, :]          # right-facing slopes catch light
    bandpx = np.maximum(1.0, band * H)[None, :]
    t = np.clip(1 - depth / bandpx, 0, 1) ** 0.80
    t = t * (0.38 + 0.62 * (lit * 0.5 + 0.5))
    b = np.array(body,  np.float32) / 255.0
    s = np.array(snowc, np.float32) / 255.0
    col = b[None, None, :] + (s - b)[None, None, :] * t[..., None]
    return canvas * (1 - alpha[..., None]) + col * alpha[..., None]

SKY_HOR_C = (47, 49, 86)
for (sd, bv, hgt, bd, sn, bk, lo, hi, sl_, sh_) in [
        (11, 0.568, 0.300, mix(SKY_HOR_C, SNOW_SH, 0.24), mix(SNOW_SH, SKY_HOR_C, 0.34),
         0.034, 0.16, 1.00, 0.060, 0.165),
        (23, 0.614, 0.250, (44, 49, 88), (104, 114, 166), 0.030, 0.20, 1.00, 0.050, 0.140),
        (37, 0.652, 0.165, (31, 36, 71), ( 85,  94, 144), 0.024, 0.24, 1.00, 0.042, 0.115)]:
    rl = ridgeline(sd, bv, hgt, lo, hi, sl_, sh_)
    bandw = (bk * (0.40 + 0.95 * fbm1(W, 4, sd + 77))).astype(np.float32)
    canvas = mountain_np(canvas, rl, bandw, bd, sn)

# ================================================================ PINES
def pine(d, x, ybase, h, w, col, snow=None, tiers=6):
    trunk_w = max(1, px(w * 0.09))
    d.line([x, ybase, x, ybase - h * 0.12], fill=C(mix(col, (0, 0, 0), 0.3)), width=trunk_w)
    for i in range(tiers):
        t = i / (tiers - 1.0)
        cy = ybase - h * (0.08 + 0.92 * t)
        hw = w * (1.0 - 0.80 * t) * 0.5
        th = h * 0.26 * (1.0 - 0.45 * t)
        d.polygon([(x - hw, cy), (x + hw, cy), (x, cy - th)], fill=C(col))
        if snow:
            d.polygon([(x - hw * 0.88, cy - th * 0.06), (x + hw * 0.22, cy - th * 0.06),
                       (x, cy - th * 0.80)], fill=C(snow))

def forest(canvas, v_base, count, hmin, hmax, col, snowc, u0=0.0, u1=1.0, seed=1, blur=0):
    lay, d = layer()
    r = random.Random(seed)
    for u in sorted(r.uniform(u0, u1) for _ in range(count)):
        h = V(r.uniform(hmin, hmax))
        pine(d, U(u), V(v_base + r.uniform(-0.006, 0.006)), h, h * r.uniform(0.34, 0.46),
             col, snowc if r.random() < 0.8 else None, tiers=r.randint(5, 7))
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(px(blur)))
    return comp(canvas, lay)

canvas = forest(canvas, 0.662, 100, 0.030, 0.066, PINE_F, mix(PINE_F, SNOW_MID, 0.45),
                0.42, 1.02, seed=4, blur=2)

# ================================================================ FAR VILLAGE
vil, d = layer()
lights, dl = layer()
vb = 0.682
def house(x, y, w, h, roof=0.55, win=2):
    d.polygon([(x, y), (x + w, y), (x + w, y - h), (x, y - h)], fill=C((36, 33, 52)))
    d.polygon([(x - w * 0.09, y - h), (x + w * 1.09, y - h), (x + w * 0.5, y - h * (1 + roof))],
              fill=C(mix(SNOW_SH, SNOW_HI, 0.22)))
    for i in range(win):
        wx = x + w * (0.22 + 0.45 * i); wy = y - h * 0.62
        dl.rectangle([wx, wy, wx + w * 0.20, wy + h * 0.34], fill=C(AMBER_HOT))

r = random.Random(88)
for _ in range(30):
    u = r.uniform(0.600, 0.950); w = V(r.uniform(0.016, 0.028))
    house(U(u), V(vb + r.uniform(-0.004, 0.006)), w, w * r.uniform(0.62, 0.85), win=r.randint(1, 2))
cx, cy = U(0.806), V(vb - 0.002); cw = V(0.028)
house(cx, cy, cw * 1.5, cw * 0.95, 0.5, 2)
tw = cw * 0.44
d.rectangle([cx + cw * 0.5, cy - cw * 2.30, cx + cw * 0.5 + tw, cy - cw * 0.3], fill=C((40, 36, 56)))
d.polygon([(cx + cw * 0.5 - tw * 0.20, cy - cw * 2.30), (cx + cw * 0.5 + tw * 1.20, cy - cw * 2.30),
           (cx + cw * 0.5 + tw * 0.5, cy - cw * 3.25)], fill=C(mix(SNOW_SH, SNOW_HI, 0.25)))
dl.rectangle([cx + cw * 0.5 + tw * 0.28, cy - cw * 2.00,
              cx + cw * 0.5 + tw * 0.72, cy - cw * 1.60], fill=C(AMBER_HOT))
canvas = comp(canvas, vil)
canvas = glow(canvas, lights, 28, 0.80, (1.0, 0.70, 0.38))
canvas = glow(canvas, lights, 8, 0.60)
canvas = comp(canvas, lights)

canvas = forest(canvas, 0.700, 80, 0.026, 0.052, PINE_M, mix(PINE_M, SNOW_MID, 0.38),
                0.44, 1.02, seed=9, blur=1)

# ================================================================ LAKE
lake_top = 0.712
lk, d = layer()
f = fbm1(W, 5, 303)
step = max(1, int(3 * S))
shore = [(x, V(lake_top + (f[x] - 0.5) * 0.006)) for x in range(0, W, step)]
d.polygon([(U(0.38), V(1.02))] + shore + [(W, V(lake_top)), (W, V(1.02))], fill=C(LAKE))
canvas = comp(canvas, lk)

rf, d = layer()
r = random.Random(12)
cols = [(U(u), AMBER_HOT) for u in [0.610, 0.642, 0.672, 0.699, 0.728, 0.755, 0.780,
                                    0.806, 0.828, 0.853, 0.877, 0.905, 0.931]]
cols.append((U(mu), MOONC))
for (x, col) in cols:
    depth = V(0.175)
    yy = V(lake_top)
    while yy < V(lake_top + 0.20):
        t = min(1.0, max(0.0, (yy - V(lake_top)) / depth))
        a = int(165 * (1 - t) ** 1.4 * r.uniform(0.45, 1.0))
        wdt = V(0.0035) * (1 + t * 3.6) * r.uniform(0.6, 1.5)
        hgt = max(1, V(0.0016) * r.uniform(0.6, 1.6))
        ox = r.uniform(-1, 1) * V(0.004) * t * 4.5
        d.rectangle([x - wdt + ox, yy, x + wdt + ox, yy + hgt], fill=C(col, a))
        yy += hgt + V(0.0020) * r.uniform(0.7, 2.2)
rf = rf.filter(ImageFilter.GaussianBlur(px(3)))
canvas = comp(canvas, rf)
canvas = glow(canvas, rf, 22, 0.40, (1.0, 0.74, 0.42))

# ================================================================ SNOW GROUND
def drift(d, v_left, v_right, amp, col, seed, oct_=6):
    f = fbm1(W, oct_, seed, 0.55)
    base = np.linspace(v_left, v_right, W)
    ys = V(1) * base - (f - 0.5) * V(amp)
    pts = [(x, ys[x]) for x in range(0, W, max(1, int(3 * S)))]
    d.polygon([(0, H)] + pts + [(W - 1, ys[-1]), (W, H)], fill=C(col))

gr, d = layer()
drift(d, 0.775, 0.905, 0.030, SNOW_DEEP, 501)
drift(d, 0.812, 0.930, 0.034, SNOW_SH,   502)
drift(d, 0.862, 0.952, 0.046, SNOW_MID,  503)
drift(d, 0.928, 0.975, 0.050, SNOW,      504)
canvas = comp(canvas, gr)

mn, d = layer()
r = random.Random(61)
for _ in range(110):
    u = r.uniform(-0.02, 1.02)
    v = r.uniform(0.80 + u * 0.09, 1.03)
    w = V(r.uniform(0.03, 0.14)); h = w * r.uniform(0.20, 0.40)
    t = min(1.0, max(0.0, (v - 0.80) / 0.23))
    d.ellipse([U(u) - w, V(v) - h, U(u) + w, V(v) + h],
              fill=C(mix(SNOW_SH, SNOW_HI, 0.30 + 0.60 * t), 140))
mn = mn.filter(ImageFilter.GaussianBlur(px(38)))
canvas = comp(canvas, mn)

warm = np.exp(-(((xx - 0.285) ** 2) / 0.038 + ((y - 0.855) ** 2) / 0.022))
canvas = np.clip(canvas + warm[..., None] * np.array([0.215, 0.120, 0.042], np.float32), 0, 1)
warm2 = np.exp(-(((xx - 0.175) ** 2) / 0.010 + ((y - 0.800) ** 2) / 0.0045))
canvas = np.clip(canvas + warm2[..., None] * np.array([0.150, 0.082, 0.026], np.float32), 0, 1)

# warm / cool mottling so the snow is not one flat value
mot = fbm2(max(48, H // 12), max(48, W // 12), 5, 616)
mot = np.asarray(Image.fromarray((mot * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
                 np.float32) / 255.0
snowmask = np.clip((y - 0.735) / 0.090, 0, 1)
canvas = np.clip(canvas + ((mot - 0.5) * snowmask)[..., None]
                 * np.array([0.070, 0.044, 0.016], np.float32), 0, 1)

# contact shadows where things meet the snow
sdw, d = layer()
def soft_shadow(cu, cv, ru, rv, a=130):
    d.ellipse([U(cu - ru), V(cv - rv), U(cu + ru), V(cv + rv)], fill=(16, 18, 46, a))
soft_shadow(0.195, 0.782, 0.170, 0.024, 140)
soft_shadow(0.400, 0.806, 0.080, 0.015, 115)
soft_shadow(0.026, 0.962, 0.052, 0.022, 105)
sdw = sdw.filter(ImageFilter.GaussianBlur(px(44)))
canvas = comp(canvas, sdw)

# ================================================================ CABIN
cab, d = layer()
cl,  dl = layer()

GY = 0.772
d.rectangle([U(0.113), V(0.345), U(0.152), V(0.470)], fill=C((50, 38, 36)))
d.rectangle([U(0.108), V(0.337), U(0.157), V(0.358)], fill=C((60, 46, 42)))
d.rectangle([U(0.106), V(0.327), U(0.159), V(0.345)], fill=C(mix(SNOW_HI, SNOW, 0.4)))

apex  = (U(0.196), V(0.356))
eaveL = (U(0.034), V(0.556)); eaveR = (U(0.358), V(0.556))
d.polygon([eaveL, eaveR, apex], fill=C(WOOD))
d.polygon([(U(0.050), V(0.556)), (U(0.342), V(0.556)), (U(0.196), V(0.392))], fill=C(WOOD_L))
d.rectangle([U(0.052), V(0.556), U(0.330), V(GY)], fill=C(WOOD))
for i in range(10):
    yy = V(0.566 + i * 0.0235)
    d.line([U(0.052), yy, U(0.330), yy], fill=C(WOOD_D, 140), width=px(5))
d.rectangle([U(0.300), V(0.556), U(0.330), V(GY)], fill=C(mix(WOOD, (0, 0, 0), 0.20)))
# front door with a glowing fanlight
d.rectangle([U(0.276), V(0.618), U(0.322), V(0.772)], fill=C(mix(WOOD_D, WOOD, 0.35)))
d.rectangle([U(0.276), V(0.618), U(0.322), V(0.772)], outline=C(WOOD_D), width=px(8))
dl.rectangle([U(0.284), V(0.628), U(0.314), V(0.652)], fill=C(AMBER_HOT))
d.ellipse([U(0.314) - px(7), V(0.700) - px(7), U(0.314) + px(7), V(0.700) + px(7)],
          fill=C((188, 150, 92)))

d.polygon([(U(0.014), V(0.576)), apex, (U(0.210), V(0.348)), (U(0.030), V(0.586))], fill=C(WOOD_D))
d.polygon([apex, (U(0.380), V(0.576)), (U(0.372), V(0.590)), (U(0.186), V(0.352))], fill=C(WOOD_D))
d.polygon([(U(0.004), V(0.588)), (U(0.196), V(0.330)), (U(0.390), V(0.588)),
           (U(0.372), V(0.600)), (U(0.196), V(0.366)), (U(0.020), V(0.600))], fill=C(SNOW_HI))
r = random.Random(33)
for i in range(52):
    t = i / 51.0
    if t < 0.5:
        k = t / 0.5; ux = 0.004 + 0.192 * k; uy = 0.588 - 0.258 * k
    else:
        k = (t - 0.5) / 0.5; ux = 0.196 + 0.194 * k; uy = 0.330 + 0.258 * k
    rr = V(r.uniform(0.011, 0.023))
    d.ellipse([U(ux) - rr, V(uy) - rr * 0.85, U(ux) + rr, V(uy) + rr * 0.90], fill=C(SNOW_HI))
for i in range(26):                                      # eave drips
    k = r.random()
    side = r.random() < 0.5
    ux = (0.010 + 0.182 * k) if side else (0.200 + 0.186 * k)
    uy = (0.596 - 0.252 * k) if side else (0.344 + 0.252 * k)
    rr = V(r.uniform(0.005, 0.011))
    d.ellipse([U(ux) - rr, V(uy) - rr * 0.3, U(ux) + rr, V(uy) + rr * 1.7], fill=C(SNOW))

for i in range(30):                                      # icicles along the eaves
    k = r.random()
    side = r.random() < 0.5
    ux = (0.012 + 0.180 * k) if side else (0.202 + 0.182 * k)
    uy = (0.596 - 0.252 * k) if side else (0.346 + 0.252 * k)
    ln = V(r.uniform(0.012, 0.034)); wd = V(r.uniform(0.0035, 0.0065))
    d.polygon([(U(ux) - wd, V(uy)), (U(ux) + wd, V(uy)), (U(ux), V(uy) + ln)],
              fill=C(mix(SNOW, SNOW_HI, 0.5 + 0.5 * r.random()), 235))

def window(u0, v0, u1, v1, mull=True):
    dl.rectangle([U(u0), V(v0), U(u1), V(v1)], fill=C(AMBER))
    dl.rectangle([U(u0) + px(14), V(v0) + px(14), U(u1) - px(14), V(v1) - px(14)],
                 fill=C(AMBER_HOT))
    d.rectangle([U(u0) - px(8), V(v0) - px(8), U(u1) + px(8), V(v1) + px(8)],
                outline=C(WOOD_D), width=px(10))
    if mull:
        mx = (U(u0) + U(u1)) / 2; my = (V(v0) + V(v1)) / 2
        d.line([mx, V(v0), mx, V(v1)], fill=C(WOOD_D), width=px(8))
        d.line([U(u0), my, U(u1), my], fill=C(WOOD_D), width=px(8))

window(0.158, 0.418, 0.232, 0.500)
window(0.064, 0.600, 0.148, 0.712)
window(0.176, 0.604, 0.262, 0.714)
for (a, b, v) in [(0.150, 0.240, 0.410), (0.056, 0.156, 0.592), (0.168, 0.270, 0.596)]:
    d.rounded_rectangle([U(a), V(v) - px(18), U(b), V(v) + px(4)], radius=px(10), fill=C(SNOW_HI))

d.polygon([(U(0.300), V(0.560)), (U(0.470), V(0.596)), (U(0.470), V(0.612)), (U(0.300), V(0.578))],
          fill=C(WOOD_D))
d.polygon([(U(0.296), V(0.548)), (U(0.476), V(0.586)), (U(0.472), V(0.602)), (U(0.292), V(0.566))],
          fill=C(SNOW_HI))
for pu in (0.330, 0.452):
    d.rectangle([U(pu), V(0.588), U(pu) + px(24), V(GY)], fill=C(WOOD_D))
d.rectangle([U(0.330), V(0.692), U(0.466), V(0.706)], fill=C(WOOD))
d.rectangle([U(0.330), V(0.688), U(0.466), V(0.696)], fill=C(SNOW))
for i in range(7):
    bx = U(0.338 + i * 0.019)
    d.rectangle([bx, V(0.702), bx + px(11), V(GY)], fill=C(WOOD_D))

for i in range(4):                                       # steps: wood with snow edge
    yy = 0.770 + i * 0.015
    x0, x1 = U(0.338 - i * 0.012), U(0.452 + i * 0.012)
    d.rectangle([x0, V(yy), x1, V(yy + 0.016)], fill=C(mix(WOOD, WOOD_D, 0.3)))
    d.rectangle([x0, V(yy), x1, V(yy + 0.005)], fill=C(mix(SNOW, SNOW_HI, 0.6 - i * 0.12)))

for (lu, lv) in [(0.287, 0.620), (0.395, 0.630), (0.466, 0.642)]:
    lw = V(0.010)
    d.line([U(lu), V(lv - 0.030), U(lu), V(lv - 0.006)], fill=C(WOOD_D), width=px(5))
    dl.rounded_rectangle([U(lu) - lw, V(lv), U(lu) + lw, V(lv + 0.028)], radius=px(6), fill=C(AMBER))
    d.rounded_rectangle([U(lu) - lw, V(lv), U(lu) + lw, V(lv + 0.028)], radius=px(6),
                        outline=C(WOOD_D), width=px(6))

bulbs = []
for i in range(34):
    t = i / 33.0
    if t < 0.5:
        k = t / 0.5; ux = 0.016 + 0.180 * k; uy = 0.600 - 0.248 * k + 0.024 * math.sin(k * math.pi)
    else:
        k = (t - 0.5) / 0.5; ux = 0.196 + 0.188 * k; uy = 0.352 + 0.248 * k + 0.024 * math.sin(k * math.pi)
    bulbs.append((ux, uy))
for i in range(12):
    t = i / 11.0
    bulbs.append((0.302 + 0.168 * t, 0.574 + 0.036 * t + 0.014 * math.sin(t * math.pi)))
prev = None
for (ux, uy) in bulbs:
    if prev:
        d.line([U(prev[0]), V(prev[1]), U(ux), V(uy)], fill=C((40, 32, 28), 170), width=px(3))
    prev = (ux, uy)
    rr = px(8)
    dl.ellipse([U(ux) - rr, V(uy) - rr, U(ux) + rr, V(uy) + rr], fill=C(AMBER_HOT))

canvas = comp(canvas, cab)
canvas = glow(canvas, cl, 160, 0.42, (1.0, 0.58, 0.24))
canvas = glow(canvas, cl, 45,  0.46, (1.0, 0.70, 0.36))
canvas = glow(canvas, cl, 12,  0.40, (1.0, 0.85, 0.62))
canvas = comp(canvas, cl)

sm, d = layer()
r = random.Random(205)
sx, sy = U(0.1325), V(0.327)
if not LIVE:
    for i in range(80):
        t = i / 79.0
        rr = V(0.009 + t * 0.034)
        ox = math.sin(t * 5.0) * V(0.034) * t + t * V(0.062)
        oy = -t * V(0.250)
        d.ellipse([sx + ox - rr, sy + oy - rr, sx + ox + rr, sy + oy + rr],
                  fill=(208, 214, 238, int(95 * (1 - t) ** 1.2)))
    sm = sm.filter(ImageFilter.GaussianBlur(px(24)))
    canvas = comp(canvas, sm)

# ================================================================ FENCE + JETTY
fjs, d = layer()
for i in range(8):
    fx = 0.432 + i * 0.0355
    d.ellipse([U(fx) - V(0.012), V(0.862 - i * 0.0052 + 0.026),
               U(fx) + V(0.020), V(0.862 - i * 0.0052 + 0.036)], fill=(16, 18, 46, 120))
fjs = fjs.filter(ImageFilter.GaussianBlur(px(16)))
canvas = comp(canvas, fjs)

fj, d = layer()
# jetty, out on the water
d.polygon([(U(0.772), V(0.772)), (U(0.930), V(0.752)), (U(0.936), V(0.764)), (U(0.776), V(0.786))],
          fill=C(WOOD))
d.polygon([(U(0.772), V(0.770)), (U(0.930), V(0.750)), (U(0.932), V(0.757)), (U(0.774), V(0.777))],
          fill=C(SNOW))
for i in range(5):
    jx = 0.792 + i * 0.030
    d.rectangle([U(jx), V(0.768), U(jx) + px(13), V(0.800)], fill=C(WOOD_D))

# fence, down in the foreground snow
fy = 0.862
for i in range(8):
    fx = 0.432 + i * 0.0355
    tilt = fy - i * 0.0052
    d.rectangle([U(fx), V(tilt - 0.046), U(fx) + px(24), V(tilt + 0.028)], fill=C(WOOD))
    d.rectangle([U(fx) - px(2), V(tilt - 0.049), U(fx) + px(26), V(tilt - 0.0435)], fill=C(SNOW))
    d.rectangle([U(fx) + px(16), V(tilt - 0.046), U(fx) + px(24), V(tilt + 0.028)],
                fill=C(WOOD_D, 170))
for rv in (0.028, 0.006):
    y0 = fy - rv; y1 = fy - rv - 0.0364
    d.polygon([(U(0.432), V(y0)), (U(0.690), V(y1)), (U(0.690), V(y1 + 0.009)),
               (U(0.432), V(y0 + 0.009))], fill=C(WOOD_L))
    d.polygon([(U(0.432), V(y0)), (U(0.690), V(y1)), (U(0.690), V(y1 + 0.0035)),
               (U(0.432), V(y0 + 0.0035))], fill=C(SNOW))
canvas = comp(canvas, fj)

fp, d = layer()
r = random.Random(900)
for i in range(15):
    t = i / 14.0
    u = 0.400 + t * 0.200; v = 0.806 + t * 0.108
    rr = V(0.0050 + t * 0.0040)
    off = (-1 if i % 2 else 1) * rr * 1.5
    d.ellipse([U(u) + off - rr, V(v) - rr * 0.60, U(u) + off + rr, V(v) + rr * 0.60],
              fill=C(SNOW_SH, 185))
fp = fp.filter(ImageFilter.GaussianBlur(px(5)))
canvas = comp(canvas, fp)

# ================================================================ SNOW-LADEN BOUGHS
def bough(d, x0, y0, length, droop, thick, seed, dir=1, wiggle=3.0, tilt=0.0):
    """A limb: dark needle mass underneath, irregular snow load lying on top."""
    r = random.Random(seed)
    n = 70
    path = []
    for i in range(n):
        t = i / (n - 1.0)
        ux = x0 + dir * length * t
        uy = y0 + tilt * t + droop * (t ** 1.8) + 0.012 * math.sin(t * wiggle)
        path.append((ux, uy, t))

    nz_t = fbm1(n, 6, seed + 1, 0.55)      # ragged top of the foliage
    nz_b = fbm1(n, 5, seed + 2, 0.55)      # ragged underside
    nz_s = fbm1(n, 7, seed + 3, 0.60)      # bumpy snow thickness

    top, bot, snow_bot, lit_bot = [], [], [], []
    for i, (ux, uy, t) in enumerate(path):
        k = thick * (1 - 0.46 * t)
        up   = k * (0.75 + 1.10 * nz_t[i])
        down = k * (1.40 + 2.60 * nz_b[i])
        ty = V(uy - up)
        sb = V(uy - up + k * (0.20 + 2.10 * nz_s[i] ** 1.4))
        top.append((U(ux), ty))
        bot.append((U(ux), V(uy + down)))
        snow_bot.append((U(ux), sb))
        lit_bot.append((U(ux), ty + (sb - ty) * 0.48))

    d.polygon(top + bot[::-1], fill=C(NEEDLE))                     # needle mass
    # needle tips breaking the underside
    for i in range(0, n, 2):
        if r.random() < 0.55:
            k = thick * (1 - 0.46 * path[i][2])
            ln = V(k) * r.uniform(0.8, 2.4)
            d.line([bot[i][0], bot[i][1] - V(k) * 0.3,
                    bot[i][0] + r.uniform(-0.7, 0.7) * ln, bot[i][1] + ln],
                   fill=C(NEEDLE), width=px(r.uniform(5, 12)))
    d.polygon(top + snow_bot[::-1], fill=C(SNOW_MID))              # snow load
    d.polygon(top + lit_bot[::-1], fill=C(SNOW_HI))                # lit crown

    # a couple of side twigs dropping from the limb
    for _ in range(3):
        k0 = r.randint(10, n - 12)
        (ux, uy, t) = path[k0]
        tl = length * r.uniform(0.08, 0.20)
        m = 16
        tt, tb = [], []
        for j in range(m):
            s = j / (m - 1.0)
            vx = ux + dir * tl * s
            vy = uy + 0.060 * s * s
            k = thick * 0.48 * (1 - 0.5 * s)
            tt.append((U(vx), V(vy - k * 0.8)))
            tb.append((U(vx), V(vy + k * 1.5)))
        d.polygon(tt + tb[::-1], fill=C(NEEDLE))
        d.polygon(tt + [(x, yv + V(thick * 0.30)) for (x, yv) in tt][::-1],
                  fill=C(mix(SNOW, SNOW_HI, 0.5)))

tr, d = layer()
# trunk with an irregular, tapering silhouette
r = random.Random(555)
nseg = 48
edge = fbm1(nseg, 5, 771)
left, right = [], []
for i in range(nseg):
    t = i / (nseg - 1.0)
    vy = -0.03 + t * 1.07
    half = 0.0185 + 0.020 * t                       # wider toward the bottom
    cxu = 0.021 + 0.009 * (1 - t) - 0.004 * math.sin(t * 2.2)
    j = (edge[i] - 0.5) * 0.009
    left.append((U(cxu - half + j * 0.5), V(vy)))
    right.append((U(cxu + half + j), V(vy)))
d.polygon(left + right[::-1], fill=C((34, 25, 20)))
for _ in range(40):                                  # bark strokes
    t = r.random()
    uy0 = -0.03 + t * 1.07
    half = 0.0185 + 0.020 * t
    cxu = 0.021 + 0.009 * (1 - t)
    ux0 = cxu - half + r.random() * half * 2
    d.line([U(ux0), V(uy0), U(ux0 + r.uniform(-0.003, 0.003)), V(uy0 + r.uniform(0.05, 0.17))],
           fill=C((58, 41, 31), 150), width=px(r.uniform(4, 11)))
# lit right edge
band = [(right[i][0] - V(0.008), right[i][1]) for i in range(nseg)]
d.polygon(band + right[::-1], fill=C((88, 62, 42), 150))
# snow caught on the upper-left of the trunk
for i in range(0, nseg, 5):
    if r.random() < 0.45:
        w = px(r.uniform(14, 34))
        d.ellipse([left[i][0] - w * 0.4, left[i][1] - w * 0.5,
                   left[i][0] + w * 1.1, left[i][1] + w * 0.5],
                  fill=C(mix(SNOW_MID, SNOW_HI, r.random()), 220))

for (bx, by, bl, bd_, bt, sd, tl) in [
        (0.232, -0.046, 0.200, 0.045, 0.034, 108,  0.030),
        (0.150, -0.030, 0.245, 0.050, 0.040, 109, -0.018),
        (0.086, -0.044, 0.280, 0.052, 0.046, 110,  0.055),
        (0.040, -0.020, 0.300, 0.058, 0.050, 105,  0.010),
        (0.042,  0.030, 0.255, 0.072, 0.048, 101,  0.048),
        (0.044,  0.090, 0.210, 0.082, 0.042, 102, -0.022),
        (0.046,  0.138, 0.165, 0.078, 0.035, 104,  0.040),
        (0.048,  0.198, 0.120, 0.066, 0.028, 107, -0.010),
        (0.112,  0.010, 0.235, 0.060, 0.044, 111,  0.038),
        (0.190, -0.018, 0.195, 0.048, 0.036, 112, -0.012),
        (0.062,  0.062, 0.240, 0.068, 0.046, 113,  0.026)]:
    bough(d, bx, by, bl, bd_, bt, sd, tilt=tl, wiggle=2.2 + (sd % 5) * 0.7)
canvas = comp(canvas, tr)

# right-edge snowy conifer - kept clear of the moon
rc, d = layer()
for (by, bl, bt, sd, tl) in [(0.238, 0.165, 0.046, 201,  0.030),
                             (0.336, 0.150, 0.042, 202, -0.016),
                             (0.432, 0.132, 0.037, 203,  0.034),
                             (0.530, 0.112, 0.032, 204, -0.008),
                             (0.624, 0.094, 0.027, 205,  0.026)]:
    bough(d, 1.045, by, bl, 0.046, bt, sd, dir=-1, tilt=tl, wiggle=2.0 + (sd % 4) * 0.8)
canvas = comp(canvas, rc)

sh, d = layer()
r = random.Random(77)
for _ in range(24):
    u = r.uniform(0.02, 0.98); v = r.uniform(0.855, 0.918)
    if 0.28 < u < 0.52 and v < 0.89:
        continue
    for _ in range(r.randint(3, 6)):
        ln = V(r.uniform(0.016, 0.040))
        d.line([U(u), V(v), U(u) + r.uniform(-0.6, 0.6) * ln, V(v) - ln],
               fill=C((34, 30, 54), 205), width=px(r.uniform(3, 7)))
canvas = comp(canvas, sh)

# ================================================================ ATMOSPHERE
if not LIVE:
    fl, d = layer()
    r = random.Random(1234)
    for _ in range(380):
        u = r.random(); v = r.random()
        rr = px(r.uniform(2, 7))
        d.ellipse([U(u) - rr, V(v) - rr, U(u) + rr, V(v) + rr],
                  fill=(255, 255, 255, int(r.uniform(25, 100))))
    fl = fl.filter(ImageFilter.GaussianBlur(px(2)))
    canvas = comp(canvas, fl)

haze = np.clip(1 - np.abs(y - 0.675) / 0.13, 0, 1) ** 2
canvas = np.clip(canvas + haze[..., None] * np.array([0.028, 0.030, 0.050], np.float32), 0, 1)

lum = canvas @ np.array([0.2126, 0.7152, 0.0722], np.float32)
bright = np.clip((lum - 0.62) / 0.38, 0, 1)[..., None] * canvas
bi = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8))
for (rad, amt) in ((px(12), 0.26), (px(48), 0.18), (px(150), 0.11)):
    b = np.asarray(bi.filter(ImageFilter.GaussianBlur(rad)), np.float32) / 255.0
    canvas = np.clip(canvas + b * amt, 0, 1)

# ---- hand-painted brush pass: short strokes that pick up the colour beneath
def brush_pass(canvas, count, seed, len_lo, len_hi, wid_lo, wid_hi, alpha, jit):
    base = (np.clip(canvas, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(base)
    dd = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed)
    FN = 160
    ang_f = fbm2(FN, FN, 4, seed + 11)
    for _ in range(count):
        x = r.randrange(W); yy_ = r.randrange(H)
        c = base[yy_, x]
        j = r.uniform(-jit, jit)
        col = (int(min(255, max(0, c[0] + j))),
               int(min(255, max(0, c[1] + j * 0.92))),
               int(min(255, max(0, c[2] + j * 1.12))))
        a = ang_f[min(FN - 1, yy_ * FN // H), min(FN - 1, x * FN // W)]
        ang = (a - 0.5) * 1.45
        ln = r.uniform(len_lo, len_hi) * S
        dx = math.cos(ang) * ln; dy = math.sin(ang) * ln * 0.38
        aa = int(alpha * (0.45 if yy_ < H * 0.42 else 1.0))
        dd.line([x - dx, yy_ - dy, x + dx, yy_ + dy],
                fill=(col[0], col[1], col[2], aa),
                width=max(1, int(r.uniform(wid_lo, wid_hi) * S)))
    return np.asarray(img, np.float32) / 255.0

# stroke area scales with S^2 and so does the frame, so the count stays fixed
canvas = brush_pass(canvas, 95000, 4001, 14, 36, 6, 15, 58, 15)
canvas = brush_pass(canvas, 50000, 4002,  6, 16, 3,  9, 42, 11)

# painterly texture
tex = fbm2(max(64, H // 5), max(64, W // 5), 6, 4242)
tex = np.asarray(Image.fromarray((tex * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
                 np.float32) / 255.0
canvas *= (0.915 + 0.170 * tex[..., None])
grain = np.random.default_rng(5).normal(0, 0.010, (H, W, 1)).astype(np.float32)
canvas = np.clip(canvas + grain, 0, 1)

vx = (xx - 0.5) * 2; vy = (y - 0.52) * 2
vig = 1 - 0.32 * np.clip((vx ** 2 * 0.75 + vy ** 2 * 0.85), 0, 1) ** 1.4
canvas *= vig[..., None]

l2 = (canvas @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
canvas = canvas + (1 - l2) * np.array([-0.014, -0.005, 0.034], np.float32) \
                + l2 * np.array([0.024, 0.009, -0.016], np.float32)
canvas = np.clip((np.clip(canvas, 0, 1) - 0.5) * 1.085 + 0.5 + 0.010, 0, 1)

img = Image.fromarray((canvas * 255).astype(np.uint8))
mf = img.filter(ImageFilter.ModeFilter(size=max(3, int(7 * S) | 1)))
img = Image.blend(img, mf, 0.16)
img = img.filter(ImageFilter.UnsharpMask(radius=px(4), percent=60, threshold=3))
img.save(OUT, "PNG")
print("wrote", OUT, img.size)

if LIVE:
    import json, os
    manifest = {
        "note": "All coordinates are normalised 0-1, origin top-left, over a 16:10 frame.",
        "moon":    {"x": mu, "y": mv, "r": mr},
        "chimney": {"x": 0.1325, "y": 0.327},
        "lake":    {"x": 0.38, "y": 0.712, "w": 0.62, "h": 0.22},
        "windows": [
            {"x": 0.158, "y": 0.418, "w": 0.074, "h": 0.082},
            {"x": 0.064, "y": 0.600, "w": 0.084, "h": 0.112},
            {"x": 0.176, "y": 0.604, "w": 0.086, "h": 0.110},
            {"x": 0.284, "y": 0.628, "w": 0.030, "h": 0.024}
        ],
        "lanterns": [
            {"x": 0.287, "y": 0.634}, {"x": 0.395, "y": 0.644}, {"x": 0.466, "y": 0.656}
        ],
        "bulbs":   [{"x": round(bx, 5), "y": round(by, 5)} for (bx, by) in bulbs],
        "reflections": [
            {"x": u, "y": 0.712} for u in
            [0.610, 0.642, 0.672, 0.699, 0.728, 0.755, 0.780,
             0.806, 0.828, 0.853, 0.877, 0.905, 0.931]
        ],
        "villageWindows": {"x": 0.600, "y": 0.640, "w": 0.360, "h": 0.060},
        "calmBottomFraction": 0.0667
    }
    mp = os.path.splitext(OUT)[0] + "-manifest.json"
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print("wrote", mp, len(manifest["bulbs"]), "bulbs")
