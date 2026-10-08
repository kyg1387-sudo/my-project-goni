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
vf = []
for g, a, b in segs:
    for f in LUT[g].split(","):
        name, _, args = f.partition("=")
        vf.append(f"{name}={args}:enable='between(t,{a:.3f},{b:.3f})'")
vf.append("vignette=angle=PI/5.5")
vf.append("noise=alls=5:allf=t+u")
vf.append("format=yuv420p")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", ",".join(vf), "-map", "0:v", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
print(f"저장: {out} — 구간 {len(segs)}개: " + ", ".join(f"{g} {a:.1f}~{b:.1f}" for g, a, b in segs[:12]) + (" …" if len(segs) > 12 else ""))
