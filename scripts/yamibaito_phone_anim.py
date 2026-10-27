#!/usr/bin/env python3
"""『時給5万円の罠』 폰 화면 컷 = 정지 키프레임 + 실제 스마트폰 UI 애니메이션 로컬 합성(고니감독님 지적 2026-10-25).
i2v는 합성 화면 글자를 뭉갠다(제20장 10 ①) → 화면이 보이는 컷은 전부 정지 판 위에 프레임 단위로 실제 UI(알림 배너 슬라이드·대화 말풍선 도착·
스크롤·버튼 누름·발신/착신 화면)를 원근 합성하고 편집 푸시인으로 교체 클립을 만든다. 誓約書 컷(S02bd)은 가로쓰기로 재합성.
    python3 scripts/yamibaito_phone_anim.py [S02a,S02d,...]   → assets/video-overrides/yamibaito/sceneNN.mp4 + out/fin/phone_anim/<id>-{0,mid,end}.jpg
"""
import json, math, os, subprocess, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from yamibaito_ja_overlay import order_quad, warp_canvas, SW, SH, GO_R, GO_B, MIN_B, font
KF = os.path.join(ROOT, "assets", "portraits", "yamibaito-keyframes")
BASE = os.path.join(KF, "_v2")  # 합성 전 원본(무지 화면)
OUT = os.path.join(ROOT, "assets", "video-overrides", "yamibaito")
QA = os.path.join(ROOT, "out", "fin", "phone_anim")
SB = os.path.join(ROOT, "scripts", "storyboard", "yamibaito.json")
QUADS = json.load(open(os.path.join(ROOT, "productions", "yamibaito-ja", "screen_quads.json")))
QUADS.update({"S02a": [[900, 610], [1080, 505], [1425, 790], [1235, 905]], "S02k": None})  # S02k는 새 키프레임에서 검출
W, H, FPS = 1920, 1080, 24  # finalize CLIPS로 직접 덮는 1080p(조립 720p 통일을 우회, 고니감독님 2026-10-26 지시 ④)
SS = 2  # UI 캔버스 슈퍼샘플(글자 선명도)
HD = os.path.join(ROOT, "out", "fin", "hd")
INK = (28, 30, 36); GREY = (120, 124, 134); LINE_BG = (170, 186, 212); GREEN = (111, 206, 88); RED = (226, 54, 54); BLUE = (0, 112, 214)


def ease(t):
    t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3


def spring(t):  # 배너 도착(살짝 오버슈트)
    t = min(max(t, 0.0), 1.0); return 1 - math.exp(-6 * t) * math.cos(7 * t)


def tl(d, s, f):
    return d.textlength(s, font=f)


# ─── 공통 UI 부품 ─────────────────────────────────────────────────────────────
def status_bar(d, dark=False, time="1:02"):
    col = (245, 245, 248) if dark else INK
    d.text((52, 46), time, font=font(GO_B, 38), fill=col, anchor="lm")
    x = SW - 230
    for i, h in enumerate((10, 16, 22, 28)):  # 전파 막대
        d.rounded_rectangle((x + i * 14, 60 - h, x + i * 14 + 9, 60), 2, fill=col)
    d.text((x + 72, 46), "5G", font=font(GO_B, 30), fill=col, anchor="lm")
    bx = SW - 100
    d.rounded_rectangle((bx, 30, bx + 62, 62), 7, outline=col, width=3); d.rounded_rectangle((bx + 64, 40, bx + 68, 52), 2, fill=col)
    d.rounded_rectangle((bx + 5, 35, bx + 5 + 38, 57), 4, fill=col)  # 잔량 약 70%


def home_bar(d, dark=False):
    d.rounded_rectangle((SW / 2 - 130, SH - 26, SW / 2 + 130, SH - 16), 5, fill=(230, 230, 235) if dark else (20, 20, 24))


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n" or tl(d, cur + ch, f) > maxw:
            lines.append(cur); cur = "" if ch == "\n" else ch
        else:
            cur += ch
    if cur: lines.append(cur)
    return lines


def chat_header(d, name="倉庫スタッフ募集（公式）", sub="オンライン"):
    d.rectangle((0, 88, SW, 200), fill=(248, 248, 250)); d.line((0, 200, SW, 200), fill=(215, 215, 220), width=2)
    d.line((40, 144, 58, 126), fill=BLUE, width=5); d.line((40, 144, 58, 162), fill=BLUE, width=5)  # 뒤로
    d.ellipse((90, 112, 158, 180), fill=(60, 66, 80)); d.text((124, 146), "倉", font=font(GO_B, 30), fill="white", anchor="mm")
    d.text((180, 134), name, font=font(GO_B, 34), fill=INK, anchor="lm"); d.text((180, 172), sub, font=font(GO_R, 24), fill=(90, 160, 90), anchor="lm")
    d.ellipse((SW - 70, 138, SW - 60, 148), fill=GREY); d.ellipse((SW - 54, 138, SW - 44, 148), fill=GREY); d.ellipse((SW - 38, 138, SW - 28, 148), fill=GREY)


