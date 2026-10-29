#!/usr/bin/env python3
"""『引きこもりの息子』 PC 화면 합성(고니감독님 지시 2026-10-29 「모니터링 PC 화면에는 장면에 맞게 정확하게」「전체 PC 화면 수정」, 무료·로컬).

키프레임의 모니터는 무지(밝은 흰 면)로 생성되어 있다(제7장 6 — 생성기가 화면에 가짜 글자를 만들기 때문). 이 도구가
① 밝은 직사각 화면 면을 자동 검출(사각형 근사) → ② 이야기 시점에 맞는 일본어 UI를 그려 → ③ 원근 변형 + 휘도 키(화면 픽셀에만,
앞을 지나는 머리·손은 그대로)로 합성 + LCD 질감(제15장 17)을 입힌다.
같은 함수로 i2v 클립의 매 프레임도 합성한다(카메라 고정 → 키프레임에서 잡은 사각형 그대로, finalize에서 호출).

화면 내용(이야기 시점별):
  sleep  — 절전(검은 화면, 옅은 반사)            : S03c(낮)·S09a~S09e(아버지가 들어오기 전)
  lock   — 잠금 화면 + 비밀번호 입력란            : S09f(창업일 8자리 입력)
  work   — 大樹의 밤 작업(코드·모니터링·화상회의) : S05·S10h·S23 등 大樹 방
  dash   — 매출 대시보드(月間売上 ¥12,500,000)      : S09g~S10·S11 일부
  desk   — 폴더 하나 「父さんの工場」의 바탕화면    : S11a~S11c
  memo   — 메모 + 의존도 그래프 87%               : S11d~S11k
  office — 공장 사무실 생산관리 표                  : 사무실·공장 컷
  off    — 꺼진 화면                               : 회의실·거실 TV
사용법: python3 scripts/hikikomori_screens.py preview [id,…]   → assets/preview/hikikomori-screens/<id>.png + 시트
"""
import json, os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FONTM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SW, SH = 1600, 900


def F(sz, mono=False):
    return ImageFont.truetype(FONTM if mono else FONT, sz)


# ---------- 화면 내용 ----------
def sleep_screen():
    im = Image.new("RGB", (SW, SH), (6, 8, 12)); a = np.asarray(im).astype(float)
    g = np.linspace(0, 1, SW)[None, :, None] * np.linspace(0, 1, SH)[:, None, None]
    a += g * 10  # 유리 반사 기운
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


def lock_screen(dots=8):
    im = Image.new("RGB", (SW, SH)); d = ImageDraw.Draw(im)
    for y in range(SH):
        c = int(18 + 22 * y / SH); d.line([(0, y), (SW, y)], fill=(c, c + 6, c + 22))
    d.ellipse((SW / 2 - 70, 230, SW / 2 + 70, 370), fill=(70, 86, 110))
    d.ellipse((SW / 2 - 28, 255, SW / 2 + 28, 311), fill=(150, 165, 185)); d.pieslice((SW / 2 - 52, 305, SW / 2 + 52, 405), 180, 360, fill=(150, 165, 185))
    d.text((SW / 2, 420), "daiki", font=F(44), fill=(235, 238, 245), anchor="mm")
    d.rounded_rectangle((SW / 2 - 260, 480, SW / 2 + 260, 548), 8, fill=(240, 242, 246))
    d.text((SW / 2 - 240, 514), "●" * dots, font=F(30), fill=(40, 44, 52), anchor="lm")
    d.text((SW / 2, 590), "パスワード", font=F(28), fill=(200, 206, 218), anchor="mm")
    d.text((SW / 2, 650), "ヒント：工場の創業日", font=F(24), fill=(150, 158, 175), anchor="mm")
    d.text((80, SH - 90), "2:13", font=F(64), fill=(230, 233, 240), anchor="lm")
    d.text((86, SH - 40), "11月4日 火曜日", font=F(26), fill=(200, 205, 215), anchor="lm")
    return im


