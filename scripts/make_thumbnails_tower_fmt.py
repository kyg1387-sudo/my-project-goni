#!/usr/bin/env python3
"""『タワマンのボスママ』 썸네일 A/B/C — 고니감독님 참고 이미지 3종 형식(2026-10-17, 채널 倉庫番 썸네일), 1920x1080, 로컬.
  A 실사 드라마형(「定年まで三か月の…」): 어두운 실사, 인물 왼쪽 크게 + 오른쪽 위 검은 라벨 + 빨강/노랑 2줄 + 반투명 검은 띠 노란 2줄
  B 인용구 클로즈업형(「土下座しろ」): 어두운 실사, 얼굴 오른쪽 크게 + 왼쪽 흰 3줄 + 아래 초대형 명조 인용구(불꽃 그라데이션·붉은 글로)
  C 웹툰형(「地獄を見せてやる」): 일러스트, 흰 라벨 + 왼쪽 세로 4줄 + 금테 붉은 배지 + 검은 띠
A·B는 승인 키프레임(실사, 자막 없음), C는 assets/portraits/thumb-tower-fmtC/fmtC-N.png(2560x1440 생성). 오른쪽 아래(재생 시간)는 비운다.
사용법: python3 scripts/make_thumbnails_tower_fmt.py [C그림번호]   (확정 2026-10-17: 1)
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from make_thumbnails_ashita import GOTH, MIN, W, H, band, big, glow, label, put  # noqa: E402
from make_thumbnails_yanagi_v2 import cover, text_layer, to_pil, vignette  # noqa: E402

KF = os.path.join(ROOT, "assets", "portraits", "tower-keyframes")
OUT = os.path.join(ROOT, "productions", "tower-bossmom-ja", "thumbnails-fmt")
FIRE = ((255, 236, 60), (255, 150, 20), (225, 30, 20))
YELLOW = ((255, 250, 150), (255, 225, 30), (250, 180, 0))
RED = ((255, 90, 80), (225, 20, 20), (150, 0, 0))


def kf(name):
    return cv2.cvtColor(cv2.imread(os.path.join(KF, f"{name}-1.png")), cv2.COLOR_BGR2RGB)


def crowd_bg(name, plate="S16c", blur=7):
    """키프레임 인물만 남기고 배경을 같은 회의장 만석 판(흐림)으로 — 본편 tower_bg_swap과 같은 처리(빈 의자 배경 방지)."""
    from rembg import new_session, remove
    a = kf(name)
    m = np.asarray(remove(Image.fromarray(a), session=new_session("u2net_human_seg"), only_mask=True)).astype(np.float32) / 255
    m = cv2.GaussianBlur(cv2.erode(m, np.ones((7, 7), np.uint8)), (0, 0), 2)[..., None]
    p = kf(plate)[260:768]
    p = cv2.GaussianBlur(cv2.resize(p, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_CUBIC).astype(np.float32), (0, 0), blur) * 0.9
    return (a * m + p * (1 - m)).astype(np.uint8)


def grade(a, left_dark=False, right_dark=False, lift=108):
    a = cv2.addWeighted(a, 1.5, cv2.GaussianBlur(a, (0, 0), 2.5), -0.5, 0).astype(np.float32)
    g = a.mean(axis=2, keepdims=True); a = a * 0.7 + g * 0.3
    a = a * np.array([0.92, 0.97, 1.05]); a = (a - 128) * 1.12 + lift
    if left_dark:
        a = a * (0.32 + 0.68 * np.clip((np.arange(W) - 380) / 620, 0, 1)[None, :, None])
    if right_dark:
        a = a * (0.4 + 0.6 * np.clip((1250 - np.arange(W)) / 520, 0, 1)[None, :, None])
    return to_pil(vignette(np.clip(a, 0, 255), 0.55)).convert("RGBA")


def thumb_a():
    """실사 드라마형: 오다기리 왼쪽 크게(본편과 같은 만석 배경) + 오른쪽 위 글자."""
    a = cover(crowd_bg("S16b"), W, H, 0.45, 0.40, zoom=1.25)   # 얼굴 x≈620(왼쪽 3분의 1)
    img = grade(a, right_dark=True, lift=124)
    img.alpha_composite(label("スカッとする話", 62, (12, 12, 12, 255), (255, 255, 255), border=(255, 255, 255, 255)), (1150, 36))
    l1 = big("42階の女王の…", 120, gradient=RED, stroke_w=10, outer_w=6)
    img.alpha_composite(l1, (1880 - l1.width, 150))
    l2a = big("本当の", 128, gradient=RED, stroke_w=10, outer_w=6)
    l2b = big("持ち主", 140, gradient=YELLOW, stroke_w=10, outer_w=6)
    x0 = 1890 - l2a.width - l2b.width + 30
    img.alpha_composite(glow(l2b, (255, 200, 0), 18, 1.2), (x0 + l2a.width - 30, 302))
    img.alpha_composite(l2a, (x0, 310))
    img.alpha_composite(band(["ボスママの正体は、", "ただの賃借人だった"], 70, alpha=200), (1000, 720))
    return img.convert("RGB")


def thumb_b():
    """인용구 클로즈업형: 우는 리코 얼굴 오른쪽 크게 + 왼쪽 흰 3줄 + 아래 인용구."""
    img = grade(cover(kf("S03e"), W, H, 0.37, 0.50, zoom=1.35), left_dark=True, lift=118)   # 얼굴 x≈1300·턱이 인용구 위
    cone = Image.new("L", (W, H), 0)
    ImageDraw.Draw(cone).polygon([(820, 0), (1100, 0), (1350, H), (560, H)], fill=34)
    img = Image.alpha_composite(img, Image.merge("RGBA", [Image.new("L", (W, H), 255)] * 3 + [cone.filter(ImageFilter.GaussianBlur(80))]))
    for i, s in enumerate(["5歳の娘を", "締め出した", "ボスママは言った…"]):
        lay = text_layer(s, GOTH, 104, (255, 255, 255), (0, 0, 0), 12)
        sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.putalpha(lay.split()[3].filter(ImageFilter.GaussianBlur(10)))
        put(img, sh, 54, 180 + i * 140); put(img, lay, 46, 170 + i * 140)
    q = text_layer("「上の子専用よ」", MIN, 176, None, (255, 255, 255), 12, gradient=((255, 238, 90), (255, 140, 20), (215, 20, 10)),
                   outer=(10, 0, 0), outer_w=8)
    q = glow(q, (220, 20, 0), 40, 2.0)
    put(img, q, (W - q.width) // 2 - 120, H - q.height + 40)
    return img.convert("RGB")


def thumb_c(n):
    """웹툰형: 왼쪽 유미 위로 세로 4줄, 가운데 무릎 꿇은 레이카 위 배지, 아래 검은 띠."""
    src = Image.open(os.path.join(ROOT, "assets", "portraits", "thumb-tower-fmtC", f"fmtC-{n}.png")).convert("RGB").resize((W, H), Image.LANCZOS)
    # 유미 얼굴이 글자 옆에 오도록 그림을 0.85배로 줄여 오른쪽 아래에 두고, 왼쪽·위 빈자리는 같은 그림을 흐리고 어둡게 채운다(ashita hd 방식)
    k = 0.85; sw, sh = int(W * k), int(H * k); ox, oy = W - sw, H - sh
    canvas = Image.eval(src.filter(ImageFilter.GaussianBlur(22)), lambda v: int(v * 0.35))
    small = src.resize((sw, sh), Image.LANCZOS)
    m = Image.new("L", (sw, sh), 255); md = ImageDraw.Draw(m)
    for i in range(60):
        md.line([(i, 0), (i, sh)], fill=int(255 * i / 60)); md.line([(0, i), (sw, i)], fill=int(255 * i / 60))
    canvas.paste(small, (ox, oy), m.filter(ImageFilter.GaussianBlur(6)))
    img = canvas.convert("RGBA")
    img.alpha_composite(label("スカッとする話", 70, (255, 255, 255, 255), (20, 20, 20)), (34, 26))
    rows = [("最上階の", 112, FIRE, None), ("女王を", 140, None, (255, 255, 255)), ("堕とした", 168, FIRE, None), ("1冊の通帳", 186, YELLOW, None)]   # 위 2줄은 유미 얼굴(x≈490~) 왼쪽, 아래 2줄은 가슴 아래
    y = 132
    for s, size, grad, fill in rows:
        lay = text_layer(s, GOTH, size, fill, (255, 255, 255) if grad else (0, 0, 0), 12,
                         gradient=grad, outer=(0, 0, 0) if grad else None, outer_w=9 if grad else 0)
        put(img, lay, 6, y); y += lay.height - 44
    badge = label("ボスママの横領、暴かれる", 46, (175, 18, 18, 255), (255, 255, 255), pad=(30, 8))
    num = big("27件の証拠", 104, gradient=((255, 255, 190), (255, 225, 40), (255, 160, 0)), stroke_w=8, outer_w=6)
    box = Image.new("RGBA", (max(badge.width, num.width) + 44, badge.height + num.height + 4), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 28, fill=(255, 200, 40, 255))
    ImageDraw.Draw(box).rounded_rectangle([7, 7, box.width - 8, box.height - 8], 24, fill=(165, 14, 14, 245))
    box.alpha_composite(badge, ((box.width - badge.width) // 2, 12)); box.alpha_composite(num, ((box.width - num.width) // 2, badge.height - 6))
    img.alpha_composite(box, C_BADGE)
    img.alpha_composite(band(["家賃滞納、そして…"], 72, alpha=235, pad=(34, 16)), C_BAND)
    return img.convert("RGB")


C_BADGE, C_BAND = (790, 250), (800, 905)   # 무릎 꿇은 레이카(x≈1210~1430)를 가리지 않게: 배지는 위 창 쪽, 띠는 그녀 왼쪽 바닥(검수 2026-10-17)


def save(im, tag):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"tower-thumb-{tag}-JP.jpg"); im.save(p, quality=94)
    im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
    print("저장:", p)


def main():
    save(thumb_a(), "A")
    save(thumb_b(), "B")
    n = sys.argv[1] if len(sys.argv) > 1 else None
    if n:
        save(thumb_c(n), "C")


if __name__ == "__main__":
    main()
