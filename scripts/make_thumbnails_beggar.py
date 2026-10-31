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
from make_thumbnails_ashita import GOTH, MIN, W, H, band, big, glow, label, put  # noqa: E402
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
              rows=[("追い出した", 134, FIRE, None), ("老人は", 140, None, (255, 255, 255)), ("財閥の", 184, FIRE, None), ("会長だった", 162, YELLOW, None)],
              row_y=320, shade=95, shade_w=640, badge=("支配人、土下座", "七十年前の恩"), badge_xy=(780, 24), band=None),
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
        img.alpha_composite(lab, (x0, 26)); y = v.get("row_y", 130)
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


# ---------------------------------------------------------------- B 교체: 『運転手のくせに』 썸네일 형식(고니감독님 첨부 2026-10-31)
#  왼쪽 = 어두운 배경 + 아래 불꽃(생성 그림) + 작은 검은 라벨 + 흰 글자 1줄 + 초대형 노랑→주황 그라데이션 2줄째(굵은 검은 테)
#  가운데 = 노란 번개(대각선, 검은 테·글로) / 오른쪽 = 악역(외치는 얼굴)·회장(냉정) 얼굴 클로즈업(생성 그림)
#  악역 입 옆 세로 말풍선(흰 바탕·검은 굵은 글자) / 오른쪽 아래(재생 시간 칸 왼쪽) 「〜の末路」 태그
D = dict(src="beggar-thumb-d/thumbD2-{n}fix.png", label="スカッとする話", line1="追い出した老人は…", line1_size=92, line1_y=180,
         line2="会長だった", line2_size=182, line2_y=740, bubble="知らなかった‼", bubble_xy=(1225, 50), tail_to=(1095, 560),
         bolt_x=(770, 640), tag="支配人の末路", tag_xy=(1290, 960))
GOLD = ((255, 250, 120), (255, 214, 0), (255, 140, 0))


