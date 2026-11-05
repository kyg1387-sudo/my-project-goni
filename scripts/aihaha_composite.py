#!/usr/bin/env python3
"""『母が遺したビデオレター』 PHASE 4 일본어·화면 합성(제7장 6·제11장 3·제15장 17·제19장 13 — 조립 전, 무료·로컬).
키프레임(assets/portraits/aihaha-keyframes-raw/<id>-1.png, Kill Gate 확정본)의 무지 면에 scripts/aihaha_graphics.py 그래픽을
원근 변형해 얹고 assets/portraits/aihaha-keyframes/<id>-1.png를 덮어쓴다(원본은 raw 폴더에 그대로).
  paper  곱하기 합성 — 종이 색에 가까운 픽셀만(손·펜은 그대로), 램프 그늘이 글자에도 그대로 남는다
  lcd    발광 화면 — LCD 흰색 0.88·푸른 기·백라이트 비네트·유리 반사 18%·가장자리 무름, 밝은 무지 화면 픽셀만 교체(앞의 손 보호)
  dark   꺼져 있던 어두운 화면에 켜진 화면을 얹음(어두운 픽셀만 교체 — 화면 위 엄지·손가락 보호)
동영상이 재생되는 화면(H0b·S04l·S09e 태블릿·TV)은 움직이는 영상이므로 여기서 하지 않고 finalize에서 매 프레임 합성한다.
사용법: python3 scripts/aihaha_composite.py [id,…]   (생략하면 전부)
"""
import os
import sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "assets", "portraits", "aihaha-keyframes-raw")
OUT = os.path.join(ROOT, "assets", "portraits", "aihaha-keyframes")
GFX = os.path.join(ROOT, "assets", "preview", "aihaha-graphics")
REF = os.path.join(ROOT, "assets", "portraits", "aihaha-ref")
G = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
GB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
M = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"


def F(p, s):
    return ImageFont.truetype(p, s)


def gfx(name):
    return Image.open(os.path.join(GFX, name + ".png")).convert("RGB")


