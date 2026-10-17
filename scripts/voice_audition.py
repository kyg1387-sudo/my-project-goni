#!/usr/bin/env python3
"""배역 목소리 오디션 — 후보 목소리마다 오디션 대사를 생성해 배역별 비교 파일로 묶는다.

오디션 설정(scripts/audition/<작품>.json)의 배역마다 후보 목소리 × 오디션 대사를 fal.ai로
생성한다. 엔진은 MiniMax(speech-02-hd, 감정·속도 파라미터)와 ElevenLabs v3(대사 앞
연기 태그)를 지원한다. 결과:

    auditions/<작품>/<배역>/<번호>-<엔진>-<목소리>.mp3   후보별 (대사들을 1초 간격으로 이음)
    auditions/<작품>/index.md                             후보 번호표 (청취 후 번호로 선택)

이미 있는 후보 파일은 재사용(재과금 없음). 생성 실패한 후보는 건너뛰고 index에 표시한다.

사용법:
    export FAL_API_KEY=...
    python3 scripts/voice_audition.py scripts/audition/beggar-chairman.json
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import download_retry, fal_run, find_audio_url  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def tts(engines, cand, line, key, label):
    """후보 목소리로 대사 1줄을 생성해 오디오 URL을 돌려준다. 실패 시 None."""
    eng = engines[cand["engine"]]
    if cand["engine"] == "mm":
        setting = {"voice_id": cand["voice"], "speed": line.get("speed", 1.0)}
        if line.get("emotion", "neutral") != "neutral":
            setting["emotion"] = line["emotion"]
        payload = {"text": line["text"], "voice_setting": setting,
                   "language_boost": eng.get("language_boost", "Japanese")}
    else:  # el — 연기 태그는 2~4단어로 짧게 (긴 지시문은 낭독으로 누출됨)
        text = f"{line['tag']} {line['text']}" if line.get("tag") else line["text"]
        payload = {"text": text, "voice": cand["voice"]}
        if eng.get("language_code"):
            payload["language_code"] = eng["language_code"]
    result = fal_run(eng["model"], payload, key, label)
    return find_audio_url(result) if result else None


def join_with_gaps(parts, out_path, gap=1.0):
    """대사 파일들을 gap초 무음을 사이에 두고 하나로 잇는다."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for p in parts:
        cmd += ["-i", p]
    chains, labels = [], []
    for k in range(len(parts)):
        pad = f",apad=pad_dur={gap}" if k < len(parts) - 1 else ""
        chains.append(f"[{k}:a]aformat=sample_rates=44100:channel_layouts=stereo{pad}[a{k}]")
        labels.append(f"[a{k}]")
    chains.append("".join(labels) + f"concat=n={len(parts)}:v=0:a=1[out]")
    cmd += ["-filter_complex", ";".join(chains), "-map", "[out]",
            "-c:a", "libmp3lame", "-q:a", "3", out_path]
    subprocess.run(cmd, check=True)


def main():
    if len(sys.argv) != 2:
        sys.exit("사용법: python3 scripts/voice_audition.py scripts/audition/<작품>.json")
    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다. (키를 코드나 채팅에 넣지 마세요)")
    with open(sys.argv[1], encoding="utf-8") as f:
        cfg = json.load(f)

    base = os.path.join(ROOT, "auditions", cfg["work"])
    tmp = os.path.join(base, ".tmp")
    os.makedirs(tmp, exist_ok=True)
    index = [f"# 「{cfg['work']}」 목소리 오디션", "",
             "배역별로 후보 파일을 들어 보고 마음에 드는 **번호**를 알려 주세요.", ""]
    failed = 0

    for role in cfg["roles"]:
        role_dir = os.path.join(base, role["role"])
        os.makedirs(role_dir, exist_ok=True)
        index += [f"## {role['label']}", "",
                  "오디션 대사: " + " / ".join(f"「{l['text']}」" for l in role["lines"]), "",
                  "| 번호 | 엔진 | 목소리 | 파일 |", "|---|---|---|---|"]
        for n, cand in enumerate(role["candidates"], start=1):
            name = f"{n:02d}-{cand['engine']}-{cand['voice']}.mp3"
            out = os.path.join(role_dir, name)
            engine = "MiniMax" if cand["engine"] == "mm" else "ElevenLabs v3"
            if not os.path.exists(out):
                parts = []
                for i, line in enumerate(role["lines"], start=1):
                    label = f"{role['role']} {n:02d} {cand['voice']} #{i}"
                    print(f"[{label}] {line['text'][:24]}")
                    url = tts(cfg["engines"], cand, line, key, label)
                    part = os.path.join(tmp, f"{role['role']}-{n:02d}-{i}.audio")
                    if not url or not download_retry(url, part):
                        parts = None
                        break
                    parts.append(part)
                if parts:
                    join_with_gaps(parts, out)
            if os.path.exists(out):
                index.append(f"| {n} | {engine} | {cand['voice']} | `{role['role']}/{name}` |")
            else:
                failed += 1
                index.append(f"| {n} | {engine} | {cand['voice']} | 생성 실패 (과금 없음) |")
        index.append("")

    with open(os.path.join(base, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index) + "\n")
    subprocess.run(["rm", "-rf", tmp], check=False)
    print(f"완료 → auditions/{cfg['work']}/ (실패 후보 {failed}개)")


if __name__ == "__main__":
    main()
