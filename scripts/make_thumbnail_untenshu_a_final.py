#!/usr/bin/env python3
"""『運転手のくせに』 썸네일 A안 최종(고니감독님 제작본 기반, 무과금·로컬).
고니감독님 썸네일의 왼쪽(글자·배경·번개)은 그대로 두고, 번개 오른쪽 인물 영역을 본편 인물로 다시 합성한다.
  부장 = 大塚(S17f: 홍조·땀·빨간 넥타이·회색 스트라이프), 회장 = 黒田(S17c: 백발 올백·흰 콧수염·남색 정장·보라 넥타이)
  말풍선 「違うんです!!」(세로) 다시 그림, 「部長の末路」 박스는 재생 시간 표시 위로 올림, 1280x720 JPG.
사용법: make_thumbnail_untenshu_a_final.py
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "assets", "portraits", "untenshu-keyframes")
TH = os.path.join(ROOT, "assets", "thumbnails", "untenshu")
GOTH = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")
W, H = 1984, 1116          # 고니감독님 원본(16:9 크롭) 좌표


def kf(n):
    return Image.open(os.path.join(K, f"{n}-1.png")).convert("RGB")


def place(src, scale, anchor_src, anchor_dst, size=(W, H)):
    """src를 scale배 해서 src의 anchor 점이 캔버스 anchor_dst에 오도록 배치한 캔버스 크기 이미지."""
    im = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
    ox = round(anchor_dst[0] - anchor_src[0] * scale); oy = round(anchor_dst[1] - anchor_src[1] * scale)
    can = Image.new("RGB", size); can.paste(im, (ox, oy))
    m = Image.new("L", size, 0); m.paste(255, (ox, oy, ox + im.width, oy + im.height))
    return can, m


def speed_lines(center, seed, n=140, inner=330, alpha=150):
    rnd = random.Random(seed)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = center
    for _ in range(n):
        a = rnd.uniform(0, 2 * math.pi); w = rnd.uniform(0.003, 0.010)
        r0 = inner + rnd.uniform(0, 220); r1 = 2600
        d.polygon([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a - w), cy + r1 * math.sin(a - w)),
                   (cx + r1 * math.cos(a + w), cy + r1 * math.sin(a + w))], fill=(0, 0, 0, alpha))
    return lay


def main():
    user = Image.open(os.path.join(TH, "src-A-user.png")).convert("RGB")
    a = np.array(user).astype(int)
    yel = (a[..., 0] > 220) & (a[..., 1] > 200) & (a[..., 2] < 90)
    # 번개 오른쪽 경계(행마다 노란 픽셀 최대 x + 외곽선), 위아래로 매끄럽게
    bx = np.full(H, 1000.0)
    for y in range(H):
        xs = np.where(yel[y, 850:1150])[0]
        if len(xs):
            bx[y] = 850 + xs.max() + 8
    for y in range(1, H):
        if not yel[y, 850:1150].any():
            bx[y] = bx[y - 1]
    # 오른쪽 인물 패널: 大塚(S17f) — 얼굴 중심 (766,230)을 (1330,600)에, 黒田(S17c) — 얼굴 중심 (915,330)을 (1800,330)에
    otsuka, mo = place(kf("S18f"), 1.5, (861, 190), (1290, 560))
    kuroda, mk = place(kf("S17c"), 1.55, (840, 350), (1790, 380))
    panel = otsuka.copy()
    km = Image.new("L", (W, H), 0)
    ImageDraw.Draw(km).polygon([(1600, 0), (W, 0), (W, H), (1640, H), (1600, 700)], fill=255)
    km = km.filter(ImageFilter.GaussianBlur(45))
    panel = Image.composite(kuroda, panel, km)
    # 홍조(R51 표정과 같은 방향): 大塚 얼굴에 붉은 기
    fl = Image.new("L", (W, H), 0); ImageDraw.Draw(fl).ellipse((1150, 400, 1430, 720), fill=95)
    panel = Image.composite(Image.blend(panel, Image.new("RGB", (W, H), (235, 40, 30)), 0.5), panel, fl.filter(ImageFilter.GaussianBlur(45)))
    panel = ImageEnhance.Contrast(panel).enhance(1.12)
    panel = ImageEnhance.Color(panel).enhance(1.15)
    # 만화 집중선(검정)·불꽃 빛(아래 주황)
    panel = panel.convert("RGBA")
    sl = speed_lines((1330, 560), seed=9)
    hole = Image.new("L", (W, H), 0); ImageDraw.Draw(hole).ellipse((1060, 300, 1620, 1000), fill=255); ImageDraw.Draw(hole).rectangle((1600, 0, W, H), fill=255)
    sl.putalpha(Image.composite(Image.new("L", (W, H), 0), sl.getchannel("A"), hole.filter(ImageFilter.GaussianBlur(60))))
    panel.alpha_composite(sl)
    panel = panel.convert("RGB")
    # 아래쪽은 고니감독님 원본의 불꽃을 그대로 이어 붙임(y>880, 박스 자리 제외)
    flame_src = user.copy()
    fm = Image.new("L", (W, H), 0); fd = ImageDraw.Draw(fm)
    for y in range(860, H):
        fd.line([(0, y), (W, y)], fill=int(255 * min(1, (y - 860) / 120)))
    # 원본 박스(1290~1984, 930~1100) 자리는 불꽃 대신 패널 유지
    fd.rectangle((1270, 920, W, H), fill=0)
    fm = fm.filter(ImageFilter.GaussianBlur(6))
    panel = Image.composite(flame_src, panel, fm)
    # 박스 자리 아래쪽은 원본 왼쪽 불꽃을 비춰 넣는 대신 붉은 그라데이션으로 마감
    glow = Image.new("RGB", (W, H), (230, 70, 10))
    gm = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(gm)
    for y in range(900, H):
        gd.line([(1270, y), (W, y)], fill=int(200 * (y - 900) / (H - 900)))
    panel = Image.composite(glow, panel, gm.filter(ImageFilter.GaussianBlur(20)))
    # 왼쪽(원본) + 오른쪽(패널)
    mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    for y in range(H):
        md.line([(int(bx[y]), y), (W, y)], fill=255)
    out = Image.composite(panel, user, mask.filter(ImageFilter.GaussianBlur(1.5)))
    d = ImageDraw.Draw(out)
    # 세로 말풍선 「違うんです!!」
    cx, top, bot, half = 1150, 30, 530, 88
    rnd = random.Random(2)
    pts = [(cx - half, top + 30)]
    for y in range(top + 30, bot - 30, 34):
        pts.append((cx - half - rnd.choice([0, 14]), y))
    pts += [(cx - 20, bot - 30), (cx - 60, bot + 60), (cx + 25, bot - 30), (cx + half, bot - 30)]
    for y in range(bot - 30, top + 30, -34):
        pts.append((cx + half + rnd.choice([0, 14]), y))
    pts += [(cx + half, top + 30), (cx + 40, top), (cx - 40, top)]
    d.polygon([(x + 7, y + 7) for x, y in pts], fill=(0, 0, 0))
    d.polygon(pts, fill=(255, 255, 255), outline=(0, 0, 0), width=6)
    f = ImageFont.truetype(GOTH, 66)
    y = top + 44
    for ch in "違うんです":
        d.text((cx, y), ch, font=f, fill=(0, 0, 0), anchor="mt"); y += 72
    d.text((cx, y), "!!", font=ImageFont.truetype(GOTH, 60), fill=(0, 0, 0), anchor="mt")
    # 「部長の末路」 박스: 재생 시간 표시(오른쪽 아래) 위로
    fb = ImageFont.truetype(GOTH, 96)
    bb = d.textbbox((0, 0), "部長の末路", font=fb)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x1, y1 = W - 40, H - 120
    x0, y0 = x1 - tw - 70, y1 - th - 56
    d.polygon([(x0 - 40, y1), (x0, y0), (x1, y0), (x1, y1)], fill=(0, 0, 0))
    d.text((x0 + 35 - bb[0], y0 + 28 - bb[1]), "部長の末路", font=fb, fill=(255, 255, 255))
    final = out.resize((1280, 720), Image.LANCZOS)
    p = os.path.join(TH, "untenshu-thumb-A-manga-JP.jpg")
    final.save(p, quality=92)
    print("저장:", p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main()
