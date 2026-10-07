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


def cam(src, out, sec, fx):
    n = max(1, int(math.ceil(sec * FPS)))
    tmp = out + ".png"; fit_png(src, tmp)
    run(["-loop", "1", "-i", tmp, "-vf", zoom_vf(n, fx) + ",format=yuv420p", "-frames:v", str(n)] + ENC + [out])
    os.remove(tmp)


def cam_states(sid, out, sec, fx, states):
    """같은 카메라로 상태별 클립을 만든 뒤 시간차 크로스페이드(0.15초)."""
    n = max(1, int(math.ceil(sec * FPS)))
    ins, tmps = [], []
    for t, f in states:
        p = os.path.join(OUT, f"_{sid}_{len(tmps)}.png"); fit_png(os.path.join(KF, f), p); tmps.append(p)
        ins += ["-loop", "1", "-i", p]
    chains = [f"[{k}:v]{zoom_vf(n, fx)}[z{k}]" for k in range(len(states))]
    cur = "z0"
    for k in range(1, len(states)):
        t0 = states[k][0] * sec; d = 0.15
        chains.append(f"[{cur}][z{k}]blend=all_expr='A*(1-clip((T-{t0:.3f})/{d},0,1))+B*clip((T-{t0:.3f})/{d},0,1)'[b{k}]")
        cur = f"b{k}"
    run(ins + ["-filter_complex", ";".join(chains) + f";[{cur}]format=yuv420p[o]", "-map", "[o]", "-frames:v", str(n)] + ENC + [out])
    for p in tmps:
        os.remove(p)


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


def default_fx(s):
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
POST_FX = {"S01f": "pull", "S19g": "pull", "S06a": "dutch5"}   # i2v는 카메라 지시를 무시 → 편집에서(제8장 6)
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
    """합성 전 키프레임 ↔ 클립 프레임 ORB 호모그래피로 합성 표기(차이 영역)를 프레임마다 옮겨 붙인다."""
    def __init__(self, sid):
        raw = np.asarray(Image.open(os.path.join(RAW, f"{sid}-1.png")).convert("RGB"))
        comp = np.asarray(Image.open(os.path.join(KF, f"{sid}-1.png")).convert("RGB"))
        diff = (np.abs(comp.astype(np.int16) - raw.astype(np.int16)).max(2) > 6).astype(np.uint8)
        diff = cv2.dilate(cv2.morphologyEx(diff, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), np.ones((7, 7), np.uint8))
        self.comp, self.mask = comp.astype(np.float32), cv2.GaussianBlur(diff.astype(np.float32), (0, 0), 2)
        self.orb = cv2.ORB_create(5000); self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.kk, self.kd = self.orb.detectAndCompute(cv2.cvtColor(raw, cv2.COLOR_RGB2GRAY), None)
        self.H = None

    def apply(self, f):
        g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY); fk, fd = self.orb.detectAndCompute(g, None)
        if fd is not None and len(fk) > 20:
            ms = sorted(self.bf.match(self.kd, fd), key=lambda m: m.distance)[:600]
            if len(ms) > 20:
                Hm, inl = cv2.findHomography(np.float32([self.kk[m.queryIdx].pt for m in ms]), np.float32([fk[m.trainIdx].pt for m in ms]), cv2.RANSAC, 3.0)
                if Hm is not None and inl.sum() > 15:
                    self.H = Hm if self.H is None else 0.6 * self.H + 0.4 * Hm   # 떨림 완화
        if self.H is None:
            return f
        c = cv2.warpPerspective(self.comp, self.H, (W, H)); m = cv2.warpPerspective(self.mask, self.H, (W, H))[..., None]
        return np.clip(f * (1 - m) + c * m, 0, 255).astype(np.uint8)


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
        fr = list(read_frames(src))
        if sid in signs:
            tr = SignTracker(sid); fr = [tr.apply(f) for f in fr]
        if sid in POST_FX:
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
