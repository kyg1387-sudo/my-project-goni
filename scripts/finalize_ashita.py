#!/usr/bin/env python3
"""『明日から来なくていい』 PHASE 6 마무리 (로컬, 무과금). finalize_yanagi.py 구조.

1) 조립 후 패치(자막이 구워진 화면을 덮으므로 패치 클립에 같은 자막을 같은 시각으로 다시 굽는다)
   - STILL_REDO: 흰 띠를 다시 잡은 키프레임(S17da·S15bb) 정지 푸시인
   - FX: i2v 컷 편집 카메라(규격 제8장 6) — 원본은 자막 없는 생성 클립 assets/preview/ashita-kara/sceneNN.mp4
2) 후크: 0~4초 경보 저음 드론 + 심장 박동(설계 결정 ①, −60dB 2초 무음 금지 충족),
   H1(4~9초) = 본편 S12c 립싱크 구간(자막 포함) + 남는 시간 S12c 키프레임 푸시인, 음성 L22를 입 모양 위치에 믹스(후크 BGM −6dB)
3) 색감 통일: 전편 공통 미세 대비·채도 + 필름 그레인
4) 아웃트로: out/ashita-outro.mp4(+구독 버튼) → append_outro.py(본편 1.0초 페이드아웃 → 검은 화면 0.8초 → 아웃트로 → 엔드카드)
5) 전달본: deliveries/ashita-kara/ashita-kara-final.mp4(28MB 조각) + 480p 미리보기
사용법: python3 scripts/finalize_ashita.py <burn 완성본.mp4> [--no-outro]
"""
import glob
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = shutil.which("ffmpeg")
OUTD = os.path.join(ROOT, "out")
SBJ = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "ashita-kara.json"), encoding="utf-8"))
SB = SBJ["scenes"]
AUDIO = json.load(open(os.path.join(ROOT, "scripts", "audio", "ashita-kara.json"), encoding="utf-8"))
LOCK = {l["tag"]: l for l in json.load(open(os.path.join(ROOT, "productions", "ashita-kara-ja", "lock.json"), encoding="utf-8"))["lines"]}
KF = os.path.join(ROOT, "assets", "portraits", "ashita-kara-keyframes")
W, H = 1920, 1080

STILL_REDO = ["S17da", "S15bb"]                       # 흰 띠(한쪽만 잘랐던 실수) 다시 잡은 키프레임
FX = {"S10a": "jib", "S12a": "dutch5+hh", "S17a": "hh", "S18e": "hh"}   # 스토리보드 edit_fx(craneup·dutch5,handheld·handheld)


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


def fx_filter(fx):
    zp = lambda z, x="iw/2-(iw/zoom/2)", y="ih/2-(ih/zoom/2)": f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s=1920x1080:fps=24"
    shake = "crop=1920:1080:x='(iw-1920)/2+9*sin(t*5.3)+4*sin(t*11.7)':y='(ih-1080)/2+6*sin(t*4.1)+3*sin(t*9.3)'"
    if fx == "jib":      # 크레인 업: 화면이 아래에서 위로 천천히 올라감
        return zp("1.10", y="(ih-ih/zoom)*(0.9-0.8*min(1,on/110))")
    if fx == "hh":
        return f"scale=2112:1188,{shake}"
    if fx == "dutch5+hh":
        return f"rotate=5*PI/180:ow=iw:oh=ih:c=black,scale=2400:1350,{shake}"
    return "null"


def fx_clip(src, out, fx, sec):
    base = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=24,tpad=stop_mode=clone:stop_duration=2,trim=0:{sec + 0.05:.3f},setpts=PTS-STARTPTS"
    run(["-i", src, "-filter_complex", f"[0:v]{base},{fx_filter(fx)},format=yuv420p[v]", "-map", "[v]", "-an",
         "-c:v", "libx264", "-crf", "16", out])


