#!/usr/bin/env python3
"""『柳の葉と一杯の水』 키프레임 화면 속 가상 표기 합성 (무과금, 로컬) → 최종 키프레임 폴더.

규격 제7장 6: 생성 화면은 무지 → 실글꼴 원화를 원근 변형해 얹는다. 이 작품의 표기(사용자 확정 2026-10-05):
  간판   「やなぎマート 鎌倉店」 (scripts/yanagi_signage.py 원화) — 초록 무지 간판 띠를 찾아 덮는다(아래 색 띠까지).
  번호판 「品川 300 あ ・・・1」 — 세단 컷의 흰 무지판.
  명찰   점장 「店長代理 坂本」, 유나 「沖」 — 가슴의 흰 무지 명찰.
자동 검출(색·모양)이 기본이고, 틀리면 QUADS에 네 모서리를 직접 적는다(키프레임 1344x768 픽셀, 왼위·오른위·오른아래·왼아래).
초점이 나간 면은 원화를 같은 정도로 흐리고, 원래 면의 밝기 변화를 곱해 조명을 따른다.

입력: assets/portraits/yanagi-kf-a|b/<id>-1.png (승인본)  출력: assets/portraits/yanagi-keyframes/<id>-1.png (전 컷)
검수: productions/willow-leaf-ja/qa/합성_검수.jpg (합성된 자리 확대)
사용법: python3 scripts/yanagi_composite.py
"""
import json
import os
import shutil
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import yanagi_signage as sg  # noqa: E402

SB = os.path.join(ROOT, "scripts", "storyboard", "yanagi.json")
OUT = os.path.join(ROOT, "assets", "portraits", "yanagi-keyframes")
QA = os.path.join(ROOT, "productions", "willow-leaf-ja", "qa", "합성_검수.jpg")
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FD = os.path.join(ROOT, "scripts", "fonts")
NAMES = {"SAKA": "店長代理　坂本", "YUNA": "沖"}
QUADS = {
    "S27k": {"name": [(712, 355), (848, 355), (848, 400), (712, 400)]},   # 점장 명찰 ECU(손가락 걸침)
    "S06a": {"sign": [(-640, 0), (246, 0), (246, 100), (-640, 100)], "door": [(154, 182), (253, 181), (253, 273), (154, 274)]},   # 화면 왼위에 잘린 간판(오른쪽 끝만 보임)
    "S21a": {"plate": [(976, 481), (1091, 480), (1092, 545), (976, 546)]},
}
INPAINT = {"S21a": [(1003, 312, 1028, 354)],   # 남은 엠블럼(보닛 장식) 지우기
           }
FILL = {"S20b": [((723, 146, 750, 190), (752, 146, 770, 190))]}  # 유리문 밖 실존 편의점 로고 → 옆 배경색으로 채움
BLUR = {"S27c2": [(245, 632, 552, 768)], "S27b": [(245, 632, 552, 768)]}  # 책상 위 서류 외계어 흐림
# 생성 실패 컷을 합격 컷에서 로컬로 만든다: S27b = S27c2 태블릿 화면에 CCTV 흑백 화면(S02a 장면) 합성
FROM = {"S27b": ("S27c2", "S02a", [(530, 373), (825, 371), (846, 517), (520, 519)])}


def cctv_art(src_id):
    im = Image.open(os.path.join(ROOT, f"assets/portraits/yanagi-kf-b/{src_id}-1.png")).convert("L")
    a = np.asarray(im.resize((640, 366))).astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 1.2) * 0.85 + 20 + np.random.default_rng(7).normal(0, 9, a.shape)
    for y in range(0, a.shape[0], 3):
        a[y] *= 0.9  # 주사선
    a = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(np.stack([a * 0.95, a, a * 1.02], -1).clip(0, 255).astype(np.uint8))
_QUADS_NOTE = {}   # {"S20d": {"sign": [...], "plate": [...], "name": [...]}} — 자동 검출 보정용
SKIP = {"S21b": {"plate"}, "S06a": {"name"}, "S27d": {"name"}, "S15a": {"name"}, "S20a": {"name"}}    # {"S08a": {"name"}} — 해당 표기 합성 안 함(가려짐·너무 작음)


