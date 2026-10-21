#!/usr/bin/env python3
"""bento 한국어 자막 검수판(제7장 12·제10장 5·제15장 14·26) — 일본어 자막(구워짐) 위에 [화자] 한국어 번역을 얹는다.
대본 00_script_ja.md의 「일본어」 → 한국어 줄을 subs/bento.ass 이벤트에 일본어 본문 대조로 묶는다(순번 아님 — 제15장 26).
사용법: python3 productions/bento-ja/make_ko_review.py <입력.mp4> <출력.mp4> [시작초 끝초]
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
KO_NAME = {"Narration": "내레이션", "Shuzo": "슈조", "Sumie": "스미에", "TakumiBoy": "타쿠미(소년)", "Takumi": "타쿠미",
           "Mio": "미오", "Hina": "히나", "HookLine": "내레이션"}
norm = lambda s: re.sub(r"[\s、。，,！!？?「」『』…―ー\-・.\\N]", "", s.replace("\\N", ""))


def script_pairs():
    pairs, last = [], None
    for l in open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8"):
        m = re.search(r":「(.+)」\s*$", l.strip())
        if m:
            last = m.group(1); continue
        m = re.match(r"\s*→\s*(.+)", l)
        if m and last:
            pairs.append((norm(last), m.group(1).strip())); last = None
    return pairs


def t2s(t):
    h, m, s = t.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)


def s2t(x):
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def main(src, out, a=None, b=None):
    pairs = script_pairs()
    evs = []
    for l in open(os.path.join(REPO, "subs", "bento.ass"), encoding="utf-8"):
        if l.startswith("Dialogue:"):
            p = l.rstrip("\n").split(",", 9)
            if p[3] in ("Caption", "Title"):
                continue
            evs.append((t2s(p[1]), t2s(p[2]), p[3].replace("_c", ""), p[9]))
    ko, i, miss = [], 0, 0
    while i < len(evs):
        st, en, sty, txt = evs[i]
        acc, j = norm(txt), i
        cand = [k for k, (ja, _) in enumerate(pairs) if ja.startswith(acc)]
        if not cand:
            miss += 1; i += 1; continue
        k = cand[0]
        while acc != pairs[k][0] and j + 1 < len(evs) and pairs[k][0].startswith(acc + norm(evs[j + 1][3])):
            j += 1; acc += norm(evs[j][3])
        ko.append((st, evs[j][1], sty, pairs[k][1], max(e[3].count("\\N") + 1 for e in evs[i:j + 1])))
        i = j + 1
    head = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "", "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: KO,WenQuanYi Zen Hei,50,&H0000E6FF,&H0000E6FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,4,1,2,120,120,0,1",
            "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    off = a or 0.0
    for st, en, sty, k, n in ko:
        if a is not None and (en < a or st > b):
            continue
        head.append(f"Dialogue: 0,{s2t(max(0, st - off))},{s2t(en - off)},KO,,0,0,{150 + 86 * (n - 1)},,[{KO_NAME.get(sty, sty)}] {k}")
    ap = os.path.join(HERE, "PHASE6_검수", "ko.ass"); os.makedirs(os.path.dirname(ap), exist_ok=True)
    open(ap, "w", encoding="utf-8").write("\n".join(head) + "\n")
    cut = ["-ss", str(a), "-to", str(b)] if a is not None else []
    subprocess.run(["ffmpeg", "-y", "-v", "error", *cut, "-i", src, "-vf", f"ass={ap}", "-c:v", "libx264", "-crf", "21", "-preset", "veryfast",
                    "-c:a", "copy", out], check=True)
    print(out, f"한국어 {len(ko)}줄, 대조 실패 이벤트 {miss}")


if __name__ == "__main__":
    a = [float(x) for x in sys.argv[3:5]] if len(sys.argv) > 4 else [None, None]
    main(sys.argv[1], sys.argv[2], *a)
