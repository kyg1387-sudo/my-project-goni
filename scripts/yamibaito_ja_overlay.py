#!/usr/bin/env python3
"""『時給5万円の罠』 화면 속 일본어 글자 합성(제11장 3, 로컬·무과금) — bento_ja_overlay.py 방식.
무지로 생성한 키프레임(2560x1440) 위에 실글꼴 UI 캔버스를 원근 변형해 얹는다(발광 화면은 lcd 합성: 화면 밝기 유지 + 글자 + 유리 반사, 제15장 17).
  폰 화면: productions/yamibaito-ja/screen_quads.json(자동 검출 + 수동 보정) 4점.  봉투·서약서: 수동 4점.
  시계(S07m 3:00 · S08a 2:58): 기존 바늘 인페인트 후 바늘을 그린다.  뉴스(S10m): 하단 자막 띠.
원본은 assets/portraits/yamibaito-keyframes/_v2/에 보관하고, 다시 돌리면 _v2에서 새로 만든다.
사용법: python3 scripts/yamibaito_ja_overlay.py [id,...]
"""
import json, os, shutil, sys, math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
F = lambda n: os.path.join(ROOT, "scripts", "fonts", n)
GO_R, GO_B, MIN_B, HAND = F("ZenKakuGothicNew-Regular.ttf"), F("ZenKakuGothicNew-Bold.ttf"), F("ZenOldMincho-Bold.ttf"), F("KleeOne-Regular.ttf")
KF = os.path.join(ROOT, "assets", "portraits", "yamibaito-keyframes")
BAK = os.path.join(KF, "_v2")
QUADS = json.load(open(os.path.join(ROOT, "productions", "yamibaito-ja", "screen_quads.json"), encoding="utf-8"))
QUADS["S02a"] = [[900, 610], [1080, 505], [1425, 790], [1235, 905]]  # 자동 검출이 책상 반사를 잡음 → 수동
QUADS["S02h"] = [[1490, 1215], [1700, 1190], [1720, 1300], [1510, 1330]]  # 바닥 봉투(수동)
QUADS["S02i"] = [[1423, 718], [1625, 777], [1338, 892], [1148, 842]]  # 침대 위 서류(자동 검출 1차)
QUADS["S02k"] = [[705, 390], [1105, 335], [1335, 1080], [965, 1150]]  # 자동 검출이 폰보다 크게 잡음 → 수동
SW, SH = 720, 1560  # 폰 캔버스


def font(p, s):
    return ImageFont.truetype(p, s)


def order_quad(q, top="up"):
    """4점을 TL,TR,BR,BL로. 폰 윗변 = 짧은 변 중 top 방향(up: y 작은 쪽, left/right: x)."""
    pts = np.array(q, np.float32); c = pts.mean(axis=0)
    pts = sorted(pts, key=lambda p: math.atan2(p[1] - c[1], p[0] - c[0]))  # 시계 방향(화면 좌표)
    pts = np.array(pts)
    edges = [(i, np.linalg.norm(pts[i] - pts[(i + 1) % 4])) for i in range(4)]
    def key(e):
        m = (pts[e[0]] + pts[(e[0] + 1) % 4]) / 2
        return {"up": m[1], "down": -m[1], "left": m[0], "right": -m[0]}[top]
    i = min(edges, key=key)[0]  # 윗변 = top 방향으로 가장 치우친 변(검출 사각형이 기울어도 안정, 시계 방향이므로 i→i+1 = TL→TR)
    return [tuple(pts[(i + k) % 4]) for k in range(4)]