# ---------- 원화 ----------
def plate_art(digit="1"):
    W, H = 660, 330; G = (18, 90, 50)
    im = Image.new("RGB", (W, H), (246, 246, 240)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, W - 7, H - 7), radius=22, outline=G, width=8)
    f1 = ImageFont.truetype(GOTHIC, 88); w = d.textlength("品川 300", font=f1); d.text(((W - w) / 2, 24), "品川 300", font=f1, fill=G)
    d.text((34, 185), "あ", font=ImageFont.truetype(GOTHIC, 92), fill=G)
    for k in range(3):
        cx = 200 + k * 95; d.ellipse((cx - 16, 228, cx + 16, 260), fill=G)
    f3 = ImageFont.truetype(GOTHIC, 200); bb = d.textbbox((0, 0), digit, font=f3)
    d.text((560 - (bb[2] - bb[0]) / 2 - bb[0], 320 - bb[3]), digit, font=f3, fill=G)
    return im


def name_art(text):
    W, H = 600, 200
    im = Image.new("RGB", (W, H), (248, 248, 244)); d = ImageDraw.Draw(im)
    m = sg.mark(150).convert("RGBA"); im.paste(m, (22, 25), m)
    f = ImageFont.truetype(os.path.join(FD, "ZenMaruGothic-Black.ttf"), 96 if len(text) <= 2 else 64)
    bb = d.textbbox((0, 0), text, font=f)
    d.text((190 + (W - 210 - (bb[2] - bb[0])) / 2 - bb[0], (H - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=(30, 30, 30))
    return im


def door_art():
    W, H = 600, 380
    im = Image.new("RGB", (W, H), (246, 246, 242)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 60), fill=sg.GREEN_B); d.rectangle((0, 60, W, 70), fill=sg.GOLD)
    m = sg.mark(120).convert("RGBA"); im.paste(m, (30, 110), m)
    fm = ImageFont.truetype(os.path.join(FD, "ZenMaruGothic-Black.ttf"), 64); d.text((175, 105), "やなぎマート", font=fm, fill=sg.GREEN_B)
    d.text((175, 185), "鎌倉店", font=ImageFont.truetype(os.path.join(FD, "ZenMaruGothic-Black.ttf"), 44), fill=(40, 40, 40))
    f2 = ImageFont.truetype(GOTHIC, 30); t = "運営：緒方ホールディングス株式会社"; w = d.textlength(t, font=f2)
    d.text(((W - w) / 2, 300), t, font=f2, fill=(50, 50, 50))
    return im


SIGN = sg.main_panel().convert("RGB")


# ---------- 검출 ----------
def order(pts):
    pts = np.array(pts, np.float32); s = pts.sum(1); d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)


