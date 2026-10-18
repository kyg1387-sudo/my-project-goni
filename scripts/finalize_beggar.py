#!/usr/bin/env python3
"""『みすぼらしい老人は、財閥会長だった』 PHASE 6 마무리 (로컬, 무과금) — finalize_tsuki.py 구조를 이 작품 후반 메모(08_후반메모.md)에 맞춰 줄임.

1) 조립 후 패치(구워진 자막 위에 같은 자막을 다시 굽는다)
   - PHONE: S06c 榊의 휴대폰 화면에 본편 S04c(이와키가 입구에서 할아버지를 막는 장면) 키프레임을 손떨림 영상처럼 lcd 합성(고니감독님 지적 2:56)
   - MANUAL: S06g(i2v 2회 웨이터가 카메라로 걸어옴) → 홀 키프레임 푸시인 + 구석의 할아버지 와이드로 나눔(5초 넘는 한 구도 금지)
2) 색: S10e 회상 세피아, 전편 공통 미세 그레인·대비
3) 후크 0~3.6초: BGM 없는 구간에 저음 드론 + 심장 박동 2회(−60dB 2초 무음 방지, 제12장 1)
4) 라우드니스 −14 LUFS / −1 dBTP(제12장 3)
5) 아웃트로(build_beggar_outro.py 산출) + 구독 버튼(outro_cta_overlay.py) + 엔드카드(append_outro.py) → 전달본(28MB 조각 + 480p)
사용법: python3 scripts/finalize_beggar.py <burn 완성본.mp4> [--no-outro]
"""
import glob, json, os, shutil, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = shutil.which("ffmpeg")
OUTD = os.path.join(ROOT, "out")
SB = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "beggar-chairman.json"), encoding="utf-8"))["scenes"]
AUDIO = json.load(open(os.path.join(ROOT, "scripts", "audio", "beggar-chairman.json"), encoding="utf-8"))
KF = os.path.join(ROOT, "assets", "portraits", "beggar-chairman-keyframes")
W, H = 1920, 1080
# (컷, 키프레임, 컷 시작 후 초, 길이 None=끝까지)
MANUAL = [("S06g", "S04a", 0.0, 3.9), ("S06g", "S05o", 3.9, None)]
SEPIA = ["S10e", "S10f"]
# 고니감독님 지적(0:04): S10r 지배인 표정·할아버지 흔들림 부자연 → 키프레임 r21 + i2v 재생성 클립으로 본편 S10r과 후크 H0(S10r 재사용) 모두 교체
CLIPS = [("S10r", "assets/preview/beggar-chairman/scene81.mp4"), ("H0", "assets/preview/beggar-chairman/scene81.mp4"),
         # 8:03 L41: 앞 岩城의 입이 같이 움직임 → 源蔵 CU + 岩城 뒷모습(r22-3) 립싱크, 구동 음성은 본편 정렬(line079 +0.065초)
         ("S14d", "assets/auditions/beggar-s14d-omni/omni-s14d.mp4")]
# S06c 휴대폰 화면 사각형(키프레임 1344x768 기준, r9 S06c-1) — 화면 안쪽 꼭짓점 TL, TR, BR, BL
# r20 S06c-3(고니감독님 지적 2:55: 팔이 차 앞 허공으로 뻗은 r9를 뒷좌석 손 가까이 인서트로 교체, r9는 S06c-1_old.png)
PHONE = ("S06c", "S04c", [(522, 341), (751, 335), (754, 451), (523, 457)])  # 가로로 든 휴대폰


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def bounds():
    d = [float(x) for x in AUDIO["scene_durations"]]
    t, out = 0.0, {}
    for k, (s, x) in enumerate(zip(SB, d)):
        out[s["id"]] = (t, t + x); t += x - (1 / 24 if k < len(d) - 1 else 0)
    return out


def coeffs(dst, src):
    m = []
    for (x, y), (u, v) in zip(dst, src):
        m += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
    return np.linalg.solve(np.array(m, float), np.array([c for p in src for c in p], float)).tolist()


