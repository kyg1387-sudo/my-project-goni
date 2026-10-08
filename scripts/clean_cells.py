#!/usr/bin/env python3
"""시트 셀 정리(무과금, 제7장 5·제2장 1): 셀 가장자리의 흰/검은 띠와 하단 라벨 글자 띠를 잘라낸다.
라벨 글자가 든 셀을 참조하면 키프레임에 글자가 새어 들어갈 수 있어 PHASE 4 전에 정리한다. 원본은 같은 폴더 _v1/에 보관.
사용법: clean_cells.py [--label 0.14] <png>...   (--label: 하단 라벨 띠 비율, 지정한 뒤의 파일에만 적용)"""
import os, shutil, sys
import numpy as np
from PIL import Image


def bands(a, axis):
    m = a.mean(axis=(axis, 2)); s = a.std(axis=(axis, 2))
    flat = ((m < 14) | (m > 225)) & (s < 8)
    n = len(flat); lo = 0
    while lo < n // 3 and flat[lo]:
        lo += 1
    hi = n
    while hi > n * 2 // 3 and flat[hi - 1]:
        hi -= 1
    return lo, hi


def clean(p, label=0.0):
    im = Image.open(p).convert("RGB"); W, H = im.size; a = np.asarray(im).astype(float)
    t, b = bands(a, 1); l, r = bands(a, 0)
    if label:
        b = min(b, int(H * (1 - label)))
    if t < 2 and H - b < 2 and l < 2 and W - r < 2:
        return False
    d = os.path.join(os.path.dirname(p), "_v1"); os.makedirs(d, exist_ok=True)
    if not os.path.exists(os.path.join(d, os.path.basename(p))):
        shutil.copy(p, os.path.join(d, os.path.basename(p)))
    im.crop((l, t, r, b)).save(p)
    print(f"{os.path.basename(p)}: 상{t} 하{H - b} 좌{l} 우{W - r} → {r - l}x{b - t}")
    return True


if __name__ == "__main__":
    label = 0.0
    args = sys.argv[1:]
    while args:
        x = args.pop(0)
        if x == "--label":
            label = float(args.pop(0)); continue
        clean(x, label)
