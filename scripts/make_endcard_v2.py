#!/usr/bin/env python3
"""美談ものがたり 엔드카드 v2(제19장 30③): 제목을 왼쪽 아래에 두고 오른쪽 위 1/3×1/2를 비워
YouTube 엔딩 화면 「동영상」 칸(최소 크기·위쪽 여백 고정)이 제목을 가리지 않게 한다. 오른쪽 아래는 「구독」 원 자리.
사용법: python3 scripts/make_endcard_v2.py  → assets/brand/endcard-midam-ja-v2.png / .mp4(5.5초, 소리 endcard-bed.wav)"""
import os, random, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H = 1280, 720
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
OUT = os.path.join(ROOT, "assets/brand/endcard-midam-ja-v2")

def background():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W * 0.35) / W) ** 2 + ((y - H * 0.6) / H) ** 2)
    base = np.clip(1 - d * 1.1, 0, 1)[..., None] * np.array([34, 24, 16]) + np.array([12, 9, 7])
    im = Image.fromarray(base.astype("uint8"))
    bok = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(bok)
    rnd = random.Random(7)
    for _ in range(26):
        r = rnd.randint(18, 70); cx = rnd.randint(-40, W + 40); cy = rnd.randint(-40, H + 40)
        g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(196, 160, 100, rnd.randint(28, 70)))
    bok = bok.filter(ImageFilter.GaussianBlur(14))
    im = im.convert("RGBA"); im.alpha_composite(bok)
    return im

def text(im):
    d = ImageDraw.Draw(im); x0 = 90
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    ft = ImageFont.truetype(SERIF, 104, index=0)
    gd.text((x0, 388), "美談ものがたり", font=ft, fill=(255, 220, 150, 150))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
    d.text((x0, 388), "美談ものがたり", font=ft, fill=(252, 240, 214, 255))
    d.line([x0, 556, x0 + 380, 556], fill=(205, 165, 105, 255), width=2)
    d.ellipse([x0 + 186, 552, x0 + 194, 560], fill=(205, 165, 105, 255))
    d.text((x0, 574), "小さなぬくもりの物語を、あなたに", font=ImageFont.truetype(SERIF, 34, index=0), fill=(236, 220, 190, 255))
    d.text((x0, 638), "チャンネル登録 ・ 高評価 ・ 通知をオン", font=ImageFont.truetype(SERIF, 27, index=0), fill=(205, 175, 130, 255))
    return im

if __name__ == "__main__":
    im = text(background()).convert("RGB"); im.save(OUT + ".png")
    bed = os.path.join(ROOT, "assets/brand/endcard-bed.wav")
    vf = "zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=132:s=1280x720:fps=24,fade=in:st=0:d=0.5,fade=out:st=5.0:d=0.5,format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", OUT + ".png", "-i", bed, "-vf", vf, "-t", "5.5",
                    "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT + ".mp4"], check=True)
    print(OUT + ".png", OUT + ".mp4")
