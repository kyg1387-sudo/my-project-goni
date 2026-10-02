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
    # 본 실행 1차 Kill Gate(2026-10-01): S06·S13 두건 누락, S11 실내 생성, S25 무전기가 바닥에 놓임 → 보강
    "S06": ("Mandatory wardrobe: the grandmother wears the faded brown floral headscarf tied over her hair exactly as in "
            "the reference sheet — her hair must be covered by the scarf. Long shot, full body visible, she walks "
            "toward camera-left pulling the handcart."),
    "S11": ("Setting is OUTDOORS: the camera is outside the security booth; Kim stands on the pavement beside the "
            "flower bed in front of the booth, seen from behind, placing a neat stack of flattened cardboard boxes on "
            "the ground next to the flowers. The booth window is visible in the background. No interior walls."),
    "S13": ("Mandatory wardrobe: the grandmother wears the faded brown floral headscarf tied over her hair exactly as in "
            "the reference sheet — her hair must be covered by the scarf. Long shot: she has parked the handcart by "
            "the rubble wall and is walking away from it."),
    "S25": ("Close-up on legs and shoes only, from the knees down, low camera: tired steps on the wet pavement. "
            "Nothing lies on the ground — no radio, no objects dropped; the radio stays clipped on his belt out of frame."),
    # 일관성 패스 실증: 연속성 앵커(S07) 영향으로 S06가 '상자 싣기' 자세가 됨 → 동작 명시. S40↔S41 옥수수 봉지 재질 불일치 → 소품 연속성.
    "S06": ("Action: the grandmother is WALKING along the sidewalk toward camera-left, body upright with a slight stoop, "
            "one hand behind her gripping the cart's leather-wrapped drawbar T-grip, the cart trailing behind her. "
            "She is NOT bending over and NOT loading boxes; the cart bed already holds a few flattened boxes."),
    "S41": ("Prop continuity: the bag in Kim's hand is the SAME small clear plastic zip bag of yellow boiled corn kernels "
            "that sits on the windowsill in the continuity frame — a transparent plastic bag, NOT a paper bag."),
    "S09": ("Close-up on the grandmother's gloved hands wiping, with a small rag, the leather-wrapped short cross-bar at "
            "the end of the cart's single straight drawbar pole; the pole is ONE bar, the grip is ONE short cross-bar."),
    "S26": ("FACE IDENTITY IS THE PRIORITY: Kim's face must be the exact same face as the character sheet (top-row left "
            "panel), rendered large and sharp — medium shot from the knees up, face at least one quarter of the frame height. "
            "Exactly ONE person in the frame: Kim alone, walking toward camera and looking around; Choi is NOT present. Every handcart "
            "standing in the yard is the same model as the prop reference: single straight drawbar pole with a short "
            "leather-wrapped cross-bar grip. No carts with U-shaped push handles."),
    "S37": ("CLOSE-UP, 85mm: the frame is filled by the grandmother's two gloved hands cupping the leather-wrapped short "
            "cross-bar at the end of the cart's single straight drawbar pole (ONE pole, ONE cross-bar, exactly like the "
            "handle reference); her body is only partly visible at the frame edge, no full figure, no wide shot."),
    "S42": ("Action: the grandmother is WALKING along the sidewalk, body upright with a slight stoop, one hand behind her "
            "holding the short leather-wrapped cross-bar at the end of the cart's single drawbar pole, the cart trailing "
            "behind her. She is NOT bending over, NOT loading boxes, NOT standing still."),
    "S29": ("Composition: Kim stands at the FRONT of the cart, facing the camera, the cart bed BEHIND him and to one side. "
            "He has lifted the end of the cart's single straight drawbar pole and holds its short leather-wrapped "
            "cross-bar grip in both hands at waist height, the pole running back past his hip to the cart. ONE pole, ONE "
            "short cross-bar — NOT a U-shaped loop, NOT two parallel bars, NOT a push handle behind the cart."),
    "S34": ("Kim walks away from the camera PULLING the cart by its front drawbar T-grip with one hand behind him, "
            "the cart trailing behind him nearer to the camera; same cart as the prop reference, no rear push handle."),
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


