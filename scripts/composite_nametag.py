#!/usr/bin/env python3
"""정지 이미지 위에 실제 한글 명찰 텍스트를 합성한다 (CLAUDE.md ④ 카메오 명찰 방식).

생성 모델은 화면 속 글자를 못 쓴다(비석·간판·명찰 전부 가짜 문자로 번짐, 실증) —
그래서 장면 생성 시엔 "아무 글자도 없는 매끈한 명찰"만 지시하고, 실제 이름은 이
스크립트로 후처리 합성한다. 두 가지 용도:
  1) 기준 초상(카메오 등) 정지 사진에 미리 합성한 뒤 그 사진으로 image-to-video 생성.
  2) 이미 생성된 장면에서 명찰 글자가 뭉개졌을 때, 명찰 클로즈업 정지 인서트 컷을
     만들어 편집에서 교체(무과금 수리, EP1 교훈 ⑦ / CLAUDE.md ④).

명찰은 별도 투명 레이어에 그린 뒤 --angle(도, 시계방향 양수)만큼 기울여서 합성한다 —
옷감이 몸통 각도를 따라 기울어져 있는데 명찰을 수평으로 평평하게 얹으면 "화면 위에
붙인 그래픽 스티커"처럼 뜬다(실증: 참교육사이다 77번 장면, 사용자 지적 — "명찰은
가슴에 부착하는것인데 화면에 명찰이 나오네"). 옷 표면 기울기에 맞춰 회전시키고
아래에 옅은 그림자를 깔아야 실제로 옷에 핀으로 꽂힌 물체처럼 보인다. --angle은
--pick 격자 미리보기에서 명찰 주변 옷깃/단추 줄의 기울기를 눈으로 재서 정할 것.

사용법:
    python3 scripts/composite_nametag.py \
        --image frame.jpg --out frame-named.jpg \
        --text 김영곤 --box 590,392,120,34 --angle -8
    # --box 없이 --pick 만 주면 좌표 그리드를 오버레이한 미리보기를 먼저 만들어
    # 명찰 위치·기울기를 눈으로 찾을 수 있다.
        python3 scripts/composite_nametag.py --image frame.jpg --out grid.jpg --pick
    # 실물 사원증 스타일(상단 포인트 컬러 줄 + 직함/이름 + 하단 로마자 표기 바):
        python3 scripts/composite_nametag.py \
            --image frame.jpg --out frame-named.jpg --style badge \
            --text 한도희 --rank 요양보호사 --romanized "D. H. HAN" \
            --box 335,1028,165,62 --angle -10
"""

import argparse
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

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
    """명찰 좌표·기울기를 눈으로 찾기 위한 격자 오버레이 미리보기를 만든다."""
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


def render_tag_layer(w, h, draw_fn, radius=6):
    """(w, h) 크기의 투명 RGBA 레이어에 draw_fn(draw, 0, 0, w, h)로 명찰 내용을 그려
    돌려준다 — 회전·그림자 합성을 위해 원본 프레임과 분리해 그린다."""
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw_fn(draw, 0, 0, w, h)
    return layer


def paste_tag(base_image, tag_layer, box, angle=0.0,
              shadow_offset=(2, 3), shadow_blur=3, shadow_opacity=110,
              soften=0.7):
    """tag_layer(투명 RGBA, box의 w×h 크기)를 box 중심을 기준으로 angle도만큼
    회전시켜 그림자와 함께 base_image에 합성한다 — 옷 표면 기울기에 맞추면
    "붙어 있는 물체"처럼 보이고, 수평 그대로 얹으면 "화면 위 그래픽"처럼 붕 뜬다.
    soften(px)만큼 살짝 블러를 줘 벡터로 그린 명찰 가장자리·글자가 영상 프레임의
    사진 질감(약간의 노이즈·압축 블러)과 안 섞이고 "스티커처럼" 튀는 것을 줄인다
    (실증: 완전히 또렷한 벡터 텍스트는 사용자가 "어색해"로 지적)."""
    x, y, w, h = box
    base = base_image.convert("RGBA")
    cx, cy = x + w / 2, y + h / 2

    # 그림자: 명찰과 같은 실루엣(알파 채널)을 검게 칠해 오프셋 후 블러
    shadow = Image.new("RGBA", tag_layer.size, (0, 0, 0, 0))
    shadow_alpha = tag_layer.split()[3].point(lambda a: shadow_opacity if a > 0 else 0)
    shadow.putalpha(shadow_alpha)
    shadow_rot = shadow.rotate(angle, expand=True, resample=Image.BICUBIC)
    shadow_rot = shadow_rot.filter(ImageFilter.GaussianBlur(shadow_blur))
    sw, sh = shadow_rot.size
    sx = round(cx - sw / 2 + shadow_offset[0])
    sy = round(cy - sh / 2 + shadow_offset[1])
    base.alpha_composite(shadow_rot, (sx, sy))

    if soften > 0:
        tag_layer = tag_layer.filter(ImageFilter.GaussianBlur(soften))
    tag_rot = tag_layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    tw, th = tag_rot.size
    tx = round(cx - tw / 2)
    ty = round(cy - th / 2)
    base.alpha_composite(tag_rot, (tx, ty))
    return base.convert("RGB")


