#!/usr/bin/env python3
"""#03 『老舗旅館の嫁』 쇼츠 5종 생성(무과금, 기존 완성본 재활용).
세로 1080x1920: 흐린 확대 배경 + 본편(1.2배 확대·가운데) + 상단 후크 문구 2줄 + 하단 「本編は▶チャンネルから」.
사용법: build_chika_shorts.py <chika-complete.mp4> [out_dir=deliveries/shorts]
컷 경계는 subs/ryokan-ko-trim.ass의 줄 시작 −0.45초 / 줄 끝 +1.2초(제6장 5 여운)."""
import os, re, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FONT = os.path.join(ROOT, "scripts/fonts/ZenMaruGothic-Black.ttf")
SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "deliveries/shorts")
os.makedirs(OUT, exist_ok=True)

# (번호, 시작 줄, 끝 줄, 상단 문구 1, 상단 문구 2, 파일 태그)
SHORTS = [
    (1, "line025", "line030", "「代わりはいくらでもいる」", "追い出された嫁の返事", "kawari"),
    (2, "line050", "line057", "繁忙期初日、一本の電話", "売上の4割が消えた", "cancel"),
    (3, "line046", "line049", "「お給料はゼロだったわね」", "じゃあ、あなたが決めて", "offer"),
    (4, "line062", "line066", "「あなたの代わりなら」", "いくらでもいますから", "callback"),
    (5, "line070", "line075", "「お願い、戻ってきて」", "嫁の答えは――", "ending"),
]

def ass_times():
    ev = {}
    for ln in open(os.path.join(ROOT, "subs/ryokan-ko-trim.ass"), encoding="utf-8"):
        m = re.match(r"^Dialogue: \d+,([^,]+),([^,]+),(\w+),[^,]*,\d+,\d+,\d+,([^,]*),", ln.strip())
        if m and m.group(4):
            k = m.group(4); ev.setdefault(k, [m.group(1), m.group(2)]); ev[k][1] = m.group(2)
    def sec(t):
        h, mnt, s = t.split(":"); return int(h) * 3600 + int(mnt) * 60 + float(s)
    return {k: (sec(a), sec(b)) for k, (a, b) in ev.items()}

def esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")

T = ass_times()
rows = []
for n, a, b, l1, l2, tag in SHORTS:
    t0 = max(0.0, T[a][0] - 0.45); t1 = T[b][1] + 1.2
    dur = t1 - t0
    assert dur <= 60.0, f"short {n} {dur:.1f}s > 60s"
    out = os.path.join(OUT, f"ryokan-short-{n:02d}-{tag}.mp4")
    vf = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:3,eq=brightness=-0.18:saturation=0.8[bgb];"
        "[fg]scale=1296:-2,crop=1080:ih[fgc];"
        "[bgb][fgc]overlay=0:(H-h)/2[v1];"
        f"[v1]drawtext=fontfile='{FONT}':text='{esc(l1)}':fontsize=84:fontcolor=white:borderw=7:bordercolor=black:x=(w-tw)/2:y=330,"
        f"drawtext=fontfile='{FONT}':text='{esc(l2)}':fontsize=84:fontcolor=#FFE04A:borderw=7:bordercolor=black:x=(w-tw)/2:y=440,"
        f"drawtext=fontfile='{FONT}':text='{esc('▶ 本編はチャンネルから')}':fontsize=50:fontcolor=white:borderw=5:bordercolor=black:x=(w-tw)/2:y=1500,"
        f"fade=t=out:st={dur-0.5:.2f}:d=0.5[v]"
    )
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", SRC,
           "-filter_complex", vf, "-map", "[v]", "-map", "0:a",
           "-af", f"afade=t=out:st={dur-0.6:.2f}:d=0.6",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "24",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    rows.append((n, tag, t0, t1, dur, out))
    print(f"short {n}: {t0:.2f}~{t1:.2f} ({dur:.1f}s) → {out}")
print("완료", len(rows), "개")
