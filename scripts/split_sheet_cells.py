#!/usr/bin/env python3
"""시트 이미지를 흰 거터 기준으로 셀 단위로 자른다(무과금, 로컬). 라벨 띠(셀 아래 글자)는 잘라낸다.

사용법: python3 scripts/split_sheet_cells.py <sheet.png> <out_dir> <prefix> <rows> <cols> [name1,name2,...]
"""
import sys, os
import numpy as np
from PIL import Image

def bands(profile, thresh, min_len):
    out, start = [], None
    for i, v in enumerate(profile):
        if v and start is None: start = i
        if not v and start is not None:
            if i - start >= min_len: out.append((start, i))
            start = None
    if start is not None and len(profile) - start >= min_len: out.append((start, len(profile)))
    return out

def split(path, rows, cols):
    im = Image.open(path).convert("RGB"); a = np.asarray(im).astype(int)
    white = (a.min(axis=2) > 235)
    col_white = white.mean(axis=0) > 0.97
    row_white = white.mean(axis=1) > 0.97
    xs = bands(~col_white, 0, a.shape[1] // (cols * 3))
    ys = bands(~row_white, 0, a.shape[0] // (rows * 4))
    return im, xs, ys

if __name__ == "__main__":
    path, out, prefix, rows, cols = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    names = sys.argv[6].split(",") if len(sys.argv) > 6 else None
    im, xs, ys = split(path, rows, cols)
    # 라벨 띠처럼 얇은 행 밴드는 제외: 높이 상위 rows개만 사용
    ys = sorted(sorted(ys, key=lambda b: b[1] - b[0], reverse=True)[:rows])
    xs = sorted(sorted(xs, key=lambda b: b[1] - b[0], reverse=True)[:cols])
    assert len(xs) == cols and len(ys) == rows, (xs, ys)
    os.makedirs(out, exist_ok=True)
    k = 0
    for r, (y0, y1) in enumerate(ys):
        for c, (x0, x1) in enumerate(xs):
            name = names[k] if names else f"r{r+1}c{c+1}"
            im.crop((x0 + 2, y0 + 2, x1 - 2, y1 - 2)).save(os.path.join(out, f"{prefix}-{name}.png"))
            k += 1
    print(path, "->", k, "cells", [(x1 - x0, y1 - y0) for (x0, x1) in xs[:1] for (y0, y1) in ys[:1]])