def phone_clip(out, sec, tmp):
    """휴대폰 화면에 본편 장면을 세로 영상처럼 띄우고(손떨림 흉내 = 프레임마다 조금씩 이동), lcd 느낌(밝기·푸른 기·반사)을 준 뒤 푸시인."""
    sid, src_id, quad = PHONE
    base = Image.open(os.path.join(KF, f"{sid}-1.png")).convert("RGB")
    src = Image.open(os.path.join(KF, f"{src_id}-1.png")).convert("RGB")
    sw, sh = src.size
    (x0, y0), (x1, _), (_, y2) = quad[0], quad[1], quad[3]
    ratio = (x1 - x0) / (y2 - y0)  # 화면 사각형 비율에 맞춘 가로 영상
    cw = int(sw * 0.9); chh = min(sh, int(cw / ratio))
    n = int(sec * 24) + 2
    fdir = os.path.join(tmp, "phone"); os.makedirs(fdir, exist_ok=True)
    PW = 480; PH = int(PW / ratio)
    for i in range(n):
        dx = int((sw - cw) * 0.5 + 14 * np.sin(i * 0.37) + 7 * np.sin(i * 1.1))
        # 휴대폰으로 찍은 영상처럼: 좌우 흔들림 + 미세 회전·확대 흔들림 + 약간 무른 화질(고니감독님 지적 2:55 — 영화 장면처럼 너무 깨끗함)
        z = 1.08 + 0.02 * np.sin(i * 0.23)
        cw2, ch2 = int(cw / z), int(chh / z); dy = int((chh - ch2) * (0.5 + 0.35 * np.sin(i * 0.53)))
        crop = src.crop((dx, dy + (sh - chh) // 2, dx + cw2, dy + (sh - chh) // 2 + ch2)).rotate(1.2 * np.sin(i * 0.41), resample=Image.BICUBIC).resize((PW, PH))
        crop = crop.filter(ImageFilter.GaussianBlur(0.7))
        crop = Image.blend(crop, Image.new("RGB", crop.size, (215, 228, 255)), 0.10)  # 백라이트 푸른 기
        d = ImageDraw.Draw(crop)
        d.rectangle((0, PH - 10, PW, PH - 5), fill=(90, 90, 90)); d.rectangle((0, PH - 10, int(PW * (0.15 + 0.6 * i / n)), PH - 5), fill=(235, 50, 50))  # 진행 바
        warp = crop.transform(base.size, Image.PERSPECTIVE, coeffs(quad, [(0, 0), (PW, 0), (PW, PH), (0, PH)]), Image.BICUBIC)
        mask = Image.new("L", base.size, 0); ImageDraw.Draw(mask).polygon(quad, fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(0.8))
        fr = Image.composite(warp, base, mask)
        glare = Image.new("RGB", base.size, (255, 255, 255))
        fr = Image.composite(Image.blend(fr, glare, 0.06), fr, mask)  # 유리 반사
        fr.save(os.path.join(fdir, f"{i:04d}.png"))
    run(["-framerate", "24", "-i", os.path.join(fdir, "%04d.png"), "-vf",
         f"scale={W * 2}:{H * 2},zoompan=z='1+0.06*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=24,format=yuv420p",
         "-frames:v", str(n), "-c:v", "libx264", "-crf", "16", out])


def patch(src, out, tmp):
    B = bounds()
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_beggar_overrides as ov
    ov.W, ov.H = W, H
    ass = os.path.join(ROOT, "subs", "beggar-chairman.ass")
    fdir = os.environ.get("FONTSDIR", "/usr/share/fonts")
    segs = []
    a, b = B[PHONE[0]]
    c = os.path.join(tmp, "phone.mp4"); phone_clip(c, b - a + 0.1, tmp); segs.append((a, b, c))
    for sid, clip in CLIPS:  # 조립 후 다시 만든 i2v 클립을 그 컷 자리에 그대로 덮는다(burn 재실행 없이, 제12장 4)
        a, b = B[sid]; segs.append((a, b, os.path.join(ROOT, clip)))
    for sid, kf_id, off, sec in MANUAL:
        lo, hi = B[sid]
        a = lo + off; b = hi - 0.02 if sec is None else min(hi - 0.02, a + sec)
        c = os.path.join(tmp, f"m_{sid}_{kf_id}.mp4")
        ov.cam(os.path.join(KF, f"{kf_id}-1.png"), c, b - a + 0.1, "push"); segs.append((a, b, c))
    inputs, fc, last = ["-i", src], [], "[0:v]"
    for k, (a, b, c) in enumerate(segs, start=1):
        inputs += ["-i", c]
        fc.append(f"[{k}:v]scale={W}:{H},trim=0:{b - a:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={ass}:fontsdir={fdir}[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    s0, s1 = B[SEPIA[0]][0], B[SEPIA[-1]][1]
    fc.append(f"{last}colorchannelmixer=enable='between(t,{s0:.3f},{s1:.3f})':rr=.393:rg=.769:rb=.189:gr=.349:gg=.686:gb=.168:br=.272:bg=.534:bb=.131,"
              "eq=contrast=1.03:saturation=0.97,noise=alls=3:allf=t+u,format=yuv420p[v]")
    run(inputs + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "copy", out])


def hook_bed(path):
    fc = ("sine=f=110:d=3.6,aeval=val(0)*(1-0.5*t/3.6):c=mono[s1];anoisesrc=d=3.6:c=brown:a=0.3,lowpass=f=220[n];"
          "[s1][n]amix=inputs=2:normalize=0,volume=0.32,afade=t=in:st=0:d=0.3,afade=t=out:st=3.3:d=0.3[dr];"
          "sine=f=52:d=0.18,afade=t=out:st=0.05:d=0.13,volume=1.7,adelay=500|500[b1];sine=f=52:d=0.16,afade=t=out:st=0.04:d=0.12,volume=1.3,adelay=800|800[b2];"
          "[dr][b1][b2]amix=inputs=3:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo[a]")
    run(["-filter_complex", fc, "-map", "[a]", "-t", "3.6", path])


def main():
    src0 = sys.argv[1]
    tmp = os.path.join(OUTD, "fin"); os.makedirs(tmp, exist_ok=True)
    mixed = os.path.join(tmp, "mixed.mp4")
    if "--from-mixed" not in sys.argv:  # 오디오만 다시 마감할 때는 영상 패치를 건너뛴다
        patched = os.path.join(tmp, "patched.mp4"); patch(src0, patched, tmp)
        bed = os.path.join(tmp, "hookbed.wav"); hook_bed(bed)
        run(["-i", patched, "-i", bed, "-filter_complex", "[0:a][1:a]amix=inputs=2:normalize=0:duration=first[a]", "-map", "0:v", "-map", "[a]",
             "-c:v", "copy", "-c:a", "pcm_s16le", mixed.replace(".mp4", ".mov")])
    main_out = os.path.join(tmp, "main.mp4")
    mov = mixed.replace(".mp4", ".mov")
    # burn 산출 오디오가 영상보다 5.5초 짧아 본편 끝에서 BGM이 뚝 끊기고 6초 무음이 생겼다(1차 최종본 실증) →
    # 오디오 끝 3초 페이드 + 영상 길이까지 채움 + 전편 룸톤 베드 약 −52dBFS(제15장 13)
    ad = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=duration", "-of", "csv=p=0", mov]))
    vd = dur(mov)
    fc = (f"[0:a]afade=t=out:st={max(ad - 3.0, 0):.3f}:d=3,apad=whole_dur={vd:.3f}[m];"
          f"anoisesrc=d={vd:.3f}:c=brown:a=1,lowpass=f=250,volume=-40dB,aformat=sample_rates=44100:channel_layouts=stereo[rt];"
          "[m][rt]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89:level=0[a]")
    run(["-i", mov, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-ar", "44100",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", main_out])
    print("본편 마무리:", main_out, round(dur(main_out), 2))
    if "--no-outro" not in sys.argv:
        outro(main_out, tmp)


def outro(main_out, tmp):
    outro = os.path.join(OUTD, "beggar-outro.mp4")
    meta = json.load(open(os.path.join(OUTD, "beggar-outro.json")))
    hs = meta["host_start"]
    cta = os.path.join(tmp, "outro-cta.mp4")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), outro, cta, f"{hs[1] + 1.0:.2f}", f"{hs[1] + 1.8:.2f}", f"{hs[2] - 0.2:.2f}"], check=True)
    final = os.path.join(OUTD, "beggar-final.mp4")
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), main_out, final], check=True, env=env)
    print(f"완성: {final} ({dur(final):.1f}초) / 본편 {dur(main_out):.1f}초 / 아웃트로 {dur(cta):.1f}초")
    fix_glyphs(final)


# 1955 회상 S10f: 랙 포커스 끝에서 노렌의 가짜 한자(「抉粋什」「口白」)가 선명해짐(최종본 검수) → 무지 노렌으로 채움(배경 소품, 제11장 10)
DELOGO = [("S10f", [(1195, 140, 110, 340), (1418, 385, 80, 120)])]


def fix_glyphs(final):
    b = bounds(); vf = []
    for sid, boxes in DELOGO:
        a, e = b[sid]
        vf += [f"delogo=x={x}:y={y}:w={w}:h={h}:enable='between(t,{a - 0.1:.2f},{e + 0.1:.2f})'" for x, y, w, h in boxes]
    tmpf = final.replace(".mp4", "_g.mp4")
    run(["-i", final, "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy", tmpf])
    os.replace(tmpf, final); print("가짜 글자 채움:", [d[0] for d in DELOGO])


if __name__ == "__main__":
    if "--glyphs-only" in sys.argv:
        fix_glyphs(os.path.join(OUTD, "beggar-final.mp4"))
    else:
        main()
