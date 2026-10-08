#!/usr/bin/env python3
"""완성 본편에서 립싱크 클로즈업의 배경만 교체(무과금, 로컬) — 감독님 지적 2026-10-07
「할아버지 장면 일관성」: OmniHuman 컷 뒤가 단상·빈 의자(방향·인원이 앞뒤 컷과 다름).

프레임마다 인물을 분리(rembg u2net_human_seg)해 배경을 '만석 회의장(같은 방) 흐린 판'으로 바꾼다.
자막은 배경 교체 뒤 같은 스타일로 다시 입힌다(원본 자막과 같은 위치·모양이라 겹쳐도 그대로). 시각은 조립 검수 report.txt 장면 경계.
사용법: tower_bg_swap.py <in.mp4> <out.mp4> <report.txt>
"""
import os
import re
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
W, H, FPS, SUB_TOP = 1920, 1080, 24, 830
# 컷 → 배경 판(키프레임, 크롭 x0,y0,x1,y1, 흐림) — 같은 회의장 만석 뒤쪽
ERODE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
# 감독님 지적(2026-10-08 앉은 사람과 서 있는 사람 방향이 반대): 객석에 서서 단상을 보는 인물 클로즈업 뒤로 단상·스크린이 보였다
# → 단상에서 객석을 본 역방향 판(PLATE_R 임시총회 약 40명, PLATE_T 통상총회 만석). 할아버지(맨 뒤에서 단상을 봄)는 돌아본 주민 뒷머리(S16c).
REV_R, REV_T = "assets/portraits/tower-kf-b-r/PLATE_R-1.png", "assets/portraits/tower-kf-b-r/PLATE_T-1.png"
PLATES = {"S16b": ("S16c", (0, 260, 1344, 768), 9), "S16f": ("S16c", (0, 260, 1344, 768), 9),
          "S17e": ("S16c", (0, 260, 1344, 768), 9), "S14m": (REV_T, (0, 200, 1344, 768), 9),
          "S05e": (REV_R, (0, 200, 1344, 768), 9), "S07b": (REV_R, (0, 200, 1344, 768), 9),
          "S13d": (REV_T, (0, 200, 1344, 768), 9), "S17i2": (REV_T, (0, 200, 1344, 768), 9)}


def plate(sid):
    k, box, blur = PLATES[sid]
    path = os.path.join(ROOT, k) if "/" in k else os.path.join(ROOT, "assets/portraits/tower-keyframes", f"{k}-1.png")
    im = Image.open(path).convert("RGB").crop(box)
    a = cv2.resize(np.asarray(im), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), blur)
    return a * 0.92   # 배경을 살짝 어둡게(인물 분리감)


def shifted_ass(a, b, out):
    ts = lambda t: (lambda h, m, x: int(h) * 3600 + int(m) * 60 + float(x))(*t.split(":"))
    tc = lambda x: f"{int(max(0, x) // 3600)}:{int(max(0, x) % 3600 // 60):02d}:{max(0, x) % 60:05.2f}"
    lines = open(os.path.join(ROOT, "subs/tower.ass"), encoding="utf-8").read().splitlines(); o = []
    for l in lines:
        if l.startswith("Dialogue:"):
            q = l.split(",", 9)
            if not (ts(q[2]) > a and ts(q[1]) < b):
                continue
            q[1], q[2] = tc(ts(q[1]) - a), tc(ts(q[2]) - a); l = ",".join(q)
        o.append(l)
    open(out, "w", encoding="utf-8").write("\n".join(o) + "\n")
    return out


def main():
    src, out, report = sys.argv[1:4]
    rep = open(report, encoding="utf-8").read()
    T = {m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(r"^(S\S+):\s+([0-9.]+) ~\s+([0-9.]+)s", rep, re.M)}
    from rembg import remove, new_session
    sess = new_session("u2net_human_seg")
    work = out + ".work"; os.makedirs(work, exist_ok=True)
    segs = []
    for sid in PLATES:
        a, b = T[sid]; a += 0.05; b -= 0.05
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        F = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
        P = plate(sid); prev = None
        p = os.path.join(work, f"{sid}.mp4")
        ass = shifted_ass(a, b, os.path.join(work, f"{sid}.ass"))   # 배경을 바꾼 자리의 번인 자막을 같은 스타일로 다시 입힌다
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-vf", f"ass={ass}", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", p], stdin=subprocess.PIPE)
        for f in F:
            small = Image.fromarray(f).resize((W // 2, H // 2))
            m = np.asarray(remove(small, session=sess, only_mask=True)).astype(np.float32) / 255
            m = cv2.resize(m, (W, H))
            m = cv2.erode(m, ERODE)   # 원본 역광 림(흰 테두리)까지 오려지는 후광 제거
            m = m if prev is None else 0.6 * m + 0.4 * prev   # 가장자리 깜빡임 완화
            prev = m
            a_ = cv2.GaussianBlur(m, (0, 0), 2.0)[..., None]
            o = f.astype(np.float32) * a_ + P * (1 - a_)
            enc.stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes())
        enc.stdin.close(); enc.wait()
        segs.append((a, b, p)); print(f"{sid}: {a:.2f}~{b:.2f}s 배경 교체 {len(F)}프레임")
    ins = ["-i", src]
    for _, _, p in segs:
        ins += ["-i", p]
    fc, cur = [], "[0:v]"
    for k, (a, b, _) in enumerate(segs):
        fc.append(f"[{k + 1}:v]setpts=PTS+{a:.3f}/TB[s{k}];{cur}[s{k}]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]")
        cur = f"[o{k}]"
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc) + f";{cur}format=yuv420p[v]", "-map", "[v]", "-map", "0:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
    print("저장:", out)


if __name__ == "__main__":
    main()
