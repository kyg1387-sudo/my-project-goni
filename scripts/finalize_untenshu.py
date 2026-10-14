#!/usr/bin/env python3
"""『運転手のくせに』 PHASE 6 마무리 (로컬, 무과금). finalize_ashita.py 구조 + 運転手 교훈(R33·R34·R37·R38).

1) 조립 후 패치(구운 자막을 덮으므로 패치 클립에 같은 자막을 같은 시각으로 다시 굽는다)
   - LISTEN: 두 사람이 보이는 립싱크 컷 = 립싱크 클립 위에 「말하지 않는 사람만 움직이는 i2v」를 그 사람 윤곽(깃털 마스크)으로 합성
     (R34 — OmniHuman은 말하지 않는 사람까지 입을 움직이거나 돌아본다. 정지 고정은 「얼어 있는 사람」이라 금지)
   - FX: 편집 카메라(제8장 6) — S06e 더치 5°+핸드헬드(갑질 1회), S20a 더치 7°(몰락 1회)
   - LCUT: 4.5초 넘는 립싱크 대사는 말 끝 무렵 듣는 사람의 실제 반응(i2v)으로 잠깐 넘어갔다 돌아온다(제10장 8)
   - 후크 재사용: H0a = S20a 실제 클립(더치 7°), H1 = S06e 합성 클립 + L11 음성(입 모양 위치)
2) 소리: 후크 0~4.3초 드론+심장 박동(−60dB 2초 무음 금지), S18 첫머리 블랙박스 스피커 음(L11 원음 대역 제한),
   S17b 문 열림 직전 문손잡이 소리
3) 밝기: 밤 장면 평균 40/255 미만이면 어두운 중간 톤만 곡선으로 들어 올림(R55 LIFT) + 전편 공통 그레이딩·그레인
4) 아웃트로: out/untenshu-outro.mp4(build_untenshu_outro.py) + 구독 버튼 → append_outro.py → 엔드카드
5) 전달본: deliveries/untenshu/untenshu-final.mp4(28MB 조각) + 480p
사용법: python3 scripts/finalize_untenshu.py <burn 완성본.mp4> [--no-outro | --outro-only]
입력: assets/preview/untenshu/sceneNN.mp4(생성 클립, export_files), assets/preview/untenshu-omni/omniNN.mp4(burn export_omni),
      assets/preview/untenshu-listen/sceneNN.mp4·untenshu-drv/scene01.mp4(듣는 사람 i2v)
"""
import glob
import json
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = shutil.which("ffmpeg")
OUTD = os.path.join(ROOT, "out")
SBJ = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "untenshu.json"), encoding="utf-8"))
SB = SBJ["scenes"]
AUDIO = json.load(open(os.path.join(ROOT, "scripts", "audio", "untenshu.json"), encoding="utf-8"))
LOCK = {l["tag"]: l for l in json.load(open(os.path.join(ROOT, "productions", "untenshu-ja", "lock.json"), encoding="utf-8"))["lines"]}
KF = os.path.join(ROOT, "assets", "portraits", "untenshu-keyframes")
PREV = os.path.join(ROOT, "assets", "preview", "untenshu")
OMNI = os.path.join(ROOT, "assets", "preview", "untenshu-omni")
OVR = os.path.join(ROOT, "assets", "video-overrides", "untenshu")
IDX = {s["id"]: i + 1 for i, s in enumerate(SB)}
W, H = 1920, 1080
NORM = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=24,setsar=1,format=yuv420p"

