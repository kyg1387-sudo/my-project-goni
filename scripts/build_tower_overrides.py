#!/usr/bin/env python3
"""『タワマンのボスママ』 무료 교체 클립(video-overrides) 생성 — 규격 제7장 2, 제8장 6 (로컬, 무과금).

스토리보드 방식별로 assets/video-overrides/tower/sceneNN.mp4 (NN = 장면 순번, 1부터)를 만든다. 1920x1080 24fps.
  still  정지 키프레임 → 편집 카메라 한 가지(와이드 = 느린 팬, 그 외 = 슬로 푸시인 1.00→1.05, edit_fx가 있으면 그것)
         dutch7 = 7° 회전(악역 붕괴 모티프), dollyzoom = 인물 마스크 2.5D(배경만 줌아웃, 인물 고정)
  gfx    합성 완료 키프레임 + 시간차 등장(_states.json: 스크린 쌍·피라미드·스크린 점등) 크로스페이드
  omni   대사 CU 정지 프레임 — burn 단계에서 OmniHuman이 음성 구동 영상으로 바꾼다
  card   타이틀·엔딩 카드(실글꼴, 페이드)
  reuse  원본 컷(still·gfx)에서 바로 만든다
i2v 컷(pro·lite)은 만들지 않는다(생성 후 post 단계: pull·dutch5·3분할 — post_i2v).
길이 = scene_durations + 0.5초(디졸브 겹침 여유).
사용법: python3 scripts/build_tower_overrides.py [장면ID ...]
        python3 scripts/build_tower_overrides.py post <clips_dir>   # 생성 i2v 클립 후처리(편집 카메라·3분할) → overrides에 추가
"""
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SB = os.path.join(ROOT, "scripts", "storyboard", "tower.json")
AUDIO = os.path.join(ROOT, "scripts", "audio", "tower.json")
KF = os.path.join(ROOT, "assets", "portraits", "tower-keyframes")
OUT = os.path.join(ROOT, "assets", "video-overrides", "tower")
W, H, FPS = 1920, 1080, 24
MIN_B = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")
MIN_R = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Regular.ttf")
CARDS = {"S01i": ("『タワマンのボスママ』", MIN_B, 96, (236, 226, 200)),
         "S19h": ("見ていないところで、人は決まる。", MIN_R, 64, (236, 232, 222))}
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-an"]


def run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)


def zoom_vf(n, fx):
    """4배 업스케일 위 zoompan(서브픽셀, 떨림 방지). 한 컷 한 무빙."""
    t = f"(on/{n})"
    z, x, y = f"1+0.05*{t}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if fx == "pull":
        z = f"1.06-0.06*{t}"
    elif fx == "pan":
        z = "1.07"; x = f"(iw-iw/zoom)*(0.2+0.6*{t})"
    elif fx == "static":
        z = "1.0"
    vf = f"scale={W * 3}:{H * 3},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS}"
    if fx.startswith("dutch"):
        deg = float(fx[5:] or 5)
        vf += f",rotate={deg}*PI/180:ow={W}:oh={H}:c=black,scale={int(W * 1.2)}:{int(H * 1.2)},crop={W}:{H}"
    return vf


