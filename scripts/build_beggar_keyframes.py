#!/usr/bin/env python3
"""『みすぼらしい老人は、財閥会長だった』 PHASE 4 키프레임 스펙 생성기 — build_tsuki_keyframes.py를 옮긴 것(내장 규칙 동일).

scripts/storyboard/beggar-chairman.json(PHASE 3)을 읽어 generate-video.yml portraits_spec 스펙을 만든다. 손으로 스펙을 고치지 않는다.
단계: p:<id,…> 시범 / a 립싱크 컷 / b 나머지 / r<n>:<id,…> 재생성(컷당 2장)
이 작품 차이: 귀걸이는 승인 시트의 고정 특징(岩城 검은 스터드·間宮 은 스터드·ちひろ 작은 검은 스터드)이므로 「no earrings」를 쓰지 않는다.
눈물·땀(제18장 1): 생성기 문장(TEARS/SWEAT/WET_HOLD)을 그대로 쓰고, 립싱크 컷은 흐르지 않는 눈물만.
"""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "beggar-chairman.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "beggar-kf-{}.json")
FACE_DIR = "assets/portraits/beggar-faces"
CELLS = "assets/portraits/beggar-cast/cells"
PEOPLE = [
    ("genzo", "Takamiya Genzo (78, lean, close-cropped white hair, short white beard, one small mole above LEFT eyebrow, NO glasses)"),
    ("iwaki", "Iwaki (45, restaurant manager, black hair slicked back, thin black moustache, NO glasses, small black stud earrings in both ears)"),
    ("mamiya", "Mamiya (32, stocky, round face, reddish-brown hair short on the sides, small silver stud earrings, NO glasses)"),
    ("chihiro", "Harukawa Chihiro (21, waitress, straight blunt bangs, low black ponytail, NO glasses, tiny black stud earrings)"),
    ("sakaki", "Sakaki (64, secretary, combed-back silver-white hair, short grey moustache, thin SILVER-rimmed glasses)"),
    ("boy", "the boy (8, winter 1955, close-shaved head, chapped red cheeks, patched dark wool jacket, NO glasses)"),
]
FACE_KINDS = ("face", "d")
PILOT_DONE = {"S13i", "S12f"}  # 시범 승인(assets/portraits/beggar-kf-pilot/*-fixed). S11i는 표정 강화로 a단계에서 재생성
LOC_NOTE = {
    "loc-hall": "The restaurant walls are bare dark wood: no posters, no menus on the wall, no signs; tables have plain white cloths and plain ceramic.",
    "loc-entrance": "The entrance has a plain indigo noren with NO print, a blank closed book, NO sign boards.",
    "loc-hotel": "The hotel has NO name, NO sign, NO lettering anywhere.",
    "loc-kitchen-car": "No labels on containers, no stickers, no screens with text.",
    "loc-udonya-1955": "The 1955 shop has a plain unprinted cloth noren and NO signboard, NO paper notices with writing.",
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
    "corner": "LIGHTING OVERRIDES THE LOCATION REFERENCE: the dim corner by the restroom corridor, cold flat fluorescent spill, the warm pendants far away, faces readable.",
    "tension": "LIGHTING OVERRIDES THE LOCATION REFERENCE: cold overhead light falling vertically, harsh shadows under the brows, warm pendants dimmed.",
    "reveal": "LIGHTING OVERRIDES THE LOCATION REFERENCE: strong warm backlight rim from the tall window behind the old man, faces still readable.",
    "sepia": "LIGHTING OVERRIDES THE LOCATION REFERENCE: winter night 1955, warm bare-bulb glow, cold blue snow light, sepia period tone.",
    "car_n": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, city lights streaking across the window, faces readable.",
    "dusk": "LIGHTING OVERRIDES THE LOCATION REFERENCE: golden hour, low warm sun, long shadows.",
}
EMO_OVERRIDE = {
    "H3": "NO title, NO words, NO letters anywhere in the image; the empty sky above the tower is clean.",
    "S04a": "NO captions, NO labels, NO words anywhere.",
    "S07d": "FURNITURE LOCKED: the old man sits properly ON one wooden chair that is fully behind the far side of the small table, his legs under the table; the chair is not in front of him and does not pass through his body or legs; NO extra empty chair between him and the camera. Correct, solid furniture geometry.",
    "S07i": "FURNITURE LOCKED: correct, solid furniture geometry — chairs stand on the floor behind or beside the table, no chair passes through any person, no floating chair legs.",
    "S05l": "SPEAKER LOCKED: Iwaki (black slicked-back hair, thin black moustache, black three-piece suit, black sleeves, NOT a white shirt sleeve) STANDS beside the small corner table by the restroom corridor and is the face at three-quarter angle, his hand setting a plain black leather check presenter on the white tablecloth; the old man SITS at the table and appears ONLY as a blurred back of white hair and grey jacket shoulder at the near left edge. NO writing on the folder.",
    "S11b": "POSE LOCKED: Iwaki is STANDING upright in the dim restaurant corner aisle, chest-up, both arms down at his sides, facing the old man in the foreground; NO table in front of him, NO cards, NO other people or silhouettes beyond, NO earrings.",
    "S04d": "NO captions, NO labels, NO words anywhere.",
    "S04c": "SPEAKER LOCKED: Iwaki (black slicked-back hair, thin black moustache, black three-piece suit) has stepped out from the podium into the doorway and is the face at three-quarter angle, his right arm stretched straight out across the entrance with the palm raised toward the old man, blocking him; the old man appears ONLY as a blurred back of white hair and grey jacket shoulder at the near left edge, stopped in front of the raised palm.",
    "S04b": "Iwaki is at three-quarter angle turned toward the doorway on the LEFT, looking toward the arriving guest off-screen left, NOT looking at the camera. Only this one person.",
    "S04f": "Iwaki is at three-quarter angle facing screen LEFT toward the old man in the foreground, NOT looking at the camera.",
    "S04i": "SPEAKER LOCKED: Iwaki (black slicked-back hair, thin black moustache, black three-piece suit) is the face at three-quarter angle, jerking his chin toward the back of the hall; the old man appears ONLY as a blurred back of white hair and grey jacket shoulder at the near left edge. Both people STANDING.",
    "S04e": "SPEAKER LOCKED: Iwaki (black slicked-back hair, thin black moustache, black three-piece suit) stands behind the podium scoffing, both people STANDING (the old man is NOT seated), the face at three-quarter angle; the old man appears ONLY as a blurred back of white hair at the near left edge.",
    "S07b": "PEOPLE LOCKED: exactly two people. Chihiro (young woman, black low ponytail, white blouse, navy apron) is the face at three-quarter angle setting down tea; the ONLY other person is the old man seen strictly from behind (white hair, grey jacket) at the near left edge. Do NOT show the old man's face.",
    "S07k": "PEOPLE LOCKED: the near-edge foreground person is the OLD MAN seen from behind (close-cropped WHITE hair, grey jacket), NOT a dark-haired man.",
    "S09b": "NO white box, NO card, NO rectangle, NO text anywhere in the frame.",
    "S10p": "WARDROBE LOCKED: Chihiro wears NO apron any more (it was taken off), only a plain white long-sleeve blouse.",
    "S10t": "WARDROBE LOCKED: Chihiro wears NO apron any more (it was taken off), only a plain white long-sleeve blouse.",
    "S10r": "ACTION LOCKED: Iwaki grips the old man's frayed grey jacket sleeve with one hand and yanks it sharply toward the door, leaning in with contempt, mouth closed; the old man is pulled half off balance but his face stays calm and dignified; low angle; NOT posing side by side.",
    "S11f": "INSERT ONLY: polished black leather shoes and black trouser hems striding across a white marble lobby floor, camera at ground level; NO torso, NO hands, NO envelope, NO face.",
    "S12a": "LOCATION LOCKED: the SAME dark-wood restaurant hall with white tablecloths and amber pendant lamps as the reference; a heavy dark wooden door at the far end swinging open; NO posters, NO light wood, NO counter seats, NO signs.",
    "S13a": "POSE LOCKED: Genzo is STANDING upright (he has risen from his chair), tall and calm, backlit by the bright window behind him; low angle close-up; NOT seated, NO bowl.",
    "S13e": "POSE LOCKED: Genzo is STANDING upright in the hall, looking slowly around, backlit; low angle medium shot; NOT seated, NO bowl in his hands.",
    "S13g": "FRAMING LOCKED: CLOSE-UP of Genzo STANDING, his face about half of the frame height, gazing into the distance, warm window rim light; NOT seated, NOT a wide shot.",
    "S14a": "POSE LOCKED: Iwaki is sinking DOWN onto his knees on the dark wooden floor, knees touching the floor, hands trembling; high angle; NOT standing.",
    "S14b": "LOCATION LOCKED: the SAME dark-wood restaurant with white tablecloths. Bird's-eye view straight down from the ceiling: Iwaki in a black suit prostrate in dogeza, forehead on the dark wooden floor between white-clothed tables; NO light wood, NO counter, NO bright windows.",
    "S14c": "POSE LOCKED: Iwaki is ON HIS KNEES on the floor, lifting only his head to look UP at the standing old man (only the old man's grey trouser legs, blurred, at the near edge), begging, tears and sweat, NO smile; high angle looking down at Iwaki.",
    "S14d": "POSE LOCKED: Genzo is STANDING, looking DOWN at the man kneeling below him (only the kneeling man's blurred black hair at the bottom edge); low angle; NOT seated.",
    "S14f": "POSE LOCKED: Genzo is STANDING, close-up at three-quarter angle, calm and stern; low angle; NOT seated, NO black bars.",
    "S14g": "A PERSON MUST BE IN FRAME: low-angle close-up of Genzo STANDING in the corner, listening without expression.",
    "S15c": "POSE LOCKED: Genzo is SEATED on the wooden chair at the corner table (NOT on the floor), close-up, smiling warmly, eyes wet.",
    "S15f": "FRAMING LOCKED: CLOSE-UP of Genzo seated at the table chewing udon, his face about half of the frame height, eyes closed, a clear tear bead on the lower lid; NOT a wide shot.",
    "S17a": "NO white box, NO card, NO rectangle, NO text anywhere.",
    "S06c": "INSERT ONLY: a gloved hand holding a smartphone in the back seat of a car; the screen is blank and glowing; NO face.",
    "S13i": "FRAMING LOCKED: CLOSE-UP, camera about 1 metre from Genzo, his face fills about HALF of the frame height, cut at the upper chest, NOT a wide shot, NO table, NO papers, NO cards in frame. EXPRESSION LOCKED: Genzo's eyes are wet and glistening with tears pooled on the lower lids but NOT running; a quiet, deep, sorrowful dignity; lips closed; a warm window rim light behind him.",
    "S12f": "FRAMING LOCKED: Iwaki is STANDING (not seated), medium close-up cut at mid-chest, camera about 1.2 metres away, his face about one third of the frame height, NO cup, NO papers; the frame is NOT rotated (the tilt is added in editing). EXPRESSION LOCKED: Iwaki is in SHOCK — face gone pale, eyes wide, lips parted and trembling slightly, fine beads of cold sweat on his forehead and temples, NO smile; no tilt.",
    "S11i": "POSE LOCKED: Chihiro stands with both arms spread wide in front of the old man (his blurred back at the near edge), eyes wet and brimming with tears that do not run, jaw set, protective and brave.",
}
ANGER_CLOSED = ("Fury shown only in the wide-open glaring eyes, furrowed brow, flared nostrils and clenched jaw: eyes OPEN and fixed on the listener, "
                "lips pressed together, mouth CLOSED, NOT shouting (speech is added later).")