# 듣는 사람 합성: (말하지 않는 사람 i2v, 마스크 도형(키프레임 1344x768 좌표), 편집 카메라, 반복 필요 여부)
LISTEN = {
    "S06e": ("assets/preview/untenshu-drv/scene01.mp4", [("rect", 0, 0, 511, 768)], "dutch5+hh"),
    "S05e": ("assets/preview/untenshu-listen/scene01.mp4",
             [("ell", 160, 40, 440, 320), ("poly", [(150, 320), (570, 320), (585, 768), (125, 768)])], ""),
    "S07e": ("assets/preview/untenshu-listen/scene02.mp4",
             [("ell", 360, 100, 585, 360), ("poly", [(330, 370), (600, 370), (610, 768), (300, 768)])], ""),
    "S10b": ("assets/preview/untenshu-fix2/scene01-3s.mp4", [("rect", 0, 0, 600, 768)], ""),   # R45 새 구도: 기사 앞 왼쪽
}
FX = {"S20a": "dutch7",
      "S02b": "mirrorcrop"}   # R54: 룸미러 아래 매달린 빈 태그가 흔들려 「공중에 뜬 액자」처럼 보임 → 거울 안쪽으로 1.9배 당김
# 고니감독님 검수 수정(R41~R52): 장면 → (교체 클립, 사용 시작초, 사용 길이 — 그 뒤는 마지막 프레임 정지)
REDO = {
    "S06c": ("assets/preview/untenshu-fix1/scene01.mp4", 0.0, None),     # 룸미러 손님 2명(R42)
    "S06d": ("assets/preview/untenshu-fix1/scene02.mp4", 0.0, None),     # 大塚 옆 小川(R42)
    "S10a": ("assets/preview/untenshu-fix1/scene03.mp4", 0.0, None),     # 뒷좌석 무릎 위 액자(R45)
    "S15g": ("assets/preview/untenshu-fix2/scene02.mp4", 0.0, None),     # 뒷좌석 시점 룸미러(R48)
    "S13a": ("assets/preview/untenshu/scene60.mp4", 0.0, 1.2),           # 모자가 손에 있는 구간까지 → 정지(R46)
    "S09c": ("assets/preview/untenshu/scene38.mp4", 0.0, 0.15),          # 지폐가 좌석에 놓인 첫 프레임 정지(R43)
    "S17a": ("assets/auditions/untenshu-s10b-omni/omni-S17a.mp4", 0.0, None),   # 배경 고정 립싱크(R50)
    "S10b": ("assets/auditions/untenshu-omni2/omni-S10b.mp4", 0.0, None),       # 뒷좌석 구도 립싱크(R45)
    "S17f": ("assets/auditions/untenshu-omni2/omni-S17f.mp4", 0.0, None),       # 당황·홍조·땀(R51)
    "S18f": ("assets/auditions/untenshu-omni2/omni-S18f.mp4", 0.0, None),       # 당황·홍조·땀(R52)
    "S23c": ("assets/auditions/untenshu-s23c-omni/omni-S23c.mp4", 0.0, None),   # 미소 짓는 小川 립싱크(R55)
}
STILL_REDO = ["S06b", "S05b", "S08a", "S23b", "S13c"]   # 새 키프레임 정지+편집 카메라(R41·R42·R47)
# (말하는 컷, 대사 태그, 듣는 사람 반응 클립 장면, 반응 길이) — 같은 장면의 역방향 반응(제10장 8)
LCUT_OFF = True   # 고니감독님 「말하는 사람과 화면 인물 일치」(R44) — 듣는 사람 L컷 사용 안 함
LCUT = [("S05e", "L07", "S05c", 1.3), ("S06e", "L11", "S06c", 1.2), ("S07e", "L14", "S07d", 1.3),
        ("S11d", "L24", "S11e", 1.2), ("S11h", "P2", "S11i", 1.2), ("S12a", "L27", "S12b", 1.2),
        ("S18f", "L37", "S18b", 1.2), ("S19b", "L39", "S19c", 1.4), ("S20f", "L44", "S20d", 1.3),
        ("S21b", "L46", "S21a", 1.8)]
