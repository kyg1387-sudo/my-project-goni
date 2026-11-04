#!/usr/bin/env python3
"""초점 밖 앞 인물(어깨 너머)에 생긴 안경 지우기(제21장 16·19, 무료·로컬). 원본은 같은 폴더 _v1/에 보관.
안경테 선(다리)과 렌즈 영역만 마스크하고, 줄마다 얼굴 윤곽선 왼쪽은 피부색·오른쪽은 배경색으로 채운 뒤 흐림 + 그레인.
사용법: kf_fg_glasses_fix.py <png> <arm x1 y1 x2 y2> <lens cx cy rx ry> <edge x_top y_top x_bot y_bot> [side=R]
  side=R: 얼굴이 렌즈 왼쪽(배경이 오른쪽), side=L: 반대."""
import os, shutil, sys
import cv2, numpy as np

p = sys.argv[1]; v = list(map(int, sys.argv[2:14])); side = sys.argv[14] if len(sys.argv) > 14 else "R"
d = os.path.join(os.path.dirname(p), "_v1"); os.makedirs(d, exist_ok=True)
orig = os.path.join(d, os.path.basename(p))
if not os.path.exists(orig):
    shutil.copy(p, orig)
a = cv2.imread(orig); m = np.zeros(a.shape[:2], np.uint8)
cv2.line(m, (v[0], v[1]), (v[2], v[3]), 255, 10)
cv2.ellipse(m, (v[4], v[5]), (v[6], v[7]), 0, 0, 360, 255, -1)
m = cv2.dilate(m, np.ones((5, 5), np.uint8))
r = a.astype(float).copy(); ys, _ = np.where(m > 0)
for y in range(ys.min(), ys.max() + 1):
    row = np.where(m[y] > 0)[0]
    if len(row) == 0:
        continue
    x0, x1 = row.min(), row.max()
    t = (y - v[9]) / max(1, v[11] - v[9]); ex = v[8] + (v[10] - v[8]) * t
    L = a[y, max(x0 - 6, 0):max(x0 - 1, 1)].mean(0); R = a[y, x1 + 2:x1 + 8].mean(0)
    for x in range(x0, x1 + 1):
        r[y, x] = (L if x < ex else R) if side == "R" else (R if x > ex else L)
bl = cv2.GaussianBlur(r.astype(np.uint8), (0, 0), 4); mm = cv2.GaussianBlur(m.astype(float) / 255, (0, 0), 3)[..., None]
out = bl * mm + a * (1 - mm) + np.random.normal(0, 2.5, a.shape) * mm
cv2.imwrite(p, np.clip(out, 0, 255).astype(np.uint8)); print("안경 제거:", p)
