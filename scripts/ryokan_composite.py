#!/usr/bin/env python3
"""『老舗旅館の嫁』 #03 키프레임 화면·장부·명판 그래픽 합성 (무과금, 로컬) — 규격 제7장 6, 제11장 17(lcd), chika_composite.py 구조.

생성 화면은 무지 → 실글꼴 원화를 원근 변형해 얹는다. 문구는 대본 §7(G4·G6·G7·G8)·스토리보드 gfx/signage 그대로.
  lcd      발광 화면(휴대폰·노트북): LCD 흰색·백라이트·유리 반사·주사선·블룸(tower_composite.apply)
  ink      먹·인쇄(곱하기): 장부 빨간 숫자, 목판 글자
  replace  명판 면 교체
시간차 등장(교체 클립에서 크로스페이드): S11c 별점 4.8→3.1, S13h 「−２，０００万円」 카운트업 → <id>-s<k>.png + _states.json
입력: assets/portraits/ryokan-kf-raw/<id>-1.png (합성 전 확정본 — 처음 실행 때 ryokan-keyframes에서 복사)
출력: assets/portraits/ryokan-keyframes/<id>-1.png, 검수: assets/qa/ryokan/PHASE5_합성_검수.jpg
사용법: python3 scripts/ryokan_composite.py [id ...]
"""
import json
import os
import shutil
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from tower_composite import apply, canvas, ctext, fit, font  # noqa: E402

RAW = os.path.join(ROOT, "assets", "portraits", "ryokan-kf-raw")
OUT = os.path.join(ROOT, "assets", "portraits", "ryokan-keyframes")
QA = os.path.join(ROOT, "assets", "qa", "ryokan", "PHASE5_합성_검수.jpg")
FD = os.path.join(ROOT, "scripts", "fonts")
MIN_B, MIN_R = os.path.join(FD, "ZenOldMincho-Bold.ttf"), os.path.join(FD, "ZenOldMincho-Regular.ttf")
GOTH = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"
MONT = os.path.join(FD, "Montserrat-VF.ttf")
INK, RED, NAVY, GREY = (28, 24, 22), (196, 32, 28), (24, 44, 92), (110, 110, 112)


def P(*pts):
    return [list(p) for p in pts]


