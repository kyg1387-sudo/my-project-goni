#!/usr/bin/env python3
"""EP3 PHASE 5 장면 파일 생성기 (규격서 PHASE 5: 승인 키프레임 → Image-to-Video, 극미세 모션만).

scripts/storyboard/kim-cart-grandma.json(PHASE 3 Lock)의 카메라·모션 지시와
assets/portraits/ep3-keyframes/sNN-1.png(PHASE 4 Lock)를 결합해
scripts/scenes/kim-cart-grandma.json 을 만든다. 장면 길이는 PHASE 1 Lock(durations)을 그대로 쓴다.
또한 scripts/audio/kim-cart-grandma.json 에 scene_durations(조립용)와 lipsync_skip_scenes(화자가 화면에
없는 리액션 컷)를 기록한다. 손으로 고치지 말고 이 스크립트를 다시 돌릴 것.
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = os.path.join(ROOT, "scripts", "storyboard", "kim-cart-grandma.json")
OLD = os.path.join(ROOT, "scripts", "scenes", "_archive", "kim-cart-grandma.t2v-handover.json")
OUT = os.path.join(ROOT, "scripts", "scenes", "kim-cart-grandma.json")
AUDIO = os.path.join(ROOT, "scripts", "audio", "kim-cart-grandma.json")
KF = "assets/portraits/ep3-keyframes/{sid}-1.png"

# 대사가 걸리는 장면과 화면 속 화자(PHASE 3 샷 리스트 기준). 화자가 화면에 없는 리액션 컷은 립싱크 제외.
TALKING = {1: "Kim", 15: "the grandmother", 28: "Choi", 29: "Kim", 31: "Choi", 36: "the grandmother"}
LIPSYNC_SKIP = [2, 30, 37]  # 대사 6장면(1·15·28·29·31·36)은 omnihuman(오디오 구동)으로 생성
CART_RIGID = [3, 6, 7, 8, 9, 12, 13, 26, 29, 31, 32, 33, 34, 35, 36, 37, 42]  # 리어카 손잡이가 보이는 컷  # 김씨 목소리에 최사장 리액션(S02·S30), 할머니 목소리에 손 클로즈업(S37)

STYLE = ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, "
         "keep the exact look, faces, wardrobe, props and lighting of the first frame; natural slow motion only; "
         "no text, no captions, no logos, no sudden movement, no new people entering")

sb = json.load(open(SB, encoding="utf-8"))
old = json.load(open(OLD, encoding="utf-8"))
durations = [int(d) for d in old["durations"]]
assert len(durations) == len(sb["scenes"]) == 44

scenes = []
for k, sc in enumerate(sb["scenes"]):
    n = k + 1
    kf = KF.format(sid=sc["id"].lower())
    parts = [f"Camera: {sc['camera']}.", f"Motion: {sc['motion']}"]
    if n in TALKING:
        parts.append(f"{TALKING[n]} is speaking Korean softly: lips move gently and naturally with small jaw "
                     f"movement, no exaggerated mouth shapes, teeth not shown, head turn under 10 degrees.")
    else:
        parts.append("Mouths stay closed; no talking.")
    if not any(not r.startswith("LOC@") for r in sb["scenes"][k]["refs"]):
        # 파일럿 실증(S03): 무인 인서트에 손이 들어옴 → 무인 컷은 사람·손 진입 금지를 명시
        parts.append("This is an empty insert shot: no person, no hand, no arm or body part ever enters the frame; "
                     "only the objects and the camera move.")
    if n in CART_RIGID:
        # 실증(S29): i2v 변환 중 끌채가 U자로 변형 → 소품 형태 고정을 명시
        parts.append("The handcart is a rigid prop and keeps EXACTLY the shape of the first frame: one single straight "
                     "drawbar pole with one short leather-wrapped cross-bar grip; the handle never bends, splits, "
                     "duplicates or turns into a loop; hands stay where they are on the grip.")
    parts.append("Everything else in the frame stays still except gentle ambient motion (dust, mist, light).")
    scenes.append({"prompt": " ".join(parts), "image": kf, "duration": durations[k]})

out = {
    "_설명": "EP3 PHASE 5 장면 파일 — scripts/build_ep3_phase5_scenes.py 생성. 장면마다 승인 키프레임(image)을 첫 프레임으로 "
            "고정해 Image-to-Video(fal Seedance lite i2v)로 변환한다. prompt는 PHASE 3 Lock의 카메라·모션 지시(승인 목록만). "
            "이전 텍스트→영상 파일은 scripts/scenes/_archive/ 에 보관.",
    "ratio": "16:9",
    "style": STYLE,
    "durations": durations,
    "scenes": scenes,
}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

audio = json.load(open(AUDIO, encoding="utf-8"))
audio["scene_durations"] = durations
audio["lipsync_skip_scenes"] = LIPSYNC_SKIP
audio["omnihuman_scenes"] = [1, 15, 28, 29, 31, 36]
json.dump(audio, open(AUDIO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"장면 {len(scenes)}개, 총 {sum(durations)}초, 립싱크 대상 {sorted(TALKING)} / 제외 {LIPSYNC_SKIP}")
print("예시 S01:", scenes[0]["prompt"][:200])
