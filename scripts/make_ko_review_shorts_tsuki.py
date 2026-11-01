#!/usr/bin/env python3
"""『月に帰った契約社員』 쇼츠 한국어 검수판(고니감독님 검수 전용, 업로드본 아님, 제10장 5).
쇼츠 5편을 이어 붙여 각 편 맨 위에 [번호·한국어 제목], 영상과 일본어 자막 사이에 [화자] 한국어 번역(노란 글씨)을 얹은 540x960.
번역: subs/tsuki-ko.json(subs/tsuki.ass 대사와 1:1), 쇼츠 구간: productions/tsuki-ja/shorts.json.
사용법: make_ko_review_shorts_tsuki.py <출력.mp4>
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SHORTS = os.path.join(ROOT, "assets", "shorts", "tsuki")
spec = json.load(open(os.path.join(ROOT, "productions/tsuki-ja/shorts.json"), encoding="utf-8"))
ko = json.load(open(os.path.join(ROOT, "subs/tsuki-ko.json"), encoding="utf-8"))
ev = [l for l in open(os.path.join(ROOT, "subs/tsuki.ass"), encoding="utf-8") if l.startswith("Dialogue:")]
assert len(ev) == len(ko["lines"])
KO_TITLE = {"1-gomi": "계약사원에게 「달에서 온 쓰레기」", "2-kyohi": "정사원 제안을 거절한 계약사원",
            "3-anten": "해고한 지 30일, 회사의 불이 꺼졌다", "4-200oku": "위조 도장… 위약금은 200억 엔",
            "5-takeyabu": "「사람 목숨이 걸린 곳만은 멈추지 않았습니다」"}


def sec(t):
    h, m, s = t.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)


def tc(s):
    s = max(s, 0); return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def main():
    out = sys.argv[1]
    tmp = tempfile.mkdtemp(); parts = []
    for k, sh in enumerate(spec["shorts"], 1):
        a, b = float(sh["start"]), float(sh["end"])
        src = os.path.join(SHORTS, f"{spec['prefix']}-short-{sh['id']}-JP.mp4")
        lines = [f"Dialogue: 0,{tc(0)},{tc(b - a + 1.2)},T,,0,0,0,,[쇼츠 {k}] {KO_TITLE[sh['id']]}"]
        for l, kl in zip(ev, ko["lines"]):
            p = l.split(",", 9); s, e = sec(p[1]), sec(p[2])
            if e <= a or s >= b or p[3] in spec.get("skip_styles", []):
                continue
            spk = ko["speakers"].get(p[3], p[3])
            text = kl if isinstance(kl, str) else kl.get("ko", "")
            lines.append(f"Dialogue: 0,{tc(s - a)},{tc(min(e, b) - a)},K,,0,0,0,,[{spk}] {text}")
        ass = os.path.join(tmp, f"{k}.ass")
        open(ass, "w", encoding="utf-8").write(
            "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: T,Noto Sans CJK KR,46,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,3,8,0,8,40,40,60,1\n"
            "Style: K,Noto Sans CJK KR,48,&H0000F0FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,4,2,8,50,50,1080,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(lines) + "\n")
        p = os.path.join(tmp, f"{k}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"ass={ass},scale=540:960", "-c:v", "libx264", "-crf", "24",
                        "-c:a", "aac", "-b:a", "128k", p], check=True)
        parts.append(p)
    lst = os.path.join(tmp, "l.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    print("저장:", out)


if __name__ == "__main__":
    main()
