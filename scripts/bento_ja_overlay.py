#!/usr/bin/env python3
"""『閉店間際の弁当屋』 화면 속 일본어 글자 합성(제11장 3, 로컬·무과금) — beggar_ja_overlay.py 방식 + 스티커 자동 검출.
무지로 생성한 키프레임(2560x1440) 위에 실글꼴 캔버스를 원근 변형해 곱하기로 얹는다. i2v 전에 끝낸다(PHASE 4 마감).
  스티커 「半額」: 빨간 원 스티커를 색으로 찾아 타원에 맞춰 흰 글자(빨간 부분에만 — 손가락에 가린 곳은 그대로).
  종이·간판: 수동 4점(키프레임 검수 격자에서 잼).  사진: S14b(子ども食堂) 키프레임을 사진 안에 축소 합성.
  흐림: 작은 배경 가짜 글자(제11장 2).
원본은 assets/portraits/bento-keyframes/_v1/에 보관하고, 다시 돌리면 _v1에서 새로 만든다.
사용법: python3 scripts/bento_ja_overlay.py
"""
import os, shutil
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
F = lambda n: os.path.join(ROOT, "scripts", "fonts", n)
MIN_B, MIN_R, HAND = F("ZenOldMincho-Bold.ttf"), F("ZenOldMincho-Regular.ttf"), F("KleeOne-Regular.ttf")
GOTH = F("ZenMaruGothic-Black.ttf")
KF = os.path.join(ROOT, "assets", "portraits", "bento-keyframes")
BAK = os.path.join(KF, "_v1")


def coeffs(dst, src):
    m = []
    for (x, y), (u, v) in zip(dst, src):
        m += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
    return np.linalg.solve(np.array(m, float), np.array([c for p in src for c in p], float)).tolist()


def paste_quad(base, canvas, quad, blur=0.8, mode="multiply"):
    W, H = base.size
    cw, ch = canvas.size
    warp = canvas.transform((W, H), Image.PERSPECTIVE, coeffs(quad, [(0, 0), (cw, 0), (cw, ch), (0, ch)]), Image.BICUBIC,
                            fillcolor=(255, 255, 255)).filter(ImageFilter.GaussianBlur(blur))
    return ImageChops.multiply(base.convert("RGB"), warp)


def vtext(d, x, y, text, font, fill, step=1.0):
    """세로쓰기 한 줄(위→아래). 구두점은 오른쪽 위로 살짝."""
    s = font.size
    for ch in text:
        dx, dy = (s * 0.45, -s * 0.45) if ch in "、。" else (0, 0)
        if ch in "ー―…":
            im = Image.new("L", (s, s), 0); ImageDraw.Draw(im).text((0, 0), ch, font=font, fill=255)
            d._image.paste(Image.new("RGB", (s, s), fill), (int(x), int(y)), im.rotate(-90))
        else:
            d.text((x + dx, y + dy), ch, font=font, fill=fill)
        y += s * step
    return y


# ---- 캔버스 ----
def letter_canvas(W=900, H=1000):
    c = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(c)
    ink = (40, 44, 70)
    f = ImageFont.truetype(HAND, 74)
    cols = ["おじさん。", "あの夜の弁当は、半額では、", "ありませんでしたね。"]
    x = W - 150
    for t in cols:
        vtext(d, x, 40, t, f, ink, 1.02); x -= 210
    return c


def sign_canvas(W=1600, H=470):
    c = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(c)
    f = ImageFont.truetype(MIN_B, 230)
    t = "こまどり弁当"; w = d.textlength(t, font=f)
    d.text(((W - w) / 2, (H - 260) / 2), t, font=f, fill=(34, 40, 66))
    return c


def notice_canvas(W=300, H=1200):
    c = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(c)
    vtext(d, W - 120, 40, "閉店のお知らせ", ImageFont.truetype(MIN_B, 88), (30, 30, 30), 1.05)
    vtext(d, W - 220, 70, "長い間ありがとうございました", ImageFont.truetype(MIN_R, 38), (60, 60, 60), 1.05)
    return c


