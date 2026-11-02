#!/usr/bin/env python3
"""키프레임 작은 가짜 글자 무료 제거(규격 제7장 5) — 지정 영역을 얕은 심도처럼 흐리게(가장자리 페더링).
원본은 같은 폴더 _v1/에 보관(이미 있으면 덮어쓰지 않음). 영역 목록은 JSON {"<png>": [[x0,y0,x1,y1,반경], ...]}.
사용법: kf_glyph_blur.py <regions.json>  (같은 영역 재실행 시 두 번 흐려지므로 영역은 한 번만 적용)"""
import json, os, shutil, sys
from PIL import Image, ImageDraw, ImageFilter


def blur(p, boxes):
    im = Image.open(p).convert("RGB")
    d = os.path.join(os.path.dirname(p), "_v1"); os.makedirs(d, exist_ok=True)
    keep = os.path.join(d, os.path.basename(p))
    if not os.path.exists(keep):
        shutil.copy(p, keep)
    for x0, y0, x1, y1, r in boxes:
        b = im.filter(ImageFilter.GaussianBlur(r))
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rectangle((x0, y0, x1, y1), fill=255)
        im = Image.composite(b, im, m.filter(ImageFilter.GaussianBlur(max(3, r // 2))))
    im.save(p)
    print(f"{os.path.basename(p)}: {len(boxes)}곳 흐림")


if __name__ == "__main__":
    for p, boxes in json.load(open(sys.argv[1], encoding="utf-8")).items():
        if not p.startswith("_"):
            blur(p, boxes)
