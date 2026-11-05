#!/usr/bin/env python3
"""『母が遺したビデオレター』 화면·서류 일본어 그래픽(무료·로컬) — 키프레임의 무지 면에 PHASE 4에서 합성(제7장 6·제19장 13, 06_장면정합표 3·4절).
대본과 1:1(제14장 6): 貸主 ひだまりファイナンス株式会社 · 借主 佐伯佐和子 · 合計4,700万円 · 収入印紙 칸 공란(NA18b) · 申述人 공란 · 令和8年10月3日 ·
民法第915条 · 「該当なし」 3社(CIC·JICC·KSC — 기관 로고 없이 이름만) · 돌봄 카메라 「07/03 23:41」 · 메시지 앱은 일반 UI(실제 서비스 로고·상표 없음).
사용법: python3 scripts/aihaha_graphics.py  → assets/preview/aihaha-graphics/*.png + _sheet.jpg"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets", "preview", "aihaha-graphics"); os.makedirs(OUT, exist_ok=True)
G = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
M = next((p for p in ("/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf", "/usr/share/fonts/truetype/fonts-japanese-mincho.ttf") if os.path.exists(p)), G)
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
HAND = os.path.join(ROOT, "assets", "fonts", "KleeOne-SemiBold.ttf")
def F(sz, f=G): return ImageFont.truetype(f, sz)
INK = (30, 30, 34); RED = (196, 32, 36); PAPER = (247, 243, 232)

def seal(d, cx, cy, r, ch="佐伯"):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED, width=max(3, r // 9))
    f = F(int(r * 0.78), M)
    for i, c in enumerate(ch):
        d.text((cx, cy - r * 0.42 + i * r * 0.84), c, font=f, fill=RED, anchor="mm")

def loan(no, amount, date):
    W, H = 1240, 1754; im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im)
    d.text((W // 2, 150), "金銭消費貸借契約書", font=F(64, M), fill=INK, anchor="mm")
    d.text((W - 120, 70), f"No. {no:03d}", font=F(28), fill=INK, anchor="rm")
    # 収入印紙 칸 — 비어 있음(NA18b)
    d.rectangle((W - 330, 230, W - 120, 470), outline=(120, 120, 120), width=3)
    for y in range(240, 470, 18): d.line((W - 330, y, W - 320, y), fill=(150, 150, 150))
    d.text((W - 225, 350), "収入印紙", font=F(30), fill=(140, 140, 140), anchor="mm")
    y = 560
    rows = [("貸主", "ひだまりファイナンス株式会社"), ("借主", "佐伯　佐和子"), ("借入金額", f"金　{amount}　円也"), ("契約日", date),
            ("返済方法", "元利均等返済　毎月末日"), ("利率", "年　一五・〇パーセント")]
    for k, v in rows:
        d.text((150, y), k, font=F(38, M), fill=INK); d.text((420, y), v, font=F(42, M), fill=INK); d.line((150, y + 62, W - 150, y + 62), fill=(170, 170, 170), width=2); y += 120
    for i, t in enumerate(["第一条　借主は貸主より上記金額を借り受け、これを受領した。", "第二条　借主は前項の金員を上記の方法により返済する。",
                           "第三条　本契約に関する紛争は、千葉地方裁判所を管轄裁判所とする。"]):
        d.text((150, 1330 + i * 64), t, font=F(30, M), fill=INK)
    d.text((150, 1560), "借主　住所　千葉県　　　　　　　　　　　　　氏名　佐伯　佐和子", font=F(30, M), fill=INK)
    seal(d, W - 230, 1575, 62)
    seal(d, 150, 150, 56)  # 捨印(위 여백 왼쪽, 같은 실인) — S04e 접사의 인영과 같은 자리(R45, 2026-11-05)
    return im

def report(org, full):
    W, H = 1600, 1000; im = Image.new("RGB", (W, H), (250, 251, 253)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 110), fill=(38, 64, 110)); d.text((60, 55), f"{org}　信用情報開示報告書", font=F(46), fill=(255, 255, 255), anchor="lm")
    d.text((W - 60, 55), "開示日 2026/08/27", font=F(30), fill=(220, 228, 240), anchor="rm")
    d.text((80, 190), full, font=F(32), fill=(70, 80, 95))
    d.text((80, 270), "照会対象者　佐伯 佐和子 様（被相続人）　　開示請求者　佐伯 由紀子 様（相続人）", font=F(34), fill=INK)
    d.rectangle((80, 360, W - 80, 820), outline=(190, 198, 210), width=3)
    d.text((W // 2, 470), "登録されている信用情報", font=F(40), fill=(90, 98, 110), anchor="mm")
    d.text((W // 2, 640), "該当なし", font=F(150), fill=(200, 30, 40), anchor="mm")
    d.text((80, 880), "※ 貸付・クレジット・保証に関する登録はありません。", font=F(30), fill=(90, 98, 110))
    return im

def form(date):
    W, H = 1240, 1754; im = Image.new("RGB", (W, H), (252, 252, 248)); d = ImageDraw.Draw(im)
    d.text((W // 2, 130), "相 続 の 放 棄 の 申 述 書", font=F(60, M), fill=INK, anchor="mm")
    d.text((140, 250), "千葉家庭裁判所　御中", font=F(36, M), fill=INK); d.text((W - 140, 250), date, font=F(36, M), fill=INK, anchor="ra")
    box = (140, 340, W - 140, 760); d.rectangle(box, outline=INK, width=3)
    d.text((170, 370), "申述人", font=F(40, M), fill=INK)
    for i, k in enumerate(["本籍", "住所", "氏名", "被相続人との関係"]):
        yy = 450 + i * 75; d.text((300, yy), k, font=F(32, M), fill=INK); d.line((520, yy + 42, W - 170, yy + 42), fill=(160, 160, 160), width=2)
    d.rectangle((140, 800, W - 140, 1100), outline=INK, width=3); d.text((170, 830), "被相続人", font=F(40, M), fill=INK)
    d.text((300, 910), "氏名　佐伯　佐和子", font=F(34, M), fill=INK); d.text((300, 990), "死亡当時の住所　千葉県", font=F(34, M), fill=INK)
    d.text((140, 1180), "申述の趣旨　　相続の放棄をする。", font=F(38, M), fill=INK)
    d.text((140, 1290), "申述の理由　　□ 債務超過のため　　□ その他", font=F(34, M), fill=INK)
    return im

def law():
    W, H = 1600, 1000; im = Image.new("RGB", (W, H), (244, 238, 222)); d = ImageDraw.Draw(im)
    d.text((120, 120), "民法", font=F(40, M), fill=(90, 80, 70)); d.text((120, 240), "（相続の承認又は放棄をすべき期間）", font=F(40, M), fill=INK)
    d.text((120, 330), "第九百十五条", font=F(48, M), fill=INK)
    t = ["相続人は、自己のために相続の開始が", "あったことを知った時から三箇月以内に、", "相続について、単純若しくは限定の承認", "又は放棄をしなければならない。"]
    for i, l in enumerate(t):
        d.text((160, 440 + i * 86), l, font=F(52, M), fill=INK)
    d.line((160, 440 + 86 + 64, 160 + 54 * 14, 440 + 86 + 64), fill=(200, 60, 50), width=5)  # 「三箇月以内」 줄 밑줄(손으로 그은 듯)
    return im

def calendar():
    W, H = 1000, 1000; im = Image.new("RGB", (W, H), (250, 250, 248)); d = ImageDraw.Draw(im)
    d.text((W // 2, 110), "2026　10月", font=F(80), fill=INK, anchor="mm")
    days = ["日", "月", "火", "水", "木", "金", "土"]
    for i, k in enumerate(days):
        d.text((90 + i * 130, 230), k, font=F(40), fill=(200, 40, 40) if i == 0 else (40, 80, 170) if i == 6 else INK, anchor="mm")
    first = 4  # 2026-10-01 = 木
    for n in range(1, 32):
        c = (first + n - 1) % 7; r = (first + n - 1) // 7
        x, y = 90 + c * 130, 330 + r * 125
        d.text((x, y), str(n), font=F(54), fill=(200, 40, 40) if c == 0 else (40, 80, 170) if c == 6 else INK, anchor="mm")
        if n == 3:
            d.ellipse((x - 52, y - 52, x + 52, y + 52), outline=RED, width=7)
    return im

def chat(rows, title):
    W, H = 900, 1600; im = Image.new("RGB", (W, H), (235, 238, 244)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 150), fill=(250, 250, 252)); d.text((W // 2, 95), title, font=F(46), fill=INK, anchor="mm"); d.text((40, 95), "＜", font=F(46), fill=INK, anchor="lm")
    y = 220
    for kind, txt, date in rows:
        d.text((W // 2, y), date, font=F(28), fill=(120, 126, 140), anchor="mm"); y += 50
        if kind == "video":
            d.rounded_rectangle((60, y, 560, y + 300), 24, fill=(30, 30, 36)); d.polygon([(280, y + 110), (280, y + 190), (350, y + 150)], fill=(240, 240, 240))
            d.text((540, y + 280), txt, font=F(26), fill=(230, 230, 230), anchor="rd"); y += 350
        elif kind == "voice":
            d.rounded_rectangle((60, y, 640, y + 120), 60, fill=(255, 255, 255)); d.polygon([(110, y + 35), (110, y + 85), (155, y + 60)], fill=(60, 160, 90))
            for i in range(26): h = 10 + (i * 37 % 40); d.line((190 + i * 14, y + 60 - h // 2, 190 + i * 14, y + 60 + h // 2), fill=(120, 130, 140), width=6)
            d.text((610, y + 60), txt, font=F(30), fill=INK, anchor="rm"); y += 170
    return im

def card(text, size=96, w=1920, h=1080, serif=True):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); f = ImageFont.truetype(SERIF_B, size, index=0) if serif else F(size, G)
    for dx in range(-6, 7, 2):
        for dy in range(-6, 7, 2): d.text((w // 2 + dx, h // 2 + dy), text, font=f, fill=(0, 0, 0, 200), anchor="mm")
    d.text((w // 2, h // 2), text, font=f, fill=(255, 255, 255, 255), anchor="mm"); return im

def corner(text):
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(im); f = F(54, M)
    for dx in (-3, 0, 3):
        for dy in (-3, 0, 3): d.text((120 + dx, 110 + dy), text, font=f, fill=(0, 0, 0, 200))
    d.text((120, 110), text, font=f, fill=(255, 255, 255, 255)); return im

def cctv(ts):
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(im); f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 44)
    d.text((60, 50), f"CAM 02  廊下", font=F(44), fill=(235, 235, 235, 255)); d.text((1860, 50), ts, font=f, fill=(235, 235, 235, 255), anchor="ra")
    d.ellipse((1800, 990, 1830, 1020), fill=(220, 40, 40, 255)); d.text((1785, 1005), "REC", font=f, fill=(235, 235, 235, 255), anchor="rm"); return im

items = {
    "S04c_loan1": loan(1, "壱千八百万", "令和八年三月十日"), "S04c_loan2": loan(2, "壱千五百万", "令和八年四月二日"), "S04c_loan3": loan(3, "壱千四百万", "令和八年五月十五日"),
    "S06f_cic": report("CIC", "株式会社シー・アイ・シー（割賦販売法・貸金業法指定信用情報機関）"),
    "S06g_jicc": report("JICC", "株式会社日本信用情報機構（貸金業法指定信用情報機関）"),
    "S06g_ksc": report("KSC", "全国銀行個人信用情報センター"),
    "S08i_form_blank": form("令和　　年　　月　　日"), "S09a_form": form("令和八年十月三日"),
    "S08o_law": law(), "S08p_calendar": calendar(),
    "S08h_chat": chat([("video", "2:14", "8月25日(火)"), ("video", "2:14", "9月2日(水)"), ("video", "2:14", "9月10日(木)")], "翔太"),
    "S13a_voice": chat([("voice", "0:12", "6月30日(火)")], "お母さん"),
    "card_H2b": card("この動画は、誰が作ったのか。", 92), "card_H3": card("母が遺したビデオレター", 120), "card_S08q": card("この後――母の動画が、もう一度流れる", 78),
    "corner_S01a": corner("三年前"), "corner_S02a": corner("七月三日　通夜"), "corner_S04a": corner("八月十九日　四十九日"),
    "corner_S07a": corner("千葉県警"), "corner_S08a": corner("九月"), "corner_S12a": corner("十一月"), "cctv_S03a": cctv("2026/07/03 23:41:12"),
}
for k, im in items.items():
    im.save(os.path.join(OUT, k + ".png"))
# 확인 시트
thumbs = []
for k, im in items.items():
    t = im.convert("RGBA"); bg = Image.new("RGBA", t.size, (60, 64, 72, 255)); bg.alpha_composite(t); t = bg.convert("RGB"); t.thumbnail((380, 300)); thumbs.append((k, t))
cols = 6; sheet = Image.new("RGB", (cols * 400, ((len(thumbs) + cols - 1) // cols) * 340), (30, 30, 30)); dd = ImageDraw.Draw(sheet)
for i, (k, t) in enumerate(thumbs):
    x, y = (i % cols) * 400, (i // cols) * 340; sheet.paste(t, (x + 10, y + 34)); dd.text((x + 10, y + 6), k, font=F(22), fill=(255, 220, 120))
sheet.save(os.path.join(ROOT, "productions", "aihaha-ja", "PHASE4_화면서류그래픽.jpg"), quality=86)
print(len(items))
