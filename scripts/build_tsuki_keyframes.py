#!/usr/bin/env python3
"""『月に帰った契約社員』(tsuki) PHASE 4 키프레임 스펙 생성기 — build_ashita_keyframes.py의 교훈 ①~⑱을 처음부터 규칙으로 내장.

scripts/storyboard/tsuki.json(PHASE 3)을 읽어 generate-video.yml portraits_spec 스펙을 만든다. 손으로 스펙을 고치지 않는다.
단계:
  p:<id,…>   시범 3컷(B안 어깨 너머 립싱크) — scripts/portraits/tsuki-kf-pilot.json
  a          립싱크(d) 컷 전부 — 참조 = 표정 셀 + 뒷모습 셀(전경 인물) + 로케이션
  b          나머지 — 얼굴이 보이는 컷은 배경 없는 얼굴 크롭(assets/portraits/tsuki-faces/<k>.png)을 1번 참조로
  r<n>:<id,…> 재생성(컷당 2장) — scripts/portraits/tsuki-kf-r<n>.json
내장 규칙(ashita 실증): 얼굴 1/3 이상·손 포함 어깨 너머(TIGHT 금지) / 분노는 입 닫힘 / 뒷모습 컷은 얼굴 참조 제거·뒷모습 셀만 /
어두운 장면은 조명 고정 문장이 로케이션 참조보다 우선 / 인서트는 얼굴·머리 없음 / 합성 면은 무지 / 연속 컷 앵글 고정 문장 / 16:9 띠 금지.
"""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "tsuki.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "tsuki-kf-{}.json")
FACE_DIR = "assets/portraits/tsuki-faces"
PEOPLE = [
    ("hikaru", "Takeuchi Hikaru (26, slim contract worker, short black hair with long bangs, mole under LEFT eye, NO glasses, NO earrings)"),
    ("washio", "Washio (59, heavy executive, greying slicked-back hair, thin round GOLD-rimmed glasses, NO earrings)"),
    ("hino", "Hino (46, manager, black 7:3 side-parted hair, thick eyebrows, NO glasses, NO earrings, white handkerchief)"),
    ("sakura", "Mizutani Sakura (24, office clerk, black chin-length bob with side bangs, NO glasses, small pearl stud earrings, NO name tag)"),
    ("shinoda", "Shinoda (52, city official, grey-streaked short hair, thin rectangular BLACK-framed glasses, beige trench coat, NO earrings)"),
    ("haru", "Takeuchi Haru (83, tiny old woman, white hair in a low bun, deeply wrinkled, NO glasses, tiny dark stud earrings, indigo apron)"),
]
FACE_KINDS = ("face", "d")
LOC_NOTE = {
    "loc-ctrl": "All control-room walls are bare; consoles have plain unlabeled panels; monitors show only abstract shapes, solid colour or are dark.",
    "loc-board": "The boardroom walls are bare: no posters, no plaques; the long table is glossy dark wood; the screen is plain grey.",
    "loc-dev": "Office walls are bare: no posters, no notices; screens show only abstract diagrams or solid colour with no lettering.",
    "loc-exec": "The executive office walls are bare; book spines are plain; no plaques, no framed certificates with writing.",
    "loc-bamboo": "The workshop walls are bare wood and plaster: no posters, no signs, no clutter; only bamboo, tools and strips.",
    "loc-hq": "The building and gate have NO company sign, NO lettering, NO flags.",
    "loc-yard": "Switchgear cabinets have blank smooth doors with NO labels, NO stickers, NO warning signs.",
}
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
FACE13 = ("Framing from mid-chest up: the speaker's head and shoulders fill the frame, the face about one third of the frame height and sharp, "
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
    "ctrl_black": "LIGHTING OVERRIDES THE LOCATION REFERENCE: blackout — ceiling lights off, most monitors dark; lit only by dim red emergency lamps; mid-tones still visible, faces readable, not pure black.",
    "ctrl_red": "LIGHTING OVERRIDES THE LOCATION REFERENCE: every monitor solid red, deep red light on faces, ceiling lights dim.",
    "dev_red": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, the video wall solid red washing the room in red, cold fluorescent overhead, windows black.",
    "dev_green": "LIGHTING OVERRIDES THE LOCATION REFERENCE: dawn, pale daylight from the windows, the video wall solid calm green.",
    "exec_night": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, windows black with city lights, ceiling lights off; the only light is one warm desk lamp.",
    "yard": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night; warm sodium lamps plus a cold blue full-moon rim light; sky dark.",
    "hq_moon": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night under a huge full moon; wet pavement reflections; sky dark blue.",
    "moon": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, cold blue full-moon light; one warm window glow.",
    "dusk": "LIGHTING OVERRIDES THE LOCATION REFERENCE: golden dusk, low warm sun, long shadows.",
    "dawn": "LIGHTING OVERRIDES THE LOCATION REFERENCE: pale blue dawn, thin mist, no sodium lamps.",
    "board_night": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, warm interior lights, city lights beyond the glass, sky black.",
}
ANGER_CLOSED = ("Fury shown only in the eyes, furrowed brow, flared nostrils and clenched jaw: lips pressed together, mouth CLOSED, NOT shouting "
                "(speech is added later).")


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


def build(sc, stage):
    refs = list(sc["refs"])
    people = [r for r in refs if who_of(os.path.basename(r))[0]]
    is_back = any(os.path.basename(r).endswith("-fullback.png") for r in refs) and sc["kind"] != "d"
    if stage != "p" and sc["kind"] in FACE_KINDS and not is_back:  # 배경 없는 얼굴 크롭을 1번 참조로(동일 인물)
        face = []
        for r in people:
            k, _ = who_of(os.path.basename(r))
            f = f"{FACE_DIR}/{k}.png"
            if os.path.exists(os.path.join(ROOT, f)) and f not in face and not os.path.basename(r).endswith("-fullback.png"):
                face.append(f)
        refs = face + refs
    if sc["kind"] == "d":  # 전경 인물(두 번째 who)은 뒷모습 셀로
        if len(people) >= 2:
            k2, _ = who_of(os.path.basename(people[1]))
            back = f"assets/portraits/tsuki-cast/cells/{k2}-fullback.png"
            refs = [r for r in refs if r != people[1]] + [back]
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
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
    if sc["kind"] == "d":
        parts.append(OTS + " " + FACE13)
        if any(k in (sc.get("act") or "").lower() for k in ("fury", "shout", "scream", "explode")):
            parts.append(ANGER_CLOSED)
        parts.append("Mouth gently closed or barely parted (speech is added later); natural skin texture, both eyes sharp and symmetrical; no earrings.")
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
    json.dump({"_설명": f"tsuki PHASE 4 키프레임 {name} (build_tsuki_keyframes.py 생성, 직접 수정 금지).", "_style_preset": sb["preset"], "characters": chars},
              open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(c["count"] for c in chars)
    print(f"{name} 키프레임 {len(chars)}컷 {n}장 → {path} (약 {n * 0.04:.2f}달러)")


if __name__ == "__main__":
    main()
