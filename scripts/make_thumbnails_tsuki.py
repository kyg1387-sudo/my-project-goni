#!/usr/bin/env python3
"""『月に帰った契約社員』 썸네일 A/B(1920x1080, 무과금·로컬) — make_thumbnails_ashita.py hd 방식(제0장 8).
생성 그림: assets/portraits/tsuki-thumb-anime-hd/anime-hd-N.png(2560x1440, 오른쪽 = 光 얼굴 크게, 왼쪽 = 무릎 꿇은 鷲尾).
글자는 왼쪽 위 3줄 이내(휴대폰 기준) + 금테 붉은 배지 + 검은 띠. 오른쪽 아래(재생 시간)는 비운다. 360px 축소본도 저장.
  A 【泣ける】 계열: 「ゴミ」と捨てた男が 二百億円の 特許だった
  B 【スカッと】 계열: 月から来たゴミと 笑った役員の 三十日後
사용법: python3 scripts/make_thumbnails_tsuki.py [A그림번호 B그림번호]   (기본 1 2)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from make_thumbnails_ashita import GOTH, W, H, band, big, label, put  # noqa: E402
from make_thumbnails_yanagi_v2 import text_layer  # noqa: E402

SRC = os.path.join(ROOT, "assets", "portraits", "tsuki-thumb-anime-hd")
OUT = os.path.join(ROOT, "assets", "thumbnails", "tsuki")
FIRE = ((255, 236, 60), (255, 150, 20), (225, 30, 20))
YELLOW = ((255, 250, 150), (255, 225, 30), (250, 180, 0))
ICE = ((225, 245, 255), (150, 205, 255), (60, 120, 230))

VARIANTS = {
    # rows: (글자, 크기, 그라데이션, 단색)  — 3줄 이내
    "A": dict(tag="泣ける話", rows=[("「ゴミ」と", 150, None, (255, 255, 255)), ("捨てた男が", 170, FIRE, None),
                                   ("二百億円の鍵", 178, YELLOW, None)],
              badge="役員全員、土下座", num="三十日後、倒産", band="月に帰った契約社員"),
    "B": dict(tag="スカッとする話", rows=[("月から来た", 150, ICE, None), ("ゴミと笑った", 160, FIRE, None),
                                      ("役員の末路", 186, YELLOW, None)],
              badge="契約社員の逆襲", num="違約金 二百億円", band="三十日後、会社が止まった"),
}


def darken_left(src):
    """왼쪽 위 글자 자리를 어둡게(그림은 그대로, 오른쪽 光 얼굴은 손대지 않음)."""
    img = src.convert("RGBA")
    shade = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shade)
    d.rectangle([0, 0, 1040, 700], fill=150)
    shade = shade.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(shade)
    img.alpha_composite(dark)
    return img


def thumb(n, v):
    src = Image.open(os.path.join(SRC, f"anime-hd-{n}.png")).convert("RGB").resize((W, H), Image.LANCZOS)
    img = darken_left(src)
    img.alpha_composite(label(v["tag"], 66, (255, 255, 255, 255), (20, 20, 20)), (34, 26))
    y = 128
    for s, size, grad, fill in v["rows"]:
        lay = text_layer(s, GOTH, size, fill, (255, 255, 255) if grad else (0, 0, 0), 12,
                         gradient=grad, outer=(0, 0, 0) if grad else None, outer_w=9 if grad else 0)
        put(img, lay, 6, y)
        y += lay.height - 48
    badge = label(v["badge"], 46, (175, 18, 18, 255), (255, 255, 255), pad=(28, 8))
    num = big(v["num"], 92, gradient=((255, 255, 190), (255, 225, 40), (255, 160, 0)), stroke_w=8, outer_w=6)
    box = Image.new("RGBA", (max(badge.width, num.width) + 44, badge.height + num.height + 4), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 28, fill=(255, 200, 40, 255))
    ImageDraw.Draw(box).rounded_rectangle([7, 7, box.width - 8, box.height - 8], 24, fill=(165, 14, 14, 245))
    box.alpha_composite(badge, ((box.width - badge.width) // 2, 12))
    box.alpha_composite(num, ((box.width - num.width) // 2, badge.height - 6))
    img.alpha_composite(box, (40, 700))                               # 왼쪽 아래(무릎 꿇은 鷲尾 위쪽)
    img.alpha_composite(band([v["band"]], 64, alpha=235, pad=(32, 14)), (40, 950))
    return img.convert("RGB")


def main(na=1, nb=2):
    os.makedirs(OUT, exist_ok=True)
    for tag, n in (("A", na), ("B", nb)):
        p = os.path.join(OUT, f"tsuki-thumb-{tag}-JP.jpg")
        im = thumb(n, VARIANTS[tag])
        im.save(p, quality=94)
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        print("저장:", p)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]) if a else 1, int(a[1]) if len(a) > 1 else 2)