CODE = ["package auth", "", "// 認証トークンの検証（ヴァイスベルク研究所 向け）", "func VerifyToken(t string) (*Claims, error) {",
        "    key, err := kms.Fetch(ctx, \"lab-signing-key\")", "    if err != nil {", "        return nil, fmt.Errorf(\"鍵の取得に失敗: %w\", err)", "    }",
        "    claims, err := jwt.Parse(t, key)", "    if err != nil || claims.Expired() {", "        audit.Log(\"不正なトークン\", t[:8])",
        "        return nil, ErrUnauthorized", "    }", "    return claims, nil", "}", "", "// 次回: 多要素認証の導入（12/1 まで）"]
LOG = ["$ ./scan --target northgate-prod", "[02:11:04] 脆弱性スキャン開始 … 1,284 ホスト", "[02:11:58] OK  TLS 設定", "[02:12:31] OK  認証基盤",
       "[02:13:02] WARN 旧バージョンの API を検出（3 件）", "[02:13:40] 修正パッチを適用しました", "[02:14:05] 完了  重大な問題 0 件", "$ _"]


def work_screen(kind):
    im = Image.new("RGB", (SW, SH), (30, 31, 36)); d = ImageDraw.Draw(im)
    if kind == "code":
        d.rectangle((0, 0, SW, 46), fill=(45, 46, 52)); d.text((20, 23), "auth/verify.go — security-core", font=F(24), fill=(190, 192, 200), anchor="lm")
        d.rectangle((0, 46, 64, SH), fill=(38, 39, 44))
        for i, ln in enumerate(CODE):
            y = 70 + i * 46
            d.text((44, y), str(i + 1), font=F(24, True), fill=(110, 112, 120), anchor="rm")
            col = (106, 153, 85) if ln.strip().startswith("//") else (86, 156, 214) if ln.startswith(("func", "package")) else (212, 212, 212)
            d.text((86, y), ln, font=F(26, True) if not any(ord(c) > 0x3000 for c in ln) else F(26), fill=col, anchor="lm")
    elif kind == "term":
        im.paste((12, 14, 16), (0, 0, SW, SH))
        for i, ln in enumerate(LOG):
            col = (230, 190, 90) if "WARN" in ln else (120, 210, 130) if "OK" in ln or "完了" in ln else (210, 214, 220)
            d.text((40, 70 + i * 62), ln, font=F(32), fill=col, anchor="lm")
    elif kind == "meet":
        im.paste((24, 26, 30), (0, 0, SW, SH)); d.rectangle((0, 0, SW, 60), fill=(36, 38, 44))
        d.text((24, 30), "定例会議　ヴァイスベルク研究所 × D. Seo　（現地 10:00）", font=F(26), fill=(225, 228, 235), anchor="lm")
        names = ["M. Weber", "K. Fischer", "L. Braun", "瀬尾"]
        for k, nm in enumerate(names):
            x0 = 40 + (k % 2) * 770; y0 = 90 + (k // 2) * 395
            d.rounded_rectangle((x0, y0, x0 + 740, y0 + 375), 12, fill=(48, 52, 60))
            d.ellipse((x0 + 300, y0 + 110, x0 + 440, y0 + 250), fill=(90 + 30 * k, 110, 150 - 20 * k))
            d.text((x0 + 370, y0 + 180), nm[0], font=F(64), fill=(240, 240, 245), anchor="mm")
            d.text((x0 + 20, y0 + 345), nm, font=F(26), fill=(220, 222, 228), anchor="lm")
    elif kind == "graph":
        im.paste((20, 24, 32), (0, 0, SW, SH))
        d.text((40, 40), "トラフィック監視　ノースゲート・システムズ", font=F(30), fill=(220, 225, 235), anchor="lm")
        rng = np.random.default_rng(3)
        for row, (lab, col) in enumerate([("リクエスト数", (90, 170, 250)), ("応答時間", (250, 180, 80)), ("エラー率", (240, 100, 100))]):
            y0 = 110 + row * 260; d.text((40, y0), lab, font=F(24), fill=(170, 176, 190), anchor="lm")
            pts = np.cumsum(rng.normal(0, 6, 60)) + 120
            pts = (pts - pts.min()) / (np.ptp(pts) + 1) * 170
            d.line([(60 + i * 25, y0 + 220 - p) for i, p in enumerate(pts)], fill=col, width=4)
            d.line([(60, y0 + 222), (SW - 60, y0 + 222)], fill=(60, 66, 80), width=2)
    return im


def dash_screen():
    im = Image.new("RGB", (SW, SH), (244, 246, 249)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, SW, 70), fill=(28, 44, 78)); d.text((30, 35), "Seo Security Lab　ダッシュボード", font=F(30), fill=(255, 255, 255), anchor="lm")
    d.text((SW - 30, 35), "瀬尾大樹 — リードセキュリティアーキテクト", font=F(24), fill=(200, 210, 230), anchor="rm")
    d.rounded_rectangle((40, 100, 760, 330), 12, fill=(255, 255, 255), outline=(220, 224, 232))
    d.text((70, 140), "月間売上", font=F(30), fill=(90, 98, 112), anchor="lm"); d.text((70, 240), "¥12,500,000", font=F(80), fill=(20, 30, 50), anchor="lm")
    d.rounded_rectangle((800, 100, SW - 40, 330), 12, fill=(255, 255, 255), outline=(220, 224, 232))
    vals = [6.2, 7.1, 7.8, 8.9, 10.4, 11.2, 12.5]
    for i, v in enumerate(vals):
        x = 850 + i * 105; h = int(v / 12.5 * 170); d.rectangle((x, 310 - h, x + 60, 310), fill=(60, 120, 220))
    d.text((830, 125), "売上推移（7か月）", font=F(22), fill=(90, 98, 112), anchor="lm")
    d.rounded_rectangle((40, 360, SW - 40, SH - 40), 12, fill=(255, 255, 255), outline=(220, 224, 232))
    d.text((70, 400), "主要クライアント", font=F(28), fill=(40, 50, 70), anchor="lm")
    rows = [("ノースゲート・システムズ", "米国", "セキュリティ設計", "継続"), ("東証プライム上場IT企業", "日本", "脆弱性診断", "継続"),
            ("ヴァイスベルク研究所", "ドイツ", "研究基盤の防御設計", "新規")]
    for i, r in enumerate(rows):
        y = 470 + i * 100; d.line([(70, y - 40), (SW - 70, y - 40)], fill=(230, 232, 238), width=2)
        for x, t in zip((70, 700, 900, 1350), r):
            d.text((x, y), t, font=F(30), fill=(30, 36, 48), anchor="lm")
    return im