# ---------- 추가 그래픽(대본 1:1) ----------
def portrait():
    """영정 사진 = 佐和子 정면(점 1개, 승인 시트) — 흑백이 아닌 옅은 컬러, 흰 매트 안쪽."""
    im = Image.open(os.path.join(REF, "sawako-front.png")).convert("RGB")
    w, h = im.size; s = min(w, h)
    face = im.crop(((w - s) // 2, 0, (w - s) // 2 + s, s)).resize((600, 600), Image.LANCZOS)
    a = np.asarray(face).astype(float); g = a.mean(2, keepdims=True); a = a * 0.75 + g * 0.25  # 오래된 사진처럼 채도 조금
    return Image.fromarray(np.clip(a * 0.96 + 6, 0, 255).astype("uint8")).resize((480, 600))


def seal_macro():
    """S04e — 佐伯 실인 붉은 인영 확대(차용증 그래픽과 같은 도장 모양)."""
    im = Image.new("RGB", (900, 600), (255, 255, 255)); d = ImageDraw.Draw(im)
    cx, cy, r = 450, 300, 230
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(196, 34, 40), width=22)
    d.text((cx, cy - 92), "佐", font=F(M, 190), fill=(196, 34, 40), anchor="mm")
    d.text((cx, cy + 96), "伯", font=F(M, 190), fill=(196, 34, 40), anchor="mm")
    a = np.asarray(im).astype(float)
    rng = np.random.default_rng(3); n = rng.random(a.shape[:2])  # 인주가 덜 묻은 자국
    red = (a[..., 1] < 200)
    a[red & (n < 0.10)] = 255
    return Image.fromarray(cv2.GaussianBlur(a.astype("uint8"), (0, 0), 1.2))


def stamp_box():
    """S06b — 수입인지 붙이는 자리(점선 테두리 + 収入印紙), 비어 있음."""
    im = Image.new("RGB", (400, 460), (255, 255, 255)); d = ImageDraw.Draw(im)
    for i in range(0, 400, 22):
        d.line([(30 + i, 30), (min(30 + i + 12, 370), 30)], fill=(70, 70, 70), width=4)
        d.line([(30 + i, 430), (min(30 + i + 12, 370), 430)], fill=(70, 70, 70), width=4)
    for j in range(0, 400, 22):
        d.line([(30, 30 + j), (30, min(30 + j + 12, 430))], fill=(70, 70, 70), width=4)
        d.line([(370, 30 + j), (370, min(30 + j + 12, 430))], fill=(70, 70, 70), width=4)
    d.text((200, 230), "収入\n印紙", font=F(M, 86), fill=(90, 90, 90), anchor="mm", align="center", spacing=18)
    return im


def app_screen():
    """S06e — 신용정보 개시 신청 화면(인터넷 개시, 본인 확인 입력 단계)."""
    W, H = 1600, 1000; im = Image.new("RGB", (W, H), (244, 246, 250)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 110], fill=(22, 70, 140)); d.text((60, 55), "信用情報の開示申込", font=F(GB, 54), fill="white", anchor="lm")
    d.text((80, 190), "STEP 2 / 3　ご本人様情報の入力", font=F(GB, 46), fill=(22, 70, 140))
    rows = [("氏名", "佐伯　佐和子"), ("生年月日", "昭和二十六年　十月　二日"), ("開示の種類", "相続人による開示（故人の信用情報）"), ("申込者", "佐伯　由紀子（長女）")]
    for i, (k, v) in enumerate(rows):
        y = 300 + i * 140
        d.text((100, y), k, font=F(G, 42), fill=(60, 60, 70))
        d.rectangle([460, y - 20, 1480, y + 70], outline=(150, 160, 180), width=3, fill="white")
        d.text((490, y + 25), v, font=F(G, 44), fill=(20, 20, 30), anchor="lm")
    d.rounded_rectangle([1100, 880, 1480, 965], radius=14, fill=(22, 70, 140)); d.text((1290, 922), "次へ進む", font=F(GB, 44), fill="white", anchor="mm")
    return im


def carecam():
    """S06i — 돌봄 카메라 앱 재생 화면: S03a 복도 영상(흑백) 정지 + 07/03 23:41 + 일시정지 아이콘."""
    W, H = 1600, 1000; im = Image.new("RGB", (W, H), (18, 18, 20)); d = ImageDraw.Draw(im)
    d.text((60, 50), "見守りカメラ　録画再生", font=F(GB, 46), fill=(230, 230, 230), anchor="lm")
    src = os.path.join(RAW, "S03a-1.png")
    fr = Image.open(src).convert("L").convert("RGB").resize((1360, 765)) if os.path.exists(src) else Image.new("RGB", (1360, 765), (60, 60, 60))
    im.paste(fr, (120, 110))
    d.text((150, 140), "2026/07/03 23:41:12", font=F(GB, 40), fill=(255, 255, 255))
    d.text((1300, 140), "廊下", font=F(GB, 40), fill=(255, 255, 255))
    d.rectangle([120, 900, 1480, 914], fill=(90, 90, 95)); d.rectangle([120, 900, 1010, 914], fill=(230, 60, 60))
    d.ellipse([985, 890, 1035, 925], fill=(255, 255, 255))
    d.rectangle([760, 440, 790, 540], fill=(255, 255, 255)); d.rectangle([815, 440, 845, 540], fill=(255, 255, 255))  # 일시정지
    d.text((120, 950), "23:41:12", font=F(G, 34), fill=(200, 200, 200), anchor="lm"); d.text((1480, 950), "23:59:59", font=F(G, 34), fill=(200, 200, 200), anchor="rm")
    return im


