#!/usr/bin/env python3
"""『母が遺したビデオレター』 쇼츠 한국어 검수판(고니감독님 검수 전용, 업로드본 아님, 제10장 5) — make_ko_review_shorts_tsuki.py 구조.
쇼츠 4편을 이어 붙여 각 편 맨 위에 [번호·한국어 제목], 영상과 일본어 자막 사이에 [화자] 한국어 번역(노란 글씨)을 얹은 540x960.
번역은 대본(00_script_ja.md)의 「→ 한국어」를 일본어 본문 일치로 찾는다(제15장 26). 조각(_c)은 앞 줄 시간을 늘린다.
사용법: make_ko_review_shorts_aihaha.py <출력.mp4>
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SHORTS = os.path.join(ROOT, "assets", "shorts", "aihaha")
spec = json.load(open(os.path.join(ROOT, "productions/aihaha-ja/shorts.json"), encoding="utf-8"))
body = open(os.path.join(ROOT, "productions/aihaha-ja/00_script_ja.md"), encoding="utf-8").read()
pairs = [(m.group(1), m.group(2).strip()) for m in re.finditer(r"「(.+?)」[^\n]*\n\s*→\s*(.+)", body)]
SPK = {"Naration": "내레이션(유키코)", "Yukiko": "유키코", "Sawako": "사와코(어머니)", "AIHaha": "영상 속 어머니(AI)", "Tsuyoshi": "쓰요시(숙부)", "Yoriko": "요리코(숙모)", "Shota": "쇼타(사촌)", "Miyashita": "미야시타(형사)"}
KO_TITLE = {"1-mabataki": "돌아가신 엄마의 영상이 한 번도 눈을 깜빡이지 않는다", "2-ashiba": "엄마 영상 속 창밖에 있어야 할 비계가 없다",
            "3-ai": "「방금 『AI』라고 하셨죠」", "4-kigen": "상속 포기 기한은 「어제」였습니다"}


def sec(t):
    h, m, s = t.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)


def tc(s):
    s = max(s, 0); return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def norm(t):
    return re.sub(r"[\s　]", "", t.replace("\\N", ""))


rows = []
for l in open(os.path.join(ROOT, "subs/aihaha.ass"), encoding="utf-8"):
    if not l.startswith("Dialogue:"):
        continue
    f = l.split(",", 9); a, b, style, text = sec(f[1]), sec(f[2]), f[3], f[9].strip()
    if style.endswith("_c"):
        rows[-1][1] = b; continue
    ja = norm(text)
    ko = next((k for j, k in pairs if norm(j).startswith(ja) or ja.startswith(norm(j))), None)
    ko = ko or "（번역 없음）"
    rows.append([a, b, f"[{SPK.get(style, style)}] {ko}"])


def main():
    out = sys.argv[1]
    tmp = tempfile.mkdtemp(); parts = []
    shorts = spec["shorts"]
    if os.environ.get("AVATAR"):  # 3D 아바타 시험판 쇼츠 ③만(같은 구간·같은 자막)
        shorts = [dict(next(x for x in shorts if x["id"] == "3-touchaku"), id="3-touchaku-avatar")]
        KO_TITLE["3-touchaku-avatar"] = "[3D 아바타판] 은둔형 외톨이가 계약 자리에 나타났다"
    for k, sh in enumerate(shorts, 1):
        segs = [(float(x), float(y)) for x, y in (sh.get("segments") or [[sh["start"], sh["end"]]])]
        offs, acc = [], 0.0
        for x, y in segs:
            offs.append(acc); acc += y - x
        a, b = 0.0, acc  # 쇼츠 시간(구간 이어 붙임, make_shorts.py segments와 같은 계산)
        src = os.path.join(SHORTS, f"{spec['prefix']}-short-{sh['id']}-JP.mp4")
        lines = [f"Dialogue: 0,{tc(0)},{tc(b - a + 1.2)},T,,0,0,0,,[쇼츠 {k}] {KO_TITLE[sh['id']]}"]
        for s, e, t in rows:
            for (x, y), o in zip(segs, offs):
                s0, s1 = max(s, x), min(e, y)
                if s1 - s0 > 0.15:
                    lines.append(f"Dialogue: 0,{tc(s0 - x + o)},{tc(s1 - x + o)},K,,0,0,0,,{t}")
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
