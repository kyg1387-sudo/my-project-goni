#!/usr/bin/env python3
"""키프레임 레터박스·필러박스 자동 크롭 (규격 제7장 5). 검은/흰 띠를 잘라 16:9로 중앙 크롭 후 원래 크기로 맞춘다.
원본은 같은 폴더 _v1/에 보관. 사용법: kf_letterbox_fix.py <png>... (띠가 없으면 건너뜀)"""
import os, shutil, sys
import numpy as np
from PIL import Image


def bands(a, axis):
    m = a.mean(axis=(axis, 2)); s = a.std(axis=(axis, 2))
    flat = ((m < 14) | (m > 242)) & (s < 6)
    n = len(flat); lo = 0
    while lo < n // 3 and flat[lo]:
        lo += 1
    hi = n
    while hi > n * 2 // 3 and flat[hi - 1]:
        hi -= 1
    return lo, hi


def fix(p):
    im = Image.open(p).convert("RGB"); W, H = im.size; a = np.asarray(im).astype(float)
    t, b = bands(a, 1); l, r = bands(a, 0)
    if t < 4 and H - b < 4 and l < 4 and W - r < 4:
        return False
    c = im.crop((l, t, r, b)); cw, ch = c.size
    if cw / ch > 16 / 9:
        nw = int(ch * 16 / 9); c = c.crop(((cw - nw) // 2, 0, (cw - nw) // 2 + nw, ch))
    else:
        nh = int(cw * 9 / 16); c = c.crop((0, (ch - nh) // 2, cw, (ch - nh) // 2 + nh))
    d = os.path.join(os.path.dirname(p), "_v1"); os.makedirs(d, exist_ok=True)
    shutil.copy(p, os.path.join(d, os.path.basename(p)))
    c.resize((W, H), Image.LANCZOS).save(p)
    print(f"{os.path.basename(p)}: 띠 상{t} 하{H - b} 좌{l} 우{W - r} → 크롭 {c.size}")
    return True


if __name__ == "__main__":
    for p in sys.argv[1:]:
        fix(p)
