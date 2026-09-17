#!/usr/bin/env python3
"""인물 기준 초상 이미지 생성기.

scripts/portraits/<작품>.json 의 인물 목록을 읽어 fal.ai 이미지 모델로
정면 초상 후보를 생성한다. out/portraits/<id>-N.png 가 이미 있으면
재사용(이어하기)한다. 여기서 확정된 초상이 image-to-video 장면 생성의
기준 이미지가 된다 (인물 일관성 + 재생성 비용 절감).

환경 변수:
  FAL_API_KEY        필수
  FAL_IMAGE_MODEL    기본값: fal-ai/bytedance/seedream/v3/text-to-image
사용법: python scripts/generate_portraits.py <작품>
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

FAL_IMAGE_MODEL = os.environ.get(
    "FAL_IMAGE_MODEL", "fal-ai/bytedance/seedream/v3/text-to-image")
OUT_DIR = os.environ.get("PORTRAIT_OUT_DIR", "out/portraits")


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


def extract_image_urls(result):
    if not isinstance(result, dict):
        return []
    images = result.get("images") or []
    if isinstance(result.get("image"), dict):
        images = [result["image"]]
    return [im["url"] for im in images if isinstance(im, dict) and im.get("url")]


def fal_image(key, prompt, num_images):
    headers = {"Authorization": f"Key {key}"}
    # 모델별 파라미터 차이를 흡수: 실패하면 다음 페이로드로 재시도
    payloads = [
        {"prompt": prompt, "aspect_ratio": "3:4", "num_images": num_images},
        {"prompt": prompt, "image_size": "portrait_4_3", "num_images": num_images},
        {"prompt": prompt, "num_images": num_images},
    ]
    for payload in payloads:
        status, task = http_json(f"https://queue.fal.run/{FAL_IMAGE_MODEL}", payload, headers)
        if status != 200:
            print(f"  [fal] 작업 생성 실패 (HTTP {status}): {task} — 다른 파라미터로 재시도")
            continue
        status_url, result_url = task["status_url"], task["response_url"]
        print(f"  [fal] 작업 생성됨: {task['request_id']}")
        while True:
            time.sleep(5)
            _, info = http_json(status_url, headers=headers)
            state = info.get("status")
            if state == "COMPLETED":
                r_status, result = http_json(result_url, headers=headers)
                urls = extract_image_urls(result)
                if not urls:
                    print(f"  [fal] 결과에 이미지가 없음 (HTTP {r_status}): {result}")
                    break
                return urls
            if state in ("FAILED", "CANCELLED", "ERROR"):
                print(f"  [fal] 생성 실패: {info}")
                break
            print(f"  [fal] 대기 중... ({state})")
    return []


def main():
    if len(sys.argv) < 2:
        sys.exit("사용법: generate_portraits.py <작품>")
    spec_path = os.path.join("scripts", "portraits", f"{sys.argv[1]}.json")
    spec = json.load(open(spec_path, encoding="utf-8"))
    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY가 필요합니다 (GitHub Secrets).")
    os.makedirs(OUT_DIR, exist_ok=True)

    failed = []
    for person in spec["characters"]:
        pid, count = person["id"], int(person.get("count", 2))
        todo = [n for n in range(1, count + 1)
                if not os.path.exists(os.path.join(OUT_DIR, f"{pid}-{n}.png"))]
        if not todo:
            print(f"[{pid}] 이미 생성됨 — 재사용")
            continue
        print(f"[{pid}] {len(todo)}장 생성: {person['prompt'][:60]}…")
        urls = fal_image(key, person["prompt"], len(todo))
        if len(urls) < len(todo):
            failed.append(pid)
        for n, url in zip(todo, urls):
            path = os.path.join(OUT_DIR, f"{pid}-{n}.png")
            urllib.request.urlretrieve(url, path)
            print(f"  저장됨 → {path}")

    if failed:
        sys.exit(f"생성 실패 인물: {', '.join(failed)}")
    print("모든 초상 생성 완료")


if __name__ == "__main__":
    main()