# 현장음(고니감독님 「현장감 있게 사운드」): 목소리 없는 환경음 베드(ElevenLabs SFX, assets/auditions/untenshu-sfx)를 장면 공간마다
# 대사 아래 낮게 깔고(−30 LUFS 정규화 후 BED_VOL), 공간이 바뀔 때 0.5초 교차. 무인 컷은 burn의 장면 현장음(mmaudio)이 이미 있어 건너뜀.
SFX = os.path.join(ROOT, "assets", "auditions", "untenshu-sfx")
BED_VOL = 0.55
# 공간별 목표 크기(LUFS): 비·차는 또렷이, 방 소리는 은은하게
TARGET = {"amb-meeting": -44.0, "amb-hospital": -44.0, "amb-lobby": -42.0, "amb-office": -38.0, "amb-garage-dawn": -36.0,
          "amb-lathe": -32.0, "amb-old-taxi": -32.0}
def bed_for(sid):
    if sid in ("H3",) or sid in AMB_SKIP:
        return None
    pre = sid[:3]
    table = {"H0a": "amb-meeting", "H0b": "amb-meeting", "H1": "amb-taxi-rain", "H2": "amb-meeting"}
    if sid in table:
        return table[sid]
    if pre in ("S01", "S02") or sid in ("S05b", "S05c", "S05d", "S05e", "S06b", "S06c", "S06d", "S06e", "S07a", "S07b", "S07c", "S07d", "S07e",
                                       "S08a", "S08b", "S15e", "S15g"):
        return "amb-taxi-drive"
    if sid in ("S05a", "S09e", "S10d") or pre == "S03":
        return "amb-rain-street"
    if pre in ("S09", "S10") or sid in ("S23b", "S23c", "S23d"):
        return "amb-taxi-rain"
    if pre == "S04" or sid in ("S22d", "S22e", "S22f", "S23a", "S23e"):
        return "amb-izakaya-rain"
    if pre in ("S11", "S12") or sid in ("S22a", "S22c"):
        return "amb-office"
    if pre == "S13" or sid == "S14d":
        return "amb-garage-dawn"
    if sid in ("S14a", "S14b"):
        return "amb-old-taxi"
    if sid == "S14c":
        return "amb-lathe"
    if sid in ("S15a", "S15b", "S15c", "S15d"):
        return "amb-hospital"
    if pre == "S16" or sid == "S22b":
        return "amb-lobby"
    if pre in ("S17", "S18", "S19", "S20", "S21"):
        return "amb-meeting"
    return None
AMB_SKIP = set(AUDIO_AMB := [s["id"] for s, p in zip(SB, AUDIO.get("ambience_prompts", [])) if p.strip()])
# 효과음: (장면, 장면 안 시각, 파일, 볼륨)
FOLEY = [("S01c", 0.8, "fx-wiper", 0.5), ("S03e", 0.1, "fx-car-pull-away", 0.7), ("S05a", 0.4, "fx-car-door-close", 0.6),
         ("S07a", -0.25, "fx-seat-kick", 0.9), ("S07a", 0.35, "fx-frame-fall", 0.8), ("S09b", 0.3, "fx-meter-beep", 0.5),
         ("S09c", 0.4, "fx-paper-toss", 0.7), ("S09e", 3.6, "fx-car-door-slam", 0.9), ("S10d", 4.2, "fx-car-door-close", 0.6),
         ("S10f", 0.0, "fx-car-pull-away", 0.6), ("S15e", 0.6, "fx-wiper", 0.4), ("S17b", 2.4, "fx-footsteps-marble", 0.6),
         ("S17g", 0.3, "fx-tablet-slide", 0.6), ("S20a", 0.2, "fx-knees-floor", 0.8), ("S22a", 0.4, "fx-pen-sign", 0.6),
         ("S23c", 0.2, "fx-umbrella-fold", 0.6), ("S23e", 0.0, "fx-car-pull-away", 0.6),
         # R49 발소리·동작음(고니감독님 「복도 걸을 때 구두 발소리」)
         ("S11b", 0.0, "fx-heels-office", 0.7), ("S16b", 0.0, "fx-heels-marble", 0.7), ("S16e", 0.0, "fx-heels-marble", 0.8),
         ("S16e", 4.5, "fx-heels-marble", 0.6), ("S22b", 0.0, "fx-men-shoes-corridor", 0.8), ("S22f", 0.3, "fx-men-shoes-wet", 0.6),
         ("S11h", 0.3, "fx-chair-creak", 0.6), ("S18b", 0.3, "fx-glasses-fold", 0.6), ("S11d", 0.4, "fx-documents", 0.6),
         ("S23a", 0.2, "fx-door-car-open", 0.6), ("S05a", 0.0, "fx-door-car-open", 0.5)]
