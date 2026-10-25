"""Animatic of script B (15-16 s) from stills: cuts on her sentences and on the music beat,
a zoom-in on every shot, her voice, music, sound effects, captions and iPhone grain.

Usage: python3 -I render.py   (writes ../media/reel_b/ and edit.json)
"""
import json
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
AUD = os.path.join(HERE, "audio")
OUT = os.path.join(HERE, "..", "media", "reel_b")
W, H, FPS, SR = 1080, 1920, 30, 44100
END = 16.0
BEAT = 0.4644          # measured on the generated track (129 BPM)
BEAT0 = 0.074          # first beat in the track
D = 6.62               # the drop: music opens on "¡y esto es lo que hago!"
FONT = "/usr/share/fonts/opentype/inter/"

# ---------- Timeline ----------
# Voice take B: source windows -> output start (seconds)
VOICE = [("intro_b", 0.19, 2.47, 0.10), ("intro_b", 2.67, 3.75, 2.50), ("intro_b", 3.87, 5.75, 3.68), ("intro_b", 5.95, 8.83, 5.66),
         ("cta", 0.11, 2.12, 12.80), ("cta", 2.32, 3.22, 14.95)]
CAPTIONS = [(0.10, 1.20, "¡Esta casa"), (1.20, 2.44, "NO existe!"), (2.50, 3.63, "Todavía…"), (3.68, 4.42, "Pero te la voy"),
            (4.42, 4.92, "a enseñar"), (4.92, 5.61, "IGUAL."), (5.66, 6.62, "Soy Claudia,"), (6.68, 7.70, "¡y esto es"),
            (7.70, 8.50, "lo que hago!"), (12.86, 13.82, "¿Vendes obra nueva"), (13.82, 14.95, "en Cataluña?")]

def montage():
    plan = [("p03", 1, "", "Dron en picado sobre la villa del acantilado, Costa Brava"),
            ("p04", 1, "", "Ella camina por el borde de la piscina al atardecer"),
            ("p05", 1, "", "Terraza del ático en Barcelona, la Sagrada Familia al fondo"),
            ("p07", 1, "", "Ella se gira y se ríe en la terraza"),
            ("p06", 1, "", "Su mano sobre la isla de piedra de la cocina"),
            ("p10", 1, "VILLAS", "Dron que cae sobre la piscina hacia el mar"),
            ("p08", 1, "MASÍAS", "Dron sobre la masía del Empordà con caballos"),
            ("p09", 2, "A CABALLO", "Ella a caballo junto a la masía"),
            ("p11", 1, "", "Salón de doble altura con la escalera de roble"),
            ("p12", 1, "", "Ella abre de día la misma puerta del principio"),
            ("p13", 1, "ANTES DE LA", "Ella en la obra del 22@ con casco"),
            ("p14", 2, "PRIMERA PIEDRA", "Dron que se aleja de la villa encendida de noche")]
    t, cuts = D, []
    for img, beats, word, desc in plan:
        t1 = t + beats * BEAT
        cuts.append(dict(img=img, t0=t, t1=t1, word=word, desc=desc, kind="beat"))
        t = t1
    return cuts

FACE1, FACE15 = (0.553, 0.413), (0.522, 0.413)
CUTS = [
    dict(img="p01_v1", t0=0.0, t1=2.44, z=(1.00, 1.09), f=(0.5, 0.45), kind="talk", embudo="Atención",
         desc="Noche: la villa encendida, la piscina delante y ella en la puerta, la luz en la cara"),
    dict(img="p01_v1", t0=2.44, t1=3.63, z=(1.85, 1.95), f=FACE1, kind="talk", embudo="Atención",
         desc="Corte en salto: mismo plano, muy cerca de su cara"),
    dict(img="p01_v1", t0=3.63, t1=5.61, z=(1.30, 1.45), f=(0.553, 0.47), kind="talk", embudo="Retención",
         desc="Otro salto: plano medio, ella con seguridad"),
    dict(img="p15", t0=5.61, t1=D, z=(1.00, 1.07), f=FACE15, kind="talk", embudo="Presentación",
         desc="Primer plano en la puerta: se presenta"),
] + montage() + [
    dict(img="p15", t0=13.12, t1=END, z=(1.04, 1.16), f=FACE15, kind="talk", embudo="Venta",
         desc="Vuelta a la puerta de noche: la llamada a la acción y el pie legal"),
]
for c in CUTS:
    c.setdefault("z", (1.04, 1.17)); c.setdefault("f", (0.5, 0.5)); c.setdefault("word", "")
    c.setdefault("embudo", "Prueba")

def speech_in(t0, t1):
    return " ".join(txt for a, b, txt in CAPTIONS if a < t1 - 0.05 and b > t0 + 0.05)

# ---------- Pictures ----------
def font(name, size): return ImageFont.truetype(FONT + name, size)

