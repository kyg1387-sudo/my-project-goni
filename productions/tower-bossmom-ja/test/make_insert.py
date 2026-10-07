#!/usr/bin/env python3
"""시험 장면 인서트(무료): 키프레임 배경의 빈 프로젝터 스크린을 크롭·업스케일하고,
실제 일본어 폰트로 만든 가상 통장 내역 그래픽을 스크린 면에 합성한다(마이크 등 앞 물체는 원본 유지)."""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
src, out = sys.argv[1], sys.argv[2]
kf = Image.open(src).convert("RGB")
X0, Y0, X1, Y1 = 752, 60, 1312, 375          # 크롭 영역(16:9)
SX0, SY0, SX1, SY1 = 853, 110, 1210, 357     # 스크린 흰 면(키프레임 좌표)
W, H = 1920, 1080
s = W / (X1 - X0)
crop = kf.crop((X0, Y0, X1, Y1)).resize((W, H), Image.LANCZOS)
orig = np.asarray(crop).astype(int)
# 배경은 얕은 심도처럼 살짝 흐리게(스크린 그래픽만 또렷)
bg = crop.filter(ImageFilter.GaussianBlur(3))
sx0, sy0 = int((SX0 - X0) * s), int((SY0 - Y0) * s)
sx1, sy1 = int((SX1 - X0) * s), int((SY1 - Y0) * s)
gw, gh = sx1 - sx0, sy1 - sy0
g = Image.new("RGB", (gw, gh), (250, 250, 248))
d = ImageDraw.Draw(g)
F = "scripts/fonts/ZenMaruGothic-Black.ttf"
f1, f2, f3 = ImageFont.truetype(F, int(gh * .065)), ImageFont.truetype(F, int(gh * .052)), ImageFont.truetype(F, int(gh * .045))
pad = int(gw * .04)
d.rectangle((0, 0, gw, int(gh * .14)), fill=(28, 52, 96))
d.text((pad, gh * .035), "管理組合 普通預金・取引明細（写し）", font=f1, fill="white")
heads = ["日付", "出金額（振込）", "振込先"]
rows = [("2025/11/10", "2,000,000円"), ("2026/01/20", "2,500,000円"), ("2026/04/15", "3,000,000円")]
cells = [[*r, "西園寺ビルメンテナンス"] for r in rows]
gap = int(gw * .035)
colw = [max(d.textlength(c[k], font=f2) for c in cells + [heads]) for k in range(3)]
xs = [pad]
for k in range(2):
    xs.append(xs[-1] + colw[k] + gap)
for k, h in enumerate(heads):
    d.text((xs[k], gh * .19), h, font=f3, fill=(100, 100, 100))
for i, c in enumerate(cells):
    y = gh * (.31 + i * .19)
    d.line((pad * .7, y - gh * .035, gw - pad * .7, y - gh * .035), fill=(215, 215, 215), width=3)
    for k, t in enumerate(c):
        d.text((xs[k], y), t, font=f2, fill=(205, 25, 25) if k == 1 else (30, 30, 30))
    d.ellipse((xs[2] - gw * .015, y - gh * .03, xs[2] + colw[2] + gw * .015, y + gh * .1), outline=(205, 25, 25), width=5)
assert xs[2] + colw[2] < gw - pad * .5, "글자가 스크린 밖으로 나감"
# 프로젝터 투사 느낌: 약간 부드럽게 + 밝기
g = g.filter(ImageFilter.GaussianBlur(0.8))
bg.paste(g, (sx0, sy0))
# 스크린 앞 물체(마이크 등 어두운 픽셀)는 원본 유지
res = np.asarray(bg).astype(int)
lum = orig.mean(axis=2)
m = np.zeros(lum.shape, bool)
mx0, my0, mx1 = int((960 - X0) * s), int((300 - Y0) * s), int((1020 - X0) * s)  # 마이크 영역만
m[my0:sy1, mx0:mx1] = lum[my0:sy1, mx0:mx1] < 140
res[m] = orig[m]
Image.fromarray(res.astype(np.uint8)).save(out)
print("저장:", out)
