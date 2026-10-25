#!/usr/bin/env python3
"""『時給5万円の罠』 무료 교체 클립(video-overrides) 생성 — build_bento_overrides.py를 옮긴 것 — 규격 제7장 2, 제8장 6 (로컬, 무과금).
build_yanagi_overrides.py 구조. 스토리보드 방식별로 assets/video-overrides/bento/sceneNN.mp4(NN = 장면 순번, 1부터).
  still  정지 키프레임 → 편집 카메라(기본 슬로 푸시인 1.00→1.05 / pullback / dutch7 / bw(흑백) / dollyzoom 근사)
  omni   대사 CU 정지 프레임(움직임 없음) — 조립 단계에서 OmniHuman이 음성 구동 영상으로 바꾼다
  card   검은 화면(제목·자막 글자는 클립에 직접 그린다(.ass Caption 없음, 제15장 12))
  reuse  원본이 정지면 바로 만들고, i2v·OMNI 원본이면 임시 정지 클립 + 목록(생성 후 replace_reuse로 실제 클립에서 잘라 교체)
i2v 컷(pro·lite)의 편집 효과(craneup·handheld·dutch5)는 조립 후 마무리 단계에서 입힌다.
키프레임은 assets/portraits/bento-keyframes/(kf_pick.py + bento_ja_overlay.py). 1280x720 24fps(concat 규격).
사용법: python3 scripts/build_bento_overrides.py            # 전부
        python3 scripts/build_bento_overrides.py replace_reuse <clips_dir>
        python3 scripts/build_bento_overrides.py only S05c,S09c      # 키프레임 교체한 컷만 다시
"""
import json
import math
import os
import shutil
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = os.path.join(ROOT, "scripts", "storyboard", "yamibaito.json")
KF = os.path.join(ROOT, "assets", "portraits", "yamibaito-keyframes")
OUT = os.path.join(ROOT, "assets", "video-overrides", "yamibaito")
FF = shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()
W, H, FPS = 1280, 720, 24
# i2v 검수 불합격 → 무료 정지 푸시인 폴백(비립싱크 화자 등). 이 작품은 비립싱크 화자 컷 0 — 검수 후 필요 시 추가
# i2v 1초 시트 검수(2026-10-21) 불합격 → 무료 정지 푸시인 폴백(제11장 9·제18장 6):
# S07b 지붕 연기, S07c 열차가 화면을 가로지름, S08f 화면 밖 어른 얼굴 등장, S10bd 듣는 사람 입이 계속 움직임, S11a 정장 남자 등장,
# S11b 봉투가 늘어남, S12g 편지가 두꺼운 책으로 변함, S12k 우는 얼굴이 미소로(눈물 장면 반전), S12r 편지 가짜 글자 선명, S14a 문 안 인물, S14e 뒤돌아 뒤통수
# 2차 검수(2026-10-21): S11c 봉투가 두 장으로 늘어남, S13k 놓은 손이 다시 와서 옮김, S10be 칼질(깎기) 동작이 어설픔 → 정지 푸시인
# S03bb 동생 모자에 방울이 생겨남, S10bf 정면 응시로 시작(키프레임을 i2v 마지막 프레임 = 진열장을 보는 옆얼굴로 교체)
# S05b 지갑이 손가락 하나에 매달리고 동전이 저절로 떨어짐(2차 지적) → r16 손 편집 키프레임 + 정지 푸시인
# S08g 끝 2.5초부터 비닐봉투가 천 보따리로 변함(3차 점검)
I2V_FALLBACK = {"H4", "S02k", "S02bg", "S02bi", "S03e", "S04f", "S07m", "S06o", "S08f", "S08n"}  # i2v 1초 시트 검수 불합격(2026-10-25) → 무료 정지 푸시인 폴백(제11장 9·제18장 6): H4 보케가 글자 간판으로 선명해짐, S02k·S02bi 폰 화면 합성 글자 변형, S02bg 방 조명이 켜짐, S03e 폰을 들어 화면이 백지, S04f 안대를 내리지 않고 벗음, S07m 시계가 발광하며 바늘 이동, S06o 무지 통장 더미에 가짜 인쇄 카드가 생성됨


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


# 핵심 소품·글자로 다가가는 푸시인(제8장 4-2, 휴대폰 가독성)
CAM_OVERRIDE = {"S09b": "pushto:0.42:0.72:1.9", "S07a": "pushto:0.55:0.55:1.25", "S02h": "pushto:0.62:0.86:1.5", "S02i": "pushto:0.54:0.56:1.6", "S10m": "push"}  # 키패드·봉투 글자로 푸시인(제8장 4-2)
CARD_SRC = {"H3": "H2b", "S11m": "S11l"}
CARD_SUB = {"H3": "この物語は、実際の手口をもとにした再現ドラマ（フィクション）です"}  # 질문 카드 배경(정지 프레임 블러) — 검은 화면 금지(제15장 20)


