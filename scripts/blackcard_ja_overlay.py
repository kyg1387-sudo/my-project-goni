#!/usr/bin/env python3
"""『ブラックカード』 소품·화면 일본어 합성(제7장 6·제11장 3·제19장 13 — 조립 전, 무료). hikikomori_ja_overlay.py 구조.
무지 면에 실글꼴 글자를 원근 변형해 곱하기 합성(종이), 발광 화면은 lcd 모드(제15장 17).
결과는 assets/preview/blackcard-screens/<id>.png (build_blackcard_overrides.py가 정지·립싱크 컷 원본으로 씀, i2v 컷은 finalize가 매 프레임).
QUADS(네 꼭짓점, 키프레임 좌표)는 Kill Gate 합격 키프레임을 보고 채운다.
사용법: python3 scripts/blackcard_ja_overlay.py [id,...]"""
import os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KF = os.path.join(ROOT, "assets", "portraits", "blackcard-keyframes")
OUT = os.path.join(ROOT, "assets", "preview", "blackcard-screens")
G = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
M = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf" if os.path.exists("/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf") else G
HAND = os.path.join(ROOT, "assets", "fonts", "KleeOne-SemiBold.ttf")


def F(p, s):
    return ImageFont.truetype(p, s)


# ---------- 아트(글자 면) ----------
def passbook():
    """S03c 통장 마지막 줄 残高 3,218(대본 L016a)."""
    W, H = 1600, 900; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    hd = ["年月日", "摘要", "お支払金額", "お預り金額", "差引残高"]; xs = [40, 330, 700, 1000, 1300]
    for x, h in zip(xs, hd):
        d.text((x, 40), h, font=F(G, 40), fill=(60, 70, 120))
    d.line([(20, 95), (W - 20, 95)], fill=(120, 130, 170), width=3)
    rows = [("26-10-25", "給与　ハスミシヨウジ", "", "312,400", "318,218"), ("26-10-27", "ローン返済", "185,000", "", "133,218"),
            ("26-10-28", "カード", "98,000", "", "35,218"), ("26-10-30", "引出", "32,000", "", "3,218")]
    for i, r in enumerate(rows):
        y = 150 + i * 72
        for x, t in zip(xs, r):
            d.text((x, y), t, font=F(G, 40), fill=(35, 35, 45))
        d.line([(20, y + 50), (W - 20, y + 50)], fill=(200, 205, 220), width=2)
    d.rectangle((1290, 150 + 3 * 72 - 8, 1560, 150 + 3 * 72 + 52), outline=(200, 40, 40), width=4)
    return im


def divorce_form(seal_left=True, seal_right=False, torn=False):
    """離婚届 — 妻 칸(왼쪽)에만 인감(대본 7절 L024), 夫 칸 비움."""
    W, H = 1400, 1000; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.text((W / 2, 90), "離　婚　届", font=F(M, 96), fill=(25, 25, 30), anchor="mm")
    d.text((W / 2, 170), "令和七年十一月　　日　届出", font=F(M, 34), fill=(40, 40, 45), anchor="mm")
    for i, (lab, val) in enumerate([("氏名", "高橋　健二　　　　　高橋　美咲"), ("生年月日", "昭和五十八年　　月　　日　　平成　　年　　月　　日"), ("住所", "東京都　　　区　　　　　　　　　"),
                                    ("離婚の種別", "☑ 協議離婚　□ 調停　□ 審判　□ 裁判"), ("未成年の子", "なし")]):
        y = 250 + i * 80
        d.text((80, y), lab, font=F(M, 34), fill=(40, 40, 45)); d.text((360, y), val, font=F(M, 34), fill=(40, 40, 45))
        d.line([(60, y + 58), (W - 60, y + 58)], fill=(150, 150, 160), width=2)
    d.text((W / 2, 700), "届　出　人　署　名　押　印", font=F(M, 40), fill=(40, 40, 45), anchor="mm")
    for k, (x, lab) in enumerate([(230, "妻"), (880, "夫")]):
        d.rectangle((x, 760, x + 300, 940), outline=(90, 90, 100), width=3)
        d.text((x + 150, 790), lab, font=F(M, 36), fill=(40, 40, 45), anchor="mm")
    d.text((350, 880), "高橋　美咲", font=F(HAND, 48), fill=(30, 30, 60), anchor="mm")
    if seal_left:
        d.ellipse((456, 800, 522, 866), outline=(200, 40, 40), width=5); d.text((489, 833), "高橋", font=F(M, 26), fill=(200, 40, 40), anchor="mm")
    return im


