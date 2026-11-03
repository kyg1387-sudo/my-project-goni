#!/usr/bin/env python3
"""B안 템포(무료 로컬): 由紀子 내레이션(NA*) 템포 ≥1.0, 줄 안 쉼표 정적 0.45초 초과분을 0.35초로 압축
(「……」가 든 줄은 0.8초까지 유지 — 의도된 여운, 제19장 5). 결과는 lock_tempo가 이미 적용된 mp3.
사용법: python3 productions/aihaha-ja/pace_variant.py <출력폴더>  → lock_estimate.py <출력폴더> (LOCK_TEMPO_APPLIED=1)"""
import json, re, subprocess, sys, os
D = "assets/auditions/aihaha-tts"; OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
spec = {t["id"]: t for t in json.load(open("scripts/auditions/aihaha-tts.json"))["tests"]}
tags = {}
for ln in open("productions/aihaha-ja/05_톤연출표.md"):
    c = [x.strip() for x in ln.split("|")]
    if len(c) > 5 and re.fullmatch(r"line\d{3}", c[1]): tags[c[1]] = (c[2], c[5])
for rec, t in spec.items():
    tag, txt = tags[rec]
    tp = t.get("lock_tempo", 1.0)
    if tag.startswith("NA"): tp = max(tp, 1.0)
    cap = 0.8 if "……" in txt else 0.35
    src = f"{D}/{rec}.mp3"
    L = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout)
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", src, "-af", "silencedetect=n=-40dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)] + [L]
    segs = list(zip(st, en))
    a0, a1 = 0.0, L
    if segs and segs[0][0] < 0.05: a0 = segs[0][1]; segs = segs[1:]
    if segs and L - segs[-1][1] < 0.3: a1 = segs[-1][0]; segs = segs[:-1]
    # 남길 구간: 말 + 정적(최대 cap, 가운데를 잘라 양끝 숨 유지)
    keep, cur = [], a0
    for s_, e in segs:
        if e - s_ > cap:
            h = cap / 2; keep.append((cur, s_ + h)); cur = e - h
    keep.append((cur, a1))
    sel = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in keep)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", f"aselect='{sel}',asetpts=N/SR/TB,atempo={tp}", "-ar", "44100", "-b:a", "160k", f"{OUT}/{rec}.mp3"], check=True)
print("done", len(spec))
