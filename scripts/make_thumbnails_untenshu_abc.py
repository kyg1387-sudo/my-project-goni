#!/usr/bin/env python3
"""『運転手のくせに』 A/B/C 테스트 썸네일 3종(1280x720, 무과금·로컬, 승인 키프레임만) — 고니감독님 2026-10-15 기획.
  A 화려한 만화/웹툰풍(30~40대 직장인·젊은 층): 공황 大塚 + 오른쪽 로우앵글 黒田, 번개·불꽃·집중선, 「怒鳴った運転手は… 会長だった」
  B 결말 충격형 도게자(사이다 매니아): 스포트라이트 속 무릎 꿇은 大塚(버즈아이), 흰 극태 고딕 + 두꺼운 검정 외곽선
  C 정통 TV 드라마풍(50~60대 시니어): 효과 없이 실제 드라마 캡처처럼 어깨 너머 黒田, 하단 중앙 흰 명조 + 은은한 글로우
오른쪽 아래(재생 시간 표시)는 비운다. 피·폭력 없음. 실존 기업명 없음.
사용법: make_thumbnails_untenshu_abc.py [out_dir]  (기본 assets/thumbnails/untenshu)
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "assets", "portraits", "untenshu-keyframes")
GOTH = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")
MIN = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")
W, H = 1280, 720


def kf(name):
    return Image.open(os.path.join(K, f"{name}-1.png")).convert("RGB")


def cover(im, w, h, cx=0.5, cy=0.5, zoom=1.0):
    s = max(w / im.width, h / im.height) * zoom
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = int(min(max(im.width * cx - w / 2, 0), im.width - w)); y = int(min(max(im.height * cy - h / 2, 0), im.height - h))
    return im.crop((x, y, x + w, y + h))


def font(p, s):
    return ImageFont.truetype(p, s)


def text3d(im, xy, text, f, fill=(255, 255, 255), stroke=(0, 0, 0), sw=10, depth=7, shadow=(0, 0, 0)):
    """굵은 외곽선 + 입체 그림자(오른쪽 아래로 depth 겹)."""
    d = ImageDraw.Draw(im)
    x, y = xy
    for k in range(depth, 0, -1):
        d.text((x + k, y + k), text, font=f, fill=shadow, stroke_width=sw, stroke_fill=shadow)
    d.text((x, y), text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)


def gradient_text(im, xy, text, f, top, bottom, sw=11, depth=8):
    """빨강→노랑 그라데이션 글자 + 검정 외곽선 + 입체 그림자."""
    x, y = xy
    d = ImageDraw.Draw(im)
    for k in range(depth, 0, -1):
        d.text((x + k, y + k), text, font=f, fill=(0, 0, 0), stroke_width=sw, stroke_fill=(0, 0, 0))
    d.text((x, y), text, font=f, fill=(0, 0, 0), stroke_width=sw, stroke_fill=(0, 0, 0))
    bb = d.textbbox((x, y), text, font=f)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).text((x, y), text, font=f, fill=255)
    g = Image.new("RGB", im.size)
    gd = ImageDraw.Draw(g)
    for yy in range(bb[1], bb[3] + 1):
        t = (yy - bb[1]) / max(bb[3] - bb[1], 1)
        gd.line([(bb[0], yy), (bb[2], yy)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    im.paste(g, (0, 0), m)


def lightning(size, start, end, seed, width=5, color=(255, 240, 160)):
    """번개(흰 심 + 노란·푸른 글로우)를 RGBA 레이어로."""
    rnd = random.Random(seed)
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    pts = [start]
    n = 9
    for i in range(1, n):
        t = i / n
        x = start[0] + (end[0] - start[0]) * t + rnd.uniform(-38, 38)
        y = start[1] + (end[1] - start[1]) * t + rnd.uniform(-14, 14)
        pts.append((x, y))
    pts.append(end)
    glow = Image.new("RGBA", size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.line(pts, fill=color + (230,), width=width * 5, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(9))
    lay.alpha_composite(glow)
    d = ImageDraw.Draw(lay)
    d.line(pts, fill=color + (255,), width=width + 2, joint="curve")
    d.line(pts, fill=(255, 255, 255, 255), width=max(width - 2, 2), joint="curve")
    # 잔가지
    for j in range(2):
        a = rnd.randint(2, n - 3); bx, by = pts[a]
        br = [(bx, by)]
        for _ in range(3):
            bx += rnd.uniform(-60, 20); by += rnd.uniform(15, 45); br.append((bx, by))
        d.line(br, fill=color + (220,), width=max(width - 2, 2))
    return lay


def speed_lines(size, center, seed, n=110, inner=230, color=(255, 255, 255), alpha=70):
    rnd = random.Random(seed)
    lay = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = center
    for _ in range(n):
        a = rnd.uniform(0, 2 * math.pi); w = rnd.uniform(0.004, 0.012)
        r0 = inner + rnd.uniform(0, 120); r1 = 1600
        p = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
             (cx + r1 * math.cos(a - w), cy + r1 * math.sin(a - w)),
             (cx + r1 * math.cos(a + w), cy + r1 * math.sin(a + w))]
        d.polygon(p, fill=color + (alpha,))
    return lay


def flames(size, seed, base_y, height=260):
    """화면 아래쪽 불꽃(노이즈 혀 모양 + 주황·빨강 그라데이션 + 글로우)."""
    rnd = random.Random(seed)
    w, h = size
    m = Image.new("L", size, 0); d = ImageDraw.Draw(m)
    x = -20
    while x < w + 20:
        tw = rnd.randint(40, 90); th = rnd.randint(int(height * 0.4), height)
        d.polygon([(x, base_y), (x + tw * 0.5 + rnd.uniform(-15, 15), base_y - th), (x + tw, base_y)], fill=255)
        x += tw * 0.6
    if base_y < h:
        d.rectangle((0, base_y, w, h), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(10))
    col = Image.new("RGB", size); cd = ImageDraw.Draw(col)
    for y in range(h):
        t = min(max((base_y - y) / height, 0), 1)
        c = (255, int(70 + 180 * t), int(10 + 40 * t)) if t > 0.0 else (200, 30, 0)
        cd.line([(0, y), (w, y)], fill=c)
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    lay.paste(col, (0, 0), m.point(lambda v: int(v * 0.85)))
    return lay


def burst_bubble(im, center, rx, ry, text, f, seed):
    """흰 폭발형 말풍선 + 검정 굵은 글자."""
    rnd = random.Random(seed)
    cx, cy = center
    pts = []
    n = 26
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1.0 if i % 2 == 0 else rnd.uniform(0.68, 0.8)
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    d = ImageDraw.Draw(im)
    sh = [(x + 6, y + 6) for x, y in pts]
    d.polygon(sh, fill=(0, 0, 0))
    d.polygon(pts, fill=(255, 255, 255), outline=(0, 0, 0), width=5)
    bb = d.textbbox((0, 0), text, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), text, font=f, fill=(200, 0, 0),
           stroke_width=3, stroke_fill=(0, 0, 0))


def badge(im, xy, text, f, bg=(0, 0, 0), fg=(255, 255, 255), pad=(18, 8)):
    d = ImageDraw.Draw(im)
    bb = d.textbbox(xy, text, font=f)
    d.rectangle((bb[0] - pad[0], bb[1] - pad[1], bb[2] + pad[0], bb[3] + pad[1]), fill=bg)
    d.text(xy, text, font=f, fill=fg)


def vignette(im, strength=0.65):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).ellipse((-im.width * 0.15, -im.height * 0.2, im.width * 1.15, im.height * 1.2), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(160)).point(lambda v: int(255 - (255 - v) * strength))
    return Image.composite(im, Image.new("RGB", im.size), m)


def left_shade(im, frac=0.5, dark=0.82):
    g = Image.new("L", im.size, 0); d = ImageDraw.Draw(g)
    edge = int(im.width * frac)
    for x in range(im.width):
        t = max(0.0, 1 - x / edge) if x < edge else 0.0
        d.line([(x, 0), (x, im.height)], fill=int(255 * dark * min(1, t * 1.4)))
    return Image.composite(Image.new("RGB", im.size), im, g)


def grain(im, amt=10, seed=7):
    rnd = random.Random(seed)
    n = Image.effect_noise(im.size, amt).convert("RGB")
    return ImageChops.add(ImageChops.subtract(im, Image.new("RGB", im.size, (amt // 2,) * 3)), n.point(lambda v: v // 8))


# ───────── A: 화려한 만화/웹툰풍 ─────────
def thumb_a():
    base = cover(kf("S17f"), W, H, cx=0.50, cy=0.40, zoom=1.45)     # 홍조·땀·억지 웃음의 大塚
    base = ImageEnhance.Color(base).enhance(1.35)
    base = ImageEnhance.Contrast(base).enhance(1.15)
    # 붉은-주황 그레이딩
    base = Image.blend(base, Image.new("RGB", base.size, (255, 80, 20)), 0.16)
    # 오른쪽 끝: 로우앵글처럼 올려다보는 黒田(차가운 푸른 톤, 번개 경계)
    kur = cover(kf("S19e"), 380, H, cx=0.33, cy=0.36, zoom=1.35)
    kur = ImageEnhance.Color(kur).enhance(0.7)
    kur = Image.blend(kur, Image.new("RGB", kur.size, (20, 40, 90)), 0.28)
    kur = kur.transform(kur.size, Image.AFFINE, (1, 0, 0, 0, 1, 0))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon([(940, 0), (W, 0), (W, H), (1000, H), (960, 470), (1010, 300), (930, 160)], fill=255)
    canvas = Image.new("RGB", (W, H)); canvas.paste(kur, (W - 380, 0))
    base = Image.composite(canvas, base, mask)
    base = base.convert("RGBA")
    base.alpha_composite(speed_lines((W, H), (720, 260), seed=3, alpha=55))
    base = left_shade(base.convert("RGB"), frac=0.55, dark=0.88).convert("RGBA")
    base.alpha_composite(flames((W, H), seed=5, base_y=H + 10, height=200))
    # 경계 번개 + 위쪽 번개 두 줄
    base.alpha_composite(lightning((W, H), (930, 0), (1000, H), seed=11, width=6, color=(255, 236, 120)))
    base.alpha_composite(lightning((W, H), (470, 0), (560, 150), seed=21, width=4, color=(170, 210, 255)))
    base.alpha_composite(lightning((W, H), (300, 0), (150, 120), seed=31, width=3, color=(255, 236, 120)))
    im = base.convert("RGB")
    badge(im, (34, 26), "スカッとする話", font(GOTH, 40))
    text3d(im, (30, 112), "怒鳴った", font(GOTH, 96), sw=10, depth=8)
    text3d(im, (30, 228), "運転手は…", font(GOTH, 96), sw=10, depth=8)
    gradient_text(im, (24, 360), "会長", font(GOTH, 168), (235, 20, 20), (255, 220, 0), sw=12, depth=10)
    text3d(im, (370, 420), "だった", font(GOTH, 104), sw=10, depth=8)
    burst_bubble(im, (700, 92), 160, 84, "違うんです!!", font(GOTH, 50), seed=4)
    # 오른쪽 하단 박스(재생 시간 표시 자리 위)
    d = ImageDraw.Draw(im)
    f = font(GOTH, 54)
    bb = d.textbbox((0, 0), "部長の末路", font=f)
    bx1, by1 = W - 30, H - 96
    bx0, by0 = bx1 - (bb[2] - bb[0]) - 40, by1 - (bb[3] - bb[1]) - 30
    d.rectangle((bx0, by0, bx1, by1), fill=(0, 0, 0), outline=(255, 214, 0), width=4)
    d.text((bx0 + 20 - bb[0], by0 + 15 - bb[1]), "部長の末路", font=f, fill=(255, 220, 0))
    return im


# ───────── B: 결말 충격형 도게자 ─────────
def thumb_b():
    bg = cover(kf("S20d"), W, H, cx=0.42, cy=0.52, zoom=1.22)
    bg = ImageEnhance.Contrast(bg).enhance(1.18)
    bg = ImageEnhance.Color(bg).enhance(0.85)
    bg = Image.blend(bg, Image.new("RGB", bg.size, (20, 26, 36)), 0.10)
    bg = vignette(bg, 0.75)
    bg = left_shade(bg, frac=0.42, dark=0.55)
    badge(bg, (34, 26), "スカッとする話", font(GOTH, 40))
    text3d(bg, (30, 100), "運転手を", font(GOTH, 104), sw=12, depth=6)
    text3d(bg, (30, 226), "怒鳴った部長", font(GOTH, 104), sw=12, depth=6)
    text3d(bg, (30, 400), "翌朝、", font(GOTH, 90), sw=11, depth=6)
    text3d(bg, (30, 500), "土下座", font(GOTH, 128), fill=(255, 225, 0), sw=13, depth=7)
    d = ImageDraw.Draw(bg)
    f = font(MIN, 46)
    d.text((W - 40, 40), "相手は――", font=f, fill=(255, 255, 255), anchor="ra", stroke_width=5, stroke_fill=(0, 0, 0))
    d.text((W - 40, 100), "昨夜の運転手", font=font(MIN, 58), fill=(255, 255, 255), anchor="ra", stroke_width=6, stroke_fill=(0, 0, 0))
    return bg


# ───────── C: 정통 TV 드라마풍 ─────────
def thumb_c():
    bg = cover(kf("S17c"), W, H, cx=0.62, cy=0.40, zoom=1.18)
    bg = ImageEnhance.Color(bg).enhance(0.82)
    bg = ImageEnhance.Contrast(bg).enhance(1.05)
    bg = Image.blend(bg, Image.new("RGB", bg.size, (60, 50, 40)), 0.08)     # 따뜻한 드라마 톤
    g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
    for y in range(int(H * 0.62), H):
        gd.line([(0, y), (W, y)], fill=int(235 * min(1, (y - H * 0.62) / (H * 0.24))))
    bg = Image.composite(Image.new("RGB", (W, H)), bg, g)
    bg = vignette(bg, 0.45)
    bg = grain(bg, 12)
    # 글자: 흰 명조 + 은은한 글로우(외곽선 없음)
    def glow_text(xy, text, f, anchor="ma", alpha=170):
        lay = Image.new("L", (W, H), 0)
        ImageDraw.Draw(lay).text(xy, text, font=f, fill=255, anchor=anchor)
        gl = lay.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * alpha / 255))
        nonlocal bg
        bg = Image.composite(Image.new("RGB", (W, H), (255, 236, 200)), bg, gl)
        ImageDraw.Draw(bg).text(xy, text, font=f, fill=(255, 255, 255), anchor=anchor)
    glow_text((W // 2, 492), "タクシーで怒鳴りつけた運転手は", font(MIN, 50), alpha=120)
    glow_text((W // 2, 566), "取引先の会長だった", font(MIN, 96), alpha=160)
    d = ImageDraw.Draw(bg)
    d.text((44, 36), "「昨夜は、どうも」", font=font(MIN, 44), fill=(240, 236, 228))
    return bg


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "thumbnails", "untenshu")
    os.makedirs(out, exist_ok=True)
    for name, fn in (("A-manga", thumb_a), ("B-dogeza", thumb_b), ("C-drama", thumb_c)):
        p = os.path.join(out, f"untenshu-thumb-{name}-JP.jpg")
        fn().save(p, quality=93); print("저장:", p)


if __name__ == "__main__":
    main()
