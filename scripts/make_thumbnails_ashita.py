#!/usr/bin/env python3
"""『明日から来なくていい』 썸네일 2종(1280x720, 무과금·로컬, 승인 키프레임만 사용) — make_thumbnails_yanagi_v2.py 방식 간소판.
  A 결말 반전형 — 왼쪽 애원하는 田中(붉은 조명) / 오른쪽 내려다보는 佐藤, 「クビにした男が / 百億円の鍵だった」
  B 갑질 충격형 — 비웃으며 해고하는 田中 + 「明日から来るな！」 + 「七日後、土下座したのは…」
오른쪽 아래(재생 시간 표시)는 비운다. 피·폭력 없음. 실존 기업명 없음(가상 회사).
사용법: make_thumbnails_ashita.py [out_dir]  (기본 assets/thumbnails/ashita)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "assets", "portraits", "ashita-kara-keyframes")
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


def outlined(d, xy, text, font, fill, stroke, sw, anchor="la"):
    d.text(xy, text, font=font, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


def shade(im, top=0.0, bottom=0.75):
    """아래쪽을 어둡게(글자 가독성)."""
    g = Image.linear_gradient("L").resize((W, H))
    g = g.point(lambda v: int(255 * (top + (bottom - top) * v / 255)))
    return Image.composite(Image.new("RGB", (W, H)), im, g)


def thumb_a():
    left = cover(kf("S25a"), 700, H, cx=0.33, cy=0.42, zoom=1.35)
    left = ImageEnhance.Color(left).enhance(1.15)
    right = cover(kf("S26a"), 700, H, cx=0.55, cy=0.40, zoom=1.30)
    base = Image.new("RGB", (W, H))
    base.paste(left, (0, 0))
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).polygon([(700, 0), (W, 0), (W, H), (580, H)], fill=255)
    canvas = Image.new("RGB", (W, H)); canvas.paste(right, (W - 700, 0))
    base = Image.composite(canvas, base, mask)
    d = ImageDraw.Draw(base)
    d.line([(700, 0), (580, H)], fill=(255, 215, 0), width=10)
    base = shade(base, 0.0, 0.70)
    d = ImageDraw.Draw(base)
    outlined(d, (40, 470), "クビにした男が", ImageFont.truetype(GOTH, 92), (255, 255, 255), (0, 0, 0), 8)
    outlined(d, (40, 580), "百億円の鍵だった", ImageFont.truetype(GOTH, 104), (255, 214, 0), (120, 0, 0), 9)
    outlined(d, (40, 36), "「助けてくれ…」", ImageFont.truetype(MIN, 64), (255, 255, 255), (90, 0, 0), 6)
    return base


def thumb_b():
    bg = cover(kf("S12c"), W, H, cx=0.30, cy=0.40, zoom=1.25)
    bg = ImageEnhance.Contrast(bg).enhance(1.1)
    inset = cover(kf("S25b"), 380, 300, cx=0.5, cy=0.55, zoom=1.6)
    bg = shade(bg, 0.0, 0.65)
    d = ImageDraw.Draw(bg)
    outlined(d, (W - 40, 40), "明日から", ImageFont.truetype(GOTH, 110), (255, 255, 255), (0, 0, 0), 9, "ra")
    outlined(d, (W - 40, 165), "来るな！", ImageFont.truetype(GOTH, 150), (235, 30, 30), (255, 255, 255), 8, "ra")
    bg.paste(inset, (40, 380))
    d.rectangle((40, 380, 420, 680), outline=(255, 214, 0), width=6)
    outlined(d, (460, 500), "七日後、", ImageFont.truetype(MIN, 70), (255, 255, 255), (0, 0, 0), 6)
    outlined(d, (460, 590), "土下座したのは…", ImageFont.truetype(MIN, 76), (255, 214, 0), (0, 0, 0), 7)
    return bg


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "thumbnails", "ashita")
    os.makedirs(out, exist_ok=True)
    for name, fn in (("A-kagi", thumb_a), ("B-kuruna", thumb_b)):
        p = os.path.join(out, f"ashita-thumb-{name}-JP.jpg")
        fn().save(p, quality=92); print("저장:", p)


if __name__ == "__main__":
    main()