def find_sign(a):
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV); H, W = a.shape[:2]
    m = ((hsv[..., 0] > 55) & (hsv[..., 0] < 95) & (hsv[..., 1] > 90) & (hsv[..., 2] > 45)).astype(np.uint8)
    m[int(H * 0.75):] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    best = None
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if w < W * 0.12 or area < H * W * 0.004 or w / max(h, 1) < 2.6:
            continue
        fill = area / (w * h)
        if fill < 0.55:
            continue
        if best is None or area > best[1]:
            best = (i, area)
    if not best:
        return None
    cnt, _ = cv2.findContours((lab == best[0]).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    q = order(cv2.boxPoints(cv2.minAreaRect(max(cnt, key=cv2.contourArea))))
    # 아래 색 띠(빨강·주황)까지 덮도록 아래로 18% 연장
    h = np.linalg.norm(q[3] - q[0]); dv = (q[3] - q[0]) / max(h, 1) * h * 0.18
    q[2] += dv; q[3] += dv
    return q


def green_around(a, q, k=1.6):
    x, y, w, h = cv2.boundingRect(q.astype(np.int32)); cx, cy = x + w / 2, y + h / 2
    x0, x1 = int(max(0, cx - w * k)), int(min(a.shape[1], cx + w * k)); y0, y1 = int(max(0, cy - h * k * 1.5)), int(min(a.shape[0], cy + h * k * 1.5))
    hsv = cv2.cvtColor(a[y0:y1, x0:x1], cv2.COLOR_RGB2HSV)
    g = (hsv[..., 0] > 45) & (hsv[..., 0] < 95) & (hsv[..., 1] > 22)
    return g.mean() if g.size else 0


def find_white_rect(a, region, aspect, area_frac, need_green=0.0, max_tilt=90):
    H, W = a.shape[:2]; x0, y0, x1, y1 = [int(v) for v in region]
    sub = a[y0:y1, x0:x1]; hsv = cv2.cvtColor(sub, cv2.COLOR_RGB2HSV)
    m = ((hsv[..., 1] < 45) & (hsv[..., 2] > 175)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    for c in cnts:
        area = cv2.contourArea(c)
        if not (H * W * area_frac[0] <= area <= H * W * area_frac[1]):
            continue
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(c)
        long_, short = max(rw, rh), max(min(rw, rh), 1)
        if not (aspect[0] <= long_ / short <= aspect[1]) or area / (rw * rh + 1e-6) < 0.75:
            continue
        bp = cv2.boxPoints(((cx, cy), (rw, rh), ang)); e1, e2 = bp[1] - bp[0], bp[2] - bp[1]
        lv = e1 if np.linalg.norm(e1) >= np.linalg.norm(e2) else e2
        tilt = abs(np.degrees(np.arctan2(lv[1], lv[0]))); tilt = min(tilt, 180 - tilt)
        if tilt > max_tilt:
            continue
        if need_green and green_around(a, order(cv2.boxPoints(((cx + x0, cy + y0), (rw, rh), ang)))) < need_green:
            continue
        if best is None or area > best[0]:
            best = (area, c)
    if not best:
        return None
    q = order(cv2.boxPoints(cv2.minAreaRect(best[1])))
    return q + np.array([x0, y0], np.float32)


# ---------- 합성 ----------
def sharpness(a, q):
    x, y, w, h = cv2.boundingRect(q.astype(np.int32)); g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    pad = max(3, h // 6); roi = g[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad]
    return cv2.Laplacian(roi, cv2.CV_64F).var() if roi.size else 0


def apply(a, art, q, blur_ref=None, keep_shading=True):
    H, W = a.shape[:2]; art = np.asarray(art).astype(np.float32); h, w = art.shape[:2]
    qh = np.linalg.norm(q[3] - q[0])
    # 초점이 나간 면이면 원화도 흐림(라플라시안 분산이 낮을수록 강하게)
    s = sharpness(a, q) if blur_ref is None else blur_ref
    sigma = 0 if s > 400 else (qh * 0.035 * (1 - s / 400))
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (w, 0), (w, h), (0, h)]), q)
    p = cv2.warpPerspective(art, M, (W, H), flags=cv2.INTER_AREA)
    m = cv2.warpPerspective(np.full((h, w), 1, np.float32), M, (W, H))
    if sigma > 0.5:
        p = cv2.GaussianBlur(p, (0, 0), sigma); m = cv2.GaussianBlur(m, (0, 0), sigma * 0.6)
    else:
        m = cv2.GaussianBlur(m, (3, 3), 0)
    out = p
    if keep_shading:
        lum = cv2.GaussianBlur(a.astype(np.float32).mean(2), (0, 0), max(2, qh * 0.15))
        ins = m > 0.5
        rel = np.clip(lum / max(lum[ins].mean(), 1), 0.7, 1.2)[..., None] if ins.any() else 1
        out = p * rel
    m = m[..., None]
    return np.clip(a * (1 - m) + out * m, 0, 255).astype(np.uint8)


