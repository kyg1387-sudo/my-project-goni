"""고니감독님 제공 썸네일(외부 생성, 글자 포함) 보정 — 워터마크 제거·「実録！」→「衝撃！」·폰 보조 문구 교체·젤 눈물 정리 → 1280x720 A2/B2 + 168·360px 확인본 (로컬, 무료)."""
import os, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "assets/thumbnails/yamibaito"); SRC = os.path.join(D, "src")
FONT = os.path.join(ROOT, "scripts/fonts/ZenMaruGothic-Black.ttf")
FONT_SQ = os.path.join(ROOT, "scripts/fonts/ZenKakuGothicNew-Bold.ttf")  # 원본 흰 글자(각고딕)와 맞추는 용
RED, WHITE, BLACK = (225, 20, 20), (255, 255, 255), (0, 0, 0)

def inpaint(a, boxes, r=9):
    m = np.zeros(a.shape[:2], np.uint8)
    for x0, y0, x1, y1 in boxes: m[y0:y1, x0:x1] = 255
    return cv2.inpaint(a, m, r, cv2.INPAINT_TELEA)

def text_layer(size, lines, font_px, fill, outline, outline_w, outer=None, outer_w=0, line_gap=1.05, align="left", font=None, bold=0):
    im = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(im); f = ImageFont.truetype(font or FONT, font_px)
    y = 0
    for ln in lines:
        w = d.textlength(ln, font=f); x = 0 if align == "left" else (size[0] - w) / 2
        if outer: d.text((x, y), ln, font=f, fill=outer, stroke_width=outer_w, stroke_fill=outer)
        d.text((x, y), ln, font=f, fill=outline, stroke_width=outline_w + bold, stroke_fill=outline)
        d.text((x, y), ln, font=f, fill=fill, stroke_width=bold, stroke_fill=fill)  # bold: 획 굵히기(Black 대용)
        y += int(font_px * line_gap)
    return im

def paste(a, layer, x, y, deg=0.0):
    if deg: layer = layer.rotate(deg, expand=True, resample=Image.BICUBIC)
    base = Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB)).convert("RGBA"); base.alpha_composite(layer, (int(x), int(y)))
    return cv2.cvtColor(np.array(base.convert("RGB")), cv2.COLOR_RGB2BGR)

def streak_clean(a, boxes):
    """젤 눈물 줄기·방울: 상자 안에서 주변보다 밝은 좁은 하이라이트만 인페인트(피부 질감 유지)."""
    g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32); bl = cv2.GaussianBlur(g, (0, 0), 9)
    m = np.zeros(a.shape[:2], np.uint8)
    for x0, y0, x1, y1 in boxes:
        sub = ((g - bl) > 14)[y0:y1, x0:x1]; m[y0:y1, x0:x1] = sub.astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((7, 7), np.uint8))
    return cv2.inpaint(a, m, 6, cv2.INPAINT_TELEA)

def finish(a, name):
    """2000x1091 → 위아래 17px 복제 패딩으로 16:9 → 1280x720 JPG(≤2MB) + 360·168 확인본."""
    a = cv2.copyMakeBorder(a, 17, 17, 0, 0, cv2.BORDER_REPLICATE)
    out = cv2.resize(a, (1280, 720), interpolation=cv2.INTER_AREA)
    p = os.path.join(D, f"yamibaito-thumb-{name}-JP.jpg"); q = 92
    while True:
        cv2.imwrite(p, out, [cv2.IMWRITE_JPEG_QUALITY, q])
        if os.path.getsize(p) <= 2_000_000 or q <= 70: break
        q -= 4
    cv2.imwrite(os.path.join(D, f"yamibaito-thumb-{name}-phone360.jpg"), cv2.resize(out, (360, 203), interpolation=cv2.INTER_AREA))
    cv2.imwrite(os.path.join(D, f"yamibaito-thumb-{name}-phone168.png"), cv2.resize(out, (168, 95), interpolation=cv2.INTER_AREA))
    print(name, p, os.path.getsize(p) // 1000, "KB")
    return out

WM = [(1885, 985, 1965, 1045)]  # 생성기 워터마크 ✦

def make_A():
    a = cv2.imread(os.path.join(SRC, "ext-A-cage.webp"))
    a = inpaint(a, WM + [(70, 345, 405, 475)])                       # 워터마크 + 「実録！」
    a = inpaint(a, [(1445, 325, 1925, 600)], 11)                     # 폰 안 작은 붉은 문구
    a = paste(a, text_layer((430, 160), ["衝撃！"], 118, WHITE, BLACK, 9, font=FONT_SQ, bold=2), 72, 338)
    lay = text_layer((560, 300), ["即日現金", "面接なし"], 112, RED, WHITE, 8, outer=BLACK, outer_w=16, line_gap=1.12, align="center")
    a = paste(a, lay, 1400, 300, deg=-9)
    return finish(a, "A2")

def make_B():
    a = cv2.imread(os.path.join(SRC, "ext-B-face.webp"))
    a = inpaint(a, WM)
    a = inpaint(a, [(1440, 330, 1925, 745)], 11)                     # 「闇バイトの闇、暴露 時給5万円」
    a = streak_clean(a, [(270, 560, 345, 720), (620, 560, 700, 720), (790, 520, 870, 660)])
    lay = text_layer((560, 320), ["一週間で", "消えた"], 122, RED, WHITE, 8, outer=BLACK, outer_w=16, line_gap=1.12, align="center")
    a = paste(a, lay, 1395, 345, deg=-9)
    return finish(a, "B2")

if __name__ == "__main__":
    A = make_A(); B = make_B()
    C = cv2.imread(os.path.join(D, "yamibaito-thumb-C-JP.jpg"))
    sheet = np.vstack([np.hstack([cv2.resize(x, (640, 360)) for x in (A, B, C)]),
                       np.hstack([cv2.copyMakeBorder(cv2.resize(x, (168, 95), interpolation=cv2.INTER_AREA), 0, 265, 0, 472, cv2.BORDER_CONSTANT, value=(30, 30, 30)) for x in (A, B, C)])])
    cv2.imwrite(os.path.join(D, "yamibaito-thumb-ABC-check.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88]); print("check sheet")
