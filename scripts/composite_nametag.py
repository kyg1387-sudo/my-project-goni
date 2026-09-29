#!/usr/bin/env python3
"""정지 이미지 위에 실제 한글 명찰 텍스트를 합성한다 (CLAUDE.md ④ 카메오 명찰 방식).

생성 모델은 화면 속 글자를 못 쓴다(비석·간판·명찰 전부 가짜 문자로 번짐, 실증) —
그래서 장면 생성 시엔 "아무 글자도 없는 매끈한 명찰"만 지시하고, 실제 이름은 이
스크립트로 후처리 합성한다. 두 가지 용도:
  1) 기준 초상(카메오 등) 정지 사진에 미리 합성한 뒤 그 사진으로 image-to-video 생성.
  2) 이미 생성된 장면에서 명찰 글자가 뭉개졌을 때, 명찰 클로즈업 정지 인서트 컷을
     만들어 편집에서 교체(무과금 수리, EP1 교훈 ⑦ / CLAUDE.md ④).

명찰 영역은 흰 배경 둥근 사각형으로 먼저 덮어 그린 뒤(기존 가짜 글자 제거) 그
위에 텍스트를 그린다 — 밑에 남은 흔적이 안 비치게 한다.

사용법:
    python3 scripts/composite_nametag.py \
        --image frame.jpg --out frame-named.jpg \
        --text 김영곤 --box 590,392,120,34
    # --box 없이 --pick 만 주면 좌표 그리드를 오버레이한 미리보기를 먼저 만들어
    # 명찰 위치를 눈으로 찾을 수 있다.
        python3 scripts/composite_nametag.py --image frame.jpg --out grid.jpg --pick
"""

import argparse
import os

from PIL import Image, ImageDraw, ImageFont

# 자막(.ass)에 쓰는 것과 같은 폰트 패밀리로 통일 — 화면 안 다른 텍스트와 질감이 다르면
# "합성한 티"가 난다.
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]


def find_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    raise SystemExit(
        "한글 폰트를 못 찾았습니다. 'apt-get install -y fonts-noto-cjk'로 설치하세요 "
        f"(확인한 경로: {FONT_CANDIDATES})."
    )


def draw_grid(image, step=50):
    """명찰 좌표를 눈으로 찾기 위한 격자 오버레이 미리보기를 만든다."""
    img = image.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    font = ImageFont.truetype(find_font(), 16)
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=(255, 0, 0, 128), width=1)
        draw.text((x + 2, 2), str(x), fill=(255, 0, 0), font=font)
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=(255, 0, 0, 128), width=1)
        draw.text((2, y + 2), str(y), fill=(255, 0, 0), font=font)
    return img


def composite(image, text, box, tag_color=(250, 250, 248), text_color=(20, 20, 20),
              radius=6, padding_ratio=0.14):
    """box=(x,y,w,h) 영역을 명찰 색으로 덮어 그린 뒤 가운데 정렬로 텍스트를 그린다."""
    x, y, w, h = box
    img = image.convert("RGB").copy()
    draw = ImageDraw.Draw(img)

    # 1) 기존 명찰(가짜 글자 포함) 지우기 — 깨끗한 배경으로 덮어 그림
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=tag_color,
                            outline=(180, 180, 175), width=1)

    # 2) 박스 높이에 맞춰 폰트 크기를 자동으로 줄여가며 폭 안에 맞는 최대 크기 찾기
    font_path = find_font()
    pad = int(h * padding_ratio)
    max_w, max_h = w - 2 * pad, h - 2 * pad
    size = max_h
    font = ImageFont.truetype(font_path, size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    while (tw > max_w or th > max_h) and size > 4:
        size -= 1
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    tx = x + (w - tw) / 2 - bbox[0]
    ty = y + (h - th) / 2 - bbox[1]
    draw.text((tx, ty), text, fill=text_color, font=font)
    return img


def parse_box(s):
    x, y, w, h = (int(v) for v in s.split(","))
    return (x, y, w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--box", type=parse_box, default=None,
                    help="명찰 영역 'x,y,w,h' (원본 이미지 픽셀 좌표)")
    ap.add_argument("--pick", action="store_true",
                    help="합성 대신 좌표 격자 미리보기만 저장 (명찰 위치 찾기용)")
    ap.add_argument("--tag-color", default="250,250,248")
    ap.add_argument("--text-color", default="20,20,20")
    args = ap.parse_args()

    image = Image.open(args.image)

    if args.pick:
        draw_grid(image).save(args.out, quality=95)
        print(f"격자 미리보기 저장 → {args.out} (명찰 x,y,w,h를 읽어 --box로 다시 실행)")
        return

    if not args.box or not args.text:
        raise SystemExit("--box와 --text가 필요합니다 (좌표를 모르면 --pick 먼저 실행)")

    tag_color = tuple(int(v) for v in args.tag_color.split(","))
    text_color = tuple(int(v) for v in args.text_color.split(","))
    result = composite(image, args.text, args.box, tag_color, text_color)
    result.save(args.out, quality=95)
    print(f"합성 완료 → {args.out} (텍스트: '{args.text}', 영역: {args.box})")


if __name__ == "__main__":
    main()
