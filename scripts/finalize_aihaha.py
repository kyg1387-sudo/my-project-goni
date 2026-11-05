#!/usr/bin/env python3
"""『母が遺したビデオレター』 PHASE 6 마무리 (로컬, 무과금) — finalize_hikikomori.py 구조 + 이 작품 설계.

1) 컷 패치(원본 클립 → 매 프레임 처리 → 1920x1080 → 편집 카메라 → 같은 자막을 다시 구워 그 컷 자리에 덮음)
   - VIDSCREEN : 정지 컷(H0b 태블릿·S04l 태블릿·S09e TV) 화면 속에 가짜 비디오레터(H0a 립싱크 + 가짜 효과)를 매 프레임 합성
   - LAPTOP    : S06g(i2v) 노트북 화면 JICC → KSC 「該当なし」(lcd, 시간 중앙값으로 사람 보호)
   - FAKE      : H0a·S05a 가짜 영상 효과(배럴 2%·색수차 1px·입 12프레임 지연), CCTV: S03a·S06k(흑백·어안·15fps·압축·타임스탬프)
   - REUSE     : H2a ← S01e 립싱크(진짜 어머니), S05a ← H0a(창 쪽 푸시인), S06k ← S03a 정지 프레임 펀치 인(가방 쥔 손)
   - PAGEBLUR  : S07h 법전·S10h 서류의 가짜 글자 줄 흐림(종이색 픽셀만, 손 보호)
   - 카메라    : 설계표(18_카메라줌설계.md) 더치·핸드헬드·펀치·슬로 푸시·돌리줌 + 4.5초 넘는 립싱크 점프 컷(말 안 정적에서 1.00→1.10)
                 + 5초 넘는 한 구도(최우선 원칙 6②)는 가운데에서 1.10배 리프레임(두 번째 카메라), S01b는 5초 이후 정지 푸시(약통 변형 구간 제거)
2) 구석 소자막·H2b 중앙 카드 오버레이(클립 글자, .ass Caption 없음), 어두운 장면 리프트(평균 40/255 미만), 미세 대비·그레인
3) 오디오: 후크 0~3.5초 드론+심장 박동, 컷별 효과음(07_샷리스트 sfx), 장소별 반사음(19_통합지침-적용표 2절 — 대사만, 내레이션·AI母 건조),
   어머니 LINE 음성(S13 L56·L57) 휴대폰 대역 제한 + 방 공기음, 룸톤 베드, −14 LUFS / −1 dBTP
4) 아웃트로 + 구독 버튼 + 엔드카드 v2
사용법: python3 scripts/finalize_aihaha.py <remix 완성본.mp4> [--only S09g,S17d] [--patches-only] [--no-outro] [--rebuild]
"""
import json, math, os, re, shutil, subprocess, sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SKIT = "aihaha"
W, H, FPS = 1920, 1080, 24
FF = shutil.which("ffmpeg")
OUTD = os.path.join(ROOT, "out")
SB = json.load(open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), encoding="utf-8"))["scenes"]
AUDIO = json.load(open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), encoding="utf-8"))
KF = os.path.join(ROOT, "assets", "portraits", f"{SKIT}-keyframes")
GFX = os.path.join(ROOT, "assets", "preview", f"{SKIT}-graphics")
I2V = os.path.join(ROOT, "assets", "preview", SKIT)
OMNI_DIR = os.path.join(ROOT, "assets", "preview", f"{SKIT}-audio")
OVR = os.path.join(ROOT, "assets", "video-overrides", SKIT)
IDX = {s["id"]: k + 1 for k, s in enumerate(SB)}
BY = {s["id"]: s for s in SB}
OMNI = set(AUDIO["omnihuman_scenes"])
MINCHO = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf")

# ---------- 설계 ----------
FX = {"S04p": "dutch5", "S09r": "dutch7", "S08b": "handheld", "S08d": "handheld", "S08f": "handheld", "S09m": "punch", "S10k": "slowpush",
      "S05b": "dollyzoom", "S05a": "pushwin", "S06k": "punchhand"}  # 18_카메라줌설계.md (S02a matchcut·S11a·S13h는 교체 클립에 이미 반영)
PUNCH_AT = {"S09m": 0.35}
REUSE = {"H2a": ("S01e", 0.0), "S05a": ("H0a", 0.0), "S06k": ("S03a", 3.0)}  # (원본 컷, 원본 시작 초)
VIDSCREEN = {  # 키프레임(1344x768) 화면 네 꼭짓점(TL·TR·BR·BL) — 화면 위쪽 = 영상 위쪽
    "H0b": [(655.7, 294.3), (854.3, 385.7), (612.9, 522.9), (473.6, 442.9)],
    "S04l": [(735.0, 378.5), (916.0, 388.5), (954.0, 553.5), (769.5, 557.5)],
    "S09e": [(616.7, 444.0), (780.7, 444.0), (780.7, 537.3), (616.7, 537.3)],
}
VID_OFFSET = {"H0b": 0.0, "S04l": 1.2, "S09e": 2.0}  # 같은 영상의 다른 구간(L02·L11·L26 — 같은 음성 파일 재사용, 제21장 9)
LAPTOP = ("S06g", [(503.75, 461.7), (720.8, 450.0), (739.2, 588.3), (523.75, 610.8)],
          [(725.8, 478.3), (713.3, 515.8), (692.5, 557.5), (669.6, 595.0), (760, 640), (760, 440)])  # 화면 사각형, 앞 인물(머리·어깨) 보호 다각형
TVOFF = {"S10c": [(214, 307), (481, 307), (481, 490), (214, 490)]}  # 배경 TV가 흰 무지로 빛남 → 꺼진 화면(어두운 유리 + 옅은 반사), 매 프레임
PAGEBLUR = {"S07h": (100, 330, 760, 600), "S10h": (880, 450, 1344, 768)}  # 키프레임 좌표, 종이색 픽셀만 흐림
CCTV = {"S03a", "S06k"}
POST_CCTV = {"S06k", "S03a"}  # 펀치 인 뒤에 CCTV 화면 글자를 얹는다(먼저 얹으면 확대로 글자가 잘림)
FAKE = {"H0a", "S05a"}
S01B_HOLD = 5.0  # S01b 5초 이후 약통이 납작해짐 → 5초 프레임 정지 + 슬로 푸시
CORNERS = {"S01a": "corner_S01a", "S02a": "corner_S02a", "S04a": "corner_S04a", "S07a": "corner_S07a", "S08a": "corner_S08a", "S12a": "corner_S12a"}
CARD = ("H2b", "card_H2b", 4.15)  # 중앙 카드 — NA1 자막(~20.09초)이 끝난 뒤 2.3초만(자막과 글자 이중 금지, 2026-11-05 후크 점검)
EYES = ("H1", 2.6, (0.50, 0.30), 2.8)  # 0:09 「一度も瞬きをしなかった」 — 첫 2.6초 = 태블릿 속 가짜 엄마의 눈 ECU(깜빡임 없는 정지 응시 + 화면 픽셀 질감)
SPLIT = {  # 립싱크 재생성 검수(2026-11-05): (원본 컷 또는 omniNN, 원본 시작 초, 사용 길이 — None이면 컷 끝까지)
    "S11b": [("S11c", 0.0, None)],  # 「千葉県警です」 립싱크 거절 + 재생성본(omni128)은 「あの動画は」 첫 0.4초 입이 닫힘(R43) → 宮下 목소리 전체를 叔母의 굳는 얼굴 위로(L컷, 다음 컷 S11c와 한 호흡)
    "S11d": [("omni130", 0.0, 1.5), ("S11e", 0.0, None)],  # 1.7초부터 없던 叔母 등장·옷깃 꽃(재생성은 고개 90° 회전) → 「大野頼子さん」에서 叔母의 떨리는 손으로 L컷
    "S10i": [("omni120", 0.0, 2.02), ("S10j", 0.0, None)],  # 재생성 2회 모두 끝 「ん」에서 입이 크게 벌어짐(R43) → 마지막 0.25초는 叔父 반응으로 미리 넘김(L컷)
    "S07b": [("S07a", 2.2, 2.42), ("omni64", 2.42, None)],  # 「この動画と借用書を、」 동안 립싱크 입이 닫힘(R43) → 앞 와이드(S07a) 이어서 목소리 선행(J컷), 「調べていただけますか」부터 립싱크
}
OFFSET = {"S11c": 2.5, "S11e": 2.96, "S11g": 0.17, "S10j": 0.25}  # S11g: 원본 입이 소리보다 4프레임 늦음(R43 실측) → 영상을 4프레임 앞당김  # 위 L컷에서 앞부분을 쓴 컷은 뒤 구간부터(같은 움직임 반복 금지)
CLIP_FIXED = {"S02f"}  # 립싱크 재생성으로 교체한 컷(omni22.mp4, 원본 _v1) — 패치로 덮는다
CREEP = {  # 긴장 정적 구간 카메라(고니감독님 2026-11-05 「카메라 각도와 줌으로도 긴장감」): (최대 배율, cx, cy, 미세 흔들림)
    "S03a": (1.10, 0.62, 0.52, False), "S08l": (1.08, 0.5, 0.5, False), "S08n": (1.05, 0.5, 0.42, False),
    "S09p": (1.06, 0.5, 0.42, True), "S10j": (1.08, 0.5, 0.45, True),
}
KF_REDO = {"S08k", "S13f", "S04c", "S04e"}  # 마무리 단계에서 키프레임을 고친 정지 컷(족자 「南無阿弥陀仏」) — 교체 클립과 같은 푸시인으로 다시 만듦
STATIC = {"S05c", "S08i", "S08o"}  # 움직이는 컷 3연속 끊기 — 정지 교체 클립(푸시인) 대신 완전 고정(돌리줌 직후 정지 = 충격의 여운)
FX.update({"S10a": "punch"}); PUNCH_AT["S10a"] = 0.1  # 탁자 내리침 순간 — 펀치 인 3회째(작품당 6회 이하)
MULTICAM = {"S01i", "S06f", "S06j", "S07c", "S07g", "S09q", "S11d"}  # 같은 크기·각도 연속 쌍의 두 번째 컷 → 1.10배 화각 교체(제19장 17③, 제8장 2)
POLICE = {s["id"] for s in SB if s["lighting"] == "police_red"}  # S11 — 창으로 들어오는 경광등 빛 맥동(붉은 0.55Hz·푸른 엇박)
GRADE = {  # 조명 큐별 색(제8장 1·제3장 2) — 장면 안에서는 일정, 경계에서만 바뀜(색감 급변 금지)
    "wake": "colorbalance=rm=0.03:bm=-0.03:rh=0.02",                 # 통야 3200K 텅스텐
    "morning": "colorbalance=rm=0.02:bm=-0.02,eq=saturation=1.03",   # 간병 회상 디퓨즈 아침빛
    "sep_day": "colorbalance=rm=0.02:bm=-0.02,eq=saturation=1.03", "warm_liv": "colorbalance=rm=0.025:bm=-0.025",
    "night_lamp": "colorbalance=bs=0.025:rh=0.03:bh=-0.02",          # 밤 스탠드: 따뜻한 하이라이트·차가운 그림자
    "ryotei": "colorbalance=rm=0.015:bm=-0.01",
    "cold_liv": "colorbalance=rm=-0.02:bm=0.03,eq=saturation=0.95:contrast=1.02",  # 대면 형광등 5600K
    "analysis": "colorbalance=rm=-0.015:bm=0.025,eq=saturation=0.96", "police": "colorbalance=rm=-0.02:bm=0.03,eq=saturation=0.94",
    "nov_room": "colorbalance=rm=0.015:bm=-0.005,eq=saturation=1.02", "nov": "colorbalance=rm=0.015:bm=-0.005",
    "dusk": "colorbalance=rm=0.03:bm=-0.02:rh=0.03", "grey": "eq=saturation=0.94",
}
JLEAD = {"S03a": -0.5, "S04a": -0.5, "S09a": -0.5, "S13a": -0.5, "S11a": -0.3, "S02a": -0.5}  # 장면 연결 J컷(대본 10절) — 다음 장면 소리를 먼저
EXTRA_SFX = [("mokugyo", "S02a", -0.5, -18.0),  # S01 → S02 매치컷: 독경(목탁) 선행
             # 궁금증 극대화(고니감독님 2026-11-05 「궁금증을 최고로」): 광고 지점·반전 직전 1~2초 심장 박동으로 당기고 정점은 정적 + 저음 임팩트(최우선 원칙 6④)
             ("heartbeat", "S05a", -1.8, -15.0),  # 1차 광고 지점(3:23) 「息をのんだ」 직후 — 무엇을 봤나?
             ("heartbeat", "S09n", 0.3, -15.0),   # 「今、AIって」 실언 뒤 정적(479~486초)
             ("heartbeat", "S10k", -1.5, -15.0),  # 결정타 「期限は」 직전
             ("drone", "S08q", 0.0, -18.0),       # 2차 광고 예고 카드 「この後――」 아래 저음
             ("heartbeat", "S03b", 0.4, -14.0),   # 정적 구간(BGM 0) 1:44~1:55 빈 서랍
             ("heartbeat", "S06k", 0.5, -14.0)]   # 정적 구간 4:43~4:53 叔母의 손


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
    return "i2v" if os.path.exists(os.path.join(I2V, f"scene{i:02d}.mp4")) else "still"


