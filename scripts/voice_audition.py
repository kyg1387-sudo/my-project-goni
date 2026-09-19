#!/usr/bin/env python3
"""목소리 오디션 생성기.

scripts/auditions/<작품>.json 의 시험 목록(배역 후보 목소리 × 핵심 감정 대사)을
읽어 TTS 샘플을 생성한다. out/audition/<id>.mp3 가 있으면 재사용한다.
본편 제작 전 사용자가 듣고 배역을 확정하기 위한 것 (감정표현력 기준).

사용법: python scripts/voice_audition.py <작품>   (FAL_API_KEY 필요)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

OUT_DIR = os.environ.get("AUDITION_OUT_DIR", "out/audition")


def http_json(url, payload=None, headers=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            body = json.loads(body)
        except ValueError:
            pass
        return e.code, body


def find_audio_url(result):
    if not isinstance(result, dict):
        return None
    for k in ("audio", "audio_file", "audio_url"):
        v = result.get(k)
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
        if isinstance(v, str) and v.startswith("http"):
            return v
    return None


def fal_run(model, payload, key, tag):
    headers = {"Authorization": f"Key {key}"}
    status, task = http_json(f"https://queue.fal.run/{model}", payload, headers)
    if status != 200:
        print(f"  [{tag}] 작업 생성 실패 (HTTP {status}): {task}")
        return None
    while True:
        time.sleep(4)
        _, info = http_json(task["status_url"], headers=headers)
        state = info.get("status")
        if state == "COMPLETED":
            _, result = http_json(task["response_url"], headers=headers)
            return result
        if state in ("FAILED", "CANCELLED", "ERROR"):
            print(f"  [{tag}] 생성 실패: {info}")
            return None


def main():
    if len(sys.argv) < 2:
        sys.exit("사용법: voice_audition.py <작품>")
    spec = json.load(open(os.path.join("scripts", "auditions", f"{sys.argv[1]}.json"),
                          encoding="utf-8"))
    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY가 필요합니다.")
    os.makedirs(OUT_DIR, exist_ok=True)
    failed = []
    for t in spec["tests"]:
        path = os.path.join(OUT_DIR, f"{t['id']}.mp3")
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            print(f"[{t['id']}] 기존 파일 재사용")
            continue
        model = t.get("model", spec.get("tts_model", "fal-ai/minimax/speech-02-hd"))
        if model == "elevenlabs-direct":
            # 사용자 본인 ElevenLabs 계정의 보이스(개인 클론) — ELEVENLABS_API_KEY 필요
            el_key = os.environ.get("ELEVENLABS_API_KEY")
            if not el_key:
                failed.append(t["id"])
                print(f"[{t['id']}] ELEVENLABS_API_KEY 시크릿이 없습니다 — 건너뜀")
                continue
            print(f"[{t['id']}] elevenlabs-direct {t['voice']}: {t['text'][:30]}…")
            req = urllib.request.Request(
                f"https://api.elevenlabs.io/v1/text-to-speech/{t['voice']}",
                data=json.dumps({
                    "text": t["text"],
                    "model_id": t.get("el_model", "eleven_v3"),
                }).encode(),
                headers={"Content-Type": "application/json", "xi-api-key": el_key},
                method="POST")
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    open(path, "wb").write(resp.read())
                print(f"  저장됨 → {path}")
            except urllib.error.HTTPError as e:
                print(f"  [{t['id']}] ElevenLabs 오류 (HTTP {e.code}): {e.read().decode(errors='replace')[:300]}")
                failed.append(t["id"])
            continue
        if "elevenlabs" in model:
            # ElevenLabs (fal 호스팅) — v3는 감정을 대사 안의 오디오 태그([sobbing] 등)로 지시
            payload = {"text": t["text"], "voice": t["voice"]}
            for k in ("stability", "similarity_boost", "style", "speed"):
                if k in t:
                    payload[k] = t[k]
        else:
            voice_setting = {"voice_id": t["voice"], "speed": float(t.get("speed", spec.get("speed", 1.0)))}
            if t.get("emotion") and t["emotion"] != "neutral":
                voice_setting["emotion"] = t["emotion"]
            payload = {
                "text": t["text"],
                "voice_setting": voice_setting,
                "language_boost": spec.get("language_boost", "Korean"),
            }
        print(f"[{t['id']}] {model} {t['voice']}/{t.get('emotion','-')}: {t['text'][:30]}…")
        result = fal_run(model, payload, key, t["id"])
        url = find_audio_url(result) if result else None
        if not url:
            failed.append(t["id"])
            continue
        urllib.request.urlretrieve(url, path)
        print(f"  저장됨 → {path}")
    if failed:
        sys.exit(f"생성 실패: {', '.join(failed)}")
    print("오디션 샘플 생성 완료")


if __name__ == "__main__":
    main()
