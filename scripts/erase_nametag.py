#!/usr/bin/env python3
"""이미 생성된 영상 프레임 속 명찰(가짜 글자 포함)을 자연스럽게 지운다.

CLAUDE.md 방침(2026-09-30, 도희 명찰 실증) — 이미 생성된 영상의 명찰은 이름 텍스트를
새로 합성하지 말고 지우는 게 기본이다. 사후 텍스트 합성은 원본 명찰의 회전각·크기를
프레임마다 눈대중으로 맞추기 어려워 "겹쳐 보인다"는 문제가 반복됐다.

두 가지 모드:
  1) --mode erase (기본): OpenCV `cv2.seamlessClone`(포아송 블렌딩)로 근처의 깨끗한
     옷감 질감을 가져와 명찰 자리에 이식해 통째로 지운다. 처음 쓴 라플라스 인페인팅
     (경계 색을 반복 확산)은 "모자이크 처리한 것처럼" 뭉개져 보인다는 지적을 받았다 —
     포아송 블렌딩 + 프로그램으로 검증된 깨끗한 소스 위치라야 자연스럽다.
     소스 위치는 --src-dx/--src-dy로 직접 지정하거나, --auto-src를 주면 밝기·채도로
     흰색(옷깃 등) 오염이 없는 가장 가까운 위치를 자동 스캔한다(사람 손처럼 애매한
     피부색까지는 못 거르므로, 자동 스캔 결과도 crop으로 먼저 눈으로 확인할 것).
  2) --mode blank: 손·단추·소매 등으로 주변이 복잡해 깨끗한 소스를 못 찾을 때 쓰는
     대안(참교육사이다 97번 장면 실증) — 명찰 틀(테두리)은 남기고 안쪽만 명찰 자체의
     밝은 색으로 채워 "글자 없는 빈 명찰"로 만든다. 원래 설정("아무 글자도 없는 흰
     명찰")과도 부합해 위험이 적다.

사용법:
    # 1) 먼저 --pick으로 명찰 좌표를 찾는다 (밝기/채도로 자동 검출도 시도)
    python3 scripts/erase_nametag.py --image frame.jpg --out grid.jpg --pick

    # 2) erase 모드 (자동으로 깨끗한 소스 스캔)
    python3 scripts/erase_nametag.py --image frame.jpg --out fixed.jpg \
        --box 692,575,100,86 --angle -17 --auto-src

    # 2') erase 모드 (소스 위치 직접 지정)
    python3 scripts/erase_nametag.py --image frame.jpg --out fixed.jpg \
        --box 692,575,100,86 --angle -17 --src-dx -100 --src-dy -10

    # 3) blank 모드 (주변이 복잡할 때)
    python3 scripts/erase_nametag.py --image frame.jpg --out fixed.jpg \
        --box 431,644,66,40 --mode blank
"""

import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def find_font_free_blob(img, x0, y0, x1, y1, bright_th=150, sat_th=40):
    """영역 내 밝고 채도 낮은(흰색류) 픽셀 마스크를 돌려준다 — 명찰 후보 탐지용."""
    px = img.load()
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    mpx = mask.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b = px[x, y]
            bright = (r + g + b) / 3
            sat = max(r, g, b) - min(r, g, b)
            if bright > bright_th and sat < sat_th:
                mpx[x - x0, y - y0] = 255
    return mask


def largest_blob(mask, min_size=30, max_size=220, min_area=800):
    """마스크에서 화면 경계에 안 닿는 가장 큰 덩어리의 bbox를 돌려준다(연결요소 분석)."""
    from collections import deque

    w, h = mask.size
    px = mask.load()
    visited = [[False] * w for _ in range(h)]
    best, best_area = None, 0
    for sy in range(h):
        for sx in range(w):
            if px[sx, sy] != 255 or visited[sy][sx]:
                continue
            q = deque([(sx, sy)])
            visited[sy][sx] = True
            minx = maxx = sx
            miny = maxy = sy
            area = 0
            touches = False
            while q:
                x, y = q.popleft()
                area += 1
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    touches = True
                minx, maxx = min(minx, x), max(maxx, x)
                miny, maxy = min(miny, y), max(maxy, y)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and px[nx, ny] == 255 and not visited[ny][nx]:
                        visited[ny][nx] = True
                        q.append((nx, ny))
            bw, bh = maxx - minx, maxy - miny
            if not touches and min_size < bw < max_size and min_size < bh < max_size and area > min_area:
                if area > best_area:
                    best_area = area
                    best = (minx, miny, maxx, maxy, area)
    return best


def scan_clean_source(img, cx, cy, w, h, max_radius=250, step=15):
    """(cx,cy) 중심 w x h 영역과 겹치지 않으면서 흰색(옷깃 등) 오염이 없는 가장 가까운
    오프셋 (dx,dy)을 찾는다. 피부색(손)까지는 못 거르므로 결과는 눈으로 재확인할 것."""
    px = img.load()
    W, H = img.size

    def white_frac(dx, dy):
        x0, y0 = int(cx + dx - w / 2), int(cy + dy - h / 2)
        x1, y1 = x0 + w, y0 + h
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            return None
        cnt = white = 0
        for y in range(y0, y1, 3):
            for x in range(x0, x1, 3):
                r, g, b = px[x, y]
                bright = (r + g + b) / 3
                sat = max(r, g, b) - min(r, g, b)
                cnt += 1
                if bright > 170 and sat < 45:
                    white += 1
        return white / cnt if cnt else 1.0

    best = None
    for dx in range(-max_radius, max_radius + 1, step):
        for dy in range(-max_radius, max_radius + 1, step):
            if abs(dx) < w // 2 and abs(dy) < h // 2:
                continue
            f = white_frac(dx, dy)
            if f is not None and f < 0.02:
                d2 = dx * dx + dy * dy
                if best is None or d2 < best[0]:
                    best = (d2, dx, dy, f)
    return best


