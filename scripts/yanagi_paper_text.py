#!/usr/bin/env python3
"""『柳の葉と一杯の水』 서류·화면 속 일본어 글자 합성 (규격 제7장 6 — 무지 면 생성 → 실글꼴·원근 합성, 무과금).

JA_OVERLAY(PHASE 3) 대상: S11b 休学届+病院 통지 / S14e 始末書 / S14f 病院 미납 통지(2회째) / S14j 在庫ロス原因報告(시말서 첨부) /
S15b 「喉の渇いた方、どうぞお持ちください」 손글씨 쪽지. 손·손가락이 면을 가리면 살색 마스크로 손을 다시 위에 올린다.
입력·출력: assets/portraits/yanagi-keyframes/<id>-1.png (합성 전 원본은 _pre/에 보관 → 다시 돌려도 이중 합성 안 됨)
사용법: python3 scripts/yanagi_paper_text.py
"""
import os
import shutil
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
def apply(a, art, q):
    """곱하기 블렌드: 종이·화면의 원래 밝기·그늘은 그대로 두고 잉크만 얹는다(먹이 종이에 스민 것처럼)."""
    H, W = a.shape[:2]; art = np.asarray(art).astype(np.float32) / 255.0; h, w = art.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (w, 0), (w, h), (0, h)]), q)
    p = cv2.warpPerspective(art, M, (W, H), flags=cv2.INTER_AREA, borderValue=(1, 1, 1))
    p = cv2.GaussianBlur(p, (0, 0), 0.6)
    # 원화 바탕(종이색)을 1로 정규화 → 글자만 어두워짐
    bg = np.median(art.reshape(-1, 3), axis=0)
    p = np.clip(p / np.maximum(bg, 1e-3), 0, 1)
    return np.clip(a.astype(np.float32) * p, 0, 255).astype(np.uint8)

KF = os.path.join(ROOT, "assets", "portraits", "yanagi-keyframes")
FD = os.path.join(ROOT, "scripts", "fonts")
MINCHO_B, MINCHO, KLEE = (os.path.join(FD, n) for n in ("ZenOldMincho-Bold.ttf", "ZenOldMincho-Regular.ttf", "KleeOne-Regular.ttf"))
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
INK = (35, 35, 40)


def paper(w, h, bg=(244, 243, 238)):
    return Image.new("RGB", (w, h), bg)


def shimatsusho():
    im = paper(700, 960); d = ImageDraw.Draw(im)
    d.text((350, 70), "始 末 書", font=ImageFont.truetype(MINCHO_B, 76), fill=INK, anchor="mm")
    f = ImageFont.truetype(MINCHO, 28)
    d.text((620, 150), "令和八年八月七日", font=f, fill=INK, anchor="rm")
    d.text((80, 205), "やなぎマート鎌倉店　店長代理　坂本健二　殿", font=f, fill=INK)
    body = ["私は、店舗の備品である給水器の水および", "紙コップを、許可なく私的に使用いたしました。",
            "ここに深くお詫び申し上げるとともに、", "今後二度とこのようなことのないよう", "誓約いたします。"]
    for i, t in enumerate(body):
        d.text((80, 300 + i * 56), t, font=f, fill=INK)
    d.text((80, 640), "なお、本件の弁償として三万円を", font=f, fill=INK)
    d.text((80, 696), "給与より差し引くことに同意します。", font=f, fill=INK)
    d.text((620, 820), "氏名　沖　結菜", font=ImageFont.truetype(MINCHO, 32), fill=INK, anchor="rm")
    d.ellipse((560, 860, 620, 920), outline=(170, 40, 40), width=3)  # 빈 날인란
    for y in (290, 630):
        d.line((70, y - 12, 630, y - 12), fill=(200, 200, 195), width=1)
    return im


def kyugaku_letter():
    im = paper(700, 960); d = ImageDraw.Draw(im)
    d.text((350, 80), "休 学 届", font=ImageFont.truetype(MINCHO_B, 72), fill=INK, anchor="mm")
    f = ImageFont.truetype(MINCHO, 30)
    for i, t in enumerate(["学部　文学部　　学年　二年", "氏名　沖　結菜", "休学期間　一年間", "理由　家庭の経済的事情のため"]):
        d.text((80, 220 + i * 90), t, font=f, fill=INK)
        d.line((70, 262 + i * 90, 630, 262 + i * 90), fill=(190, 190, 185), width=2)
    return im


