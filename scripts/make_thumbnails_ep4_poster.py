#!/usr/bin/env python3
"""EP4 썸네일 A·B 「포스터 그래픽」 테스트판(1280x720). 무과금, 로컬.

스포츠 하이라이트 포스터 기법을 인정극 톤으로 옮긴다:
  다중 레이어(배경 → 빛 에너지 → 조연 인물 → 거대 클로즈업), 일러스트화(포스터라이즈·먹선·하프톤),
  에너지 이펙트(번개 대신 금빛 섬광·불꽃·눈), 그런지 스플래터, 사선 3D 오버사이즈 글자, 레드·골드 강조 보정.
얼굴은 원본 질감을 유지(가벼운 일러스트화)해 일그러짐 인상을 피한다. 글자는 얼굴을 덮지 않는다. 「実話」 금지.

필요: pip install "rembg[cpu]" (최초 1회 isnet-general-use 모델 자동 다운로드)
사용법: make_thumbnails_ep4_poster.py <out_dir> [cache_dir]
"""
import math
import os
import random
import sys

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "assets", "portraits", "ep4-keyframes")
DELA = os.path.join(ROOT, "scripts", "fonts", "DelaGothicOne-Regular.ttf")
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
W, H = 1280, 720
GOLD, RED, WHITE = (255, 200, 60), (210, 28, 36), (255, 255, 255)


# ---------- 소재 ----------
def keyframe(name):
    return Image.open(os.path.join(K, f"{name}-1.png")).convert("RGB")


ERASE = {"S45": [(800, 372, 905, 500)]}   # 누끼에 붙어 남는 소품(원본 좌표, 상자 안 어두운 픽셀만 지움)


def cutout(name, cache):
    """인물 누끼(RGBA). 가장 큰 덩어리만 남겨 창틀·소품 잔여물 제거."""
    p = os.path.join(cache, f"cut_{name}.png")
    if not os.path.exists(p):
        from rembg import new_session, remove
        remove(keyframe(name), session=new_session("isnet-general-use")).save(p)
    im = Image.open(p).convert("RGBA")
    a = np.array(im.split()[3])
    n, lab, st, _ = cv2.connectedComponentsWithStats((a > 128).astype(np.uint8))
    if n > 2:
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        keep = cv2.dilate((lab == big).astype(np.uint8), np.ones((9, 9), np.uint8))
        a = (a * keep).astype(np.uint8)
    if name in ERASE:
        g = np.array(im.convert("L"))
        for x0, y0, x1, y1 in ERASE[name]:
            box = a[y0:y1, x0:x1]
            box[g[y0:y1, x0:x1] < 110] = 0
        a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    im.putalpha(Image.fromarray(a))
    return im


# ---------- 일러스트화 ----------
def toon(rgba, levels=7, line=0.55, halftone=0.35, dot=7):
    """포스터라이즈 + 먹선 + 그림자 하프톤. 알파 유지."""
    rgb = np.array(rgba.convert("RGB"))
    a = np.array(rgba.split()[3])
    sm = rgb
    for _ in range(2):
        sm = cv2.bilateralFilter(sm, 9, 40, 9)
    ycc = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    skin = cv2.inRange(ycc, (40, 135, 85), (255, 175, 135)).astype(np.float32) / 255.0
    skin = cv2.GaussianBlur(skin, (21, 21), 0)
    keep = 1 - skin * 0.8                        # 피부는 단계화·먹선·하프톤을 약하게(주름 과장·얼룩 방지)
    lab = cv2.cvtColor(sm, cv2.COLOR_RGB2LAB).astype(np.float32)
    L = lab[..., 0]
    step = 255.0 / levels
    Lq = np.floor(L / step) * step + step / 2
    q = 0.55 * keep
    lab[..., 0] = L * (1 - q) + Lq * q
    out = cv2.cvtColor(lab.clip(0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    g = cv2.medianBlur(g, 5)
    edges = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 6)
    edges = cv2.GaussianBlur(255 - edges, (3, 3), 0).astype(np.float32) / 255.0
    out *= (1 - edges[..., None] * line * keep[..., None])
    # 하프톤: 어두운 곳일수록 큰 점(45° 격자)
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx + yy) / math.sqrt(2) / dot
    v = (xx - yy) / math.sqrt(2) / dot
    d = np.sqrt((u - np.round(u)) ** 2 + (v - np.round(v)) ** 2)
    dark = np.clip((120 - L) / 120.0, 0, 1)
    dots = (d < dark * 0.55).astype(np.float32)
    dots = cv2.GaussianBlur(dots, (3, 3), 0)
    out *= (1 - dots[..., None] * halftone * keep[..., None])
    res = Image.fromarray(out.clip(0, 255).astype(np.uint8))
    res.putalpha(Image.fromarray(a))
    return res