def price_canvas(W=360, H=700):
    c = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(c)
    vtext(d, W - 130, 260, "唐揚げ弁当", ImageFont.truetype(MIN_B, 70), (30, 30, 30), 1.0)
    vtext(d, 70, 330, "五百円", ImageFont.truetype(MIN_B, 70), (150, 24, 24), 1.0)
    return c


def envelope_back_canvas(W=1000, H=1000):
    c = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(c)
    vtext(d, 150, 520, "朝倉拓海", ImageFont.truetype(HAND, 64), (38, 40, 60), 1.05)
    vtext(d, 240, 560, "東京都杉並区", ImageFont.truetype(HAND, 36), (70, 70, 90), 1.05)
    return c


# ---- 스티커 ----
def red_mask(a):
    hsv = cv2.cvtColor(a, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    return (((h <= 6) | (h >= 172)) & (s > 170) & (v > 90)).astype(np.uint8) * 255  # 손 피부(붉은 기)는 채도 170 미만 — 1차 실증


def sticker(a, min_area=1500, box=None, max_n=2):
    m = red_mask(a)
    if box:
        x0, y0, x1, y1 = box; keep = np.zeros_like(m); keep[y0:y1, x0:x1] = m[y0:y1, x0:x1]; m = keep
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    def round_enough(c):  # 스티커 = 타원에 가까운 덩어리(손·간판 제외)
        (_, _), (MA, ma), _ = cv2.fitEllipse(c)
        return cv2.contourArea(c) / (np.pi * MA * ma / 4 + 1) > 0.80 and min(MA, ma) / max(MA, ma) > 0.25
    cs = sorted([c for c in cs if cv2.contourArea(c) > min_area and len(c) >= 5 and round_enough(c)], key=cv2.contourArea, reverse=True)[:max_n]
    for c in cs:
        (cx, cy), (MA, ma), ang = cv2.fitEllipse(c)
        R = 400
        txt = Image.new("L", (2 * R, 2 * R), 0); d = ImageDraw.Draw(txt)
        f = ImageFont.truetype(GOTH, int(R * 0.62))
        w = d.textlength("半額", font=f); d.text((R - w / 2, R - R * 0.40), "半額", font=f, fill=255)
        txt = txt.resize((max(2, int(MA)), max(2, int(ma))), Image.LANCZOS).rotate(-ang + 0, expand=True) if False else \
            txt.resize((max(2, int(MA)), max(2, int(ma))), Image.LANCZOS)
        t = np.array(txt)
        M = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), -(ang - 90) if MA < ma else -ang, 1.0)
        size = int(max(MA, ma) * 1.2)
        M[0, 2] += size / 2 - t.shape[1] / 2; M[1, 2] += size / 2 - t.shape[0] / 2
        t = cv2.warpAffine(t, M, (size, size))
        x0, y0 = int(cx - size / 2), int(cy - size / 2)
        full = np.zeros(a.shape[:2], np.uint8)
        xs, ys = max(0, x0), max(0, y0); xe, ye = min(a.shape[1], x0 + size), min(a.shape[0], y0 + size)
        full[ys:ye, xs:xe] = t[ys - y0:ye - y0, xs - x0:xe - x0]
        ell = np.zeros(a.shape[:2], np.uint8); cv2.ellipse(ell, ((cx, cy), (MA * 0.92, ma * 0.92), ang), 255, -1)
        full = cv2.GaussianBlur(full, (0, 0), 1.2).astype(np.float32) / 255 * ((ell > 0) & (cv2.dilate(red_mask(a), np.ones((5, 5), np.uint8)) > 0))
        a = (a * (1 - full[..., None] * 0.92) + np.array([245, 245, 250]) * full[..., None] * 0.92).astype(np.uint8)
    return a, len(cs)