def chat_input(d):
    d.rectangle((0, SH - 150, SW, SH), fill=(248, 248, 250)); d.line((0, SH - 150, SW, SH - 150), fill=(215, 215, 220), width=2)
    d.text((36, SH - 88), "+", font=font(GO_R, 50), fill=BLUE, anchor="lm")
    d.rounded_rectangle((90, SH - 118, SW - 100, SH - 58), 30, fill="white", outline=(205, 205, 210), width=2)
    d.text((115, SH - 88), "メッセージを入力", font=font(GO_R, 28), fill=(170, 170, 178), anchor="lm")
    d.ellipse((SW - 84, SH - 112, SW - 36, SH - 64), fill=BLUE); d.rounded_rectangle((SW - 65, SH - 100, SW - 55, SH - 82), 5, fill="white")
    home_bar(d)


def bubble(d, c, x, y, lines, f, side, width=None, time=None, read=False, scale=1.0):
    """말풍선. side L(상대, 흰)·R(나, 초록). 반환: 다음 y."""
    pad, lh = 26, int(f.size * 1.45)
    w = width or (max(tl(d, s, f) for s in lines) + pad * 2)
    h = lh * len(lines) + pad * 2 - 8
    if side == "L":
        box = (x, y, x + w, y + h); fill, col = (255, 255, 255), INK
    else:
        box = (SW - 40 - w, y, SW - 40, y + h); fill, col = GREEN, INK
    if scale < 1.0:  # 도착 애니메이션(작게→제 크기)
        cx, cy = (box[0] + box[2]) / 2, box[3]
        box = (cx - (box[2] - box[0]) / 2 * scale, cy - h * scale, cx + (box[2] - box[0]) / 2 * scale, cy)
        d.rounded_rectangle(box, 26, fill=fill); return y + h + 14
    d.rounded_rectangle(box, 26, fill=fill)
    for i, s in enumerate(lines):
        d.text((box[0] + pad, box[1] + pad + i * lh), s, font=f, fill=col)
    if time:
        tx = box[2] + 14 if side == "L" else box[0] - 14
        if read and side == "R": d.text((tx, box[3] - 44), "既読", font=font(GO_R, 20), fill=GREY, anchor="ra")
        d.text((tx, box[3] - 20), time, font=font(GO_R, 20), fill=GREY, anchor="la" if side == "L" else "ra")
    return y + h + 14


def typing_dots(d, x, y, t):
    d.rounded_rectangle((x, y, x + 120, y + 64), 26, fill="white")
    for i in range(3):
        k = 0.5 + 0.5 * math.sin((t * 6 - i * 0.9))
        d.ellipse((x + 24 + i * 30, y + 26 - 6 * k, x + 40 + i * 30, y + 42 - 6 * k), fill=(150, 150, 158))


OFFER = ["【急募】倉庫内 軽作業スタッフ", "日給ではなく、時給です。", "・面接なし／履歴書不要", "・即日現金手渡し", "・今夜22時〜 送迎あり"]


def offer_card(d, y, pressed=0.0, sent=False):
    """시급 5만 엔 구인 카드 + 「応募する」 버튼. pressed 0~1 = 눌림 진하기."""
    x, w = 40, SW - 120
    d.rounded_rectangle((x, y, x + w, y + 470), 26, fill="white")
    d.text((x + 26, y + 28), OFFER[0], font=font(GO_B, 30), fill=INK)
    d.text((x + 26, y + 84), "時給", font=font(GO_B, 36), fill=RED); d.text((x + 108, y + 66), "50,000", font=font(GO_B, 78), fill=RED); d.text((x + 390, y + 84), "円", font=font(GO_B, 36), fill=RED)
    yy = y + 170
    for s in OFFER[2:]:
        d.text((x + 26, yy), s, font=font(GO_R, 28), fill=(60, 60, 66)); yy += 44
    by = y + 330
    col = tuple(int(c * (1 - 0.35 * pressed)) for c in RED)
    d.rounded_rectangle((x + 26, by, x + w - 26, by + 108), 22, fill=col)
    d.text((x + w / 2, by + 54), "送信中…" if sent else "応募する", font=font(GO_B, 40), fill="white", anchor="mm")
    return y + 470 + 14


MSGS = [("L", ["はじめまして！", "求人をご覧いただき", "ありがとうございます"], "1:02"), ("L", ["人手が足りず、", "今夜からでも入れる方を", "急募しています。"], "1:02"),
        ("L", ["内容はこちらです↓"], "1:03"), ("OFFER", None, "1:03")]


