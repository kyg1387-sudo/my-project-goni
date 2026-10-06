#!/usr/bin/env python3
"""본편 완성본 → 세로 쇼츠(1080x1920, EP3 형식): 흐린 배경 + 위 훅 제목 + 가운데 16:9 영상(원 자막 영역은 잘라냄)
+ 아래 큰 일본어 자막(원 .ass 타이밍 재사용) + 끝 「続きは本編で」 1.2초. 무과금, 로컬.

사용법: make_shorts.py <본편.mp4(자막 입힘, 아웃트로 전)> <subs.ass> <spec.json> <out_dir>
spec: {"shorts":[{"id":"1-letter","start":88.9,"end":112.3,"title":"…\\N…"}]}
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "scripts", "fonts")


def t2s(t):
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def s2t(x):
    x = max(x, 0)
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap(text, limit=15):
    """세로 화면용 줄바꿈: 한 줄 최대 약 15자. 범위 안의 마지막 。、…』」 뒤에서 끊고, 없으면 15자에서 끊는다."""
    t = text.replace("\\N", "")
    out = []
    while len(t) > limit + 2:
        cut = max((k + 1 for k in range(5, limit + 1) if t[k] in "。、…』」？！?!"), default=0)
        if not cut:  # 문장부호가 없으면 조사 뒤에서 끊는다
            cut = max((k + 1 for k in range(7, limit + 1) if t[k] in "がでにをはのと"), default=limit)
        while cut < len(t) and t[cut] in "…。、』」？！?!—":  # 구두점·말줄임표로 시작하는 줄 금지
            cut += 1
        out.append(t[:cut]); t = t[cut:]
    if t:
        out.append(t)
    return "\\N".join(out)


def events(ass_path):
    out = []
    for line in open(ass_path, encoding="utf-8"):
        if line.startswith("Dialogue:"):
            p = line.split(",", 9)
            out.append((t2s(p[1]), t2s(p[2]), p[3], p[9].strip()))
    return out


HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Zen Old Mincho,74,&H0040E0FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,3,8,60,60,330,1
Style: Sub,IPAGothic,52,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,8,70,70,1250,1
Style: Cap,Zen Old Mincho,58,&H00C4F3FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,8,70,70,1250,1
Style: End,Zen Old Mincho,80,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    src, ass_path, spec_path, out_dir = sys.argv[1:5]
    os.makedirs(out_dir, exist_ok=True)
    ev = events(ass_path)
    spec = json.load(open(spec_path, encoding="utf-8"))
    for sh in spec["shorts"]:
        a, b = float(sh["start"]), float(sh["end"])
        dur = b - a
        tail = 1.2
        lines = [f"Dialogue: 0,{s2t(0)},{s2t(dur + tail)},Title,,0,0,0,,{sh['title']}"]
        for s, e, style, text in ev:
            if e <= a or s >= b:
                continue
            st = "Cap" if style == "Caption" else "Sub"
            lines.append(f"Dialogue: 0,{s2t(s - a)},{s2t(min(e, b) - a)},{st},,0,0,0,,{wrap(text)}")
        lines.append(f"Dialogue: 0,{s2t(dur)},{s2t(dur + tail)},End,,0,0,0,,{sh.get('end_text', '続きは本編で')}")
        sub = os.path.join(out_dir, f"_{sh['id']}.ass")
        open(sub, "w", encoding="utf-8").write(HEAD + "\n".join(lines) + "\n")
        out = os.path.join(out_dir, f"{spec['prefix']}-short-{sh['id']}-JP.mp4")
        # 원 자막(하단)을 피해 위 80%만 쓰고, 흐린 배경 위 가운데(위쪽 약간)에 놓는다
        fc = (f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={tail},split[s1][s2];"
              f"[s1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.12[bg];"
              f"[s2]crop=iw:ih*0.80:0:0,scale=1080:-2[fg];"
              f"[bg][fg]overlay=0:560,ass={sub}:fontsdir={FONTS},fade=t=in:st=0:d=0.3[v];"
              f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,"
              f"afade=t=out:st={dur - 0.6:.3f}:d=0.6,apad=pad_dur={tail}[a]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
        os.remove(sub)
        print(f"저장: {out} ({dur + tail:.1f}s)")


if __name__ == "__main__":
    main()
