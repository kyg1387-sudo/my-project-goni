#!/usr/bin/env python3
"""일본 택시 번호판 합성 — 무과금, 로컬 (運転手 R22).

생성 모델이 그린 번호판의 가짜 글자를 실물 규격의 가상 번호판으로 덮는다.
사업용(택시) = 녹색 바탕·흰 글자, 위 줄 「지역명 + 분류번호」, 아래 줄 「히라가나 + 일련번호(37-08)」.
지역명은 실존하지 않는 가상 지명(기본 「東都」)이라 실제 차량과 겹치지 않는다.
사용법: plate_overlay.py <in.png> <out.png> x0 y0 x1 y1 [--light 0.75] [--blur 0.6] [--text "東都 500|あ|37-08"]
  x0..y1 = 번호판 네 모서리를 감싸는 사각형(원본 픽셀). light = 장면 밝기에 맞춘 명도 배율.
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "ZenMaruGothic-Black.ttf")
GREEN, WHITE = (24, 92, 58), (238, 240, 236)


def plate(text, w=660, h=330):
    top, kana, num = text.split("|")
    im = Image.new("RGB", (w, h), GREEN)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, w - 9, h - 9), radius=22, outline=WHITE, width=7)
    ft, fk, fn = ImageFont.truetype(FONT, 78), ImageFont.truetype(FONT, 84), ImageFont.truetype(FONT, 168)
    tw = d.textlength(top, font=ft)
    d.text(((w - tw) / 2, 22), top, font=ft, fill=WHITE)
    d.text((36, 170), kana, font=fk, fill=WHITE)
    nw = d.textlength(num, font=fn)
    d.text((w - nw - 40, 110), num, font=fn, fill=WHITE)
    for x in (w * 0.2, w * 0.8):  # 볼트 자리
        d.ellipse((x - 9, 26, x + 9, 44), fill=(200, 205, 200))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("box", nargs=4, type=int)
    ap.add_argument("--light", type=float, default=0.75)
    ap.add_argument("--blur", type=float, default=0.6)
    ap.add_argument("--text", default="東都 500|あ|37-08")
    a = ap.parse_args()
    x0, y0, x1, y1 = a.box
    base = Image.open(a.src).convert("RGB")
    p = plate(a.text).resize((x1 - x0, y1 - y0), Image.LANCZOS)
    p = ImageEnhance.Brightness(p).enhance(a.light).filter(ImageFilter.GaussianBlur(a.blur))
    base.paste(p, (x0, y0))
    base.save(a.dst)
    print(a.dst)


if __name__ == "__main__":
    main()
