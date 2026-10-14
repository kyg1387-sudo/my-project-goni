#!/usr/bin/env python3
"""PHASE 2 시트를 칸 단위 참조 이미지로 자르기 — 무과금, 로컬 (運転手).

3x3 인물 시트 → <id>-front·45·profile·full·back·side·expr1·expr2·expr3.png
2x2 장소 시트 → <id>-c1..c4.png (칸 아래 캡션 띠는 잘라냄)
흰 여백(거터)은 자동으로 다듬는다. 사용법: cut_sheet_cells.py <시트 폴더> <출력 폴더> <파일...>
"""
import os, sys
import numpy as np
from PIL import Image

NAMES3 = ["front", "45", "profile", "full", "back", "side", "expr1", "expr2", "expr3"]


def trim(im, thr=238):
    a = np.asarray(im.convert("L"))
    rows = np.where((a < thr).mean(axis=1) > 0.04)[0]
    cols = np.where((a < thr).mean(axis=0) > 0.04)[0]
    if len(rows) < 10 or len(cols) < 10:
        return im
    return im.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))


def gutters(a, axis, n):
    """흰 거터 위치를 찾아 n칸 경계 반환(못 찾으면 균등 분할)."""
    prof = (a > 238).mean(axis=axis)
    L = len(prof); bounds = [0]
    for k in range(1, n):
        c = L * k // n; w = L // (n * 6)
        seg = prof[c - w:c + w]
        bounds.append(c - w + int(np.argmax(seg)) if seg.max() > 0.85 else c)
    return bounds + [L]


def main():
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    for f in sys.argv[3:]:
        im = Image.open(os.path.join(src, f)).convert("RGB")
        a = np.asarray(im.convert("L"))
        base = f.rsplit("-1.png", 1)[0]
        n = 3 if "sheet" in base and not base.startswith("props") else 2
        xs, ys = gutters(a, 0, n), gutters(a, 1, n)
        for i in range(n):
            for j in range(n):
                c = im.crop((xs[j], ys[i], xs[j + 1], ys[i + 1]))
                if n == 2:  # 캡션 띠(칸 위·아래 흰 바탕+글자) 제거: 흰 비율이 높은 줄을 위·아래에서 걷어낸다
                    ca = np.asarray(c.convert("L"))
                    white = (ca > 225).mean(axis=1)
                    top, bot = 0, len(white)
                    while bot > top + 10 and white[bot - 1] > 0.35:
                        bot -= 1
                    while top < bot - 10 and white[top] > 0.35:
                        top += 1
                    c = c.crop((0, top, c.width, bot))
                c = trim(c)
                name = f"{base}-{NAMES3[i * 3 + j]}" if n == 3 else f"{base}-c{i * 2 + j + 1}"
                c.save(os.path.join(dst, name + ".png"))
        print(base, xs, ys)


if __name__ == "__main__":
    main()