# R53 장면별 강조 음악(고니감독님 「장면에 맞게 BGM 더 강하게」): (장면, 장면 안 시작초, 곡, 볼륨, 길이)
CUES = [("H0a", 0.0, "cue-hook", 0.55, 19.0), ("S06e", -1.5, "cue-outburst", 0.5, 12.0), ("S07a", -0.3, "cue-sorrow", 0.5, 9.0),
        ("S15a", 0.0, "cue-flashback", 0.5, 26.0), ("S17b", 0.0, "cue-reveal", 0.6, 12.0), ("S20a", 0.0, "cue-verdict", 0.5, 26.0),
        ("S21b", 0.0, "cue-hope", 0.45, 28.0)]
CUE_DIR = os.path.join(ROOT, "assets", "auditions", "untenshu-bgm-cues")
LIFT = "curves=all='0/0 0.06/0.13 0.25/0.38 0.6/0.72 1/1',eq=gamma=1.12:saturation=1.05"
LIFT_BELOW = 40.0


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


def line_file(tag):
    lid = next(f for f, t, _ in SBJ["audio_map"] if t == tag)
    p = os.path.join(ROOT, "assets", "audio-overrides", "untenshu", f"{lid}.mp3")
    return p if os.path.exists(p) else next(src for f, t, src in SBJ["audio_map"] if t == tag)


def src_clip(sid):
    """그 장면의 실제 클립: 검수 교체(REDO) → 립싱크 → i2v 생성 클립 → 교체 클립(정지) 순."""
    if sid in REDO and os.path.exists(os.path.join(ROOT, REDO[sid][0])):
        return os.path.join(ROOT, REDO[sid][0])
    for p in (os.path.join(OMNI, f"omni{IDX[sid]:02d}.mp4"), os.path.join(PREV, f"scene{IDX[sid]:02d}.mp4"),
              os.path.join(OVR, f"scene{IDX[sid]:02d}.mp4")):
        if os.path.exists(p):
            return p
    raise SystemExit(f"클립 없음: {sid}")


def mask_png(shapes, path):
    k, oy = W / 1344, (W * 768 / 1344 - H) / 2
    tr = lambda x, y: (x * k, y * k - oy)
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for sh in shapes:
        if sh[0] == "rect":
            d.rectangle([tr(sh[1], sh[2]), tr(sh[3], sh[4])], fill=255)
        elif sh[0] == "ell":
            d.ellipse([tr(sh[1], sh[2]), tr(sh[3], sh[4])], fill=255)
        else:
            d.polygon([tr(x, y) for x, y in sh[1]], fill=255)
    m.filter(ImageFilter.GaussianBlur(18)).save(path)


def fx_filter(fx):
    shake = "crop=1920:1080:x='(iw-1920)/2+9*sin(t*5.3)+4*sin(t*11.7)':y='(ih-1080)/2+6*sin(t*4.1)+3*sin(t*9.3)'"
    if fx == "hh":
        return f"scale=2112:1188,{shake}"
    if fx == "mirrorcrop":
        return "crop=iw/1.9:ih/1.9:(iw-iw/1.9)*0.55:ih*0.05,scale=1920:1080:flags=lanczos"
    if fx == "dutch7":
        return "rotate=7*PI/180:ow=iw:oh=ih:c=black,scale=2400:1350,crop=1920:1080"
    if fx == "dutch5+hh":
        return f"rotate=5*PI/180:ow=iw:oh=ih:c=black,scale=2400:1350,{shake}"
    return "null"


