"""Casting pipeline: download Magnific results, split casting sheets, compress, build the casting page.

Usage:
  python3 -I pipeline.py fetch  <creations_get dump> <manifest.json> <download dir>
  python3 -I pipeline.py media  <manifest.json> <download dir> <media dir>
  python3 -I pipeline.py page   <manifest.json> <output html>
"""
import json, os, re, subprocess, sys
from PIL import Image

KINDS = ("sheet", "villa", "door")
PANELS = ("seria", "sonrisa", "perfil", "cuerpo")
REGIONS = ("España", "Europa", "EE. UU.")


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


def media(manifest, dl, out):
    os.makedirs(out, exist_ok=True)
    for c in load(manifest):
        n = f"{c['n']:02d}"
        sheet = os.path.join(dl, f"{n}_sheet.png")
        if os.path.exists(sheet):
            im = Image.open(sheet)
            w = im.width // 4
            for i, name in enumerate(PANELS):
                save_jpeg(im.crop((i * w, 0, (i + 1) * w, im.height)), os.path.join(out, f"{n}_{name}.jpg"), 480)
        for kind in ("villa", "door"):
            src = os.path.join(dl, f"{n}_{kind}.png")
            if os.path.exists(src):
                save_jpeg(Image.open(src), os.path.join(out, f"{n}_{kind}.jpg"), 600)


def page(manifest, out_html):
    cands = load(manifest)
    labels = {"seria": "Seria", "sonrisa": "Sonrisa", "perfil": "Perfil", "cuerpo": "Cuerpo", "villa": "Villa", "door": "Puerta"}
    groups = []
    for region in REGIONS:
        cards = []
        for c in [c for c in cands if c["region"] == region]:
            n = f"{c['n']:02d}"
            shots = "".join(
                f'<figure><img src="media/casting/{n}_{k}.jpg" alt="Candidata {c["n"]}, {labels[k].lower()}" loading="lazy"><figcaption>{labels[k]}</figcaption></figure>'
                for k in ("seria", "sonrisa", "perfil", "cuerpo", "villa", "door")
            )
            cards.append(
                f'<article class="cc"><div class="cc-head"><span class="num">{c["n"]}</span><b>{c["label"]}</b><span>{c["age"]} años</span></div><div class="cc-shots">{shots}</div></article>'
            )
        groups.append(f'<div class="row-lab"><span class="lab">{region}</span></div>' + "".join(cards))
    html = '<section id="casting-interno"><div class="head"><h2>Casting interno</h2><span class="lab">15 candidatas · 24 a 26 años</span></div><p class="ask">Elige tus <span>3 finalistas</span>.</p>' + "".join(groups) + "</section>"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"fetch": fetch, "media": media, "page": page}[cmd](*args)
