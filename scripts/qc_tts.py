#!/usr/bin/env python3
"""생성된 대사 TTS를 Whisper로 전사해 언어 오염(중국어/영어 혼입)을 검사한다.

out/audio/line*.mp3 각각을 fal Whisper로 전사한 뒤, 자막(.ass)의 원문과 비교해
목표 언어 비율이 낮거나(다른 언어로 발화) 원문과 겹치는 글자가 적은 줄을 플래그한다.
--lang ja(일본 채널 기본)는 한글·영문이 한 글자라도 섞이면 불량으로 본다.
결과는 로그로 출력한다 (마지막에 "불량 줄: ..." 요약).

사용법:
    export FAL_API_KEY=... ; pip install fal-client
    python3 scripts/qc_tts.py --ass subs/<스킷>.ass --audio-dir out/audio --lang ja
"""

import argparse
import glob
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import parse_ass, fal_run, fal_upload  # noqa: E402


def hangul_ratio(text):
    letters = [c for c in text if c.isalpha() or "一" <= c <= "鿿"]
    if not letters:
        return 0.0
    hangul = [c for c in letters if "가" <= c <= "힣"]
    return len(hangul) / len(letters)


def is_japanese(c):
    return ("\u3040" <= c <= "\u30ff") or ("一" <= c <= "鿿") or c == "ー"


def japanese_ratio(text):
    letters = [c for c in text if c.isalpha() or is_japanese(c)]
    if not letters:
        return 0.0
    return sum(1 for c in letters if is_japanese(c)) / len(letters)


def foreign_chars(text):
    """일본어 줄에 섞이면 안 되는 한글·라틴 문자."""
    return [c for c in text if ("가" <= c <= "힣") or ("a" <= c.lower() <= "z")]


def char_overlap_ja(expected, transcript):
    """원문 가나·한자 중 전사에 등장하는 비율(순서 무시, 대략적).
    TTS 입력은 읽기 가나, 전사는 한자일 수 있어 기준을 낮게 잡는다."""
    exp = [c for c in expected if is_japanese(c)]
    if not exp:
        return 1.0
    tr = set(transcript)
    return sum(1 for c in exp if c in tr) / len(exp)


def char_overlap(expected, transcript):
    """원문 한글 글자 중 전사에 등장하는 비율(순서 무시, 대략적)."""
    exp = [c for c in expected if "가" <= c <= "힣"]
    if not exp:
        return 1.0
    tr = set(transcript)
    return sum(1 for c in exp if c in tr) / len(exp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ass", required=True)
    ap.add_argument("--audio-dir", default="out/audio")
    ap.add_argument("--model", default="fal-ai/whisper")
    ap.add_argument("--lang", default="ko", choices=["ko", "ja"])
    args = ap.parse_args()

    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다.")

    lines = parse_ass(args.ass)
    files = sorted(glob.glob(os.path.join(args.audio_dir, "line*.mp3")))
    print(f"자막 {len(lines)}줄, 오디오 파일 {len(files)}개")

    def check(path):
        idx = int(re.search(r"line(\d+)", path).group(1))
        expected = lines[idx - 1][4] if idx - 1 < len(lines) else ""
        url = fal_upload(path, key)
        payload = {"audio_url": url, "task": "transcribe"}
        if args.lang == "ja":
            payload["language"] = "ja"
        result = fal_run(args.model, payload, key, f"qc {idx:03d}")
        transcript = (result or {}).get("text", "").strip()
        if args.lang == "ja":
            ratio = japanese_ratio(transcript)
            overlap = char_overlap_ja(expected, transcript)
            foreign = foreign_chars(transcript)
            bad = bool(foreign) or ratio < 0.9 or overlap < 0.4
            label = f"일본어비율 {ratio:.2f} 일치 {overlap:.2f}"
            if foreign:
                label += f" 외국문자 {''.join(foreign)}"
        else:
            ratio = hangul_ratio(transcript)
            overlap = char_overlap(expected, transcript)
            bad = ratio < 0.8 or overlap < 0.5
            label = f"한글비율 {ratio:.2f} 일치 {overlap:.2f}"
        mark = "❌" if bad else "✅"
        print(f"{mark} [{idx:03d}] {label}\n"
              f"      원문: {expected}\n      전사: {transcript}")
        return idx, bad

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, files))

    bad = sorted(i for i, b in results if b)
    print(f"\n검사 완료: 총 {len(results)}줄 중 불량 {len(bad)}줄")
    print("불량 줄:", " ".join(f"{i:03d}" for i in bad) if bad else "없음")


if __name__ == "__main__":
    main()
