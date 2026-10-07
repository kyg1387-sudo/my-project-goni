#!/usr/bin/env python3
"""『タワマンのボスママ』 키프레임 화면 속 일본어 표기 합성 (무과금, 로컬) — 규격 제7장 6.

생성 화면은 무지(또는 외계어) → 실글꼴 원화를 원근 변형해 얹는다. 표기 문구는 대본(00_script_ja.md)·스토리보드 signage/gfx 그대로.
  ink      먹·인쇄(곱하기) — 판·현수막·종이 질감과 조명이 비친다
  replace  면을 통째로 바꿈(외계어가 있던 판·화면·종이). keep_shading이면 원래 면의 밝기 변화를 곱한다
  emit     발광 화면(노트북·휴대폰·LCD) — 그림자 곱하지 않음
초점이 나간 면은 원화를 같은 정도로 흐린다(라플라시안). 손·펜이 면을 가리는 컷은 PROTECT(피부·빨간 펜·어두운 소매)로 보호.

입력: assets/portraits/tower-kf-raw/<id>-1.png (합성 대상 컷의 합성 전 확정본 — 처음 실행 때 tower-keyframes에서 복사)
출력: assets/portraits/tower-keyframes/<id>-1.png, 시간차 등장 컷은 <id>-s<k>.png + _states.json
검수: productions/tower-bossmom-ja/qa/합성_검수.jpg
사용법: python3 scripts/tower_composite.py [id ...]
"""
import json
import os
import shutil
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RAW = os.path.join(ROOT, "assets", "portraits", "tower-kf-raw")
OUT = os.path.join(ROOT, "assets", "portraits", "tower-keyframes")
QA = os.path.join(ROOT, "productions", "tower-bossmom-ja", "qa", "합성_검수.jpg")
FD = os.path.join(ROOT, "scripts", "fonts")
MIN_B, MIN_R = os.path.join(FD, "ZenOldMincho-Bold.ttf"), os.path.join(FD, "ZenOldMincho-Regular.ttf")
MARU, KLEE, MONT = os.path.join(FD, "ZenMaruGothic-Black.ttf"), os.path.join(FD, "KleeOne-Regular.ttf"), os.path.join(FD, "Montserrat-VF.ttf")
GOTH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
BAG = os.path.join(ROOT, "assets", "portraits", "tower-cast", "cells", "prop-bag.png")

TOWER_JA, TOWER_EN = "グランタワー東京ベイ", "GRAND TOWER TOKYO BAY"
BANNER_RINJI = "グランタワー東京ベイ管理組合　臨時総会"
BANNER_TSUJO = "グランタワー東京ベイ管理組合　通常総会"
COMPANY = "西園寺ビルメンテナンス株式会社"
NAVY, INK, RED, BRASS_INK = (24, 36, 72), (28, 28, 30), (196, 30, 36), (58, 40, 18)


def font(path, px):
    f = ImageFont.truetype(path, max(6, int(px)))
    if path == MONT:   # 가변 글꼴 기본값은 Thin — 간판 각인 굵기로
        f.set_variation_by_name("SemiBold")
    return f


def canvas(w, h, bg=(0, 0, 0, 0)):
    return Image.new("RGBA", (int(w), int(h)), bg)


def ctext(d, cx, y, text, f, fill, spacing=0):
    if spacing:
        tw = sum(d.textlength(c, font=f) for c in text) + spacing * (len(text) - 1)
        x = cx - tw / 2
        for c in text:
            d.text((x, y), c, font=f, fill=fill); x += d.textlength(c, font=f) + spacing
        return
    bb = d.textbbox((0, 0), text, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], y - bb[1]), text, font=f, fill=fill)


def fit(d, text, path, maxw, px):
    while px > 6 and d.textlength(text, font=font(path, px)) > maxw:
        px -= 1
    return font(path, px)


# ---------------- 원화 ----------------
def art_plaque(w, h, lines=None, ink=BRASS_INK):
    """금속·석재 명판 각인(곱하기용, 투명 바탕). 세로형이면 줄을 나눈다."""
    im = canvas(w, h); d = ImageDraw.Draw(im)
    if lines is None:
        lines = [("GRAND TOWER", MONT, 0.11), ("TOKYO BAY", MONT, 0.08), ("", None, 0.05),
                 ("グランタワー", MIN_B, 0.15), ("東京ベイ", MIN_B, 0.15)] if h > w * 0.9 else \
                [(TOWER_EN, MONT, 0.12), (TOWER_JA, MIN_B, 0.26)]
    tot = sum(s for _, _, s in lines) * h * 1.25; y = (h - tot) / 2
    for t, p, s in lines:
        if t:
            f = fit(d, t, p, w * 0.84, s * h); ctext(d, w / 2, y, t, f, ink + (255,))
        y += s * h * 1.25
    d.rectangle((w * 0.06, h * 0.06, w * 0.94, h * 0.94), outline=ink + (110,), width=max(1, int(w * 0.012)))
    return im


