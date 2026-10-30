#!/usr/bin/env python3
"""『引きこもりの息子』 PHASE 6 마무리 (로컬, 무과금) — finalize_beggar.py 구조 + 이 작품 설계(18_카메라줌설계.md·17_배경전수점검.md).

1) 컷 패치(원본 클립 → 매 프레임 처리 → 1920x1080 → 편집 카메라 → 같은 자막을 다시 구워 그 컷 자리에 덮음)
   - SCREEN : i2v 컷 PC 화면 매 프레임 합성(screens.json, 키프레임 좌표 → 클립 좌표 자동 정합, 제19장 13)
   - PAPER  : S17d·S17e 서명 종이에 계약서 글자 매 프레임 합성(손·펜은 채도 키로 보호)
   - PLATE  : S12a 세단 일본 번호판 / BADGE: S24g 金田 명찰(템플릿 추적)
   - 카메라 : 점프 컷(립싱크 4.5초 초과, 말 안 정적에서 1.00→1.10), 펀치 인(6~8프레임 1.12배), 슬로 줌 인(1.00→1.05)·아웃(1.06→1.00),
              POV 숨 흔들림(S08b·S09a·S09f) — 확대 상한 1.12배(제19장 17)
   - S20e   : 립싱크 앞 1.25초 + 나머지는 由美子 반응 L컷(S20c 원본 뒤쪽), S22b: 새 립싱크(누락 컷 재생성, 제19장 19)
2) 색: 전편 공통 미세 대비·그레인, 어두운 장면(평균 40/255 미만) 중간 톤 리프트(제11장 11)
3) 후크 0~3.5초 드론 + 심장 박동, 룸톤 베드 −52dBFS, −14 LUFS / −1 dBTP
4) 아웃트로 + 구독 버튼 + 엔드카드
사용법: python3 scripts/finalize_hikikomori.py <remix 완성본.mp4> [--only S09g,S17d] [--patches-only] [--no-outro]
"""
import json, math, os, shutil, subprocess, sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import hikikomori_screens as scr  # noqa: E402
import hikikomori_ja_overlay as jov  # noqa: E402

FF = shutil.which("ffmpeg")
OUTD = os.path.join(ROOT, "out")
SB = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "hikikomori.json"), encoding="utf-8"))["scenes"]
AUDIO = json.load(open(os.path.join(ROOT, "scripts", "audio", "hikikomori.json"), encoding="utf-8"))
KF = os.path.join(ROOT, "assets", "portraits", "hikikomori-keyframes")
SCREENS = json.load(open(os.path.join(ROOT, "productions", "hikikomori-ja", "screens.json"), encoding="utf-8"))
W, H, FPS = 1920, 1080, 24
IDX = {s["id"]: k + 1 for k, s in enumerate(SB)}
OMNI = set(AUDIO["omnihuman_scenes"])

# ---------- 설계(18_카메라줌설계.md) ----------
JUMP = ["S04f", "S05e", "S05i", "S12e", "S12h", "S12i", "S12j", "S15f", "S18g", "S19a", "S21d", "S22b", "S23e", "S23g", "S23k"]
PUNCH = {"S09g": 0.5, "S10c": 0.4, "S11c": 0.4, "S18b": 0.6, "S22a": 0.5}  # 컷 시작 후 몇 초에 터뜨리는지
ZIN = ["S09h", "S11f", "S11j", "S12d", "S15b", "S15i", "S18f", "S20c", "S23c", "S23j", "S24g"]  # i2v 감정 정점 CU(정지 컷은 이미 푸시인)
ZOUT = ["S06d", "S11k", "S13e", "S14b", "S22e", "S24d"]
POV = ["S08b", "S09a", "S09f"]
CLIP_OVERRIDE = {"S22b": "assets/auditions/hikikomori-outro-omni/omni-s22b.mp4",
                 "S05a": "assets/preview/hikikomori-fix/S05a.mp4"}  # 문손잡이: 두 손이 레버 하나를 겹쳐 쥠 → 옆에서 한 손 ECU(r12-3) 정지 푸시인(고니감독님 지적 1:30)  # 립싱크 누락 컷 재생성(제19장 19)
