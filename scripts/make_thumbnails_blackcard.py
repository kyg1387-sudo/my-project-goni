#!/usr/bin/env python3
"""『ブラックカード』(第1話) 썸네일 A·B·C(무과금·로컬) — make_thumbnails_beggar.py abc 형식(제18장 12·제13장 5).
생성 그림: assets/portraits/blackcard-thumb-abc/thumb{A,B,C}-N.png(2560x1440).
  A 어두운 실사(健二 얼굴 오른쪽 + 카드, 왼쪽 글자) / B 웹툰(의자째 무너진 柴田·무릎 꿇은 美咲·내려다보는 健二) / C 따뜻한 투샷(健二 + 会長)
산출: assets/thumbnails/blackcard/blackcard-thumb-{A,B,C}-JP.jpg(1280x720, 2MB 이하) + 360px·168px 확인본.
사용법: python3 scripts/make_thumbnails_blackcard.py A번호 B번호 C번호
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import make_thumbnails_beggar as mb  # noqa: E402

FIRE, YELLOW, RED = mb.FIRE, mb.YELLOW, mb.RED
SRC = os.path.join(ROOT, "assets", "portraits", "blackcard-thumb-abc")
mb.OUT = os.path.join(ROOT, "assets", "thumbnails", "blackcard")
mb.ABC = {
    "A": dict(src="thumbA-{n}s.png", side="L", label=None,
              rows=[("希望退職の翌日", 112, None, (255, 255, 255)), ("元部下は――", 112, None, (255, 255, 255))],
              row_y=300, quote="ビルのオーナー", quote_size=196),
    "B": dict(src="thumbB-{n}.png", side="L", label="スカッとする話",
              rows=[("切った部下が", 150, FIRE, None), ("ビルの主に", 150, YELLOW, None)],
              row_y=120, shade=95, shade_w=1000, badge=("妻の不倫相手は", "上司だった"), badge_xy=(930, 24), band=None),
    "C": dict(src="thumbC-{n}.png", side="R", label=None,
              rows=[("十五年、捨てられた男の", 88, RED, None), ("本当の復讐", 118, YELLOW, None)], x0=640, row_y=36,
              band=["「判子は――ここ」", "三度目の、その言葉"], band_xy=(1060, 780)),
}


def shift_right(n, dx=140):
    """A: 글자와 카드를 든 손이 겹치지 않게 그림을 오른쪽으로 밀고 왼쪽은 검정(제0장 8)."""
    src = Image.open(os.path.join(SRC, f"thumbA-{n}.png")).convert("RGB").resize((mb.W, mb.H), Image.LANCZOS)
    out = Image.new("RGB", (mb.W, mb.H), (4, 6, 10)); out.paste(src, (dx, 0))
    out.save(os.path.join(SRC, f"thumbA-{n}s.png"))


if __name__ == "__main__":
    a = (sys.argv[1:] + ["1", "1", "1"])[:3]
    shift_right(a[0])
    mb.ABC_SRC = SRC
    mb.abc_final(dict(zip("ABC", a)))
    for t in "ABC":
        for suf in ("-JP.jpg", "-phone360.jpg", "-phone168.png"):
            p = os.path.join(mb.OUT, f"beggar-thumb-{t}{suf}")
            if os.path.exists(p):
                os.replace(p, p.replace("beggar-thumb", "blackcard-thumb"))
