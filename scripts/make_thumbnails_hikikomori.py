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
              rows=[("「ゴミ」と", 112, None, (255, 255, 255)), ("追い出した息子の", 112, None, (255, 255, 255)), ("部屋を開けると…", 112, None, (255, 255, 255))],
              row_y=230, quote="月商1250万", quote_size=230),
    "B": dict(src="thumbB-{n}.png", side="L", label="スカッとする話",
              rows=[("引きこもり息子が", 120, FIRE, None), ("父の工場を救った", 120, YELLOW, None)],
              row_y=130, shade=95, shade_w=1100, badge=("専務、土下座", "取引お断り"), badge_xy=(1180, 24), band=None),
    "C": dict(src="thumbC-{n}.png", side="R", label="感動する話", label_style="black",
              rows=[("「ゴミ」と呼んだ", 104, RED, None), ("息子が守ったもの", 100, YELLOW, None)], x0=930,
              band=["四年間、黙って", "工場を支えた息子"], band_xy=(1060, 760)),
}


def shift_right(n, dx=420):
    """A: 얼굴이 가운데라 글자와 겹침 → 그림을 오른쪽으로 밀고 왼쪽은 검정으로(제0장 8 「그림을 오른쪽으로 민다」)."""
    src = Image.open(os.path.join(SRC, f"thumbA-{n}.png")).convert("RGB").resize((mb.W, mb.H), Image.LANCZOS)
    out = Image.new("RGB", (mb.W, mb.H), (4, 6, 10)); out.paste(src, (dx, 0))
    out.save(os.path.join(SRC, f"thumbA-{n}s.png"))


if __name__ == "__main__":
    a = (sys.argv[1:] + ["2", "1", "3"])[:3]
    shift_right(a[0])
    mb.ABC_SRC = SRC
    mb.abc_final(dict(zip("ABC", a)))
    for t in "ABC":  # 파일 이름 접두어
        for suf in ("-JP.jpg", "-phone360.jpg", "-phone168.png"):
            p = os.path.join(mb.OUT, f"beggar-thumb-{t}{suf}")
            if os.path.exists(p):
                os.replace(p, p.replace("beggar-thumb", "hikikomori-thumb"))
