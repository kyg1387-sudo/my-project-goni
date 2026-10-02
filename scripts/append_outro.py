#!/usr/bin/env python3
"""완성본 뒤에 공통 아웃트로(진행자 구독·좋아요 멘트, assets/auditions/outro-host/OUTRO-SCENE.mp4)를 붙인다.
본편과 아웃트로를 명확히 구분: 본편 끝 1.0초 페이드아웃(영상·소리) → 검은 화면 0.8초 → 아웃트로 0.5초 페이드인.
1280x720 24fps 44.1kHz 스테레오로 정규화. 사용법: append_outro.py <final.mp4> <out.mp4>
"""
import subprocess, sys
src, out = sys.argv[1], sys.argv[2]
outro = "assets/auditions/outro-host/OUTRO-SCENE.mp4"
endcard = "assets/brand/endcard-midam.mp4"  # 채널 엔드카드(5.5s, 자체 음악 베드) — 아웃트로 뒤 0.6s 크로스페이드로 이어짐
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).decode())
d0, d1 = dur(src), dur(outro)
FO, GAP, FI = 1.0, 0.8, 0.5
norm = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1,format=yuv420p"
fc = (f"[0:v]{norm},fade=t=out:st={d0-FO:.3f}:d={FO}[v0];"
      f"[0:a]aformat=sample_rates=44100:channel_layouts=stereo,afade=t=out:st={d0-FO:.3f}:d={FO}[a0];"
      f"color=c=black:s=1280x720:r=24:d={GAP}[vg];anullsrc=r=44100:cl=stereo:d={GAP}[ag];"
      f"[1:v]{norm},fade=t=in:st=0:d={FI}[v1];"
      f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,afade=t=in:st=0:d={FI}[a1];"
      f"[2:v]{norm}[v2];[2:a]aformat=sample_rates=44100:channel_layouts=stereo[a2];"
      f"[v1][v2]xfade=transition=fade:duration=0.6:offset={d1-0.6:.3f}[v12];[a1][a2]acrossfade=d=0.6[a12];"
      f"[v0][a0][vg][ag][v12][a12]concat=n=3:v=1:a=1[v][a]")
subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-i",outro,"-i",endcard,"-filter_complex",fc,"-map","[v]","-map","[a]",
                "-c:v","libx264","-preset","medium","-crf","18","-c:a","aac","-b:a","192k",out], check=True)
print(f"저장: {out} (본편 {d0:.1f}s + 검은 화면 {GAP}s + 아웃트로 {d1:.1f}s + 엔드카드 {dur(endcard):.1f}s, 겹침 0.6s)")