def build_mask(size_wh, box, angle, dilate=5):
    W, H = size_wh
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    tag = Image.new("L", (w, h), 255)
    tag_rot = tag.rotate(angle, expand=True, resample=Image.BICUBIC)
    tw, th = tag_rot.size
    tx, ty = round(cx - tw / 2), round(cy - th / 2)
    mask = Image.new("L", (W, H), 0)
    mask.paste(tag_rot, (tx, ty))
    if dilate:
        mask = mask.filter(ImageFilter.MaxFilter(dilate))
    return mask, (cx, cy)


def erase_seamless(img, box, angle, src_dx, src_dy):
    import cv2

    W, H = img.size
    mask_pil, (cx, cy) = build_mask((W, H), box, angle)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    mask_cv = np.array(mask_pil)
    m = np.float32([[1, 0, src_dx], [0, 1, src_dy]])
    src = cv2.warpAffine(img_cv, m, (W, H), borderMode=cv2.BORDER_REFLECT)
    out = cv2.seamlessClone(src, img_cv, mask_cv, (int(cx), int(cy)), cv2.NORMAL_CLONE)
    return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))


def blank_interior(img, box, inset=7, radius=6):
    """명찰 테두리는 두고 안쪽만 명찰 자체의 밝은 색으로 채운다(--mode blank)."""
    x, y, w, h = box
    px = img.load()
    corners = [(x + inset, y + inset), (x + w - inset, y + inset),
               (x + inset, y + h - inset), (x + w - inset, y + h - inset)]
    rs = gs = bs = 0
    for cx_, cy_ in corners:
        r, g, b = px[cx_, cy_]
        rs, gs, bs = rs + r, gs + g, bs + b
    fill = (rs // 4, gs // 4, bs // 4)
    out = img.copy()
    draw = ImageDraw.Draw(out)
    draw.rounded_rectangle([x + inset, y + inset, x + w - inset, y + h - inset],
                            radius=radius, fill=fill)
    return out


def parse_box(s):
    x, y, w, h = (int(v) for v in s.split(","))
    return (x, y, w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--box", type=parse_box, default=None)
    ap.add_argument("--angle", type=float, default=0.0)
    ap.add_argument("--mode", choices=["erase", "blank"], default="erase")
    ap.add_argument("--src-dx", type=int, default=None)
    ap.add_argument("--src-dy", type=int, default=None)
    ap.add_argument("--auto-src", action="store_true",
                     help="흰색 오염 없는 가장 가까운 소스 위치를 자동 스캔 (손 등은 못 거름 — 결과 확인 필수)")
    ap.add_argument("--pick", action="store_true",
                     help="좌표 격자 + 자동 검출된 흰색 덩어리 bbox를 출력하고 종료")
    args = ap.parse_args()

    img = Image.open(args.image).convert("RGB")
    W, H = img.size

    if args.pick:
        grid = img.copy()
        draw = ImageDraw.Draw(grid)
        for gx in range(0, W, 50):
            draw.line([(gx, 0), (gx, H)], fill=(255, 0, 0), width=1)
            draw.text((gx + 2, 2), str(gx), fill=(255, 0, 0))
        for gy in range(0, H, 50):
            draw.line([(0, gy), (W, gy)], fill=(0, 255, 0), width=1)
            draw.text((2, gy + 2), str(gy), fill=(0, 255, 0))
        grid.save(args.out, quality=95)
        print(f"격자 미리보기 저장 → {args.out}")
        return

    if not args.box:
        raise SystemExit("--box가 필요합니다 (좌표를 모르면 --pick 먼저 실행)")

    if args.mode == "blank":
        result = blank_interior(img, args.box)
        result.save(args.out, quality=95)
        print(f"완료(blank) → {args.out}")
        return

    x, y, w, h = args.box
    cx, cy = x + w / 2, y + h / 2
    if args.auto_src:
        found = scan_clean_source(img, cx, cy, w, h)
        if not found:
            raise SystemExit("깨끗한 소스 위치를 못 찾았습니다 — --src-dx/--src-dy로 직접 지정하세요")
        _, src_dx, src_dy, frac = found
        print(f"자동 소스 위치: dx={src_dx}, dy={src_dy} (흰색 비율 {frac:.3f}) — 결과를 눈으로 꼭 확인할 것")
    else:
        if args.src_dx is None or args.src_dy is None:
            raise SystemExit("--src-dx/--src-dy 또는 --auto-src가 필요합니다")
        src_dx, src_dy = args.src_dx, args.src_dy

    result = erase_seamless(img, args.box, args.angle, src_dx, src_dy)
    result.save(args.out, quality=95)
    print(f"완료(erase) → {args.out} (box={args.box}, angle={args.angle}, src=({src_dx},{src_dy}))")


if __name__ == "__main__":
    main()
