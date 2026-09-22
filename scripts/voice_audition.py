#!/usr/bin/env python3
"""목소리 오디션 생성기.

scripts/auditions/<작품>.json 의 시험 목록(배역 후보 목소리 × 핵심 감정 대사)을
읽어 TTS 샘플을 생성한다. out/audition/<id>.mp3 가 있으면 재사용한다.
본편 제작 전 사용자가 듣고 배역을 확정하기 위한 것 (감정표현력 기준).

사용법: python scripts/voice_audition.py <작품>   (FAL_API_KEY 필요)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

OUT_DIR = os.environ.get("AUDITION_OUT_DIR", "out/audition")


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


def find_audio_url(result):
    if not isinstance(result, dict):
        return None
    for k in ("audio", "audio_file", "audio_url"):
        v = result.get(k)
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
        if isinstance(v, str) and v.startswith("http"):
            return v
    return None


def fal_run(model, payload, key, tag):
    headers = {"Authorization": f"Key {key}"}
    status, task = http_json(f"https://queue.fal.run/{model}", payload, headers)
    if status != 200:
        print(f"  [{tag}] 작업 생성 실패 (HTTP {status}): {task}")
        return None
    while True:
        time.sleep(4)
        _, info = http_json(task["status_url"], headers=headers)
        state = info.get("status")
        if state == "COMPLETED":
            _, result = http_json(task["response_url"], headers=headers)
            return result
        if state in ("FAILED", "CANCELLED", "ERROR"):
            print(f"  [{tag}] 생성 실패: {info}")
            return None


def el_request(method, url, key, payload=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json", "xi-api-key": key},
        method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:300]


def el_resolve_voice(name, key, _cache={}):
    """이름으로 ElevenLabs 목소리 ID를 찾는다: 내 목소리 → 도서관 검색+추가 순."""
    if name in _cache:
        return _cache[name]
    import urllib.parse
    status, data = el_request("GET", "https://api.elevenlabs.io/v1/voices", key)
    if status == 200 and isinstance(data, dict):
        for v in data.get("voices", []):
            if (v.get("name") or "").lower().startswith(name.lower()):
                print(f"  내 목소리에서 발견: {v['name']} → {v['voice_id']}")
                _cache[name] = v["voice_id"]
                return v["voice_id"]
    status, data = el_request(
        "GET", "https://api.elevenlabs.io/v1/shared-voices?page_size=12&search="
        + urllib.parse.quote(name), key)
    if status != 200 or not isinstance(data, dict):
        print(f"  도서관 검색 실패 (HTTP {status}): {data}")
        return None
    for v in data.get("voices", []):
        if not (v.get("name") or "").lower().startswith(name.lower()):
            continue
        vid, owner = v["voice_id"], v.get("public_owner_id")
        print(f"  도서관에서 발견: {v['name']} | id={vid}")
        a_status, added = el_request(
            "POST", f"https://api.elevenlabs.io/v1/voices/add/{owner}/{vid}",
            key, {"new_name": name})
        if a_status == 200 and isinstance(added, dict):
            use_id = added.get("voice_id", vid)
            print(f"  내 목소리에 추가됨 → {use_id}")
            _cache[name] = use_id
            return use_id
        print(f"  내 목소리 추가 실패 (HTTP {a_status}): {added} — 원본 ID로 시도")
        _cache[name] = vid
        return vid
    print(f"  '{name}' 목소리를 찾지 못했습니다.")
    return None


def el_child_search(cfg):
    """ElevenLabs 목소리 도서관에서 어린 남자아이 목소리를 검색해 후보 샘플을 만든다."""
    key = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    if not key:
        sys.exit("ELEVENLABS_API_KEY 시크릿이 필요합니다.")
    os.makedirs(OUT_DIR, exist_ok=True)
    text = cfg["text"]
    seen, picks = set(), []
    for q in cfg.get("queries", ["korean boy child", "boy kid", "child"]):
        import urllib.parse
        status, data = el_request(
            "GET",
            "https://api.elevenlabs.io/v1/shared-voices?page_size=12&search="
            + urllib.parse.quote(q), key)
        if status != 200:
            print(f"[검색 '{q}'] 실패 (HTTP {status}): {data}")
            continue
        for v in data.get("voices", []):
            vid = v.get("voice_id")
            if not vid or vid in seen:
                continue
            gender = (v.get("gender") or "").lower()
            age = (v.get("age") or "").lower()
            if gender and gender != "male":
                continue
            if age and age not in ("young", "child"):
                continue
            seen.add(vid)
            picks.append(v)
    picks = picks[:4]
    if not picks:
        sys.exit("도서관 검색 결과가 없습니다.")
    failed = []
    for i, v in enumerate(picks, 1):
        name = v.get("name", f"voice{i}")
        vid, owner = v["voice_id"], v.get("public_owner_id")
        print(f"[후보{i}] {name} | id={vid} | age={v.get('age')} lang={v.get('language')} "
              f"| use_case={v.get('use_case')}")
        path = os.path.join(OUT_DIR, f"EL아이후보{i}-{name[:20]}.mp3")
        added_status, added = el_request(
            "POST", f"https://api.elevenlabs.io/v1/voices/add/{owner}/{vid}",
            key, {"new_name": f"minho-cand-{i}"})
        if added_status == 200 and isinstance(added, dict):
            use_id = added.get("voice_id", vid)
            t_status = None
            for model in ("eleven_v3", "eleven_multilingual_v2"):
                req = urllib.request.Request(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{use_id}",
                    data=json.dumps({"text": text, "model_id": model}).encode(),
                    headers={"Content-Type": "application/json", "xi-api-key": key},
                    method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        open(path, "wb").write(resp.read())
                    print(f"  생성됨 ({model}) → {path}")
                    t_status = 200
                    break
                except urllib.error.HTTPError as e:
                    t_status = e.code
                    print(f"  [{model}] 오류 (HTTP {e.code}): {e.read().decode(errors='replace')[:200]}")
            if t_status != 200:
                failed.append(name)
        else:
            print(f"  내 목소리 추가 실패 (HTTP {added_status}): {added} — 미리듣기로 대체")
            prev = v.get("preview_url")
            if prev:
                urllib.request.urlretrieve(prev, path)
                print(f"  미리듣기 저장 → {path}")
            else:
                failed.append(name)
    if failed:
        print(f"실패: {', '.join(failed)}")
    print("어린이 목소리 후보 탐색 완료")


def main():
    if len(sys.argv) < 2:
        sys.exit("사용법: voice_audition.py <작품>")
    spec = json.load(open(os.path.join("scripts", "auditions", f"{sys.argv[1]}.json"),
                          encoding="utf-8"))
    if spec.get("el_child_search"):
        el_child_search(spec["el_child_search"])
        return
    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY가 필요합니다.")
    os.makedirs(OUT_DIR, exist_ok=True)
    failed = []
    for t in spec["tests"]:
        path = os.path.join(OUT_DIR, f"{t['id']}.mp3")
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            print(f"[{t['id']}] 기존 파일 재사용")
            continue
        model = t.get("model", spec.get("tts_model", "fal-ai/minimax/speech-02-hd"))
        if model == "elevenlabs-direct":
            # 사용자 본인 ElevenLabs 계정의 보이스(개인 클론) — ELEVENLABS_API_KEY 필요
            el_key = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
            if not el_key:
                failed.append(t["id"])
                print(f"[{t['id']}] ELEVENLABS_API_KEY 시크릿이 없습니다 — 건너뜀")
                continue
            vid = t.get("voice") or el_resolve_voice(t["voice_name"], el_key)
            if not vid:
                failed.append(t["id"])
                continue
            print(f"[{t['id']}] elevenlabs-direct {vid}: {t['text'][:30]}…")

            def el_tts(voice_id):
                req = urllib.request.Request(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    data=json.dumps({
                        "text": t["text"],
                        "model_id": t.get("el_model", "eleven_v3"),
                    }).encode(),
                    headers={"Content-Type": "application/json", "xi-api-key": el_key},
                    method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        open(path, "wb").write(resp.read())
                    print(f"  저장됨 → {path}")
                    return True
                except urllib.error.HTTPError as e:
                    print(f"  [{t['id']}] ElevenLabs 오류 (HTTP {e.code}): "
                          f"{e.read().decode(errors='replace')[:300]}")
                    return False

            if el_tts(vid):
                continue
            # 라이브러리 목소리가 계정에 없어 거부된 경우: 이름으로 추가 후 1회 재시도
            rid = el_resolve_voice(t["voice_name"], el_key) if t.get("voice_name") else None
            if rid and rid != vid and el_tts(rid):
                continue
            failed.append(t["id"])
            continue
        if "elevenlabs" in model:
            # ElevenLabs (fal 호스팅) — v3는 감정을 대사 안의 오디오 태그([sobbing] 등)로 지시
            payload = {"text": t["text"], "voice": t["voice"]}
            for k in ("stability", "similarity_boost", "style", "speed"):
                if k in t:
                    payload[k] = t[k]
        else:
            voice_setting = {"voice_id": t["voice"], "speed": float(t.get("speed", spec.get("speed", 1.0)))}
            if t.get("emotion") and t["emotion"] != "neutral":
                voice_setting["emotion"] = t["emotion"]
            payload = {
                "text": t["text"],
                "voice_setting": voice_setting,
                "language_boost": spec.get("language_boost", "Korean"),
            }
        print(f"[{t['id']}] {model} {t['voice']}/{t.get('emotion','-')}: {t['text'][:30]}…")
        result = fal_run(model, payload, key, t["id"])
        url = find_audio_url(result) if result else None
        if not url:
            failed.append(t["id"])
            continue
        urllib.request.urlretrieve(url, path)
        print(f"  저장됨 → {path}")
    if failed:
        sys.exit(f"생성 실패: {', '.join(failed)}")
    print("오디션 샘플 생성 완료")


if __name__ == "__main__":
    main()
