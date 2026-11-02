#!/usr/bin/env python3
"""『明日から来なくていい』 화면 속 일본어 글자 합성(규격 제7장 6, 로컬·무과금) — ja_text_overlay.py 방식의 정지 컷판.

생성 키프레임은 무지(글자 없음)로 만들었고, 실제 일본어는 실글꼴로 평면 캔버스에 그린 뒤 면의 네 모서리(키프레임 1344x768 좌표)에
원근 변형해 얹는다. 종이·명함 = 곱하기(종이 결·조명 유지), 화면 = 그대로 덮기. 대상 6컷은 모두 정지 푸시인 컷이라 키프레임에 합성하면
교체 클립(build_ashita_overrides.py)에 그대로 반영된다(H2는 S19b 재사용이라 함께 반영).
회사명은 가상(고니감독님 확정 2026-10-11): 朝凪テクノロジー / 天城都市開発.
출력: assets/portraits/ashita-ja/<id>-1.png → productions/ashita-kara-ja/kf_select.json 에서 지정
사용법: python3 scripts/ashita_ja_overlay.py
"""
import json
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
F = lambda n: os.path.join(ROOT, "scripts", "fonts", n)
MIN_B, MIN_R, GOTH = F("ZenOldMincho-Bold.ttf"), F("ZenOldMincho-Regular.ttf"), F("ZenMaruGothic-Black.ttf")
SRC = os.path.join(ROOT, "assets", "portraits", "ashita-kara-keyframes")
OUT = os.path.join(ROOT, "assets", "portraits", "ashita-ja")
SEL = os.path.join(ROOT, "productions", "ashita-kara-ja", "kf_select.json")
INK = (34, 30, 36)


def coeffs(dst, w, h):
    """출력 좌표(dst 네 점) → 캔버스 좌표(0,0)-(w,h) 원근 계수(PIL PERSPECTIVE)."""
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def place(base, layer, quad, mode):
    """layer(RGBA 평면 캔버스)를 quad에 원근 변형해 base(RGB)에 합성."""
    w, h = layer.size
    warped = layer.transform(base.size, Image.PERSPECTIVE, coeffs(quad, w, h), Image.BICUBIC)
    warped = warped.filter(ImageFilter.GaussianBlur(0.6))          # 카메라 초점·해상도에 맞춰 살짝 무르게
    rgb, a = warped.convert("RGB"), warped.split()[3]
    if mode == "multiply":
        mixed = ImageChops.multiply(base, rgb)
        return Image.composite(mixed, base, a)
    return Image.composite(rgb, base, a)