def bolt(img, x_top, x_bot, w=70):
    """대각선 번개: 위(x_top,0) → 아래(x_bot,H)로 꺾이는 지그재그 다각형, 노랑 채움 + 주황 안쪽 + 검은 테 + 글로."""
    pts_c = [(x_top, -20), (x_top - 40, 300), (x_top + 60, 330), (x_bot - 30, 700), (x_bot + 70, 720), (x_bot - 60, H + 20)]
    left = [(x - w // 2, y) for x, y in pts_c]
    right = [(x + w // 2, y) for x, y in pts_c][::-1]
    poly = left + right
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon(poly, fill=(255, 220, 40, 255), outline=(0, 0, 0, 255))
    inner = [(x - w // 5, y) for x, y in pts_c] + [(x + w // 5, y) for x, y in pts_c][::-1]
    d.polygon(inner, fill=(255, 250, 200, 255))
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(edge).line(poly + [poly[0]], fill=(0, 0, 0, 255), width=10)
    g = lay.split()[3].filter(ImageFilter.GaussianBlur(28)).point(lambda v: min(255, int(v * 1.4)))
    glowl = Image.new("RGBA", (W, H), (255, 190, 0, 0)); glowl.putalpha(g)
    img.alpha_composite(glowl); img.alpha_composite(edge); img.alpha_composite(lay)


def vbubble(img, text, xy, tail_to, size=86):
    """세로 말풍선: 흰 둥근 사각 + 검은 테 + 꼬리(악역 입 쪽), 글자는 세로쓰기."""
    from PIL import ImageFont
    f = ImageFont.truetype(GOTH, size)
    n = len(text); bw, bh = size + 70, n * (size + 4) + 70
    x, y = xy
    d = ImageDraw.Draw(img)
    tx, ty = tail_to
    d.polygon([(x + bw // 2 - 26, y + bh - 30), (x + bw // 2 + 26, y + bh - 30), (tx, ty)], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
    d.rounded_rectangle([x, y, x + bw, y + bh], 46, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=7)
    d.polygon([(x + bw // 2 - 22, y + bh - 8), (x + bw // 2 + 22, y + bh - 8), (tx - 6, ty - 14)], fill=(255, 255, 255, 255))
    for i, ch in enumerate(text):
        cy = y + 40 + i * (size + 4) + size // 2
        if ch == "‼":  # 글꼴에 「‼」가 없어 「！」 두 개를 한 칸에 나란히(세로쓰기 가로 묶음)
            fs = ImageFont.truetype(GOTH, int(size * 0.8))
            for dx in (-size // 5, size // 5):
                d.text((x + bw // 2 + dx, cy), "!", font=fs, fill=(10, 10, 10, 255), anchor="mm", stroke_width=3, stroke_fill=(10, 10, 10, 255))
            continue
        d.text((x + bw // 2, cy), ch, font=f, fill=(10, 10, 10, 255), anchor="mm")


def thumb_d(n, v=D):
    img = Image.open(os.path.join(ABC_SRC, v["src"].format(n=n))).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    shade = Image.new("L", (W, H), 0); ImageDraw.Draw(shade).rectangle([0, 0, 640, H], fill=110)
    shade = shade.filter(ImageFilter.GaussianBlur(110)); dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(shade)
    img.alpha_composite(dark)
    bolt(img, *v["bolt_x"])
    img.alpha_composite(label(v["label"], 58, (12, 12, 12, 255), (255, 255, 255), border=(255, 255, 255, 255)), (24, 26))
    l1 = text_layer(v["line1"], GOTH, v["line1_size"], (255, 255, 255), (0, 0, 0), 14)
    put(img, l1, 0, v["line1_y"])
    l2 = glow(big(v["line2"], v["line2_size"], gradient=GOLD, stroke_w=16, outer_w=12), color=(255, 90, 0), r=20, strength=1.3)
    put(img, l2, -30, v["line2_y"])
    vbubble(img, v["bubble"], v["bubble_xy"], v["tail_to"])
    tag = label(v["tag"], 54, (150, 10, 10, 245), (255, 255, 255), border=(255, 210, 60, 255), pad=(26, 8))
    img.alpha_composite(tag, v["tag_xy"])
    return img.convert("RGB")


def d_final(n):
    im = thumb_d(n)
    p = os.path.join(OUT, "beggar-thumb-B-JP.jpg")
    im.resize((1280, 720), Image.LANCZOS).save(p, quality=92)
    im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
    im.resize((168, 95), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone168.png"))
    print("저장:", p, os.path.getsize(p) // 1024, "KB")


# ---------------------------------------------------------------- E: 고니감독님 제공 썸네일 편집판(2026-10-31) — 실사 레스토랑, 머리 숙인 岩城·서 있는 源蔵(낡은 점퍼)
#  왼쪽 위 노란 【スカッと】(검은 테) + 흰 「追い出した老人は」 + 초대형 빨강 그라데이션 「財閥会長」(크림 테·검은 바깥 테)
CRIMSON = ((255, 90, 70), (215, 20, 20), (120, 0, 0))
E = dict(src="beggar-thumb-e/thumbE-{n}fix.png", tag="【スカッと】", line1="追い出した老人は", line2="財閥会長")


def thumb_e(n, v=E, x0=30):
    src = Image.open(os.path.join(ABC_SRC, v["src"].format(n=n))).convert("RGB")
    sw, sh = src.size  # 인물을 휴대폰에서 크게: 왼쪽 10%·아래 10%를 잘라 1.11배 확대(얼굴 화면 높이 약 14%)
    img = src.crop((int(sw * 0.10), 0, sw, int(sh * 0.90))).resize((W, H), Image.LANCZOS).convert("RGBA")
    shade = Image.new("L", (W, H), 0); ImageDraw.Draw(shade).rectangle([0, 0, 1150, 560], fill=125)
    shade = shade.filter(ImageFilter.GaussianBlur(110)); dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(shade)
    img.alpha_composite(dark)
    t = text_layer(v["tag"], GOTH, 128, (255, 240, 0), (0, 0, 0), 13)
    put(img, t, x0 - 30, 6)
    l1 = text_layer(v["line1"], GOTH, 96, (255, 255, 255), (0, 0, 0), 13)
    put(img, l1, x0 - 20, 165)
    l2 = text_layer(v["line2"], MIN, 236, None, (255, 244, 214), 14, gradient=CRIMSON, outer=(0, 0, 0), outer_w=10)
    put(img, l2, x0 - 40, 270)
    return img.convert("RGB")


def e_final(n, tag="E"):
    im = thumb_e(n)
    p = os.path.join(OUT, f"beggar-thumb-{tag}-JP.jpg")
    im.resize((1280, 720), Image.LANCZOS).save(p, quality=92)
    im.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
    im.resize((168, 95), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone168.png"))
    print("저장:", p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "e":  # e 그림번호 — 고니감독님 제공 썸네일 편집판
        e_final(a[1] if len(a) > 1 else "1"); sys.exit()
    if a and a[0] == "d":  # d 그림번호 — B를 『運転手のくせに』 형식으로 교체
        d_final(a[1] if len(a) > 1 else "1"); sys.exit()
    if a and a[0] == "abc":  # abc A번호 B번호 C번호
        abc_final(dict(zip("ABC", (a[1:] + ["1", "1", "1"])[:3]))); sys.exit()
    main(int(a[0]) if a else 1, int(a[1]) if len(a) > 1 else 2)
