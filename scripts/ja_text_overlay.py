#!/usr/bin/env python3
"""EP4 화면 속 일본어 글자 합성(docs/EP4-일본어글자합성-계획.md, 사용자 승인 2026-10-04).

생성 화면은 무지(글자 없음)로 만들고, 실제 일본어는 실글꼴로 그려 원근 변형해 얹는다. 무과금(로컬).
- 면 위치: 키프레임(1344x768) 기준 네 모서리(QUADS). 영상은 첫 프레임 기준으로 면 안쪽 특징점을
  광류 추적(LK)해 프레임마다 호모그래피를 다시 계산 → 카메라·종이가 미세하게 움직여도 따라간다.
- 블렌드: 먹·연필·크레용 = 곱하기(종이 질감·조명이 비침), 흰 글자(빨간 예고장) = 종이 밝기 비례 밝히기.
사용법:
  ja_text_overlay.py still <장면> <입력.png> <출력.png>     # 키프레임 미리보기
  ja_text_overlay.py video <장면> <입력.mp4> <출력.mp4>     # 클립 합성(오디오 없음)
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda n: os.path.join(ROOT, "scripts", "fonts", n)
MINCHO_B, MINCHO = F("ZenOldMincho-Bold.ttf"), F("ZenOldMincho-Regular.ttf")
HACHI, KLEE = F("HachiMaruPop-Regular.ttf"), F("KleeOne-Regular.ttf")
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
KW, KH = 1344, 768  # 키프레임 좌표계

# 면 네 모서리: 왼위, 오른위, 오른아래, 왼아래 (키프레임 픽셀)
QUADS = {
    "S07": [(824, 167), (1111, 169), (1114, 585), (825, 586)],
    "S42": [(823, 167), (1112, 169), (1116, 586), (825, 586)],
    "S18": [(262, 178), (882, 120), (1140, 612), (330, 690)],
    "S22": [(482, 222), (945, 220), (1022, 600), (428, 605)],
    "S43": [(589, 131), (697, 128), (697, 183), (590, 186)],
}


def canvas(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def centered(d, y, text, font, fill, w):
    tw = d.textlength(text, font=font)
    d.text(((w - tw) / 2, y), text, font=font, fill=fill)


def art_s07():
    """빨간 단전 예고장: 흰 명조 글자."""
    w, h = 840, 1188
    im = canvas(w, h); d = ImageDraw.Draw(im)
    centered(d, 150, "停電予告", ImageFont.truetype(MINCHO_B, 150), (255, 255, 255, 255), w)
    d.line([(110, 360), (730, 360)], fill=(255, 255, 255, 230), width=6)
    f = ImageFont.truetype(MINCHO_B, 66)
    for i, t in enumerate(["管理費未納のため、", "送電を停止します。"]):
        centered(d, 470 + i * 105, t, f, (255, 255, 255, 255), w)
    centered(d, 960, "管理事務所", ImageFont.truetype(MINCHO_B, 64), (255, 255, 255, 255), w)
    return im, "light"


def art_s42():
    """흰 완납 통지: 먹색 명조 글자."""
    w, h = 840, 1188
    im = canvas(w, h); d = ImageDraw.Draw(im); ink = (28, 26, 30, 255)
    centered(d, 140, "お知らせ", ImageFont.truetype(MINCHO_B, 130), ink, w)
    d.line([(120, 330), (720, 330)], fill=ink, width=5)
    f = ImageFont.truetype(MINCHO, 60)
    for i, t in enumerate(["1801号室", "未納管理費は", "全額納付されました。"]):
        centered(d, 440 + i * 100, t, f, ink, w)
    centered(d, 960, "管理事務所", ImageFont.truetype(MINCHO_B, 64), ink, w)
    return im, "multiply"


def art_s18():
    """아이 편지: 하치마루팝 크레용, 줄마다 색이 다르고 삐뚤빼뚤."""
    w, h = 1000, 980
    im = canvas(w, h)
    lines = [("サンタさんへ", (200, 40, 45)), ("うちは 18かいです。", (40, 80, 170)),
             ("いいこに していました。", (225, 110, 25)), ("おかあさんが なかないように", (200, 40, 45)),
             ("でんきだけは", (40, 80, 170)), ("けさないでください。", (40, 80, 170)), ("れん", (225, 110, 25))]
    rng = np.random.default_rng(18)
    for i, (t, col) in enumerate(lines):
        size = 64 if i else 72
        layer = canvas(w, 140); d = ImageDraw.Draw(layer)
        d.text((10, 10), t, font=ImageFont.truetype(HACHI, size), fill=col + (235,))
        layer = layer.rotate(float(rng.uniform(-3, 3)), resample=Image.BICUBIC, center=(0, 70))
        x = 60 + int(rng.uniform(-10, 25)) + (440 if t == "れん" else 0)
        im.alpha_composite(layer, (x, 30 + i * 128))
    # 크레용 질감: 알파에 거친 노이즈
    a = np.asarray(im).astype(np.float32)
    a[..., 3] *= np.clip(rng.normal(0.85, 0.18, a.shape[:2]), 0.35, 1.0)
    return Image.fromarray(a.astype(np.uint8)), "multiply"


def art_s22():
    """아내의 글귀: 클레 원 연필, 마지막 장 아래 귀퉁이."""
    w, h = 1000, 820
    im = canvas(w, h); d = ImageDraw.Draw(im); ink = (70, 64, 60, 200)
    f = ImageFont.truetype(KLEE, 54)
    for i, t in enumerate(["わたしたちにも 子どもがいたら…", "あなたに一度、サンタさんを", "やってほしかったな"]):
        d.text((70 + i * 6, 470 + i * 92), t, font=f, fill=ink)
    return im.filter(ImageFilter.GaussianBlur(0.8)), "multiply"


def art_s43():
    """관리사무소 명판: 갈색 나무판 위 크림색 명조."""
    w, h = 1080, 540
    im = canvas(w, h); d = ImageDraw.Draw(im)
    centered(d, 170, "管理事務所", ImageFont.truetype(MINCHO_B, 172), (245, 232, 200, 255), w)
    return im, "light"


ART = {"S07": art_s07, "S42": art_s42, "S18": art_s18, "S22": art_s22, "S43": art_s43}


def warp_art(art, quad, size):
    W, H = size
    src = np.float32([[0, 0], [art.width, 0], [art.width, art.height], [0, art.height]])
    M = cv2.getPerspectiveTransform(src, np.float32(quad))
    rgba = np.asarray(art).astype(np.float32)
    return cv2.warpPerspective(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))


def blend(frame, warped, mode, rng):
    f = frame.astype(np.float32)
    a = (warped[..., 3:4] / 255.0)
    a = cv2.GaussianBlur(a, (0, 0), 0.6)[..., None] if a.ndim == 3 else a
    if mode == "multiply":
        ink = warped[..., :3] / 255.0
        out = f * (1 - a * (1 - ink))
    else:  # light: 종이 자체 밝기를 따라 밝히기(그늘진 곳은 덜 밝게)
        lum = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None] / 255.0
        target = warped[..., :3] * np.clip(0.55 + lum * 0.9, 0, 1)
        out = f * (1 - a * 0.88) + target * a * 0.88
    out += rng.normal(0, 1.5, out.shape) * a  # 글자에도 필름 그레인
    return np.clip(out, 0, 255).astype(np.uint8)


def scaled_quad(sid, W, H):
    return [(x * W / KW, y * H / KH) for x, y in QUADS[sid]]


def still(sid, src, out):
    frame = cv2.imread(src)
    H, W = frame.shape[:2]
    art, mode = ART[sid]()
    art_bgr = Image.fromarray(np.asarray(art)[..., [2, 1, 0, 3]])
    res = blend(frame, warp_art(art_bgr, scaled_quad(sid, W, H), (W, H)), mode, np.random.default_rng(1))
    cv2.imwrite(out, res)


def video(sid, src, out):
    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    art, mode = ART[sid]()
    art_bgr = Image.fromarray(np.asarray(art)[..., [2, 1, 0, 3]])
    q0 = np.float32(scaled_quad(sid, W, H))
    ok, f0 = cap.read()
    g0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    # 면 주변(살짝 넓힌 영역)의 특징점을 추적해 호모그래피 추정
    mask = np.zeros_like(g0)
    cv2.fillConvexPoly(mask, cv2.convexHull((q0 + (q0 - q0.mean(0)) * 0.35).astype(np.int32)), 255)
    p0 = cv2.goodFeaturesToTrack(g0, 200, 0.01, 6, mask=mask)
    tmp = out + ".noaudio.mp4"
    vw = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    rng = np.random.default_rng(1)
    gp, pp, quad, n = g0, p0, q0, 0
    frame = f0
    while ok:
        if n > 0 and pp is not None and len(pp) >= 8:
            g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            p1, st, _ = cv2.calcOpticalFlowPyrLK(gp, g, pp, None, winSize=(21, 21), maxLevel=3)
            good0, good1 = pp[st == 1], p1[st == 1]
            if len(good0) >= 8:
                Hm, _ = cv2.findHomography(good0, good1, cv2.RANSAC, 2.0)
                if Hm is not None:
                    quad = cv2.perspectiveTransform(quad.reshape(-1, 1, 2), Hm).reshape(-1, 2)
                gp, pp = g, good1.reshape(-1, 1, 2)
        vw.write(blend(frame, warp_art(art_bgr, quad, (W, H)), mode, rng))
        ok, frame = cap.read(); n += 1
    vw.release()
    os.system(f'ffmpeg -v error -y -i "{tmp}" -c:v libx264 -crf 18 -pix_fmt yuv420p -an "{out}" && rm -f "{tmp}"')
    print(f"저장: {out} ({n}프레임, 추적 특징점 {0 if p0 is None else len(p0)}개)")


if __name__ == "__main__":
    mode, sid, src, out = sys.argv[1:5]
    (still if mode == "still" else video)(sid, src, out)
