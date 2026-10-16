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


def fit(d, text, size, maxw):
    """글자가 maxw 안에 들어오게 크기를 줄인 폰트."""
    while size > 10:
        f = ImageFont.truetype(GOTH, size)
        if d.textlength(text, font=f) <= maxw:
            return f
        size -= 4
    return ImageFont.truetype(GOTH, size)


def layer(w, h):
    """벽이 화면의 1/3 폭이라 휴대폰에서 읽히게 큰 글자 3줄만(폭에 맞춰 자동 축소)."""
    L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    rows = [("制御ライセンス　期限切れ", 0.15, 0.20, (255, 235, 230, 255)),
            ("電力グリッド　停止", 0.26, 0.50, (255, 255, 255, 255)),
            ("商業地区 停止　オフィス街 停止　物流拠点 停止", 0.11, 0.80, (255, 225, 220, 255))]
    for text, fs, y, col in rows:
        d.text((w / 2, h * y), text, font=fit(d, text, int(h * fs), w * 0.92), fill=col, anchor="mm")
    a = L.split()[3].filter(ImageFilter.GaussianBlur(12)).point(lambda v: min(255, int(v * 1.2)))
    G = Image.new("RGBA", (w, h), (255, 240, 235, 0)); G.putalpha(a)
    G.alpha_composite(L)
    return G


def main():
    src, out = sys.argv[1], sys.argv[2]
    cap = cv2.VideoCapture(src)
    W, H, fps = int(cap.get(3)), int(cap.get(4)), cap.get(5) or 24
    quad = np.float32([(x * W, y * H) for x, y in WALL])
    lw, lh = 1600, 900
    L = np.array(layer(lw, lh))
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [lw, 0], [lw, lh], [0, lh]]), quad)
    warped = cv2.warpPerspective(L, M, (W, H))
    wa = warped[:, :, 3].astype(np.float32) / 255.0
    wrgb = warped[:, :, :3][:, :, ::-1].astype(np.float32)          # RGB→BGR
    tmp = tempfile.mkdtemp(); raw = os.path.join(tmp, "v.mp4")
    wr = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    n = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        b, g, r = f[:, :, 0].astype(np.int16), f[:, :, 1].astype(np.int16), f[:, :, 2].astype(np.int16)
        red = ((r > 120) & (r - g > 60) & (r - b > 60)).astype(np.uint8) * 255   # 켜진(붉은) 타일만
        red = cv2.erode(red, np.ones((9, 9), np.uint8))
        m = cv2.GaussianBlur(red, (0, 0), 3).astype(np.float32) / 255.0 * wa
        a3 = m[:, :, None] * 0.92
        f = (f.astype(np.float32) * (1 - a3) + wrgb * a3).astype(np.uint8)
        wr.write(f); n += 1
    wr.release()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", out], check=True)
    print(f"{out}: {n}프레임 {W}x{H}")


if __name__ == "__main__":
    main()
