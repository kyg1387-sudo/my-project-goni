#!/usr/bin/env python3
"""조립본 전수 검수(CLAUDE.md 제6장 7) — 무과금, 로컬.

출력(out_dir):
  transitions.jpg  모든 장면 경계 앞뒤 0.3초 프레임 쌍(전환·디졸브 확인)
  mouth_SNN.jpg    대사 장면 입 부분 0.25초 간격 크롭(립싱크·치아 뭉개짐)
  scenes_1s.jpg    장면별 중간 프레임 + 1초 간격(인물 대조·재생성 컷)
  report.txt       길이, 장면 경계, −60dB 이하 2초 이상 무음, 1초 창 음량 최저·최고
사용법: qa_assembly.py <final.mp4> <scripts/audio/<skit>.json> <scripts/storyboard/<skit>.json> <out_dir>
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = ImageFont.truetype("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", 18)


def frame(video, t, w=320, crop=None):
    vf = (f"crop={crop}," if crop else "") + f"scale={w}:-2"
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.3f}", "-i", video, "-frames:v", "1",
                          "-vf", vf, "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    from io import BytesIO
    return Image.open(BytesIO(out)).convert("RGB")


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 8 + 10 * len(text), 22], fill=(0, 0, 0))
    d.text((4, 2), text, font=FONT, fill=(255, 255, 0))
    return im


def grid(ims, cols, path):
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    c = Image.new("RGB", (w * cols, h * rows), "white")
    for k, im in enumerate(ims):
        c.paste(im, ((k % cols) * w, (k // cols) * h))
    c.save(path, quality=85)


def main():
    video, audio_cfg, sb_path, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    cfg = json.load(open(audio_cfg, encoding="utf-8"))
    sb = json.load(open(sb_path, encoding="utf-8"))
    ids = [s["id"] for s in sb["scenes"]]
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]))
    d = [float(x) for x in cfg["scene_durations"]]
    ov = [float(x) for x in cfg["transitions"]] + [0.0] * len(d)
    ov = [o if o >= 1 / 24 else 1 / 24 for o in ov][:len(d)]
    ov[-1] = 0
    bounds, t = [], 0.0
    for x, o in zip(d, ov):
        bounds.append((t, t + x)); t += x - o
    rep = [f"영상 길이 {dur:.2f}s (계획 {t:.2f}s)", ""]

    # 전환 시트
    ims = []
    for k in range(1, len(bounds)):
        cut = bounds[k][0]
        kind = f"디졸브{ov[k - 1]:.1f}" if ov[k - 1] > 0.05 else "컷"
        ims.append(label(frame(video, cut - 0.3), f"{ids[k - 1]}→{ids[k]} {kind}"))
        ims.append(label(frame(video, cut + 0.3 + ov[k - 1]), f"{cut:.1f}s 뒤"))
    grid(ims, 8, os.path.join(out, "transitions.jpg"))

    # 대사 입 크롭
    for n in cfg.get("omnihuman_scenes", []):
        t0, t1 = bounds[n - 1]
        ims = [label(frame(video, x, 240, "iw*0.36:ih*0.4:iw*0.32:ih*0.42"), f"{x:.2f}")
               for x in np.arange(t0 + 0.1, t1 - 0.05, 0.25)]
        grid(ims, 10, os.path.join(out, f"mouth_{ids[n - 1]}.jpg"))

    # 장면별 1초 간격
    ims = []
    for k, (t0, t1) in enumerate(bounds):
        for x in np.arange(t0 + 0.2, t1 - 0.1, 1.0)[:8]:
            ims.append(label(frame(video, x, 240), f"{ids[k]} {x:.0f}s"))
    grid(ims, 10, os.path.join(out, "scenes_1s.jpg"))

    # 음량: 0.1초 RMS → −60dB 이하 2초 이상 구간, 1초 창 최저/최고
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    win = 800
    rms = np.sqrt(np.mean(a[:len(a) // win * win].reshape(-1, win) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    silent, start = [], None
    for i, v in enumerate(db):
        if v < -60 and start is None: start = i
        if (v >= -60 or i == len(db) - 1) and start is not None:
            if (i - start) * 0.1 >= 2.0: silent.append((start * 0.1, i * 0.1))
            start = None
    rep.append("−60dB 이하 2초 이상 무음: " + (", ".join(f"{s:.1f}~{e:.1f}s" for s, e in silent) or "없음"))
    sec = db[:len(db) // 10 * 10].reshape(-1, 10).mean(1)
    rep.append(f"1초 창 평균 음량: 최저 {sec.min():.1f}dB({sec.argmin()}s) / 최고 {sec.max():.1f}dB({sec.argmax()}s) / 전체 평균 {sec.mean():.1f}dB")
    low = [f"{i}s({v:.0f})" for i, v in enumerate(sec) if v < -45]
    rep.append("−45dB 미만 1초 창: " + (", ".join(low) or "없음"))
    rep.append("")
    rep += [f"{ids[k]}: {b0:7.2f} ~ {b1:7.2f}s" for k, (b0, b1) in enumerate(bounds)]
    open(os.path.join(out, "report.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    print("\n".join(rep[:6]))


if __name__ == "__main__":
    main()
