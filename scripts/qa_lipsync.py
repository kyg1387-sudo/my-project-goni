#!/usr/bin/env python3
"""립싱크 전수 자동 검수(R43, 2026-11-05 — 「처음부터 안 맞는 것」 재발 방지, 지속 개선 원칙 4).

완성본에서 립싱크 컷마다 ① 입 벌림(얼굴 랜드마크: 윗·아랫입술 안쪽 거리 / 얼굴 높이)과 ② 음성 포락선(300~3400Hz)을
프레임 단위로 만들고 상호상관으로 「입이 소리보다 몇 프레임 늦은가/빠른가」와 상관 세기를 잰다.
판정: |지연| ≤ 2프레임 & 상관 ≥ 0.30 = PASS, 그 밖은 CHECK(0.25초 입 크롭 시트로 눈 검수), 얼굴 못 찾음 = NOFACE.
출력: 표(마크다운) + 컷별 입 크롭 시트(0.25초 간격) — productions/<작품>/lipsync-qa/
사용법: python3 scripts/qa_lipsync.py <작품 SKIT> <완성본.mp4> [컷ID,…]   (컷 생략 = 립싱크 컷 전부 + 화면 속 영상 컷)
모델: mediapipe face_landmarker.task (MP_MODEL 환경변수 또는 scratchpad 경로)
"""
import importlib
import json
import os
import subprocess
import sys

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FPS = 24
MODEL = os.environ.get("MP_MODEL", "face_landmarker.task")


def frames(video, a, b, scale=960):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", video, "-vf", f"fps={FPS},scale={scale}:{int(round(scale * 9 / 16 / 2)) * 2}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    h = int(round(scale * 9 / 16 / 2)) * 2
    n = len(raw) // (scale * h * 3)
    return np.frombuffer(raw[: n * scale * h * 3], np.uint8).reshape(n, h, scale, 3)


def envelope(video, a, b):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", video, "-vn", "-ac", "1", "-ar", "16000",
           "-af", "highpass=f=300,lowpass=f=3400", "-f", "s16le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768
    hop = 16000 // FPS
    n = len(x) // hop
    e = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-9)
    return 20 * np.log10(e)


def mouth_series(fr):
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    opt = vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL), num_faces=3, running_mode=vision.RunningMode.VIDEO)
    out, boxes = [], []
    with vision.FaceLandmarker.create_from_options(opt) as lm:
        for i, f in enumerate(fr):
            r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(f)), int(i * 1000 / FPS))
            if not r.face_landmarks:
                out.append(np.nan); boxes.append(None); continue
            # 가장 큰 얼굴 = 화면의 주인공(앞 인물의 흐린 뒷머리는 랜드마크가 잡히지 않음)
            best = max(r.face_landmarks, key=lambda L: (max(p.y for p in L) - min(p.y for p in L)))
            ys = [p.y for p in best]; hgt = max(ys) - min(ys)
            out.append(abs(best[14].y - best[13].y) / max(hgt, 1e-6))
            xs = [p.x for p in best]
            boxes.append((min(xs), min(ys), max(xs), max(ys), best[13].x, (best[13].y + best[14].y) / 2))
    return np.array(out), boxes


def lag_corr(m, e, maxlag=12):
    ok = ~np.isnan(m)
    if ok.sum() < FPS:
        return None, 0.0
    m = np.where(ok, m, np.nanmedian(m))
    n = min(len(m), len(e)); m, e = m[:n], e[:n]
    m = (m - m.mean()) / (m.std() + 1e-9)
    e = np.clip(e, -60, None); e = (e - e.mean()) / (e.std() + 1e-9)
    best, bl = -9, 0
    for L in range(-maxlag, maxlag + 1):  # L > 0: 입이 소리보다 L프레임 늦음
        if L >= 0:
            c = np.mean(m[L:] * e[: n - L])
        else:
            c = np.mean(m[: n + L] * e[-L:])
        if c > best:
            best, bl = c, L
    return bl, float(best)


def crop_sheet(fr, boxes, out, step=6):
    tiles = []
    for i in range(0, len(fr), step):
        bx = boxes[i] if i < len(boxes) else None
        h, w = fr[i].shape[:2]
        if bx:
            cx, cy = bx[4] * w, bx[5] * h; s = (bx[3] - bx[1]) * h * 0.55
        else:
            cx, cy, s = w / 2, h * 0.45, h * 0.2
        x0, y0 = int(max(cx - s, 0)), int(max(cy - s * 0.7, 0))
        c = fr[i][y0:int(min(cy + s * 0.7, h)), x0:int(min(cx + s, w))]
        if c.size == 0:
            continue
        c = cv2.resize(c, (200, 140))
        cv2.putText(c, f"{i / FPS:.2f}", (4, 14), 0, 0.45, (255, 255, 0), 1)
        tiles.append(c)
    if not tiles:
        return
    cols = 8; rows = (len(tiles) + cols - 1) // cols
    sheet = np.zeros((rows * 140, cols * 200, 3), np.uint8)
    for k, t in enumerate(tiles):
        sheet[(k // cols) * 140:(k // cols + 1) * 140, (k % cols) * 200:(k % cols + 1) * 200] = t
    cv2.imwrite(out, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))


def main():
    skit, video = sys.argv[1], sys.argv[2]
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    sys.argv = [sys.argv[0]]
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    F = importlib.import_module(f"finalize_{skit}")
    B = F.bounds()
    ids = [s["id"] for s in F.SB if F.IDX[s["id"]] in F.OMNI] + list(getattr(F, "VIDSCREEN", {}))
    ids = sorted(set(ids), key=lambda s: F.IDX[s])
    if only:
        ids = [s for s in ids if s in only]
    prod = {"aihaha": "aihaha-ja"}.get(skit, skit)
    od = os.path.join(ROOT, "productions", prod, "lipsync-qa"); os.makedirs(od, exist_ok=True)
    rows = []
    for sid in ids:
        a, b = B[sid]
        fr = frames(video, a, b); e = envelope(video, a, b)
        m, boxes = mouth_series(fr)
        lag, c = lag_corr(m, e)
        face = float(np.mean(~np.isnan(m)))
        verdict = "NOFACE" if lag is None else ("PASS" if abs(lag) <= 2 and c >= 0.30 else "CHECK")
        crop_sheet(fr, boxes, os.path.join(od, f"{sid}.jpg"))
        rows.append((sid, a, b, lag, c, face, verdict))
        print(f"{sid:5s} {int(a // 60)}:{a % 60:05.2f} 지연 {lag if lag is not None else '-':>3}프레임 상관 {c:.2f} 얼굴 {face:.0%} → {verdict}", flush=True)
    with open(os.path.join(od, "result.json"), "w", encoding="utf-8") as f:
        json.dump([dict(zip(["id", "start", "end", "lag", "corr", "face", "verdict"], r)) for r in rows], f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
