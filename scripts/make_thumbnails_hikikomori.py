#!/usr/bin/env python3
"""『引きこもりの息子』 썸네일 A·B·C(무과금·로컬) — make_thumbnails_beggar.py abc 형식(제18장 12·제13장 5).
생성 그림: assets/portraits/hikikomori-thumb-abc/thumb{A,B,C}-N.png(2560x1440). 차별어 미사용.
  A 어두운 실사(아버지 얼굴 오른쪽 — 그림을 오른쪽으로 밀어 왼쪽에 글자) / B 웹툰(무릎 꿇은 전무·아들·아버지) / C 따뜻한 투샷(스키야키)
산출: assets/thumbnails/hikikomori/hikikomori-thumb-{A,B,C}-JP.jpg(1280x720, 2MB 이하) + 360px·168px 확인본.
사용법: python3 scripts/make_thumbnails_hikikomori.py A번호 B번호 C번호
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import make_thumbnails_beggar as mb  # noqa: E402

FIRE, YELLOW, RED = mb.FIRE, mb.YELLOW, mb.RED
SRC = os.path.join(ROOT, "assets", "portraits", "hikikomori-thumb-abc")
mb.OUT = os.path.join(ROOT, "assets", "thumbnails", "hikikomori")
mb.ABC = {
    "A": dict(src="thumbA-{n}s.png", side="L", label=None,
              rows=[("引きこもり息子の", 120, None, (255, 255, 255)), ("部屋の画面に…", 120, None, (255, 255, 255))],
              row_y=300, quote="月商1250万", quote_size=270),  # 2차(2026-10-31): 168px 가독성 — 4줄 → 2줄 + 숫자 확대
    "B": dict(src="thumbB-{n}z.png", side="L", label="スカッとする話",
              rows=[("父の工場を", 150, FIRE, None), ("救った息子", 150, YELLOW, None)],
              row_y=120, shade=95, shade_w=1000, badge=("専務、土下座", "取引お断り"), badge_xy=(830, 24), band=None),  # 2차: 글자 2줄 크게(확대는 얼굴 잘림으로 불채택), 배지는 아들 머리를 가려 위쪽 가운데로(2026-10-31)
    "D": dict(src="thumbB3d-{n}s.png", side="L", label="スカッとする話",  # 3D 아바타판 B(고니감독님 제안 2026-10-31)
              rows=[("父の工場を", 150, FIRE, None), ("救った息子", 150, YELLOW, None)],
              row_y=120, shade=95, shade_w=1000, badge=("専務、土下座", "取引お断り"), badge_xy=(830, 24), band=None),
    "C": dict(src="thumbC-{n}.png", side="R", label="感動する話", label_style="black",
              rows=[("「ゴミ」と呼んだ", 104, RED, None), ("息子が守ったもの", 100, YELLOW, None)], x0=930,
              band=["四年間、黙って", "工場を支えた息子"], band_xy=(1060, 760)),
}


def shift_right(n, dx=420):
    """A: 얼굴이 가운데라 글자와 겹침 → 그림을 오른쪽으로 밀고 왼쪽은 검정으로(제0장 8 「그림을 오른쪽으로 민다」)."""
    src = Image.open(os.path.join(SRC, f"thumbA-{n}.png")).convert("RGB").resize((mb.W, mb.H), Image.LANCZOS)
    out = Image.new("RGB", (mb.W, mb.H), (4, 6, 10)); out.paste(src, (dx, 0))
    out.save(os.path.join(SRC, f"thumbA-{n}s.png"))


def shift_down_d(n, dy=170):
    """D(3D판): 2줄 제목이 아버지 머리를 가림 → 그림을 아래로 내리고 위는 흐린 같은 배경으로(얼굴 가림 금지)."""
    from PIL import ImageFilter, ImageEnhance
    src = Image.open(os.path.join(ROOT, "assets", "portraits", "hikikomori-avatar", f"thumbB3d-{n}.png")).convert("RGB").resize((mb.W, mb.H), Image.LANCZOS)
    out = Image.new("RGB", (mb.W, mb.H)); out.paste(src.crop((0, 0, mb.W, mb.H - dy)), (0, dy))
    top = src.crop((0, 0, mb.W, dy)).filter(ImageFilter.GaussianBlur(25)); out.paste(ImageEnhance.Brightness(top).enhance(0.7), (0, 0))
    out.save(os.path.join(SRC, f"thumbB3d-{n}s.png"))


def zoom_b(n, z=1.0):
    """B: 1.15배 확대는 아들 머리·아버지 얼굴이 잘려 불채택(2026-10-31) — 원본 구도 유지(z=1.0), 글자만 2줄 확대."""
    src = Image.open(os.path.join(SRC, f"thumbB-{n}.png")).convert("RGB")
    w, h = src.size; cw, ch = int(w / z), int(h / z)
    src.crop((w - cw, h - ch, w, h)).resize((w, h), Image.LANCZOS).save(os.path.join(SRC, f"thumbB-{n}z.png"))


if __name__ == "__main__":
    a = (sys.argv[1:] + ["2", "1", "3"])[:3]
    shift_right(a[0]); zoom_b(a[1])
    mb.ABC_SRC = SRC
    picks = dict(zip("ABC", a))
    if len(sys.argv) > 4:
        picks["D"] = sys.argv[4]; shift_down_d(sys.argv[4])
    mb.abc_final(picks)
    for t in "ABCD":  # 파일 이름 접두어
        for suf in ("-JP.jpg", "-phone360.jpg", "-phone168.png"):
            p = os.path.join(mb.OUT, f"beggar-thumb-{t}{suf}")
            if os.path.exists(p):
                os.replace(p, p.replace("beggar-thumb", "hikikomori-thumb"))
