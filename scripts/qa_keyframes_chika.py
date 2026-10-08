#!/usr/bin/env python3
"""#02 PHASE 4 Kill Gate 자동 검사(무과금): 띠(레터박스)·크기·얼굴 수·앵글 분포 + 검수용 콘택트시트.
사용법: qa_keyframes_chika.py <키프레임 폴더> <출력 접두어>  → <접두어>_NN.jpg, 표준출력에 요약"""
import json, os, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
F = ImageFont.truetype("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", 20)
DET = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def edge_strip(a):
    r = a.mean(1); c = a.mean(0)
    f = lambda v: sum(1 for x in v if x > 228 or x < 10)
    return f(r[:12]) + f(r[-12:]), f(c[:12]) + f(c[-12:])


def main():
    kdir, out = sys.argv[1], sys.argv[2]
    sb = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "chika.json"), encoding="utf-8"))
    shots = [s for s in sb["scenes"] if s.get("keyframe") and os.path.exists(os.path.join(kdir, s["id"] + "-1.png"))]
    rows, flags = [], []
    for s in shots:
        p = os.path.join(kdir, s["id"] + "-1.png")
        im = cv2.imread(p); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        h, w = g.shape
        rs, cs = edge_strip(g.astype(int))
        faces = DET.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
        nf = len(faces)
        who = [os.path.basename(r).split("-")[0] for r in s["refs"] if "/cells/" in r and not os.path.basename(r).startswith(("loc", "angle", "prop"))]
        note = []
        if rs >= 6 or cs >= 6: note.append(f"띠{rs}/{cs}")
        if abs(w / h - 16 / 9) > 0.03: note.append(f"비율{w}x{h}")
        if s["kind"] in ("ins", "empty", "estill", "gfx") and nf >= 1 and s["kind"] != "gfx": note.append(f"얼굴{nf}(무인컷)")
        if s["kind"] == "sil" and nf >= 1: note.append(f"얼굴{nf}(실루엣)")
        if s["kind"] in ("react", "face") and nf == 0: note.append("얼굴0")
        if nf >= 2 and s["kind"] in ("d", "react", "face"): note.append(f"얼굴{nf}")
        rows.append((s, p, note))
        if note: flags.append((s["id"], s["kind"], s["size"], s["angle"], note))
    # 콘택트시트 20장씩
    W, H, cols = 448, 252, 5
    for k in range(0, len(rows), 20):
        sub = rows[k:k + 20]; nr = (len(sub) + cols - 1) // cols
        m = Image.new("RGB", (W * cols + (cols + 1) * 8, (H + 40) * nr + 8), (20, 20, 20)); d = ImageDraw.Draw(m)
        for i, (s, p, note) in enumerate(sub):
            x, y = 8 + (i % cols) * (W + 8), 8 + (i // cols) * (H + 40)
            m.paste(Image.open(p).convert("RGB").resize((W, H)), (x, y))
            d.text((x, y + H + 2), f"{s['id']} {s['kind']} {s['size']} {s['angle']} {s['tier']}", font=F, fill=(255, 230, 80))
            if note: d.text((x, y + H + 20), " ".join(note), font=F, fill=(255, 90, 90))
        m.save(f"{out}_{k // 20 + 1:02d}.jpg", quality=85)
    from collections import Counter
    ang = Counter(s["angle"] for s, _, _ in rows)
    print(f"검사 {len(rows)}장, 자동 플래그 {len(flags)}건, 앵글 분포 {dict(ang)}")
    for f in flags: print("  ", f)


if __name__ == "__main__":
    main()