def chat_canvas(t, show=4, scroll=0, pressed=0.0, sent=False, confirm=0.0, conds=False, arrive=None):
    """LINE풍 대화 화면. show = 보이는 메시지 수, arrive = (index, 도착 진행 0~1), conds = 조건 3줄 대화."""
    c = Image.new("RGBA", (SW, SH), LINE_BG + (255,)); d = ImageDraw.Draw(c)
    y = 230 - scroll
    f = font(GO_R, 30)
    d.rounded_rectangle((SW / 2 - 70, y - 10, SW / 2 + 70, y + 30), 20, fill=(140, 156, 186)); d.text((SW / 2, y + 10), "今日", font=font(GO_R, 22), fill="white", anchor="mm"); y += 50
    seq = MSGS if not conds else [("R", ["応募します。", "よろしくお願いします。"], "1:04"), ("L", ["ありがとうございます。", "採用です。"], "1:04"),
                                 ("L", ["条件は三つだけ。"], "1:05"), ("L", ["ひとつ。身分証を預かります。"], "1:05"), ("L", ["ふたつ。スマホは当日回収。"], "1:05"),
                                 ("L", ["みっつ。口外すれば、", "家族にも責任。"], "1:06"), ("L", ["同意なら、誓約書を書いて", "写真を送ってください。"], "1:06")]
    for i, (side, lines, tm) in enumerate(seq[:show]):
        sc = 1.0
        if arrive and arrive[0] == i:
            if arrive[1] < 0.55:  # 입력 중 점
                typing_dots(d, 40, y, t); y += 80; continue
            sc = spring((arrive[1] - 0.55) / 0.45)
        if side == "OFFER":
            y = offer_card(d, y, pressed, sent)
        else:
            y = bubble(d, c, 40, y, lines, f, side, time=tm, read=True, scale=min(sc, 1.0))
    # 헤더·입력줄·상태바는 스크롤 위에
    d.rectangle((0, 0, SW, 88), fill=(248, 248, 250)); status_bar(d); chat_header(d); chat_input(d)
    if confirm > 0:  # 응모 접수 시트
        k = ease(confirm)
        ov = Image.new("RGBA", (SW, SH), (0, 0, 0, int(120 * k))); c.alpha_composite(ov); d = ImageDraw.Draw(c)
        sy = SH - int(520 * k)
        d.rounded_rectangle((0, sy, SW, SH + 60), 40, fill=(255, 255, 255))
        d.ellipse((SW / 2 - 60, sy + 50, SW / 2 + 60, sy + 170), fill=GREEN); d.line((SW / 2 - 28, sy + 112, SW / 2 - 6, sy + 136, SW / 2 + 30, sy + 86), fill="white", width=10, joint="curve")
        d.text((SW / 2, sy + 230), "応募を受け付けました", font=font(GO_B, 40), fill=INK, anchor="mm")
        d.text((SW / 2, sy + 290), "担当者より折り返しご連絡します", font=font(GO_R, 28), fill=GREY, anchor="mm")
        d.rounded_rectangle((60, sy + 360, SW - 60, sy + 460), 24, fill=BLUE); d.text((SW / 2, sy + 410), "OK", font=font(GO_B, 36), fill="white", anchor="mm")
    return c


def lock_canvas(t, arrivals):
    """잠금 화면 + 알림 배너 도착(위에서 스프링 슬라이드). arrivals = 배너별 도착 시각(초)."""
    c = Image.new("RGBA", (SW, SH), (12, 16, 30, 255)); d = ImageDraw.Draw(c)
    for yy in range(SH):  # 어두운 남색 그라데이션 벽지
        k = yy / SH; d.line((0, yy, SW, yy), fill=(int(14 + 30 * k), int(18 + 24 * k), int(40 + 46 * k)))
    d.rounded_rectangle((SW / 2 - 40, 30, SW / 2 + 40, 42), 6, fill=(40, 40, 48))  # 잠금 자물쇠 자리
    d.text((SW / 2, 240), "1:02", font=font(GO_R, 200), fill=(235, 236, 242), anchor="mm")
    d.text((SW / 2, 370), "10月23日 木曜日", font=font(GO_R, 40), fill=(205, 208, 220), anchor="mm")
    banners = [("【急募】時給50,000円", "倉庫内作業・今夜から。面接なし、履歴書不要。"), ("まだ募集中です", "即日現金手渡し。送迎あります。"), ("あと2名で締切ります", "返信お待ちしています。")]
    y = 520
    for i, (title, body) in enumerate(banners):
        if t < arrivals[i]: continue
        k = spring((t - arrivals[i]) / 0.55)
        yb = y + int((1 - k) * -260)
        card = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((36, yb, SW - 36, yb + 170), 34, fill=(255, 255, 255, 215))
        cd.rounded_rectangle((60, yb + 30, 150, yb + 120), 22, fill=(60, 180, 90)); cd.rounded_rectangle((80, yb + 60, 130, yb + 92), 12, fill="white"); cd.ellipse((98, yb + 86, 110, yb + 102), fill="white")
        cd.text((176, yb + 42), "メッセージ", font=font(GO_R, 22), fill=(80, 80, 88)); cd.text((SW - 70, yb + 42), "今", font=font(GO_R, 22), fill=(80, 80, 88), anchor="ra")
        cd.text((176, yb + 74), title, font=font(GO_B, 30), fill=INK); cd.text((176, yb + 118), body, font=font(GO_R, 24), fill=(60, 60, 66))
        c.alpha_composite(card); y += 190
    d = ImageDraw.Draw(c); status_bar(d, dark=True)
    d.ellipse((60, SH - 200, 160, SH - 100), fill=(255, 255, 255, 70)); d.ellipse((SW - 160, SH - 200, SW - 60, SH - 100), fill=(255, 255, 255, 70))
    home_bar(d, dark=True)
    return c


