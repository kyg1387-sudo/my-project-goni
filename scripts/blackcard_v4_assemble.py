#!/usr/bin/env python3
"""ブラックカード v4 조립(2026-11-04 고니감독님 지적 반영): v3 완성본 위에 수정 컷(정지 푸시인·합성 클립)을 한 번에 덮고,
결말의 중복 CTA 구간(S12y~S12zz, L108·L109 — 아웃트로 진행자와 중복)을 잘라낸 뒤 아웃트로·엔드카드를 다시 붙이고 리미터.
사용법: blackcard_v4_assemble.py <v3 final.mp4> <body_end 초> <out final.mp4>  (교체 목록은 FIX)
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], "out/blackcard-remix.mp4"] + sys.argv[1:]  # finalize_blackcard가 argv[1]을 remix로 읽음
import finalize_blackcard as fb  # noqa: E402

ROOT = fb.ROOT; OV = os.path.join(ROOT, "assets", "video-overrides", "blackcard")
FIX = {"S04g": "scene49_still.mp4", "S04h": "scene50_still.mp4", "S05f": "scene59_still.mp4", "S06i": "scene74_still.mp4",
       "S07b": "scene78_still.mp4", "S08g": None, "S08l": "scene109_fix.mp4", "S09a": "scene119_still.mp4", "S09e": "scene123_fix.mp4",
       "S10i": "scene135_fix.mp4", "S11a": "scene144_still.mp4", "S11c": "scene146_still.mp4", "S12a": "scene148_fix.mp4",
       "S12d": "scene151_still.mp4", "S12f": "scene153_still.mp4", "S12l": "scene159_still.mp4", "S12m": "scene160_still.mp4",
       "S12n": "scene161_still.mp4", "S12p": "scene162_still.mp4", "S12q": "scene164_still.mp4", "S12s": "scene166_still.mp4"}


def main():
    src, body_end, out = sys.argv[2], float(sys.argv[3]), sys.argv[4]
    B = fb.bounds(); tmp = os.path.join(fb.OUTD, "fin-bc"); os.makedirs(tmp, exist_ok=True)
    inputs, fc, last, k = ["-i", src], [], "[0:v]", 1
    for sid, clip in FIX.items():
        p = os.path.join(tmp, "cut_S08g.mp4") if clip is None else os.path.join(OV, clip)
        if not os.path.exists(p):
            print("없음(건너뜀):", sid, p); continue
        a, b = B[sid]
        inputs += ["-i", p]
        fc.append(f"[{k}:v]trim=0:{b - a + 1 / fb.FPS:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
        print(f"교체 {sid} {a:.2f}-{b:.2f} ← {os.path.basename(p)}"); k += 1
    fc.append(f"{last}trim=0:{body_end:.3f},setpts=PTS-STARTPTS,fade=t=out:st={body_end - 1.0:.3f}:d=1.0,format=yuv420p[v]")
    fc.append(f"[0:a]atrim=0:{body_end:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={body_end - 1.5:.3f}:d=1.5[a]")
    script = os.path.join(tmp, "v4_fc.txt"); open(script, "w").write(";\n".join(fc))
    body = os.path.join(tmp, "main_v4.mp4")
    fb.run(inputs + ["-filter_complex_script", script, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                     "-c:a", "aac", "-b:a", "192k", body])
    print("본편 v4:", body, round(fb.dur(body), 2))
    cta = os.path.join(tmp, "outro-cta.mp4")
    if not os.path.exists(cta):
        meta = json.load(open(os.path.join(fb.OUTD, "blackcard-outro.json"))); hs = meta["host_start"]
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), os.path.join(fb.OUTD, "blackcard-outro.mp4"), cta,
                        f"{hs[1] + 1.0:.2f}", f"{hs[1] + 1.8:.2f}", f"{hs[2] - 0.2:.2f}"], check=True)
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), body, out], check=True, env=env)
    lim = out.replace(".mp4", "_lim.mp4")
    fb.run(["-i", out, "-c:v", "copy", "-af", "alimiter=limit=0.7:attack=3:release=40:level=false", "-c:a", "aac", "-b:a", "192k", lim])
    os.replace(lim, out); os.remove(body)
    print("완성:", out, round(fb.dur(out), 2))


if __name__ == "__main__":
    main()