def desk_screen(open_folder=False):
    im = Image.new("RGB", (SW, SH)); d = ImageDraw.Draw(im)
    for y in range(SH):
        d.line([(0, y), (SW, y)], fill=(16, 34 + int(30 * y / SH), 70 + int(40 * y / SH)))
    x, y = SW - 220, 120
    d.rounded_rectangle((x, y + 18, x + 130, y + 110), 8, fill=(240, 196, 80)); d.rounded_rectangle((x, y, x + 60, y + 30), 6, fill=(240, 196, 80))
    d.text((x + 65, y + 140), "父さんの工場", font=F(30), fill=(255, 255, 255), anchor="mm")
    if open_folder:
        d.rounded_rectangle((200, 160, 1250, 760), 10, fill=(250, 250, 252)); d.rectangle((200, 160, 1250, 210), fill=(230, 232, 238))
        d.text((220, 185), "父さんの工場", font=F(26), fill=(30, 30, 40), anchor="lm")
        for i, nm in enumerate(["瀬尾精工_再建計画.pdf", "鳳凰工業_依存度.xlsx", "メモ.txt", "値下げ記録_5年分.xlsx"]):
            d.text((260, 270 + i * 80), "📄 " + nm if False else nm, font=F(30), fill=(30, 40, 60), anchor="lm")
    return im


