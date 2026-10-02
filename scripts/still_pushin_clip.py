#!/usr/bin/env python3
"""키프레임 1장 → 슬로 푸시인(1.00→1.05) 정지 클립 (규격 승인 모션: slow cinematic push-in).
i2v 변환이 소품을 변형시키는 컷의 폴백. 사용법: still_pushin_clip.py <keyframe.png> <out.mp4> <seconds>
"""
import subprocess, sys
src, out, sec = sys.argv[1], sys.argv[2], float(sys.argv[3])
fps, frames = 24, int(round(float(sys.argv[3]) * 24))
# 4배 업스케일 후 zoompan으로 서브픽셀 줌(떨림 방지), 1280x720 24fps
vf = (f"scale=5120:2880,zoompan=z='1+0.05*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
      f":d={frames}:s=1280x720:fps={fps},format=yuv420p")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", src, "-vf", vf, "-t", f"{sec}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-an", out], check=True)
print("저장:", out)
