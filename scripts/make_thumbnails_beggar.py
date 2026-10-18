#!/usr/bin/env python3
"""『みすぼらしい老人は、財閥会長だった』 썸네일 A/B(무과금·로컬) — make_thumbnails_tsuki.py 방식(제0장 8·제12장 8·제13장 5).
생성 그림: assets/portraits/beggar-thumb-anime-hd/anime-hd-N.png(2560x1440 애니메이션 화풍, 오른쪽 = 源蔵 얼굴 크게, 왼쪽 아래 = 무릎 꿇은 岩城).
글자는 왼쪽 위(흰 라벨 + 3줄 이내) + 금테 붉은 배지 + 검은 띠. 오른쪽 아래(재생 시간)는 비운다. 차별어(乞食·物乞い) 미사용(제17장 4 ③).
산출: 업로드용 1280x720 JPG(2MB 이하) + 휴대폰 확인용 360px·168px.
  A 【スカッと】: 追い出した老人は 財閥の 会長だった
  B 【感動】   : 七十年前の 一杯の 恩返し
사용법: python3 scripts/make_thumbnails_beggar.py [A그림번호 B그림번호]   (기본 1 2, 1차 애니메이션판)
        python3 scripts/make_thumbnails_beggar.py abc A번호 B번호 C번호   (고니감독님 첨부 형식 A·B·C, beggar-thumb-abc)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from make_thumbnails_ashita import GOTH, W, H, band, big, glow, label, put  # noqa: E402
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


# ---------------------------------------------------------------- 고니감독님 첨부 형식 A·B·C(2026-10-18)
#  A 어두운 실사: 오른쪽 얼굴 크게 + 왼쪽 흰 글자 3줄 + 아래 초대형 인용구 「」(불꽃 그라데이션·붉은 글로)
#  B 웹툰: 왼쪽 위 흰 라벨 + 세로 4줄 초대형 그라데이션 글자 + 금테 붉은 배지 + 검은 띠
#  C 따뜻한 실사 투샷: 오른쪽 위 검은 라벨 + 빨강/노랑 2줄 제목(흰 테) + 아래 반투명 검은 띠 노란 글자 2줄
ABC_SRC = os.path.join(ROOT, "assets", "portraits")
RED = ((255, 120, 110), (235, 40, 40), (160, 10, 10))
ABC = {
    "A": dict(src="beggar-thumb-a3/thumbA3-{n}fix.png", side="L", label=None,
              rows=[("みすぼらしい", 112, None, (255, 255, 255)), ("老人に", 112, None, (255, 255, 255)), ("支配人は言った…", 112, None, (255, 255, 255))],
              row_y=300, quote="「裏口から出ろ」", quote_size=210),
    "B": dict(src="beggar-thumb-abc/thumbB-{n}.png", side="L", label="スカッとする話",
              rows=[("追い出した", 128, FIRE, None), ("老人は", 140, None, (255, 255, 255)), ("財閥の", 150, FIRE, None), ("会長だった", 138, YELLOW, None)],
              shade=95, shade_w=640, badge=("支配人、土下座", "七十年前の恩"), badge_xy=(780, 24), band=None),
    "C": dict(src="beggar-thumb-abc2/thumbC2-{n}fix.png", side="R", label="感動する話", label_style="black",
              rows=[("三万円の店で…", 112, RED, None), ("老人が頼んだもの", 104, YELLOW, None)], x0=1010,
              band=["その一杯が、", "店の運命を変える"], band_xy=(1060, 760)),
}


def thumb_fmt(tag, n):
    v = ABC[tag]
    img = Image.open(os.path.join(ABC_SRC, v["src"].format(n=n))).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    shade = Image.new("L", (W, H), 0); d = ImageDraw.Draw(shade)
    if v["side"] == "L":
        d.rectangle([0, 0, v.get("shade_w", 980), H if tag == "A" else 820], fill=v.get("shade", 140 if tag != "A" else 110))
    else:
        d.rectangle([900, 0, W, 420], fill=150)
    shade = shade.filter(ImageFilter.GaussianBlur(120)); dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(shade)
    img.alpha_composite(dark)
    if v["side"] == "L":
        x0, y = 34, v.get("row_y", 40)
    else:
        x0, y = v.get("x0", 1010), 40
    if v["label"]:
        if v.get("label_style") == "black":
            lab = label(v["label"], 62, (10, 10, 10, 255), (255, 255, 255), border=(255, 255, 255, 255))
        else:
            lab = label(v["label"], 64, (255, 255, 255, 255), (20, 20, 20))
        img.alpha_composite(lab, (x0, 26)); y = 130
    for s_, size, grad, fill in v["rows"]:
        lay = text_layer(s_, GOTH, size, fill, (255, 255, 255) if grad else (0, 0, 0), 12,
                         gradient=grad, outer=(0, 0, 0) if grad else None, outer_w=9 if grad else 0)
        put(img, lay, x0 - 28, y); y += lay.height - (48 if size >= 140 else 40)
    if v.get("quote"):
        lay = glow(big(v["quote"], v["quote_size"], gradient=FIRE, stroke_w=12, outer_w=10))
        put(img, lay, 40, H - lay.height + 30)
    if v.get("badge"):
        b1 = label(v["badge"][0], 46, (175, 18, 18, 255), (255, 255, 255), pad=(26, 8))
        num = big(v["badge"][1], 92, gradient=((255, 255, 190), (255, 225, 40), (255, 160, 0)), stroke_w=8, outer_w=6)
        box = Image.new("RGBA", (max(b1.width, num.width) + 44, b1.height + num.height + 4), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 28, fill=(255, 200, 40, 255))
        ImageDraw.Draw(box).rounded_rectangle([7, 7, box.width - 8, box.height - 8], 24, fill=(165, 14, 14, 245))
        box.alpha_composite(b1, ((box.width - b1.width) // 2, 12)); box.alpha_composite(num, ((box.width - num.width) // 2, b1.height - 6))
        img.alpha_composite(box, v["badge_xy"])
    if v.get("band"):
        img.alpha_composite(band(v["band"], 66, alpha=225, pad=(30, 14)), v["band_xy"])
    return img.convert("RGB")


def abc_final(picks, only=None):
    os.makedirs(OUT, exist_ok=True)
    for tag, n in picks.items():
        if only and tag not in only:
            continue
        im = thumb_fmt(tag, n)
        p = os.path.join(OUT, f"beggar-thumb-{tag}-JP.jpg")
        im.resize((1280, 720), Image.LANCZOS).save(p, quality=92)
        assert os.path.getsize(p) < 2 * 1024 * 1024
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        im.resize((168, 95), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone168.png"))
        print("저장:", p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "abc":  # abc A번호 B번호 C번호
        abc_final(dict(zip("ABC", (a[1:] + ["1", "1", "1"])[:3]))); sys.exit()
    main(int(a[0]) if a else 1, int(a[1]) if len(a) > 1 else 2)