def cam(src, out, sec, fx):
    """편집 카메라 — 4배 업스케일 위 zoompan(서브픽셀, 떨림 방지). 한 컷 한 무빙(제8장 6)."""
    n = max(1, int(math.ceil(sec * FPS)))
    t = f"(on/{n})"
    z, x, y = "1.0", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    moves = [m for m in fx.split(",") if m and m != "bw"]
    mv = moves[0] if moves else "push"
    if mv in ("push", "pushin", "rack"):
        z = f"1+0.05*{t}"
    elif mv in ("pull", "pullback"):
        z = f"1.06-0.06*{t}"
    elif mv == "dollyzoom":  # 인물 마스크 없는 근사: 1.6초 안에 빠른 줌인 후 유지(정체 발각 1회, 제8장 4)
        k = int(1.6 * FPS)
        z = f"if(lt(on,{k}),1+0.14*on/{k},1.14)"
    elif mv == "static":
        z = "1.0"
    elif mv.startswith("pushto"):  # pushto:cx:cy:zmax — 핵심 소품(메뉴 마지막 줄)으로 다가가는 푸시인(제8장 4-2, 휴대폰 가독성)
        _, cx, cy, zm = mv.split(":")
        z = f"1+{float(zm) - 1:.3f}*{t}"
        x = f"min(max(iw*{cx}-iw/zoom/2,0),iw-iw/zoom)"
        y = f"min(max(ih*{cy}-ih/zoom/2,0),ih-ih/zoom)"
    vf = f"scale={W * 4}:{H * 4},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS}"
    if mv.startswith("dutch"):
        deg = float(mv[5:] or 5)
        vf = (f"scale={W * 4}:{H * 4},zoompan=z='1+0.03*{t}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},"
              f"rotate={deg}*PI/180:ow={W}:oh={H}:c=black,scale={int(W * 1.25)}:{int(H * 1.25)},crop={W}:{H}")
    if "bw" in fx.split(","):
        vf += ",hue=s=0"
    vf += ",format=yuv420p"
    run(["-loop", "1", "-i", src, "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-an", out])


def black(out, sec):
    n = int(round(sec * FPS))
    # 순수 검정은 20KB 미만이 되어 generate_video.py가 깨진 파일로 봄(MIN_CLIP_BYTES) → 아주 옅은 필름 그레인을 얹는다
    run(["-f", "lavfi", "-i", f"color=c=0x060606:s={W}x{H}:r={FPS}", "-vf", "noise=alls=8:allf=t,format=yuv420p",
         "-frames:v", str(n), "-c:v", "libx264", "-crf", "26", "-an", out])


