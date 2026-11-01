#!/usr/bin/env python3
"""tsuki 시범 립싱크 컷(assets/auditions/tsuki-pilot-omni/omni-*.mp4)을 이어 붙여 한국어 검수판(480p)을 만든다(무료).
각 컷: 위에 [컷 ID · 화자] 한국어 번역(노란 글씨), 아래 일본어 원문. 사용법: make_ko_pilot_tsuki.py <출력.mp4>"""
import json, os, re, subprocess, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
out = sys.argv[1]
spec = json.load(open(os.path.join(ROOT, "scripts/auditions/tsuki-pilot-omni.json"), encoding="utf-8"))
ko = json.load(open(os.path.join(ROOT, "subs/tsuki-ko.json"), encoding="utf-8"))["tags"]
t = open(os.path.join(ROOT, "productions/tsuki-ja/00_script_ja.md"), encoding="utf-8").read().split("## 4. 대본")[1].split("## 5.")[0]
ja = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(r"^\s+(L\d+[a-c]?)\s*([^\s:「(\[]*)[^「\n]*「(.+)」", t, re.M)}
def dur(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
def tc(s): return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
parts, ev, pos, lst = [], [], 0.0, os.path.join(ROOT, "out", "pilot_list.txt")
os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
with open(lst, "w") as f:
    for x in spec["tests"]:
        p = os.path.join(ROOT, "assets/auditions/tsuki-pilot-omni", x["id"] + ".mp4")
        if not os.path.exists(p):
            print("없음", p); continue
        d = dur(p); spk, text = ja[x["audio_id"]]
        ev.append(f"Dialogue: 0,{tc(pos)},{tc(pos + d)},KO,,0,0,0,,[{x['id'][5:]} · {spk}] {ko[x['audio_id']]}")
        ev.append(f"Dialogue: 0,{tc(pos)},{tc(pos + d)},JA,,0,0,0,,{text}")
        f.write(f"file '{p}'\n"); pos += d
ass = os.path.join(ROOT, "out", "pilot_ko.ass")
open(ass, "w", encoding="utf-8").write("\n".join([
    "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "", "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    "Style: KO,Noto Sans CJK KR,60,&H0000E5FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,8,120,120,60,1",
    "Style: JA,Noto Sans CJK JP,66,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,120,120,90,1",
    "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"] + ev) + "\n")
tmp = os.path.join(ROOT, "out", "pilot_concat.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=24", tmp], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-vf", f"ass={ass},scale=-2:480", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "copy", out], check=True)
print(out, f"{pos:.1f}s")
