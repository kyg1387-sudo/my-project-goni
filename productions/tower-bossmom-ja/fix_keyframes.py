#!/usr/bin/env python3
"""타워맨션 PHASE 4 무료 보정 — B단계 원본(tower-kf-b)에서 인서트 크롭·벽 종이 가짜 글자 흐림을 적용해
최종 폴더(tower-keyframes)에 쓴다. 좌표는 1344x768 원본 기준의 절반(672x384 격자)으로 적고 2배 한다.
레터박스는 scripts/kf_letterbox_fix.py가 따로 처리한다(최종 폴더에서 실행).
"""
import os
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "assets", "portraits", "tower-kf-b")
SRC_R = os.path.join(REPO, "assets", "portraits", "tower-kf-b-r")  # 재생성분(있으면 우선)
DST = os.path.join(REPO, "assets", "portraits", "tower-keyframes")

# 인서트 크롭(16:9 박스, x0, y0, x1, y1) — 스펙의 ECU·인서트 구도로 좁힌다
CROPS = {
    "S07c": (140, 80, 460, 260),    # 안경 너머 두 눈
    "S14o": (0, 114, 480, 384),     # 앞줄 엄마 3명(4번째 인물 제외)
    "S06c": (340, 215, 580, 350),   # 버건디 가방·금 체인·뱅글
    "S07c2": (170, 215, 410, 350),  # 펜 끝·수첩
    "S14n": (360, 226, 640, 384),   # 통장을 내려놓는 손
    "S16i": (160, 249, 400, 384),   # 지팡이 손잡이를 쥔 손
    "S16i2": (186, 220, 426, 355),  # 체인 끈을 쥔 떨리는 손가락
    "S15a": (160, 110, 480, 290),   # 재생성분: 스탠드를 쥔 손(빈 마이크 집게·왼쪽 종이 제외)
    "S05c": (95, 63, 665, 384),     # 재생성분: 박수 치는 세 엄마(시트 일치) 중심
}
# 흐림 영역 — 키즈룸 복도 벽 게시물·작은 메모(가짜 글자). 배경 심도처럼 보이게 강하게 흐린다
BLURS = {
    "S03a": [(0, 80, 112, 188), (436, 148, 478, 198)],
    "S03b": [(20, 122, 68, 208)],
    "S03c": [(18, 122, 80, 204)],
    "S03d": [(0, 38, 108, 172), (428, 130, 466, 174)],
    "S03e2": [(0, 52, 118, 184), (450, 148, 482, 208)],
    "S18a": [(0, 44, 96, 184), (432, 148, 466, 184)],
}


def blur(im, box, r=7):
    x0, y0, x1, y1 = [2 * v for v in box]
    pad = 12
    reg = im.crop((x0 - pad, y0 - pad, x1 + pad, y1 + pad)).filter(ImageFilter.GaussianBlur(r))
    # 가장자리 이음새가 보이지 않게 둥근 마스크로 섞는다
    m = Image.new("L", reg.size, 0)
    m.paste(255, (pad, pad, reg.size[0] - pad, reg.size[1] - pad))
    m = m.filter(ImageFilter.GaussianBlur(pad / 2))
    im.paste(reg, (x0 - pad, y0 - pad), m)


def src(sid):
    r = os.path.join(SRC_R, f"{sid}-1.png")
    return r if sid in ("S15a", "S05c") else os.path.join(SRC, f"{sid}-1.png")


def main():
    for sid, box in CROPS.items():
        im = Image.open(src(sid)).convert("RGB")
        c = im.crop(tuple(2 * v for v in box))
        print(f"{sid}: 크롭 {c.size} → 1344x768 ({1344 / c.size[0]:.1f}배)")
        c.resize(im.size, Image.LANCZOS).save(os.path.join(DST, f"{sid}-1.png"))
    for sid, boxes in BLURS.items():
        im = Image.open(os.path.join(SRC, f"{sid}-1.png")).convert("RGB")
        for b in boxes:
            blur(im, b)
        im.save(os.path.join(DST, f"{sid}-1.png"))
        print(f"{sid}: 흐림 {len(boxes)}곳")


if __name__ == "__main__":
    main()
