#!/usr/bin/env python3
"""『母が遺したビデオレター』 확정 키프레임 모으기 — productions/aihaha-ja/kf_pick.json(Kill Gate 확정)을
assets/portraits/aihaha-keyframes/<id>-1.png(스토리보드 keyframe 경로)로 복사, 16:9·1344x768로 맞춘다.
일본어·화면 합성(aihaha_composite.py)은 이 폴더에서 출발하고 합성 전 원본은 aihaha-keyframes-raw/에 둔다.
사용법: python3 scripts/assemble_aihaha_keyframes.py"""
import json, os
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PICK = os.path.join(ROOT, "productions", "aihaha-ja", "kf_pick.json")
OUT = os.path.join(ROOT, "assets", "portraits", "aihaha-keyframes")
RAW = os.path.join(ROOT, "assets", "portraits", "aihaha-keyframes-raw")


def main():
    pick = json.load(open(PICK, encoding="utf-8"))
    sb = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "aihaha.json"), encoding="utf-8"))["scenes"]
    need = [s["id"] for s in sb if s.get("keyframe")]
    miss = [k for k in need if k not in pick]
    assert not miss, f"확정되지 않은 키프레임: {miss}"
    os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)
    for k in need:
        st, f = pick[k].split("/")
        im = Image.open(os.path.join(ROOT, "assets", "portraits", f"aihaha-kf-{st}", f + ".png")).convert("RGB")
        if im.size != (1344, 768):
            w, h = im.size; tw = min(w, round(h * 16 / 9)); th = round(tw * 9 / 16)
            im = im.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th)).resize((1344, 768), Image.LANCZOS)
        im.save(os.path.join(RAW, f"{k}-1.png")); im.save(os.path.join(OUT, f"{k}-1.png"))
    print(f"키프레임 {len(need)}컷 → {OUT}")


if __name__ == "__main__":
    main()