def art_brass_plate(w, h):
    """석재 기둥에 붙일 황동 명판(replace)."""
    a = np.zeros((int(h), int(w), 3), np.float32)
    g = np.linspace(0, 1, int(w))[None, :, None]
    a[:] = np.array([176, 146, 92]) * (0.82 + 0.25 * np.sin(g * 3.1)) + np.random.default_rng(3).normal(0, 3, a.shape)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im); d.rectangle((0, 0, w - 1, h - 1), outline=(120, 92, 48, 255), width=max(2, int(w * 0.02)))
    im.alpha_composite(art_plaque(w, h))
    return im


def art_banner(w, h, text):
    im = canvas(w, h); d = ImageDraw.Draw(im)
    f = fit(d, text, MIN_B, w * 0.9, h * 0.52)
    ctext(d, w / 2, h * 0.24, text, f, NAVY + (255,))
    return im


def art_label(w, h, text, path=MIN_B, color=INK, scale=0.55, sub=None):
    im = canvas(w, h); d = ImageDraw.Draw(im)
    f = fit(d, text, path, w * 0.84, h * scale)
    bb = d.textbbox((0, 0), text, font=f); th = bb[3] - bb[1]
    y = (h - th) / 2 - (h * 0.08 if sub else 0)
    ctext(d, w / 2, y, text, f, color + (255,))
    if sub:
        fs = fit(d, sub, MONT, w * 0.8, h * 0.16); ctext(d, w / 2, y + th + h * 0.08, sub, fs, color + (200,))
    return im


def art_kids_board(w, h, rule, rule_color):
    im = canvas(w, h); d = ImageDraw.Draw(im)
    ctext(d, w / 2, h * 0.12, "KIDS ROOM", font(MONT, h * 0.08), (90, 120, 160, 255))
    ctext(d, w / 2, h * 0.24, "キッズルーム", fit(d, "キッズルーム", MARU, w * 0.8, h * 0.17), (40, 90, 150, 255))
    d.line((w * 0.12, h * 0.5, w * 0.88, h * 0.5), fill=(150, 160, 175, 255), width=max(1, int(h * 0.008)))
    ctext(d, w / 2, h * 0.58, rule, fit(d, rule, MARU, w * 0.84, h * 0.12), rule_color + (255,))
    ctext(d, w / 2, h * 0.82, "グランタワー東京ベイ管理組合", fit(d, "グランタワー東京ベイ管理組合", MIN_B, w * 0.6, h * 0.055), (80, 80, 90, 255))
    return im


def art_lounge(w, h):
    im = canvas(w, h, (238, 236, 230, 255)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h * 0.2), fill=(40, 44, 58, 255))
    ctext(d, w / 2, h * 0.05, "SKY LOUNGE", font(MONT, h * 0.1), (214, 190, 130, 255))
    ctext(d, w / 2, h * 0.27, "スカイラウンジ ご予約について", fit(d, "スカイラウンジ ご予約について", MIN_B, w * 0.8, h * 0.08), (50, 50, 60, 255))
    ctext(d, w / 2, h * 0.43, "上層階優先", fit(d, "上層階優先", MIN_B, w * 0.78, h * 0.27), (150, 24, 30, 255), spacing=int(w * 0.02))
    ctext(d, w / 2, h * 0.79, "40階以上の居住者の予約を優先します", fit(d, "40階以上の居住者の予約を優先します", MIN_R, w * 0.82, h * 0.07), (60, 60, 70, 255))
    ctext(d, w / 2, h * 0.9, "管理組合理事会", fit(d, "管理組合理事会", MIN_R, w * 0.4, h * 0.055), (90, 90, 100, 255))
    return im


def art_notice(w, h):
    im = canvas(w, h); d = ImageDraw.Draw(im)
    ctext(d, w / 2, h * 0.07, "お知らせ", font(MIN_B, h * 0.07), INK + (255,))
    ctext(d, w / 2, h * 0.2, "修繕積立金", fit(d, "修繕積立金", MIN_B, w * 0.7, h * 0.12), INK + (255,))
    ctext(d, w / 2, h * 0.36, "来月より 1.8倍に", fit(d, "来月より 1.8倍に", MIN_B, w * 0.82, h * 0.1), RED + (255,))
    ctext(d, w / 2, h * 0.49, "値上げ予定", fit(d, "値上げ予定", MIN_B, w * 0.6, h * 0.1), RED + (255,))
    ctext(d, w / 2, h * 0.64, "臨時総会にて承認を", fit(d, "臨時総会にて承認を", MIN_R, w * 0.72, h * 0.06), INK + (255,))
    ctext(d, w / 2, h * 0.72, "お諮りいたします", fit(d, "お諮りいたします", MIN_R, w * 0.72, h * 0.06), INK + (255,))
    ctext(d, w * 0.6, h * 0.86, "管理組合 理事長", fit(d, "管理組合 理事長", MIN_R, w * 0.5, h * 0.045), INK + (230,))
    return im


