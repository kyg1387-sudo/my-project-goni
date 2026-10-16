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


def occluder(frame, ref, H, alpha):
    """기준 프레임의 액자 안쪽을 현재 위치로 옮겨 비교 — 크게 달라진 화소(손가락)는 원본을 남긴다."""
    h, w = frame.shape[:2]
    ref_fwd = cv2.warpPerspective(ref, H, (w, h))
    d = np.abs(frame.astype(np.int16) - ref_fwd.astype(np.int16)).max(2).astype(np.uint8)
    m = ((d > 55) & (alpha > 0.3)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    m = cv2.dilate(m, np.ones((9, 9), np.uint8))
    return cv2.GaussianBlur(m, (0, 0), 2).astype(np.float32) / 255.0


def composite(frame, quad, photo, lum_ref, ref=None, H=None):
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
    if ref is not None:
        alpha = alpha * (1.0 - occluder(frame, ref, H, alpha))
    a3 = alpha[:, :, None]
    return (frame.astype(np.float32) * (1 - a3) + warped * a3).astype(np.uint8)


def track(frames, quad0, win):
    """SIFT 특징 매칭 + RANSAC 호모그래피(첫 프레임 기준). 액자 주변(사각형을 90px 넓힌 영역)의 특징만 쓴다."""
    sift = cv2.SIFT_create(nfeatures=3000)
    g0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    mask0 = np.zeros(g0.shape, np.uint8)
    cv2.fillPoly(mask0, [np.int32(quad0)], 255)
    mask0 = cv2.dilate(mask0, np.ones((181, 181), np.uint8))
    k0, d0 = sift.detectAndCompute(g0, mask0)
    x0, y0, x1, y1 = win
    bf = cv2.BFMatcher(cv2.NORM_L2)
    H = np.eye(3, dtype=np.float64)
    pts = np.float32(quad0).reshape(-1, 1, 2)
    quads, Hs = [], []
    for k, f in enumerate(frames):
        if k:
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            wmask = np.zeros(g.shape, np.uint8)
            q_prev = cv2.perspectiveTransform(pts, H)
            cv2.fillPoly(wmask, [np.int32(q_prev)], 255)
            wmask = cv2.dilate(wmask, np.ones((261, 261), np.uint8))
            k1, d1 = sift.detectAndCompute(g, wmask)
            if d1 is not None and len(k1) >= 8:
                m = bf.knnMatch(d0, d1, k=2)
                good = [a for a, b in (x for x in m if len(x) == 2) if a.distance < 0.75 * b.distance]
                if len(good) >= 10:
                    src = np.float32([k0[a.queryIdx].pt for a in good]).reshape(-1, 1, 2)
                    dst = np.float32([k1[a.trainIdx].pt for a in good]).reshape(-1, 1, 2)
                    Hn, inl = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
                    if Hn is not None and inl.sum() >= 8:
                        H = Hn
        q = cv2.perspectiveTransform(pts, H).reshape(-1, 2)
        quads.append(q); Hs.append(H.copy())
    # 떨림 완화: 꼭짓점 좌표를 5프레임 이동 평균
    arr = np.array(quads)
    sm = arr.copy()
    for i in range(len(arr)):
        a, b = max(0, i - 2), min(len(arr), i + 3)
        sm[i] = arr[a:b].mean(0)
    return [q for q in sm], Hs


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
        quads, Hs = track(frames, quad0, win)
        lum = None
        seg = os.path.join(tmp, f"{sid}.mp4")
        wr = cv2.VideoWriter(seg, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (1920, 1080))
        lum = photo.astype(np.float32).mean()
        for fr, q, Hk in zip(frames, quads, Hs):
            wr.write(composite(fr, q, photo, lum, frames[0], Hk))
        wr.release()
        segs.append((a, a + len(frames) / FPS, seg))
        for tag, j in (("mid", len(frames) // 2), ("end", len(frames) - 1)):
            cv2.imwrite(os.path.join(tmp, f"{sid}_{tag}.jpg"), composite(frames[j], quads[j], photo, lum, frames[0], Hs[j]))
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
