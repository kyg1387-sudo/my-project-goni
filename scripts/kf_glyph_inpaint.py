#!/usr/bin/env python3
"""밝은 종이·간판 위의 가짜 글자(어두운 획)만 찾아 인페인트로 지운다(무료, 제11장 2·10 — 작은 배경 글자용).

박스 안에서 주변보다 어두운 획 픽셀을 마스크로 잡아 cv2.inpaint(TELEA)로 메운다. 종이 모양·그림자는 유지된다.
사용법: python3 scripts/kf_glyph_inpaint.py 입력.png 출력.png x0,y0,x1,y1 [x0,y0,x1,y1 ...]
"""
import sys
import cv2
import numpy as np


def clean(img, boxes, k=21, delta=28):
    out = img.copy()
    for x0, y0, x1, y1 in boxes:
        roi = out[y0:y1, x0:x1]
        g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        bg = cv2.medianBlur(g, k if k % 2 else k + 1)
        mask = ((bg.astype(int) - g.astype(int)) > delta).astype(np.uint8) * 255
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)
        out[y0:y1, x0:x1] = cv2.inpaint(roi, mask, 5, cv2.INPAINT_TELEA)
    return out


if __name__ == "__main__":
    src, dst, *bx = sys.argv[1:]
    boxes = [tuple(int(v) for v in b.split(",")) for b in bx]
    cv2.imwrite(dst, clean(cv2.imread(src), boxes))
    print(f"{dst}: {len(boxes)}개 영역 정리")
