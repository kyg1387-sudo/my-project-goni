#!/usr/bin/env python3
"""『月に帰った契約社員』 화면 속 일본어 글자 합성(제11장 3, 로컬·무과금) — ashita_ja_overlay.py 방식.
무지로 생성한 키프레임(1344x768) 위에 실글꼴로 그린 평면 캔버스를 원근 변형해 얹는다. 화면 = 덮기, 종이 = 곱하기.
출력: assets/portraits/tsuki-ja/<id>-1.png → kf_select.json에 등록(assemble_tsuki_keyframes.py가 읽음).
사용법: python3 scripts/tsuki_ja_overlay.py"""
import json, os
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
F = lambda n: os.path.join(ROOT, "scripts", "fonts", n)
MIN_B, GOTH = F("ZenOldMincho-Bold.ttf"), F("ZenMaruGothic-Black.ttf")
SRC = os.path.join(ROOT, "assets", "portraits", "tsuki-kf-b")
OUT = os.path.join(ROOT, "assets", "portraits", "tsuki-ja")
SEL = os.path.join(ROOT, "productions", "tsuki-ja", "kf_select.json")
INK = (34, 30, 36)


def coeffs(dst, w, h):
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def place(base, layer, quad, mode="over", blur=0.6):
    w, h = layer.size
    warped = layer.transform(base.size, Image.PERSPECTIVE, coeffs(quad, w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
    rgb, a = warped.convert("RGB"), warped.split()[3]
    if mode == "multiply":
        return Image.composite(ImageChops.multiply(base, rgb), base, a)
    return Image.composite(rgb, base, a)


def Q(*pts):  # 0~1 비율 좌표 → 픽셀(1344x768)
    return [(x * 1344, y * 768) for x, y in pts]


def screen(im, quad, lines, color=(255, 255, 255), bg=(190, 20, 20, 230), font=GOTH, size=72, sub=None):
    w, h = 1000, 420
    L = Image.new("RGBA", (w, h), bg); d = ImageDraw.Draw(L)
    f = ImageFont.truetype(font, size)
    y = h / 2 - (len(lines) - 1) * size * 0.7
    for s in lines:
        d.text((w / 2, y), s, font=f, fill=color, anchor="mm"); y += size * 1.4
    if sub:
        d.text((w / 2, h - 60), sub, font=ImageFont.truetype(font, 34), fill=color, anchor="mm")
    return place(im, L, quad)


def paper(im, quad, title, body=(), tsize=54, bsize=30, w=800, h=1100, mode="multiply", title_y=90):
    L = Image.new("RGBA", (w, h), (255, 255, 255, 0)); d = ImageDraw.Draw(L)
    d.text((w / 2, title_y), title, font=ImageFont.truetype(MIN_B, tsize), fill=INK + (255,), anchor="mm")
    y = title_y + tsize + 40
    for s in body:
        d.text((80, y), s, font=ImageFont.truetype(MIN_B, bsize), fill=INK + (235,), anchor="lm"); y += bsize * 1.9
    return place(im, L, quad, mode)


def s05a(im): return screen(im, Q((0.33, 0.14), (0.72, 0.17), (0.72, 0.49), (0.33, 0.52)), ["負荷分散　失敗"], bg=(0, 0, 0, 0), size=84, sub="月見野スマートシティ 電力グリッド")
def s06a(im): return screen(im, Q((0.37, 0.03), (0.80, 0.03), (0.80, 0.27), (0.37, 0.27)), ["負荷分散　正常"], color=(10, 60, 20), bg=(120, 235, 140, 215), size=78, sub="KAGUYA　稼働中")
def s08b(im): return paper(im, Q((0.22, 0.40), (0.69, 0.40), (0.79, 0.95), (0.10, 0.95)), "特許権譲渡証", ["特許第　　　号「電力系統負荷分散制御プログラム」", "譲渡人　竹内　光", "譲受人　月浦エナジー株式会社", "上記特許を受ける権利を、譲受人に譲渡します。"], tsize=50, bsize=26)
def s16ba(im): return screen(im, Q((0.22, 0.14), (0.79, 0.14), (0.79, 0.40), (0.22, 0.40)), ["期限まで、あと一日"], bg=(0, 0, 0, 0), size=100, sub="ライセンス更新待ち　23:59:41")
def s16bb(im): return screen(im, Q((0.27, 0.19), (0.71, 0.19), (0.71, 0.47), (0.27, 0.47)), ["認証失敗"], bg=(205, 25, 25, 250), size=110, sub="ERROR  KAGUYA LICENSE KEY  INVALID")
def s17a(im): return screen(im, Q((0.665, 0.59), (0.80, 0.55), (0.835, 0.68), (0.70, 0.73)), ["篠田室長"], color=(240, 240, 240), bg=(18, 18, 22, 250), size=90, sub="着信中…")
def s18a(im): return screen(im, Q((0.40, 0.13), (0.60, 0.13), (0.60, 0.41), (0.40, 0.41)), ["ライセンス", "期限切れ"], bg=(0, 0, 0, 0), size=92)
def s20a(im): return paper(im, Q((0.12, 0.22), (0.52, 0.13), (0.55, 0.20), (0.15, 0.30)), "月浦エナジー　株価急落", tsize=60, w=900, h=180, title_y=90)
def s20b(im): return paper(im, Q((0.44, 0.16), (0.65, 0.19), (0.66, 0.74), (0.40, 0.72)), "解散のお知らせ", ["月浦エナジー株式会社は、", "本日をもって解散いたしました。", "長らくのご愛顧、誠にありがとう", "ございました。"], tsize=72, bsize=38)
def s20c(im): return paper(im, Q((0.20, 0.48), (0.60, 0.48), (0.60, 0.66), (0.20, 0.66)), "告　訴　状", tsize=66, w=800, h=260, title_y=130)


JOBS = {"S05a": s05a, "S06a": s06a, "S08b": s08b, "S16ba": s16ba, "S16bb": s16bb, "S17a": s17a, "S18a": s18a, "S20a": s20a, "S20b": s20b, "S20c": s20c}


def main():
    os.makedirs(OUT, exist_ok=True)
    sel = json.load(open(SEL, encoding="utf-8")) if os.path.exists(SEL) else {}
    for sid, fn in JOBS.items():
        src = sel.get(sid) if sel.get(sid, "").endswith(".png") and "tsuki-ja" not in sel.get(sid, "") else os.path.join(SRC, f"{sid}-1.png")
        im = Image.open(os.path.join(ROOT, src) if not os.path.isabs(src) else src).convert("RGB")
        if im.size != (1344, 768):
            im = im.resize((1344, 768), Image.LANCZOS)
        out = os.path.join(OUT, f"{sid}-1.png")
        fn(im).save(out)
        sel[sid] = os.path.relpath(out, ROOT)
        print("합성:", sid, "→", sel[sid])
    json.dump(sel, open(SEL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
