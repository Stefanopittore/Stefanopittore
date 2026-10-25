"""Casting pipeline: download Magnific results, split casting sheets, compress, build the casting page.

Usage:
  python3 -I pipeline.py fetch  <creations_get dump> <manifest.json> <download dir>
  python3 -I pipeline.py media  <manifest.json> <download dir> <media dir>
  python3 -I pipeline.py page   <manifest.json> <casting.html> [persona.json]
"""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image

KINDS = ("sheet", "swim_elegant", "swim_bold", "door", "presenter")
SCENES = KINDS[1:]
PANELS = ("seria", "sonrisa", "perfil", "cuerpo")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def urls_from_dump(dump):
    text = open(dump, encoding="utf-8").read()
    found = {}
    for block in re.split(r"\n  - identifier: ", "\n" + text)[1:]:
        ident = block.split("\n", 1)[0].strip()
        m = re.search(r'\n    url: "([^"]+)"', block)
        if m:
            found[ident] = m.group(1)
    return found


def fetch(dump, manifest, dl):
    os.makedirs(dl, exist_ok=True)
    urls = urls_from_dump(dump)
    for c in load(manifest):
        for kind in KINDS:
            ident = c.get(kind)
            if ident and ident in urls:
                out = os.path.join(dl, f"{c['n']:02d}_{kind}.png")
                subprocess.run(["curl", "-sS", "--max-time", "120", "-o", out, urls[ident]], check=True)


def save_jpeg(im, path, width):
    im = im.convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, "JPEG", quality=80, optimize=True, progressive=True)


def panel_ranges(im):
    """Find the four panels of a casting sheet: the model leaves gutters or hard edges near each quarter."""
    g = np.asarray(im.convert("L"), dtype=np.int16)
    w = g.shape[1]
    d = np.median(np.abs(g[:, 1:] - g[:, :-1]), axis=0)
    cuts = []
    for k in (1, 2, 3):
        c, r = int(w * k / 4), int(w * 0.07)
        win = d[c - r:c + r]
        xs = np.where(win >= max(6, win.max() * 0.5))[0] + c - r
        if len(xs) == 0:
            cuts.append((c, c))
            continue
        best = int(xs[np.argmax(d[xs])])
        near = xs[np.abs(xs - best) <= 60]
        a, b = int(near.min()) + 1, int(near.max()) + 1
        cuts.append((a, b) if b - a > 2 else (best + 1, best + 1))
    edges = [0] + [x for ab in cuts for x in ab] + [w]
    return [(edges[2 * i], edges[2 * i + 1]) for i in range(4)]


def trim_white(im):
    """Drop flat near-white borders (gutters, outer frame) around a panel."""
    g = np.asarray(im.convert("L"), dtype=np.int16)
    flat = lambda a: a.mean() > 238 and a.std() < 8
    top, bottom, left, right = 0, g.shape[0], 0, g.shape[1]
    while bottom - top > 50 and flat(g[top, left:right]): top += 1
    while bottom - top > 50 and flat(g[bottom - 1, left:right]): bottom -= 1
    while right - left > 50 and flat(g[top:bottom, left]): left += 1
    while right - left > 50 and flat(g[top:bottom, right - 1]): right -= 1
    return im.crop((left, top, right, bottom))


def media(manifest, dl, out):
    """Small JPEGs for the feed and a high-resolution copy in hd/ for zooming."""
    hd = os.path.join(out, "hd")
    os.makedirs(hd, exist_ok=True)
    for c in load(manifest):
        n = f"{c['n']:02d}"
        sheet = os.path.join(dl, f"{n}_sheet.png")
        if os.path.exists(sheet):
            im = Image.open(sheet)
            for (a, b), name in zip(panel_ranges(im), PANELS):
                panel = trim_white(im.crop((a, 0, b, im.height)))
                save_jpeg(panel, os.path.join(out, f"{n}_{name}.jpg"), 480)
                save_jpeg(panel, os.path.join(hd, f"{n}_{name}.jpg"), 1400)
        for kind in SCENES:
            src = os.path.join(dl, f"{n}_{kind}.png")
            if os.path.exists(src):
                save_jpeg(Image.open(src), os.path.join(out, f"{n}_{kind}.jpg"), 600)
                save_jpeg(Image.open(src), os.path.join(hd, f"{n}_{kind}.jpg"), 1400)


def embed(text, script_id, data):
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return re.sub(r'(<script id="%s" type="application/json">).*?(</script>)' % script_id,
                  lambda m: m.group(1) + blob + m.group(2), text, count=1, flags=re.S)


def page(manifest, html, persona=None):
    keep = ("n", "group", "groupLine", "label", "age", "chips", "inspired")
    text = open(html, encoding="utf-8").read()
    text = embed(text, "cast-data", [{k: c[k] for k in keep if k in c} for c in load(manifest)])
    if persona:
        text = embed(text, "persona-data", load(persona))
    with open(html, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"fetch": fetch, "media": media, "page": page}[cmd](*args)
