#!/usr/bin/env python3
"""『みすぼらしい老人は、財閥会長だった』 화면 속 일본어 글자 합성(제11장 3, 로컬·무과금) — tsuki_ja_overlay.py 방식.
무지로 생성한 키프레임(1344x768) 위에 실글꼴로 그린 평면 캔버스를 원근 변형해 곱하기로 얹는다.
S16b 메뉴판: 대본 NA 「その日から、鷹宮亭のメニューの最後には、こう書かれています。」 → 마지막 줄 「かけうどん　お代は、お気持ちで」.
출력: assets/portraits/beggar-ja/<id>-1.png → kf_select.json 등록.
사용법: python3 scripts/beggar_ja_overlay.py"""
import json, os
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
F = lambda n: os.path.join(ROOT, "scripts", "fonts", n)
MIN_B, MIN_R = F("ZenOldMincho-Bold.ttf"), F("ZenOldMincho-Regular.ttf")
KF = os.path.join(ROOT, "assets", "portraits", "beggar-chairman-keyframes")
OUT = os.path.join(ROOT, "assets", "portraits", "beggar-ja")
SEL = os.path.join(ROOT, "productions", "beggar-chairman-ja", "kf_select.json")


def coeffs(dst, src):
    m = []
    for (x, y), (u, v) in zip(dst, src):
        m += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
    return np.linalg.solve(np.array(m, float), np.array([c for p in src for c in p], float)).tolist()


def menu_canvas(W=540, H=860):
    c = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(c)
    ink, red = (38, 30, 24), (120, 28, 22)
    def ctr(y, t, f, col=ink):
        w = d.textlength(t, font=f); d.text(((W - w) / 2, y), t, font=f, fill=col)
    ctr(46, "鷹宮亭", ImageFont.truetype(MIN_B, 62))
    ctr(124, "お品書き", ImageFont.truetype(MIN_R, 34))
    d.line((90, 182, W - 90, 182), fill=ink, width=2)
    f = ImageFont.truetype(MIN_R, 32)
    y = 222
    for name, price in [("会席　鷹", "三万円"), ("会席　宮", "二万円"), ("季節の御膳", "一万二千円"), ("天ぷら膳", "八千円")]:
        d.text((72, y), name, font=f, fill=ink); w = d.textlength(price, font=f); d.text((W - 72 - w, y), price, font=f, fill=ink)
        y += 78
    d.line((90, y + 8, W - 90, y + 8), fill=ink, width=2)
    fb = ImageFont.truetype(MIN_B, 40)
    ctr(y + 52, "かけうどん", fb, red)
    ctr(y + 112, "お代は、お気持ちで", ImageFont.truetype(MIN_B, 36), red)
    return c


def apply(base, canvas, quad, blur=0.6):
    W, H = base.size
    cw, ch = canvas.size
    warp = canvas.transform((W, H), Image.PERSPECTIVE, coeffs(quad, [(0, 0), (cw, 0), (cw, ch), (0, ch)]), Image.BICUBIC,
                            fillcolor=(255, 255, 255)).filter(ImageFilter.GaussianBlur(blur))
    return ImageChops.multiply(base.convert("RGB"), warp)


JOBS = {"S16b": (menu_canvas, [(602, 202), (873, 203), (868, 636), (603, 636)])}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sel = json.load(open(SEL, encoding="utf-8"))
    for sid, (mk, quad) in JOBS.items():
        base = Image.open(os.path.join(KF, f"{sid}-1.png"))
        out = os.path.join(OUT, f"{sid}-1.png")
        apply(base, mk(), quad).save(out)
        sel[sid] = os.path.relpath(out, ROOT)
        print("합성:", out)
    json.dump(sel, open(SEL, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