# ---------------- 원화 ----------------
def art_game(w, h):
    """휴대폰 게임 화면: 글자 없는 흐린 UI(색 블록·게이지·원형 버튼)."""
    im = canvas(w, h, (40, 60, 120, 255)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(3)
    for _ in range(18):
        x, y = rng.uniform(0, w), rng.uniform(0, h * 0.75); r = rng.uniform(w * 0.04, w * 0.12)
        col = tuple(int(v) for v in rng.integers(90, 255, 3)) + (230,)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    d.rounded_rectangle([w * 0.08, h * 0.84, w * 0.92, h * 0.9], radius=h * 0.03, fill=(30, 30, 50, 255))
    d.rounded_rectangle([w * 0.08, h * 0.84, w * 0.62, h * 0.9], radius=h * 0.03, fill=(80, 220, 120, 255))
    for i in range(3):
        cx = w * (0.25 + 0.25 * i); d.ellipse([cx - w * 0.07, h * 0.92, cx + w * 0.07, h * 0.92 + w * 0.14], fill=(255, 200, 60, 255))
    return im.filter(ImageFilter.GaussianBlur(float(max(1.5, w * 0.006))))


# 감독님 지적(2026-10-20, 4:19 휴대폰 메일): 흰 바탕에 영어 제목만 나열 → 실제 메일 앱 받은편지함처럼
# (상태바·「受信トレイ」·미읽음 수·발신자·제목·미리보기·시각·파란 점·예약사이트 취소 알림). 내용은 대본 S10「最初に崩れたのは、予約だった」에 맞춘다.
MAILS = [  # (발신자, 제목, 미리보기, 시각, 미읽음)
    ("Emily Carter", "Re: Re: Booking request – still waiting", "Hello again, this is my third email. Could you please confirm…", "10:12", True),
    ("予約サイト通知", "キャンセル：10月14日 2名 1泊", "ゲストが予約をキャンセルしました。理由：施設から返信がない", "9:48", True),
    ("Chen Wei-Lin (Taipei)", "Group tour inquiry (18 guests) – URGENT", "We have not received any reply. Please respond by Friday or…", "8:30", True),
    ("Sophie Martin", "Cancellation – no reply received", "Since we didn't hear back from you, we have booked another…", "昨日", True),
    ("予約サイト通知", "キャンセル：10月12日 4名 2泊", "ゲストが予約をキャンセルしました。理由：施設から返信がない", "昨日", True),
    ("Thomas Müller", "Airport shuttle timetable?", "Is there a shuttle from the airport to the ryokan? We arrive…", "昨日", True),
    ("Anna Rossi", "Question about vegetarian dinner", "My husband is vegetarian. Is it possible to change the kaiseki…", "10/7", True),
    ("予約サイト通知", "【重要】返信率低下のお知らせ", "過去7日間の返信率が40%を下回りました。掲載順位に影響する…", "10/7", True),
    ("James Park", "Late check-in possible?", "Our train arrives at 21:30. Would a late check-in be…", "10/6", True),
    ("佐藤 美咲", "予約確認のお礼", "丁寧なご返信ありがとうございました。当日を楽しみに…", "10/5", False),
    ("Laura Bennett", "Thank you for your reply", "Thank you so much for the quick answer. See you in…", "10/5", False),
    ("Hiro Travel", "Is the onsen tattoo friendly?", "One of our guests has a small tattoo. Is the onsen…", "10/4", True),
]
BLUE, DARK, MID, LIGHT = (0, 106, 255, 255), (28, 28, 32, 255), (112, 112, 118, 255), (228, 229, 234, 255)
AV = [(230, 120, 60), (70, 140, 230), (90, 170, 110), (200, 90, 150), (120, 110, 220), (220, 170, 50)]


def _avatar(d, cx, cy, r, name, k, px):
    if name.startswith("予約"):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 94, 184, 255)); d.rectangle([cx - r * 0.5, cy - r * 0.32, cx + r * 0.5, cy + r * 0.32], fill=(255, 255, 255, 255))
        d.rectangle([cx - r * 0.5, cy - r * 0.32, cx + r * 0.5, cy - r * 0.1], fill=(255, 210, 60, 255)); return
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=AV[k % len(AV)] + (255,))
    ini = name[0]; f = font(GOTH if ord(ini) > 0x2000 else MONT, px)
    ctext(d, cx, cy - px * 0.62, ini, f, (255, 255, 255, 255))


def _row_text(d, x, y, maxw, name, subj, prev, when, unread, fs):
    fn = font(GOTH if any(ord(c) > 0x2000 for c in name) else MONT, fs)
    fsub = font(GOTH if any(ord(c) > 0x2000 for c in subj) else MONT, fs * 0.92)
    fpre = font(GOTH if any(ord(c) > 0x2000 for c in prev) else MONT, fs * 0.84)
    ft = font(GOTH if any(ord(c) > 0x2000 for c in when) else MONT, fs * 0.8)
    tw = d.textlength(when, font=ft); d.text((x + maxw - tw, y), when, font=ft, fill=BLUE if unread else MID)
    d.text((x, y), name, font=fn, fill=DARK, stroke_width=1 if unread else 0, stroke_fill=DARK)
    def clip(t, f, w):
        while d.textlength(t, font=f) > w and len(t) > 2:
            t = t[:-2] + "…"
        return t
    d.text((x, y + fs * 1.3), clip(subj, fsub, maxw - tw - fs * 0.5), font=fsub, fill=DARK if unread else MID, stroke_width=1 if unread else 0, stroke_fill=DARK)
    d.text((x, y + fs * 2.5), clip(prev, fpre, maxw), font=fpre, fill=MID)


