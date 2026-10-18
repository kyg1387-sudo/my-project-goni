#!/usr/bin/env python3
"""검수용 영상: 완성본 위에 한글 자막(subs/chika-ko.ass)을 추가로 입힌다(일본어 자막 위, 작게). 업로드본이 아니라 검수 전용.
사용법: review_ko.py <in.mp4> <out.mp4> [subs/chika-ko.ass]"""
import subprocess, sys
src, out = sys.argv[1:3]; ass = sys.argv[3] if len(sys.argv) > 3 else "subs/chika-ko.ass"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"ass={ass}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
print("저장:", out)
