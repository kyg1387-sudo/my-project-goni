#!/usr/bin/env python3
"""『時給5万円の罠』 PHASE 6 마무리 (로컬, 무과금) — finalize_beggar.py 구조 + bento 결산(제19장 17)·제20장 7 반영.

1) 영상 패치(구워진 자막 위에 같은 자막을 다시 굽는다)
   - CLIPS: 조립 후 다시 만든 i2v·립싱크 클립을 그 컷 자리에 덮음(burn 재실행 없이, 제12장 4)
   - MANUAL: 5초 넘는 한 구도 컷을 같은 장면 키프레임 푸시인 인서트로 깸(제12장 5)
   - CAPTIONS: 시점 소자막 「東京 深夜一時」「一日目」「三日目」「六日目」를 왼쪽 위 명조로 2.4초(페이드), 암전 없음(제19장 14 ①·제15장 20)
   - JUMPS: 시간 점프 경계에 앞 컷 마지막 프레임 0.6초 디졸브(대사 싱크 불변)
   - LIFT: 어두운 장면 평균 밝기 40/255 미만이면 중간 톤만 곡선으로 올림(제11장 11·제13장 3), 전편 공통 미세 그레인
2) 효과음 믹스: productions/yamibaito-ja/sfx_timeline.json(44개) × assets/auditions/yamibaito-sfx/<name>.mp3 를 타임코드에 배치
   (−26~−14 dBFS, 대사 구간 −6 dB — Lock 줄 시각으로 게이트, 제19장 10 ④·제15장 22)
3) 룸톤 베드 −52dBFS + 끝 페이드 + 라우드니스 −14 LUFS / −1 dBTP(제12장 3·제15장 13), silencedetect −60dB 2초 0건 확인
4) 아웃트로(build_yamibaito_outro.py 산출) + 구독 버튼(outro_cta_overlay.py) + 엔드카드(append_outro.py)
사용법: python3 scripts/finalize_yamibaito.py <burn 완성본.mp4> [--no-outro] [--from-mixed] [--no-sfx]
"""
import json, os, shutil, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = shutil.which("ffmpeg")
OUTD = os.path.join(ROOT, "out")
SB = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "yamibaito.json"), encoding="utf-8"))["scenes"]
AUDIO = json.load(open(os.path.join(ROOT, "scripts", "audio", "yamibaito.json"), encoding="utf-8"))
LOCK = json.load(open(os.path.join(ROOT, "productions", "yamibaito-ja", "lock.json"), encoding="utf-8"))
SFX = json.load(open(os.path.join(ROOT, "productions", "yamibaito-ja", "sfx_timeline.json"), encoding="utf-8"))["events"]
SFX_DIR = os.path.join(ROOT, "assets", "auditions", "yamibaito-sfx")
KF = os.path.join(ROOT, "assets", "portraits", "yamibaito-keyframes")
ASS = os.path.join(ROOT, "subs", "yamibaito.ass")
W, H, FPS = 1920, 1080, 24
# (컷, 키프레임, 컷 시작 후 초, 길이 None=끝까지) — 1초 시트 검수 뒤 지정(5초 넘는 한 구도)
MANUAL = []
# (컷, 교체 클립 경로) — 재생성 i2v·립싱크 클립
CLIPS = []
# 시점 소자막: 컷 시작 +0.3초부터 2.4초, 왼쪽 위(제19장 14 ①)
CAPTIONS = {"S01a": "東京　深夜一時", "S06a": "一日目", "S07a": "三日目", "S07f": "六日目"}
# 시간 점프 경계(이 컷의 시작에서 앞 컷 마지막 프레임을 0.6초 디졸브)
JUMPS = ["S06a", "S07a", "S07f"]
# 타이틀 카드: H4(보케 정지 판) 위 가운데 큰 명조 「時給5万円の罠」 + 작은 「闇バイト　再現ドラマ」(조립본 검수에서 타이틀 글자 누락 확인, 2026-10-25)
TITLE = ("H4", "時給5万円の罠", "闇バイト　再現ドラマ")
XF = 0.6
# 효과음 베드 길이(초) — 타임라인에 dur가 없는 지속음
SFX_DUR = {"van_interior": 40, "drone_low": 9, "fluorescent": 36, "clock_tick": 19, "heartbeat_fast": 13, "breath_run": 10, "wind_night": 15,
           "wind_road": 26, "breath_phone": 8, "birds": 56, "silence_room": 1.0, "siren_far": 6}


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def bounds():
    d = [float(x) for x in AUDIO["scene_durations"]]
    t, out = 0.0, {}
    for k, (s, x) in enumerate(zip(SB, d)):
        out[s["id"]] = (t, t + x); t += x - (1 / FPS if k < len(d) - 1 else 0)
    return out


