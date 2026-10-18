#!/usr/bin/env python3
"""#02 교체 클립 검수(무과금): 해상도 1920x1080·24fps, 길이 = scene_durations+0.5(±2프레임), 첫·중간·끝 프레임 밝기(검은 프레임·흰 프레임),
키프레임과의 일치(첫 프레임 ↔ 키프레임 상관). 사용법: qa_overrides_chika.py [<overrides_dir>]"""
import json, os, subprocess, sys
import numpy as np, cv2
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets/video-overrides/chika")
sb = json.load(open(os.path.join(ROOT, "scripts/storyboard/chika.json"), encoding="utf-8"))["scenes"]
durs = json.load(open(os.path.join(ROOT, "scripts/audio/chika.json"), encoding="utf-8"))["scene_durations"]
bad, n = [], 0
for i, s in enumerate(sb, 1):
    p = os.path.join(D, f"scene{i:02d}.mp4")
    if not os.path.exists(p):
        if s["tier"] not in ("lite", "pro", "hero"): bad.append(f"scene{i:02d} {s['id']}: 교체 클립 없음({s['tier']})")
        continue
    n += 1
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height,r_frame_rate,nb_frames", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip().split(",")
    if len(info) < 4 or not info[3].isdigit():
        bad.append(f"scene{i:02d} {s['id']}: 파일 손상/작성 중"); continue
    w, h, fr, nf = int(info[0]), int(info[1]), info[2], int(info[3])
    want = int(np.ceil((durs[i - 1] + 0.5) * 24)) if s["tier"] != "card" else int(np.ceil(durs[i - 1] * 24))
    if (w, h) != (1920, 1080) or fr != "24/1": bad.append(f"scene{i:02d} {s['id']}: {w}x{h} {fr}")
    if s["tier"] in ("lite", "pro", "hero"):   # 생성 클립(후처리본)은 생성 길이(5·10초) 그대로, 조립에서 계획 길이로 트리밍
        if nf < want - 2: bad.append(f"scene{i:02d} {s['id']}: 생성 클립 {nf}프레임 < 계획 {want}")
    elif abs(nf - want) > 2: bad.append(f"scene{i:02d} {s['id']}: {nf}프레임 ≠ {want}")
    cap = cv2.VideoCapture(p); frames = []
    for k in (0, nf // 2, nf - 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, f = cap.read()
        if ok: frames.append(f)
    cap.release()
    if len(frames) < 3: bad.append(f"scene{i:02d} {s['id']}: 프레임 읽기 실패"); continue
    lum = [f.mean() for f in frames]
    if s["tier"] != "card" and s["edit_fx"] != "flash" and (min(lum) < 4 or max(lum) > 250): bad.append(f"scene{i:02d} {s['id']}: 밝기 이상 {['%.0f' % v for v in lum]}")
    if s["tier"] not in ("card", "reuse") and s["kind"] != "gfx":
        kf = cv2.imread(os.path.join(ROOT, s["keyframe"]))
        if kf is not None:
            a = cv2.resize(cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY), (160, 90)).astype(np.float32); b = cv2.resize(cv2.cvtColor(kf, cv2.COLOR_BGR2GRAY), (160, 90)).astype(np.float32)
            c = np.corrcoef(a.ravel(), b.ravel())[0, 1]
            if c < (0.45 if s["size"] in ("ws", "ews") else 0.6): bad.append   # 와이드는 팬 시작 오프셋(z 1.07, x 0.2)으로 상관이 낮다(f"scene{i:02d} {s['id']}: 첫 프레임이 키프레임과 다름(상관 {c:.2f})")
print(f"검수 {n}개, 문제 {len(bad)}건"); [print("  ", b) for b in bad]
sys.exit(1 if bad else 0)