LCUT = {"S20e": (1.25, "S20c", 2.0)}  # (립싱크 사용 초, 반응 컷, 반응 원본 시작 초) — S20e 1.3초 뒤 일어서며 방이 바뀜
PAPER = {"S17d": [(486, 478), (828, 478), (880, 628), (424, 632)], "S17e": [(480, 290), (890, 290), (945, 670), (418, 678)]}  # 키프레임 종이 네 꼭짓점
PLATE = ("S12a", (797, 641, 855, 669))
BADGE = ("S24g", (791, 604, 836, 624))


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def bounds():
    """조립 타임라인: 장면 경계마다 1프레임 겹침(frame_quantize, 전편 168프레임 = 7.0초 짧음)."""
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
    return "i2v" if os.path.exists(os.path.join(ROOT, "assets", "preview", "hikikomori", f"scene{i:02d}.mp4")) else "still"


def raw_path(sid):
    if sid in CLIP_OVERRIDE:
        return os.path.join(ROOT, CLIP_OVERRIDE[sid])
    i, k = IDX[sid], kind(sid)
    if k == "omni":
        return os.path.join(ROOT, "assets", "preview", "hikikomori-audio", f"omni{i:02d}.mp4")
    if k == "i2v":
        return os.path.join(ROOT, "assets", "preview", "hikikomori", f"scene{i:02d}.mp4")
    return os.path.join(ROOT, "assets", "video-overrides", "hikikomori", f"scene{i:02d}.mp4")


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
    """generate_audio norm_filter(fit=crop)과 같은 정규화: 가득 채우고 가운데 크롭."""
    h, w = f.shape[:2]; s = max(W / w, H / h)
    r = cv2.resize(f, (math.ceil(w * s), math.ceil(h * s)), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    y0, x0 = (r.shape[0] - H) // 2, (r.shape[1] - W) // 2
    return r[y0:y0 + H, x0:x0 + W]


def kf_map(sid, frame):
    """키프레임(1344x768) 좌표 → 클립 좌표 (scale, ox, oy). 첫 프레임과 키프레임 정합(matchTemplate)."""
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


def map_entry(e, s, ox, oy):
    e = dict(e); e["q"] = mapq(e["q"], s, ox, oy)
    if e.get("occ"):
        e["occ"] = [[cx * s - ox, cy * s - oy, rx * s, ry * s] for cx, cy, rx, ry in e["occ"]]
    if e.get("occpoly"):
        e["occpoly"] = mapq(e["occpoly"], s, ox, oy)
    return e


_content = {}
_orig_content = scr.content
scr.content = lambda kind: _content.setdefault(kind, _orig_content(kind))  # 화면 내용은 컷 동안 같다 — 매 프레임 다시 그리지 않음


def sign_page():
    """S17e ECU — 계약서 마지막 장. 키프레임 종이에 이미 그어진 펜 선(종이 폭 19~50%, 높이 66%)을 서명란 밑줄로 쓴다."""
    w, h = 1054, 776; im = Image.new("RGB", (w, h), (255, 255, 255)); d = ImageDraw.Draw(im); m = ImageFont.truetype(jov.M, 30)
    rows = ["第７条（協議）", "本契約に定めのない事項は、甲乙誠実に協議のうえ定める。", "", "本契約の成立を証するため、本書二通を作成し、",
            "甲乙記名押印のうえ、各一通を保有する。", "", "令和七年十一月　　日"]
    for i, t in enumerate(rows):
        d.text((70, 70 + i * 48), t, font=m, fill=(45, 45, 50))
    d.text((int(w * 0.185), int(h * 0.66) - 6), "甲", font=ImageFont.truetype(jov.M, 34), fill=(45, 45, 50), anchor="rb")
    d.text((int(w * 0.56), int(h * 0.80)), "乙　鳳凰工業株式会社　代表取締役", font=m, fill=(45, 45, 50))
    return im


def plate_art():
    im = Image.new("RGB", (440, 220), (246, 246, 240)); d = ImageDraw.Draw(im)
    d.rectangle((4, 4, 435, 215), outline=(40, 90, 50), width=6)
    g = jov.G
    d.text((150, 52), "品川 330", font=ImageFont.truetype(g, 52), fill=(30, 85, 45), anchor="mm")
    d.text((52, 150), "な", font=ImageFont.truetype(g, 54), fill=(30, 85, 45), anchor="mm")
    d.text((262, 150), "12-48", font=ImageFont.truetype(g, 112), fill=(30, 85, 45), anchor="mm")
    return im


def badge_art():
    im = Image.new("RGB", (300, 120), (236, 236, 232)); d = ImageDraw.Draw(im)
    d.rectangle((2, 2, 297, 117), outline=(150, 150, 150), width=3)
    d.text((150, 62), "金田", font=ImageFont.truetype(jov.M, 78), fill=(35, 35, 40), anchor="mm")
    return im


def paste_rect(f, art, box, track=None):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    a = cv2.resize(np.asarray(art), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA).astype(float)
    reg = f[y0:y1, x0:x1].astype(float)
    lum = reg.mean(2, keepdims=True) / max(reg.mean(), 1)
    out = f.copy(); out[y0:y1, x0:x1] = np.clip(a * np.clip(lum, 0.7, 1.1) * (reg.mean() / 240.0), 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(out, (0, 0), 0.6); out[y0:y1, x0:x1] = blur[y0:y1, x0:x1]
    return out


def process_native(sid, frames):
    """원본 해상도에서 매 프레임 합성(화면·종이·번호판·명찰)."""
    need = (sid in SCREENS and kind(sid) == "i2v") or sid in PAPER or sid in (PLATE[0], BADGE[0])
    if not need or kind(sid) != "i2v":
        return frames
    s, ox, oy = kf_map(sid, frames[0])
    out = []
    if sid in SCREENS:
        ents = [map_entry(e, s, ox, oy) for e in SCREENS[sid]]
        g0 = frames[0].mean(2)
        for e in ents:  # 밝은 무지 화면을 가린 「replace」 항목은 i2v에서 사람이 움직이므로 휘도 키로(정적 occ 다각형은 움직임을 못 따라감)
            if e["mode"] == "replace":
                m = np.zeros(g0.shape, np.uint8); cv2.fillConvexPoly(m, np.int32(e["q"]), 1)
                if e.get("occpoly"):
                    cv2.fillPoly(m, [np.int32(e["occpoly"])], 0)
                if m.any() and np.median(g0[m > 0]) > 150:
                    e["mode"] = "lum"; e.pop("occpoly", None); e["occ"] = []
        med = np.median(np.stack(frames[::3]).astype(np.float32), axis=0)  # 화면은 고정, 사람은 움직임 → 시간 중앙값 = 빈 화면
        for f in frames:
            d = np.linalg.norm(f.astype(np.float32) - med, axis=2)
            still = np.clip(1 - (d - 28) / 30, 0, 1).astype(np.float32)
            still = cv2.erode(still, np.ones((7, 7), np.uint8)); still = cv2.GaussianBlur(still, (0, 0), 2)
            out.append(np.asarray(scr.apply_plan(Image.fromarray(f), ents, extra=still)))
        frames = out; out = []
    if sid in PAPER:
        art = jov.contract() if sid == "S17d" else sign_page()
        q = mapq(PAPER[sid], s, ox, oy)
        for f in frames:
            out.append(np.asarray(jov.put(Image.fromarray(f), art, q, tol=45, strength=0.88)))
        frames = out; out = []
    if sid in (PLATE[0], BADGE[0]):
        sid0, box, art = (PLATE[0], PLATE[1], plate_art()) if sid == PLATE[0] else (BADGE[0], BADGE[1], badge_art())
        b = mapq([box[:2], box[2:]], s, ox, oy); box = (b[0][0], b[0][1], b[1][0], b[1][1])
        x0, y0, x1, y1 = [int(round(v)) for v in box]
        tmpl = cv2.cvtColor(frames[0], cv2.COLOR_RGB2GRAY)[y0 - 6:y1 + 6, x0 - 6:x1 + 6]
        for f in frames:  # 명찰은 숨·몸 움직임을 따라간다(템플릿 추적, 탐색 ±24px)
            g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY)
            sy0, sx0 = max(y0 - 30, 0), max(x0 - 30, 0)
            r = cv2.matchTemplate(g[sy0:y1 + 30, sx0:x1 + 30], tmpl, cv2.TM_CCOEFF_NORMED); _, _, _, loc = cv2.minMaxLoc(r)
            dx, dy = sx0 + loc[0] + 6 - x0, sy0 + loc[1] + 6 - y0
            out.append(paste_rect(f, art, (x0 + dx, y0 + dy, x1 + dx, y1 + dy)))
        frames = out
    return frames


# ---------- 편집 카메라 ----------
def zoom_frame(f, z, cx=0.5, cy=0.5, dx=0.0, dy=0.0):
    if abs(z - 1) < 1e-4 and not dx and not dy:
        return f
    cw, ch = W / z, H / z
    x0 = min(max(cx * W - cw / 2 + dx * W, 0), W - cw); y0 = min(max(cy * H - ch / 2 + dy * H, 0), H - ch)
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def quiet_point(path, lo, hi):
    """립싱크 클립 자체 음성(구동 대사)에서 말 안 정적(0.3초 이상) 가운데 시각 — lo~hi 사이, 없으면 None."""
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
        tj = quiet_point(src, 0.35 * sec, 0.75 * sec) or 0.5 * sec  # 정적이 없으면 가운데(자막 경계와 겹치면 아래에서 민다)
        kj = int(round(tj * FPS)); print(f"  [{sid}] 점프 컷 {tj:.2f}s")
        return [zoom_frame(f, 1.10 if i >= kj else 1.0, 0.5, 0.40) for i, f in enumerate(frames)]
    if sid in PUNCH:
        k0 = int(PUNCH[sid] * FPS)
        return [zoom_frame(f, 1 + 0.12 * min(max((i - k0) / 7, 0), 1), 0.5, 0.45) for i, f in enumerate(frames)]
    if sid in ZIN:
        return [zoom_frame(f, 1 + 0.05 * i / max(n - 1, 1), 0.5, 0.42) for i, f in enumerate(frames)]
    if sid in ZOUT:
        return [zoom_frame(f, 1.06 - 0.06 * i / max(n - 1, 1)) for i, f in enumerate(frames)]
    if sid in POV:  # 1인칭 — 숨 쉬는 듯한 상하 흔들림 + 아주 느린 좌우(걸음 없이)
        return [zoom_frame(f, 1.07, dx=0.004 * math.sin(i / 9.0), dy=0.005 * math.sin(i / 13.0 + 1)) for i, f in enumerate(frames)]
    return frames


def build_cut(sid, sec, tmp):
    src = raw_path(sid)
    out = os.path.join(tmp, f"cut_{sid}.mp4")
    if os.path.exists(out) and "--rebuild" not in sys.argv:  # 컷 클립 캐시(바꾼 컷은 --rebuild --only로 다시)
        return out
    if not os.path.exists(src):
        print(f"  [{sid}] 원본 없음 — 건너뜀: {src}")
        return None
    if sid in LCUT:
        keep, rid, rstart = LCUT[sid]
        a = [cover(f) for f in read_frames(src)][:int(round(keep * FPS))]
        b = [cover(f) for f in process_native(rid, read_frames(raw_path(rid)))][int(rstart * FPS):]
        frames = a + b
    else:
        frames = [cover(f) for f in process_native(sid, read_frames(src))]
    n = int(round(sec * FPS)) + 1
    frames = (frames + [frames[-1]] * n)[:n]  # tpad clone + trim(조립과 같은 방식)
    frames = camera(sid, frames, sec, src)
    write_frames(frames, out)
    return out


# 후크(0~20초): 본편 실제 클립 재사용 — 교체 클립이 키프레임 정지(입 안 움직임·흰 무지 화면)·검은 카드로 남아 있었음(최종 1차 검수)
HOOK = {"H0": ("S05e", 0.213 - 0.32), "H1": ("S09g", 0.0), "H2a": ("S11g", 0.0), "H2b": ("S11h", 0.0)}  # (원본 컷, 원본 시작 초 — 음수면 첫 프레임 유지)
CARD = ("H2b", "息子は、ずっと隠していた。", 0.5)  # 중앙 카드(굵은 명조), 컷 시작 후 초
TITLE = ("H3", "引きこもりの息子")  # 직전 컷 블러 위 타이틀 — 암전 금지(제15장 20)
MINCHO = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")


def text_frame(f, txt, size, alpha, dy=0):
    im = Image.fromarray(f).convert("RGBA"); lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fnt = ImageFont.truetype(MINCHO, size); a = int(255 * alpha)
    for o in range(6, 0, -2):  # 부드러운 그림자
        d.text((W / 2 + 3, H / 2 + 3 + dy), txt, font=fnt, fill=(0, 0, 0, a // (o + 1)), anchor="mm", stroke_width=o, stroke_fill=(0, 0, 0, a // (o + 1)))
    d.text((W / 2, H / 2 + dy), txt, font=fnt, fill=(255, 255, 255, a), anchor="mm")
    im.alpha_composite(lay); return np.asarray(im.convert("RGB"))


def build_hook(hid, sec, tmp):
    out = os.path.join(tmp, f"cut_{hid}.mp4")
    if os.path.exists(out) and "--rebuild" not in sys.argv:
        return out
    n = int(round(sec * FPS)) + 1
    if hid == TITLE[0]:
        last = cv2.GaussianBlur(cover(read_frames(raw_path(HOOK["H2b"][0]))[-1]), (0, 0), 22) * 0.5
        last = last.astype(np.uint8)
        frames = [text_frame(zoom_frame(last, 1 + 0.04 * i / n), TITLE[1], 150, min(1, i / 14) * min(1, (n - i) / 10)) for i in range(n)]
    else:
        sid, off = HOOK[hid]
        src = raw_path(sid)
        fr = [cover(f) for f in process_native(sid, read_frames(src, max(off, 0)))]
        fr = [fr[0]] * int(round(max(-off, 0) * FPS)) + fr
        frames = (fr + [fr[-1]] * n)[:n]
        if hid == CARD[0]:
            k0 = int(CARD[2] * FPS)
            frames = [text_frame(f, CARD[1], 88, min(1, max(0, (i - k0) / 10)) * min(1, (n - i) / 8), dy=-420) if i >= k0 else f for i, f in enumerate(frames)]  # 화면 위 빈 벽(얼굴 가림 금지)
    write_frames(frames, out)
    return out


def targets():
    t = set(JUMP) | set(PUNCH) | set(ZIN) | set(ZOUT) | set(POV) | set(LCUT) | set(CLIP_OVERRIDE) | set(PAPER) | {PLATE[0], BADGE[0]}
    t |= {s for s in SCREENS if kind(s) == "i2v"}
    return sorted(t, key=lambda s: IDX[s])


def patch(src, out, tmp, only=None):
    B = bounds()
    ass = os.path.join(ROOT, "subs", "hikikomori.ass")
    fdir = os.environ.get("FONTSDIR", "/usr/share/fonts")
    segs = []
    for hid in list(HOOK) + [TITLE[0]]:
        if only and hid not in only:
            continue
        a, b = B[hid]; print(f"[{hid}] 후크 {a:.2f}~{b:.2f}s")
        segs.append((a, b - 1 / FPS, build_hook(hid, b - a, tmp)))
    for sid in targets():
        if only and sid not in only:
            continue
        a, b = B[sid]
        print(f"[{sid}] {kind(sid)} {a:.2f}~{b:.2f}s")
        c = build_cut(sid, b - a, tmp)
        if c:
            segs.append((a, b - 1 / FPS, c))
    inputs, fc, last = ["-i", src], [], "[0:v]"
    for k, (a, b, c) in enumerate(segs, start=1):
        inputs += ["-i", c]
        fc.append(f"[{k}:v]trim=0:{b - a + 1 / FPS:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={ass}:fontsdir={fdir}[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    fc.append(f"{last}eq=contrast=1.03:saturation=0.98,{lift_filter(src)}noise=alls=3:allf=t+u,format=yuv420p[v]")
    script = os.path.join(tmp, "patch_fc.txt"); open(script, "w").write(";\n".join(fc))
    run(inputs + ["-filter_complex_script", script, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                  "-c:a", "copy", out])
    return [s for s in targets() if not only or s in only]


def lift_filter(src):
    """어두운 장면(가운데 프레임 평균 40/255 미만)만 중간 톤을 들어 올림 — 검정은 그대로(제11장 11)."""
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
    fc = ("sine=f=110:d=3.5,aeval=val(0)*(1-0.5*t/3.5):c=mono[s1];anoisesrc=d=3.5:c=brown:a=0.3,lowpass=f=220[n];"
          "[s1][n]amix=inputs=2:normalize=0,volume=0.32,afade=t=in:st=0:d=0.3,afade=t=out:st=3.2:d=0.3[dr];"
          "sine=f=52:d=0.18,afade=t=out:st=0.05:d=0.13,volume=1.7,adelay=600|600[b1];sine=f=52:d=0.16,afade=t=out:st=0.04:d=0.12,volume=1.3,adelay=900|900[b2];"
          "[dr][b1][b2]amix=inputs=3:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo[a]")
    run(["-filter_complex", fc, "-map", "[a]", "-t", "3.5", path])


def master(patched, out):
    bed = patched.replace(".mp4", "_hook.wav"); hook_bed(bed)
    vd = dur(patched)
    ad = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=duration", "-of", "csv=p=0", patched]))
    fc = (f"[0:a]afade=t=out:st={max(ad - 2.5, 0):.3f}:d=2.5,apad=whole_dur={vd:.3f}[m];[1:a]apad=whole_dur={vd:.3f}[h];"
          f"anoisesrc=d={vd:.3f}:c=brown:a=1,lowpass=f=250,volume=-40dB,aformat=sample_rates=44100:channel_layouts=stereo[rt];"
          "[m][h][rt]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89:level=0[a]")
    run(["-i", patched, "-i", bed, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-ar", "44100", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])


def outro(main_out, tmp):
    outro = os.path.join(OUTD, "hikikomori-outro.mp4")
    meta = json.load(open(os.path.join(OUTD, "hikikomori-outro.json")))
    hs = meta["host_start"]
    cta = os.path.join(tmp, "outro-cta.mp4")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), outro, cta, f"{hs[1] + 1.0:.2f}", f"{hs[1] + 1.8:.2f}", f"{hs[2] - 0.2:.2f}"], check=True)
    final = os.path.join(OUTD, "hikikomori-final.mp4")
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), main_out, final], check=True, env=env)
    print(f"완성: {final} ({dur(final):.1f}초) / 본편 {dur(main_out):.1f}초")


def main():
    src = sys.argv[1]
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    tmp = os.path.join(OUTD, "fin-hik"); os.makedirs(tmp, exist_ok=True)
    if "--patches-only" in sys.argv:  # 컷 클립만 만들어 검수
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