MEMO = ["鳳凰の値下げ、あと一年で限界。", "新しい取引先を、必ず見つける。", "", "・ヴァイスベルク研究所：部品の加工先を探している", "・父さんの旋盤なら作れる",
        "", "父さんには、決まってから話す。"]


def memo_screen():
    im = Image.new("RGB", (SW, SH), (250, 250, 247)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, SW, 50), fill=(232, 232, 228)); d.text((20, 25), "メモ.txt", font=F(24), fill=(60, 60, 60), anchor="lm")
    for i, ln in enumerate(MEMO):
        d.text((60, 110 + i * 62), ln, font=F(36), fill=(30, 30, 30), anchor="lm")
    x0, y0 = 1040, 120; d.rounded_rectangle((x0, y0, SW - 40, 560), 10, fill=(255, 255, 255), outline=(215, 215, 210))
    d.text((x0 + 20, y0 + 30), "鳳凰工業への依存度", font=F(26), fill=(50, 50, 50), anchor="lm")
    d.pieslice((x0 + 90, y0 + 80, x0 + 410, y0 + 400), -90, -90 + 360 * 0.87, fill=(210, 70, 60)); d.pieslice((x0 + 90, y0 + 80, x0 + 410, y0 + 400), -90 + 360 * 0.87, 270, fill=(200, 200, 200))
    d.text((x0 + 250, y0 + 240), "87%", font=F(56), fill=(255, 255, 255), anchor="mm")
    return im


def office_screen():
    im = Image.new("RGB", (SW, SH), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, SW, 60), fill=(33, 115, 70)); d.text((20, 30), "生産管理表　瀬尾精工", font=F(30), fill=(255, 255, 255), anchor="lm")
    cols = ["品番", "品名", "数量", "納期", "取引先"]; xs = [30, 230, 700, 900, 1150]
    rows = [("A-1024", "シャフト", "400", "11/08", "鳳凰工業"), ("A-1031", "フランジ", "250", "11/10", "鳳凰工業"), ("B-0207", "ブッシュ", "1,200", "11/12", "鳳凰工業"),
            ("C-0090", "試作ピン", "30", "11/15", "鳳凰工業"), ("A-1040", "スリーブ", "600", "11/20", "鳳凰工業")]
    for j, c in enumerate(cols):
        d.text((xs[j], 110), c, font=F(30), fill=(30, 30, 30), anchor="lm")
    for i, r in enumerate(rows):
        y = 190 + i * 90; d.line([(20, y - 45), (SW - 20, y - 45)], fill=(210, 210, 210), width=2)
        for j, t in enumerate(r):
            d.text((xs[j], y), t, font=F(30), fill=(40, 40, 40), anchor="lm")
    return im


def off_screen():
    return Image.new("RGB", (SW, SH), (8, 9, 11))



def dashnum_screen():
    im = dash_screen().crop((0, 70, 800, 520)).resize((SW, SH), Image.LANCZOS)
    return im


def clients_screen():
    im = dash_screen(); return im.crop((0, 340, SW, SH)).resize((SW, SH), Image.LANCZOS)


def cal_screen():
    im = Image.new("RGB", (SW, SH), (250, 251, 253)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, SW, 70), fill=(40, 90, 170)); d.text((30, 35), "カレンダー　11月", font=F(32), fill=(255, 255, 255), anchor="lm")
    days = ["月", "火", "水", "木", "金", "土", "日"]; cw = (SW - 120) / 7
    for i, dn in enumerate(days):
        x = 100 + i * cw; d.text((x + cw / 2, 105), f"{dn}  {i + 3}日", font=F(28), fill=(60, 60, 70), anchor="mm")
        d.line([(x, 130), (x, SH - 20)], fill=(225, 228, 235), width=2)
    for h in range(6):
        y = 160 + h * 120; d.text((90, y), f"午前{h * 2}:00" if h else "午前0:00", font=F(22), fill=(140, 144, 155), anchor="rm")
        d.line([(100, y), (SW - 20, y)], fill=(235, 237, 242), width=1)
    for i in range(7):
        x = 100 + i * cw
        d.rounded_rectangle((x + 8, 280, x + cw - 8, 395), 8, fill=(66, 133, 244))
        d.text((x + 18, 300), "午前2:00", font=F(22), fill=(255, 255, 255), anchor="lm")
        d.text((x + 18, 335), "オンライン会議", font=F(22), fill=(255, 255, 255), anchor="lm")
        d.text((x + 18, 368), "（現地 午前10:00）", font=F(18), fill=(225, 235, 255), anchor="lm")
    return im