def art_mail_phone(w, h):
    """휴대폰 메일 앱 받은편지함(세로)."""
    im = canvas(w, h, (255, 255, 255, 255)); d = ImageDraw.Draw(im)
    fs = h * 0.026
    d.text((w * 0.07, h * 0.012), "9:41", font=font(MONT, fs * 1.1), fill=DARK, stroke_width=1, stroke_fill=DARK)
    bx, by = w * 0.93, h * 0.016 + fs * 0.55
    d.rounded_rectangle([bx - fs * 1.5, by - fs * 0.38, bx, by + fs * 0.38], radius=fs * 0.15, outline=DARK, width=max(1, int(fs * 0.08)))
    d.rectangle([bx - fs * 1.42, by - fs * 0.3, bx - fs * 0.5, by + fs * 0.3], fill=(52, 199, 89, 255))
    for i in range(4):
        d.rectangle([bx - fs * 3.6 + i * fs * 0.33, by + fs * 0.35 - fs * (0.25 + 0.15 * i), bx - fs * 3.6 + i * fs * 0.33 + fs * 0.2, by + fs * 0.35], fill=DARK)
    d.text((w * 0.07, h * 0.055), "＜ メールボックス", font=font(GOTH, fs * 0.95), fill=BLUE)
    d.text((w * 0.07, h * 0.085), "受信トレイ", font=font(GOTH, fs * 2.0), fill=DARK, stroke_width=1, stroke_fill=DARK)
    d.rounded_rectangle([w * 0.07, h * 0.135, w * 0.93, h * 0.165], radius=h * 0.012, fill=(239, 239, 243, 255))
    d.text((w * 0.11, h * 0.139), "検索", font=font(GOTH, fs * 0.9), fill=MID)
    cnt = sum(1 for m in MAILS if m[4])
    y = h * 0.18; row = h * 0.086
    for k, (name, subj, prev, when, unread) in enumerate(MAILS):
        if y + row > h * 0.93:
            break
        if unread:
            d.ellipse([w * 0.045, y + fs * 0.55, w * 0.045 + fs * 0.6, y + fs * 1.15], fill=BLUE)
        _avatar(d, w * 0.135, y + row * 0.42, w * 0.055, name, k, fs * 1.2)
        _row_text(d, w * 0.22, y + fs * 0.25, w * 0.71, name, subj, prev, when, unread, fs)
        d.line([w * 0.22, y + row, w, y + row], fill=LIGHT, width=1); y += row
    d.rectangle([0, h * 0.93, w, h], fill=(249, 249, 251, 255)); d.line([0, h * 0.93, w, h * 0.93], fill=LIGHT, width=1)
    ctext(d, w * 0.5, h * 0.945, f"未読 {cnt + 25} 件", font(GOTH, fs * 0.9), MID)
    return im.filter(ImageFilter.GaussianBlur(float(max(0.8, w * 0.0015))))