def bank_canvas(t):
    c = Image.new("RGBA", (SW, SH), (243, 244, 247, 255)); d = ImageDraw.Draw(c)
    d.rectangle((0, 0, SW, 230), fill=(0, 70, 150)); status_bar(d, dark=True)
    d.text((40, 150), "みらいネット銀行", font=font(GO_B, 40), fill="white", anchor="lm"); d.text((SW - 40, 150), "ログアウト", font=font(GO_R, 24), fill=(200, 215, 240), anchor="rm")
    k = ease((t - 0.35) / 0.6)
    if k <= 0:  # 로딩
        for i in range(3):
            a = 0.5 + 0.5 * math.sin(t * 8 - i * 1.2); d.ellipse((SW / 2 - 50 + i * 40, 600, SW / 2 - 30 + i * 40, 620), fill=tuple(int(150 + 60 * a) for _ in range(3)))
        home_bar(d); return c
    card = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    A = int(255 * k)
    cd.rounded_rectangle((36, 270, SW - 36, 640), 30, fill=(255, 255, 255, A))
    cd.text((70, 320), "普通預金", font=font(GO_R, 28), fill=(90, 90, 96, A)); cd.text((SW - 70, 320), "本店 ****2341", font=font(GO_R, 24), fill=(120, 120, 128, A), anchor="ra")
    cd.text((70, 390), "残高", font=font(GO_R, 28), fill=(90, 90, 96, A))
    cd.text((SW - 70, 470), "¥3,217", font=font(GO_B, 104), fill=(24, 24, 30, A), anchor="rm")
    cd.text((SW - 70, 545), "10/23 1:02 時点", font=font(GO_R, 22), fill=(140, 140, 148, A), anchor="ra")
    for i, s in enumerate(("振込", "入出金明細", "カード")):
        cd.rounded_rectangle((60 + i * 210, 580, 230 + i * 210, 626), 23, fill=(0, 70, 150, A)); cd.text((145 + i * 210, 603), s, font=font(GO_B, 24), fill=(255, 255, 255, A), anchor="mm")
    cd.text((40, 690), "入出金明細", font=font(GO_B, 30), fill=(40, 40, 46, A))
    y = 750
    rows = (("10/20", "家賃 口座振替", "引落不能", True), ("10/18", "コンビニATM 出金", "-10,000", False), ("10/15", "給与 コンビニ", "+48,320", False), ("10/10", "奨学金返還", "-14,000", False), ("10/05", "携帯電話料金", "-6,480", False), ("10/01", "電気料金", "-5,130", False))
    for date, name, amt, bad in rows:
        cd.rounded_rectangle((36, y, SW - 36, y + 96), 18, fill=(255, 255, 255, A))
        cd.text((60, y + 48), date, font=font(GO_R, 24), fill=(120, 120, 128, A), anchor="lm"); cd.text((160, y + 48), name, font=font(GO_R, 28), fill=(40, 40, 46, A), anchor="lm")
        col = (210, 40, 40, A) if (bad or amt.startswith("-")) else (30, 120, 60, A)
        cd.text((SW - 60, y + 48), amt, font=font(GO_B, 30), fill=col, anchor="rm")
        if bad: cd.rounded_rectangle((160, y + 66, 330, y + 90), 12, fill=(255, 230, 230, A)); cd.text((245, y + 78), "残高不足", font=font(GO_B, 18), fill=(200, 40, 40, A), anchor="mm")
        y += 110
    c.alpha_composite(card); d = ImageDraw.Draw(c); home_bar(d); return c


