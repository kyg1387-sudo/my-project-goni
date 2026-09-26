#!/usr/bin/env python3
"""완성본 오디오를 타임스탬프 포함 Whisper로 전사해 자막(.ass) 타이밍과 대조한다.

각 자막 큐에 대해, 큐 시간창(±여유)과 겹치는 전사 청크에서 원문 한글 글자가
얼마나 등장하는지 계산한다. 제자리 일치율이 낮은데 이웃 시간대에서 발견되면
'밀림'으로 보고한다.

사용법: python3 scripts/qc_sync.py --ass subs/<스킷>.ass --config scripts/audio/<스킷>.json \
            --video out/final.mp4 --report sync-report.txt
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import parse_ass, fal_run, fal_upload  # noqa: E402


def hangul(text):
    return [c for c in text if "가" <= c <= "힣"]


def coverage(expected, text):
    exp = hangul(expected)
    if not exp:
        return 1.0
    pool = set(text)
    return sum(1 for c in exp if c in pool) / len(exp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ass", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--report", default="sync-report.txt")
    args = ap.parse_args()

    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY 필요")

    wav = "qc-mix.mp3"
    subprocess.run(["ffmpeg", "-y", "-i", args.video, "-vn", "-ac", "1",
                    "-b:a", "96k", wav], check=True, capture_output=True)
    url = fal_upload(wav, key)
    result = fal_run("fal-ai/whisper",
                     {"audio_url": url, "task": "transcribe",
                      "language": "ko", "chunk_level": "segment"},
                     key, "sync-qc", timeout_s=1800)
    chunks = (result or {}).get("chunks") or []
    if not chunks:
        sys.exit(f"청크 없음: {json.dumps(result)[:300]}")

    def text_between(t0, t1):
        out = []
        for c in chunks:
            ts = c.get("timestamp") or [None, None]
            s, e = ts[0], ts[1]
            if s is None:
                continue
            if e is None:
                e = s + 5
            if s < t1 and e > t0:
                out.append(c.get("text", ""))
        return " ".join(out)

    cfg = json.load(open(args.config, encoding="utf-8"))
    silent = set(cfg.get("silent_styles", []))
    lines = [l for l in parse_ass(args.ass) if l[2] not in silent]

    rep = []
    bad = []
    for k, (s, e, st, nm, tx) in enumerate(lines):
        here = coverage(tx, text_between(s - 0.7, e + 0.7))
        if here >= 0.55:
            mark, note = "✅", ""
        else:
            # 이웃 시간대 탐색: 어디로 밀렸는지
            best_off, best_cov = 0, here
            for off in (-6, -4, -2, 2, 4, 6, 8, 10):
                c = coverage(tx, text_between(s + off - 0.7, e + off + 0.7))
                if c > best_cov:
                    best_cov, best_off = c, off
            if best_cov >= 0.55 and best_off != 0:
                mark, note = "❌", f"약 {best_off:+d}초 밀림(일치 {best_cov:.2f})"
                bad.append((k + 1, best_off))
            else:
                mark, note = "⚠️", f"주변에서도 못 찾음(제자리 {here:.2f})"
                bad.append((k + 1, None))
        line = f"{mark} [{k+1:03d}] {s:7.1f}s [{st}] 일치 {here:.2f} {note} | {tx[:30]}"
        rep.append(line)
        print(line)

    summary = f"\n총 {len(lines)}줄 중 문제 {len(bad)}줄: " + \
              " ".join(f"{n:03d}" for n, _ in bad[:40])
    rep.append(summary)
    print(summary)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")


if __name__ == "__main__":
    main()
