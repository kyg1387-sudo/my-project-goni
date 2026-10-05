#!/usr/bin/env python3
"""『柳の葉と一杯の水』 PHASE 6 마무리 (로컬, 무과금).

1) 후크 H1(0:02~0:09): 본편 S24b(회장 「あの日…どこにいる」) 립싱크 구간을 그대로 가져와 얹고(자막 포함),
   남는 시간은 S24b 키프레임 슬로 푸시인으로 잇는다. 음성은 확정 TTS line047을 입 모양 위치에 믹스(후크 BGM은 그 동안 -6dB).
2) 색감 통일: 전편 공통 미세 대비·채도 + 필름 그레인(규격 제8장 6, pro·lite 혼합 소스를 한 영화처럼).
3) 아웃트로 연결: out/yanagi-outro.mp4(+구독 버튼) → append_outro.py(본편 1.0초 페이드아웃 → 검은 화면 0.8초 → 아웃트로 → 엔드카드).
4) 전달본: deliveries/yanagi-final.mp4(28MB 조각) + 480p 미리보기.
사용법: python3 scripts/finalize_yanagi.py <burn 완성본.mp4>
"""
import json
import os
import shutil
import subprocess
import sys

import imageio_ffmpeg

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = imageio_ffmpeg.get_ffmpeg_exe()
OUTD = os.path.join(ROOT, "out")
SB = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "yanagi.json"), encoding="utf-8"))["scenes"]
LOCK = json.load(open(os.path.join(ROOT, "productions", "willow-leaf-ja", "lock.json"), encoding="utf-8"))
AUDIO = json.load(open(os.path.join(ROOT, "scripts", "audio", "yanagi.json"), encoding="utf-8"))


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


def dur(p):
    e = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def bounds():
    d = [float(x) for x in AUDIO["scene_durations"]]
    t, out = 0.0, {}
    for s, x in zip(SB, d):
        out[s["id"]] = (t, t + x); t += x
    return out


def main():
    src = sys.argv[1]
    os.makedirs(OUTD, exist_ok=True)
    B = bounds()
    h0, h1 = B["H1"]; s0, s1 = B["S24b"]
    row = next(r for r in LOCK["rows"] if r["id"] == "line047")
    off = row["start"] - s0                          # S24b 안에서 line047이 시작하는 위치
    seg = s1 - s0
    tmp = os.path.join(OUTD, "fin"); os.makedirs(tmp, exist_ok=True)
    W, H = 1920, 1080
    # 1) 후크 H1 영상: [S24b 립싱크 구간] + [키프레임 푸시인]
    run(["-ss", f"{s0:.3f}", "-i", src, "-t", f"{seg:.3f}", "-an", "-vf", f"scale={W}:{H},fps=24,format=yuv420p",
         "-c:v", "libx264", "-crf", "16", os.path.join(tmp, "h1a.mp4")])
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_yanagi_overrides as ov
    ov.W, ov.H = W, H
    rest = (h1 - h0) - seg
    ov.cam(os.path.join(ROOT, "assets/portraits/yanagi-keyframes/S24b-1.png"), os.path.join(tmp, "h1b.mp4"), rest + 0.1, "push")
    run(["-i", os.path.join(tmp, "h1a.mp4"), "-i", os.path.join(tmp, "h1b.mp4"), "-filter_complex",
         f"[0:v][1:v]concat=n=2:v=1:a=0,trim=0:{h1 - h0:.3f},setpts=PTS-STARTPTS[v]", "-map", "[v]",
         "-c:v", "libx264", "-crf", "16", os.path.join(tmp, "h1.mp4")])
    # 본편에 후크 H1 덮어쓰기 + line047 믹스 + 색감 통일
    v047 = os.path.join(ROOT, "assets/audio-overrides/yanagi/line047.mp3")
    t047 = h0 + off
    l047 = dur(v047)
    grade = "eq=contrast=1.03:saturation=0.96:gamma=0.99,noise=alls=4:allf=t+u"
    fc = (f"[1:v]setpts=PTS-STARTPTS+{h0:.3f}/TB[h];[0:v][h]overlay=enable='between(t,{h0:.3f},{h1:.3f})':eof_action=pass,{grade},format=yuv420p[v];"
          f"[0:a]volume=enable='between(t,{t047 - 0.2:.3f},{t047 + l047 + 0.3:.3f})':volume=0.5[ab];"
          f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={int(t047 * 1000)}|{int(t047 * 1000)}[vo];"
          f"[ab][vo]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[a]")
    main_out = os.path.join(tmp, "main.mp4")
    run(["-i", src, "-i", os.path.join(tmp, "h1.mp4"), "-i", v047, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", main_out])
    # 3) 아웃트로 + 엔드카드
    outro = os.path.join(OUTD, "yanagi-outro.mp4")
    meta = json.load(open(os.path.join(OUTD, "yanagi-outro.json")))
    hs = meta["host_start"][0]
    cta = os.path.join(tmp, "outro-cta.mp4")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), outro, cta,
                    f"{hs + 1.6:.2f}", f"{hs + 2.6:.2f}", f"{meta['host_start'][1] - 0.2:.2f}"], check=True,
                   env={**os.environ, "PATH": os.path.dirname(FF) + os.pathsep + os.environ.get("PATH", "")})
    final = os.path.join(OUTD, "yanagi-final.mp4")
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), main_out, final], check=True, env=env)
    # 4) 전달본
    dd = os.path.join(ROOT, "deliveries", "yanagi"); os.makedirs(dd, exist_ok=True)
    run(["-i", final, "-vf", "scale=-2:480", "-c:v", "libx264", "-crf", "28", "-c:a", "aac", "-b:a", "96k",
         os.path.join(dd, "yanagi-final-480p.mp4")])
    print(f"완성: {final} ({dur(final):.1f}초) / 본편 {dur(main_out):.1f}초 / 아웃트로 {dur(cta):.1f}초")


if __name__ == "__main__":
    main()