def content(kind):
    return {"sleep": sleep_screen, "lock": lock_screen, "dash": dash_screen, "desk": desk_screen, "deskopen": lambda: desk_screen(True),
            "memo": memo_screen, "office": office_screen, "off": off_screen, "code": lambda: work_screen("code"), "term": lambda: work_screen("term"),
            "meet": lambda: work_screen("meet"), "graph": lambda: work_screen("graph"), "dashnum": dashnum_screen,
            "clients": clients_screen, "cal": cal_screen}[kind]()


# ---------- 컷별 화면 배정(왼쪽→오른쪽) ----------
WORK3 = ["code", "graph", "term"]
PLAN = {
    "S03c": ["off"] * 3, "S05b": ["code", "meet", "term"], "S05c": WORK3, "S05d": WORK3, "S05e": WORK3, "S05f": ["code", "term", "graph"], "S05g": WORK3,
    "S05h": WORK3, "S05i": ["meet", "code", "term"], "S09a": ["sleep"] * 3, "S09b": ["sleep"] * 3, "S09c": ["sleep"] * 3, "S09d": ["sleep"] * 3,
    "S09e": ["sleep"], "S09f": ["sleep", "lock", "sleep"], "S09g": ["graph", "dash", "term"], "S09h": ["graph", "dash", "term"],
    "S10b": ["graph", "dash", "term"], "S10f": ["graph", "dash", "term"], "S10h": ["meet", "code", "term"],
    "S11a": ["graph", "desk", "term"], "S11d": ["graph", "memo", "term"], "S11f": ["graph", "memo", "term"], "S11g": ["memo", "graph"],
    "S11h": ["graph", "memo", "term"], "S11i": ["graph", "memo", "term"], "S11j": ["graph", "memo", "term"], "S11k": ["graph", "memo", "term"],
    "S23c": ["code", "meet", "term"], "S23d": WORK3, "S23e": WORK3, "S23f": WORK3, "S23g": WORK3, "S23j": WORK3, "S23k": WORK3, "S23h": ["code"],
}
DEFAULT_BY_LOC = {"ROOM_N": WORK3, "ROOM_C": WORK3, "ROOM_M": WORK3, "OFF_D": ["office"] * 3, "OFF_DESK": ["office"] * 3, "OFF_N": ["off"] * 3,
                  "FAC_D": ["office"] * 3, "LATHE": ["office"] * 3, "MEET": ["off"] * 3, "MEET_T": ["off"] * 3, "MEET_DOOR": ["off"] * 3,
                  "MEET_OPEN": ["off"] * 3, "HOME_DIN": ["off"] * 3, "HOME_LIV": ["off"] * 3}
SKIP = {"S10a", "S10c", "S10d", "S10e", "S11b", "S11c", "S11e", "S19e"}  # 전체 화면 합성 컷(별도 대시보드 렌더 — 같은 함수로 화면 전체)
FULL = {"S10a": "dash", "S10c": "dash", "S10d": "dash", "S10e": "cal", "S11b": "desk", "S11c": "desk", "S11e": "memo"}