def warp_canvas(base_bgr, canvas_rgba, quad, mode="lcd", alpha=1.0):
    """canvas(RGBA PIL, SWxSH)를 quad에 원근 변형해 합성. lcd: 화면의 원래 밝기·반사를 남기고 글자를 곱하기/더하기."""
    H, W = base_bgr.shape[:2]
    cw, ch = canvas_rgba.size
    src = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]]); dst = np.float32(quad)
    M = cv2.getPerspectiveTransform(src, dst)
    rgba = cv2.cvtColor(np.array(canvas_rgba), cv2.COLOR_RGBA2BGRA)
    warp = cv2.warpPerspective(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = cv2.GaussianBlur(warp[..., 3], (0, 0), 0.8).astype(np.float32)[..., None] / 255 * alpha
    col = warp[..., :3].astype(np.float32)
    out = base_bgr.astype(np.float32)
    if mode == "lcd":  # 화면 바탕(흰 무지)은 두고 UI 색만 얹는다 — 바탕 밝기를 0.86배로 눌러 LCD 질감(제15장 17)
        out = out * (1 - a) + (col * 0.93 + out * 0.07) * a
    else:  # 종이: 곱하기
        out = out * (1 - a) + (out * (col / 255)) * a
    return np.clip(out, 0, 255).astype(np.uint8)


def phone_bg(color=(246, 247, 250)):
    c = Image.new("RGBA", (SW, SH), color + (255,)); d = ImageDraw.Draw(c)
    d.text((40, 28), "1:02", font=font(GO_B, 40), fill=(20, 20, 20)); d.text((SW - 170, 30), "▮▮▮ 5G", font=font(GO_R, 32), fill=(20, 20, 20))
    return c, d


def lockscreen_canvas():
    c = Image.new("RGBA", (SW, SH), (18, 22, 36, 255)); d = ImageDraw.Draw(c)
    d.text((SW / 2, 230), "1:02", font=font(GO_R, 190), fill=(240, 240, 245), anchor="mm")
    d.text((SW / 2, 360), "10月23日 木曜日", font=font(GO_R, 44), fill=(220, 220, 230), anchor="mm")
    y = 560
    for title, body in (("倉庫バイト求人", "【急募】時給50,000円"), ("倉庫バイト求人", "面接なし・履歴書不要"), ("倉庫バイト求人", "即日現金 今夜から可")):
        d.rounded_rectangle((40, y, SW - 40, y + 150), 28, fill=(255, 255, 255, 60))
        d.rounded_rectangle((60, y + 28, 150, y + 118), 22, fill=(230, 60, 60))
        d.text((105, y + 73), "求", font=font(GO_B, 48), fill="white", anchor="mm")
        d.text((175, y + 42), title, font=font(GO_B, 36), fill=(255, 255, 255))
        d.text((175, y + 92), body, font=font(GO_R, 38), fill=(235, 235, 240))
        d.text((SW - 70, y + 42), "今", font=font(GO_R, 30), fill=(200, 200, 210), anchor="ra")
        y += 175
    return c


def dm_canvas(highlight=False, full=True, condition=False):
    c, d = phone_bg()
    d.rectangle((0, 90, SW, 200), fill=(255, 255, 255)); d.line((0, 200, SW, 200), fill=(220, 220, 225), width=2)
    d.text((40, 145), "‹", font=font(GO_B, 60), fill=(40, 120, 240), anchor="lm")
    d.ellipse((110, 105, 190, 185), fill=(90, 90, 100)); d.text((150, 145), "求", font=font(GO_B, 40), fill="white", anchor="mm")
    d.text((215, 128), "倉庫バイト求人", font=font(GO_B, 40), fill=(20, 20, 20)); d.text((215, 172), "オンライン", font=font(GO_R, 26), fill=(80, 170, 90))
    def bubble(y, lines, big=None):
        h = 60 + sum(52 for _ in lines) + (120 if big else 0)
        d.rounded_rectangle((40, y, SW - 90, y + h), 34, fill=(255, 255, 255), outline=(225, 225, 230))
        yy = y + 30
        if big:
            d.text((70, yy), big, font=font(GO_B, 64), fill=(220, 40, 40)); yy += 120
        for ln in lines:
            d.text((70, yy), ln, font=font(GO_R, 36), fill=(30, 30, 30)); yy += 52
        return y + h + 26
    y = 240
    if condition:
        y = bubble(y, ["条件は三つだけです。"])
        y = bubble(y, ["① スマホは持ち込み禁止", "② 移動中は必ずアイマスク", "③ 口外した場合、本人および", "　 家族が責任を負う"])
        y = bubble(y, ["問題なければ「応募する」を", "押してください。"])
    else:
        y = bubble(y, ["簡単なデータ整理と", "倉庫の検品補助。", "夜間五時間。"], big="時給 50,000円" if highlight or full else None)
        y = bubble(y, ["即日現金。履歴書不要。", "寮・食事つき。", "週給 1,500,000円 も可能"])
        y = bubble(y, ["今夜から働けます。", "応募は下のボタンから。"])
    d.rounded_rectangle((60, SH - 230, SW - 60, SH - 110), 40, fill=(225, 40, 40))
    d.text((SW / 2, SH - 170), "応募する", font=font(GO_B, 54), fill="white", anchor="mm")
    return c


def apply_button_canvas():
    c, d = phone_bg()
    d.text((SW / 2, 520), "時給 50,000円", font=font(GO_B, 92), fill=(220, 40, 40), anchor="mm")
    d.text((SW / 2, 640), "即日現金 ・ 面接なし", font=font(GO_R, 44), fill=(60, 60, 60), anchor="mm")
    d.rounded_rectangle((90, 760, SW - 90, 920), 48, fill=(225, 40, 40))
    d.text((SW / 2, 840), "応募する", font=font(GO_B, 66), fill="white", anchor="mm")
    return c


def bank_canvas():
    c, d = phone_bg((255, 255, 255))
    d.rectangle((0, 90, SW, 260), fill=(0, 92, 170)); d.text((40, 175), "ネットバンク", font=font(GO_B, 44), fill="white", anchor="lm")
    d.text((40, 330), "普通預金　残高", font=font(GO_R, 38), fill=(90, 90, 90))
    d.text((SW - 40, 470), "¥3,217", font=font(GO_B, 110), fill=(20, 20, 20), anchor="rm")
    d.line((40, 560, SW - 40, 560), fill=(220, 220, 220), width=2)
    y = 610
    for date, name, amt in (("10/20", "家賃（再引落）", "— 失敗"), ("10/15", "コンビニ給与", "+48,320"), ("10/10", "奨学金返還", "-14,000"), ("10/05", "携帯料金", "-6,480")):
        d.text((40, y), date, font=font(GO_R, 30), fill=(120, 120, 120)); d.text((160, y), name, font=font(GO_R, 34), fill=(30, 30, 30))
        d.text((SW - 40, y), amt, font=font(GO_B, 34), fill=(200, 40, 40) if "-" in amt or "失敗" in amt else (30, 120, 60), anchor="ra"); y += 80
    return c


def sns_canvas():
    c, d = phone_bg((255, 255, 255))
    y = 110
    for col, cap in (((70, 140, 200), "最高の海！ 🌊"), ((250, 180, 60), "夜景やばい"), ((90, 160, 110), "卒業旅行3日目")):
        d.ellipse((40, y, 110, y + 70), fill=(180, 180, 190)); d.text((130, y + 15), "friend", font=font(GO_R, 32), fill=(30, 30, 30))
        g = Image.new("RGBA", (SW - 80, 420)); gd = ImageDraw.Draw(g)
        for i in range(420):
            k = i / 420; gd.line((0, i, SW - 80, i), fill=tuple(int(col[j] * (1 - 0.45 * k) + 20 * k) for j in range(3)) + (255,))
        c.paste(g, (40, y + 90)); d.text((40, y + 530), cap, font=font(GO_R, 34), fill=(30, 30, 30)); y += 600
    return c


def search_canvas():
    c, d = phone_bg((255, 255, 255))
    d.rounded_rectangle((40, 110, SW - 40, 200), 45, fill=(240, 240, 243)); d.text((80, 155), "警察 相談 電話", font=font(GO_R, 38), fill=(40, 40, 40), anchor="lm")
    y = 260
    d.text((40, y), "警察相談専用電話", font=font(GO_B, 46), fill=(26, 13, 171)); y += 70
    d.text((40, y), "#9110", font=font(GO_B, 96), fill=(26, 13, 171)); y += 130
    d.text((40, y), "犯罪やトラブルに巻き込まれそうなど、", font=font(GO_R, 30), fill=(60, 60, 60)); y += 44
    d.text((40, y), "緊急ではない相談はこちらへ。", font=font(GO_R, 30), fill=(60, 60, 60)); y += 44
    d.text((40, y), "全国共通 ・ 24時間（一部地域）", font=font(GO_R, 30), fill=(60, 60, 60)); y += 90
    d.rounded_rectangle((40, y, SW - 40, y + 130), 30, fill=(40, 170, 90)); d.text((SW / 2, y + 65), "📞 #9110 に発信", font=font(GO_B, 44), fill="white", anchor="mm"); y += 170
    d.text((40, y), "緊急の場合は 110 番へ", font=font(GO_R, 30), fill=(120, 120, 120))
    return c


def call_canvas():
    c = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.text((SW / 2, 300), "#9110", font=font(GO_B, 120), fill=(30, 30, 30), anchor="mm")
    d.text((SW / 2, 420), "警察相談専用電話", font=font(GO_R, 44), fill=(80, 80, 80), anchor="mm")
    return c


def incoming_canvas():
    c = Image.new("RGBA", (SW, SH), (20, 24, 40, 255)); d = ImageDraw.Draw(c)
    d.ellipse((SW / 2 - 130, 300, SW / 2 + 130, 560), fill=(120, 120, 135)); d.text((SW / 2, 430), "母", font=font(GO_B, 120), fill="white", anchor="mm")
    d.text((SW / 2, 660), "母", font=font(GO_B, 96), fill="white", anchor="mm")
    d.text((SW / 2, 760), "着信中…", font=font(GO_R, 44), fill=(200, 200, 210), anchor="mm")
    d.ellipse((110, SH - 400, 290, SH - 220), fill=(230, 60, 60)); d.ellipse((SW - 290, SH - 400, SW - 110, SH - 220), fill=(60, 200, 90))
    return c


def paper_canvas(w, h, lines, f, fill=(30, 30, 40), vertical=False, top=60):
    c = Image.new("RGBA", (w, h), (255, 255, 255, 0)); d = ImageDraw.Draw(c)
    if vertical:
        x = w - top
        for text, size in lines:
            ff = font(f, size); y = 60
            for ch in text:
                d.text((x, y), ch, font=ff, fill=fill); y += size * 1.05
            x -= size * 1.5
    else:
        y = top
        for text, size in lines:
            d.text((40, y), text, font=font(f, size), fill=fill); y += size * 1.4
    return c


def draw_clock(a, cx, cy, r, hour, minute):
    """기존 바늘을 지우고(밝은 원판 인페인트) 바늘을 그린다. 실제 벽시계 비율."""
    m = np.zeros(a.shape[:2], np.uint8); cv2.circle(m, (int(cx), int(cy)), int(r * 0.82), 255, -1)
    g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY); dark = ((g < 120) & (m > 0)).astype(np.uint8) * 255
    dark = cv2.dilate(dark, np.ones((9, 9), np.uint8))
    a = cv2.inpaint(a, dark, 7, cv2.INPAINT_TELEA)
    def hand(ang_deg, length, width, col):
        rad = math.radians(ang_deg - 90)
        p2 = (int(cx + math.cos(rad) * length), int(cy + math.sin(rad) * length))
        p1 = (int(cx - math.cos(rad) * length * 0.12), int(cy - math.sin(rad) * length * 0.12))
        cv2.line(a, p1, p2, col, width, cv2.LINE_AA)
    hand((hour % 12 + minute / 60) * 30, r * 0.52, int(r * 0.055), (25, 25, 28))
    hand(minute * 6, r * 0.78, int(r * 0.04), (25, 25, 28))
    cv2.circle(a, (int(cx), int(cy)), int(r * 0.05), (25, 25, 28), -1, cv2.LINE_AA)
    return a


