#!/usr/bin/env python3
"""#03 『老舗旅館の嫁』 최종 마스터링(chika_master.py 구조)(03_시네마규격 audio_engineering, 규격 PHASE 6) — 무과금, 로컬.
loudnorm 2패스 −14 LUFS / TP −1.0 dBTP / LRA 11, 내레이션 대역(1~3kHz) BGM 충돌은 조립 단계 BGM 볼륨으로 이미 낮춤.
사용법: ryokan_master.py <in.mp4> <out.mp4>"""
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
# 제11장 22(2026-10-09, 외부 검수 「효과음 0개」): 설계 효과음(scripts/audio/chika.json _효과음) + 추가 큐를 ElevenLabs 생성 소스로 타임코드 믹스
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SFX_DIR = os.path.join(ROOT, "assets", "auditions", "ryokan-sfx")
# #03: 효과음 소스 id = 설계 kind 이름 그대로(scripts/auditions/ryokan-sfx.json). 레벨(dBFS 상대) — 대사 구간은 −6dB 추가(제11장 22)
KIND = {k: (k, db) for k, db in {"handset_creak": -20, "phone_set_down": -18, "fluorescent_on": -20, "knife_on_board": -20, "lamp_switch": -22,
        "wiping_stop": -20, "teacup_click": -16, "fan_snap": -15, "binder_drop": -14, "phone_notify": -18, "notify_triple": -16, "bass_hit": -12,
        "phone_ring": -16, "handset_drop": -8, "riser": -10, "pen_scratch": -20, "bus_airbrake": -18, "phone_vibrate2": -18, "phone_vibrate3": -18,
        "taxi_door": -17, "phone_face_down": -18, "distant_laughter_no_words": -22}.items()}
# 환경 보강 큐(사운드 설계서): 의자 삐걱·발소리·장지문·빗소리
LOCK_SHIFT = float(os.environ.get("LOCK_SHIFT", "0"))   # 2026-10-20 line071 재녹음으로 Lock이 +1.13초 밀림(line001 이후) → 손큐 보정
EXTRA = [(t + LOCK_SHIFT, k, db) for t, k, db in [(78.0, "chair_creak", -24), (147.0, "footsteps_tatami", -24), (160.5, "shoji_slide", -22), (352.0, "rain_roof", -20), (387.0, "chair_creak", -24)]]
# 시청자 검증 수정(2026-10-19): 조립 후 로컬 트림 구간(원본 타임코드) — 효과음 큐를 같은 만큼 당긴다
TRIMS = [tuple(float(v) for v in t.split("-")) for t in os.environ.get("TRIMS", "").split(",") if t]
def shift(t):
    for a, b in TRIMS:
        if a <= t < b:
            return None
    return t - sum(b - a for a, b in TRIMS if b <= t)
cues = []
try:
    cfg = json.load(open(os.path.join(ROOT, "scripts", "audio", "ryokan.json"), encoding="utf-8"))
    for c in cfg.get("_효과음", []):
        f, db = KIND.get(c["kind"], (None, None))
        if f:
            cues.append((float(c["at"]), f, db))
except FileNotFoundError:
    pass
cues += EXTRA
cues = [(shift(t), f, db) for t, f, db in cues]; cues = [(t, f, db) for t, f, db in cues if t is not None]
cues = [(t, f, db) for t, f, db in cues if os.path.exists(os.path.join(SFX_DIR, f + ".mp3"))]
DRONE = [(shift(394.3), 5.2)]   # (시작, 길이) — S13g 수화기 낙하 뒤 BGM 공백: 저역 드론이 0.8초에 차올라 끝에서 빠진다
DRONE = [(t, d) for t, d in DRONE if t is not None]
inputs = ["-i", src, "-f", "lavfi", "-i", "anoisesrc=color=brown:sample_rate=48000:amplitude=0.5:seed=7"]
parts = [f"[1:a]lowpass=f=900,highpass=f=60,volume={ROOM_TONE_DB}dB[rt]"]
labels = ["[0:a]", "[rt]"]
for j, (t, d) in enumerate(DRONE):
    inputs += ["-f", "lavfi", "-t", f"{d:.2f}", "-i", "sine=frequency=46:sample_rate=48000"]
    k = sum(1 for x in inputs if x == "-i") - 1
    parts.append(f"[{k}:a]aformat=channel_layouts=stereo,tremolo=f=0.6:d=0.4,lowpass=f=120,afade=t=in:d=0.8,afade=t=out:st={d - 1.2:.2f}:d=1.2,volume=-27dB,adelay={int(t * 1000)}:all=1[dr{j}]")
    labels.append(f"[dr{j}]")
for k, (t, f, db) in enumerate(cues):
    inputs += ["-i", os.path.join(SFX_DIR, f + ".mp3")]
    idx = sum(1 for x in inputs if x == "-i") - 1
    parts.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={db}dB,adelay={int(t * 1000)}:all=1[s{k}]")
    labels.append(f"[s{k}]")
fc = ";".join(parts) + f";{''.join(labels)}amix=inputs={len(labels)}:duration=first:dropout_transition=0:normalize=0[mixed];[mixed]{af}[a]"
print(f"효과음 {len(cues)}개 믹스: " + ", ".join(f"{t:.1f}s {f}" for t, f, _ in sorted(cues)))
subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-ar", "48000", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], check=True)
print(f"저장: {out} — 입력 {st['input_i']} LUFS / TP {st['input_tp']} → 목표 −14 LUFS / TP −1.0")
