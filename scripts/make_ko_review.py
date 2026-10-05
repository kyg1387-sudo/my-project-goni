#!/usr/bin/env python3
"""한국어 검수용 자막 영상(감독님 검수 전용, 업로드본 아님) — 일본어 자막 위쪽에 [화자] 한국어 번역을 노란 글씨로 얹은 480p.
번역: subs/<skit>-ko.json (subs/<skit>.ass 대사 순서와 1:1). 아웃트로 진행자 4줄은 out/<skit>-outro.json 시각으로.
사용법: make_ko_review.py <완성본.mp4> <출력.mp4>   (FONTSDIR=Noto Sans CJK 글꼴 폴더)
"""
import json, os, re, subprocess, sys
import imageio_ffmpeg
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = imageio_ffmpeg.get_ffmpeg_exe()
src, out = sys.argv[1], sys.argv[2]
ko = json.load(open(os.path.join(ROOT, "subs/yanagi-ko.json"), encoding="utf-8"))
ev = [l for l in open(os.path.join(ROOT, "subs/yanagi.ass"), encoding="utf-8") if l.startswith("Dialogue:")]
assert len(ev) == len(ko["lines"]), (len(ev), len(ko["lines"]))
def sec(t):
    h, m, s = t.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
def tc(s):
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
rows = []
for l, k in zip(ev, ko["lines"]):
    f = l.split(",", 9); a, b, style = sec(f[1]), sec(f[2]), f[3]
    rows.append((a, b, f"[{ko['speakers'].get(style, style)}] {k}"))
meta = json.load(open(os.path.join(ROOT, "out/yanagi-outro.json")))
# 아웃트로 시작 = 본편 길이 + 검은 화면 0.8초(append_outro.py)
main = 581.25 + 0.8
tts = {"075": meta["t075"], "076": meta["host_start"][0], "077": meta["host_start"][1], "078": meta["host_start"][2]}
for n, t in tts.items():
    rows.append((main + t, main + t + 4.0, f"[진행자] {ko['outro'][n]}"))
ass = os.path.join(ROOT, "out/yanagi-ko.ass")
with open(ass, "w", encoding="utf-8") as fp:
    fp.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n\n[V4+ Styles]\n"
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
             "Style: KO,Noto Sans CJK JP,50,&H0000F0FF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,3,12,0,8,120,120,40,1\n\n"
             "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    for a, b, t in rows:
        fp.write(f"Dialogue: 0,{tc(a)},{tc(b)},KO,,0,0,0,,{t}\n")
fd = os.environ.get("FONTSDIR", "/usr/share/fonts")
subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vf", f"ass={ass}:fontsdir={fd},scale=-2:480", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "27", "-c:a", "aac", "-b:a", "96k", out], check=True)
print("저장:", out, len(rows), "줄")
