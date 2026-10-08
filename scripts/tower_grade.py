#!/usr/bin/env python3
"""『タワマンのボスママ』 회의장 긴장감 그레이딩 + 립싱크 컷 크롭 (무과금, 로컬) — 감독님 지적 2026-10-07
「회의하는데 긴장감도 없고」 → 규격 제8장 1(압박·갑질 = 위에서 떨어지는 차가운 형광등 5600K+, 대면 = 강한 대비).

- 임시총회(S05a~S07c2): 차갑게(그림자·중간톤 청색), 대비 +8%, 채도 −8%, 약한 비네트
- 통상총회 폭로~몰락(S13a~S17i2): 대비 +12%, 채도 −10%, 차갑게, 비네트 조금 강하게
- (폐기) 립싱크 컷 확대 — 번인 자막과 충돌. 립싱크 컷 배경은 재생성(유료)으로만 고칠 수 있다
핸드헬드(미세 흔들림)는 넣지 않는다(감독님 '영상 떨림' 지적 직후 — 떨림으로 보일 수 있음).
시각은 조립 검수 report.txt 장면 경계. 영상만 다시 인코딩, 오디오 복사.
사용법: tower_grade.py <in.mp4> <out.mp4> <report.txt>
"""
import re
import subprocess
import sys

src, out, report = sys.argv[1:4]
rep = open(report, encoding="utf-8").read()
T = {m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(r"^(S\S+):\s+([0-9.]+) ~\s+([0-9.]+)s", rep, re.M)}
A = (T["S05a"][0], T["S07c2"][1])      # 임시총회
B = (T["S13a"][0], T["S17i2"][1])      # 통상총회 폭로~몰락
# 립싱크 컷 확대(빈 의자 가리기)는 시험 결과 폐기: 3줄 자막이 크롭 창 안에 걸려 이중 자막·얼굴 과확대(2026-10-07)
ZOOM = {}
Z = 1.25   # 크롭 창(1536x864)을 화면 위쪽에 붙여 아래 번인 자막(약 y 870~)을 빼고, 확대본 위에 원래 자막을 다시 입힌다

en = lambda a, b: f"enable='between(t,{a:.3f},{b:.3f})'"
vf = [
    f"colorbalance=rs=-0.04:bs=0.06:rm=-0.03:bm=0.04:{en(*A)}",
    f"eq=contrast=1.08:saturation=0.92:{en(*A)}",
    f"vignette=angle=PI/5:{en(*A)}",
    f"colorbalance=rs=-0.05:bs=0.07:rm=-0.03:bm=0.05:{en(*B)}",
    f"eq=contrast=1.12:saturation=0.90:{en(*B)}",
    f"vignette=angle=PI/4.2:{en(*B)}",
]
chain = "[0:v]" + ",".join(vf) + "[g]"
cur = "[g]"
parts = [chain]
for k, (sid, cy) in enumerate(ZOOM.items()):
    a, b = T[sid]; a += 0.04; b -= 0.04
    cw, ch = int(1920 / Z) // 2 * 2, int(1080 / Z) // 2 * 2
    x, y = (1920 - cw) // 2, 0
    parts.append(f"{cur}split[s{k}a][s{k}b];[s{k}b]crop={cw}:{ch}:{x}:{y},scale=1920:1080:flags=lanczos,ass=subs/tower.ass[z{k}];"
                 f"[s{k}a][z{k}]overlay=0:0:{en(a, b)}[o{k}]")
    cur = f"[o{k}]"
fc = ";".join(parts) + f";{cur}format=yuv420p[v]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[v]", "-map", "0:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
print(f"저장: {out} — 임시총회 {A[0]:.1f}~{A[1]:.1f}s, 통상총회 {B[0]:.1f}~{B[1]:.1f}s 그레이딩, 립싱크 {len(ZOOM)}컷 확대")
