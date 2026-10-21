#!/usr/bin/env python3
"""『閉店間際の弁当屋』(bento) PHASE 4 키프레임 스펙 생성기 — build_beggar_keyframes.py를 옮긴 것(내장 규칙 동일).

scripts/storyboard/bento.json(PHASE 3)을 읽어 generate-video.yml portraits_spec 스펙을 만든다. 손으로 스펙을 고치지 않는다.
단계: p:<id,…> 시범(컷당 2장) / a 립싱크 컷 / b 나머지 / r<n>:<id,…> 재생성(컷당 2장)
이 작품 차이: 모델 seedream v4 edit 2560x1440(PHASE 2 시트에서 실사·일관성 검증), 귀걸이·안경 없음, 같은 인물 두 나이
(修三 43·73, 拓海 12·42)는 나이별 셀·얼굴 크롭을 따로 쓴다. 「AI 제작이 아닌 것처럼」(제19장 7): 실사 피부·실제 눈물·상황 표정.
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "bento.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "bento-kf-{}.json")
FACE_DIR = "assets/portraits/bento-faces"
CELLS = "assets/portraits/bento-cast/cells"
PEOPLE = [
    ("shuzo1996", "Noguchi Shuzo in 1996 (43, square angular face, strong jaw, thick straight black eyebrows, short cropped black hair greying at the temples, clean-shaven, NO glasses, NO earrings)"),
    ("shuzo2026", "Noguchi Shuzo now (73, the same square angular face and strong jaw, thick straight WHITE eyebrows, short cropped WHITE hair, deep wrinkles, clean-shaven, NO glasses, NO earrings)"),
    ("sumie", "Noguchi Sumie (40, round soft face, gentle down-turned eyes, black hair in a low bun, NO glasses, NO earrings, NO moles)"),
    ("takumi12", "Asakura Takumi as a boy (12, thin face, LARGE round dark eyes with double eyelids, ears sticking out slightly, messy black fringe, NO glasses)"),
    ("takumi42", "Asakura Takumi grown up (42, the same LARGE round dark eyes with double eyelids and slightly protruding ears, short neat black hair, slim face, NO glasses, NO earrings)"),
    ("mio6", "Asakura Mio (6, round face, black bob with straight blunt bangs, NO glasses)"),
    ("hina8", "Asakura Hina (8, oval face, black hair in two low pigtails, NO glasses)"),
    ("mio36", "Asakura Mio grown up (36, round face, black bob with straight blunt bangs, NO glasses, NO earrings)"),
]
FACE_KINDS = ("face", "d")
PILOT_DONE = {"S08j", "S13d", "S13f"}  # 시범 승인(2026-10-20): S08j=r3-1·S13d=r2-1·S13f=r2-1 + 로컬 보정 → assets/portraits/bento-kf-pilot-ok/
LOC_NOTE = {
    "loc-shop96": "The 1996 shop: a small boxy CRT television, blank paper price cards, a plain round wall clock with a BLANK face, NO signs, NO posters with writing.",
    "loc-shop26": "The shop now, thirty years older: faded walls, a slim flat TV, a blank white paper notice, NO signs, NO posters with writing.",
    "loc-street": "NO readable signs, NO shop names, NO cars, NO headlights.",
    "loc-kitchen": "No labels on containers, no menus, no papers with writing.",
    "loc-shokudo": "No signs with writing, no posters with writing; children only as blurred backs.",
}
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
FACE13 = ("MEDIUM CLOSE-UP, the camera about 1.5 metres from the speaker: the speaker's head is near the top edge of the frame and the frame is cut at "
          "mid-chest, so the speaker's head and shoulders fill the centre of the frame and the face is about one third of the frame height (NOT a wide "
          "shot, NOT full body, the room is only a blurred background). Framing from mid-chest up: the speaker's head and shoulders fill the frame, the face about one third of the frame height and sharp, "
          "turned about 35 degrees toward the other person (never straight at the camera, never full profile); the speaker's hands and what "
          "they hold are visible at the bottom of the frame; 50mm lens, f/2.0, shallow depth of field.")
OTS = ("Over-the-shoulder two-shot composition: the listener is at the near foreground edge seen strictly from behind — only the back of the "
       "head, hair and one shoulder, soft and out of focus; the listener's face is NOT visible.")
INSERT = ("EXTREME CLOSE-UP INSERT: only the hands / object described fill the frame; NO face, NO head and NO shoulders anywhere in the frame — "
          "the person is out of frame except the hands, wrists and sleeves. Shallow depth of field.")
BACK = ("The person is seen strictly from behind — only the back of the head, hair, ears and shoulders are visible, the face turned away from "
        "the camera; the mouth is never visible.")
ANGLE = {"HA": "CAMERA: steep high angle, looking down from about 4 metres above.", "OH": "CAMERA: directly overhead, looking straight down.",
         "BE": "CAMERA: bird's-eye view straight down from the ceiling.", "LA": "CAMERA: low angle, looking up from about waist height.",
         "SIDE": "CAMERA: from the side or behind — the face in side profile or hidden, NOT facing the camera."}
BLANK = ("Every paper, document, form, envelope, phone screen and monitor surface is completely blank and clean: NO printed lines, NO characters, "
         "NO headings, NO tables, NO numerals, NO stamps with characters (Japanese text is composited later).")
LIGHT_NOTE = {
    "s96": "LIGHTING: night in 1996, the glass showcase's own warm 3200K light is the key light on the faces from below, a warm ceiling lamp, deep soft shadows, faces clearly readable.",
    "s96rain": "LIGHTING: rainy night in 1996, warm 3200K showcase key light inside, cold blue wet street beyond the glass door, faces clearly readable.",
    "s26": "LIGHTING: night now, cool 5600K fluorescent light and the showcase glow, faded, lonely, faces readable.",
    "s26warm": "LIGHTING: night now, the showcase's warm glow and one warm lamp, cool fluorescent low, intimate, faces clearly readable.",
    "letter": "LIGHTING: night now, a warm desk lamp on the counter lighting the face from below and the side, the rest of the shop dim and cool.",
    "kit96": "LIGHTING: the small back kitchen in 1996, one warm 3200K bulb, steam glowing.",
    "hosp": "LIGHTING: soft diffused afternoon window backlight in a quiet hospital room, low contrast.",
}
REAL = ("REAL PHOTOGRAPH, live-action Japanese film still: natural skin texture with visible pores and fine lines, no airbrushed or plastic skin, "
        "no beauty filter, natural colour, real fabric texture; NOT an illustration, NOT 3D, NOT CGI.")
EMO_OVERRIDE = {
    "S08j": "SPEAKER LOCKED: Shuzo in 1996 (black hair greying at the temples, white headband towel, white cook's jacket, navy apron) leans on the counter with both hands, the face at three-quarter angle toward the boy, gruff but warm, a faint softening around the eyes; the boy appears ONLY as a blurred back of messy black hair and navy jumper shoulder at the near LEFT edge, shorter than the counter edge. The lit glass showcase between them. It is NIGHT: the window behind him is dark night, NO daylight. His ears are bare: NO earrings, NO ear piercing, NO stud. His cheeks are clean: NO scar, NO cut, NO wound mark. The counter front and the wall below the counter are plain, NO papers or notes pinned anywhere.",
    "S13d": "SPEAKER LOCKED: grown-up Takumi (42, LARGE round dark eyes, slightly protruding ears, short neat black hair, charcoal overcoat) stands just inside the shop doorway (his daughter's small hand in his, below the frame edge, NOT visible), the face at three-quarter angle toward the old man, eyes red-rimmed and wet with tears pooled but NOT running, a small closed-mouth smile with lips together; at most ONE thin clear tear track on ONE cheek only, the other cheek completely dry, no droplet chains; the old man appears ONLY as a blurred back of short WHITE hair and grey cardigan shoulder at the near RIGHT edge. Behind Takumi: the glass sliding door and the dark night street.",
    "S13f": "SPEAKER LOCKED: old Shuzo (73, short WHITE hair, white eyebrows, deep wrinkles, grey cardigan under a faded navy apron) behind the counter with one hand resting on the ONE single remaining bento box on the counter top (no other bentos on the counter), the face at three-quarter angle toward Takumi, choked up: eyes red and wet with tears pooled but NOT running, mouth corners pulled down, chin trembling, NOT smiling; grown-up Takumi appears ONLY as a blurred back of short black hair and charcoal coat shoulder at the near LEFT edge.",
}
# 키프레임 1차 Kill Gate(2026-10-20) 컷별 고정 문장 — 맨 앞(구도 다음)에 넣는다
_PINK = "WARDROBE LOCKED: Sumie wears a PALE PINK triangle headscarf (NOT white), exactly the colour in the reference."
SHOT_FIX = {
    "S03a": _PINK, "S03b": _PINK, "S03c": _PINK, "S03d": _PINK,
    "S04b": "PEOPLE LOCKED: exactly TWO people — Shuzo behind the counter, and the boy ONLY as the blurred back of the head and shoulder at the near LEFT edge; the boy appears nowhere else in the frame.",
    "S08c": "The foreground boy's ear is covered by his messy hair. Every sign and board in the background is blank and out of focus.",
    "S12d": "He reads the letter with bare eyes, holding it at arm's length — no eyewear on his face at all.",
    "S06b": "FRAMING FIRST — CLOSE-UP: head and shoulders fill the frame, the face one third of the frame height or larger; NOT a medium or wide shot.",
    "S08n": "FRAMING FIRST — eye-level CLOSE-UP with a normal 50mm perspective, head and shoulders; NOT fisheye, NOT looking down from above, NOT distorted.",
    "S10bb": "Sumie has bare hair streaked with grey in a low bun — ignore any headscarf in the reference; she wears only the pale-blue hospital gown.",
    "S13n": "He holds the photograph up with its plain white BACK facing the camera; the picture side faces Takumi and is NOT visible.",
    "S13s": "PEOPLE LOCKED: exactly TWO people; behind old Shuzo only the shop's back wall and kitchen curtain — NO window, NO platform, NO street, NO passers-by.",
    "S14b": "AGE LOCKED: the younger man beside the old man is 42 years old (crow's feet, mature face, the same face as reference), NOT a teenager.",
    "S10bd": "Shuzo wears only a grey cardigan over a white shirt — ignore any apron in the reference.",
    # 2차 검수(2026-10-21): 손에 든 그릇·도시락이 몸 앞 허공에 뜸(1:32·2:2x) → 받침면에 닿은 부감 인서트
    "S03e": "Keep the exact kitchen, sink and bowl of the last reference image; ADD two man's hands resting in the rice water inside the bowl. GRAVITY LOCKED: the bowl sits on the bottom of the steel sink, its base touching the steel with a soft contact shadow; the hands only rest in the rice, they do NOT hold or lift the bowl; NO person standing behind the bowl.",
    "S04d": "GRAVITY LOCKED: the bento box lies flat on the steel counter top with a soft contact shadow under it, nobody holds or lifts it; ONE hand with metal tongs only; normal bento size (about 20 cm wide); NO person standing behind the box.",
    # 아이들 대사(L06a·L06b)가 어른 컷에 깔림(1:42) → 아이들이 보이는 컷으로, 화자 입은 가림
    "S03ba": "PEOPLE LOCKED: exactly THREE people — Sumie ONLY as a blurred back and shoulder at the near LEFT edge (face NOT visible), and the two children small in the middle distance on the bench; the boy's face is turned down toward the food (mouth NOT visible).",
    "S03bb": "PEOPLE LOCKED: exactly TWO children — the little sister ONLY as the blurred back of her red knit hat and yellow jacket shoulder at the near LEFT edge (face NOT visible, she faces away from the camera), and the boy at three-quarter angle toward her, lips together.",
    # 2차 검수(2026-10-21): 나가는 컷 키프레임이 정면(들어오는 자세) → i2v가 들어오다 돌아 나감. 나가는 컷은 처음부터 등이 카메라 쪽
    "S09l": "POSE LOCKED: both children are seen strictly from BEHIND (backs of heads, NO faces visible), already facing OUT toward the dark doorway, NOT walking in; PEOPLE LOCKED: exactly THREE people — Shuzo only as a back at the near right edge.",
    "S08g": "GRAVITY LOCKED: the plastic bag stands on the counter top; the bento boxes are closed with their clear lids shut; the hands hold only the box edges.",
    "S10be": "The apple is a WHOLE round apple (NOT cut in half, NOT sliced), its peel removed in one continuous strip only partway round; the knife blade rests flat, not cutting.",
    "S03bd": "WARDROBE LOCKED: the boy wears the SAME navy zip jacket over a grey shirt as the reference, long sleeves; he is SEATED on the bench, NOT standing; the little sister in a red knit hat and yellow padded jacket sits beside him.",
}
ANGER_CLOSED = ("Fury shown only in the wide-open glaring eyes, furrowed brow, flared nostrils and clenched jaw: eyes OPEN and fixed on the listener, "
                "lips pressed together, mouth CLOSED, NOT shouting (speech is added later).")


def who_of(name):
    return next(((k, v) for k, v in PEOPLE if name.startswith(k + "-")), (None, None))


def short(path):
    k, v = who_of(os.path.basename(path))
    return v.split(" (")[0] if v else "the other person"


def speaker_close(sc, people):
    """키프레임 1차 실증: FRAME_FIRST만으로는 립싱크 컷 26개 중 16개가 원경(얼굴 1/10~1/7). 시범 r2에서 통한 화자·앞 인물 배치 문장을 자동으로."""
    side = "RIGHT" if "right foreground" in sc["subject"].lower() else "LEFT"
    other = "LEFT" if side == "RIGHT" else "RIGHT"
    return (f"SPEAKER CLOSE: {short(people[0])} is about one metre from the camera on the {other} side of the frame, head and shoulders filling "
            f"about half of the frame width, the face one third of the frame height or larger, at three-quarter angle toward {short(people[1])}. "
            f"{short(people[1])} appears ONLY as a soft out-of-focus back of the head and one shoulder at the near {side} edge, cut by the frame "
            "(face NOT visible). Any counter or showcase is only a thin sliver at the bottom of the frame; the room behind is a soft blur.")


def describe(path, i):
    name = os.path.basename(path)
    if path.startswith(FACE_DIR):
        who = dict(PEOPLE).get(name[:-4], "the character")
        return (f"Reference image {i} is a tight face crop of {who}: reproduce exactly this face, age, hairstyle and eyewear; identity ONLY — "
                "do NOT copy its camera angle, background or lighting.")
    k, v = who_of(name)
    if k and name.endswith("-back.png"):
        return f"Reference image {i} is the BACK VIEW of {v}: this person appears seen from behind exactly like this (hair, wardrobe); do not show this person's face."
    if k:
        return (f"Reference image {i} is the character sheet cell of {v}: copy this exact face, hairstyle, eyewear, wardrobe and age; ignore its "
                "background, framing and any sheet layout.")
    if name.startswith("prop-"):
        return f"Reference image {i} is the prop reference: copy the object's exact shape, size and material; ignore any background or labels."
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing and light direction; ignore any "
            "borders, labels or wall papers.")


NO_FACE = {}
PROP_ADD = {"S03e": "assets/portraits/bento-kf-r9/S03e-1.png",  # r9 싱크·그릇 구도는 합격, 손만 빠짐 → 그 판에 손을 넣는 편집
            "S09i": CELLS + "/prop-origami.png",  # 소품 참조 없는 「paper bird」가 2회 연속 종이학 → 울새 소품 셀 참조
            "S06a": CELLS + "/loc-shop96-curtain.png", "S13b": CELLS + "/loc-shop26-ots.png"}  # 참조 없는 t2i 시계 인서트에 사람 얼굴 2회 → 무인 장소 판 참조(edit)  # 소품 참조 없는 「paper bird」가 2회 연속 종이학 → 울새 소품 셀 참조
ONE_TAKE = {"S06a", "S10a", "S13b", "S06b", "S10bd", "S13n", "S12d", "S09i", "S08a"}  # 재생성 중 단순 결함 컷은 1장(승인 예산 안, 2026-10-20)
NO_BACKCELL = set()  # 뒷모습 전신 셀이 원경 전신 구도를 끌어옴 — 앞 인물은 글로만
NO_LOC = set()  # 장소 참조가 원경·후광(오려 붙인 테두리)을 만든 컷 — 장소는 글로만
# 시범 1차(2026-10-20): 립싱크 3컷 6장 모두 장소 참조를 따라 원경(얼굴 1/6)으로 나옴 → 립싱크 컷은 장소 참조를 기본으로 뺀다(제18장 4)
FRAME_FIRST = ("FRAMING FIRST — TIGHT MEDIUM CLOSE-UP, chest-up portrait framing: the speaker's head and shoulders fill about half of the frame width, "
               "the face is one third of the frame height or larger; the room is only a soft out-of-focus background. NOT a wide shot, NOT a medium "
               "shot, NOT full body, no floor visible.")
# 「red eyes / reddened eye rims」는 홍채까지 빨갛게 만든다(시범 1차 S13d, 제18장 12 ②) — 눈물 문장을 치환
EYE_FIX = [("eyes red-rimmed and wet", "eyes wet"), ("eyes red-rimmed", "eyes wet"), ("his eyes red", "his eyes wet"), ("eyes red and wet", "eyes wet"),
           ("reddened eye rims", "natural skin tone around the eyes"), ("only the eyelid edges faintly pink", "natural skin tone around the eyes")]
# 시범 립싱크 S13f: 눈물이 가는 줄이 아니라 물방울 2~3개 줄로 보임(AI 티) → 눈물 컷에 한 줄·연속 문장
TEAR_LINE = "Any tear is ONE thin continuous transparent line on ONE cheek only, never a chain of separate droplets or beads, never on both cheeks."
EYE_SAFE = "EYES: natural dark brown irises and clear white sclera; NO red irises, NO glowing eyes, NO red eye whites, NO pink or red eyelids, NO eyeshadow, NO red nose, NO makeup."


def build(sc, stage):
    refs = list(sc["refs"])
    if sc["id"] in PROP_ADD:
        refs = refs + [PROP_ADD[sc["id"]]]
    if sc["id"] in NO_LOC or sc["kind"] == "d":
        refs = [r for r in refs if not os.path.basename(r).startswith("loc-")]
    people = [r for r in refs if who_of(os.path.basename(r))[0]]
    is_back = any(os.path.basename(r).endswith("-back.png") for r in refs) and sc["kind"] != "d"
    if sc["kind"] in FACE_KINDS and not is_back:  # 시범에도 얼굴 크롭(동일 인물 — 제19장 7 ①)  # 배경 없는 얼굴 크롭을 1번 참조로(동일 인물)
        face = []
        for r in people:
            k, _ = who_of(os.path.basename(r))
            f = f"{FACE_DIR}/{k}.png"
            if k in NO_FACE.get(sc["id"], ()) or (sc.get("ots") and r == people[-1]) or (sc["kind"] == "d" and r != people[0]):  # 전경 뒷모습 인물은 얼굴 크롭 제외  # 뒷모습 화자(비립싱크 VO)는 얼굴 크롭 제외 — 정면을 끌어온다
                continue
            if os.path.exists(os.path.join(ROOT, f)) and f not in face and not os.path.basename(r).endswith("-back.png"):
                face.append(f)
        refs = face + refs
    if sc["kind"] == "d" or sc.get("ots"):  # 전경 인물(두 번째 who)은 뒷모습 셀로
        if len(people) >= 2:
            k2, _ = who_of(os.path.basename(people[1]))
            back = f"{CELLS}/{k2}-back.png"
            refs = [r for r in refs if r != people[1]] + ([] if sc["id"] in NO_BACKCELL else [back])
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
    if sc["kind"] == "d":
        parts.append(FRAME_FIRST)
    if sc["id"] in SHOT_FIX:
        parts.append(SHOT_FIX[sc["id"]])
    if sc["kind"] == "d" and sc["id"] not in EMO_OVERRIDE and len(people) >= 2:
        parts.append(speaker_close(sc, people))
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    if sc["id"] in EMO_OVERRIDE:
        parts.append(EMO_OVERRIDE[sc["id"]])
    parts.append(sc["keyframe_prompt"])
    for r in sc["refs"]:
        b = os.path.basename(r)
        for k, v in LOC_NOTE.items():
            if b.startswith(k) and v not in parts:
                parts.append(v)
    if sc.get("lighting") in LIGHT_NOTE:
        parts.append(LIGHT_NOTE[sc["lighting"]])
    if sc["kind"] == "ins" and people:
        parts.append(INSERT)
    if is_back:
        parts.append(BACK)
    if sc.get("angle") in ANGLE and not (sc["angle"] == "SIDE" and is_back):
        parts.append(ANGLE[sc["angle"]])
    if sc.get("ja_overlay"):
        parts.append(BLANK)
    if sc.get("ots"):
        parts.append("REVERSE OVER-THE-SHOULDER COMPOSITION: the near-edge foreground person is the one SPEAKING, seen strictly from behind — only the "
                     "blurred back of the head and one shoulder at the frame edge, face and mouth NOT visible. The person beyond is the LISTENER at "
                     "three-quarter angle, eyes on the speaker, NEVER looking into the camera, face at least one third of the frame height, mouth closed. "
                     f"FOREGROUND IDENTITY LOCKED: the blurred foreground back is {dict(PEOPLE).get(who_of(os.path.basename(people[-1]))[0], 'the speaker')} — "
                     "no other person may stand in the foreground.")
    if sc["kind"] == "d":
        parts.append((OTS + " " + FACE13) if len(people) >= 2 else (FACE13 + " Only this one person is in the frame: NO other person, NO foreground shoulder or head."))
        if any(k in (sc.get("act") or "") for k in ("NOT smiling",)):
            parts.append("EXPRESSION AT 70 PERCENT: brows knotted, the corners of the mouth pulled down, eyes red and wet with pooled tears, jaw tight; absolutely NO smile.")
        if any(k in (sc.get("act") or "").lower() for k in ("fury", "shout", "scream", "explode")):
            parts.append(ANGER_CLOSED)
        parts.append("Mouth gently closed or barely parted (speech is added later); natural skin texture, both eyes sharp and symmetrical; earrings exactly as in the reference (none if the reference has none).")
    parts.append(REAL)
    parts.append(FULL)
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    prompt = " ".join(parts)
    for a, b in EYE_FIX:
        prompt = prompt.replace(a, b)
    if re.search(r"\btears?\b", re.sub(r"Negative:.*?\.(?= [A-Z])", "", prompt).replace("gel tears", "")):  # 네거티브의 「gel tears」는 제외
        prompt = prompt.replace("Absolutely no text, letters", TEAR_LINE + " " + EYE_SAFE + " Absolutely no text, letters")
    # 참조가 없는 컷(무인 시계·광장)은 edit 모델이 거부해 2회 연속 실패(S06a·S10a·S13b) → text-to-image
    model = "fal-ai/bytedance/seedream/v4/edit" if refs else "fal-ai/bytedance/seedream/v4/text-to-image"
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": prompt, "model": model, "extra": {"image_size": {"width": 2560, "height": 1440}}}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    stage, _, only = arg.partition(":")
    stage = stage.lower(); only = set(only.split(",")) if only else None
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    chars, missing = [], []
    for sc in sb["scenes"]:
        if not sc.get("keyframe"):
            continue
        if stage == "p" or stage.startswith("r"):
            if sc["id"] not in only:
                continue
        else:
            if (stage != "ab" and (stage == "a") != (sc["kind"] == "d" and bool(sc.get("line")))) or (only and sc["id"] not in only):
                continue
            if not only and sc["id"] in PILOT_DONE:
                continue
        c = build(sc, stage)
        missing += [f for f in c["refs"] if not os.path.exists(os.path.join(ROOT, f))]
        if only:
            c["count"] = 1 if sc["id"] in ONE_TAKE else 2
        chars.append(c)
    if (stage == "p" or stage.startswith("r")) and len(chars) != len(only):
        raise SystemExit(f"컷 일부 없음: {sorted(only - {c['id'] for c in chars})}")
    if missing:
        raise SystemExit("참조 파일 없음: " + ", ".join(sorted(set(missing))))
    name = "pilot" if stage == "p" else stage if stage.startswith("r") else stage + ("-r" if only else "")
    path = OUT.format(name)
    json.dump({"_설명": f"bento PHASE 4 키프레임 {name} (build_bento_keyframes.py 생성, 직접 수정 금지). seedream v4 edit 2560x1440, 약 0.03달러/장.", "_style_preset": sb["preset"], "characters": chars},
              open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(c["count"] for c in chars)
    print(f"{name} 키프레임 {len(chars)}컷 {n}장 → {path} (약 {n * 0.03:.2f}달러)")


if __name__ == "__main__":
    main()
