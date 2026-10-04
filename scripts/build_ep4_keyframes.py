#!/usr/bin/env python3
"""EP4 PHASE 4 키프레임 스펙 생성기 (규격서 PHASE 4: Multi-Reference 렌더링).

scripts/storyboard/kim-christmas.json(PHASE 3 Lock, build_ep4_phase3.py 생성)을 읽어
generate_portraits.py 스펙을 만든다. 스토리보드를 고치면 이 스크립트를 다시 돌릴 뿐, 스펙을 손으로 고치지 않는다.

- 참조 = PHASE 2 셀(인물 셀 + 로케이션 셀 + 소품 셀). EP3 카메오는 시트(GMA·CART).
- 출력: scripts/portraits/ep4-keyframes.json(전체), scripts/portraits/ep4-keyframes-pilot.json(파일럿 3장).
  generate-video.yml portraits_spec=<스펙> → assets/portraits/<스펙>/<id>-1.png. 합격 파일럿은 ep4-keyframes/로 복사해 재사용.
- 키프레임이 필요 없는 컷: S01(S44 재사용)·S02(S45 재사용)·S30(S28 재사용).
사용법: python3 scripts/build_ep4_keyframes.py
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "kim-christmas.json")
OUT_PATH = os.path.join(ROOT, "scripts", "portraits", "ep4-keyframes.json")
PILOT_PATH = os.path.join(ROOT, "scripts", "portraits", "ep4-keyframes-pilot.json")
PILOT_IDS = ["S36", "S41", "S50"]  # 보행 뒷모습 / 2인 실내 발견 / 대사 CU — 난이도 3유형(사용자 승인 파일럿)
CELLS = "assets/portraits/ep4-cast/cells"

SHOT = {
    "cu": "Close-up, chest-up, single person (no hands in frame)",
    "insert": "Insert close-up on the described detail",
    "ecu": "Extreme close-up",
    "medium": "Medium shot",
    "long": "Long shot (full figure and surroundings)",
    "xlong": "Extreme long establishing shot",
}
WHO = {
    "KIMW": ("kimw", "Kim, the apartment-complex security guard (Korean man in his early 60s)"),
    "MOM": ("mom", "Ren's mother (Japanese single mother in her early-to-mid 30s)"),
    "REN": ("ren", "Ren (7-year-old Japanese boy)"),
    "CLERK": ("clerk", "Sato, the management-office clerk (Japanese woman in her 40s)"),
}
WARDROBE = {
    "KIMW": ("Kim's wardrobe is locked: an old, worn dark navy-charcoal padded winter jacket with visible pilling and frayed "
             "cuffs (no logo, no patch) over a thin plain navy guard uniform; no name tag, no badge, no cap, no hat."),
    "MOM": ("The mother's look is locked: long straight black hair tied low at the nape, tired face without makeup, NO glasses; "
            "outdoors a plain beige long padded coat, indoors a plain grey cardigan; no logos."),
    "REN": ("Ren's look is locked: bowl haircut, round red cheeks; daytime a plain mustard knit sweater; at night a plain navy "
            "padded vest over grey pajama pants; no prints, no logos."),
    "CLERK": ("The clerk's look is locked: short black bob, black-rimmed glasses, plain navy cardigan over a white blouse; "
              "no name tag, no badge, no lanyard text."),
}
GMA_LOCK = ("The grandmother (EP3 character) keeps her locked look: faded brown floral headscarf covering her hair, thick plain "
            "navy quilted jacket, brown work gloves; her handcart has a single straight drawbar ending in a short leather-wrapped "
            "cross-bar with a pair of men's work gloves tucked on it.")
# 장면별 구도 보강(스토리보드 내용은 바꾸지 않고 프레이밍만 분명히)
COMPOSITION = {
    "S36": ("Camera at the BOTTOM of one long straight flight of concrete stairs, looking up the flight: Kim is about one third of "
            "the way up, his back fully to the camera, mid-step climbing UPWARD, the small tabletop tree with the knitted red-and-white "
            "star hugged against his chest (only the star and the top of the tree peek over his shoulder). Many more steps continue "
            "straight above him to the next floor; NO landing, NO turn of the stairs near him. One warm sensor light glows at the top of "
            "the flight; the rest is dim and cool."),
    "S37": ("Rear full shot from behind Kim in the interior corridor: he stands with his back to the camera in front of the steel door of "
            "unit 1801, having just set the small lit tree with the knitted star on the floor at the door; his head is bowed slightly, "
            "body still facing the door. The blank metal number plate beside the door faces the camera."),
    "S24": ("Long shot on a snowy path at dusk, camera static at the side: Kim (left, walking right) and the grandmother pulling her "
            "handcart (right, walking left) are just passing each other in the middle of the frame, both giving a small polite bow of "
            "the head; both seen in three-quarter side view, full bodies visible, small in frame."),
    "S41": ("Interior 18th-floor corridor (same as the location reference), camera facing the open steel door of unit 1801 from the side at child height: the mother stands "
            "in the doorway in a plain grey cardigan, frozen, one hand on the door; Ren beside her beams with his mouth closed and "
            "points down at the small lit tree with the knitted star standing on the corridor floor at their feet. "
            "Both faces clearly visible, matching their references."),
    "S50": ("SINGLE PORTRAIT: exactly one person (Kim) and NOBODY else — no foreground shoulder, no back of another head, "
            "no over-the-shoulder framing. Chest-up close-up inside the guard booth, looking just off-lens camera-left, head straight. His face must be the exact same face as the KIM reference. "
            "A faint kind smile is already on his face (50%), lips just parted. No hands, no cup, no kettle in frame."),
}


def resolve(ref):
    """'KIMW@expr-smile' → (파일, 설명) 목록."""
    kind, cell = ref.split("@", 1)
    if kind == "LOC":
        return [(f"{CELLS}/loc-{cell}.png", "the LOCATION reference photo: reproduce this exact place — same materials, "
                 "layout, light direction and color temperature — as the setting of the frame (people and time of day as described).")]
    if kind == "PROP":
        return [(f"{CELLS}/prop-{cell}.png", "a PROP reference: reproduce this exact object — same shape, materials, colors "
                 "and wear — at a natural scale in the scene (ignore the white studio background).")]
    if kind == "GMA":
        return [("assets/portraits/ep3-cast/grandma-sheet-1.png", "the CHARACTER master sheet of the elderly paper-collecting "
                 "grandmother (Japanese-series cameo): identical face, age and wardrobe; the sheet's grid must NOT appear.")]
    if kind == "CART":
        return [("assets/portraits/ep3-cart/cells/cart-front34.png", "the PROP reference of her handcart: same steel frame, "
                 "mesh rails, two spoked wheels and single straight drawbar with a leather-wrapped cross-bar.")]
    prefix, who = WHO[kind]
    return [(f"{CELLS}/{prefix}-{cell}.png", f"the CHARACTER reference of {who}: put this exact same person in the frame — "
             "identical face, hair, skin, age and wardrobe — using it as the identity, pose and expression guide.")]


def build_prompt(sc, preset, negative, plain):
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, "
             "no panels, no borders, no captions."]
    files = []
    for ref in sc["refs"]:
        for path, desc in resolve(ref):
            files.append(path)
            parts.append(f"Reference image {len(files)} is {desc}")
    kinds = {r.split("@", 1)[0] for r in sc["refs"]}
    for k, line in WARDROBE.items():
        if k in kinds:
            parts.append(line)
    if "GMA" in kinds:
        parts.append(GMA_LOCK)
    parts.append(f"Shot: {SHOT[sc['shot']]} — frame exactly at this shot size.")
    parts.append(f"Subject: {sc['subject'].strip()}")
    if sc["id"] in COMPOSITION:
        parts.append(COMPOSITION[sc["id"]])
    if sc.get("expression"):
        parts.append(f"Mood / expression (pre-baked at 50%): {sc['expression']}.")
    if sc.get("environment"):
        parts.append(f"Environment: {sc['environment']}.")
    parts.append(f"Cinematography: {sc['lens']}.")
    parts.append(f"Lighting: {sc['lighting']}.")
    parts.append(f"Style: {preset}.")
    people = kinds & {"KIMW", "MOM", "REN", "CLERK", "GMA"}
    if people:
        parts.append("No people in the frame other than those described; every visible person is one of the referenced characters.")
    else:
        parts.append("Completely unpopulated unless hands are described: no faces, no silhouettes.")
    if sc.get("ja_overlay"):
        parts.append("The surface that will later receive composited Japanese text faces the camera squarely, flat and evenly lit, "
                     "and is completely blank.")
    parts.append(plain)
    parts.append("Absolutely no text, letters, numbers, logos, signage or symbols anywhere in the image.")
    parts.append(f"Negative: {negative}.")
    return " ".join(parts), files


def main():
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    chars, missing = [], []
    for sc in sb["scenes"]:
        if not sc.get("keyframe"):
            continue
        prompt, files = build_prompt(sc, sb["preset"], sb["negative"], sb["plain_props"])
        missing += [f for f in files if not os.path.exists(os.path.join(ROOT, f))]
        chars.append({"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": files, "prompt": prompt})
    if missing:
        raise SystemExit("참조 파일 없음: " + ", ".join(sorted(set(missing))))
    head = {"_설명": "EP4 PHASE 4 키프레임(build_ep4_keyframes.py 생성, 직접 수정 금지). 참조 = PHASE 2 셀.",
            "_style_preset": sb["preset"]}
    json.dump({**head, "characters": chars}, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pilot = [c for c in chars if c["id"] in PILOT_IDS]
    json.dump({**head, "_설명": head["_설명"] + " 파일럿 3장(S36·S41·S50).", "characters": pilot},
              open(PILOT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"키프레임 {len(chars)}장 스펙 → {OUT_PATH}\n파일럿 {len(pilot)}장 → {PILOT_PATH}")


if __name__ == "__main__":
    main()
