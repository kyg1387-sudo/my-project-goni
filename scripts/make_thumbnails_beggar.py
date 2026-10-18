#!/usr/bin/env python3
"""『みすぼらしい老人は、財閥会長だった』 썸네일 A/B(무과금·로컬) — make_thumbnails_tsuki.py 방식(제0장 8·제12장 8·제13장 5).
생성 그림: assets/portraits/beggar-thumb-anime-hd/anime-hd-N.png(2560x1440 애니메이션 화풍, 오른쪽 = 源蔵 얼굴 크게, 왼쪽 아래 = 무릎 꿇은 岩城).
글자는 왼쪽 위(흰 라벨 + 3줄 이내) + 금테 붉은 배지 + 검은 띠. 오른쪽 아래(재생 시간)는 비운다. 차별어(乞食·物乞い) 미사용(제17장 4 ③).
산출: 업로드용 1280x720 JPG(2MB 이하) + 휴대폰 확인용 360px·168px.
  A 【スカッと】: 追い出した老人は 財閥の 会長だった
  B 【感動】   : 七十年前の 一杯の 恩返し
사용법: python3 scripts/make_thumbnails_beggar.py [A그림번호 B그림번호]   (기본 1 2)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from make_thumbnails_ashita import GOTH, W, H, band, big, label, put  # noqa: E402
from make_thumbnails_yanagi_v2 import text_layer  # noqa: E402

SRC = os.path.join(ROOT, "assets", "portraits", "beggar-thumb-anime-hd")
PREFIX = os.environ.get("THUMB_PREFIX", "anime-hdfix")  # 1차 anime-hd-4에서 源蔵 귀걸이·땀방울을 로컬 인페인트(2차 anime-hd2는 전부 분할 화면 → 불채택)
OUT = os.path.join(ROOT, "assets", "thumbnails", "beggar")
FIRE = ((255, 236, 60), (255, 150, 20), (225, 30, 20))
YELLOW = ((255, 250, 150), (255, 225, 30), (250, 180, 0))
WARM = ((255, 245, 220), (255, 200, 120), (235, 120, 40))

VARIANTS = {
    # rows: (글자, 크기, 그라데이션, 단색) — 3줄 이내
    "A": dict(tag="スカッとする話", rows=[("追い出した老人は", 116, None, (255, 255, 255)), ("財閥の", 170, FIRE, None),
                                      ("会長だった", 176, YELLOW, None)],
              badge="支配人、土下座", num="明日から来るな", band="みすぼらしい老人は、財閥会長だった"),
    "B": dict(tag="感動する話", rows=[("七十年前の", 128, None, (255, 255, 255)), ("一杯のうどん", 158, WARM, None),
                                   ("その恩返し", 170, FIRE, None)],
              badge="店員に奨学金", num="七十年ぶりの味", band="みすぼらしい老人は、財閥会長だった"),
}


def darken_left(src, h):
    """왼쪽 위 글자 자리를 어둡게(오른쪽 源蔵 얼굴은 손대지 않음)."""
    img = src.convert("RGBA")
    shade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shade).rectangle([0, 0, 980, h], fill=150)
    shade = shade.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(shade)
    img.alpha_composite(dark)
    return img


def thumb(n, v, badge_xy, band_xy):
    src = Image.open(os.path.join(SRC, f"{PREFIX}-{n}.png")).convert("RGB").resize((W, H), Image.LANCZOS)
    img = darken_left(src, 720)
    img.alpha_composite(label(v["tag"], 64, (255, 255, 255, 255), (20, 20, 20)), (34, 26))
    y = 124
    for s, size, grad, fill in v["rows"]:
        lay = text_layer(s, GOTH, size, fill, (255, 255, 255) if grad else (0, 0, 0), 12,
                         gradient=grad, outer=(0, 0, 0) if grad else None, outer_w=9 if grad else 0)
        put(img, lay, 6, y)
        y += lay.height - 48
    if badge_xy is None:  # 무릎 꿇은 岩城(왼쪽 아래 가운데)을 가리지 않게 배지 생략, 띠만
        img.alpha_composite(band([v["band"]], 46, alpha=230, pad=(26, 10)), band_xy)
        return img.convert("RGB")
    b1 = label(v["badge"], 44, (175, 18, 18, 255), (255, 255, 255), pad=(26, 8))
    num = big(v["num"], 80, gradient=((255, 255, 190), (255, 225, 40), (255, 160, 0)), stroke_w=8, outer_w=6)
    box = Image.new("RGBA", (max(b1.width, num.width) + 44, b1.height + num.height + 4), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 28, fill=(255, 200, 40, 255))
    ImageDraw.Draw(box).rounded_rectangle([7, 7, box.width - 8, box.height - 8], 24, fill=(165, 14, 14, 245))
    box.alpha_composite(b1, ((box.width - b1.width) // 2, 12)); box.alpha_composite(num, ((box.width - num.width) // 2, b1.height - 6))
    img.alpha_composite(box, badge_xy)
    img.alpha_composite(band([v["band"]], 50, alpha=230, pad=(28, 12)), band_xy)
    return img.convert("RGB")


def main(na=1, nb=2, badge_xy=None, band_xy=(0, 1000)):
    os.makedirs(OUT, exist_ok=True)
    for tag, n in (("A", na), ("B", nb)):
        im = thumb(n, VARIANTS[tag], badge_xy, band_xy)
        p = os.path.join(OUT, f"beggar-thumb-{tag}-JP.jpg")
        im.resize((1280, 720), Image.LANCZOS).save(p, quality=92)
        assert os.path.getsize(p) < 2 * 1024 * 1024
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        im.resize((168, 95), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone168.png"))
        print("저장:", p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]) if a else 1, int(a[1]) if len(a) > 1 else 2)
