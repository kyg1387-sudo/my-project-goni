#!/usr/bin/env python3
"""『柳の葉と一杯の水』 썸네일 시안 2종(1280x720). 무과금, 로컬 — 승인된 키프레임만 쓴다(인물 일관성).
A: 감독님 기획안(점장 vs 회장 대비 + 유나 손) 적용판 — 문구는 대본 표현으로 교체.
B: 반전형(추방된 노인 → 정장 회장).
글자: 본체 → 1차 테두리 → 2차 테두리(바깥) + 번짐 없는 그림자. 오른쪽 아래(재생 시간 표시 자리)는 비운다.
사용법: make_thumbnails_yanagi.py <out_dir>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "assets", "portraits", "yanagi-keyframes")
FONT = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")  # 두꺼운 라운드 고딕(OFL, 상업 사용 가능)
W, H = 1280, 720
YELLOW, WHITE, BLACK = (255, 230, 0), (255, 255, 255), (0, 0, 0)
BLOOD, SCARLET, RED = (200, 0, 0), (255, 42, 0), (230, 0, 0)


def kf(name, box):
    return Image.open(os.path.join(K, f"{name}-1.png")).convert("RGB").crop(box)


def tint(im, rgb, amount):
    return Image.blend(im, Image.new("RGB", im.size, rgb), amount)


def fade_mask(size, left=0, right=0, vert=0):
    """좌우(필요하면 위아래) 가장자리를 부드럽게 녹이는 마스크."""
    w, h = size
    m = Image.new("L", size, 255)
    d = ImageDraw.Draw(m)
    for x in range(w):
        a = 255
        if left and x < left:
            a = int(255 * x / left)
        if right and x > w - right:
            a = min(a, int(255 * (w - x) / right))
        d.line([(x, 0), (x, h)], fill=a)
    if vert:
        v = Image.new("L", size, 255)
        dv = ImageDraw.Draw(v)
        for y in range(h):
            dv.line([(0, y), (w, y)], fill=int(255 * min(1, y / vert, (h - y) / vert)))
        m = Image.fromarray(__import__("numpy").minimum(__import__("numpy").asarray(m), __import__("numpy").asarray(v)))
    return m


def rim(im, rgb, side, width=90, strength=0.55):
    """한쪽 가장자리에 색 역광(림 라이트) 느낌."""
    w, h = im.size
    g = Image.new("L", (w, h))
    d = ImageDraw.Draw(g)
    for i in range(width):
        x = i if side == "left" else w - 1 - i
        d.line([(x, 0), (x, h)], fill=int(255 * strength * (1 - i / width)))
    return Image.composite(Image.new("RGB", (w, h), rgb), im, g)


def tri_text(base, xy, s, size, fill, inner, inner_w, outer, outer_w, colors=None):
    """본체 fill + 1차 테두리 inner(inner_w) + 2차 테두리 outer(바깥, outer_w) + 검정 그림자(번짐 없음).
    colors: {글자 인덱스: 색} — 일부 글자만 색 반전."""
    f = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(base)
    x, y = xy
    total = inner_w + outer_w
    d.text((x + 8, y + 8), s, font=f, fill=BLACK, stroke_width=total, stroke_fill=BLACK)
    d.text((x, y), s, font=f, fill=outer, stroke_width=total, stroke_fill=outer)
    d.text((x, y), s, font=f, fill=inner, stroke_width=inner_w, stroke_fill=inner)
    cx = x
    for i, ch in enumerate(s):
        d.text((cx, y), ch, font=f, fill=(colors or {}).get(i, fill))
        cx += d.textlength(ch, font=f)
    return d.textbbox((x, y), s, font=f, stroke_width=total)


def tag(base, xy, s, size=46):
    f = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(base)
    x, y = xy
    w = d.textlength(s, font=f)
    d.rounded_rectangle([x, y, x + w + 40, y + size + 28], radius=10, fill=RED, outline=WHITE, width=4)
    d.text((x + 20, y + 8), s, font=f, fill=WHITE)


def thumb_a():
    """기획안 적용판: 왼쪽 40% 점장(차가운 푸른 톤 + 붉은 역광), 오른쪽 40% 회장(금빛·무거운 그늘), 가운데 유나의 떨리는 손."""
    bg = Image.new("RGB", (W, H), (8, 12, 22))
    # 점장 S14g (얼굴 중심 약 x660,y320) — 왼쪽 40%
    man = kf("S14g", (330, 60, 990, 768)).resize((560, 600), Image.LANCZOS)
    man = tint(ImageEnhance.Contrast(man).enhance(1.15), (20, 60, 140), 0.28)
    man = rim(man, (255, 20, 20), "left", 110, 0.6)
    bg.paste(man, (0, 120), fade_mask(man.size, right=120))
    # 회장 S27g (얼굴 중심 약 x660,y190) — 오른쪽 40%
    og = kf("S27g", (360, 0, 960, 640)).resize((560, 600), Image.LANCZOS)
    og = ImageEnhance.Brightness(tint(ImageEnhance.Contrast(og).enhance(1.1), (150, 110, 30), 0.22)).enhance(0.85)
    og = rim(og, (255, 200, 80), "right", 120, 0.45)
    bg.paste(og, (W - 560, 120), fade_mask(og.size, left=120))
    # 가운데: 유나의 떨리는 손(S14d2) 작은 인서트
    hands = kf("S14d2", (80, 260, 760, 768)).resize((300, 224), Image.LANCZOS)
    hands = ImageEnhance.Brightness(hands).enhance(0.9)
    bg.paste(hands, ((W - 300) // 2, 300), fade_mask(hands.size, left=70, right=70, vert=50))
    # 1열(위): 대본 대사 그대로 — 노랑 + 피색 빨강 12 + 흰색 6
    tri_text(bg, (40, 18), "「黙ってハンコ、押しなよ」", 84, YELLOW, BLOOD, 12, WHITE, 6)
    # 2열(아래 왼쪽, 오른쪽 아래 재생 시간 자리 비움): 흰 + 검정 14 + 다홍 6, 「末路」만 빨강
    s = "店長代理の末路"
    tri_text(bg, (40, 560), s, 110, WHITE, BLACK, 14, SCARLET, 6, {5: RED, 6: RED})
    return bg


def thumb_b():
    """반전형: 왼쪽 쫓겨난 노인(S02b) → 오른쪽 정장 회장(S27g)."""
    bg = Image.new("RGB", (W, H), (10, 10, 14))
    old = kf("S02b", (420, 40, 1140, 768)).resize((600, 607), Image.LANCZOS)
    old = tint(old, (230, 140, 60), 0.12)
    bg.paste(old, (0, 113), fade_mask(old.size, right=140))
    og = kf("S27g", (360, 0, 960, 640)).resize((560, 600), Image.LANCZOS)
    og = rim(tint(ImageEnhance.Contrast(og).enhance(1.12), (150, 110, 30), 0.18), (255, 200, 80), "right", 120, 0.4)
    bg.paste(og, (W - 560, 120), fade_mask(og.size, left=140))
    tri_text(bg, (40, 18), "追い出した老人は…", 96, YELLOW, BLOOD, 12, WHITE, 6)
    tag(bg, (40, 470), "三日後")
    tri_text(bg, (40, 560), "会長だった", 120, WHITE, BLACK, 14, SCARLET, 6, {0: RED, 1: RED})
    return bg


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "productions", "willow-leaf-ja", "thumbnails")
    os.makedirs(out, exist_ok=True)
    for name, fn in (("A-기획안적용", thumb_a), ("B-반전형", thumb_b)):
        p = os.path.join(out, f"yanagi-thumb-{name}.jpg")
        fn().save(p, quality=92)
        print(p)
