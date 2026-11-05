#!/usr/bin/env python3
"""실감 시계 초침 소리 합성(R48, 2026-11-05 고니감독님 「시계바늘 가는 소리로 전혀 안 느껴짐·너무 빠름 → 째깍째깍 실감 나게」).
실제 기계식 시계: 1초에 한 번, 째(틱)·깍(톡)이 번갈아(음높이 살짝 다름), 한 박마다 탈진기 이중 딸깍(12ms 뒤 작은 두 번째 딸깍),
금속 울림(2.6·4.0·6.1kHz, 감쇠 7ms) + 케이스 울림(190Hz, 12ms) + 아주 옅은 방 반사. 박자 흔들림 ±3ms(기계 느낌).
  wall  = 벽시계(크고 낮음)   watch = 손목시계(작고 높음, 가까이 듣는 소리)
사용법: python3 scripts/make_clock_tick.py <wall|watch> <초> <출력.wav|.mp3>
"""
import subprocess
import sys

import numpy as np

SR = 48000


def click(freqs, amp, rng, tau=0.007, body=190.0):
    n = int(0.06 * SR); t = np.arange(n) / SR
    noise = rng.normal(0, 1, n) * np.exp(-t / 0.0025)
    # 고역 강조(1.5kHz 아래 제거) — 1차 차분
    noise = np.concatenate([[0], np.diff(noise)])
    ring = sum(a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) for f, a in freqs) * np.exp(-t / tau)
    thump = 0.35 * np.sin(2 * np.pi * body * t) * np.exp(-t / 0.012)
    return amp * (0.55 * noise / 3 + ring + thump)


def make(kind, sec, seed=7):
    rng = np.random.default_rng(seed)
    out = np.zeros(int((sec + 0.2) * SR))
    if kind == "wall":
        base = [(2600, 0.5), (4000, 0.35), (6100, 0.2)]; body, amp, tau = 170.0, 0.6, 0.009
    else:
        base = [(3400, 0.5), (5200, 0.35), (7600, 0.22)]; body, amp, tau = 420.0, 0.45, 0.005
    k = 0; t0 = 0.25
    while t0 < sec:
        tock = k % 2 == 1
        fr = [(f * (0.88 if tock else 1.0), a) for f, a in base]
        a = amp * (0.82 if tock else 1.0) * rng.uniform(0.95, 1.05)
        c1 = click(fr, a, rng, tau, body); c2 = click(fr, a * 0.38, rng, tau * 0.8, body)
        i = int(t0 * SR); j = i + int(0.012 * SR)
        out[i:i + len(c1)] += c1[: len(out) - i]
        out[j:j + len(c2)] += c2[: max(len(out) - j, 0)]
        k += 1; t0 += 1.0 + rng.uniform(-0.003, 0.003)
    # 방 반사(아주 옅게) — 18ms·31ms
    for d, g in ((0.018, 0.18), (0.031, 0.10)):
        s = int(d * SR); out[s:] += g * out[:-s]
    out = out / (np.abs(out).max() + 1e-9) * 0.7
    return out[: int(sec * SR)]


if __name__ == "__main__":
    kind, sec, dst = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    x = (make(kind, sec) * 32767).astype(np.int16)
    p = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", "-ar", "44100", dst], input=x.tobytes())
    print(dst)
