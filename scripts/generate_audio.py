#!/usr/bin/env python3
"""콩트 영상에 대사 음성(TTS)과 배경 소리를 입힌다.

fal.ai의 ElevenLabs TTS로 대사를 생성하고(사장/손님 목소리 구분),
Stable Audio로 밤거리 노점 배경음을 만든 뒤, ffmpeg로 영상에 믹싱한다.
배경음 생성에 실패하면 대사만이라도 입힌다.

사용법:
    export FAL_API_KEY=...
    python3 scripts/generate_audio.py <입력영상.mp4> <출력영상.mp4>
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

VENDOR_VOICE = "Josh"    # 사장: 낮고 능청스러운 남성 목소리
CUSTOMER_VOICE = "Sarah" # 손님: 밝은 여성 목소리

# (시작 초, 목소리, 대사) — 12초 시퀀스의 자막 타이밍(subs/bungeoppang-seq003.ass)과 동일
LINES = [
    (0.0, VENDOR_VOICE, "내가 볼때는, 이 동네는..."),
    (2.0, VENDOR_VOICE, "예쁜 언니밖에 없어요!"),
    (4.0, CUSTOMER_VOICE, "하하하! 아 진짜 못 말려!"),
    (6.0, VENDOR_VOICE, "너무 예뻐서 삼백 원."),
    (8.0, VENDOR_VOICE, "내일 오면 공짜예요."),
    (10.0, VENDOR_VOICE, "내일은 더 예뻐질 거니까!"),
]

AMBIENCE_PROMPT = ("cozy Korean night street food market ambience, distant chatter, "
                   "sizzling griddle, gentle winter wind, warm and lively")


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


def fal_run(model, payload, key):
    """fal 큐에 작업을 넣고 완료까지 기다린 뒤 결과 dict를 돌려준다. 실패 시 None."""
    headers = {"Authorization": f"Key {key}"}
    status, task = http_json(f"https://queue.fal.run/{model}", payload, headers)
    if status != 200:
        print(f"  [fal:{model}] 작업 생성 실패 (HTTP {status}): {task}")
        return None
    while True:
        time.sleep(3)
        _, info = http_json(task["status_url"], headers=headers)
        state = info.get("status")
        if state == "COMPLETED":
            _, result = http_json(task["response_url"], headers=headers)
            return result
        if state in ("FAILED", "CANCELLED", "ERROR"):
            print(f"  [fal:{model}] 실패: {info}")
            return None


def find_audio_url(result):
    """결과에서 오디오 URL을 찾는다 (모델마다 필드 이름이 다름)."""
    if not isinstance(result, dict):
        return None
    for key in ("audio", "audio_file", "audio_url"):
        v = result.get(key)
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
        if isinstance(v, str) and v.startswith("http"):
            return v
    return None


def main():
    if len(sys.argv) != 3:
        sys.exit("사용법: generate_audio.py <입력영상.mp4> <출력영상.mp4>")
    video_in, video_out = sys.argv[1], sys.argv[2]
    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다.")

    workdir = os.path.join(os.path.dirname(video_out) or ".", "audio")
    os.makedirs(workdir, exist_ok=True)

    # 1) 대사 TTS 생성
    voice_files = []  # (시작초, 파일경로)
    for i, (start, voice, text) in enumerate(LINES, start=1):
        print(f"[대사 {i}] ({voice}) {text}")
        result = fal_run("fal-ai/elevenlabs/tts/multilingual-v2",
                         {"text": text, "voice": voice, "speed": 1.1}, key)
        url = find_audio_url(result)
        if not url:
            sys.exit(f"[대사 {i}] TTS 실패 — 결과: {result}")
        path = os.path.join(workdir, f"line{i:02d}.mp3")
        urllib.request.urlretrieve(url, path)
        voice_files.append((start, path))

    # 2) 배경음 생성 (실패해도 계속 진행)
    ambience = None
    print("[배경음] 밤거리 노점 앰비언스 생성 중...")
    result = fal_run("fal-ai/stable-audio", {"prompt": AMBIENCE_PROMPT, "seconds_total": 12}, key)
    url = find_audio_url(result)
    if url:
        ambience = os.path.join(workdir, "ambience.mp3")
        urllib.request.urlretrieve(url, ambience)
    else:
        print("[배경음] 생성 실패 — 대사만 입힙니다.")

    # 3) ffmpeg 믹싱: 각 대사를 제 타이밍으로 밀고(adelay), 배경음은 볼륨을 낮춰 합친다
    inputs = ["-i", video_in]
    filters = []
    mix_labels = []
    for idx, (start, path) in enumerate(voice_files, start=1):
        inputs += ["-i", path]
        ms = int(start * 1000)
        filters.append(f"[{idx}:a]adelay={ms}|{ms}[v{idx}]")
        mix_labels.append(f"[v{idx}]")
    if ambience:
        inputs += ["-i", ambience]
        amb_idx = len(voice_files) + 1
        filters.append(f"[{amb_idx}:a]volume=0.25[amb]")
        mix_labels.append("[amb]")
    filters.append(f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:normalize=0[aout]")

    cmd = ["ffmpeg", "-y", *inputs,
           "-filter_complex", ";".join(filters),
           "-map", "0:v", "-map", "[aout]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
           video_out]
    print("실행:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"완료 → {video_out}")


if __name__ == "__main__":
    main()
