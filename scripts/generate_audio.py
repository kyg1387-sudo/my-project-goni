#!/usr/bin/env python3
"""자막(.ass) 타이밍에 맞춰 대사 TTS와 배경음악을 생성해 영상에 입힌다.

fal.ai의 TTS(MiniMax speech)와 음악 생성(Lyria 2) 모델을 사용한다.
자막 파일의 각 Dialogue 줄에서 시작 시각·화자(Style/Name)·텍스트를 읽어
화자별 목소리로 음성을 만들고, 자막이 뜨는 시점에 맞춰 배치한 뒤
배경음악을 낮은 볼륨으로 깔아 영상에 믹싱한다.

사용법:
    export FAL_API_KEY=...
    python3 scripts/generate_audio.py \
        --ass subs/<스킷>.ass \
        --config scripts/audio/<스킷>.json \
        --video out/<스킷>-skit-subbed.mp4 \
        --out out/<스킷>-skit-final.mp4

ffmpeg/ffprobe가 PATH에 있어야 한다. BGM 생성에 실패하면 경고만 남기고
대사만으로 계속 진행한다.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_video import http_json, download  # noqa: E402


def download_retry(url, path, attempts=3):
    """일시적 네트워크 오류(불완전 수신 등)에 대비해 다운로드를 재시도한다."""
    for attempt in range(1, attempts + 1):
        try:
            download(url, path)
            return True
        except Exception as e:
            print(f"  다운로드 실패 ({attempt}/{attempts}): {e}")
            if attempt < attempts:
                time.sleep(2 * attempt)
    return False

WORK_DIR = None  # main에서 out/audio 로 설정


# ---------- fal.ai 큐 공통 ----------

def fal_run(model, payload, key, label, timeout_s=600):
    """fal 큐에 작업을 넣고 완료까지 기다려 결과 dict를 돌려준다. 실패 시 None."""
    headers = {"Authorization": f"Key {key}"}
    status, task = http_json(f"https://queue.fal.run/{model}", payload, headers)
    if status != 200:
        print(f"  [{label}] 작업 생성 실패 (HTTP {status}): {task}")
        return None
    status_url, result_url = task["status_url"], task["response_url"]
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(3)
        _, info = http_json(status_url, headers=headers)
        state = info.get("status")
        if state == "COMPLETED":
            _, result = http_json(result_url, headers=headers)
            return result
        if state in ("FAILED", "CANCELLED", "ERROR"):
            print(f"  [{label}] 생성 실패: {info}")
            return None
    print(f"  [{label}] 시간 초과")
    return None


def find_audio_url(obj):
    """응답 구조가 모델마다 달라, 오디오로 보이는 첫 URL을 재귀로 찾는다."""
    if isinstance(obj, str):
        if obj.startswith("http") and re.search(r"\.(mp3|wav|m4a|ogg|flac)(\?|$)", obj):
            return obj
        return None
    if isinstance(obj, dict):
        # audio/url 류의 키를 우선 탐색
        for k in ("audio", "audio_url", "audio_file", "url"):
            if k in obj:
                found = find_audio_url(obj[k])
                if found:
                    return found
        for v in obj.values():
            found = find_audio_url(v)
            if found:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = find_audio_url(v)
            if found:
                return found
    return None


# ---------- 자막 파싱 ----------

def parse_time(t):
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_ass(path):
    """(start초, end초, style, name, text) 목록을 돌려준다."""
    lines = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw.startswith("Dialogue:"):
                continue
            fields = raw[len("Dialogue:"):].strip().split(",", 9)
            if len(fields) < 10:
                continue
            start, end, style, name = fields[1], fields[2], fields[3], fields[4]
            text = re.sub(r"\{[^}]*\}", "", fields[9]).replace("\\N", " ").strip()
            if text:
                lines.append((parse_time(start), parse_time(end), style, name, text))
    return lines


# ---------- TTS / BGM ----------

def tts_line(cfg, key, index, voice, text, emotion=None):
    voice_setting = {"voice_id": voice, "speed": float(cfg.get("speed", 1.05))}
    if emotion and emotion != "neutral":
        voice_setting["emotion"] = emotion
    payload = {
        "text": text,
        "voice_setting": voice_setting,
        "language_boost": cfg.get("language_boost", "Korean"),
    }
    result = fal_run(cfg["tts_model"], payload, key, f"tts {index:03d}")
    if result is None:
        return None
    url = find_audio_url(result)
    if not url:
        print(f"  [tts {index:03d}] 응답에서 오디오 URL을 못 찾음: {result}")
        return None
    path = os.path.join(WORK_DIR, f"line{index:03d}.mp3")
    return path if download_retry(url, path) else None


def make_bgm(cfg, key):
    model = cfg.get("bgm_model")
    prompt = cfg.get("bgm_prompt")
    if not model or not prompt:
        return None
    result = fal_run(model, {"prompt": prompt}, key, "bgm")
    if result is None:
        return None
    url = find_audio_url(result)
    if not url:
        print(f"  [bgm] 응답에서 오디오 URL을 못 찾음: {result}")
        return None
    path = os.path.join(WORK_DIR, "bgm.audio")
    return path if download_retry(url, path) else None


# ---------- 믹싱 ----------

def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def mix(video, clips, bgm, bgm_volume, out_path):
    """clips: [(start초, 파일)] — 영상 오디오 트랙으로 믹싱해 out_path에 저장."""
    duration = probe_duration(video)
    cmd = ["ffmpeg", "-y", "-i", video]
    for _, path in clips:
        cmd += ["-i", path]
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", bgm]

    parts, mix_inputs = [], []
    for k, (start, _) in enumerate(clips):
        ms = int(round(start * 1000))
        parts.append(f"[{k + 1}:a]adelay={ms}:all=1[d{k}]")
        mix_inputs.append(f"[d{k}]")
    if bgm:
        parts.append(
            f"[{len(clips) + 1}:a]atrim=0:{duration:.3f},"
            f"afade=t=out:st={max(duration - 2, 0):.3f}:d=2,volume={bgm_volume}[bg]")
        mix_inputs.append("[bg]")
    parts.append(
        "".join(mix_inputs)
        + f"amix=inputs={len(mix_inputs)}:duration=longest:normalize=0,"
        + f"atrim=0:{duration:.3f}[aout]")

    script = os.path.join(WORK_DIR, "filter.txt")
    with open(script, "w") as f:
        f.write(";\n".join(parts))
    cmd += ["-filter_complex_script", script,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out_path]
    subprocess.run(cmd, check=True)


def main():
    global WORK_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--ass", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다. (키를 코드나 채팅에 넣지 마세요)")

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    WORK_DIR = os.path.join(os.path.dirname(args.out) or ".", "audio")
    os.makedirs(WORK_DIR, exist_ok=True)

    lines = parse_ass(args.ass)
    print(f"자막 {len(lines)}줄 파싱됨")

    clips = []
    for i, (start, _end, style, name, text) in enumerate(lines, start=1):
        voice = (cfg.get("name_voices", {}).get(name)
                 or cfg.get("style_voices", {}).get(style)
                 or cfg["default_voice"])
        # 감정: 줄 번호별 지정이 우선, 없으면 스타일 기본값
        emotion = (cfg.get("emotion_overrides", {}).get(str(i))
                   or cfg.get("style_emotions", {}).get(style))
        print(f"[{i:03d}/{len(lines)}] {start:7.2f}s {voice}/{emotion or 'neutral'}: {text[:30]}")
        path = tts_line(cfg, key, i, voice, text, emotion)
        if not path:  # 한 번 재시도
            print(f"  [tts {i:03d}] 재시도")
            path = tts_line(cfg, key, i, voice, text, emotion)
        if not path:
            sys.exit(f"[tts {i:03d}] 생성 실패 — 위 로그를 확인하세요.")
        clips.append((start, path))

    print("배경음악 생성 중...")
    bgm = make_bgm(cfg, key)
    if not bgm:
        print("경고: 배경음악 생성 실패 — 대사만으로 계속 진행합니다.")

    print("믹싱 중...")
    mix(args.video, clips, bgm, float(cfg.get("bgm_volume", 0.22)), args.out)
    print(f"완료 → {args.out}")


if __name__ == "__main__":
    main()
