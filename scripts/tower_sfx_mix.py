#!/usr/bin/env python3
"""『タワマンのボスママ』 효과음 합성·믹스 (무과금, 로컬) — 규격 제6장 4(−60dB 2초 이상 무음 금지), 제1장 PHASE 6.

generate_audio.py는 효과음 목록(scripts/audio/tower.json의 `_효과음`, 메모 키)을 읽지 않는다(조립 검수 2026-10-07:
스크린 쌍 ドン 누락, S14e~S14h 7초 디지털 무음). 완성본 오디오 위에 합성 효과음을 얹는다(영상은 그대로 복사).
  don        일본 예능식 저음 임팩트(タイコ風: 120→45Hz 스윕 + 저역 노이즈 버스트)
  heartbeat  심장 박동(lub-dub, 70bpm) — 구간 지정
  close      엘리베이터 문 닫힘(공기 소리 + 둔탁한 닿음)
  pen        종이 위 펜 긋기(고역 노이즈 변조)
  stamp      도장(짧은 둔탁음 + 종이 탁)
  room       방 공기음(저역 필터 노이즈, 아주 작게) — 음악 공백 메우기
사용법: tower_sfx_mix.py <in.mp4> <out.mp4>
"""
import subprocess
import sys

import numpy as np

SR = 44100
rng = np.random.default_rng(11)
# (종류, 시작, 길이/옵션, 음량 dBFS 최대값) — 시각은 본편(569.5s) 기준, lock·report.txt 장면 경계에서
EVENTS = [
    ("close", 11.10, 1.2, -20),     # S01d 문 닫힘(엘리베이터)
    ("don", 35.30, 1.4, -11),       # S01i 타이틀 『タワマンのボスママ』
    ("pen", 250.40, 1.6, -30),      # S10a 빨간 펜 동그라미
    ("don", 256.00, 1.4, -11),      # 「二千四百万円」 강조
    ("don", 363.05, 1.2, -12),      # 스크린 쌍 ①
    ("don", 366.25, 1.2, -12),      # 스크린 쌍 ②
    ("don", 369.45, 1.6, -10),      # 스크린 쌍 ③(정지) — BGM 차단
    ("heartbeat", 369.70, 6.40, -16),  # 3분할·ざわ… 동안 심장 박동(무음 메움)
    ("room", 369.30, 6.80, -48),
    ("stamp", 468.20, 0.5, -14),    # 「家賃滞納」 Stamp
    ("room", 514.60, 3.30, -46),    # S17i2→S17-2a 음악 공백
]


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x):
        s = (1 - a) * v + a * s; y[i] = s
    return y


def don(sec):
    n = int(sec * SR); t = np.arange(n) / SR
    f = 45 + 75 * np.exp(-t / 0.08)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.45)
    hit = lowpass(rng.normal(0, 1, n), 900) * env(n, 0.001, 0.05) * 1.5
    sub = np.sin(2 * np.pi * 38 * t) * env(n, 0.01, 0.7) * 0.6
    return body + hit + sub


def heartbeat(sec):
    n = int(sec * SR); x = np.zeros(n); beat = 60 / 70
    for k in np.arange(0, sec, beat):
        for off, f, g in ((0.0, 58, 1.0), (0.24, 52, 0.7)):
            i = int((k + off) * SR); m = min(int(0.18 * SR), n - i)
            if m <= 0:
                continue
            tt = np.arange(m) / SR
            x[i:i + m] += g * np.sin(2 * np.pi * f * tt) * env(m, 0.004, 0.06)
    fade = np.minimum(1, np.arange(n) / (0.4 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.6 * SR))
    return lowpass(x, 300) * fade


def close(sec):
    n = int(sec * SR); t = np.arange(n) / SR
    air = lowpass(rng.normal(0, 1, n), 1800) * np.sin(np.pi * np.clip(t / (sec * 0.8), 0, 1)) * 0.4
    i = int(sec * 0.78 * SR); m = n - i
    thud = np.zeros(n); thud[i:] = np.sin(2 * np.pi * 70 * np.arange(m) / SR) * env(m, 0.002, 0.08)
    return air + thud


def pen(sec):
    n = int(sec * SR); t = np.arange(n) / SR
    hiss = rng.normal(0, 1, n); hiss = hiss - lowpass(hiss, 2500)
    mod = 0.5 + 0.5 * np.sin(2 * np.pi * 7 * t) ** 2
    return hiss * mod * np.sin(np.pi * t / sec) * 0.6


def stamp(sec):
    n = int(sec * SR)
    slap = lowpass(rng.normal(0, 1, n), 3000) * env(n, 0.0005, 0.018)
    body = np.sin(2 * np.pi * 95 * np.arange(n) / SR) * env(n, 0.001, 0.07)
    return slap + body


def room(sec):
    n = int(sec * SR); x = lowpass(lowpass(rng.normal(0, 1, n), 400), 400)
    fade = np.minimum(1, np.arange(n) / (0.5 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.5 * SR))
    return x * fade


GEN = {"don": don, "heartbeat": heartbeat, "close": close, "pen": pen, "stamp": stamp, "room": room}


def main():
    src, out = sys.argv[1], sys.argv[2]
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).decode())
    track = np.zeros(int(total * SR) + SR)
    for kind, at, sec, db in EVENTS:
        x = GEN[kind](sec); x = x / (np.abs(x).max() + 1e-9) * 10 ** (db / 20)
        i = int(at * SR); track[i:i + len(x)] += x[:len(track) - i]
    wav = out + ".sfx.wav"
    pcm = (np.clip(track, -1, 1) * 32767).astype(np.int16)
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", wav], input=stereo.tobytes(), check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", wav, "-filter_complex",
                    "[0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0];[1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1];"
                    "[a0][a1]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print(f"저장: {out} (효과음 {len(EVENTS)}개)")


if __name__ == "__main__":
    main()