def art_mail_desk(w, h):
    """노트북 메일 클라이언트(가로): 왼쪽 폴더 사이드바 + 목록."""
    im = canvas(w, h, (255, 255, 255, 255)); d = ImageDraw.Draw(im)
    fs = h * 0.036; sw = w * 0.2
    d.rectangle([0, 0, sw, h], fill=(242, 242, 246, 255)); d.rectangle([0, 0, w, h * 0.09], fill=(236, 236, 240, 255))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([w * 0.012 + i * fs * 0.8, h * 0.03, w * 0.012 + i * fs * 0.8 + fs * 0.55, h * 0.03 + fs * 0.55], fill=c + (255,))
    d.rounded_rectangle([sw + w * 0.02, h * 0.02, w * 0.98, h * 0.07], radius=h * 0.015, fill=(255, 255, 255, 255), outline=LIGHT)
    d.text((sw + w * 0.035, h * 0.028), "検索", font=font(GOTH, fs * 0.85), fill=MID)
    cnt = sum(1 for m in MAILS if m[4]) + 25
    folders = [("受信トレイ", str(cnt), True), ("VIP", "", False), ("送信済み", "", False), ("下書き", "3", False), ("ゴミ箱", "", False)]
    fy = h * 0.14
    for nm, n, sel in folders:
        if sel:
            d.rounded_rectangle([w * 0.012, fy - fs * 0.25, sw - w * 0.012, fy + fs * 1.05], radius=fs * 0.3, fill=(214, 226, 250, 255))
        d.text((w * 0.03, fy), nm, font=font(GOTH, fs * 0.9), fill=DARK if sel else MID)
        if n:
            tw = d.textlength(n, font=font(MONT, fs * 0.8)); d.text((sw - w * 0.025 - tw, fy + fs * 0.05), n, font=font(MONT, fs * 0.8), fill=BLUE if sel else MID)
        fy += fs * 1.7
    y = h * 0.11; row = h * 0.112; x = sw + w * 0.035
    for k, (name, subj, prev, when, unread) in enumerate(MAILS):
        if y + row > h:
            break
        if unread:
            d.ellipse([sw + w * 0.012, y + fs * 0.45, sw + w * 0.012 + fs * 0.5, y + fs * 0.95], fill=BLUE)
        _row_text(d, x, y + fs * 0.2, w * 0.98 - x, name, subj, prev, when, unread, fs * 0.95)
        d.line([x, y + row, w, y + row], fill=LIGHT, width=1); y += row
    return im.filter(ImageFilter.GaussianBlur(float(max(0.8, w * 0.0015))))


def art_mail(w, h):
    return art_mail_phone(w, h) if w < h else art_mail_desk(w, h)


def _star_row(d, x, y, r, n, color, gap=None):
    gap = gap or r * 2.5
    for i in range(5):
        cx = x + i * gap
        pts = [(cx + r * (1 if k % 2 == 0 else 0.45) * np.cos(np.pi / 2 + k * np.pi / 5), y - r * (1 if k % 2 == 0 else 0.45) * np.sin(np.pi / 2 + k * np.pi / 5)) for k in range(10)]
        d.polygon(pts, fill=color if i < n else (214, 214, 220, 255))


# 감독님 지적(2026-10-20, 5:02 노트북 리뷰): 점수·별·문장만 → 실제 예약사이트 리뷰 페이지처럼(사이트 머리띠·숙소명·口コミ 수·
# 평점 타일+평가어·항목별 막대·리뷰 카드: 이름·국가·날짜·별·제목·본문). 점수가 내려가면 평가어·막대·최신 리뷰가 함께 바뀐다.
GOOD_REVIEWS = [("Emily C.", "オーストラリア", "2025年9月", 5, "Perfect stay, perfect English", "The young okami answered every email the same day and spoke perfect English."),
                ("田中 和子", "日本", "2025年9月", 5, "心のこもったおもてなし", "若女将さんの気配りが素晴らしく、母も大満足でした。")]
BAD_REVIEWS = [("Michael R.", "アメリカ", "2025年10月", 1, "Staff couldn't speak English at all", "Nobody answered our emails. The shuttle never came and no one at the desk understood us."),
               ("鈴木 恵", "日本", "2025年10月", 1, "最悪の対応。二度と泊まらない。", "予約したはずの部屋が用意されておらず、謝罪もありませんでした。")]


