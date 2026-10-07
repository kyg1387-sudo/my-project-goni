#!/usr/bin/env python3
"""인물 일관성 대조 시트(제작규격 보강 EP4 §7) — 무과금, 로컬.

스토리보드 refs(예 KIMW@front, MOM@expr-tearful)로 인물별 등장 장면을 자동 수집해,
시트 정면 셀 + 각 장면 키프레임의 얼굴 크롭을 인물마다 한 줄로 늘어놓는다.
여러 명이 나오는 장면은 얼굴이 가장 큰 사람을 고르므로 라벨에 '*'를 붙인다(직접 확인).
사용법: qa_faces.py <scripts/storyboard/<skit>.json> <out.jpg> [키프레임 폴더(기본 assets/portraits/<ep>-keyframes)]
필요: pip install "opencv-python-headless<5" (얼굴 검출기 포함 버전)
"""
import json
import os
import sys

import cv2
from PIL import Image, ImageDraw, ImageFont

FONT = ImageFont.truetype("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", 20)
FRONT = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
PROFILE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
SKIP = ("LOC", "PROP", "CART", "GMA")


def face_tile(path, label, size=220):
    im = cv2.imread(path)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    fs = list(FRONT.detectMultiScale(g, 1.1, 5, minSize=(24, 24))) or list(PROFILE.detectMultiScale(g, 1.1, 4, minSize=(24, 24)))
    if fs:
        x, y, w, h = max(fs, key=lambda r: r[2] * r[3])
        m = int(w * 0.5)
        im = im[max(0, y - m):y + h + m, max(0, x - m):x + w + m]
    else:
        label += "?"
    t = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)).resize((size, size))
    d = ImageDraw.Draw(t)
    d.rectangle([0, 0, 10 + 11 * len(label), 24], fill=(0, 0, 0))
    d.text((4, 2), label, font=FONT, fill=(255, 255, 0))
    return t


def main():
    sb = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    kdir = sys.argv[3] if len(sys.argv) > 3 else None
    ref_map = sb.get("ref_map", {})
    people = {}
    for s in sb["scenes"]:
        kf = s.get("keyframe")
        if kdir and kf:
            kf = os.path.join(kdir, os.path.basename(kf))
        if not kf or not os.path.exists(kf):
            continue
        chars = [r.split("@")[0] for r in s.get("refs", []) if "@" in r and r.split("@")[0] not in SKIP]
        for c in dict.fromkeys(chars):
            people.setdefault(c, []).append((kf, s["id"] + ("*" if len(set(chars)) > 1 else "")))
    rows = []
    for c, items in people.items():
        tiles = []
        pat = ref_map.get(c, "")
        if "<cell>" in pat:
            front = pat.replace("<cell>", "front")
            if os.path.exists(front):
                tiles.append(face_tile(front, "SHEET"))
        tiles += [face_tile(p, lab) for p, lab in items]
        r = Image.new("RGB", (220 * len(tiles) + 90, 220), "white")
        ImageDraw.Draw(r).text((4, 100), c, font=FONT, fill="black")
        for k, t in enumerate(tiles):
            r.paste(t, (90 + k * 220, 0))
        rows.append(r)
    W = max(r.size[0] for r in rows)
    sheet = Image.new("RGB", (W, 230 * len(rows)), "white")
    for k, r in enumerate(rows):
        sheet.paste(r, (0, k * 230))
    sheet.save(out, quality=90)
    print(f"저장: {out} — " + ", ".join(f"{c} {len(v)}장면" for c, v in people.items()))


if __name__ == "__main__":
    main()
