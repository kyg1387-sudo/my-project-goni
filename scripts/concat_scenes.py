#!/usr/bin/env python3
"""장면 클립들을 동일 규격으로 정규화해 이어붙인다.

- 1280x720 / 24fps 통일, 화면비 유지 + 패딩 (찌그러짐 방지)
- 장면 파일(JSON)의 계획 길이(duration)로 각 클립을 정확히 자름
  (생성 클립이 몇 프레임 길 때 생기는 자막·음성 누적 오차 방지;
  짧은 클립은 마지막 프레임을 늘려 채움)

사용법: python3 scripts/concat_scenes.py <scenes.json> <클립 폴더> <출력.mp4>
"""

import glob
import json
import os
import subprocess
import sys


def main():
    scenes_json, clips_dir, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(scenes_json, encoding="utf-8") as f:
        data = json.load(f)
    default_dur = int(data.get("duration", 5))
    durations = [int(s.get("duration", default_dur)) if isinstance(s, dict) else default_dur
                 for s in data["scenes"]]

    clips = sorted(glob.glob(os.path.join(clips_dir, "scene*.mp4")))
    if len(clips) != len(durations):
        sys.exit(f"클립 {len(clips)}개 != 계획 장면 {len(durations)}개")

    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-i", c]
    parts = []
    for k, d in enumerate(durations):
        parts.append(f"[{k}:v]scale=1280:720:force_original_aspect_ratio=decrease,"
                     f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1,"
                     f"tpad=stop_mode=clone:stop_duration=15,trim=duration={d},"
                     f"setpts=PTS-STARTPTS[v{k}]")
    parts.append("".join(f"[v{k}]" for k in range(len(clips)))
                 + f"concat=n={len(clips)}:v=1:a=0[vc]")
    script = os.path.join(clips_dir, "concat_filter.txt")
    with open(script, "w") as f:
        f.write(";\n".join(parts))
    cmd += ["-filter_complex_script", script, "-map", "[vc]", "-an",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", out_path]
    subprocess.run(cmd, check=True)
    print(f"완료 → {out_path} ({len(clips)}개 장면, 총 {sum(durations)}초)")


if __name__ == "__main__":
    main()
