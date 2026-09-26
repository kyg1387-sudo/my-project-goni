#!/usr/bin/env python3
"""생성된 대사 TTS를 Whisper로 전사해 언어 오염(중국어/영어 혼입)을 검사한다.

out/audio/line*.mp3 각각을 fal Whisper로 전사한 뒤, 자막(.ass)의 원문과 비교해
한글 비율이 낮거나(다른 언어로 발화) 원문과 겹치는 글자가 적은 줄을 플래그한다.
결과는 로그로 출력한다 (마지막에 "불량 줄: ..." 요약).

사용법:
    export FAL_API_KEY=... ; pip install fal-client
    python3 scripts/qc_tts.py --ass subs/<스킷>.ass --audio-dir out/audio
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


def char_overlap(expected, transcript):
    """원문 한글 글자 중 전사에 등장하는 비율(순서 무시, 대략적)."""
    exp = [c for c in expected if "가" <= c <= "힣"]
    if not exp:
        return 1.0
    tr = set(transcript)
    return sum(1 for c in exp if c in tr) / len(exp)


def looks_like_speech(transcript):
    """효과음 전사에서 말소리 혼입 판단. Whisper는 무음/소음에도 짧은 환청
    문구("Thank you." 등)를 내므로, CJK 글자가 있거나 단어가 3개 이상이면
    말소리 의심으로 플래그한다."""
    cjk = sum(1 for c in transcript if "가" <= c <= "힣" or "一" <= c <= "鿿")
    words = [w for w in re.split(r"\s+", transcript) if w]
    return cjk >= 2 or len(words) >= 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ass", required=True)
    ap.add_argument("--audio-dir", default="out/audio")
    ap.add_argument("--model", default="fal-ai/whisper")
    ap.add_argument("--patterns", default="line*.mp3",
                    help='검사 파일 패턴(쉼표 구분, 예 "amb*.wav,bgm.audio")')
    ap.add_argument("--config", default="",
                    help="오디오 설정 json (silent_styles 제외에 필요)")
    ap.add_argument("--report", default="",
                    help="결과를 저장할 텍스트 파일 경로 (선택)")
    args = ap.parse_args()

    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다.")

    lines = parse_ass(args.ass)
    if args.config:
        import json
        with open(args.config, encoding="utf-8") as f:
            silent = set(json.load(f).get("silent_styles", []))
        lines = [ln for ln in lines if ln[2] not in silent]
    files = []
    for pat in args.patterns.split(","):
        files += sorted(glob.glob(os.path.join(args.audio_dir, pat.strip())))
    print(f"자막 {len(lines)}줄, 오디오 파일 {len(files)}개")
    report = []

    def check(path):
        name = os.path.basename(path)
        m = re.search(r"line(\d+)", name)
        url = fal_upload(path, key)
        result = fal_run(args.model, {"audio_url": url, "task": "transcribe"},
                         key, f"qc {name}")
        transcript = (result or {}).get("text", "").strip()
        if m:  # 대사 TTS: 원문 대조
            idx = int(m.group(1))
            expected = lines[idx - 1][4] if idx - 1 < len(lines) else ""
            ratio = hangul_ratio(transcript)
            overlap = char_overlap(expected, transcript)
            bad = ratio < 0.8 or overlap < 0.5
            mark = "❌" if bad else "✅"
            msg = (f"{mark} [{idx:03d}] 한글비율 {ratio:.2f} 일치 {overlap:.2f}\n"
                   f"      원문: {expected}\n      전사: {transcript}")
        else:  # 현장음/BGM: 말소리 혼입 검사
            bad = looks_like_speech(transcript)
            mark = "❌" if bad else "✅"
            msg = f"{mark} [{name}] 전사: {transcript!r}"
        print(msg)
        report.append(msg)
        return name, bad

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, files))

    bad = sorted(n for n, b in results if b)
    summary = (f"\n검사 완료: 총 {len(results)}개 중 불량 {len(bad)}개\n"
               f"불량: {' '.join(bad) if bad else '없음'}")
    print(summary)
    report.append(summary)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
