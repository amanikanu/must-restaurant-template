"""Regenerates every image in build/v2 from the masters in assets/.

  - crops / resizes the photography
  - chroma-keys the product shots (ketchup bottle, fried chicken) properly:
      connected background mask -> soft matte -> despill -> edge erode
  - slices the portrait contact sheet into avatars

The page build (tools/make.py) then inlines build/v2 into index.html.

Run:  python3 tools/prep_images.py
"""
from collections import deque
import pathlib

import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "assets"
OUT = ROOT / "build" / "v2"
OUT.mkdir(parents=True, exist_ok=True)


def save(im, name, q=80):
    path = OUT / f"{name}.webp"
    im.save(path, "WEBP", quality=q, method=6)
    print(f"  {name:18s} {im.size[0]}x{im.size[1]:<4d} {path.stat().st_size // 1024:4d} KB")


def square_crop(im, fill=1.0, size=400):
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    if fill != 1.0:
        inner = im.resize((int(size * fill),) * 2, Image.LANCZOS)
        canvas = Image.new("RGB", (size, size), (255, 255, 255))
        canvas.paste(inner, ((size - inner.size[0]) // 2,) * 2)
        return canvas
    return im.resize((size, size), Image.LANCZOS)


def landscape(im, out_size):
    """Crop to `out_size` aspect (w, h) from the centre and resize."""
    tw, th = out_size
    w, h = im.size
    target = tw / th
    if w / h > target:
        nw = int(h * target)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize(out_size, Image.LANCZOS)


# ---------------------------------------------------------------- chroma key
def chroma_key(src_path, dst_name, max_w, key_tol=60, glass_tone=(62, 26, 18), erode=1, kill_pale=False):
    """Remove a flat chroma backdrop and return a clean, opaque product cutout.

    1. flood fill the background from the frame -> hard mask
    2. alpha: 0 outside, 1 inside, with a 1-2 px antialiased ramp that excludes
       greenish pixels (so no coloured fringe is ever produced)
    3. transparent glass that showed the backdrop through it is re-toned to the
       product's own glass colour, so the cutout looks right on ANY background
    """
    im = Image.open(src_path).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    h, w, _ = a.shape

    border = np.concatenate([a[0:6].reshape(-1, 3), a[-6:].reshape(-1, 3),
                             a[:, 0:6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    key = np.median(border, axis=0)
    dist = np.sqrt(((a - key) ** 2).sum(axis=2))
    r_, g_, b_ = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    greenish = np.clip((g_ - np.maximum(r_, b_)) / 30.0, 0, 1)      # 1 = pure backdrop

    # 1. background = 4-connected flood fill from the frame over backdrop-like pixels
    near = (dist < key_tol) & (greenish > 0.25)
    seen = np.zeros((h, w), dtype=bool)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if near[y, x] and not seen[y, x]:
                seen[y, x] = True
                dq.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if near[y, x] and not seen[y, x]:
                seen[y, x] = True
                dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and near[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                dq.append((ny, nx))

    bg = seen
    # 2. matte: hard inside, antialiased 2px ramp that ignores green pixels
    alpha = np.where(bg, 0.0, 1.0)
    grown = np.asarray(Image.fromarray(bg.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    rim = grown & ~bg
    alpha[rim & (greenish > 0.30)] = 0.0                       # never keep backdrop
    alpha[rim & (greenish <= 0.30)] = 1.0

    # 3. de-spill (only where the green is strong, so the white label is untouched)
    rgb = a.astype(np.float32)
    spill = greenish > 0.32
    limit = np.maximum(rgb[:, :, 0], rgb[:, :, 2])
    rgb[:, :, 1] = np.where(spill, np.minimum(rgb[:, :, 1], limit), rgb[:, :, 1])
    if glass_tone:
        tone = np.array(glass_tone, dtype=np.float32)
        t = (np.clip((greenish - 0.32) / 0.68, 0, 1) * 0.92)[:, :, None]
        rgb = np.where(spill[:, :, None], rgb * (1 - t) + tone * t, rgb)

    if kill_pale:   # drop the pale haze left by soft shadows on the backdrop
        lum = rgb.mean(axis=2)
        pale = (lum > 204) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 26)
        alpha = np.where(pale, 0.0, alpha)

    out = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8),
                     (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
    img = Image.fromarray(out, "RGBA")

    if erode:                                                   # tighten the outline
        al = img.split()[3].filter(ImageFilter.MinFilter(erode * 2 + 1))
        img.putalpha(al.filter(ImageFilter.GaussianBlur(0.5)))

    img = img.crop(img.getbbox())
    if img.width > max_w:
        img = img.resize((max_w, round(img.height * max_w / img.width)), Image.LANCZOS)
    save(img, dst_name, 90)
    return img


def qa_sheet(img, name):
    """Composite a cutout over white / orange / charcoal to prove the edges are clean."""
    pad = 24
    cols = [(255, 255, 255), (254, 159, 5), (28, 28, 28)]
    W = img.width * len(cols) + pad * (len(cols) + 1)
    H = img.height + pad * 2
    sheet = Image.new("RGB", (W, H), (255, 255, 255))
    x = pad
    for c in cols:
        tile = Image.new("RGBA", (img.width + pad * 2, H - pad * 2), c + (255,))
        tile.alpha_composite(img, (pad, 0))
        sheet.paste(tile.convert("RGB"), (x - pad, pad))
        x += img.width + pad
    sheet.save(ROOT / "screenshots" / f"qa-{name}.png")
    print(f"  QA sheet -> screenshots/qa-{name}.png")


# ---------------------------------------------------------------- build
print("chroma keys:")
# transparent glass, no re-tone -> keeps the bottle looking real on any background
bottle = chroma_key(SRC / "v3-bottle-key.jpg", "ketchup", 300, key_tol=70, erode=1,
                    glass_tone=None)
qa_sheet(bottle, "ketchup")
# chicken: shot on chroma green so it can float on the white footer without a box
chicken = chroma_key(SRC / "v4-chicken-key.jpg", "fried-chicken", 620, key_tol=60, erode=1,
                     glass_tone=None, kill_pale=True)
qa_sheet(chicken, "fried-chicken")

print("hero + plates:")
im = Image.open(SRC / "v2-hero-satay.jpg").convert("RGB")
cx, cy, r = 682, 375, 338
save(im.crop((cx - r, cy - r, cx + r, cy + r)).resize((900, 900), Image.LANCZOS), "hero-satay", 82)

for name, out in [("v2-small-prawn", "small-prawn"), ("v2-small-grill", "small-grill"),
                  ("v2-small-meatballs", "small-meatballs")]:
    save(square_crop(Image.open(SRC / f"{name}.jpg").convert("RGB"), 1.0, 400), out)

print("section art:")
save(square_crop(Image.open(SRC / "v2-about-tacos.jpg").convert("RGB"), 0.98, 800), "about-tacos", 82)
save(landscape(Image.open(SRC / "v2-breakfast.jpg").convert("RGB"), (880, 660)), "breakfast", 80)
save(landscape(Image.open(SRC / "lunch.jpg").convert("RGB"), (880, 660)), "lunch-tray", 80)
save(landscape(Image.open(SRC / "dinner.jpg").convert("RGB"), (880, 660)), "dinner-board", 80)

print("portraits:")
sheet = Image.open(SRC / "v2-portraits.jpg").convert("RGB")
w, h = sheet.size
for name, (cxi, cyi) in {"portrait-1": (0, 0), "portrait-2": (1, 0),
                         "portrait-3": (0, 1), "portrait-4": (1, 1)}.items():
    q = sheet.crop((cxi * w // 2, cyi * h // 2, (cxi + 1) * w // 2, (cyi + 1) * h // 2))
    save(q.resize((240, 240), Image.LANCZOS), name, 82)
save(square_crop(Image.open(SRC / "v2-portrait-mary.jpg").convert("RGB"), 1.0, 240), "portrait-mary", 82)

print("\ndone — now run: python3 tools/make.py")
