#!/usr/bin/env python3
"""#02 최종 마스터링(03_시네마규격 audio_engineering, 규격 PHASE 6) — 무과금, 로컬.
loudnorm 2패스 −14 LUFS / TP −1.0 dBTP / LRA 11, 내레이션 대역(1~3kHz) BGM 충돌은 조립 단계 BGM 볼륨으로 이미 낮춤.
사용법: chika_master.py <in.mp4> <out.mp4>"""
import json, re, subprocess, sys
src, out = sys.argv[1:3]
p = subprocess.run(["ffmpeg", "-v", "info", "-i", src, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True)
m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S); st = json.loads(m.group(0))
af = (f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:measured_LRA={st['input_lra']}"
      f":measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true:print_format=summary")
# 제11장 13(2026-10-09): 룸톤 베드 — BGM 구간 사이 페이드 공백(#02 1차 조립: 24~30s·281~286s·410~412s)이 −60dB 이하
# 2초 이상 완전 무음으로 남아 규격(제6장 4) 위반. 전편에 약 −52dBFS RMS 수준의 저역 룸톤(갈색 잡음+저역 통과)을 깔아 인공 적막을 없앤다.
ROOM_TONE_DB = -30
fc = (f"[1:a]lowpass=f=900,highpass=f=60,volume={ROOM_TONE_DB}dB[rt];"
      f"[0:a][rt]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mixed];"
      f"[mixed]{af}[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-f", "lavfi", "-i", "anoisesrc=color=brown:sample_rate=48000:amplitude=0.5:seed=7",
                "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-ar", "48000", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", out], check=True)
print(f"저장: {out} — 입력 {st['input_i']} LUFS / TP {st['input_tp']} → 목표 −14 LUFS / TP −1.0")
