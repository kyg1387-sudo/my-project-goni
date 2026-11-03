#!/usr/bin/env python3
"""3D 아바타 시험 쇼츠(쇼츠 ③ 「引きこもりが契約の場に現れた」 같은 구간·같은 소리) — 고니감독님 제안 2026-10-31.
본편 main.mp4의 오디오(대사·BGM·효과음)를 그대로 쓰고 화면만 아바타 컷으로 바꾼 뒤 make_shorts.py로 세로 쇼츠를 만든다(실사판과 화풍만 다른 A/B).
컷: 립싱크 5(assets/auditions/hikikomori-avatar-omni/omni-<컷>.mp4), 나머지 11 = 아바타 키프레임 정지 + 편집 카메라.
사용법: python3 scripts/make_avatar_short_hikikomori.py
"""
import json, os, subprocess, sys
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finalize_hikikomori as f  # noqa: E402
import build_hikikomori_overrides as ov  # noqa: E402

ROOT = f.ROOT
KF = os.path.join(ROOT, "assets/portraits/hikikomori-avatar-final")
OMNI = os.path.join(ROOT, "assets/auditions/hikikomori-avatar-omni")
T0, T1 = 430.0, 500.0  # 작업 구간(쇼츠 ③ 439.8~493.8 포함)
CAM = {"S18c": "push", "S18e": "handheld", "S18f": "push", "S19b": "push", "S19c": "pull", "S19d": "push", "S19e": "push",
       "S19g": "handheld", "S20a": "push", "S20b": "pull", "S20c": "push"}
OMNIS = ["S18d", "S18g", "S19a", "S19f", "S20d"]
TMP = os.path.join(ROOT, "out", "avatar-short"); os.makedirs(TMP, exist_ok=True)


def main():
    ov.W, ov.H = 1920, 1080
    B = f.bounds(); segs = []
    for cid in list(CAM) + OMNIS:
        a, b = B[cid]
        if cid in OMNIS:
            src = os.path.join(OMNI, f"omni-{cid}.mp4"); clip = os.path.join(TMP, f"{cid}.mp4")
            alt = os.path.join(ROOT, "assets/auditions/hikikomori-avatar-omni2", f"omni-{cid}.mp4")  # 재생성분 우선(S18d 고개 90° 돌림)
            if os.path.exists(alt):
                src = alt
            f.run(["-i", src, "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,tpad=stop_mode=clone:stop_duration=2",
                   "-t", f"{b - a + 0.1:.3f}", "-an", "-c:v", "libx264", "-crf", "16", clip])
        else:
            clip = os.path.join(TMP, f"{cid}.mp4"); ov.cam(os.path.join(KF, f"{cid}.png"), clip, b - a + 0.1, CAM[cid])
        segs.append((a - T0, b - T0 - 1 / 24, clip))
    base = os.path.join(TMP, "base.mp4")
    f.run(["-ss", f"{T0}", "-to", f"{T1}", "-i", os.path.join(ROOT, "out/fin-hik/main.mp4"), "-c:v", "libx264", "-crf", "16", "-c:a", "aac", "-b:a", "192k", base])
    inputs, fc, last = ["-i", base], [], "[0:v]"
    for k, (a, b, c) in enumerate(segs, start=1):
        inputs += ["-i", c]
        fc.append(f"[{k}:v]setpts=PTS-STARTPTS+{a:.3f}/TB[p{k}]")
        fc.append(f"{last}[p{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{k}]"); last = f"[o{k}]"
    fc.append(f"{last}eq=contrast=1.03,noise=alls=2:allf=t+u,format=yuv420p[v]")
    seg = os.path.join(TMP, "avatar-seg.mp4")
    f.run(inputs + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "17", "-c:a", "copy", seg])
    # 자막(.ass)을 작업 구간 기준으로 당긴 사본 + 쇼츠 스펙(시작·끝도 T0 기준)
    def sh(t):
        h, m, s = t.split(":"); v = max(0.0, int(h) * 3600 + int(m) * 60 + float(s) - T0)
        return f"{int(v // 3600)}:{int(v % 3600 // 60):02d}:{v % 60:05.2f}"
    ass = os.path.join(TMP, "sub.ass"); out = []
    for l in open(os.path.join(ROOT, "subs/hikikomori.ass"), encoding="utf-8"):
        if l.startswith("Dialogue:"):
            p = l.split(",", 9); p[1], p[2] = sh(p[1]), sh(p[2]); l = ",".join(p)
        out.append(l)
    open(ass, "w", encoding="utf-8").write("".join(out))
    spec = json.load(open(os.path.join(ROOT, "productions/hikikomori-ja/shorts.json"), encoding="utf-8"))
    s3 = dict(next(x for x in spec["shorts"] if x["id"] == "3-touchaku")); s3["id"] = "3-touchaku-avatar"
    s3["start"] = round(s3["start"] - T0, 3); s3["end"] = round(s3["end"] - T0, 3)
    sp = os.path.join(TMP, "spec.json"); json.dump({"prefix": "hikikomori", "shorts": [s3]}, open(sp, "w"), ensure_ascii=False)
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts/make_shorts.py"), seg, ass, sp, os.path.join(ROOT, "assets/shorts/hikikomori")], check=True)


if __name__ == "__main__":
    main()
