#!/usr/bin/env python3
"""썸네일 베이스(AI 생성, 글자 없음) 위에 일본어 카피를 실글꼴로 합성(무과금) — 생성기가 글자를 그리면 외계어가 나온다(제2장).
감독님 지정 카피(2026-10-08): A 전후 대비형 · B 결정적 증거형 · C 권선징악 사이다형.
사용법: make_thumb_copy.py [--tower] <A베이스.png> <B베이스.png> <C베이스.png> <출력 폴더>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BLACK = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")
W, H = 1280, 720
YELLOW, RED, WHITE, INK, TEAL = (255, 222, 0), (220, 20, 30), (255, 255, 255), (10, 10, 10), (0, 200, 190)


def font(px):
    return ImageFont.truetype(BLACK, int(px))


def fit_px(d, text, maxw, px):
    while px > 20 and d.textlength(text, font=font(px)) > maxw:
        px -= 2
    return px


def outlined(d, xy, text, px, fill, stroke, sw, anchor="la"):
    d.text(xy, text, font=font(px), fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


def arrow(d, x, y, size, fill, stroke):
    """➔(글꼴에 없음) — 도형으로 그린 굵은 화살표."""
    s = size
    pts = [(x, y - s * 0.16), (x + s * 0.55, y - s * 0.16), (x + s * 0.55, y - s * 0.38), (x + s, y),
           (x + s * 0.55, y + s * 0.38), (x + s * 0.55, y + s * 0.16), (x, y + s * 0.16)]
    d.polygon(pts, fill=stroke); d.polygon([(px + (2 if px > x else 3), py) for px, py in pts], fill=fill)


def base(path):
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height); im = im.resize((int(im.width * s + 0.5), int(im.height * s + 0.5)), Image.LANCZOS)
    return im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))


def thumb_a(src):
    """썸네일 크기에서 읽히도록 두 줄·대형(2026-10-08 검수: 한 줄은 글자가 너무 작음)."""
    im = base(src); d = ImageDraw.Draw(im)
    px = 54   # 웃는 얼굴(머리 x≈360부터)을 가리지 않는 폭(실측)
    for k, t in enumerate(("「紙と一緒に", "　カビてろｗ」")):
        outlined(d, (22, 22 + k * (px + 10)), t, px, YELLOW, RED, 10)
    px2 = 88; lines = ("「10年横領で", "即日クビ」")
    ys = [H - 30 - (px2 + 10), H - 30]
    for t, y in zip(lines, ys):
        tw = d.textlength(t, font=font(px2)); outlined(d, (W - 26 - tw, y), t, px2, WHITE, INK, 10, "ls")
    tw0 = d.textlength(lines[0], font=font(px2))
    arrow(d, W - 26 - tw0 - px2 * 1.0, ys[0] - px2 * 0.36, px2 * 0.85, WHITE, INK)
    return im


MINCHO = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")


def fix_invoice(im):
    """B 베이스(thumbB-1) 전표: AI가 그린 도장 속 외계어·제목 낙서를 지우고 실글꼴로 다시 그린다(제2장).
    도장 중심·반지름·종이 기울기는 1280x720 실측(2026-10-08)."""
    import cv2
    import numpy as np
    a = np.asarray(im).copy()
    mk = np.zeros(a.shape[:2], np.uint8)
    cv2.circle(mk, (729, 395), 66, 255, -1)                      # 도장 전체
    cv2.rectangle(mk, (500, 188), (556, 216), 255, -1)            # 제목 낙서
    cv2.rectangle(mk, (498, 243), (542, 260), 255, -1)            # 붉은 잔글씨
    a = cv2.inpaint(a, mk, 7, cv2.INPAINT_TELEA)
    im = Image.fromarray(a)
    # 제목 「請求書」(종이 기울기 약 -4도)
    t = Image.new("RGBA", (160, 40), (0, 0, 0, 0)); ImageDraw.Draw(t).text((0, 2), "請 求 書", font=ImageFont.truetype(MINCHO, 26), fill=(40, 52, 90, 230))
    t = t.rotate(4, resample=Image.BICUBIC, expand=True); im.paste(t, (500, 180), t)
    # 붉은 도장: 이중 원 + 「承認」(인주 번짐·얼룩)
    r = 60; st = Image.new("RGBA", (2 * r + 20, 2 * r + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(st); c = r + 10
    red = (210, 24, 36, 235)
    d.ellipse((c - r, c - r, c + r, c + r), outline=red, width=7)
    d.ellipse((c - r + 12, c - r + 12, c + r - 12, c + r - 12), outline=red, width=3)
    d.text((c, c - 18), "承", font=ImageFont.truetype(MINCHO, 40), fill=red, anchor="mm")
    d.text((c, c + 22), "認", font=ImageFont.truetype(MINCHO, 40), fill=red, anchor="mm")
    arr = np.asarray(st).astype(np.float32)
    noise = np.random.default_rng(7).uniform(0.6, 1.0, arr.shape[:2])
    arr[..., 3] *= cv2.GaussianBlur(noise.astype(np.float32), (0, 0), 1.2)
    st = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).rotate(-8, resample=Image.BICUBIC)
    im.paste(st, (729 - c, 395 - c), st)
    return im


def thumb_b(src):
    im = base(src)
    if os.path.basename(src) == "thumbB-1.png":
        im = fix_invoice(im)
    d = ImageDraw.Draw(im)
    t1 = "「この伝票、見覚えありますよね？」"; px = fit_px(d, t1, W * 0.94, 70)
    outlined(d, (W / 2, 26), t1, px, TEAL, INK, 9, "ma")
    t2 = "【3,000万円 業務上横領】"; px2 = fit_px(d, t2, W * 0.78, 80)
    tw = d.textlength(t2, font=font(px2)); cx, cy = W / 2, H * 0.86   # 도장(증거)을 가리지 않게 아래로
    pad_x, pad_y = 30, 20
    box = (cx - tw / 2 - pad_x, cy - px2 / 2 - pad_y, cx + tw / 2 + pad_x, cy + px2 / 2 + pad_y)
    d.rectangle((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), fill=WHITE)
    d.rectangle(box, fill=RED)
    outlined(d, (cx, cy), t2, px2, WHITE, (90, 0, 0), 4, "mm")
    return im


def thumb_c(src):
    im = base(src); d = ImageDraw.Draw(im)
    t1 = "「お前の代わりは幾らでもいるｗ」"; px = fit_px(d, t1, W * 0.9, 68)
    outlined(d, (W / 2, 24), t1, px, YELLOW, INK, 9, "ma")
    t2 = "「無能部長、完全破滅＆逮捕！」"; px2 = fit_px(d, t2, W * 0.86, 96)
    tw = d.textlength(t2, font=font(px2)); x = (W - tw) / 2 + px2 * 0.5; y = H - 34
    outlined(d, (x, y), t2, px2, RED, WHITE, 10, "ls")
    arrow(d, x - px2 * 1.0, y - px2 * 0.36, px2 * 0.85, RED, WHITE)
    return im


# 『タワマンのボスママ』 애니메이션풍(2026-10-08 감독님 요청) — 카피는 본편 대사·사실(2,400만 엔·집세 체납·42층 주인)에 맞춤
def two_lines(d, lines, px, fill, stroke, x, y, right=False, gap=10):
    for k, t in enumerate(lines):
        if right:
            tw = d.textlength(t, font=font(px)); outlined(d, (x - tw, y + k * (px + gap)), t, px, fill, stroke, 10)
        else:
            outlined(d, (x, y + k * (px + gap)), t, px, fill, stroke, 10)


def tower_a(src, px_left=60):
    im = base(src); d = ImageDraw.Draw(im)
    two_lines(d, ("「低層階は荷物用", "　エレベーターへｗ」"), px_left, YELLOW, RED, 22, 22)
    px2 = 86; lines = ("「家賃滞納で", "即・退去」"); y0 = H - 30 - 2 * px2 - 10
    two_lines(d, lines, px2, WHITE, INK, W - 26, y0, right=True)
    tw0 = d.textlength(lines[0], font=font(px2)); arrow(d, W - 26 - tw0 - px2, y0 + px2 * 0.5, px2 * 0.85, WHITE, INK)
    return im


def tower_b(src):
    im = base(src); d = ImageDraw.Draw(im)
    t1 = "「この通帳、ご覧ください」"; px = fit_px(d, t1, W * 0.9, 78)
    outlined(d, (W / 2, 24), t1, px, TEAL, INK, 10, "ma")
    t2 = "【2,400万円 業務上横領】"; px2 = fit_px(d, t2, W * 0.78, 80)
    tw = d.textlength(t2, font=font(px2)); cx, cy = W / 2, H * 0.86
    box = (cx - tw / 2 - 30, cy - px2 / 2 - 20, cx + tw / 2 + 30, cy + px2 / 2 + 20)
    d.rectangle((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), fill=WHITE); d.rectangle(box, fill=RED)
    outlined(d, (cx, cy), t2, px2, WHITE, (90, 0, 0), 4, "mm")
    return im


def tower_c(src):
    im = base(src); d = ImageDraw.Draw(im)
    t1 = "「私は42階のオーナーよｗ」"; px = fit_px(d, t1, W * 0.86, 76)
    outlined(d, (W / 2, 22), t1, px, YELLOW, INK, 10, "ma")
    t2 = "「本当の持ち主、登場！」"; px2 = fit_px(d, t2, W * 0.8, 96)
    tw = d.textlength(t2, font=font(px2)); x = (W - tw) / 2 + px2 * 0.5; y = H - 34
    outlined(d, (x, y), t2, px2, RED, WHITE, 10, "ls"); arrow(d, x - px2, y - px2 * 0.36, px2 * 0.85, RED, WHITE)
    return im


def main():
    if sys.argv[1] == "--tower":
        a, b, c, out = sys.argv[2:6]; os.makedirs(out, exist_ok=True)
        for name, fn, src in (("A-반전형-anime", tower_a, a), ("B-통장형-anime", tower_b, b), ("C-진짜주인형-anime", tower_c, c)):
            p = os.path.join(out, f"tower-thumb-{name}.jpg"); fn(src).save(p, quality=92); print("저장:", p)
        return
    a, b, c, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    for name, fn, src in (("A-전후대비형", thumb_a, a), ("B-증거폭로형", thumb_b, b), ("C-사이다형", thumb_c, c)):
        p = os.path.join(out, f"thumb-{name}.jpg"); fn(src).save(p, quality=92); print("저장:", p)


if __name__ == "__main__":
    main()
