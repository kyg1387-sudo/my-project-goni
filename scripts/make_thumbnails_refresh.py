#!/usr/bin/env python3
"""옛 본편 썸네일 리프레시 — 실사 표준(제0장 8 개정·제22장 13·14, 2026-11-07).

승자 양식(財閥会長 A/B 45.4%): 본편 실사 프레임 · 권력 역전 투샷(좌우 대각 분할) · 반전 결과어 초대형 ·
밝기 115 이상 · 오른쪽 아래(재생 시간) 비움. 프레임은 본편 완성 영상·키프레임에서 뽑는다(무료).

사용법: python3 scripts/make_thumbnails_refresh.py <작품키> [--src <프레임 폴더>] [--out assets/thumbs/refresh]
       결과: <out>/<작품키>-A.jpg·-B.jpg(1280x720, 2MB 이하) + -A_360.jpg 확인본 → thumb_check.py 로 검사
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GOTH = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")
W, H = 1920, 1080
GOLD = ((255, 248, 150), (255, 214, 40), (235, 150, 10))      # 노랑 → 금 (결과어)
FIRE = ((255, 236, 60), (255, 150, 20), (225, 30, 20))         # 노랑 → 주황 → 빨강


def text_layer(s, size, fill=None, gradient=None, stroke=(0, 0, 0), stroke_w=12, outer=None, outer_w=0):
    f = ImageFont.truetype(GOTH, size)
    pad = stroke_w + outer_w + 24
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), s, font=f)
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    o = (pad - bb[0], pad - bb[1])
    if outer:
        d.text(o, s, font=f, fill=outer, stroke_width=stroke_w + outer_w, stroke_fill=outer)
    d.text(o, s, font=f, fill=fill or (255, 255, 255), stroke_width=stroke_w, stroke_fill=stroke)
    if gradient:
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).text(o, s, font=f, fill=255)
        g = Image.new("RGB", (w, h))
        gd = ImageDraw.Draw(g)
        top, mid, bot = gradient
        for y in range(h):
            t = (y - pad) / max(1, h - 2 * pad)
            c = [top[i] + (mid[i] - top[i]) * min(1, t * 2) if t < 0.5 else mid[i] + (bot[i] - mid[i]) * (t - 0.5) * 2 for i in range(3)]
            gd.line([(0, y), (w, y)], fill=tuple(int(max(0, min(255, v))) for v in c))
        lay.paste(g, (0, 0), m)
    return lay


def glow(lay, color=(0, 0, 0), r=18, strength=1.8):
    pad = Image.new("RGBA", (lay.width + 4 * r, lay.height + 4 * r), (0, 0, 0, 0))
    pad.alpha_composite(lay, (2 * r, 2 * r))
    a = pad.split()[3].filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * strength)))
    g = Image.new("RGBA", pad.size, color + (0,))
    g.putalpha(a)
    return Image.alpha_composite(g, pad)


def band(s, size, fg=(255, 226, 40), bg=(0, 0, 0, 205), pad=(34, 18)):
    f = ImageFont.truetype(GOTH, size)
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), s, font=f)
    lay = Image.new("RGBA", (bb[2] - bb[0] + pad[0] * 2, bb[3] - bb[1] + pad[1] * 2), bg)
    ImageDraw.Draw(lay).text((pad[0] - bb[0], pad[1] - bb[1]), s, font=f, fill=fg, stroke_width=3, stroke_fill=(0, 0, 0))
    return lay


def put(img, lay, x, y):
    tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    tmp.paste(lay, (int(x), int(y)), lay)
    img.alpha_composite(tmp)


def grade(im, bright=1.0, contrast=1.0, sat=1.0, warm=0, lift=0):
    """밝기·대비·채도·색온도. lift 는 어두운 톤만 들어 올림(검정은 유지, 제11장 11 방식)."""
    im = im.convert("RGB")
    if lift:
        lut = [min(255, int(v + lift * (1 - v / 255) ** 1.5)) for v in range(256)]
        im = im.point(lut * 3)
    im = ImageEnhance.Brightness(im).enhance(bright)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(sat)
    if warm:
        r, g, b = im.split()
        r = r.point(lambda v: min(255, v + warm)); b = b.point(lambda v: max(0, v - warm))
        im = Image.merge("RGB", (r, g, b))
    return im


def kill_subs(im, y0=720, feather=90):
    """본편 완성 영상 프레임의 구운 자막(화면 아래)을 지운다: y0 아래를 강하게 흐리고 어둡게, 경계는 부드럽게."""
    blur = ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(40))).enhance(0.6)
    m = Image.new("L", (1, H), 0)
    for y in range(H):
        m.putpixel((0, y), 0 if y < y0 else int(255 * min(1, (y - y0) / feather)))
    return Image.composite(blur, im, m.resize(im.size))


def panel(path, cx, cy, zoom, w, h, subs=False, **g):
    """프레임에서 (cx,cy)를 중심으로 zoom 배 확대해 w×h 패널로 자른다. subs=True 는 구운 자막을 지운다."""
    im = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
    if subs:
        im = kill_subs(im)
    im = grade(im, **g)
    sw, sh = w / zoom, h / zoom
    box = (cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2)
    return im.crop(tuple(int(v) for v in box)).resize((w, h), Image.LANCZOS)


def split2(left, right, slant=140, line=(255, 255, 255), lw=10):
    """좌우 대각 분할(가운데 기울어진 흰 선) — 역전 투샷."""
    base = Image.new("RGB", (W, H))
    base.paste(left, (0, 0))
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    mid = W // 2
    d.polygon([(mid + slant, 0), (W, 0), (W, H), (mid - slant, H)], fill=255)
    base.paste(right, (0, 0), m)
    d2 = ImageDraw.Draw(base)
    d2.line([(mid + slant, 0), (mid - slant, H)], fill=line, width=lw)
    return base.convert("RGBA")


# ---------------------------------------------------------------- 작품별 설정
def halves(L, R, lx, rx):
    """L 은 얼굴 x=lx 가 왼쪽 반 가운데(480)에, R 은 얼굴 x=rx 가 오른쪽 반 가운데(1440)에 오도록 옮긴다."""
    def shift(im, fx, tx):
        out = Image.new("RGB", (W, H))
        dx = int(tx - fx)
        out.paste(im, (dx, 0))
        if dx > 0:
            out.paste(im.crop((0, 0, dx, H)).transpose(Image.FLIP_LEFT_RIGHT), (0, 0))
        elif dx < 0:
            out.paste(im.crop((W + dx, 0, W, H)).transpose(Image.FLIP_LEFT_RIGHT), (W + dx, 0))
        return out
    return split2(shift(L, lx, 480), shift(R, rx, 1440))


def shade_bottom(img, y0=600, alpha=190):
    """아래쪽 글자 받침: 위로 갈수록 투명해지는 검은 그라데이션(구운 자막도 가린다)."""
    g = Image.new("L", (1, H), 0)
    for y in range(H):
        g.putpixel((0, y), 0 if y < y0 else int(alpha * min(1, (y - y0) / 160)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay.putalpha(g.resize((W, H)))
    img.alpha_composite(lay)


def face_x(fx, cx, zoom):
    return (fx - cx) * zoom + W / 2


def ryokan(src):
    f = lambda n: os.path.join(src, n)
    out = {}
    # A: 결과형 — 왼쪽 「戻ってきて」라고 비는 姑(밤 사무실) ↔ 오른쪽 온화한 若菜(따뜻한 빛). 결과어 초대형은 얼굴 아래 받침 위.
    L = panel(f("hq_524.0.png"), 960, 600, 1.05, W, H, subs=True, bright=1.42, contrast=1.02, lift=55)
    R = panel(f("S18f.png"), 980, 560, 1.05, W, H, bright=1.28, contrast=1.02, sat=1.12, warm=6, lift=36)
    img = halves(L, R, 960, 980)
    shade_bottom(img, 600, 150)
    put(img, band("老舗旅館の3か月後", 78, fg=(255, 236, 60), bg=(0, 0, 0, 215)), 0, 0)
    put(img, glow(text_layer("追い出した嫁に", 132, stroke_w=12)), 40, 630)
    put(img, glow(text_layer("戻ってきて", 268, gradient=GOLD, stroke=(255, 255, 255), stroke_w=15, outer=(0, 0, 0), outer_w=12), r=24), 10, 735)
    out["A"] = img
    # B: 대사→역전 — 왼쪽 「代わりはいくらでもいる」 小姑 ↔ 오른쪽 웃는 若菜. 결과어 「立場逆転」.
    L = panel(f("hq_575.png"), 1020, 620, 1.05, W, H, subs=True, bright=1.36, contrast=1.02, sat=1.05, lift=48)
    R = panel(f("S18g.png"), 980, 560, 1.05, W, H, bright=1.28, contrast=1.02, sat=1.12, warm=6, lift=36)
    img = halves(L, R, 1020, 980)
    shade_bottom(img, 600, 150)
    put(img, glow(text_layer("「代わりはいくらでもいる」", 104, stroke_w=11)), 20, 20)
    put(img, glow(text_layer("3か月後", 150, stroke_w=12)), 50, 620)
    put(img, glow(text_layer("立場逆転", 244, gradient=GOLD, stroke=(255, 255, 255), stroke_w=15, outer=(0, 0, 0), outer_w=12), r=24), 340, 730)
    out["B"] = img
    return out


def full(path, **g):
    """외부 생성 그림 1장(16:9 근처)을 1920x1080으로 맞춘다(가운데 크롭)."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    tw = min(w, int(h * 16 / 9)); th = int(tw * 9 / 16)
    im = im.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th)).resize((W, H), Image.LANCZOS)
    return grade(im, **g)


