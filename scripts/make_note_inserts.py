#!/usr/bin/env python3
"""김씨의 쪽지 (EP2) — 쪽지·수첩 필체 인서트 클립 생성기 (무과금 로컬 렌더).

생성 모델은 화면 속 글자를 못 쓰므로(EP1 실증), 필체 인서트 8컷은
PIL로 종이+실제 한글 손글씨 폰트를 합성해 5초 클립으로 만들고
assets/video-overrides/kim-note/sceneNN.mp4 로 저장한다.
generate-video.yml 이 생성 전에 out/ 으로 복사해 해당 장면 생성을 건너뛴다(=비용 0).

필체 구분: 아내=나눔펜(가늘고 단정), 김씨=나눔붓(굵고 뭉툭), 준호=나눔펜+글자 흔들림(서툰 글씨).
폰트: NanumPenScript / NanumBrushScript (OFL, scripts/fonts/ 또는 FONT_DIR).

사용법: python3 scripts/make_note_inserts.py [출력폴더]
"""
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(ROOT, "scripts", "fonts"))
PEN = os.path.join(FONT_DIR, "NanumPenScript-Regular.ttf")
BRUSH = os.path.join(FONT_DIR, "NanumBrushScript-Regular.ttf")
W, H = 1280, 720
INK = (52, 48, 58)          # 짙은 잉크색
INK_OLD = (88, 74, 60)      # 바랜 잉크색