def main():
    sb = json.load(open(SB, encoding="utf-8"))["scenes"]
    os.makedirs(OUT, exist_ok=True)
    log, crops = [], []
    for s in sb:
        if not s.get("keyframe"):
            continue
        src = os.path.join(ROOT, f"assets/portraits/yanagi-kf-{'a' if s['kind'] == 'd' else 'b'}/{s['id']}-1.png")
        dst = os.path.join(OUT, f"{s['id']}-1.png")
        if s["id"] in FROM:
            base, cc, q = FROM[s["id"]]
            src = os.path.join(ROOT, f"assets/portraits/yanagi-kf-b/{base}-1.png")
        if not os.path.exists(src):
            log.append(f"{s['id']}: 키프레임 없음"); continue
        a = np.asarray(Image.open(src).convert("RGB")).copy()
        if s["id"] in FROM:
            hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
            skin = ((hsv[..., 0] < 25) & (hsv[..., 1] > 40) & (hsv[..., 2] > 90)).astype(np.float32)
            skin = cv2.GaussianBlur(cv2.dilate(skin, np.ones((5, 5), np.uint8)), (0, 0), 2)[..., None]
            b = apply(a, cctv_art(cc), np.float32(q), blur_ref=1000, keep_shading=False)
            a = (b * (1 - skin) + a * skin).astype(np.uint8)
        for (x0, y0, x1, y1), (sx0, sy0, sx1, sy1) in FILL.get(s["id"], []):
            col = np.median(a[sy0:sy1, sx0:sx1].reshape(-1, 3), axis=0)
            a[y0:y1, x0:x1] = col; a[y0 - 4:y1 + 4, x0 - 2:x1 + 4] = cv2.GaussianBlur(a[y0 - 4:y1 + 4, x0 - 2:x1 + 4], (0, 0), 2)
        for (x0, y0, x1, y1) in BLUR.get(s["id"], []):
            a[y0:y1, x0:x1] = cv2.GaussianBlur(a[y0:y1, x0:x1], (0, 0), 9)
        done, sid, skip, qd = [], s["id"], SKIP.get(s["id"], set()), QUADS.get(s["id"], {})
        sigs = " ".join(s.get("signage", []))
        for (x0, y0, x1, y1) in INPAINT.get(sid, []):
            mk = np.zeros(a.shape[:2], np.uint8); mk[y0:y1, x0:x1] = 255
            a = cv2.cvtColor(cv2.inpaint(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), mk, 5, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB)
            done.append(("inpaint", np.float32([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])))
        if "やなぎマート" in sigs and "sign" not in skip:
            q = np.float32(qd["sign"]) if "sign" in qd else find_sign(a)
            if q is not None:
                a = apply(a, SIGN, q); done.append(("sign", q))
        if "運営" in sigs and "door" not in skip:
            H, W = a.shape[:2]
            q = np.float32(qd["door"]) if "door" in qd else find_white_rect(a, (0, H * 0.15, W, H * 0.8), (1.0, 2.4), (0.0004, 0.01), max_tilt=12)
            if q is not None:
                a = apply(a, door_art(), q); done.append(("door", q))
        if ("品川" in sigs or "plate" in qd) and "plate" not in skip:
            H, W = a.shape[:2]
            q = np.float32(qd["plate"]) if "plate" in qd else find_white_rect(a, (0, H * 0.35, W, H), (1.5, 2.6), (0.0004, 0.02))
            if q is not None:
                a = apply(a, plate_art(), q); done.append(("plate", q))
        if (s["nameplates"] and s["size"] not in ("ecu",) or "name" in qd) and "name" not in skip:
            H, W = a.shape[:2]
            key = "SAKA" if ("店長代理 坂本" in s["nameplates"] or any("sakamoto" in r for r in s["refs"])) else "YUNA"
            q = np.float32(qd["name"]) if "name" in qd else find_white_rect(a, (0, H * 0.25, W, H), (2.0, 5.5), (0.0002, 0.012), need_green=0.12, max_tilt=25)
            if q is not None:
                a = apply(a, name_art(NAMES[key]), q); done.append(("name", q))
        Image.fromarray(a).save(dst)
        for kind, q in done:
            x, y, w, h = cv2.boundingRect(q.astype(np.int32)); pad = max(30, h)
            box = (max(0, x - pad), max(0, y - pad), min(a.shape[1], x + w + pad), min(a.shape[0], y + h + pad))
            crops.append((f"{sid} {kind}", Image.fromarray(a).crop(box)))
        if done:
            log.append(f"{sid}: " + ", ".join(k for k, _ in done))
    # 검수 시트
    if crops:
        T = 300; cols = 5; rows = (len(crops) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * T, rows * (T + 24)), "white"); d = ImageDraw.Draw(sheet)
        f = ImageFont.truetype(GOTHIC, 18)
        for i, (lab, im) in enumerate(crops):
            im.thumbnail((T, T)); x, y = (i % cols) * T, (i // cols) * (T + 24)
            sheet.paste(im, (x, y + 24)); d.text((x + 4, y + 3), lab, font=f, fill="black")
        os.makedirs(os.path.dirname(QA), exist_ok=True); sheet.save(QA, quality=85)
    import yanagi_paper_text  # 서류·화면 일본어 글자(합성본 위에 다시 얹음)
    yanagi_paper_text.run(fresh=True)
    print("\n".join(log)); print(f"합성 {len(crops)}곳 → {OUT}, 검수 {QA}")


if __name__ == "__main__":
    main()