def fit_png(src, dst):
    """키프레임(1344x768 등)을 16:9로 가운데 맞춰 1920x1080 PNG로."""
    im = Image.open(src).convert("RGB"); w, h = im.size
    if abs(w / h - 16 / 9) > 0.01:
        nw = min(w, int(h * 16 / 9)); nh = int(nw * 9 / 16)
        im = im.crop(((w - nw) // 2, (h - nh) // 2, (w - nw) // 2 + nw, (h - nh) // 2 + nh))
    im.resize((W, H), Image.LANCZOS).save(dst)
    return dst


def cam_matrix(fx, t, w, h):
    """원본(w x h) → 1920x1080 출력의 정확한 실수 아핀 행렬(감독님 지적 '영상 떨림' 2026-10-07:
    ffmpeg zoompan은 좌표를 정수 픽셀로 반올림해 슬로 푸시인에서 프레임마다 0.3~0.7px 불규칙하게 떨렸다)."""
    e = t * t * (3 - 2 * t) * 0.35 + t * 0.65   # 시작·끝을 살짝 부드럽게
    z, cx, cy, deg = 1.0, 0.5, 0.5, 0.0
    if fx in ("", "push", "rack"):
        z = 1 + 0.05 * e
    elif fx == "pull":
        z = 1.06 - 0.06 * e
    elif fx == "pan":
        z = 1.07; cx = 0.5 + (0.2 + 0.6 * e - 0.5) * (1 - 1 / z)
    elif fx.startswith("dutch"):
        z = 1.2 * (1 + 0.03 * e); deg = float(fx[5:] or 5)
    base = max(W / w, H / h)   # 16:9 채우기
    M = cv2.getRotationMatrix2D((cx * w, cy * h), deg, base * z)
    M[0, 2] += W / 2 - cx * w; M[1, 2] += H / 2 - cy * h
    return M


def render(imgs_fn, out, n, fx):
    """imgs_fn(i) → 원본 RGB(float32) — 프레임마다 정확한 아핀으로 1920x1080 렌더."""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"] + ENC + [out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        im = imgs_fn(i); h, w = im.shape[:2]
        M = cam_matrix(fx, i / max(1, n - 1), w, h)
        fr = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()


def load(src):
    return np.asarray(Image.open(src).convert("RGB")).astype(np.float32)


def cam(src, out, sec, fx):
    n = max(1, int(math.ceil(sec * FPS))); im = load(src)
    render(lambda i: im, out, n, fx)


def cam_states(sid, out, sec, fx, states):
    """같은 카메라로 상태 이미지를 시간차 크로스페이드(0.15초)."""
    n = max(1, int(math.ceil(sec * FPS))); ims = [load(os.path.join(KF, f)) for _, f in states]
    ts = [t * sec for t, _ in states]

    def frame(i):
        t = i / FPS; im = ims[0]
        for k in range(1, len(ims)):
            a = min(1.0, max(0.0, (t - ts[k]) / 0.15))
            if a > 0:
                im = im * (1 - a) + ims[k] * a
        return im
    render(frame, out, n, fx)


def dollyzoom(src, out, sec):
    """돌리줌(작품 1회, 정체 발각 순간): GrabCut 인물 마스크, 인물은 1.12배 고정, 배경은 1.12→1.0 줌아웃."""
    n = max(1, int(math.ceil(sec * FPS)))
    a = np.asarray(Image.open(fit_png(src, out + ".png")).convert("RGB")); os.remove(out + ".png")
    mask = np.zeros(a.shape[:2], np.uint8)
    rect = (int(W * 0.36), int(H * 0.02), int(W * 0.28), int(H * 0.8))
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    m = ((mask == 1) | (mask == 3)).astype(np.uint8)
    ff = m.copy(); cv2.floodFill(ff, np.zeros((H + 2, W + 2), np.uint8), (0, 0), 1)
    m = (m | (1 - ff)).astype(np.float32)   # 인물 안쪽 구멍(어두운 이너 V넥) 메움 — 배경 배율 차이가 비치지 않게
    m = cv2.GaussianBlur(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), (0, 0), 2)[..., None]

    def scale(img, s):
        M = np.float32([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]])
        return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    fg, fm = scale(a.astype(np.float32), 1.12), scale(m[..., 0], 1.12)[..., None]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"] + ENC + [out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        t = i / max(1, n - 1); e = t * t * (3 - 2 * t)
        bg = scale(a.astype(np.float32), 1.12 - 0.12 * e)
        p.stdin.write(np.clip(bg * (1 - fm) + fg * fm, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()


def card(sid, out, sec):
    text, path, px, col = CARDS[sid]
    im = Image.new("RGB", (W, H), "black"); d = ImageDraw.Draw(im); f = ImageFont.truetype(path, px)
    bb = d.textbbox((0, 0), text, font=f)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], (H - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=col)
    p = out + ".png"; im.save(p)
    n = int(math.ceil(sec * FPS)); fi = int(0.8 * FPS)
    run(["-loop", "1", "-i", p, "-vf", f"fade=in:0:{fi},fade=out:{n - fi}:{fi},format=yuv420p", "-frames:v", str(n), "-r", str(FPS)] + ENC + [out])
    os.remove(p)


FX_OVERRIDE = {"S02b": "push"}   # 그래픽 패널이 팬에 잘리지 않게


def default_fx(s):
    if s["id"] in FX_OVERRIDE:
        return FX_OVERRIDE[s["id"]]
    if s["edit_fx"] in ("push", "pull", "pan", "dutch7", "dutch5", "dollyzoom"):
        return s["edit_fx"]
    return "pan" if s["size"] in ("ws", "ews") else "push"


def main(only=None):
    sb = json.load(open(SB, encoding="utf-8"))["scenes"]
    durs = json.load(open(AUDIO, encoding="utf-8"))["scene_durations"]
    states = json.load(open(os.path.join(KF, "_states.json")))
    ids = {s["id"]: i for i, s in enumerate(sb, start=1)}
    os.makedirs(OUT, exist_ok=True)
    made, log = 0, []
    for i, s in enumerate(sb, start=1):
        if only and s["id"] not in only:
            continue
        tier, out, sec = s["tier"], os.path.join(OUT, f"scene{i:02d}.mp4"), durs[i - 1] + 0.5
        if tier in ("pro", "lite"):
            continue
        if tier == "card":
            card(s["id"], out, durs[i - 1]); made += 1; log.append(f"scene{i:02d} {s['id']} card"); continue
        src_id = s["kind"].split(":", 1)[1] if tier == "reuse" else s["id"]
        src = os.path.join(KF, f"{src_id}-1.png")
        if tier == "omni":
            fx = "static"
        elif tier == "reuse":
            fx = "push"
        else:
            fx = default_fx(s)
        if fx == "dollyzoom":
            dollyzoom(src, out, sec)
        elif src_id in states and tier in ("gfx", "reuse"):
            st = states[src_id] if tier == "gfx" else states[src_id][-1:]   # 재사용(정지 화면)은 마지막 상태
            cam_states(s["id"], out, sec, fx, st) if len(st) > 1 else cam(os.path.join(KF, st[0][1]), out, sec, fx)
        else:
            cam(src, out, sec, fx)
        made += 1; log.append(f"scene{i:02d} {s['id']} {tier} {fx}")
    print("\n".join(log)); print(f"교체 클립 {made}개 → {OUT}")


# ---------------- 생성 i2v 클립 후처리(무과금) ----------------
RAW = os.path.join(ROOT, "assets", "portraits", "tower-kf-raw")
POST_FX = {"S01f": "pull", "S19g": "pull", "S06a": "dutch5",   # i2v는 카메라 지시를 무시 → 편집에서(제8장 6)
           "S01a": "slow2.0"}   # 생성 검수: 2초 뒤 문이 닫히기 시작(이야기상 S01d에서 닫힘) → 앞 2초만 느리게 늘림
SPLIT = ["S14f", "S14g", "S14h"]                                  # 3분할: 패널이 하나씩 늘어난다


def read_frames(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, H, W, 3)


def write_frames(frames, out):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"] + ENC + [out],
                         stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close(); p.wait()


class SignTracker:
    """합성 표기를 i2v 클립에 붙인다 — 두 단계(감독님 지적 2026-10-07: 간판이 떨림, 측정 결과 프레임간 최대 107px).
    1) 표기 주변(사각형 bbox를 넉넉히 넓힌 영역)의 특징점만으로 프레임마다 위치·배율·회전(부분 아핀)을 구한다
       — 화면 전체 특징점은 걷는 사람·군중에 끌려 흔들렸다.
    2) 클립 전체의 사각형 모서리 궤적을 이상치 제거 후 '직선(1차)'으로 맞춘다 — 고정 카메라 i2v의 미세 드리프트만 남고 떨림 0.
    3) 맞춘 모서리로 프레임별 원근 변환을 만들어 합성본(차이 영역)을 붙인다."""
    def __init__(self, sid):
        import tower_composite as tc
        raw = np.asarray(Image.open(os.path.join(RAW, f"{sid}-1.png")).convert("RGB"))
        comp = np.asarray(Image.open(os.path.join(KF, f"{sid}-1.png")).convert("RGB"))
        diff = (np.abs(comp.astype(np.int16) - raw.astype(np.int16)).max(2) > 6).astype(np.uint8)
        diff = cv2.dilate(cv2.morphologyEx(diff, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), np.ones((7, 7), np.uint8))
        self.comp, self.mask = comp.astype(np.float32), cv2.GaussianBlur(diff.astype(np.float32), (0, 0), 2)
        self.kh, self.kw = raw.shape[:2]
        jobs = tc.JOBS.get(sid) or [(None, tc.PAIRS[sid][0], None)]
        self.q = np.float32(jobs[0][1])
        x, y, w, h = cv2.boundingRect(self.q.astype(np.int32)); pad = max(90, int(max(w, h) * 1.2))
        self.box = (max(0, x - pad), max(0, y - pad), min(self.kw, x + w + pad), min(self.kh, y + h + pad))
        m = np.zeros(raw.shape[:2], np.uint8); m[self.box[1]:self.box[3], self.box[0]:self.box[2]] = 255
        m[diff > 0] = 0   # 합성 글자 자리(원본은 무지)는 특징점에서 뺀다
        self.orb = cv2.ORB_create(3000); self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.kk, self.kd = self.orb.detectAndCompute(cv2.cvtColor(raw, cv2.COLOR_RGB2GRAY), m)
        self.sx = W / self.kw   # 키프레임 → 프레임(16:9 맞춤) 배율

    def corners(self, f):
        x0, y0, x1, y1 = [int(v * self.sx) for v in self.box]; pad = int(60 * self.sx)
        m = np.zeros((H, W), np.uint8); m[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad] = 255
        fk, fd = self.orb.detectAndCompute(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), m)
        if fd is None or self.kd is None or len(fk) < 8:
            return None
        ms = sorted(self.bf.match(self.kd, fd), key=lambda mm: mm.distance)[:400]
        if len(ms) < 8:
            return None
        A, inl = cv2.estimateAffinePartial2D(np.float32([self.kk[mm.queryIdx].pt for mm in ms]), np.float32([fk[mm.trainIdx].pt for mm in ms]),
                                             method=cv2.RANSAC, ransacReprojThreshold=2.5)
        if A is None or inl.sum() < 8:
            return None
        return cv2.transform(self.q.reshape(-1, 1, 2), A).reshape(-1, 2)

    def run(self, frames):
        n = len(frames); obs = [self.corners(f) for f in frames]
        t = np.array([i for i in range(n) if obs[i] is not None], np.float64)
        if len(t) < max(5, n // 5):   # 추적 실패 → 배율만 맞춘 고정 위치
            fit = np.repeat((self.q * self.sx)[None], n, 0)
        else:
            P = np.array([obs[int(i)] for i in t]).reshape(len(t), -1)   # (프레임, 8)
            keep = np.ones(len(t), bool)
            for _ in range(3):   # 직선 맞춤 + 이상치(중앙 절대편차 3배) 제거 반복
                co = np.polyfit(t[keep], P[keep], 1)
                res = np.abs(P - (np.outer(t, co[0]) + co[1])).max(1)
                mad = np.median(res[keep]) + 1e-6
                keep = res < max(3 * mad, 1.5)
            co = np.polyfit(t[keep], P[keep], 1)
            fit = (np.outer(np.arange(n), co[0]) + co[1]).reshape(n, 4, 2)
        src = np.float32([(0, 0), (self.kw, 0), (self.kw, self.kh), (0, self.kh)])
        out = []
        for i, f in enumerate(frames):
            Hm = cv2.getPerspectiveTransform(self.q, np.float32(fit[i]))
            c = cv2.warpPerspective(self.comp, Hm, (W, H)); mk = cv2.warpPerspective(self.mask, Hm, (W, H))[..., None]
            out.append(np.clip(f * (1 - mk) + c * mk, 0, 255).astype(np.uint8))
        self.fit = fit
        return out


def cam_frames(frames, fx):
    n = len(frames); out = []
    for i, f in enumerate(frames):
        t = i / max(1, n - 1)
        if fx == "pull":
            s = 1.06 - 0.06 * t
        else:
            s = 1.0
        M = cv2.getRotationMatrix2D((W / 2, H / 2), float(fx[5:]) if fx.startswith("dutch") else 0.0, s * (1.2 if fx.startswith("dutch") else 1.0))
        out.append(cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT))
    return out


