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
import shutil
import sys
import time
import urllib.error
import urllib.request

POLL_TIMEOUT_S = int(os.environ.get("POLL_TIMEOUT_S", "1800"))

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "out")
MIN_CLIP_BYTES = 20_000  # 이보다 작으면 깨진 파일로 본다(정지 타이틀 카드 클립은 100KB 미만일 수 있음)
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
            if int(scene.get("hero_takes") or 1) > 1:   # 히어로 컷: 같은 키프레임으로 N테이크(#02 B안, 편집에서 최고 테이크 선택)
                SCENE_TAKES[k + 1] = int(scene["hero_takes"])
        else:
            prompt, dur, refs = scene, base_dur, []
        override = os.path.join(OUT_DIR, f"scene{k + 1:02d}.mp4")  # 오버라이드 클립이 있으면 생성 안 함 → 길이 제한 없음
        has_override = os.path.exists(override) and os.path.getsize(override) > MIN_CLIP_BYTES
        if image and not os.path.exists(image) and not has_override \
                and not (isinstance(scene, dict) and scene.get("override_required")):
            # 교체 클립이 있으면 키프레임이 없어도 된다(정지 푸시인·재사용 컷)
            sys.exit(f"[scene {k + 1:02d}] 키프레임 파일이 없습니다: {image}")
        if dur not in (5, 10) and not has_override:
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
    deadline = time.time() + POLL_TIMEOUT_S  # 무한 대기 방지(잡 타임아웃까지 상태를 모르는 일 차단)
    while True:
        if time.time() > deadline:
            print(f"  [poll] {POLL_TIMEOUT_S}초 안에 끝나지 않아 중단합니다 — 같은 작업을 다시 제출하지 말고 fal 대시보드에서 상태를 확인하세요.")
            return None
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
    deadline = time.time() + POLL_TIMEOUT_S  # 무한 대기 방지(잡 타임아웃까지 상태를 모르는 일 차단)
    while True:
        if time.time() > deadline:
            print(f"  [poll] {POLL_TIMEOUT_S}초 안에 끝나지 않아 중단합니다 — 같은 작업을 다시 제출하지 말고 fal 대시보드에서 상태를 확인하세요.")
            return None
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
SCENE_TAKES = {}  # 장면 번호 → 테이크 수(히어로 컷)


KLING_NEGATIVE = ("blur, distortion, morphing faces, extra people, extra fingers, text, letters, watermark, "
                  "fast motion, spinning, running, dramatic body movement")


def fal_generate_i2v(key, index, prompt, duration, ratio, image_url, out_path=None):
    """승인 키프레임 1장을 첫 프레임으로 고정해 영상을 만든다(규격서 PHASE 5: Text-to-Video 금지).
    모델별 파라미터 차이를 흡수하기 위해 페이로드를 순서대로 시도한다. out_path가 있으면 그 파일로 저장(히어로 테이크)."""
    headers = {"Authorization": f"Key {key}"}
    m, r = SCENE_I2V.get(index, (None, None))
    model, res = m or FAL_I2V_MODEL, r or I2V_RESOLUTION
    base = {"prompt": prompt, "image_url": image_url, "duration": str(duration), "resolution": res}
    print(f"  [fal i2v] {model} {res}")
    if "kling" in model:   # Kling(fal): #02 파일럿 실증 — resolution·aspect_ratio를 포함한 일반 페이로드도 수락됨. 네거티브·cfg를 더한다
        payloads = [dict(base, aspect_ratio=ratio, negative_prompt=KLING_NEGATIVE, cfg_scale=0.5),
                    dict(base, aspect_ratio=ratio), base,
                    {"prompt": prompt, "image_url": image_url, "duration": str(duration)}]
    else:
        payloads = [dict(base, aspect_ratio=ratio), base,
                    {"prompt": prompt, "image_url": image_url, "duration": str(duration)}]
    for payload in payloads:
        status, task = http_json(f"https://queue.fal.run/{model}", payload, headers)
        if status != 200:
            print(f"  [fal i2v] 작업 생성 실패 (HTTP {status}): {task} — 다른 파라미터로 재시도")
            continue
        status_url, result_url = task["status_url"], task["response_url"]
        print(f"  [fal i2v] 작업 생성됨: {task['request_id']}")
        deadline = time.time() + POLL_TIMEOUT_S  # 무한 대기 방지(잡 타임아웃까지 상태를 모르는 일 차단)
        while True:
            if time.time() > deadline:
                print(f"  [poll] {POLL_TIMEOUT_S}초 안에 끝나지 않아 중단합니다 — 같은 작업을 다시 제출하지 말고 fal 대시보드에서 상태를 확인하세요.")
                return None
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
                path = out_path or os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
                download(url, path)
                return path
            if state in ("FAILED", "CANCELLED", "ERROR"):
                print(f"  [fal i2v] 생성 실패: {info}")
                break
            print(f"  [fal i2v] 대기 중... ({state})")
    return None


