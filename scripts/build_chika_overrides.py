#!/usr/bin/env python3
"""『地下倉庫の伝票』 무료 교체 클립(video-overrides) 생성 (build_tower_overrides.py 구조) — 규격 제7장 2, 제8장 6 (로컬, 무과금).

스토리보드 방식별로 assets/video-overrides/chika/sceneNN.mp4 (NN = 장면 순번, 1부터)를 만든다. 1920x1080 24fps.
  still  정지 키프레임 → 편집 카메라 한 가지(와이드 = 느린 팬, 그 외 = 슬로 푸시인 1.00→1.05, edit_fx가 있으면 그것)
         dutch7 = 7° 회전(악역 붕괴 모티프), dollyzoom = 인물 마스크 2.5D(배경만 줌아웃, 인물 고정)
  gfx    합성 완료 키프레임 + 시간차 등장(_states.json: 스크린 쌍·피라미드·스크린 점등) 크로스페이드
  omni   대사 CU 정지 프레임 — burn 단계에서 OmniHuman이 음성 구동 영상으로 바꾼다
  card   타이틀·엔딩 카드(실글꼴, 페이드)
  reuse  원본 컷(still·gfx)에서 바로 만든다
i2v 컷(pro·lite)은 만들지 않는다(생성 후 post 단계: pull·dutch5·3분할 — post_i2v).
길이 = scene_durations + 0.5초(디졸브 겹침 여유).
사용법: python3 scripts/build_chika_overrides.py [장면ID ...]
        python3 scripts/build_chika_overrides.py post <clips_dir>   # 생성 i2v 클립 후처리(표기 추적·편집 카메라·더치·핸드헬드) → overrides에 추가
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
SB = os.path.join(ROOT, "scripts", "storyboard", "chika.json")
AUDIO = os.path.join(ROOT, "scripts", "audio", "chika.json")
KF = os.path.join(ROOT, "assets", "portraits", "chika-keyframes")
OUT = os.path.join(ROOT, "assets", "video-overrides", "chika")
W, H, FPS = 1920, 1080, 24
MIN_B = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")
MIN_R = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Regular.ttf")
CARDS = {"S01g": ("『地下倉庫の伝票』", MIN_B, 104, (236, 226, 200)),
         "S01h": ("二か月前", MIN_R, 72, (236, 232, 222)),
         "S09a": ("廃棄まで、あと二十日", MIN_R, 72, (236, 232, 222)),
         "S10g": ("廃棄まで、あと十四日", MIN_R, 72, (236, 232, 222)),
         "S11a": ("廃棄まで、あと三日", MIN_R, 72, (236, 232, 222)),
         "S17e": ("一か月後", MIN_R, 72, (236, 232, 222))}
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
    if fx == "crash":   # 정체 발각 순간: 빠르게 다가갔다가 멈춤(앞 40%에 대부분 진행)
        z = 1 + 0.14 * (1 - (1 - min(1.0, t / 0.4)) ** 3); cy = 0.5 - 0.5 * (1 - 1 / z)   # 얼굴 쪽(위)으로 — 화면 밖이 드러나지 않는 한도까지
    elif fx in ("", "push", "rack", "flash"):
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
    if fx == "flash":   # 프로젝터 점등: 첫 0.3초 흰 플래시가 빠르게 빠진다
        fl = int(0.3 * FPS)
        render(lambda i: im * (1 - max(0.0, 1 - i / fl)) + 255 * max(0.0, 1 - i / fl) if i < fl else im, out, n, fx)
        return
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


# 수정 9(2026-10-07): 회의장 재생성 컷 중 i2v 대신 정지 편집 카메라로(추가 과금 없이)
FORCE_STILL = set()
FX_OVERRIDE = {"S14d": "dollyzoom", "S14g": "flash", "S02c": "push"}   # S16d: 돌리줌 분리 실패(연설대가 갈라져 앞으로 나옴, 감독님 지적) → 빠른 푸시인   # 그래픽 패널이 팬에 잘리지 않게


# 감독님 지적(정지 영상 과다 2026-10-07): 사람이 있는 정지 컷은 2.5D 시차(인물·배경 분리, 서로 다른 속도),
# 연속 정지 컷은 무빙을 번갈아(같은 무빙 연속 금지). 미세하게 — 떨림으로 보이지 않게.
PARALLAX_MOVES = ["dolly_in", "truck_l", "dolly_out", "truck_r"]
_SEG = None


def person_mask(src):
    global _SEG
    cache = os.path.join(ROOT, "assets", "portraits", "chika-masks", os.path.basename(src))
    if os.path.exists(cache):
        return np.asarray(Image.open(cache).convert("L")).astype(np.float32) / 255
    from rembg import remove, new_session
    if _SEG is None:
        _SEG = new_session("u2net_human_seg")
    m = remove(Image.open(src).convert("RGB"), session=_SEG, only_mask=True)
    os.makedirs(os.path.dirname(cache), exist_ok=True); m.save(cache)
    return np.asarray(m).astype(np.float32) / 255


def parallax(src, out, sec, move):
    """인물(전경)과 배경을 따로 움직이는 2.5D 카메라. 배경의 인물 자리는 미리 메워 둔다(inpaint)."""
    n = max(1, int(math.ceil(sec * FPS)))
    im = np.asarray(Image.open(src).convert("RGB")); h, w = im.shape[:2]
    m = person_mask(src)
    hard = (m > 0.4).astype(np.uint8)
    hole = cv2.dilate(hard, np.ones((25, 25), np.uint8))
    bg = cv2.inpaint(im, hole * 255, 9, cv2.INPAINT_TELEA).astype(np.float32)
    fg = im.astype(np.float32); a = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None]
    base = max(W / w, H / h)
    def M(z, dx):
        T = cv2.getRotationMatrix2D((w / 2, h / 2), 0, base * z)
        T[0, 2] += W / 2 - w / 2 + dx * W; T[1, 2] += H / 2 - h / 2
        return T
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"] + ENC + [out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        t = i / max(1, n - 1); e = t * t * (3 - 2 * t) * 0.4 + t * 0.6
        if move == "dolly_in":
            zb, zf, db, df = 1.03 + 0.02 * e, 1.03 + 0.06 * e, 0, 0
        elif move == "dolly_out":
            zb, zf, db, df = 1.05 - 0.02 * e, 1.09 - 0.06 * e, 0, 0
        else:
            sgn = -1 if move == "truck_l" else 1
            zb, zf, db, df = 1.06, 1.06, sgn * (0.006 - 0.012 * e), sgn * (0.016 - 0.032 * e)
        B = cv2.warpAffine(bg, M(zb, db), (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        F = cv2.warpAffine(fg, M(zf, df), (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        A = cv2.warpAffine(a, M(zf, df), (W, H), flags=cv2.INTER_LINEAR)[..., None]
        p.stdin.write(np.clip(B * (1 - A) + F * A, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()


def default_fx(s, k=0):
    if s["id"] in FX_OVERRIDE:
        return FX_OVERRIDE[s["id"]]
    if s["edit_fx"] == "" and s["size"] not in ("ws", "ews") and k % 2 == 1:
        return "pull"   # 연속 정지 컷에서 밀기·당기기 교차
    if s["edit_fx"].split()[0] in ("push", "pull", "pan", "dutch7", "dutch5", "dollyzoom") if s["edit_fx"] else False:
        return s["edit_fx"].split()[0]
    return "pan" if s["size"] in ("ws", "ews") else "push"


def main(only=None):
    sb = json.load(open(SB, encoding="utf-8"))["scenes"]
    durs = json.load(open(AUDIO, encoding="utf-8"))["scene_durations"]
    states = json.load(open(os.path.join(KF, "_states.json")))
    ids = {s["id"]: i for i, s in enumerate(sb, start=1)}
    os.makedirs(OUT, exist_ok=True)
    made, log = 0, []
    run_i, prev_still = 0, False
    for i, s in enumerate(sb, start=1):
        if only and s["id"] not in only:
            continue
        tier, out, sec = s["tier"], os.path.join(OUT, f"scene{i:02d}.mp4"), durs[i - 1] + 0.5
        if tier in ("pro", "lite") and s["id"] not in FORCE_STILL:
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
            fx = default_fx(s, i)
        people = s["size"] != "ecu" and s["kind"] not in ("ins", "estill", "empty") and any(k in str(s["refs"]) for k in ("saori", "gondo", "miyamoto", "kiritani", "okochi"))
        if tier in ("still", "reuse") or s["id"] in FORCE_STILL:
            run_i = run_i + 1 if prev_still else 0
        prev_still = tier in ("still", "reuse", "gfx") or s["id"] in FORCE_STILL
        if fx == "dollyzoom":
            dollyzoom(src, out, sec)
        elif people and fx in ("push", "pan", "pull") and (tier == "still" or s["id"] in FORCE_STILL):
            mv = PARALLAX_MOVES[(i + run_i) % len(PARALLAX_MOVES)]
            parallax(src, out, sec, mv); fx = "parallax:" + mv
        elif src_id in states and tier in ("gfx", "reuse"):
            st = states[src_id] if tier == "gfx" else states[src_id][-1:]   # 재사용(정지 화면)은 마지막 상태
            cam_states(s["id"], out, sec, fx, st) if len(st) > 1 else cam(os.path.join(KF, st[0][1]), out, sec, fx)
        else:
            cam(src, out, sec, fx)
        made += 1; log.append(f"scene{i:02d} {s['id']} {tier} {fx}")
    print("\n".join(log)); print(f"교체 클립 {made}개 → {OUT}")


# ---------------- 생성 i2v 클립 후처리(무과금) ----------------
RAW = os.path.join(ROOT, "assets", "portraits", "chika-kf-raw")
# i2v는 카메라 지시를 무시 → 편집에서(제8장 6): 악역 컷 더치·핸드헬드(제8장 4·4-1), S18h 풀백(엔딩 크레인 대용)
POST_FX = {"S05a": "dutch5", "S15b2": "dutch7", "S18h": "pull", "S12a2": "hand", "S12d": "hand"}


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
        import chika_composite as tc
        raw = np.asarray(Image.open(os.path.join(RAW, f"{sid}-1.png")).convert("RGB"))
        comp = np.asarray(Image.open(os.path.join(KF, f"{sid}-1.png")).convert("RGB"))
        diff = (np.abs(comp.astype(np.int16) - raw.astype(np.int16)).max(2) > 6).astype(np.uint8)
        diff = cv2.dilate(cv2.morphologyEx(diff, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), np.ones((7, 7), np.uint8))
        self.kh, self.kw = raw.shape[:2]
        jobs = tc.JOBS[sid]
        self.q = np.float32(jobs[0][1])
        # 감독님 지적(현수막 떨림 2026-10-07): i2v가 합성 키프레임의 글자를 스스로 다시 그려, 우리 글자 테두리 밖으로
        # 매 프레임 모양이 바뀌는 AI 글자 잔상(점·이중 선)이 비쳤다 → 글자 주변만이 아니라 판·천 면 전체(사각형 6% 확장)를 덮는다
        c = self.q.mean(0); qe = c + (self.q - c) * 1.06
        face = np.zeros((self.kh, self.kw), np.uint8); cv2.fillPoly(face, [qe.astype(np.int32)], 1)
        cover = np.maximum(face, diff)
        self.comp, self.mask = comp.astype(np.float32), cv2.GaussianBlur(cover.astype(np.float32), (0, 0), 1.5)
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
    """편집 카메라(제8장 4-1): dutchN = N° 회전 + 1.2배, pull = 풀백, hand = 미세 핸드헬드(±0.6% 위치, ±0.3° 회전, 저주파)."""
    n = len(frames); out = []
    rng = np.random.default_rng(7)
    k = int(n / 6) + 2; nx, ny, nr = (np.convolve(rng.normal(0, 1, n + k), np.ones(k) / k, "valid")[:n] for _ in range(3))
    nx, ny, nr = (v / (np.abs(v).max() + 1e-6) for v in (nx, ny, nr))
    for i, f in enumerate(frames):
        t = i / max(1, n - 1)
        s = 1.06 - 0.06 * t if fx == "pull" else 1.0
        deg = float(fx[5:]) if fx.startswith("dutch") else 0.0
        if fx == "hand":
            s, deg = 1.03, 0.3 * nr[i]
        M = cv2.getRotationMatrix2D((W / 2, H / 2), deg, s * (1.2 if fx.startswith("dutch") else 1.0))
        if fx == "hand":
            M[0, 2] += 0.006 * W * nx[i]; M[1, 2] += 0.006 * H * ny[i]
        out.append(cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT))
    return out



def post(clips):
    sys.path.insert(0, os.path.join(ROOT, "scripts")); import chika_composite as tc
    sb = json.load(open(SB, encoding="utf-8"))["scenes"]; durs = json.load(open(AUDIO, encoding="utf-8"))["scene_durations"]
    idx = {s["id"]: i for i, s in enumerate(sb, start=1)}
    signs = set(tc.JOBS)
    for i, s in enumerate(sb, start=1):
        sid = s["id"]
        if s["tier"] not in ("pro", "lite", "hero") or not (sid in signs or sid in POST_FX):
            continue
        src = os.path.join(clips, f"scene{i:02d}.mp4")
        if not os.path.exists(src):
            print(f"scene{i:02d} {sid}: 클립 없음 — export_files로 먼저 가져오기"); continue
        fx = POST_FX.get(sid, "")
        if fx.startswith("slow"):
            t0 = float(fx[4:]); need = durs[i - 1] + 0.5; tmp = os.path.join(OUT, f"_{sid}_slow.mp4")
            run(["-t", f"{t0}", "-i", src, "-vf", f"setpts={need / t0:.4f}*PTS,minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:vsbmc=1"] + ENC + [tmp])
            src = tmp
        fr = list(read_frames(src))
        if src.endswith("_slow.mp4"):
            os.remove(src)
        if sid in signs:
            tr = SignTracker(sid); fr = tr.run(fr)
        if sid in POST_FX and not fx.startswith("slow"):
            fr = cam_frames(fr, POST_FX[sid])
        write_frames(fr, os.path.join(OUT, f"scene{i:02d}.mp4")); print(f"scene{i:02d} {sid}: " + " + ".join(x for x in ("표기 추적" if sid in signs else "", POST_FX.get(sid, "")) if x))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "post":
        post(sys.argv[2])
    else:
        main(set(sys.argv[1:]) or None)