def art_ledger(w, h):
    im = canvas(w, h); d = ImageDraw.Draw(im)
    rows = [("令和5年 4月", "外壁調査費", "3,200,000"), ("令和5年10月", "緊急補修費", "4,500,000"),
            ("令和6年 2月", "外壁調査費", "3,800,000"), ("令和6年 7月", "緊急補修費", "5,100,000"), ("令和7年 1月", "緊急補修費", "4,200,000")]
    f = font(GOTH, h * 0.1); y = h * 0.08
    for a, b, c in rows:
        d.text((w * 0.04, y), a, font=f, fill=(60, 60, 70, 235)); d.text((w * 0.34, y), b, font=f, fill=(40, 40, 50, 255))
        d.text((w * 0.96 - d.textlength(c, font=f), y), c, font=f, fill=(40, 40, 50, 255)); y += h * 0.17
    return im


def art_lcd(w, h):
    im = canvas(w, h, (172, 178, 160, 255)); d = ImageDraw.Draw(im)
    t = "24,000,000."
    f = fit(d, t, GOTH, w * 0.9, h * 0.72)
    tw = d.textlength(t, font=f); d.text((w * 0.95 - tw, h * 0.12), t, font=f, fill=(32, 36, 30, 255))
    return im


def art_laptop(w, h):
    im = canvas(w, h, (236, 238, 242, 255)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h * 0.09), fill=(52, 70, 104, 255))
    d.text((w * 0.03, h * 0.02), "登記情報提供サービス", font=font(GOTH, h * 0.05), fill=(255, 255, 255, 255))
    d.text((w * 0.06, h * 0.14), "法人登記　履歴事項", font=font(MIN_B, h * 0.075), fill=(30, 30, 40, 255))
    rows = [("商号", COMPANY), ("代表者", "代表取締役　西園寺 剛"), ("本店所在地", "東京都港区 レンタルオフィス内"),
            ("従業員数", "0名"), ("設立", "令和5年3月1日")]
    y = h * 0.29; f1, f2 = font(GOTH, h * 0.052), font(GOTH, h * 0.058)
    for k, v in rows:
        d.rectangle((w * 0.06, y - h * 0.015, w * 0.94, y + h * 0.1), outline=(170, 176, 190, 255))
        d.rectangle((w * 0.06, y - h * 0.015, w * 0.3, y + h * 0.1), fill=(222, 228, 240, 255))
        d.text((w * 0.08, y + h * 0.01), k, font=f1, fill=(50, 50, 60, 255))
        d.text((w * 0.33, y + h * 0.005), v, font=f2, fill=(20, 20, 30, 255) if k != "代表者" else (190, 20, 30, 255))
        y += h * 0.115
    return im