def recover_requests(key):
    """fal 큐에서 이미 COMPLETED된 요청을 내려받기만 한다(재과금 없음) — env FAL_RECOVER="01:request_id,03:request_id".
    #02 파일럿 실증: 생성은 끝났는데 내려받기 코드 오류로 클립을 잃은 경우의 무료 회수 경로(제7장 9)."""
    spec = os.environ.get("FAL_RECOVER", "").strip()
    if not spec:
        return
    if not key:
        sys.exit("FAL_RECOVER에는 FAL_API_KEY가 필요합니다.")
    headers = {"Authorization": f"Key {key}"}
    for item in spec.split(","):
        idx, _, rid = item.strip().partition(":")
        index = int(idx)
        m, _r = SCENE_I2V.get(index, (None, None)); model = m or FAL_I2V_MODEL
        parts = model.split("/")
        cands = [f"https://queue.fal.run/{'/'.join(parts[:2])}/requests/{rid}", f"https://queue.fal.run/{model}/requests/{rid}"]
        got = None
        for url in cands:
            st, res = http_json(url, headers=headers)
            if st == 200 and isinstance(res, dict) and isinstance(res.get("video"), dict) and res["video"].get("url"):
                got = res["video"]["url"]; break
            print(f"  [recover {index:02d}] {url} → HTTP {st}")
        if not got:
            sys.exit(f"[recover {index:02d}] 요청 {rid} 결과를 찾지 못했습니다(만료 또는 잘못된 id).")
        path = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
        download(got, path)
        if SCENE_TAKES.get(index, 1) > 1:
            shutil.copy(path, os.path.join(OUT_DIR, f"scene{index:02d}_take1.mp4"))
        print(f"  [recover {index:02d}] 회수 완료(재과금 없음)")


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


I2V_RATE_USD = {"pro": 0.108, "lite": 0.036, "kling": 0.112}  # 2026-10-04 fal 잔액 차이 실측(제작규격-보강-EP4 §1); kling 3.0 pro = 공시 단가(첫 실행에서 실측)