def text_layer(txt, size, name="InterDisplay-ExtraBold.otf", fill=(255, 255, 255), shadow=170, pad=40):
    f = font(name, size)
    box = f.getbbox(txt)
    w, h = box[2] - box[0] + 2 * pad, box[3] - box[1] + 2 * pad
    sh = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sh).text((pad - box[0], pad - box[1] + 4), txt, font=f, fill=shadow)
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.putalpha(sh)
    ImageDraw.Draw(layer).text((pad - box[0], pad - box[1]), txt, font=f, fill=fill + (255,))
    return layer

def pill(txt, size, name, fg, bg, padx=34, pady=18, radius=None):
    f = font(name, size)
    box = f.getbbox(txt)
    w, h = box[2] - box[0] + 2 * padx, box[3] - box[1] + 2 * pady
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius or h // 2, fill=bg)
    d.text((padx - box[0], pady - box[1]), txt, font=f, fill=fg)
    return im

SRC = {}
def src(name):
    if name not in SRC: SRC[name] = Image.open(os.path.join(RAW, name + ".png")).convert("RGB")
    return SRC[name]

def frame_of(c, u, dx=0, dy=0):
    im = src(c["img"])
    z = c["z"][0] + (c["z"][1] - c["z"][0]) * (1 - (1 - u) ** 3 if c["kind"] == "beat" else u)
    cw = im.width / z; ch = cw * H / W
    if ch > im.height: ch = im.height; cw = ch * W / H
    cx = min(max(c["f"][0] * im.width + dx, cw / 2), im.width - cw / 2)
    cy = min(max(c["f"][1] * im.height + dy, ch / 2), im.height - ch / 2)
    return im.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def paste_center(base, layer, cx, cy, scale=1.0):
    if scale != 1.0: layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BICUBIC)
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))

