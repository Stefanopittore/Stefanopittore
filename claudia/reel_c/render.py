"""Animatic of the "Villa Olivera" reel (Claudia nº 12) from stills.

The cuts follow her words: every shot starts on a phrase or word of the voice take, and the montage
after the twist cuts on the music beat. On-screen text only repeats what she says.

Usage: python3 -I render.py [voice]   voice = isabel (default) | any key in VOICES with timings
Writes ../media/reel_c/animatic[_voice].mp4, stills and edit.json.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, AUD = os.path.join(HERE, "raw"), os.path.join(HERE, "audio")
MUS = os.path.join(HERE, "..", "reel_b", "audio")          # music and effects from the first animatic
OUT = os.path.join(HERE, "..", "media", "reel_c")
W, H, FPS, SR = 1080, 1920, 30, 44100
BEAT, BEAT0 = 0.4644, 0.074
TEMPO = 1.08          # a touch quicker, pitch untouched
FONT = "/usr/share/fonts/opentype/inter/"

# Word timings of each take (seconds in the source file), from the TTS alignment
VOICES = {
    "isabel": dict(file="e_isabel.mp3", words={
        "Esta": 1.367, "los": 2.407, "acabados:": (3.207, 3.927), "travertino": (4.087, 5.087), "roble": (5.287, 5.887),
        "y": 6.087, "mar.": (8.007, 8.447), "Lo": 8.802, "mejor?": (8.887, 9.447), "Que": 9.607, "existe.": (10.327, 11.007),
        "Tu": 11.351, "promoción": (11.967, 12.807), "nunca": 12.887, "real.": (14.167, 14.687), "Soy": 14.967,
        "Vitruvi.": (17.087, 17.887), "Escríbeme.": (17.927, 18.607)}),
}
# Phrases kept from the take (first word, last word); the silences between them are tightened
PHRASES = [("Esta", "acabados:"), ("travertino", "travertino"), ("roble", "roble"), ("y", "mar."), ("Lo", "mejor?"),
           ("Que", "existe."), ("Tu", "promoción"), ("nunca", "real."), ("Soy", "Vitruvi."), ("Escríbeme.", "Escríbeme.")]
GAPS = [0.08, 0.06, 0.06, 0.22, 0.10, 0.16, 0.04, 0.16, 0.05]   # after each phrase but the last
LEAD, TAIL, PRE, POST = 0.30, 0.45, 0.04, 0.09

def start_of(v, w): t = v["words"][w]; return t[0] if isinstance(t, tuple) else t
def end_of(v, w): t = v["words"][w]; return t[1] if isinstance(t, tuple) else t

def timeline(v):
    """Output start/end of each phrase, and a function mapping a source word time to output time."""
    out, t = [], LEAD
    for i, (a, b) in enumerate(PHRASES):
        s0, s1 = start_of(v, a) - PRE, end_of(v, b) + POST
        d = (s1 - s0) / TEMPO
        out.append(dict(src=(s0, s1), t0=t, t1=t + d))
        t += d + (GAPS[i] if i < len(GAPS) else 0)
    def at(word, phrase):
        p = out[phrase]
        return p["t0"] + (start_of(v, word) - p["src"][0]) / TEMPO
    return out, at, out[-1]["t1"] + TAIL

def build(vkey):
    v = VOICES[vkey]
    ph, at, end = timeline(v)
    drop = ph[6]["t0"]                                   # "Tu próxima promoción": the music opens here
    beat = [drop + k * BEAT for k in range(12)]
    shots = [
        dict(img="s01_caballo", t0=0.0, t1=at("los", 0), z=(1.0, 1.10), f=(0.5, 0.5), embudo="Atención",
             desc="Primera toma: ella a caballo entre los olivos, delante de la villa, mira a cámara"),
        dict(img="s02_paseo", t0=at("los", 0), t1=ph[1]["t0"], z=(1.0, 1.08), f=(0.5, 0.45), embudo="Atención",
             desc="Entra caminando en el salón y lo enseña con la mano"),
        dict(img="s03_travertino", t0=ph[1]["t0"], t1=ph[2]["t0"], z=(1.0, 1.14), embudo="Interés", desc="Su mano sobre el travertino"),
        dict(img="s04_roble", t0=ph[2]["t0"], t1=ph[3]["t0"], z=(1.0, 1.14), embudo="Interés", desc="La escalera de roble macizo"),
        dict(img="s05_piscina", t0=ph[3]["t0"], t1=ph[4]["t0"], z=(1.0, 1.08), f=(0.45, 0.45), embudo="Interés",
             desc="En la piscina infinita, señala el horizonte"),
        dict(img="s10_giro", t0=ph[4]["t0"], t1=ph[5]["t0"], z=(1.0, 1.05), f=(0.53, 0.42), embudo="Giro",
             desc="Anochece; plano medio, sonrisa cómplice"),
        dict(img="s10_giro", t0=ph[5]["t0"], t1=drop, z=(1.5, 1.6), f=(0.53, 0.40), embudo="Giro",
             desc="Corte en salto, más cerca: revela que no existe"),
    ]
    mont = [("v00_villa", 1, "Dron sobre la villa al atardecer"), ("s06_cocina", 1, "Cocina: isla de travertino y roble"),
            ("s07_bano", 1, "Baño con bañera de piedra frente al mar"), ("s08_dormitorio", 1, "Dormitorio con vistas"),
            ("s09_terraza", 1, "Terraza con mesa puesta al atardecer"), ("s11_dron_noche", 2, "Dron: la villa encendida de noche")]
    k = 0
    for img, n, desc in mont:
        shots.append(dict(img=img, t0=beat[k], t1=beat[k + n], z=(1.03, 1.17), kind="beat", embudo="Deseo", desc=desc))
        k += n
    shots[-1]["t1"] = ph[8]["t0"]                        # hold the night drone until she speaks again
    shots.append(dict(img="s12_cierre", t0=ph[8]["t0"], t1=end, z=(1.0, 1.10), f=(0.49, 0.42), embudo="Acción",
                      desc="Primer plano de noche junto a la piscina: se presenta y pide que le escribas"))
    for s in shots:
        s.setdefault("kind", "talk"); s.setdefault("f", (0.5, 0.5))
    # Captions = her words; the montage shows the tagline she says, big
    caps = [(ph[0]["t0"], at("los", 0), "Esta villa cuenta"), (at("los", 0), ph[0]["t1"] + 0.05, "con los mejores acabados"),
            (ph[1]["t0"], ph[1]["t1"], "travertino…"), (ph[2]["t0"], ph[2]["t1"], "roble…"),
            (ph[3]["t0"], ph[3]["t0"] + (ph[3]["t1"] - ph[3]["t0"]) * 0.45, "y una piscina"),
            (ph[3]["t0"] + (ph[3]["t1"] - ph[3]["t0"]) * 0.45, ph[3]["t1"] + 0.1, "que se funde con el mar."),
            (ph[4]["t0"], ph[4]["t1"] + 0.08, "¿Lo mejor?"), (ph[5]["t0"], ph[5]["t1"] + 0.1, "Que todavía no existe."),
            (ph[8]["t0"], at("Vitruvi.", 8) - 0.6, "Soy Claudia,"), (at("Vitruvi.", 8) - 0.6, ph[8]["t1"] + 0.05, "presentadora IA de Vitruvi.")]
    titles = [(ph[6]["t0"], ph[6]["t1"] + 0.03, "TU PRÓXIMA PROMOCIÓN"), (ph[7]["t0"], ph[7]["t1"] + 0.12, "NUNCA SE SINTIÓ\nTAN REAL")]
    cta_t = ph[9]["t0"] - 0.05
    return dict(vkey=vkey, v=v, ph=ph, end=end, drop=drop, shots=shots, caps=caps, titles=titles, cta=cta_t)

# ---------- Pictures ----------
def font(name, size): return ImageFont.truetype(FONT + name, size)

def text_layer(txt, size, name="InterDisplay-ExtraBold.otf", shadow=170, pad=40, spacing=8):
    f = font(name, size)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    box = d0.multiline_textbbox((0, 0), txt, font=f, spacing=spacing, align="center")
    w, h = int(box[2] - box[0] + 2 * pad), int(box[3] - box[1] + 2 * pad)
    sh = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sh).multiline_text((pad - box[0], pad - box[1] + 4), txt, font=f, fill=shadow, spacing=spacing, align="center")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0)); layer.putalpha(sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(layer).multiline_text((pad - box[0], pad - box[1]), txt, font=f, fill=(255, 255, 255, 255), spacing=spacing, align="center")
    if layer.width > 1000: layer = layer.resize((1000, int(layer.height * 1000 / layer.width)), Image.LANCZOS)
    return layer

def pill(txt, size, name, fg, bg, padx=34, pady=18):
    f = font(name, size); box = f.getbbox(txt)
    w, h = int(box[2] - box[0] + 2 * padx), int(box[3] - box[1] + 2 * pady)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg); d.text((padx - box[0], pady - box[1]), txt, font=f, fill=fg)
    return im

SRC = {}
def src(name):
    if name not in SRC: SRC[name] = Image.open(os.path.join(RAW, name + ".png")).convert("RGB")
    return SRC[name]

def frame_of(s, u, dx=0, dy=0):
    im = src(s["img"])
    e = 1 - (1 - u) ** 3 if s["kind"] == "beat" else u
    z = s["z"][0] + (s["z"][1] - s["z"][0]) * e
    cw = im.width / z; ch = cw * H / W
    if ch > im.height: ch = im.height; cw = ch * W / H
    cx = min(max(s["f"][0] * im.width + dx, cw / 2), im.width - cw / 2)
    cy = min(max(s["f"][1] * im.height + dy, ch / 2), im.height - ch / 2)
    return im.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def paste_center(base, layer, cx, cy, scale=1.0):
    if scale != 1.0: layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BICUBIC)
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))

def render_video(E, path):
    caps = {t: text_layer(t, 78) for _, _, t in E["caps"]}
    tits = {t: text_layer(t, 118, "InterDisplay-Black.otf", shadow=210) for _, _, t in E["titles"]}
    label = pill("Presentadora IA · @vitruvistudio", 30, "Inter-SemiBold.otf", (255, 255, 255, 255), (0, 0, 0, 110), 22, 12)
    place = text_layer("Begur · Costa Brava", 34, "Inter-SemiBold.otf", shadow=200, pad=16)
    cta = pill("Escríbeme  →", 66, "InterDisplay-Bold.otf", (16, 16, 16, 255), (255, 255, 255, 240), 52, 26)
    foot = text_layer("Presentadora IA de @vitruvistudio · Infografías no contractuales", 28, "Inter-SemiBold.otf", shadow=200, pad=20)
    rng = np.random.default_rng(7)
    shake = [(14, -8), (-8, 5), (4, -3), (-2, 1)]
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "5M", "-bufsize", "10M", "-tune", "grain",
                           "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    shots, end = E["shots"], E["end"]
    for i in range(int(round(end * FPS))):
        t = i / FPS
        s = next((s for s in shots if s["t0"] <= t + 1e-6 < s["t1"]), shots[-1])
        k = int(round((t - s["t0"]) * FPS))
        dx, dy = shake[k] if s["kind"] == "beat" and k < len(shake) else (0, 0)
        fr = frame_of(s, min(1, (t - s["t0"]) / (s["t1"] - s["t0"])), dx, dy).convert("RGBA")
        for a, b, txt in E["titles"]:
            if a <= t < b: paste_center(fr, tits[txt], W / 2, H * 0.46, max(1.0, 1.18 - 0.18 * (t - a) / 0.12))
        for a, b, txt in E["caps"]:
            if a <= t < b: paste_center(fr, caps[txt], W / 2, 1380 if t >= shots[-1]["t0"] else 1250, max(1.0, 1.1 - 0.1 * (t - a) / 0.08))
        fr.alpha_composite(label, (44, 150))
        if t < shots[1]["t1"]: paste_center(fr, place, W / 2, 1450)
        if t >= shots[-1]["t0"]: paste_center(fr, foot, W / 2, 1490)
        if t >= E["cta"]: paste_center(fr, cta, W / 2, 1380, max(1.0, 1.2 - 0.2 * (t - E["cta"]) / 0.12))
        a = np.asarray(fr.convert("RGB"), dtype=np.float32)
        if 0 <= t - E["drop"] < 2 / FPS: a = a + (255 - a) * (0.8 if t - E["drop"] < 1 / FPS else 0.35)
        g = rng.normal(0, 5.0, (H // 2, W // 2, 1)).astype(np.float32)
        a += np.repeat(np.repeat(g, 2, 0), 2, 1)
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()

# ---------- Sound ----------
def load(path, tempo=1.0):
    af = ["-af", f"atempo={tempo}"] if tempo != 1.0 else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, *af, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def place(track, clip, at, gain=1.0, fin=0.01, fout=0.02):
    clip = clip.copy() * gain
    a, b = int(fin * SR), int(fout * SR)
    if a: clip[:a] *= np.linspace(0, 1, a)
    if b: clip[-b:] *= np.linspace(1, 0, b)
    s = int(at * SR)
    if s < 0: clip = clip[-s:]; s = 0
    e = min(len(track), s + len(clip)); track[s:e] += clip[:e - s]

def lowpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 4), len(x)).astype(np.float32)

def env(points, n):
    t = np.arange(n) / SR; ts, vs = zip(*points); return np.interp(t, ts, vs).astype(np.float32)

def at_level(x, db): return x * (10 ** (db / 20) / (np.sqrt((x ** 2).mean()) + 1e-9))

def render_audio(E, path):
    ph, end, D = E["ph"], E["end"], E["drop"]
    n = int(end * SR)
    take = load(os.path.join(AUD, E["v"]["file"]), TEMPO)
    voice = np.zeros(n, np.float32)
    for p in ph:
        seg = take[int(p["src"][0] / TEMPO * SR):int(p["src"][1] / TEMPO * SR)]
        loud = seg[np.abs(seg) > 0.02]
        place(voice, seg * (0.12 / (np.sqrt((loud ** 2).mean()) + 1e-6)), p["t0"], fin=0.012, fout=0.035)
    voice *= 0.89 / (np.abs(voice).max() + 1e-6)
    mus = load(os.path.join(MUS, "music.mp3"))
    off = (BEAT0 + round((D - BEAT0) / BEAT) * BEAT) - D
    off += BEAT * np.ceil(-off / BEAT) if off < 0 else 0
    m = mus[int(off * SR):int(off * SR) + n]; m = np.pad(m, (0, n - len(m)))
    lp = lowpass(m, 420)
    twist = ph[4]["t0"]
    k = env([(0, 1), (twist - 0.05, 1), (twist + 0.05, 0), (D - 0.02, 0), (D, 1), (end, 1)], n)   # muffled during the twist
    music = m * k + lp * (1 - k) * 1.3
    music *= env([(0, 0.0), (0.25, 0.42), (twist - 0.05, 0.42), (twist + 0.1, 0.30), (D - 0.02, 0.30), (D, 0.9),
                  (ph[7]["t1"] + 0.1, 0.9), (ph[8]["t0"], 0.45), (ph[9]["t1"] + 0.02, 0.45), (ph[9]["t1"] + 0.06, 0.0), (end, 0.0)], n)
    music *= env([(0, 1), (D + 0.05, 1), (D + 0.12, 0.55), (ph[7]["t1"], 0.55), (ph[7]["t1"] + 0.1, 1), (end, 1)], n)
    fx = np.zeros(n, np.float32)
    riser, impact, whoosh = (at_level(load(os.path.join(MUS, k + ".mp3")), v) for k, v in (("riser", -22), ("impact", -17), ("whoosh", -24)))
    hooves = at_level(load(os.path.join(AUD, "hooves.mp3")), -24)
    place(fx, hooves[: int(1.6 * SR)], 0.0, 1.0, fin=0.02, fout=0.3)
    place(fx, riser, D - len(riser) / SR + 0.02, 1.0, fin=0.4, fout=0.02)
    place(fx, impact[: int(1.3 * SR)], D, 1.0, fin=0.0, fout=0.6)
    for s in E["shots"][1:5]: place(fx, whoosh[: int(0.5 * SR)], s["t0"] - 0.18, 0.7, fin=0.04, fout=0.08)
    place(fx, impact[: int(0.9 * SR)] * 0.6, ph[9]["t0"], 1.0, fin=0.0, fout=0.5)     # small hit on "Escríbeme"
    mix = np.tanh((voice + music * 0.55 + fx) * 1.1) / np.tanh(1.1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(np.repeat(mix[:, None], 2, 1), -1, 1) * 32767).astype(np.int16).tobytes())

# ---------- Stills and timeline ----------
def export(E):
    os.makedirs(os.path.join(OUT, "hd"), exist_ok=True)
    spoken = lambda a, b: " ".join(t.replace("\n", " ") for x, y, t in E["caps"] + E["titles"] if x < b - 0.05 and y > a + 0.05)
    rows = []
    for i, s in enumerate(E["shots"], 1):
        name = f"s{i:02d}.jpg"; still = frame_of(s, 0.5)
        still.save(os.path.join(OUT, "hd", name), quality=86, optimize=True, progressive=True)
        still.resize((540, 960), Image.LANCZOS).save(os.path.join(OUT, name), quality=84, optimize=True, progressive=True)
        rows.append(dict(n=i, seg=f"{s['t0']:.2f}-{s['t1']:.2f}".replace(".", ","), t0=round(s["t0"], 3), t1=round(s["t1"], 3),
                         img=f"media/reel_c/{name}", hd=f"media/reel_c/hd/{name}", fuente=s["img"], embudo=s["embudo"], imagen=s["desc"],
                         voz=spoken(s["t0"], s["t1"]), texto="", ella=s["img"] in ("s01_caballo", "s02_paseo", "s03_travertino", "s04_roble",
                                                                                  "s05_piscina", "s10_giro", "s12_cierre")))
    return rows

if __name__ == "__main__":
    vkey = sys.argv[1] if len(sys.argv) > 1 else "isabel"
    E = build(vkey)
    os.makedirs(OUT, exist_ok=True)
    rows = export(E)
    render_audio(E, os.path.join(HERE, "mix.wav"))
    render_video(E, os.path.join(HERE, "video.mp4"))
    name = "animatic.mp4" if vkey == "isabel" else f"animatic_{vkey}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "video.mp4"), "-i", os.path.join(HERE, "mix.wav"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                    "-movflags", "+faststart", "-shortest", os.path.join(OUT, name)], check=True)
    frame_of(E["shots"][0], 0.0).save(os.path.join(OUT, "poster.jpg"), quality=84)
    json.dump(dict(voz=vkey, duracion=round(E["end"], 2), drop=round(E["drop"], 3), beat=BEAT, planos=rows),
              open(os.path.join(HERE, "edit.json"), "w"), ensure_ascii=False, indent=1)
    print(len(rows), "planos,", round(E["end"], 2), "s")