def preflight(scenes_file, scenes):
    """유료 생성 전에 비용을 추산하고 위험한 경로를 막는다(무료).

    - override_required 장면(정지 푸시인·재사용·카드)에 교체 클립이 없으면 중단 → 유료 i2v/t2v로 새는 일 차단
    - 키프레임 없는 장면(t2v)은 규격서 PHASE 5-1에 따라 기본 금지(allow_t2v: true일 때만 허용)
    - budget_usd를 넘는 추산이면 중단
    """
    with open(scenes_file, encoding="utf-8") as f:
        data = json.load(f)
    raw = data["scenes"]
    missing, t2v, cost, paid = [], [], 0.0, 0
    for index, (prompt, duration, refs, image) in enumerate(scenes, start=1):
        existing = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
        if os.path.exists(existing) and os.path.getsize(existing) > MIN_CLIP_BYTES:
            continue
        spec = raw[index - 1] if isinstance(raw[index - 1], dict) else {}
        if spec.get("override_required"):
            missing.append(index)
            continue
        if not image:
            t2v.append(index)
        model, res = SCENE_I2V.get(index, (None, None))
        model, res = model or FAL_I2V_MODEL, res or I2V_RESOLUTION
        tier = "kling" if "kling" in model else ("lite" if "lite" in model else "pro")
        takes = SCENE_TAKES.get(index, 1)
        existing_takes = sum(1 for t in range(1, takes + 1)
                             if os.path.exists(os.path.join(OUT_DIR, f"scene{index:02d}_take{t}.mp4")))
        cost += duration * I2V_RATE_USD[tier] * max(0, takes - existing_takes)
        paid += 1
    if missing:
        sys.exit("교체 클립이 필요한 장면에 파일이 없습니다(유료 생성으로 새는 것 차단): "
                 + " ".join(f"scene{i:02d}" for i in missing)
                 + " — assets/video-overrides/<skit>/에 정지 푸시인 등을 먼저 넣으세요.")
    if t2v and not data.get("allow_t2v"):
        sys.exit("키프레임 없는 장면(t2v)은 금지입니다: " + " ".join(f"scene{i:02d}" for i in t2v)
                 + " — image를 지정하거나 의도한 경우만 allow_t2v: true")
    n_takes = sum(SCENE_TAKES.get(i, 1) for i in range(1, len(scenes) + 1) if i in SCENE_TAKES)
    print(f"[비용 추산] 새로 생성할 장면 {paid}개(히어로 테이크 {n_takes}개 포함), 약 {cost:.2f}달러 "
          f"(실측 단가 pro 0.108/s, lite 0.036/s, kling 0.112/s)")
    budget = data.get("budget_usd")
    if budget is not None and cost > float(budget) + 1e-9:
        sys.exit(f"추산 {cost:.2f}달러가 budget_usd {float(budget):.2f}달러를 넘어 중단합니다.")


def main():
    scenes_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SCENES_FILE
    scenes, ratio = load_scenes(scenes_file)
    print(f"장면 파일: {scenes_file} ({len(scenes)}개 장면, 화면비 {ratio})")

    os.makedirs(OUT_DIR, exist_ok=True)
    recover_requests(os.environ.get("FAL_API_KEY"))
    preflight(scenes_file, scenes)
    paths = []
    provider = None
    fal_key = os.environ.get("FAL_API_KEY")
    for index, (prompt, duration, refs, image) in enumerate(scenes, start=1):
        existing = os.path.join(OUT_DIR, f"scene{index:02d}.mp4")
        if os.path.exists(existing) and os.path.getsize(existing) > MIN_CLIP_BYTES:
            print(f"[scene {index:02d}] 기존 파일 재사용 (이어하기)")
            paths.append(existing)
            continue
        print(f"[scene {index:02d}] ({duration}s) {prompt[:40]}...")
        if image:
            # 규격서 PHASE 5-1: 승인 키프레임만 Image-to-Video로 변환
            if not fal_key:
                sys.exit("image(키프레임)가 있는 장면에는 FAL_API_KEY가 필요합니다.")
            img_url = fal_upload(fal_key, image)
            takes = SCENE_TAKES.get(index, 1)
            if takes > 1:   # 히어로 컷: scene{NN}_take{k}.mp4로 N테이크, 1번 테이크를 기본 클립으로(편집에서 교체)
                path = None
                for t in range(1, takes + 1):
                    tp = os.path.join(OUT_DIR, f"scene{index:02d}_take{t}.mp4")
                    if os.path.exists(tp) and os.path.getsize(tp) > MIN_CLIP_BYTES:
                        print(f"  [take {t}/{takes}] 기존 파일 재사용")
                    else:
                        print(f"  [take {t}/{takes}] 생성")
                        if not fal_generate_i2v(fal_key, index, prompt, duration, ratio, img_url, out_path=tp):
                            sys.exit(f"[scene {index:02d}] 테이크 {t} 생성 실패 — 위 로그를 확인하세요.")
                    path = path or tp
                shutil.copy(path, existing)
                paths.append(existing)
                continue
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
