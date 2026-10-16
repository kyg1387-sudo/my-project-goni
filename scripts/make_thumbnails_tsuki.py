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
from make_thumbnails_ashita import GOTH, W, H, band, big, glow, label, put  # noqa: E402
from make_thumbnails_yanagi_v2 import text_layer  # noqa: E402

SRC = os.path.join(ROOT, "assets", "portraits", "tsuki-thumb-anime-hd")
OUT = os.path.join(ROOT, "assets", "thumbnails", "tsuki")
FIRE = ((255, 236, 60), (255, 150, 20), (225, 30, 20))
YELLOW = ((255, 250, 150), (255, 225, 30), (250, 180, 0))
ICE = ((225, 245, 255), (150, 205, 255), (60, 120, 230))

VARIANTS = {
    # rows: (글자, 크기, 그라데이션, 단색)  — 3줄 이내
    "A": dict(tag="泣ける話", rows=[("「ゴミ」と捨てた男が", 112, None, (255, 255, 255)), ("二百億円の鍵", 158, FIRE, None)],
              badge="役員全員、土下座", num="三十日後、倒産", band="月に帰った契約社員"),
    "B": dict(tag="スカッとする話", rows=[("月から来た", 136, ICE, None), ("ゴミと笑った", 146, FIRE, None),
                                      ("役員の末路", 166, YELLOW, None)],
              badge="契約社員の逆襲", num="違約金 二百億円", band="三十日後、会社が止まった"),
}


def darken_left(src, h=700):
    """왼쪽 위 글자 자리를 어둡게(그림은 그대로, 오른쪽 光 얼굴은 손대지 않음)."""
    img = src.convert("RGBA")
    shade = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shade)
    d.rectangle([0, 0, 1040, h], fill=150)
    shade = shade.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(shade)
    img.alpha_composite(dark)
    return img


def thumb(n, v):
    src = Image.open(os.path.join(SRC, f"anime-hd-{n}.png")).convert("RGB").resize((W, H), Image.LANCZOS)
    img = darken_left(src, 700 if len(v["rows"]) > 2 else 420)
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
    img.alpha_composite(box, (40, 830))                               # 왼쪽 아래(鷲尾의 무릎·비상등 위, 얼굴은 가리지 않음)
    return img.convert("RGB")


# ---------------------------------------------------------------- 고니감독님 생성 그림 3종(2026-10-16) — A 어두운 실사 / B 웹툰 / C 실사 투샷
USER = {
    "A": dict(src="user-A-src.png", label=None, side="L",
              rows=[("月から来たゴミと", 118, None, (255, 255, 255)), ("笑われた男は", 118, None, (255, 255, 255)), ("消えた…", 118, None, (255, 255, 255))],
              quote="「行かないで」", quote_size=230, badge=None, band=None),
    "B": dict(src="user-B-src.png", label="感動する話", side="L",
              rows=[("捨てた男が", 150, FIRE, None), ("二百億円の", 160, YELLOW, None), ("鍵だった", 186, FIRE, None)],
              quote=None, badge=("偽造の判子、暴かれる", "違約金 二百億円"), band="三十日後、会社が止まった", badge_xy=(1120, 640), band_xy=(1080, 940)),
    "B2": dict(src="user-B2-src.png", label="感動する話", side="L",      # 얼굴 중앙 확대판(좌우는 흐린 확장) — 글자를 좌우 흐린 면에
               rows=[("捨てた男が", 140, FIRE, None), ("二百億円の", 150, YELLOW, None), ("鍵だった", 170, FIRE, None)],
               quote=None, badge=("偽造の判子、暴かれる", "違約金 二百億円"), band="三十日後、会社が止まった", badge_xy=(1180, 520), band_xy=(1130, 840), badge_num=76),
    "C": dict(src="user-C-src.png", label="感動する話", side="R",
              rows=[("契約社員をクビにした…", 84, ((255, 120, 110), (235, 40, 40), (160, 10, 10)), None),
                    ("三十日後、", 108, YELLOW, None), ("灯りが消えた", 108, YELLOW, None)],
              quote=None, badge=None, band=["竹とんぼが、", "会社の命運を変える"], band_xy=(1000, 820)),
}


