#!/usr/bin/env python3
"""『地下倉庫の伝票』 키프레임 화면 속 일본어 표기·그래픽 합성 (무과금, 로컬) — 규격 제7장 6, tower_composite.py 구조.

생성 화면은 무지(또는 외계어) → 실글꼴 원화를 원근 변형해 얹는다. 문구는 대본 §7·스토리보드 signage/gfx 그대로.
  ink      먹·인쇄(곱하기) — 현수막·라벨·종이 질감이 비친다
  replace  면을 통째로 바꿈(외계어 판·화면·종이). 면의 밝기 변화를 곱한다
  screen   투사 화면(프로젝터)      emit  발광 화면(노트북·모니터)
입력: assets/portraits/chika-kf-raw/<id>-1.png (합성 전 확정본 — 처음 실행 때 chika-keyframes에서 복사)
출력: assets/portraits/chika-keyframes/<id>-1.png, 시간차 등장 컷은 <id>-s<k>.png + _states.json
검수: assets/qa/chika/PHASE5_합성_검수.jpg
사용법: python3 scripts/chika_composite.py [id ...]
"""
import json
import os
import shutil
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from tower_composite import apply, canvas, ctext, fit, font  # noqa: E402  (합성 엔진 재사용)

RAW = os.path.join(ROOT, "assets", "portraits", "chika-kf-raw")
OUT = os.path.join(ROOT, "assets", "portraits", "chika-keyframes")
QA = os.path.join(ROOT, "assets", "qa", "chika", "PHASE5_합성_검수.jpg")
FD = os.path.join(ROOT, "scripts", "fonts")
MIN_B, MIN_R = os.path.join(FD, "ZenOldMincho-Bold.ttf"), os.path.join(FD, "ZenOldMincho-Regular.ttf")
GOTH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
MONT = os.path.join(FD, "Montserrat-VF.ttf")

COMPANY = "帝都商事株式会社"
BANNER_AUD = f"{COMPANY}　新規事業計画 発表会"
BANNER_BQ = "祝　権藤常務取締役　就任内定"
NAVY, INK, RED, GOLD = (24, 36, 72), (28, 28, 30), (196, 30, 36), (120, 90, 30)
ADDR = "東京都練馬区石神井台三丁目12-8"
FATHER = "田村　清"


def P(*pts):
    return [list(p) for p in pts]


def box(d, x0, y0, x1, y1, fill=None, outline=INK + (255,), w=2):
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=w)


