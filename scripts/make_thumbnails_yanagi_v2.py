#!/usr/bin/env python3
"""『柳の葉と一杯の水』 썸네일 A/B 테스트 2차 3종(1280x720, 무과금·로컬, 승인 키프레임만 사용).
감독님 요청(2026-10-10, 스포츠 하이라이트 포스터 기법 분석 반영):
  A 만화·웹툰풍 — 툰 외곽선·하프톤·붉은 번개·잉크 스플래터·기울어진 3D 금속 글자 → 30~40대
  B 결말 충격형 — 도게자(수직 부감) + 위에서 내려다보는 회장 → 사이다 매니아
  C 정통 TV 드라마풍 — 이펙트 없음, 시네마 레터박스·명조 자막 → 50~60대 시니어
오른쪽 아래(재생 시간 표시)는 비운다. 피·폭력 없음.
사용법: make_thumbnails_yanagi_v2.py [out_dir]
"""
import os
import random
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "assets", "portraits", "yanagi-keyframes")
GOTHIC = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")
MINCHO = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")
W, H = 1280, 720


def kf(name):
    return cv2.cvtColor(cv2.imread(os.path.join(K, f"{name}-1.png")), cv2.COLOR_BGR2RGB)


def to_pil(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def cover(a, w, h, cx=0.5, cy=0.5, zoom=1.0):
    """비율 유지 확대(zoom 배) 후 중심(cx, cy) 기준으로 w x h 크롭."""
    s = max(w / a.shape[1], h / a.shape[0]) * zoom
    b = cv2.resize(a, (round(a.shape[1] * s), round(a.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
    x = int(np.clip(b.shape[1] * cx - w / 2, 0, b.shape[1] - w))
    y = int(np.clip(b.shape[0] * cy - h / 2, 0, b.shape[0] - h))
    return b[y:y + h, x:x + w]


def cutout(a, rect):
    """GrabCut 인물 분리 → 부드러운 알파(0~1)."""
    mask = np.zeros(a.shape[:2], np.uint8)
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), mask, rect, bg, fg, 6, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 1.0, 0.0).astype(np.float32)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cs, _ = cv2.findContours((m > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    full = np.zeros_like(m)
    if cs:
        cv2.drawContours(full, [max(cs, key=cv2.contourArea)], -1, 1.0, -1)   # 가장 큰 덩어리만, 내부 구멍 채움
    return cv2.GaussianBlur(full, (0, 0), 1.5)


def toon(a, halftone=True):
    """툰 셰이딩: 색 단순화 + 굵은 잉크 외곽선 + 어두운 면 하프톤 점."""
    sm = cv2.bilateralFilter(a, 9, 60, 60)
    q = (sm // 36) * 36 + 18                                   # 포스터라이즈
    out = cv2.addWeighted(sm, 0.55, q.astype(np.uint8), 0.45, 0).astype(np.float32)
    g = cv2.cvtColor(sm, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(g, 40, 110)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8))
    out[edges > 0] *= 0.08
    if halftone:
        dots = np.zeros(g.shape, np.uint8)
        for y in range(0, g.shape[0], 9):
            for x in range((y // 9) % 2 * 4, g.shape[1], 9):
                v = g[y, x]
                if v < 110:
                    cv2.circle(dots, (x, y), max(1, int((110 - v) / 32)), 255, -1)
        out[dots > 0] *= 0.55
    out = (out - 128) * 1.18 + 128                              # 대비 강조
    return np.clip(out, 0, 255)


def lightning(size, seed, n=7, color=(255, 70, 20), core=(255, 235, 200), around=None):
    """프랙털 번개 레이어(RGBA). around=(cx, cy, rx, ry) 주변에서 바깥으로 뻗는다."""
    rnd = random.Random(seed)
    w, h = size
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    lines = Image.new("RGBA", size, (0, 0, 0, 0))
    dg, dl = ImageDraw.Draw(glow), ImageDraw.Draw(lines)

    def bolt(p, q, depth):
        if depth == 0:
            return [p, q]
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        L = ((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2) ** 0.5
        mx += rnd.uniform(-1, 1) * L * 0.22
        my += rnd.uniform(-1, 1) * L * 0.22
        return bolt(p, (mx, my), depth - 1)[:-1] + bolt((mx, my), q, depth - 1)

    for _ in range(n):
        if around:
            cx, cy, rx, ry = around
            ang = rnd.uniform(0, 6.283)
            import math
            p = (cx + math.cos(ang) * rx * 0.8, cy + math.sin(ang) * ry * 0.8)
            q = (cx + math.cos(ang) * rx * 2.2 + rnd.uniform(-60, 60), cy + math.sin(ang) * ry * 2.0 + rnd.uniform(-60, 60))
        else:
            p = (rnd.uniform(0, w), rnd.uniform(0, h)); q = (rnd.uniform(0, w), rnd.uniform(0, h))
        pts = bolt(p, q, 6)
        dg.line(pts, fill=color + (230,), width=16)
        dl.line(pts, fill=core + (255,), width=3)
        for k in range(rnd.randint(1, 3)):                       # 가지
            i = rnd.randrange(len(pts) // 3, len(pts))
            b = pts[i]
            e = (b[0] + rnd.uniform(-160, 160), b[1] + rnd.uniform(-160, 160))
            bp = bolt(b, e, 4)
            dg.line(bp, fill=color + (200,), width=9)
            dl.line(bp, fill=core + (230,), width=2)
    glow = glow.filter(ImageFilter.GaussianBlur(9))
    return Image.alpha_composite(glow, lines)


def splatter(size, seed, n=60, color=(10, 6, 4), edge_only=True):
    rnd = random.Random(seed)
    w, h = size
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        if edge_only:
            side = rnd.choice("lrtb")
            x = rnd.uniform(0, 90) if side == "l" else rnd.uniform(w - 90, w) if side == "r" else rnd.uniform(0, w)
            y = rnd.uniform(0, 70) if side == "t" else rnd.uniform(h - 70, h) if side == "b" else rnd.uniform(0, h)
        else:
            x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.choice([2, 3, 4, 6, 9, 14, 22])
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (rnd.randint(150, 240),))
        for _ in range(rnd.randint(0, 5)):                        # 튄 방울
            a = rnd.uniform(0, 6.283); dist = r + rnd.uniform(4, 30)
            import math
            sx, sy = x + math.cos(a) * dist, y + math.sin(a) * dist
            rr = max(1, r // rnd.randint(3, 6))
            d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=color + (200,))
    return lay.filter(ImageFilter.GaussianBlur(0.6))


def text_layer(s, font, size, fill, stroke, stroke_w, extrude=0, extrude_color=(60, 0, 0), shear=0.0,
               gradient=None, outer=None, outer_w=0):
    """글자 레이어(RGBA): 바깥 테두리·3D 돌출·그라데이션 채움·기울기(이탤릭)."""
    f = ImageFont.truetype(font, size)
    pad = stroke_w + outer_w + extrude + 20
    bbox = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), s, font=f)
    w, h = bbox[2] - bbox[0] + pad * 2, bbox[3] - bbox[1] + pad * 2
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    o = (pad - bbox[0], pad - bbox[1])
    for k in range(extrude, 0, -1):                              # 3D 돌출(오른쪽 아래)
        d.text((o[0] + k, o[1] + k), s, font=f, fill=extrude_color, stroke_width=stroke_w + outer_w, stroke_fill=extrude_color)
    if outer:
        d.text(o, s, font=f, fill=outer, stroke_width=stroke_w + outer_w, stroke_fill=outer)
    d.text(o, s, font=f, fill=stroke, stroke_width=stroke_w, stroke_fill=stroke)
    if gradient:                                                  # 금속 그라데이션 채움
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).text(o, s, font=f, fill=255)
        g = Image.new("RGB", (w, h))
        top, mid, bot = gradient
        gd = ImageDraw.Draw(g)
        for y in range(h):
            t = (y - pad) / max(1, h - 2 * pad)
            c = [int(top[i] + (mid[i] - top[i]) * min(1, t * 2)) if t < 0.5 else int(mid[i] + (bot[i] - mid[i]) * (t - 0.5) * 2) for i in range(3)]
            gd.line([(0, y), (w, y)], fill=tuple(max(0, min(255, v)) for v in c))
        lay.paste(g, (0, 0), m)
    else:
        d.text(o, s, font=f, fill=fill)
    if shear:
        lay = lay.transform((w + int(abs(shear) * h), h), Image.AFFINE, (1, shear, -abs(shear) * h if shear > 0 else 0, 0, 1, 0),
                            resample=Image.BICUBIC)
    return lay


def banner(s, size=46, color=(214, 20, 24)):
    f = ImageFont.truetype(GOTHIC, size)
    tw = ImageDraw.Draw(Image.new("L", (1, 1))).textlength(s, font=f)
    w, h = int(tw) + 90, size + 34
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.polygon([(22, 0), (w, 0), (w - 22, h), (0, h)], fill=(0, 0, 0, 255))
    d.polygon([(26, 4), (w - 6, 4), (w - 26, h - 4), (4, h - 4)], fill=color + (255,))
    d.text((45, 10), s, font=f, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    return lay.transform((w, h), Image.AFFINE, (1, 0.12, -0.06 * h, 0, 1, 0), resample=Image.BICUBIC)


def grain(a, amt=7, seed=1):
    n = np.random.default_rng(seed).normal(0, amt, a.shape[:2])[..., None]
    return np.clip(a + n, 0, 255)


def vignette(a, k=0.55):
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    r = np.sqrt(((xx - a.shape[1] / 2) / (a.shape[1] / 2)) ** 2 + ((yy - a.shape[0] / 2) / (a.shape[0] / 2)) ** 2)
    return a * (1 - k * np.clip(r - 0.35, 0, 1))[..., None]


# ---------------------------------------------------------------- A 만화·웹툰풍
def thumb_a():
    # 배경: 매장 내부(회장 판결 컷 배경)를 흐리고 붉게 + 방사형 집중선
    src = kf("S27g")
    bg = cv2.GaussianBlur(cover(src, W, H, 0.5, 0.45), (0, 0), 10).astype(np.float32)
    bg = bg * np.array([1.0, 0.35, 0.25]) * 0.55 + np.array([70, 0, 0])
    bgi = to_pil(vignette(bg, 0.7)).convert("RGBA")
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rays)
    rnd = random.Random(3)
    cx, cy = 900, 330
    import math
    for i in range(90):
        a = i / 90 * 6.283 + rnd.uniform(-0.02, 0.02)
        r1, r2 = rnd.uniform(240, 330), 1500
        wdt = rnd.uniform(0.004, 0.014)
        dr.polygon([(cx + math.cos(a) * r1, cy + math.sin(a) * r1),
                    (cx + math.cos(a - wdt) * r2, cy + math.sin(a - wdt) * r2),
                    (cx + math.cos(a + wdt) * r2, cy + math.sin(a + wdt) * r2)], fill=(255, 190, 120, rnd.randint(25, 70)))
    bgi = Image.alpha_composite(bgi, rays)
    # 번개(인물 뒤)
    bgi = Image.alpha_composite(bgi, lightning((W, H), 11, n=8, around=(900, 330, 210, 260)))
    # 주인공: 회장(툰 처리, 크게) — 오른쪽
    alpha = cutout(src, (360, 10, 600, 758))
    t = toon(src)
    rgba = np.dstack([t, alpha * 255]).astype(np.uint8)
    ch = Image.fromarray(rgba, "RGBA").crop((330, 0, 1000, 768))
    ch = ch.resize((int(ch.width * 0.98), int(ch.height * 0.98)), Image.LANCZOS)
    # 인물 외곽 흰 테두리(만화 컷 느낌)
    edge = ch.split()[3].filter(ImageFilter.MaxFilter(9))
    outline = Image.new("RGBA", ch.size, (255, 240, 220, 0)); outline.putalpha(edge.point(lambda v: 255 if v > 60 else 0))
    bgi.alpha_composite(outline, (560, -4)); bgi.alpha_composite(ch, (560, -4))
    # 번개(인물 앞, 가장자리만)
    bgi = Image.alpha_composite(bgi, lightning((W, H), 29, n=4, around=(900, 380, 240, 300)))
    # 과거 컷: 쫓겨난 노인(툰, 기울어진 패널) — 왼쪽 아래
    old = cover(kf("S02b"), 400, 300, 0.58, 0.42)
    op = to_pil(toon(old)).convert("RGBA")
    panel = Image.new("RGBA", (420, 320), (0, 0, 0, 255)); panel.paste(op, (10, 10))
    ImageDraw.Draw(panel).rectangle([10, 10, 409, 309], outline=(255, 255, 255), width=6)
    panel = panel.rotate(5, expand=True, resample=Image.BICUBIC)
    bgi.alpha_composite(panel, (36, 380))
    cap = text_layer("三日前", GOTHIC, 34, (255, 255, 255), (0, 0, 0), 6, shear=0.18)
    bgi.alpha_composite(cap, (60, 360))
    # 글자: 배너 + 3D 금속 글자(기울임)
    bgi.alpha_composite(banner("スカッと大逆転！", 44), (28, 22))
    t1 = text_layer("追い出した老人は", GOTHIC, 70, (255, 255, 255), (0, 0, 0), 10, extrude=6, extrude_color=(40, 0, 0), shear=0.2)
    bgi.alpha_composite(t1, (18, 104))
    t2 = text_layer("会長", GOTHIC, 200, None, (20, 0, 0), 14, extrude=14, extrude_color=(110, 10, 0), shear=0.22,
                    gradient=((255, 250, 210), (255, 196, 40), (200, 90, 0)), outer=(255, 255, 255), outer_w=6)
    bgi.alpha_composite(t2, (6, 178))
    t3 = text_layer("だった!!", GOTHIC, 92, (255, 255, 255), (0, 0, 0), 12, extrude=8, extrude_color=(80, 0, 0), shear=0.22)
    bgi.alpha_composite(t3, (440, 254))
    bgi = Image.alpha_composite(bgi, splatter((W, H), 7, n=70))
    return bgi.convert("RGB")


# ---------------------------------------------------------------- B 결말 충격형
def thumb_b():
    d = cover(kf("S27e"), W, H, 0.405, 0.45, zoom=1.28).astype(np.float32)   # 점장이 화면 오른쪽 아래 중앙에 오도록
    d = (d - 128) * 1.15 + 118
    d = d * np.array([0.92, 0.98, 1.06])                         # 차가운 형광등 톤
    img = to_pil(vignette(d, 0.65)).convert("RGBA")
    # 위에서 내려다보는 회장 — 오른쪽 위 원형 인서트(냉정한 시선)
    og = cover(kf("S27g"), 290, 290, 0.5, 0.3)
    ogp = to_pil(og * np.array([0.95, 0.98, 1.05])).convert("RGBA")
    m = Image.new("L", (290, 290), 0); ImageDraw.Draw(m).ellipse([0, 0, 289, 289], fill=255)
    ring = Image.new("RGBA", (306, 306), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([0, 0, 305, 305], fill=(255, 255, 255, 255))
    img.alpha_composite(ring, (950, 18)); img.paste(ogp, (958, 26), m)
    # 거친 붉은 띠 + 글자
    img.alpha_composite(banner("三日後――", 46, (20, 20, 20)), (26, 24))
    t1 = text_layer("土下座", GOTHIC, 176, None, (0, 0, 0), 14, extrude=10, extrude_color=(90, 0, 0), shear=0.16,
                    gradient=((255, 120, 100), (230, 0, 0), (140, 0, 0)), outer=(255, 255, 255), outer_w=7)
    img.alpha_composite(t1, (10, 96))
    t2 = text_layer("店長代理の末路", GOTHIC, 72, (255, 255, 255), (0, 0, 0), 12, extrude=6, extrude_color=(60, 0, 0), shear=0.16)
    img.alpha_composite(t2, (12, 330))
    img = Image.alpha_composite(img, splatter((W, H), 21, n=40))
    return img.convert("RGB")


# ---------------------------------------------------------------- C 정통 TV 드라마풍
def thumb_c():
    a = cover(kf("S26g"), W, H, 0.40, 0.40, zoom=1.12).astype(np.float32)
    a = a * np.array([1.04, 0.99, 0.92])                         # 따뜻한 필름 톤
    a = (a - 128) * 0.96 + 126
    a = grain(vignette(a, 0.5), 5)
    img = to_pil(a)
    # 시네마 레터박스
    bar = 74
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, bar], fill=(0, 0, 0)); d.rectangle([0, H - bar, W, H], fill=(0, 0, 0))
    # 명조 자막(드라마 타이틀 느낌) — 왼쪽, 얼굴 피함
    def mtext(xy, s, size, fill=(255, 255, 255)):
        f = ImageFont.truetype(MINCHO, size)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 4), s, font=f, fill=(0, 0, 0, 200))
        img.paste(Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(4))).convert("RGB"))
        ImageDraw.Draw(img).text(xy, s, font=f, fill=fill)
    mtext((60, 118), "六十年前の", 92, (255, 246, 228))
    mtext((60, 228), "一杯の水が", 92, (255, 246, 228))
    mtext((60, 338), "つないだもの", 92, (255, 214, 140))
    f = ImageFont.truetype(MINCHO, 30)
    ImageDraw.Draw(img).text((64, 468), "老人を追い出した店長代理と、", font=f, fill=(225, 220, 210))
    ImageDraw.Draw(img).text((64, 510), "ひとりの店員の物語", font=f, fill=(225, 220, 210))
    ImageDraw.Draw(img).text((40, 20), "美談ものがたり", font=ImageFont.truetype(MINCHO, 30), fill=(210, 190, 150))
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "productions", "willow-leaf-ja", "thumbnails", "v2")
    os.makedirs(out, exist_ok=True)
    for name, fn in (("A-만화이펙트", thumb_a), ("B-도게자결말", thumb_b), ("C-TV드라마", thumb_c)):
        p = os.path.join(out, f"yanagi-thumb2-{name}.jpg")
        fn().save(p, quality=92)
        print(p, os.path.getsize(p) // 1024, "KB")