def jirei():
    """S08g·S08l 辞令(희망퇴직) — 柴田 서명·인감 칸."""
    W, H = 1400, 1000; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.text((W / 2, 110), "辞　　令", font=F(M, 110), fill=(25, 25, 30), anchor="mm")
    body = ["柴田　隆　殿", "", "貴殿の希望退職の申出を受理し、", "令和七年十一月末日をもって退職とする。", "退職金は規定どおり支給する。", "",
            "　　　　　　　　　　　　蓮見商事株式会社", "　　　　　　　　　　　　筆頭株主　高橋　健二"]
    for i, t in enumerate(body):
        d.text((120, 250 + i * 66), t, font=F(M, 40), fill=(40, 40, 45))
    d.text((900, 850), "署名　　　　　　　　　印", font=F(M, 36), fill=(40, 40, 45)); d.line([(990, 900), (1240, 900)], fill=(60, 60, 60), width=2)
    return im


def memo():
    """S07d 호텔 메모(손글씨, L050)."""
    im = Image.new("RGB", (900, 600), (252, 250, 244)); d = ImageDraw.Draw(im)
    for i, t in enumerate(["本日十二時、", "最上階のレストラン。", "個室はご用意しております。"]):
        d.text((450, 150 + i * 130), t, font=F(HAND, 70), fill=(30, 30, 50), anchor="mm")
    im = im.rotate(-2, resample=Image.BICUBIC, fillcolor=(252, 250, 244))
    a = cv2.GaussianBlur(np.asarray(im).astype(float), (0, 0), 1.2)
    return Image.fromarray(a.astype("uint8"))


def news():
    """S07g 태블릿 뉴스(L052)."""
    W, H = 1600, 1000; im = Image.new("RGB", (W, H), (248, 248, 250)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 90), fill=(30, 40, 70)); d.text((60, 45), "経済ニュース", font=F(G, 44), fill=(255, 255, 255), anchor="lm")
    d.text((60, 160), "六本木ルクスタワー、所有権移転", font=F(G, 70), fill=(25, 25, 30))
    d.text((60, 260), "11月1日　午前6時12分", font=F(G, 32), fill=(110, 110, 120))
    body = ["六本木の大型複合ビル「六本木ルクスタワー」の所有権が、", "個人へ移転したことが登記情報で明らかになった。", "取得額は非公表。同ビルには蓮見商事の本社が入居している。",
            "関係者によると、取引は二十四時間以内に完了したという。"]
    for i, t in enumerate(body):
        d.text((60, 340 + i * 60), t, font=F(G, 36), fill=(45, 45, 50))
    return im


def phone_hitsuuchi():
    """S06a·S12a 휴대폰 「非通知」 착신 화면(lcd)."""
    W, H = 720, 1500; im = Image.new("RGB", (W, H), (12, 12, 16)); d = ImageDraw.Draw(im)
    d.text((W / 2, 420), "非通知", font=F(G, 110), fill=(240, 240, 240), anchor="mm")
    d.text((W / 2, 560), "着信中…", font=F(G, 54), fill=(170, 170, 180), anchor="mm")
    d.ellipse((120, 1150, 320, 1350), fill=(200, 50, 50)); d.ellipse((400, 1150, 600, 1350), fill=(50, 170, 80))
    return im


def taxi_meter():
    """S04j 미터 2,340円(L031a)."""
    W, H = 900, 400; im = Image.new("RGB", (W, H), (10, 20, 12)); d = ImageDraw.Draw(im)
    d.text((W / 2, H / 2), "¥2,340", font=F(G, 190), fill=(90, 230, 120), anchor="mm")
    return im