def intercom():
    """S11a — 인터폰 카메라 영상: 밤 현관 앞 宮下(본편 시트 얼굴·남색 정장) + 양 가장자리 제복 경찰 2명.
    실제 인터폰처럼 저해상도로 그린 뒤 어안 왜곡·탈색·노이즈를 준다(화면 속 글자 없음)."""
    W, H = 192, 108
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    bg = np.zeros((H, W, 3)); base = np.array([34, 36, 40.0])
    glow = np.exp(-(((xx - 96) / 70) ** 2 + ((yy + 10) / 45) ** 2))  # 위쪽 현관등(따뜻한 빛)
    bg[:] = base; bg += glow[..., None] * np.array([70, 62, 48.0])
    bg[:, 150:156] += 18  # 문틀
    im = Image.fromarray(np.clip(bg, 0, 255).astype("uint8"))
    m = Image.open(os.path.join(REF, "miyashita-front.png")).convert("RGB")
    ma = np.asarray(m).astype(float); hsv = cv2.cvtColor(ma.astype("uint8"), cv2.COLOR_RGB2HSV)
    fg = ~((ma.mean(2) > 205) & (hsv[..., 1] < 30))  # 흰 배경만 뺀다
    alpha = Image.fromarray((cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 1.5) * 255).astype("uint8"))
    sc = 100 / m.height; m2 = m.resize((int(m.width * sc), 100), Image.LANCZOS); a2 = alpha.resize(m2.size, Image.LANCZOS)
    im.paste(m2, (96 - m2.width // 2, H - 100 + 8), a2)
    d = ImageDraw.Draw(im)
    for cx in (14, 178):  # 제복 경찰 = 가장자리에서 반쯤 잘린 모자·어깨(초점 밖)
        d.polygon([(cx - 26, H), (cx - 22, 70), (cx + 22, 70), (cx + 26, H)], fill=(22, 28, 52))
        d.ellipse([cx - 13, 40, cx + 13, 74], fill=(122, 98, 84))
        d.polygon([(cx - 16, 46), (cx - 13, 30), (cx + 13, 30), (cx + 16, 46)], fill=(18, 22, 40))
        d.rectangle([cx - 16, 44, cx + 16, 48], fill=(10, 12, 22)); d.ellipse([cx - 2, 33, cx + 2, 38], fill=(150, 130, 70))
    a = np.asarray(im).astype(float)
    edge = np.zeros((H, W)); edge[:, :40] = 1; edge[:, -40:] = 1
    a = a * (1 - edge[..., None]) + cv2.GaussianBlur(a, (0, 0), 1.8) * edge[..., None]
    k = 0.32; nx = (xx - W / 2) / (W / 2); ny = (yy - H / 2) / (W / 2); r2 = nx ** 2 + ny ** 2  # 어안(배럴)
    mx = (W / 2 + nx * (1 - k * r2) * (W / 2)).astype(np.float32); my = (H / 2 + ny * (1 - k * r2) * (W / 2)).astype(np.float32)
    a = cv2.remap(a.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderValue=(10, 10, 12))
    g = a.mean(2, keepdims=True); a = a * 0.45 + g * 0.55 + np.array([-4, 4, 8.0])  # 탈색·푸른 기(감시 카메라)
    a = a + np.random.default_rng(7).normal(0, 5, a.shape)
    a = cv2.GaussianBlur(a, (0, 0), 0.5)
    vig = 1 - 0.35 * r2; a = a * vig[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8")).resize((384, 216), Image.BILINEAR)


def law_left():
    """S08o 왼쪽 면 — 앞 조문(第九百十四条 이전 면). 작게 보이는 질감이지만 가짜 글자 대신 실제 조문 모양."""
    W, H = 1200, 700; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    rows = [("（相続の放棄の方式）", 40), ("第九百三十八条　相続の放棄をしようとする者は、", 44), ("その旨を家庭裁判所に申述しなければならない。", 44), ("", 0),
            ("（相続の放棄の効力）", 40), ("第九百三十九条　相続の放棄をした者は、その相続に", 44), ("関しては、初めから相続人とならなかったものとみなす。", 44)]
    for i, (t, sz) in enumerate(rows):
        if t:
            d.text((40, 40 + i * 92), t, font=F(M, sz), fill=(40, 38, 36))
    return im


def tablet_law():
    """S08o 태블릿 — 법령 검색 결과처럼 보이는 화면(상표 없음): 남색 머리띠·조문 제목·본문·형광 표시."""
    W, H = 800, 600; im = Image.new("RGB", (W, H), (250, 250, 248)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 70], fill=(30, 50, 90)); d.text((30, 18), "民法", font=F(GB, 34), fill=(255, 255, 255))
    d.text((30, 110), "第九百十五条（相続の承認又は放棄をすべき期間）", font=F(GB, 30), fill=(20, 20, 24))
    d.rectangle([30, 196, 700, 236], fill=(255, 236, 120))
    for i, t in enumerate(["相続人は、自己のために相続の開始があったことを", "知った時から三箇月以内に、相続について、単純若しくは", "限定の承認又は放棄をしなければならない。"]):
        d.text((30, 160 + i * 42 if i == 0 else 200 + (i - 1) * 42), t, font=F(G, 26), fill=(40, 40, 44))
    for y in range(340, 560, 40):
        d.line([(30, y), (W - 30 - (y % 120), y)], fill=(205, 205, 210), width=10)
    return im


# ---------- 합성 방식 ----------
def warp(art, quad, W, H, border=(255, 255, 255)):
    a = np.asarray(art.convert("RGB")).astype(float); h, w, _ = a.shape
    Mx = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    return cv2.warpPerspective(a, Mx, (W, H), flags=cv2.INTER_AREA, borderValue=border)


def polymask(quad, W, H, feather=1.2):
    m = np.zeros((H, W), np.float32); cv2.fillConvexPoly(m, np.int32(np.round(quad)), 1.0)
    return cv2.GaussianBlur(m, (0, 0), feather) if feather else m


def paper(b, art, quad, tol=55, strength=0.9, blur=0.7, clean=0):
    H, W, _ = b.shape
    if clean:  # 무지 면에 생긴 가짜 글자·숫자(가는 어두운 획)를 먼저 지운다 — 밝기 닫힘 연산(손처럼 큰 면은 거의 그대로)
        poly0 = cv2.dilate(polymask(quad, W, H, 0), np.ones((5, 5), np.uint8))
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (clean, clean))
        closed = cv2.morphologyEx(b.astype(np.float32), cv2.MORPH_CLOSE, k)
        diff = (closed - b).mean(2)
        thin = (diff > 18).astype(np.float32) * poly0  # 획 부분만 교체
        thin = cv2.GaussianBlur(thin, (0, 0), 0.8)[..., None]
        b = b * (1 - thin) + closed * thin
    wa = warp(art, quad, W, H)
    if blur:
        wa = cv2.GaussianBlur(wa, (0, 0), blur)  # 실제 렌즈 해상도에 맞춤(너무 날카로우면 붙인 티)
    poly = polymask(quad, W, H, 0)
    med = np.median(b[poly > 0], axis=0); dist = np.linalg.norm(b - med, axis=2)
    key = np.clip(1 - (dist - tol) / 40, 0, 1) * poly
    key = cv2.GaussianBlur(cv2.erode(key, np.ones((3, 3), np.uint8)), (0, 0), 1.0)
    return b * (1 - (1 - wa / 255.0) * strength * key[..., None])


def lcd(b, art, quad, keep_thr=150, refl=0.18, blur=0.8, mode="bright"):
    H, W, _ = b.shape
    a = np.asarray(art.convert("RGB")).astype(float)
    a = a * 0.88 + np.array([4, 8, 18])  # LCD 흰색은 순백이 아니다 — 약간 푸른 기
    h, w, _ = a.shape; yy, xx = np.mgrid[0:h, 0:w]
    vig = 1 - 0.10 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)  # 백라이트 비네트
    a = a * vig[..., None]
    a[::3] *= 0.97  # 아주 옅은 주사선
    wa = warp(Image.fromarray(np.clip(a, 0, 255).astype("uint8")), quad, W, H, border=(0, 0, 0))
    if blur:
        wa = cv2.GaussianBlur(wa, (0, 0), blur)
    poly = polymask(quad, W, H, 1.0)
    lum = b.mean(2)
    if mode == "bright":  # 밝은 무지 화면만 교체 — 화면 앞 손가락(어두움)은 보호
        key = np.clip((lum - keep_thr) / 30, 0, 1)
    else:  # 꺼진 어두운 화면 — 어두운 픽셀만 교체(밝은 피부 손가락 보호)
        key = np.clip((keep_thr - lum) / 30, 0, 1)
    key = cv2.GaussianBlur(key.astype(np.float32), (0, 0), 1.0) * poly
    out = wa * (1 - refl) + b * refl  # 유리 반사
    return b * (1 - key[..., None]) + out * key[..., None]