def raw_path(sid):
    i, k = IDX[sid], kind(sid)
    if k == "omni":
        return os.path.join(OMNI_DIR, f"omni{i:02d}.mp4")
    if k == "i2v":
        return os.path.join(I2V, f"scene{i:02d}.mp4")
    return os.path.join(OVR, f"scene{i:02d}.mp4")


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


def kf_img(sid):
    return np.asarray(Image.open(os.path.join(KF, f"{sid}-1.png")).convert("RGB"))


def kf_map(sid, frame):
    """키프레임(1344x768) 좌표 → 클립 좌표 (scale, ox, oy). 첫 프레임과 키프레임 정합(matchTemplate)."""
    k = cv2.cvtColor(kf_img(sid), cv2.COLOR_RGB2GRAY).astype(np.float32)
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
    return [(x * s - ox, y * s - oy) for x, y in q]


# ---------- 화면 합성 ----------
def warp(art, quad, w, h):
    a = art.astype(np.float32); hh, ww = a.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]]), np.float32(quad))
    return cv2.warpPerspective(a, M, (w, h), flags=cv2.INTER_AREA, borderValue=(0, 0, 0))


def lcd_put(b, art, quad, keep=150, refl=0.15, blur=0.8, protect=None):
    """밝은 무지 화면만 교체(LCD 흰색·푸른 기·비네트·반사) — aihaha_composite.lcd와 같은 규칙. protect: 0~1(1 = 앞 사람 보호)."""
    h, w = b.shape[:2]
    a = art.astype(np.float32) * 0.88 + np.array([4, 8, 18], np.float32)
    ah, aw = a.shape[:2]; yy, xx = np.mgrid[0:ah, 0:aw]
    a *= (1 - 0.10 * (((xx - aw / 2) / (aw / 2)) ** 2 + ((yy - ah / 2) / (ah / 2)) ** 2))[..., None]
    wa = cv2.GaussianBlur(warp(np.clip(a, 0, 255), quad, w, h), (0, 0), blur)
    poly = np.zeros((h, w), np.float32); cv2.fillConvexPoly(poly, np.int32(np.round(quad)), 1.0); poly = cv2.GaussianBlur(poly, (0, 0), 1.0)
    bf = b.astype(np.float32)
    key = np.clip((bf.mean(2) - keep) / 30, 0, 1); key = cv2.GaussianBlur(key, (0, 0), 1.0) * poly
    if protect is not None:
        key *= (1 - protect)
    out = wa * (1 - refl) + bf * refl
    return np.clip(bf * (1 - key[..., None]) + out * key[..., None], 0, 255).astype(np.uint8)


def tv_off(f, quad):
    """켜진 무지 TV → 꺼진 화면: 밝은 화면 영역(밝기 140↑)을 찾아 넓혀(번짐 포함) 어두운 유리색으로 통째로 덮고 원래 밝기 10%를 반사로 남김.
    밝기 키를 반만 걸면 초점 밖 화면 가장자리에 하늘색 테두리가 남고, 기준을 낮추면 벽까지 어두워진다(S10c 실측)."""
    h, w = f.shape[:2]
    poly = np.zeros((h, w), np.uint8); cv2.fillConvexPoly(poly, np.int32(np.round(quad)), 1)
    bright = ((f.mean(2) > 140) & (poly > 0)).astype(np.uint8)
    m = cv2.dilate(bright, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 3.0)[..., None]
    g = f.astype(np.float32); dark = np.array([22, 25, 30], np.float32) + 0.10 * g
    return np.clip(g * (1 - m) + dark * m, 0, 255).astype(np.uint8)


