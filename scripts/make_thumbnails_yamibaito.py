#!/usr/bin/env python3
"""『時給5万円の罠』 썸네일 3종(무과금·로컬) — 고니감독님 첨부 참고 6장 형식(2026-10-22).
위쪽 1/3에 초대형 굵은 글자 1~2줄(노랑 그라데이션 + 검은 테 / 빨강 그라데이션 + 흰 테 + 검은 바깥 테 / 흰 글자 + 검은 테),
아래는 본편 인물 실사의 감정 정점(제13장 5 — 썸네일 인물 = 본편 인물). 오른쪽 아래(재생 시간)는 비운다.
그림: assets/portraits/bento-thumb2/<id>-N.png (2560x1440). 산출: 1280x720 JPG(2MB 이하) + 휴대폰 확인용 360px·168px.
사용법: python3 scripts/make_thumbnails_yamibaito.py [A B C A2 B2]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from make_thumbnails_ashita import GOTH, W, H  # noqa: E402
from make_thumbnails_yanagi_v2 import text_layer  # noqa: E402

SRC = os.path.join(ROOT, "assets", "portraits", "yamibaito-thumb")
OUT = os.path.join(ROOT, "assets", "thumbnails", "yamibaito")
YEL = ((255, 252, 170), (255, 222, 30), (255, 150, 0))
RED = ((255, 70, 60), (225, 10, 10), (150, 0, 0))

# 글자 조각: (글자, 색 종류) — y = 줄 위치(1920x1080 기준), size = 글자 크기(가로 폭에 맞춰 자동 축소)
VARIANTS = {
    # A(자극) 안대: 얼굴 오른쪽, 글자 왼쪽 2줄 — 「時給5万円」 노랑 / 「の罠」 빨강
    "A": dict(src="TA_mask-1", x=40, max_w=1000, lines=[(60, 250, [("時給5万円", "yel")]), (340, 250, [("の罠", "red")])]),
    # B 철문+赤色灯: 위 1줄 「消された」 흰+검은 테 / 「24歳」 빨강
    "B": dict(src="TB_door-2", x=None, max_w=1850, lines=[(24, 270, [("消された", "white"), ("24歳", "red")])]),
    # C 공중전화: 글자 왼쪽 2줄 「ここに」 흰 / 「出口はない」 빨강
    "C": dict(src="TC_phone-1", x=40, max_w=1000, lines=[(60, 230, [("ここに", "white")]), (320, 230, [("出口はない", "red")])]),
}


def seg(s, kind, size):
    if kind == "red":
        return text_layer(s, GOTH, size, None, (255, 255, 255), 16, gradient=RED, outer=(0, 0, 0), outer_w=7)
    if kind == "yel":
        return text_layer(s, GOTH, size, None, (0, 0, 0), 18, gradient=YEL, outer=(255, 255, 255), outer_w=0)
    return text_layer(s, GOTH, size, (255, 255, 255), (0, 0, 0), 18)


def line_layer(parts, size, max_w=W - 70):
    while True:
        lays = [seg(s, k, size) for s, k in parts]
        tw = sum(l.width for l in lays) - 40 * (len(lays) - 1)
        if tw <= max_w or size < 120:
            break
        size -= 6
    hh = max(l.height for l in lays)
    out = Image.new("RGBA", (tw, hh), (0, 0, 0, 0))
    x = 0
    for l in lays:
        out.alpha_composite(l, (x, (hh - l.height) // 2)); x += l.width - 40
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0)); sh.putalpha(out.getchannel("A").point(lambda a: int(a * 0.7)))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    full = Image.new("RGBA", (tw + 24, hh + 24), (0, 0, 0, 0))
    full.alpha_composite(sh, (18, 18)); full.alpha_composite(out, (0, 0))
    return full


def thumb(tag):
    v = VARIANTS[tag]
    img = Image.open(os.path.join(SRC, f"{v['src']}.png")).convert("RGB")
    if v.get("crop"):                                                 # 얼굴을 크게(휴대폰 목록에서 표정이 보이게)
        img = img.crop(v["crop"])
    if v.get("lift"):                                                 # 어두운 중간 톤만 들어 올림(검정 유지, 제11장 11)
        g = v["lift"]; img = img.point(lambda c: int(255 * (c / 255) ** (1 / g)))
    img = img.resize((W, H), Image.LANCZOS).convert("RGBA")
    shade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shade).rectangle([0, 0, W if v["x"] is None else 1150, 420 if v["x"] is None else 680], fill=120)        # 글자 자리만 살짝 어둡게(대비)
    shade = shade.filter(ImageFilter.GaussianBlur(90))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(shade)
    img.alpha_composite(dark)
    for y, size, parts in v["lines"]:
        lay = line_layer(parts, size, v["max_w"])
        img.alpha_composite(lay, (v["x"] if v["x"] is not None else (W - lay.width) // 2 + 6, y))
    return img.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    for tag in sys.argv[1:] or ["A", "B", "C"]:
        im = thumb(tag)
        p = os.path.join(OUT, f"yamibaito-thumb-{tag}-JP.jpg")
        im.resize((1280, 720), Image.LANCZOS).save(p, quality=92)
        assert os.path.getsize(p) < 2 * 1024 * 1024
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        im.resize((168, 95), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone168.png"))
        print("저장:", p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main()
