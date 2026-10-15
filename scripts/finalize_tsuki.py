#!/usr/bin/env python3
"""『月に帰った契約社員』 PHASE 6 마무리 (로컬, 무과금) — finalize_ashita.py 구조, 이 작품 설계(7-3절·9절)를 자동 반영.

1) 조립 후 패치(자막이 구워진 화면 위에 같은 자막을 같은 시각으로 다시 굽는다)
   - FX: i2v 컷 편집 카메라(스토리보드 edit_fx: handheld·dutch5·dutch7·dollyzoom·pullback·tiltdown·pushin) — 원본 assets/preview/tsuki/sceneNN.mp4
   - LCUT: 4.5초 넘는 립싱크 대사 → 말 끝 무렵 같은 장면의 듣는 사람(face 컷) 키프레임 푸시인으로 잠깐(목소리 계속)
2) 후크: 0~3.5초 서버 팬 정지 드론 + 심장 박동 1회(자막 등장 0.5초), H1 = 본편 S14c 립싱크 구간 + L26 음성 믹스
3) 색감 통일 + 어두운 구간(S18, S16b) 중간 톤 리프트(평균 40/255 기준, 휴대폰)
4) 아웃트로(build_tsuki_outro.py 산출) → append_outro.py → 전달본(28MB 조각 + 480p)
사용법: python3 scripts/finalize_tsuki.py <burn 완성본.mp4> [--no-outro | --outro-only]
"""
import glob, json, os, shutil, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = shutil.which("ffmpeg")
OUTD = os.path.join(ROOT, "out")
SBJ = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "tsuki.json"), encoding="utf-8"))
SB = SBJ["scenes"]
AUDIO = json.load(open(os.path.join(ROOT, "scripts", "audio", "tsuki.json"), encoding="utf-8"))
LOCK = {l["tag"]: l for l in json.load(open(os.path.join(ROOT, "productions", "tsuki-ja", "lock.json"), encoding="utf-8"))["lines"]}
KF = os.path.join(ROOT, "assets", "portraits", "tsuki-keyframes")
W, H = 1920, 1080
FX_MAP = {"handheld": "hh", "dutch5": "dutch5+hh", "dutch7": "dutch7", "dollyzoom": "dollyzoom", "pullback": "pull", "tiltdown": "tilt", "pushin": "push"}
FX = {s["id"]: FX_MAP[next(f for f in s["edit_fx"].split(",") if f in FX_MAP)] for s in SB
      if s["tier"] == "lite" and any(f in FX_MAP for f in s["edit_fx"].split(","))}
# L컷: 4.5초 넘는 립싱크 대사 → 같은 장면에서 그 컷 뒤 첫 face 컷(듣는 사람)
LCUT = []
for i, s in enumerate(SB):
    if s["tier"] == "omni" and s["line"] and LOCK[s["line"]]["dur"] > 4.5:
        lis = next((x for x in SB[i + 1:i + 4] if x["scene"] == s["scene"] and x["kind"] == "face" and x.get("keyframe")), None)
        if lis:
            LCUT.append((s["id"], s["line"], lis["id"], 1.3))
DARK = [("S18a", "S18h"), ("S16ba", "S16bh")]
LIFT = "curves=all='0/0 0.06/0.13 0.25/0.38 0.6/0.72 1/1',eq=gamma=1.10:saturation=1.04"
HOOK_VOICE = ("H1", "S14c", "L26")


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


def dur(p):
    e = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def bounds():
    d = [float(x) for x in AUDIO["scene_durations"]]
    t, out = 0.0, {}
    for k, (s, x) in enumerate(zip(SB, d)):
        out[s["id"]] = (t, t + x); t += x - (1 / 24 if k < len(d) - 1 else 0)
    return out


def fx_filter(fx):
    zp = lambda z, x="iw/2-(iw/zoom/2)", y="ih/2-(ih/zoom/2)": f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s=1920x1080:fps=24"
    shake = "crop=1920:1080:x='(iw-1920)/2+9*sin(t*5.3)+4*sin(t*11.7)':y='(ih-1080)/2+6*sin(t*4.1)+3*sin(t*9.3)'"
    if fx == "hh":
        return f"scale=2112:1188,{shake}"
    if fx == "push":
        return zp("1+0.05*min(1,on/120)")
    if fx == "pull":
        return zp("1.06-0.06*min(1,on/120)")
    if fx == "tilt":
        return zp("1.10", y="(ih-ih/zoom)*(0.1+0.8*min(1,on/110))")
    if fx == "dollyzoom":
        return zp("if(lt(on,38),1+0.14*on/38,1.14)")
    if fx == "dutch7":
        return "rotate=7*PI/180:ow=iw:oh=ih:c=black,scale=2400:1350,crop=1920:1080"
    if fx == "dutch5+hh":
        return f"rotate=5*PI/180:ow=iw:oh=ih:c=black,scale=2400:1350,{shake}"
    return "null"


