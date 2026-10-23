#!/usr/bin/env python3
"""뺨에 이미 그려진 눈물 줄기(밝고 가는 반짝임)만 지운다(무료) — 눈물 흐름 컷은 키프레임 = 고인 눈물·마른 뺨, 흐름은 i2v(제19장 14·15).

박스 안에서 주변 피부보다 밝은 가는 획을 마스크로 잡아 cv2.inpaint(TELEA). 아래 눈꺼풀의 고인 눈물은 박스 밖에 두어 남긴다.
사용법: python3 scripts/kf_tear_inpaint.py 입력.png 출력.png x0,y0,x1,y1 [...]
"""
import sys
import cv2
import numpy as np


def clean(img, boxes, delta=14):
    out = img.copy()
    for x0, y0, x1, y1 in boxes:
        roi = out[y0:y1, x0:x1]
        g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY).astype(np.int16)
        base = cv2.medianBlur(g.astype(np.uint8), 31).astype(np.int16)
        m = ((g - base) > delta).astype(np.uint8) * 255
        m = cv2.dilate(m, np.ones((7, 7), np.uint8))
        out[y0:y1, x0:x1] = cv2.inpaint(roi, m, 6, cv2.INPAINT_TELEA)
    return out


if __name__ == "__main__":
    img = cv2.imread(sys.argv[1])
    boxes = [tuple(int(v) for v in b.split(",")) for b in sys.argv[3:]]
    cv2.imwrite(sys.argv[2], clean(img, boxes))
    print(sys.argv[2], len(boxes), "영역")
