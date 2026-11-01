#!/usr/bin/env python3
"""EP4 일본어 썸네일 3종(1280x720, EP3 형식: 큰 일본어 문구·굵은 테두리·빨간 태그·하단 한 줄). 무과금, 로컬.
실화 주장 없음(「実話」 금지). 사용법: make_thumbnails_ep4.py <out_dir>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "assets", "portraits", "ep4-keyframes")
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
MINCHO = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")
W, H = 1280, 720
YELLOW, WHITE, RED = (255, 214, 40), (255, 255, 255), (214, 32, 38)


def load(name, box=None, size=(W, H), dark=0.85):
    im = Image.open(os.path.join(K, f"{name}-1.png")).convert("RGB")
    if box:
        im = im.crop(box)
    im = im.resize(size, Image.LANCZOS)
    return ImageEnhance.Brightness(im).enhance(dark)


def text(d, xy, s, size, fill, stroke=10, font=GOTHIC):
    f = ImageFont.truetype(font, size)
    d.text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    return d.textbbox(xy, s, font=f, stroke_width=stroke)


def tag(d, xy, s, size=44):
    f = ImageFont.truetype(GOTHIC, size)
    x, y = xy
    w = d.textlength(s, font=f)
    d.rounded_rectangle([x, y, x + w + 40, y + size + 26], radius=10, fill=RED)
    d.text((x + 20, y + 10), s, font=f, fill=WHITE)


def shade_left(im, frac=0.62):
    """왼쪽 글자 자리를 어둡게(가독성)."""
    g = Image.new("L", (W, H))
    gd = ImageDraw.Draw(g)
    for x in range(W):
        a = int(max(0, 1 - x / (W * frac)) * 170)
        gd.line([(x, 0), (x, H)], fill=a)
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, g)


def bottom_line(d, s, size=40):
    f = ImageFont.truetype(GOTHIC, size)
    d.rectangle([0, H - size - 40, W, H], fill=(0, 0, 0, 200))
    d.text((40, H - size - 22), s, font=f, fill=WHITE, stroke_width=3, stroke_fill=(0, 0, 0))


def thumb_a():
    """김씨 창구 CU + 「言わないで ください」."""
    im = load("S28", box=(0, 40, 1050, 631))  # 김씨를 오른쪽으로
    im = shade_left(im, 0.55)
    d = ImageDraw.Draw(im, "RGBA")
    tag(d, (40, 36), "12月24日")
    text(d, (30, 160), "言わないで", 112, WHITE, 11)
    text(d, (30, 300), "ください", 140, YELLOW, 12)
    bottom_line(d, "警備員が払った「三か月分の管理費」…")
    return im


def thumb_b():
    """좌 엄마 눈물 / 우 김씨 미소 분할 + 「誰が払ったの？」."""
    im = Image.new("RGB", (W, H))
    left = load("S45", box=(250, 0, 950, 700), size=(640, H), dark=0.9)
    right = load("S50", box=(200, 0, 900, 700), size=(640, H), dark=0.95)
    im.paste(left, (0, 0)); im.paste(right, (640, 0))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([636, 0, 644, H], fill=YELLOW)
    tag(d, (40, 36), "クリスマスの朝")
    d.rectangle([0, 505, W, 640], fill=(0, 0, 0, 140))
    text(d, (90, 508), "誰が払ったの？", 118, YELLOW, 11)
    bottom_line(d, "防犯カメラに映っていたのは…")
    return im


def thumb_c():
    """새벽 문 앞 트리 + 「午前4時 ドアの前に」."""
    im = load("S38", dark=1.25)
    im = shade_left(im, 0.6)
    d = ImageDraw.Draw(im, "RGBA")
    tag(d, (40, 36), "18階・午前4時")
    text(d, (36, 160), "チャイムは", 120, WHITE, 11)
    text(d, (36, 300), "鳴らさな", 140, YELLOW, 12)
    text(d, (36, 450), "かった", 140, YELLOW, 12)
    bottom_line(d, "無口な警備員が置いていった、小さなツリー")
    return im


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, fn in (("A-ienaide", thumb_a), ("B-darega", thumb_b), ("C-chaimu", thumb_c)):
        p = os.path.join(out, f"EP4-thumb-{name}-JP.jpg")
        fn().save(p, quality=92)
        print("저장:", p)


if __name__ == "__main__":
    main()