def sns_canvas(t, photos, scroll):
    c = Image.new("RGBA", (SW, SH), (255, 255, 255, 255)); d = ImageDraw.Draw(c)
    y = 190 - scroll
    posts = (("yuki_0712", "最高の海！ 卒業旅行1日目 🌴".replace(" 🌴", ""), "いいね！ 213件", "4時間前"), ("ryo.travel", "夜景やばい。来てよかった", "いいね！ 158件", "6時間前"), ("mai_mai", "卒業旅行3日目。みんなありがとう", "いいね！ 301件", "昨日"))
    for (user, cap, likes, ago), ph in zip(posts, photos):
        d.ellipse((30, y, 100, y + 70), fill=(200, 200, 210)); d.ellipse((34, y + 4, 96, y + 66), outline=(230, 80, 120), width=4)
        d.text((120, y + 35), user, font=font(GO_B, 28), fill=INK, anchor="lm"); d.text((SW - 40, y + 35), "・・・", font=font(GO_B, 22), fill=INK, anchor="rm")
        c.paste(ph.resize((SW, SW)), (0, y + 90))
        yy = y + 90 + SW + 20
        d.polygon([(44, yy + 12), (54, yy + 2), (64, yy + 12), (74, yy + 2), (84, yy + 12), (64, yy + 36)], outline=INK, width=3)  # 하트(선)
        d.ellipse((120, yy, 156, yy + 36), outline=INK, width=3); d.polygon([(206, yy + 2), (240, yy + 18), (206, yy + 36)], outline=INK, width=3)
        d.text((40, yy + 60), likes, font=font(GO_B, 26), fill=INK); d.text((40, yy + 100), user, font=font(GO_B, 26), fill=INK); d.text((40 + tl(d, user, font(GO_B, 26)) + 14, yy + 100), cap, font=font(GO_R, 26), fill=INK)
        d.text((40, yy + 140), ago, font=font(GO_R, 22), fill=GREY)
        y = yy + 200
    d.rectangle((0, 0, SW, 180), fill="white"); d.line((0, 180, SW, 180), fill=(225, 225, 230), width=2); status_bar(d)
    d.text((40, 136), "Photogram", font=font(MIN_B, 44), fill=INK, anchor="lm")
    d.polygon([(SW - 200, 136), (SW - 190, 124), (SW - 180, 136), (SW - 170, 124), (SW - 160, 136), (SW - 180, 160)], outline=INK, width=3)
    d.polygon([(SW - 110, 122), (SW - 60, 136), (SW - 110, 150)], outline=INK, width=3)
    d.rectangle((0, SH - 130, SW, SH), fill="white"); d.line((0, SH - 130, SW, SH - 130), fill=(225, 225, 230), width=2)
    for i in range(5):
        x = 72 + i * 144; d.rounded_rectangle((x - 18, SH - 100, x + 18, SH - 64), 8, outline=INK, width=3, fill=INK if i == 0 else None)
    home_bar(d); return c


def search_canvas(t):
    c = Image.new("RGBA", (SW, SH), (255, 255, 255, 255)); d = ImageDraw.Draw(c); status_bar(d)
    d.rounded_rectangle((30, 100, SW - 30, 180), 24, fill=(238, 238, 242)); d.text((60, 140), "警察 相談 電話 番号", font=font(GO_R, 30), fill=INK, anchor="lm"); d.ellipse((SW - 90, 120, SW - 50, 160), outline=GREY, width=3)
    d.line((0, 230, SW, 230), fill=(225, 225, 230), width=2); d.text((40, 205), "すべて", font=font(GO_B, 24), fill=BLUE, anchor="lm"); d.line((40, 229, 110, 229), fill=BLUE, width=4); d.text((150, 205), "画像", font=font(GO_R, 24), fill=GREY, anchor="lm"); d.text((230, 205), "ニュース", font=font(GO_R, 24), fill=GREY, anchor="lm")
    y = 280
    d.text((40, y), "警察庁 › 相談窓口", font=font(GO_R, 22), fill=GREY); y += 40
    d.text((40, y), "警察相談専用電話「#9110」", font=font(GO_B, 36), fill=(26, 13, 171)); y += 60
    for s in ("犯罪やトラブルに巻き込まれそうなど、緊急で", "はない相談は #9110 へ。全国共通・各都道府県", "警察本部の相談窓口につながります。"):
        d.text((40, y), s, font=font(GO_R, 26), fill=(60, 60, 66)); y += 38
    y += 20
    d.rounded_rectangle((40, y, SW - 40, y + 120), 26, fill=(40, 170, 90)); d.ellipse((70, y + 35, 120, y + 85), fill="white"); d.text((SW / 2 + 20, y + 60), "#9110 に発信", font=font(GO_B, 40), fill="white", anchor="mm"); y += 160
    d.rounded_rectangle((40, y, SW - 40, y + 90), 20, fill=(255, 240, 240)); d.text((SW / 2, y + 45), "緊急の場合は 110 番へ", font=font(GO_B, 28), fill=(190, 40, 40), anchor="mm"); y += 130
    d.line((40, y, SW - 40, y), fill=(230, 230, 235), width=2); y += 30
    d.text((40, y), "闇バイト相談 › 若者向け", font=font(GO_R, 22), fill=GREY); y += 40
    d.text((40, y), "「高額バイト」に応募してしまったら", font=font(GO_B, 32), fill=(26, 13, 171)); y += 56
    for s in ("一人で抱え込まず、すぐに警察へ。被害者として", "保護されます。身分証を渡してしまった場合も…"):
        d.text((40, y), s, font=font(GO_R, 26), fill=(60, 60, 66)); y += 38
    home_bar(d); return c


