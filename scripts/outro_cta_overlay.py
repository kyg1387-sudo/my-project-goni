#!/usr/bin/env python3
"""아웃트로 클립에 「高評価」「チャンネル登録」 버튼과 작은 채널 로고를 합성한다(무과금, 로컬).
버튼은 멘트 '高評価とチャンネル登録で'에 맞춰 순차로 떠오르고, 유튜브 최종 화면 요소 자리(끝 9초) 전에 사라진다.
사용법: outro_cta_overlay.py <in.mp4> <out.mp4> [like_in] [sub_in] [cta_out]
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_B = os.path.join(ROOT, "scripts/fonts/ZenOldMincho-Bold.ttf")
FONT_R = os.path.join(ROOT, "scripts/fonts/ZenOldMincho-Regular.ttf")
LOGO_TEXT = "美談ものがたり"


def probe_size(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    for tok in out.replace(",", " ").split():
        if "x" in tok and tok.split("x")[0].isdigit() and tok.split("x")[1].isdigit():
            w, h = map(int, tok.split("x"))
            if w >= 320:
                return w, h
    raise SystemExit("해상도를 못 읽음: " + path)


def pill(w, h, text, fill, color, font_px):
    """그림자 있는 둥근 알약 버튼(RGBA)."""
    pad = int(h * 0.35)
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + h * 0.06, pad + w, pad + h + h * 0.06],
                                         radius=h // 2, fill=(0, 0, 0, 110))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(h * 0.12)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], radius=h // 2, fill=fill)
    f = ImageFont.truetype(FONT_B, font_px)
    tw = d.textlength(text, font=f)
    d.text((pad + (w - tw) / 2, pad + h / 2), text, font=f, fill=color, anchor="lm")
    return img, pad


def main():
    src, out = sys.argv[1], sys.argv[2]
    like_in = float(sys.argv[3]) if len(sys.argv) > 3 else 12.2
    sub_in = float(sys.argv[4]) if len(sys.argv) > 4 else 13.0
    cta_out = float(sys.argv[5]) if len(sys.argv) > 5 else 15.9
    W, H = probe_size(src)
    tmp = tempfile.mkdtemp()

    # 버튼: 미리보기 시안과 같은 위치(가로 56%~99%, 세로 62%~71%)
    bh = int(H * 0.092)
    like, pad = pill(int(W * 0.172), bh, "高評価", (246, 244, 240, 240), (34, 30, 28, 255), int(bh * 0.46))
    sub, _ = pill(int(W * 0.246), bh, "チャンネル登録", (184, 28, 36, 245), (255, 255, 255, 255), int(bh * 0.46))
    y = int(H * 0.62) - pad
    like_x = int(W * 0.56) - pad
    sub_x = int(W * 0.56) + int(W * 0.172) + int(W * 0.016) - pad
    like_p, sub_p = os.path.join(tmp, "like.png"), os.path.join(tmp, "sub.png")
    like.save(like_p)
    sub.save(sub_p)

    # 로고: 좌상단 작은 명조체, 은은한 크림색 + 얇은 그림자
    lf = ImageFont.truetype(FONT_R, int(H * 0.036))
    logo = Image.new("RGBA", (int(W * 0.3), int(H * 0.08)), (0, 0, 0, 0))
    ImageDraw.Draw(logo).text((4, 6), LOGO_TEXT, font=lf, fill=(0, 0, 0, 120))
    logo = logo.filter(ImageFilter.GaussianBlur(2))
    ImageDraw.Draw(logo).text((2, 4), LOGO_TEXT, font=lf, fill=(250, 244, 230, 225))
    logo_p = os.path.join(tmp, "logo.png")
    logo.save(logo_p)

    fade = 0.45
    fc = (
        f"[1:v]format=rgba,fade=t=in:st=0.3:d=0.8:alpha=1[lg];"
        f"[2:v]format=rgba,fade=t=in:st={like_in}:d={fade}:alpha=1,"
        f"fade=t=out:st={cta_out - fade}:d={fade}:alpha=1[lk];"
        f"[3:v]format=rgba,fade=t=in:st={sub_in}:d={fade}:alpha=1,"
        f"fade=t=out:st={cta_out - fade}:d={fade}:alpha=1[sb];"
        f"[0:v][lg]overlay={int(W * 0.03)}:{int(H * 0.045)}:shortest=1[v1];"
        f"[v1][lk]overlay={like_x}:{y}:shortest=1[v2];"
        f"[v2][sb]overlay={sub_x}:{y}:shortest=1,format=yuv420p[v]"
    )
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src]
    for p in (logo_p, like_p, sub_p):
        cmd += ["-loop", "1", "-i", p]
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "0:a?", "-c:v", "libx264",
            "-preset", "medium", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("저장:", out)


if __name__ == "__main__":
    main()