def barrel(f, k):
    h, w = f.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (xx - w / 2) / (w / 2), (yy - h / 2) / (w / 2); r2 = nx * nx + ny * ny
    mx = (w / 2 + nx * (1 - k * r2) * (w / 2)).astype(np.float32); my = (h / 2 + ny * (1 - k * r2) * (w / 2)).astype(np.float32)
    return cv2.remap(f, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def fake_video(frames):
    """극 중 AI 영상(제21장 4): 배럴 2%·색수차 1px·지나치게 매끈한 피부(약한 bilateral)·입은 소리와 정확히 일치(R43)."""
    out = []
    for f in frames:
        g = barrel(f, 0.02)
        g = cv2.bilateralFilter(g, 5, 18, 5)
        r, gg, bb = cv2.split(g)
        r = np.roll(r, 1, axis=1); bb = np.roll(bb, -1, axis=1)
        out.append(cv2.merge([r, gg, bb]))
    return out  # 입 지연 없음(R43 — 의도한 0.5초 지연이 시청자에게는 립싱크 오류로 보였다)


# ---------- 서류 매 프레임 합성(R44·R46, 2026-11-05 「날인 종이가 많이 나오는데 정확하게 내용」) ----------
# 컷 → [(x0, y0, x1, y1, 그림, 회전, 세기, 흐림, 방식)] — 좌표 = cover 뒤 1920x1080(카메라 효과 전).
#   그림: "loan1~3" 차용증(S04c와 같은 그래픽) · "back" 뒷면(인물이 읽는 쪽이 앞면 → 우리에게는 뒷면, 앞면 인쇄가 옅게 비침) · "report" 「該当なし」 보고서
#   회전 0~3: 종이 네 모서리(왼쪽 위부터 시계 방향) 기준 글자 위쪽 방향 — 2 = 맞은편 사람을 향해 놓인 종이(우리에게는 거꾸로)
#   방식: "static" 탁자 위(전 프레임 중앙값 사각형) · "track" 손에 든 종이(프레임마다 추적 + 부드럽게)
PAPERS = {
    "S04b": [(560, 930, 880, 1080, "loan1", 0, 0.85, 1.6, "static"), (900, 960, 1360, 1080, "loan2", 0, 0.85, 1.4, "static"),
             (1500, 1010, 1920, 1080, "loan3", 0, 0.85, 1.8, "static")],
    "S04g": [(640, 840, 1100, 1080, "back", 0, 0.16, 3.0, "track"), (950, 815, 1340, 960, "back", 0, 0.16, 2.0, "track"),
             (1000, 950, 1360, 1080, "loan2", 2, 0.8, 1.6, "static")],
    "S04d": [(1300, 990, 1920, 1080, "loan2", 2, 0.8, 1.6, "static")],
    "S04r": [(1080, 640, 1400, 800, "loan1", 2, 0.7, 2.2, "static")],
    "S04j": [(1480, 990, 1920, 1080, "loan1", 0, 0.8, 1.8, "static")],
    "S04f": [(1100, 930, 1540, 1080, "loan1", 1, 0.8, 1.6, "static"), (1450, 920, 1920, 1080, "loan2", 1, 0.8, 2.0, "static")],
    "S04l": [(330, 860, 1010, 1010, "loan3", 0, 0.75, 2.4, "static")],
    "S07e": [(540, 860, 1380, 1080, "back", 0, 0.14, 2.5, "track")],
    "S07g": [(780, 870, 1340, 1080, "back", 0, 0.14, 2.5, "track")],
    "S09o": [(700, 900, 1060, 1080, "back", 0, 0.14, 2.5, "track"), (980, 860, 1300, 1080, "back", 0, 0.14, 2.5, "track")],
}


AUTO_SHEETS = {"S04a": (["loan1", "loan2", "loan3"], 0.85, 1.1,
                         [[(515, 640), (740, 540), (1310, 865), (827, 1411)], [(769, 533), (1067, 387), (1620, 627), (1333, 847)],
                          [(1067, 387), (1413, 320), (1833, 467), (1620, 627)]])}
# 叔父가 펼쳐 놓은 차용증 3장(R44): 세 장이 모두 놓인 앞 구간(PINGPONG)만 쓰고, 첫 프레임에서 잰 네 모서리를 배경 특징점 호모그래피로
# 카메라 움직임에 맞춰 옮긴다(프레임마다 종이를 새로 찾으면 장이 붙어 보이거나 글자가 깜빡임 — 실측)


def auto_sheets(sid, frames):
    names, strength, blur, quads = AUTO_SHEETS[sid]
    arts = [cv2.GaussianBlur(paper_art(n), (0, 0), blur * 2) for n in names]
    orb = cv2.ORB_create(3000); g0 = cv2.cvtColor(frames[0], cv2.COLOR_RGB2GRAY)
    hsv0 = cv2.cvtColor(frames[0], cv2.COLOR_RGB2HSV)
    mask0 = (~(((hsv0[..., 0] < 25) & (hsv0[..., 1] > 50)))).astype(np.uint8) * 255  # 손(피부)은 특징점에서 제외
    k0, d0 = orb.detectAndCompute(g0, mask0); bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    out = []; Hp = np.eye(3)
    for f in frames:
        g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY); k1, d1 = orb.detectAndCompute(g, None)
        Hm = Hp
        if d1 is not None and len(k1) > 50:
            mt = sorted(bf.match(d0, d1), key=lambda m: m.distance)[:600]
            if len(mt) > 30:
                A = np.float32([k0[m.queryIdx].pt for m in mt]); Bp = np.float32([k1[m.trainIdx].pt for m in mt])
                H_, inl = cv2.findHomography(A, Bp, cv2.RANSAC, 3.0)
                if H_ is not None and inl.sum() > 25:
                    Hm = H_
        Hp = Hp * 0.5 + Hm * 0.5  # 떨림 완화
        hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV)
        paper = ((hsv[..., 2] > 140) & (hsv[..., 1] < 60)).astype(np.float32)
        paper = cv2.GaussianBlur(cv2.erode(paper, np.ones((5, 5), np.uint8)), (0, 0), 1.5)
        gg = f.astype(np.float32)
        for art, q in zip(arts, quads):
            qq = cv2.perspectiveTransform(np.float32(q)[None], Hp)[0]
            ah, aw = art.shape[:2]
            M = cv2.getPerspectiveTransform(np.float32([[0, 0], [aw, 0], [aw, ah], [0, ah]]), qq)
            wa = cv2.warpPerspective(art, M, (f.shape[1], f.shape[0]), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
            poly = np.zeros(f.shape[:2], np.float32); cv2.fillConvexPoly(poly, np.int32(qq), 1.0)
            key = paper * cv2.GaussianBlur(cv2.erode(poly, np.ones((7, 7), np.uint8)), (0, 0), 1.0)
            gg = gg * (1 - (1 - wa / 255.0) * strength * key[..., None])
        out.append(np.clip(gg, 0, 255).astype(np.uint8))
    return out


def paper_art(name):
    if name.startswith("loan"):
        return np.asarray(Image.open(os.path.join(GFX, f"S04c_{name}.png")).convert("RGB")).astype(np.float32)
    if name == "back":  # 뒷면: 앞면 인쇄가 거울상으로 옅게(종이를 통해 비침)
        a = np.asarray(Image.open(os.path.join(GFX, "S04c_loan1.png")).convert("RGB")).astype(np.float32)[:, ::-1]
        return cv2.GaussianBlur(a, (0, 0), 3.0)
    return np.asarray(Image.open(os.path.join(GFX, "S09a_form.png")).convert("RGB")).astype(np.float32)


def _order(pts):
    c = pts.mean(0); ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]); p = pts[np.argsort(ang)]
    k = int(np.argmin(p.sum(1))); return np.roll(p, -k, axis=0)  # 왼쪽 위부터 시계 방향(화면 좌표, y 아래)