def sticker(rgba, outline=7, color=(0, 0, 0), glow=None, glow_r=22):
    """누끼 외곽에 굵은 먹선(+선택적 빛 번짐)."""
    pad = outline + glow_r * 2
    big = Image.new("RGBA", (rgba.width + pad * 2, rgba.height + pad * 2), (0, 0, 0, 0))
    a = rgba.split()[3].point(lambda v: 255 if v > 100 else 0)
    canvas_a = Image.new("L", big.size, 0)
    canvas_a.paste(a, (pad, pad))
    if glow:
        ga = canvas_a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(glow_r))
        big.paste(Image.new("RGBA", big.size, glow + (255,)), (0, 0), ga.point(lambda v: min(255, v * 2)))
    ring = canvas_a.filter(ImageFilter.MaxFilter(outline * 2 + 1))
    big.paste(Image.new("RGBA", big.size, color + (255,)), (0, 0), ring)
    big.alpha_composite(rgba, (pad, pad))
    return big, pad


# ---------- 에너지·질감 ----------
def bolt(d, p0, p1, color, width, rough=0.28, depth=6, rng=random):
    pts = [p0, p1]
    disp = math.dist(p0, p1) * rough
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1
            off = rng.uniform(-disp, disp)
            new += [(mx - dy / ln * off, my + dx / ln * off), b]
        pts = new
        disp *= 0.55
    d.line(pts, fill=color, width=width, joint="curve")
    return pts


def energy_layer(size, origin, rays, seed, palette=((255, 150, 40), (255, 220, 120), (230, 40, 30))):
    """금빛·주홍 섬광 줄기 + 불꽃 입자. 가산 합성용 RGB."""
    rng = random.Random(seed)
    w, h = size
    core = Image.new("RGB", size, 0)
    d = ImageDraw.Draw(core)
    for i in range(rays):
        ang = rng.uniform(0, 2 * math.pi) if isinstance(origin, tuple) else 0
        ox, oy = origin
        ln = rng.uniform(0.35, 0.7) * max(w, h)
        p1 = (ox + math.cos(ang) * ln, oy + math.sin(ang) * ln)
        col = palette[i % len(palette)]
        pts = bolt(d, (ox, oy), p1, col, rng.choice((2, 3, 4)), rng=rng)
        for _ in range(2):  # 곁가지
            s = pts[rng.randrange(len(pts) // 3, len(pts) - 1)]
            a2 = ang + rng.uniform(-0.8, 0.8)
            bolt(d, s, (s[0] + math.cos(a2) * ln * 0.3, s[1] + math.sin(a2) * ln * 0.3), col, 2, rng=rng)
    for _ in range(260):  # 불꽃 입자
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.choice((1, 1, 2, 2, 3))
        d.ellipse([x - r, y - r, x + r, y + r], fill=rng.choice(palette))
    glow = core.filter(ImageFilter.GaussianBlur(10))
    glow2 = core.filter(ImageFilter.GaussianBlur(28))
    out = ImageChops.add(ImageChops.add(core, glow), ImageChops.add(glow, glow2))
    return out


def light_burst(size, center, color, radius, strength=1.0):
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xx - center[0], yy - center[1]) / radius
    ang = np.arctan2(yy - center[1], xx - center[0])
    rays = 0.55 + 0.45 * np.cos(ang * 18) ** 8
    v = np.exp(-r ** 2 * 1.6) * (0.6 + 0.4 * rays) * strength
    img = (np.array(color, np.float32)[None, None] * v[..., None]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(img)


def snow(img, n, seed, rmax=3):
    rng = random.Random(seed)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1, rmax)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rng.randint(120, 230)))
    lay = lay.filter(ImageFilter.GaussianBlur(0.8))
    img.alpha_composite(lay)


