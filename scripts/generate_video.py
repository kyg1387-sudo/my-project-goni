#!/usr/bin/env python3
"""붕어빵 가격 콩트 → 장면별 쇼츠 영상 생성.

Ark(Seedance)와 fal.ai를 모두 지원한다. ARK_API_KEY가 있으면 Ark의 두 리전
(BytePlus, Volcengine)을 차례로 시도하고, 실패하면 FAL_API_KEY로 fal.ai
Seedance에 폴백한다.

사용법:
    export ARK_API_KEY=... 또는 export FAL_API_KEY=...
    python3 scripts/generate_video.py

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

# 장면별 텍스트-투-비디오 프롬프트. 9:16 세로(쇼츠), 장면당 5초.
# 생성 모델은 한글 자막 렌더링이 불안정하므로 자막은 편집 단계에서 얹는 것을 전제로,
# 여기서는 연기/구도 중심으로 프롬프트를 구성한다.
# 캐릭터 일관성을 위해 사장/손님 고양이의 생김새 묘사를 모든 장면에 동일하게 반복한다.
SAJANG = "네이비색 야구모자를 삐딱하게 쓴 회색과 흰색 무늬의 귀여운 아기 고양이 사장님"
GOKAEK = "분홍 리본을 목에 맨 하얀 아기 고양이 손님"

SCENES = [
    f"한국 겨울 길거리 붕어빵 노점, 김이 모락모락 나는 붕어빵 틀, {GOKAEK}이 다가와 가격을 묻고 "
    f"{SAJANG}이 능청스럽게 웃으며 대답하는 장면, 실사풍, 따뜻한 저녁 조명, 코미디 톤",

    f"붕어빵 노점 앞, {GOKAEK}이 어이없다는 표정으로 웃음을 터뜨리고 {SAJANG}이 진지한 척 앞발로 "
    f"손님 얼굴을 가리키며 다시 살펴보는 과장된 연기, 실사풍, 클로즈업 위주, 코미디 톤",

    f"{SAJANG}이 활짝 웃으며 붕어빵을 봉투에 담아 건네고 {GOKAEK}이 크게 웃는 장면, 실사풍, "
    f"훈훈한 마무리 분위기, 겨울 길거리 야경 보케",

    f"{SAJANG}이 카메라를 정면으로 보며 혀를 살짝 내밀고 윙크하는 브이로그식 마무리 컷, 실사풍, "
    f"씁쓸하면서도 만족스러운 표정, 코미디 쇼츠 엔딩 느낌",
]


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


def ark_generate(base_url, model, key, index, prompt):
    headers = {"Authorization": f"Bearer {key}"}
    status, task = http_json(f"{base_url}/contents/generations/tasks", {
        "model": model,
        "content": [{"type": "text", "text": f"{prompt} --ratio 9:16 --duration 5"}],
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


def fal_generate(key, index, prompt):
    headers = {"Authorization": f"Key {key}"}
    status, task = http_json(f"https://queue.fal.run/{FAL_MODEL}", {
        "prompt": prompt,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        "duration": "5",
    }, headers)
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
            _, result = http_json(result_url, headers=headers)
            path = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
            download(result["video"]["url"], path)
            return path
        if state in ("FAILED", "CANCELLED", "ERROR"):
            print(f"  [fal] 생성 실패: {info}")
            return None
        print(f"  [fal] 대기 중... ({state})")


# ---------- 메인 ----------

def pick_provider():
    """실제로 첫 장면 생성에 성공하는 공급자 함수를 골라 돌려준다."""
    ark_key = os.environ.get("ARK_API_KEY")
    fal_key = os.environ.get("FAL_API_KEY")
    candidates = []
    if ark_key:
        override = os.environ.get("ARK_BASE_URL"), os.environ.get("ARK_VIDEO_MODEL")
        pairs = [override] if all(override) else ARK_CANDIDATES
        for base_url, model in pairs:
            candidates.append((f"ark {base_url} / {model}",
                               lambda i, p, b=base_url, m=model: ark_generate(b, m, ark_key, i, p)))
    if fal_key:
        candidates.append((f"fal.ai {FAL_MODEL}", lambda i, p: fal_generate(fal_key, i, p)))
    if not candidates:
        sys.exit("ARK_API_KEY 또는 FAL_API_KEY 환경 변수가 필요합니다. (키를 코드나 채팅에 넣지 마세요)")
    return candidates


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    paths = []
    provider = None
    for index, prompt in enumerate(SCENES, start=1):
        print(f"[scene {index:02d}] {prompt[:40]}...")
        if provider:
            path = provider(index, prompt)
            if not path:
                sys.exit(f"[scene {index:02d}] 생성 실패 — 위 로그를 확인하세요.")
        else:
            path = None
            for name, fn in pick_provider():
                print(f"  공급자 시도: {name}")
                path = fn(index, prompt)
                if path:
                    provider = fn
                    break
            if not path:
                sys.exit("모든 공급자에서 생성에 실패했습니다 — 위 로그를 확인하세요.")
        paths.append(path)

    print("\n생성 완료. 클립 이어붙이기 (ffmpeg 필요):")
    print("  ls out/scene*.mp4 | sed \"s/^/file '/;s/$/'/\" > out/list.txt")
    print("  ffmpeg -f concat -safe 0 -i out/list.txt -c copy out/bungeoppang-skit.mp4")
    return paths


if __name__ == "__main__":
    main()
