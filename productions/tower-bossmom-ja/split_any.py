"""불규칙 배치 시트를 패널 단위로 자른다(흰 거터 기준, 라벨 글자 띠 제외). 사용: split_any.py <png> <out_dir> <prefix>"""
import sys, os
import numpy as np
from PIL import Image

def bands(prof, minlen):
    res, st = [], None
    for i, v in enumerate(prof):
        if v and st is None: st = i
        if not v and st is not None:
            if i - st >= minlen: res.append((st, i))
            st = None
    if st is not None and len(prof) - st >= minlen: res.append((st, len(prof)))
    return res

src, out, prefix = sys.argv[1:4]
im = Image.open(src).convert("RGB"); a = np.asarray(im).astype(int)
nonw = a.min(axis=2) < 230
os.makedirs(out, exist_ok=True)
k = 0
for (x0, x1) in bands(nonw.mean(axis=0) > 0.05, 120):
    for (y0, y1) in bands(nonw[:, x0:x1].mean(axis=1) > 0.5, 100):  # 라벨 글자 띠는 밀도가 낮아 제외
        sub = nonw[y0:y1, x0:x1]
        for (sx0, sx1) in bands(sub.mean(axis=0) > 0.5, 120):
            k += 1
            im.crop((x0 + sx0 + 2, y0 + 2, x0 + sx1 - 2, y1 - 2)).save(os.path.join(out, f"{prefix}-p{k}.png"))
            print(f"{prefix}-p{k}", (x0 + sx0, y0, x0 + sx1, y1))