def erase_mark(im, box=(1780, 960, 1920, 1080)):
    """생성기 워터마크(오른쪽 아래 ✦)를 바로 위 영역을 흐려 덮어 지운다(재생 시간 자리라 글자는 두지 않는다)."""
    x0, y0, x1, y1 = box
    patch = im.crop((x0, y0 - (y1 - y0), x1, y0)).filter(ImageFilter.GaussianBlur(6))
    im.paste(patch, (x0, y0))
    return im


def ryokan_text_A(img):
    shade_bottom(img, 600, 160)
    put(img, band("老舗旅館の3か月後", 78, fg=(255, 236, 60), bg=(0, 0, 0, 215)), 0, 0)
    put(img, glow(text_layer("追い出した嫁に", 126, stroke_w=12)), 50, 612)
    put(img, glow(text_layer("戻ってきて", 256, gradient=GOLD, stroke=(255, 255, 255), stroke_w=15, outer=(0, 0, 0), outer_w=12), r=24), 10, 712)
    return img


def ryokan_gen(src):
    f = lambda n: os.path.join(src, n)
    out = {}
    # A2: 고니감독님 생성 그림(우는 姑 + 미소 若菜) + A 글자 그대로
    img = erase_mark(full(f("gen_A.jpg"), bright=1.46, contrast=1.04, sat=1.06, lift=54)).convert("RGBA")
    out["A2"] = ryokan_text_A(img)
    # A3: 혼합 — 왼쪽 생성 姑(감정) + 오른쪽 본편 키프레임 若菜(본편과 같은 얼굴, 제13장 5 R60)
    gen = erase_mark(full(f("gen_A.jpg"), bright=1.46, contrast=1.04, sat=1.06, lift=54))
    R = panel(f("S18f.png"), 980, 560, 1.05, W, H, bright=1.28, contrast=1.02, sat=1.12, warm=6, lift=36)
    gen_l = Image.new("RGB", (W, H)); gen_l.paste(gen, (0, 0))
    out["A3"] = ryokan_text_A(halves(gen_l, R, 480, 980) if False else split2(gen_l, shift_to(R, 980, 1440)))
    return out


def shift_to(im, fx, tx):
    out = Image.new("RGB", (W, H))
    dx = int(tx - fx)
    out.paste(im, (dx, 0))
    if dx > 0:
        out.paste(im.crop((0, 0, dx, H)).transpose(Image.FLIP_LEFT_RIGHT), (0, 0))
    return out


WORKS = {"ryokan": ryokan, "ryokan_gen": ryokan_gen}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "thumbs", "refresh"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for k, img in WORKS[a.work](a.src).items():
        im = img.convert("RGB").resize((1280, 720), Image.LANCZOS)
        p = os.path.join(a.out, f"{a.work}-{k}.jpg")
        im.save(p, quality=90)
        im.resize((360, 203), Image.LANCZOS).save(p.replace(".jpg", "_360.jpg"), quality=90)
        print(p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main()
