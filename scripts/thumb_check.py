#!/usr/bin/env python3
"""썸네일 수치 검사 (제22장 13·14, 2026-11-07 상위 30선 대조 기준).

사용법: python3 scripts/thumb_check.py <이미지> [<이미지> ...]
기준(휴대폰 목록에서 묻히지 않게, 우리 10편 중앙값 → 30선 중앙값 근처로):
  밝기(평균 휘도) ≥ 115 · 어두운 면적(L<40) ≤ 25% · 흰+노랑 글자 면적 ≥ 10% (색 다양성 85는 참고 — 실사는 낮게 나옴)
  오른쪽 아래 재생 시간 자리(가로 80~100%·세로 85~100%)에 큰 글자 없음(경고만)
측정은 320x180 축소본에서 한다(30선 대조와 같은 방법).
"""
import sys

import numpy as np
from PIL import Image

TH = dict(L=115, dark=25.0, text=10.0, C=85)


def metrics(path):
    im = Image.open(path).convert("RGB").resize((320, 180))
    a = np.asarray(im).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    L = 0.299 * r + 0.587 * g + 0.114 * b
    hsv = np.asarray(im.convert("HSV")).astype(float)
    h, s = hsv[..., 0], hsv[..., 1]
    rg, yb = r - g, 0.5 * (r + g) - b
    C = np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    white = (L > 225) & (s < 40)
    yellow = (s > 140) & (L > 150) & (h > 25) & (h < 50)
    corner = (white | yellow)[153:, 256:].mean() * 100
    return dict(L=L.mean(), dark=(L < 40).mean() * 100, text=(white | yellow).mean() * 100, C=C, corner=corner)


def main():
    bad = 0
    for p in sys.argv[1:]:
        m = metrics(p)
        fails = []
        if m["L"] < TH["L"]:
            fails.append(f"밝기 {m['L']:.0f}<{TH['L']}")
        if m["dark"] > TH["dark"]:
            fails.append(f"어두운 면적 {m['dark']:.0f}%>{TH['dark']:.0f}%")
        if m["text"] < TH["text"]:
            fails.append(f"흰·노랑 글자 {m['text']:.1f}%<{TH['text']:.0f}%")
        warn = f" (경고: 재생 시간 자리 글자 {m['corner']:.0f}%)" if m["corner"] > 15 else ""
        if m["C"] < TH["C"]:   # 실사 사진은 색 다양성이 낮게 나온다(感動 30선 실사 상위 30~72) → 경고만
            warn += f" (참고: 색 다양성 {m['C']:.0f}<{TH['C']}, 실사면 무시 가능)"
        bad += bool(fails)
        print(f"{'FAIL' if fails else 'PASS'} {p} | 밝기 {m['L']:.0f} 어두움 {m['dark']:.0f}% 글자 {m['text']:.1f}% 색 {m['C']:.0f}"
              f"{' | ' + ' / '.join(fails) if fails else ''}{warn}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