def call_canvas(t, number="#9110", name="警察相談専用電話", dial=True):
    c = Image.new("RGBA", (SW, SH), (24, 26, 34, 255)); d = ImageDraw.Draw(c)
    for yy in range(SH):
        k = yy / SH; d.line((0, yy, SW, yy), fill=(int(28 + 20 * k), int(30 + 18 * k), int(40 + 24 * k)))
    status_bar(d, dark=True)
    d.text((SW / 2, 300), number, font=font(GO_B, 96), fill=(240, 240, 245), anchor="mm")
    d.text((SW / 2, 390), name, font=font(GO_R, 36), fill=(200, 200, 210), anchor="mm")
    dots = "・" * (1 + int(t * 2) % 3)
    d.text((SW / 2, 460), ("発信中" + dots) if dial else "通話中 00:0%d" % int(t), font=font(GO_R, 30), fill=(170, 170, 180), anchor="mm")
    for i, lab in enumerate(("消音", "キーパッド", "スピーカー")):
        x = 150 + i * 210; d.ellipse((x - 70, 760, x + 70, 900), fill=(255, 255, 255, 40)); d.text((x, 950), lab, font=font(GO_R, 24), fill=(220, 220, 228), anchor="mm")
    for i, lab in enumerate(("追加", "FaceTime", "連絡先")):
        x = 150 + i * 210; d.ellipse((x - 70, 1020, x + 70, 1160), fill=(255, 255, 255, 40)); d.text((x, 1210), lab, font=font(GO_R, 24), fill=(220, 220, 228), anchor="mm")
    d.ellipse((SW / 2 - 80, 1290, SW / 2 + 80, 1450), fill=(230, 60, 60)); d.rounded_rectangle((SW / 2 - 36, 1358, SW / 2 + 36, 1382), 12, fill="white")
    home_bar(d, dark=True); return c


def incoming_canvas(t):
    c = Image.new("RGBA", (SW, SH), (18, 20, 30, 255)); d = ImageDraw.Draw(c)
    for yy in range(SH):
        k = yy / SH; d.line((0, yy, SW, yy), fill=(int(20 + 26 * k), int(22 + 22 * k), int(34 + 30 * k)))
    status_bar(d, dark=True)
    d.ellipse((SW / 2 - 110, 260, SW / 2 + 110, 480), fill=(120, 124, 140)); d.text((SW / 2, 370), "母", font=font(GO_B, 100), fill="white", anchor="mm")
    d.text((SW / 2, 570), "母", font=font(GO_B, 72), fill=(240, 240, 245), anchor="mm"); d.text((SW / 2, 650), "携帯", font=font(GO_R, 32), fill=(190, 190, 200), anchor="mm")
    d.text((SW / 2, 720), "着信中…", font=font(GO_R, 32), fill=(170, 170, 180), anchor="mm")
    d.text((SW / 2 - 210, 1110), "リマインダー", font=font(GO_R, 22), fill=(220, 220, 228), anchor="mm"); d.text((SW / 2 + 210, 1110), "メッセージ", font=font(GO_R, 22), fill=(220, 220, 228), anchor="mm")
    d.ellipse((SW / 2 - 240, 1040, SW / 2 - 180, 1080), fill=(255, 255, 255, 60)); d.ellipse((SW / 2 + 180, 1040, SW / 2 + 240, 1080), fill=(255, 255, 255, 60))
    p = 0.5 + 0.5 * math.sin(t * 5)
    for cx, col, lab in ((150, (230, 60, 60), "拒否"), (SW - 150, (60, 200, 90), "応答")):
        if col[1] == 200:
            r = 90 + 26 * p; ov = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); od = ImageDraw.Draw(ov); od.ellipse((cx - r, 1300 - r, cx + r, 1300 + r), fill=(60, 200, 90, int(90 * (1 - p)))); c.alpha_composite(ov); d = ImageDraw.Draw(c)
        d.ellipse((cx - 80, 1220, cx + 80, 1380), fill=col); d.rounded_rectangle((cx - 34, 1290, cx + 34, 1312), 11, fill="white")
        d.text((cx, 1430), lab, font=font(GO_R, 26), fill=(230, 230, 236), anchor="mm")
    home_bar(d, dark=True); return c


def pledge_canvas():
    """誓約書 — 종이 윗변 = 멀리 있는 변, 가로쓰기(고니감독님 지적: 글자가 90° 돌아감). 캔버스 1000x1300(세로 A4 비율)."""
    w, h = 1000, 1300
    c = Image.new("RGBA", (w, h), (255, 255, 255, 0)); d = ImageDraw.Draw(c)
    d.text((w / 2, 130), "誓　約　書", font=font(MIN_B, 92), fill=(30, 30, 40), anchor="mm")
    y = 260
    for s in ("一、業務内容を他言しません。", "一、連絡はこのアカウントのみ使用します。", "一、口外した場合、本人および家族が", "　　一切の責任を負います。"):
        d.text((80, y), s, font=font(MIN_B, 44), fill=(30, 30, 40)); y += 78
    y += 40
    d.text((80, y), "氏名", font=font(MIN_B, 44), fill=(30, 30, 40)); d.line((200, y + 52, 760, y + 52), fill=(60, 60, 70), width=3)
    d.text((860, y + 20), "印", font=font(MIN_B, 44), fill=(30, 30, 40), anchor="mm"); d.ellipse((815, y - 25, 905, y + 65), outline=(150, 150, 160), width=3)
    return c


# ─── 컷 정의 ──────────────────────────────────────────────────────────────────
def load_photos():
    ph = []
    for n in ("sns-beach", "sns-night", "sns-street"):
        p = os.path.join(ROOT, "assets", "portraits", "yamibaito-phone-fix", f"{n}-1.png")
        ph.append(Image.open(p).convert("RGB") if os.path.exists(p) else Image.new("RGB", (SW, SW), (90, 130, 170)))
    return ph


