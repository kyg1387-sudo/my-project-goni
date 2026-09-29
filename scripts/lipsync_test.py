#!/usr/bin/env python3
"""기존 장면 클립 1개 + 대사 1줄로 립싱크 시험을 만든다 (voice_test.py의 립싱크판).

정식 파이프라인(generate_audio.py --lipsync)은 스킷 전체 자막·장면을 요구하지만,
"이 목소리·이 클립으로 입모양이 자연스럽게 나오는지"만 미리 싸게 확인하고 싶을 때
쓰는 독립 시험 도구다. TTS 1줄 + 립싱크 1회만 과금된다(스킷 전체 재생성 없음).

fal.ai·typecast.ai는 이 세션(sandbox)에서 네트워크가 막혀 있어 로컬 실행은 안 되고,
GitHub Actions(lipsync-test.yml)에서만 실행된다.

사용법 (워크플로 내부에서):
    python3 scripts/lipsync_test.py \
        --video video-tests/참교육사이다/scene62.mp4 \
        --text "바다요? 아재. 나가 저 바다서 십 년 묵고 산 사람이요." \
        --voice tc_67b68ff3ba5438793103bfab --engine typecast \
        --emotion happy --out out/lipsync-test.mp4
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import (  # noqa: E402
    fal_run, fal_upload, find_video_url, download_retry, typecast_tts_line, tts_line,
)

WORK_DIR = "out/lipsync-test-work"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--engine", default="typecast", choices=["typecast", "minimax"])
    ap.add_argument("--emotion", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lipsync-model", default="fal-ai/sync-lipsync")
    args = ap.parse_args()

    import generate_audio
    generate_audio.WORK_DIR = WORK_DIR
    os.makedirs(WORK_DIR, exist_ok=True)

    fal_key = (os.environ.get("FAL_API_KEY") or "").strip()
    if not fal_key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다.")

    print(f"[1/3] TTS 생성 ({args.engine}): {args.text[:40]}...")
    if args.engine == "typecast":
        tc_key = (os.environ.get("TYPECAST_API_KEY") or "").strip()
        if not tc_key:
            sys.exit("TYPECAST_API_KEY 환경 변수가 필요합니다.")
        cfg = {}
        audio_path = typecast_tts_line(cfg, tc_key, 1, args.voice, args.text, args.emotion)
    else:
        cfg = {"tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Korean"}
        audio_path = tts_line(cfg, fal_key, 1, args.voice, args.text, args.emotion)
    if not audio_path:
        sys.exit("TTS 생성 실패 — 위 로그를 확인하세요.")
    print(f"  → {audio_path}")

    print(f"[2/3] 클립·오디오 업로드 후 립싱크 요청 ({args.lipsync_model})...")
    v_url = fal_upload(args.video, fal_key)
    a_url = fal_upload(audio_path, fal_key)
    payload = {"video_url": v_url, "audio_url": a_url}
    if "sync-lipsync" in args.lipsync_model:
        payload["sync_mode"] = "cut_off"
    result = fal_run(args.lipsync_model, payload, fal_key, "lipsync-test", timeout_s=1200)
    if not result:
        sys.exit("립싱크 생성 실패 — 위 로그를 확인하세요.")
    url = find_video_url(result)
    if not url:
        sys.exit(f"응답에서 영상 URL을 못 찾음: {result}")

    print("[3/3] 결과 다운로드...")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    if not download_retry(url, args.out):
        sys.exit("결과 다운로드 실패")
    print(f"완료 → {args.out}")


if __name__ == "__main__":
    main()