def listen_clip(sid, out, sec, tmp):
    """립싱크 + 말하지 않는 사람 i2v(그 사람 윤곽만) 합성, 짧으면 앞뒤로 되감아 이어 붙임(숨·깜빡임은 되감아도 자연스럽다)."""
    lis, shapes, fx = LISTEN[sid]
    mpath = os.path.join(tmp, f"mask_{sid}.png"); mask_png(shapes, mpath)
    lis = os.path.join(ROOT, lis)
    ll = dur(lis)
    lchain = f"[1:v]{NORM}"
    if ll < sec + 0.1:
        lchain += f",split[la][lb];[lb]reverse[lr];[la][lr]concat=n=2:v=1:a=0"
    lchain += f",trim=0:{sec + 0.05:.3f},setpts=PTS-STARTPTS,format=rgba[l]"
    fc = (f"[0:v]{NORM},tpad=stop_mode=clone:stop_duration=2,trim=0:{sec + 0.05:.3f},setpts=PTS-STARTPTS[o];{lchain};"
          f"[2:v]format=gray,scale={W}:{H}[m];[l][m]alphamerge[lm];[o][lm]overlay=0:0:shortest=1,{fx_filter(fx)},format=yuv420p[v]")
    run(["-i", src_clip(sid), "-i", lis, "-loop", "1", "-i", mpath, "-filter_complex", fc, "-map", "[v]", "-an",
         "-c:v", "libx264", "-crf", "16", out])


def fx_clip(src, out, fx, sec, start=0.0):
    run(["-ss", f"{start:.3f}", "-i", src, "-filter_complex",
         f"[0:v]{NORM},tpad=stop_mode=clone:stop_duration=2,trim=0:{sec + 0.05:.3f},setpts=PTS-STARTPTS,{fx_filter(fx)},format=yuv420p[v]",
         "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", out])


def patch(src, out, tmp):
    B = bounds()
    fdir = os.environ.get("FONTSDIR", "/usr/share/fonts")
    ass = os.path.join(ROOT, "subs", "untenshu.ass")
    segs, made = [], {}
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_untenshu_overrides as ov
    ov.W, ov.H = W, H
    for sid in STILL_REDO:
        a, b = B[sid]; c = os.path.join(tmp, f"S_{sid}.mp4")
        sc = next(x for x in SB if x["id"] == sid)
        ov.cam(os.path.join(KF, f"{sid}-1.png"), c, b - a + 0.1, sc["edit_fx"] or "push")
        segs.append((a, b, c)); made[sid] = c
    for sid, (clip, st, use) in REDO.items():
        if sid in LISTEN or not os.path.exists(os.path.join(ROOT, clip)):
            continue
        a, b = B[sid]; c = os.path.join(tmp, f"R_{sid}.mp4")
        cut = f",trim=0:{use:.3f},setpts=PTS-STARTPTS" if use else ""
        run(["-ss", f"{st:.3f}", "-i", os.path.join(ROOT, clip), "-filter_complex",
             f"[0:v]{NORM}{cut},tpad=stop_mode=clone:stop_duration={b - a + 1:.2f},trim=0:{b - a + 0.05:.3f},setpts=PTS-STARTPTS,format=yuv420p[v]",
             "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", c])
        segs.append((a, b, c)); made[sid] = c
    for sid in LISTEN:
        a, b = B[sid]; c = os.path.join(tmp, f"L_{sid}.mp4")
        listen_clip(sid, c, b - a, tmp); segs.append((a, b, c)); made[sid] = c
    for sid, fx in FX.items():
        a, b = B[sid]; c = os.path.join(tmp, f"F_{sid}.mp4")
        fx_clip(src_clip(sid), c, fx, b - a); segs.append((a, b, c)); made[sid] = c
    for sid, tag, lis, sec in ([] if LCUT_OFF else LCUT):
        if LOCK[tag]["dur"] < 4.5:
            continue
        e = LOCK[tag]["end"]
        a, b = e - sec, e + 0.15
        lo, hi = B[sid]
        a, b = max(a, lo + 1.5), min(b, hi - 0.6)
        if b - a < 0.8:
            continue
        c = os.path.join(tmp, f"C_{sid}.mp4")
        fx_clip(made.get(lis) or src_clip(lis), c, "", b - a + 0.1, start=0.6)
        segs.append((a, b, c))
    # 후크 재사용 컷
    h0, h1 = B["H0a"]; c = os.path.join(tmp, "H0a.mp4"); fx_clip(made["S20a"], c, "", h1 - h0); segs.append((h0, h1, c))
    h0, h1 = B["H1"]; c = os.path.join(tmp, "H1.mp4"); fx_clip(made["S06e"], c, "", h1 - h0); segs.append((h0, h1, c))
    inputs, fc, last = ["-i", src], [], "[0:v]"
    for k, (a, b, c) in enumerate(segs, start=1):
        inputs += ["-i", c]
        fc.append(f"[{k}:v]trim=0:{b - a:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={ass}:fontsdir={fdir}[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    run(inputs + ["-filter_complex", ";".join(fc), "-map", last, "-map", "0:a", "-c:v", "libx264", "-preset", "medium",
                  "-crf", "17", "-c:a", "copy", out])
    print("패치:", ", ".join(f"{os.path.basename(c)[:-4]} {a:.2f}-{b:.2f}" for a, b, c in segs))