def detect_quad(path, roi=None):
    """무지(밝은) 화면 사각형 검출 → 4점."""
    a = cv2.imread(path); g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    m = (g > 215).astype(np.uint8) * 255
    if roi: x0, y0, x1, y1 = roi; mm = np.zeros_like(m); mm[y0:y1, x0:x1] = m[y0:y1, x0:x1]; m = mm
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cnts, key=cv2.contourArea)
    return cv2.boxPoints(cv2.minAreaRect(c)).astype(int).tolist()


def cut_defs():
    photos = load_photos()
    D = {}
    D["H0"] = dict(top="up", frame=lambda t, s: lock_canvas(t, [0.15, 0.8, 1.45]), cam="pushto:1.25")
    D["S02a"] = dict(top="up", frame=lambda t, s: lock_canvas(t, [0.4, 1.5, 2.7]), cam="pushto:1.45")
    def s02b(t, s):
        times = [0.2, 1.3, 2.5, 3.4]
        n = sum(1 for x in times if t >= x); arr = None
        if n and t - times[n - 1] < 0.9: arr = (n - 1, (t - times[n - 1]) / 0.9)
        return chat_canvas(t, show=max(n, 1), arrive=arr)
    D["S02b"] = dict(top="up", frame=s02b, cam="pushto:1.6")
    D["S02d"] = dict(top="up", frame=lambda t, s: chat_canvas(t, show=4, scroll=int(420 * ease((t - 0.7) / 1.6))), cam="push", sway=True)
    D["S02g"] = dict(top="up", frame=lambda t, s: bank_canvas(t), cam="pushto:1.6")
    D["S02k"] = dict(top="up", frame=lambda t, s: sns_canvas(t, photos, int(60 + 900 * ease((t - 0.3) / (s - 0.5)))), cam="push", roi=(300, 0, 1900, 1440))
    D["S02ba"] = dict(top="up", frame=lambda t, s: chat_canvas(t, show=min(7, 3 + int(t / 1.1)), conds=True, scroll=60), cam="pushto:1.3")
    def s02bi(t, s):
        pr = 0.0; sent = False; conf = 0.0
        if 1.0 <= t < 1.3: pr = min(1, (t - 1.0) / 0.1)
        elif t >= 1.3: pr = max(0, 1 - (t - 1.3) / 0.2); sent = t >= 1.35
        if t >= 2.0: conf = (t - 2.0) / 0.45
        return chat_canvas(t, show=4, scroll=640, pressed=pr, sent=sent, confirm=conf)
    D["S02bi"] = dict(top="right", frame=s02bi, cam="static")
    D["S03b"] = dict(top="up", frame=lambda t, s: search_canvas(t), cam="pushto:1.4")
    D["S03c"] = dict(top="up", frame=lambda t, s: call_canvas(t), cam="push", sway=True)
    D["S03e"] = dict(top="up", frame=lambda t, s: incoming_canvas(t), cam="push")
    return D


