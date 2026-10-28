"""벽시계 바늘 재작도(S07m 3:00 · S08a 2:58) — 타원(원근) 좌표로 바늘을 그린다(제20장 12 ⑨).
사용법: python3 scripts/yamibaito_clock_fix.py  → 키프레임 덮어쓰기 + out/fin/hd/sceneNN.mp4(1920x1080 푸시인)
"""
import os, sys, math, json, cv2, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KF = os.path.join(ROOT, "assets/portraits/yamibaito-keyframes")
HD = os.path.join(ROOT, "out/fin/hd"); QA = os.path.join(ROOT, "out/fin/phone_anim")
# sid: (원본 판, 중심, 눈금 바깥 반축 a·b, 시, 분)  — fitEllipse로 눈금 화소에서 측정(2026-10-28)
CLOCKS = {
    # 끝 3개: 인페인트 안쪽 타원 비율, 추가로 지울 옛 바늘 구간 [(각도, 시작 비율, 끝 비율)], 어두움 문턱(문자판 밝기보다 충분히 낮게 — 회색 문자판에 205를 쓰면 전체가 지워져 줄무늬)
    "S07m": ("S07m-1.png", (1801, 655), (443, 446), 3, 0, 0.80, [(348, 0.55, 0.86)], 140),   # NA43c 「午前三時」
    "S08a": ("_v2/S08a-1.png", (854, 713), (434, 580), 2, 58, 0.87, [], 205),              # NA44 「午前二時五十八分」
}

def pt(c, ab, deg, frac):
    th = math.radians(deg)
    return (int(round(c[0] + ab[0] * frac * math.sin(th))), int(round(c[1] - ab[1] * frac * math.cos(th))))

def hand(a, c, ab, deg, frac, width, tail=0.12):
    p2 = pt(c, ab, deg, frac); p1 = pt(c, ab, deg + 180, frac * tail)
    cv2.line(a, (p1[0] + 3, p1[1] + 4), (p2[0] + 3, p2[1] + 4), (40, 40, 44), width + 2, cv2.LINE_AA)  # 옅은 그림자
    cv2.line(a, p1, p2, (22, 22, 26), width, cv2.LINE_AA)

def fix(sid):
    src, c, ab, h, m, inner_f, extra, thr = CLOCKS[sid]
    a = cv2.imread(os.path.join(KF, src))
    g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    inner = np.zeros_like(g); cv2.ellipse(inner, c, (int(ab[0] * inner_f), int(ab[1] * inner_f)), 0, 0, 360, 255, -1)
    for deg, f0, f1 in extra:  # 눈금 띠 안쪽까지 뻗은 옛 바늘 끝만 좁게 지운다(눈금은 건드리지 않음)
        cv2.line(inner, pt(c, ab, deg, f0), pt(c, ab, deg, f1), 255, int(ab[0] * 0.08))
    dark = ((g < thr) & (inner > 0)).astype(np.uint8) * 255
    dark = cv2.dilate(dark, np.ones((13, 13), np.uint8))
    a = cv2.inpaint(a, dark, 9, cv2.INPAINT_TELEA)
    hand(a, c, ab, (h % 12 + m / 60) * 30, 0.56, int(ab[0] * 0.052))
    hand(a, c, ab, m * 6, 0.82, int(ab[0] * 0.036))
    cv2.ellipse(a, c, (int(ab[0] * 0.045), int(ab[1] * 0.045)), 0, 0, 360, (22, 22, 26), -1, cv2.LINE_AA)
    out = os.path.join(KF, f"{sid}-1.png"); cv2.imwrite(out, a)
    os.makedirs(QA, exist_ok=True); cv2.imwrite(os.path.join(QA, f"{sid}.jpg"), cv2.resize(a, (1280, 720)), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return out

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_yamibaito_overrides as ov; ov.W, ov.H = 1920, 1080
    sb = json.load(open(os.path.join(ROOT, "scripts/storyboard/yamibaito.json"), encoding="utf-8"))["scenes"]
    num = {s["id"]: i + 1 for i, s in enumerate(sb)}; durs = {s["id"]: s["assembled_s"] + 0.5 for s in sb}
    os.makedirs(HD, exist_ok=True)
    for sid in (sys.argv[1].split(",") if len(sys.argv) > 1 else CLOCKS):
        p = fix(sid); print("시계 재작도", sid, CLOCKS[sid][3:5], "→", p)
        ov.cam(p, os.path.join(HD, f"scene{num[sid]:02d}.mp4"), durs[sid], "push"); print("HD", f"scene{num[sid]:02d}.mp4")