def text(d, xy, s, font, fill, anchor="la"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def paper(w, h):
    return Image.new("RGBA", (w, h), (255, 255, 255, 0))


def s06a(im):  # 결재 서류 — 손 아래 빈 영역(종이 아래쪽 40%)에만 글자
    L = paper(1000, 1400); d = ImageDraw.Draw(L)
    text(d, (500, 820), "補助金交付申請書", ImageFont.truetype(MIN_B, 92), INK + (235,), "mm")
    f = ImageFont.truetype(MIN_R, 40)
    for i, s in enumerate(["件名　変電設備更新工事", "申請者　朝凪テクノロジー株式会社",
                           "申請額　金参億円也", "担当　森 美咲"]):
        text(d, (150, 960 + i * 70), s, f, INK + (215,))
    d.rectangle((150, 1260, 850, 1262), fill=INK + (150,))
    return place(im, L, [(186, 285), (610, 165), (840, 600), (392, 752)], "multiply")


def s09b(im):  # 변경 이력 표 — 머리줄을 덮어 실제 항목명, 노란 두 줄에 변경 내용
    L = Image.new("RGBA", (1440, 776), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    g = ImageFont.truetype(GOTH, 22); gb = ImageFont.truetype(GOTH, 24)
    d.rectangle((0, 0, 1440, 22), fill=(220, 224, 228, 255))
    text(d, (10, 2), "変更履歴 ― 継電器 型番 変更　（朝凪テクノロジー 変電設備更新工事）", g, (40, 44, 52, 255))
    d.rectangle((0, 22, 1440, 46), fill=(206, 212, 218, 255))
    for x, s in [(14, "No."), (90, "機器"), (420, "変更前"), (640, "変更後"), (860, "理由"), (1120, "承認")]:
        text(d, (x, 24), s, g, (30, 34, 40, 255))
    for y, row in [(298, ["12", "保護継電器", "OCR-500A", "OCR-300B", "コスト削減", "森"]),
                   (428, ["13", "サージ保護装置", "SPD-Ⅱ", "SPD-Ⅲ", "コスト削減", "森"])]:
        for x, s in zip([14, 90, 420, 640, 860, 1120], row):
            text(d, (x, y), s, gb, (120, 20, 20, 255))
    return place(im, L, [(316, 276), (1033, 276), (1033, 664), (316, 664)], "over")


def s19b(im):  # 경고 화면 — 흰 패널 안쪽
    L = Image.new("RGBA", (800, 500), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    text(d, (400, 200), "アクセス拒否", ImageFont.truetype(GOTH, 118), (196, 20, 28, 255), "mm")
    text(d, (400, 360), "使用許諾 失効 ― 認証者：佐藤 誠", ImageFont.truetype(GOTH, 46), (40, 40, 44, 255), "mm")
    return place(im, L, [(624, 288), (742, 288), (742, 360), (624, 360)], "over")


def s26b(im):  # 명함 — 떨어지는 카드(긴 변 = 글자 방향)
    L = paper(910, 550); d = ImageDraw.Draw(L)
    text(d, (80, 90), "株式会社 佐藤電設技術研究所", ImageFont.truetype(MIN_R, 44), INK + (230,))
    text(d, (455, 290), "佐藤　誠", ImageFont.truetype(MIN_B, 120), INK + (240,), "mm")
    text(d, (455, 400), "代表取締役　第一種電気主任技術者", ImageFont.truetype(MIN_R, 38), INK + (220,), "mm")
    return place(im, L, [(615, 305), (780, 420), (720, 503), (553, 385)], "multiply")


def s27a(im):  # 주가 그래프 — 화면 위 제목, 아래 시간축
    L = Image.new("RGBA", (1100, 700), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rectangle((0, 0, 1100, 62), fill=(8, 22, 36, 255))
    text(d, (20, 10), "朝凪テクノロジー（株）　株価", ImageFont.truetype(GOTH, 40), (225, 240, 245, 255))
    text(d, (1080, 10), "▼ 68.4%", ImageFont.truetype(GOTH, 44), (255, 70, 70, 255), "ra")
    d.rectangle((0, 650, 1100, 700), fill=(8, 22, 36, 255))
    for i, s in enumerate(["9:00", "10:00", "11:00", "13:00", "14:00", "15:00"]):
        text(d, (40 + i * 200, 660), s, ImageFont.truetype(GOTH, 28), (150, 200, 215, 255))
    return place(im, L, [(760, 432), (1200, 414), (1205, 692), (762, 692)], "over")


def s27d(im):  # 손해배상 청구서 — 종이 방향(위 = 화면 오른쪽 위)
    L = paper(1000, 1400); d = ImageDraw.Draw(L)
    text(d, (500, 200), "損害賠償請求書", ImageFont.truetype(MIN_B, 110), INK + (240,), "mm")
    f = ImageFont.truetype(MIN_R, 44)
    text(d, (110, 380), "朝凪テクノロジー株式会社　御中", f, INK + (225,))
    text(d, (500, 560), "請求金額　金壱百億円也", ImageFont.truetype(MIN_B, 70), INK + (235,), "mm")
    for i, s in enumerate(["一、補助金の不正請求に係る返還", "一、保護装置等級の無断変更による損害",
                           "一、主任技術者不在の試運転に係る損害"]):
        text(d, (130, 720 + i * 80), s, f, INK + (215,))
    text(d, (870, 1180), "天城都市開発株式会社", ImageFont.truetype(MIN_R, 46), INK + (225,), "ra")
    return place(im, L, [(810, 140), (1188, 298), (800, 668), (387, 445)], "multiply")


# 합성 원본(검수 채택 키프레임) — 재실행해도 두 번 겹쳐 그리지 않도록 고정
SOURCE = {"S06a": "assets/portraits/ashita-kf-b/S06a-1.png", "S09b": "assets/portraits/ashita-kf-r1/S09b-2.png",
          "S19b": "assets/portraits/ashita-kf-r1/S19b-2.png", "S26b": "assets/portraits/ashita-kf-b/S26b-1.png",
          "S27a": "assets/portraits/ashita-kf-b/S27a-1.png", "S27d": "assets/portraits/ashita-kf-r1/S27d-1.png"}
JOBS = {"S06a": s06a, "S09b": s09b, "S19b": s19b, "S26b": s26b, "S27a": s27a, "S27d": s27d}


def main():
    os.makedirs(OUT, exist_ok=True)
    sel = json.load(open(SEL, encoding="utf-8"))
    for sid, fn in JOBS.items():
        src = SOURCE[sid]
        im = Image.open(os.path.join(ROOT, src)).convert("RGB")
        out = os.path.join(OUT, f"{sid}-1.png")
        fn(im).save(out)
        sel[sid] = f"assets/portraits/ashita-ja/{sid}-1.png"
        print(sid, "←", src)
    json.dump(sel, open(SEL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
