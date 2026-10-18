#!/usr/bin/env python3
"""『タワマンのボスママ』 아웃트로 조립 — 규격 제0장(9:30~10:30 아웃트로·여운), 제7장 10 (로컬, 무과금).

구성: ① 본편 하이라이트 몽타주 5컷(편집 카메라) — 각 컷에 본편 명대사(목소리만, 자막 포함)
      ② 진행자 허리 위 omni-062(감사 인사) → ③ 가슴 위 CU omni-063(高評価·チャンネル登録 버튼, outro_cta_overlay.py)
      ④ 허리 위 omni-064(댓글 유도) → ⑤ 손 흔들기 omni-065(마무리) → ⑥ 손 흔드는 키프레임 슬로 푸시인 2.4초(엔드카드 전 여운)
음악: 채널 공통 outro-bed(보컬 없음)를 전 구간 베드로(-13dB), 끝 1.5초 페이드아웃. 컷 사이 0.5초 디졸브.
입력: assets/auditions/tower-outro/{omni-06x.mp4, pad06x.mp3, outro-bed.mp3}, assets/audio-overrides/tower/lineNNN.mp3
출력: out/tower-outro.mp4 (1920x1080 24fps, 44.1kHz 스테레오) — 이어서 append_outro.py로 본편 + 엔드카드
사용법: python3 scripts/build_tower_outro.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_tower_overrides as ov  # noqa: E402

A = os.path.join(ROOT, "assets", "auditions", "tower-outro")
VO = os.path.join(ROOT, "assets", "audio-overrides", "tower")
KF = os.path.join(ROOT, "assets", "portraits", "tower-keyframes")
HOST = os.path.join(ROOT, "assets", "portraits", "yanagi-host")
OUT = os.path.join(ROOT, "out", "tower-outro.mp4")
W, H, FPS, XF, HOLD = 1920, 1080, 24, 0.5, 0.5
# (키프레임, 카메라, 대사 파일, 시작, 끝(초), 자막, 자막 스타일) — 구간은 무음 검출로 구절 경계(build 기록 참조)
MONTAGE = [
    ("S01a-1.png", "push", "line001", 0.85, 4.90, "低層階の方は、荷物用エレベーターを使ってくださる?", "Reika"),
    ("S06c-1.png", "push", "line020", 4.62, 8.28, "あなたの部屋の値段、私のバッグ三つ分でしょ?", "Reika"),
    ("S14a-s1.png", "push", "line040", 0.00, 3.60, "この通帳を、ご覧ください", "Yumi"),
    ("S16i-1.png", "push", "line048", 0.00, 3.94, "……四十二階の持ち主は、私だがね", "Odagiri"),
    ("S19f-1.png", "push", "line060", 1.45, 5.35, "お荷物の多い方は、荷物用エレベーターをどうぞ", "Yumi"),
]
HOSTS = [("062", "最後までご覧いただき、ありがとうございました。"),
         ("063", "スカッとしていただけたら、高評価とチャンネル登録で\\N応援していただけると嬉しいです。"),
         ("064", "あなたのマンションにも、こんなボスママ、いませんか?\\Nぜひコメントで教えてください。"),
         ("065", "それでは、また次のお話で。")]
STYLE = {"Reika": "&H00B4B4FF", "Yumi": "&H00F0E6C8", "Odagiri": "&H00DCDCDC", "Host": "&H00F0F0F0"}


def run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode())


def first_pause(p, after=0.6):
    """'…たら、' 뒤 첫 쉼(버튼 등장 시점)."""
    e = subprocess.run(["ffmpeg", "-i", p, "-af", "silencedetect=n=-38dB:d=0.12", "-f", "null", "-"], capture_output=True, text=True).stderr
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", e)]
    return next((x for x in ends if x > after), 1.5)


def main():
    tmp = tempfile.mkdtemp()
    clips, voice, subs = [], [], []
    for k, (kf, fx, line, a, b, text, st) in enumerate(MONTAGE):
        seg = (b - a) + 0.9
        p = os.path.join(tmp, f"m{k}.mp4"); ov.cam(os.path.join(KF, kf), p, seg + XF, fx); clips.append(p)
        v = os.path.join(tmp, f"v{k}.wav")
        run(["-i", os.path.join(VO, f"{line}.mp3"), "-af", f"atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={b - a - 0.06:.3f}:d=0.06,"
             "aformat=sample_rates=44100:channel_layouts=stereo", v])
        voice.append([v, None, text, st])
    for n, text in HOSTS:
        p = os.path.join(tmp, f"h{n}.mp4")
        run(["-i", os.path.join(A, f"omni-{n}.mp4"), "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p,setsar=1,"
             f"tpad=stop_mode=clone:stop_duration={HOLD}", "-an", "-c:v", "libx264", "-crf", "17", p])
        clips.append(p); voice.append([os.path.join(A, f"pad{n}.mp3"), None, text, "Host"])
    wave = os.path.join(tmp, "wave.mp4"); ov.cam(os.path.join(HOST, "host-wave-1.png"), wave, 2.4 + XF, "push"); clips.append(wave)
    lens = [dur(c) for c in clips]
    starts, t = [], 0.0
    for L in lens:
        starts.append(t); t += L - XF
    total = starts[-1] + lens[-1]
    for k in range(len(MONTAGE)):
        voice[k][1] = starts[k] + 0.45
    for j in range(len(HOSTS)):
        voice[len(MONTAGE) + j][1] = starts[len(MONTAGE) + j]
    # 영상: 디졸브 체인 + 자막
    fc, last = [], "[0:v]"
    for k in range(1, len(clips)):
        fc.append(f"{last}[{k}:v]xfade=transition=fade:duration={XF}:offset={starts[k]:.3f}[x{k}]"); last = f"[x{k}]"
    ass = os.path.join(tmp, "o.ass")
    tc = lambda s: f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
    with open(ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\n\n[V4+ Styles]\n"
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        for name, col in STYLE.items():
            f.write(f"Style: {name},Noto Sans CJK JP,{54 if name == 'Host' else 58},{col},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{4 if name == 'Host' else 5},1,2,200,200,70,1\n")
        f.write("\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for v, st0, text, style in voice:
            f.write(f"Dialogue: 0,{tc(st0 + 0.1)},{tc(st0 + dur(v) + 0.3)},{style},,0,0,0,,{text}\n")
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    for v, *_ in voice:
        inputs += ["-i", v]
    inputs += ["-stream_loop", "-1", "-i", os.path.join(A, "outro-bed.mp3")]
    nc, nv = len(clips), len(voice)
    am = [f"[{nc + j}:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={int(st0 * 1000)}|{int(st0 * 1000)}[vo{j}]" for j, (_, st0, _, _) in enumerate(voice)]
    am.append(f"[{nc + nv}:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{total:.3f},volume=0.22,afade=t=in:st=0:d=1.0,afade=t=out:st={total - 1.5:.3f}:d=1.5[bed]")
    am.append("".join(f"[vo{j}]" for j in range(nv)) + f"[bed]amix=inputs={nv + 1}:normalize=0:duration=longest,atrim=0:{total:.3f},alimiter=limit=0.89[a]")
    raw = os.path.join(tmp, "raw.mp4")
    run(inputs + ["-filter_complex", ";".join(fc) + f";{last}ass={ass}[v];" + ";".join(am), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
                  "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "aac", "-b:a", "192k", raw])
    # 구독 버튼: omni-063 안 '…たら、' 뒤 쉼에 「高評価」, 0.8초 뒤 「チャンネル登録」, 063 컷 끝에서 사라짐
    h63 = len(MONTAGE) + 1
    like_in = starts[h63] + first_pause(os.path.join(A, "pad063.mp3"))
    cta_out = starts[h63] + lens[h63] - XF
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    subprocess.run(["python3", os.path.join(ROOT, "scripts", "outro_cta_overlay.py"), raw, OUT, f"{like_in:.2f}", f"{like_in + 0.8:.2f}", f"{cta_out:.2f}"], check=True)
    json.dump({"total": round(total, 2), "starts": [round(x, 2) for x in starts], "like_in": round(like_in, 2)},
              open(os.path.join(os.path.dirname(OUT), "tower-outro.json"), "w"))
    print(f"저장: {OUT} ({total:.1f}초, 컷 시작 {[round(x, 1) for x in starts]}, 버튼 {like_in:.1f}s)")


if __name__ == "__main__":
    main()
