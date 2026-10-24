"""Casting pipeline: download Magnific results, split casting sheets, compress, build the casting page.

Usage:
  python3 -I pipeline.py fetch  <creations_get dump> <manifest.json> <download dir>
  python3 -I pipeline.py media  <manifest.json> <download dir> <media dir>
  python3 -I pipeline.py page   <manifest.json> <casting.html>
"""
import json, os, re, subprocess, sys
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
        for kind in SCENES:
            src = os.path.join(dl, f"{n}_{kind}.png")
            if os.path.exists(src):
                save_jpeg(Image.open(src), os.path.join(out, f"{n}_{kind}.jpg"), 600)


def page(manifest, html):
    keep = ("n", "group", "groupLine", "label", "chips", "inspired")
    data = [{k: c[k] for k in keep if k in c} for c in load(manifest)]
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    text = open(html, encoding="utf-8").read()
    text = re.sub(r'(<script id="cast-data" type="application/json">).*?(</script>)',
                  lambda m: m.group(1) + blob + m.group(2), text, count=1, flags=re.S)
    with open(html, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"fetch": fetch, "media": media, "page": page}[cmd](*args)