def _paper_quad(f, box):
    x0, y0, x1, y1 = box
    sub = f[y0:y1, x0:x1]
    hsv = cv2.cvtColor(sub, cv2.COLOR_RGB2HSV)
    m = ((hsv[..., 2] > 150) & (hsv[..., 1] < 50)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None, None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    if st[k, cv2.CC_STAT_AREA] < 1500:
        return None, None
    comp = (lab == k).astype(np.uint8)
    cs, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(max(cs, key=cv2.contourArea))
    q = None
    for eps in (0.02, 0.03, 0.045, 0.06, 0.08):
        ap = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
        if len(ap) == 4:
            q = ap.reshape(4, 2).astype(np.float32); break
    if q is None:
        q = cv2.boxPoints(cv2.minAreaRect(hull)).astype(np.float32)
    full = np.zeros(f.shape[:2], np.uint8); full[y0:y1, x0:x1] = comp
    return _order(q + [x0, y0]), full


def papers(sid, frames):
    out = [f.astype(np.float32) for f in frames]
    for (x0, y0, x1, y1, name, rot, strength, blur, mode) in PAPERS[sid]:
        art = paper_art(name); ah, aw = art.shape[:2]
        if blur:
            art = cv2.GaussianBlur(art, (0, 0), blur * aw / 600)
        qs = [_paper_quad(f, (x0, y0, x1, y1))[0] for f in frames]
        good = [q for q in qs if q is not None]
        if not good:
            print(f"  [{sid}] 종이 못 찾음 {name} {x0},{y0}"); continue
        med = np.median(np.stack(good), 0)
        area0 = cv2.contourArea(med.astype(np.float32))
        if mode == "track":  # 손으로 들어 올린 종이(아랫면이 보임)·잘못 잡힌 면적은 건너뜀 → 그 프레임은 무지 그대로
            qs = [q if q is not None and abs(cv2.contourArea(q.astype(np.float32)) / max(area0, 1) - 1) < 0.35 else None for q in qs]
        sm, prev = [], None
        for q in qs:
            if mode == "track" and q is None:
                sm.append(None); continue
            if mode == "static" or q is None:
                q = med if mode == "static" or prev is None else prev
            elif prev is not None:
                q = prev * 0.6 + q * 0.4
            prev = q; sm.append(q)
        src = np.roll(np.float32([[0, 0], [aw, 0], [aw, ah], [0, ah]]), rot, axis=0)
        for i, f in enumerate(frames):
            if sm[i] is None:
                continue
            M = cv2.getPerspectiveTransform(src, np.float32(sm[i]))
            wa = cv2.warpPerspective(art, M, (f.shape[1], f.shape[0]), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
            _, comp = _paper_quad(f, (x0, y0, x1, y1))
            if comp is None:
                continue
            key = cv2.GaussianBlur(cv2.erode(comp.astype(np.float32), np.ones((5, 5), np.uint8)), (0, 0), 1.5)
            poly = np.zeros(f.shape[:2], np.float32); cv2.fillConvexPoly(poly, np.int32(sm[i]), 1.0)
            key = key * cv2.GaussianBlur(poly, (0, 0), 1.0)
            out[i] = out[i] * (1 - (1 - wa / 255.0) * strength * key[..., None])
    return [np.clip(o, 0, 255).astype(np.uint8) for o in out]


# 립싱크 결과에서 말하는 동안 입이 닫힌 구간(R43 전수 검수): 같은 클립을 확대한 손·소품 인서트로 가린다 (시작초, 끝초, 배율, cx, cy)
INSERTS = {}


# 생성 영상 중간에 결함이 생기는 컷: 깨끗한 앞 구간만 동작 보간(광학 흐름)으로 천천히 앞뒤로 오가며 채움(R50 — S13c 1초 뒤 오른손목에 시계가 하나 더 생김)
PINGPONG = {"S13c": (0, 15, 3), "S04a": (0, 15, 3)}  # (시작 프레임, 끝 프레임, 느리게 배수)


def slow_pingpong(fr, a, b, k):
    seg = fr[a:b + 1]; dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    out = []
    for i in range(len(seg) - 1):
        f0, f1 = seg[i], seg[i + 1]; out.append(f0)
        g0, g1 = cv2.cvtColor(f0, cv2.COLOR_RGB2GRAY), cv2.cvtColor(f1, cv2.COLOR_RGB2GRAY)
        fl = dis.calc(g0, g1, None); fb = dis.calc(g1, g0, None)
        h, w = g0.shape; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        for j in range(1, k):
            t = j / k
            m0 = cv2.remap(f0, xx + fb[..., 0] * t, yy + fb[..., 1] * t, cv2.INTER_LINEAR)
            m1 = cv2.remap(f1, xx + fl[..., 0] * (1 - t), yy + fl[..., 1] * (1 - t), cv2.INTER_LINEAR)
            out.append(cv2.addWeighted(m0, 1 - t, m1, t, 0))
    out.append(seg[-1])
    loop = out + out[-2:0:-1]
    return (loop * 10)[: max(len(fr), 4 * len(loop))]


# 손목시계 시계판(R49, 2026-11-05 「이 장면은 어떤 장면인지 정확하게」): 생성 영상의 시계판이 바늘 없는 흰 원판 → 실제 바늘(저녁 7시 48분)
# + 날짜 창 「3」(10월 3일 = 기한 다음 날) + 1초마다 움직이는 초침(시계 소리와 같은 박자), 케이스는 다른 컷과 같은 은색(금색으로 바뀌는 결함)
WATCHES = {"S10c": dict(ref=30, seed=(1062, 510), axes=(62, 68), win=24, keys=[(0, (1078, 495, 58, 42, -15)), (12, (1076, 497, 56, 48, -8))], keys_until=20, hm=(7, 48), date="3", sec0=12)}


def _dial_art(h, m, sec, date, n=240):
    im = Image.new("RGB", (n, n), (255, 255, 255)); d = ImageDraw.Draw(im); c = n / 2; r = n / 2 - 6
    for k in range(60):
        a = math.radians(k * 6); L = 0.13 if k % 5 == 0 else 0.05; wdt = 5 if k % 5 == 0 else 2
        p0 = (c + math.sin(a) * r * (0.93 - L), c - math.cos(a) * r * (0.93 - L)); p1 = (c + math.sin(a) * r * 0.93, c - math.cos(a) * r * 0.93)
        if k != 15:
            d.line([p0, p1], fill=(70, 70, 74), width=wdt)
    bx = (c + r * 0.50, c - r * 0.12, c + r * 0.80, c + r * 0.12)  # 3시 날짜 창
    d.rectangle(bx, fill=(252, 252, 250), outline=(90, 90, 90), width=2)
    d.text(((bx[0] + bx[2]) / 2, c + 1), date, font=ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", int(r * 0.2)), fill=(25, 25, 28), anchor="mm")
    def hand(ang, L, wdt, col, back=0.12):
        a = math.radians(ang); d.line([(c - math.sin(a) * r * back, c + math.cos(a) * r * back), (c + math.sin(a) * r * L, c - math.cos(a) * r * L)], fill=col, width=wdt)
    hand((h % 12) * 30 + m * 0.5, 0.52, 9, (30, 30, 34)); hand(m * 6 + sec * 0.1, 0.80, 6, (30, 30, 34)); hand(sec * 6, 0.86, 2, (160, 30, 30), 0.2)
    d.ellipse((c - 6, c - 6, c + 6, c + 6), fill=(30, 30, 34))
    return np.asarray(im).astype(np.float32)


def watches(sid, frames):
    cfg = WATCHES[sid]; out = []; found = [None] * len(frames)
    # 기준 프레임의 시계(원판+케이스) 모양을 템플릿으로 앞뒤 프레임을 따라감(흰 원판과 흰 벽이 색으로는 안 갈림)
    k0 = cfg["ref"]; cx, cy = cfg["seed"]; ax, ay = cfg["axes"]; T = 46
    gray = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in frames]
    tpl = gray[k0][int(cy - T):int(cy + T), int(cx - T):int(cx + T)]
    for order in (range(k0, len(frames)), range(k0 - 1, -1, -1)):
        prev = np.array([cx, cy], float)
        for i in order:
            x0, y0 = int(prev[0] - T - cfg["win"]), int(prev[1] - T - cfg["win"])
            win = gray[i][max(y0, 0):y0 + 2 * (T + cfg["win"]), max(x0, 0):x0 + 2 * (T + cfg["win"])]
            r = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
            if mv < cfg.get("min_score", 0.45):
                break  # 시계가 비스듬해져 모양이 달라지면 거기서 멈춤(그 앞 프레임은 원래 그대로)
            prev = np.array([max(x0, 0) + ml[0] + T, max(y0, 0) + ml[1] + T], float)
            found[i] = np.array([prev[0], prev[1], ax, ay, 0.0])
            nt = gray[i][int(prev[1] - T):int(prev[1] + T), int(prev[0] - T):int(prev[0] + T)]
            if nt.shape == tpl.shape:
                tpl = cv2.addWeighted(tpl, 0.6, nt, 0.4, 0)  # 템플릿을 조금씩 갱신(시계가 천천히 돌아가도 따라감)
        tpl = gray[k0][int(cy - T):int(cy + T), int(cx - T):int(cx + T)]
    for (k, e0) in cfg.get("keys", []):  # 비스듬한 앞 구간: 손으로 잰 타원(중심·축·기울기)으로 고정하고 추적 구간까지 보간
        found[k] = np.array(e0, float)
    ks = [k for k, _ in cfg.get("keys", [])]
    if ks:
        k1 = cfg["keys_until"]; a0 = found[ks[-1]]; a1 = found[k1] if found[k1] is not None else a0
        for i in range(ks[-1] + 1, k1):
            t = (i - ks[-1]) / (k1 - ks[-1]); found[i] = a0 * (1 - t) + a1 * t
        for j in range(len(ks) - 1):
            for i in range(ks[j] + 1, ks[j + 1]):
                t = (i - ks[j]) / (ks[j + 1] - ks[j]); found[i] = found[ks[j]] * (1 - t) + found[ks[j + 1]] * t
    good = [e for e in found if e is not None]
    sm = []; last = None
    for e in found:
        if e is None:
            sm.append(None); continue
        last = e if last is None else np.r_[last[:4] * 0.5 + e[:4] * 0.5, e[4]]; sm.append(last)
    for i, f in enumerate(frames):
        e = sm[i]; g = f.astype(np.float32)
        if e is None or min(e[2], e[3]) < 10:
            out.append(f); continue
        sec = cfg["sec0"] + int(i / FPS)
        art = _dial_art(cfg["hm"][0], cfg["hm"][1], sec, cfg["date"])
        n = art.shape[0]; (ex, ey, ea, eb, ang) = e
        a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
        # 단위 원 → 타원(축 ea·eb, 회전 ang): 원판 안쪽 92%
        M = np.float32([[ca * ea / n * 0.92, -sa * eb / n * 0.92, 0], [sa * ea / n * 0.92, ca * eb / n * 0.92, 0]])
        M[:, 2] = [ex, ey] - M[:, :2] @ [n / 2, n / 2]
        wa = cv2.warpAffine(art, M, (f.shape[1], f.shape[0]), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
        wa = cv2.GaussianBlur(wa, (0, 0), 0.8)
        mk = np.zeros(f.shape[:2], np.float32); cv2.ellipse(mk, ((ex, ey), (ea * 0.95, eb * 0.95), ang), 1.0, -1); mk = cv2.GaussianBlur(mk, (0, 0), 1.2)
        g = g * (1 - (1 - wa / 255.0) * 0.92 * mk[..., None])
        # 케이스 은색: 시계 둘레(축 1.7배) 안의 금빛(색상 16~25·채도 40~120·밝음, 실측) 픽셀만 무채색 금속으로 — 피부(색상 ≤ 14·채도 높음)는 그대로
        zone = np.zeros(f.shape[:2], np.uint8); cv2.ellipse(zone, ((ex, ey), (ea * 1.7, eb * 1.7), ang), 1, -1)
        hsv = cv2.cvtColor(np.clip(g, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
        gold = ((hsv[..., 0] >= 14) & (hsv[..., 0] <= 28) & (hsv[..., 1] > 35) & (hsv[..., 1] < 140) & (hsv[..., 2] > 85) & (zone > 0)).astype(np.float32)
        gold = np.clip(cv2.GaussianBlur(gold, (0, 0), 0.8) * 1.3, 0, 1)
        lum = g.mean(2, keepdims=True) * 1.05 + 3
        g = g * (1 - gold[..., None]) + np.concatenate([lum * 0.98, lum, lum * 1.03], 2) * gold[..., None]
        out.append(np.clip(g, 0, 255).astype(np.uint8))
    print(f"  [{sid}] 시계판 추적 {len(good)}/{len(frames)}")
    return out


# 화면·소품 정합(R47): 좌표 = cover 뒤 1920x1080. paused = 방금 본 가짜 영상의 멈춘 화면(재생 표시줄 + 재생 버튼),
# off = 꺼진 화면(어두운 유리 + 옅은 반사), photo = 어머니 사진(영정·액자)
SCREENS_C = {
    "H2b": [("pausedtrack", (950, 520, 1600, 800))],  # 태블릿을 내려놓으며 화면이 켜짐 → 켜진 화면 사각형을 프레임마다 찾아 멈춘 영상으로
    "S05c": [("paused", [(320, 852), (468, 845), (475, 945), (320, 950)])],
    "S08l": [("paused", [(855, 918), (985, 912), (993, 948), (862, 955)]), ("photo", [(866, 549), (929, 549), (929, 644), (866, 644)])],
    "S09k": [("offfull", [(232, 874), (600, 878), (600, 1080), (234, 1080)])],
    "S13c": [("off", [(1312, 962), (1620, 962), (1625, 1080), (1312, 1080)])],
}


def _paused_art():
    f = cv2.resize(cover(kf_img("H0a")), (640, 360), interpolation=cv2.INTER_AREA).astype(np.float32)
    f = fake_video([f.astype(np.uint8)])[0].astype(np.float32) * 0.9
    f[330:336, 20:620] = f[330:336, 20:620] * 0.4 + 90; f[330:336, 20:260] = (235, 60, 60)  # 재생 표시줄(멈춘 지점)
    im = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse((290, 150, 350, 210), fill=(0, 0, 0, 0), outline=(240, 240, 240), width=4)
    d.polygon([(311, 163), (311, 197), (339, 180)], fill=(240, 240, 240))  # 재생 버튼(일시정지 상태)
    return np.asarray(im).astype(np.float32)


def screens_c(sid, frames):
    sys.path.insert(0, os.path.join(ROOT, "scripts")); import aihaha_composite as C
    out = frames
    for kind_, q in SCREENS_C[sid]:
        if kind_ == "off":
            out = [tv_off(f, q) for f in out]
        elif kind_ == "offfull":  # 화면 전체가 하늘색으로 빛남(밝기 키로는 테두리가 남음) → 사각형 전체를 꺼진 유리로(위쪽이 살짝 밝은 반사)
            h_, w_ = out[0].shape[:2]; poly = np.zeros((h_, w_), np.float32); cv2.fillConvexPoly(poly, np.int32(q), 1.0)
            poly = cv2.GaussianBlur(poly, (0, 0), 2.5)[..., None]
            ys = np.linspace(1, 0, h_)[:, None, None]
            res = []
            for f in out:
                g = f.astype(np.float32); dark = np.array([20, 23, 28], np.float32) + 0.06 * g + 10 * ys
                res.append(np.clip(g * (1 - poly) + dark * poly, 0, 255).astype(np.uint8))
            out = res
        elif kind_ == "paused":
            art = _paused_art(); med = np.median(np.stack(out[::4]).astype(np.float32), 0)
            res = []
            for f in out:
                d = np.linalg.norm(f.astype(np.float32) - med, axis=2)
                prot = cv2.GaussianBlur(np.clip((d - 26) / 30, 0, 1).astype(np.float32), (0, 0), 2)  # 화면 앞을 지나는 손 보호
                res.append(lcd_put(f, art, q, keep={'H2b': 70}.get(sid, 150), refl=0.12, blur=0.9, protect=prot))
            out = res
        elif kind_ == "pausedtrack":
            art = _paused_art(); x0, y0, x1, y1 = q; res = []; prev = None
            for f in out:
                sub = f[y0:y1, x0:x1]; m = (sub.max(2) > 95).astype(np.uint8)
                m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
                n, lab, st, _ = cv2.connectedComponentsWithStats(m)
                if n < 2 or st[1:, cv2.CC_STAT_AREA].max() < 3000:
                    res.append(f); continue
                k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
                cs, _ = cv2.findContours((lab == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                hull = cv2.convexHull(max(cs, key=cv2.contourArea)); qq = None
                for eps in (0.02, 0.035, 0.05, 0.07):
                    ap = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
                    if len(ap) == 4:
                        qq = ap.reshape(4, 2).astype(np.float32); break
                if qq is None:
                    qq = cv2.boxPoints(cv2.minAreaRect(hull)).astype(np.float32)
                qq = _order(qq + [x0, y0]); c_ = qq.mean(0); qq = c_ + (qq - c_) * 1.09  # 화면 가장자리까지(가장자리 어두운 띠가 검출에서 빠짐)
                prev = qq if prev is None else prev * 0.5 + qq * 0.5
                res.append(lcd_put(f, art, prev, keep=-200, refl=0.10, blur=0.9))  # 화면 전체 교체(원래 앱 아이콘이 비치지 않게)
            out = res
        elif kind_ == "photo":
            ph = np.asarray(C.portrait().convert("RGB")).astype(np.float32)
            out = [np.clip(C.put_photo(f.astype(float), C.portrait(), q, blur=1.6), 0, 255).astype(np.uint8) for f in out]
    return out


def cctv(frames):
    """돌봄 카메라: 흑백·어안 6%·15fps 끊김·압축 블록·노이즈 + 타임스탬프(그래픽)."""
    ts = np.asarray(Image.open(os.path.join(GFX, "cctv_S03a.png")).convert("RGBA").resize((W, H))).astype(np.float32)
    out, last = [], None
    for i, f in enumerate(frames):
        if i % 8 in (2, 5, 7) and last is not None:  # 24 → 약 15fps
            out.append(last); continue
        g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY); g = cv2.cvtColor(g, cv2.COLOR_GRAY2RGB)
        g = barrel(g, 0.06)
        small = cv2.resize(g, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
        g = cv2.resize(small, (W, H), interpolation=cv2.INTER_NEAREST) * 0.25 + g * 0.75
        g = g + np.random.default_rng(i).normal(0, 6, g.shape)
        g = g * (1 - ts[..., 3:] / 255) + ts[..., :3] * (ts[..., 3:] / 255)
        last = np.clip(g, 0, 255).astype(np.uint8); out.append(last)
    return out


def h0a_frames():
    fr = [cover(f) for f in read_frames(raw_path("H0a"))]
    return fake_video(fr)


# 화면 속 가짜 영상(R43): V1 = L01 립싱크(omni01 = H0a), V2 = L02 립싱크(같은 키프레임, aihaha-omni-fix3 omni-02v).
# 컷마다 (컷 안 시각, 영상, 그 시각의 영상 시각) — 완성본 소리와 패드 음성의 상호상관으로 잼(H0b L02 −0.01초, S04l L01 −0.07·L02 +3.46초, S09e L01 −0.10초)
VIDSEQ = {"H0b": [(0.0, "V2", 0.01)], "S04l": [(0.0, "V1", 0.07), (3.46, "V2", 0.0)], "S09e": [(0.0, "V1", 0.10)]}
V2_PATH = os.path.join(ROOT, "assets", "auditions", "aihaha-omni-fix3", "omni-02v.mp4")
_VCACHE = {}


def video_letter(name):
    if name not in _VCACHE:
        path = raw_path("H0a") if name == "V1" else V2_PATH
        _VCACHE[name] = fake_video([cover(f) for f in read_frames(path)])
    return _VCACHE[name]


def vid_screen(sid, n):
    """정지 키프레임 화면 속에 가짜 영상(재생바 포함)을 매 프레임 합성 → 1344x768 프레임 n장. 입 모양은 그 컷에서 들리는 대사와 일치(VIDSEQ)."""
    base = kf_img(sid); seq = VIDSEQ[sid]; k0 = int(VID_OFFSET[sid] * FPS)
    out = []
    for i in range(n):
        t = i / FPS; t0, name, st = [x for x in seq if x[0] <= t + 1e-6][-1]
        src = video_letter(name); f = src[min(int(round((t - t0 + st) * FPS)), len(src) - 1)]
        art = cv2.resize(f, (640, 360), interpolation=cv2.INTER_AREA).astype(np.float32)
        bar = int(640 * min(1.0, (k0 + i) / (134 * FPS) + 0.02))
        art[340:346, 20:620] = art[340:346, 20:620] * 0.4 + 90
        art[340:346, 20:20 + max(bar - 20, 4)] = (235, 60, 60)
        out.append(lcd_put(base, np.clip(art, 0, 255), VIDSCREEN[sid], keep=150, refl=0.12, blur=0.7))
    return out


def laptop(frames):
    sid, q0, occ0 = LAPTOP
    s, ox, oy = kf_map(sid, frames[0]); q = mapq(q0, s, ox, oy); occ = mapq(occ0, s, ox, oy)
    a1 = np.asarray(Image.open(os.path.join(GFX, "S06g_jicc.png")).convert("RGB"))
    a2 = np.asarray(Image.open(os.path.join(GFX, "S06g_ksc.png")).convert("RGB"))
    h, w = frames[0].shape[:2]
    om = np.zeros((h, w), np.float32); cv2.fillPoly(om, [np.int32(occ)], 1.0); om = cv2.GaussianBlur(om, (0, 0), 3)
    med = np.median(np.stack(frames[::3]).astype(np.float32), axis=0)
    out = []
    for i, f in enumerate(frames):
        d = np.linalg.norm(f.astype(np.float32) - med, axis=2)
        moving = 1 - np.clip(1 - (d - 28) / 30, 0, 1)
        prot = np.clip(np.maximum(om, cv2.GaussianBlur(moving.astype(np.float32), (0, 0), 2)), 0, 1)
        out.append(lcd_put(f, a1 if i < len(frames) // 2 else a2, q, keep=170, refl=0.15, protect=prot))
    return out


def page_blur(sid, frames):
    s, ox, oy = kf_map(sid, frames[0]); x0, y0, x1, y1 = PAGEBLUR[sid]
    (ax, ay), (bx, by) = mapq([(x0, y0), (x1, y1)], s, ox, oy)
    out = []
    for f in frames:
        g = f.copy(); h, w = f.shape[:2]
        X0, Y0, X1, Y1 = max(int(ax), 0), max(int(ay), 0), min(int(bx), w), min(int(by), h)
        reg = f[Y0:Y1, X0:X1].astype(np.float32)
        hsv = cv2.cvtColor(f[Y0:Y1, X0:X1], cv2.COLOR_RGB2HSV).astype(np.float32)
        m = np.clip((reg.mean(2) - 120) / 30, 0, 1) * np.clip((90 - hsv[..., 1]) / 30, 0, 1)  # 밝고 채도 낮은 종이만(손 피부 제외)
        m = cv2.GaussianBlur(cv2.erode(m, np.ones((5, 5), np.uint8)), (0, 0), 2)[..., None]
        bl = cv2.GaussianBlur(reg, (0, 0), 2.6)
        g[Y0:Y1, X0:X1] = np.clip(reg * (1 - m) + bl * m, 0, 255).astype(np.uint8)
        out.append(g)
    return out


# ---------- 편집 카메라 ----------
def zoom_frame(f, z, cx=0.5, cy=0.5, dx=0.0, dy=0.0, rot=0.0):
    if abs(z - 1) < 1e-4 and not dx and not dy and not rot:
        return f
    M = cv2.getRotationMatrix2D((cx * W, cy * H), rot, z)  # (cx,cy)를 고정점으로 확대 — z≥1이면 가장자리가 비지 않음(회전 7°는 z≥1.06)
    M[0, 2] += dx * W; M[1, 2] += dy * H
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


def jump_cuts():
    """4.5초 넘는 립싱크 컷(설계 효과 없는 것) — 점프 컷 1.00→1.10(제19장 17①)."""
    return [s["id"] for s in SB if IDX[s["id"]] in OMNI and s["assembled_s"] > 4.5 and s["id"] not in FX and s["id"] not in SPLIT]  # SPLIT 컷은 이미 컷이 바뀜(연속 두 번 끊김 금지)


def long_cuts():
    """5초 넘는 한 구도(립싱크·설계 효과 제외) — 가운데에서 1.10배 리프레임(최우선 원칙 6②)."""
    return [s["id"] for s in SB if s["assembled_s"] > 5.0 and IDX[s["id"]] not in OMNI and s["id"] not in FX and s["id"] not in CREEP and s["id"] not in STATIC and s["tier"] != "card"]


def camera(sid, frames, sec, src):
    n = len(frames); fx = FX.get(sid, "")
    if sid in jump_cuts():
        tj = quiet_point(src, 0.35 * sec, 0.75 * sec) or 0.5 * sec
        kj = int(round(tj * FPS)); print(f"  [{sid}] 점프 컷 {tj:.2f}s")
        return [zoom_frame(f, 1.10 if i >= kj else 1.0, 0.5, 0.40) for i, f in enumerate(frames)]
    if fx.startswith("dutch"):  # 악역 탐욕·붕괴(제8장 4) — 회전 + 회전 여백 확대
        deg = float(fx[5:]); return [zoom_frame(f, 1.12 + 0.02 * i / max(n - 1, 1), rot=deg) for i, f in enumerate(frames)]
    if fx == "handheld":  # 악역 패닉 미세 흔들림(제8장 4-1)
        return [zoom_frame(f, 1.06, dx=0.004 * math.sin(i / 7.0), dy=0.004 * math.cos(i / 9.0)) for i, f in enumerate(frames)]
    if fx == "punch":
        k0 = int(PUNCH_AT.get(sid, 0.4) * FPS)
        return [zoom_frame(f, 1 + 0.12 * min(max((i - k0) / 7, 0), 1), 0.5, 0.45) for i, f in enumerate(frames)]
    if fx == "slowpush":
        return [zoom_frame(f, 1 + 0.05 * i / max(n - 1, 1), 0.5, 0.42) for i, f in enumerate(frames)]
    if fx == "dollyzoom":  # 작품당 1회(정체 발각, 제8장 4) — 인물 마스크 없는 근사
        k = int(1.6 * FPS); return [zoom_frame(f, 1 + 0.12 * min(i / k, 1), 0.5, 0.42) for i, f in enumerate(frames)]
    if fx == "pushwin":  # 가짜 영상 재시청 — 창밖 완공 타워 쪽으로
        return [zoom_frame(f, 1 + 0.10 * i / max(n - 1, 1), 0.72, 0.35) for i, f in enumerate(frames)]
    if fx == "punchhand":
        return [zoom_frame(f, 1 + 0.12 * min(i / 8, 1), 0.64, 0.60) for i, f in enumerate(frames)]
    if sid in CREEP:  # 정적 속에서 천천히 조여 오는 카메라(드레드 줌), 악역은 미세 핸드헬드
        zm, cx, cy, shake = CREEP[sid]
        return [zoom_frame(f, 1 + (zm - 1) * (i / max(n - 1, 1)) ** 1.3 + (0.01 if shake else 0), cx, cy,
                           dx=0.003 * math.sin(i / 6.0) if shake else 0, dy=0.003 * math.cos(i / 8.0) if shake else 0) for i, f in enumerate(frames)]
    if sid in MULTICAM:
        return [zoom_frame(f, 1.10, 0.5, 0.42) for f in frames]
    if sid in long_cuts():
        k = n // 2
        return [zoom_frame(f, (1.0 + 0.02 * i / k) if i < k else (1.10 + 0.02 * (i - k) / max(n - k, 1)), 0.5, 0.45) for i, f in enumerate(frames)]
    return frames


def source_frames(sid):
    """컷 원본 프레임(1920x1080) — 재사용·가짜 영상·CCTV·화면 합성·흐림 처리 포함."""
    if sid in REUSE:
        rid, off = REUSE[sid]
        fr = [cover(f) for f in read_frames(raw_path(rid), off)]
        if sid == "S05a":  # 내레이션 위에서 가짜 엄마 입이 움직이면 「다른 사람 말에 입이 움직임」(R43) → 다시 보며 멈춘 화면(입 다문 키프레임)
            fr = [cover(kf_img("H0a"))] * (int(round(BY[sid]["assembled_s"] * FPS)) + 2)
        if sid == "S06k":  # 일시정지 화면(정지 프레임) + CCTV
            fr = [fr[0]] * 200
        if rid in FAKE or sid in FAKE:
            fr = fake_video(fr)
        if sid in CCTV and sid not in POST_CCTV:
            fr = cctv(fr)
        return fr
    if sid in STATIC:
        n = int(round(BY[sid]["assembled_s"] * FPS)) + 2
        return [cover(kf_img(sid))] * n
    if sid in KF_REDO:
        n = int(round(BY[sid]["assembled_s"] * FPS)) + 2; base = cover(kf_img(sid))
        return [zoom_frame(base, 1 + 0.05 * i / n) for i in range(n)]
    if sid in VIDSCREEN:
        n = int(round(BY[sid]["assembled_s"] * FPS)) + 2
        base = [cover(f) for f in vid_screen(sid, n)]
        return [zoom_frame(f, 1 + 0.04 * i / n, 0.5, 0.5) for i, f in enumerate(base)]  # 정지 컷 기본 푸시인(교체 클립과 같음)
    if sid in SPLIT:
        out, n = [], int(round(BY[sid]["assembled_s"] * FPS)) + 2
        for src, st, ln in SPLIT[sid]:
            path = os.path.join(OMNI_DIR, f"{src}.mp4") if src.startswith("omni") else raw_path(src)
            fr = [cover(f) for f in read_frames(path, st)]
            k = int(round(ln * FPS)) if ln else n - len(out)
            out += (fr + [fr[-1]] * k)[:k]
        return out
    fr = read_frames(raw_path(sid), OFFSET.get(sid, 0.0))
    if sid in PINGPONG:
        fr = slow_pingpong(fr, *PINGPONG[sid])
    if sid == EYES[0]:
        k = int(EYES[1] * FPS); src = h0a_frames(); f0 = src[2]  # 말하기 전 입을 다문 프레임(입 벌린 채 정지 금지)
        cx, cy = EYES[2]; z = EYES[3]
        yy, xx = np.mgrid[0:H, 0:W]
        sub = np.stack([(xx % 3 == 0), (xx % 3 == 1), (xx % 3 == 2)], -1).astype(np.float32) * 0.10 + 0.93  # LCD 서브픽셀
        eyes = []
        for j in range(k):
            g = zoom_frame(f0, z + 0.06 * j / k, cx, cy).astype(np.float32) * sub
            g = g * (1 + 0.015 * math.sin(j * 1.7)) + np.random.default_rng(j).normal(0, 2.5, g.shape)  # 화면 깜빡임·센서 노이즈(눈은 그대로)
            eyes.append(np.clip(g, 0, 255).astype(np.uint8))
        rest = [cover(f) for f in fr]
        return eyes + rest
    if sid == LAPTOP[0]:
        fr = laptop(fr)
    if sid in PAGEBLUR:
        fr = page_blur(sid, fr)
    if sid in TVOFF:
        sc, ox, oy = kf_map(sid, fr[0]); q = mapq(TVOFF[sid], sc, ox, oy)
        fr = [tv_off(f, q) for f in fr]
    fr = [cover(f) for f in fr]
    if sid in PAPERS:
        fr = papers(sid, fr)
    if sid in AUTO_SHEETS:
        fr = auto_sheets(sid, fr)
    if sid in WATCHES:
        fr = watches(sid, fr)
    if sid in FAKE:
        fr = fake_video(fr)
    if sid in CCTV and sid not in POST_CCTV:  # POST_CCTV는 build_cut에서 1회만(R47 Q1 — 글자 이중 표시)
        fr = cctv(fr)
    if sid == "S01b":
        k = int(S01B_HOLD * FPS); n = int(round(BY[sid]["assembled_s"] * FPS)) + 2
        fr = fr[:k] + [zoom_frame(fr[k - 1], 1 + 0.05 * j / max(n - k, 1), 0.45, 0.6) for j in range(max(n - k, 0))]
    return fr


def police(frames):
    """경광등: 붉은 기가 있는 픽셀(커튼·벽 반사)만 붉은·푸른 빛이 엇박으로 맥동 — 얼굴 전체를 칠하지 않는다(제21장 17④)."""
    out = []
    for i, f in enumerate(frames):
        g = f.astype(np.float32); t = i / FPS
        red = np.clip((g[..., 0] - g[..., 1] - 18) / 40, 0, 1)
        pr = 0.5 + 0.5 * math.sin(2 * math.pi * 0.55 * t); pb = 0.5 + 0.5 * math.sin(2 * math.pi * 0.55 * t + math.pi)
        amb = 0.05 * (0.5 + 0.5 * math.sin(2 * math.pi * 0.55 * t))  # 방 전체에 아주 옅은 붉은 기(창빛)
        g[..., 0] *= 1 + 0.22 * pr * red + amb
        g[..., 2] *= 1 + 0.14 * pb * red
        out.append(np.clip(g, 0, 255).astype(np.uint8))
    return out


def build_cut(sid, sec, tmp):
    out = os.path.join(tmp, f"cut_{sid}.mp4")
    if os.path.exists(out) and "--rebuild" not in sys.argv:
        return out
    src = raw_path(REUSE[sid][0]) if sid in REUSE else raw_path(sid)
    if sid in SPLIT:
        src = os.path.join(OMNI_DIR, f"{SPLIT[sid][-1][0]}.mp4") if SPLIT[sid][-1][0].startswith("omni") else raw_path(SPLIT[sid][-1][0])
    if sid not in VIDSCREEN and not os.path.exists(src):
        print(f"  [{sid}] 원본 없음 — 건너뜀: {src}")
        return None
    frames = source_frames(sid)
    if sid in SCREENS_C:
        frames = screens_c(sid, frames)
    if sid in POLICE:
        frames = police(frames)
    n = int(round(sec * FPS)) + 1
    frames = (frames + [frames[-1]] * n)[:n]
    raw_fr = frames
    frames = camera(sid, frames, sec, src)
    for (t0, t1, z, cx, cy) in INSERTS.get(sid, []):  # 립싱크 입이 닫힌 구간 → 같은 클립의 손·소품 인서트(R43)
        for i in range(int(t0 * FPS), min(int(t1 * FPS), len(frames))):
            frames[i] = zoom_frame(raw_fr[i], z, cx, cy)
    if sid in POST_CCTV:
        frames = cctv(frames)
    write_frames(frames, out)
    return out


def moving_check():
    """움직이는 카메라 컷 비율 35% 이하·연속 3컷 금지(제19장 17) — 정지 교체 클립(푸시인)도 움직이는 컷으로 센다."""
    mv = [x["id"] in CREEP or FX.get(x["id"], "") in ("dutch5", "dutch7", "handheld", "slowpush", "dollyzoom", "pushwin", "punchhand", "punch")
          or (x["tier"] == "still" and x["id"] not in STATIC) for x in SB]
    run3 = [SB[i]["id"] for i in range(len(SB) - 2) if mv[i] and mv[i + 1] and mv[i + 2]]
    print(f"움직이는 카메라 컷 {sum(mv)}/{len(SB)} = {sum(mv) / len(SB):.0%} · 연속 3컷 {run3}")
    return sum(mv) / len(SB), run3


def targets():
    t = set(FX) | set(REUSE) | set(VIDSCREEN) | {LAPTOP[0], EYES[0]} | MULTICAM | POLICE | set(CREEP) | STATIC | KF_REDO | set(TVOFF) | set(SPLIT) | set(OFFSET) | CLIP_FIXED | set(PAGEBLUR) | set(PAPERS) | set(PINGPONG) | set(WATCHES) | set(SCREENS_C) | set(INSERTS) | set(AUTO_SHEETS) | CCTV | FAKE | {"S01b"} | set(jump_cuts()) | set(long_cuts())
    t -= {"S11a", "S13h", "S02a"}
    return sorted(t, key=lambda s: IDX[s])


def overlays(B):
    """구석 소자막·중앙 카드(RGBA 1920x1080 그래픽) — (그래픽, 시작, 끝)."""
    ov = [(os.path.join(GFX, f"{g}.png"), B[sid][0] + 0.3, min(B[sid][0] + 3.2, B[sid][1])) for sid, g in CORNERS.items()]
    sid, g, off = CARD
    ov.append((os.path.join(GFX, f"{g}.png"), B[sid][0] + off, B[sid][1] - 0.1))
    return ov


def grade_filter(B):
    """같은 조명 큐가 이어지는 컷을 한 구간으로 묶어 색 필터를 건다."""
    runs, cur = [], None
    for x in SB:
        a, b = B[x["id"]]; g = x["lighting"]
        if cur and cur[0] == g:
            cur[2] = b
        else:
            if cur:
                runs.append(cur)
            cur = [g, a, b]
    runs.append(cur)
    parts = []
    for g, a, b in runs:
        for flt in GRADE.get(g, "").split(","):
            if flt:
                parts.append(f"{flt}:enable='between(t,{a:.3f},{b:.3f})'")
    return "".join(p + "," for p in parts)


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


def missing_sources():
    """패치 대상 컷 원본이 로컬에 있는지(제21장 30 — 없으면 조용히 건너뛰어 효과가 빠진 실증)."""
    miss = []
    for sid in targets():
        paths = [raw_path(REUSE[sid][0]) if sid in REUSE else raw_path(sid)] if sid not in VIDSCREEN else []
        if sid in SPLIT:
            paths = [os.path.join(OMNI_DIR, f"{p}.mp4") if p.startswith("omni") else raw_path(p) for p, _, _ in SPLIT[sid]]
        miss += [(sid, p) for p in paths if not os.path.exists(p)]
    if any(s_ in VIDSEQ and n == "V2" for s_ in VIDSEQ for _, n, _ in VIDSEQ[s_]) and not os.path.exists(V2_PATH):
        miss.append(("VIDSEQ", V2_PATH))
    return miss


def patch(src, out, tmp, only=None):
    B = bounds()
    miss = missing_sources()
    if miss and "--allow-missing" not in sys.argv:
        sys.exit("원본 없음 — 무료 반출(export_files)부터: " + ", ".join(f"{a}:{os.path.basename(b)}" for a, b in miss))
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
    inputs, fc, last = ["-i", src], [], "[0:v]"
    for k, (a, b, c) in enumerate(segs, start=1):
        inputs += ["-i", c]
        fc.append(f"[{k}:v]trim=0:{b - a + 1 / FPS:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB,ass={ass}:fontsdir={fdir}[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    k0 = len(segs)
    for j, (g, a, b) in enumerate(overlays(B), start=k0 + 1):
        inputs += ["-loop", "1", "-t", f"{b - a:.3f}", "-i", g]
        fc.append(f"[{j}:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1,fade=t=out:st={max(b - a - 0.4, 0):.3f}:d=0.4:alpha=1,setpts=PTS-STARTPTS+{a:.3f}/TB[g{j}]")
        fc.append(f"{last}[g{j}]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[q{j}]"); last = f"[q{j}]"
    fc.append(f"{last}eq=contrast=1.03:saturation=0.98,{grade_filter(B)}{lift_filter(src)}noise=alls=3:allf=t+u,format=yuv420p[v]")
    script = os.path.join(tmp, "patch_fc.txt"); open(script, "w").write(";\n".join(fc))
    run(inputs + ["-filter_complex_script", script, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                  "-c:a", "copy", out])
    return [s for s in targets() if not only or s in only]


# ---------- 오디오 ----------
SPACE = {  # 19_통합지침-적용표 2절: 장면 → (지연 ms, 감쇠, 섞는 양 dB)
    "room": (12, 0.25, -24), "living": (18, 0.30, -22), "ryotei": (25, 0.30, -22), "police": (22, 0.40, -20), "genkan": (15, 0.35, -21),
}
SCENE_SPACE = {"S01": "room", "S02": "living", "S03": "living", "S04": "ryotei", "S05": "room", "S06": "living", "S07": "police",
               "S08": "living", "S09": "living", "S10": "living", "S11": "living", "S13": "room"}
DRY_STYLES = {"Naration", "AIHaha"}  # 내레이션 = 반사 없는 클로즈마이크, 가짜 영상 = 무잔향 건조
PHONE_LINES = []  # 어머니 LINE 음성(S13 Sawako) — 휴대폰 스피커 대역 제한


def ass_events():
    ev = []
    for ln in open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), encoding="utf-8"):
        if not ln.startswith("Dialogue:"):
            continue
        p = ln.split(",", 9); st = p[3]
        def t(x):
            h, m, s = x.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
        ev.append((t(p[1]), t(p[2]), st))
    return ev


def scene_at(t, B):
    for sid, (a, b) in B.items():
        if a <= t < b:
            return sid
    return SB[-1]["id"]


def sfx_list():
    """07_샷리스트 「- Sxx: sfx:<id>」 → (파일, 컷, 오프셋, 피크 dBFS). 정점(저음 임팩트·탁자·인터폰)은 −9, 나머지 −16."""
    out = []
    for ln in open(os.path.join(ROOT, "productions", f"{SKIT}-ja", "07_샷리스트.md"), encoding="utf-8"):
        m = re.match(r"- (\S+): sfx:(\w+)", ln.strip())
        if m and m.group(1) in IDX:
            sid, sx = m.groups(); p = os.path.join(ROOT, "assets", "sfx", SKIT, f"{sx}.mp3")
            if sx == "watch_tick":
                continue  # 시계 초침은 CLOCK 구간 단위로(파일 하나를 컷 시작에 얹으면 12초 동안 컷 경계를 넘어 계속 울림)
            pk = -9.0 if sx in ("sub_hit", "table_slam", "intercom_chime") else (-14.0 if sx in ("drone", "heartbeat", "siren_far") else -16.0)
            out.append((p, sid, JLEAD.get(sid, 0.05), pk))
    for sx, sid, off, pk in EXTRA_SFX:
        out.append((os.path.join(ROOT, "assets", "sfx", SKIT, f"{sx}.mp3"), sid, off, pk))
    # 긴장 정적 구간(BGM 0) 안의 효과음은 최대로(고니감독님 「최대한 높여」): 임팩트 −4, 나머지 −7 dBFS — 어머니 음성 구간(여운)은 그대로
    B = bounds(); win = [(w["start"], w["end"]) for w in AUDIO["bgm_silence"] if w["sfx_boost_db"] >= 5]
    def boost(p, sid, off, pk):
        t = B[sid][0] + off
        if any(a - 0.6 <= t <= b for a, b in win):
            pk = max(pk, -4.0 if os.path.basename(p)[:-4] in ("sub_hit", "table_slam", "intercom_chime") else -7.0)
        return (p, sid, off, pk)
    return [boost(*x) for x in out]


# 시계 초침(R48, 고니감독님 「시계바늘 가는 소리로 실감 나게 째깍째깍」): 실제 기계식 시계처럼 1초 한 번 째·깍 교대(make_clock_tick.py),
# 시계가 보이거나 정적 속에서 시간을 재는 구간에만 그 구간 길이만큼 — (파일, 시작 컷, 끝 컷, 피크 dBFS)
CLOCK = [("watch_tick", "S01i", "S01i", -24.0),   # 어머니가 떠난 아침 — 손목시계를 푸는 손
         ("watch_tick", "S08i", "S08i", -10.0),   # 펜 끝이 떨림(정적 구간)
         ("watch_tick", "S08l", "S08n", -9.0),    # 혼자 남은 밤 「腕時計の針だけが、静かに進んでいた」(정적 구간)
         ("watch_tick", "S10c", "S10c", -16.0),   # 「今日は、何日ですか」 시계를 봄
         ("wall_clock", "S10j", "S10j", -8.0),    # 결정타 앞 한 박자 — 벽시계(정적 구간)
         ("watch_tick", "S10l", "S10l", -11.0)]   # 시계 접사 「時計に負けていた」


def clock_list():
    B = bounds(); out = []
    for sx, a, b, pk in CLOCK:
        out.append((os.path.join(ROOT, "assets", "sfx", SKIT, f"{sx}.mp3"), B[a][0], B[b][1], pk))
    return out


def peak_db(path):
    e = subprocess.run([FF, "-v", "info", "-i", path, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(e.split("max_volume:")[1].split("dB")[0])


def voice_layers(B, vd, tmp):
    """대사 반사음(젖은 소리만) + 어머니 LINE 음성 휴대폰 처리 — 대사 줄 원본(audio-overrides)을 자막 시각에 놓는다."""
    ev = ass_events(); lines = sorted(f for f in os.listdir(os.path.join(ROOT, "assets", "audio-overrides", SKIT)) if f.startswith("line"))
    assert len(ev) == len(lines), f"자막 {len(ev)} ≠ 음성 {len(lines)}"
    ins, fc, labs, phone = [], [], "", []
    for k, ((a, b, st), f) in enumerate(zip(ev, lines)):
        sid = scene_at(a + 0.05, B); sc = sid[:3]
        if st in DRY_STYLES or sc not in SCENE_SPACE:
            continue
        p = os.path.join(ROOT, "assets", "audio-overrides", SKIT, f); ms = int(a * 1000)
        j = 2 + len(ins) // 2; ins += ["-i", p]  # 입력 0 = 패치본, 1 = 후크 베드
        if st == "Sawako" and sc == "S13":  # 휴대폰 스피커: 대역 제한 + 방 반사(마른 원음은 패치에서 대체)
            phone.append((a, b))
            fc.append(f"[{j}:a]aformat=sample_rates=44100:channel_layouts=stereo,highpass=f=320,lowpass=f=5800,acompressor=threshold=-18dB:ratio=3,"
                      f"aecho=0.85:0.5:14:0.22,volume=0.9,adelay={ms}|{ms},apad=whole_dur={vd:.3f}[v{j}]")
        else:
            d, dc, db = SPACE[SCENE_SPACE[sc]]
            fc.append(f"[{j}:a]aformat=sample_rates=44100:channel_layouts=stereo,aecho=0:1:{d}|{d * 2 + 7}:{dc}|{dc * 0.5:.2f},"
                      f"volume={db}dB,adelay={ms}|{ms},apad=whole_dur={vd:.3f}[v{j}]")
        labs += f"[v{j}]"
    return ins, fc, labs, phone


def hook_bed(path):
    fc = ("sine=f=110:d=3.5,aeval=val(0)*(1-0.5*t/3.5):c=mono[s1];anoisesrc=d=3.5:c=brown:a=0.3,lowpass=f=220[n];"
          "[s1][n]amix=inputs=2:normalize=0,volume=0.32,afade=t=in:st=0:d=0.3,afade=t=out:st=3.2:d=0.3[dr];"
          "sine=f=52:d=0.18,afade=t=out:st=0.05:d=0.13,volume=1.7,adelay=600|600[b1];sine=f=52:d=0.16,afade=t=out:st=0.04:d=0.12,volume=1.3,adelay=900|900[b2];"
          "[dr][b1][b2]amix=inputs=3:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo[a]")
    run(["-filter_complex", fc, "-map", "[a]", "-t", "3.5", path])


def master(patched, out, tmp):
    bed = os.path.join(tmp, "hook.wav"); hook_bed(bed)
    vd = dur(patched)
    ad = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=duration", "-of", "csv=p=0", patched]))
    B = bounds()
    vins, vfc, vlabs, phone = voice_layers(B, vd, tmp)
    nv = len(vins) // 2
    sfx_in, sfx_fc, labs = [], [], ""
    for k, (p, sid, off, pk) in enumerate([x for x in sfx_list() if os.path.exists(x[0])]):
        ms = max(int((B[sid][0] + off) * 1000), 0); j = 2 + nv + k
        sfx_in += ["-i", p]
        sfx_fc.append(f"[{j}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={pk - peak_db(p):.2f}dB,adelay={ms}|{ms},apad=whole_dur={vd:.3f}[x{k}]")
        labs += f"[x{k}]"; print(f"효과음 {os.path.basename(p)} @ {sid} → 피크 {pk} dBFS")
    for k2, (p, t0, t1, pk) in enumerate(clock_list()):
        j = 2 + nv + len(sfx_in) // 2; ms = int(t0 * 1000); d_ = t1 - t0
        sfx_in += ["-i", p]
        sfx_fc.append(f"[{j}:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{d_:.3f},afade=t=in:d=0.15,afade=t=out:st={max(d_ - 0.3, 0):.3f}:d=0.3,"
                      f"volume={pk - peak_db(p):.2f}dB,adelay={ms}|{ms},apad=whole_dur={vd:.3f}[c{k2}]")
        labs += f"[c{k2}]"; print(f"시계 {os.path.basename(p)} {t0:.2f}~{t1:.2f}s → 피크 {pk} dBFS")
    # 어머니 LINE 음성 구간: 원본 믹스의 마른 목소리를 내리고(BGM 0 구간, 방 공기음은 룸톤이 채움) 휴대폰 처리본으로
    duck = "".join(f",volume=enable='between(t,{a - 0.05:.3f},{b + 0.15:.3f})':volume=0.12" for a, b in phone)
    # 정적 구간 베드(최우선 원칙 6①): BGM 0인 구간의 효과음 사이가 −36~−42 dBFS로 비어 인공적 적막 → 방 공기음 + 아주 낮은 서브 드론으로 −30~−32에 맞춤
    win = [(w["start"], w["end"]) for w in AUDIO["bgm_silence"]]
    en = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in win)
    sfx_fc.append(f"anoisesrc=d={vd:.3f}:c=brown:a=1,lowpass=f=380,volume=-20dB,aformat=sample_rates=44100:channel_layouts=stereo,"
                  f"volume=volume='{en}':eval=frame[tb1]"); labs += "[tb1]"
    sfx_fc.append(f"sine=f=46:d={vd:.3f},volume=-27dB,aformat=sample_rates=44100:channel_layouts=stereo,volume=volume='{en}':eval=frame[tb2]"); labs += "[tb2]"
    n = 3 + nv + len(sfx_fc)
    fc = (f"[0:a]afade=t=out:st={max(ad - 2.5, 0):.3f}:d=2.5{duck},apad=whole_dur={vd:.3f}[m];[1:a]apad=whole_dur={vd:.3f}[h];"
          f"anoisesrc=d={vd:.3f}:c=brown:a=1,lowpass=f=250,volume=-40dB,aformat=sample_rates=44100:channel_layouts=stereo[rt];"
          + "".join(x + ";" for x in vfc)
          + "".join(x + ";" for x in sfx_fc) +
          f"[m][h][rt]{vlabs}{labs}amix=inputs={n}:normalize=0:duration=first,loudnorm=I=-14:TP=-2.0:LRA=11,aresample=176400,alimiter=limit=0.84:level=0,aresample=44100[a]")
    script = os.path.join(tmp, "master_fc.txt"); open(script, "w").write(fc)
    run(["-i", patched, "-i", bed] + vins + sfx_in + ["-filter_complex_script", script, "-map", "0:v", "-map", "[a]", "-ar", "44100",
                                                       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])


def outro(main_out, tmp):
    outro = os.path.join(OUTD, f"{SKIT}-outro.mp4")
    meta = json.load(open(os.path.join(OUTD, f"{SKIT}-outro.json")))
    hs = meta["host_start"]
    cta = os.path.join(tmp, "outro-cta.mp4")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/outro_cta_overlay.py"), outro, cta, f"{hs[2] + 1.1:.2f}", f"{hs[2] + 0.35:.2f}", f"{hs[3] - 0.2:.2f}"], check=True)  # 「チャンネル登録(0.35초)と高評価(1.1초)も」
    final = os.path.join(OUTD, f"{SKIT}-final.mp4")
    env = {**os.environ, "OUTRO": cta, "ENDCARD": os.path.join(ROOT, "assets/brand/endcard-midam-ja-v2.mp4"), "OUT_SIZE": "1920x1080"}
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/append_outro.py"), main_out, final], check=True, env=env)
    print(f"완성: {final} ({dur(final):.1f}초) / 본편 {dur(main_out):.1f}초")


def main():
    src = sys.argv[1]
    only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
    tmp = os.path.join(OUTD, "fin-aihaha"); os.makedirs(tmp, exist_ok=True)
    if "--patches-only" in sys.argv:
        B = bounds()
        for sid in (only or targets()):
            a, b = B[sid]; print(sid, build_cut(sid, b - a, tmp))
        return
    patched = os.path.join(tmp, "patched.mp4")
    if "--remaster" in sys.argv:  # 영상 패치는 그대로, 오디오만 새 remix(src)로 바꿔 끼워 다시 마스터링(정적 구간 등 오디오 수정 — 무료)
        p2 = os.path.join(tmp, "patched_remix.mp4")
        run(["-i", patched, "-i", src, "-map", "0:v", "-map", "1:a", "-c", "copy", p2]); patched = p2  # -shortest 금지(remix 오디오가 짧으면 본편이 잘림 — 실측 3.5초)
    else:
        done = patch(src, patched, tmp, only)
        print("패치 컷", len(done), done)
    main_out = os.path.join(tmp, "main.mp4"); master(patched, main_out, tmp)
    print("본편 마무리:", main_out, round(dur(main_out), 2))
    if "--no-outro" not in sys.argv:
        outro(main_out, tmp)


if __name__ == "__main__":
    main()
