#!/usr/bin/env python3
"""캐릭터 시트를 참조 이미지로 넣어 특정 장면(들)을 reference-to-video로 재생성한다.

일반 text-to-video(fal-ai/bytedance/seedance/v1/lite/text-to-video)는 긴 프롬프트에서
가끔 엉뚱한 인물/장소를 생성한다(참교육사이다 118장면 본 제작에서 다수 실증) —
그 장면들만 캐릭터 시트를 참조로 넣어 다시 만든다. 인물 얼굴·의상이 시트에 고정되므로
"다른 사람처럼 나옴" 문제가 구조적으로 줄어든다(docs/영화제작규칙집.md §1-2 방식).

사용법 (워크플로 내부):
    python3 scripts/regen_scene_ref.py \
        --scenes-json scripts/scenes/참교육사이다.json \
        --scene 31 --characters 한도희,서회장 \
        --out out/scene31.mp4
    # --scene에 쉼표로 여러 개 지정 가능(각각 --characters-map으로 다른 인물 지정 시
    # JSON 매핑 파일을 --map으로 대신 넘긴다: {"31": ["한도희","서회장"], "43": [...]})
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_video import http_json, download  # noqa: E402
from build_character_sheets import CHARACTERS, OUT_DIR as SHEETS_DIR  # noqa: E402

REF_MODEL = os.environ.get(
    "FAL_REF_VIDEO_MODEL", "bytedance/seedance-2.0/fast/reference-to-video")


def sheet_path(name):
    fields = CHARACTERS[name]
    return os.path.join(SHEETS_DIR, f"{fields['name_en'].lower().replace(' ', '-')}.jpg")


def find_video_url(obj):
    import re
    if isinstance(obj, str):
        return obj if obj.startswith("http") and re.search(r"\.(mp4|mov|webm)(\?|$)", obj) else None
    if isinstance(obj, dict):
        for k in ("video", "video_url", "url"):
            if k in obj:
                found = find_video_url(obj[k])
                if found:
                    return found
        for v in obj.values():
            found = find_video_url(v)
            if found:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = find_video_url(v)
            if found:
                return found
    return None


def fal_upload(path, key):
    os.environ.setdefault("FAL_KEY", key)
    import fal_client
    return fal_client.upload_file(path)


def regen_one(key, prompt, ref_paths, duration, ratio, out_path, label):
    ref_urls = [fal_upload(p, key) for p in ref_paths]
    headers = {"Authorization": f"Key {key}"}
    payload = {
        "prompt": prompt,
        "image_urls": ref_urls,
        "duration": str(duration),
        "aspect_ratio": ratio,
        "resolution": "720p",
    }
    status, task = http_json(f"https://queue.fal.run/{REF_MODEL}", payload, headers)
    if status != 200:
        print(f"  [{label}] 작업 생성 실패 (HTTP {status}): {task}")
        return False
    status_url, result_url = task["status_url"], task["response_url"]
    print(f"  [{label}] 작업 생성됨: {task.get('request_id')}")
    while True:
        time.sleep(10)
        _, info = http_json(status_url, headers=headers)
        state = info.get("status")
        if state == "COMPLETED":
            _, result = http_json(result_url, headers=headers)
            url = find_video_url(result)
            if not url:
                print(f"  [{label}] 응답에서 영상 URL을 못 찾음: {result}")
                return False
            download(url, out_path)
            return True
        if state in ("FAILED", "CANCELLED", "ERROR"):
            print(f"  [{label}] 생성 실패: {info}")
            return False
        print(f"  [{label}] 대기 중... ({state})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes-json", help="지정 장면 재생성 모드에 필요 (--custom-* 미사용 시)")
    ap.add_argument("--scene", help="단일 장면 번호 (1부터)")
    ap.add_argument("--characters", help="--scene용 쉼표 구분 인물 이름")
    ap.add_argument("--map", help="여러 장면용 JSON 매핑 파일 {\"31\": [\"한도희\",\"서회장\"], ...}")
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--custom-image", help="캐릭터 시트 대신 쓸 임의 참조 이미지 경로 "
                    "(카메오 등, CHARACTERS 목록에 없는 인물용)")
    ap.add_argument("--custom-prompt", help="--custom-image와 함께 쓰는 장면 프롬프트")
    ap.add_argument("--custom-duration", type=int, default=8)
    ap.add_argument("--custom-ratio", default="16:9")
    ap.add_argument("--custom-out", help="--custom-image 결과 파일 경로")
    args = ap.parse_args()

    key = (os.environ.get("FAL_API_KEY") or "").strip()
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다.")

    if args.custom_image:
        if not (args.custom_prompt and args.custom_out):
            sys.exit("--custom-image에는 --custom-prompt와 --custom-out이 함께 필요합니다.")
        ok = regen_one(key, args.custom_prompt, [args.custom_image], args.custom_duration,
                        args.custom_ratio, args.custom_out, "custom")
        sys.exit(0 if ok else "커스텀 장면 생성 실패")

    if not args.scenes_json:
        sys.exit("--scenes-json이 필요합니다 (또는 --custom-image 모드 사용).")

    with open(args.scenes_json, encoding="utf-8") as f:
        data = json.load(f)
    scenes, duration, ratio = data["scenes"], int(data.get("duration", 5)), data.get("ratio", "16:9")

    if args.map:
        mapping = json.load(open(args.map, encoding="utf-8"))
    elif args.scene and args.characters:
        mapping = {args.scene: [c.strip() for c in args.characters.split(",")]}
    else:
        sys.exit("--scene+--characters 또는 --map 중 하나가 필요합니다.")

    os.makedirs(args.out_dir, exist_ok=True)
    failed = []
    for scene_no, chars in mapping.items():
        idx = int(scene_no) - 1
        prompt = scenes[idx]
        refs = [sheet_path(c) for c in chars]
        for c, p in zip(chars, refs):
            if not os.path.exists(p):
                sys.exit(f"캐릭터 시트가 없습니다: {c} -> {p} (build_character_sheets.py 먼저 실행)")
        out_path = os.path.join(args.out_dir, f"scene{int(scene_no):02d}.mp4")
        print(f"[scene {scene_no}] 참조 인물: {chars}")
        ok = regen_one(key, prompt, refs, duration, ratio, out_path, f"scene {scene_no}")
        if not ok:
            failed.append(scene_no)

    if failed:
        sys.exit(f"실패한 장면: {failed}")
    print("전체 완료.")


if __name__ == "__main__":
    main()