def add_sticker(a, cx, cy, ax, ay, ang=0):
    """스티커가 빠진 컷(S07f) — 빨간 원 스티커를 그린다(뚜껑 위, 원근 타원)."""
    out = a.copy()
    cv2.ellipse(out, (cx, cy), (ax, ay), ang, 0, 360, (40, 36, 210), -1, cv2.LINE_AA)
    hi = out.copy(); cv2.ellipse(hi, (cx - ax // 4, cy - ay // 3), (ax // 2, ay // 3), ang, 0, 360, (90, 90, 235), -1, cv2.LINE_AA)
    out = cv2.addWeighted(out, 0.85, hi, 0.15, 0)
    return cv2.GaussianBlur(out, (0, 0), 1.0)


def blur_regions(a, boxes, sigma=9):
    m = np.zeros(a.shape[:2], np.float32)
    for x0, y0, x1, y1 in boxes:
        m[y0:y1, x0:x1] = 1
    m = cv2.GaussianBlur(m, (0, 0), 12)[..., None]
    return (a * (1 - m) + cv2.GaussianBlur(a, (0, 0), sigma) * m).astype(np.uint8)


def photo_in(a, quad, src, border=0.10):
    q = np.array(quad, np.float32); c = q.mean(axis=0); q = c + (q - c) * (1 - 2 * border)
    s = cv2.imread(src); h, w = s.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), q)
    warp = cv2.warpPerspective(s, M, (a.shape[1], a.shape[0]))
    m = cv2.warpPerspective(np.full((h, w), 255, np.uint8), M, (a.shape[1], a.shape[0]))
    m = cv2.GaussianBlur(m, (0, 0), 1.2).astype(np.float32)[..., None] / 255
    warp = cv2.addWeighted(warp, 0.82, np.full_like(warp, 40), 0.18, 0)  # 빛바랜 사진·조명
    return (a * (1 - m) + warp * m).astype(np.uint8)


def crop_up(a, x0, y0, x1, y1):
    return cv2.resize(a[y0:y1, x0:x1], (a.shape[1], a.shape[0]), interpolation=cv2.INTER_LANCZOS4)


QUAD = {
    "H1": (letter_canvas, [(1250, 720), (1900, 800), (2150, 1440), (1120, 1440)]),
    "H3": (sign_canvas, [(1480, 196), (2274, 196), (2274, 430), (1480, 430)]),
    "S01a": (notice_canvas, [(2030, 500), (2120, 476), (2124, 876), (2030, 840)]),
    "S05a": (price_canvas, [(260, 710), (424, 690), (468, 1000), (296, 1024)]),
    "S12a": (envelope_back_canvas, [(276, 820), (1210, 320), (2284, 584), (1480, 1330)]),  # 네 방향 비교 후 똑바로 읽히는 순서
}
STICKER = {"S01c": None, "S01d": None, "S02a": None, "S05a": (250, 650, 480, 860), "S12p": None, "S13a": None, "S15a": (1100, 430, 1560, 880)}
BLUR = {"S12o": [(420, 0, 1060, 270), (1680, 0, 1790, 140)], "S11b": [(1150, 300, 1490, 1310)]}


def main():
    os.makedirs(BAK, exist_ok=True)
    jobs = sorted(set(QUAD) | set(STICKER) | set(BLUR) | {"S07f", "S12o", "S02a"})
    for sid in jobs:
        p = os.path.join(KF, f"{sid}-1.png"); b = os.path.join(BAK, f"{sid}-1.png")
        if not os.path.exists(b):
            shutil.copy(p, b)
        a = cv2.imread(b)
        if sid == "S02a":  # 머리 없는 듯한 인물 → 손·스티커만 남게 크롭(무료, 1.67배)
            a = crop_up(a, 0, 216, 1536, 1080)
        if sid in QUAD:
            mk, quad = QUAD[sid]
            im = paste_quad(Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB)), mk(), quad)
            a = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
        if sid == "S07f":
            a = add_sticker(a, 1430, 650, 150, 52, -2)
        if sid in STICKER or sid == "S07f":
            a, n = sticker(a, box=STICKER.get(sid))
            print(sid, "스티커", n)
        if sid == "S12o":
            a = photo_in(a, [(2130, 1210), (2320, 1290), (2220, 1424), (2020, 1340)], os.path.join(KF, "S14b-1.png"))
        if sid in BLUR:
            a = blur_regions(a, BLUR[sid])
        cv2.imwrite(p, a)
        print("합성", sid)


if __name__ == "__main__":
    main()