def paper(size, tone=(246, 242, 230), aged=False, lines=False):
    """따뜻한 조명의 종이 질감: 미세 노이즈 + 가장자리 그림자 + (선택) 가로줄."""
    w, h = size
    im = Image.new("RGB", size, tone)
    rnd = random.Random(42)
    px = im.load()
    for _ in range(w * h // 14):  # 섬유 노이즈
        x, y = rnd.randrange(w), rnd.randrange(h)
        r, g, b = px[x, y]
        d = rnd.randint(-7, 7)
        px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))
    if aged:  # 누런 얼룩
        stain = Image.new("L", size, 0)
        sd = ImageDraw.Draw(stain)
        for _ in range(6):
            x, y = rnd.randrange(w), rnd.randrange(h)
            rad = rnd.randint(w // 8, w // 4)
            sd.ellipse([x - rad, y - rad, x + rad, y + rad], fill=rnd.randint(14, 30))
        stain = stain.filter(ImageFilter.GaussianBlur(w // 12))
        im = Image.composite(Image.new("RGB", size, (214, 196, 156)), im, stain)
    d = ImageDraw.Draw(im)
    if lines:
        for y in range(90, h - 20, 72):
            d.line([(50, y), (w - 50, y)], fill=(206, 198, 182), width=2)
    # 가장자리 음영(비네트)
    vig = Image.new("L", size, 0)
    vd = ImageDraw.Draw(vig)
    vd.rectangle([w // 22, h // 22, w - w // 22, h - h // 22], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(w // 16))
    dark = Image.new("RGB", size, tuple(int(c * 0.78) for c in tone))
    return Image.composite(im, dark, vig)


def draw_text(im, text, font_path, size, color, jitter=0.0, y0=None, x_pad=70,
              line_gap=1.28, align_center=False):
    """여러 줄 손글씨. jitter>0 이면 글자별 위치·크기를 흔들어 서툰 글씨 느낌."""
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(font_path, size)
    lines = text.split("\n")
    lh = int(size * line_gap)
    total_h = lh * len(lines)
    y = y0 if y0 is not None else (im.height - total_h) // 2
    rnd = random.Random(7)
    for line in lines:
        if jitter <= 0:
            tw = d.textlength(line, font=font)
            x = (im.width - tw) // 2 if align_center else x_pad
            d.text((x, y), line, font=font, fill=color)
        else:
            tw = sum(d.textlength(ch, font=font) for ch in line)
            x = (im.width - tw) // 2 if align_center else x_pad
            for ch in line:
                f2 = ImageFont.truetype(font_path, size + rnd.randint(-int(size * jitter),
                                                                      int(size * jitter)))
                dy = rnd.randint(-int(size * jitter), int(size * jitter))
                rot = rnd.uniform(-4, 4)
                cw = int(d.textlength(ch, font=f2)) + 8
                if cw > 8:
                    tile = Image.new("RGBA", (cw + 16, int(size * 1.6)), (0, 0, 0, 0))
                    ImageDraw.Draw(tile).text((8, 0), ch, font=f2, fill=color)
                    tile = tile.rotate(rot, resample=Image.BICUBIC, expand=False)
                    im.paste(tile, (int(x), int(y + dy)), tile)
                x += d.textlength(ch, font=font)
        y += lh
    return im


def note_card(text, font_path, size, aged=False, jitter=0.0, lines=False, sub=None):
    """책상 위 쪽지 한 장(화면 가득) 렌더."""
    bg = Image.new("RGB", (W, H), (38, 30, 24))  # 어두운 나무 책상 톤
    wood = bg.load()
    rnd = random.Random(3)
    for yy in range(H):
        warm = int(10 * math.sin(yy / 47.0))
        for xx in range(0, W, 3):
            r, g, b = wood[xx, yy]
            d = rnd.randint(-4, 4) + warm
            wood[xx, yy] = (max(0, r + d + 6), max(0, g + d), max(0, b + d - 2))
    bg = bg.filter(ImageFilter.GaussianBlur(1))
    pw, ph = int(W * 0.72), int(H * 0.80)
    tone = (222, 206, 168) if aged else (246, 242, 230)
    note = paper((pw, ph), tone=tone, aged=aged, lines=lines)
    ink = INK_OLD if aged else INK
    note = draw_text(note, text, font_path, size, ink, jitter=jitter, align_center=True)
    if sub:  # 오른쪽 아래 작은 서명줄
        sd = ImageDraw.Draw(note)
        sf = ImageFont.truetype(font_path, int(size * 0.55))
        tw = sd.textlength(sub, font=sf)
        sd.text((pw - tw - 60, ph - int(size * 0.55) - 50), sub, font=sf, fill=ink)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([(W - pw) // 2 + 14, (H - ph) // 2 + 18,
                                  (W + pw) // 2 + 14, (H + ph) // 2 + 18], fill=(0, 0, 0, 130))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    bg.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), sh)
    bg.paste(note, ((W - pw) // 2, (H - ph) // 2))
    return bg


def notebook_page(text, font_path, size, color=INK, unfinished=False):
    """펼친 수첩 페이지(꽃무늬 테두리 힌트 + 가로줄)."""
    im = note_card("", font_path, size, lines=False)
    pw, ph = int(W * 0.72), int(H * 0.80)
    page = paper((pw, ph), tone=(248, 244, 236), lines=True)
    d = ImageDraw.Draw(page)
    for i, cx in enumerate(range(40, pw - 30, 54)):  # 꽃무늬 테두리 힌트(상단 점무늬)
        c = [(214, 168, 178), (196, 202, 168), (206, 186, 208)][i % 3]
        d.ellipse([cx, 22, cx + 14, 36], fill=c)
    page = draw_text(page, text, font_path, size, color, y0=110, x_pad=80)
    if unfinished:  # 쓰다 만 채 끊긴 획
        d2 = ImageDraw.Draw(page)
        lines_ = text.split("\n")
        f = ImageFont.truetype(font_path, size)
        last = lines_[-1]
        lw = d2.textlength(last, font=f)
        y = 110 + int(size * 1.28) * (len(lines_) - 1) + size // 2
        d2.line([(80 + lw + 6, y), (80 + lw + 66, y + 16)], fill=INK_OLD, width=5)
    im.paste(page, ((W - pw) // 2, (H - ph) // 2))
    return im


def two_notes(left_text, right_text):
    """두 쪽지 나란히 (아내=바랜 종이/김씨=흰 종이)."""
    bg = note_card("", PEN, 40)  # 책상 배경 재사용
    nw, nh = int(W * 0.40), int(H * 0.62)
    old = paper((nw, nh), tone=(222, 206, 168), aged=True)
    old = draw_text(old, left_text, PEN, 54, INK_OLD, align_center=True)
    new = paper((nw, nh), tone=(247, 244, 234))
    new = draw_text(new, right_text, BRUSH, 64, INK, align_center=True)
    for im2, x, rot in ((old, int(W * 0.065), 2.5), (new, int(W * 0.53), -1.8)):
        r = im2.convert("RGBA").rotate(rot, resample=Image.BICUBIC, expand=True)
        bg.paste(r, (x, (H - r.height) // 2), r)
    return bg


def three_notes(texts):
    """쪽지 모음 3장 (김씨 필체, 살짝 겹쳐 나란히)."""
    bg = note_card("", PEN, 40)
    nw, nh = int(W * 0.30), int(H * 0.52)
    xs = [int(W * 0.045), int(W * 0.355), int(W * 0.665)]
    rots = [3.0, -2.0, 2.2]
    for text, x, rot in zip(texts, xs, rots):
        note = paper((nw, nh), tone=(247, 244, 234))
        note = draw_text(note, text, BRUSH, 46, INK, align_center=True)
        r = note.convert("RGBA").rotate(rot, resample=Image.BICUBIC, expand=True)
        bg.paste(r, (x, (H - r.height) // 2), r)
    return bg


def to_clip(im, out_mp4, seconds=5):
    png = out_mp4.replace(".mp4", ".png")
    big = im.resize((W * 2, H * 2), Image.LANCZOS)  # zoompan 떨림 방지용 업스케일
    big.save(png)
    frames = seconds * 24
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", png, "-t", str(seconds),
        "-vf", (f"zoompan=z='1+0.012*on/{frames}':x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=24,setsar=1"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24", out_mp4,
    ], check=True, capture_output=True)
    os.remove(png)
    print("생성:", out_mp4)


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "assets", "video-overrides", "kim-note")
    os.makedirs(out_dir, exist_ok=True)

    cards = {
        # scene10: 수첩 아내 필체 (쓰다 만 채 끊김)
        10: notebook_page("수요일마다 504호에\n반찬 걸어 줄 것.\n그 청년, 밥은 먹고 사는지.\n그 청년—",
                          PEN, 62, color=INK_OLD, unfinished=True),
        # scene14: 김씨 첫 쪽지
        14: note_card("먹게.", BRUSH, 150),
        # scene18: 김씨 두 번째 쪽지
        18: note_card("국은 데워 먹게.", BRUSH, 110),
        # scene23: 쪽지 모음 3장
        23: three_notes(["김치\n새로 했네.", "환절기다.\n감기\n조심하게.", "무리하지\n말게."]),
        # scene36: 준호의 서툰 쪽지
        36: note_card("드세요.", PEN, 150, jitter=0.10),
        # scene41: 아내의 7년 전 쪽지 (바램)
        41: note_card("밥 한 끼의 온기가,\n사람을 살린단다.", PEN, 84, aged=True,
                      sub="— 504호 청년에게"),
        # scene46: 두 쪽지 나란히 (무음 여운)
        46: two_notes("밥 한 끼의 온기가,\n사람을 살린단다.", "국은 데워\n먹게."),
        # scene53: 수첩 김씨 필체 (마지막 한 줄)
        53: notebook_page("여보.\n그 청년, 오늘\n문 열고 나갔소.", BRUSH, 72),
    }
    for n, im in cards.items():
        to_clip(im, os.path.join(out_dir, f"scene{n:02d}.mp4"))
    print(f"완료: {len(cards)}개 인서트 → {out_dir}")


if __name__ == "__main__":
    main()
