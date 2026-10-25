#!/usr/bin/env python3
"""『時給5万円の罠』 한국어 검수용 자막 영상(고니감독님 검수 전용, 업로드본 아님) — make_ko_review_tsuki.py 구조.
일본어 자막 이벤트마다 대본(00_script_ja.md)의 「→ 한국어」 번역을 [화자]와 함께 화면 위쪽 노란 글씨로 얹은 480p.
대응은 일본어 본문 일치로 찾는다(순번 대응 금지 — 제15장 26). 조각(<스타일>_c)은 앞 줄 번역의 표시 시간을 늘린다.
사용법: make_ko_review_yamibaito.py <완성본.mp4> <출력.mp4> [아웃트로 시작(초) — 생략 시 본편만]
"""
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = shutil.which("ffmpeg")
SPK = {"Narration": "내레이션", "Kenta": "켄타", "Yuto": "유토", "Otoko": "남자", "Tencho": "점장", "Haha": "어머니", "Keisatsu": "경찰관",
       "HookLine": "남자"}
src, out = sys.argv[1], sys.argv[2]
body = open(os.path.join(ROOT, "productions/yamibaito-ja/00_script_ja.md"), encoding="utf-8").read()
pairs = [(m.group(1), m.group(2).strip()) for m in re.finditer(r"「(.+?)」[^\n]*\n\s*→\s*(.+)", body)]
assert pairs, "대본에서 번역 줄을 찾지 못함"
pairs.append(("迷ったときは、警察相談専用電話、#9110へ。", "망설여질 때는, 경찰 상담 전용 전화 #9110으로."))  # NA65 자막은 가나 읽기 대신 「#9110へ」로 표기(음성은 가나)


def sec(t):
    h, m, s = t.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)


def tc(s):
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def norm(t):
    return re.sub(r"[\s　]", "", t.replace("\\N", ""))


rows, miss = [], []
for l in open(os.path.join(ROOT, "subs/yamibaito.ass"), encoding="utf-8"):
    if not l.startswith("Dialogue:"):
        continue
    f = l.split(",", 9); a, b, style, text = sec(f[1]), sec(f[2]), f[3], f[9].strip()
    if style in ("Caption", "Title"):
        continue
    if style.endswith("_c"):
        rows[-1][1] = b; continue
    ja = norm(text)
    ko = next((k for j, k in pairs if norm(j).startswith(ja) or ja.startswith(norm(j))), None)
    if ko is None:
        miss.append(text); ko = "（번역 없음）"
    rows.append([a, b, f"[{SPK.get(style, style)}] {ko}"])
assert not miss, f"번역 대응 실패 {len(miss)}줄: {miss[:3]}"
if len(sys.argv) > 3:  # 아웃트로 진행자 멘트(build_yamibaito_outro.py LINES의 번역, 시작 = out/yamibaito-outro.json host_start)
    import json
    o0 = float(sys.argv[3]); oj = json.load(open(os.path.join(ROOT, "out/yamibaito-outro.json")))
    OUTRO_KO = ["끝까지 봐 주셔서 감사합니다.", "여러분 주변에, 「너무 좋은 구인」을 보고 있는 분은 없으신가요?",
                "느끼신 점이 있으면 댓글로 알려 주세요.", "구독과 좋아요로, 다음 이야기에서 만나요."]
    hs = oj["host_start"] + [oj["total"] - 0.3]
    for i, k in enumerate(OUTRO_KO):
        rows.append([o0 + hs[i], o0 + hs[i + 1] - 0.1, f"[진행자] {k}"])
ass = os.path.join(ROOT, "out/yamibaito-ko.ass"); os.makedirs(os.path.dirname(ass), exist_ok=True)
with open(ass, "w", encoding="utf-8") as fp:
    fp.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n\n[V4+ Styles]\n"
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
             "Style: KO,WenQuanYi Zen Hei,50,&H0000F0FF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,3,12,0,8,120,120,40,1\n\n"
             "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    for a, b, t in rows:
        fp.write(f"Dialogue: 0,{tc(a)},{tc(b)},KO,,0,0,0,,{t}\n")
fd = os.environ.get("FONTSDIR", "/usr/share/fonts")
subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vf", f"ass={ass}:fontsdir={fd},scale=-2:480", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "27", "-c:a", "aac", "-b:a", "96k", out], check=True)
print("저장:", out, len(rows), "줄")