# ---------- 검출·합성 ----------
def detect(img, min_frac=0.004):
    """밝고 채도 낮은 사각형 = 무지 모니터 면. [(4점 TL,TR,BR,BL), …] 왼쪽→오른쪽."""
    a = np.asarray(img.convert("RGB")); hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    m = ((hsv[..., 2] > 175) & (hsv[..., 1] < 70)).astype("uint8") * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    H, W = m.shape; out = []
    for c in cs:
        ar = cv2.contourArea(c)
        if ar < min_frac * W * H:
            continue
        hull = cv2.convexHull(c); ap = cv2.approxPolyDP(hull, 0.03 * cv2.arcLength(hull, True), True)
        if len(ap) != 4 or ar / max(cv2.contourArea(ap), 1) < 0.8:
            continue
        p = ap.reshape(4, 2).astype(float); s = p.sum(1); df = np.diff(p, axis=1).ravel()
        q = np.array([p[s.argmin()], p[df.argmin()], p[s.argmax()], p[df.argmax()]])
        w = np.linalg.norm(q[1] - q[0]); h = np.linalg.norm(q[3] - q[0])
        if not (0.9 < w / max(h, 1) < 3.2) or q[0][1] < 2 and q[2][1] > H - 2:  # 화면 비율·전체 화면 아님
            continue
        out.append(q)
    return sorted(out, key=lambda q: q[:, 0].mean())


def composite(img, quads, kinds, blur=1.2):
    """휘도 키 합성: 원래 흰 화면 픽셀에만 내용, 앞을 가리는 머리·손은 그대로. LCD 질감 포함."""
    base = np.asarray(img.convert("RGB")).astype(float); H, W, _ = base.shape; out = base.copy()
    for q, kind in zip(quads, kinds):
        src = content(kind)
        if kind not in ("sleep", "off"):  # LCD: 백라이트 비네트·약간 푸른 기·주사선
            s = np.asarray(src).astype(float)
            yy, xx = np.mgrid[0:SH, 0:SW]; vig = 1 - 0.12 * (((xx - SW / 2) / (SW / 2)) ** 2 + ((yy - SH / 2) / (SH / 2)) ** 2)
            s = s * vig[..., None] * 0.92; s[..., 2] *= 1.04; s[::3] *= 0.97
            src = Image.fromarray(s.clip(0, 255).astype("uint8"))
        M = cv2.getPerspectiveTransform(np.float32([[0, 0], [SW, 0], [SW, SH], [0, SH]]), np.float32(q))
        warped = cv2.warpPerspective(np.asarray(src), M, (W, H), flags=cv2.INTER_AREA).astype(float)
        poly = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(poly, q.astype(np.int32), 1)
        lum = base.mean(2); key = np.clip((lum - 140) / 60, 0, 1) * poly  # 흰 화면만
        key = cv2.GaussianBlur(key, (0, 0), 1.2)
        if blur:
            warped = cv2.GaussianBlur(warped, (0, 0), blur)
        # 원래 화면 밝기(심도·노출)를 반영: 원래가 회색이면 내용도 어둡게
        gain = np.clip(lum / 235.0, 0.55, 1.0)[..., None]
        out = out * (1 - key[..., None]) + warped * gain * key[..., None]
        # 화면 빛 번짐(베젤 블룸, 아주 약하게)
    return Image.fromarray(out.clip(0, 255).astype("uint8"))


def plan_for(sc):
    if sc["id"] in PLAN:
        return PLAN[sc["id"]]
    return DEFAULT_BY_LOC.get(next((k for k in DEFAULT_BY_LOC if any(k.lower().replace("_", "-") in r for r in sc.get("refs", []))), ""), WORK3)


def lcd(src, kind):
    if kind in ("sleep", "off"):
        return src
    s = np.asarray(src).astype(float)
    yy, xx = np.mgrid[0:SH, 0:SW]; vig = 1 - 0.12 * (((xx - SW / 2) / (SW / 2)) ** 2 + ((yy - SH / 2) / (SH / 2)) ** 2)
    s = s * vig[..., None] * 0.92; s[..., 2] *= 1.04; s[::3] *= 0.97
    return Image.fromarray(s.clip(0, 255).astype("uint8"))