def art_review(w, h, score):
    """예약사이트 리뷰 페이지(노트북). score 4.8→3.1 상태 전환."""
    im = canvas(w, h, (244, 245, 248, 255)); d = ImageDraw.Draw(im)
    fs = h * 0.045; bad = score < 4.0
    d.rectangle([0, 0, w, h * 0.095], fill=(0, 56, 110, 255))
    d.rounded_rectangle([w * 0.03, h * 0.02, w * 0.17, h * 0.075], radius=h * 0.01, fill=(255, 255, 255, 255))
    d.text((w * 0.045, h * 0.03), "Yado Reserve", font=font(MONT, fs * 0.8), fill=(0, 56, 110, 255))
    d.rounded_rectangle([w * 0.22, h * 0.022, w * 0.7, h * 0.073], radius=h * 0.025, fill=(255, 255, 255, 255))
    d.text((w * 0.235, h * 0.03), "月見荘  10月14日〜15日  大人2名", font=font(GOTH, fs * 0.75), fill=MID)
    d.text((w * 0.03, h * 0.12), "月見荘（つきみそう）", font=font(GOTH, fs * 1.25), fill=DARK, stroke_width=1, stroke_fill=DARK)
    d.text((w * 0.03, h * 0.19), "温泉旅館 · 創業大正十二年 · 口コミ 1,284件", font=font(GOTH, fs * 0.72), fill=MID)
    # 평점 타일
    col = (196, 40, 32, 255) if bad else (0, 112, 72, 255)
    d.rounded_rectangle([w * 0.03, h * 0.27, w * 0.2, h * 0.52], radius=h * 0.02, fill=col)
    ctext(d, w * 0.115, h * 0.285, f"{score:.1f}", font(MONT, fs * 2.6), (255, 255, 255, 255))
    word = "とても良い" if score >= 4.5 else "良い" if score >= 4.0 else "普通" if score >= 3.5 else "やや不満"
    ctext(d, w * 0.115, h * 0.425, word, font(GOTH, fs * 0.8), (255, 255, 255, 255))
    ctext(d, w * 0.115, h * 0.47, "総合評価", font(GOTH, fs * 0.6), (230, 235, 240, 255))
    # 항목별 막대
    cats = [("スタッフ", score - 0.1), ("清潔さ", min(5, score + 0.3)), ("設備", min(5, score + 0.1)), ("立地", 4.6), ("コスパ", score - 0.2)]
    by = h * 0.28
    for nm, v in cats:
        d.text((w * 0.24, by), nm, font=font(GOTH, fs * 0.68), fill=DARK)
        d.rounded_rectangle([w * 0.33, by + fs * 0.25, w * 0.6, by + fs * 0.55], radius=fs * 0.15, fill=(224, 226, 232, 255))
        d.rounded_rectangle([w * 0.33, by + fs * 0.25, w * 0.33 + w * 0.27 * max(0.05, v / 5), by + fs * 0.55], radius=fs * 0.15, fill=col)
        d.text((w * 0.615, by), f"{max(1.0, v):.1f}", font=font(MONT, fs * 0.68), fill=DARK); by += h * 0.05
    # 최신 리뷰 카드
    d.text((w * 0.03, h * 0.56), "最新の口コミ", font=font(GOTH, fs * 0.85), fill=DARK, stroke_width=1, stroke_fill=DARK)
    rv = BAD_REVIEWS if bad else GOOD_REVIEWS
    cy = h * 0.63
    for k, (name, ctry, date, stars, title, body) in enumerate(rv):
        d.rounded_rectangle([w * 0.03, cy, w * 0.97, cy + h * 0.17], radius=h * 0.015, fill=(255, 255, 255, 255), outline=(222, 224, 230, 255))
        d.ellipse([w * 0.05, cy + h * 0.03, w * 0.05 + fs * 1.4, cy + h * 0.03 + fs * 1.4], fill=AV[(k + 2) % len(AV)] + (255,))
        ctext(d, w * 0.05 + fs * 0.7, cy + h * 0.03 + fs * 0.25, name[0], font(GOTH if ord(name[0]) > 0x2000 else MONT, fs * 0.8), (255, 255, 255, 255))
        d.text((w * 0.1, cy + h * 0.025), name, font=font(GOTH if any(ord(c) > 0x2000 for c in name) else MONT, fs * 0.7), fill=DARK)
        d.text((w * 0.1, cy + h * 0.065), f"{ctry} · {date}", font=font(GOTH, fs * 0.55), fill=MID)
        _star_row(d, w * 0.84, cy + h * 0.05, fs * 0.32, stars, (196, 40, 32, 255) if stars <= 2 else (255, 170, 0, 255))
        d.text((w * 0.1, cy + h * 0.1), title, font=fit(d, title, GOTH if any(ord(c) > 0x2000 for c in title) else MONT, w * 0.84, fs * 0.72), fill=DARK, stroke_width=1, stroke_fill=DARK)
        d.text((w * 0.1, cy + h * 0.135), body, font=fit(d, body, GOTH if any(ord(c) > 0x2000 for c in body) else MONT, w * 0.84, fs * 0.55), fill=MID)
        cy += h * 0.19
    return im.filter(ImageFilter.GaussianBlur(float(max(0.8, w * 0.0012))))


