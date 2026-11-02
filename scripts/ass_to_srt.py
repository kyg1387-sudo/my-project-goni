#!/usr/bin/env python3
"""조립용 .ass → 유튜브 업로드용 .srt(검색 색인용). 지정 스타일(화면에 이미 구워진 제목·강조 자막)은 뺀다. 아웃트로 줄은 JSON으로 덧붙인다.
사용법: ass_to_srt.py <subs.ass> <out.srt> [--skip Caption,Title,HookLine] [--append outro.json(offset_s + lines[{start,end,text}])]"""
import json, re, sys


def t2s(t):
    h, m, s = t.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)


def srt_t(x):
    ms = int(round(x * 1000)); h, r = divmod(ms, 3600000); m, r = divmod(r, 60000); s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    a = sys.argv; src, out = a[1], a[2]
    skip = set(a[a.index("--skip") + 1].split(",")) if "--skip" in a else set()
    ev = []
    for l in open(src, encoding="utf-8"):
        if l.startswith("Dialogue:"):
            p = l.rstrip("\n").split(",", 9)
            if p[3] in skip: continue
            txt = re.sub(r"\{[^}]*\}", "", p[9]).replace("\\N", "\n").strip()
            if txt: ev.append((t2s(p[1]), t2s(p[2]), txt))
    if "--append" in a:
        o = json.load(open(a[a.index("--append") + 1], encoding="utf-8")); off = o.get("offset_s", 0)
        ev += [(off + x["start"], off + x["end"], x["text"]) for x in o["lines"]]
    ev.sort()
    with open(out, "w", encoding="utf-8") as f:
        for i, (s, e, t) in enumerate(ev, 1):
            f.write(f"{i}\n{srt_t(s)} --> {srt_t(e)}\n{t}\n\n")
    print(f"{out}: {len(ev)}줄")


if __name__ == "__main__":
    main()
