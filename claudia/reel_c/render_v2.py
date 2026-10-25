"""Animatic v2 of the Villa Olivera reel: hook «Nada de lo que vas a ver existe», twist «Ni yo»,
tagline on the beat and a concrete call to action («Mándame el plano… y te la enseño así»).

Voice: Elena Navarro (ElevenLabs v4). Her phrases are cut where the take really speaks (measured
by energy), and each phrase gets its own shot; the montage after the twist cuts on the music beat.

Usage: python3 -I render_v2.py   (writes ../media/reel_d/ and edit_v2.json)
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R  # noqa: E402  (pictures, text and sound helpers)

HERE = R.HERE
OUT = os.path.join(HERE, "..", "media", "reel_d")
W, H, FPS, SR = R.W, R.H, R.FPS, R.SR
TEMPO = 1.05
TAKE = "e_elena_v2a.mp3"
# Where the take really speaks (seconds), one window per phrase
SEGS = [(0.04, 2.31), (2.69, 3.82), (4.16, 5.50), (5.96, 6.93), (7.43, 8.09), (8.68, 12.14), (12.58, 13.97), (14.27, 15.02), (15.24, 16.26)]
TEXT = ["Nada de lo que vas a ver existe.", "Ni esta villa…", "ni esta piscina…", "ni el caballo.", "Ni yo.",
        "Tu próxima promoción… nunca se sintió tan real.", "Soy Claudia, de Vitruvi.", "Mándame el plano…", "y te la enseño así."]
GAPS = [0.12, 0.10, 0.10, 0.55, 0.32, 0.15, 0.10, 0.08]     # the long one is the silence before «Ni yo»
LEAD, TAIL, PRE, POST = 0.25, 0.6, 0.03, 0.06
TAG_SPLIT = 0.41                                              # «Tu próxima promoción…» | «nunca se sintió tan real.»

def timeline():
    out, t = [], LEAD
    for i, (a, b) in enumerate(SEGS):
        s0, s1 = max(0.0, a - PRE), b + POST
        d = (s1 - s0) / TEMPO
        out.append(dict(src=(s0, s1), t0=t, t1=t + d, text=TEXT[i]))
        t += d + (GAPS[i] if i < len(GAPS) else 0)
    return out, out[-1]["t1"] + TAIL

def build():
    ph, end = timeline()
    drop = ph[5]["t0"]
    beat = [drop + k * R.BEAT for k in range(12)]
    twist_cut = ph[3]["t1"] + 0.12
    shots = [
        dict(img="s01_caballo", t0=0.0, t1=ph[1]["t0"], z=(1.0, 1.12), f=(0.5, 0.5), embudo="Gancho",
             desc="Ella a caballo delante de la villa al atardecer: la imagen más espectacular y la frase que choca"),
        dict(img="v00_villa", t0=ph[1]["t0"], t1=ph[2]["t0"], z=(1.0, 1.15), embudo="Retención", desc="Dron sobre la villa"),
        dict(img="s05_piscina", t0=ph[2]["t0"], t1=ph[3]["t0"], z=(1.0, 1.10), f=(0.46, 0.45), embudo="Retención",
             desc="Ella en la piscina infinita sobre el mar"),
        dict(img="s01_caballo", t0=ph[3]["t0"], t1=twist_cut, z=(1.55, 1.7), f=(0.42, 0.55), embudo="Retención",
             desc="Vuelta al caballo, de cerca"),
        dict(img="s10_giro", t0=twist_cut, t1=drop, z=(1.25, 1.45), f=(0.53, 0.40), embudo="Giro",
             desc="Silencio en su cara al anochecer… y la sonrisa: «Ni yo»"),
    ]
    mont = [("s02_paseo", "Ella entra en el salón y lo enseña"), ("s03_travertino", "Su mano sobre el travertino"),
            ("s06_cocina", "Cocina de travertino y roble"), ("s07_bano", "Bañera de piedra frente al mar"),
            ("s04_roble", "Escalera de roble macizo"), ("s09_terraza", "Terraza con la mesa puesta al atardecer"),
            ("s11_dron_noche", "La villa encendida de noche")]
    for k, (img, desc) in enumerate(mont):
        shots.append(dict(img=img, t0=beat[k], t1=beat[k + 1], z=(1.03, 1.17), kind="beat", embudo="Deseo", desc=desc,
                          f=(0.5, 0.45) if img == "s02_paseo" else (0.5, 0.5)))
    shots[-1]["t1"] = ph[6]["t0"]
    shots += [
        dict(img="s12_cierre", t0=ph[6]["t0"], t1=ph[7]["t0"], z=(1.0, 1.06), f=(0.49, 0.42), embudo="Acción", desc="Se presenta, de noche junto a la piscina"),
        dict(img="s13_plano", t0=ph[7]["t0"], t1=ph[8]["t0"], z=(1.0, 1.12), embudo="Acción", desc="Su mano desliza un plano hacia ti: «Mándame el plano…»"),
        dict(img="s12_cierre", t0=ph[8]["t0"], t1=end, z=(1.14, 1.0), f=(0.49, 0.42), embudo="Acción", desc="«…y te la enseño así», sonríe; el último fotograma enlaza con el primero"),
    ]
    for s in shots:
        s.setdefault("kind", "talk"); s.setdefault("f", (0.5, 0.5))
    t5 = ph[5]; split = t5["t0"] + (t5["t1"] - t5["t0"]) * TAG_SPLIT
    caps = [(ph[i]["t0"], ph[i]["t1"] + 0.08, ph[i]["text"]) for i in (1, 2, 3, 6, 7, 8)]
    titles = [(0.0, ph[1]["t0"], "Nada de lo que vas\na ver existe.", 0.665, 96, "InterDisplay-ExtraBold.otf"),
              (ph[4]["t0"], drop, "Ni yo.", 0.68, 150, "InterDisplay-Black.otf"),
              (t5["t0"], split + 0.03, "TU PRÓXIMA PROMOCIÓN", 0.46, 118, "InterDisplay-Black.otf"),
              (split, t5["t1"] + 0.12, "NUNCA SE SINTIÓ\nTAN REAL", 0.46, 118, "InterDisplay-Black.otf")]
    return dict(ph=ph, end=end, drop=drop, shots=shots, caps=caps, titles=titles, cta=ph[7]["t0"], twist=twist_cut)

def render_video(E, path):
    caps = {t: R.text_layer(t, 80) for _, _, t in E["caps"]}
    tits = {t: R.text_layer(t, size, name, shadow=210) for _, _, t, _, size, name in E["titles"]}
    label = R.pill("Contenido creado con IA · @vitruvistudio", 30, "Inter-SemiBold.otf", (255, 255, 255, 255), (0, 0, 0, 110), 22, 12)
    cta = R.pill("Mándame tu plano  →", 60, "InterDisplay-Bold.otf", (16, 16, 16, 255), (255, 255, 255, 240), 48, 24)
    foot = R.text_layer("Infografías no contractuales · Vitruvi Studio", 28, "Inter-SemiBold.otf", shadow=200, pad=20)
    rng = np.random.default_rng(11)
    shake = [(14, -8), (-8, 5), (4, -3), (-2, 1)]
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "5M", "-bufsize", "10M", "-tune", "grain",
                           "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    shots, end = E["shots"], E["end"]
    ending = shots[-3]["t0"]
    for i in range(int(round(end * FPS))):
        t = i / FPS
        s = next((s for s in shots if s["t0"] <= t + 1e-6 < s["t1"]), shots[-1])
        k = int(round((t - s["t0"]) * FPS))
        dx, dy = shake[k] if s["kind"] == "beat" and k < len(shake) else (0, 0)
        fr = R.frame_of(s, min(1, (t - s["t0"]) / (s["t1"] - s["t0"])), dx, dy).convert("RGBA")
        for a, b, txt, y, _, _ in E["titles"]:
            if a <= t < b: R.paste_center(fr, tits[txt], W / 2, H * y, max(1.0, 1.15 - 0.15 * (t - a) / 0.12))
        for a, b, txt in E["caps"]:
            if a <= t < b: R.paste_center(fr, caps[txt], W / 2, 1360 if t >= ending else 1250, max(1.0, 1.1 - 0.1 * (t - a) / 0.08))
        fr.alpha_composite(label, (44, 150))
        if t >= E["cta"]: R.paste_center(fr, cta, W / 2, 1480, max(1.0, 1.2 - 0.2 * (t - E["cta"]) / 0.12))
        if t >= ending: R.paste_center(fr, foot, W / 2, 1575)
        a = np.asarray(fr.convert("RGB"), dtype=np.float32)
        if 0 <= t - E["drop"] < 2 / FPS: a = a + (255 - a) * (0.8 if t - E["drop"] < 1 / FPS else 0.35)
        g = rng.normal(0, 5.0, (H // 2, W // 2, 1)).astype(np.float32)
        a += np.repeat(np.repeat(g, 2, 0), 2, 1)
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()

def render_audio(E, path):
    ph, end, D = E["ph"], E["end"], E["drop"]
    n = int(end * SR)
    take = R.load(os.path.join(R.AUD, TAKE), TEMPO)
    voice = np.zeros(n, np.float32)
    for p in ph:
        seg = take[int(p["src"][0] / TEMPO * SR):int(p["src"][1] / TEMPO * SR)]
        loud = seg[np.abs(seg) > 0.02]
        R.place(voice, seg * (0.12 / (np.sqrt((loud ** 2).mean()) + 1e-6)), p["t0"], fin=0.012, fout=0.035)
    voice *= 0.89 / (np.abs(voice).max() + 1e-6)
    mus = R.load(os.path.join(R.MUS, "music.mp3"))
    off = (R.BEAT0 + round((D - R.BEAT0) / R.BEAT) * R.BEAT) - D
    off += R.BEAT * np.ceil(-off / R.BEAT) if off < 0 else 0
    m = mus[int(off * SR):int(off * SR) + n]; m = np.pad(m, (0, n - len(m)))
    hush0, hush1 = ph[3]["t1"] + 0.02, D                      # silence on her face, then «Ni yo»
    last = ph[8]["t1"]
    music = m * R.env([(0, 0.0), (0.2, 0.45), (hush0 - 0.1, 0.45), (hush0 + 0.12, 0.0), (hush1 - 0.01, 0.0), (hush1, 0.9),
                       (ph[5]["t1"] + 0.1, 0.9), (ph[6]["t0"], 0.42), (last + 0.02, 0.42), (last + 0.06, 0.0), (end, 0.0)], n)
    music *= R.env([(0, 1), (D + 0.05, 1), (D + 0.12, 0.6), (ph[5]["t1"], 0.6), (ph[5]["t1"] + 0.1, 1), (end, 1)], n)
    fx = np.zeros(n, np.float32)
    impact, whoosh = (R.at_level(R.load(os.path.join(R.MUS, k + ".mp3")), v) for k, v in (("impact", -17), ("whoosh", -24)))
    hooves = R.at_level(R.load(os.path.join(R.AUD, "hooves.mp3")), -24)
    crick = R.at_level(R.load(os.path.join(R.MUS, "crickets.mp3")), -30)
    R.place(fx, hooves[: int(1.8 * SR)], 0.0, 1.0, fin=0.02, fout=0.3)
    R.place(fx, hooves[: int(1.0 * SR)], E["shots"][3]["t0"], 0.8, fin=0.05, fout=0.3)
    R.place(fx, crick[: int((hush1 - hush0 + 0.4) * SR)], hush0, 1.0, fin=0.15, fout=0.2)
    R.place(fx, impact[: int(1.3 * SR)], D, 1.0, fin=0.0, fout=0.6)
    for s in E["shots"][1:4]: R.place(fx, whoosh[: int(0.5 * SR)], s["t0"] - 0.18, 0.7, fin=0.04, fout=0.08)
    R.place(fx, impact[: int(0.9 * SR)] * 0.5, last - 0.05, 1.0, fin=0.0, fout=0.5)
    mix = np.tanh((voice + music * 0.55 + fx) * 1.1) / np.tanh(1.1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(np.repeat(mix[:, None], 2, 1), -1, 1) * 32767).astype(np.int16).tobytes())

def export(E):
    os.makedirs(os.path.join(OUT, "hd"), exist_ok=True)
    said = [(p["t0"], p["t1"], p["text"]) for p in E["ph"]]
    spoken = lambda a, b: " ".join(t for x, y, t in said if x < b - 0.05 and y > a + 0.05)
    rows = []
    for i, s in enumerate(E["shots"], 1):
        name = f"s{i:02d}.jpg"; still = R.frame_of(s, 0.5)
        still.save(os.path.join(OUT, "hd", name), quality=86, optimize=True, progressive=True)
        still.resize((540, 960), Image.LANCZOS).save(os.path.join(OUT, name), quality=84, optimize=True, progressive=True)
        on = [t.replace("\n", " ") for a, b, t, *_ in E["titles"] if a < s["t1"] - 0.05 and b > s["t0"] + 0.05]
        rows.append(dict(n=i, seg=f"{s['t0']:.2f}-{s['t1']:.2f}".replace(".", ","), t0=round(s["t0"], 3), t1=round(s["t1"], 3),
                         img=f"media/reel_d/{name}", hd=f"media/reel_d/hd/{name}", fuente=s["img"], embudo=s["embudo"], imagen=s["desc"],
                         voz=spoken(s["t0"], s["t1"]), texto=" · ".join(on),
                         ella=s["img"] in ("s01_caballo", "s02_paseo", "s03_travertino", "s04_roble", "s05_piscina", "s10_giro", "s12_cierre", "s13_plano")))
    return rows

if __name__ == "__main__":
    E = build()
    os.makedirs(OUT, exist_ok=True)
    rows = export(E)
    render_audio(E, os.path.join(HERE, "mix.wav"))
    render_video(E, os.path.join(HERE, "video.mp4"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "video.mp4"), "-i", os.path.join(HERE, "mix.wav"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                    "-movflags", "+faststart", "-shortest", os.path.join(OUT, "animatic.mp4")], check=True)
    R.frame_of(E["shots"][0], 0.0).save(os.path.join(OUT, "poster.jpg"), quality=84)
    json.dump(dict(voz="elena", duracion=round(E["end"], 2), drop=round(E["drop"], 3), beat=R.BEAT, planos=rows),
              open(os.path.join(HERE, "edit_v2.json"), "w"), ensure_ascii=False, indent=1)
    print(len(rows), "planos,", round(E["end"], 2), "s")
