#!/usr/bin/env python3
"""여운 줄의 「……」 정적 늘리기(무료, 로컬) — 발성 디렉션 3-2(복선·여운 구간 0.5~0.8초 정적) 적용.

Typecast는 「……」를 평균 0.37초(최소 0.15초) 정적으로 만든다(2026-10-29 실측 43줄). 지정한 여운 줄만
발화 안쪽의 0.2초 넘는 정적을 TARGET초(최대 MAX초)로 늘린다. 긴장 줄(亮介·真壁·고함)은 손대지 않는다.
원본은 assets/auditions/hikikomori-tts/_v1/<id>-orig.mp3 로 보관(이미 있으면 그 원본에서 다시 만든다 = 반복 실행 안전).
사용법: python3 productions/hikikomori-ja/pace_pauses.py [--dry]
"""
import json, os, shutil, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUD = os.path.join(REPO, "assets", "auditions", "hikikomori-tts")
SR, TARGET, MAX, MIN_GAP = 44100, 0.6, 0.8, 0.2  # 0.2 미만은 촉음(っ)·파열음 폐쇄일 수 있어 제외
# 복선·여운·감정 정점 줄(대본 태그). 긴장 구간(S12 亮介, S17~S20 真壁, 고함 L01·L08·L09·L29)은 제외 — 끊어 치는 리듬 유지
PACE = ["L02", "L11", "NA12", "L22", "L23", "L26", "L36", "L39", "L39a", "L40", "L45", "L52", "L58", "L59", "L61", "NA23"]


def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def gaps(x):
    env = np.convolve(np.abs(x), np.ones(441) / 441, "same")
    on = env > 0.01
    idx = np.where(on)[0]
    a, b = idx[0], idx[-1]
    out, i = [], a
    while i < b:
        if not on[i]:
            j = i
            while j < b and not on[j]:
                j += 1
            if (j - i) / SR > MIN_GAP:
                out.append((i, j))
            i = j
        else:
            i += 1
    return out


def main():
    dry = "--dry" in sys.argv
    tags = [l.split("|")[2].strip() for l in open(os.path.join(HERE, "05_톤연출표.md"), encoding="utf-8") if l.startswith("| line")]
    ids = [l.split("|")[1].strip() for l in open(os.path.join(HERE, "05_톤연출표.md"), encoding="utf-8") if l.startswith("| line")]
    tag2id = dict(zip(tags, ids))
    os.makedirs(os.path.join(AUD, "_v1"), exist_ok=True)
    total_add = 0.0
    for tag in PACE:
        fid = tag2id[tag]
        cur = os.path.join(AUD, fid + ".mp3")
        orig = os.path.join(AUD, "_v1", fid + "-orig.mp3")
        src = orig if os.path.exists(orig) else cur
        x = load(src)
        g = gaps(x)
        parts, last, add = [], 0, 0.0
        for i, j in g:
            d = (j - i) / SR
            want = min(MAX, max(d, TARGET))
            mid = (i + j) // 2
            parts += [x[last:mid], np.zeros(int((want - d) * SR), np.float32)]
            last = mid
            add += want - d
        parts.append(x[last:])
        total_add += add
        print(f"{fid} {tag}: 정적 {[round((j - i) / SR, 2) for i, j in g]} → +{add:.2f}초")
        if dry or add < 0.01:
            continue
        if not os.path.exists(orig):
            shutil.copy(cur, orig)
        y = np.concatenate(parts)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-c:a", "libmp3lame", "-b:a", "192k", cur], input=y.tobytes(), check=True)
    print(f"합계 +{total_add:.1f}초 ({len(PACE)}줄)")


if __name__ == "__main__":
    main()
