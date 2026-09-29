#!/usr/bin/env python3
"""후보 목소리 몇 줄만 빠르게 시험 생성한다 (본 제작 전 무과금 검증용, 비용 원칙 1).

자막·영상 파이프라인과 무관하게, 지정한 대사 몇 줄을 후보 voice_id들로만 생성해
어미 발음(특히 사투리)이 자연스러운지 듣고 배역을 고르기 위한 것이다.
generate_audio.py와 같은 fal.ai MiniMax speech-02-hd 호출 방식을 그대로 쓴다.

사용법:
    export FAL_API_KEY=...
    python3 scripts/voice_test.py --lines scripts/audio/<skit>-voice-test.json \
        --out voice-tests/<skit>
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import fal_run, find_audio_url, download_retry  # noqa: E402

TTS_MODEL = "fal-ai/minimax/speech-02-hd"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True, help="시험 대사 목록 JSON")
    ap.add_argument("--out", required=True, help="mp3 저장 폴더")
    ap.add_argument("--language-boost", default="Korean")
    args = ap.parse_args()

    key = os.environ["FAL_API_KEY"]
    os.makedirs(args.out, exist_ok=True)

    with open(args.lines, encoding="utf-8") as f:
        items = json.load(f)

    failed = []
    for item in items:
        out_path = os.path.join(args.out, f"{item['id']}.mp3")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"[{item['id']}] 기존 파일 재사용")
            continue

        voice_setting = {"voice_id": item["voice"], "speed": item.get("speed", 1.0)}
        if item.get("emotion") and item["emotion"] != "neutral":
            voice_setting["emotion"] = item["emotion"]
        payload = {
            "text": item["text"],
            "voice_setting": voice_setting,
            "language_boost": args.language_boost,
        }

        print(f"[{item['id']}] {item.get('character', '')} / {item['voice']} 생성 중…")
        result = fal_run(TTS_MODEL, payload, key, item["id"])
        if result is None:
            failed.append(item["id"])
            continue
        url = find_audio_url(result)
        if not url or not download_retry(url, out_path):
            failed.append(item["id"])
            continue
        print(f"[{item['id']}] 완료 → {out_path}")

    if failed:
        print(f"실패한 항목: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