def zoom_frame(img, z, cx=0.5, cy=0.5, dx=0.0, dy=0.0):
    h, w = img.shape[:2]
    cw, ch = w / z, h / z
    x0 = min(max(w * cx - cw / 2 + dx, 0), w - cw); y0 = min(max(h * cy - ch / 2 + dy, 0), h - ch)
    M = np.float32([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA if z < 1.01 else cv2.INTER_LINEAR)


def screen_fx(base, q):
    """유리 반사(장면을 뒤집어 흐린 판, Screen 12%)·화면 글로우·비네팅 마스크를 한 번 만든다(고니감독님 지시 ②③)."""
    H_, W_ = base.shape[:2]
    mask = np.zeros((H_, W_), np.uint8); cv2.fillConvexPoly(mask, np.array(q, np.int32), 255)
    m = mask.astype(np.float32) / 255
    refl = cv2.GaussianBlur(cv2.flip(base, 0), (0, 0), 25).astype(np.float32)
    # 밝은 광원만 남긴 반사(형광등·창)
    g = cv2.cvtColor(refl.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    hi = np.clip((g - 110) / 145, 0, 1)[..., None]
    refl = refl * hi * 0.12 * m[..., None]
    # 비네팅: 화면 가장자리 0.88
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5); dist = np.clip(dist / max(dist.max(), 1) * 3, 0, 1)
    vig = (0.88 + 0.12 * dist)[..., None]
    # 글로우: 화면 바깥으로 번지는 발광
    glow_m = cv2.GaussianBlur(cv2.dilate(mask, np.ones((25, 25), np.uint8)), (0, 0), 38).astype(np.float32) / 255
    glow_m = np.clip(glow_m - m, 0, 1)[..., None]
    return m[..., None], refl, vig, glow_m


def render(sid, spec, sec, base_path, quad, extra=None):
    os.makedirs(HD, exist_ok=True)
    out = os.path.join(HD, f"scene{NUM[sid]:02d}.mp4")
    base = cv2.imread(base_path)
    if extra: base = extra(base)
    q = order_quad(quad, spec["top"])
    m, refl, vig, glow_m = screen_fx(base, q)
    n = int(math.ceil(sec * FPS))
    rng = np.random.default_rng(7); sx = sy = 0.0
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-an", out], stdin=subprocess.PIPE)
    os.makedirs(QA, exist_ok=True)
    for i in range(n):
        t = i / FPS
        canvas = spec["frame"](t, sec)
        if SS > 1: canvas = canvas.resize((SW * SS, SH * SS), Image.LANCZOS)
        fr = warp_canvas(base, canvas, q, "lcd").astype(np.float32)
        fr = fr * (1 - m) + (fr * vig + refl) * m                      # 비네팅 + 유리 반사(Screen 근사)
        col = (fr * m).sum(axis=(0, 1)) / max(m.sum(), 1)               # 화면 평균색으로 글로우
        fr = np.clip(fr + glow_m * col * 0.22, 0, 255).astype(np.uint8)
        k = i / n
        if spec["cam"] == "push": z, cx, cy = 1.0 + 0.05 * k, 0.5, 0.5
        elif spec["cam"].startswith("pushto"):  # 폰 중심으로 다가가 화면을 크게(제8장 4-2·휴대폰 가독성)
            zm = float(spec["cam"].split(":")[1]); qc = np.mean(q, axis=0)
            z = 1.0 + (zm - 1.0) * ease(k / 0.85); cx, cy = qc[0] / base.shape[1], qc[1] / base.shape[0]
        else: z, cx, cy = 1.0, 0.5, 0.5
        if spec.get("sway"):  # 손에 든 폰: 미세 핸드헬드
            sx = 0.9 * sx + rng.normal(0, 1.2); sy = 0.9 * sy + rng.normal(0, 1.2)
        f = zoom_frame(fr, z, cx, cy, dx=sx, dy=sy)
        p.stdin.write(f.tobytes())
        if i in (0, n // 2, n - 1):
            cv2.imwrite(os.path.join(QA, f"{sid}-{('0', 'mid', 'end')[(0, n // 2, n - 1).index(i)]}.jpg"), f, [cv2.IMWRITE_JPEG_QUALITY, 85])
    p.stdin.close(); p.wait()
    print(f"{sid} → {out} ({n}f)")


def pledge_fix():
    """S02bd: 誓約書 가로쓰기 재합성 + 책상 위 폰에 조건 DM 화면 → 키프레임 교체 + 정지 푸시인."""
    base = cv2.imread(os.path.join(BASE, "S02bd-1.png"))
    paper_q = [(938, 322), (1838, 976), (1257, 1776), (357, 1122)]  # TL=먼 왼쪽, TR=먼 오른쪽, BR=가까운 오른쪽, BL=가까운 왼쪽
    a = warp_canvas(base, pledge_canvas(), paper_q, "paper")
    phone_q = order_quad([[1505, -40], [1966, 220], [1894, 367], [1434, 110]], "left")  # 화면 윗변 = 왼쪽 짧은 변(노치)
    a = warp_canvas(a, chat_canvas(0, show=7, conds=True, scroll=60), phone_q, "lcd")
    cv2.imwrite(os.path.join(KF, "S02bd-1.png"), a)
    return a


SB_SCENES = json.load(open(SB, encoding="utf-8"))["scenes"]
NUM = {s["id"]: i + 1 for i, s in enumerate(SB_SCENES)}
DUR = {s["id"]: s["assembled_s"] + 0.5 for s in SB_SCENES}

if __name__ == "__main__":
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    D = cut_defs()
    for sid, spec in D.items():
        if only and sid not in only: continue
        base_path = os.path.join(BASE, f"{sid}-1.png")
        q = QUADS.get(sid)
        if q is None:
            base_path = os.path.join(KF, f"{sid}-1.png"); q = detect_quad(base_path, spec.get("roi")); print(sid, "검출 quad", q)
        if not os.path.exists(base_path): print("원본 없음", sid); continue
        render(sid, spec, DUR[sid], base_path, q)
    if not only or "S02bd" in only:
        a = pledge_fix()
        from build_yamibaito_overrides import cam
        cam(os.path.join(KF, "S02bd-1.png"), os.path.join(OUT, f"scene{NUM['S02bd']:02d}.mp4"), DUR["S02bd"], "push")
        import build_yamibaito_overrides as ov; ov.W, ov.H = W, H   # 1080p 판(finalize CLIPS용)
        for hd_id, fx in (("S02bd", "push"), ("S07m", "push"), ("S08n", "push")):
            ov.cam(os.path.join(KF, f"{hd_id}-1.png"), os.path.join(HD, f"scene{NUM[hd_id]:02d}.mp4"), DUR[hd_id], fx)
        cv2.imwrite(os.path.join(QA, "S02bd.jpg"), cv2.resize(a, (1280, 720)), [cv2.IMWRITE_JPEG_QUALITY, 85]); print("S02bd 재합성")
