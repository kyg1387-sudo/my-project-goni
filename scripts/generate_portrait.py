#!/usr/bin/env python3
"""배역 기준 초상 이미지를 생성한다 (image-to-video/reference-to-video용).

- 새 초상: fal FLUX로 텍스트 → 이미지
- 파생 초상: 기존 초상을 편집 모델로 의상/배경만 바꿔 같은 얼굴 유지
  (예: 로비 코트 차림 → 실내 재킷 차림)

사용법:
    python3 scripts/generate_portrait.py --name miran-coat --prompt "..."
    python3 scripts/generate_portrait.py --name miran-tweed --prompt "..." \
        --edit-from assets/portraits/miran-coat.png
결과는 assets/portraits/<name>.png 에 저장된다.
"""

import argparse
import base64
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_video import http_json, download  # noqa: E402

TEXT_MODEL = os.environ.get("FAL_IMAGE_MODEL", "fal-ai/flux/dev")
EDIT_MODEL = os.environ.get("FAL_EDIT_MODEL", "fal-ai/nano-banana/edit")


def queue_run(model, payload, key):
    headers = {"Authorization": f"Key {key}"}
    status, task = http_json(f"https://queue.fal.run/{model}", payload, headers)
    if status != 200:
        sys.exit(f"작업 생성 실패 (HTTP {status}): {task}")
    print(f"작업 생성됨: {task['request_id']} ({model})")
    while True:
        time.sleep(5)
        _, info = http_json(task["status_url"], headers=headers)
        state = info.get("status")
        if state == "COMPLETED":
            _, result = http_json(task["response_url"], headers=headers)
            return result
        if state in ("FAILED", "CANCELLED", "ERROR"):
            sys.exit(f"생성 실패: {info}")
        print(f"대기 중... ({state})")


def to_data_uri(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{b64}"


def first_image_url(result):
    imgs = result.get("images") or []
    if imgs:
        return imgs[0].get("url")
    img = result.get("image")
    return img.get("url") if isinstance(img, dict) else img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--edit-from", default="",
                    help="이 초상을 편집해 같은 얼굴로 의상/배경만 변경")
    args = ap.parse_args()

    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다.")

    if args.edit_from:
        payload = {
            "prompt": args.prompt,
            "image_urls": [to_data_uri(args.edit_from)],
            "output_format": "png",
        }
        result = queue_run(EDIT_MODEL, payload, key)
    else:
        payload = {
            "prompt": args.prompt,
            "image_size": {"width": 768, "height": 1024},
            "num_images": 1,
            "output_format": "png",
        }
        result = queue_run(TEXT_MODEL, payload, key)

    url = first_image_url(result)
    if not url:
        sys.exit(f"응답에서 이미지 URL을 못 찾음: {json.dumps(result)[:500]}")
    out = os.path.join("assets", "portraits", f"{args.name}.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    download(url, out)
    print(f"저장됨: {out}")


if __name__ == "__main__":
    main()