def hook_bed(path):
    beat = lambda t: (f"sine=f=52:d=0.16,afade=t=out:st=0.04:d=0.12,volume=1.6,adelay={int(t * 1000)}|{int(t * 1000)}")
    fc = ("sine=f=48:d=4.3[s1];sine=f=96:d=4.3,volume=0.35[s2];anoisesrc=d=4.3:c=brown:a=0.25,lowpass=f=180[n];"
          "[s1][s2][n]amix=inputs=3:normalize=0,volume=0.30,afade=t=in:st=0:d=1.2,afade=t=out:st=3.9:d=0.4[dr];"
          f"{beat(1.55)}[b1];{beat(1.85)}[b2];{beat(2.95)}[b3];{beat(3.25)}[b4];"
          "[dr][b1][b2][b3][b4]amix=inputs=5:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo[a]")
    run(["-filter_complex", fc, "-map", "[a]", "-t", "4.3", path])


def door_click(path):
    """문손잡이: 짧은 금속성 클릭 2번 + 낮은 쿵(문이 밀리는 소리)."""
    fc = ("anoisesrc=d=0.05:c=white:a=0.6,bandpass=f=3200:width_type=q:w=4,afade=t=out:st=0:d=0.05[c1];"
          "anoisesrc=d=0.04:c=white:a=0.5,bandpass=f=2600:width_type=q:w=4,afade=t=out:st=0:d=0.04,adelay=140|140[c2];"
          "sine=f=90:d=0.35,afade=t=out:st=0.05:d=0.3,volume=0.6,adelay=260|260[th];"
          "[c1][c2][th]amix=inputs=3:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo[a]")
    run(["-filter_complex", fc, "-map", "[a]", "-t", "0.7", path])


