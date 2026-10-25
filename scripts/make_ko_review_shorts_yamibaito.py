#!/usr/bin/env python3
"""『時給5万円の罠』 쇼츠 한국어 검수판(고니감독님 검수 전용, 업로드본 아님, 제10장 5) — make_ko_review_shorts_tsuki.py 구조.
쇼츠 5편을 이어 붙여 각 편 맨 위에 [번호·한국어 제목], 영상과 일본어 자막 사이에 [화자] 한국어 번역(노란 글씨)을 얹은 540x960.
번역은 대본(00_script_ja.md)의 「→ 한국어」를 일본어 본문 일치로 찾는다(제15장 26). 조각(_c)은 앞 줄 시간을 늘린다.
사용법: make_ko_review_shorts_beggar.py <출력.mp4>
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SHORTS = os.path.join(ROOT, "assets", "shorts", "yamibaito")
spec = json.load(open(os.path.join(ROOT, "productions/yamibaito-ja/shorts_spec.json"), encoding="utf-8"))
KO_TITLE = {"1-door": "「여기에 출구는 없다」 시급 5만 엔의 덫", "2-dm": "시급 5만 엔 구인, 조건은 세 가지뿐",
            "3-escape": "6일째 밤, 철문에서 도망쳤다", "4-110": "공중전화로 110번, 점장의 한마디", "5-mother": "어머니의 전화 「밥은 먹었니?」"}


def sec(t):
    h, m, s = t.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)


def tc(s):
    s = max(s, 0); return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def norm(t):
    return re.sub(r"[\s　]", "", t.replace("\\N", ""))


rows = []  # 본편 한국어 검수 자막(PHASE6_검수/ko.ass, make_ko_review.py 산출 — 줄 ID 대조 완료)을 그대로 쓴다
for l in open(os.path.join(ROOT, "out/yamibaito-ko.ass"), encoding="utf-8"):
    if l.startswith("Dialogue:"):
        f = l.split(",", 9); rows.append([sec(f[1]), sec(f[2]), f[9].strip()])


def main():
    out = sys.argv[1]
    tmp = tempfile.mkdtemp(); parts = []
    for k, sh in enumerate(spec["shorts"], 1):
        a, b = float(sh["start"]), float(sh["end"])
        src = os.path.join(SHORTS, f"{spec['prefix']}-short-{sh['id']}-JP.mp4")
        lines = [f"Dialogue: 0,{tc(0)},{tc(b - a + 1.2)},T,,0,0,0,,[쇼츠 {k}] {KO_TITLE[sh['id']]}"]
        for s, e, t in rows:
            if e <= a or s >= b:
                continue
            lines.append(f"Dialogue: 0,{tc(s - a)},{tc(min(e, b) - a)},K,,0,0,0,,{t}")
        ass = os.path.join(tmp, f"{k}.ass")
        open(ass, "w", encoding="utf-8").write(
            "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: T,WenQuanYi Zen Hei,46,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,3,8,0,8,40,40,40,1\n"
            "Style: K,WenQuanYi Zen Hei,46,&H0000F0FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,4,2,8,50,50,1060,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(lines) + "\n")
        p = os.path.join(tmp, f"{k}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"ass={ass},scale=540:960", "-c:v", "libx264", "-crf", "24",
                        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", p], check=True)
        parts.append(p)
    lst = os.path.join(tmp, "l.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    print("저장:", out)


if __name__ == "__main__":
    main()
