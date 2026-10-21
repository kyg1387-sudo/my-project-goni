#!/usr/bin/env python3
"""bento 시간 점프 마무리(로컬·무과금, 제19장 14) — 2차 검수 「갑자기 할머니·할아버지 장면」(6:11) 지적.

조립본은 전 장면 하드컷(transitions 0)이라 시대가 바뀌는 경계에서 시청자가 길을 잃는다. 타이밍(대사·립싱크)을 건드리지 않고:
  ① 시간·시대 경계 디졸브: 앞 장면 마지막 프레임을 정지해 다음 장면 위에서 서서히 사라지게(뒤 장면은 그대로 진행 → 대사 싱크 불변)
  ② 시점 자막: 다음 장면 위 왼쪽 위 구석 소자막(명조, 페이드), .ass가 아니라 영상에 직접(제15장 12·20 — 암전 없음)
  ③ 편지 속 회상 컷: 따뜻하게 바랜 색(채도↓·앰버·비네트)으로 현재와 구분 + 들어가고 나올 때 짧은 디졸브
사용법: python3 productions/bento-ja/time_transitions.py <입력.mp4> <출력.mp4>
"""
import os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FONT = os.path.join(REPO, "scripts", "fonts", "ZenOldMincho-Bold.ttf")
FPS = 24

# (컷 id, 디졸브 초, 시점 자막) — 컷 id의 시작 시각이 경계
JUMPS = [
    ("S02a", 0.8, "三十年前　平成八年"),   # 현재 → 1996 (대본 S02 시점 자막, 1차 조립에서 빠짐)
    ("S10a", 0.8, None),                  # 마지막 밤 → 계절이 돌고(몽타주)
    ("S10b", 0.6, None),
    ("S10ba", 1.0, "二十年後"),            # 1996 주방 → 병실(2016, 「十年前、澄江さんは…」와 맞물림)
    ("S10bf", 1.0, "三十年後"),             # 병실 → 2026 가게(NA21a 「三十年、守り続けた」와 맞물림, 2차 검수 지적)
]
FLASHBACK = [("S12c", "S12c"), ("S12e", "S12f"), ("S12h", "S12h"), ("S12m", "S12n")]  # 편지 속 회상(처음 컷, 끝 컷)
FB_DISSOLVE = 0.4
CAP_AT, CAP_LEN = 0.35, 3.0


def shot_times():
    t = {}
    for ln in open(os.path.join(HERE, "07_샷리스트.md"), encoding="utf-8"):
        m = re.match(r"\| (\S+) \| (\d+):(\d+)\.(\d+) - (\d+):(\d+)\.(\d+) \|", ln)
        if m:
            a = lambda mm, ss, ff: int(mm) * 60 + int(ss) + int(ff) / FPS
            t[m.group(1)] = (a(*m.group(2, 3, 4)), a(*m.group(5, 6, 7)))
    return t


def caption_png(text, path, w):
    s = w / 1920
    f = ImageFont.truetype(FONT, int(54 * s))
    pad = int(40 * s)
    box = f.getbbox(text)
    W, H = box[2] + pad * 2, box[3] + pad * 2
    im = Image.new("RGBA", (W, H))
    sh = Image.new("RGBA", (W, H))
    ImageDraw.Draw(sh).text((pad, pad), text, font=f, fill=(0, 0, 0, 200))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6 * s)))
    d = ImageDraw.Draw(im)
    d.text((pad, pad), text, font=f, fill=(250, 246, 236, 255))
    ly = pad + box[3] + int(12 * s)  # 글자 아래 가는 선(시점 자막 표지)
    d.line([(pad, ly), (pad + int(box[2] * 0.55), ly)], fill=(250, 246, 236, 180), width=max(1, int(2 * s)))
    im.save(path)
    return int(90 * s), int(70 * s)


def probe(p, key):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", f"stream={key}", "-of", "csv=p=0", p],
                          capture_output=True, text=True).stdout.strip()


def main(src, out):
    t = shot_times()
    w = int(probe(src, "width"))
    tmp = tempfile.mkdtemp()
    # 1패스: 회상 컷 색 바램
    fb = [(t[a][0], t[b][1]) for a, b in FLASHBACK]
    en = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in fb)
    graded = os.path.join(tmp, "graded.mp4")
    vf = (f"eq=saturation=0.62:contrast=0.94:brightness=0.02:enable='{en}',"
          f"colorbalance=rs=0.08:gs=0.03:bs=-0.08:rm=0.06:bm=-0.06:enable='{en}',"
          f"vignette=angle=0.55:enable='{en}'")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf, "-c:v", "libx264", "-crf", "15", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", graded], check=True)
    # 2패스: 디졸브(앞 장면 마지막 프레임 정지 → 페이드아웃) + 시점 자막
    bounds = [(t[sid][0], d, cap) for sid, d, cap in JUMPS]
    for a, b in fb:
        bounds += [(a, FB_DISSOLVE, None), (b, FB_DISSOLVE, None)]
    ins, fl, cur = ["-i", graded], [], "[0:v]"
    for k, (T, d, cap) in enumerate(sorted(bounds)):
        png = os.path.join(tmp, f"last{k}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{T - 1.5 / FPS:.3f}", "-i", graded, "-frames:v", "1", png], check=True)
        n = ins.count("-i")
        ins += ["-loop", "1", "-t", f"{d:.3f}", "-i", png]
        fl.append(f"[{n}:v]format=rgba,fade=t=out:st=0:d={d:.3f}:alpha=1,setpts=PTS-STARTPTS+{T:.3f}/TB[f{k}]")
        fl.append(f"{cur}[f{k}]overlay=eof_action=pass[v{k}]")
        cur = f"[v{k}]"
        if cap:
            cp = os.path.join(tmp, f"cap{k}.png")
            x, y = caption_png(cap, cp, w)
            n = ins.count("-i")
            ins += ["-loop", "1", "-t", f"{CAP_LEN:.3f}", "-i", cp]
            s0 = T + CAP_AT
            fl.append(f"[{n}:v]format=rgba,fade=t=in:st=0:d=0.6:alpha=1,fade=t=out:st={CAP_LEN - 0.7:.3f}:d=0.7:alpha=1,"
                      f"setpts=PTS-STARTPTS+{s0:.3f}/TB[c{k}]")
            fl.append(f"{cur}[c{k}]overlay={x}:{y}:eof_action=pass[w{k}]")
            cur = f"[w{k}]"
    fl[-1] = fl[-1].rsplit("[", 1)[0] + "[vout]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fl), "-map", "[vout]", "-map", "0:a",
                    "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", out], check=True)
    print(out, "디졸브", len(bounds), "곳 · 시점 자막", sum(1 for *_, c in JUMPS if c), "개 · 회상 색 바램", len(fb), "구간")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
