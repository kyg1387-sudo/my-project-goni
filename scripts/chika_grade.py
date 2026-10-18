#!/usr/bin/env python3
"""『地下倉庫の伝票』 장소별 공통 그레이딩 + 35mm 그레인 (무과금, 로컬) — 03_시네마규격.json color_grading, 규격 제8장 6.

조립본(report.txt 장면 경계)을 읽어 장면의 조명 키(스토리보드 light)에 따라 구간별 색을 통일한다. 영상만 다시 인코딩, 오디오 복사.
  지하 창고·복도(arc*, cor)      Teal_Cold_Desaturated — 그림자 청록, 채도 −10%, 대비 +8% (책상 램프의 따뜻한 풀은 남김)
  지하 엔딩(arc_end)             Warm_Orange_Soft — 따뜻한 오렌지, 대비 −3%
  사무실·강당·엘리베이터           Neutral_Corporate_Slightly_Cool — 청색 +3%, 채도 −5%
  연회장(bq, bq_press)           Warm_Amber_Gold — 하이라이트 앰버, 채도 +5%
  연회장 냉색(bq_cold, bq_proj)   차갑게 — 청색 +6%, 채도 −10%, 대비 +10%
  전편: 35mm 그레인(약) + 아주 약한 비네트
사용법: chika_grade.py <in.mp4> <out.mp4> <report.txt>
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
src, out, report = sys.argv[1:4]
sb = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "chika.json"), encoding="utf-8"))["scenes"]
light = {s["id"]: s["light"] for s in sb}
rep = open(report, encoding="utf-8").read()
T = [(m.group(1), float(m.group(2)), float(m.group(3))) for m in re.finditer(r"^(S\S+):\s+([0-9.]+) ~\s+([0-9.]+)s", rep, re.M)]


def group(lk):
    if lk == "arc_end":
        return "end"
    if lk.startswith("arc") or lk == "cor":
        return "basement"
    if lk in ("bq_cold", "bq_proj"):
        return "bq_cold"
    if lk.startswith("bq"):
        return "bq_warm"
    return "corp"


LUT = {
    "basement": "colorbalance=rs=-0.05:gs=0.02:bs=0.05:rm=-0.03:gm=0.02:bm=0.03,eq=contrast=1.08:saturation=0.90",
    "end": "colorbalance=rs=0.05:gs=0.01:bs=-0.05:rh=0.03:bh=-0.03,eq=contrast=0.97:saturation=1.04",
    "corp": "colorbalance=bs=0.03:bm=0.02,eq=contrast=1.02:saturation=0.95",
    "bq_warm": "colorbalance=rh=0.03:gh=0.01:bh=-0.03:rm=0.02,eq=contrast=1.02:saturation=1.05",
    "bq_cold": "colorbalance=rs=-0.04:bs=0.06:rm=-0.03:bm=0.04,eq=contrast=1.10:saturation=0.90",
}
# 같은 그룹의 연속 장면을 하나의 구간으로 합친다(필터 수 절감)
segs = []
for sid, a, b in T:
    g = group(light.get(sid, "aud"))
    if segs and segs[-1][0] == g and abs(segs[-1][2] - a) < 0.05:
        segs[-1][2] = b
    else:
        segs.append([g, a, b])
# 제11장 15 보강(2026-10-10): 단일 패스 인코딩이 2시간 상한을 넘겨 두 번 중단 → 장면 경계에서 N조각으로 나눠 병렬 인코딩 후 무손실 이어붙임
import math
from concurrent.futures import ThreadPoolExecutor
N = int(os.environ.get("GRADE_CHUNKS", str(max(1, min(4, os.cpu_count() or 1)))))
total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).decode())
bounds = sorted(set([0.0] + [b for _, _, b in T if b < total - 0.5] + [total]))
targets = [total * k / N for k in range(1, N)]
cuts = [0.0] + [min(bounds, key=lambda x: abs(x - t)) for t in targets] + [total]
cuts = sorted(set(cuts))


def vf_for(off):
    vf = []
    for g, a, b in segs:
        for f in LUT[g].split(","):
            name, _, args = f.partition("=")
            vf.append(f"{name}={args}:enable='between(t,{a - off:.3f},{b - off:.3f})'")
    vf += ["vignette=angle=PI/5.5", "noise=alls=5:allf=t+u", "format=yuv420p"]
    return ",".join(vf)


def encode(k):
    a, b = cuts[k], cuts[k + 1]
    part = f"{out}.part{k:02d}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", src, "-vf", vf_for(a), "-map", "0:v", "-an",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-threads", "1" if len(cuts) > 2 else "0", "-r", "24", part], check=True)
    return part


with ThreadPoolExecutor(max_workers=len(cuts) - 1) as pool:
    parts = list(pool.map(encode, range(len(cuts) - 1)))
lst = out + ".concat.txt"
open(lst, "w").write("".join(f"file '{os.path.abspath(p_)}'\n" for p_ in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", src, "-map", "0:v", "-map", "1:a?",
                "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", out], check=True)
for p_ in parts + [lst]:
    os.remove(p_)
print(f"저장: {out} — 구간 {len(segs)}개, 병렬 {len(parts)}조각 {[round(c, 1) for c in cuts]}: " + ", ".join(f"{g} {a:.1f}~{b:.1f}" for g, a, b in segs[:8]) + " …")
