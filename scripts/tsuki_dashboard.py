#!/usr/bin/env python3
"""월浦エナジー 관제 화면(대시보드) 렌더러 — 고니감독님 지시 2026-10-16 「모니터 화면을 각본에 맞게 실감나게」.
참조: 관제실 격자 지도·텔레메트리·그래프·회로 발광. PIL로 그려 화면 쿼드에 합성(정지 컷) 또는 색 마스크로 i2v 클립에 합성.
모드: red(負荷分散 失敗) / green(正常) / countdown(期限まで あと一日) / authfail(認証失敗) / expired(ライセンス期限切れ) / blackout(制御停止)
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GOTH = os.path.join(ROOT, "scripts", "fonts", "ZenMaruGothic-Black.ttf")
DISTRICTS = ["商業地区", "オフィス街", "物流拠点", "住宅地区", "工業団地", "港湾地区", "鉄道沿線", "大学", "DC", "官庁街", "倉庫街", "空港"]


def F(size): return ImageFont.truetype(GOTH, max(8, int(size)))


def palette(mode):
    if mode == "green": return (40, 230, 120), (10, 40, 22), (120, 255, 180)
    if mode in ("countdown",): return (255, 150, 60), (40, 18, 8), (255, 220, 160)
    return (255, 70, 60), (45, 8, 8), (255, 200, 190)        # red 계열


def dashboard(w, h, mode="red", title=None, big=None, sub=None, seed=7):
    """w x h RGBA 대시보드. 왼쪽 2/3 격자 지도 + 오른쪽 텔레메트리, 위 헤더, 가운데 큰 상태 문구."""
    rnd = random.Random(seed)
    fg, bg, hi = palette(mode)
    im = Image.new("RGBA", (w, h), bg + (255,)); d = ImageDraw.Draw(im)
    # 배경 미세 격자(회로 느낌)
    for x in range(0, w, max(12, w // 80)): d.line([(x, 0), (x, h)], fill=fg + (22,))
    for y in range(0, h, max(12, h // 45)): d.line([(0, y), (w, y)], fill=fg + (22,))
    # 헤더
    d.rectangle([0, 0, w, h * 0.11], fill=fg + (40,)); d.line([(0, h * 0.11), (w, h * 0.11)], fill=fg + (200,), width=2)
    d.text((w * 0.02, h * 0.055), title or "月浦エナジー　電力グリッド監視", font=F(h * 0.05), fill=hi + (255,), anchor="lm")
    d.text((w * 0.98, h * 0.055), "KAGUYA v2.3  " + ("ONLINE" if mode == "green" else "ALERT"), font=F(h * 0.038), fill=hi + (230,), anchor="rm")
    # 격자 지도(왼쪽) : 도로망 + 구역 블록
    mx0, my0, mx1, my1 = w * 0.02, h * 0.15, w * 0.64, h * 0.93
    d.rectangle([mx0, my0, mx1, my1], outline=fg + (160,), width=2)
    cols, rows = 6, 4
    cw, ch = (mx1 - mx0) / cols, (my1 - my0) / rows
    for i in range(cols * rows):
        c, r = i % cols, i // cols
        x0, y0 = mx0 + c * cw + 6, my0 + r * ch + 6
        x1, y1 = x0 + cw - 12, y0 + ch - 12
        on = (mode == "green") or rnd.random() < (0.25 if mode in ("expired", "blackout") else 0.55)
        fill = fg + (70 if on else 18,)
        d.rectangle([x0, y0, x1, y1], fill=fill, outline=fg + (120,))
        # 블록 안 건물 사각형
        for k in range(rnd.randint(3, 6)):
            bx = x0 + rnd.uniform(0.1, 0.7) * (x1 - x0); by = y0 + rnd.uniform(0.1, 0.6) * (y1 - y0)
            d.rectangle([bx, by, bx + rnd.uniform(0.08, 0.25) * (x1 - x0), by + rnd.uniform(0.1, 0.3) * (y1 - y0)], outline=fg + (150,))
        name = DISTRICTS[i] if i < len(DISTRICTS) else f"区画{i + 1:02d}"
        state = "稼働" if mode == "green" else ("停止" if not on else "警告")
        d.text((x0 + 6, y1 - 6), f"{name}　{state}", font=F(ch * 0.17), fill=hi + (240,), anchor="ld")
    # 도로(발광선)
    for k in range(7):
        y = my0 + rnd.uniform(0.05, 0.95) * (my1 - my0)
        d.line([(mx0, y), (mx1, y)], fill=hi + (90,), width=2)
    for k in range(9):
        x = mx0 + rnd.uniform(0.05, 0.95) * (mx1 - mx0)
        d.line([(x, my0), (x, my1)], fill=hi + (90,), width=2)
    # 텔레메트리(오른쪽)
    tx0, ty0, tx1 = w * 0.66, h * 0.15, w * 0.98
    rows_t = [("総負荷", f"{rnd.uniform(1.2, 2.4):.2f} GW"), ("周波数", "50.0 Hz" if mode == "green" else f"{rnd.uniform(48.1, 49.4):.1f} Hz"),
              ("系統電圧", "275 kV" if mode == "green" else f"{rnd.randint(190, 240)} kV"), ("稼働区画", "24 / 24" if mode == "green" else f"{rnd.randint(3, 11)} / 24"),
              ("制御ノード", "正常" if mode == "green" else "応答なし"), ("ライセンス", "有効" if mode == "green" else ("残り 0 日" if mode == "countdown" else "無効"))]
    for k, (a, b) in enumerate(rows_t):
        y = ty0 + k * h * 0.075
        d.text((tx0, y), a, font=F(h * 0.04), fill=fg + (255,), anchor="lt")
        d.text((tx1, y), b, font=F(h * 0.045), fill=hi + (255,), anchor="rt")
        d.line([(tx0, y + h * 0.06), (tx1, y + h * 0.06)], fill=fg + (90,))
    # 그래프(부하 곡선)
    gx0, gy0, gx1, gy1 = tx0, h * 0.62, tx1, h * 0.93
    d.rectangle([gx0, gy0, gx1, gy1], outline=fg + (160,))
    pts = []
    n = 40
    for k in range(n):
        t = k / (n - 1)
        v = 0.5 + 0.25 * math.sin(t * 9) + rnd.uniform(-0.05, 0.05)
        if mode != "green" and t > 0.7: v = max(0.02, v - (t - 0.7) * 1.6)
        pts.append((gx0 + t * (gx1 - gx0), gy1 - v * (gy1 - gy0)))
    d.line(pts, fill=hi + (255,), width=3)
    d.text((gx0 + 6, gy0 + 4), "負荷分散 / 24h", font=F(h * 0.035), fill=fg + (255,), anchor="lt")
    # 큰 상태 문구(가운데)
    if big:
        bf = F(h * 0.17)
        tw = d.textlength(big, font=bf)
        bx, by = w / 2, h * 0.5
        d.rectangle([bx - tw / 2 - w * 0.02, by - h * 0.11, bx + tw / 2 + w * 0.02, by + h * 0.11], fill=(0, 0, 0, 150), outline=hi + (200,), width=3)
        d.text((bx, by - (h * 0.03 if sub else 0)), big, font=bf, fill=hi + (255,), anchor="mm")
        if sub:
            d.text((bx, by + h * 0.075), sub, font=F(h * 0.05), fill=hi + (230,), anchor="mm")
    # 글로우
    glow = im.filter(ImageFilter.GaussianBlur(6))
    out = Image.alpha_composite(glow, im)
    return out


if __name__ == "__main__":
    import sys
    dashboard(1600, 800, sys.argv[1] if len(sys.argv) > 1 else "red", big="負荷分散　失敗", sub="月見野スマートシティ 電力グリッド").save(sys.argv[2] if len(sys.argv) > 2 else "/tmp/dash.png")
