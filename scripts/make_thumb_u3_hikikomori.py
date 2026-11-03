#!/usr/bin/env python3
"""썸네일 T1(고니감독님 시안 U3 「お前はゴミだ」 분할 구도) 재구성 — 본편 인물 일치(R60)·가짜 글자 0.
왼쪽 = 生成 健太郎 오열 CU(hikikomori-thumb-u3l, 본편 얼굴·수염 없음), 오른쪽 = 본편 키프레임 S05c(어두운 방 모니터 빛 속 大樹, 화면 합성본),
글자 = 로컬 합성(흰 「お前は」 + 노란 「ゴミだ」, 굵은 명조 + 검은 테 + 그림자). 오른쪽 아래(재생 시간)는 비운다.
사용법: python3 scripts/make_thumb_u3_hikikomori.py <왼쪽 번호 1~3> [얼굴 가로 위치 0~1]
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H = 1920, 1080
OUT = os.path.join(ROOT, "assets", "thumbnails", "hikikomori")
F = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")


def main(n, cx=0.30):
    L = Image.open(os.path.join(ROOT, f"assets/portraits/hikikomori-thumb-u3l/U3L-{n}.png")).convert("RGB")
    lw, lh = L.size; cw = int(lh * (W / 2) / H)  # 왼쪽 절반 비율로, 인물(왼쪽~가운데)을 중심에
    x0 = max(0, min(lw - cw, int(lw * cx) - cw // 2))
    left = L.crop((x0, 0, x0 + cw, lh)).resize((W // 2, H), Image.LANCZOS)
    # 오른쪽: S05c(어두운 방, 모니터 3대 빛 속 大樹) — S05f는 밝고 머리가 글자에 가려 불채택(2026-10-31)
    R = Image.open(os.path.join(ROOT, "assets/preview/hikikomori-screens/S05c.png")).convert("RGB")
    rw, rh = R.size; cw2 = int(rh * (W / 2) / H)
    right = R.crop((40, 0, 40 + cw2, rh)).resize((W // 2, H), Image.LANCZOS)
    right = ImageEnhance.Contrast(ImageEnhance.Brightness(right).enhance(1.05)).enhance(1.15)
    img = Image.new("RGB", (W, H), (8, 10, 14))
    dy = 110  # 글자(위 0~290px)가 아버지 머리를 가리지 않게 인물을 아래로(얼굴 가림 금지, 제0장 8)
    img.paste(left.crop((0, 0, W // 2, H - dy)), (0, dy))
    top = left.crop((0, 0, W // 2, dy)).filter(ImageFilter.GaussianBlur(20)); img.paste(ImageEnhance.Brightness(top).enhance(0.5), (0, 0))
    img.paste(right, (W // 2, 0))
    d = ImageDraw.Draw(img); d.line([(W // 2, 0), (W // 2, H)], fill=(0, 0, 0), width=8)  # 분할선
    # 위쪽 글자 띠를 살짝 어둡게(글자 대비)
    shade = Image.new("L", (W, H), 0); ImageDraw.Draw(shade).rectangle([0, 0, W, 300], fill=150)
    shade = shade.filter(ImageFilter.GaussianBlur(60)); img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, shade)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); f = ImageFont.truetype(F, 250)
    parts = [("お前は", (255, 255, 255)), ("ゴミだ", (255, 214, 0))]
    widths = [ld.textlength(t, font=f) for t, _ in parts]; x = W - 40 - sum(widths); y = 18
    for (t, c), w_ in zip(parts, widths):
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((x + 10, y + 12), t, font=f, fill=(0, 0, 0, 200))
        lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        ld.text((x, y), t, font=f, fill=c, stroke_width=12, stroke_fill=(0, 0, 0)); x += w_
    img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, "hikikomori-thumb-T1-JP.jpg")
    img.resize((1280, 720), Image.LANCZOS).save(p, quality=92)
    img.resize((360, 203), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone360.jpg"), quality=90)
    img.resize((168, 95), Image.LANCZOS).save(p.replace("-JP.jpg", "-phone168.png"))
    print("저장:", p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "3", float(sys.argv[2]) if len(sys.argv) > 2 else 0.40)  # U3L-3: 얼굴이 가로 약 40% 위치
