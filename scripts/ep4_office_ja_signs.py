#!/usr/bin/env python3
"""EP4 관리사무소 v2-1(사용자 선택): 유리 너머 달력·게시물 외계어 → 실제 일본어(12月 달력, お知らせ), 모니터 상표 글자 제거.
사용법: ep4_office_ja_signs.py assets/portraits/ep4-cast/loc-mgmt-office-v2-1.png assets/portraits/ep4-cast/cells/loc-mgmt-office-counter.png
"""
import numpy as np, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC, OUT = sys.argv[1], sys.argv[2]
G = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
M = "/home/user/my-project-goni/scripts/fonts/ZenOldMincho-Bold.ttf"
im = Image.open(SRC).convert("RGB")
a = np.asarray(im).astype(np.float32)
K = 10  # 고해상도로 그린 뒤 축소

def calendar(w, h):
    W, H = w * K, h * K
    c = Image.new("RGB", (W, H), (236, 236, 232)); d = ImageDraw.Draw(c)
    ph = int(H * 0.40)  # 상단 사진(겨울 하늘·눈산)
    for y in range(ph):
        t = y / ph; d.line([(0, y), (W, y)], fill=(int(120 + 70 * t), int(150 + 60 * t), int(190 + 40 * t)))
    d.polygon([(0, ph), (W * .35, ph * .45), (W * .6, ph * .75), (W * .8, ph * .5), (W, ph)], fill=(225, 230, 238))
    f1 = ImageFont.truetype(M, int(W * .2)); d.text((W * .06, ph + H * .02), "12月", font=f1, fill=(40, 40, 45))
    f2 = ImageFont.truetype(G, int(W * .085))
    gy, rows, cw = ph + H * .14, 6, W / 7
    rh = (H * .95 - gy) / rows
    day, start = 1, 1  # 1일 = 월요일
    for r in range(rows):
        for col in range(7):
            if r == 0 and col < start or day > 31: continue
            col_fill = (190, 40, 40) if col == 0 else (70, 90, 160) if col == 6 else (50, 50, 55)
            d.text((col * cw + cw * .15, gy + r * rh), str(day), font=f2, fill=col_fill); day += 1
            if day > 31: break
    return c

def notice(w, h):
    W, H = w * K, h * K
    c = Image.new("RGB", (W, H), (238, 238, 234)); d = ImageDraw.Draw(c)
    ft = ImageFont.truetype(G, int(W * .17)); d.text((W * .1, H * .06), "お知らせ", font=ft, fill=(30, 50, 120))
    d.line([(W * .08, H * .27), (W * .92, H * .27)], fill=(30, 50, 120), width=int(K * .8))
    fb = ImageFont.truetype(G, int(W * .085))
    for i, t in enumerate(["年末年始の", "ごみ収集日", "12月29日〜1月3日", "は収集しません。", "", "　管理事務所"]):
        d.text((W * .1, H * (.34 + i * .1)), t, font=fb, fill=(45, 45, 50))
    return c

def paste(box, art, keep_green=False):
    x0, y0, x1, y1 = box
    reg = a[y0:y1, x0:x1]
    art = art.resize((x1 - x0, y1 - y0), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.55))
    ar = np.asarray(art).astype(np.float32)
    # 원본 종이의 밝기·색감(유리 너머, 조명) 맞춤: 원본 밝은 부분 평균에 맞춰 스케일
    paper = np.percentile(reg.reshape(-1, 3), 85, axis=0)
    ar = ar / ar.reshape(-1, 3).max(0) * paper
    ar += np.random.default_rng(1).normal(0, 2.0, ar.shape)
    m = np.ones(reg.shape[:2], np.float32)
    if keep_green:  # 앞쪽 화분 잎은 원본 유지
        g = (reg[..., 1] > reg[..., 0] + 8) & (reg[..., 1] > reg[..., 2] + 8)
        m[g] = 0
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))) / 255.
    # 가장자리 1px 페더
    e = np.ones_like(m); e[0, :] = e[-1, :] = e[:, 0] = e[:, -1] = .5
    m = (m * e)[..., None]
    a[y0:y1, x0:x1] = reg * (1 - m) + ar * m

paste((714, 236, 749, 304), calendar(35, 68))
paste((679, 304, 712, 352), notice(33, 48), keep_green=True)
# 모니터 뒷면 상표 글자: 주변 검은 면으로 덮기
y0, y1, x0, x1 = 397, 409, 800, 832
fill = np.median(np.concatenate([a[y0 - 6:y0 - 2, x0:x1].reshape(-1, 3), a[y1 + 2:y1 + 6, x0:x1].reshape(-1, 3)]), axis=0)
a[y0:y1, x0:x1] = fill + np.random.default_rng(2).normal(0, 1.5, (y1 - y0, x1 - x0, 3))
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT)
print("저장", OUT)
