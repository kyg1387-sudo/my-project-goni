#!/usr/bin/env python3
"""『引きこもりの息子』 아웃트로 조립 — 규격 제7장 10 (로컬, 무과금). build_tsuki_outro.py 구조.

구성: ① 하이라이트 몽타주(본편 정지 컷 4개, 편집 카메라) — 반전 → 응징 → 여운 → 새 출발
      ② 진행자 가슴 위 립싱크 omni-out1(감사·구독·좋아요) — 버튼 합성은 finalize 단계(outro_cta_overlay.py)
      ③ 허리 위 omni-out2(댓글 유도)  ④ 가슴 위 omni-out3(다음 화 예고)  ⑤ 손 흔들기 omni-out4(마무리)
      ⑥ 손 흔드는 키프레임 2.6초 슬로 푸시인(OmniHuman은 손을 내려 버림 — 버들잎 교훈) → 엔드카드는 append_outro.py
진행자: 공식 진행자 얼굴 + 스타일 A(고니감독님 선택 2026-10-30 — 로 시뇽·더스티 로즈 보 블라우스·금 드롭 귀걸이), hikikomori-host-a cu-1·각도 컷·wave-2.
음악: outro-bed(채널 공통, 보컬 없음)를 전 구간 낮게, 끝 1.5초 페이드아웃. 컷 사이 0.6초 디졸브. 진행자 컷 끝 0.8초 정지(입 다문 채).
입력: assets/auditions/hikikomori-outro-omni/{omni-out1..4.mp4, pad1..pad4}.mp3
출력: out/hikikomori-outro.mp4 (1920x1080 24fps, 44.1kHz 스테레오) + out/hikikomori-outro.json(진행자 시작 시각)
사용법: python3 scripts/build_hikikomori_outro.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = shutil.which("ffmpeg")
A = os.path.join(ROOT, "assets", "auditions", "hikikomori-outro-omni")
BED = os.path.join(ROOT, "assets", "auditions", "yanagi-outro", "outro-bed.mp3")
KF = os.path.join(ROOT, "assets", "portraits", "hikikomori-keyframes")
WAVE_KF = os.path.join(ROOT, "assets", "portraits", "hikikomori-host-a", "host-wave-2.png")
OUT = os.path.join(ROOT, "out", "hikikomori-outro.mp4")
W, H, FPS = 1920, 1080, 24
HOLD = 0.8
MONTAGE = [("S05e", "push"), ("S11c", "push"), ("S21a", "push"), ("S24d", "pull")]  # 대본 OUT1: 문을 벌컥 여는 健太郎 → 「父さんの工場」 폴더 → 계약서를 찢는 손 → 식탁
SEG = 2.2
XF = 0.6
HOSTS = [("omni-out1", "pad1"), ("omni-out2", "pad2"), ("omni-out3", "pad3"), ("omni-out4", "pad4")]
LINES = {
    "pad1": "最後までご覧いただき、\\Nありがとうございました。",
    "pad2": "スカッとした方は、ぜひ\\Nチャンネル登録と高評価をお願いします",
    "pad3": ["皆様なら、部屋を出ていく息子さんに\\N何と声をかけますか？", "コメントで教えてください"],
    "pad4": ["次回も、胸がスカッとする物語を\\Nお届けします。お楽しみに", "それでは、また次回\\Nお会いしましょう"],
}
FONT = "Zen Old Mincho"
# 고니감독님 지적(9:58): 허리 위 컷 왼쪽 가장자리로 몸과 떨어진 손이 지나감(OmniHuman 잔상) → 왼쪽 20%를 잘라 확대(x0, y0, 폭 비율)
CROP = {}  # 가장자리 잔상 검수 후 지정


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


def dur(p):
    e = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def norm(src, out, extra=""):
    run(["-i", src, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p,setsar=1{extra}",
         "-c:v", "libx264", "-crf", "17", "-an", out])


def main():
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_hikikomori_overrides as ov
    ov.W, ov.H = W, H
    tmp = tempfile.mkdtemp()
    parts = []
    for i, (sid, fx) in enumerate(MONTAGE):
        scr = os.path.join(ROOT, "assets", "preview", "hikikomori-screens", f"{sid}.png")
        p = os.path.join(tmp, f"m{i}.mp4"); ov.cam(scr if os.path.exists(scr) else os.path.join(KF, f"{sid}-1.png"), p, SEG + XF, fx); parts.append(p)
    hosts = []
    for vid, _ in HOSTS:
        p = os.path.join(tmp, f"{vid}.mp4")
        pre = ""
        if vid in CROP:
            x0, y0, k = CROP[vid]
            pre = f",crop=iw*{k}:ih*{k}:iw*{x0}:ih*{y0},scale={W}:{H}:flags=lanczos"
        norm(os.path.join(A, f"{vid}.mp4"), p, extra=f"{pre},tpad=stop_mode=clone:stop_duration={HOLD}"); hosts.append(p)
    # 마지막 정지는 omni-out4의 마지막 프레임에서 — 손 흔드는 키프레임으로 디졸브하면 얼굴·손이 이중으로 겹침(1차 조립 실증)
    last_png = os.path.join(tmp, "out4_last.png")
    run(["-sseof", "-0.1", "-i", os.path.join(A, "omni-out4.mp4"), "-frames:v", "1", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", last_png])
    wave = os.path.join(tmp, "wave.mp4")
    ov.cam(last_png, wave, 2.6, "push")
    clips = parts + hosts + [wave]
    lens = [dur(c) for c in clips]
    # 진행자 컷끼리는 하드컷(1프레임) — 말하는 얼굴끼리 0.6초 디졸브하면 두 얼굴이 겹쳐 보임(1차 조립 실증). 몽타주 안·몽타주→진행자만 디졸브
    xf = lambda k: XF if k <= len(parts) else 1 / FPS
    fc, last, off = [], "[0:v]", 0.0
    for k in range(1, len(clips)):
        off += lens[k - 1] - xf(k)
        fc.append(f"{last}[{k}:v]xfade=transition=fade:duration={xf(k):.4f}:offset={off:.3f}[v{k}]"); last = f"[v{k}]"
    total = off + lens[-1]
    host_start = [sum(lens[:len(parts)]) - XF * len(parts)]
    for k in range(len(parts), len(parts) + len(hosts) - 1):
        host_start.append(host_start[-1] + lens[k] - xf(k + 1))
    voice = [(os.path.join(A, f"{aid}.mp3"), host_start[j]) for j, (_, aid) in enumerate(HOSTS)]
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    for v, _ in voice:
        inputs += ["-i", v]
    inputs += ["-stream_loop", "-1", "-i", BED]
    nb = len(clips) + len(voice)
    amix = [f"[{len(clips) + j}:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={int(t * 1000)}|{int(t * 1000)}[vo{j}]"
            for j, (_, t) in enumerate(voice)]
    amix.append(f"[{nb}:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{total:.3f},volume=0.22,"
                f"afade=t=in:st=0:d=1.0,afade=t=out:st={total - 1.5:.3f}:d=1.5[bed]")
    amix.append("".join(f"[vo{j}]" for j in range(len(voice))) + f"[bed]amix=inputs={len(voice) + 1}:normalize=0:duration=longest,"
                f"atrim=0:{total:.3f},alimiter=limit=0.89[a]")
    ass = os.path.join(tmp, "o.ass")
    tc = lambda s: f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
    with open(ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\n\n[V4+ Styles]\n"
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                f"Style: Host,{FONT},66,&H00F0F0F0,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,200,200,70,1\n\n"
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for j, ((v, a), (_, aid)) in enumerate(zip(voice, HOSTS)):
            ls = LINES[aid] if isinstance(LINES[aid], list) else [LINES[aid]]
            nxt = voice[j + 1][1] - 0.05 if j + 1 < len(voice) else total
            d = min(dur(v) + 0.3, nxt - a); w = [len(x) for x in ls]; t0 = a  # 다음 멘트와 자막 겹침 금지
            for x, n in zip(ls, w):  # 2줄 넘는 멘트는 글자 수 비례로 나눠 표시(제15장 21)
                t1 = t0 + d * n / sum(w); f.write(f"Dialogue: 0,{tc(t0)},{tc(t1)},Host,,0,0,0,,{x}\n"); t0 = t1
    fdir = os.path.join(ROOT, "scripts", "fonts")
    vchain = ";".join(fc) + f";{last}ass={ass}:fontsdir={fdir}[v]"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    run(inputs + ["-filter_complex", vchain + ";" + ";".join(amix), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
                  "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "aac", "-b:a", "192k", OUT])
    json.dump({"total": round(total, 2), "host_start": [round(x, 2) for x in host_start]},
              open(os.path.join(os.path.dirname(OUT), "hikikomori-outro.json"), "w"))
    print(f"저장: {OUT} ({total:.1f}초, 진행자 시작 {[round(x, 1) for x in host_start]})")


if __name__ == "__main__":
    main()
