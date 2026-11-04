#!/usr/bin/env python3
"""완성본 위에 교체 클립(정지·fix)을 컷 시각에 overlay하고 자막을 절대 시각으로 다시 굽는다(제20장 17 ④). 오디오는 복사.
사용법: blackcard_patch_cuts.py <in.mp4> <out.mp4> <SID=clip.mp4|SID=!clip.mp4> [...]   (clip은 assets/video-overrides/blackcard/ 기준, "!"는 자막이 이미 구워진 클립 → ass 생략)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], "out/blackcard-remix.mp4"] + sys.argv[1:]
import finalize_blackcard as fb  # noqa: E402

src, out, pairs = sys.argv[2], sys.argv[3], sys.argv[4:]
B = fb.bounds(); OV = os.path.join(fb.ROOT, "assets", "video-overrides", "blackcard")
ass = os.path.join(fb.ROOT, "subs", "blackcard-v4.ass"); fdir = os.environ.get("FONTSDIR", "/usr/share/fonts")
inputs, fc, last, k = ["-i", src], [], "[0:v]", 1
for pr in pairs:
    sid, clip = pr.split("="); nosub = clip.startswith("!"); clip = clip.lstrip("!"); a, b = B[sid]; p = os.path.join(OV, clip); assert os.path.exists(p), p
    inputs += ["-i", p]
    sub = "" if nosub else f",ass={ass}:fontsdir={fdir}"
    fc.append(f"[{k}:v]trim=0:{b - a + 1 / fb.FPS:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB{sub}[p{k}]")
    fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    print(f"교체 {sid} {a:.2f}-{b:.2f} ← {clip}"); k += 1
fc.append(f"{last}format=yuv420p[v]")
script = os.path.join(fb.OUTD, "fin-bc", "patch_fc.txt"); os.makedirs(os.path.dirname(script), exist_ok=True); open(script, "w").write(";\n".join(fc))
fb.run(inputs + ["-filter_complex_script", script, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "copy", out])
print("완성:", out, round(fb.dur(out), 2))