def grunge(img, seed, amount=1.0, corners=("tl", "tr", "bl", "br")):
    """모서리 먹물 스플래터 + 스크래치(인물 뒤 레이어에서 호출)."""
    rng = random.Random(seed)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ink = (10, 8, 8, 220)
    for c in corners:
        for _ in range(int(3 * amount)):
            cx = rng.uniform(-60, 90) if c[1] == "l" else W - rng.uniform(-60, 90)
            cy = rng.uniform(-60, 70) if c[0] == "t" else H - rng.uniform(-60, 70)
            R = rng.uniform(18, 40)
            for _ in range(10):  # 덩어리를 겹친 원으로(불규칙 윤곽)
                ox, oy, r = rng.gauss(0, R * 0.5), rng.gauss(0, R * 0.5), R * rng.uniform(0.35, 0.7)
                d.ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r], fill=ink)
            for _ in range(rng.randint(15, 30)):  # 튄 방울
                a = rng.uniform(0, 2 * math.pi)
                dist = R * rng.uniform(1.1, 4.0)
                r = max(1.0, rng.uniform(1, 5) * (1.3 - dist / (R * 4)))
                x, y = cx + math.cos(a) * dist, cy + math.sin(a) * dist
                d.ellipse([x - r, y - r, x + r, y + r], fill=ink)
    for _ in range(int(40 * amount)):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        ln, a = rng.uniform(20, 90), rng.uniform(-0.4, 0.4) + rng.choice((0, math.pi / 2))
        d.line([x, y, x + math.cos(a) * ln, y + math.sin(a) * ln], fill=(255, 240, 220, 28), width=1)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.6)))


def grade(img, warm=1.0):
    """대비↑, 그림자 청록·하이라이트 앰버, 채도 살짝↑."""
    a = np.array(img.convert("RGB")).astype(np.float32) / 255.0
    a = np.clip((a - 0.5) * 1.18 + 0.5, 0, 1)
    lum = a.mean(axis=2, keepdims=True)
    sh = (1 - lum) ** 2
    hi = lum ** 2
    a += sh * np.array([-0.03, 0.01, 0.05]) + hi * np.array([0.06, 0.02, -0.05]) * warm
    out = Image.fromarray((a.clip(0, 1) * 255).astype(np.uint8))
    return ImageEnhance.Color(out).enhance(1.12).convert("RGBA")


