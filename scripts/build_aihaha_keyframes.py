#!/usr/bin/env python3
"""『母が遺したビデオレター』 PHASE 4 키프레임 스펙 생성기 — build_hikikomori_keyframes.py를 옮긴 것(내장 규칙 동일, 손으로 스펙을 고치지 않는다).

scripts/storyboard/aihaha.json(PHASE 3)을 읽어 generate-video.yml portraits_spec 스펙(scripts/portraits/aihaha-kf-<단계>.json)을 만든다.
단계: p:<id,…> 시범 / a 립싱크 컷 / b1·b2 나머지(실행 상한 때문에 반으로) / r<n>:<id,…> 재생성(컷당 2장)
이 작품 규칙: 참조 = aihaha-ref(고니감독님 승인 PHASE 2), 비립싱크 얼굴은 45° 셀 + GAZE(제19장 10①), 눈물·땀은 승인 기준 컷(제20장 11),
창이 보이는 컷은 비계 상태 고정(제20장 6), 손 인서트는 한 손 + 물건 하나(제19장 25), 부정문 대신 긍정문(제20장 10).
사용법: python3 scripts/build_aihaha_keyframes.py p:H0a,H0b,…   → scripts/portraits/aihaha-kf-p.json
"""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "aihaha.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "aihaha-kf-{}.json")
MAX_REFS = 10
PEOPLE = {
    "yukiko": "Saeki Yukiko (46, low ponytail, thin silver wire-rim ROUND glasses, bare earlobes)",
    "sawako": "Saeki Sawako (74, short soft white permed hair, exactly one small mole on her right cheek, nothing on her face, bare earlobes)",
    "ai-haha": "the uncanny AI deepfake version of the mother (airbrushed, perfectly symmetrical, glassy staring eyes)",
    "tsuyoshi": "Ono Tsuyoshi (66, heavy-set, receding grey hair slicked back, jowls, nothing on his face, bare earlobes)",
    "yoriko": "Ono Yoriko (63, brown wavy bob, one strand pearl necklace, bare earlobes)",
    "shota": "Ono Shota (36, slim, side-swept black top with clipped sides, thick black rectangular glasses)",
    "miyashita": "Detective Miyashita (52, very short salt-and-pepper hair, square jaw, nothing on his face, plain lapels)",
}


def who_of(name):
    n = name.replace("tear-standard-", "").replace("sweat-standard-", "")
    for k in sorted(PEOPLE, key=len, reverse=True):
        if n.startswith(k):
            return k
    return None


def describe(path, i):
    b = os.path.basename(path); k = who_of(b)
    if b.startswith("tear-standard"):
        return (f"Reference image {i} is the APPROVED TEAR LOOK of {PEOPLE[k]}: reproduce exactly this face and exactly this kind of real tear — "
                "pink eye rims, glistening lower lids, at most one thin transparent track on one cheek, matte skin; ignore its background.")
    if b.startswith("sweat-standard"):
        return f"Reference image {i} is the APPROVED SWEAT LOOK of {PEOPLE[k]}: reproduce exactly this face and this subtle natural sweat; ignore its background."
    if k and b.endswith("-back.png"):
        return f"Reference image {i} is the BACK VIEW of {PEOPLE[k]}: this person appears seen from behind exactly like this (hair, build); never show this person's face."
    if k and any(w in b for w in ("mourning", "coat", "golf", "blouse", "hoodie")):
        return f"Reference image {i} is the WARDROBE reference of {PEOPLE[k]}: copy this exact outfit and the same face; ignore its white background and panel layout."
    if k:
        return (f"Reference image {i} is the approved identity photo of {PEOPLE[k]}: copy this exact face, hairstyle, eyewear and age; the WARDROBE follows "
                "the [CHARACTER] text below; ignore its white background and framing.")
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing, window view and light direction; "
            "ignore any borders or panel layout.")


FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox."
FACE13 = ("MEDIUM CLOSE-UP from mid-chest up: the speaker's head and shoulders fill the centre of the frame, the face about one third of the frame height and sharp, "
          "turned about 35 degrees toward the other person (never straight at the camera, never full profile); hands and what they hold visible at the bottom; "
          "50mm lens, f/2.0, shallow depth of field.")
