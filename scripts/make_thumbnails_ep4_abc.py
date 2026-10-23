#!/usr/bin/env python3
"""EP4 「キムさんのクリスマス」 썸네일 A/B/C 테스트 세트(1280x720, 무과금·로컬).

채널 썸네일 지침(弁当屋 제19장 16 · 老舗旅館 썸네일 템플릿 A/B/C · 제18장 12)을 따른다:
  - 인물 = 본편 키프레임 인물 그대로(제13장 5), 문구 = 본편 대사·내레이션에 있는 말만, 「実話」 금지.
  - 초대형 굵은 글자 덩어리 2~3개, 3~5자 단위로 노랑/빨강/흰 그라데이션 + 검은 테, 줄당 8자 이내.
  - 글자는 얼굴을 덮지 않는다. 오른쪽 아래(재생 시간 표시)는 비운다. 168px·360px 휴대폰 확인본을 같이 만든다.
  A 泣ける(가장 자극적): 엄마 눈물 CU + 「構わないで」と突き放した母が… + 초대형 「ごめんなさい」
  B 어두운 실사 CU(템플릿 A형): 김씨 정면 응시 + 어두운 창 쪽 글자 3줄 + 초대형 인용구 「決して、言わないで」
  C 따뜻한 실사(템플릿 C형): 김씨 미소 + 털실 별(소품) + 「亡き妻の最後の願い」 + 반투명 띠
사용법: make_thumbnails_ep4_abc.py [out_dir]
"""
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "assets", "portraits", "ep4-keyframes")
GOTH = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")
W, H = 1280, 720
YEL = ((255, 252, 170), (255, 222, 30), (255, 150, 0))
RED = ((255, 90, 70), (225, 10, 10), (140, 0, 0))
FIRE = ((255, 250, 190), (255, 170, 20), (220, 20, 10))


def keyframe(name, scale_h=None):
    im = Image.open(os.path.join(K, f"{name}-1.png")).convert("RGB")
    h = scale_h or H
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def lift(im, g=1.15):
    """어두운 중간 톤만 올림(휴대폰 목록에서 얼굴이 어둡게 묻히지 않게)."""
    return im.point(lambda c: int(255 * (c / 255) ** (1 / g)))


def shifted(name, dx, g=1.12):
    """키프레임을 dx만큼 옮겨 얼굴을 원하는 3분할 위치에 둔다. 빈 쪽은 가장자리를 늘려 흐리게 채움(글자 자리라 어둡게 덮인다)."""
    src = lift(keyframe(name), g)
    canvas = Image.new("RGB", (W, H))
    if dx > 0:
        strip = src.crop((0, 0, 24, H)).resize((dx + 40, H)).filter(ImageFilter.GaussianBlur(30))
        canvas.paste(strip, (0, 0))
    else:
        strip = src.crop((src.width - 24, 0, src.width, H)).resize((-dx + 40 + src.width - W, H)).filter(ImageFilter.GaussianBlur(30))
        canvas.paste(strip, (W - strip.width, 0))
    canvas.paste(src, (dx, 0))
    return canvas.convert("RGBA")


