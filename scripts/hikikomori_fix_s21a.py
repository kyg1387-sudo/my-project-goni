#!/usr/bin/env python3
"""S21a 계약서 찢기 — 무지 종이에 계약서 뒷면 비침(좌우 반전·옅게·흐리게) 합성(2026-10-30, 「어떤 종이인지」 전달 + 실감).
아버지는 인쇄면을 자기 쪽으로 들고 있으므로 카메라에는 뒷면 → 글자는 반전되어 옅게 비친다. 손가락은 채도 키로 보호."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hikikomori_ja_overlay as jov

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H = 1000, 1400
im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
d.text((W / 2, 120), "事業譲渡契約書", font=ImageFont.truetype(jov.M, 84), fill=(20, 20, 25), anchor="mm")
body = ["瀬尾精工（以下「甲」という）と鳳凰工業", "株式会社（以下「乙」という）は、甲の事業", "及び特許権の譲渡に関し、次のとおり契約を", "締結する。", "",
        "第１条（目的）", "甲は、その工場設備及び特許権の一切を乙に", "譲渡する。", "", "第２条（譲渡価額）", "譲渡価額は、金三千万円とする。", "",
        "第３条（引渡し）", "甲は、本契約締結後速やかに……"]
for i, t in enumerate(body):
    d.text((80, 260 + i * 62), t, font=ImageFont.truetype(jov.M, 40), fill=(30, 30, 35))
d.text((560, 1220), "甲　署名", font=ImageFont.truetype(jov.M, 40), fill=(30, 30, 35)); d.line([(720, 1250), (940, 1250)], fill=(40, 40, 40), width=2)
im = ImageOps.mirror(im).filter(ImageFilter.GaussianBlur(2.2))  # 뒷면 비침: 반전 + 종이 섬유로 번짐
L, R = im.crop((0, 0, W // 2, H)), im.crop((W // 2, 0, W, H))
base = Image.open(os.path.join(ROOT, "assets/portraits/hikikomori-keyframes/S21a-1.png")).convert("RGB")
out = jov.put(base, L, [(392, 226), (644, 224), (644, 660), (410, 666)], tol=60, strength=0.09)
out = jov.put(out, R, [(656, 224), (924, 224), (920, 660), (656, 664)], tol=60, strength=0.09)
os.makedirs(os.path.join(ROOT, "assets/preview/hikikomori-fix"), exist_ok=True)
out.save(os.path.join(ROOT, "assets/preview/hikikomori-fix/S21a.png"))
