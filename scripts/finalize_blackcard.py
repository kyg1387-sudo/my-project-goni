#!/usr/bin/env python3
"""『ブラックカード』(第1話) PHASE 6 마무리 (로컬, 무과금) — finalize_hikikomori.py 구조 + 이 작품 설계(18_카메라줌설계.md·09_정점효과음설계.md·08_기획안대조).

1) 컷 패치(원본 클립 → 매 프레임 처리 → 1920x1080 → 편집 카메라 → 같은 자막을 다시 구워 그 컷 자리에 덮음)
   - PAPER  : i2v 컷의 글자 면 매 프레임 합성(S08g 辞令, blackcard_ja_overlay.QUADS → 클립 좌표 자동 정합, 제19장 13·20)
   - 카메라 : 점프 컷(립싱크 4.5초 초과, 말 안 정적에서 1.00→1.10), 펀치 인(6~8프레임 1.12배, 6회), 슬로 줌 인(1.00→1.05)·아웃(1.06→1.00) — 상한 1.12배(제19장 17)
   - 카드   : S01k 질문 카드 · S02a 타이틀 · S08u 예고 · S12u/S12zz 카운트다운 — 직전 컷 블러 위 글자(암전 없음, 제15장 20)
   - L컷    : LCUT(립싱크 앞부분 + 듣는 사람 반응)
2) 색(재미나이 기획안 △ 항목, 로컬): 전편 공통 미세 대비·그레인, S02·S03 초록 형광 플리커(±4%, 립싱크 ±2%), S05 승인 +1 stop 램프,
   S09·S10 항공장애등 붉은 글로 2초 주기(립싱크 진폭 절반), S11 웜 → S12 한랭, 어두운 장면(평균 40/255 미만) 중간 톤 리프트(제11장 11)
3) 소리: 후크 0~3.5초 심장 박동 가속 + 천둥(ElevenLabs 선택본), 정점 효과음 피크 덧믹스(09 설계표), 룸톤 베드 −52dBFS, −14 LUFS / −1 dBTP
4) 아웃트로 + 구독 버튼 + 엔드카드(build_blackcard_outro.py 산출물)
사용법: python3 scripts/finalize_blackcard.py <remix 완성본.mp4> [--only S08g,S10g] [--patches-only] [--no-outro] [--rebuild]
"""
import json, math, os, shutil, subprocess, sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import blackcard_ja_overlay as jov  # noqa: E402

FF = shutil.which("ffmpeg")
OUTD = os.path.join(ROOT, "out")
SKIT = "blackcard"
SB = json.load(open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), encoding="utf-8"))["scenes"]
AUDIO = json.load(open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), encoding="utf-8"))
KF = os.path.join(ROOT, "assets", "portraits", f"{SKIT}-keyframes")
SFXD = os.path.join(ROOT, "assets", "auditions", f"{SKIT}-sfx")
W, H, FPS = 1920, 1080, 24
IDX = {s["id"]: k + 1 for k, s in enumerate(SB)}
OMNI = set(AUDIO["omnihuman_scenes"])
SCENE_OF = {s["id"]: s["scene"] for s in SB}

# ---------- 설계(18_카메라줌설계.md) ----------
JUMP = ["S02h", "S03b", "S06h", "S08d", "S09b", "S09d", "S10c", "S10e"]  # 4.5초 넘는 립싱크 — 말 안 정적에서 1.00→1.10
PUNCH = {"S01h": 1.6, "S05g": 3.0, "S07n": 0.3, "S10h": 0.0, "S12p": 0.4, "S12u": 1.0}  # 컷 시작 후 몇 초에 터뜨리는지(6회)
ZIN = ["S01j", "S03k", "S05i", "S06k", "S08q", "S09e", "S10o", "S12g", "S12q", "S12v"]
ZOUT = ["S05l", "S06j", "S10p", "S12w"]
CLIP_OVERRIDE = {}  # 검수 뒤 교체 클립(재생성·고정 컷)
LCUT = {}  # sid: (립싱크 사용 초, 반응 컷, 반응 원본 시작 초)
PAPER = {"S08g": jov.jirei}  # i2v 컷의 글자 면(quad는 jov.QUADS, 키프레임 좌표)
# 화면 카드(클립에 직접, 제15장 12·20): sid → (직전 컷, 글자, 크기, dy, 카드 시작 초)
CARDS = {"S01k": ("S01j", "拾ったのは、カードだけじゃなかった。", 88, 0, 0.0), "S02a": ("S01j", "ブラックカード", 170, 0, 0.0),
         "S08u": ("S08t", "この後――妻が、ドアを叩き壊す", 84, 0, 0.2), "S12zz": ("S12z", "残り　６日", 150, 0, 0.0)}
