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
    """글자 뒤 빛 번짐. 레이어 가장자리에서 번짐이 잘려 네모 띠가 보이지 않도록 먼저 2r만큼 여백을 둔다."""
    padded = Image.new("RGBA", (lay.width + 4 * r, lay.height + 4 * r), (0, 0, 0, 0))
    padded.alpha_composite(lay, (2 * r, 2 * r))
    lay = padded
    a = lay.split()[3].filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * strength)))
    g = Image.new("RGBA", lay.size, color + (0,)); g.putalpha(a)
    return Image.alpha_composite(g, lay)


def put(img, lay, x, y):
    """음수 좌표도 받는 합성(글로 여백만큼 왼쪽·위로 나가도 됨)."""
    tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    tmp.paste(lay, (x, y), lay)
    img.alpha_composite(tmp)


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




# ---------------------------------------------------------------- 그림체 샘플 + A 글자(애니메이션·아바타 비교)
def thumb_styled(src_png):
    """생성 일러스트(글자 없음) 위에 A형 글자 배치. 왼쪽을 살짝 어둡게 해 글자 가독성 확보."""
    a = cover(cv2.cvtColor(cv2.imread(src_png), cv2.COLOR_BGR2RGB), W, H, 0.5, 0.5).astype(np.float32)
    ramp = np.clip((np.arange(W) - 200) / 700, 0, 1)[None, :, None]
    a = a * (0.45 + 0.55 * ramp)
    img = to_pil(a).convert("RGBA")
    img.alpha_composite(label("スカッとする話", 64, (255, 255, 255, 255), (20, 20, 20)), (36, 30))
    img.alpha_composite(white("クビにした男が", 116), (24, 168))
    img.alpha_composite(big("百億円の", 230), (0, 318))
    img.alpha_composite(big("鍵だった", 250), (0, 596))
    badge = label("上司の不正、暴かれる", 44, (190, 20, 20, 255), (255, 255, 255), pad=(28, 10))
    num = big("三億円の改ざん", 90, gradient=((255, 255, 170), (255, 220, 40), (255, 160, 0)), stroke_w=8, outer_w=6)
    box = Image.new("RGBA", (max(badge.width, num.width) + 40, badge.height + num.height + 6), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 26, fill=(255, 200, 40, 255))
    ImageDraw.Draw(box).rounded_rectangle([7, 7, box.width - 8, box.height - 8], 22, fill=(170, 16, 16, 245))
    box.alpha_composite(badge, ((box.width - badge.width) // 2, 10))
    box.alpha_composite(num, ((box.width - num.width) // 2, badge.height - 4))
    img.alpha_composite(box, (W - box.width - 40, 560))
    img.alpha_composite(band(["懲戒解雇、そして…"], 62, alpha=235), (1150, 860))
    return img.convert("RGB")


def styled_samples(out):
    d = os.path.join(ROOT, "assets", "portraits", "ashita-style-samples")
    for n in ("anime-1", "anime-2", "avatar-1", "avatar-2"):
        p = os.path.join(out, f"ashita-thumb-{n}-JP.jpg")
        thumb_styled(os.path.join(d, f"{n}.png")).save(p, quality=92)
        print("저장:", p)


# ---------------------------------------------------------------- 아바타 확정판(휴대폰 기준, 강한 글자) — 고니감독님 선택 2026-10-12
def thumb_avatar(src_png, crop=(0.49, 0.0, 1.0, 1.0), stamp_xy=None):
    """휴대폰 썸네일(폭 약 360px)에서도 읽히게: 인물은 크게 오른쪽, 글자는 왼쪽 3줄만, 오른쪽 아래(재생 시간) 비움.
    글자 = 기울임 + 3D 돌출 + 금속 그라데이션 + 이중 테 + 글로."""
    from make_thumbnails_yanagi_v2 import banner as _banner  # noqa
    src = cv2.cvtColor(cv2.imread(src_png), cv2.COLOR_BGR2RGB)
    h0, w0 = src.shape[:2]
    x0, y0, x1, y1 = int(crop[0] * w0), int(crop[1] * h0), int(crop[2] * w0), int(crop[3] * h0)
    part = src[y0:y1, x0:x1]
    s = H / part.shape[0]
    part = cv2.resize(part, (int(part.shape[1] * s), H), interpolation=cv2.INTER_LANCZOS4)
    part = cv2.addWeighted(part, 1.35, cv2.GaussianBlur(part, (0, 0), 2.2), -0.35, 0)        # 확대 후 선명도 보정
    canvas = np.zeros((H, W, 3), np.float32)
    left = cv2.GaussianBlur(cover(src, W, H, 0.3, 0.5), (0, 0), 25).astype(np.float32) * 0.35   # 왼쪽 = 같은 장면을 흐리고 어둡게
    canvas[:] = left
    px = W - part.shape[1]
    feather = np.clip((np.arange(part.shape[1]) - 0) / 380, 0, 1)[None, :, None]
    canvas[:, px:] = canvas[:, px:] * (1 - feather) + part.astype(np.float32) * feather
    canvas = canvas * np.array([1.06, 0.97, 0.95])                                             # 붉은 조명 톤 살짝 강조
    img = to_pil(vignette(canvas, 0.35)).convert("RGBA")
    # 글자
    img.alpha_composite(_banner("スカッとする話", 58, (214, 20, 24)), (30, 30))
    l1 = text_layer("クビにした男が", GOTH, 108, (255, 255, 255), (0, 0, 0), 12, extrude=8, extrude_color=(60, 0, 0), shear=0.14)
    img.alpha_composite(l1, (22, 150))
    gold = ((255, 252, 215), (255, 205, 40), (205, 95, 0))
    red = ((255, 150, 120), (235, 20, 20), (130, 0, 0))
    l2 = text_layer("百億円の", GOTH, 208, None, (40, 0, 0), 14, extrude=16, extrude_color=(120, 20, 0), shear=0.14,
                    gradient=gold, outer=(255, 255, 255), outer_w=8)
    put(img, glow(l2, (255, 140, 0), 26, 1.1), -52, 290 - 52)
    l3 = text_layer("鍵だった", GOTH, 226, None, (20, 0, 0), 14, extrude=18, extrude_color=(70, 0, 0), shear=0.14,
                    gradient=red, outer=(255, 255, 255), outer_w=8)
    put(img, glow(l3, (255, 30, 0), 30, 1.3), -60, 560 - 60)
    # 오른쪽 붉은 도장(재생 시간이 뜨는 오른쪽 아래는 비움)
    st = Image.new("RGBA", (470, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    d.rounded_rectangle([0, 0, 469, 169], 16, outline=(230, 20, 20, 255), width=12)
    d.rounded_rectangle([18, 18, 451, 151], 8, outline=(230, 20, 20, 255), width=4)
    f = ImageFont.truetype(GOTH, 104)
    d.text((235, 88), "懲戒解雇", font=f, fill=(235, 25, 25, 255), anchor="mm", stroke_width=3, stroke_fill=(255, 255, 255, 255))
    st = st.rotate(-9, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(st, stamp_xy or (W - st.width - 30, 470))      # 사토의 얼굴(위)·田中의 얼굴(가운데)을 가리지 않는 위치
    return img.convert("RGB")


def anime_final(out):
    """고니감독님 지시(2026-10-12): 썸네일 화풍 = 애니메이션(일본 드라마 만화풍). 배치·글자는 아바타 확정판과 같은 휴대폰 기준."""
    d = os.path.join(ROOT, "assets", "portraits", "ashita-style-samples")
    for n, crop, sxy in (("anime-2", (0.43, 0.0, 1.0, 1.0), (1090, 660)), ("anime-1", (0.45, 0.0, 1.0, 1.0), None)):
        p = os.path.join(out, f"ashita-thumb-{n}-final-JP.jpg")
        im = thumb_avatar(os.path.join(d, f"{n}.png"), crop, sxy)
        im.save(p, quality=92)
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        print("저장:", p)


def avatar_final(out):
    d = os.path.join(ROOT, "assets", "portraits", "ashita-style-samples")
    for n in ("avatar-1", "avatar-2"):
        p = os.path.join(out, f"ashita-thumb-{n}-final-JP.jpg")
        im = thumb_avatar(os.path.join(d, f"{n}.png"))
        im.save(p, quality=92)
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)   # 휴대폰 크기 확인용
        print("저장:", p)


# ---------------------------------------------------------------- 인용구 클로즈업형 v2 (고니감독님 참고: 倉庫番 「土下座しろ」 썸네일)
def thumb_quote(kf_name, cx, cy, zoom, lines, quote, bright=1.0):
    """어두운 실사 + 오른쪽 큰 얼굴 + 왼쪽 흰 고딕 3줄(검은 테·그림자) + 아래 초대형 명조 인용구(노랑→주황→빨강, 흰 테, 붉은 글로)."""
    src = kf(kf_name)
    a = cover(src, W, H, cx, cy, zoom=zoom)
    a = cv2.addWeighted(a, 1.5, cv2.GaussianBlur(a, (0, 0), 2.5), -0.5, 0).astype(np.float32)   # 확대 후 선명도
    g = a.mean(axis=2, keepdims=True)
    a = a * 0.62 + g * 0.38                                       # 채도 낮춤(참고 썸네일의 탁한 실사 톤)
    a = a * np.array([0.9, 0.97, 1.06])                           # 차가운 푸른 그늘
    a = (a - 128) * 1.15 + 112
    a = 255 * (np.clip(a, 0, 255) / 255) ** (1 / bright)              # 밤 장면은 중간 톤을 들어 올림
    ramp = np.clip((np.arange(W) - 380) / 620, 0, 1)[None, :, None]
    a = a * (0.32 + 0.68 * ramp)                                  # 왼쪽(글자 자리) 어둡게
    img = to_pil(vignette(a, 0.6)).convert("RGBA")
    # 위에서 떨어지는 전등 빛(참고 썸네일의 매달린 전등 느낌)
    cone = Image.new("L", (W, H), 0)
    ImageDraw.Draw(cone).polygon([(820, 0), (1100, 0), (1350, H), (560, H)], fill=38)
    img = Image.alpha_composite(img, Image.merge("RGBA", [Image.new("L", (W, H), 255)] * 3 + [cone.filter(ImageFilter.GaussianBlur(80))]))
    for i, s in enumerate(lines):
        lay = text_layer(s, GOTH, 104, (255, 255, 255), (0, 0, 0), 12)
        sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.putalpha(lay.split()[3].filter(ImageFilter.GaussianBlur(10)))
        put(img, sh, 46 + 8, 170 + i * 140 + 10)
        put(img, lay, 46, 170 + i * 140)
    q = text_layer(quote, MIN, 184, None, (255, 255, 255), 12, gradient=((255, 238, 90), (255, 140, 20), (215, 20, 10)),
                   outer=(10, 0, 0), outer_w=8)
    q = glow(q, (220, 20, 0), 40, 2.0)
    put(img, q, (W - q.width) // 2 - 60, H - q.height + 40)
    return img.convert("RGB")


def quote_final(out):
    jobs = (("C1-quote", "S13a", 0.53, 0.30, 2.0, 1.0), ("C2-quote", "S14d", 0.30, 0.30, 1.85, 1.35))
    for name, k, cx, cy, z, br in jobs:
        p = os.path.join(out, f"ashita-thumb-{name}-JP.jpg")
        im = thumb_quote(k, cx, cy, z, ["30年", "会社を支えた男に", "上司は言った…"], "「明日から来るな」", br)
        im.save(p, quality=92)
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        print("저장:", p)


# ---------------------------------------------------------------- 애니메이션 HD판(倉庫番 「地獄を見せてやる」 형식) — 고니감독님 요청 2026-10-13
def thumb_anime_hd(src_png, shift=170):
    """2560x1440 생성 일러스트 → 1920x1080(축소라 선명). 그림을 오른쪽으로 shift만큼 밀어 왼쪽 여성 얼굴이 글자 옆에 오게 하고,
    왼쪽 빈자리는 같은 그림을 흐리고 어둡게 늘여 채운다. 글자: 흰 라벨 + 세로 4줄(불꽃·흰·불꽃·노랑) + 금테 붉은 배지 + 검은 띠."""
    src = Image.open(src_png).convert("RGB").resize((W, H), Image.LANCZOS)
    base = src.resize((W + shift, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(18))
    base = Image.eval(base, lambda v: int(v * 0.35))
    canvas = base.crop((0, 0, W, H))
    canvas.paste(src.crop((0, 0, W - shift, H)), (shift, 0))
    a = np.asarray(canvas).astype(np.float32)
    ramp = np.clip((np.arange(W) - shift) / 260, 0, 1)[None, :, None]
    a = a * (0.55 + 0.45 * ramp)                                   # 이음매를 어둠에 녹임
    img = to_pil(a).convert("RGBA")
    img.alpha_composite(label("スカッとする話", 70, (255, 255, 255, 255), (20, 20, 20)), (34, 26))
    fire = ((255, 236, 60), (255, 150, 20), (225, 30, 20))
    yellow = ((255, 250, 150), (255, 225, 30), (250, 180, 0))
    rows = [("クビにした", 126, fire, None), ("男が", 186, None, (255, 255, 255)),
            ("百億円の", 206, fire, None), ("鍵だった", 228, yellow, None)]
    y = 132
    for s, size, grad, fill in rows:
        lay = text_layer(s, GOTH, size, fill, (255, 255, 255) if grad else (0, 0, 0), 12 if grad else 12,
                         gradient=grad, outer=(0, 0, 0) if grad else None, outer_w=9 if grad else 0)
        put(img, lay, 6, y)
        y += lay.height - 44
    badge = label("上司の不正、暴かれる", 48, (175, 18, 18, 255), (255, 255, 255), pad=(30, 8))
    num = big("三億円の改ざん", 104, gradient=((255, 255, 190), (255, 225, 40), (255, 160, 0)), stroke_w=8, outer_w=6)
    box = Image.new("RGBA", (max(badge.width, num.width) + 44, badge.height + num.height + 4), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 28, fill=(255, 200, 40, 255))
    ImageDraw.Draw(box).rounded_rectangle([7, 7, box.width - 8, box.height - 8], 24, fill=(165, 14, 14, 245))
    box.alpha_composite(badge, ((box.width - badge.width) // 2, 12))
    box.alpha_composite(num, ((box.width - num.width) // 2, badge.height - 6))
    img.alpha_composite(box, (1080, 650))                      # 田中의 얼굴(위) 아래
    img.alpha_composite(band(["懲戒解雇、そして…"], 72, alpha=235, pad=(34, 16)), (1030, 880))
    return img.convert("RGB")


def anime_hd_final(out):
    d = os.path.join(ROOT, "assets", "portraits", "ashita-thumb-anime-hd")
    for tag, n in (("A", 1), ("B", 3)):
        p = os.path.join(out, f"ashita-thumb-HD-{tag}-JP.jpg")
        im = thumb_anime_hd(os.path.join(d, f"anime-hd-{n}.png"))
        im.save(p, quality=94)
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        print("저장:", p)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "hd":
        anime_hd_final(os.path.join(ROOT, "assets", "thumbnails", "ashita"))
    elif len(sys.argv) > 1 and sys.argv[1] == "quote":
        quote_final(os.path.join(ROOT, "assets", "thumbnails", "ashita"))
    elif len(sys.argv) > 1 and sys.argv[1] == "anime":
        anime_final(os.path.join(ROOT, "assets", "thumbnails", "ashita"))
    elif len(sys.argv) > 1 and sys.argv[1] == "avatar":
        avatar_final(os.path.join(ROOT, "assets", "thumbnails", "ashita"))
    elif len(sys.argv) > 1 and sys.argv[1] == "styled":
        styled_samples(os.path.join(ROOT, "assets", "thumbnails", "ashita"))
    else:
        main()