def vignette(img, k=0.55):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    m = np.clip(1 - (r - 0.6) * k, 0.35, 1)
    a = np.array(img).astype(np.float32)
    a[..., :3] *= m[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


# ---------- 3D 사선 글자 ----------
def gradient_fill(size, top, bottom, mid=None):
    w, h = size
    t = np.linspace(0, 1, h)[:, None]
    if mid is None:
        col = np.array(top) * (1 - t) + np.array(bottom) * t
    else:
        col = np.where(t < 0.5, np.array(top) * (1 - t * 2) + np.array(mid) * t * 2,
                       np.array(mid) * (2 - t * 2) + np.array(bottom) * (t * 2 - 1))
    arr = np.repeat(col[:, None, :], w, axis=1).astype(np.uint8)
    return Image.fromarray(arr.reshape(h, w, 3))


def title3d(text, size, fill=("gold",), depth=12, extrude=(120, 10, 16), stroke=10, shear=0.2,
            font=DELA, outer=(255, 255, 255)):
    """두꺼운 입체(압출) + 먹 테두리 + 바깥 흰 테두리 + 그라데이션 면 + 사선 기울임. RGBA 반환."""
    f = ImageFont.truetype(font, size)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    l, t, r, b = tmp.textbbox((0, 0), text, font=f, stroke_width=stroke)
    pad = stroke + depth + 30
    cw, ch = r - l + pad * 2, b - t + pad * 2
    org = (pad - l, pad - t)

    def mask(sw, off=(0, 0)):
        m = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(m).text((org[0] + off[0], org[1] + off[1]), text, font=f, fill=255,
                               stroke_width=sw, stroke_fill=255)
        return m

    img = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    # 그림자
    sh = mask(stroke + 6, (depth + 8, depth + 10)).filter(ImageFilter.GaussianBlur(8))
    img.paste(Image.new("RGBA", (cw, ch), (0, 0, 0, 200)), (0, 0), sh)
    # 바깥 흰 테두리(압출 포함)
    if outer:
        for i in range(depth, -1, -2):
            img.paste(Image.new("RGBA", (cw, ch), outer + (255,)), (0, 0), mask(stroke + 5, (i, i)))
    # 압출(어두운 색 → 아래로 갈수록 진하게)
    for i in range(depth, 0, -1):
        k = 0.55 + 0.45 * (1 - i / depth)
        c = tuple(int(v * k) for v in extrude)
        img.paste(Image.new("RGBA", (cw, ch), c + (255,)), (0, 0), mask(stroke, (i, i)))
    # 먹 테두리
    img.paste(Image.new("RGBA", (cw, ch), (10, 8, 8, 255)), (0, 0), mask(stroke))
    # 면
    face = mask(0)
    if fill[0] == "gold":
        g = gradient_fill((cw, ch), (255, 246, 190), (200, 120, 20), mid=(255, 205, 70))
    elif fill[0] == "white":
        g = gradient_fill((cw, ch), (255, 255, 255), (215, 220, 230))
    else:
        g = gradient_fill((cw, ch), fill[0], fill[1])
    img.paste(g, (0, 0), face)
    # 상단 광택(베벨 느낌)
    hl = ImageChops.subtract(face, face.transform(face.size, Image.AFFINE, (1, 0, 0, 0, 1, 4)))
    img.paste(Image.new("RGBA", (cw, ch), (255, 255, 255, 255)), (0, 0), hl.point(lambda v: int(v * 0.7)))
    # 사선 기울임
    if shear:
        nw = cw + int(ch * shear)
        img = img.transform((nw, ch), Image.AFFINE, (1, shear, -ch * shear, 0, 1, 0), Image.BICUBIC)
    return img.crop(img.getbbox())


def tag(img, xy, s, size=40, bg=RED):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(DELA, size)
    x, y = xy
    w = d.textlength(s, font=f)
    poly = [(x + 14, y), (x + w + 52, y), (x + w + 38, y + size + 24), (x, y + size + 24)]
    d.polygon([(px + 5, py + 6) for px, py in poly], fill=(0, 0, 0, 180))
    d.polygon(poly, fill=bg)
    d.text((x + 24, y + 8), s, font=f, fill=WHITE)


def bottom_band(img, s, size=36):
    d = ImageDraw.Draw(img, "RGBA")
    f = ImageFont.truetype(GOTHIC, size)
    y0 = H - size - 36
    d.polygon([(0, y0), (W, y0 - 10), (W, H), (0, H)], fill=(0, 0, 0, 215))
    d.line([(0, y0), (W, y0 - 10)], fill=GOLD, width=4)
    d.text((40, y0 + 12), s, font=f, fill=WHITE, stroke_width=3, stroke_fill=(0, 0, 0))


def place(base, rgba, center=None, topleft=None):
    x, y = topleft if topleft else (int(center[0] - rgba.width / 2), int(center[1] - rgba.height / 2))
    base.alpha_composite(rgba, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))


def fit(rgba, height):
    rgba = rgba.crop(rgba.getbbox())
    return rgba.resize((int(rgba.width * height / rgba.height), height), Image.LANCZOS)


def add_rgb(base, rgb, k=1.0):
    a = np.array(base).astype(np.float32)
    a[..., :3] += np.array(rgb).astype(np.float32) * k
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