def patch(src, out, tmp):
    B = bounds()
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_ashita_overrides as ov
    ov.W, ov.H = W, H
    fdir = os.environ.get("FONTSDIR", "/usr/share/fonts")
    ass = os.path.join(ROOT, "subs", "ashita-kara.ass")
    segs = []
    for sid in STILL_REDO:
        a, b = B[sid]; c = os.path.join(tmp, f"p_{sid}.mp4")
        sc = next(x for x in SB if x["id"] == sid)
        ov.cam(os.path.join(KF, f"{sid}-1.png"), c, b - a + 0.1, sc["edit_fx"])
        segs.append((a, b, c))
    idx = {x["id"]: i + 1 for i, x in enumerate(SB)}
    for sid, fx in FX.items():
        a, b = B[sid]; c = os.path.join(tmp, f"f_{sid}.mp4")
        clip = os.path.join(ROOT, f"assets/preview/ashita-kara/scene{idx[sid]:02d}.mp4")
        if not os.path.exists(clip):
            print("편집 카메라 원본 없음(건너뜀):", sid); continue
        fx_clip(clip, c, fx, b - a)
        segs.append((a, b, c))
    inputs, fc, last = ["-i", src], [], "[0:v]"
    for k, (a, b, c) in enumerate(segs, start=1):
        inputs += ["-i", c]
        fc.append(f"[{k}:v]trim=0:{b - a:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={ass}:fontsdir={fdir}[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    run(inputs + ["-filter_complex", ";".join(fc), "-map", last, "-map", "0:a", "-c:v", "libx264", "-preset", "medium",
                  "-crf", "17", "-c:a", "copy", out])
    print("패치:", ", ".join(f"{a:.2f}-{b:.2f}" for a, b, _ in segs))


def hook_bed(path):
    """0~4.3초: 경보 저음 드론(48·96Hz + 걸러진 브라운 노이즈) + 심장 박동 2회(lub-dub), 끝 0.4초 페이드아웃."""
    beat = lambda t: (f"sine=f=52:d=0.16,afade=t=out:st=0.04:d=0.12,volume=1.6,adelay={int(t * 1000)}|{int(t * 1000)}")
    fc = ("sine=f=48:d=4.3[s1];sine=f=96:d=4.3,volume=0.35[s2];anoisesrc=d=4.3:c=brown:a=0.25,lowpass=f=180[n];"
          "[s1][s2][n]amix=inputs=3:normalize=0,volume=0.30,afade=t=in:st=0:d=1.2,afade=t=out:st=3.9:d=0.4[dr];"
          f"{beat(1.55)}[b1];{beat(1.85)}[b2];{beat(2.95)}[b3];{beat(3.25)}[b4];"
          "[dr][b1][b2][b3][b4]amix=inputs=5:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo[a]")
    run(["-filter_complex", fc, "-map", "[a]", "-t", "4.3", path])