def triptych(panels, n):
    """panels: [frames 또는 None]×3 — 세로 띠 3개(가운데 크롭), 아직 안 나온 패널은 검정."""
    pw, gap = (W - 2 * 8) // 3, 8; out = []
    for i in range(n):
        fr = np.zeros((H, W, 3), np.uint8)
        for k, pf in enumerate(panels):
            if pf is None:
                continue
            f = pf[min(i, len(pf) - 1)]; x0 = (W - pw) // 2
            fr[:, k * (pw + gap):k * (pw + gap) + pw] = f[:, x0:x0 + pw]
        out.append(fr)
    return out


def post(clips):
    sys.path.insert(0, os.path.join(ROOT, "scripts")); import tower_composite as tc
    sb = json.load(open(SB, encoding="utf-8"))["scenes"]; durs = json.load(open(AUDIO, encoding="utf-8"))["scene_durations"]
    idx = {s["id"]: i for i, s in enumerate(sb, start=1)}
    signs = set(tc.JOBS) | set(tc.PAIRS)
    for i, s in enumerate(sb, start=1):
        sid = s["id"]
        if s["tier"] not in ("pro", "lite") or not (sid in signs or sid in POST_FX):
            continue
        src = os.path.join(clips, f"scene{i:02d}.mp4")
        if not os.path.exists(src):
            print(f"scene{i:02d} {sid}: 클립 없음 — export_files로 먼저 가져오기"); continue
        fx = POST_FX.get(sid, "")
        if fx.startswith("slow"):
            t0 = float(fx[4:]); need = durs[i - 1] + 0.5; tmp = os.path.join(OUT, f"_{sid}_slow.mp4")
            run(["-i", src, "-t", f"{t0}", "-vf", f"setpts={need / t0:.4f}*PTS,minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:vsbmc=1"] + ENC + [tmp])
            src = tmp
        fr = list(read_frames(src))
        if src.endswith("_slow.mp4"):
            os.remove(src)
        if sid in signs:
            tr = SignTracker(sid); fr = tr.run(fr)
        if sid in POST_FX and not fx.startswith("slow"):
            fr = cam_frames(fr, POST_FX[sid])
        write_frames(fr, os.path.join(OUT, f"scene{i:02d}.mp4")); print(f"scene{i:02d} {sid}: " + " + ".join(x for x in ("표기 추적" if sid in signs else "", POST_FX.get(sid, "")) if x))
    # 3분할
    gi = idx["S14g"]; gsrc = os.path.join(clips, f"scene{gi:02d}.mp4")
    if os.path.exists(gsrc):
        g = list(read_frames(gsrc))
        stills = {}
        for k in ("S14f", "S14h"):   # 패널 원본은 키프레임에서 새로(재실행해도 3분할이 겹치지 않게)
            tmp = os.path.join(OUT, f"_{k}.mp4"); cam(os.path.join(KF, f"{k}-1.png"), tmp, durs[idx[k] - 1] + 0.5, "push")
            stills[k] = read_frames(tmp); os.remove(tmp)
        for k, sid in enumerate(SPLIT):
            n = int(math.ceil((durs[idx[sid] - 1] + 0.5) * FPS))
            panels = [stills["S14f"], g if k >= 1 else None, stills["S14h"] if k >= 2 else None]
            write_frames(triptych(panels, n), os.path.join(OUT, f"scene{idx[sid]:02d}.mp4"))
        print("3분할 S14f·S14g·S14h 완료")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "post":
        post(sys.argv[2])
    else:
        main(set(sys.argv[1:]) or None)
