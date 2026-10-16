#!/usr/bin/env python3
"""마무리본(out/fin/main.mp4)에 재생성한 컷의 영상만 끼워 넣기(무과금). 음성·자막은 같으므로 영상 트랙만 교체하고 같은 색감 통일을 적용한다.
사용법: splice_tsuki_cut.py <새 burn 완성본.mp4> <컷ID,...> [in=out/fin/main.mp4] [out=out/fin/main.mp4]"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finalize_tsuki as F

src_new, ids = sys.argv[1], sys.argv[2].split(",")
main_in = sys.argv[3] if len(sys.argv) > 3 else os.path.join(F.OUTD, "fin", "main.mp4")
main_out = sys.argv[4] if len(sys.argv) > 4 else main_in
B = F.bounds()
grade = "eq=contrast=1.03:saturation=0.97:gamma=0.99,noise=alls=4:allf=t+u"
inputs, fc, last = ["-i", main_in], [], "[0:v]"
for k, sid in enumerate(ids, start=1):
    a, b = B[sid]
    inputs += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", src_new]
    fc.append(f"[{k}:v]{grade},setpts=PTS-STARTPTS+{a:.3f}/TB[p{k}]")
    fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    print(f"{sid}: {a:.2f}-{b:.2f}")
tmp = main_out + ".tmp.mp4"
F.run(inputs + ["-filter_complex", ";".join(fc), "-map", last, "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy", tmp])
os.replace(tmp, main_out)
print("완료:", main_out)
