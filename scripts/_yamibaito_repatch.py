#!/usr/bin/env python3
"""finalize 산출 main.mp4 위에 수정분만 다시 얹는다(전체 재실행 없이): S11m 자막 재굽기 + 시점 소자막 강화 → main_fix.mp4 → 아웃트로·엔드카드."""
import os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import finalize_yamibaito as F
B = F.bounds(); tmp = os.path.join(F.OUTD, "fin"); fdir = os.path.join(F.ROOT, "scripts", "fonts")
src = os.path.join(tmp, "main.mp4"); out = os.path.join(tmp, "main_fix.mp4")
inputs, fc, last, k = ["-i", src], [], "[0:v]", 0
for sid, clip in F.CLIPS:
    a, b = B[sid]; k += 1; inputs += ["-i", os.path.join(F.ROOT, clip)]
    fc.append(f"[{k}:v]scale={F.W}:{F.H},trim=0:{b - a:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={F.ASS}:fontsdir={fdir}[p{k}]")
    fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
for sid, text in F.CAPTIONS.items():
    a = B[sid][0] + 0.3; b = a + 2.4; png = os.path.join(tmp, f"cap2_{sid}.png"); F.caption_png(text, png)
    k += 1; inputs += ["-loop", "1", "-framerate", str(F.FPS), "-t", f"{b - a + 0.1:.2f}", "-i", png]
    fc.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1,fade=t=out:st={b - a - 0.4:.2f}:d=0.4:alpha=1,setpts=PTS+{a:.3f}/TB[c{k}]")
    fc.append(f"{last}[c{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
fc.append(f"{last}format=yuv420p[v]")
F.run(inputs + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "copy", out])
print("재패치:", out, round(F.dur(out), 2))
F.outro(out, tmp)