COUNT = {"S12u": ("残り７日", "残り６日", 1.0)}  # 구석 소자막 전환(시계 0:00과 같은 프레임)
# 색 큐(장면 단위) — 재미나이 △ 항목을 로컬로
FLICKER = {"S02", "S03"}  # 초록 형광 불규칙 플리커
STOP_UP = ("S05g", "S05i")  # 승인 → +1 stop 램프(0.8초)
RED_PULSE = {"S09", "S10"}  # 항공장애등 2초 주기
WARM = {"S07", "S11"}; COLD = {"S12"}
MINCHO = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")
PICKS = json.load(open(os.path.join(SFXD, "_picks_prelim.json"))) if os.path.exists(os.path.join(SFXD, "_picks_prelim.json")) else {}


def sfx(name):
    p = os.path.join(SFXD, PICKS.get(name, f"{name}-1.mp3"))
    return p if os.path.exists(p) else None


# 효과음 덧믹스(09_정점효과음설계.md): (소리, 컷, 컷 시작 후 초, 목표 피크 dBFS)
SFX = [("thunder", "S01a", 1.0, -14.0), ("scissors-card", "S01d", 0.6, -12.0), ("envelope-gutter", "S01e", 0.0, -16.0),
       ("paper-slide", "S03h", 0.2, -12.0),  # 콜백 원점(1막) — ③과 같은 파일
       ("payment-chime", "S04h", 0.3, -12.0), ("payment-chime", "S05f", 0.3, -12.0), ("receipt-printer", "S05g", 3.4, -9.0),
       ("paper-slide", "S08a", 0.0, -12.0), ("chair-tilt", "S08m", 0.1, -9.0), ("door-bang", "S09a", 0.1, -9.0),
       ("paper-tear", "S10g", 0.0, -9.0), ("impact-low", "S10h", 0.0, -12.0), ("clock-tick-heart", "S12u", 1.0, -12.0)]


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def bounds():
    """조립 타임라인: 장면 경계마다 1프레임 겹침(frame_quantize)."""
    d = [float(x) for x in AUDIO["scene_durations"]]
    t, out = 0.0, {}
    for k, (s, x) in enumerate(zip(SB, d)):
        a = round(t * FPS) / FPS
        out[s["id"]] = (a, round((t + x) * FPS) / FPS)
        t += x - (1 / FPS if k < len(d) - 1 else 0)
    return out


def kind(sid):
    i = IDX[sid]
    if i in OMNI:
        return "omni"
    return "i2v" if os.path.exists(os.path.join(ROOT, "assets", "preview", SKIT, f"scene{i:02d}.mp4")) else "still"


def raw_path(sid):
    if sid in CLIP_OVERRIDE:
        return os.path.join(ROOT, CLIP_OVERRIDE[sid])
    i, k = IDX[sid], kind(sid)
    if k == "omni":
        return os.path.join(ROOT, "assets", "preview", f"{SKIT}-audio", f"omni{i:02d}.mp4")
    if k == "i2v":
        return os.path.join(ROOT, "assets", "preview", SKIT, f"scene{i:02d}.mp4")
    return os.path.join(ROOT, "assets", "video-overrides", SKIT, f"scene{i:02d}.mp4")


