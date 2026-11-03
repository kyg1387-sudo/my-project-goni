#!/usr/bin/env python3
"""『引きこもりの息子』 소품 일본어 합성(제7장 6·제11장 3 — 조립 전, 무료). 무지 소품 면에 실글꼴 글자를 원근 변형해
곱하기(어둡게만) 합성하고, 종이 색에 가까운 픽셀에만 얹어 앞의 손·펜은 그대로 둔다(키).
결과는 assets/preview/hikikomori-screens/<id>.png(화면 합성본과 같은 폴더 — build_hikikomori_overrides.py가 정지·립싱크 컷 원본으로 씀).
사용법: python3 scripts/hikikomori_ja_overlay.py"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KF = os.path.join(ROOT, "assets", "portraits", "hikikomori-keyframes")
OUT = os.path.join(ROOT, "assets", "preview", "hikikomori-screens")
G = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
M = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf" if os.path.exists("/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf") else G


def F(p, s):
    return ImageFont.truetype(p, s)


HAND = os.path.join(ROOT, "assets", "fonts", "KleeOne-SemiBold.ttf")  # 손글씨(포스트잇) — 인쇄체면 합성 티가 난다


def postit():
    im = Image.new("RGB", (600, 600), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.text((250, 215), "パス：", font=F(HAND, 112), fill=(25, 30, 55), anchor="mm")
    d.text((305, 385), "工場の創業日", font=F(HAND, 96), fill=(25, 30, 55), anchor="mm")
    im = im.rotate(-4, resample=Image.BICUBIC, fillcolor=(255, 255, 255))  # 손으로 쓴 줄은 약간 기운다
    a = np.asarray(im).astype(float); a = cv2.GaussianBlur(a, (0, 0), 1.6)  # 사인펜 번짐
    return Image.fromarray(a.astype("uint8"))


def passbook(rows=10):
    W, H = 1600, 900; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    hd = ["年月日", "摘要", "お支払金額", "お預り金額", "差引残高"]; xs = [40, 330, 700, 1000, 1300]
    for x, h in zip(xs, hd):
        d.text((x, 40), h, font=F(G, 40), fill=(60, 70, 120))
    d.line([(20, 95), (W - 20, 95)], fill=(120, 130, 170), width=3)
    bal = 812345
    for i in range(rows):
        y = 150 + i * 72; m = 10 - (rows - 1) + i; yy = 6 if m > 0 else 5; mm = m if m > 0 else m + 12
        bal += 200000 - 180000
        for x, t in zip(xs, [f"{yy:02d}-{mm:02d}-25", "振込　セオ　ダイキ", "", "200,000", f"{bal:,}"]):
            d.text((x, y), t, font=F(G, 40), fill=(35, 35, 45))
        d.line([(20, y + 50), (W - 20, y + 50)], fill=(200, 205, 220), width=2)
    return im


def contract():
    W, H = 1400, 1000; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.text((W / 2, 110), "事業譲渡契約書", font=F(M, 96), fill=(25, 25, 30), anchor="mm")
    body = ["瀬尾精工（以下「甲」という）と鳳凰工業株式会社（以下「乙」という）は、",
            "甲の事業及び特許権の譲渡に関し、次のとおり契約を締結する。", "", "第１条（目的）", "甲は、その工場設備及び特許権の一切を乙に譲渡する。",
            "第２条（譲渡価額）", "譲渡価額は、金三千万円とする。"]
    for i, t in enumerate(body):
        d.text((90, 250 + i * 64), t, font=F(M, 38), fill=(40, 40, 45))
    d.text((820, 820), "甲　署名", font=F(M, 40), fill=(40, 40, 45)); d.line([(980, 850), (1300, 850)], fill=(60, 60, 60), width=2)
    return im


def put(base, art, quad, tol=55, strength=1.0, satkey=True):
    b = np.asarray(base.convert("RGB")).astype(float); H, W, _ = b.shape
    a = np.asarray(art.convert("RGB")).astype(float); h, w, _ = a.shape
    Mx = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    wa = cv2.warpPerspective(a, Mx, (W, H), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
    poly = np.zeros((H, W), np.float32); cv2.fillConvexPoly(poly, np.int32(quad), 1.0)
    med = np.median(b[poly > 0], axis=0); dist = np.linalg.norm(b - med, axis=2)
    key = np.clip(1 - (dist - tol) / 40, 0, 1) * poly
    hsv = cv2.cvtColor(b.astype("uint8"), cv2.COLOR_RGB2HSV).astype(float)
    if satkey:  # 노란 포스트잇처럼 채도 높은 종이는 끈다
        key *= np.clip((125 - hsv[..., 1]) / 30, 0, 1)  # 종이(채도 낮음, 램프 아래 약 75)만 — 손 피부(약 160)는 제외
    key = cv2.erode(key, np.ones((5, 5), np.uint8))
    key = cv2.GaussianBlur(key, (0, 0), 1.0)
    mult = 1 - (1 - wa / 255.0) * strength * key[..., None]
    return Image.fromarray((b * mult).clip(0, 255).astype("uint8"))


def main():
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(OUT, "S09e.png")
    im = put(Image.open(src if os.path.exists(src) else os.path.join(KF, "S09e-1.png")), postit(), [(298, 125), (420, 112), (440, 245), (322, 262)], tol=70, strength=0.9, satkey=False)
    im.save(os.path.join(OUT, "S09e.png"))
    put(Image.open(os.path.join(KF, "S15e-1.png")), passbook(), [(600, 478), (820, 474), (814, 596), (604, 598)], tol=60, strength=0.85).save(os.path.join(OUT, "S15e.png"))
    put(Image.open(os.path.join(KF, "S15h-1.png")), passbook(8), [(560, 828 - 572 + 0, ), (700, 820 - 572), (712, 878 - 572), (575, 890 - 572)], tol=60, strength=0.6).save(os.path.join(OUT, "S15h.png")) if False else None
    put(Image.open(os.path.join(KF, "S17b-1.png")), contract(), [(244, 320), (699, 257), (1277, 427), (848, 690)], tol=45, strength=0.9).save(os.path.join(OUT, "S17b.png"))
    print("소품 합성 완료: S09e S15e S17b")


if __name__ == "__main__":
    main()
