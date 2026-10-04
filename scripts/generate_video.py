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
    FAL_I2V_MODEL                  기본값: fal-ai/bytedance/seedance/v1/lite/image-to-video (장면에 image가 있을 때)

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
    또는 {"prompt": ..., "duration": 5|10} 객체를 섞어 쓸 수 있다. 최상위 "durations"
    배열(장면 수와 같은 길이, EP3 형식)이 있으면 그 값이 장면별 기본 길이가 된다.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    style = data.get("style", "").strip()
    global FAL_I2V_MODEL, I2V_RESOLUTION
    FAL_I2V_MODEL = data.get("i2v_model") or FAL_I2V_MODEL  # 장면 파일에서 i2v 모델·해상도 지정(예: seedance pro 1080p)
    I2V_RESOLUTION = data.get("i2v_resolution") or I2V_RESOLUTION
    default_dur = int(data.get("duration", 5))
    durations = data.get("durations")
    if durations is not None and len(durations) != len(data["scenes"]):
        sys.exit(f"durations 길이({len(durations)})가 scenes 길이({len(data['scenes'])})와 다릅니다.")
    items = []
    for k, scene in enumerate(data["scenes"]):
        base_dur = int(durations[k]) if durations is not None else default_dur
        image = None
        if isinstance(scene, dict):
            prompt, dur = scene["prompt"], int(scene.get("duration", base_dur))
            refs = scene.get("refs") or []
            image = scene.get("image")  # 규격서 PHASE 5: 승인 키프레임 → Image-to-Video
            if scene.get("i2v_model") or scene.get("i2v_resolution"):  # 장면별 화질(예: 인물 컷만 pro 1080p)
                SCENE_I2V[k + 1] = (scene.get("i2v_model") or None, scene.get("i2v_resolution") or None)
            if image and not os.path.exists(image):
                sys.exit(f"[scene {k + 1:02d}] 키프레임 파일이 없습니다: {image}")
        else:
            prompt, dur, refs = scene, base_dur, []
        override = os.path.join(OUT_DIR, f"scene{k + 1:02d}.mp4")  # 오버라이드 클립이 있으면 생성 안 함 → 길이 제한 없음
        if dur not in (5, 10) and not (os.path.exists(override) and os.path.getsize(override) > 100_000):
            sys.exit(f"[scene {k + 1:02d}] 지원하지 않는 길이 {dur}초 — Seedance는 5 또는 10초만 지원합니다.")
        items.append((f"{prompt}, {style}" if style else prompt, dur, refs, image))
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
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        # 접속 실패/시간 초과 — 호출자가 다음 공급자로 넘어갈 수 있게 오류로 돌려준다
        return 0, f"접속 실패: {e}"


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
        state = info.get("status") if isinstance(info, dict) else None
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
        state = info.get("status") if isinstance(info, dict) else None
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


FAL_I2V_MODEL = os.environ.get("FAL_I2V_MODEL", "fal-ai/bytedance/seedance/v1/lite/image-to-video")
I2V_RESOLUTION = "720p"
SCENE_I2V = {}  # 장면 번호 → (모델, 해상도) 개별 지정


def fal_generate_i2v(key, index, prompt, duration, ratio, image_url):
    """승인 키프레임 1장을 첫 프레임으로 고정해 영상을 만든다(규격서 PHASE 5: Text-to-Video 금지).
    모델별 파라미터 차이를 흡수하기 위해 페이로드를 순서대로 시도한다."""
    headers = {"Authorization": f"Key {key}"}
    m, r = SCENE_I2V.get(index, (None, None))
    model, res = m or FAL_I2V_MODEL, r or I2V_RESOLUTION
    base = {"prompt": prompt, "image_url": image_url, "duration": str(duration), "resolution": res}
    print(f"  [fal i2v] {model} {res}")
    payloads = [dict(base, aspect_ratio=ratio), base,
                {"prompt": prompt, "image_url": image_url, "duration": str(duration)}]
    for payload in payloads:
        status, task = http_json(f"https://queue.fal.run/{model}", payload, headers)
        if status != 200:
            print(f"  [fal i2v] 작업 생성 실패 (HTTP {status}): {task} — 다른 파라미터로 재시도")
            continue
        status_url, result_url = task["status_url"], task["response_url"]
        print(f"  [fal i2v] 작업 생성됨: {task['request_id']}")
        while True:
            time.sleep(10)
            _, info = http_json(status_url, headers=headers)
            state = info.get("status") if isinstance(info, dict) else None
            if state == "COMPLETED":
                r_status, result = http_json(result_url, headers=headers)
                url = None
                if isinstance(result, dict) and isinstance(result.get("video"), dict):
                    url = result["video"].get("url")
                if not url:
                    print(f"  [fal i2v] 결과에 영상이 없음 (HTTP {r_status}): {result}")
                    return None
                path = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
                download(url, path)
                return path
            if state in ("FAILED", "CANCELLED", "ERROR"):
                print(f"  [fal i2v] 생성 실패: {info}")
                break
            print(f"  [fal i2v] 대기 중... ({state})")
    return None


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
    for index, (prompt, duration, refs, image) in enumerate(scenes, start=1):
        existing = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
        if os.path.exists(existing) and os.path.getsize(existing) > 100_000:
            print(f"[scene {index:02d}] 기존 파일 재사용 (이어하기)")
            paths.append(existing)
            continue
        print(f"[scene {index:02d}] ({duration}s) {prompt[:40]}...")
        if image:
            # 규격서 PHASE 5-1: 승인 키프레임만 Image-to-Video로 변환
            if not fal_key:
                sys.exit("image(키프레임)가 있는 장면에는 FAL_API_KEY가 필요합니다.")
            img_url = fal_upload(fal_key, image)
            path = fal_generate_i2v(fal_key, index, prompt, duration, ratio, img_url)
            if not path:
                sys.exit(f"[scene {index:02d}] 생성 실패 — 위 로그를 확인하세요.")
            paths.append(path)
            continue
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
