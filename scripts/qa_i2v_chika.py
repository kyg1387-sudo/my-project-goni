#!/usr/bin/env python3
"""#02 생성 i2v 클립 검수(무과금): 첫 2초 헤드턴(얼굴 중심 이동·크기 변화), 프레임 붕괴(프레임간 급변), 첫 프레임↔키프레임 일치,
얼굴 수 변화(새 인물 난입), 테이크별 요약. 사용법: qa_i2v_chika.py <clips_dir>  (scene{NN}.mp4, scene{NN}_take{k}.mp4)"""
import glob, json, os, re, sys
import cv2, numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
D = sys.argv[1]
sb = json.load(open(os.path.join(ROOT, "scripts/storyboard/chika.json"), encoding="utf-8"))["scenes"]
DET = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def faces(g):
    return list(DET.detectMultiScale(g, 1.1, 5, minSize=(40, 40)))


rows = []
for p in sorted(glob.glob(os.path.join(D, "scene*.mp4"))):
    m = re.match(r"scene(\d+)(?:_take(\d+))?\.mp4", os.path.basename(p)); i, take = int(m.group(1)), m.group(2) or "-"
    s = sb[i - 1]
    if s["tier"] not in ("lite", "pro", "hero"): continue
    cap = cv2.VideoCapture(p); fps = cap.get(cv2.CAP_PROP_FPS) or 24; prev = None; diffs = []; fcount = []; centers = []
    k = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(cv2.resize(f, (480, 270)), cv2.COLOR_BGR2GRAY)
        if prev is not None: diffs.append(float(np.abs(g.astype(float) - prev.astype(float)).mean()))
        if k % 6 == 0:
            fs = faces(g); fcount.append(len(fs))
            if fs:
                x, y, w, h = max(fs, key=lambda r: r[2] * r[3]); centers.append((k / fps, x + w / 2, y + h / 2, w))
        if k == 0: first = g.copy()
        prev = g; k += 1
    cap.release()
    kf = cv2.imread(os.path.join(ROOT, s["keyframe"]))
    corr = float(np.corrcoef(cv2.resize(cv2.cvtColor(kf, cv2.COLOR_BGR2GRAY), (480, 270)).ravel().astype(float), first.ravel().astype(float))[0, 1]) if kf is not None else -1
    d = np.array(diffs) if diffs else np.zeros(1)
    head = [c for c in centers if c[0] <= 2.0]
    turn = max((abs(c[1] - head[0][1]) / max(1, head[0][3]) for c in head), default=0.0)   # 얼굴 너비 대비 중심 이동(첫 2초)
    note = []
    if corr < 0.7: note.append(f"키프레임 불일치 {corr:.2f}")
    if d.max() > 25: note.append(f"급변 {d.max():.0f}@{int(d.argmax() / fps * 10) / 10}s")
    if turn > 0.35: note.append(f"첫2초 얼굴 이동 {turn:.2f}")
    if fcount and max(fcount) > (1 if s["kind"] in ("face", "react", "d") else 99) and s["size"] in ("cu", "ms", "ch"): note.append(f"얼굴 수 {max(fcount)}")
    rows.append((i, s["id"], take, s["tier"], k, round(d.mean(), 2), round(d.max(), 1), round(corr, 2), round(turn, 2), " ".join(note)))
print(f"{'장면':>5} {'id':6} {'take':4} {'tier':5} {'f':>4} {'평균차':>6} {'최대차':>6} {'KF상관':>6} {'헤드턴':>6}  비고")
for r in rows: print(f"{r[0]:5d} {r[1]:6} {r[2]:4} {r[3]:5} {r[4]:4d} {r[5]:6} {r[6]:6} {r[7]:6} {r[8]:6}  {r[9]}")
print(f"클립 {len(rows)}개, 비고 있는 클립 {sum(1 for r in rows if r[9])}개")
