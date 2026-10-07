#!/usr/bin/env python3
"""i2v 클립에 키프레임과 같은 간판을 프레임마다 합성(무과금, 로컬).

키프레임(합성 전 원본, assets/portraits/yanagi-kf-b/<id>-1.png)과 각 프레임을 ORB 특징점으로 맞춰 호모그래피를 구하고,
yanagi_composite.QUADS의 간판 네 모서리를 그 프레임 좌표로 옮겨 붙인다(i2v의 미세한 카메라 흔들림·크롭 차이를 따라감).
BLUR 영역도 같은 방식으로 옮겨 흐린다.
사용법: clip_sign_overlay.py <id> <in.mp4> <out.mp4>
"""
import os, subprocess, sys
import cv2, imageio_ffmpeg, numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import yanagi_composite as yc  # noqa: E402

sid, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
FF = imageio_ffmpeg.get_ffmpeg_exe()
kf = np.asarray(Image.open(os.path.join(ROOT, f"assets/portraits/yanagi-kf-b/{sid}-1.png")).convert("RGB"))
kg = cv2.cvtColor(kf, cv2.COLOR_RGB2GRAY)
orb = cv2.ORB_create(4000)
kk, kd = orb.detectAndCompute(kg, None)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
q0 = np.float32(yc.QUADS[sid]["sign"])
blurs = yc.BLUR.get(sid, [])
COVER = {"S10c": [((592, 292, 656, 336), (664, 292, 700, 336))]}  # 이전 키프레임에서 간판 띠 위에 잘못 붙은 문 옆 판 → 옆 띠 색으로 덮음
info = subprocess.run([FF, "-i", src], capture_output=True, text=True).stderr
W, H = next((int(a), int(b)) for t in info.replace(",", " ").split() if "x" in t
            for a, _, b in [t.partition("x")] if a.isdigit() and b.isdigit() and int(a) >= 320)
dec = subprocess.Popen([FF, "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24", "-i", "-",
                        "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
Hm_prev, n, bad = None, 0, 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
    fk, fd = orb.detectAndCompute(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), None)
    Hm = None
    if fd is not None and len(fk) > 50:
        m = sorted(bf.match(kd, fd), key=lambda x: x.distance)[:600]
        if len(m) > 30:
            Hm, inl = cv2.findHomography(np.float32([kk[x.queryIdx].pt for x in m]), np.float32([fk[x.trainIdx].pt for x in m]), cv2.RANSAC, 4.0)
            if Hm is None or inl.sum() < 25:
                Hm = None
    if Hm is None:
        bad += 1; Hm = Hm_prev if Hm_prev is not None else np.diag([W / kf.shape[1], H / kf.shape[0], 1.0])
    elif Hm_prev is not None:
        Hm = 0.6 * Hm_prev + 0.4 * Hm   # 프레임 사이 떨림 완화
    Hm_prev = Hm
    q = cv2.perspectiveTransform(q0[None], Hm)[0]
    f = yc.apply(f, yc.SIGN, q)
    for (x0, y0, x1, y1), (sx0, sy0, sx1, sy1) in COVER.get(sid, []):
        r = cv2.perspectiveTransform(np.float32([[(x0, y0), (x1, y1)]]), Hm)[0].astype(int)
        s_ = cv2.perspectiveTransform(np.float32([[(sx0, sy0), (sx1, sy1)]]), Hm)[0].astype(int)
        mk = np.zeros((H, W), np.uint8); mk[r[0][1]:r[1][1], r[0][0]:r[1][0]] = 255
        f = cv2.cvtColor(cv2.inpaint(cv2.cvtColor(f, cv2.COLOR_RGB2BGR), mk, 9, cv2.INPAINT_NS), cv2.COLOR_BGR2RGB)
    for (x0, y0, x1, y1) in blurs:
        r = cv2.perspectiveTransform(np.float32([[(x0, y0), (x1, y1)]]), Hm)[0]
        a0, b0 = np.clip(r.min(0).astype(int), 0, [W - 1, H - 1]); a1, b1 = np.clip(r.max(0).astype(int), 1, [W, H])
        f[b0:b1, a0:a1] = cv2.GaussianBlur(f[b0:b1, a0:a1], (0, 0), 7)
    enc.stdin.write(f.tobytes()); n += 1
enc.stdin.close(); enc.wait(); dec.wait()
print(f"{out}: {n}프레임, 정합 실패 {bad}")
