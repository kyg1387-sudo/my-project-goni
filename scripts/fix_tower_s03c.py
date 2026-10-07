#!/usr/bin/env python3
"""수정 3·4(감독님 지적 1:19~1:21): S03b(리코 단독, 키즈룸 안 아이 2명 놀이) → S03c(마마A 등장)에서
같은 카메라인데 마마A가 갑자기 생기고 안쪽 아이들이 사라진다. 무과금 로컬 보정:
 1) S03b 클립의 1.6초 이후(본편에 쓴 다음 순간) 프레임을 배경 특징점 호모그래피로 S03c에 맞춰,
    키즈룸 안쪽(유리 너머 놀이 공간) 영역만 페더 마스크로 S03c 프레임 위에 얹는다 → 아이들이 이어서 논다.
 2) 같은 구도 점프컷 해소: 마마A·리코 투샷으로 크롭(약 2.1배).
입력: out/i2v/scene20.mp4(S03b), scene21.mp4(S03c) — 생성 Artifact 원본. 출력: assets/video-overrides/tower/scene21.mp4
"""
import os, subprocess, sys
import cv2, numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def frames(p):
    info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.split(",")
    w, h = int(info[0]), int(info[1])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", "fps=24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3), w, h


def main():
    b, bw, bh = frames(os.path.join(ROOT, "out/i2v/scene20.mp4"))
    c, w, h = frames(os.path.join(ROOT, "out/i2v/scene21.mp4"))
    b = b[int(1.6 * 24):]   # 본편 S03b 다음 순간부터
    # 배경 정렬: 놀이방 안쪽·창틀(사람 없는 영역) 특징점
    roi = np.zeros((h, w), np.uint8); roi[int(h * 0.05):int(h * 0.8), int(w * 0.45):] = 255
    orb = cv2.ORB_create(4000)
    kb, db = orb.detectAndCompute(cv2.cvtColor(b[0], cv2.COLOR_RGB2GRAY), cv2.resize(roi, (bw, bh)))
    kc, dc = orb.detectAndCompute(cv2.cvtColor(c[0], cv2.COLOR_RGB2GRAY), roi)
    ms = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(db, dc), key=lambda m: m.distance)[:500]
    Hm, inl = cv2.findHomography(np.float32([kb[m.queryIdx].pt for m in ms]), np.float32([kc[m.trainIdx].pt for m in ms]), cv2.RANSAC, 3.0)
    print("정렬 특징점", int(inl.sum()), "/", len(ms))
    # 얹을 영역: 유리 너머 놀이 공간(매트·아이들) — 마마A·리코(왼쪽 x<0.33)와 겹치지 않게
    m = np.zeros((h, w), np.float32)
    m[int(h * 0.42):int(h * 0.78), int(w * 0.50):] = 1.0
    m = cv2.GaussianBlur(m, (0, 0), 18)[..., None]
    n = len(c); out = []
    for i in range(n):
        wb = cv2.warpPerspective(b[min(i, len(b) - 1)], Hm, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        out.append((c[i] * (1 - m) + wb * m).astype(np.uint8))
    tmp = os.path.join(ROOT, "out", "s03c_comp.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", "24", "-i", "-",
                          "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in out:
        p.stdin.write(f.tobytes())
    p.stdin.close(); p.wait()
    cw = int(w * 0.72); ch = int(cw * 9 / 16); y0 = h - ch
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-vf", f"crop={cw}:{ch}:0:{y0},scale=1920:1080:flags=lanczos,unsharp=5:5:0.4,fps=24,format=yuv420p",
                    "-an", "-c:v", "libx264", "-crf", "19", os.path.join(ROOT, "assets/video-overrides/tower/scene21.mp4")], check=True)
    print("저장: assets/video-overrides/tower/scene21.mp4", f"(크롭 {cw}x{ch})")


if __name__ == "__main__":
    main()