def sns_post(w, h, date, caption, photo="bag", likes="1,284"):
    """가상 SNS 게시물(실존 서비스 UI·이름 없음)."""
    im = canvas(w, h, (255, 255, 255, 255)); d = ImageDraw.Draw(im)
    r = h * 0.035
    d.ellipse((w * 0.05, h * 0.03, w * 0.05 + r * 2, h * 0.03 + r * 2), fill=(196, 150, 120, 255))
    d.text((w * 0.05 + r * 2.4, h * 0.04), "reika_42F", font=font(MONT, h * 0.035), fill=(30, 30, 30, 255))
    y0, y1 = h * 0.11, h * 0.62
    if photo == "bag" and os.path.exists(BAG):
        p = Image.open(BAG).convert("RGB"); s = max(w / p.size[0], (y1 - y0) / p.size[1])
        p = p.resize((int(p.size[0] * s), int(p.size[1] * s)))
        p = p.crop(((p.size[0] - w) // 2, (p.size[1] - int(y1 - y0)) // 2, (p.size[0] - w) // 2 + int(w), (p.size[1] - int(y1 - y0)) // 2 + int(y1 - y0)))
        im.paste(p, (0, int(y0)))
    else:  # 리조트: 하늘·바다·모래 그라데이션 + 수영장 데크
        a = np.zeros((int(y1 - y0), int(w), 3), np.float32)
        for i in range(a.shape[0]):
            t = i / a.shape[0]
            a[i] = [110 + 60 * t, 170 + 30 * t, 235] if t < 0.45 else ([30, 140, 185] if t < 0.7 else [232, 216, 184])
        im.paste(Image.fromarray(a.astype(np.uint8)), (0, int(y0)))
        d.ellipse((w * 0.68, y0 + h * 0.04, w * 0.84, y0 + h * 0.12), fill=(255, 244, 200, 255))
    f = font(GOTH, h * 0.04)
    d.text((w * 0.05, h * 0.65), "♡  " + likes, font=f, fill=(30, 30, 30, 255))
    y = h * 0.72
    for ln in caption.split("\n"):
        d.text((w * 0.05, y), ln, font=font(GOTH, h * 0.045), fill=(20, 20, 20, 255)); y += h * 0.06
    d.text((w * 0.05, h * 0.92), date, font=font(GOTH, h * 0.032), fill=(130, 130, 130, 255))
    return im


def art_phone(w, h):
    im = canvas(w, h, (250, 250, 250, 255))
    im.alpha_composite(sns_post(w, h * 0.92, "2025.11.11", "主人からのサプライズ♡\n新作のバッグ #記念日"), (0, int(h * 0.06)))
    return im


def art_roster(w, h):
    im = canvas(w, h); d = ImageDraw.Draw(im)
    f = font(GOTH, h * 0.2)
    d.text((w * 0.05, h * 0.1), "42階", font=f, fill=INK + (255,)); d.text((w * 0.4, h * 0.1), "4201号室", font=f, fill=INK + (255,))
    d.text((w * 0.05, h * 0.52), "所有者", font=f, fill=INK + (255,))
    d.text((w * 0.4, h * 0.5), "小田切", font=font(MIN_B, h * 0.28), fill=INK + (255,))
    return im


def slide_passbook(w, h):
    im = canvas(w, h, (250, 250, 248, 255)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h * 0.13), fill=(30, 60, 110, 255))
    ctext(d, w / 2, h * 0.025, "修繕積立金口座　取引明細（抜粋）", fit(d, "修繕積立金口座　取引明細（抜粋）", MIN_B, w * 0.8, h * 0.075), (255, 255, 255, 255))
    cols = [0.04, 0.24, 0.66, 0.96]
    hdr = ["日付", "摘要", "お引出し"]
    rows = [("2025/11/10", "振込 " + COMPANY[:-4], "2,000,000"), ("2025/12/18", "振込 " + COMPANY[:-4], "1,800,000"),
            ("2026/01/20", "振込 " + COMPANY[:-4], "2,500,000"), ("2026/02/27", "振込 " + COMPANY[:-4], "1,600,000"),
            ("2026/04/15", "振込 " + COMPANY[:-4], "3,000,000")]
    y = h * 0.19; f = font(GOTH, h * 0.058)
    d.rectangle((w * 0.03, y - h * 0.01, w * 0.97, y + h * 0.075), fill=(226, 232, 242, 255))
    for c, t in zip(cols, hdr):
        d.text((w * c + (w * 0.3 if t == "お引出し" else 0), y), t, font=f, fill=(40, 40, 60, 255))
    y += h * 0.1
    for a, b, c in rows:
        d.line((w * 0.03, y - h * 0.012, w * 0.97, y - h * 0.012), fill=(200, 204, 212, 255), width=2)
        d.text((w * cols[0], y), a, font=f, fill=(30, 30, 40, 255)); d.text((w * cols[1], y), b, font=f, fill=(30, 30, 40, 255))
        d.text((w * 0.96 - d.textlength(c + "円", font=f), y), c + "円", font=f, fill=(180, 24, 30, 255)); y += h * 0.105
    ctext(d, w / 2, h * 0.86, "過去2年間　同様の振込 計27件", fit(d, "過去2年間　同様の振込 計27件", MIN_B, w * 0.7, h * 0.07), (180, 24, 30, 255))
    return im


def slide_pair(w, h, date, amount, sdate, caption, photo, stage):
    """스크린 쌍: 왼쪽 통장 행, 빨간 화살표, 오른쪽 SNS 게시물. stage 0 = 왼쪽만, 1 = 전부."""
    im = canvas(w, h, (246, 246, 244, 255)); d = ImageDraw.Draw(im)
    # 통장
    bx0, by0, bx1, by1 = w * 0.04, h * 0.2, w * 0.46, h * 0.8
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=int(h * 0.03), fill=(214, 232, 220, 255), outline=(120, 160, 135, 255), width=3)
    d.text((bx0 + w * 0.02, by0 + h * 0.04), "普通預金　修繕積立金口座", font=font(GOTH, h * 0.05), fill=(40, 70, 55, 255))
    d.text((bx0 + w * 0.02, by0 + h * 0.15), date, font=font(GOTH, h * 0.065), fill=(30, 30, 30, 255))
    d.text((bx0 + w * 0.02, by0 + h * 0.26), "振込 " + COMPANY[:-4], font=font(GOTH, h * 0.042), fill=(30, 30, 30, 255))
    fa = fit(d, amount, MIN_B, (bx1 - bx0) * 0.86, h * 0.13)
    d.rectangle((bx0 + w * 0.02, by0 + h * 0.36, bx1 - w * 0.02, by0 + h * 0.52), fill=(255, 255, 255, 255), outline=(190, 30, 36, 255), width=4)
    ctext(d, (bx0 + bx1) / 2, by0 + h * 0.375, amount, fa, (190, 24, 30, 255))
    if stage:
        ax0, ax1, ay = w * 0.49, w * 0.6, h * 0.5
        d.polygon([(ax0, ay - h * 0.04), (ax1 - w * 0.03, ay - h * 0.04), (ax1 - w * 0.03, ay - h * 0.09), (ax1, ay),
                   (ax1 - w * 0.03, ay + h * 0.09), (ax1 - w * 0.03, ay + h * 0.04), (ax0, ay + h * 0.04)], fill=(214, 40, 40, 255))
        pw, ph = w * 0.33, h * 0.9; px, py = w * 0.63, h * 0.05
        d.rounded_rectangle((px, py, px + pw, py + ph), radius=int(h * 0.05), fill=(30, 30, 34, 255))
        post = sns_post(pw * 0.9, ph * 0.88, sdate, caption, photo)
        im.alpha_composite(post, (int(px + pw * 0.05), int(py + ph * 0.06)))
    return im