def news_band(a):
    H, W = a.shape[:2]
    im = Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle((0, 940, W, 1190), fill=(10, 30, 90, 235)); d.rectangle((0, 940, W, 952), fill=(230, 40, 40, 255))
    d.rectangle((90, 975, 420, 1035), fill=(230, 40, 40, 255)); d.text((255, 1005), "速報", font=font(GO_B, 48), fill="white", anchor="mm")
    d.text((470, 1005), "若者二十七人を保護　闇バイト組織を一斉摘発", font=font(GO_B, 62), fill="white", anchor="lm")
    d.text((470, 1110), "郊外の廃工場に監禁か　警察が男ら十数人を逮捕", font=font(GO_R, 44), fill=(220, 225, 240), anchor="lm")
    d.rectangle((W - 330, 20, W - 40, 100), fill=(0, 0, 0, 140)); d.text((W - 185, 60), "LIVE 7:02", font=font(GO_B, 40), fill="white", anchor="mm")
    im = Image.alpha_composite(im, ov)
    return cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR)


JOBS = {
    "H0": ("lcd", lockscreen_canvas, "up"), "H1": ("lcd", apply_button_canvas, "up"), "S02a": ("lcd", lockscreen_canvas, "up"),
    "S02b": ("lcd", lambda: dm_canvas(full=True), "up"), "S02g": ("lcd", bank_canvas, "up"), "S02d": ("lcd", lambda: dm_canvas(full=True), "up"),
    "S02k": ("lcd", sns_canvas, "up"), "S02ba": ("lcd", lambda: dm_canvas(condition=True), "up"), "S02bi": ("lcd", apply_button_canvas, "right"),
    "S03b": ("lcd", search_canvas, "up"), "S03c": ("lcd", call_canvas, "up"), "S03e": ("lcd", incoming_canvas, "up"),
    "S02h": ("paper", lambda: paper_canvas(700, 400, [("家賃のお支払いについて（再通知）", 44), ("斉藤 健太 様", 36)], GO_B, top=90), "up"),
    "S02i": ("paper", lambda: paper_canvas(900, 560, [("奨学金返還のご案内", 60), ("返還残高　二百四十万円", 40), ("返還期間　十五年", 40)], MIN_B, top=80), "up"),
    "S02bd": ("paper", lambda: paper_canvas(1000, 1300, [("誓約書", 90), ("一、業務内容を口外しません。", 46), ("一、口外した場合、本人および", 46), ("　　家族が責任を負います。", 46), ("　", 46), ("氏名　　　　　　　　　　印", 46)], MIN_B, top=120), "up"),
}
CLOCK = {"S07m": (3, 0), "S08a": (2, 58)}


def main(only=None):
    os.makedirs(BAK, exist_ok=True)
    ids = [i for i in list(JOBS) + list(CLOCK) + ["S10m"] if not only or i in only]
    for sid in ids:
        p = os.path.join(KF, f"{sid}-1.png"); b = os.path.join(BAK, f"{sid}-1.png")
        if not os.path.exists(b):
            shutil.copy(p, b)
        a = cv2.imread(b)
        if sid in JOBS:
            mode, mk, top = JOBS[sid]
            quad = order_quad(QUADS[sid], top)
            a = warp_canvas(a, mk(), quad, mode)
        elif sid in CLOCK:
            q = np.array(QUADS.get(sid) or [], np.float32)
            if sid == "S07m":
                cx, cy, r = 1742, 686, 520
            else:
                cx, cy, r = 330, 760, 640
            a = draw_clock(a, cx, cy, r, *CLOCK[sid])
        elif sid == "S10m":
            a = news_band(a)
        cv2.imwrite(p, a); print("합성", sid)


if __name__ == "__main__":
    main(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