def main():
    src0 = sys.argv[1]
    outro_on = "--no-outro" not in sys.argv
    tmp = os.path.join(OUTD, "fin"); os.makedirs(tmp, exist_ok=True)
    B = bounds()
    src = os.path.join(tmp, "patched.mp4")
    patch(src0, src, tmp)
    # 1) 후크 H1 영상: [본편 S12c 립싱크 구간] + [S12c 키프레임 푸시인]
    h0, h1 = B["H1"]; s0, s1 = B["S12c"]
    seg = min(s1 - s0, h1 - h0)
    run(["-ss", f"{s0:.3f}", "-i", src, "-t", f"{seg:.3f}", "-an", "-vf", f"scale={W}:{H},fps=24,format=yuv420p",
         "-c:v", "libx264", "-crf", "16", os.path.join(tmp, "h1a.mp4")])
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_ashita_overrides as ov
    ov.W, ov.H = W, H
    rest = (h1 - h0) - seg
    parts = [os.path.join(tmp, "h1a.mp4")]
    if rest > 0.05:
        ov.cam(os.path.join(KF, "S12c-1.png"), os.path.join(tmp, "h1b.mp4"), rest + 0.1, "static")
        parts.append(os.path.join(tmp, "h1b.mp4"))
    ins = sum([["-i", p] for p in parts], [])
    run(ins + ["-filter_complex", "".join(f"[{i}:v]" for i in range(len(parts))) +
               f"concat=n={len(parts)}:v=1:a=0,trim=0:{h1 - h0:.3f},setpts=PTS-STARTPTS[v]", "-map", "[v]",
               "-c:v", "libx264", "-crf", "16", os.path.join(tmp, "h1.mp4")])
    # L22 음성: 본편 S12c에서 시작하는 위치를 그대로(입 모양 일치)
    l22 = next(f for f, tag, _ in SBJ["audio_map"] if tag == "L22")
    v22 = os.path.join(ROOT, f"assets/audio-overrides/ashita-kara/{l22}.mp3")
    t22 = h0 + (LOCK["L22"]["start"] - s0)
    d22 = dur(v22)
    bed = os.path.join(tmp, "hookbed.wav"); hook_bed(bed)
    grade = "eq=contrast=1.03:saturation=0.96:gamma=0.99,noise=alls=4:allf=t+u"
    fc = (f"[1:v]setpts=PTS-STARTPTS+{h0:.3f}/TB[h];[0:v][h]overlay=enable='between(t,{h0:.3f},{h1:.3f})':eof_action=pass,{grade},format=yuv420p[v];"
          f"[0:a]volume=enable='between(t,{t22 - 0.2:.3f},{t22 + d22 + 0.3:.3f})':volume=0.5[ab];"
          f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={int(t22 * 1000)}|{int(t22 * 1000)}[vo];"
          f"[3:a]aformat=sample_rates=44100:channel_layouts=stereo[hb];"
          f"[ab][vo][hb]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89[a]")
    main_out = os.path.join(tmp, "main.mp4")
    run(["-i", src, "-i", os.path.join(tmp, "h1.mp4"), "-i", v22, "-i", bed, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", main_out])
    print(f"본편 마무리: {main_out} ({dur(main_out):.2f}초), H1 음성 L22 {t22:.2f}s")
    if not outro_on:
        return
    # 4) 아웃트로 + 엔드카드
    outro = os.path.join(OUTD, "ashita-outro.mp4")
    meta = json.load(open(os.path.join(OUTD, "ashita-outro.json")))
    hs = meta["host_start"]
    cta = os.path.join(tmp, "outro-cta.mp4")
    # 「チャンネル登録と高評価」 멘트(OUT1 약 4.3~6.0초)에 맞춰 버튼 등장, 다음 진행자 컷 직전에 퇴장
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), outro, cta,
                    f"{hs[0] + 4.3:.2f}", f"{hs[0] + 5.0:.2f}", f"{hs[1] - 0.2:.2f}"], check=True)
    final = os.path.join(OUTD, "ashita-kara-final.mp4")
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), main_out, final], check=True, env=env)
    # 5) 전달본
    dd = os.path.join(ROOT, "deliveries", "ashita-kara"); os.makedirs(dd, exist_ok=True)
    for f in glob.glob(os.path.join(dd, "ashita-kara-final.mp4.part-*")):
        os.remove(f)
    subprocess.run(["split", "-b", "28m", "-d", final, os.path.join(dd, "ashita-kara-final.mp4.part-")], check=True)
    run(["-i", final, "-vf", "scale=-2:480", "-c:v", "libx264", "-crf", "28", "-c:a", "aac", "-b:a", "96k",
         os.path.join(dd, "ashita-kara-final-480p.mp4")])
    print(f"완성: {final} ({dur(final):.1f}초) / 본편 {dur(main_out):.1f}초 / 아웃트로 {dur(cta):.1f}초")


if __name__ == "__main__":
    main()
