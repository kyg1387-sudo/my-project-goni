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


MAILS = [("Booking request for October 12 – family of four", True), ("Re: Room availability in autumn season", True),
         ("Question about vegetarian dinner options", True), ("Airport shuttle timetable?", True), ("Cancellation – no reply received", True),
         ("Group tour inquiry (18 guests)", True), ("Thank you for your reply", False), ("Reservation confirmed – 2 nights", False),
         ("Late check-in possible?", True), ("Inquiry from travel agency Taipei", True), ("Is the onsen tattoo friendly?", True)]


def art_mail(w, h):
    """노트북 메일함: 영어 제목이 쌓인 목록, 미답장은 굵게·파란 점. 글자는 살짝 흐림."""
    im = canvas(w, h, (246, 247, 250, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.09], fill=(232, 234, 240, 255)); d.rectangle([0, 0, w * 0.2, h], fill=(238, 239, 244, 255))
    fb, fr = font(MONT, int(h * 0.052)), font(MONT, int(h * 0.05))
    y = h * 0.12; row = h * 0.08
    for subj, unread in MAILS:
        if y > h - row:
            break
        if unread:
            d.ellipse([w * 0.215, y + row * 0.3, w * 0.215 + h * 0.02, y + row * 0.3 + h * 0.02], fill=(40, 110, 230, 255))
        d.text((w * 0.25, y + row * 0.15), subj, font=fb if unread else fr, fill=(30, 30, 36, 255) if unread else (120, 120, 128, 255))
        d.line([w * 0.2, y + row, w, y + row], fill=(224, 226, 232, 255), width=1)
        y += row
    return im.filter(ImageFilter.GaussianBlur(float(max(1.0, w * 0.0025))))


def art_review(w, h, score):
    """예약사이트 리뷰 화면: 큰 점수 + 별 + 리뷰 2건(영어·일본어)."""
    im = canvas(w, h, (250, 250, 252, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.1], fill=(0, 56, 110, 255))
    d.rounded_rectangle([w * 0.05, h * 0.15, w * 0.95, h * 0.44], radius=h * 0.03, fill=(255, 255, 255, 255), outline=(220, 222, 228, 255))
    fs = font(MONT, int(h * 0.19)); d.text((w * 0.08, h * 0.17), f"{score:.1f}", font=fs, fill=(20, 20, 24, 255))
    bad = score < 4.0
    sx = w * 0.36
    for i in range(5):
        cx = sx + i * w * 0.075; r = h * 0.05
        filled = (score / 5 * 5) >= i + 0.5
        d.polygon([(cx + r * np.cos(np.pi / 2 + k * 2 * np.pi / 5 * (1 if k % 2 == 0 else 1)) * (1 if k % 2 == 0 else 0.45),
                    h * 0.27 - r * np.sin(np.pi / 2 + k * 2 * np.pi / 10) * (1 if k % 2 == 0 else 0.45)) for k in range(10)],
                  fill=((230, 60, 40, 255) if bad else (255, 170, 0, 255)) if filled else (210, 210, 214, 255))
    d.text((w * 0.36, h * 0.33), "Guest rating", font=font(MONT, int(h * 0.055)), fill=(120, 120, 128, 255))
    y = h * 0.5
    for txt, path, stars in (("Staff couldn't speak English at all.", MONT, 1), ("最悪の対応。二度と泊まらない。", GOTH, 1)):
        d.rounded_rectangle([w * 0.05, y, w * 0.95, y + h * 0.2], radius=h * 0.02, fill=(255, 255, 255, 255), outline=(220, 222, 228, 255))
        d.text((w * 0.08, y + h * 0.03), "★" * stars + "☆" * (5 - stars), font=font(GOTH, int(h * 0.06)), fill=(230, 60, 40, 255))
        d.text((w * 0.08, y + h * 0.1), txt, font=fit(d, txt, path, w * 0.84, h * 0.065), fill=(30, 30, 36, 255))
        y += h * 0.24
    return im


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


# ---------------- 합성 지시(키프레임 1344x768 좌표: 왼위·오른위·오른아래·왼아래) ----------------
JOBS = {
    "S05d": [("lcd", P((470, 582), (1040, 425), (905, 660), (462, 612)), lambda w, h: art_game(w, h))],
    "S10d": [("lcd", P((833, 392), (1063, 392), (1072, 535), (840, 540)), lambda w, h: art_mail(w, h))],
    "S16a": [("lcd", P((608, 648), (722, 607), (782, 630), (686, 676)), lambda w, h: art_call(w, h, "麻衣"))],
    "S18a": [("lcd", P((590, 556), (700, 538), (718, 585), (608, 606)), lambda w, h: art_call(w, h, "義母"))],
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


def remap(q, sid):
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


def main(only=None):
    os.makedirs(RAW, exist_ok=True)
    ids = list(JOBS) + list(STATES)
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