def art_ledger(w, h, text):
    """장부 위 빨간 글씨(ink): 가운데 큰 숫자."""
    im = canvas(w, h); d = ImageDraw.Draw(im)
    if text:
        ctext(d, w / 2, h * 0.3, text, fit(d, text, MIN_B, w * 0.8, h * 0.3), RED + (235,))
    return im


def art_call(w, h, name):
    """휴대폰 착신 화면: 이름 + 「着信中…」 + 응답 버튼 2개."""
    im = canvas(w, h, (18, 20, 28, 255)); d = ImageDraw.Draw(im)
    ctext(d, w / 2, h * 0.2, name, fit(d, name, GOTH, w * 0.8, h * 0.11), (250, 250, 252, 255))
    ctext(d, w / 2, h * 0.34, "着信中…", fit(d, "着信中…", GOTH, w * 0.5, h * 0.05), (170, 172, 180, 255))
    r = w * 0.11
    for cx, col in ((w * 0.28, (230, 60, 50, 255)), (w * 0.72, (60, 200, 90, 255))):
        d.ellipse([cx - r, h * 0.8 - r, cx + r, h * 0.8 + r], fill=col)
    return im


def art_plate(w, h, text):
    im = canvas(w, h, (238, 232, 220, 255)); d = ImageDraw.Draw(im)
    ctext(d, w / 2, h * 0.22, text, fit(d, text, MIN_B, w * 0.86, h * 0.55), INK + (255,))
    return im


def art_board_v(w, h, text):
    """세로 목판 글자(ink): 한 글자씩 세로."""
    im = canvas(w, h); d = ImageDraw.Draw(im); n = len(text)
    f = fit(d, "月", MIN_B, w * 0.8, h / (n + 0.6))
    for i, ch in enumerate(text):
        ctext(d, w / 2, h * (0.08 + i * 0.84 / n), ch, f, INK + (240,))
    return im


def white_quad(sid, box, thr=170):
    """무지 발광 화면(흰 면)을 자동 검출: box(x0,y0,x1,y1) 안의 밝은 픽셀 → 최소 외접 회전 사각형 → TL·TR·BR·BL 순."""
    a = np.asarray(Image.open(os.path.join(RAW, f"{sid}-1.png")).convert("RGB"))
    x0, y0, x1, y1 = box; g = a[y0:y1, x0:x1].mean(2)
    m = (g > thr).astype(np.uint8); m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cs, key=cv2.contourArea)
    ap = cv2.approxPolyDP(c, 0.04 * cv2.arcLength(c, True), True).reshape(-1, 2).astype(np.float32)
    pts = (ap if len(ap) == 4 else cv2.boxPoints(cv2.minAreaRect(c))) + np.float32([x0, y0])
    cen = pts.mean(0); pts = pts[np.argsort(np.arctan2(pts[:, 1] - cen[1], pts[:, 0] - cen[0]))]   # 시계 방향(화면 좌표)
    e = [np.linalg.norm(pts[(k + 1) % 4] - pts[k]) for k in range(4)]
    # 긴 변이 화면 세로(휴대폰 세로 화면): 짧은 변 두 개 중 위쪽(평균 y 작은 쪽)이 「위」 → 그 변의 시작점을 TL로
    short = [0, 2] if e[0] + e[2] < e[1] + e[3] else [1, 3]
    top = min(short, key=lambda k: (pts[k][1] + pts[(k + 1) % 4][1]))
    pts = np.roll(pts, -top, axis=0)
    return [list(map(float, p)) for p in pts]