def art_rules_book(w, h):
    """관리규약 펼침면 인쇄(외계어 획을 지운 종이 위 곱하기). 왼쪽 「区分所有者」, 오른쪽 「賃借人」."""
    im = canvas(w, h); d = ImageDraw.Draw(im)
    d.text((w * 0.07, h * 0.06), "管理規約　第35条（役員）", font=font(MIN_R, h * 0.065), fill=(60, 60, 60, 255))
    d.text((w * 0.07, h * 0.15), "理事及び監事は、組合員のうちから", font=font(MIN_R, h * 0.05), fill=(90, 90, 90, 255))
    ctext(d, w * 0.27, h * 0.36, "区分所有者", fit(d, "区分所有者", MIN_B, w * 0.38, h * 0.22), (20, 30, 70, 255))
    d.text((w * 0.57, h * 0.06), "第19条（専有部分の貸与）", font=font(MIN_R, h * 0.065), fill=(60, 60, 60, 255))
    ctext(d, w * 0.75, h * 0.36, "賃借人", fit(d, "賃借人", MIN_B, w * 0.32, h * 0.22), (150, 24, 30, 255))
    d.text((w * 0.57, h * 0.72), "※区分所有者ではない", font=font(MIN_R, h * 0.06), fill=(110, 40, 40, 255))
    return im


def art_envelope_text(w, h):
    im = canvas(w, h); d = ImageDraw.Draw(im)
    ctext(d, w * 0.42, h * 0.1, "家賃督促状", fit(d, "家賃督促状", MIN_B, w * 0.7, h * 0.8), (176, 24, 30, 255), spacing=int(w * 0.01))
    d.rectangle((w * 0.82, h * 0.15, w * 0.98, h * 0.85), outline=(176, 24, 30, 255), width=max(2, int(h * 0.05)))
    ctext(d, w * 0.9, h * 0.25, "親展", fit(d, "親展", MIN_B, w * 0.13, h * 0.45), (176, 24, 30, 255))
    return im


def art_pyramid(W, H, upto):
    """층별 피라미드 그래픽(오른쪽 반투명 패널). upto = 보이는 층 띠 수(아래부터)."""
    im = canvas(W, H); d = ImageDraw.Draw(im)
    x0, x1, y0, y1 = W * 0.56, W * 0.95, H * 0.12, H * 0.88
    d.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=(10, 16, 30, 150))
    cx, top, bot, half = (x0 + x1) / 2, y0 + H * 0.07, y1 - H * 0.07, (x1 - x0) * 0.42
    bands = [("低層階", (130, 140, 160)), ("中層階", (170, 175, 190)), ("上層階", (218, 186, 110))]
    n = 3
    for i, (label, col) in enumerate(bands[:upto]):
        yb, yt = bot - (bot - top) * i / n, bot - (bot - top) * (i + 1) / n
        wb, wt = half * (1 - i / n), half * (1 - (i + 1) / n)
        d.polygon([(cx - wb, yb - 4), (cx + wb, yb - 4), (cx + wt, yt + 4), (cx - wt, yt + 4)], fill=col + (235,))
        f = font(MIN_B, H * (0.05 if i < 2 else 0.042))
        ctext(d, cx, (yb + yt) / 2 - H * 0.03 + (H * 0.02 if i == 2 else 0), label, f, (20, 20, 30, 255) if i < 2 else (60, 30, 0, 255))
    return im


