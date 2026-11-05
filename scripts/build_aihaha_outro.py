#!/usr/bin/env python3
"""『母が遺したビデオレター』 아웃트로 조립 — 규격 제7장 10 (로컬, 무과금). build_hikikomori_outro.py 구조.

구성: ① 하이라이트 몽타주(본편 키프레임 4개, 편집 카메라) — 발견 → 반전 → 눈물 → 새 출발
      ② 진행자 CU omni-out1(감사) ③ 35° MCU omni-out2(가족의 호칭 질문 + 댓글 유도) ④ CU omni-out3(구독·좋아요 — 버튼은 finalize)
      ⑤ 손 흔들기 omni-out4(다음 화) ⑥ 마지막 프레임 2.6초 슬로 푸시인 → 엔드카드는 append_outro.py
진행자: 공식 진행자 얼굴 + 이 작품 스타일 D(고니감독님 지시 2026-11-05 「헤어스타일과 옷 변경」·「예쁘게」 — 웨이브 하프업·진주 핀·아이보리 카디건·세이지 블라우스).
음악: outro-bed(채널 공통, 보컬 없음)를 전 구간 낮게, 끝 1.5초 페이드아웃. 몽타주 안·몽타주→진행자만 0.6초 디졸브, 진행자 컷끼리 하드컷.
입력: assets/auditions/aihaha-outro-omni/{omni-out1..4.mp4, pad1..pad4.mp3}
출력: out/aihaha-outro.mp4 (1920x1080 24fps, 44.1kHz 스테레오) + out/aihaha-outro.json(진행자 시작 시각)
사용법: python3 scripts/build_aihaha_outro.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = shutil.which("ffmpeg")
A = os.path.join(ROOT, "assets", "auditions", "aihaha-outro-omni")
BED = os.path.join(ROOT, "assets", "auditions", "yanagi-outro", "outro-bed.mp3")
KF = os.path.join(ROOT, "assets", "portraits", "aihaha-keyframes")
OUT = os.path.join(ROOT, "out", "aihaha-outro.mp4")
W, H, FPS = 1920, 1080, 24
HOLD = 0.8
MONTAGE = [("S05b", "push"), ("S10k", "push"), ("S13d", "push"), ("S13g", "pull")]  # 진실을 안 순간 → 결정타 → 진짜 목소리의 눈물 → 창가의 새 아침
SEG = 2.2
XF = 0.6
HOSTS = [("omni-out1", "pad1"), ("omni-out2", "pad2"), ("omni-out3", "pad3"), ("omni-out4", "pad4")]
LINES = {
    "pad1": "最後までご覧いただき、\\Nありがとうございました。",
    "pad2": ["皆様のご家族には、\\N家族だけの呼び名はありますか。", "ぜひ、コメントで教えてください。"],
    "pad3": "チャンネル登録と高評価も、\\Nよろしくお願いします。",
    "pad4": "次回も、どうぞお楽しみに。",
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
    import build_aihaha_overrides as ov
    ov.W, ov.H = W, H
    tmp = tempfile.mkdtemp()
    parts = []
    for i, (sid, fx) in enumerate(MONTAGE):
        p = os.path.join(tmp, f"m{i}.mp4"); ov.cam(os.path.join(KF, f"{sid}-1.png"), p, SEG + XF, fx); parts.append(p)
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
              open(os.path.join(os.path.dirname(OUT), "aihaha-outro.json"), "w"))
    print(f"저장: {OUT} ({total:.1f}초, 진행자 시작 {[round(x, 1) for x in host_start]})")


if __name__ == "__main__":
    main()
