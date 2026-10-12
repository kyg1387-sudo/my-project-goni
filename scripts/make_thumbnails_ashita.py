#!/usr/bin/env python3
"""『明日から来なくていい』 썸네일 3종(1920x1080, 무과금·로컬, 승인 키프레임만 사용).
고니감독님 지정 형식(2026-10-12, 채널 기존 썸네일 3장 기준):
  A 웹툰 일러스트형 — 왼쪽 인물 + 왼쪽 위 흰 라벨 「スカッとする話」 + 세로로 쌓은 초대형 그라데이션 글자(노랑→주황→빨강, 흰 테·검은 테)
                      + 오른쪽 무릎 꿇은 악역·내려다보는 주인공 + 붉은 배지(금테) + 검은 띠 노란 글자
  B 실사 드라마형   — 실사 장면 그대로 + 오른쪽 위 검은 라벨 + 빨강/노랑 2줄 제목(흰 테) + 아래 반투명 검은 띠 노란 글자 2줄
  C 감정 클로즈업형 — 어두운 실사, 오른쪽 인물 얼굴 크게 + 왼쪽 흰 글자 3줄 + 아래 초대형 인용구 「」(그라데이션·붉은 글로)
오른쪽 아래(재생 시간 표시)는 비운다. 피·폭력 없음. 가상 회사명만.
사용법: make_thumbnails_ashita.py [out_dir]  (기본 assets/thumbnails/ashita)
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from make_thumbnails_yanagi_v2 import cover, cutout, text_layer, toon, to_pil, vignette  # noqa: E402

K = os.path.join(ROOT, "assets", "portraits", "ashita-kara-keyframes")
GOTH = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")
MIN = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")
W, H = 1920, 1080
FIRE = ((255, 236, 60), (255, 150, 20), (225, 30, 20))        # 노랑 → 주황 → 빨강(기존 썸네일 글자)


def kf(name):
    return cv2.cvtColor(cv2.imread(os.path.join(K, f"{name}-1.png")), cv2.COLOR_BGR2RGB)


def big(s, size, gradient=FIRE, fill=None, stroke_w=14, outer_w=10, font=GOTH):
    """기존 썸네일의 굵은 글자: 그라데이션(또는 단색) + 흰 테 + 바깥 검은 테."""
    lay = text_layer(s, font, size, fill, (255, 255, 255), stroke_w, gradient=gradient, outer=(0, 0, 0), outer_w=outer_w)
    return lay


def glow(lay, color=(255, 30, 0), r=22, strength=1.6):
    a = lay.split()[3].filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * strength)))
    g = Image.new("RGBA", lay.size, color + (0,)); g.putalpha(a)
    return Image.alpha_composite(g, lay)


def label(s, size, bg, fg, border=None, pad=(34, 14), radius=18):
    f = ImageFont.truetype(GOTH, size)
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), s, font=f)
    w, h = bb[2] - bb[0] + pad[0] * 2, bb[3] - bb[1] + pad[1] * 2
    lay = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if border:
        d.rounded_rectangle([0, 0, w + 7, h + 7], radius + 4, fill=border)
    d.rounded_rectangle([4, 4, w + 3, h + 3], radius, fill=bg)
    d.text((4 + pad[0] - bb[0], 4 + pad[1] - bb[1]), s, font=f, fill=fg)
    return lay


def band(lines, size, fg=(255, 226, 40), alpha=215, pad=(30, 16), gap=10):
    f = ImageFont.truetype(GOTH, size)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    bbs = [d0.textbbox((0, 0), s, font=f) for s in lines]
    w = max(b[2] - b[0] for b in bbs) + pad[0] * 2
    h = sum(b[3] - b[1] for b in bbs) + gap * (len(lines) - 1) + pad[1] * 2
    lay = Image.new("RGBA", (w, h), (0, 0, 0, alpha))
    d = ImageDraw.Draw(lay)
    y = pad[1]
    for s, b in zip(lines, bbs):
        d.text((pad[0] - b[0], y - b[1]), s, font=f, fill=fg, stroke_width=3, stroke_fill=(0, 0, 0))
        y += b[3] - b[1] + gap
    return lay


def person(name, rect, crop, scale, outline=True):
    """키프레임 인물 → 툰 처리 RGBA(흰 외곽선)."""
    src = kf(name)
    a = cutout(src, rect)
    rgba = np.dstack([toon(src, halftone=False), a * 255]).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA").crop(crop)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    if outline:
        edge = im.split()[3].filter(ImageFilter.MaxFilter(11))
        ol = Image.new("RGBA", im.size, (255, 245, 235, 0)); ol.putalpha(edge.point(lambda v: 255 if v > 60 else 0))
        base = Image.new("RGBA", im.size, (0, 0, 0, 0)); base.alpha_composite(ol); base.alpha_composite(im)
        return base
    return im


# ---------------------------------------------------------------- A 웹툰 일러스트형
def white(s, size, stroke_w=12):
    """흰 글자 + 검은 테(흰 테를 두르면 획이 뭉개짐 — 그라데이션 글자에만 흰 테)."""
    return text_layer(s, GOTH, size, (255, 255, 255), (0, 0, 0), stroke_w)


def thumb_a():
    # 배경: 무릎 꿇고 비는 田中 + 앞쪽 佐藤의 뒷모습(S25a)을 웹툰 톤으로, 오른쪽에 배치. 어두운 실루엣 오려내기(GrabCut)는
    # 암전 장면에서 배경을 덩어리로 잘라 내므로 쓰지 않는다.
    src = kf("S25a")
    t = toon(cv2.bilateralFilter(src, 9, 80, 80), halftone=True)
    t = t * np.array([1.05, 0.82, 0.78]) + np.array([20, 0, 0])
    r = cover(np.clip(t, 0, 255).astype(np.uint8), 1300, H, 0.47, 0.5).astype(np.float32)
    canvas = np.zeros((H, W, 3), np.float32)
    canvas[:] = np.array([70, 6, 6])
    canvas[:, W - 1300:] = r
    ramp = np.clip((np.arange(W) - (W - 1300)) / 420, 0, 1)[None, :, None]   # 왼쪽으로 붉은 어둠에 녹아듦
    canvas = canvas * (0.25 + 0.75 * ramp) + np.array([55, 4, 4]) * (1 - ramp)
    img = to_pil(vignette(canvas, 0.45)).convert("RGBA")
    # 위에서 떨어지는 스포트라이트(田中 위)
    sp = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sp).polygon([(1130, 0), (1380, 0), (1520, H), (980, H)], fill=70)
    img = Image.alpha_composite(img, Image.merge("RGBA", [Image.new("L", (W, H), 255)] * 3 + [sp.filter(ImageFilter.GaussianBlur(70))]))
    # 글자
    img.alpha_composite(label("スカッとする話", 64, (255, 255, 255, 255), (20, 20, 20)), (36, 30))
    img.alpha_composite(white("クビにした男が", 120), (24, 168))
    img.alpha_composite(big("百億円の", 236), (0, 318))
    img.alpha_composite(big("鍵だった", 256), (0, 600))
    badge = label("上司の不正、暴かれる", 46, (190, 20, 20, 255), (255, 255, 255), pad=(30, 10))
    num = big("三億円の改ざん", 96, gradient=((255, 255, 170), (255, 220, 40), (255, 160, 0)), stroke_w=8, outer_w=6)
    box = Image.new("RGBA", (max(badge.width, num.width) + 40, badge.height + num.height + 6), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 26, fill=(255, 200, 40, 255))
    ImageDraw.Draw(box).rounded_rectangle([7, 7, box.width - 8, box.height - 8], 22, fill=(170, 16, 16, 245))
    box.alpha_composite(badge, ((box.width - badge.width) // 2, 10))
    box.alpha_composite(num, ((box.width - num.width) // 2, badge.height - 4))
    img.alpha_composite(box, (W - box.width - 40, 500))
    img.alpha_composite(band(["懲戒解雇、そして…"], 66, alpha=235), (1150, 850))
    return img.convert("RGB")


# ---------------------------------------------------------------- B 실사 드라마형
def thumb_b():
    a = cover(kf("S14d"), W, H, 0.5, 0.5).astype(np.float32)
    a = (a - 128) * 1.08 + 132
    img = to_pil(vignette(a, 0.45)).convert("RGBA")
    img.alpha_composite(label("スカッとする話", 62, (12, 12, 12, 255), (255, 255, 255), border=(255, 255, 255, 255)), (1180, 40))
    l1 = big("クビ宣告の夜…", 118, gradient=((255, 90, 80), (225, 20, 20), (150, 0, 0)), stroke_w=10, outer_w=6)
    img.alpha_composite(l1, (1830 - l1.width, 150))
    l2a = big("男が残した", 128, gradient=((255, 90, 80), (225, 20, 20), (150, 0, 0)), stroke_w=10, outer_w=6)
    l2b = big("約束", 140, gradient=((255, 255, 170), (255, 220, 40), (255, 150, 0)), stroke_w=10, outer_w=6)
    x0 = 1880 - l2a.width - l2b.width + 30
    img.alpha_composite(glow(l2b, (255, 200, 0), 18, 1.2), (x0 + l2a.width - 30, 302))
    img.alpha_composite(l2a, (x0, 310))
    img.alpha_composite(band(["その遮断器が、", "百億円の現場を救う"], 74, alpha=200), (1040, 720))
    return img.convert("RGB")


# ---------------------------------------------------------------- C 감정 클로즈업형
def thumb_c():
    src = kf("S13a").astype(np.float32)
    a = cover(src.astype(np.uint8), W, H, 0.64, 0.30, zoom=2.05).astype(np.float32)
    g = a.mean(axis=2, keepdims=True)
    a = a * 0.55 + g * 0.45                                       # 채도 낮춤
    a = a * np.array([0.88, 0.95, 1.08])                           # 차가운 톤
    a = (a - 128) * 1.12 + 108
    # 왼쪽을 어둡게(글자 자리)
    ramp = np.clip((np.arange(W) - 420) / 600, 0, 1)[None, :, None]
    a = a * (0.28 + 0.72 * ramp)
    img = to_pil(vignette(a, 0.55)).convert("RGBA")
    for i, s in enumerate(["30年", "会社を支えた男に", "上司は言った…"]):
        img.alpha_composite(white(s, 104, 10), (50, 90 + i * 146))
    q = big("「明日から来るな」", 196, stroke_w=12, outer_w=8)
    q = glow(q, (230, 20, 0), 34, 1.8)
    img.alpha_composite(q, ((W - q.width) // 2 - 60, H - q.height - 20))
    return img.convert("RGB")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "thumbnails", "ashita")
    os.makedirs(out, exist_ok=True)
    for name, fn in (("A-webtoon", thumb_a), ("B-drama", thumb_b), ("C-quote", thumb_c)):
        p = os.path.join(out, f"ashita-thumb-{name}-JP.jpg")
        fn().save(p, quality=92)
        print("저장:", p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main()
