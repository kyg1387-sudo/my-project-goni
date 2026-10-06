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
    """조립본 실제 장면 경계(장면 사이 1프레임 겹침 반영 — qa_assembly 보고와 같은 계산)."""
    d = [float(x) for x in AUDIO["scene_durations"]]
    t, out = 0.0, {}
    for k, (s, x) in enumerate(zip(SB, d)):
        out[s["id"]] = (t, t + x); t += x - (1 / 24 if k < len(d) - 1 else 0)
    return out


# 조립 후 패치(검수 2026-10-05). 자막이 구워진 화면을 덮으므로 패치 클립에 같은 자막을 같은 시각으로 다시 굽는다.
STILL_REDO = ["S11b", "S14e", "S14f", "S14j", "S15b", "S27i2", "S28c"]          # 서류·화면 일본어 글자 합성 / 얼굴 결함 교체
CUTAWAY = [("S14g", 205.55, 207.75, "S14d2"), ("S14g", 210.45, 213.6, "S14e")]
# S14h: 점장 대사(line022)가 213.3초까지 이어져 유나 CU가 그 꼬리를 립싱크함(감독님 지적) → 213.6초까지 始末書 인서트로 덮고,
# 그 뒤는 유나 대사(line023)만으로 다시 만든 OmniHuman(앞 0.5초 무음 = 213.6초 시작)으로 교체
REPLACE = [(213.6, None, "S14h", "assets/auditions/yanagi-fix-omni/omni-s14h.mp4"),
           # S27m: 정면을 보고 뒷걸음으로 나가던 컷(감독님 지적) → 뒷모습으로 걸어 나가는 새 i2v(유리문 로고 지움)
           (None, None, "S27m", "assets/preview/yanagi/scene121.mp4"),
           # 간판 미표시 외부 컷(감독님 지적) → 간판 합성본
           (None, None, "S17a", "assets/preview/yanagi/scene64-sign.mp4"),
           (None, None, "S17b", "assets/preview/yanagi/scene65-sign.mp4"),
           # S02 「水を……一口だけ」 감독님 지적: 애원·탈진 모습으로 교체
           (None, None, "S02a", "assets/preview/yanagi/scene07.mp4"),
           (None, None, "S02b", "assets/auditions/yanagi-fix-s02/omni-s02b.mp4")]  # OMNI 고개 숙임·손짓 왜곡 → 인서트(대사는 계속)
CROP = {"S12b": (0.30, 1.0)}
# i2v 컷의 편집 카메라(규격 제8장 6 — 생성 지시가 아니라 편집에서). 원본은 자막 없는 생성 클립(assets/preview/yanagi/sceneNN.mp4)
FX = {"S10c": "pull", "S11a": "pan", "S14d": "dutch5+hh", "S16d": "tilt", "S23a": "dollyzoom", "S26a": "rack",
      "S27d": "hh", "S27e": "pull", "S29c": "pull"}


def fx_filter(fx, n):
    t = f"(on/{n})"
    zp = lambda z, x="iw/2-(iw/zoom/2)", y="ih/2-(ih/zoom/2)": f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s=1920x1080:fps=24"
    shake = "crop=1920:1080:x='(iw-1920)/2+9*sin(t*5.3)+4*sin(t*11.7)':y='(ih-1080)/2+6*sin(t*4.1)+3*sin(t*9.3)'"
    if fx == "pull":
        return zp(f"1.08-0.08*{t}")
    if fx == "pan":
        return zp("1.10", x=f"(iw-iw/zoom)*(0.2+0.6*{t})")
    if fx == "tilt":
        return zp("1.10", y=f"(ih-ih/zoom)*(0.15+0.7*{t})")
    if fx == "dollyzoom":   # 인물 마스크 없는 근사: 1.6초 안에 빠른 줌인(정체 발각 1회)
        return zp(f"1+0.22*{t}*{t}")
    if fx == "hh":
        return f"scale=2112:1188,{shake}"
    if fx == "dutch5+hh":
        return f"rotate=5*PI/180:ow=iw:oh=ih:c=black,scale=2400:1350,{shake}"
    return "null"


