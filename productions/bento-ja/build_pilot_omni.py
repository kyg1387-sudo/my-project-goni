#!/usr/bin/env python3
"""bento 대사 3컷 시범 립싱크 스펙(audition_spec=bento-pilot-omni) — 합격 키프레임 + 구동 음성(무음 패딩) + PHASE 3 연기 지시.

사용법: python3 productions/bento-ja/build_pilot_omni.py S08j=<keyframe.png> S13d=<…> S13f=<…>
구동 음성 assets/auditions/bento-pilot-omni/a_<컷>.mp3 = 본녹음 발화 구간 + 컷 길이까지 무음(build_lock 타임라인). OmniHuman 0.16달러/초.
"""
import json, os, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sb = {s["id"]: s for s in json.load(open(os.path.join(REPO, "scripts", "storyboard", "bento.json"), encoding="utf-8"))["scenes"]}
tests, sec = [], 0.0
for arg in sys.argv[1:]:
    sid, img = arg.split("=", 1)
    assert os.path.exists(os.path.join(REPO, img)), img
    sc = sb[sid]
    act = sc["act"]
    if "NOT smiling" in act and not act.startswith("NOT smiling"):
        act = "NOT smiling at any moment. " + act  # 제18장 4 ② 연기 지시 맨 앞
    tests.append({"id": f"omni_{sid}", "model": "omnihuman", "image": img, "audio_id": f"a_{sid}", "prompt": act})
    sec += sc["assembled_s"]
spec = {"_설명": f"bento 대사 3컷 시범 립싱크(build_pilot_omni.py 생성). 약 {sec:.1f}초 × 0.16 = {sec * 0.16:.2f}달러", "tests": tests}
json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "bento-pilot-omni.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(spec["_설명"])