def phone(lines, title="未払いのお知らせ"):
    im = Image.new("RGB", (540, 1100), (250, 250, 252)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 540, 150), fill=(232, 236, 242))
    d.text((270, 95), "メール", font=ImageFont.truetype(GOTHIC, 40), fill=(60, 60, 70), anchor="mm")
    d.text((40, 200), "【鎌倉みなと病院】", font=ImageFont.truetype(GOTHIC, 36), fill=(30, 30, 30))
    d.text((40, 260), title, font=ImageFont.truetype(GOTHIC, 44), fill=(180, 30, 30))
    f = ImageFont.truetype(GOTHIC, 34)
    for i, t in enumerate(lines):
        d.text((40, 360 + i * 64), t, font=f, fill=(40, 40, 40))
    return im


def phone_land(lines, title):
    im = Image.new("RGB", (1000, 460), (250, 250, 252)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1000, 70), fill=(214, 232, 240))
    d.text((40, 90), "【鎌倉みなと病院】" + title, font=ImageFont.truetype(GOTHIC, 46), fill=(180, 30, 30))
    f = ImageFont.truetype(GOTHIC, 40)
    for i, t in enumerate(lines):
        d.text((40, 180 + i * 70), t, font=f, fill=(40, 40, 40))
    return im


BILL = ["入院治療費のお支払いについて", "未納額　180,000円", "お支払い期限　8月20日"]


def loss_report():
    im = paper(600, 820, (248, 248, 250)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 600, 70), fill=(40, 90, 70))
    d.text((300, 36), "在庫ロス原因報告", font=ImageFont.truetype(GOTHIC, 40), fill=(255, 255, 255), anchor="mm")
    f = ImageFont.truetype(GOTHIC, 26)
    rows = [("店舗", "鎌倉店"), ("報告者", "店長代理　坂本"), ("ロス金額", "¥30,000"), ("原因", "従業員による備品の私的流用"), ("添付", "始末書（沖）")]
    for i, (k, v) in enumerate(rows):
        y = 110 + i * 70
        d.rectangle((30, y, 570, y + 56), outline=(190, 190, 195), width=2)
        d.text((46, y + 14), k, font=f, fill=(90, 90, 95)); d.text((200, y + 14), v, font=f, fill=(30, 30, 30))
    th = shimatsusho().resize((180, 247)); im.paste(th, (390, 480))
    d.rectangle((390, 480, 570, 727), outline=(150, 150, 150), width=2)
    return im


def note():
    im = paper(520, 700, (247, 244, 233)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(KLEE, 54)
    for i, t in enumerate(["喉の渇いた方、", "どうぞ", "お持ちください。"]):
        d.text((50, 120 + i * 120), t, font=f, fill=(40, 50, 90))
    return im


JOBS = {  # id: [(원화, 네 모서리)]
    "S11b": [(kyugaku_letter, [(396, 370), (655, 306), (703, 460), (487, 528)]),
             (lambda: phone(BILL), [(697, 318), (808, 316), (853, 500), (718, 508)])],
    "S14f": [(lambda: phone_land(BILL, "再度のお知らせ"), [(565, 592), (787, 598), (748, 700), (462, 690)])],
    "S14e": [(shimatsusho, [(489, 158), (752, 152), (766, 512), (502, 523)])],
    "S14j": [(loss_report, [(832, 362), (988, 358), (978, 568), (830, 563)])],
    "S15b": [(note, [(785, 460), (895, 462), (880, 610), (765, 597)])],
}


def skin_restore(base, out):
    hsv = cv2.cvtColor(base, cv2.COLOR_RGB2HSV)
    sk = (((hsv[..., 0] < 25) & (hsv[..., 1] > 45) & (hsv[..., 2] > 70))      # 맨손
          | ((hsv[..., 0] >= 18) & (hsv[..., 0] <= 38) & (hsv[..., 1] > 110) & (hsv[..., 2] > 80))).astype(np.float32)  # 노란 고무장갑
    sk = cv2.GaussianBlur(cv2.morphologyEx(sk, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)), (0, 0), 1.5)[..., None]
    return (out * (1 - sk) + base * sk).astype(np.uint8)


def run(jobs=None, fresh=False):
    pre = os.path.join(KF, "_pre"); os.makedirs(pre, exist_ok=True)
    for sid, items in (jobs or JOBS).items():
        p = os.path.join(KF, f"{sid}-1.png"); keep = os.path.join(pre, f"{sid}-1.png")
        if fresh or not os.path.exists(keep):
            shutil.copy(p, keep)
        base = np.asarray(Image.open(keep).convert("RGB")).copy(); a = base.copy()
        for fn, q in items:
            a = apply(a, fn(), np.float32(q))
        a = skin_restore(base, a)
        Image.fromarray(a).save(p); print("합성:", sid)


if __name__ == "__main__":
    run()
