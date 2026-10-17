#!/usr/bin/env python3
"""『タワマンのボスママ』 썸네일 A/B/C 지침판(제0장 8, 1920x1080, 무과금·로컬) — make_thumbnails_tsuki.py 형식.
생성 그림: assets/portraits/thumb-tower-hd/towerhd{A,B,C}-N.png(2560x1440 일본 드라마 만화풍, 오른쪽 = 주인공 얼굴 크게).
글자는 왼쪽 위 흰 라벨 + 3줄 이내 그라데이션 글자 + 금테 붉은 배지(무릎 아래) + 검은 띠. 오른쪽 아래(재생 시간)는 비운다. 360px 축소본도 저장.
  A 【スカッと】 「荷物用エレベーターへ」と笑ったボスママの末路   — 통장을 든 유미 / 무릎 꿇은 레이카
  B 【泣ける】   「上の子専用」と締め出された娘、母の反撃       — 리코를 안은 유미 / 놀이방 유리문
  C 【スカッと】 「私は42階のオーナーよ！」本当の持ち主は…      — 오다기리 / 애원하는 레이카
사용법: python3 scripts/make_thumbnails_tower_hd.py [A번호 B번호 C번호]   (기본 1 1 1)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from make_thumbnails_ashita import GOTH, W, H, band, big, label, put  # noqa: E402
from make_thumbnails_yanagi_v2 import text_layer  # noqa: E402

SRC = os.path.join(ROOT, "assets", "portraits", "thumb-tower-hd")
OUT = os.path.join(ROOT, "productions", "tower-bossmom-ja", "thumbnails-hd")
FIRE = ((255, 236, 60), (255, 150, 20), (225, 30, 20))
YELLOW = ((255, 250, 150), (255, 225, 30), (250, 180, 0))
GOLD = ((255, 255, 190), (255, 225, 40), (255, 160, 0))

V = {
    "A": dict(tag="スカッとする話", rows=[("「荷物用エレベーターへ」と", 84, None, (255, 255, 255)), ("笑ったボスママの", 132, FIRE, None), ("末路", 200, YELLOW, None)],
              badge=("42階の正体、暴かれる", "積立金2,400万円"), badge_xy=(40, 800), band=None),
    "B": dict(tag="泣ける話", rows=[("「上の子専用」と", 104, None, (255, 255, 255)), ("締め出された娘", 140, FIRE, None), ("母の反撃", 180, YELLOW, None)],
              badge=("元経理の母、帳簿を開く", "消えた2,400万円"), badge_xy=(40, 800), band=None),
    "C": dict(tag="スカッとする話", rows=[("「私は42階の", 112, None, (255, 255, 255)), ("オーナーよ！」", 150, FIRE, None), ("本当の持ち主は…", 128, YELLOW, None)],
              badge=("ボスママの正体", "ただの賃借人"), badge_xy=(40, 800), band=None),
}


def compose(src_png, v):
    img = Image.open(src_png).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    shade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shade).rectangle([0, 0, 1000, 700], fill=140)   # 왼쪽 위 글자 자리만 어둡게(오른쪽 얼굴은 그대로)
    shade = shade.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(shade); img.alpha_composite(dark)
    img.alpha_composite(label(v["tag"], 64, (255, 255, 255, 255), (20, 20, 20)), (34, 26))
    y = 124
    for s, size, grad, fill in v["rows"]:
        lay = text_layer(s, GOTH, size, fill, (255, 255, 255) if grad else (0, 0, 0), 12,
                         gradient=grad, outer=(0, 0, 0) if grad else None, outer_w=9 if grad else 0)
        put(img, lay, 6, y)
        y += lay.height - 48
    if v["badge"]:
        b1 = label(v["badge"][0], 44, (175, 18, 18, 255), (255, 255, 255), pad=(26, 8))
        num = big(v["badge"][1], 88, gradient=GOLD, stroke_w=8, outer_w=6)
        box = Image.new("RGBA", (max(b1.width, num.width) + 44, b1.height + num.height + 4), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 28, fill=(255, 200, 40, 255))
        ImageDraw.Draw(box).rounded_rectangle([7, 7, box.width - 8, box.height - 8], 24, fill=(165, 14, 14, 245))
        box.alpha_composite(b1, ((box.width - b1.width) // 2, 12)); box.alpha_composite(num, ((box.width - num.width) // 2, b1.height - 6))
        img.alpha_composite(box, v["badge_xy"])
    if v["band"]:
        img.alpha_composite(band([v["band"]], 60, alpha=235, pad=(32, 14)), v["band_xy"])
    return img.convert("RGB")


def main():
    nums = (sys.argv[1:4] + ["1", "1", "1"])[:3]
    os.makedirs(OUT, exist_ok=True)
    for tag, n in zip("ABC", nums):
        im = compose(os.path.join(SRC, f"towerhd{tag}-{n}.png"), V[tag])
        p = os.path.join(OUT, f"tower-thumb-{tag}-hd-JP.jpg"); im.save(p, quality=94)
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        print("저장:", p)


if __name__ == "__main__":
    main()
