#!/usr/bin/env python3
"""S17g 개발부 비디오월(장면 121) — 붉은 타일만 있는 i2v 위에 장면 의미(제어 정지 상황판)를 합성(고니감독님 지적 2026-10-16).
글자 층은 고정(카메라 고정), 타일이 꺼져 검게 되는 곳은 프레임마다 '붉음' 마스크로 글자도 함께 사라지게 한다.
사용법: tsuki_wall_overlay.py <scene121.mp4 원본> <출력.mp4>"""
import os, subprocess, sys, tempfile
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GOTH = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")
# 비디오월 네 모서리(원본 클립 해상도 기준 비율) — 상단 중앙 큰 벽
WALL = [(0.32, 0.115), (0.665, 0.115), (0.665, 0.345), (0.32, 0.345)]   # 1248x704 클립 실측
DISTRICTS = ["商業地区", "オフィス街", "物流拠点", "住宅地区", "工業団地", "港湾地区",
             "鉄道沿線", "大学キャンパス", "データセンター", "官庁街", "倉庫街", "空港周辺"]


def red_mask(f):
    b, g, r = f[:, :, 0].astype(np.int16), f[:, :, 1].astype(np.int16), f[:, :, 2].astype(np.int16)
    return ((r > 120) & (r - g > 60) & (r - b > 60)).astype(np.uint8) * 255


def green_mask(f):
    b, g, r = f[:, :, 0].astype(np.int16), f[:, :, 1].astype(np.int16), f[:, :, 2].astype(np.int16)
    return ((g > 110) & (g - r > 40) & (g - b > 30)).astype(np.uint8) * 255


# 장면번호: (쿼드 비율 TL,TR,BR,BL, 대시보드 모드, 큰 문구, 작은 문구, 마스크, seed)
JOBS = {
    24: ([(0.345, 0.17), (0.72, 0.19), (0.72, 0.50), (0.345, 0.52)], "red", "負荷分散　失敗", "月見野スマートシティ 電力グリッド", red_mask, 5),
    28: ([(0.375, 0.027), (0.792, 0.027), (0.792, 0.258), (0.375, 0.258)], "green", "負荷分散　正常", "KAGUYA 稼働中　全区画 安定", green_mask, 6),
    114: ([(0.26, 0.18), (0.86, 0.18), (0.86, 0.578), (0.26, 0.578)], "red", "制御停止", "かぐや ライセンス認証 失敗　全区画 応答なし", red_mask, 14),
    121: ([(0.32, 0.115), (0.665, 0.115), (0.665, 0.345), (0.32, 0.345)], "expired", "電力グリッド　停止", "制御ライセンス 期限切れ　商業地区・オフィス街・物流拠点", red_mask, 21),
}


def apply(src, out, quad_r, mode, big, sub, maskf, seed):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from tsuki_dashboard import dashboard
    cap = cv2.VideoCapture(src)
    W, H, fps = int(cap.get(3)), int(cap.get(4)), cap.get(5) or 24
    quad = np.float32([(x * W, y * H) for x, y in quad_r])
    lw, lh = 1400, 700
    L = np.array(dashboard(lw, lh, mode, big=big, sub=sub, seed=seed))
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [lw, 0], [lw, lh], [0, lh]]), quad)
    warped = cv2.warpPerspective(L, M, (W, H), flags=cv2.INTER_AREA)
    wa = cv2.GaussianBlur(warped[:, :, 3], (0, 0), 1.0).astype(np.float32) / 255.0
    wrgb = warped[:, :, :3][:, :, ::-1].astype(np.float32)
    tmp = tempfile.mkdtemp(); raw = os.path.join(tmp, "v.mp4")
    wr = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H)); n = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        m = cv2.erode(maskf(f), np.ones((7, 7), np.uint8))
        m = cv2.GaussianBlur(m, (0, 0), 3).astype(np.float32) / 255.0 * wa
        a3 = (m * 0.94)[:, :, None]
        # 화면의 원래 밝기 변화(점멸·소등)를 살리기 위해 원본 밝기로 변조
        lum = (f.astype(np.float32).max(2) / 255.0)[:, :, None]
        f = (f.astype(np.float32) * (1 - a3) + wrgb * (0.35 + 0.65 * lum) * a3).astype(np.uint8)
        wr.write(f); n += 1
    wr.release()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", out], check=True)
    print(f"{out}: {n}프레임 {W}x{H}")


def main():
    if len(sys.argv) > 2:                      # 단일: <scene.mp4> <out.mp4> [장면번호]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 121
        apply(sys.argv[1], sys.argv[2], *JOBS[n]); return
    for n, job in JOBS.items():
        src = os.path.join(ROOT, f"assets/preview/tsuki/scene{n}.mp4")
        if os.path.exists(src):
            apply(src, os.path.join(ROOT, f"assets/video-overrides/tsuki/scene{n:02d}.mp4"), *job)


if __name__ == "__main__":
    main()