def shade(img, box, alpha=170, blur=110, side=None):
    """글자 자리만 어둡게(대비). side='left'/'right'면 그쪽 절반을 그라데이션으로."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    if side:
        for x in range(W):
            t = (1 - x / (W * 0.62)) if side == "left" else (x - W * 0.38) / (W * 0.62)
            d.line([(x, 0), (x, H)], fill=int(max(0.0, min(1.0, t)) * alpha))
    else:
        d.rectangle(box, fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(blur if not side else 20))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    dark.putalpha(m)
    img.alpha_composite(dark)


def gradient(size, stops):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        a, b, u = (stops[0], stops[1], t * 2) if t < 0.5 else (stops[1], stops[2], t * 2 - 1)
        g.putpixel((0, y), tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3)))
    return g.resize((w, h))


def text_layer(s, size, kind="white", glow=None):
    """kind: white(흰+검은 테) / yel(노랑 그라데이션+검은 테) / red(빨강 그라데이션+흰 테+검은 바깥 테) / fire(불꽃 그라데이션+검은 테)."""
    f = ImageFont.truetype(GOTH, size)
    stroke = max(6, size // 9)
    outer = stroke + max(4, size // 22) if kind == "red" else 0
    pad = stroke + outer + 40
    l, t, r, b = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), s, font=f)
    cw, ch = r - l + pad * 2, b - t + pad * 2
    org = (pad - l, pad - t)

    def mask(sw):
        m = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(m).text(org, s, font=f, fill=255, stroke_width=sw, stroke_fill=255)
        return m

    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    full = mask(stroke + outer)
    sh = full.filter(ImageFilter.GaussianBlur(size // 10))
    out.paste(Image.new("RGBA", (cw, ch), (0, 0, 0, 190)), (size // 16, size // 12), sh)
    if glow:
        gl = full.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(size // 5))
        out.paste(Image.new("RGBA", (cw, ch), glow + (255,)), (0, 0), gl.point(lambda v: min(255, int(v * 1.6))))
    if outer:
        out.paste(Image.new("RGBA", (cw, ch), (0, 0, 0, 255)), (0, 0), full)
        out.paste(Image.new("RGBA", (cw, ch), (255, 255, 255, 255)), (0, 0), mask(stroke))
    else:
        out.paste(Image.new("RGBA", (cw, ch), (0, 0, 0, 255)), (0, 0), mask(stroke))
    face = mask(0)
    if kind == "white":
        out.paste(Image.new("RGBA", (cw, ch), (255, 255, 255, 255)), (0, 0), face)
    else:
        stops = {"yel": YEL, "red": RED, "fire": FIRE}[kind]
        bb = face.getbbox()
        g = Image.new("RGB", (cw, ch))
        g.paste(gradient((cw, bb[3] - bb[1]), stops), (0, bb[1]))
        out.paste(g, (0, 0), face)
    return out.crop(out.getbbox())


def line(parts, size, max_w):
    """[(글자, 종류)] 한 줄. 폭을 넘으면 글자 크기를 줄인다."""
    while True:
        lays = [text_layer(s, size, k, glow) for s, k, glow in parts]
        ov = size // 8
        tw = sum(l.width for l in lays) - ov * (len(lays) - 1)
        if tw <= max_w or size < 50:
            break
        size -= 4
    hh = max(l.height for l in lays)
    out = Image.new("RGBA", (tw, hh), (0, 0, 0, 0))
    x = 0
    for l in lays:
        out.alpha_composite(l, (x, hh - l.height))
        x += l.width - ov
    return out


def P(s, kind="white", glow=None):
    return (s, kind, glow)


def badge(img, xy, s, size=40, bg=(0, 0, 0), fg=(255, 255, 255), border=(255, 214, 40)):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(GOTH, size)
    x, y = xy
    w = d.textlength(s, font=f)
    d.rounded_rectangle([x, y, x + w + 44, y + size + 28], radius=10, fill=bg, outline=border, width=4)
    d.text((x + 22, y + 10), s, font=f, fill=fg)


def band(img, x0, x1, y0, lines, size=44):
    d = ImageDraw.Draw(img, "RGBA")
    f = ImageFont.truetype(GOTH, size)
    hgt = len(lines) * (size + 14) + 26
    d.rectangle([x0, y0, x1, y0 + hgt], fill=(0, 0, 0, 175))
    for i, s in enumerate(lines):
        d.text((x0 + 26, y0 + 14 + i * (size + 14)), s, font=f, fill=(255, 222, 30), stroke_width=3, stroke_fill=(0, 0, 0))


def circle_inset(img, name, box, center, radius, ring=(255, 255, 255)):
    src = keyframe(name, 768).crop(box).resize((radius * 2, radius * 2), Image.LANCZOS)
    m = Image.new("L", src.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, radius * 2 - 1, radius * 2 - 1], fill=255)
    lay = Image.new("RGBA", (radius * 2 + 40, radius * 2 + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([6, 10, radius * 2 + 34, radius * 2 + 38], fill=(0, 0, 0, 150))
    lay = lay.filter(ImageFilter.GaussianBlur(6))
    d = ImageDraw.Draw(lay)
    d.ellipse([12, 12, radius * 2 + 28, radius * 2 + 28], fill=ring + (255,))
    lay.paste(src, (20, 20), m)
    img.alpha_composite(lay, (center[0] - radius - 20, center[1] - radius - 20))


# ---------- 3종 ----------
def thumb_a():
    """A 泣ける: 엄마(S47) 눈물 CU를 오른쪽으로, 왼쪽 어둡게 + 2줄 + 초대형 「ごめんなさい」."""
    img = shifted("S47", 230)
    shade(img, None, alpha=215, side="left")
    shade(img, (0, 0, 250, H), alpha=120, blur=60)               # 왼쪽 채움 경계가 보이지 않게
    shade(img, (0, 520, 1100, 720), alpha=150, blur=60)
    t1 = line([P("「構わないで」と")], 70, 560)
    t2 = line([P("突き放した", "white"), P("母が…", "yel")], 70, 560)
    img.alpha_composite(t1, (34, 70))
    img.alpha_composite(t2, (34, 70 + t1.height + 6))
    big = line([P("「ごめんなさい」", "fire", (200, 20, 0))], 150, 1060)
    img.alpha_composite(big, (8, H - big.height - 34))
    return img


def thumb_b():
    """B 어두운 실사 CU: 김씨(S23) 정면 응시를 왼쪽 1/3로, 오른쪽 어두운 창 쪽에 흰 3줄 + 초대형 인용구."""
    img = shifted("S23", -250, g=1.08)
    shade(img, None, alpha=200, side="right")
    x0 = 600
    for i, s in enumerate(("給料日の夜、", "無口な警備員は", "窓口でこう言った")):
        t = line([P(s)], 56, 640)
        img.alpha_composite(t, (x0, 40 + i * (t.height + 2)))
    q1 = line([P("「決して、", "fire", (200, 20, 0))], 138, 660)
    q2 = line([P("言わないで」", "fire", (200, 20, 0))], 138, 680)
    img.alpha_composite(q1, (x0 - 10, 270))
    img.alpha_composite(q2, (x0 - 10, 270 + q1.height - 8))
    return img


def thumb_c():
    """C 따뜻한 실사: 김씨 미소(S50) 왼쪽 + 오른쪽 위 검은 라벨 + 빨강/노랑 2줄 + 털실 별 인서트 + 반투명 띠(왼쪽)."""
    img = shifted("S50", -40, g=1.05)
    shade(img, (620, 0, W, 420), alpha=150, blur=90)
    badge(img, (W - 260, 26), "泣ける話")
    t1 = line([P("亡き妻の", "red")], 128, 600)
    t2 = line([P("最後の願い", "yel")], 128, 640)
    img.alpha_composite(t1, (W - t1.width - 24, 104))
    img.alpha_composite(t2, (W - t2.width - 18, 104 + t1.height - 6))
    circle_inset(img, "S33", (390, 120, 1030, 760), (140, 150), 104)   # 소품은 얼굴·글자를 피해 왼쪽 위 창가
    band(img, 0, 900, 560, ["七年ぶりに、毛糸の星を", "小さなツリーのてっぺんへ"], 46)
    return img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "thumbnails", "ep4")
    os.makedirs(out, exist_ok=True)
    phone = []
    for tag, fn in (("A-gomennasai", thumb_a), ("B-iwanaide", thumb_b), ("C-negai", thumb_c)):
        im = fn().convert("RGB")
        p = os.path.join(out, f"EP4-abc-{tag}-JP.jpg")
        im.save(p, quality=92)
        assert os.path.getsize(p) < 2 * 1024 * 1024
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        im.resize((168, 95), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone168.png"))
        phone.append(im)
        print("저장:", p, os.path.getsize(p) // 1024, "KB")
    # 휴대폰 확인 시트: 위 360px 3장, 아래 168px 3장(실제 크기)
    sheet = Image.new("RGB", (360 * 3 + 40, 203 + 95 + 50), (24, 24, 24))
    for i, im in enumerate(phone):
        sheet.paste(im.resize((360, 203), Image.LANCZOS), (10 + i * 370, 10))
        sheet.paste(im.resize((168, 95), Image.LANCZOS), (10 + i * 370, 233))
    sheet.save(os.path.join(out, "EP4-abc-phone-check.jpg"), quality=90)


if __name__ == "__main__":
    main()
