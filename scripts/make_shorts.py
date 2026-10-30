#!/usr/bin/env python3
"""본편 완성본 → 세로 쇼츠(1080x1920, EP3 형식): 흐린 배경 + 위 훅 제목 + 가운데 16:9 영상(원 자막 영역은 잘라냄)
+ 아래 큰 일본어 자막(원 .ass 타이밍 재사용) + 끝 「続きは本編で」 1.2초. 무과금, 로컬.

사용법: make_shorts.py <본편.mp4(자막 입힘, 아웃트로 전)> <subs.ass> <spec.json> <out_dir>
spec: {"shorts":[{"id":"1-letter","start":88.9,"end":112.3,"title":"…\\N…"}]}
선택 키: "keep"(원 화면 위쪽 사용 비율, 기본 0.80 — 2줄 자막이 80% 선에 걸리면 0.78), "skip_styles"(쇼츠 자막에서 뺄
원 스타일 — 화면에 이미 구워진 강조 자막과 겹칠 때), "sub_font"(자막 글꼴, 기본 IPAGothic)
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


PUNCT = "。、…』」？！?!"
HANG = "…。、』」？！?!—"


def _kind(c):
    if "\u3040" <= c <= "\u309f":
        return "h"
    if "\u30a0" <= c <= "\u30ff" or c == "ー":
        return "k"
    if "\u4e00" <= c <= "\u9fff" or c in "々〆":
        return "j"
    return "o"


def wrap(text, limit=13, with_cost=False):
    """세로 화면용 줄바꿈(제13장 4, 휴대폰): 한 줄 최대 13자(줄 끝 구두점은 매달기 — 글자 수에서 뺌), 최대 3줄.
    동적 계획법으로 문장 전체를 나눈다 — 끊는 자리 비용: 구두점 뒤 0 < 조사 뒤 1 < 글자 종류 경계(가나→한자·가타카나) 3 < 낱말 중간 30.
    줄 수가 적을수록, 비용이 낮을수록, 줄 길이가 고를수록 좋다. 줄머리 구두점 금지(앞 줄 끝에 매단다).
    (hikikomori 쇼츠 실증: 13자 강제 절단이 「ゴ/ミ」「聞か/れた」처럼 낱말 중간을 자름, 반각 공백이 글자 수에 들어감)"""
    t = re.sub(r"[ 　]", "", text.replace("\\N", "")).strip()
    n = len(t)

    def vis(a, b):  # 줄 끝 매단 구두점은 폭에서 뺀다
        while b > a and t[b - 1] in HANG:
            b -= 1
        return b - a

    def cost(k):  # t[:k] 뒤에서 끊는 비용
        if k >= n:
            return 0
        if t[k] in HANG:
            return 99  # 줄머리 구두점
        c, d = t[k - 1], t[k]
        if c in PUNCT:
            return 0
        if c in "がでにをはのともへやか" and _kind(d) != "h":
            return 1
        if c in "がでにをはのともへ":
            return 2
        if _kind(c) != _kind(d) and not (_kind(c) == "j" and _kind(d) == "h"):  # 한자+오쿠리가나는 붙임
            return 3
        return 30
    best = {0: (0, 0, 0, [])}
    for k in range(1, n + 1):
        cands = []
        for a in range(max(0, k - limit - 3), k):
            if a not in best or vis(a, k) > limit or vis(a, k) == 0:
                continue
            L, C, V, cuts = best[a]
            cands.append((L + 1, C + cost(k), V + (limit - vis(a, k)) ** 2, cuts + [k]))
        if cands:
            best[k] = min(cands)
    L, C, _, cuts = best[n]
    out, a = [], 0
    for k in cuts:
        out.append(t[a:k]); a = k
    res = "\\N".join(out)
    return (res, C + (100 if L > 3 else 0)) if with_cost else res


def split_events(s, e, text):
    """3줄 안에서 낱말 중간을 끊어야 하는 긴 줄은 가운데에 가까운 구두점에서 두 이벤트로 나눠 글자 수 비례로 시간을 나눈다(제15장 21)."""
    w, c = wrap(text, with_cost=True)
    t = re.sub(r"[ 　]", "", text.replace("\\N", ""))
    if c < 30:
        return [(s, e, w)]
    pos = [k + 1 for k, ch in enumerate(t[:-1]) if ch in "。、？！?!…" and t[k + 1] not in HANG]
    if not pos:
        return [(s, e, w)]
    k = min(pos, key=lambda x: abs(x - len(t) / 2))
    m = s + (e - s) * k / len(t)
    return split_events(s, m, t[:k]) + split_events(m, e, t[k:])


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
Style: Sub,IPAGothic,62,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,8,70,70,1250,1
Style: Cap,Zen Old Mincho,62,&H00C4F3FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,8,70,70,1250,1
Style: End,Zen Old Mincho,80,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    src, ass_path, spec_path, out_dir = sys.argv[1:5]
    os.makedirs(out_dir, exist_ok=True)
    ev = events(ass_path)
    spec = json.load(open(spec_path, encoding="utf-8"))
    keep = float(spec.get("keep", 0.80))
    skip = set(spec.get("skip_styles", []))
    head = HEAD.replace("Style: Sub,IPAGothic", f"Style: Sub,{spec.get('sub_font', 'IPAGothic')}")
    for sh in spec["shorts"]:
        assert all(len(x) <= 13 for x in sh["title"].split("\\N")), f"쇼츠 제목 한 줄 13자 초과(제13장 4): {sh['title']}"
        a, b = float(sh["start"]), float(sh["end"])
        dur = b - a
        tail = 1.2
        lines = [f"Dialogue: 0,{s2t(0)},{s2t(dur + tail)},Title,,0,0,0,,{sh['title']}"]
        for s, e, style, text in ev:
            if e <= a or s >= b or style in skip:
                continue
            st = "Cap" if style == "Caption" else "Sub"
            for s1, e1, w in split_events(s, min(e, b), text):
                lines.append(f"Dialogue: 0,{s2t(s1 - a)},{s2t(e1 - a)},{st},,0,0,0,,{w}")
        lines.append(f"Dialogue: 0,{s2t(dur)},{s2t(dur + tail)},End,,0,0,0,,{sh.get('end_text', '続きは本編で')}")
        sub = os.path.join(out_dir, f"_{sh['id']}.ass")
        open(sub, "w", encoding="utf-8").write(head + "\n".join(lines) + "\n")
        out = os.path.join(out_dir, f"{spec['prefix']}-short-{sh['id']}-JP.mp4")
        # 원 자막(하단)을 피해 위 80%만 쓰고(흐린 배경도 같은 영역 — 배경에 흐린 자막 줄이 비치지 않게), 흐린 배경 위 가운데(위쪽 약간)에 놓는다
        fc = (f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={tail},split[s1][s2];"
              f"[s1]crop=iw:ih*{keep}:0:0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.12[bg];"
              f"[s2]crop=iw:ih*{keep}:0:0,scale=1080:-2[fg];"
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
