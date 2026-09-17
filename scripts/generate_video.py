#!/usr/bin/env python3
"""콩트/드라마 대본 → 장면별 쇼츠 영상 생성.

Ark(Seedance)와 fal.ai를 모두 지원한다. ARK_API_KEY가 있으면 Ark의 두 리전
(BytePlus, Volcengine)을 차례로 시도하고, 실패하면 FAL_API_KEY로 fal.ai
Seedance에 폴백한다.

사용법:
    export ARK_API_KEY=... 또는 export FAL_API_KEY=...
    python3 scripts/generate_video.py [scripts/scenes/<스킷>.json]

장면 파일(JSON) 형식:
    duration  장면당 길이(초). 5 또는 10. 생략 시 5
    style     모든 장면 프롬프트 뒤에 붙는 공통 지시문(인물/의상/장소 일관성 유지용)
    scenes    장면별 프롬프트 목록 — 같은 인물은 매 장면 동일한 외형 문구로 묘사할 것

환경 변수(선택):
    ARK_BASE_URL, ARK_VIDEO_MODEL  Ark 엔드포인트/모델 직접 지정
    FAL_VIDEO_MODEL                기본값: fal-ai/bytedance/seedance/v1/lite/text-to-video

결과물은 out/ 폴더에 scene01.mp4, scene02.mp4 ... 로 저장된다.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "out")
DEFAULT_SCENES_FILE = os.path.join(os.path.dirname(__file__), "scenes", "bungeoppang.json")


def load_scenes(path):
    """장면 파일을 읽어 ([(프롬프트, 길이초)], 화면비)를 돌려준다.

    생성 모델은 한글 자막 렌더링이 불안정하므로 자막은 편집 단계에서 얹는 것을 전제로,
    프롬프트는 연기/구도 중심으로 구성한다. style은 인물/의상/장소 일관성을 위해
    모든 장면 프롬프트 뒤에 공통으로 붙인다. scenes 항목은 문자열(전역 duration 사용)
    또는 {"prompt": ..., "duration": 5|10} 객체를 섞어 쓸 수 있다.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    style = data.get("style", "").strip()
    default_dur = int(data.get("duration", 5))
    items = []
    for scene in data["scenes"]:
        if isinstance(scene, dict):
            prompt, dur = scene["prompt"], int(scene.get("duration", default_dur))
            refs = scene.get("refs") or []
        else:
            prompt, dur, refs = scene, default_dur, []
        items.append((f"{prompt}, {style}" if style else prompt, dur, refs))
    return items, data.get("ratio", "9:16")


def http_json(url, payload=None, headers=None):
    """JSON 요청을 보내고 (status, body dict)를 돌려준다. HTTP 오류도 본문을 읽어 반환."""
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


def download(url, path):
    urllib.request.urlretrieve(url, path)
    print(f"  저장됨 → {path}")


# ---------- Ark (BytePlus / Volcengine) ----------

ARK_CANDIDATES = [
    ("https://ark.ap-southeast.bytepluses.com/api/v3", "seedance-1-0-pro-250528"),
    ("https://ark.cn-beijing.volces.com/api/v3", "doubao-seedance-1-0-pro-250528"),
]


def ark_generate(base_url, model, key, index, prompt, duration, ratio):
    headers = {"Authorization": f"Bearer {key}"}
    status, task = http_json(f"{base_url}/contents/generations/tasks", {
        "model": model,
        "content": [{"type": "text", "text": f"{prompt} --ratio {ratio} --duration {duration}"}],
    }, headers)
    if status != 200:
        print(f"  [ark] 작업 생성 실패 (HTTP {status}): {task}")
        return None
    task_id = task["id"]
    print(f"  [ark] 작업 생성됨: {task_id}")
    while True:
        time.sleep(10)
        status, info = http_json(f"{base_url}/contents/generations/tasks/{task_id}", headers=headers)
        state = info.get("status")
        if state == "succeeded":
            path = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
            download(info["content"]["video_url"], path)
            return path
        if state in ("failed", "cancelled"):
            print(f"  [ark] 생성 실패: {info}")
            return None
        print(f"  [ark] 대기 중... ({state})")


# ---------- fal.ai ----------

FAL_MODEL = os.environ.get("FAL_VIDEO_MODEL", "fal-ai/bytedance/seedance/v1/lite/text-to-video")
# 기준 초상(참조 이미지) 기반 생성 — 인물 일관성 유지 (refs가 있는 장면에 사용)
FAL_REF_MODEL = os.environ.get("FAL_REF_MODEL", "fal-ai/bytedance/seedance/v1/lite/reference-to-video")

_upload_cache = {}


def fal_upload(key, path):
    """로컬 참조 이미지를 fal 스토리지에 올리고 URL을 돌려준다 (파일별 1회)."""
    if path in _upload_cache:
        return _upload_cache[path]
    headers = {"Authorization": f"Key {key}"}
    status, init = http_json("https://rest.fal.ai/storage/upload/initiate", {
        "file_name": os.path.basename(path),
        "content_type": "image/png",
    }, headers)
    if status != 200 or "upload_url" not in init:
        sys.exit(f"fal 스토리지 업로드 시작 실패 (HTTP {status}): {init}")
    req = urllib.request.Request(init["upload_url"], data=open(path, "rb").read(),
                                 headers={"Content-Type": "image/png"}, method="PUT")
    with urllib.request.urlopen(req, timeout=120) as resp:
        if resp.status not in (200, 201, 204):
            sys.exit(f"fal 스토리지 업로드 실패 (HTTP {resp.status})")
    _upload_cache[path] = init["file_url"]
    print(f"  참조 이미지 업로드: {path}")
    return init["file_url"]