def draw_simple(draw, x, y, w, h, text, tag_color, text_color, radius=6,
                 padding_ratio=0.14):
    """box 전체를 명찰 색 둥근 사각형으로 채운 뒤 텍스트를 가운데 정렬로 그린다.
    테두리는 진한 선 대신 tag_color보다 살짝 어두운 톤만 얇게 둘러 "실물 명찰판의
    옆면 두께"처럼 보이게 하고, 글자는 아래쪽에 밝은 하이라이트 사본을 먼저 깔아
    살짝 파인 각인(embossed) 느낌을 준다 — EP1 경비원 김씨 금속 명찰 참고, 평평한
    벡터 텍스트만 그리면 "붙여넣은 스티커"처럼 어색해 보인다(실증)."""
    rim = tuple(max(0, c - 35) for c in tag_color)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=tag_color,
                            outline=rim, width=1)
    font_path = find_font()
    pad = int(h * padding_ratio)
    max_w, max_h = w - 2 * pad, h - 2 * pad
    font, bbox = fit_text(draw, text, font_path, max_w, max_h)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = x + (w - tw) / 2 - bbox[0]
    ty = y + (h - th) / 2 - bbox[1]
    highlight = tuple(min(255, c + 60) for c in tag_color)
    draw.text((tx, ty + 1), text, fill=highlight, font=font)
    draw.text((tx, ty), text, fill=text_color, font=font)


def fit_text(draw, text, font_path, max_w, max_h):
    """max_w x max_h 안에 들어가는 가장 큰 폰트 크기로 (font, bbox)를 돌려준다."""
    size = max(max_h, 4)
    font = ImageFont.truetype(font_path, size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    while (tw > max_w or th > max_h) and size > 4:
        size -= 1
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    return font, bbox


def draw_centered(draw, text, font, cx, cy, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), text, fill=fill, font=font)


def draw_badge(draw, x, y, w, h, name_kr, rank, romanized,
                accent_color, bg_color, text_color, radius=4):
    """실물 사원증 명찰 스타일(사용자 제공 참고 사진 기준): 상단 얇은 포인트 컬러
    줄 → 흰 바탕에 [직함 소형 + 이름 대형] → 하단 포인트 컬러 바에 로마자 표기(흰
    글자). rank/romanized가 없으면 그 줄은 생략하고 남은 공간을 이름 줄에 재분배."""
    font_path = find_font()
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=bg_color,
                            outline=(170, 170, 165), width=1)

    top_h = max(2, int(h * 0.07))
    bot_h = int(h * 0.34) if romanized else 0
    mid_h = h - top_h - bot_h

    draw.rectangle([x, y, x + w, y + top_h], fill=accent_color)
    if bot_h:
        draw.rounded_rectangle([x, y + h - bot_h, x + w, y + h], radius=radius,
                                fill=accent_color)
        draw.rectangle([x, y + h - bot_h, x + w, y + h - bot_h + radius], fill=accent_color)

    pad = max(2, int(w * 0.05))
    mid_cy = y + top_h + mid_h / 2
    if rank:
        rank_font, rank_bbox = fit_text(draw, rank, font_path,
                                         int(w * 0.22), int(mid_h * 0.55))
        rw = rank_bbox[2] - rank_bbox[0]
        name_font, name_bbox = fit_text(draw, name_kr, font_path,
                                         w - 2 * pad - rw - pad, int(mid_h * 0.8))
        nw = name_bbox[2] - name_bbox[0]
        total_w = rw + pad + nw
        start_x = x + (w - total_w) / 2
        draw_centered(draw, rank, rank_font, start_x + rw / 2, mid_cy, text_color)
        draw_centered(draw, name_kr, name_font, start_x + rw + pad + nw / 2, mid_cy, text_color)
    else:
        name_font, _ = fit_text(draw, name_kr, font_path, w - 2 * pad, int(mid_h * 0.8))
        draw_centered(draw, name_kr, name_font, x + w / 2, mid_cy, text_color)

    if bot_h:
        rom_font, _ = fit_text(draw, romanized, font_path, w - 2 * pad, int(bot_h * 0.7))
        draw_centered(draw, romanized, rom_font, x + w / 2, y + h - bot_h / 2, (255, 255, 255))


