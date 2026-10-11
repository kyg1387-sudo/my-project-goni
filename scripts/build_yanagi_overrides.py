#!/usr/bin/env python3
"""『柳の葉と一杯の水』 무료 교체 클립(video-overrides) 생성 — 규격 제7장 2, 제8장 6 (로컬, 무과금).

스토리보드의 방식별로 assets/video-overrides/yanagi/sceneNN.mp4 를 만든다(NN = 장면 순번, 1부터).
  still  정지 키프레임 → 편집 카메라(기본 슬로 푸시인 1.00→1.05 / pull / pan / tilt / jib / dutch7 / rack=푸시인)
  omni   대사 CU 정지 프레임(움직임 없음) — 조립 단계에서 OmniHuman이 음성 구동 영상으로 바꾼다
  card   타이틀 카드 『柳の葉と一杯の水』(실글꼴, 페이드)
  reuse  원본 컷이 정지(still)면 바로 만들고, i2v·OMNI 원본이면 임시로 키프레임 정지 클립을 넣고 목록에 남긴다
         (생성 후 replace_reuse 로 실제 클립에서 잘라 교체 — 무과금)
키프레임은 assets/portraits/yanagi-keyframes/(합성 완료본). 해상도 1280x720 24fps(concat 규격).
사용법: python3 scripts/build_yanagi_overrides.py            # 전부
        python3 scripts/build_yanagi_overrides.py replace_reuse <clips_dir>   # 생성 클립에서 재사용 컷 교체
"""
import json
import math
import os
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = os.path.join(ROOT, "scripts", "storyboard", "yanagi.json")
KF = os.path.join(ROOT, "assets", "portraits", "yanagi-keyframes")
OUT = os.path.join(ROOT, "assets", "video-overrides", "yanagi")
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1280, 720, 24
TITLE = "柳の葉と一杯の水"
MINCHO = os.path.join(ROOT, "scripts", "fonts", "ZenOldMincho-Regular.ttf")


def run(args):
    subprocess.run([FF, "-v", "error", "-y"] + args, check=True)


def cam(src, out, sec, fx):
    """편집 카메라 — 4배 업스케일 위 zoompan(서브픽셀, 떨림 방지). 한 컷 한 무빙(제8장 6)."""
    n = max(1, int(math.ceil(sec * FPS)))
    t = f"(on/{n})"
    z, x, y = "1.0", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if fx in ("", "push", "rack"):
        z = f"1+0.05*{t}"
    elif fx == "pull":
        z = f"1.06-0.06*{t}"
    elif fx == "pan":
        z = "1.08"; x = f"(iw-iw/zoom)*(0.15+0.7*{t})"
    elif fx == "tilt":
        z = "1.08"; y = f"(ih-ih/zoom)*(0.15+0.7*{t})"
    elif fx == "jib":
        z = "1.08"; y = f"(ih-ih/zoom)*(0.85-0.7*{t})"
    elif fx == "static":
        z = "1.0"
    vf = f"scale={W * 4}:{H * 4},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS}"
    if fx.startswith("dutch"):
        deg = float(fx[5:] or 5)
        vf += f",rotate={deg}*PI/180:ow={W}:oh={H}:c=black,scale={int(W * 1.25)}:{int(H * 1.25)},crop={W}:{H}"
    vf += ",format=yuv420p"
    run(["-loop", "1", "-i", src, "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-an", out])


def card(out, sec):
    im = Image.new("RGB", (W, H), "black"); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(MINCHO, 76); w = d.textlength(f"『{TITLE}』", font=f)
    d.text(((W - w) / 2, H / 2 - 50), f"『{TITLE}』", font=f, fill=(236, 230, 214))
    p = os.path.join(OUT, "_title.png"); im.save(p)
    n = int(round(sec * FPS))
    run(["-loop", "1", "-i", p, "-vf", f"fade=in:0:18,fade=out:{n - 18}:18,format=yuv420p", "-frames:v", str(n), "-r", str(FPS),
         "-c:v", "libx264", "-crf", "18", "-an", out])
    os.remove(p)


def main():
    sb = json.load(open(SB, encoding="utf-8"))["scenes"]
    ids = {s["id"]: i + 1 for i, s in enumerate(sb)}
    os.makedirs(OUT, exist_ok=True)
    pending, made = [], 0
    for i, s in enumerate(sb, start=1):
        out = os.path.join(OUT, f"scene{i:02d}.mp4")
        sec = s["assembled_s"] + 0.5
        tier = s["tier"]
        if tier in ("pro", "lite"):
            continue
        if tier == "card":
            card(out, s["assembled_s"]); made += 1; continue
        src_id = s["kind"].split(":", 1)[1] if tier == "reuse" else s["id"]
        src = os.path.join(KF, f"{src_id}-1.png")
        if not os.path.exists(src):
            print(f"scene{i:02d} {s['id']}: 키프레임 없음 {src_id}"); continue
        if tier == "reuse":
            src_tier = sb[ids[src_id] - 1]["tier"]
            if src_tier != "still":
                pending.append((i, s["id"], src_id))
            cam(src, out, sec, "push" if src_tier == "still" else "static")
        elif tier == "omni":
            cam(src, out, sec, "static")
        else:
            cam(src, out, sec, s["edit_fx"].split("+")[0])
        made += 1
    json.dump(pending, open(os.path.join(OUT, "_reuse_pending.json"), "w"), ensure_ascii=False)
    print(f"교체 클립 {made}개 → {OUT}\n생성 후 교체할 재사용 컷: {pending}")


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
        run(["-i", src, "-t", f"{sb[i - 1]['assembled_s'] + 0.5:.3f}", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p",
             "-c:v", "libx264", "-crf", "18", "-an", out])
        print(f"scene{i:02d} {sid} ← {src_id} 실제 클립")
    json.dump(left, open(os.path.join(OUT, "_reuse_pending.json"), "w"), ensure_ascii=False)
    print("남은 재사용 컷:", left)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "replace_reuse":
        replace_reuse(sys.argv[2])
    else:
        main()