def read_frames(path, start=0.0):
    w, h = [int(x) for x in subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                                                     "-of", "csv=p=0", path]).decode().strip().split(",")[:2]]
    p = subprocess.Popen([FF, "-v", "error", "-ss", f"{start:.3f}", "-i", path, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    out = []
    while True:
        b = p.stdout.read(w * h * 3)
        if len(b) < w * h * 3:
            break
        out.append(np.frombuffer(b, np.uint8).reshape(h, w, 3))
    p.wait()
    return out


def write_frames(frames, out):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close(); p.wait()


def cover(f):
    h, w = f.shape[:2]; s = max(W / w, H / h)
    r = cv2.resize(f, (math.ceil(w * s), math.ceil(h * s)), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    y0, x0 = (r.shape[0] - H) // 2, (r.shape[1] - W) // 2
    return r[y0:y0 + H, x0:x0 + W]


def kf_map(sid, frame):
    """키프레임 좌표 → 클립 좌표 (scale, ox, oy). 첫 프레임과 키프레임 정합."""
    k = cv2.cvtColor(np.asarray(Image.open(os.path.join(KF, f"{sid}-1.png")).convert("RGB")), cv2.COLOR_RGB2GRAY).astype(np.float32)
    a = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)
    m = 20; best = None
    for s in np.linspace(a.shape[1] / k.shape[1] - 0.01, a.shape[0] / k.shape[0] + 0.03, 30):
        kk = cv2.resize(k, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        if kk.shape[0] < a.shape[0] - 2 * m or kk.shape[1] < a.shape[1] - 2 * m:
            continue
        r = cv2.matchTemplate(kk, a[m:-m, m:-m], cv2.TM_CCOEFF_NORMED); _, v, _, loc = cv2.minMaxLoc(r)
        if best is None or v > best[0]:
            best = (v, s, loc[0] - m, loc[1] - m)
    v, s, ox, oy = best
    print(f"  [{sid}] 키프레임 정합 {v:.3f} scale {s:.4f} off ({ox},{oy})")
    return s, ox, oy


def mapq(q, s, ox, oy):
    return [[x * s - ox, y * s - oy] for x, y in q]


def process_native(sid, frames):
    """원본 해상도에서 매 프레임 합성(글자 면)."""
    if sid not in PAPER or kind(sid) != "i2v" or sid not in jov.QUADS:
        return frames
    s, ox, oy = kf_map(sid, frames[0])
    art = PAPER[sid](); q = mapq(jov.QUADS[sid], s, ox, oy)
    return [np.asarray(jov.put(Image.fromarray(f), art, q, tol=45, strength=0.88)) for f in frames]


# ---------- 편집 카메라 ----------
def zoom_frame(f, z, cx=0.5, cy=0.5, dx=0.0, dy=0.0):
    if abs(z - 1) < 1e-4 and not dx and not dy:
        return f
    cw, ch = W / z, H / z
    x0 = min(max(cx * W - cw / 2 + dx * W, 0), W - cw); y0 = min(max(cy * H - ch / 2 + dy * H, 0), H - ch)
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def quiet_point(path, lo, hi):
    a = subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(a, np.int16).astype(float)
    if not len(x):
        return None
    hop = 80; e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
    thr = max(e.max() * 0.06, 60); q = e < thr
    best, k = None, 0
    while k < len(q):
        if q[k]:
            j = k
            while j < len(q) and q[j]:
                j += 1
            t0, t1 = k * hop / 8000, j * hop / 8000
            if t1 - t0 >= 0.3 and lo <= (t0 + t1) / 2 <= hi:
                c = (t0 + t1) / 2
                if best is None or abs(c - (lo + hi) / 2) < abs(best - (lo + hi) / 2):
                    best = c
            k = j
        else:
            k += 1
    return best


def camera(sid, frames, sec, src):
    n = len(frames)
    if sid in JUMP:
        tj = quiet_point(src, 0.35 * sec, 0.75 * sec) or 0.5 * sec
        kj = int(round(tj * FPS)); print(f"  [{sid}] 점프 컷 {tj:.2f}s")
        return [zoom_frame(f, 1.10 if i >= kj else 1.0, 0.5, 0.40) for i, f in enumerate(frames)]
    if sid in PUNCH:
        k0 = int(PUNCH[sid] * FPS)
        return [zoom_frame(f, 1 + 0.12 * min(max((i - k0) / 7, 0), 1), 0.5, 0.45) for i, f in enumerate(frames)]
    if sid in ZIN:
        return [zoom_frame(f, 1 + 0.05 * i / max(n - 1, 1), 0.5, 0.42) for i, f in enumerate(frames)]
    if sid in ZOUT:
        return [zoom_frame(f, 1.06 - 0.06 * i / max(n - 1, 1)) for i, f in enumerate(frames)]
    return frames


def text_frame(f, txt, size, alpha, dy=0, corner=False):
    im = Image.fromarray(f).convert("RGBA"); lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fnt = ImageFont.truetype(MINCHO, size); a = int(255 * alpha)
    x, y, anc = (W - 90, 80, "rt") if corner else (W / 2, H / 2 + dy, "mm")
    for o in range(6, 0, -2):
        d.text((x + 3, y + 3), txt, font=fnt, fill=(0, 0, 0, a // (o + 1)), anchor=anc, stroke_width=o, stroke_fill=(0, 0, 0, a // (o + 1)))
    d.text((x, y), txt, font=fnt, fill=(255, 255, 255, a), anchor=anc)
    im.alpha_composite(lay); return np.asarray(im.convert("RGB"))


def last_frame_of(sid):
    src = raw_path(sid)
    fr = read_frames(src)
    return cover(fr[-1])


def build_cut(sid, sec, tmp):
    out = os.path.join(tmp, f"cut_{sid}.mp4")
    if os.path.exists(out) and "--rebuild" not in sys.argv:
        return out
    n = int(round(sec * FPS)) + 1
    if sid in CARDS:  # 직전 컷 블러 위 글자(암전 없음)
        prev, txt, size, dy, t0 = CARDS[sid]
        base = (cv2.GaussianBlur(last_frame_of(prev), (0, 0), 22) * 0.55).astype(np.uint8)
        k0 = int(t0 * FPS)
        frames = [text_frame(zoom_frame(base, 1 + 0.04 * i / n), txt, size, min(1, max(0, (i - k0) / 12)) * min(1, (n - i) / 10), dy) for i in range(n)]
        write_frames(frames, out); return out
    src = raw_path(sid)
    if not os.path.exists(src):
        print(f"  [{sid}] 원본 없음 — 건너뜀: {src}"); return None
    if sid in LCUT:
        keep, rid, rstart = LCUT[sid]
        a = [cover(f) for f in read_frames(src)][:int(round(keep * FPS))]
        b = [cover(f) for f in process_native(rid, read_frames(raw_path(rid)))][int(rstart * FPS):]
        frames = a + b
    else:
        frames = [cover(f) for f in process_native(sid, read_frames(src))]
    frames = (frames + [frames[-1]] * n)[:n]
    frames = camera(sid, frames, sec, src)
    if sid in COUNT:  # 구석 카운트다운 자막 전환 + 대시보드 시계 23:59 → 0:00(합성 정지 2장 위 연속 슬로 줌)
        a_txt, b_txt, tsw = COUNT[sid]; ksw = int(tsw * FPS)
        if sid in jov.QUADS:
            base = Image.open(os.path.join(KF, f"{sid}-1.png"))
            A = cover(np.asarray(jov.put_lcd(base, jov.clock("23:59"), jov.QUADS[sid])))
            Bf = cover(np.asarray(jov.put_lcd(base, jov.clock("0:00"), jov.QUADS[sid])))
            frames = [zoom_frame(A if i < ksw else Bf, 1 + 0.05 * i / max(n - 1, 1), 0.5, 0.45) for i in range(n)]
        frames = [text_frame(f, a_txt if i < ksw else b_txt, 64, 0.92, corner=True) for i, f in enumerate(frames)]
    write_frames(frames, out)
    return out


def targets():
    t = set(JUMP) | set(PUNCH) | set(ZIN) | set(ZOUT) | set(LCUT) | set(CLIP_OVERRIDE) | set(CARDS) | set(COUNT)
    t |= {s for s in PAPER if kind(s) == "i2v" and s in jov.QUADS}
    return sorted(t, key=lambda s: IDX[s])


def grade_filters(src):
    """장면 단위 색 큐(ffmpeg 필터, 전편 1패스)."""
    B = bounds(); parts = []
    sc_rng = {}
    for sid, (a, b) in B.items():
        sc = SCENE_OF[sid]; lo, hi = sc_rng.get(sc, (a, b)); sc_rng[sc] = (min(lo, a), max(hi, b))
    for sc in sorted(FLICKER):  # 초록 형광 불규칙 플리커: 15% 프레임에 −4%(립싱크 컷 −2%)
        a, b = sc_rng[sc]
        for sid, (x, y) in B.items():
            if SCENE_OF[sid] != sc:
                continue
            amp = 0.02 if kind(sid) == "omni" else 0.04
            parts.append(f"eq=brightness='-{amp}*gt(random(1),0.85)':eval=frame:enable='between(t,{x:.3f},{y:.3f})'")
    a, _ = B[STOP_UP[0]]; _, b = B[STOP_UP[1]]; t0 = B[STOP_UP[0]][1] - 0.4
    parts.append(f"eq=brightness='0.10*clip((t-{t0:.3f})/0.8,0,1)':gamma=1.04:eval=frame:enable='between(t,{t0:.3f},{b:.3f})'")
    for sc in sorted(WARM):
        a, b = sc_rng[sc]; parts.append(f"colortemperature=temperature=4300:mix=0.35:enable='between(t,{a:.3f},{b:.3f})'")
    for sc in sorted(COLD):
        a, b = sc_rng[sc]; parts.append(f"colortemperature=temperature=8200:mix=0.4:enable='between(t,{a + 2.0:.3f},{b:.3f})'")
    return ",".join(parts) + ("," if parts else "")


def red_pulse_inputs():
    """항공장애등: 오른쪽 위에서 퍼지는 붉은 글로 PNG를 2초 주기로 screen 블렌드(S09·S10)."""
    p = os.path.join(OUTD, "fin-bc", "red_glow.png")
    if not os.path.exists(p):
        y, x = np.mgrid[0:H, 0:W]; d = np.sqrt(((x - W * 0.95) / (W * 0.6)) ** 2 + ((y - H * 0.1) / (H * 0.9)) ** 2)
        g = np.clip(1 - d, 0, 1) ** 1.6
        im = np.zeros((H, W, 3), np.uint8); im[..., 0] = (g * 150).astype(np.uint8); im[..., 1] = (g * 15).astype(np.uint8); im[..., 2] = (g * 10).astype(np.uint8)
        Image.fromarray(im).save(p)
    return p


def patch(src, out, tmp, only=None):
    B = bounds()
    ass = os.path.join(ROOT, "subs", f"{SKIT}.ass")
    fdir = os.environ.get("FONTSDIR", "/usr/share/fonts")
    segs = []
    for sid in targets():
        if only and sid not in only:
            continue
        a, b = B[sid]
        print(f"[{sid}] {kind(sid)} {a:.2f}~{b:.2f}s")
        c = build_cut(sid, b - a, tmp)
        if c:
            segs.append((a, b - 1 / FPS, c))
    red = red_pulse_inputs()
    inputs, fc, last = ["-i", src, "-loop", "1", "-i", red], [], "[0:v]"
    for k, (a, b, c) in enumerate(segs, start=2):
        inputs += ["-i", c]
        fc.append(f"[{k}:v]trim=0:{b - a + 1 / FPS:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={ass}:fontsdir={fdir}[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    sc_rng = {}
    for sid, (a, b) in B.items():
        sc = SCENE_OF[sid]; lo, hi = sc_rng.get(sc, (a, b)); sc_rng[sc] = (min(lo, a), max(hi, b))
    en = "+".join(f"between(T,{sc_rng[s][0]:.3f},{sc_rng[s][1]:.3f})" for s in sorted(RED_PULSE))
    fc.append(f"{last}[1:v]blend=all_mode=screen:all_opacity='({en})*0.55*(0.5+0.5*sin(2*PI*T/2.0))':shortest=1[rp]")
    fc.append(f"[rp]{grade_filters(src)}eq=contrast=1.03:saturation=0.97,{lift_filter(src)}noise=alls=3:allf=t+u,format=yuv420p[v]")
    script = os.path.join(tmp, "patch_fc.txt"); open(script, "w").write(";\n".join(fc))
    run(inputs + ["-filter_complex_script", script, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                  "-c:a", "copy", out])
    return [s for s in targets() if not only or s in only]


def lift_filter(src):
    B = bounds(); parts = []
    for sid, (a, b) in B.items():
        f = subprocess.run([FF, "-v", "error", "-ss", f"{(a + b) / 2:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=192:108,format=gray",
                            "-f", "rawvideo", "-"], capture_output=True).stdout
        m = np.frombuffer(f, np.uint8).mean() if f else 255
        if m < 40:
            parts.append((a, b, m))
    if parts:
        print("어두운 장면 리프트:", [(round(a, 1), round(m)) for a, _, m in parts])
    return "".join(f"curves=all='0/0 0.12/0.17 0.35/0.42 1/1':enable='between(t,{a:.3f},{b:.3f})'," for a, b, _ in parts)


def hook_bed(path):
    """0~3.5초: 심장 박동 가속(ElevenLabs 선택본) + 저역 드론 — 천둥은 SFX 목록(S01a+1.0)."""
    hb = sfx("heartbeat-accel")
    if hb:
        run(["-i", hb, "-filter_complex",
             "[0:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=-12dB,afade=t=out:st=3.0:d=0.5[h];"
             "anoisesrc=d=3.5:c=brown:a=0.3,lowpass=f=200,volume=0.25,afade=t=in:st=0:d=0.3,afade=t=out:st=3.0:d=0.5,aformat=sample_rates=44100:channel_layouts=stereo[dr];"
             "[h][dr]amix=inputs=2:normalize=0[a]", "-map", "[a]", "-t", "3.5", path])
    else:
        run(["-f", "lavfi", "-i", "anoisesrc=d=3.5:c=brown:a=0.3", "-af", "lowpass=f=200,volume=0.25,aformat=sample_rates=44100:channel_layouts=stereo", path])


def peak_db(path):
    e = subprocess.run([FF, "-v", "info", "-i", path, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(e.split("max_volume:")[1].split("dB")[0])


def master(patched, out):
    bed = patched.replace(".mp4", "_hook.wav"); hook_bed(bed)
    vd = dur(patched)
    ad = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=duration", "-of", "csv=p=0", patched]))
    B = bounds(); sfx_in, sfx_fc, labs = [], [], ""
    k = 0
    for name, sid, off, pk in SFX:
        p = sfx(name)
        if not p:
            print(f"효과음 없음: {name}"); continue
        ms = int((B[sid][0] + off) * 1000)
        sfx_in += ["-i", p]
        sfx_fc.append(f"[{k + 2}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={pk - peak_db(p):.2f}dB,adelay={ms}|{ms},apad=whole_dur={vd:.3f}[x{k}]")
        labs += f"[x{k}]"; print(f"효과음 {os.path.basename(p)} @ {sid}+{off}s → 피크 {pk} dBFS"); k += 1
    n = 3 + len(sfx_fc)
    fc = (f"[0:a]afade=t=out:st={max(ad - 2.5, 0):.3f}:d=2.5,apad=whole_dur={vd:.3f}[m];[1:a]apad=whole_dur={vd:.3f}[h];"
          f"anoisesrc=d={vd:.3f}:c=brown:a=1,lowpass=f=250,volume=-40dB,aformat=sample_rates=44100:channel_layouts=stereo[rt];"
          + "".join(x + ";" for x in sfx_fc) +
          f"[m][h][rt]{labs}amix=inputs={n}:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.84:level=0[a]")
    run(["-i", patched, "-i", bed] + sfx_in + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-ar", "44100", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])


def outro(main_out, tmp):
    outro = os.path.join(OUTD, f"{SKIT}-outro.mp4")
    meta = json.load(open(os.path.join(OUTD, f"{SKIT}-outro.json")))
    hs = meta["host_start"]
    cta = os.path.join(tmp, "outro-cta.mp4")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), outro, cta, f"{hs[1] + 1.0:.2f}", f"{hs[1] + 1.8:.2f}", f"{hs[2] - 0.2:.2f}"], check=True)
    final = os.path.join(OUTD, f"{SKIT}-final.mp4")
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), main_out, final], check=True, env=env)
    print(f"완성: {final} ({dur(final):.1f}초) / 본편 {dur(main_out):.1f}초")


def main():
    src = sys.argv[1]
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    tmp = os.path.join(OUTD, "fin-bc"); os.makedirs(tmp, exist_ok=True)
    if "--patches-only" in sys.argv:
        B = bounds()
        for sid in (only or targets()):
            a, b = B[sid]; print(sid, build_cut(sid, b - a, tmp))
        return
    patched = os.path.join(tmp, "patched.mp4"); done = patch(src, patched, tmp, only)
    print("패치 컷", len(done), done)
    main_out = os.path.join(tmp, "main.mp4"); master(patched, main_out)
    print("본편 마무리:", main_out, round(dur(main_out), 2))
    if "--no-outro" not in sys.argv:
        outro(main_out, tmp)


if __name__ == "__main__":
    main()
