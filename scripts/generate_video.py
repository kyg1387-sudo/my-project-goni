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

# 장면별 텍스트-투-비디오 프롬프트. 9:16 세로(쇼츠), 숏당 5초 생성 후 편집 단계에서 앞 2초씩
# 잘라 이어붙인다(스토리보드 SEQ 003의 2초 컷 리듬 재현). 생성 모델은 한글 자막 렌더링이
# 불안정하므로 자막은 편집 단계에서 얹는 것을 전제로, 연기/구도 중심으로 프롬프트를 구성한다.
# 캐릭터 일관성을 위해 사장/손님과 배경 묘사를 모든 숏에 동일하게 반복한다.
SAJANG = ("흰색 LA 로고가 수놓인 네이비 야구모자를 쓰고 데님 멜빵바지에 크림색 스웨터를 입은 실사풍 "
          "갈색 줄무늬 고양이 붕어빵 노점 사장님")
GOKAEK = "긴 갈색 머리에 베이지색 니트와 코트를 입은 여성 손님(얼굴은 프레임에 나오지 않음)"
BG = ("밤의 한국 길거리 붕어빵 노점, 나무 간판에 한글로 '붕어빵'이라고 크게 적혀 있고 물고기 그림이 "
      "그려져 있음, 메뉴판에는 한글로 '팥 2,000'과 '슈크림 2,000'이 적혀 있음, 작은 팻말에 한글로 "
      "'따끈따끈 맛있어요'라고 적혀 있음, 화면의 모든 글자는 정확한 한글로만 표기하고 영어 알파벳이나 "
      "다른 문자는 절대 없음, 따뜻한 전구 조명 줄, 김이 모락모락 피어오름, 시네마틱 조명, 실사풍")

SCENES = [
    f"{BG}. 클로즈업: {SAJANG}이 카메라를 향해 입을 움직이며 능청스럽게 말을 시작하는 장면",

    f"{BG}. 미디엄샷: {SAJANG}이 한쪽 눈을 윙크하며 앞발로 화면 밖 손님을 가리키며 "
    f"펀치라인을 날리는 장면, 코미디 톤",

    f"{BG}. 클로즈업: {GOKAEK}이 손으로 입을 가리고 어깨를 들썩이며 웃음을 터뜨리는 장면, "
    f"얼굴은 프레임 밖, 뒤로 노점 보케",

    f"{BG}. 미디엄샷: {SAJANG}의 앞발이 물고기 그림이 그려진 따뜻한 종이봉투를 "
    f"{GOKAEK}의 기다리는 두 손에 건네주는 장면",

    f"{BG}. 와이드샷: {GOKAEK}이 종이봉투를 안고 돌아서기 시작하고, 노점에서 김이 피어오르고 "
    f"전구 조명 줄이 빛나는 장면, {SAJANG}이 노점 뒤에 서 있음",

    f"{BG}. 와이드샷: {GOKAEK}의 뒷모습이 봉투를 들고 거리를 걸어가고, {SAJANG}이 노점에서 "
    f"손을 흔들며 배웅하는 따뜻한 여운의 마지막 장면",
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