def apply_plan(img, entries, blur=1.0):
    """screens.json 항목 합성. key = 화면 원래 색(흰·파랑 무지)에 가까운 픽셀만 교체(앞 사람은 유지),
    replace = 어두운 백라이트 화면 전체 교체(occ 타원 = 앞 머리·몸은 유지). 원래 화면 밝기로 노출을 맞춘다."""
    base = np.asarray(img.convert("RGB")).astype(float); H, W, _ = base.shape; out = base.copy()
    for e in entries:
        q = np.float32(e["q"]); kind = e["kind"]
        src = np.asarray(lcd(content(kind), kind))
        M = cv2.getPerspectiveTransform(np.float32([[0, 0], [SW, 0], [SW, SH], [0, SH]]), q)
        warped = cv2.warpPerspective(src, M, (W, H), flags=cv2.INTER_AREA).astype(float)
        if blur:
            warped = cv2.GaussianBlur(warped, (0, 0), blur)
        poly = np.zeros((H, W), np.float32); cv2.fillConvexPoly(poly, q.astype(np.int32), 1.0)
        if e.get("grow"):  # 화면 가장자리 흰 테까지 덮기
            poly = cv2.dilate(poly, np.ones((2 * e["grow"] + 1,) * 2, np.uint8))
        if e["mode"] == "key":
            inside = base[poly > 0]; med = np.median(inside, axis=0)
            dist = np.linalg.norm(base - med, axis=2); key = np.clip(1 - (dist - 40) / 45, 0, 1) * poly
            key = cv2.dilate(key, np.ones((3, 3), np.uint8))  # 화면 가장자리 흰 테 제거
            gain = np.clip(base.mean(2) / max(med.mean(), 1), 0.6, 1.05)[..., None]
            lvl = 1.0
        else:
            key = poly.copy(); gain = 1.0; lvl = 0.80  # 어두운 방 화면은 조금 낮게
        for cx, cy, rx, ry in e.get("occ", []):
            m = np.ones((H, W), np.float32); cv2.ellipse(m, (int(cx), int(cy)), (int(rx), int(ry)), 0, 0, 360, 0.0, -1)
            key *= cv2.GaussianBlur(m, (0, 0), 6)
        if e.get("occpoly"):  # 앞 인물 윤곽(머리·어깨)을 다각형으로
            m = np.ones((H, W), np.float32); cv2.fillPoly(m, [np.int32(e["occpoly"])], 0.0)
            key *= cv2.GaussianBlur(m, (0, 0), 2)
        key = cv2.GaussianBlur(key, (0, 0), 1.0)
        out = out * (1 - key[..., None]) + warped * gain * lvl * key[..., None]
    return Image.fromarray(out.clip(0, 255).astype("uint8"))


def preview(only=None):
    P = json.load(open(os.path.join(ROOT, "productions", "hikikomori-ja", "screens.json"), encoding="utf-8"))
    od = os.path.join(ROOT, "assets", "preview", "hikikomori-screens"); os.makedirs(od, exist_ok=True)
    for sid, ents in P.items():
        if only and sid not in only:
            continue
        img = Image.open(os.path.join(ROOT, "assets", "portraits", "hikikomori-keyframes", sid + "-1.png")).convert("RGB")
        apply_plan(img, ents).save(os.path.join(od, sid + ".png"))
    return list(P)


def preview_old(only=None):
    sb = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "hikikomori.json"), encoding="utf-8"))["scenes"]
    od = os.path.join(ROOT, "assets", "preview", "hikikomori-screens"); os.makedirs(od, exist_ok=True)
    done = []
    for sc in sb:
        if not sc.get("keyframe") or (only and sc["id"] not in only) or sc["id"] in SKIP:
            continue
        img = Image.open(os.path.join(ROOT, sc["keyframe"])).convert("RGB")
        qs = detect(img)
        if not qs:
            continue
        kinds = plan_for(sc)
        kinds = (kinds * 3)[:len(qs)] if len(qs) > len(kinds) else (kinds[:len(qs)] if len(qs) < 3 else kinds)
        if len(qs) == 1 and sc["id"] not in PLAN:
            kinds = [kinds[len(kinds) // 2]]
        composite(img, qs, kinds).save(os.path.join(od, sc["id"] + ".png"))
        done.append((sc["id"], len(qs), kinds))
    for d in done:
        print(d)
    return done


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        preview(set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None)
