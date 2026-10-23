#!/usr/bin/env python3
"""bento PHASE 4 Kill Gate 검수 시트 — 장면별 키프레임 콘택트시트(컷 ID·방식·인물 표기) + 대사 컷 얼굴 영역 확대.

사용법: python3 productions/bento-ja/kf_review.py <키프레임 폴더(예 assets/portraits/bento-kf-ab)>
출력: productions/bento-ja/PHASE4_검수/sheet_<장면>.jpg (6열, 컷당 640x360 + 라벨)
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "PHASE4_검수")
FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 22)


def main():
    src = os.path.join(REPO, sys.argv[1])
    sb = json.load(open(os.path.join(REPO, "scripts", "storyboard", "bento.json"), encoding="utf-8"))["scenes"]
    os.makedirs(OUT, exist_ok=True)
    by_scene = {}
    for s in sb:
        f = os.path.join(src, f"{s['id']}-1.png")
        if os.path.exists(f):
            by_scene.setdefault(s["scene"], []).append((s, f))
    W, H, C = 640, 360, 6
    for sc, items in by_scene.items():
        rows = (len(items) + C - 1) // C
        sheet = Image.new("RGB", (W * C, (H + 30) * rows), "black")
        d = ImageDraw.Draw(sheet)
        for k, (s, f) in enumerate(items):
            x, y = W * (k % C), (H + 30) * (k // C)
            sheet.paste(Image.open(f).convert("RGB").resize((W, H)), (x, y + 30))
            who = ",".join(os.path.basename(r).split("-")[0] for r in s.get("refs", []) if not os.path.basename(r).startswith(("loc-", "prop-")))
            d.text((x + 6, y + 3), f"{s['id']} {s['tier']} {s.get('size','')} {who}", fill="yellow", font=FONT)
        sheet.save(os.path.join(OUT, f"sheet_{sc}.jpg"), quality=85)
        print(sc, len(items))


if __name__ == "__main__":
    main()
