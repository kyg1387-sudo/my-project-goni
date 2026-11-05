#!/usr/bin/env python3
"""흥행 썸네일 대조 시트 (제21장 3 「제목·썸네일」 단계).

키워드의 최근 N일 상위 영상 썸네일을 휴대폰 목록 크기(폭 168px·360px)로 격자에 놓고,
--ours 로 우리 썸네일 후보(A/B)를 맨 앞에 넣어 같은 크기에서 글자·얼굴·색이 묻히는지 비교한다.

사용법:
  python3 scripts/yt_thumb_sheet.py "捨てた妻 スカッと" [--days 30] [--top 12]
         [--ours assets/thumbs/x-A.jpg --ours assets/thumbs/x-B.jpg]
         [--tile 168|360] [--out docs/분석/thumbs/<날짜>-<키워드>.jpg]

주의: 썸네일 서버 i.ytimg.com 은 클라우드 환경 네트워크 정책에서 허용해야 받아진다(제21장 7).
      GitHub Actions(youtube-report.yml, thumb_keywords 입력)에서는 바로 받아진다.
"""
import argparse
import datetime as dt
import io
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yt_public_report import api, video_details, iso_dur, fmt_dur, n, short_title, JST  # noqa: E402

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "assets/fonts/NotoSansJP-Bold.ttf",
]


def font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


def fit(text, f, width):
    """글자 폭이 width를 넘지 않게 자른다(옆 칸 침범 방지)."""
    if f.getlength(text) <= width:
        return text
    while text and f.getlength(text + "…") > width:
        text = text[:-1]
    return text + "…"


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keyword")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=12, help="시트 장수(본편 대조는 --long-only --top 30)")
    ap.add_argument("--ours", action="append", default=[], help="우리 썸네일 파일(여러 개)")
    ap.add_argument("--tile", type=int, default=168, choices=(168, 360))
    ap.add_argument("--long-only", action="store_true", help="3분 초과 본편만")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    after = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=a.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    d = api("search", part="snippet", q=a.keyword, type="video", order="viewCount", publishedAfter=after,
            regionCode="JP", relevanceLanguage="ja", maxResults=min(a.top * 2, 50),
            **({"videoDuration": "long"} if a.long_only else {}))
    ids = [i["id"]["videoId"] for i in d.get("items", [])]
    vids = video_details(ids)
    rows = []
    for i in ids:
        v = vids.get(i)
        if not v:
            continue
        dur = iso_dur(v["contentDetails"]["duration"])
        if a.long_only and dur <= 180:
            continue
        th = v["snippet"]["thumbnails"]
        url = (th.get("maxres") or th.get("standard") or th.get("high") or th.get("medium"))["url"]
        rows.append((url, f"{n(v['statistics'].get('viewCount')):,}回 · {fmt_dur(dur)}",
                     v["snippet"]["title"]))
        if len(rows) >= a.top:
            break

    tiles = []
    for p in a.ours:
        tiles.append((Image.open(p).convert("RGB"), "★우리", os.path.basename(p)[:22]))
    for url, cap, title in rows:
        try:
            tiles.append((fetch(url), cap, title))
        except Exception as e:  # noqa: BLE001
            sys.exit(f"[오류] 썸네일 받기 실패 {url}: {e}\n"
                     "환경 네트워크 정책에 i.ytimg.com 을 허용하거나 Actions(thumb_keywords)로 만든다.")

    W, H = a.tile, int(a.tile * 9 / 16)
    cols = 4 if a.tile == 168 else 3
    pad, cap_h = 10, 2 * (14 if a.tile == 168 else 22) + 8
    rows_n = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (W + pad) + pad, rows_n * (H + cap_h + pad) + pad + 30), (24, 24, 24))
    dr = ImageDraw.Draw(sheet)
    f_small = font(13 if a.tile == 168 else 20)
    dr.text((pad, 6), f"{a.keyword} · 최근 {a.days}일 상위 · 타일 {W}px(휴대폰 목록 크기)", fill=(220, 220, 220), font=f_small)
    for k, (im, cap, title) in enumerate(tiles):
        r, c = divmod(k, cols)
        x, y = pad + c * (W + pad), 30 + pad + r * (H + cap_h + pad)
        im = im.resize((W, H), Image.LANCZOS)
        sheet.paste(im, (x, y))
        if cap == "★우리":
            dr.rectangle((x - 2, y - 2, x + W + 1, y + H + 1), outline=(255, 80, 80), width=2)
        dr.text((x, y + H + 3), fit(cap, f_small, W), fill=(255, 215, 120) if cap == "★우리" else (200, 200, 200), font=f_small)
        dr.text((x, y + H + 3 + (14 if a.tile == 168 else 22)), fit(title, f_small, W), fill=(170, 170, 170), font=f_small)

    out = a.out or os.path.join("docs/분석/thumbs", f"{dt.datetime.now(JST):%Y-%m-%d}-{a.keyword.replace(' ', '_')}-{W}.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out, quality=88)
    print(f"[시트] {len(tiles)}장 → {out}")


if __name__ == "__main__":
    main()
