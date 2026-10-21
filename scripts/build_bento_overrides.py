#!/usr/bin/env python3
"""『閉店間際の弁当屋』 무료 교체 클립(video-overrides) 생성 — 규격 제7장 2, 제8장 6 (로컬, 무과금).
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
SB = os.path.join(ROOT, "scripts", "storyboard", "bento.json")
KF = os.path.join(ROOT, "assets", "portraits", "bento-keyframes")
OUT = os.path.join(ROOT, "assets", "video-overrides", "bento")
FF = shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()
W, H, FPS = 1280, 720, 24
# i2v 검수 불합격 → 무료 정지 푸시인 폴백(비립싱크 화자 등). 이 작품은 비립싱크 화자 컷 0 — 검수 후 필요 시 추가
# i2v 1초 시트 검수(2026-10-21) 불합격 → 무료 정지 푸시인 폴백(제11장 9·제18장 6):
# S07b 지붕 연기, S07c 열차가 화면을 가로지름, S08f 화면 밖 어른 얼굴 등장, S10bd 듣는 사람 입이 계속 움직임, S11a 정장 남자 등장,
# S11b 봉투가 늘어남, S12g 편지가 두꺼운 책으로 변함, S12k 우는 얼굴이 미소로(눈물 장면 반전), S12r 편지 가짜 글자 선명, S14a 문 안 인물, S14e 뒤돌아 뒤통수
I2V_FALLBACK = {"S07b", "S07c", "S08f", "S10bd", "S11a", "S11b", "S12g", "S12k", "S12r", "S14a", "S14e"}


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


# 핵심 소품·글자로 다가가는 푸시인(제8장 4-2, 휴대폰 가독성)
CAM_OVERRIDE = {"H1": "pushto:0.62:0.78:1.18", "S06a": "pushto:0.26:0.17:1.35", "S05a": "pushto:0.16:0.58:1.45",
                "S12o": "pushto:0.80:0.86:1.6", "S15a": "pushto:0.51:0.45:1.3", "S13b": "pushto:0.83:0.40:1.2"}
CARD_SRC = {"S12q": "S12a"}  # 질문 카드 배경(정지 프레임 블러) — 검은 화면 금지(제15장 20)


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


def main(only=None):
    sb = json.load(open(SB, encoding="utf-8"))["scenes"]
    ids = {s["id"]: i + 1 for i, s in enumerate(sb)}
    os.makedirs(OUT, exist_ok=True)
    pending, made, miss = [], 0, []
    for i, s in enumerate(sb, start=1):
        out = os.path.join(OUT, f"scene{i:02d}.mp4")
        sec = s["assembled_s"] + 0.5
        tier = s["tier"]
        if (tier in ("pro", "lite") and s["id"] not in I2V_FALLBACK) or (only and s["id"] not in only):
            continue
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
