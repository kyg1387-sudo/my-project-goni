#!/usr/bin/env python3
"""생성된 대사 TTS를 Whisper로 전사해 언어 오염(중국어/영어 혼입)을 검사한다.

out/audio/line*.mp3 각각을 fal Whisper로 전사한 뒤, 자막(.ass)의 원문과 비교해
대상 언어 글자 비율이 낮거나(다른 언어로 발화) 원문과 겹치는 글자가 적은 줄을 플래그한다.
결과는 로그로 출력한다 (마지막에 "불량 줄: ..." 요약).

사용법:
    export FAL_API_KEY=... ; pip install fal-client
    python3 scripts/qc_tts.py --ass subs/<스킷>.ass --audio-dir out/audio [--lang ko|ja]
    (--config 지정 시 language_boost와 silent_styles를 설정에서 읽는다)
"""

import argparse
import glob
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import parse_ass, fal_run, fal_upload  # noqa: E402


def is_script(c, lang):
    """문자 c가 대상 언어 문자(ko=한글, ja=가나·한자)인지."""
    if lang == "ja":
        return ("぀" <= c <= "ヿ") or ("一" <= c <= "鿿") or ("Ａ" <= c <= "ｚ")
    return "가" <= c <= "힣"


def hangul_ratio(text, lang="ko"):
    """전사문에서 대상 언어 문자의 비율 (알파벳·한자·가나·한글만 모수로)."""
    letters = [c for c in text if c.isalpha() or "一" <= c <= "鿿"]
    if not letters:
        return 0.0
    return sum(1 for c in letters if is_script(c, lang)) / len(letters)


def char_overlap(expected, transcript, lang="ko"):
    """원문 대상 언어 글자 중 전사에 등장하는 비율(순서 무시, 대략적)."""
    exp = [c for c in expected if is_script(c, lang)]
    if not exp:
        return 1.0
    tr = set(transcript)
    return sum(1 for c in exp if c in tr) / len(exp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ass", required=True)
    ap.add_argument("--audio-dir", default="out/audio")
    ap.add_argument("--model", default="fal-ai/whisper")
    ap.add_argument("--config", default="", help="오디오 설정 JSON (language_boost/silent_styles 반영)")
    ap.add_argument("--lang", default="", help="대상 언어 ko|ja (생략 시 설정의 language_boost로 판단)")
    args = ap.parse_args()

    cfg = {}
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            cfg = json.load(f)
    lang = args.lang or ("ja" if cfg.get("language_boost", "Korean") == "Japanese" else "ko")

    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다.")

    lines = parse_ass(args.ass)
    silent = set(cfg.get("silent_styles", []))
    lines = [l for l in lines if l[2] not in silent]  # TTS 줄 번호와 맞춤
    files = sorted(glob.glob(os.path.join(args.audio_dir, "line*.mp3")))
    print(f"자막 {len(lines)}줄, 오디오 파일 {len(files)}개")

    def check(path):
        idx = int(re.search(r"line(\d+)", path).group(1))
        expected = lines[idx - 1][4] if idx - 1 < len(lines) else ""
        url = fal_upload(path, key)
        payload = {"audio_url": url, "task": "transcribe"}
        if lang == "ja":
            payload["language"] = "ja"
        result = fal_run(args.model, payload, key, f"qc {idx:03d}")
        transcript = (result or {}).get("text", "").strip()
        ratio = hangul_ratio(transcript, lang)
        overlap = char_overlap(expected, transcript, lang)
        bad = ratio < 0.8 or overlap < 0.5
        mark = "❌" if bad else "✅"
        print(f"{mark} [{idx:03d}] {lang}비율 {ratio:.2f} 일치 {overlap:.2f}\n"
              f"      원문: {expected}\n      전사: {transcript}")
        return idx, bad

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, files))

    bad = sorted(i for i, b in results if b)
    print(f"\n검사 완료: 총 {len(results)}줄 중 불량 {len(bad)}줄")
    print("불량 줄:", " ".join(f"{i:03d}" for i in bad) if bad else "없음")


if __name__ == "__main__":
    main()