# ---------------- 합성 지시(키프레임 1344x768 좌표: 왼위·오른위·오른아래·왼아래) ----------------
JOBS = {
    "S05d": [("lcd", P((765, 462), (1130, 520), (980, 768), (455, 690)), lambda w, h: art_game(w, h))],
    "S10d": [("lcd", P((833, 392), (1063, 392), (1072, 535), (840, 540)), lambda w, h: art_mail(w, h))],
    "S16a": [("lcd", white_quad("S16a", (560, 580, 820, 700)), lambda w, h: art_call(w, h, "麻衣"))],
    "S18a": [("lcd", white_quad("S18a", (530, 570, 770, 690)), lambda w, h: art_call(w, h, "義母"))],
    "S10a2": [("lcd", P((600, 295), (770, 290), (770, 630), (590, 635)), lambda w, h: art_mail(w, h))],
    "S18k": [("replace", P((940, 415), (1080, 415), (1080, 440), (940, 440)), lambda w, h: art_plate(w, h, "花筏　フロント"))],
    "S03a": [("ink", P((195, 225), (240, 225), (240, 345), (195, 345)), lambda w, h: art_board_v(w, h, "月見荘"))],
}
# 시간차 등장: (시작 비율, 원화 함수)
S11C_Q = P((600, 300), (935, 300), (935, 540), (597, 520))
S13H_Q = P((330, 540), (640, 340), (860, 440), (560, 660))
STATES = {
    "S11c": [(0.0, lambda w, h: art_review(w, h, 4.8)), (0.35, lambda w, h: art_review(w, h, 4.3)), (0.45, lambda w, h: art_review(w, h, 3.8)),
             (0.55, lambda w, h: art_review(w, h, 3.4)), (0.65, lambda w, h: art_review(w, h, 3.1))],
    "S13h": [(0.0, lambda w, h: art_ledger(w, h, "")), (0.2, lambda w, h: art_ledger(w, h, "−５００万円")), (0.4, lambda w, h: art_ledger(w, h, "−１，０００万円")),
             (0.6, lambda w, h: art_ledger(w, h, "−１，５００万円")), (0.8, lambda w, h: art_ledger(w, h, "−２，０００万円"))],
}
STATE_Q = {"S11c": ("lcd", S11C_Q), "S13h": ("ink", S13H_Q)}
SIGMA = {"S05d": 1.2, "S10d": 0.5, "S11c": 0.5, "S13h": 0.6, "S16a": 0.8, "S18a": 0.8, "S10a2": 0.5, "S18k": 0.8, "S03a": 0.9}


NO_REMAP = {"S05d", "S18a", "S16a"}   # 크롭 후 현재 키프레임에서 직접 측정한 좌표


def remap(q, sid):
    if sid in NO_REMAP:
        return q
    """좌표는 B단계 원본(1344x768, 크롭 전)에서 측정 → kf_letterbox_fix가 크롭·재확대한 현재 키프레임 좌표로 변환(_v1 원본에서 띠를 다시 계산)."""
    v1 = os.path.join(OUT, "_v1", f"{sid}-1.png")
    if not os.path.exists(v1):
        return q
    from kf_letterbox_fix import bands
    im = Image.open(v1).convert("RGB"); W0, H0 = im.size; a = np.asarray(im).astype(float)
    t, b = bands(a, 1); l, r = bands(a, 0); cw, ch = r - l, b - t
    if cw / ch > 16 / 9:
        nw = int(ch * 16 / 9); l += (cw - nw) // 2; cw = nw
    else:
        nh = int(cw * 9 / 16); t += (ch - nh) // 2; ch = nh
    return [[(x - l) * W0 / cw, (y - t) * H0 / ch] for x, y in q]


# 노렌 가문(家紋) 지우기(제2장 1): 원형 문양의 고리 영역에서 회색 선 픽셀만(머리·피부 제외) 인페인트 — S10b 3회 재생성에도 가문이 남음
PATCH = {"S10b": [(675, 220, 58, 0, (675, 262, 40, 52))]}   # (cx, cy, R, 두께=0이면 원판 전체, 보호 타원(fx, fy, rx, ry)=얼굴) 키프레임 좌표(크롭 후)