# ---------------- 대상 ----------------
P = lambda *xy: [tuple(map(float, p)) for p in xy]
JOBS = {
    # 로비 리셉션·벽 금속 명판
    "S02a2": [("ink", P((38, 308), (111, 323), (112, 422), (38, 424)), lambda w, h: art_plaque(w, h))],
    "S02c": [("ink", P((72, 299), (168, 313), (166, 408), (70, 410)), lambda w, h: art_plaque(w, h))],
    "S02d": [("ink", P((1062, 436), (1099, 428), (1100, 517), (1063, 515)), lambda w, h: art_plaque(w, h))],
    "S02e": [("ink", P((1185, 344), (1242, 331), (1243, 407), (1186, 413)), lambda w, h: art_plaque(w, h))],
    "S12-3b": [("ink", P((33, 382), (136, 381), (136, 471), (33, 472)), lambda w, h: art_plaque(w, h))],
    "S02b2": [("replace", P((1185, 330), (1290, 326), (1293, 430), (1188, 432)), lambda w, h: art_brass_plate(w, h))],
    # 라운지 예약판(외계어 판 통째 교체)
    "S02c2": [("replace", P((445, 323), (876, 323), (876, 570), (445, 570)), lambda w, h: art_lounge(w, h))],
    # 키즈룸 안내판
    "S03a": [("ink", P((967, 192), (1245, 171), (1243, 421), (971, 407)), lambda w, h: art_kids_board(w, h, "40階以上の居住者専用", (190, 30, 36)))],
    # 같은 안내판이 보이는 S03 후속 컷(연속성) — S03a와 같은 문구
    # S03d는 손바닥 인서트로 재생성(안내판이 화면에 없음) — 합성 대상에서 제외(2026-10-07)
    "S03e2": [("ink", P((994, 189), (1282, 170), (1282, 434), (994, 414)), lambda w, h: art_kids_board(w, h, "40階以上の居住者専用", (190, 30, 36)))],
    "S18a": [("ink", P((976, 177), (1265, 158), (1265, 425), (972, 407)), lambda w, h: art_kids_board(w, h, "どなたでもご利用ください", (30, 130, 70)))],
    # 통지서(손가락 보호)
    "S04b": [("paper", P((569, 392), (739, 392), (732, 605), (572, 605)), lambda w, h: art_notice(w, h))],
    # 현수막
    "S05d": [("ink", P((687, 102), (1144, 69), (1144, 143), (687, 176)), lambda w, h: art_banner(w, h, BANNER_RINJI))],
    "S06e": [("ink", P((696, 153), (1088, 133), (1088, 194), (696, 200)), lambda w, h: art_banner(w, h, BANNER_RINJI))],
    "S12-3a": [("ink", P((687, 219), (1137, 203), (1137, 250), (687, 262)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S13a": [("ink", P((848, 163), (1215, 141), (1215, 216), (848, 225)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S16a": [("ink", P((733, 164), (1282, 123), (1282, 204), (733, 236)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S17i": [("ink", P((706, 132), (1206, 93), (1202, 192), (706, 214)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S17-2c": [("ink", P((829, 114), (1284, 77), (1284, 139), (829, 169)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    # 수정 8(회의장 일관성 2026-10-07) 재생성 컷 현수막 — 방 기준(S05d·S13a)과 같은 위치
    "S05a": [("ink", P((700, 84), (1152, 74), (1152, 151), (701, 174)), lambda w, h: art_banner(w, h, BANNER_RINJI))],
    "S05b": [("ink", P((688, 85), (1143, 75), (1143, 153), (688, 176)), lambda w, h: art_banner(w, h, BANNER_RINJI))],
    "S06a": [("ink", P((689, 85), (1144, 76), (1144, 153), (689, 176)), lambda w, h: art_banner(w, h, BANNER_RINJI))],
    "S06d": [("ink", P((694, 85), (1150, 76), (1148, 153), (694, 176)), lambda w, h: art_banner(w, h, BANNER_RINJI))],
    "S14b": [("ink", P((848, 165), (1240, 143), (1240, 209), (849, 228)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S14k": [("ink", P((848, 165), (1239, 143), (1238, 206), (848, 226)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S14o": [("ink", P((848, 163), (1238, 142), (1238, 207), (848, 226)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S17h": [("ink", P((852, 163), (1240, 142), (1240, 207), (851, 225)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S14g": [("ink", P((867, 174), (1239, 139), (1239, 206), (867, 222)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S07a2": [("ink", P((687, 85), (1142, 75), (1142, 153), (687, 176)), lambda w, h: art_banner(w, h, BANNER_RINJI))],
    "S14d": [("ink", P((860, 36), (1184, 34), (1184, 92), (860, 96)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S17e2": [("ink", P((850, 166), (1240, 144), (1240, 208), (850, 230)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S16h2": [("ink", P((850, 164), (1240, 138), (1240, 224), (850, 226)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    "S16g2": [("ink", P((1037, 77), (1460, 52), (1460, 128), (1037, 143)), lambda w, h: art_banner(w, h, BANNER_TSUJO))],
    # 단상 명패·카운터 명판
    "S09a": [("ink", P((642, 390), (727, 388), (727, 430), (642, 433)), lambda w, h: art_label(w, h, "管理事務室", GOTH, (40, 40, 50), 0.42, "MANAGEMENT OFFICE"))],
    # 화물 엘리베이터 표지판
    "S19a": [("ink", P((205, 228), (269, 240), (270, 347), (206, 345)), lambda w, h: art_plaque(w, h, [("荷物用", MIN_B, 0.17), ("エレベーター", MIN_B, 0.11), ("", None, 0.04), ("SERVICE", MONT, 0.07), ("ELEVATOR", MONT, 0.07)]))],
    "S19b": [("ink", P((1032, 288), (1187, 288), (1187, 369), (1032, 369)), lambda w, h: art_label(w, h, "荷物用エレベーター", GOTH, (40, 44, 52), 0.34, "SERVICE ELEVATOR"))],
    "S19f": [("paper", P((969, 302), (1049, 302), (1049, 377), (969, 377)), lambda w, h: art_label(w, h, "荷物用エレベーター", GOTH, (40, 44, 52), 0.3, "SERVICE ELEVATOR"))],
    # 장부·계산기·노트북·휴대폰·명부
    "S10a": [("ink", P((360, 652), (850, 640), (900, 690), (420, 716)), lambda w, h: art_ledger(w, h))],
    "S10a2": [("emit", P((208, 303), (528, 249), (535, 289), (217, 356)), lambda w, h: art_lcd(w, h))],
    "S10c": [("emit", P((86, 316), (502, 317), (544, 614), (120, 628)), lambda w, h: art_laptop(w, h))],
    "S11a2": [("emit", P((766, 246), (936, 246), (936, 578), (766, 578)), lambda w, h: art_phone(w, h))],
    "S12a": [("ink", P((446, 495), (598, 491), (598, 568), (446, 571)), lambda w, h: art_roster(w, h))],
    # 스크린
    "S13e": [("screen", P((460, 200), (884, 200), (884, 412), (460, 412)), lambda w, h: slide_passbook(w, h))],
    "S16h": [("inpaint_ink", P((297, 275), (1063, 267), (1114, 420), (251, 425)), lambda w, h: art_rules_book(w, h))],
    "S17c": [("inpaint_ink", P((573, 462), (822, 474), (820, 522), (571, 510)), lambda w, h: art_envelope_text(w, h))],
}
PAIRS = {  # 스크린 쌍(2단계): 왼쪽 통장 → 화살표+게시물(ドン)
    "S14a": (P((338, 258), (842, 234), (842, 485), (338, 485)), ("2025/11/10", "2,000,000円", "2025.11.11", "主人からのサプライズ♡\n新作のハイブランドバッグ", "bag")),
    "S14c": (P((386, 243), (909, 243), (909, 486), (386, 486)), ("2026/01/20", "2,500,000円", "2026.01.21", "冬休みはハワイのスイートで\n家族時間", "resort")),
    "S14e": (P((333, 308), (865, 306), (865, 616), (333, 618)), ("2026/04/15", "3,000,000円", "2026.04.16", "主人が買ってくれた新作♥", "bag")),
}
STATE_T = {"S14a": [0.0, 0.42], "S14c": [0.0, 0.42], "S14e": [0.0, 0.3], "S02b": [0.0, 0.2, 0.42, 0.64], "S13e": [0.0, 0.18]}


# ---------------- 합성 ----------------
def sharpness(a, q):
    x, y, w, h = cv2.boundingRect(np.int32(q)); g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    pad = max(3, h // 6); roi = g[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad]
    return cv2.Laplacian(roi, cv2.CV_64F).var() if roi.size else 0


def protect_mask(a):
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    skin = (hsv[..., 0] < 25) & (hsv[..., 1] > 35) & (hsv[..., 1] < 170) & (hsv[..., 2] > 80)
    red = ((hsv[..., 0] < 8) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 120)
    dark = cv2.morphologyEx((hsv[..., 2] < 70).astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)) > 0
    m = (skin | red | dark).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(cv2.dilate(m, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.5)


def quad_size(q):
    q = np.float32(q)
    w = (np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3])) / 2
    h = (np.linalg.norm(q[3] - q[0]) + np.linalg.norm(q[2] - q[1])) / 2
    return w, h


def apply(a, mode, q, art_fn, sigma_override=None, protect=False):
    H, W = a.shape[:2]; q = np.float32(q)
    qw, qh = quad_size(q); k = max(1.0, 900 / max(qw, qh))   # 원화는 넉넉한 해상도로 그린 뒤 축소
    art = art_fn(qw * k, qh * k); arr = np.asarray(art.convert("RGBA")).astype(np.float32)
    h, w = arr.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (w, 0), (w, h), (0, h)]), q)
    p = cv2.warpPerspective(arr, M, (W, H), flags=cv2.INTER_AREA)
    inside = cv2.warpPerspective(np.ones((h, w), np.float32), M, (W, H), flags=cv2.INTER_LINEAR)
    s = sharpness(a, q)
    sigma = sigma_override if sigma_override is not None else (0 if s > 300 else qh * 0.02 * (1 - s / 300))
    if sigma > 0.4:
        p = cv2.GaussianBlur(p, (0, 0), sigma); inside = cv2.GaussianBlur(inside, (0, 0), sigma * 0.6)
    else:
        p = cv2.GaussianBlur(p, (0, 0), 0.5)
    rgb, al = p[..., :3], (p[..., 3] / 255.0)[..., None]
    af = a.astype(np.float32)
    lum = cv2.GaussianBlur(af.mean(2), (0, 0), max(2, qh * 0.12))
    ins = inside > 0.5
    rel = np.clip(lum / max(lum[ins].mean(), 1), 0.7, 1.2)[..., None] if ins.any() else 1
    if mode == "ink":
        out = af * (1 - al + al * rgb / 255.0)
    elif mode in ("replace", "screen"):
        m = inside[..., None]
        base = rgb * rel * (0.93 if mode == "screen" else 1.0)
        if mode == "screen":
            base = base * 0.9 + 18   # 투사 화면: 대비를 조금 낮추고 밝게
        out = af * (1 - m) + base * m
    elif mode == "emit":
        m = inside[..., None]; out = af * (1 - m) + rgb * 0.95 * m
    elif mode in ("paper", "inpaint_ink"):
        out = af
        if mode == "inpaint_ink":   # 외계어(어두운 획)를 지우고 종이로 메움
            mk = ((af.mean(2) < 110) & ins).astype(np.uint8) * 255
            mk = cv2.dilate(mk, np.ones((5, 5), np.uint8))
            out = cv2.inpaint(a, mk, 6, cv2.INPAINT_TELEA).astype(np.float32)
        else:
            col = np.median(af[ins].reshape(-1, 3), axis=0) if ins.any() else np.array([240, 240, 240])
            m = inside[..., None]; paper = np.clip(col * rel, 0, 255)
            out = af * (1 - m) + paper * m
        out = out * (1 - al + al * rgb / 255.0)
    else:
        raise ValueError(mode)
    if protect:
        pm = protect_mask(a)[..., None]
        out = out * (1 - pm) + af * pm
    return np.clip(out, 0, 255).astype(np.uint8)


# 무지 면은 질감이 없어 초점이 나간 것으로 오판됨 → 실제 초점(가장자리·나사 선명도)을 보고 직접 지정
SIGMA = {"S03a": 0.4, "S03d": 0.6, "S03e2": 0.6, "S18a": 0.4, "S16h": 0.5, "S19b": 1.0, "S19f": 0.5, "S11a2": 0.5, "S10c": 0.6, "S14e": 0.7,
         "S14c": 0.5, "S14a": 0.5, "S13e": 0.6, "S02c2": 0.4, "S04b": 0.4, "S12a": 0.4, "S17c": 0.4, "S10a2": 0.5, "S06a": 1.2}
PROTECT = {"S04b", "S10a", "S12a"}  # 손·펜·소매가 면을 가리는 컷


def main(only=None):
    os.makedirs(RAW, exist_ok=True)
    for sid in list(JOBS) + list(PAIRS) + ["S02b"]:   # 합성 대상만 원본 보관(처음 한 번)
        if not os.path.exists(os.path.join(RAW, f"{sid}-1.png")):
            shutil.copy(os.path.join(OUT, f"{sid}-1.png"), RAW)
    states, crops = {}, []
    sp = os.path.join(OUT, "_states.json")
    if os.path.exists(sp):
        states = json.load(open(sp))
    ids = list(JOBS) + list(PAIRS) + ["S02b"]
    for sid in ids:
        if only and sid not in only:
            continue
        a = np.asarray(Image.open(os.path.join(RAW, f"{sid}-1.png")).convert("RGB")).copy()
        qs = []
        if sid in JOBS:
            for mode, q, fn in JOBS[sid]:
                a = apply(a, mode, q, fn, SIGMA.get(sid), protect=sid in PROTECT); qs.append(q)
            if sid == "S13e":   # 스크린 점등: 꺼진 화면(어둡게) → 표
                raw = np.asarray(Image.open(os.path.join(RAW, f"{sid}-1.png")).convert("RGB")).copy()
                off = apply(raw, "screen", JOBS[sid][0][1], lambda w, h: canvas(w, h, (70, 78, 92, 255)), SIGMA.get(sid))
                Image.fromarray(off).save(os.path.join(OUT, f"{sid}-s0.png")); Image.fromarray(a).save(os.path.join(OUT, f"{sid}-s1.png"))
                states[sid] = [[t, f"{sid}-s{k}.png"] for k, t in enumerate(STATE_T[sid])]
        elif sid in PAIRS:
            q, args = PAIRS[sid]; raw = a.copy(); qs.append(q)
            for st in (0, 1):
                b = apply(raw, "screen", q, lambda w, h, st=st: slide_pair(w, h, *args, st), SIGMA.get(sid))
                Image.fromarray(b).save(os.path.join(OUT, f"{sid}-s{st}.png"))
            a = b
            states[sid] = [[t, f"{sid}-s{k}.png"] for k, t in enumerate(STATE_T[sid])]
        elif sid == "S02b":
            raw = Image.fromarray(a).convert("RGBA")
            for k in range(4):
                im = raw.copy(); im.alpha_composite(art_pyramid(*raw.size, k)); im.convert("RGB").save(os.path.join(OUT, f"{sid}-s{k}.png"))
            a = np.asarray(im.convert("RGB"))
            states[sid] = [[t, f"{sid}-s{k}.png"] for k, t in enumerate(STATE_T[sid])]
            qs.append(P((750, 90), (1280, 90), (1280, 680), (750, 680)))
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