def caption_png(text, path):
    f = ImageFont.truetype(os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Regular.ttf"), 46)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x, y = 110, 92
    d.text((x + 2, y + 2), text, font=f, fill=(0, 0, 0, 170)); d.text((x, y), text, font=f, fill=(238, 234, 224, 235))
    im.save(path)


def title_png(main, sub, path):
    f = ImageFont.truetype(os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf"), 176)
    fs = ImageFont.truetype(os.path.join(ROOT, "scripts", "fonts", "ZenKakuGothicNew-Regular.ttf"), 52)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    w = d.textlength(main, font=f); x, y = (W - w) / 2, H / 2 - 150
    for dx, dy, col in ((6, 6, (0, 0, 0, 200)), (0, 0, (248, 244, 232, 255))):
        d.text((x + dx, y + dy), main, font=f, fill=col)
    ws = d.textlength(sub, font=fs); xs = (W - ws) / 2; ys = y + 230
    d.text((xs + 2, ys + 2), sub, font=fs, fill=(0, 0, 0, 180)); d.text((xs, ys), sub, font=fs, fill=(220, 215, 205, 235))
    im.save(path)


def scene_luma(src, B):
    """장면별 평균 밝기(컷 중간 프레임 1장) → 40/255 미만 장면 목록(제11장 11)."""
    dark = []
    tmp = os.path.join(OUTD, "fin", "luma.png")
    for sid, (a, b) in B.items():
        run(["-ss", f"{(a + b) / 2:.3f}", "-i", src, "-frames:v", "1", "-vf", "scale=192:108", tmp])
        m = float(np.asarray(Image.open(tmp).convert("L")).mean())
        if m < 40:
            dark.append((sid, round(m, 1)))
    return dark


def patch(src, out, tmp):
    B = bounds()
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_yamibaito_overrides as ov
    ov.W, ov.H = W, H
    fdir = os.path.join(ROOT, "scripts", "fonts")
    segs = []
    for sid, clip in CLIPS:
        a, b = B[sid]; segs.append((a, b, os.path.join(ROOT, clip)))
    for sid, kf_id, off, sec in MANUAL:
        lo, hi = B[sid]
        a = lo + off; b = hi - 0.02 if sec is None else min(hi - 0.02, a + sec)
        c = os.path.join(tmp, f"m_{sid}_{kf_id}.mp4")
        ov.cam(os.path.join(KF, f"{kf_id}-1.png"), c, b - a + 0.1, "push"); segs.append((a, b, c))
    inputs, fc, last = ["-i", src], [], "[0:v]"
    k = 0
    for a, b, c in segs:
        k += 1; inputs += ["-i", c]
        fc.append(f"[{k}:v]scale={W}:{H},trim=0:{b - a:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={ASS}:fontsdir={fdir}[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    # 시간 점프: 앞 컷 마지막 프레임을 경계에서 0.6초 디졸브(사운드·자막 싱크 불변)
    for sid in JUMPS:
        a = B[sid][0]
        fr = os.path.join(tmp, f"jump_{sid}.png")
        run(["-ss", f"{a - 1.5 / FPS:.4f}", "-i", src, "-frames:v", "1", fr])
        k += 1; inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{XF + 0.1:.2f}", "-i", fr]
        fc.append(f"[{k}:v]format=rgba,fade=t=out:st=0:d={XF}:alpha=1,setpts=PTS+{a:.3f}/TB[j{k}]")
        fc.append(f"{last}[j{k}]overlay=enable='between(t,{a:.3f},{a + XF:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    for sid, text in CAPTIONS.items():
        a = B[sid][0] + 0.3; b = a + 2.4
        png = os.path.join(tmp, f"cap_{sid}.png"); caption_png(text, png)
        k += 1; inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{b - a + 0.1:.2f}", "-i", png]
        fc.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1,fade=t=out:st={b - a - 0.4:.2f}:d=0.4:alpha=1,setpts=PTS+{a:.3f}/TB[c{k}]")
        fc.append(f"{last}[c{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    tid, tmain, tsub = TITLE
    a = B[tid][0] + 0.15; b = B[tid][1] - 0.02
    png = os.path.join(tmp, "title.png"); title_png(tmain, tsub, png)
    k += 1; inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{b - a + 0.1:.2f}", "-i", png]
    fc.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d=0.5:alpha=1,setpts=PTS+{a:.3f}/TB[t{k}]")
    fc.append(f"{last}[t{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    dark = scene_luma(src, B)
    lift = "".join(f"+between(t,{B[s][0]:.2f},{B[s][1]:.2f})" for s, _ in dark)
    print("밝기 보정 장면(<40/255):", dark)
    lift_f = f"curves=enable='{lift[1:]}':all='0/0 0.12/0.19 0.5/0.56 1/1'," if dark else ""
    fc.append(f"{last}{lift_f}eq=contrast=1.02:saturation=0.98,noise=alls=3:allf=t+u,format=yuv420p[v]")
    run(inputs + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "copy", out])


def sfx_bus(path, total):
    """효과음 타임라인 → 한 트랙(44.1k 스테레오). 소스마다 −18 LUFS 정규화 뒤 dbfs만큼 가감, 대사 구간은 −6 dB 게이트."""
    inputs, parts, labels = [], [], []
    missing = []
    for k, e in enumerate(SFX):
        f = os.path.join(SFX_DIR, f"{e['name']}.mp3")
        if not os.path.exists(f):
            missing.append(e["name"]); continue
        d = SFX_DUR.get(e["name"]); gain = e["dbfs"] + 18
        inputs += ["-i", f]
        chain = "aformat=sample_rates=44100:channel_layouts=stereo,loudnorm=I=-18:TP=-2:LRA=9"
        if d:
            chain += f",aloop=loop=-1:size=2147483647,atrim=0:{d},afade=t=in:st=0:d=0.8,afade=t=out:st={max(d - 1.5, 0):.2f}:d=1.5"
        chain += f",volume={gain}dB,adelay={int(e['at'] * 1000)}|{int(e['at'] * 1000)}"
        parts.append(f"[{len(labels)}:a]{chain}[s{k}]"); labels.append(f"[s{k}]")
    if missing:
        print("효과음 소스 없음(건너뜀):", sorted(set(missing)))
    gate = "+".join(f"between(t,{l['start']:.2f},{l['end']:.2f})" for l in LOCK["lines"] if l["spk"] != "진행자")
    parts.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,apad=whole_dur={total:.3f},atrim=0:{total:.3f},"
                 f"volume='if({gate},0.5,1)':eval=frame[a]")
    script = os.path.join(os.path.dirname(path), "sfx_filter.txt"); open(script, "w").write(";\n".join(parts))
    run(inputs + ["-filter_complex_script", script, "-map", "[a]", "-c:a", "pcm_s16le", path])
    return len(labels)


def main():
    src0 = sys.argv[1]
    tmp = os.path.join(OUTD, "fin"); os.makedirs(tmp, exist_ok=True)
    mov = os.path.join(tmp, "mixed.mov")
    if "--from-mixed" not in sys.argv:
        patched = os.path.join(tmp, "patched.mp4"); patch(src0, patched, tmp)
        vd = dur(patched)
        if "--no-sfx" in sys.argv:
            run(["-i", patched, "-c:v", "copy", "-c:a", "pcm_s16le", mov])
        else:
            bus = os.path.join(tmp, "sfx_bus.wav"); n = sfx_bus(bus, vd); print(f"효과음 {n}개 배치")
            run(["-i", patched, "-i", bus, "-filter_complex", "[0:a][1:a]amix=inputs=2:normalize=0:duration=first[a]", "-map", "0:v", "-map", "[a]",
                 "-c:v", "copy", "-c:a", "pcm_s16le", mov])
    main_out = os.path.join(tmp, "main.mp4")
    ad = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=duration", "-of", "csv=p=0", mov]))
    vd = dur(mov)
    # burn 오디오가 영상보다 짧으면 끝에서 BGM이 끊기고 무음(제18장 10 ②) → 끝 3초 페이드 + 영상 길이까지 채움 + 룸톤 베드(제15장 13)
    fc = (f"[0:a]afade=t=out:st={max(min(ad, vd) - 3.0, 0):.3f}:d=3,apad=whole_dur={vd:.3f}[m];"
          f"anoisesrc=d={vd:.3f}:c=brown:a=1,lowpass=f=250,volume=-40dB,aformat=sample_rates=44100:channel_layouts=stereo[rt];"
          "[m][rt]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89:level=0[a]")
    run(["-i", mov, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-ar", "44100", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", main_out])
    sil = subprocess.run([FF, "-i", main_out, "-af", "silencedetect=n=-60dB:d=2", "-f", "null", "-"], capture_output=True, text=True).stderr
    print("본편 마무리:", main_out, round(dur(main_out), 2), "/ −60dB 2초 무음:", sil.count("silence_start"), "건")
    if "--no-outro" not in sys.argv:
        outro(main_out, tmp)


def outro(main_out, tmp):
    o = os.path.join(OUTD, "yamibaito-outro.mp4")
    meta = json.load(open(os.path.join(OUTD, "yamibaito-outro.json")))
    hs = meta["host_start"]
    cta = os.path.join(tmp, "outro-cta.mp4")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), o, cta, f"{hs[3] + 0.6:.2f}", f"{hs[3] + 1.4:.2f}", f"{hs[3] + 3.6:.2f}"], check=True)
    final = os.path.join(OUTD, "yamibaito-final.mp4")
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), main_out, final], check=True, env=env)
    print(f"완성: {final} ({dur(final):.1f}초) / 본편 {dur(main_out):.1f}초 / 아웃트로 {dur(cta):.1f}초")


if __name__ == "__main__":
    main()
