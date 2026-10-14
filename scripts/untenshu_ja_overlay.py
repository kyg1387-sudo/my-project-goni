#!/usr/bin/env python3
"""『運転手のくせに』 일본어 글자 합성(제11장 3 — 조립 전에) — 무과금, 로컬.
assemble_untenshu_keyframes.py가 번호판·행등 다음에 호출한다(재조립 때마다 다시).
  S09b 요금 미터 「3,860円」(붉은 7세그먼트 느낌, 빛 번짐)
  S18a 회의실 태블릿 = 드라이브 레코더 화면: 어젯밤 뒷좌석(S06e 키프레임, 대시보드 카메라 시점) + 「● REC」·시각, 원근 맞춤
  S22c 비워진 책상의 명패 「営業部長　大塚 浩二」(흐림 처리한 자리에)
좌표는 최종 키프레임(1344x768) 기준.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KF = os.path.join(ROOT, "assets", "portraits", "untenshu-keyframes")
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
MINCHO = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")


def meter():
    p = os.path.join(KF, "S09b-1.png")
    im = Image.open(p).convert("RGB")
    x0, y0, x1, y1 = 556, 176, 904, 334
    w, h = x1 - x0, y1 - y0
    panel = Image.new("RGB", (w, h), (14, 18, 16))
    d = ImageDraw.Draw(panel)
    small = ImageFont.truetype(GOTHIC, 26)
    d.text((18, 12), "料金", font=small, fill=(150, 160, 150))
    d.text((w - 110, 12), "賃走", font=small, fill=(230, 60, 50))
    big = ImageFont.truetype(GOTHIC, 92)
    txt = "3,860"
    tw = d.textlength(txt, font=big)
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    ImageDraw.Draw(glow).text((w - tw - 70, 46), txt, font=big, fill=(255, 70, 40))
    panel = Image.composite(Image.new("RGB", (w, h), (255, 70, 40)), panel, glow.convert("L").filter(ImageFilter.GaussianBlur(6)).point(lambda v: v * 0.45))
    d = ImageDraw.Draw(panel)
    d.text((w - tw - 70, 46), txt, font=big, fill=(255, 92, 60))
    d.text((w - 62, 82), "円", font=ImageFont.truetype(GOTHIC, 50), fill=(255, 92, 60))
    panel = panel.filter(ImageFilter.GaussianBlur(0.8))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=10, fill=255)
    im.paste(panel, (x0, y0), mask.filter(ImageFilter.GaussianBlur(2)))
    im.save(p)


def coeffs(src, dst):
    """dst 사각형 → src 사각형 원근 변환 계수(PIL PERSPECTIVE)."""
    import numpy as np
    a = []
    for (x, y), (u, v) in zip(dst, src):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    b = [c for pt in src for c in pt]
    return np.linalg.solve(np.array(a, float), np.array(b, float)).tolist()


def dashcam():
    p = os.path.join(KF, "S18a-1.png")
    im = Image.open(p).convert("RGB")
    feed = Image.open(os.path.join(KF, "S06e-1.png")).convert("RGB").resize((960, 540))
    feed = ImageOps.grayscale(feed).convert("RGB")
    feed = Image.blend(feed, Image.new("RGB", feed.size, (40, 60, 70)), 0.25)       # 블랙박스 야간 화질
    feed = ImageEnhance.Contrast(feed).enhance(1.15).filter(ImageFilter.GaussianBlur(0.6))
    d = ImageDraw.Draw(feed)
    f = ImageFont.truetype(GOTHIC, 34)
    d.ellipse((24, 24, 50, 50), fill=(230, 30, 30)); d.text((60, 18), "REC", font=f, fill=(240, 240, 240))
    d.text((960 - 400, 18), "2026/10/23  23:41:08", font=f, fill=(240, 240, 240))
    d.text((24, 540 - 54), "車内カメラ", font=ImageFont.truetype(GOTHIC, 28), fill=(220, 220, 220))
    quad = [(338, 384), (1012, 432), (994, 566), (270, 470)]                      # 화면 네 모서리(왼위·오위·오아래·왼아래)
    c = coeffs([(0, 0), (960, 0), (960, 540), (0, 540)], quad)
    warped = feed.transform(im.size, Image.PERSPECTIVE, c, Image.BICUBIC)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon(quad, fill=235)
    im = Image.composite(warped, im, mask.filter(ImageFilter.GaussianBlur(1.2)))
    im.save(p)


def nameplate():
    """원래 명패(은색 면·검은 테, 비스듬한 쐐기형)의 면에 원근을 맞춰 글자만 새로 얹는다."""
    p = os.path.join(KF, "S22c-1.png")
    im = Image.open(p).convert("RGB")
    q = [(381, 308), (496, 326), (494, 356), (373, 335)]          # 명패 면 네 모서리(왼위·오위·오아래·왼아래)
    w, h = 640, 170
    plate = Image.new("RGB", (w, h), (208, 210, 206))
    d = ImageDraw.Draw(plate)
    d.text((26, 24), "営業部長", font=ImageFont.truetype(MINCHO, 44), fill=(40, 40, 44))
    f = ImageFont.truetype(MINCHO, 92)
    t = "大塚 浩二"
    d.text((w - d.textlength(t, font=f) - 30, 50), t, font=f, fill=(30, 30, 34))
    plate = ImageEnhance.Brightness(plate).enhance(0.86)
    c = coeffs([(0, 0), (w, 0), (w, h), (0, h)], q)
    warped = plate.transform(im.size, Image.PERSPECTIVE, c, Image.BICUBIC).filter(ImageFilter.GaussianBlur(0.9))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon(q, fill=255)
    im = Image.composite(warped, im, mask.filter(ImageFilter.GaussianBlur(0.8)))
    im.save(p)


if __name__ == "__main__":
    meter(); nameplate()   # S18a 블랙박스 화면은 편집 생성(untenshu-kf-j) 후 dashcam_text()
    print("일본어 합성: S09b 미터 · S18a 블랙박스 · S22c 명패")
