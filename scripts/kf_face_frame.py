#!/usr/bin/env python3
"""대화 컷 얼굴 크기 맞춤 크롭(제10장 1 — 얼굴 화면 높이 1/4 이상, 무료·로컬).
가장 큰 정면/3/4 얼굴을 찾아 얼굴 높이가 화면의 target 비율이 되도록 16:9로 잘라 원래 크기로 키운다.
얼굴은 가로 1/3~2/3(화자 쪽) 위치, 눈높이는 위에서 약 35%. 앞쪽 어깨 너머 인물은 그대로 화면 가장자리에 남는다.
사용법: kf_face_frame.py <입력.png> <출력.png> [target=0.30] [hint_x=0.5] [fg=L|R|-] [face_x y w h(검출 실패 시 수동)]
fg = 어깨 너머 전경 인물 쪽 — 얼굴을 반대쪽 1/3 선에 두어 전경 어깨가 화면에 남게 한다(대화 느낌 유지)."""
import sys
import cv2
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
target = float(sys.argv[3]) if len(sys.argv) > 3 else 0.30
hint = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
im = Image.open(src).convert("RGB"); W, H = im.size
g = cv2.cvtColor(cv2.imread(src), cv2.COLOR_BGR2GRAY)
cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
fg = sys.argv[5] if len(sys.argv) > 5 else "-"
fs = list(cas.detectMultiScale(g, 1.08, 5, minSize=(40, 40)))
if len(sys.argv) > 9:
    fs = [tuple(int(v) for v in sys.argv[6:10])]
if not fs:
    sys.exit(f"얼굴 없음: {src}")
x, y, w, h = min(fs, key=lambda r: abs((r[0] + r[2] / 2) / W - hint) - r[2] / W)   # 힌트 위치에 가깝고 큰 얼굴
ch = min(H, int(h / target)); cw = int(ch * 16 / 9)
if cw > W:
    cw = W; ch = int(cw * 9 / 16)
cx = x + w / 2; cy = y + h * 0.45
pos = {"L": 0.64, "R": 0.36}.get(fg, 0.5)          # 얼굴이 놓일 가로 위치(전경 반대쪽 1/3 선)
x0 = int(min(max(cx - cw * pos, 0), W - cw)); y0 = int(min(max(cy - ch * 0.35, 0), H - ch))
im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS).save(out)
print(f"{src}: 얼굴 {w}x{h} → 크롭 {cw}x{ch} @({x0},{y0}), 얼굴 비율 {h / ch:.2f}")