def photo_back():
    """S12p 사진 뒷면 — 붉은 스탬프 『候補者 No.7』 + 손글씨 날짜(L102a·b)."""
    W, H = 1200, 800; im = Image.new("RGB", (W, H), (236, 232, 222)); d = ImageDraw.Draw(im)
    st = Image.new("RGBA", (700, 240), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle((6, 6, 694, 234), radius=18, outline=(190, 30, 30, 230), width=9)
    sd.text((350, 120), "候補者　No.7", font=F(M, 96), fill=(190, 30, 30, 225), anchor="mm")
    st = st.rotate(-6, resample=Image.BICUBIC, expand=True)
    a = np.asarray(st).astype(float); a[..., 3] *= (0.75 + 0.25 * np.random.default_rng(7).random(a.shape[:2]))  # 스탬프 번짐
    st = Image.fromarray(a.astype("uint8")); im.paste(st, (240, 200), st)
    d.text((W / 2, 600), "令和七年十一月一日", font=F(HAND, 60), fill=(40, 40, 60), anchor="mm")
    return im


def clock(txt="23:59"):
    """S12r·S12u 대시보드 시계(lcd)."""
    W, H = 800, 300; im = Image.new("RGB", (W, H), (6, 8, 14)); d = ImageDraw.Draw(im)
    d.text((W / 2, H / 2), txt, font=F(G, 200), fill=(200, 215, 235), anchor="mm")
    return im


def titles_folder():
    """S10k 협의서·청구서 표제."""
    W, H = 1200, 900; im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.text((W / 2, 140), "慰謝料請求書", font=F(M, 90), fill=(25, 25, 30), anchor="mm")
    for i, t in enumerate(["請求金額　金三千万円", "請求理由　不貞行為（相手方：柴田　隆）", "", "高橋　健二　代理人　弁護士"]):
        d.text((120, 300 + i * 80), t, font=F(M, 40), fill=(40, 40, 45))
    d.text((W / 2, 720), "財産分与協議書（分与額　零円）", font=F(M, 56), fill=(25, 25, 30), anchor="mm")
    return im


ART = {"S03c": passbook, "S03h": divorce_form, "S03i": divorce_form, "S10f": divorce_form, "S08g": jirei, "S08l": jirei, "S07d": memo,
       "S07g": news, "S06a": phone_hitsuuchi, "S12a": phone_hitsuuchi, "S04j": taxi_meter, "S12p": photo_back, "S12r": clock,
       "S12u": clock, "S10k": titles_folder}
LCD = {"S07g", "S06a", "S12a", "S04j", "S12r", "S12u"}
REPLACE = {"S03i", "S12p", "S03c"}  # 생성 면에 인쇄 글자가 남는 컷 — 곱하기 대신 종이 면을 통째로 덮고 원본 조명만 남긴다(r4 2회 실증)


def put_replace(base, art, quad, paper=(246, 244, 238)):
    b = np.asarray(base.convert("RGB")).astype(float); H, W, _ = b.shape
    a = np.asarray(art.convert("RGB")).astype(float); h, w, _ = a.shape
    Mx = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    wa = cv2.warpPerspective(a, Mx, (W, H), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
    poly = np.zeros((H, W), np.float32); cv2.fillConvexPoly(poly, np.int32(quad), 1.0)
    poly = cv2.erode(poly, np.ones((3, 3), np.uint8)); poly = cv2.GaussianBlur(poly, (0, 0), 1.0)
    lum = cv2.GaussianBlur(b.mean(2), (0, 0), 9)  # 원본 종이의 조명 분포(글자는 흐려 사라짐)
    ref = np.median(lum[poly > 0.5]) if (poly > 0.5).any() else 200.0
    shade = np.clip(lum / max(ref, 1), 0.55, 1.15)[..., None]
    out = b * (1 - poly[..., None]) + (wa * shade) * poly[..., None]
    return Image.fromarray(out.clip(0, 255).astype("uint8"))
QUADS = {"S03i": [[424, 466], [846, 366], [891, 560], [470, 660]], "S07d": [[537, 287], [720, 201], [777, 322], [593, 408]], "S08g": [[667, 379], [1083, 331], [1114, 602], [699, 650]], "S08l": [[400, 488], [973, 418], [1007, 700], [434, 769]], "S10b": [[70, 342], [627, 424], [585, 712], [28, 631]], "S10l": [[354, 500], [975, 377], [1009, 547], [388, 669]], "S12o": [[661, 277], [970, 255], [997, 624], [688, 646]], "S12p": [[533, 233], [785, 135], [900, 430], [649, 528]], "S03c": [[403, 524], [887, 430], [981, 564], [524, 679]], "S10f": [[793, 398], [1095, 390], [1024, 860], [706, 806]], "S10k": [[645, 363], [874, 336], [968, 470], [726, 511]], "S04j": [[517, 433], [648, 430], [649, 513], [519, 516]], "S06a": [[679, 47], [867, 60], [827, 417], [645, 403]], "S07g": [[974, 618], [1418, 632], [1344, 880], [927, 833]], "S09b": [[352, 477], [460, 470], [464, 782], [356, 786]], "S12a": [[672, 437], [759, 473], [665, 629], [581, 591]], "S12r": [[601, 540], [755, 540], [755, 632], [601, 632]], "S12u": [[612, 390], [793, 390], [793, 464], [612, 464]]}  # 키프레임(1344x768) 좌표, 자동 검출 8 + 격자 수동 10 (2026-11-02). S03h는 서류가 화면 밖이라 합성 없음


def put(base, art, quad, tol=55, strength=1.0, satkey=True):
    b = np.asarray(base.convert("RGB")).astype(float); H, W, _ = b.shape
    a = np.asarray(art.convert("RGB")).astype(float); h, w, _ = a.shape
    Mx = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    wa = cv2.warpPerspective(a, Mx, (W, H), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
    poly = np.zeros((H, W), np.float32); cv2.fillConvexPoly(poly, np.int32(quad), 1.0)
    med = np.median(b[poly > 0], axis=0); dist = np.linalg.norm(b - med, axis=2)
    key = np.clip(1 - (dist - tol) / 40, 0, 1) * poly
    hsv = cv2.cvtColor(b.astype("uint8"), cv2.COLOR_RGB2HSV).astype(float)
    if satkey:
        key *= np.clip((125 - hsv[..., 1]) / 30, 0, 1)
    key = cv2.erode(key, np.ones((5, 5), np.uint8)); key = cv2.GaussianBlur(key, (0, 0), 1.0)
    mult = 1 - (1 - wa / 255.0) * strength * key[..., None]
    return Image.fromarray((b * mult).clip(0, 255).astype("uint8"))


def put_lcd(base, art, quad, glow=0.9):
    """발광 화면: 원근 변형한 화면을 화면 영역(어두운 무지)에 덮고, 배경 밝기 비네트·유리 반사를 섞는다(제15장 17)."""
    b = np.asarray(base.convert("RGB")).astype(float); H, W, _ = b.shape
    a = np.asarray(art.convert("RGB")).astype(float); h, w, _ = a.shape
    Mx = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    wa = cv2.warpPerspective(a, Mx, (W, H), flags=cv2.INTER_AREA)
    poly = np.zeros((H, W), np.float32); cv2.fillConvexPoly(poly, np.int32(quad), 1.0)
    poly = cv2.erode(poly, np.ones((3, 3), np.uint8)); poly = cv2.GaussianBlur(poly, (0, 0), 1.2)
    lum = cv2.GaussianBlur(b.mean(2), (0, 0), 25) / 255.0
    screen = wa * (0.72 + 0.28 * np.clip(lum, 0, 1))[..., None] * glow + b * 0.2
    out = b * (1 - poly[..., None]) + screen * poly[..., None]
    return Image.fromarray(out.clip(0, 255).astype("uint8"))


def main():
    os.makedirs(OUT, exist_ok=True)
    ids = sys.argv[1].split(",") if len(sys.argv) > 1 else [k for k in ART if k in QUADS]
    done = []
    for sid in ids:
        if sid not in QUADS:
            print(f"[{sid}] QUADS 없음 — 건너뜀"); continue
        base = Image.open(os.path.join(KF, f"{sid}-1.png"))
        art = ART[sid]()
        im = put_lcd(base, art, QUADS[sid]) if sid in LCD else put_replace(base, art, QUADS[sid]) if sid in REPLACE else put(base, art, QUADS[sid], tol=50, strength=0.9)
        im.save(os.path.join(OUT, f"{sid}.png")); done.append(sid)
    print("합성 완료:", done)
    for k, fn in ART.items():  # 아트 미리보기(검수용)
        fn().save(os.path.join(OUT, f"_art_{k}.png")) if k in ("S03c", "S03i", "S08g", "S07d", "S07g", "S12p", "S10k") else None


if __name__ == "__main__":
    main()