def fx_clip(src, out, fx, sec):
    n = int(round(sec * 24)) + 2
    base = f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,trim=0:{sec + 0.05:.3f},setpts=PTS-STARTPTS"
    if fx == "rack":    # 초점 이동: 흐림 → 선명 0.8초
        vf = (f"[0:v]{base},split[a][b];[b]gblur=sigma=14[bl];"
              f"[a][bl]blend=all_expr='A*min(1,T/0.8)+B*(1-min(1,T/0.8))',format=yuv420p[v]")
    else:
        vf = f"[0:v]{base},{fx_filter(fx, n)},format=yuv420p[v]"
    run(["-i", src, "-filter_complex", vf, "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", out])                                   # OMNI 왼쪽 가장자리 검은 형체 → 오른쪽 70% 확대(장면 전체 고정)


def patch(src, out, tmp):
    B = bounds(); W, H = 1920, 1080
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_yanagi_overrides as ov
    ov.W, ov.H = W, H
    fdir = os.environ.get("FONTSDIR", "/usr/share/fonts")
    ass = os.path.join(ROOT, "subs", "yanagi.ass")
    segs = []   # (t0, t1, clip)
    for sid in STILL_REDO:
        a, b = B[sid]; c = os.path.join(tmp, f"p_{sid}.mp4")
        sc = next(x for x in SB if x["id"] == sid)
        ov.cam(os.path.join(ROOT, f"assets/portraits/yanagi-keyframes/{sid}-1.png"), c, b - a + 0.1, sc["edit_fx"].split("+")[0])
        segs.append((a, b, c))
    for sid, a, b, ins in CUTAWAY:
        b = b or B[sid][1]; c = os.path.join(tmp, f"c_{sid}_{a:.0f}.mp4")
        ov.cam(os.path.join(ROOT, f"assets/portraits/yanagi-keyframes/{ins}-1.png"), c, b - a + 0.1, "push")
        segs.append((a, b, c))
    idx = {x["id"]: i + 1 for i, x in enumerate(SB)}
    for sid, fx in FX.items():
        a, b = B[sid]; c = os.path.join(tmp, f"f_{sid}.mp4")
        clip = os.path.join(ROOT, f"assets/preview/yanagi/scene{idx[sid]:02d}.mp4")
        if os.path.exists(clip.replace(".mp4", "-sign.mp4")):
            clip = clip.replace(".mp4", "-sign.mp4")   # 간판 합성본(clip_sign_overlay.py)
        if not os.path.exists(clip):
            print("편집 카메라 원본 없음(건너뜀):", sid); continue
        fx_clip(clip, c, fx, b - a)
        segs.append((a, b, c))
    for a, b, sid, clip in REPLACE:
        a = a or B[sid][0]; b = b or B[sid][1]; c = os.path.join(tmp, f"r_{sid}.mp4")
        run(["-i", os.path.join(ROOT, clip), "-an", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=24,"
             f"tpad=stop_mode=clone:stop_duration=1", "-t", f"{b - a + 0.1:.3f}", "-c:v", "libx264", "-crf", "16", c])
        segs.append((a, b, c))
    for sid, (x0, x1) in CROP.items():
        a, b = B[sid]; c = os.path.join(tmp, f"k_{sid}.mp4")
        cw = (x1 - x0) * W; ch = cw * 9 / 16
        run(["-ss", f"{a:.3f}", "-i", src, "-t", f"{b - a:.3f}", "-an", "-vf",
             f"crop={cw:.0f}:{ch:.0f}:{x0 * W:.0f}:40,scale={W}:{H}:flags=lanczos,fps=24", "-c:v", "libx264", "-crf", "16", c])
        # y=40부터: 아래쪽에 구워진 원래 자막이 크롭에 들어오지 않게(자막은 패치 단계에서 다시 굽는다)
        segs.append((a, b, c))
    # 패치 클립에 자막 다시 굽기(타임스탬프를 본편 시각으로 옮겨서) → 오버레이
    inputs, fc, last = ["-i", src], [], "[0:v]"
    for k, (a, b, c) in enumerate(segs, start=1):
        inputs += ["-i", c]
        fc.append(f"[{k}:v]trim=0:{b - a:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={ass}:fontsdir={fdir}[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    run(inputs + ["-filter_complex", ";".join(fc), "-map", last, "-map", "0:a", "-c:v", "libx264", "-preset", "medium",
                  "-crf", "17", "-c:a", "copy", out])
    print("패치:", ", ".join(f"{a:.2f}-{b:.2f}" for a, b, _ in segs))


def main():
    src0 = sys.argv[1]
    os.makedirs(OUTD, exist_ok=True)
    B = bounds()
    tmp0 = os.path.join(OUTD, "fin"); os.makedirs(tmp0, exist_ok=True)
    src = os.path.join(tmp0, "patched.mp4")
    patch(src0, src, tmp0)
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