# ---------- 썸네일 ----------
def thumb_a(cache):
    """A 「言わないでください」: 눈 내리는 단지 야경 → 금빛 섬광 → 올려다보는 아이 → 거대 김씨 CU."""
    bg = keyframe("S04").resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3))
    bg = ImageEnhance.Brightness(bg).enhance(0.55).convert("RGBA")
    bg = add_rgb(bg, light_burst((W, H), (930, 300), (255, 150, 50), 520, 0.85))
    bg = add_rgb(bg, energy_layer((W, H), (930, 300), 16, seed=4), 0.9)
    grunge(bg, seed=7, corners=("tl", "bl", "br"))

    # 중간 레이어: 김씨를 올려다보는 1801호 아이(편지의 주인)
    boy = fit(cutout("S09", cache), 215)
    boy = toon(boy, levels=7, line=0.35, halftone=0.25, dot=5)
    boy, pb = sticker(boy, outline=6, glow=(255, 150, 50), glow_r=18)
    place(bg, boy, topleft=(400 - boy.width // 2, 648 - boy.height + pb))

    # 거대 클로즈업: 김씨(대사 기준 얼굴 S23)
    kim = cutout("S23", cache).crop((250, 0, 1100, 768))
    kim = toon(fit(kim, 790), levels=8, line=0.4, halftone=0.3, dot=6)
    kim, pad = sticker(kim, outline=8, glow=(255, 170, 60), glow_r=26)
    place(bg, kim, topleft=(1300 - kim.width + pad, 2 - pad))

    snow(bg, 110, seed=41, rmax=2.5)
    img = vignette(grade(bg))

    t1 = title3d("言わないで", 112, fill=("white",), depth=12, extrude=(60, 60, 80), stroke=9)
    t2 = title3d("ください", 150, fill=("gold",), depth=16, extrude=(150, 18, 22), stroke=11)
    place(img, t1, topleft=(28, 118))
    place(img, t2, topleft=(20, 262))
    tag(img, (34, 34), "12月24日")
    bottom_band(img, "警備員が払った「三か月分の管理費」…")
    return img.convert("RGB")


def thumb_b(cache):
    """B 「誰が払ったの？」: 대결 구도 분할(엄마 눈물 vs 김씨 미소) + 두 사람 사이 금빛 번개 경계(인물 뒤)."""
    bg = keyframe("S04").resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(4))
    bg = ImageEnhance.Brightness(bg).enhance(0.5).convert("RGBA")
    cold = Image.new("RGBA", (W, H), (40, 90, 170, 0))   # 좌 푸른빛 / 우 금빛
    cold.putalpha(Image.linear_gradient("L").rotate(90).resize((W, H)).point(lambda v: int(v * 0.45)))
    bg.alpha_composite(cold)
    bg = add_rgb(bg, light_burst((W, H), (1000, 280), (255, 150, 50), 560, 0.9))
    bg = add_rgb(bg, energy_layer((W, H), (640, 300), 12, seed=12), 0.55)
    lay = Image.new("RGB", (W, H), 0)
    d = ImageDraw.Draw(lay)
    rng = random.Random(11)
    for i, col in enumerate(((255, 230, 140), (255, 150, 40), (230, 40, 30), (255, 255, 255))):
        bolt(d, (690 + rng.uniform(-25, 25), -20), (600 + rng.uniform(-25, 25), H + 20), col,
             7 if i == 3 else 5, rough=0.14, rng=rng)
    glow = ImageChops.add(lay.filter(ImageFilter.GaussianBlur(8)), lay.filter(ImageFilter.GaussianBlur(30)))
    bg = add_rgb(bg, ImageChops.add(lay, glow), 1.0)
    grunge(bg, seed=9, amount=0.8, corners=("bl", "br", "tr"))

    mom = cutout("S45", cache).crop((330, 0, 1020, 768))
    mom = toon(fit(mom, 680), levels=8, line=0.4, halftone=0.28, dot=6)
    mom, pm = sticker(mom, outline=8, glow=(120, 180, 255), glow_r=24)
    place(bg, mom, topleft=(-60 - pm, 40 - pm))

    kim = cutout("S50", cache).crop((300, 0, 1080, 768))
    kim = toon(fit(kim, 700), levels=8, line=0.4, halftone=0.28, dot=6)
    kim, pk = sticker(kim, outline=8, glow=(255, 170, 60), glow_r=24)
    place(bg, kim, topleft=(W - kim.width + pk + 50, 30 - pk))

    snow(bg, 100, seed=52, rmax=2.5)
    img = vignette(grade(bg))

    t = title3d("誰が払ったの？", 132, fill=("gold",), depth=16, extrude=(150, 18, 22), stroke=11, shear=0.18)
    place(img, t, center=(W // 2, 560))
    tag(img, (34, 34), "クリスマスの朝")
    bottom_band(img, "防犯カメラに映っていたのは…")
    return img.convert("RGB")


def main():
    out = sys.argv[1]
    cache = sys.argv[2] if len(sys.argv) > 2 else os.path.join(out, ".cutcache")
    os.makedirs(out, exist_ok=True)
    os.makedirs(cache, exist_ok=True)
    for name, fn in (("A-ienaide-poster", thumb_a), ("B-darega-poster", thumb_b)):
        p = os.path.join(out, f"EP4-thumb-{name}-JP.jpg")
        fn(cache).save(p, quality=92)
        print("저장:", p)


if __name__ == "__main__":
    main()
