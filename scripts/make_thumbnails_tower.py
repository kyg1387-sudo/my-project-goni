#!/usr/bin/env python3
"""『タワマンのボスママ』 썸네일 시안 3종(1280x720). 무과금, 로컬 — 승인·합성 완료 키프레임만(인물 일관성).
글자 스타일·도구는 채널 공통(make_thumbnails_yanagi): 본체 → 1차 테두리 → 2차 테두리 + 그림자, 오른쪽 아래(재생 시간 자리)는 비움.
A 반전형: 오만한 레이카(S06b) → 바닥에 주저앉은 레이카(S17d) / B 진짜 주인형: 레이카(S16g) vs 오다기리(S16f) / C 통장형: 유미(S13d) + 스크린 쌍(S14e)
사용법: make_thumbnails_tower.py [out_dir]
"""
import os
import sys

from PIL import Image, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_thumbnails_yanagi as y  # noqa: E402

ROOT = y.ROOT
y.K = os.path.join(ROOT, "assets", "portraits", "tower-keyframes")
W, H = y.W, y.H


def face(sid, cx, cy=330, w=660, h=700):
    return y.kf(sid, (cx - w // 2, max(0, cy - h // 2), cx + w // 2, max(0, cy - h // 2) + h)).resize((560, 594), Image.LANCZOS)


def thumb_a():
    bg = Image.new("RGB", (W, H), (10, 8, 14))
    a = y.rim(y.tint(ImageEnhance.Contrast(face("S06b", 680, 360)).enhance(1.1), (150, 110, 30), 0.12), (255, 200, 80), "left", 110, 0.45)
    bg.paste(a, (0, 126), y.fade_mask(a.size, right=130))
    b = y.rim(y.tint(ImageEnhance.Contrast(face("S17d", 700, 360)).enhance(1.15), (20, 60, 140), 0.25), (255, 20, 20), "right", 110, 0.55)
    bg.paste(b, (W - 560, 126), y.fade_mask(b.size, left=130))
    y.tri_text(bg, (40, 18), "42階のボスママの正体は…", 80, y.YELLOW, y.BLOOD, 12, y.WHITE, 6)
    y.tag(bg, (40, 470), "総会で発覚")
    y.tri_text(bg, (40, 560), "ただの賃借人", 118, y.WHITE, y.BLACK, 14, y.SCARLET, 6, {3: y.RED, 4: y.RED, 5: y.RED})
    return bg


def thumb_b():
    bg = Image.new("RGB", (W, H), (8, 12, 22))
    a = y.tint(ImageEnhance.Contrast(face("S16g", 660, 380)).enhance(1.12), (20, 60, 140), 0.22)
    bg.paste(a, (0, 126), y.fade_mask(a.size, right=130))
    b = y.rim(y.tint(ImageEnhance.Contrast(face("S16f", 672, 330)).enhance(1.1), (150, 110, 30), 0.15), (255, 200, 80), "right", 120, 0.45)
    bg.paste(b, (W - 560, 126), y.fade_mask(b.size, left=130))
    y.tri_text(bg, (40, 18), "「42階の持ち主は、私だがね」", 76, y.YELLOW, y.BLOOD, 12, y.WHITE, 6)
    y.tri_text(bg, (40, 560), "本当のオーナー", 112, y.WHITE, y.BLACK, 14, y.SCARLET, 6, {5: y.RED, 6: y.RED})
    return bg


def thumb_c():
    bg = Image.new("RGB", (W, H), (10, 10, 14))
    scr = y.kf("S14e", (300, 260, 900, 660)).resize((700, 467), Image.LANCZOS)
    bg.paste(ImageEnhance.Brightness(scr).enhance(1.05), (W - 700, 140), y.fade_mask(scr.size, left=120, vert=40))
    a = y.rim(face("S13d", 672, 330), (255, 200, 80), "left", 100, 0.35)
    bg.paste(a, (0, 126), y.fade_mask(a.size, right=130))
    y.tri_text(bg, (40, 18), "「この通帳を、ご覧ください」", 76, y.YELLOW, y.BLOOD, 12, y.WHITE, 6)
    y.tri_text(bg, (40, 560), "27件の証拠", 120, y.WHITE, y.BLACK, 14, y.SCARLET, 6, {0: y.RED, 1: y.RED, 2: y.RED})
    return bg


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "productions", "tower-bossmom-ja", "thumbnails")
    os.makedirs(out, exist_ok=True)
    for name, fn in (("A-반전형", thumb_a), ("B-진짜주인형", thumb_b), ("C-통장형", thumb_c)):
        p = os.path.join(out, f"tower-thumb-{name}.jpg"); fn().save(p, quality=92); print(p)
