#!/usr/bin/env python3
"""S04 액자 속 사진 합성(고니감독님 지적 2026-10-16: 「손에 들고 있는 액자 안에 아무것도 없다」) — 로컬, 무과금.
i2v 손 인서트(S04aa·S04b)의 액자 안쪽 네 모서리를 첫 프레임에서 지정하고, ECC 호모그래피로 프레임마다 추적해
S04a 가족사진(assets/portraits/tsuki-keyframes/S04a-1.png의 인화 부분)을 원근 합성한다. 손가락(살색)이 유리 위를 지나는 곳은 원본을 남긴다.
사용법: tsuki_photo_insert.py <입력.mp4> <출력.mp4>   (입력 = out/fin/main.mp4, 영상만 다시 인코딩·오디오 복사)"""
import os, subprocess, sys, tempfile
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finalize_tsuki as F

ROOT = F.ROOT
PHOTO = os.path.join(ROOT, "assets/portraits/tsuki-keyframes/S04a-1.png")
# 컷ID: (첫 프레임 액자 안쪽 네 점 TL,TR,BR,BL — 1920x1080), 추적 창(x0,y0,x1,y1)
CUTS = {"S04aa": ([(880, 550), (1035, 540), (1045, 725), (890, 740)], (760, 440, 1180, 860)),
        "S04b": ([(945, 465), (1130, 455), (1140, 635), (955, 650)], (800, 330, 1300, 760))}
FPS = 24


def photo_print():
    im = cv2.imread(PHOTO)                      # 1280x720, 인화 부분: x 400~1013, y 27~680(세로 구도로 자름)
    p = im[27:680, 400:1013]
    p = cv2.GaussianBlur(p, (0, 0), 0.8)
    sepia = np.array([[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]])  # 오래된 인화 느낌(BGR 입력이라 채널 뒤집어 적용)
    rgb = p[:, :, ::-1].astype(np.float32)
    s = np.clip(rgb @ sepia.T, 0, 255)
    out = (0.45 * s + 0.55 * rgb) * 0.92
    return np.clip(out, 0, 255).astype(np.uint8)[:, :, ::-1]


def skin_mask(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    m = ((h <= 25) | (h >= 170)) & (s >= 60) & (v >= 90)
    m = m.astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.dilate(m, np.ones((7, 7), np.uint8))
    return cv2.GaussianBlur(m, (0, 0), 2).astype(np.float32) / 255.0


def composite(frame, quad, photo, lum_ref):
    h, w = frame.shape[:2]
    ph, pw = photo.shape[:2]
    src = np.float32([[0, 0], [pw, 0], [pw, ph], [0, ph]])
    M = cv2.getPerspectiveTransform(src, np.float32(quad))
    warped = cv2.warpPerspective(photo, M, (w, h), flags=cv2.INTER_LINEAR)
    alpha = cv2.warpPerspective(np.full((ph, pw), 255, np.uint8), M, (w, h))
    alpha = cv2.erode(alpha, np.ones((3, 3), np.uint8))
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.0).astype(np.float32) / 255.0
    # 현장 조명 반영: 액자 안쪽 원본의 평균 밝기·색을 사진에 입힌다(유리 반사·푸른 달빛)
    inner = (alpha > 0.5)
    if inner.sum() > 100:
        cur = frame[inner].astype(np.float32).mean(0)
        tint = cur / max(lum_ref, 1.0)
        warped = np.clip(warped.astype(np.float32) * (0.35 + 0.65 * tint / tint.mean()) * (0.6 + 0.4 * tint.mean()), 0, 255)
        glass = frame.astype(np.float32)
        warped = 0.82 * warped + 0.18 * glass          # 유리 반사 살짝
    alpha = alpha * (1.0 - skin_mask(frame))
    a3 = alpha[:, :, None]
    return (frame.astype(np.float32) * (1 - a3) + warped * a3).astype(np.uint8)


def track(frames, quad0, win):
    """ECC 호모그래피(첫 프레임 기준, 이전 결과로 초기화)."""
    x0, y0, x1, y1 = win
    ref = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)[y0:y1, x0:x1]
    H = np.eye(3, dtype=np.float32)
    quads, crit = [], (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 1e-5)
    pts = np.float32(quad0).reshape(-1, 1, 2) - np.float32([x0, y0])
    for k, f in enumerate(frames):
        if k:
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)[y0:y1, x0:x1]
            try:
                _, H = cv2.findTransformECC(ref, g, H.copy(), cv2.MOTION_HOMOGRAPHY, crit, None, 5)
            except cv2.error:
                pass
        q = cv2.perspectiveTransform(pts, H).reshape(-1, 2) + np.float32([x0, y0])
        quads.append(q)
    return quads


def main():
    src, out = sys.argv[1], sys.argv[2]
    B = F.bounds()
    photo = photo_print()
    tmp = tempfile.mkdtemp()
    segs = []
    for sid, (quad0, win) in CUTS.items():
        a, b = B[sid]
        n = int(round((b - a) * FPS))
        cap = cv2.VideoCapture(src); cap.set(cv2.CAP_PROP_POS_MSEC, a * 1000)
        frames = []
        for _ in range(n):
            ok, fr = cap.read()
            if not ok: break
            frames.append(fr)
        cap.release()
        quads = track(frames, quad0, win)
        lum = None
        seg = os.path.join(tmp, f"{sid}.mp4")
        wr = cv2.VideoWriter(seg, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (1920, 1080))
        for fr, q in zip(frames, quads):
            if lum is None:
                lum = photo.astype(np.float32).mean()
            wr.write(composite(fr, q, photo, lum))
        wr.release()
        segs.append((a, a + len(frames) / FPS, seg))
        cv2.imwrite(os.path.join(tmp, f"{sid}_mid.jpg"), composite(frames[len(frames) // 2], quads[len(frames) // 2], photo, lum))
        print(f"{sid}: {a:.2f}-{b:.2f} {len(frames)}프레임, 추적 끝점 이동 {np.abs(quads[-1] - quads[0]).max():.1f}px → {tmp}/{sid}_mid.jpg")
    if "--preview" in sys.argv:
        return
    inputs, fc, last = ["-i", src], [], "[0:v]"
    for k, (a, b, seg) in enumerate(segs, start=1):
        inputs += ["-i", seg]
        fc.append(f"[{k}:v]setpts=PTS-STARTPTS+{a:.3f}/TB[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    F.run(inputs + ["-filter_complex", ";".join(fc), "-map", last, "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy", out])
    print("완료:", out)


if __name__ == "__main__":
    main()
