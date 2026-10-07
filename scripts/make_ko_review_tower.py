#!/usr/bin/env python3
"""『タワマンのボスママ』 한국어 검수용 영상(감독님 검수 전용, 업로드본 아님) — 일본어 자막은 그대로 두고
화면 위쪽에 [화자] 한국어 번역을 노란 글씨로 얹은 720p(오류 확인용, 타임코드 표시).
번역: subs/tower-ko.json(subs/tower.ass 68줄과 1:1). 아웃트로는 out/tower-outro.json 컷 시작 시각 + 본편 길이 + 검은 화면 0.8초.
사용법: make_ko_review_tower.py <완성본.mp4> <출력.mp4> <본편 길이(초)>
"""
import json, os, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_tower_outro as bo  # noqa: E402
src, out, main_len = sys.argv[1], sys.argv[2], float(sys.argv[3])
ko = json.load(open(os.path.join(ROOT, "subs/tower-ko.json"), encoding="utf-8"))
ev = [l for l in open(os.path.join(ROOT, "subs/tower.ass"), encoding="utf-8") if l.startswith("Dialogue:")]
assert len(ev) == len(ko["lines"]), (len(ev), len(ko["lines"]))
sec = lambda t: (lambda h, m, s: int(h) * 3600 + int(m) * 60 + float(s))(*t.split(":"))
tc = lambda s: f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
rows = []
for l, k in zip(ev, ko["lines"]):
    f = l.split(",", 9); a, b, st = sec(f[1]), sec(f[2]), f[3]
    rows.append((a, b, k if k.startswith("(") else f"[{ko['speakers'].get(st, st)}] {k}"))
meta = json.load(open(os.path.join(ROOT, "out/tower-outro.json")))
o0 = main_len + 0.8
for k, (kf, fx, line, a, b, text, st) in enumerate(bo.MONTAGE):
    t = o0 + meta["starts"][k] + 0.45; rows.append((t, t + (b - a) + 0.3, ko["montage"][k]))
for j in range(4):
    t = o0 + meta["starts"][len(bo.MONTAGE) + j]; rows.append((t, t + 4.5, ko["host"][j]))
ass = os.path.join(ROOT, "out/tower-ko.ass")
with open(ass, "w", encoding="utf-8") as fp:
    fp.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n\n[V4+ Styles]\n"
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
             "Style: KO,Noto Sans CJK KR,46,&H0000F0FF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,3,10,0,8,100,100,30,1\n"
             "Style: TC,Noto Sans CJK KR,30,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,3,6,0,9,20,20,20,1\n\n"
             "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    for a, b, t in rows:
        fp.write(f"Dialogue: 0,{tc(a)},{tc(b)},KO,,0,0,0,,{t.replace(chr(10), ' ')}\n")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).decode())
vf = f"ass={ass},drawtext=fontfile=/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf:text='%{{pts\\:hms}}':x=w-tw-20:y=h-th-20:fontsize=34:fontcolor=white:box=1:boxcolor=black@0.5,scale=-2:720"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out], check=True)
print("저장:", out, len(rows), "줄", f"({dur:.1f}s)")
