#!/usr/bin/env python3
"""생성 영상 속 실존 브랜드 로고(빨강 포함 작은 표식) 제거 — 프레임마다 빨간 점을 추적해 주변 배경으로 메운다(무과금, 로컬).
i2v가 키프레임에서 지운 로고를 다시 그려 넣는 경우용(규격 제2장 1).
사용법: clip_logo_remove.py <in.mp4> <out.mp4> <x> <y> [반경=40] [상자 w=34] [상자 h=44]   (x,y = 첫 프레임 로고 중심, 영상 픽셀)
"""
import subprocess, sys
import cv2, imageio_ffmpeg, numpy as np

src, out, x, y = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
R = int(sys.argv[5]) if len(sys.argv) > 5 else 40
BW = int(sys.argv[6]) if len(sys.argv) > 6 else 34
BH = int(sys.argv[7]) if len(sys.argv) > 7 else 44
ff = imageio_ffmpeg.get_ffmpeg_exe()
info = subprocess.run([ff, "-i", src], capture_output=True, text=True).stderr
W, H = next((int(a), int(b)) for t in info.replace(",", " ").split() if "x" in t
            for a, _, b in [t.partition("x")] if a.isdigit() and b.isdigit() and int(a) >= 320)
dec = subprocess.Popen([ff, "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen([ff, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24", "-i", "-",
                        "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
n = lost = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
    x0, y0, x1, y1 = int(max(0, x - R)), int(max(0, y - R)), int(min(W, x + R)), int(min(H, y + R))
    sub = f[y0:y1, x0:x1].astype(int)
    red = (sub[..., 0] > 150) & (sub[..., 1] < 110) & (sub[..., 2] < 110) & (sub[..., 0] - sub[..., 1] > 70)
    if red.sum() >= 4:
        ys, xs = np.nonzero(red)
        x, y = x0 + xs.mean(), y0 + ys.mean()
    else:
        lost += 1
    m = np.zeros((H, W), np.uint8)
    cv2.rectangle(m, (int(x - BW / 2), int(y - BH / 2)), (int(x + BW / 2), int(y + BH / 2)), 255, -1)
    f = cv2.cvtColor(cv2.inpaint(cv2.cvtColor(f, cv2.COLOR_RGB2BGR), m, 7, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB)
    enc.stdin.write(f.tobytes()); n += 1
enc.stdin.close(); enc.wait(); dec.wait()
print(f"{out}: {n}프레임, 빨간 표식 못 찾은 프레임 {lost}")
