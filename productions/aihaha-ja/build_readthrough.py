#!/usr/bin/env python3
"""본녹음 110줄 → 낭독 미리듣기(Lock 순서·lock_tempo·줄 간격 0.6/0.8, 앞뒤 무음 -40dB 제거). 무료 로컬.
사용법: python3 productions/aihaha-ja/build_readthrough.py  (먼저 lock_estimate.py 실행)"""
import json, subprocess, os, sys, tempfile
D = sys.argv[1] if len(sys.argv) > 1 else "assets/auditions/aihaha-tts"; OUT = "productions/aihaha-ja/PHASE1_청취"
PFX = sys.argv[2] if len(sys.argv) > 2 else "본녹음"; APPLIED = os.environ.get("LOCK_TEMPO_APPLIED")
spec = {t["id"]: t for t in json.load(open("scripts/auditions/aihaha-tts.json"))["tests"]}
res = json.load(open("productions/aihaha-ja/lock_estimate.json"))
tmp = tempfile.mkdtemp()
TRIM = "silenceremove=start_periods=1:start_threshold=-40dB,areverse,silenceremove=start_periods=1:start_threshold=-40dB,areverse"
acts = {}
for i, (rec, tag, a, t, d, raw, txt) in enumerate(res):
    tp = 1.0 if APPLIED else spec[rec].get("lock_tempo", 1.0)
    f = f"{tmp}/{i:03d}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/{rec}.mp3", "-af", f"{TRIM},atempo={tp},aresample=44100", "-ac", "1", f], check=True)
    acts.setdefault(a, []).append((t, f))
def build(items, out):
    t0 = items[0][0]; inputs, filt = [], []
    for k, (t, f) in enumerate(items):
        inputs += ["-i", f]; ms = int((t - t0) * 1000); filt.append(f"[{k}]adelay={ms}[a{k}]")
    filt.append("".join(f"[a{k}]" for k in range(len(items))) + f"amix=inputs={len(items)}:normalize=0,loudnorm=I=-16:TP=-1.5[o]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[o]", "-b:a", "128k", out], check=True)
names = {"①": "1_후크", "②": "2_발단", "③": "3_전개", "④": "4_절정", "⑤": "5_결말", "⑥": "6_아웃트로"}
for a, items in acts.items():
    build(items, f"{OUT}/{PFX}_{names.get(a, a)}.mp3")
build([x for a in acts for x in acts[a]], f"{OUT}/{PFX}_전체낭독.mp3")
print("ok", os.listdir(OUT))
