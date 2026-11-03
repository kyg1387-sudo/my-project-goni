#!/usr/bin/env python3
"""효과음 후보 청취 파일(제20장 10 ②): 폴더의 <이름>-N.mp3를 이름 순으로 −6 dB 피크 정규화해 0.8초 간격으로 잇고,
각 클립 앞에 이름을 읽는 대신 순서표를 출력한다. 1안(prompt_influence 0.6)을 잠정 선택으로 _picks_prelim.json에 적는다.
사용법: sfx_review_file.py <폴더> [제외이름,…]
"""
import json
import os
import re
import subprocess
import sys


def peak_db(p):
    e = subprocess.run(["ffmpeg", "-v", "info", "-i", p, "-af", "astats=measure_overall=Peak_level:measure_perchannel=0", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.findall(r"Peak level dB:\s*(-?[\d.]+)", e)
    return float(m[-1]) if m else 0.0


def main():
    d = sys.argv[1]; skip = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else set()
    files = sorted(f for f in os.listdir(d) if f.endswith(".mp3") and not f.startswith("_"))
    names = sorted({re.sub(r"-\d+\.mp3$", "", f) for f in files} - skip)
    inputs, fc, k, order = [], [], 0, []
    for n in names:
        for f in [x for x in files if re.sub(r"-\d+\.mp3$", "", x) == n]:
            p = os.path.join(d, f); inputs += ["-i", p]
            fc.append(f"[{k}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={-6 - peak_db(p):.2f}dB,apad=pad_dur=0.8[s{k}]")
            order.append(f); k += 1
    fc.append("".join(f"[s{i}]" for i in range(k)) + f"concat=n={k}:v=0:a=1[a]")
    out = os.path.join(d, "_review_all.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", "[a]", "-b:a", "160k", out], check=True)
    picks = {n: f"{n}-1.mp3" for n in names}
    picks["_잠정"] = "1안(prompt_influence 0.6) 잠정 — 고니감독님 청취로 확정"
    json.dump(picks, open(os.path.join(d, "_picks_prelim.json"), "w"), ensure_ascii=False, indent=1)
    t = 0.0
    for f in order:
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(d, f)]))
        print(f"{t:6.1f}s  {f}"); t += dur + 0.8
    print("저장:", out, f"{t:.1f}s")


if __name__ == "__main__":
    main()
