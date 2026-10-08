#!/usr/bin/env python3
"""완성 본편에서 한 컷만 교체(무과금, 로컬) — 재조립(burn) 없이 수정 요청을 반영한다.

교체 클립(assets/video-overrides/<skit>/sceneNN.mp4)의 앞부분을 컷 구간 [t0, t1]에 덮고, 그 구간에 걸친 자막(subs/<skit>.ass)만
같은 스타일로 다시 입힌다. 오디오는 그대로 복사. 컷 경계는 하드컷이어야 한다(디졸브 경계면 중단).
구간은 조립 검수 report.txt(qa_assembly.py)의 장면 경계를 쓴다.
사용법: patch_final_cut.py <skit> "<장면ID> [장면ID ...]" <in.mp4> <out.mp4> <report.txt>
여러 컷은 한 번의 인코딩으로 교체한다(컷마다 전체를 다시 인코딩하면 화질이 누적 열화 — 2026-10-08 10컷 교체에서 확인).
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def ts(s):
    h, m, x = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(x)


def tc(s):
    s = max(0.0, s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def prepare(skit, sid, out, report):
    sb = json.load(open(os.path.join(ROOT, "scripts", "storyboard", f"{skit}.json"), encoding="utf-8"))["scenes"]
    au = json.load(open(os.path.join(ROOT, "scripts", "audio", f"{skit}.json"), encoding="utf-8"))
    idx = next(i for i, s in enumerate(sb, start=1) if s["id"] == sid)
    tr = au.get("transitions", [])
    if (idx >= 2 and tr[idx - 2] > 0.05) or (idx <= len(tr) and tr[idx - 1] > 0.05):
        sys.exit(f"{sid}: 디졸브 경계 — 이 도구로 교체 불가(burn 재조립 필요)")
    m = re.search(rf"^{re.escape(sid)}:\s+([0-9.]+) ~\s+([0-9.]+)s", open(report, encoding="utf-8").read(), re.M)
    t0, t1 = float(m.group(1)), float(m.group(2))
    t0 += 0.02; t1 -= 0.02   # 앞뒤 컷과 겹치는 1프레임은 원본 유지
    clip = os.path.join(ROOT, "assets", "video-overrides", skit, f"scene{idx:02d}.mp4")
    work = out + ".work"; os.makedirs(work, exist_ok=True)
    # 구간에 걸친 자막만, 구간 시작 기준으로 옮긴 ASS
    lines = open(os.path.join(ROOT, "subs", f"{skit}.ass"), encoding="utf-8").read().splitlines()
    head = [l for l in lines if not l.startswith("Dialogue:")]
    ev = []
    for l in lines:
        if not l.startswith("Dialogue:"):
            continue
        p = l.split(",", 9); a, b = ts(p[1]), ts(p[2])
        if b > t0 and a < t1:
            p[1], p[2] = tc(a - t0), tc(b - t0); ev.append(",".join(p))
    ass = os.path.join(work, "patch.ass"); open(ass, "w", encoding="utf-8").write("\n".join(head + ev) + "\n")
    patch = os.path.join(work, "patch.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-t", f"{t1 - t0:.3f}", "-vf",
                    f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,format=yuv420p,ass={ass}",
                    "-an", "-c:v", "libx264", "-crf", "16", patch], check=True)
    print(f"{sid}(scene{idx:02d}) {t0:.2f}~{t1:.2f}s 교체, 자막 {len(ev)}줄 재입힘")
    return t0, t1, patch


def main():
    skit, sids, src, out, report = sys.argv[1:6]
    segs = [prepare(skit, sid, out + "." + sid, report) for sid in sids.split()]
    ins, fc, cur = ["-i", src], [], "[0:v]"
    for k, (t0, t1, patch) in enumerate(segs):
        ins += ["-i", patch]
        fc.append(f"[{k + 1}:v]setpts=PTS+{t0:.3f}/TB[p{k}];{cur}[p{k}]overlay=0:0:enable='between(t,{t0:.3f},{t1:.3f})':eof_action=pass[o{k}]")
        cur = f"[o{k}]"
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc) + f";{cur}format=yuv420p[v]",
                    "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
    print(f"저장: {out} — {len(segs)}컷 한 번에 교체")


if __name__ == "__main__":
    main()
