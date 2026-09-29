#!/usr/bin/env python3
"""후보 목소리 몇 줄만 빠르게 시험 생성한다 (본 제작 전 무과금 검증용, 비용 원칙 1).

자막·영상 파이프라인과 무관하게, 지정한 대사 몇 줄을 후보 voice로만 생성해
어미 발음(특히 사투리)이 자연스러운지 듣고 배역을 고르기 위한 것이다.
줄마다 "engine"을 "elevenlabs"(기본) 또는 "minimax"로 지정할 수 있다.

- elevenlabs: ElevenLabs REST API 직접 호출 (동기 응답, xi-api-key 필요).
  voice는 ElevenLabs voice_id.
- minimax: generate_audio.py와 같은 fal.ai MiniMax speech-02-hd 큐 호출.
  voice는 MiniMax 프리셋 이름(예: Wise_Woman).

사용법:
    export ELEVENLABS_API_KEY=...   # elevenlabs 항목용
    export FAL_API_KEY=...          # minimax 항목용
    python3 scripts/voice_test.py --lines scripts/audio/<skit>-voice-test.json \
        --out voice-tests/<skit>
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import fal_run, find_audio_url, download_retry  # noqa: E402

MINIMAX_MODEL = "fal-ai/minimax/speech-02-hd"
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"


def elevenlabs_tts(voice_id, text, key, out_path, model_id=ELEVENLABS_MODEL_ID):
    """ElevenLabs TTS를 직접 호출해 mp3를 out_path에 저장한다. 성공 시 True."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(out_path, "wb") as f:
                f.write(resp.read())
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"  ElevenLabs 실패 (HTTP {e.code}): {body}")
        return False


def minimax_tts(voice, text, key, out_path, speed, emotion, language_boost):
    voice_setting = {"voice_id": voice, "speed": speed}
    if emotion and emotion != "neutral":
        voice_setting["emotion"] = emotion
    payload = {
        "text": text,
        "voice_setting": voice_setting,
        "language_boost": language_boost,
    }
    result = fal_run(MINIMAX_MODEL, payload, key, voice)
    if result is None:
        return False
    url = find_audio_url(result)
    return bool(url) and download_retry(url, out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True, help="시험 대사 목록 JSON")
    ap.add_argument("--out", required=True, help="mp3 저장 폴더")
    ap.add_argument("--language-boost", default="Korean", help="minimax 항목용")
    args = ap.parse_args()

    el_key = os.environ.get("ELEVENLABS_API_KEY")
    fal_key = os.environ.get("FAL_API_KEY")
    os.makedirs(args.out, exist_ok=True)

    with open(args.lines, encoding="utf-8") as f:
        items = json.load(f)

    failed = []
    for item in items:
        out_path = os.path.join(args.out, f"{item['id']}.mp3")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"[{item['id']}] 기존 파일 재사용")
            continue

        engine = item.get("engine", "elevenlabs")
        print(f"[{item['id']}] {item.get('character', '')} / {engine}:{item['voice']} 생성 중…")

        if engine == "elevenlabs":
            if not el_key:
                print(f"[{item['id']}] ELEVENLABS_API_KEY 없음 — 건너뜀")
                failed.append(item["id"])
                continue
            ok = elevenlabs_tts(item["voice"], item["text"], el_key, out_path,
                                 item.get("model_id", ELEVENLABS_MODEL_ID))
        elif engine == "minimax":
            if not fal_key:
                print(f"[{item['id']}] FAL_API_KEY 없음 — 건너뜀")
                failed.append(item["id"])
                continue
            ok = minimax_tts(item["voice"], item["text"], fal_key, out_path,
                              item.get("speed", 1.0), item.get("emotion"),
                              args.language_boost)
        else:
            print(f"[{item['id']}] 알 수 없는 engine: {engine}")
            ok = False

        if ok:
            print(f"[{item['id']}] 완료 → {out_path}")
        else:
            failed.append(item["id"])

    if failed:
        print(f"실패한 항목: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
