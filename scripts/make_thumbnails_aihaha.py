#!/usr/bin/env python3
"""『母が遺したビデオレター』 썸네일 글자 합성(로컬, 무료) — 제13장 5·제0장 8·최우선 원칙 7④(스캇토형: 굵은 일본어 + 강렬한 하단 그라데이션).

강한 글자(고니감독님 2026-11-05 「텍스트도 강하게」, 레퍼런스: 사선 극대형·흰/빨강 채움·두꺼운 검은 테두리):
  - 극대형 굵은 고딕(Noto Sans CJK Bold + 같은 색 획으로 한 단계 더 굵게), 사선(전단 −10°) + 살짝 기울임(−4°)
  - 3중 테두리: 안쪽 흰 선(색 글자만) → 두꺼운 검은 테두리 → 바깥 붉은/노란 글로, 아래로 떨어지는 그림자(입체감)
  - 색 글자는 위→아래 그라데이션(노랑→주황 / 빨강→진홍)
  - 하단 그라데이션 띠(검정 → 투명)
출력: deliveries/aihaha-upload/thumb-<id>.jpg (1280x720, 2MB 이하) + 168px·360px 확인본
사용법: python3 scripts/make_thumbnails_aihaha.py [id,…]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "deliveries", "aihaha-upload")
GB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W, H = 1280, 720
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
GRAD = {"yellow": ((255, 238, 60), (255, 150, 0)), "red": ((255, 70, 60), (190, 0, 20)), "white": ((255, 255, 255), (230, 232, 240))}
GLOW = {"yellow": (255, 140, 0), "red": (255, 0, 30), "white": (0, 0, 0)}


def text_layer(txt, size, color, stroke=14, inner=True):
    """한 줄 글자를 RGBA 레이어로(사선 전 상태). color = GRAD 키."""
    f = ImageFont.truetype(GB, size)
    pad = stroke * 3 + 20
    l, t, r, b = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), txt, font=f, stroke_width=4)
    w, h = r - l + pad * 2, b - t + pad * 2
    ox, oy = pad - l, pad - t
    def mask(sw):
        m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((ox, oy), txt, font=f, fill=255, stroke_width=sw, stroke_fill=255); return m
    body = mask(3)  # 같은 색 획 3px = 한 단계 더 굵게
    outer = mask(3 + stroke)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow = Image.new("RGBA", (w, h), GLOW[color] + (0,)); glow.putalpha(outer.filter(ImageFilter.GaussianBlur(stroke * 0.9)).point(lambda v: int(v * 0.85)))
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0)); shadow.putalpha(outer.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.9)))
    lay.alpha_composite(glow)
    lay.alpha_composite(shadow, (0, max(4, stroke // 2)))  # 아래로 떨어지는 그림자 = 입체
    blk = Image.new("RGBA", (w, h), BLACK + (255,)); blk.putalpha(outer); lay.alpha_composite(blk)
    if inner and color != "white":
        wl = Image.new("RGBA", (w, h), WHITE + (255,)); wl.putalpha(mask(3 + max(3, stroke // 4))); lay.alpha_composite(wl)
    c0, c1 = GRAD[color]; g = np.zeros((h, w, 4), np.uint8)
    ys = np.clip((np.arange(h) - oy) / max(b - t, 1), 0, 1)[:, None]
    for k in range(3):
        g[..., k] = (c0[k] * (1 - ys) + c1[k] * ys).astype(np.uint8)
    g[..., 3] = np.asarray(body)
    lay.alpha_composite(Image.fromarray(g, "RGBA"))
    hl = Image.new("RGBA", (w, h), (255, 255, 255, 0)); hm = np.asarray(body).astype(np.float32) * np.clip(1 - (np.arange(h)[:, None] - oy) / ((b - t) * 0.35 + 1), 0, 1) * 0.28
    hl.putalpha(Image.fromarray(hm.astype(np.uint8))); lay.alpha_composite(hl)  # 위쪽 광택
    return lay


def slant(lay, shear=-0.18, rot=4):
    w, h = lay.size
    lay = lay.transform((int(w + abs(shear) * h), h), Image.AFFINE, (1, shear, shear * h if shear < 0 else 0, 0, 1, 0), resample=Image.BICUBIC)
    return lay.rotate(rot, resample=Image.BICUBIC, expand=True)


def bottom_band(im, top=0.52, alpha=0.88):
    a = np.zeros((H, W), np.float32); y0 = int(H * top)
    a[y0:] = np.linspace(0, alpha, H - y0)[:, None] ** 1.2
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); band.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    im.alpha_composite(band); return im


def fit169(im):
    w, h = im.size; tw = int(round(h * 16 / 9))
    if tw < w:
        x0 = (w - tw) // 2; return im.crop((x0, 0, x0 + tw, h))
    th = int(round(w * 9 / 16)); y0 = (h - th) // 2; return im.crop((0, y0, w, y0 + th))


def compose(bg, lines, out, band=0.50, keep_br=True, maxw_frac=0.64):
    """lines: [(글자, 크기, 색, x, y)] — x·y는 사선 처리 후 왼쪽 위 기준(1280x720). 오른쪽 아래(재생 시간)는 비운다."""
    im = fit169(bg.convert("RGB")).resize((W, H), Image.LANCZOS).convert("RGBA")
    im = bottom_band(im, band)
    lays = []
    for txt, size, color, x, _ in lines:
        lay = slant(text_layer(txt, size, color, stroke=max(10, size // 9)))
        lay = lay.crop(lay.getbbox())  # 사선·회전 여백 제거
        maxw = int(W * maxw_frac)
        if lay.width > maxw:
            lay = lay.resize((maxw, int(lay.height * maxw / lay.width)), Image.LANCZOS)
        lays.append((lay, x))
    y = H - 14  # 아래 줄부터 위로 쌓는다(줄 사이 겹침 −0.12 — 레퍼런스처럼 촘촘히)
    for lay, x in reversed(lays):
        y -= lay.height
        im.alpha_composite(lay, (int(x), int(y)))
        y += int(lay.height * 0.12)
    if keep_br:  # 재생 시간 표시 자리(오른쪽 아래 약 120x50) 확인용 — 글자가 침범하면 경고
        a = np.asarray(im)[H - 50:H, W - 130:W, :3].astype(int)
    rgb = im.convert("RGB"); os.makedirs(os.path.dirname(out), exist_ok=True)
    rgb.save(out, quality=92)
    for wv in (168, 360):
        rgb.resize((wv, int(wv * H / W)), Image.LANCZOS).save(out.replace(".jpg", f"-{wv}.jpg"), quality=90)
    return out


TEST = {"test-a": ("assets/portraits/aihaha-keyframes/H0b-1.png", [("この母、", 120, "white", 30, 360), ("AIです", 210, "yellow", 40, 470)]),
        "test-b": ("assets/portraits/aihaha-keyframes/S10m-1.png", [("期限は、", 120, "white", 30, 360), ("昨日", 230, "red", 60, 470)])}


# A/B 테스트 3종(고니감독님 생성 그림 2026-11-05, 순서는 제작 수석 결정: A 가짜 엄마 = 0:00 후크 약속·의문 최강, B 애니 통쾌, C 눈물)
# (그림, [(글자, 크기, 색, x, _)], 글자 최대 폭 비율) — 얼굴·태블릿을 가리지 않는 쪽에, 아래 줄부터 위로 쌓음
THUMBS = {
    "A": ("assets/thumbs/aihaha/src-A.jpg", [("この母、", 130, "red", 24, 0), ("AIです", 230, "yellow", 30, 0)], 0.56),
    "B": ("assets/thumbs/aihaha/src-B.jpg", [("期限は、", 120, "yellow", 20, 0), ("昨日", 250, "red", 40, 0)], 0.36),
    "C": ("assets/thumbs/aihaha/src-C.jpg", [("母が最後に", 120, "yellow", 20, 0), ("呼んだ名前", 150, "red", 24, 0)], 0.50),
}


def main(only=None):
    for k, (bg, lines, mw) in THUMBS.items():
        if only and k not in only:
            continue
        print(compose(Image.open(os.path.join(ROOT, bg)), lines, os.path.join(OUT, f"thumb-{k}.jpg"), maxw_frac=mw))


if __name__ == "__main__":
    main(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