def fal_generate(key, index, prompt, duration, ratio, ref_urls=None):
    headers = {"Authorization": f"Key {key}"}
    model = FAL_REF_MODEL if ref_urls else FAL_MODEL
    payload = {
        "prompt": prompt,
        "aspect_ratio": ratio,
        "resolution": "720p",
        "duration": str(duration),
    }
    if ref_urls:
        payload["reference_image_urls"] = ref_urls
    status, task = http_json(f"https://queue.fal.run/{model}", payload, headers)
    if status != 200:
        print(f"  [fal] 작업 생성 실패 (HTTP {status}): {task}")
        return None
    status_url, result_url = task["status_url"], task["response_url"]
    print(f"  [fal] 작업 생성됨: {task['request_id']}")
    while True:
        time.sleep(10)
        _, info = http_json(status_url, headers=headers)
        state = info.get("status")
        if state == "COMPLETED":
            r_status, result = http_json(result_url, headers=headers)
            url = None
            if isinstance(result, dict):
                video = result.get("video")
                if isinstance(video, dict):
                    url = video.get("url")
            if not url:
                # 완료로 표시됐지만 결과에 영상이 없는 경우(잔액/정책/파라미터 오류 등)
                print(f"  [fal] 결과에 영상이 없음 (HTTP {r_status}): {result}")
                return None
            path = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
            download(url, path)
            return path
        if state in ("FAILED", "CANCELLED", "ERROR"):
            print(f"  [fal] 생성 실패: {info}")
            return None
        print(f"  [fal] 대기 중... ({state})")


# ---------- 메인 ----------

def pick_provider(ratio):
    """실제로 첫 장면 생성에 성공하는 공급자 함수를 골라 돌려준다."""
    ark_key = os.environ.get("ARK_API_KEY")
    fal_key = os.environ.get("FAL_API_KEY")
    candidates = []
    if ark_key:
        override = os.environ.get("ARK_BASE_URL"), os.environ.get("ARK_VIDEO_MODEL")
        pairs = [override] if all(override) else ARK_CANDIDATES
        for base_url, model in pairs:
            candidates.append((f"ark {base_url} / {model}",
                               lambda i, p, d, b=base_url, m=model: ark_generate(b, m, ark_key, i, p, d, ratio)))
    if fal_key:
        candidates.append((f"fal.ai {FAL_MODEL}", lambda i, p, d: fal_generate(fal_key, i, p, d, ratio)))
    if not candidates:
        sys.exit("ARK_API_KEY 또는 FAL_API_KEY 환경 변수가 필요합니다. (키를 코드나 채팅에 넣지 마세요)")
    return candidates


def main():
    scenes_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SCENES_FILE
    scenes, ratio = load_scenes(scenes_file)
    print(f"장면 파일: {scenes_file} ({len(scenes)}개 장면, 화면비 {ratio})")

    os.makedirs(OUT_DIR, exist_ok=True)
    paths = []
    provider = None
    fal_key = os.environ.get("FAL_API_KEY")
    for index, (prompt, duration, refs) in enumerate(scenes, start=1):
        existing = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
        if os.path.exists(existing) and os.path.getsize(existing) > 100_000:
            print(f"[scene {index:02d}] 기존 파일 재사용 (이어하기)")
            paths.append(existing)
            continue
        print(f"[scene {index:02d}] ({duration}s) {prompt[:40]}...")
        if refs:
            # 기준 초상 기반 장면 — 인물 일관성을 위해 fal 참조 모델을 사용
            if not fal_key:
                sys.exit("refs가 있는 장면에는 FAL_API_KEY가 필요합니다.")
            ref_urls = [fal_upload(fal_key, r) for r in refs]
            path = fal_generate(fal_key, index, prompt, duration, ratio, ref_urls)
            if not path:
                sys.exit(f"[scene {index:02d}] 생성 실패 — 위 로그를 확인하세요.")
            paths.append(path)
            continue
        if provider:
            path = provider(index, prompt, duration)
            if not path:
                sys.exit(f"[scene {index:02d}] 생성 실패 — 위 로그를 확인하세요.")
        else:
            path = None
            for name, fn in pick_provider(ratio):
                print(f"  공급자 시도: {name}")
                path = fn(index, prompt, duration)
                if path:
                    provider = fn
                    break
            if not path:
                sys.exit("모든 공급자에서 생성에 실패했습니다 — 위 로그를 확인하세요.")
        paths.append(path)

    print("\n생성 완료. 클립 이어붙이기 (ffmpeg 필요):")
    print("  ls out/scene*.mp4 | sed \"s/^/file '/;s/$/'/\" > out/list.txt")
    print("  ffmpeg -f concat -safe 0 -i out/list.txt -c copy out/<스킷>-skit.mp4")
    return paths


if __name__ == "__main__":
    main()
