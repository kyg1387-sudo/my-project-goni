#!/usr/bin/env python3
"""완성본 뒤에 공통 아웃트로(진행자 구독·좋아요 멘트, assets/auditions/outro-host/OUTRO-SCENE.mp4)를 붙인다.
본편 끝 0.5초 디졸브 + 오디오 크로스페이드, 1280x720 24fps로 정규화. 사용법: append_outro.py <final.mp4> <out.mp4>
"""
import subprocess, sys
src, out = sys.argv[1], sys.argv[2]
outro = "assets/auditions/outro-host/OUTRO-SCENE.mp4"
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).decode())
d0, d1, xf = dur(src), dur(outro), 0.5
fc = (f"[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1,format=yuv420p[v0];"
      f"[1:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1,format=yuv420p[v1];"
      f"[v0][v1]xfade=transition=fade:duration={xf}:offset={d0-xf:.3f}[v];"
      f"[0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0];[1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1];"
      f"[a0][a1]acrossfade=d={xf}[a]")
subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-i",outro,"-filter_complex",fc,"-map","[v]","-map","[a]",
                "-c:v","libx264","-preset","medium","-crf","18","-c:a","aac","-b:a","192k",out], check=True)
print(f"저장: {out} ({d0:.1f}s + 아웃트로 {d1:.1f}s)")