# 전체 일관성 패스(2026-10-01, 사용자 지시 "전체 일관성 있게"): 장소별 승인 키프레임을 연속성 앵커로 추가 참조.
ANCHORS = {
    "junkyard": "S28", "apt-gate": "S07", "demolition": "S13", "alley-night": "S20",
    "guard-booth-day": "S10", "guard-booth-night": "S18",
}
WARDROBE = {
    "GMA": ("The grandmother's wardrobe is locked: a faded brown floral headscarf tied over her head so that it covers "
            "her hair (a real scarf, not a thin headband), a thick plain navy quilted jacket, dark-brown baggy monpe "
            "trousers, brown work gloves; no text, no logos."),
    "CHOI": ("Choi's wardrobe is locked: a grease-stained plain grey work vest over a plain dark shirt, black work "
             "gloves, a worn radio on his belt; no text, no logos, no name tag."),
}


EXTRA_REFS = {"S41": "assets/portraits/ep3-keyframes/s40-1.png"}  # 소품 연속성(옥수수 봉지)


ANCHOR_SKIP = {"S26", "S29", "S37", "S42"}  # 연속성 앵커가 동작·인물 구성을 끌어간 실증 → 앵커 제외


def anchor_for(scene):
    if scene["id"] in ANCHOR_SKIP:
        return None
    loc = [r for r in scene["refs"] if r.startswith("LOC@")]
    if not loc:
        return None
    cell = loc[0].split("@", 1)[1]
    place = cell.rsplit("-", 1)[0]
    if place == "guard-booth":
        place = "guard-booth-night" if cell.endswith("night") else "guard-booth-day"
    sid = ANCHORS.get(place)
    if not sid or sid == scene["id"]:
        return None
    return f"assets/portraits/ep3-keyframes/{sid.lower()}-1.png"


def resolve(ref):
    """'KIM@front-neutral' / 'LOC@junkyard-day' → (파일 경로, 참조 설명문 조각)."""
    kind, cell = ref.split("@", 1)
    if kind == "CART":
        # 소품 앵커(2026-10-01 추가): 장면마다 손잡이가 달라지던 리어카를 마스터 시트로 잠근다
        # 2026-10-02: 시트 전체 대신 셀 2장(3/4 앞모습, 손잡이 클로즈업)을 각각 참조 — 손잡이 형태 준수율 향상
        return ["assets/portraits/ep3-cart/cells/cart-front34.png",
                "assets/portraits/ep3-cart/cells/cart-handle.png"], (
            "the PROP master sheet of the paper-collecting handcart: reproduce this exact same cart — same steel-tube "
            "frame, mesh side rails, two large spoked wheels, and the long single tubular front drawbar ending in a T-shaped cross grip "
            "that is wound with the frayed brown leather strap. The pull handle must be visible and is what a person "
            "holds to pull the cart. The sheet's grid layout and white gutters must NOT appear in the output.")
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
    for ref in refs:
        path, desc = resolve(ref)
        if isinstance(path, list):
            files.append(path[0])
            parts.append(f"Reference image {len(files)} is {desc}")
            files.append(path[1])
            parts.append(f"Reference image {len(files)} is a close-up of that same cart's handle: ONE straight pole "
                         "ending in ONE short horizontal cross-bar wrapped in brown leather with a hanging strap end. "
                         "Every handcart in the frame has exactly this handle — never a U-shaped loop, never two "
                         "parallel bars, never a shopping-cart style push bar.")
        else:
            files.append(path)
            parts.append(f"Reference image {len(files)} is {desc}")
    extra = EXTRA_REFS.get(scene["id"])
    if extra and os.path.exists(extra):
        files.append(extra)
        parts.append(f"Reference image {len(files)} is the PROP continuity frame: the exact same small clear plastic bag "
                     "of boiled corn must appear, identical material and color.")
    anchor = anchor_for(scene)
    if anchor and os.path.exists(anchor):
        files.append(anchor)
        parts.append(f"Reference image {len(files)} is the CONTINUITY frame: an approved still from the same location "
                     "earlier in this film — match its exact set dressing, props layout, materials, colors and lens look "
                     "so both shots clearly belong to the same place; only the camera angle, time of day and action differ.")
    has_people = any(not r.startswith(("LOC@", "CART@")) for r in refs)
    for kind, line in WARDROBE.items():
        if any(r.startswith(kind + "@") for r in refs):
            parts.append(line)
    if any(r.startswith("KIM@") for r in refs):
        parts.append("Kim's wardrobe is locked: a plain LONG-SLEEVE dark navy security-guard shirt and dark trousers, "
                     "pristine clean chest with NO name tag, NO badge, NO insignia, NO patch, NO lettering of any kind; "
                     "the only item on him is a small radio on his belt.")
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
