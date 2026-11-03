#!/usr/bin/env python3
"""PHASE 1 Lock 1차 계산 — 녹음 실측(앞뒤 무음 제거 ÷ lock_tempo) + 줄 간격(같은 화자 0.6 / 교체 0.8) + 대본의 무언 비트.
사용법: python3 productions/aihaha-ja/lock_estimate.py [녹음폴더]"""
import json, re, subprocess, sys, os
D = sys.argv[1] if len(sys.argv) > 1 else "assets/auditions/aihaha-tts"
spec = {t["id"]: t for t in json.load(open("scripts/auditions/aihaha-tts.json"))["tests"]}
rows = []
for ln in open("productions/aihaha-ja/05_톤연출표.md"):
    c = [x.strip() for x in ln.split("|")]
    if len(c) > 5 and re.fullmatch(r"line\d{3}", c[1]): rows.append((c[1], c[2], c[3], c[5]))
scr = open("productions/aihaha-ja/00_script_ja.md").read().split("## 4. 대본")[1].split("## 5.")[0]
act_of, act = {}, None
for ln in scr.splitlines():
    m = re.match(r"^### (\S)", ln)
    if m: act = m.group(1)
    m = re.match(r"^\s*((?:NA|L|OUT)\d+\w*)\b", ln)
    if m: act_of.setdefault(m.group(1), act)
def dur(p):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-af",
        "silenceremove=start_periods=1:start_threshold=-40dB,areverse,silenceremove=start_periods=1:start_threshold=-40dB,areverse",
        "-f", "wav", "-"], capture_output=True).stdout
    return max(0.0, (len(out) - 44) / (44100 * 2 * 1)) if out else 0.0
def raw(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
# 무언 비트(대본 지문): 「무언 N초」「N초 정적」「정적 N초」「카드 ... N초」
extra = {}
cur = None
for ln in scr.splitlines():
    m = re.match(r"^\s*((?:NA|L|OUT)\d+\w*)\b", ln)
    if m: cur = m.group(1)
    for s in re.findall(r"(?:무언\s*|정적\s*|정적\(룸톤\)\s*)(\d+(?:\.\d+)?)초|(\d+(?:\.\d+)?)초\s*정적|카드[^\n]*?(\d+(?:\.\d+)?)초", ln):
        v = float(next(x for x in s if x))
        if cur: extra[cur] = extra.get(cur, 0) + v
res, t, prev = [], 0.0, None
pauses = []
acts = {}
for rec, tag, role, text in rows:
    p = f"{D}/{rec}.mp3"
    import os
    if not os.path.exists(p): print("없음", p); continue
    # 정확한 길이: silencedetect(-40dB, 0.25s)로 말 시작·끝 — 끝의 작은 잡음(<0.3s)·숨은 무시, 줄 안 1.0초 넘는 정적은 보고
    L = raw(p)
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", p, "-af", "silencedetect=n=-40dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)] + [L]
    segs = list(zip(st, en))
    a0, a1 = 0.0, L
    if segs and segs[0][0] < 0.05: a0 = segs[0][1]; segs = segs[1:]
    if segs and L - segs[-1][1] < 0.3: a1 = segs[-1][0]; segs = segs[:-1]
    longp = [round(e - s_, 2) for s_, e in segs if e - s_ > 1.0]
    if longp: pauses.append((rec, tag, longp))
    d = (a1 - a0) / (1.0 if os.environ.get("LOCK_TEMPO_APPLIED") else spec[rec].get("lock_tempo", 1.0))
    spk = role.split("(")[0]
    gap = 0 if prev is None else (0.6 if spk == prev else 0.8)
    t += gap
    a = act_of.get(tag, "?")
    res.append((rec, tag, a, round(t, 2), round(d, 2), raw(p), text))
    t += d + extra.get(tag, 0)
    acts[a] = acts.get(a, 0) + d + gap + extra.get(tag, 0)
    prev = spk
json.dump(res, open("productions/aihaha-ja/lock_estimate.json", "w"), ensure_ascii=False, indent=0)
print(f"총 {int(t//60)}:{t%60:04.1f} ({t:.1f}s), 무언 비트 합 {sum(extra.values()):.1f}s")
for a, v in acts.items(): print(a, f"{v:.1f}s", f"{100*v/t:.0f}%")
for r in res:
    if r[1] in ("NA13", "NA28", "NA31", "NA32", "OUT1"): print("마커", r[1], f"{int(r[3]//60)}:{r[3]%60:04.1f}", r[6][:20])
print("1.0초 넘는 줄 안 정적:", pauses)
print("raw 최장/최단:", max(res, key=lambda r: r[4])[:5], min(res, key=lambda r: r[4])[:5])