def parse_box(s):
    x, y, w, h = (int(v) for v in s.split(","))
    return (x, y, w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="", help="--style simple일 때 표시할 텍스트")
    ap.add_argument("--box", type=parse_box, default=None,
                    help="명찰 영역 'x,y,w,h' (원본 이미지 픽셀 좌표, 기울기 반영 전 기준 크기)")
    ap.add_argument("--angle", type=float, default=0.0,
                    help="명찰을 옷 표면 기울기에 맞춰 회전시킬 각도(도, 시계방향 양수). "
                         "--pick 격자에서 명찰 주변 옷깃/단추 줄 기울기를 보고 정할 것 — "
                         "0으로 두면 수평으로 붕 떠 보인다(실증).")
    ap.add_argument("--pick", action="store_true",
                    help="합성 대신 좌표 격자 미리보기만 저장 (명찰 위치 찾기용)")
    ap.add_argument("--style", default="simple", choices=["simple", "badge"],
                    help="simple=흰 배경에 텍스트 한 줄, badge=실물 사원증 스타일"
                         "(직함+이름 / 로마자 표기, 사용자 참고 사진 기준)")
    ap.add_argument("--tag-color", default="250,250,248")
    ap.add_argument("--text-color", default="20,20,20")
    ap.add_argument("--accent-color", default="196,30,30", help="badge 스타일의 포인트 컬러")
    ap.add_argument("--rank", default=None, help="badge 스타일: 직함 (예 '요양보호사')")
    ap.add_argument("--romanized", default=None, help="badge 스타일: 로마자 표기 (예 'D. H. HAN')")
    ap.add_argument("--shadow-opacity", type=int, default=110,
                    help="명찰 아래 그림자 진하기(0=그림자 없음, 0~255)")
    ap.add_argument("--soften", type=float, default=0.7,
                    help="명찰 전체에 줄 블러(px) — 벡터 텍스트가 영상 프레임보다 "
                         "또렷해서 스티커처럼 튀는 것을 줄인다. 0=블러 없음.")
    args = ap.parse_args()

    image = Image.open(args.image)

    if args.pick:
        draw_grid(image).save(args.out, quality=95)
        print(f"격자 미리보기 저장 → {args.out} (명찰 x,y,w,h와 기울기를 읽어 --box/--angle로 다시 실행)")
        return

    if not args.box or not args.text:
        raise SystemExit("--box와 --text가 필요합니다 (좌표를 모르면 --pick 먼저 실행)")

    x, y, w, h = args.box
    if args.style == "badge":
        accent = tuple(int(v) for v in args.accent_color.split(","))
        tag_color = tuple(int(v) for v in args.tag_color.split(","))
        text_color = tuple(int(v) for v in args.text_color.split(","))
        layer = render_tag_layer(
            w, h,
            lambda d, lx, ly, lw, lh: draw_badge(
                d, lx, ly, lw, lh, args.text, args.rank, args.romanized,
                accent, tag_color, text_color))
    else:
        tag_color = tuple(int(v) for v in args.tag_color.split(","))
        text_color = tuple(int(v) for v in args.text_color.split(","))
        layer = render_tag_layer(
            w, h,
            lambda d, lx, ly, lw, lh: draw_simple(
                d, lx, ly, lw, lh, args.text, tag_color, text_color))

    result = paste_tag(image, layer, args.box, angle=args.angle,
                        shadow_opacity=args.shadow_opacity, soften=args.soften)
    result.save(args.out, quality=95)
    print(f"합성 완료 → {args.out} (스타일: {args.style}, 텍스트: '{args.text}', "
          f"영역: {args.box}, 각도: {args.angle}도)")


if __name__ == "__main__":
    main()
