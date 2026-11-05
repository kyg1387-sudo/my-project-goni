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
    d = ImageDraw.Draw(im)
    for cx in (14, 178):  # 제복 경찰 두 명 = 화면 양 가장자리에 반쯤 걸림(현관등 밖이라 얼굴은 그늘)
        d.polygon([(cx - 30, H), (cx - 24, 72), (cx + 24, 72), (cx + 30, H)], fill=(24, 30, 54))
        d.ellipse([cx - 12, 44, cx + 12, 76], fill=(74, 62, 56))
        d.polygon([(cx - 15, 50), (cx - 12, 33), (cx + 12, 33), (cx + 15, 50)], fill=(18, 22, 40))
        d.rectangle([cx - 15, 47, cx + 15, 51], fill=(10, 12, 22)); d.ellipse([cx - 2, 36, cx + 2, 41], fill=(150, 130, 70))
    im = Image.fromarray(cv2.GaussianBlur(np.asarray(im).astype(np.float32), (0, 0), 1.2).astype("uint8"))  # 뒤 인물은 초점 밖
    im.paste(m2, (96 - m2.width // 2, H - 100 + 8), a2)
    a = np.asarray(im).astype(float)
    edge = np.zeros((H, W)); edge[:, :40] = 1; edge[:, -40:] = 1
    a = a * (1 - edge[..., None]) + cv2.GaussianBlur(a, (0, 0), 1.0) * edge[..., None]
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


def _status(d, W, t, dark=False):
    c = (245, 245, 245) if dark else (20, 20, 24)
    d.text((70, 62), t, font=F(GB, 40), fill=c, anchor="lm")
    d.rounded_rectangle((W - 150, 48, W - 82, 78), 8, outline=c, width=3); d.rectangle((W - 146, 52, W - 104, 74), fill=c)  # 배터리
    for i in range(4):
        d.rectangle((W - 260 + i * 16, 74 - 8 - i * 6, W - 250 + i * 16, 74), fill=c)  # 안테나


def chat_shota():
    """S08h — 由紀子 휴대폰: 翔太가 매일 밤 보낸 같은 동영상(썸네일 = 극 중 가짜 비디오레터 H0a 화면), 날짜별."""
    W, H = 1080, 2340; im = Image.new("RGB", (W, H), (140, 170, 206)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 250), fill=(36, 44, 58)); _status(d, W, "23:14", dark=True)
    d.text((60, 180), "＜", font=F(G, 52), fill=(240, 240, 240), anchor="lm"); d.text((W // 2, 180), "翔太", font=F(GB, 52), fill=(245, 245, 245), anchor="mm")
    th = Image.open(os.path.join(OUT, "H0a-1.png")).convert("RGB"); th = th.crop((180, 0, 1164, 768)).resize((560, 437), Image.LANCZOS)
    face = Image.open(os.path.join(REF, "shota-front.png")).convert("RGB"); fs = min(face.size); face = face.crop((0, 0, fs, fs)).resize((96, 96))
    mask = Image.new("L", (96, 96), 0); ImageDraw.Draw(mask).ellipse((0, 0, 95, 95), fill=255)
    y = 300
    for date, tm in (("8月25日(火)", "22:58"), ("9月2日(水)", "23:06"), ("9月10日(木)", "22:41")):
        d.rounded_rectangle((W // 2 - 150, y, W // 2 + 150, y + 56), 28, fill=(118, 146, 182)); d.text((W // 2, y + 28), date, font=F(G, 32), fill=(255, 255, 255), anchor="mm")
        y += 100; im.paste(face, (36, y), mask)
        im.paste(th, (156, y)); d.rounded_rectangle((156, y, 716, y + 437), 26, outline=(140, 170, 206), width=10)
        cx, cy = 436, y + 218; d.ellipse((cx - 60, cy - 60, cx + 60, cy + 60), fill=(0, 0, 0)); d.polygon([(cx - 20, cy - 34), (cx - 20, cy + 34), (cx + 38, cy)], fill=(255, 255, 255))
        d.rounded_rectangle((590, y + 380, 700, y + 424), 12, fill=(0, 0, 0)); d.text((645, y + 402), "2:14", font=F(G, 30), fill=(255, 255, 255), anchor="mm")
        d.text((736, y + 420), tm, font=F(G, 28), fill=(70, 86, 110), anchor="ld"); y += 520
    d.rectangle((0, H - 150, W, H), fill=(248, 248, 250)); d.rounded_rectangle((150, H - 120, W - 150, H - 40), 40, fill=(236, 237, 240))
    return im


def voice_mom():
    """S13a — 어머니 휴대폰: 由紀子와의 대화, 6/29 통원 확인 → 6/30 어머니가 보낸 음성 메시지 1개(0:12). 대화 상대 이름은 「由紀子」
    (「ゆっこ」 호칭은 직후 음성 L56에서 처음 드러나야 한다 — NA36 반전 보호)."""
    W, H = 1080, 2340; im = Image.new("RGB", (W, H), (140, 170, 206)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 250), fill=(36, 44, 58)); _status(d, W, "8:12", dark=True)
    d.text((60, 180), "＜", font=F(G, 52), fill=(240, 240, 240), anchor="lm"); d.text((W // 2, 180), "由紀子", font=F(GB, 52), fill=(245, 245, 245), anchor="mm")
    face = Image.open(os.path.join(REF, "yukiko-front.png")).convert("RGB"); fs = min(face.size); face = face.crop((0, 0, fs, fs)).resize((96, 96))
    mask = Image.new("L", (96, 96), 0); ImageDraw.Draw(mask).ellipse((0, 0, 95, 95), fill=255)
    def chip(y, t):
        d.rounded_rectangle((W // 2 - 150, y, W // 2 + 150, y + 56), 28, fill=(118, 146, 182)); d.text((W // 2, y + 28), t, font=F(G, 32), fill=(255, 255, 255), anchor="mm")
    chip(520, "6月29日(月)")
    im.paste(face, (36, 620), mask); d.rounded_rectangle((156, 620, 760, 730), 40, fill=(255, 255, 255)); d.text((196, 675), "明日の病院、10時だからね", font=F(G, 40), fill=(20, 20, 24), anchor="lm")
    d.text((776, 728), "19:02", font=F(G, 28), fill=(70, 86, 110), anchor="ld")
    d.rounded_rectangle((790, 780, 1040, 890), 40, fill=(156, 226, 126)); d.text((915, 835), "はーい", font=F(G, 40), fill=(20, 20, 24), anchor="mm")
    d.text((774, 888), "19:05", font=F(G, 28), fill=(70, 86, 110), anchor="rd")
    chip(980, "6月30日(火)")
    y = 1080; d.rounded_rectangle((420, y, 1040, y + 140), 70, fill=(156, 226, 126))
    d.ellipse((450, y + 25, 540, y + 115), fill=(255, 255, 255)); d.polygon([(482, y + 45), (482, y + 95), (522, y + 70)], fill=(70, 150, 70))
    for i in range(22):
        h = 14 + (i * 29 % 46); d.line((570 + i * 16, y + 70 - h // 2, 570 + i * 16, y + 70 + h // 2), fill=(80, 120, 70), width=7)
        d.ellipse((570 + i * 16 - 3, y + 70 - h // 2 - 3, 570 + i * 16 + 3, y + 70 - h // 2 + 3), fill=(80, 120, 70))
    d.text((1010, y + 70), "0:12", font=F(G, 34), fill=(30, 60, 30), anchor="rm")
    d.text((404, y + 138), "21:47", font=F(G, 28), fill=(70, 86, 110), anchor="rd")
    d.rectangle((0, H - 150, W, H), fill=(248, 248, 250)); d.rounded_rectangle((150, H - 120, W - 150, H - 40), 40, fill=(236, 237, 240))
    return im


def report3(title, org):
    """S09i — 개시 결과서(대본: 3장 모두 「該当なし」). 기관명은 실존 기관 대신 일반 명칭."""
    W, H = 1240, 1754; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.text((W // 2, 150), title, font=F(GB, 64), fill=(25, 25, 30), anchor="mm")
    d.text((W - 110, 260), "令和8年9月18日", font=F(G, 34), fill=(40, 40, 44), anchor="ra")
    d.text((110, 340), org, font=F(G, 34), fill=(40, 40, 44))
    d.text((110, 440), "照会対象者　佐伯　佐和子　様", font=F(G, 40), fill=(25, 25, 30))
    d.rectangle((110, 560, W - 110, 1100), outline=(60, 60, 66), width=4)
    d.text((W // 2, 660), "登録されている情報", font=F(G, 40), fill=(60, 60, 66), anchor="mm")
    d.text((W // 2, 880), "該当なし", font=F(GB, 170), fill=(20, 20, 24), anchor="mm")
    for i, t in enumerate(["※ お借入れ・クレジット・保証に関する", "　 登録情報はございません。"]):
        d.text((110, 1200 + i * 60), t, font=F(G, 34), fill=(60, 60, 66))
    return im


def intercom_clean(b):
    """S11a(r6 ECU) — 가짜 라벨 글자·아래로 늘어진 코일선 제거(무지 벽·무지 패널) 후 화면에 현관 카메라 영상."""
    b = inpaint(b, [(548, 345, 576, 357), (660, 422, 696, 434), (560, 450, 576, 463), (600, 483, 700, 497)])
    m = np.zeros(b.shape[:2], np.uint8); cv2.rectangle(m, (530, 566), (608, 760), 255, -1)
    r = cv2.inpaint(b.astype("uint8"), m, 15, cv2.INPAINT_TELEA).astype(float)
    wall = cv2.GaussianBlur(r, (0, 0), 6)  # 벽은 고르게
    mm = cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), 3)[..., None]
    out = b * (1 - mm) + (wall + np.random.default_rng(5).normal(0, 2.2, b.shape)) * mm
    out[538:572, 532:606] = b[538:572, 612:686]  # 코일선이 가린 본체 아래 그림자 = 옆 그림자 복사
    edge = np.zeros(b.shape[:2], np.float32); cv2.rectangle(edge, (528, 536), (610, 576), 1.0, 2)
    edge = cv2.GaussianBlur(edge, (0, 0), 2)[..., None]
    return out * (1 - edge) + cv2.GaussianBlur(out, (0, 0), 2) * edge


def scroll_nembutsu():
    """S08k 불단 족자 — 가짜 붓글씨 대신 실제 「南無阿弥陀仏」(세로, 먹색). 초점 밖이라 크게 흐림."""
    W, H = 300, 900; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf"), 128)
    for i, ch in enumerate("南無阿弥陀仏"):
        d.text((W // 2, 80 + i * 140), ch, font=f, fill=(20, 20, 24), anchor="mm")
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
    elif mode == "neutral":  # 회색 무지 화면 위 손가락(밝기가 비슷함) — 채도 낮은(R≈B) 밝은 픽셀만
        key = np.clip((lum - keep_thr) / 20, 0, 1) * np.clip((24 - (b[..., 0] - b[..., 2])) / 10, 0, 1)
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


def doc_dof(b, art, quad, focus, tol=55, strength=0.9, near=0.7, far=3.2, reach=420, ystretch=1.7):
    """접사 서류 합성(R45): 서류 전체를 원근(quad = 그림 네 모서리, 화면 밖 허용)으로 얹고, 초점(focus) 거리에 따라 흐림을 키운다
    (얕은 심도 — 초점 면의 인영만 선명, 멀어질수록 무름. 세로 거리는 깊이 변화가 커서 ystretch배로 센다)."""
    H, W, _ = b.shape
    wa = warp(art, quad, W, H)
    yy, xx = np.mgrid[0:H, 0:W]; d = np.sqrt((xx - focus[0]) ** 2 + ((yy - focus[1]) * ystretch) ** 2)
    t = np.clip((d - 90) / reach, 0, 1)
    levels = [near, (near + far) / 2, far]; blurred = [cv2.GaussianBlur(wa, (0, 0), s_) for s_ in levels]
    wa = np.where((t < 0.5)[..., None], blurred[0] * (1 - 2 * t[..., None]) + blurred[1] * (2 * t[..., None]),
                  blurred[1] * (2 - 2 * t[..., None]) + blurred[2] * (2 * t[..., None] - 1))
    poly = polymask(quad, W, H, 0)
    med = np.median(b[poly > 0], axis=0); dist = np.linalg.norm(b - med, axis=2)
    key = np.clip(1 - (dist - tol) / 40, 0, 1) * poly
    key = cv2.GaussianBlur(cv2.erode(key, np.ones((3, 3), np.uint8)), (0, 0), 1.0)
    return b * (1 - (1 - wa / 255.0) * strength * key[..., None])


# ---------- 컷별 합성(좌표 = 1344x768 원본) ----------
JOBS = {
    "S02a": lambda b: put_photo(b, portrait(), [(645, 366), (708, 366), (708, 457), (645, 457)]),
    "S04c": lambda b: paper(paper(paper(b, gfx("S04c_loan1"), [(175, 363), (497, 363), (464, 659), (54, 659)]),
                                  gfx("S04c_loan2"), [(520, 363), (836, 363), (867, 659), (480, 659)]),
                            gfx("S04c_loan3"), [(860, 363), (1176, 363), (1294, 659), (898, 659)]),
    # 인영만 있던 종이(R45) → 차용증 전체(위 여백 왼쪽 捨印 = 같은 실인, 제목·貸主·借主 줄)를 종이 모서리·윗변에 맞춰 원근 합성, 초점은 인영
    "S04e": lambda b: doc_dof(inpaint(b, [(452, 402, 724, 500)]), gfx("S04c_loan1"), [(305, 440), (1666, 105), (3179, 666), (1818, 1001)], focus=(590, 428), strength=0.93),
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
    "S08p": lambda b: paper(blank(b, [(543, 383), (806, 379), (805, 620), (544, 627)], inset=3), gfx("S08p_calendar"), [(546, 384), (804, 381), (803, 621), (547, 627)], tol=75, strength=1.0, blur=0.9),
    "S08h": lambda b: lcd(b, chat_shota(), [(527, 264), (663, 243), (768, 501), (634.5, 538)], keep_thr=165, refl=0.10, blur=0.7),
    "S13a": lambda b: lcd(b, voice_mom(), [(796.7, 228.9), (942.2, 260.6), (786.7, 497.8), (660, 457.8)], keep_thr=168, refl=0.08, blur=0.8, mode="neutral"),
    "S09i": lambda b: paper(paper(paper(blank(b, [(578, 205), (780, 205), (780, 226), (578, 226)], inset=0, k=9, sigma=3),
                                              report3("信用情報開示報告書", "指定信用情報機関　開示窓口"), [(150, 181), (467, 181), (398, 553), (0, 551)], tol=60, strength=0.92, blur=0.9),
                                        report3("本人開示結果のお知らせ", "個人信用情報センター"), [(497, 181), (814, 181), (841, 553), (441, 553)], tol=60, strength=0.92, blur=0.9),
                                  report3("登録情報開示報告書", "信用情報機構　開示担当"), [(864, 177), (1187, 177), (1289, 551), (908, 553)], tol=60, strength=0.92, blur=0.9),
    "S09a": lambda b: paper(b, gfx("S09a_form"), [(504, 591), (732, 581), (793, 672), (531, 699)], strength=0.9, blur=1.0, clean=9),
    "S13f": lambda b: put_photo(b, portrait(), [(452, 516), (528, 516), (528, 596), (452, 596)], blur=1.0),  # 탁자 위 작은 액자 = 진짜 어머니 사진(무지 흰 사각형 → 「AIは顔も声も真似できた」 위 진짜 얼굴)
    "S08k": lambda b: put_photo(paper(blank(b, [(600, 165), (700, 165), (700, 330), (600, 330)], inset=2, k=21, sigma=6), scroll_nembutsu(),
                            [(612, 168), (688, 168), (688, 322), (612, 322)], tol=90, strength=0.75, blur=3.2),
                                portrait(), [(570, 404), (750, 404), (750, 620), (570, 620)], blur=2.6),  # 영정 속 엉뚱한 남자 → 어머니(제21장 21① 재발)
    "S11a": lambda b: screen_full(intercom_clean(b), intercom(), [(561, 249), (688, 249), (688, 326), (561, 326)], blur=0.9, bloom=0.18),
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
