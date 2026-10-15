#!/usr/bin/env python3
"""『運転手のくせに』 A/B/C 테스트 썸네일 3종(1280x720, 무과금·로컬, 승인 키프레임만) — 고니감독님 2026-10-15 기획.
  A 화려한 만화/웹툰풍(30~40대 직장인·젊은 층): 공황 大塚 + 오른쪽 로우앵글 黒田, 번개·불꽃·집중선, 「怒鳴った運転手は… 会長だった」
  B 결말 충격형(사이다 매니아, 고니감독님 예시 형식): 눈물 흘리는 大塚 얼굴 + 상황 3줄 + 거대 인용구 「運転手のくせに」
  C 정통 TV 드라마풍(50~60대 시니어, 고니감독님 예시 형식): 택시 안 黒田와 사진을 내미는 小川, 빨강 제목 2줄 + 노란 박스
오른쪽 아래(재생 시간 표시)는 비운다. 피·폭력 없음. 실존 기업명 없음.
사용법: make_thumbnails_untenshu_abc.py [out_dir]  (기본 assets/thumbnails/untenshu)
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

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
    """B안(2026-10-15 고니감독님 예시 형식): 오른쪽 눈물·식은땀의 大塚 얼굴 크게(S19c 좌우 반전), 어두운 배경 +
    위 조명, 왼쪽 상황 3줄(흰 극태 고딕), 아래 거대한 인용구 「運転手のくせに」(명조, 빨강→노랑 + 붉은 글로우)."""
    src = ImageOps.mirror(kf("S19c"))
    bg = cover(src, W, H, cx=0.57, cy=0.36, zoom=1.3)
    bg = ImageEnhance.Color(bg).enhance(0.75)
    bg = ImageEnhance.Contrast(bg).enhance(1.12)
    bg = ImageEnhance.Brightness(bg).enhance(0.62)
    bg = Image.blend(bg, Image.new("RGB", bg.size, (14, 22, 30)), 0.22)
    # 얼굴에 빛을 남기고 나머지를 어둡게(위 조명)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse((640, 20, 1240, 660), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(110))
    lit = ImageEnhance.Brightness(cover(src, W, H, cx=0.57, cy=0.36, zoom=1.3)).enhance(0.95)
    lit = ImageEnhance.Color(lit).enhance(0.85)
    bg = Image.composite(lit, bg, m)
    bg = vignette(bg, 0.7)
    bg = left_shade(bg, frac=0.5, dark=0.6)
    for k, line in enumerate(["タクシーで", "怒鳴った部長に", "会長は言った…"]):
        text3d(bg, (40, 120 + k * 112), line, font(GOTH, 84), sw=8, depth=5)
    # 아래 인용구: 붉은 글로우 → 그라데이션 글자
    q = "「運転手のくせに」"
    fq = font(MIN, 150)
    d = ImageDraw.Draw(bg)
    bb = d.textbbox((0, 0), q, font=fq)
    x = (W - (bb[2] - bb[0])) // 2 - bb[0] - 20; y = 505
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).text((x, y), q, font=fq, fill=255, stroke_width=18, stroke_fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.85))
    bg = Image.composite(Image.new("RGB", (W, H), (200, 20, 10)), bg, glow)
    gradient_text(bg, (x, y), q, fq, (255, 236, 90), (225, 25, 15), sw=9, depth=0)
    return bg


# ───────── C: 정통 TV 드라마풍(2026-10-15 고니감독님 예시 형식) ─────────
def thumb_c():
    """택시 안 黒田(기사)와 아내 사진을 내미는 小川(S10b), 따뜻한 앰버 톤. 위 오른쪽 둥근 검정 배지 + 빨강 제목 2줄
    (끝 낱말만 노랑), 아래 반투명 검정 박스에 노란 2줄."""
    bg = cover(kf("S10b"), W, H, cx=0.5, cy=0.55, zoom=1.0)
    bg = ImageEnhance.Color(bg).enhance(0.9)
    bg = Image.blend(bg, Image.new("RGB", bg.size, (120, 70, 25)), 0.16)      # 따뜻한 앰버
    bg = ImageEnhance.Contrast(bg).enhance(1.08)
    bg = vignette(bg, 0.5)
    g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)                     # 위쪽 제목 자리 어둡게
    for y in range(0, 220):
        gd.line([(0, y), (W, y)], fill=int(170 * (1 - y / 220)))
    bg = Image.composite(Image.new("RGB", (W, H)), bg, g)
    d = ImageDraw.Draw(bg)
    # 배지(둥근 검정 + 흰 테)
    fb = font(GOTH, 42)
    bb = d.textbbox((0, 0), "スカッとする話", font=fb)
    bw, bh = bb[2] - bb[0] + 48, bb[3] - bb[1] + 26
    bx = 30; by = 22
    d.rounded_rectangle((bx, by, bx + bw, by + bh), 14, fill=(0, 0, 0), outline=(255, 255, 255), width=3)
    d.text((bx + 24 - bb[0], by + 13 - bb[1]), "スカッとする話", font=fb, fill=(255, 255, 255))
    red_top, red_bot = (255, 70, 60), (190, 10, 10)
    def title(xy, text, f, top, bot):
        x, y = xy
        ImageDraw.Draw(bg).text((x + 4, y + 5), text, font=f, fill=(0, 0, 0), stroke_width=12, stroke_fill=(0, 0, 0))
        ImageDraw.Draw(bg).text((x, y), text, font=f, fill=(255, 255, 255), stroke_width=9, stroke_fill=(255, 255, 255))
        gradient_text(bg, (x, y), text, f, top, bot, sw=0, depth=0)
    f1 = font(GOTH, 64)
    t1 = "床に落ちた妻の写真…"
    w1 = d.textlength(t1, font=f1)
    title((W - 36 - w1, 14), t1, f1, red_top, red_bot)
    f2 = font(GOTH, 76)
    a2, b2 = "拾った部下の", "運命"
    wa, wb = d.textlength(a2, font=f2), d.textlength(b2, font=f2)
    x2 = W - 36 - (wa + wb)
    title((x2, 96), a2, f2, red_top, red_bot)
    title((x2 + wa, 96), b2, f2, (255, 250, 150), (255, 190, 0))
    # 아래 반투명 박스
    fb2 = font(GOTH, 50)
    lines = ["その運転手は、", "取引先の会長だった"]
    x0, y0 = 420, 572
    wmax = max(d.textlength(s, font=fb2) for s in lines)
    box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(box).rectangle((x0, y0, x0 + wmax + 50, y0 + 140), fill=(0, 0, 0, 175))
    bg = bg.convert("RGBA"); bg.alpha_composite(box); bg = bg.convert("RGB")
    d = ImageDraw.Draw(bg)
    for k, s in enumerate(lines):
        d.text((x0 + 25, y0 + 12 + k * 64), s, font=fb2, fill=(255, 222, 40), stroke_width=2, stroke_fill=(0, 0, 0))
    return bg


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "thumbnails", "untenshu")
    os.makedirs(out, exist_ok=True)
    for name, fn in (("A-manga", thumb_a), ("B-dogeza", thumb_b), ("C-drama", thumb_c)):
        p = os.path.join(out, f"untenshu-thumb-{name}-JP.jpg")
        fn().save(p, quality=93); print("저장:", p)


if __name__ == "__main__":
    main()