def soundscape(path, total, tmp):
    """현장음 베드(공간별 연속 구간마다 루프·교차 0.5초) + 효과음 → 한 트랙 wav."""
    B = bounds()
    runs = []
    for sc in SB:
        bed = bed_for(sc["id"]); a, b = B[sc["id"]]
        if bed and runs and runs[-1][0] == bed and abs(runs[-1][2] - a) < 0.1:
            runs[-1][2] = b
        elif bed:
            runs.append([bed, a, b])
    norm = {}
    for bed in {r[0] for r in runs} | {f[2] for f in FOLEY}:
        src = os.path.join(SFX, f"{bed}.mp3")
        if not os.path.exists(src):
            print("현장음 없음(건너뜀):", bed); continue
        n = os.path.join(tmp, f"n_{bed}.wav")
        e = subprocess.run([FF, "-i", src, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        lufs = float([l for l in e.splitlines() if l.strip().startswith("I:")][-1].split()[1])
        target = TARGET.get(bed, -20.0 if bed.startswith("fx-") else -30.0)
        gain = max(-30.0, min(20.0, target - lufs))          # 거의 무음인 방 소리를 −30까지 끌어올리면 잡음이 커진다 → +20dB 상한
        run(["-i", src, "-af", f"volume={gain:.1f}dB,aformat=sample_rates=44100:channel_layouts=stereo", n]); norm[bed] = n
    ins, fc, labels = [], [], []
    for bed, a, b in runs:
        if bed not in norm:
            continue
        k = len(ins) // 4
        ins += ["-stream_loop", "-1", "-i", norm[bed]]
        L = b - a + 0.5
        fc.append(f"[{k}:a]atrim=start={(a * 7.3) % 5:.2f}:duration={L:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.5,"
                  f"afade=t=out:st={L - 0.5:.3f}:d=0.5,volume={BED_VOL},adelay={int(max(0, a - 0.25) * 1000)}|{int(max(0, a - 0.25) * 1000)}[b{k}]")
        labels.append(f"[b{k}]")
    for sid, off, fx, vol in FOLEY:
        if fx not in norm:
            continue
        k = len(ins) // 4
        ins += ["-stream_loop", "0", "-i", norm[fx]]
        t = max(0.0, B[sid][0] + off)
        fc.append(f"[{k}:a]volume={vol:.2f},adelay={int(t * 1000)}|{int(t * 1000)}[f{k}]"); labels.append(f"[f{k}]")
    for sid, off, cue, vol, L in CUES:
        src = os.path.join(CUE_DIR, f"{cue}.mp3")
        if not os.path.exists(src):
            print("강조 음악 없음(건너뜀):", cue); continue
        k = len(ins) // 4
        ins += ["-stream_loop", "0", "-i", src]
        t = max(0.0, B[sid][0] + off)
        fc.append(f"[{k}:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{L:.2f},asetpts=PTS-STARTPTS,"
                  f"equalizer=f=2000:t=q:w=1.0:g=-4,loudnorm=I=-20:TP=-3,volume={vol},afade=t=in:d=0.8,"
                  f"afade=t=out:st={L - 2.5:.2f}:d=2.5,adelay={int(t * 1000)}|{int(t * 1000)}[c{k}]")
        labels.append(f"[c{k}]")
    if not labels:
        run(["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo", "-t", f"{total:.2f}", path]); return
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{total:.3f}[a]")
    run(ins + ["-filter_complex", ";".join(fc), "-map", "[a]", path])
    print(f"현장음: 베드 {len(runs)}구간, 효과음 {len(FOLEY)}개, 강조 음악 {len(CUES)}곡")


def dark_ranges(src):
    """장면마다 가운데 프레임 평균 밝기 → 40/255 미만 장면 구간(R55)."""
    B, out = bounds(), []
    tmpf = os.path.join(OUTD, "fin", "_lum.png")
    for s in SB:
        a, b = B[s["id"]]
        run(["-ss", f"{(a + b) / 2:.3f}", "-i", src, "-frames:v", "1", "-vf", "scale=320:-2", tmpf])
        im = Image.open(tmpf).convert("L")
        mean = sum(im.getdata()) / (im.width * im.height)
        if mean < LIFT_BELOW:
            out.append((s["id"], a, b, mean))
    return out


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
    dark = dark_ranges(src)
    print("밝기 보정(평균<40):", ", ".join(f"{sid} {m:.0f}" for sid, _, _, m in dark) or "없음")
    # 음성: H1 = L11(본편 S06e와 같은 입 모양 위치), S18a 첫머리 = L11 블랙박스 스피커 음, S17b 직전 문손잡이
    l11 = line_file("L11")
    h0 = B["H1"][0]; s0 = B["S06e"][0]
    t_h1 = h0 + (LOCK["L11"]["start"] - s0)
    t_rec = B["S18a"][0] + 0.3
    t_door = max(0.0, B["S17b"][0] - 0.15)
    bed = os.path.join(tmp, "hookbed.wav"); hook_bed(bed)
    amb = os.path.join(tmp, "soundscape.wav"); soundscape(amb, dur(src), tmp)
    door = os.path.join(tmp, "door.wav"); door_click(door)
    ranges = "+".join(f"between(t,{a:.3f},{b:.3f})" for _, a, b, _ in dark) or "0"
    lift = ",".join(f"{f.split('=', 1)[0]}=enable='{ranges}':{f.split('=', 1)[1]}" for f in LIFT.split(",", 1))
    grade = f"{lift},eq=contrast=1.03:saturation=0.96:gamma=0.99,noise=alls=4:allf=t+u"
    d11 = dur(l11)
    fc = (f"[0:v]{grade},format=yuv420p[v];"
          f"[0:a]volume=enable='between(t,{t_h1 - 0.2:.3f},{t_h1 + d11 + 0.3:.3f})':volume=0.5[ab];"
          f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[x1][x2];"
          f"[x1]adelay={int(t_h1 * 1000)}|{int(t_h1 * 1000)}[vo];"
          f"[x2]highpass=f=300,lowpass=f=3400,acrusher=bits=9:mix=0.25,volume=0.8,adelay={int(t_rec * 1000)}|{int(t_rec * 1000)}[rec];"
          f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo[hb];"
          f"[3:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={int(t_door * 1000)}|{int(t_door * 1000)}[dc];"
          f"[4:a]aformat=sample_rates=44100:channel_layouts=stereo[sc];"
          f"[ab][vo][rec][hb][dc][sc]amix=inputs=6:normalize=0:duration=first,alimiter=limit=0.89[a]")
    run(["-i", src, "-i", l11, "-i", bed, "-i", door, "-i", amb, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", main_out])
    print(f"본편 마무리: {main_out} ({dur(main_out):.2f}초), H1 L11 {t_h1:.2f}s, 블랙박스 {t_rec:.2f}s, 문 {t_door:.2f}s")
    if outro_on:
        outro(main_out, tmp)


def outro(main_out, tmp):
    outro = os.path.join(OUTD, "untenshu-outro.mp4")
    meta = json.load(open(os.path.join(OUTD, "untenshu-outro.json")))
    hs = meta["host_start"]
    cta = os.path.join(tmp, "outro-cta.mp4")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), outro, cta,
                    f"{hs[0] + 4.3:.2f}", f"{hs[0] + 5.0:.2f}", f"{hs[1] - 0.2:.2f}"], check=True)
    final = os.path.join(OUTD, "untenshu-final.mp4")
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), main_out, final], check=True, env=env)
    dd = os.path.join(ROOT, "deliveries", "untenshu"); os.makedirs(dd, exist_ok=True)
    for f in glob.glob(os.path.join(dd, "untenshu-final.mp4.part-*")):
        os.remove(f)
    subprocess.run(["split", "-b", "28m", "-d", final, os.path.join(dd, "untenshu-final.mp4.part-")], check=True)
    run(["-i", final, "-vf", "scale=-2:480", "-c:v", "libx264", "-crf", "28", "-c:a", "aac", "-b:a", "96k",
         os.path.join(dd, "untenshu-final-480p.mp4")])
    print(f"완성: {final} ({dur(final):.1f}초) / 본편 {dur(main_out):.1f}초 / 아웃트로 {dur(cta):.1f}초")


if __name__ == "__main__":
    main()