def render_video(path):
    cap_layers = {txt: text_layer(txt, 86) for _, _, txt in CAPTIONS}
    word_layers = {c["word"]: text_layer(c["word"], 132, "InterDisplay-Black.otf", shadow=200) for c in CUTS if c["word"]}
    for k, l in word_layers.items():
        if l.width > 980: word_layers[k] = l.resize((980, int(l.height * 980 / l.width)), Image.LANCZOS)
    label = pill("Presentadora IA · @vitruvistudio", 30, "Inter-SemiBold.otf", (255, 255, 255, 255), (0, 0, 0, 110), 22, 12)
    cta = pill("Escríbeme  →", 66, "InterDisplay-Bold.otf", (16, 16, 16, 255), (255, 255, 255, 240), 52, 26)
    foot = text_layer("Presentadora IA de @vitruvistudio · Infografías no contractuales", 28, "Inter-SemiBold.otf", shadow=200, pad=20)
    rng = np.random.default_rng(7)
    shake = [(14, -8), (-8, 5), (4, -3), (-2, 1)]
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "5M", "-bufsize", "10M", "-tune", "grain",
                           "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    n = int(round(END * FPS))
    for i in range(n):
        t = i / FPS
        c = next(c for c in CUTS if c["t0"] <= t + 1e-6 < c["t1"]) if t < CUTS[-1]["t1"] else CUTS[-1]
        k = int(round((t - c["t0"]) * FPS))
        dx, dy = shake[k] if c["kind"] == "beat" and k < len(shake) else (0, 0)
        u = (t - c["t0"]) / (c["t1"] - c["t0"])
        fr = frame_of(c, min(1, u), dx, dy).convert("RGBA")
        if c["word"]:
            pop = max(1.0, 1.25 - 0.25 * (t - c["t0"]) / 0.12)
            paste_center(fr, word_layers[c["word"]], W / 2, H * 0.47, pop)
        for a, b, txt in CAPTIONS:
            if a <= t < b:
                pop = max(1.0, 1.12 - 0.12 * (t - a) / 0.08)
                paste_center(fr, cap_layers[txt], W / 2, 1210 if t < D or t >= 12.5 else 1330, pop)
        fr.alpha_composite(label, (44, 150))
        if t >= 13.12: paste_center(fr, foot, W / 2, 1440)
        if t >= 14.95:
            paste_center(fr, cta, W / 2, 1210, max(1.0, 1.2 - 0.2 * (t - 14.95) / 0.12))
        a = np.asarray(fr.convert("RGB"), dtype=np.float32)
        if 0 <= t - D < 2 / FPS: a = a + (255 - a) * (0.8 if t - D < 1 / FPS else 0.35)   # white flash on the drop
        g = rng.normal(0, 5.0, (H // 2, W // 2, 1)).astype(np.float32)                     # coarse sensor grain, as on a phone
        a += np.repeat(np.repeat(g, 2, 0), 2, 1)
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()

# ---------- Sound ----------
def load(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(AUD, name + ".mp3"), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def place(track, clip, at, gain=1.0, fin=0.01, fout=0.02):
    clip = clip.copy() * gain
    a, b = int(fin * SR), int(fout * SR)
    if a: clip[:a] *= np.linspace(0, 1, a)
    if b: clip[-b:] *= np.linspace(1, 0, b)
    s = int(at * SR)
    if s < 0: clip = clip[-s:]; s = 0
    e = min(len(track), s + len(clip))
    track[s:e] += clip[:e - s]

def lowpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 4), len(x)).astype(np.float32)

def env(points, n):
    t = np.arange(n) / SR; ts, vs = zip(*points)
    return np.interp(t, ts, vs).astype(np.float32)

def render_audio(path):
    n = int(END * SR)
    voice = np.zeros(n, np.float32)
    clips = {k: load(k) for k in ("intro_b", "cta")}
    for k, a, b, at in VOICE:
        seg = clips[k][int(a * SR):int(b * SR)]
        loud = seg[np.abs(seg) > 0.02]
        seg = seg * (0.12 / (np.sqrt((loud ** 2).mean()) + 1e-6))     # same speech level for both takes
        place(voice, seg, at, fin=0.015, fout=0.04)
    voice *= 0.89 / (np.abs(voice).max() + 1e-6)
    # Music aligned so a beat falls on the drop and on every cut after it
    mus = load("music")
    off = (BEAT0 + round((D - BEAT0) / BEAT) * BEAT) - D
    off += BEAT * np.ceil(-off / BEAT) if off < 0 else 0
    m = mus[int(off * SR):int(off * SR) + n]
    m = np.pad(m, (0, n - len(m)))
    lp = lowpass(m, 450)
    mix_k = env([(0, 0), (D - 0.02, 0), (D, 1), (END, 1)], n)
    music = lp * (1 - mix_k) * 1.3 + m * mix_k
    # Level: soft under her intro, full in the montage, ducked under her voice, cut dead on "Escríbeme"
    music *= env([(0, 0.0), (0.4, 0.28), (D - 0.02, 0.28), (D, 0.85), (8.5, 0.55), (8.7, 0.85), (12.7, 0.85), (12.9, 0.42),
                  (14.93, 0.42), (14.96, 0.0), (END, 0.0)], n)
    music *= env([(0, 1), (6.68, 1), (6.75, 0.33), (8.45, 0.33), (8.6, 1), (END, 1)], n)
    fx = np.zeros(n, np.float32)
    def at_level(x, db):      # every effect to a fixed loudness, whatever level it was generated at
        return x * (10 ** (db / 20) / (np.sqrt((x ** 2).mean()) + 1e-9))
    riser, impact, whoosh, crick = (at_level(load(k), v) for k, v in (("riser", -22), ("impact", -17), ("whoosh", -24), ("crickets", -30)))
    place(fx, riser, D - len(riser) / SR + 0.02, 1.0, fin=0.4, fout=0.02)
    place(fx, impact[: int(1.3 * SR)], D, 1.0, fin=0.0, fout=0.6)
    for tc in (8.94, 11.27, 12.20):
        place(fx, whoosh[: int(0.7 * SR)], tc - 0.25, 1.0, fin=0.05, fout=0.1)
    amb = np.tile(crick, 3)
    place(fx, amb[: int((D + 0.3) * SR)], 0.0, 1.0, fin=0.3, fout=0.3)
    place(fx, amb[: int(3.2 * SR)], 12.95, 1.2, fin=0.25, fout=0.4)
    mix = voice + music * 0.55 + fx
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    st = np.repeat(mix[:, None], 2, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())

# ---------- Stills for the page and the timeline ----------
def export(cuts):
    os.makedirs(os.path.join(OUT, "hd"), exist_ok=True)
    rows = []
    for i, c in enumerate(cuts, 1):
        still = frame_of(c, 0.5)
        name = f"s{i:02d}.jpg"
        still.save(os.path.join(OUT, "hd", name), quality=86, optimize=True, progressive=True)
        still.resize((540, 960), Image.LANCZOS).save(os.path.join(OUT, name), quality=84, optimize=True, progressive=True)
        rows.append(dict(n=i, seg=f"{c['t0']:.2f}-{c['t1']:.2f}".replace(".", ","), t0=round(c["t0"], 3), t1=round(c["t1"], 3),
                         img=f"media/reel_b/{name}", hd=f"media/reel_b/hd/{name}", fuente=c["img"], embudo=c["embudo"],
                         imagen=c["desc"], voz=speech_in(c["t0"], c["t1"]) if c["kind"] == "talk" or c["t0"] < 8.5 else "",
                         texto=c["word"], ella=c["img"] not in ("p03", "p05", "p08", "p10", "p11", "p14")))
    return rows

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rows = export(CUTS)
    render_audio(os.path.join(HERE, "mix.wav"))
    render_video(os.path.join(HERE, "video.mp4"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "video.mp4"), "-i", os.path.join(HERE, "mix.wav"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                    "-movflags", "+faststart", "-shortest", os.path.join(OUT, "animatic.mp4")], check=True)
    frame_of(CUTS[0], 0.0).save(os.path.join(OUT, "poster.jpg"), quality=84)
    json.dump(dict(duracion=END, beat=BEAT, drop=D, planos=rows), open(os.path.join(HERE, "edit.json"), "w"), ensure_ascii=False, indent=1)
    print(len(rows), "planos")
