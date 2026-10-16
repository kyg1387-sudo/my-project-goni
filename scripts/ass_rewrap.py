#!/usr/bin/env python3
"""휴대폰 기준 자막 줄바꿈 재적용(대본 8절: 1줄 20자 이내·2줄, 44자 초과 내레이션만 3줄). 이벤트 수·시각은 바꾸지 않는다(한국어 검수판 매핑 유지).
사용법: ass_rewrap.py <in.ass> <out.ass> [limit=20] [skip_styles=Title,Caption]"""
import math, re, sys

NOHEAD = "…—、。!?？！』」"


def split_best(text, n):
    """text를 n줄로: 등분 지점에 가장 가까운 구두점(없으면 조사) 뒤에서 자른다."""
    cands = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "、。…!?？！」』" and text[i + 1] not in NOHEAD]
    weak = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "がでにをはのとへも" and text[i + 1] not in NOHEAD]
    cuts, start = [], 0
    for k in range(1, n):
        target = round(len(text) * k / n)
        strong = [c for c in cands if start + 4 <= c <= len(text) - 4]
        soft = [c for c in weak if start + 4 <= c <= len(text) - 4]
        c = min(strong, key=lambda i: abs(i - target)) if strong else None
        if c is None or abs(c - target) > 5:          # 구두점이 멀면 조사 뒤에서 자른다
            pool = strong + soft
            c = min(pool, key=lambda i: abs(i - target)) if pool else target
        cuts.append(c); start = c
    parts, prev = [], 0
    for c in cuts + [len(text)]:
        parts.append(text[prev:c]); prev = c
    return [p for p in parts if p]


def rewrap(text, limit):
    plain = re.sub(r"\{[^}]*\}", "", text).replace("\\N", "")
    if plain != text and re.search(r"\{[^}]*\}", text):
        return text                                   # 태그 있는 줄은 손대지 않음
    lines = text.split("\\N")
    if max(len(x) for x in lines) <= limit + 2 and len(lines) <= 2:
        return text
    n = min(3, max(2, math.ceil(len(plain) / limit)))
    return "\\N".join(split_best(plain, n))


def main():
    src, out = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    skip = set((sys.argv[4] if len(sys.argv) > 4 else "Title,Caption").split(","))
    res, changed, mx = [], 0, 0
    for l in open(src, encoding="utf-8"):
        if l.startswith("Dialogue:"):
            p = l.rstrip("\n").split(",", 9)
            if p[3] not in skip:
                new = rewrap(p[9], limit)
                if new != p[9]:
                    changed += 1; p[9] = new
                mx = max(mx, max(len(x) for x in re.sub(r"\{[^}]*\}", "", p[9]).split("\\N")))
            l = ",".join(p) + "\n"
        res.append(l)
    open(out, "w", encoding="utf-8").write("".join(res))
    print(f"{out}: {changed}줄 재배치, 최장 줄 {mx}자")


if __name__ == "__main__":
    main()