def fx_clip(src, out, fx, sec):
    base = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=24,tpad=stop_mode=clone:stop_duration=2,trim=0:{sec + 0.05:.3f},setpts=PTS-STARTPTS"
    run(["-i", src, "-filter_complex", f"[0:v]{base},{fx_filter(fx)},format=yuv420p[v]", "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", out])


def patch(src, out, tmp):
    B = bounds()
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_tsuki_overrides as ov
    ov.W, ov.H = W, H
    fdir = os.environ.get("FONTSDIR", "/usr/share/fonts")
    ass = os.path.join(ROOT, "subs", "tsuki.ass")
    segs = []
    idx = {x["id"]: i + 1 for i, x in enumerate(SB)}
    for sid, fx in FX.items():
        a, b = B[sid]; c = os.path.join(tmp, f"f_{sid}.mp4")
        clip = os.path.join(ROOT, f"assets/preview/tsuki/scene{idx[sid]:02d}.mp4")
        if not os.path.exists(clip):
            print("편집 카메라 원본 없음(건너뜀):", sid); continue
        fx_clip(clip, c, fx, b - a); segs.append((a, b, c))
    for sid, tag, lis, sec in LCUT:
        e = LOCK[tag]["end"]
        a, b = e - sec, e + 0.15
        lo, hi = B[sid]
        a, b = max(a, lo + 1.5), min(b, hi - 0.6)
        if b - a < 0.8:
            continue
        c = os.path.join(tmp, f"l_{sid}.mp4")
        ov.cam(os.path.join(KF, f"{lis}-1.png"), c, b - a + 0.1, "push"); segs.append((a, b, c))
    if not segs:
        shutil.copy(src, out); return
    inputs, fc, last = ["-i", src], [], "[0:v]"
    for k, (a, b, c) in enumerate(segs, start=1):
        inputs += ["-i", c]
        fc.append(f"[{k}:v]trim=0:{b - a:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={ass}:fontsdir={fdir}[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    run(inputs + ["-filter_complex", ";".join(fc), "-map", last, "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "copy", out])
    print("패치:", ", ".join(f"{sid} {a:.1f}-{b:.1f}" for (a, b, _), sid in zip(segs, list(FX) + [l[0] for l in LCUT])))


def hook_bed(path):
    """0~3.8초: 서버 팬이 멈추는 드론(피치가 천천히 내려감) + 심장 박동 1회(0.5초, 자막 등장), 끝 0.3초 페이드."""
    fc = ("sine=f=120:d=3.8,aeval=val(0)*(1-0.5*t/3.8):c=mono[s1];anoisesrc=d=3.8:c=brown:a=0.3,lowpass=f=220[n];"
          "[s1][n]amix=inputs=2:normalize=0,volume=0.32,afade=t=in:st=0:d=0.3,afade=t=out:st=3.5:d=0.3[dr];"
          "sine=f=52:d=0.18,afade=t=out:st=0.05:d=0.13,volume=1.7,adelay=500|500[b1];sine=f=52:d=0.16,afade=t=out:st=0.04:d=0.12,volume=1.3,adelay=800|800[b2];"
          "[dr][b1][b2]amix=inputs=3:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo[a]")
    run(["-filter_complex", fc, "-map", "[a]", "-t", "3.8", path])


