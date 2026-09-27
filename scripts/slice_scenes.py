#!/usr/bin/env python3
"""완성본 영상을 장면 클립들로 프레임 정밀 분할한다 (무과금 복구/재조립용).

균등 시간 분할 대신 총 프레임 수를 기준으로 경계를 프레임 단위로 계산해
segment muxer로 한 번에 자른다 — 반복 분할 시 경계 밀림/중복 프레임을 방지.

사용법: python3 scripts/slice_scenes.py <완성본.mp4> <scenes.json> <출력폴더>
"""

import json
import os
import subprocess
import sys


def probe(path, entries, stream="v:0"):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", stream,
         "-count_frames", "-show_entries", entries,
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return out.stdout.strip().splitlines()


def main():
    video, scenes_json, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    n = len(json.load(open(scenes_json, encoding="utf-8"))["scenes"])
    total_frames = int(probe(video, "stream=nb_read_frames")[0])
    boundaries = [round(k * total_frames / n) for k in range(1, n)]
    os.makedirs(outdir, exist_ok=True)
    print(f"{video} ({total_frames}프레임) → {n}개 장면, 경계 {boundaries[:5]}...")
    tmp = os.path.join(outdir, "part%03d.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-i", video, "-an",
         "-f", "segment", "-segment_frames", ",".join(map(str, boundaries)),
         "-reset_timestamps", "1", "-force_key_frames",
         "expr:eq(n," + ")+eq(n,".join(map(str, boundaries)) + ")",
         "-c:v", "libx264", "-preset", "fast", "-crf", "18", tmp],
        check=True, capture_output=True)
    for k in range(n):
        src = os.path.join(outdir, f"part{k:03d}.mp4")
        dst = os.path.join(outdir, f"scene{k + 1:02d}.mp4")
        os.replace(src, dst)
        print(f"  scene{k + 1:02d}.mp4")
    print("프레임 정밀 슬라이스 완료")


if __name__ == "__main__":
    main()
