#!/usr/bin/env python3
"""인물 시트(3x3) 동일 인물 대조판 — 무과금, 로컬 (運転手 R18).

시트 9칸을 잘라 얼굴을 검출해 인물마다 한 줄로 늘어놓는다(1번 = 정면 기준 칸).
각 칸은 정면 칸과 나이·머리·수염·점·안경·귀걸이·눈물을 눈으로 대조한다(★5).
사용법: qa_sheet_faces.py <out.jpg> <sheet.png> [<sheet.png> ...]
"""
import os, sys
import cv2
from PIL import Image, ImageDraw, ImageFont

FONT_P = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FONT = ImageFont.truetype(FONT_P, 18) if os.path.exists(FONT_P) else ImageFont.load_default()
FRONT = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
PROFILE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
CELLS = ["1 front", "2 45deg", "3 profile", "4 full", "5 back", "6 full", "7 expr1", "8 expr2", "9 expr3"]


def face(cell, size):
    g = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    fs = list(FRONT.detectMultiScale(g, 1.1, 5, minSize=(20, 20))) or list(PROFILE.detectMultiScale(g, 1.1, 4, minSize=(20, 20)))
    if fs:
        x, y, w, h = max(fs, key=lambda r: r[2] * r[3])
        m = int(w * 0.45)
        cell = cell[max(0, y - m):y + h + m, max(0, x - m):x + w + m]
    im = Image.fromarray(cv2.cvtColor(cell, cv2.COLOR_BGR2RGB))
    im.thumbnail((size, size))
    t = Image.new("RGB", (size, size), "white")
    t.paste(im, ((size - im.width) // 2, (size - im.height) // 2))
    return t, bool(fs)


def main():
    out, sheets = sys.argv[1], sys.argv[2:]
    size, lab = 200, 150
    board = Image.new("RGB", (lab + size * 9, (size + 24) * len(sheets)), "white")
    d = ImageDraw.Draw(board)
    for r, p in enumerate(sheets):
        im = cv2.imread(p)
        H, W = im.shape[:2]
        y0 = r * (size + 24)
        d.text((6, y0 + size // 2), os.path.basename(p).replace(".png", ""), fill="black", font=FONT)
        for k in range(9):
            i, j = divmod(k, 3)
            cell = im[i * H // 3:(i + 1) * H // 3, j * W // 3:(j + 1) * W // 3]
            t, ok = face(cell, size)
            board.paste(t, (lab + k * size, y0))
            d.text((lab + k * size + 4, y0 + size + 2), CELLS[k] + ("" if ok else " (no face)"), fill="black", font=FONT)
    board.save(out, quality=88)
    print(out)


if __name__ == "__main__":
    main()