def patch_crest(a, rings):
    out = a.copy(); H, W = a.shape[:2]
    for cx, cy, R, th, face in rings:
        yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        fx, fy, rx, ry = face; keep = (((xx - fx) / rx) ** 2 + ((yy - fy) / ry) ** 2) < 1   # 얼굴 타원은 손대지 않는다(1차: 얼굴 하이라이트가 회색으로 잡혀 뭉개짐)
        ann = (r < R + th) if th == 0 else ((r > R - th) & (r < R + th))
        hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV); lum = a.mean(2)
        grey = (hsv[..., 1] < 110) & (lum > 52)                      # 회색 문양 선(노렌 남색·검은 머리 제외)
        skin = (hsv[..., 0] < 25) & (hsv[..., 1] > 35) & (lum > 80)   # 피부
        m = (ann & grey & ~skin & ~keep).astype(np.uint8)
        m = cv2.dilate(m, np.ones((5, 5), np.uint8)) * 255
        out = cv2.inpaint(out, m, 5, cv2.INPAINT_TELEA)
    return out


def main(only=None):
    os.makedirs(RAW, exist_ok=True)
    ids = list(JOBS) + list(STATES) + [k for k in PATCH if k not in JOBS and k not in STATES]
    for sid in ids:
        if not os.path.exists(os.path.join(RAW, f"{sid}-1.png")):
            shutil.copy(os.path.join(OUT, f"{sid}-1.png"), RAW)
    states, crops = {}, []
    sp = os.path.join(OUT, "_states.json")
    if os.path.exists(sp):
        states = json.load(open(sp))
    for sid in ids:
        if only and sid not in only:
            continue
        a = np.asarray(Image.open(os.path.join(RAW, f"{sid}-1.png")).convert("RGB")).copy()
        qs = []
        if sid in PATCH:
            a = patch_crest(a, PATCH[sid]); qs += [[[cx - R - th, cy - R - th], [cx + R + th, cy - R - th], [cx + R + th, cy + R + th], [cx - R - th, cy + R + th]] for cx, cy, R, th, _ in PATCH[sid]]
        if sid in JOBS:
            for mode, q, fn in JOBS[sid]:
                q = remap(q, sid); a = apply(a, mode, q, fn, SIGMA.get(sid)); qs.append(q)
        if sid in STATES:
            mode, q = STATE_Q[sid]; q = remap(q, sid); raw = a.copy()
            for k, (t, fn) in enumerate(STATES[sid]):
                b = apply(raw, mode, q, fn, SIGMA.get(sid)); Image.fromarray(b).save(os.path.join(OUT, f"{sid}-s{k}.png"))
            states[sid] = [[t, f"{sid}-s{k}.png"] for k, (t, _) in enumerate(STATES[sid])]; a = b; qs.append(q)
        Image.fromarray(a).save(os.path.join(OUT, f"{sid}-1.png"))
        for q in qs:
            x, y, w, h = cv2.boundingRect(np.int32(q)); pad = max(24, h // 2)
            crops.append((sid, Image.fromarray(a).crop((max(0, x - pad), max(0, y - pad), min(a.shape[1], x + w + pad), min(a.shape[0], y + h + pad)))))
    json.dump(states, open(sp, "w"), ensure_ascii=False, indent=1)
    T = 380; cols = 4; rows = (len(crops) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * T, rows * (T + 24)), "white"); d = ImageDraw.Draw(sheet)
    for i, (lab, im) in enumerate(crops):
        im = im.copy(); im.thumbnail((T, T)); x, y = (i % cols) * T, (i // cols) * (T + 24)
        sheet.paste(im, (x, y + 24)); d.text((x + 4, y + 3), lab, font=font(GOTH, 18), fill="black")
    os.makedirs(os.path.dirname(QA), exist_ok=True); sheet.save(QA, quality=85)
    print(f"합성 {len(crops)}곳 → {OUT}, 검수 {QA}")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