def main():
    src0 = sys.argv[1]
    outro_on = "--no-outro" not in sys.argv
    tmp = os.path.join(OUTD, "fin"); os.makedirs(tmp, exist_ok=True)
    main_out = os.path.join(tmp, "main.mp4")
    if "--outro-only" in sys.argv:
        return outro(main_out, tmp)
    B = bounds()
    src = os.path.join(tmp, "patched.mp4")
    patch(src0, src, tmp)
    hid, ssid, tag = HOOK_VOICE
    h0, h1 = B[hid]; s0, s1 = B[ssid]
    seg = min(s1 - s0, h1 - h0)
    run(["-ss", f"{s0:.3f}", "-i", src, "-t", f"{seg:.3f}", "-an", "-vf", f"scale={W}:{H},fps=24,format=yuv420p", "-c:v", "libx264", "-crf", "16", os.path.join(tmp, "h1a.mp4")])
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_tsuki_overrides as ov
    ov.W, ov.H = W, H
    rest = (h1 - h0) - seg
    parts = [os.path.join(tmp, "h1a.mp4")]
    if rest > 0.05:
        ov.cam(os.path.join(KF, f"{ssid}-1.png"), os.path.join(tmp, "h1b.mp4"), rest + 0.1, "static"); parts.append(os.path.join(tmp, "h1b.mp4"))
    ins = sum([["-i", p] for p in parts], [])
    run(ins + ["-filter_complex", "".join(f"[{i}:v]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0,trim=0:{h1 - h0:.3f},setpts=PTS-STARTPTS[v]",
               "-map", "[v]", "-c:v", "libx264", "-crf", "16", os.path.join(tmp, "h1.mp4")])
    lf = next(f for f, t, _ in SBJ["audio_map"] if t == tag)
    vfile = os.path.join(ROOT, f"assets/audio-overrides/tsuki/{lf}.mp3")
    tv = h0 + (LOCK[tag]["start"] - s0); dv = dur(vfile)
    bed = os.path.join(tmp, "hookbed.wav"); hook_bed(bed)
    lifts = []
    for a_id, b_id in DARK:
        b0, b1 = B[a_id][0], B[b_id][1]
        lifts.append(",".join(f"{f.split('=', 1)[0]}=enable='between(t,{b0:.3f},{b1:.3f})':{f.split('=', 1)[1]}" for f in LIFT.split(",", 1)))
    grade = ",".join(lifts) + ",eq=contrast=1.03:saturation=0.97:gamma=0.99,noise=alls=4:allf=t+u"
    fc = (f"[1:v]setpts=PTS-STARTPTS+{h0:.3f}/TB[h];[0:v][h]overlay=enable='between(t,{h0:.3f},{h1:.3f})':eof_action=pass,{grade},format=yuv420p[v];"
          f"[0:a]volume=enable='between(t,{tv - 0.2:.3f},{tv + dv + 0.3:.3f})':volume=0.5[ab];"
          f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={int(tv * 1000)}|{int(tv * 1000)}[vo];"
          f"[3:a]aformat=sample_rates=44100:channel_layouts=stereo[hb];"
          f"[ab][vo][hb]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89[a]")
    run(["-i", src, "-i", os.path.join(tmp, "h1.mp4"), "-i", vfile, "-i", bed, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", main_out])
    print(f"본편 마무리: {main_out} ({dur(main_out):.2f}초), H1 음성 {tag} {tv:.2f}s, L컷 {len(LCUT)}, FX {len(FX)}")
    if outro_on:
        outro(main_out, tmp)


def outro(main_out, tmp):
    outro = os.path.join(OUTD, "tsuki-outro.mp4")
    meta = json.load(open(os.path.join(OUTD, "tsuki-outro.json")))
    hs = meta["host_start"]
    cta = os.path.join(tmp, "outro-cta.mp4")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), outro, cta, f"{hs[1] + 4.0:.2f}", f"{hs[1] + 4.8:.2f}", f"{hs[2] - 0.2:.2f}"], check=True)
    final = os.path.join(OUTD, "tsuki-final.mp4")
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), main_out, final], check=True, env=env)
    dd = os.path.join(ROOT, "deliveries", "tsuki"); os.makedirs(dd, exist_ok=True)
    for f in glob.glob(os.path.join(dd, "tsuki-final.mp4.part-*")):
        os.remove(f)
    subprocess.run(["split", "-b", "28m", "-d", final, os.path.join(dd, "tsuki-final.mp4.part-")], check=True)
    run(["-i", final, "-vf", "scale=-2:480", "-c:v", "libx264", "-crf", "28", "-c:a", "aac", "-b:a", "96k", os.path.join(dd, "tsuki-final-480p.mp4")])
    print(f"완성: {final} ({dur(final):.1f}초) / 본편 {dur(main_out):.1f}초 / 아웃트로 {dur(cta):.1f}초")


if __name__ == "__main__":
    main()
