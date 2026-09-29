#!/usr/bin/env python3
"""정지 이미지 1장 + 대사 1줄로 오디오 구동 생성(OmniHuman) 시험을 만든다.

CLAUDE.md ⑤(3): "립싱크 정밀도 한계(한국어 음소 입 모양 근사치)는 대사 클로즈업
장면을 오디오 구동 생성(OmniHuman류)으로 만들어 보완" — lipsync_test.py(기존
영상에 사후로 입모양을 재합성하는 방식)와 달리, 이 스크립트는 애초에 오디오를
기준으로 통째로 새 영상을 생성한다(fal-ai/bytedance/omnihuman). 다인물 프레임에서
립싱크 모델이 엉뚱한 얼굴에 입을 맞추는 사고가 있었으므로, 반드시 화자 1인만
나오는 단독 이미지를 입력으로 써야 한다.

가격: $0.14/초 (fal.ai 공식, 2026-09 기준) — 대사 1줄(3~5초) 기준 1달러 미만.

사용법 (워크플로 내부에서):
    python3 scripts/omnihuman_test.py \
        --image video-tests/참교육사이다/stills/dohee-face-crop.jpg \
        --text "바다요? 아재. 나가 저 바다서 십 년 묵고 산 사람이요." \
        --voice tc_67b68ff3ba5438793103bfab --engine typecast \
        --out out/omnihuman-test.mp4
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import (  # noqa: E402
    fal_run, fal_upload, find_video_url, download_retry, typecast_tts_line, tts_line,
)

WORK_DIR = "out/omnihuman-test-work"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--engine", default="typecast", choices=["typecast", "minimax"])
    ap.add_argument("--emotion", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="fal-ai/bytedance/omnihuman/v1.5")
    ap.add_argument("--resolution", default="720p", choices=["720p", "1080p"])
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

    print(f"[2/3] 이미지·오디오 업로드 후 OmniHuman 생성 요청 ({args.model})...")
    img_url = fal_upload(args.image, fal_key)
    a_url = fal_upload(audio_path, fal_key)
    payload = {"image_url": img_url, "audio_url": a_url, "resolution": args.resolution}
    result = fal_run(args.model, payload, fal_key, "omnihuman-test", timeout_s=1200)
    if not result:
        sys.exit("OmniHuman 생성 실패 — 위 로그를 확인하세요.")
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