# ---------------- 원화 ----------------
def art_banner(w, h, text, color=NAVY, bg=None):
    im = canvas(w, h, bg or (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = fit(d, text, MIN_B, w * 0.9, h * 0.5)
    ctext(d, w / 2, h * 0.26, text, f, color + (255,))
    return im


def art_plate(w, h, lines, bg=(236, 236, 232, 255), color=INK, path=GOTH, scale=None):
    """흰·스틸 명판: 여러 줄 중앙."""
    im = canvas(w, h, bg); d = ImageDraw.Draw(im)
    n = len(lines); sc = scale or min(0.62 / n, 0.5)
    fs = [fit(d, t, path, w * 0.86, h * sc) for t in lines]
    th = [d.textbbox((0, 0), t, font=f)[3] - d.textbbox((0, 0), t, font=f)[1] for t, f in zip(lines, fs)]
    gap = h * 0.08; total = sum(th) + gap * (n - 1); y = (h - total) / 2
    for t, f, hh in zip(lines, fs, th):
        ctext(d, w / 2, y, t, f, color + (255,)); y += hh + gap
    return im


def art_label(w, h, text, sub=None):
    """상자 라벨(먹): 연도 + 伝票."""
    im = canvas(w, h); d = ImageDraw.Draw(im)
    f = fit(d, text, GOTH, w * 0.86, h * (0.34 if sub else 0.46))
    bb = d.textbbox((0, 0), text, font=f); th = bb[3] - bb[1]
    y = h * 0.18 if sub else (h - th) / 2
    ctext(d, w / 2, y, text, f, INK + (255,))
    if sub:
        fs = fit(d, sub, GOTH, w * 0.86, h * 0.3); ctext(d, w / 2, y + th + h * 0.1, sub, fs, INK + (255,))
    box(d, w * 0.03, h * 0.03, w * 0.97, h * 0.97, outline=INK + (110,), w=max(1, int(h * 0.015)))
    return im


def art_idcard(w, h):
    im = canvas(w, h, (246, 246, 244, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.16], fill=NAVY + (255,))
    ctext(d, w / 2, h * 0.035, COMPANY, fit(d, COMPANY, GOTH, w * 0.9, h * 0.085), (255, 255, 255, 255))
    box(d, w * 0.3, h * 0.22, w * 0.7, h * 0.56, fill=(200, 205, 214, 255), outline=(150, 150, 150, 255), w=1)
    ctext(d, w / 2, h * 0.58, "企画部", fit(d, "企画部", GOTH, w * 0.8, h * 0.08), INK + (255,))
    ctext(d, w / 2, h * 0.67, "権藤　誠一", fit(d, "権藤　誠一", MIN_B, w * 0.85, h * 0.12), INK + (255,))
    return im


def slide_base(w, h):
    im = canvas(w, h, (240, 244, 250, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.13], fill=NAVY + (255,))
    d.rectangle([0, h * 0.13, w, h * 0.14], fill=(180, 150, 60, 255))
    return im, d


def art_ppt_title(w, h):
    im, d = slide_base(w, h)
    ctext(d, w * 0.5, h * 0.03, "新規事業計画　発表会", fit(d, "新規事業計画　発表会", GOTH, w * 0.8, h * 0.075), (255, 255, 255, 255))
    ctext(d, w * 0.5, h * 0.3, "サプライチェーン再構築案", fit(d, "サプライチェーン再構築案", MIN_B, w * 0.85, h * 0.14), NAVY + (255,))
    ctext(d, w * 0.5, h * 0.5, "— 物流コスト 18% 削減に向けて —", fit(d, "— 物流コスト 18% 削減に向けて —", GOTH, w * 0.7, h * 0.06), INK + (255,))
    tag = "作成者：森川沙織（最終更新 03:42）"
    f = fit(d, tag, GOTH, w * 0.5, h * 0.045)
    d.rectangle([w * 0.03, h * 0.9, w * 0.03 + d.textlength(tag, font=f) + h * 0.06, h * 0.97], fill=(255, 250, 200, 255), outline=(200, 170, 60, 255), width=2)
    d.text((w * 0.03 + h * 0.03, h * 0.905), tag, font=f, fill=INK + (255,))
    return im


def art_ppt_p42(w, h):
    im, d = slide_base(w, h)
    ctext(d, w * 0.5, h * 0.03, "P.42　サプライチェーン再構築案", fit(d, "P.42　サプライチェーン再構築案", GOTH, w * 0.85, h * 0.075), (255, 255, 255, 255))
    lines = ["① 地方倉庫 3拠点 → 2拠点へ統合", "② 直送比率 35% → 60%", "③ 在庫回転 年8回 → 年12回", "④ 初年度コスト削減 ▲4.2億円"]
    f = fit(d, max(lines, key=len), GOTH, w * 0.8, h * 0.08)
    for i, t in enumerate(lines):
        d.text((w * 0.08, h * (0.24 + i * 0.16)), t, font=f, fill=INK + (255,))
    d.text((w * 0.86, h * 0.92), "42", font=fit(d, "42", GOTH, w * 0.1, h * 0.05), fill=(120, 120, 120, 255))
    return im


def art_intranet(w, h):
    im = canvas(w, h, (250, 250, 250, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.1], fill=(50, 60, 90, 255))
    d.text((w * 0.03, h * 0.02), f"{COMPANY}　社内ポータル", font=fit(d, f"{COMPANY}　社内ポータル", GOTH, w * 0.6, h * 0.055), fill=(255, 255, 255, 255))
    d.text((w * 0.06, h * 0.17), "人事発令（本日付）", font=fit(d, "人事発令（本日付）", GOTH, w * 0.5, h * 0.07), fill=NAVY + (255,))
    d.line([w * 0.06, h * 0.27, w * 0.94, h * 0.27], fill=(180, 180, 180, 255), width=2)
    t1, t2, t3 = "【異動】企画部　森川沙織", "→　総務部付　文書管理室（地下二階）", "発令日：本日　　承認：企画部長　権藤"
    d.text((w * 0.08, h * 0.34), t1, font=fit(d, t1, GOTH, w * 0.84, h * 0.09), fill=INK + (255,))
    d.text((w * 0.12, h * 0.48), t2, font=fit(d, t2, GOTH, w * 0.8, h * 0.09), fill=RED + (255,))
    d.text((w * 0.08, h * 0.68), t3, font=fit(d, t3, GOTH, w * 0.84, h * 0.06), fill=(90, 90, 90, 255))
    return im


def art_voucher(w, h):
    """지출결의서(종이 통째 교체): 표 + 문구 + 빨간 인영."""
    im = canvas(w, h, (228, 206, 150, 255)); d = ImageDraw.Draw(im)
    ctext(d, w * 0.5, h * 0.05, "支　出　決　議　書", fit(d, "支　出　決　議　書", MIN_B, w * 0.5, h * 0.1), INK + (255,))
    d.line([w * 0.06, h * 0.19, w * 0.94, h * 0.19], fill=INK + (200,), width=2)
    rows = [("支払先", "株式会社サンライズ企画"), ("件　名", "コンサルタント料（当月分）"), ("金　額", "￥250,000－"), ("承認者", "企画部長　権藤")]
    fk = fit(d, "承認者", GOTH, w * 0.14, h * 0.07); fv = fit(d, rows[0][1], GOTH, w * 0.52, h * 0.085)
    for i, (k, v) in enumerate(rows):
        y0 = h * (0.23 + i * 0.15); y1 = y0 + h * 0.13
        box(d, w * 0.06, y0, w * 0.26, y1, outline=INK + (170,), w=2); box(d, w * 0.26, y0, w * 0.74, y1, outline=INK + (170,), w=2)
        d.text((w * 0.08, y0 + h * 0.025), k, font=fk, fill=INK + (255,)); d.text((w * 0.28, y0 + h * 0.02), v, font=fv, fill=INK + (255,))
    for i in range(3):   # 결재란
        x0 = w * (0.76 + i * 0.065)
        box(d, x0, h * 0.23, x0 + w * 0.06, h * 0.33, outline=INK + (170,), w=2)
    cx, cy, r = w * 0.84, h * 0.6, h * 0.11   # 인영
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RED + (210,), width=max(2, int(h * 0.012)))
    ctext(d, cx, cy - r * 0.45, "権藤", fit(d, "権藤", MIN_B, r * 1.5, r * 0.9), RED + (210,))
    return im


def art_db(w, h, highlight=True):
    """전표 데이터베이스(스프레드시트): サンライズ 행 노랑."""
    im = canvas(w, h, (252, 252, 252, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.09], fill=(60, 110, 70, 255))
    d.text((w * 0.02, h * 0.015), "支出伝票DB_2016-2025.xlsx", font=fit(d, "支出伝票DB_2016-2025.xlsx", GOTH, w * 0.6, h * 0.055), fill=(255, 255, 255, 255))
    cols = ["日付", "支払先", "件名", "金額", "承認"]; xs = [0.0, 0.16, 0.42, 0.72, 0.88, 1.0]
    fh = fit(d, "支払先", GOTH, w * 0.12, h * 0.055)
    y = h * 0.11
    for j, c in enumerate(cols):
        box(d, w * xs[j], y, w * xs[j + 1], y + h * 0.07, fill=(225, 230, 225, 255), outline=(180, 180, 180, 255), w=1)
        d.text((w * xs[j] + w * 0.01, y + h * 0.012), c, font=fh, fill=INK + (255,))
    rows = [("2024/01/31", "東海運輸株式会社", "倉庫保管料", "1,240,000", "権藤"), ("2024/01/31", "株式会社サンライズ企画", "コンサルタント料", "250,000", "権藤"),
            ("2024/02/15", "大和梱包資材", "資材購入", "386,500", "権藤"), ("2024/02/29", "株式会社サンライズ企画", "コンサルタント料", "250,000", "権藤"),
            ("2024/03/10", "北関東物流", "配送委託費", "2,015,000", "権藤"), ("2024/03/31", "株式会社サンライズ企画", "コンサルタント料", "250,000", "権藤"),
            ("2024/04/30", "株式会社サンライズ企画", "コンサルタント料", "250,000", "権藤"), ("2024/05/08", "丸和印刷", "カタログ印刷", "412,000", "権藤")]
    fr = fit(d, "株式会社サンライズ企画", GOTH, w * 0.24, h * 0.05)
    for i, r in enumerate(rows):
        y = h * (0.18 + i * 0.09)
        hl = highlight and "サンライズ" in r[1]
        for j, v in enumerate(r):
            box(d, w * xs[j], y, w * xs[j + 1], y + h * 0.085, fill=(255, 240, 120, 255) if hl else None, outline=(200, 200, 200, 255), w=1)
            d.text((w * xs[j] + w * 0.01, y + h * 0.018), v, font=fr, fill=INK + (255,))
    return im


def art_registry(w, h):
    im = canvas(w, h, (246, 242, 230, 255)); d = ImageDraw.Draw(im)
    ctext(d, w / 2, h * 0.04, "履歴事項全部証明書", fit(d, "履歴事項全部証明書", MIN_B, w * 0.8, h * 0.07), INK + (255,))
    ctext(d, w / 2, h * 0.12, "株式会社サンライズ企画", fit(d, "株式会社サンライズ企画", GOTH, w * 0.8, h * 0.055), INK + (255,))
    rows = [("本店", ADDR), ("会社成立の年月日", "平成28年4月1日"), ("目的", "経営コンサルティング業"), ("資本金の額", "金100万円"),
            ("役員に関する事項", f"代表取締役　{FATHER}"), ("", ADDR)]
    fk = fit(d, "役員に関する事項", GOTH, w * 0.3, h * 0.045); fv = fit(d, ADDR, GOTH, w * 0.56, h * 0.05)
    for i, (k, v) in enumerate(rows):
        y0 = h * (0.22 + i * 0.12)
        box(d, w * 0.05, y0, w * 0.38, y0 + h * 0.11, outline=INK + (150,), w=1); box(d, w * 0.38, y0, w * 0.95, y0 + h * 0.11, outline=INK + (150,), w=1)
        d.text((w * 0.06, y0 + h * 0.03), k, font=fk, fill=INK + (255,))
        d.text((w * 0.4, y0 + h * 0.028), v, font=fv, fill=(RED if i >= 4 else INK) + (255,))
    return im


def art_application(w, h):
    im = canvas(w, h, (240, 236, 220, 255)); d = ImageDraw.Draw(im)
    ctext(d, w / 2, h * 0.04, "弔慰金支給申請書", fit(d, "弔慰金支給申請書", MIN_B, w * 0.8, h * 0.07), INK + (255,))
    rows = [("申請者", "企画部長　権藤　誠一"), ("続柄", "義父"), ("故人氏名", FATHER), ("故人住所", ADDR), ("申請日", "七年前　三月十二日")]
    fk = fit(d, "故人氏名", GOTH, w * 0.24, h * 0.05); fv = fit(d, ADDR, GOTH, w * 0.6, h * 0.05)
    for i, (k, v) in enumerate(rows):
        y0 = h * (0.2 + i * 0.14)
        box(d, w * 0.05, y0, w * 0.33, y0 + h * 0.12, outline=INK + (150,), w=1); box(d, w * 0.33, y0, w * 0.95, y0 + h * 0.12, outline=INK + (150,), w=1)
        d.text((w * 0.06, y0 + h * 0.033), k, font=fk, fill=INK + (255,))
        d.text((w * 0.35, y0 + h * 0.03), v, font=fv, fill=(RED if k in ("続柄", "故人住所") else INK) + (255,))
    return im


def art_log(w, h):
    im = canvas(w, h, (22, 26, 34, 255)); d = ImageDraw.Draw(im)
    d.text((w * 0.03, h * 0.03), "承認ログ　system_approval.log", font=fit(d, "承認ログ　system_approval.log", GOTH, w * 0.7, h * 0.06), fill=(140, 200, 140, 255))
    rows = ["2024-02-29 18:02  承認  企画部長 権藤  社内端末 PC-0412", "2024-02-29 23:48  承認  企画部長 権藤  社外リモート接続", "2024-03-31 23:51  承認  企画部長 権藤  社外リモート接続", "2024-04-30 23:46  承認  企画部長 権藤  社外リモート接続"]
    f = fit(d, rows[1], GOTH, w * 0.92, h * 0.06)
    for i, t in enumerate(rows):
        y = h * (0.2 + i * 0.17)
        if i >= 1:
            d.rectangle([w * 0.02, y - h * 0.02, w * 0.98, y + h * 0.1], fill=(120, 90, 20, 255) if i == 1 else (60, 50, 25, 255))
        d.text((w * 0.03, y), t, font=f, fill=(255, 230, 120, 255) if i == 1 else (200, 210, 220, 255))
    return im


def art_receipt(w, h):
    im = canvas(w, h, (250, 248, 240, 255)); d = ImageDraw.Draw(im)
    ctext(d, w / 2, h * 0.05, "領　収　書", fit(d, "領　収　書", MIN_B, w * 0.5, h * 0.1), INK + (255,))
    rows = ["銀座　CLUB  L'ÉTOILE", "2024/02/29　23:41", "ご飲食代　￥186,000－", "上記正に領収いたしました", f"{COMPANY}　権藤 様"]
    f = fit(d, rows[2], GOTH, w * 0.8, h * 0.09)
    for i, t in enumerate(rows):
        y = h * (0.24 + i * 0.14)
        if i == 1:
            d.rectangle([w * 0.1, y - h * 0.015, w * 0.9, y + h * 0.1], fill=(255, 240, 120, 255))
        ctext(d, w / 2, y, t, f, (RED if i == 1 else INK) + (255,))
    return im


def art_mail(w, h, sent=False):
    im = canvas(w, h, (247, 248, 250, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.1], fill=(70, 80, 100, 255))
    d.text((w * 0.03, h * 0.02), "内部通報ホットライン（監査室直通）", font=fit(d, "内部通報ホットライン（監査室直通）", GOTH, w * 0.7, h * 0.055), fill=(255, 255, 255, 255))
    rows = [("宛先", "監査室　内部通報窓口"), ("件名", "企画部における不正支出の疑い（10年分の伝票）"), ("添付", "証拠資料一式.zip（1,214 ファイル）")]
    fk = fit(d, "宛先", GOTH, w * 0.1, h * 0.06); fv = fit(d, rows[1][1], GOTH, w * 0.78, h * 0.06)
    for i, (k, v) in enumerate(rows):
        y = h * (0.17 + i * 0.14)
        d.text((w * 0.04, y), k, font=fk, fill=(90, 90, 90, 255)); d.text((w * 0.16, y), v, font=fv, fill=INK + (255,))
        d.line([w * 0.04, y + h * 0.1, w * 0.96, y + h * 0.1], fill=(210, 210, 210, 255), width=1)
    if sent:
        d.rectangle([w * 0.2, h * 0.62, w * 0.8, h * 0.88], fill=(235, 250, 238, 255), outline=(40, 150, 80, 255), width=3)
        ctext(d, w / 2, h * 0.68, "送信完了", fit(d, "送信完了", GOTH, w * 0.5, h * 0.14), (30, 130, 70, 255))
    else:
        d.rectangle([w * 0.62, h * 0.72, w * 0.94, h * 0.9], fill=NAVY + (255,))
        ctext(d, w * 0.78, h * 0.76, "送信", fit(d, "送信", GOTH, w * 0.25, h * 0.1), (255, 255, 255, 255))
    return im


def art_projector(w, h):
    """프로젝터 스크린: 왼쪽 전표, 오른쪽 자금 흐름도."""
    im = canvas(w, h, (236, 242, 250, 255)); d = ImageDraw.Draw(im)
    ctext(d, w / 2, h * 0.03, "サンライズ企画　資金の流れ", fit(d, "サンライズ企画　資金の流れ", GOTH, w * 0.7, h * 0.08), NAVY + (255,))
    v = art_voucher(int(w * 0.4), int(h * 0.62)); im.paste(v, (int(w * 0.05), int(h * 0.17)))
    x0 = w * 0.52
    boxes = [(0.2, f"{COMPANY}\n経費（接待・コンサル）"), (0.47, "株式会社サンライズ企画\n（ペーパーカンパニー）"), (0.74, "妻の実家\n代表取締役＝義父")]
    f = fit(d, "株式会社サンライズ企画", GOTH, w * 0.38, h * 0.055)
    for i, (yy, t) in enumerate(boxes):
        y = h * yy
        box(d, x0, y, w * 0.95, y + h * 0.17, fill=(255, 255, 255, 255), outline=NAVY + (255,), w=3)
        for k, line in enumerate(t.split("\n")):
            ctext(d, (x0 + w * 0.95) / 2, y + h * (0.02 + k * 0.075), line, f, (RED if i == 2 and k == 1 else INK) + (255,))
        if i < 2:
            ay0 = y + h * 0.17; ay1 = h * boxes[i + 1][0]
            d.line([(x0 + w * 0.95) / 2, ay0, (x0 + w * 0.95) / 2, ay1], fill=RED + (255,), width=4)
            d.polygon([((x0 + w * 0.95) / 2 - w * 0.015, ay1 - h * 0.03), ((x0 + w * 0.95) / 2 + w * 0.015, ay1 - h * 0.03), ((x0 + w * 0.95) / 2, ay1)], fill=RED + (255,))
    t = "25万円 × 120か月 ＝ 3,000万円"
    ctext(d, w * 0.735, h * 0.93, t, fit(d, t, GOTH, w * 0.44, h * 0.06), RED + (255,))
    return im


def art_certificate(w, h):
    im = canvas(w, h, (248, 246, 236, 255)); d = ImageDraw.Draw(im)
    box(d, w * 0.03, h * 0.04, w * 0.97, h * 0.96, outline=GOLD + (255,), w=max(2, int(h * 0.012)))
    ctext(d, w / 2, h * 0.09, "表　彰　状", fit(d, "表　彰　状", MIN_B, w * 0.5, h * 0.16), INK + (255,))
    ctext(d, w / 2, h * 0.32, "宮本　殿", fit(d, "宮本　殿", MIN_B, w * 0.4, h * 0.1), INK + (255,))
    body = ["あなたは十年にわたり文書管理室において", "記録の保全に尽力し　会社の信頼回復に", "多大な貢献をされました"]
    fb = fit(d, body[0], MIN_R, w * 0.84, h * 0.065)
    for i, t in enumerate(body):
        ctext(d, w / 2, h * (0.47 + i * 0.1), t, fb, INK + (255,))
    ctext(d, w / 2, h * 0.82, f"{COMPANY}　代表取締役社長　大河内", fit(d, f"{COMPANY}　代表取締役社長　大河内", MIN_R, w * 0.8, h * 0.06), INK + (255,))
    return im


# ---------------- 합성 지시(키프레임 1344x768 좌표: 왼위·오른위·오른아래·왼아래) ----------------
STEEL = (170, 176, 182, 255)
JOBS = {
    # 강당 현수막·PPT
    "S02a": [("replace", P((495, 34), (873, 36), (873, 95), (495, 92)), lambda w, h: art_banner(w, h, BANNER_AUD, bg=(232, 226, 206, 255)))],
    "S02d": [("ink", P((341, 118), (1019, 118), (1019, 138), (341, 138)), lambda w, h: art_banner(w, h, BANNER_AUD)),
             ("screen", P((341, 171), (1014, 171), (1014, 537), (341, 537)), lambda w, h: art_ppt_p42(w, h))],
    "S02c": [("screen", P((0, 0), (689, 0), (689, 475), (0, 475)), lambda w, h: art_ppt_title(w, h))],
    # 사무실 모니터(인사 발령)
    "S04a": [("emit", P((362, 248), (958, 248), (958, 612), (362, 612)), lambda w, h: art_intranet(w, h))],
    # 지하 창고 문 명판·벽 표지·상자 라벨
    "S06a": [("replace", P((643, 416), (679, 416), (679, 441), (643, 441)), lambda w, h: art_plate(w, h, ["文書管理室"], bg=STEEL))],
    "S11b": [("replace", P((118, 200), (157, 205), (157, 300), (118, 305)), lambda w, h: art_plate(w, h, ["B2", "文書", "管理室"], bg=STEEL, scale=0.2))],
    "S11d": [("replace", P((458, 287), (503, 302), (502, 343), (457, 330)), lambda w, h: art_plate(w, h, ["文書管理室"], bg=STEEL))],
    "S11d2": [("replace", P((834, 329), (879, 323), (880, 385), (834, 391)), lambda w, h: art_plate(w, h, ["文書", "管理室"], bg=STEEL, scale=0.3))],
    "S11f": [("replace", P((631, 291), (658, 291), (658, 317), (631, 317)), lambda w, h: art_plate(w, h, ["文書管理室"], bg=(228, 228, 224, 255)))],
    "S06g2": [("ink", P((221, 496), (431, 525), (420, 621), (219, 588)), lambda w, h: art_label(w, h, "2016年度", "支出伝票"))],
    "S18d": [("ink", P((870, 368), (1042, 371), (1040, 506), (868, 503)), lambda w, h: art_label(w, h, "権藤関連", "証拠書類"))],
    # 전표·DB·등기부·신청서·로그·영수증·핫라인
    "S07d": [("replace", P((474, 320), (903, 378), (875, 609), (442, 545)), lambda w, h: art_voucher(w, h))],
    "S09b": [("emit", P((709, 295), (1070, 279), (1019, 560), (656, 519)), lambda w, h: art_db(w, h))],
    "S09g": [("emit", P((133, 306), (492, 296), (523, 508), (164, 541)), lambda w, h: art_db(w, h))],
    "S09h": [("replace", P((492, 385), (636, 388), (631, 583), (488, 580)), lambda w, h: art_registry(w, h)),
             ("replace", P((646, 386), (752, 388), (748, 596), (640, 592)), lambda w, h: art_application(w, h)),
             ("emit", P((793, 298), (1034, 298), (1034, 394), (793, 394)), lambda w, h: art_db(w, h))],
    "S10b": [("emit", P((376, 359), (590, 336), (606, 485), (393, 508)), lambda w, h: art_log(w, h))],
    "S10c": [("replace", P((404, 408), (928, 277), (979, 479), (454, 610)), lambda w, h: art_receipt(w, h)),
             ("emit", P((-79, 206), (201, 133), (281, 436), (0, 509)), lambda w, h: art_log(w, h))],
    # 연회장 현수막·프로젝터·사원증·표창장
    "S13a2": [("ink", P((380, 235), (962, 235), (962, 318), (380, 318)), lambda w, h: art_banner(w, h, BANNER_BQ, color=RED))],
    "S17a": [("ink", P((359, 277), (994, 277), (994, 373), (359, 373)), lambda w, h: art_banner(w, h, BANNER_BQ, color=RED))],
    "S14g": [("ink", P((355, 201), (975, 201), (975, 276), (355, 276)), lambda w, h: art_banner(w, h, BANNER_BQ, color=RED)),
             ("screen", P((394, 308), (925, 308), (925, 551), (394, 551)), lambda w, h: art_projector(w, h))],
    "S17b": [("replace", P((829, 500), (950, 500), (950, 700), (829, 700)), lambda w, h: art_idcard(w, h))],
    "S18f": [("replace", P((690, 205), (1045, 277), (996, 523), (640, 451)), lambda w, h: art_certificate(w, h))],
}
# 시간차 등장(교체 클립에서 크로스페이드): (시작 비율, 상태 생성 함수)
STATES = {
    "S09i": [(0.0, None), (0.45, "redline")],
    "S10e": [(0.0, lambda w, h: art_mail(w, h, False)), (0.62, lambda w, h: art_mail(w, h, True))],
}
S09I_Q = [P((421, 310), (644, 310), (644, 591), (421, 591)), P((696, 310), (946, 306), (950, 591), (700, 594))]
S10E_Q = P((52, 228), (612, 141), (677, 564), (118, 650))
SIGMA = {"S02c": 0.5, "S09b": 0.6, "S09g": 0.6,  "S06a": 0.9, "S11b": 0.8, "S11d": 0.5, "S11d2": 0.6, "S11f": 0.6, "S02a": 0.8, "S02d": 0.7, "S13a2": 0.5, "S17a": 0.6, "S14g": 0.7,
         "S17b": 0.5, "S18f": 0.5, "S07d": 0.5, "S09h": 0.5, "S10c": 0.6, "S10b": 0.5, "S04a": 0.6, "S18d": 0.4, "S06g2": 0.5}


# 레터박스 크롭한 원본(kf_letterbox_fix / 수동)의 좌표 보정: (l, t, w, h) → 측정 좌표는 크롭 전 기준
CROP = {"S06a": (48, 33, 1248, 702), "S18f": (57, 38, 1230, 692), "S09i": (130, 73, 1084, 610)}


def remap(q, sid):
    if sid not in CROP:
        return q
    l, t, w, h = CROP[sid]
    return [[(x - l) * 1344 / w, (y - t) * 768 / h] for x, y in q]


def redline(a):
    """S09i: 등기부 주소와 신청서 주소를 잇는 빨간 선."""
    im = Image.fromarray(a).convert("RGBA"); ov = canvas(*im.size); d = ImageDraw.Draw(ov)
    p0, p1 = (tuple(int(v) for v in remap([[600, 552]], "S09i")[0]), tuple(int(v) for v in remap([[745, 500]], "S09i")[0]))   # 등기부 役員 주소 행 ↔ 신청서 故人住所 행(크롭 보정)
    d.line([p0, p1], fill=RED + (230,), width=5)
    for p in (p0, p1):
        d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], outline=RED + (230,), width=4)
    im.alpha_composite(ov); return np.asarray(im.convert("RGB"))


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
        if sid == "S09i":
            q0, q1 = remap(S09I_Q[0], sid), remap(S09I_Q[1], sid)
            a = apply(a, "replace", q0, art_registry, 0.5); a = apply(a, "replace", q1, art_application, 0.5)
            Image.fromarray(a).save(os.path.join(OUT, f"{sid}-s0.png"))
            b = redline(a); Image.fromarray(b).save(os.path.join(OUT, f"{sid}-s1.png"))
            states[sid] = [[t, f"{sid}-s{k}.png"] for k, (t, _) in enumerate(STATES[sid])]; a = b; qs += [q0, q1]
        elif sid == "S10e":
            raw = a.copy()
            for k, (t, fn) in enumerate(STATES[sid]):
                b = apply(raw, "emit", S10E_Q, fn, 0.6); Image.fromarray(b).save(os.path.join(OUT, f"{sid}-s{k}.png"))
            states[sid] = [[t, f"{sid}-s{k}.png"] for k, (t, _) in enumerate(STATES[sid])]; a = b; qs.append(S10E_Q)
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
