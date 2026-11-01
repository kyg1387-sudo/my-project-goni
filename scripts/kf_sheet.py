#!/usr/bin/env python3
"""키프레임 Kill Gate 검수 시트 — 단계 폴더(assets/portraits/<skit>-kf-<stage>)의 <id>-1.png를 6열 시트로 묶고,
손 인서트(ins·estill, 제19장 25)는 640px 확대 시트를 따로 만든다. 라벨은 IPAGothic(일본어·영숫자).
사용법: python3 scripts/kf_sheet.py <skit> <stage> [out_dir]   예) python3 scripts/kf_sheet.py blackcard a"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"


def sheet(items, cols, cellw, out, title):
    font = ImageFont.truetype(FONT, 20) if os.path.exists(FONT) else ImageFont.load_default()
    tiles = []
    for label, path in items:
        im = Image.open(path).convert("RGB"); r = cellw / im.width
        tiles.append((label, im.resize((cellw, int(im.height * r)))))
    if not tiles:
        return
    h = max(t.height for _, t in tiles) + 30
    rows = (len(tiles) + cols - 1) // cols
    S = Image.new("RGB", (cols * cellw + (cols + 1) * 8, rows * h + 44), "white"); d = ImageDraw.Draw(S)
    d.text((10, 10), title, fill="black", font=font)
    for i, (label, t) in enumerate(tiles):
        x = 8 + (i % cols) * (cellw + 8); y = 44 + (i // cols) * h
        S.paste(t, (x, y + 26)); d.text((x, y + 2), label, fill=(170, 0, 0), font=font)
    S.save(out, quality=86); print(out, S.size, len(tiles))


def main():
    skit, stage = sys.argv[1], sys.argv[2]
    outd = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "productions", f"{skit}-ja")
    sb = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "scripts", "storyboard", f"{skit}.json"), encoding="utf-8"))["scenes"]}
    d = os.path.join(ROOT, "assets", "portraits", f"{skit}-kf-{stage}")
    files = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    items = [(f"{f[:-4]} {sb.get(f.split('-')[0], {}).get('kind', '')} {sb.get(f.split('-')[0], {}).get('size', '')}/{sb.get(f.split('-')[0], {}).get('angle', '')}", os.path.join(d, f)) for f in files]
    for k in range(0, len(items), 36):
        sheet(items[k:k + 36], 6, 420, os.path.join(outd, f"KG_{stage}_{k // 36 + 1}.jpg"), f"{skit} keyframes {stage} ({k + 1}~{min(k + 36, len(items))}/{len(items)})")
    hands = [(l, p) for l, p in items if sb.get(os.path.basename(p).split("-")[0], {}).get("kind") in ("ins", "estill")]
    for k in range(0, len(hands), 12):
        sheet(hands[k:k + 12], 3, 640, os.path.join(outd, f"KG_{stage}_hands_{k // 12 + 1}.jpg"), f"{skit} inserts {stage} 640px (hand count / fingers / object / body continuity)")


if __name__ == "__main__":
    main()