def put_photo(b, art, quad, blur=0.8):
    """액자 속 사진 — 완전히 교체 + 장면 조명(액자 위치의 평균 밝기·색)에 맞춤 + 유리 반사 10%."""
    H, W, _ = b.shape
    wa = warp(art, quad, W, H, border=(0, 0, 0))
    poly = polymask(quad, W, H, 1.0)
    reg = b[poly > 0.5]
    tone = reg.mean(0) / 255.0
    wa = wa * (0.55 + 0.45 * tone / tone.max())  # 텅스텐 조명 색을 사진에 입힘
    wa = cv2.GaussianBlur(wa, (0, 0), blur)
    out = wa * 0.9 + b * 0.1
    return b * (1 - poly[..., None]) + out * poly[..., None]


def blank(b, quad, inset=4, k=21, sigma=9):
    """무지 면을 통째로 다시 칠한다(가짜 숫자·글자가 굵어 닫힘 연산으로 안 지워질 때) — 큰 닫힘 + 마스크 정규화 흐림 + 그레인."""
    H, W, _ = b.shape
    m = cv2.erode(polymask(quad, W, H, 0), np.ones((inset * 2 + 1, inset * 2 + 1), np.uint8))
    closed = cv2.morphologyEx(b.astype(np.float32), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    num = cv2.GaussianBlur(closed * m[..., None], (0, 0), sigma); den = cv2.GaussianBlur(m, (0, 0), sigma)[..., None]
    est = num / np.maximum(den, 1e-3) + np.random.default_rng(3).normal(0, 1.6, b.shape)
    mm = cv2.GaussianBlur(m, (0, 0), 1.0)[..., None]
    return b * (1 - mm) + est * mm


def screen_full(b, art, quad, blur=0.9, bloom=0.25):
    """작은 켜진 화면 — 화면 전체 교체 + 가장자리 빛 번짐(인터폰처럼 어두운 화면 위)."""
    H, W, _ = b.shape
    wa = warp(art, quad, W, H, border=(0, 0, 0)); wa = cv2.GaussianBlur(wa, (0, 0), blur)
    poly = polymask(quad, W, H, 0.8)
    out = b * (1 - poly[..., None]) + wa * poly[..., None]
    glow = cv2.GaussianBlur(wa * poly[..., None], (0, 0), 6) * bloom
    return out + glow


def punch(b, cx, cy, z):
    """편집 확대(저장 단계) — 같은 해상도로 다시 맞춘다(ECU 설계인데 원본이 원경일 때)."""
    H, W, _ = b.shape; w, h = W / z, H / z
    x0 = int(round(min(max(cx - w / 2, 0), W - w))); y0 = int(round(min(max(cy - h / 2, 0), H - h)))
    return cv2.resize(b[y0:y0 + int(h), x0:x0 + int(w)].astype(np.float32), (W, H), interpolation=cv2.INTER_LANCZOS4).astype(float)


def inpaint(b, boxes):
    m = np.zeros(b.shape[:2], np.uint8)
    for x0, y0, x1, y1 in boxes:
        cv2.ellipse(m, ((x0 + x1) // 2, (y0 + y1) // 2), ((x1 - x0) // 2, (y1 - y0) // 2), 0, 0, 360, 255, -1)
    r = cv2.inpaint(b.astype("uint8"), m, 9, cv2.INPAINT_TELEA).astype(float)
    return r + np.random.default_rng(1).normal(0, 2.0, b.shape) * (m[..., None] > 0)


def flip180(im):
    return im.rotate(180)


# ---------- 컷별 합성(좌표 = 1344x768 원본) ----------
JOBS = {
    "S02a": lambda b: put_photo(b, portrait(), [(645, 366), (708, 366), (708, 457), (645, 457)]),
    "S04c": lambda b: paper(paper(paper(b, gfx("S04c_loan1"), [(175, 363), (497, 363), (464, 659), (54, 659)]),
                                  gfx("S04c_loan2"), [(520, 363), (836, 363), (867, 659), (480, 659)]),
                            gfx("S04c_loan3"), [(860, 363), (1176, 363), (1294, 659), (898, 659)]),
    "S04e": lambda b: paper(inpaint(b, [(455, 405, 720, 495)]), seal_macro(), [(455, 398), (725, 380), (735, 488), (462, 505)], strength=0.95, blur=1.4),
    "S06a": lambda b: paper(b, ImageOps.mirror(gfx("S04c_loan1")), [(160, 606), (520, 590), (560, 636), (162, 652)], strength=0.22, blur=1.6),
    "S06b": lambda b: paper(b, stamp_box(), [(820, 585), (900, 582), (912, 640), (828, 645)], strength=0.85, blur=0.9),
    "S06e": lambda b: lcd(b, app_screen(), [(1051, 309), (1257, 289), (1125, 726), (1001, 659)]),
    "S06f": lambda b: lcd(b, gfx("S06f_cic"), [(743, 431), (1039, 427), (1008, 699), (710, 665)]),
    "S06i": lambda b: lcd(b, carecam(), [(208, 215), (706, 250), (773, 589), (228, 629)], blur=1.4),
    "S08i": lambda b: paper(b, gfx("S08i_form_blank"), [(215, 473), (699, 468), (712, 511), (215, 528)], strength=0.85, blur=1.0, clean=9),
    "S08i2": lambda b: paper(b, flip180(gfx("S08i_form_blank")), [(565, 374), (755, 374), (790, 642), (534, 642)], strength=0.9, clean=11),
    "S08o": lambda b: lcd(paper(paper(blank(blank(b, [(682, 606), (790, 602), (836, 634), (716, 640)], inset=3, k=11, sigma=4),
                                                 [(554, 609), (648, 597), (662, 632), (556, 644)], inset=3, k=11, sigma=4),
                                           gfx("S08o_law").crop((90, 90, 1280, 800)), [(684, 605), (788, 601), (838, 638), (714, 644)], tol=80, strength=0.9, blur=0.8),
                                     law_left(), [(556, 606), (642, 597), (660, 634), (558, 647)], tol=80, strength=0.75, blur=0.8),
                          tablet_law(), [(940.5, 578), (1022, 607.5), (966, 679.5), (888, 642.5)], keep_thr=120, refl=0.12, blur=0.9),
    "S08p": lambda b: paper(blank(b, [(574, 518), (764, 512), (767, 691), (575, 692)]), gfx("S08p_calendar"), [(578, 517), (763, 508), (766, 692), (575, 692)], tol=70, strength=1.0, blur=0.9),
    "S09a": lambda b: paper(b, gfx("S09a_form"), [(504, 591), (732, 581), (793, 672), (531, 699)], strength=0.9, blur=1.0, clean=9),
    "S11a": lambda b: punch(screen_full(b, intercom(), [(558.5, 357.5), (591.5, 357.5), (591.5, 377.5), (558.5, 377.5)], blur=0.5), 575, 390, 1.5),
}


def main(only=None):
    done = []
    for k, fn in JOBS.items():
        if only and k not in only:
            continue
        b = np.asarray(Image.open(os.path.join(RAW, f"{k}-1.png")).convert("RGB")).astype(float)
        out = np.clip(fn(b), 0, 255).astype("uint8")
        Image.fromarray(out).save(os.path.join(OUT, f"{k}-1.png")); done.append(k)
    print("합성:", done)


if __name__ == "__main__":
    main(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
