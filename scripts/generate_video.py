#!/usr/bin/env python3
"""붕어빵 가격 콩트 → 장면별 쇼츠 영상 생성 (Ark Seedance API).

사용법:
    export ARK_API_KEY=발급받은-키          # 절대 코드에 하드코딩하지 않기
    python3 scripts/generate_video.py

환경 변수:
    ARK_API_KEY      (필수) Ark API 키
    ARK_BASE_URL     기본값: https://ark.ap-southeast.bytepluses.com/api/v3
                     (Volcengine 중국 리전이면 https://ark.cn-beijing.volces.com/api/v3)
    ARK_VIDEO_MODEL  기본값: seedance-1-0-pro-250528
                     (Volcengine이면 doubao-seedance-1-0-pro-250528)

결과물은 out/ 폴더에 scene01.mp4, scene02.mp4 ... 로 저장된다.
"""

import json
import os
import sys
import time
import urllib.request

BASE_URL = os.environ.get("ARK_BASE_URL", "https://ark.ap-southeast.bytepluses.com/api/v3")
MODEL = os.environ.get("ARK_VIDEO_MODEL", "seedance-1-0-pro-250528")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "out")

# 장면별 텍스트-투-비디오 프롬프트. 9:16 세로(쇼츠), 장면당 5초.
# 생성 모델은 한글 자막 렌더링이 불안정하므로 자막은 편집 단계에서 얹는 것을 전제로,
# 여기서는 연기/구도 중심으로 프롬프트를 구성한다.
SCENES = [
    "한국 겨울 길거리 붕어빵 노점, 김이 모락모락 나는 붕어빵 틀, 손님(젊은 여성)이 다가와 가격을 묻고 "
    "포장마차 사장(중년 남성)이 능청스럽게 웃으며 대답하는 장면, 따뜻한 저녁 조명, 코미디 톤 --ratio 9:16 --duration 5",

    "붕어빵 노점 앞, 손님이 어이없다는 표정으로 웃음을 터뜨리고 사장이 진지한 척 손가락으로 손님 얼굴을 "
    "가리키며 다시 살펴보는 과장된 연기, 클로즈업 위주, 코미디 톤 --ratio 9:16 --duration 5",

    "붕어빵 사장이 활짝 웃으며 붕어빵을 봉투에 담아 건네고 손님이 크게 웃는 장면, 훈훈한 마무리 분위기, "
    "겨울 길거리 야경 보케 --ratio 9:16 --duration 5",

    "붕어빵 노점 사장이 카메라를 정면으로 보며 어깨를 으쓱하는 브이로그식 마무리 컷, 씁쓸하면서도 "
    "만족스러운 미소, 코미디 쇼츠 엔딩 느낌 --ratio 9:16 --duration 5",
]


def api(path, payload=None):
    key = os.environ.get("ARK_API_KEY")
    if not key:
        sys.exit("ARK_API_KEY 환경 변수가 필요합니다. (.env 참고 — 코드나 채팅에 키를 넣지 마세요)")
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST" if payload else "GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def generate_scene(index, prompt):
    task = api("/contents/generations/tasks", {
        "model": MODEL,
        "content": [{"type": "text", "text": prompt}],
    })
    task_id = task["id"]
    print(f"[scene {index:02d}] 작업 생성됨: {task_id}")

    while True:
        time.sleep(10)
        status = api(f"/contents/generations/tasks/{task_id}")
        state = status.get("status")
        if state == "succeeded":
            url = status["content"]["video_url"]
            path = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
            urllib.request.urlretrieve(url, path)
            print(f"[scene {index:02d}] 완료 → {path}")
            return path
        if state in ("failed", "cancelled"):
            sys.exit(f"[scene {index:02d}] 생성 실패: {status}")
        print(f"[scene {index:02d}] 대기 중... ({state})")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    paths = [generate_scene(i + 1, p) for i, p in enumerate(SCENES)]
    print("\n생성 완료. 클립 이어붙이기 (ffmpeg 필요):")
    print("  ls out/scene*.mp4 | sed \"s/^/file '/;s/$/'/\" > out/list.txt")
    print("  ffmpeg -f concat -safe 0 -i out/list.txt -c copy out/bungeoppang-skit.mp4")
    return paths


if __name__ == "__main__":
    main()