def who_of(name):
    return next(((k, v) for k, v in PEOPLE if name.startswith(k + "-")), (None, None))


def describe(path, i):
    name = os.path.basename(path)
    if path.startswith(FACE_DIR):
        who = dict(PEOPLE).get(name[:-4], "the character")
        return (f"Reference image {i} is a tight face crop of {who}: reproduce exactly this face, age, hairstyle and eyewear; identity ONLY — "
                "do NOT copy its camera angle, background or lighting.")
    k, v = who_of(name)
    if k and name.endswith("-fullback.png"):
        return f"Reference image {i} is the BACK VIEW of {v}: this person appears seen from behind exactly like this (hair, wardrobe); do not show this person's face."
    if k:
        return (f"Reference image {i} is the character sheet cell of {v}: copy this exact face, hairstyle, eyewear, wardrobe and age; ignore its "
                "background, framing and any sheet layout.")
    if name.startswith("props-"):
        return f"Reference image {i} is the prop reference: copy the object's exact shape, size and material; ignore any background or labels."
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing and light direction; ignore any "
            "borders, labels or wall papers.")


NO_FACE = {}


def build(sc, stage):
    refs = list(sc["refs"])
    people = [r for r in refs if who_of(os.path.basename(r))[0]]
    is_back = any(os.path.basename(r).endswith("-fullback.png") for r in refs) and sc["kind"] != "d"
    if stage != "p" and sc["kind"] in FACE_KINDS and not is_back:  # 배경 없는 얼굴 크롭을 1번 참조로(동일 인물)
        face = []
        for r in people:
            k, _ = who_of(os.path.basename(r))
            f = f"{FACE_DIR}/{k}.png"
            if k in NO_FACE.get(sc["id"], ()) or (sc.get("ots") and r == people[-1]):  # 뒷모습 화자(비립싱크 VO)는 얼굴 크롭 제외 — 정면을 끌어온다
                continue
            if os.path.exists(os.path.join(ROOT, f)) and f not in face and not os.path.basename(r).endswith("-fullback.png"):
                face.append(f)
        refs = face + refs
    if sc["kind"] == "d" or sc.get("ots"):  # 전경 인물(두 번째 who)은 뒷모습 셀로
        if len(people) >= 2:
            k2, _ = who_of(os.path.basename(people[1]))
            back = f"{CELLS}/{k2}-fullback.png"
            refs = [r for r in refs if r != people[1]] + [back]
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
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
    parts.append(FULL)
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": " ".join(parts)}


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
            if (stage == "a") != (sc["kind"] == "d" and bool(sc.get("line"))) or (only and sc["id"] not in only):
                continue
            if not only and sc["id"] in PILOT_DONE:
                continue
        c = build(sc, stage)
        missing += [f for f in c["refs"] if not os.path.exists(os.path.join(ROOT, f))]
        if only and stage != "p":
            c["count"] = 2
        chars.append(c)
    if (stage == "p" or stage.startswith("r")) and len(chars) != len(only):
        raise SystemExit(f"컷 일부 없음: {sorted(only - {c['id'] for c in chars})}")
    if missing:
        raise SystemExit("참조 파일 없음: " + ", ".join(sorted(set(missing))))
    name = "pilot" if stage == "p" else stage if stage.startswith("r") else stage + ("-r" if only else "")
    path = OUT.format(name)
    json.dump({"_설명": f"beggar-chairman PHASE 4 키프레임 {name} (build_beggar_keyframes.py 생성, 직접 수정 금지).", "_style_preset": sb["preset"], "characters": chars},
              open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(c["count"] for c in chars)
    print(f"{name} 키프레임 {len(chars)}컷 {n}장 → {path} (약 {n * 0.04:.2f}달러)")


if __name__ == "__main__":
    main()
