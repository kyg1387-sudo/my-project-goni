#!/usr/bin/env python3
"""완성본 영상을 장면 클립들로 다시 잘라낸다 (Artifact 만료 시 무과금 복구용).

완성본(자막 구움·오디오 포함)을 장면 수만큼 균등 분할해 out/sceneNN.mp4
(영상 전용, 오디오 제거)로 저장한다. 자막이 이미 구워져 있으므로 이후 조립은
--no-burn 모드로 진행하고, 교체된(자막 없는) 새 클립에만 개별 자막을 입힌다.

사용법: python3 scripts/slice_scenes.py <완성본.mp4> <scenes.json> <출력폴더>
"""

import json
import os
import subprocess
import sys


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main():
    video, scenes_json, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    data = json.load(open(scenes_json, encoding="utf-8"))
    default_dur = int(data.get("duration", 5))
    # 장면별 길이(5/10초 혼용)가 있으면 그 비율대로, 없으면 균등 분할
    weights = [int(s.get("duration", default_dur)) if isinstance(s, dict) else default_dur
               for s in data["scenes"]]
    n = len(weights)
    total = probe_duration(video)
    unit = total / sum(weights)
    os.makedirs(outdir, exist_ok=True)
    print(f"{video} ({total:.2f}s) → 장면 {n}개 (기준 {unit * default_dur:.3f}s/{default_dur}s 장면)")
    t = 0.0
    for k, w in enumerate(weights):
        seg = unit * w
        out = os.path.join(outdir, f"scene{k + 1:02d}.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", video,
             "-t", f"{seg:.3f}", "-an",
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", out],
            check=True, capture_output=True)
        print(f"  scene{k + 1:02d}.mp4 ({seg:.2f}s)")
        t += seg
    print("슬라이스 완료")


if __name__ == "__main__":
    main()