def card(sid, text, out, sec):
    """질문 카드: 배경 키프레임 블러 + 어둡게 + 가운데 명조 흰 글자(그림자), 느린 푸시인. 글자는 클립에 직접(제15장 12)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    bg = Image.open(os.path.join(KF, f"{CARD_SRC[sid]}-1.png")).convert("RGB").resize((W * 2, H * 2)).filter(ImageFilter.GaussianBlur(18))
    bg = Image.eval(bg, lambda v: int(v * 0.55))
    d = ImageDraw.Draw(bg)
    f = ImageFont.truetype(os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Bold.ttf"), 92)
    sub = CARD_SUB.get(sid)
    if sub:  # 하단 소자막(픽션 고지)
        fs = ImageFont.truetype(os.path.join(ROOT, "scripts", "fonts", "ZenKakuGothicNew-Regular.ttf"), 40)
        sw = d.textlength(sub, font=fs); d.text(((W * 2 - sw) / 2 + 3, H * 2 - 150 + 3), sub, font=fs, fill=(0, 0, 0)); d.text(((W * 2 - sw) / 2, H * 2 - 150), sub, font=fs, fill=(215, 215, 215))
    dash = text.endswith("――"); body = text.rstrip("―")  # 명조 글꼴에 「―」 글리프가 없어 빈칸 → 선으로 그린다
    dw = 2 * f.size if dash else 0
    w = d.textlength(body, font=f) + dw; x, y = (W * 2 - w) / 2, H - 60
    for dx, dy, col in ((4, 4, (0, 0, 0)), (0, 0, (250, 246, 236))):
        d.text((x + dx, y + dy), body, font=f, fill=col)
        if dash:
            lx = x + dx + d.textlength(body, font=f) + 8; ly = y + dy + f.size * 0.62
            d.line((lx, ly, lx + dw - 16, ly), fill=col, width=6)
    tmp = os.path.join(OUT, f"_card_{sid}.png"); bg.save(tmp)
    cam(tmp, out, sec, "push")


TEAR_SPOT = {}  # 2차 검수(2026-10-21): i2v가 종이에 젤 같은 큰 물 덩어리를 흘림 → 정지 푸시인 + 작은 눈물 자국 한 방울(키프레임 2560 좌표·반지름·시각)


def tear_spot(src, out, sec, spec):
    """편지 종이에 눈물 한 방울이 떨어져 번지는 자국(실감: 지름 1cm 남짓, 젖은 종이가 살짝 어둡고 가장자리가 조금 더 진함)."""
    import numpy as np
    from PIL import Image
    cx, cy, r, t0 = spec
    base = np.asarray(Image.open(src).convert("RGB").resize((2560, 1440), Image.LANCZOS)).astype(np.float32)
    yy, xx = np.mgrid[0:1440, 0:2560]
    dist = np.hypot((xx - cx) * 1.0, (yy - cy) * 1.15)  # 기울어진 종이 → 살짝 타원
    n = int(round(sec * FPS))
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for k in range(n):
        t = k / FPS
        img = base
        g = min(max((t - t0) / 0.35, 0.0), 1.0)
        if g > 0:
            rr = r * (0.35 + 0.65 * g)
            inside = np.clip((rr - dist) / 2.5, 0, 1)
            rim = np.exp(-((dist - rr) / 2.2) ** 2) * (dist < rr + 4)
            dark = 1 - (0.09 * inside + 0.08 * rim) * g
            img = base * dark[..., None]
            img[..., 2] *= 1 + 0.015 * inside * g  # 젖은 종이의 아주 옅은 회청색
        z = 1 + 0.06 * t / sec  # 느린 푸시인(편집 카메라)
        cw, ch = 2560 / z, 1440 / z
        x0, y0 = cx - cw * (cx / 2560), cy - ch * (cy / 1440)
        fr = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()


# 2차 검수(2026-10-21 「시간도 정확하게」): 생성 시계는 바늘이 12시(두 바늘 위) — 대본은 「9시를 지난다(S06a)·9시를 가리킨다(S13b)」.
# 같은 시계 판(S13b 키프레임, 바늘 지움)에 바늘을 직접 그리고 초침을 1초마다 째깍(8:59:57 → 9:00 정각 통과). 2026 평면 TV가 보이는 왼쪽은 잘라 1996 장면에도 쓴다.
CLOCK = {}  # 시계는 키프레임에 바늘을 그려 넣음(yamibaito_ja_overlay.py)
CLOCK_PLATE, CLOCK_C, CLOCK_R, CLOCK_SX, CLOCK_CROP = "S13b-1.png", (1696, 620), 500, 0.93, (427, 0, 2560, 1200)


def clock_clip(out, sec, t_start):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    cx, cy = CLOCK_C
    src = os.path.join(KF, "_v1", CLOCK_PLATE) if os.path.exists(os.path.join(KF, "_v1", CLOCK_PLATE)) else os.path.join(KF, CLOCK_PLATE)
    a = cv2_imread(src)
    g = a.mean(axis=2)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    inner = np.hypot((xx - cx) / CLOCK_SX, yy - cy) < CLOCK_R * 0.86
    m = ((g < 150) & inner).astype(np.uint8) * 255
    import cv2
    m = cv2.dilate(m, np.ones((9, 9), np.uint8))
    plate = Image.fromarray(cv2.cvtColor(cv2.inpaint(a, m, 7, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB))
    SS = 2  # 안티에일리어스용 확대
    def hands(t):
        h, mi, se = (t / 3600) % 12, (t / 60) % 60, int(t) % 60
        lay = Image.new("RGBA", (plate.width * SS, plate.height * SS))
        d = ImageDraw.Draw(lay)
        def hand(frac, length, width, color, tail=0):
            th = 2 * np.pi * frac
            dx, dy = np.sin(th) * CLOCK_SX, -np.cos(th)
            p0 = ((cx - dx * tail) * SS, (cy - dy * tail) * SS)
            p1 = ((cx + dx * length) * SS, (cy + dy * length) * SS)
            d.line([p0, p1], fill=color, width=int(width * SS))
        hand(h / 12, CLOCK_R * 0.52, 15, (22, 30, 52, 255), 40)
        hand(mi / 60, CLOCK_R * 0.86, 10, (22, 30, 52, 255), 50)
        hand(se / 60, CLOCK_R * 0.90, 4, (170, 30, 30, 255), 90)
        d.ellipse([(cx - 18) * SS, (cy - 18) * SS, (cx + 18) * SS, (cy + 18) * SS], fill=(40, 40, 46, 255))
        lay = lay.resize(plate.size, Image.LANCZOS)
        sh = Image.new("RGBA", plate.size); sh.paste((0, 0, 0, 90), (0, 0), lay.split()[3]); sh = sh.filter(ImageFilter.GaussianBlur(5))
        img = plate.convert("RGBA"); img.alpha_composite(sh, (8, 10)); img.alpha_composite(lay)
        return img.convert("RGB")
    x0, y0, x1, y1 = CLOCK_CROP
    n = int(round(sec * FPS))
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    cache = {}
    for k in range(n):
        t = t_start + k / FPS
        key = int(t)
        if key not in cache:
            cache = {key: hands(key + 0.0)}  # 초침은 1초마다 째깍(분·시침도 그 초 기준)
        z = 1 + 0.05 * k / n
        w, h = (x1 - x0) / z, (y1 - y0) / z
        ccx, ccy = (x0 + x1) / 2 + (cx - (x0 + x1) / 2) * (1 - 1 / z), (y0 + y1) / 2 + (cy - (y0 + y1) / 2) * (1 - 1 / z)
        fr = cache[key].crop((int(ccx - w / 2), int(ccy - h / 2), int(ccx + w / 2), int(ccy + h / 2))).resize((W, H), Image.LANCZOS)
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()


def cv2_imread(path):
    import cv2
    return cv2.imread(path)


def main(only=None):
    sb = json.load(open(SB, encoding="utf-8"))["scenes"]
    ids = {s["id"]: i + 1 for i, s in enumerate(sb)}
    os.makedirs(OUT, exist_ok=True)
    pending, made, miss = [], 0, []
    for i, s in enumerate(sb, start=1):
        out = os.path.join(OUT, f"scene{i:02d}.mp4")
        sec = s["assembled_s"] + 0.5
        tier = s["tier"]
        if (tier in ("pro", "lite") and s["id"] not in I2V_FALLBACK and s["id"] not in TEAR_SPOT) or (only and s["id"] not in only):
            continue
        if s["id"] in CLOCK:
            clock_clip(out, sec, CLOCK[s["id"]]); made += 1; continue
        if s["id"] in TEAR_SPOT:
            tear_spot(os.path.join(KF, f"{s['id']}-1.png"), out, sec, TEAR_SPOT[s["id"]]); made += 1; continue
        if s["id"] in I2V_FALLBACK:
            cam(os.path.join(KF, f"{s['id']}-1.png"), out, sec, "push"); made += 1; continue
        if tier == "card":
            card(s["id"], s["caption"], out, sec) if s.get("caption") else black(out, sec); made += 1; continue
        src_id = s["kind"].split(":", 1)[1] if tier == "reuse" else s["id"]
        src = os.path.join(KF, f"{src_id}-1.png")
        if not os.path.exists(src):
            miss.append(s["id"]); continue
        if tier == "reuse":
            src_tier = sb[ids[src_id] - 1]["tier"]
            if src_tier != "still":
                pending.append((i, s["id"], src_id))
            cam(src, out, sec, "push" if src_tier == "still" else "static")
        elif tier == "omni":
            cam(src, out, sec, "static")
        else:
            cam(src, out, sec, CAM_OVERRIDE.get(s["id"], s["edit_fx"]))
        made += 1
    if not only:
        json.dump(pending, open(os.path.join(OUT, "_reuse_pending.json"), "w"), ensure_ascii=False)
    print(f"교체 클립 {made}개 → {OUT}\n생성 후 교체할 재사용 컷: {pending}")
    if miss:
        sys.exit(f"키프레임 없음: {miss}")


def replace_reuse(clips):
    """생성된 i2v 클립(sceneNN.mp4 폴더)에서 재사용 컷을 잘라 교체(무과금). OMNI 원본은 조립 후 별도 교체."""
    sb = json.load(open(SB, encoding="utf-8"))["scenes"]
    ids = {s["id"]: i + 1 for i, s in enumerate(sb)}
    pending = json.load(open(os.path.join(OUT, "_reuse_pending.json")))
    left = []
    for i, sid, src_id in pending:
        src = os.path.join(clips, f"scene{ids[src_id]:02d}.mp4")
        if sb[ids[src_id] - 1]["tier"] not in ("pro", "lite") or not os.path.exists(src):
            left.append((i, sid, src_id)); continue
        out = os.path.join(OUT, f"scene{i:02d}.mp4")
        run(["-i", src, "-t", f"{sb[i - 1]['assembled_s'] + 0.5:.3f}", "-vf",
             f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p",
             "-c:v", "libx264", "-crf", "18", "-an", out])
        print(f"scene{i:02d} {sid} ← {src_id} 실제 클립")
    json.dump(left, open(os.path.join(OUT, "_reuse_pending.json"), "w"), ensure_ascii=False)
    print("남은 재사용 컷:", left)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "replace_reuse":
        replace_reuse(sys.argv[2])
    elif len(sys.argv) > 2 and sys.argv[1] == "only":
        main(set(sys.argv[2].split(",")))
    else:
        main()
