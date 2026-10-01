#!/usr/bin/env python3
"""EP3 PHASE 4 키프레임 스펙 생성기 (규격서 PHASE 4: Image-to-Image / Multi-Reference 렌더링).

scripts/storyboard/kim-cart-grandma.json(PHASE 3 Lock 데이터)을 그대로 읽어
generate_portraits.py가 먹는 스펙(scripts/portraits/ep3-keyframes.json)을 만든다.
드리프트 방지 원칙(아카이브 교훈 ㉒): 스토리보드를 고치면 이 스크립트를 다시 돌릴 뿐,
스펙을 손으로 옮겨 적지 않는다.

- 장면당 키프레임 1장, 참조 = 캐릭터 마스터 시트(KIM/GMA/CHOI) + 로케이션 셀(LOC) 멀티 레퍼런스.
- 출력은 generate-video.yml portraits 모드 규약에 따라 assets/portraits/<spec>/<id>-1.png 에 커밋된다.
- 파일럿 스펙(ep3-keyframes-pilot.json, 3장)을 따로 만들어 "시트 참조 → 단일 프레임" 생성이
  되는지 소액으로 먼저 검증한다(비용 원칙). 합격 파일럿은 assets/portraits/ep3-keyframes/로 복사해
  본 실행에서 재사용(재과금 없음).

사용법: python3 scripts/build_ep3_keyframes.py
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "kim-cart-grandma.json")
OUT_PATH = os.path.join(ROOT, "scripts", "portraits", "ep3-keyframes.json")
PILOT_PATH = os.path.join(ROOT, "scripts", "portraits", "ep3-keyframes-pilot.json")
PILOT_IDS = ["S01", "S03", "S21"]  # 투샷 대사컷 / 무인 인서트 / 야간 비 전신 — 난이도 3유형

# 파일럿 실증(2026-10-01): 트럭 적재함에 한글풍 레터링, 골판지 상자에 인쇄 라벨 자국이 생김 →
# 소품도 '무지'로 명시하고 네거티브를 보강한다(아카이브 교훈: 화면 속 글자는 모델이 못 쓴다).
PLAIN_PROPS = ("All props are plain and unprinted: vehicles have no lettering or decals, cardboard boxes and "
               "paper bundles are plain brown with no printed labels, stamps, tape markings or barcodes, "
               "walls and boards are blank.")
EXTRA_NEGATIVE = "lettering on vehicles, printed labels on boxes, shipping stamps, barcodes, stickers, posters"

# 장면별 구도 보강(스토리보드 Lock 내용을 바꾸지 않고, 프레이밍·배치만 더 분명히 지시).
# 파일럿 S01: 두 인물이 나란히 서서 화면 밖을 보는 그림이 나옴 → 대치 구도를 명시.
COMPOSITION = {
    "S01": ("Composition: Kim stands between Choi and the handcart with his body turned toward Choi; the two "
            "men face each other at close range in a confrontation, Kim nearer to camera. Frame them from the "
            "chest up as a medium close-up two-shot, both faces clearly visible."),
}

SHEETS = {
    "KIM": ("assets/portraits/ep3-cast/kim-sheet-1.png", "Kim, the apartment security guard (Korean man in his early 60s)"),
    "GMA": ("assets/portraits/ep3-cast/grandma-sheet-1.png", "the elderly paper-collecting grandmother (Korean woman in her late 70s)"),
    "CHOI": ("assets/portraits/ep3-choi/choi-sheet-1.png", "Choi, the scrapyard owner (Korean man in his 50s)"),
}
PANEL = {
    "front": "top-row left panel (frontal head and shoulders)",
    "45": "top-row middle panel (45-degree three-quarter view)",
    "side": "top-row right panel (profile)",
    "fullbody-front": "middle-row left panel (full body, front)",
    "fullbody-back": "middle-row middle panel (full body, back view)",
    "fullbody-side": "middle-row right panel (full body, side)",
    "front-neutral": "bottom-row left panel (neutral calm expression)",
    "front-smile": "bottom-row middle panel (faint gentle smile)",
    "front-tense": "bottom-row right panel (tense, worried expression)",
    "front-wary": "bottom-row right panel (tense, wary expression)",
    "45-neutral": "top-row middle panel (45-degree view) with the calm neutral expression of the bottom-row left panel",
    "hands": "hands exactly as they appear in the middle-row full-body panels (same skin, same age)",
}


def resolve(ref):
    """'KIM@front-neutral' / 'LOC@junkyard-day' → (파일 경로, 참조 설명문 조각)."""
    kind, cell = ref.split("@", 1)
    if kind == "LOC":
        path = f"assets/portraits/ep3-cast/cells/loc-{cell}.png"
        return path, ("the LOCATION reference photo: reproduce this exact place — same materials, "
                      "layout, light direction and color temperature — as the setting of the frame.")
    path, who = SHEETS[kind]
    panel = PANEL[cell]
    return path, (f"the CHARACTER master sheet of {who}: put this exact same person in the frame — identical "
                  f"face, hair, skin, age and wardrobe — using its {panel} as the pose and expression guide. "
                  "The sheet's grid layout, white gutters and other panels must NOT appear in the output.")


def build_prompt(scene, preset, negative):
    refs = scene["refs"]
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, "
             "NOT a grid, NOT a contact sheet, no panels, no borders, no captions."]
    files = []
    for n, ref in enumerate(refs, 1):
        path, desc = resolve(ref)
        files.append(path)
        parts.append(f"Reference image {n} is {desc}")
    has_people = any(not r.startswith("LOC@") for r in refs)
    parts.append(f"Shot: {scene['shot']} — frame exactly at this shot size.")
    parts.append(f"Subject: {scene['subject'].strip()}")
    if scene["id"] in COMPOSITION:
        parts.append(COMPOSITION[scene["id"]])
    if scene.get("expression") and scene["expression"].strip() not in ("", "—", "-"):
        parts.append(f"Expression (pre-baked at 50%): {scene['expression'].strip()}")
    parts.append(f"Environment: {scene['environment'].strip()}.")
    parts.append(f"Cinematography: {scene['lens'].strip()}.")
    parts.append(f"Lighting: {scene['lighting'].strip()}.")
    parts.append(f"Style: {preset}.")
    if has_people:
        parts.append("No people in the frame other than those described above; every visible person must be one of the referenced characters.")
    else:
        parts.append("Completely unpopulated: not a single person, silhouette or body part anywhere in the frame.")
    parts.append(PLAIN_PROPS)
    parts.append("Absolutely no text, letters, numbers, logos, signage or symbols anywhere in the image.")
    parts.append(f"Negative: {negative}, {EXTRA_NEGATIVE}.")
    return " ".join(parts), files


def main():
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    items = []
    for sc in sb["scenes"]:
        prompt, files = build_prompt(sc, sb["preset"], sb["negative"])
        for f in files:
            if not os.path.exists(os.path.join(ROOT, f)):
                sys.exit(f"{sc['id']}: 참조 파일 없음 — {f}")
        items.append({"id": sc["id"].lower(), "count": 1, "aspect_ratio": "16:9",
                      "refs": files, "prompt": prompt})
    desc = ("EP3 PHASE 4 키프레임 스펙 — scripts/build_ep3_keyframes.py가 PHASE 3 Lock 데이터"
            "(scripts/storyboard/kim-cart-grandma.json)에서 자동 생성. 손으로 고치지 말고 생성기를 다시 돌릴 것. "
            "실행: generate-video.yml portraits_spec=ep3-keyframes → assets/portraits/ep3-keyframes/sNN-1.png. "
            "Kill Gate(외계어·손가락·눈동자·그리드 출력) 불합격 장면은 portraits_regen_ids로 부분 재생성.")
    json.dump({"_설명": desc, "characters": items}, open(OUT_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    pilot = [it for it in items if it["id"].upper() in PILOT_IDS]
    json.dump({"_설명": "EP3 PHASE 4 파일럿(3장): 시트 참조로 단일 16:9 프레임·얼굴 일치가 나오는지 소액 검증. "
                        "합격분은 assets/portraits/ep3-keyframes/로 복사해 본 실행에서 재사용.",
               "characters": pilot}, open(PILOT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"생성: {OUT_PATH} ({len(items)}장), {PILOT_PATH} ({len(pilot)}장)")
    print("참조 파일 종류:", len({f for it in items for f in it['refs']}))


if __name__ == "__main__":
    main()
