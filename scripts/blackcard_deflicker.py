#!/usr/bin/env python3
"""ブラックカード v6: S09·S10(밤 사무실, 항공장애등 red pulse 구간)의 프레임 교대 밝기(12 Hz 깜박임, 제20장 11)를 컷 단위 deflicker로 제거.
원인: finalize의 red pulse(blend all_expr + enable)가 프레임마다 밝기를 ±2/255 교대로 바꿈(원본 omni 클립은 교대 0). 컷 경계를 넘지 않도록 컷마다 잘라 deflicker=size=5:mode=pm 뒤 같은 시각에 overlay.
사용법: blackcard_deflicker.py <in.mp4> <out.mp4>
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], "out/blackcard-remix.mp4"] + sys.argv[1:]
import finalize_blackcard as fb  # noqa: E402

src, out = sys.argv[2], sys.argv[3]
B = fb.bounds(); tmp = os.path.join(fb.OUTD, "fin-bc", "dfl"); os.makedirs(tmp, exist_ok=True)
cuts = [(k, a, b) for k, (a, b) in B.items() if k.startswith(("S09", "S10"))]
inputs, fc, last, i = ["-i", src], [], "[0:v]", 1
for k, a, b in cuts:
    p = os.path.join(tmp, f"{k}.mp4")
    if not os.path.exists(p):
        fb.run(["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", src, "-an", "-vf", "deflicker=size=5:mode=pm", "-c:v", "libx264", "-crf", "15", "-preset", "fast", p])
    inputs += ["-i", p]
    fc.append(f"[{i}:v]setpts=PTS-STARTPTS+{a:.3f}/TB[d{i}]")
    fc.append(f"{last}[d{i}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{i}]"); last = f"[o{i}]"; i += 1
fc.append(f"{last}format=yuv420p[v]")
script = os.path.join(tmp, "fc.txt"); open(script, "w").write(";\n".join(fc))
fb.run(inputs + ["-filter_complex_script", script, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "copy", out])
print("완성:", out, len(cuts), "컷 deflicker")