OTS = ("Over-the-shoulder two-shot: the listener at the near foreground edge seen strictly from behind — only the back of the head and one shoulder, soft and "
       "out of focus; the listener's face NOT visible.")
INSERT = ("EXTREME CLOSE-UP INSERT: only the hand(s) and object described fill the frame; the arm continues naturally to the sleeve at the frame edge; "
          "NO face and NO head anywhere in the frame. Shallow depth of field.")
BACK = "The person is seen strictly from behind — only the back of the head, hair and shoulders; the face turned away; the mouth never visible."
ANGLE = {"HA": "CAMERA: high angle, looking down.", "OH": "CAMERA: directly overhead, looking straight down.", "BE": "CAMERA: bird's-eye view straight down from the ceiling.",
         "LA": "CAMERA: low angle, looking up from about waist height.", "SIDE": "CAMERA: from the side or behind — the face in side profile or hidden, NOT facing the camera."}
BLANK = ("Every paper, form, envelope, calendar, book page, phone screen, TV and monitor surface is completely blank and clean: NO printed lines, NO characters, "
         "NO numerals (Japanese text and screen content are composited later).")
LIGHT_NOTE = {"sep_day": "LIGHTING OVERRIDES THE LOCATION REFERENCE: early-autumn afternoon daylight, the ceiling light off.",
              "wake": "LIGHTING OVERRIDES THE LOCATION REFERENCE: warm 3200K tungsten of a home wake, faces half in shadow, incense haze.",
              "police_red": "LIGHTING OVERRIDES THE LOCATION REFERENCE: cold ceiling fluorescent plus slow red and blue police light reflections on the window glass.",
              "warm_liv": "LIGHTING OVERRIDES THE LOCATION REFERENCE: the round ceiling light is OFF; only a warm table lamp.",
              "cold_liv": "LIGHTING: the round ceiling fluorescent light is ON, cold flat white light from above.",
              "night_lamp": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, one warm floor lamp only, deep shadows."}
LOC_NOTE = "The rooms have NO calendars with writing, NO posters, NO notices, NO name plates; everything plain."
GAZE_DEFAULT = "GAZE LOCKED: nobody in the frame looks into the camera lens; eyes stay on the person or object described, head turned 30 to 40 degrees from the lens."
EMO_OVERRIDE = {
    "H0a": ("THIS IS A HOME VIDEO LETTER STILL: the elderly woman sits centred on a chair facing the lens dead-on (the ONLY shot where someone looks into the lens), chest-up, "
            "perfectly symmetrical; behind her the window shows the SAME finished tower as the location reference (no scaffolding, no mesh, no cranes)."),
    "S01e": "PEOPLE LOCKED: exactly two people — the mother seated in the brown armchair by the window, and Yukiko's blurred shoulder and ponytail at the near edge.",
    "S01g": "PEOPLE LOCKED: exactly two people — Yukiko kneeling beside the armchair, and the mother's blurred white-haired head and lavender shoulder at the near edge.",
    "S01h": "Exactly two hands: the mother's old hand wearing the small brown-leather watch resting on Yukiko's younger hand on a blanket; nothing else.",
    "S01a": "Exactly two people seen from behind: Yukiko standing and pushing a plain wheelchair, the white-haired mother seated in it; small in the wide frame.",
    "S02a": "The framed portrait on the altar shows a plain soft pale surface inside the frame (the photograph is composited later).",
    "S02b": "PEOPLE LOCKED: exactly three people at the low table — the uncle (black mourning suit), the aunt (black mourning dress, pearls), the cousin (black suit, black glasses).",
    "S02g": "PEOPLE LOCKED: the uncle, aunt and cousin at the low table, and Yukiko alone kneeling near the altar; nobody else.",
    "S03a": "Exactly one person: the aunt in a black mourning dress with a black handbag, seen from a high corner; nobody else in the hallway.",
    "S08k": "The framed portrait on the small altar shows a plain soft pale surface inside the frame (the photograph is composited later).",
    "S11j": "Exactly three people slumped on the sofa seen from directly above; nobody else.",
    "S13d": "Yukiko alone, close-up, the morning window light from the left exactly like the approved tear reference.",
}
SEAT = "SEATED/FURNITURE LOCKED: seated people sit on zabuton or chairs pulled in to the table; no furniture passes through any body."


def build(sc):
    refs = list(sc["refs"])
    people = [r for r in refs if who_of(os.path.basename(r))]
    is_back = bool(people) and os.path.basename(people[0]).endswith("-back.png") and sc["kind"] != "d"
    if len(refs) > MAX_REFS:
        refs = refs[:MAX_REFS]
    assert len(refs) <= MAX_REFS
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    if sc["kind"] == "d" and sc["id"] != "H0a":
        parts.append("FRAMING LOCKED FIRST: chest-up MEDIUM CLOSE-UP, the speaker's face at least ONE THIRD of the frame height; NOT a wide shot, NO full body.")
    if sc["kind"] in ("face", "d", "pstill") and sc["id"] != "H0a":
        parts.append(GAZE_DEFAULT)
    if "phone" not in (sc["subject"] + " " + (sc.get("motion") or "")).lower():
        parts.append("Nobody holds a phone.")
    if sc["id"] in EMO_OVERRIDE:
        parts.append(EMO_OVERRIDE[sc["id"]])
    parts.append(sc["keyframe_prompt"])
    parts.append(LOC_NOTE)
    if sc.get("lighting") in LIGHT_NOTE:
        parts.append(LIGHT_NOTE[sc["lighting"]])
    if sc["kind"] in ("ins", "estill") and people:
        parts.append(INSERT)
    if is_back:
        parts.append(BACK)
    if sc.get("angle") in ANGLE and not (sc["angle"] == "SIDE" and is_back):
        parts.append(ANGLE[sc["angle"]])
    if sc.get("ja_overlay"):
        parts.append(BLANK)
    if "SEATED" in (sc.get("motion") or "") or "seated" in sc["subject"].lower():
        parts.append(SEAT)
    if sc.get("ots"):
        parts.append("REVERSE OVER-THE-SHOULDER COMPOSITION: the near-edge foreground person is the SPEAKER seen strictly from behind (blurred back of the head and one "
                     "shoulder, face NOT visible); the LISTENER beyond at three-quarter angle, eyes on the speaker, never into the lens, face at least one third of the frame height.")
    if sc["kind"] == "d" and sc["id"] != "H0a":
        parts.append((OTS + " " + FACE13) if len(people) >= 2 else (FACE13 + " Only this one person is in the frame: NO foreground shoulder or head."))
        if "NOT smiling" in (sc.get("act") or ""):
            parts.append("EXPRESSION AT 70 PERCENT: brows knotted, the corners of the mouth pulled down, jaw tight; absolutely NO smile.")
        parts.append("Mouth gently closed (speech is added later); natural skin texture with pores, both eyes sharp and symmetrical.")
    parts.append(FULL)
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": " ".join(parts)}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    stage, _, only = arg.partition(":")
    only = set(only.split(",")) if only else None
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    chars, missing = [], []
    ids_b = [x["id"] for x in sb["scenes"] if x.get("keyframe") and not (x["kind"] == "d" and x.get("line"))]
    for sc in sb["scenes"]:
        if not sc.get("keyframe"):
            continue
        if stage == "p" or stage.startswith("r"):
            if sc["id"] not in only:
                continue
        else:
            if (stage == "a") != (sc["kind"] == "d" and bool(sc.get("line"))):
                continue
            if stage in ("b1", "b2") and (ids_b.index(sc["id"]) < len(ids_b) // 2) != (stage == "b1"):
                continue
            if only and sc["id"] in only:  # 제외 목록(시범 완료분)
                continue
        c = build(sc)
        if stage.startswith("r"):
            c["count"] = 2
        missing += [f for f in c["refs"] if not os.path.exists(os.path.join(ROOT, f))]
        chars.append(c)
    assert not missing, f"참조 파일 없음: {sorted(set(missing))}"
    out = OUT.format(stage)
    json.dump({"_설명": f"『母が遺したビデオレター』 PHASE 4 키프레임 {stage} — {len(chars)}장(build_aihaha_keyframes.py 생성). 약 {len(chars) * 0.04 * (2 if stage.startswith('r') else 1):.2f}달러.",
               "characters": chars}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(out, len(chars))


if __name__ == "__main__":
    main()
