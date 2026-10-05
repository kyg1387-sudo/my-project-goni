#!/usr/bin/env python3
"""『柳の葉と一杯の水』 아웃트로(약 28초) 조립 — 규격 제7장 10 (로컬, 무과금).

구성: ① 하이라이트 몽타주(본편 정지 컷 5개 x 1.8초, 편집 카메라) + 진행자 인사 line075
      ② 진행자 CU 립싱크 omni-076(구독·좋아요 부탁) — 버튼 합성(outro_cta_overlay.py)
      ③ 허리 위 립싱크 omni-077(다음 화 예고)  ④ 손 흔들기 립싱크 omni-078(마무리)
음악: outro-bed(lyria2, 보컬 없음)를 전 구간 -20dB 베드로, 끝 1.5초 페이드아웃. 컷 사이 0.4초 디졸브.
자막: 진행자 대사를 일본어 자막(본편 Caption과 같은 글꼴 계열)으로 입힌다.
입력: assets/auditions/yanagi-outro/{omni-076,omni-077,omni-078}.mp4, outro-bed.mp3, line075(yanagi-tts)
출력: out/yanagi-outro.mp4 (1920x1080 24fps, 44.1kHz 스테레오)
사용법: python3 scripts/build_yanagi_outro.py
"""
import json
import os
import subprocess
import tempfile

import imageio_ffmpeg

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = imageio_ffmpeg.get_ffmpeg_exe()
A = os.path.join(ROOT, "assets", "auditions", "yanagi-outro")
A2 = os.path.join(ROOT, "assets", "auditions", "yanagi-outro-slow")  # 감독님 지적(말이 빠름·전환 끊김) 반영: tempo 0.88 재녹음
HOLD = 0.8   # 진행자 컷 끝 정지(입 다문 채) — 다음 컷 디졸브가 말소리 위에 걸리지 않게
KF = os.path.join(ROOT, "assets", "portraits", "yanagi-keyframes")
OUT = os.path.join(ROOT, "out", "yanagi-outro.mp4")
W, H, FPS = 1920, 1080, 24
MONTAGE = [("S08b", "push"), ("S26h", "push"), ("S27e", "pull"), ("S28j2", "push"), ("S29b", "push")]  # 베풂 → 눈물 → 응징 → 재회 → 여운
SEG = 2.4   # 몽타주 컷 길이(디졸브 0.6초 포함 시 실제 노출 약 2.4초)
XF = 0.6
LINES = {
    "075": "最後までご覧いただき、ありがとうございました。",
    "076": "心に残る物語でしたら、高評価とチャンネル登録で\\N応援していただけると嬉しいです。",
    "077": "次回も、時代を超えて人の心を温める、\\N優しさと絆の物語をお届けします。",
    "078": "それでは、また次のお話で。",
}
FONT = "Noto Sans CJK JP"


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


def dur(p):
    e = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def norm(src, out, sec=None, extra=""):
    t = ["-t", f"{sec:.3f}"] if sec else []
    run(["-i", src] + t + ["-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p,setsar=1{extra}",
                           "-c:v", "libx264", "-crf", "17", "-an", out])


def main():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_yanagi_overrides as ov
    ov.W, ov.H = W, H
    tmp = tempfile.mkdtemp()
    parts = []
    for i, (sid, fx) in enumerate(MONTAGE):
        p = os.path.join(tmp, f"m{i}.mp4"); ov.cam(os.path.join(KF, f"{sid}-1.png"), p, SEG + XF, fx); parts.append(p)
    hosts = []
    for n in ("076", "077", "078"):
        p = os.path.join(tmp, f"h{n}.mp4")
        # 마지막 손 흔들기는 끝 프레임을 2.4초 머금어 여운(엔드카드로 넘어가기 전 끊김 방지)
        norm(os.path.join(A2, f"omni-{n}s.mp4"), p, extra=f",tpad=stop_mode=clone:stop_duration={HOLD}"); hosts.append(p)
    # 마지막: 손 흔드는 키프레임(OmniHuman은 손을 내려 버림) 2.6초 슬로 푸시인 — 엔드카드 전 여운
    wave = os.path.join(tmp, "wave.mp4")
    ov.cam(os.path.join(ROOT, "assets/portraits/yanagi-host/host-wave-1.png"), wave, 2.6 + XF, "push")
    clips = parts + hosts + [wave]
    lens = [dur(c) for c in clips]
    # 디졸브 체인
    fc, last, off = [], "[0:v]", 0.0
    for k in range(1, len(clips)):
        off += lens[k - 1] - XF
        fc.append(f"{last}[{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[v{k}]"); last = f"[v{k}]"
    total = off + lens[-1]
    host_start = [sum(lens[:len(parts)]) - XF * len(parts)]
    for k in range(len(parts), len(parts) + len(hosts) - 1):
        host_start.append(host_start[-1] + lens[k] - XF)
    # 음성: line075는 몽타주 3번째 컷부터, 076~078은 각 립싱크 영상의 원래 음성(같은 TTS) 위치
    t075 = SEG * 3 - 0.4  # 4번째 컷(재회의 손)부터 — 응징 컷 위에 감사 인사가 얹히지 않게
    voice = [(os.path.join(A2, "line075s.mp3"), t075)]
    voice += [(os.path.join(A2, f"pad{n}.mp3"), host_start[j]) for j, n in enumerate(("076", "077", "078"))]
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    for v, _ in voice:
        inputs += ["-i", v]
    inputs += ["-stream_loop", "-1", "-i", os.path.join(A, "outro-bed.mp3")]
    nb = len(clips) + len(voice)
    amix = []
    for j, (_, t) in enumerate(voice):
        amix.append(f"[{len(clips) + j}:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={int(t * 1000)}|{int(t * 1000)}[vo{j}]")
    amix.append(f"[{nb}:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{total:.3f},volume=0.22,"
                f"afade=t=in:st=0:d=1.0,afade=t=out:st={total - 1.5:.3f}:d=1.5[bed]")
    amix.append("".join(f"[vo{j}]" for j in range(len(voice))) + f"[bed]amix=inputs={len(voice) + 1}:normalize=0:duration=longest,"
                f"atrim=0:{total:.3f},alimiter=limit=0.89[a]")
    # 자막(ASS)
    ass = os.path.join(tmp, "o.ass")
    times = {"075": (t075, t075 + dur(voice[0][0]))}
    for j, n in enumerate(("076", "077", "078")):
        times[n] = (host_start[j], host_start[j] + dur(voice[j + 1][0]))
    tc = lambda s: f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
    with open(ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\n\n[V4+ Styles]\n"
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                f"Style: Host,{FONT},54,&H00F0F0F0,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,200,200,70,1\n\n"
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for n, (a, b) in times.items():
            f.write(f"Dialogue: 0,{tc(a)},{tc(b + 0.4)},Host,,0,0,0,,{LINES[n]}\n")
    fdir = os.environ.get("FONTSDIR", "/usr/share/fonts")  # Noto Sans CJK JP Bold(본편 자막과 같은 글꼴)
    vchain = ";".join(fc) + f";{last}ass={ass}:fontsdir={fdir}[v]"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    run(inputs + ["-filter_complex", vchain + ";" + ";".join(amix), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
                  "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "aac", "-b:a", "192k", OUT])
    json.dump({"total": round(total, 2), "host_start": [round(x, 2) for x in host_start], "t075": t075},
              open(os.path.join(os.path.dirname(OUT), "yanagi-outro.json"), "w"))
    print(f"저장: {OUT} ({total:.1f}초, 진행자 시작 {[round(x, 1) for x in host_start]})")


if __name__ == "__main__":
    main()