def fix_B_certificate(img):
    """웹툰 그림의 특허증·서류 가짜 글자(제2장 1) → 크림색 종이 위에 실글꼴 「特許証」 합성."""
    from PIL import ImageFont
    d = ImageDraw.Draw(img)
    # 특허증(왼쪽 아래 큰 종이) — 원본 2000x1116 기준 좌표를 1920x1080으로 환산
    box = (452, 690, 690, 1080)
    strip = img.crop((400, 690, 452, 1080)).filter(ImageFilter.GaussianBlur(10)); img.paste(strip, (400, 690))
    d.rectangle(box, fill=(246, 240, 222, 255))
    d.rectangle((box[0] + 10, box[1] + 10, box[2] - 10, box[3] - 10), outline=(200, 170, 90, 255), width=4)
    f = ImageFont.truetype(os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf"), 58)
    d.text(((box[0] + box[2]) // 2, box[1] + 64), "特許証", font=f, fill=(60, 40, 30, 255), anchor="mm")
    f2 = ImageFont.truetype(os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Regular.ttf"), 22)
    for i, t in enumerate(["発明の名称　負荷分散制御", "特許権者　竹内　光", "登録日　二年前"]):
        d.text((box[0] + 24, box[1] + 130 + i * 44), t, font=f2, fill=(70, 50, 40, 255))
    for k in range(4):
        d.line((box[0] + 24, box[1] + 290 + k * 32, box[2] - 24, box[1] + 290 + k * 32), fill=(150, 130, 100, 120), width=2)
    d.ellipse((box[2] - 110, box[3] - 110, box[2] - 40, box[3] - 40), outline=(190, 40, 40, 220), width=4)
    # 篠田 손의 서류 2곳 — 작은 글자는 흐림 허용(배경 소품)
    for bx in [(1395, 350, 1560, 520), (1500, 730, 1700, 830)]:
        reg = img.crop(bx).filter(ImageFilter.GaussianBlur(9)); img.paste(reg, bx[:2])
    return img


def thumb_user(v):
    src = Image.open(os.path.join(OUT, v["src"])).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    img = src
    if v["src"] == "user-B-src.png":
        img = fix_B_certificate(img)
    # 글자 자리 어둡게(왼쪽 또는 오른쪽 위)
    shade = Image.new("L", (W, H), 0); d = ImageDraw.Draw(shade)
    if v["side"] == "L": d.rectangle([0, 0, 1000 if "B2" not in v["src"] else 640, 760], fill=140)
    else: d.rectangle([900, 0, W, 440], fill=150)
    shade = shade.filter(ImageFilter.GaussianBlur(120)); dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(shade); img.alpha_composite(dark)
    x0 = 34 if v["side"] == "L" else 1000
    y = 40
    if v["label"]:
        img.alpha_composite(label(v["label"], 62, (255, 255, 255, 255), (20, 20, 20)), (x0, 26)); y = 128 if v["side"] == "L" else 112
    for s, size, grad, fill in v["rows"]:
        lay = text_layer(s, GOTH, size, fill, (255, 255, 255) if grad else (0, 0, 0), 12, gradient=grad, outer=(0, 0, 0) if grad else None, outer_w=9 if grad else 0)
        put(img, lay, x0 - 28, y); y += lay.height - 48
    if v["quote"]:
        lay = big(v["quote"], v["quote_size"], gradient=FIRE, stroke_w=12, outer_w=10)
        lay = glow(lay) if "glow" in globals() else lay
        put(img, lay, 60, H - lay.height - 20)
    if v["badge"]:
        b1 = label(v["badge"][0], 44, (175, 18, 18, 255), (255, 255, 255), pad=(26, 8))
        num = big(v["badge"][1], v.get("badge_num", 88), gradient=((255, 255, 190), (255, 225, 40), (255, 160, 0)), stroke_w=8, outer_w=6)
        box = Image.new("RGBA", (max(b1.width, num.width) + 44, b1.height + num.height + 4), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 28, fill=(255, 200, 40, 255))
        ImageDraw.Draw(box).rounded_rectangle([7, 7, box.width - 8, box.height - 8], 24, fill=(165, 14, 14, 245))
        box.alpha_composite(b1, ((box.width - b1.width) // 2, 12)); box.alpha_composite(num, ((box.width - num.width) // 2, b1.height - 6))
        img.alpha_composite(box, v["badge_xy"])
    if v["band"]:
        lines = v["band"] if isinstance(v["band"], list) else [v["band"]]
        img.alpha_composite(band(lines, 62 if "B2" not in v["src"] else 52, alpha=235, pad=(32, 14)), v["band_xy"])
    return img.convert("RGB")


def user_final():
    os.makedirs(OUT, exist_ok=True)
    for tag, v in USER.items():
        p = os.path.join(OUT, f"tsuki-thumb-{tag}-JP.jpg")
        im = thumb_user(v); im.save(p, quality=94)
        im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
        print("저장:", p)


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
    if a and a[0] == "user":
        user_final(); sys.exit()
    main(int(a[0]) if a else 1, int(a[1]) if len(a) > 1 else 2)
