#!/usr/bin/env python3
"""Lock 미리듣기(무료): lock.json 타임코드대로 line mp3를 배치해 한 트랙으로 합친다(후크 20초·아웃트로 포함, BGM 없음).
사용법: python3 productions/soukaion-ja/make_lock_preview.py  → productions/soukaion-ja/06_Lock음성미리듣기.mp3"""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIO = os.path.join(REPO, "assets", "auditions", "soukaion-tts")
lock = json.load(open(os.path.join(HERE, "lock.json")))
total = lock["total"] + 2.0
inputs, filters, n = [], [], 0
t_out = lock["body_end"] + 1.0
for x in lock["lines"]:
    p = os.path.join(AUDIO, x["audio"] + ".mp3")
    if not os.path.exists(p):
        continue
    if "start" in x:
        st = x["start"]
    elif x["scene"] == "OUT":  # 아웃트로: 본편 끝 뒤 순서대로
        st = t_out; t_out += x["dur"] + 0.8
    else:
        continue
    delay = max(0.0, st - x["lead"] / x.get("stretch", 1.0))
    f = x.get("stretch", 1.0)
    inputs += ["-i", p]
    at = f"atempo={f}," if abs(f - 1.0) > 1e-3 else ""
    filters.append(f"[{n}:a]{at}aresample=44100,aformat=channel_layouts=mono,adelay={int(delay*1000)}|{int(delay*1000)}[a{n}]"); n += 1
mix = "".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0:dropout_transition=0,volume=1.0,apad=whole_dur={total}[out]"
out = os.path.join(HERE, "06_Lock음성미리듣기.mp3")
r = subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters) + ";" + mix, "-map", "[out]", "-t", str(total), "-c:a", "libmp3lame", "-q:a", "4", out], capture_output=True, text=True)
print("ok" if r.returncode == 0 else r.stderr[-800:], n, "lines", out)
