#!/usr/bin/env python3
"""키프레임 테두리(흰/검 레터박스·액자) 자동 제거 후 16:9 중앙 크롭·원해상도 복원.
사용법: python3 scripts/trim_keyframe_borders.py assets/portraits/ep3-keyframes [--min 8]
원본은 같은 폴더의 _uncropped/ 에 보관한다. 테두리가 없으면 손대지 않는다.
"""
import os
import sys

from PIL import Image, ImageOps

d = sys.argv[1]
min_px = int(sys.argv[2]) if len(sys.argv) > 2 else 8
os.makedirs(os.path.join(d, "_uncropped"), exist_ok=True)


def is_flat(line, tol=18):
    """픽셀 행/열이 거의 단색(흰 또는 검)인가."""
    px = list(line)
    m = sum(sum(p[:3]) / 3 for p in px) / len(px)
    if not (m < 40 or m > 215):
        return False
    return all(abs(sum(p[:3]) / 3 - m) < tol for p in px[::4])


for f in sorted(os.listdir(d)):
    if not f.endswith(".png"):
        continue
    path = os.path.join(d, f)
    im = Image.open(path).convert("RGB")
    W, H = im.size
    top = 0
    while top < H // 3 and is_flat([im.getpixel((x, top)) for x in range(0, W, 2)]):
        top += 1
    bot = H
    while bot > 2 * H // 3 and is_flat([im.getpixel((x, bot - 1)) for x in range(0, W, 2)]):
        bot -= 1
    left = 0
    while left < W // 3 and is_flat([im.getpixel((left, y)) for y in range(top, bot, 2)]):
        left += 1
    right = W
    while right > 2 * W // 3 and is_flat([im.getpixel((right - 1, y)) for y in range(top, bot, 2)]):
        right -= 1
    if top < min_px and (H - bot) < min_px and left < min_px and (W - right) < min_px:
        continue
    core = im.crop((left, top, right, bot))
    out = ImageOps.fit(core, (W, H), method=Image.LANCZOS, centering=(0.5, 0.5))
    im.save(os.path.join(d, "_uncropped", f))
    out.save(path)
    print(f"{f}: 테두리 제거 top={top} bottom={H - bot} left={left} right={W - right} → {W}x{H} 복원")
