#!/usr/bin/env python3
"""50엔 동전 고증 로컬 보정(제19장 6·9 ⑦) — 생성기가 가운데 구멍 없는 큰 「50」 동전만 그려서(4회) 동전마다 각인을 얕은 심도처럼 흐리고
가운데 둥근 구멍(손바닥 피부가 비침 + 안쪽 그림자)을 그린다. 원본은 assets/portraits/bento-keyframes/_v1/에 보관.
사용법: python3 productions/bento-ja/coin_fix.py
"""
import os, shutil
import cv2, numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
KF = os.path.join(REPO, "assets", "portraits", "bento-keyframes")
COINS = {  # 컷: [(cx, cy, ax, ay, 각도)] 뒤 → 앞 순서
    "S02c": [(1095, 1085, 92, 85, 0), (1422, 930, 108, 88, -10), (1268, 1062, 110, 90, 0), (1462, 1157, 116, 90, -5), (1225, 1268, 122, 102, 0)],
    "S08f": [(1240, 770, 86, 72, -8), (1395, 853, 88, 75, -8), (1275, 993, 96, 85, -5), (1468, 1010, 96, 82, -5), (1380, 1175, 108, 92, -5)],
}


PALM = {"S02c": (1700, 820), "S08f": (1150, 600)}
OLD_HOLES = {"S08f": [(1237, 717), (1388, 795), (1270, 923), (1442, 948), (1376, 1107)]}  # 생성기가 가장자리에 뚫은 구멍


def fix(img, coins, old=(), palm_xy=None):
    out = img.copy()
    palm = np.median(img[palm_xy[1] - 10:palm_xy[1] + 10, palm_xy[0] - 10:palm_xy[0] + 10].reshape(-1, 3), axis=0)
    if old:
        m = np.zeros(img.shape[:2], np.uint8)
        for x, y in old:
            cv2.circle(m, (x, y), 11, 255, -1)
        out = cv2.inpaint(out, m, 6, cv2.INPAINT_TELEA)
    for cx, cy, ax, ay, ang in coins:
        m = np.zeros(img.shape[:2], np.uint8)
        cv2.ellipse(m, (cx, cy), (int(ax * 0.86), int(ay * 0.86)), ang, 0, 360, 255, -1)
        mf = cv2.GaussianBlur(m, (0, 0), 4).astype(np.float32)[..., None] / 255
        blur = cv2.GaussianBlur(out, (0, 0), max(ax, ay) / 9)
        silver = np.full_like(out, out[m > 0].reshape(-1, 3).mean(axis=0).astype(np.uint8))
        face = cv2.addWeighted(blur, 0.75, silver, 0.25, 0)
        out = (out * (1 - mf) + face * mf).astype(np.uint8)
        # 가운데 구멍: 동전 아래 손바닥 피부색 + 위쪽 안쪽 그림자
        skin = img[min(img.shape[0] - 1, cy + int(ay * 1.35)), cx].astype(int)
        if cv2.cvtColor(np.uint8([[skin]]), cv2.COLOR_BGR2HSV)[0, 0, 1] < 45:  # 아래가 다른 동전(은색)이면 손바닥 기준점 색
            skin = palm.astype(int)
        hx, hy = int(ax * 0.24), int(ay * 0.24)
        cv2.ellipse(out, (cx, cy), (hx, hy), ang, 0, 360, tuple(int(v) for v in skin), -1, cv2.LINE_AA)
        cv2.ellipse(out, (cx, cy - 2), (hx, hy), ang, 200, 340, tuple(int(v * 0.55) for v in skin), 3, cv2.LINE_AA)
        cv2.ellipse(out, (cx, cy), (hx + 2, hy + 2), ang, 0, 360, (205, 205, 210), 2, cv2.LINE_AA)
    return out


def main():
    os.makedirs(os.path.join(KF, "_v1"), exist_ok=True)
    for c, coins in COINS.items():
        p = os.path.join(KF, f"{c}-1.png"); bak = os.path.join(KF, "_v1", f"{c}-1.png")
        if not os.path.exists(bak):
            shutil.copy(p, bak)
        cv2.imwrite(p, fix(cv2.imread(bak), coins, OLD_HOLES.get(c, ()), PALM[c]))
        print("보정", c)


if __name__ == "__main__":
    main()
