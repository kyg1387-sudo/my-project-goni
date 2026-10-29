#!/usr/bin/env python3
"""『引きこもりの息子』 PHASE 2 승인 시트 → 셀 분할(무과금, 로컬). 행마다 칸 수가 달라도(健太郎 가운데 4칸, 사무실 v1 왼쪽 큰 칸) 흰 거터로 자른다.
출력: assets/portraits/hikikomori-cast/cells/<이름>.png — 키프레임 참조용(03_마스터에셋.md 사용 가능 셀만).
사용법: python3 productions/hikikomori-ja/split_cells.py
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
P = "assets/portraits/"
OUT = os.path.join(ROOT, P, "hikikomori-cast", "cells")


def bands(mask, min_len):
    out, st = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and st is None:
            st = i
        if not v and st is not None:
            if i - st >= min_len:
                out.append((st, i))
            st = None
    return out


def grid(path, by_col=False, thr=235, frac=0.985):
    """by_col=False: 행 → 행 안의 칸(인물 시트). by_col=True: 열 → 열 안의 칸(장소 시트는 열마다 칸 높이가 다르다). 결과는 [묶음][칸]."""
    im = Image.open(os.path.join(ROOT, path)).convert("RGB"); a = np.asarray(im).astype(int)
    white = a.min(axis=2) > thr
    if by_col:
        cols = bands(white.mean(axis=0) < frac, a.shape[1] // 12)
        return im, [[(x0, y0, x1, y1) for y0, y1 in bands(white[:, x0:x1].mean(axis=1) < frac, a.shape[0] // 8)] for x0, x1 in cols]
    rows = bands(white.mean(axis=1) < frac, a.shape[0] // 8)
    return im, [[(x0, y0, x1, y1) for x0, x1 in bands(white[y0:y1].mean(axis=0) < frac, a.shape[1] // 12)] for y0, y1 in rows]


# 시트: (경로, 행별 이름 목록) — 이름 None = 저장 안 함(금지 셀)
SHEETS = {
    "kentaro": (P + "hikikomori-cast-2/kentaro-sheet-v2-1.png", [["front0", "45", "profile"], ["full", "fullback", "side", "side2"], ["calm", "anger", "grief"]]),  # 하단: 평온·억누른 분노·참는 슬픔
    "daiki": (P + "hikikomori-cast-2/daiki-suit-sheet-1.png", [["front0", "45", "profile"], ["suitfull", "suitback", "suitside"], ["resolute", "cool", "smile"]]),
    "daikih": (P + "hikikomori-cast/daiki-hood-sheet-1.png", [["hood45x", "hood45", "hoodprofile"], ["hoodfull", "hoodback", "hoodback2"], [None, None, None]]),
    "yumiko": (P + "hikikomori-cast/yumiko-sheet-1.png", [["front0", "45", "profile"], ["full", "fullback", "fullback2"], ["calm", "worry", None]]),
    "seiji": (P + "hikikomori-cast-2/seiji-sheet-v2-1.png", [["front0", "45", "profile"], ["full", "fullback", "side"], ["smug", "sneer", "forced"]]),
    "ryosuke": (P + "hikikomori-cast-3/ryosuke-sheet-v3-1.png", [["front0", "45", "profile"], ["full", "fullback", "side"], ["cold", "aside", "shock"]]),
    "makabe": (P + "hikikomori-cast-2/makabe-sheet-v2-1.png", [["front0", "45", "profile"], ["full", "fullback", "side"], ["cold", "stern", None]]),
    "kaneda": (P + "hikikomori-cast/kaneda-sheet-1.png", [["front0", "45", "profile"], ["full", "fullback", "side"], ["focus", "concern", "smile"]]),
}
# 장소·소품 시트는 열 단위 이름(왼쪽 열 위→아래, 오른쪽 열 위→아래)
LOCS = {
    "loc-home": (P + "hikikomori-cast-2/loc-home-v2-1.png", [["living-day", "hall-night"], ["dining-night", "genkan"]]),
    "loc-room": (P + "hikikomori-cast-2/loc-daiki-room-v2-1.png", [["desk-night", "monitor-night"], ["corner-night", None]]),
    "loc-room1": (P + "hikikomori-cast/loc-daiki-room-1.png", [[None, None], [None, "bed-day"]]),
    "loc-factory": (P + "hikikomori-cast/loc-factory-1.png", [["floor-day", "floor-night"], ["lathe", "exterior"]]),
    "loc-office1": (P + "hikikomori-cast/loc-office-1.png", [["day-wide"], ["day-desk", None]]),
    "loc-office2": (P + "hikikomori-cast-2/loc-office-v2-1.png", [[None, "night-lamp"], [None, None]]),
    "loc-meeting": (P + "hikikomori-cast/loc-meeting-1.png", [["wide", "table"], ["door", "door-open"]]),
    "props": (P + "hikikomori-cast/props-sheet-1.png", [["passbook", "contract"], ["postit", "sukiyaki"], ["tablet", "photo"]]),
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for key, (path, names) in list(SHEETS.items()) + list(LOCS.items()):
        im, cells = grid(path, by_col=key in LOCS, frac=0.9 if key in LOCS else 0.985)
        shape = [len(r) for r in cells]; want = [len(r) for r in names]
        assert shape == want, f"{key}: 셀 배치 {shape} ≠ 기대 {want}"
        n = 0
        for row, nrow in zip(cells, names):
            for (x0, y0, x1, y1), nm in zip(row, nrow):
                if nm:
                    im.crop((x0 + 3, y0 + 3, x1 - 3, y1 - 3)).save(os.path.join(OUT, f"{key}-{nm}.png")); n += 1
        print(f"{key}: {shape} → {n}칸 저장")
