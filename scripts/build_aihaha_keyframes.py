#!/usr/bin/env python3
"""『母が遺したビデオレター』 PHASE 4 키프레임 스펙 생성기 — build_hikikomori_keyframes.py를 옮긴 것(내장 규칙 동일, 손으로 스펙을 고치지 않는다).

scripts/storyboard/aihaha.json(PHASE 3)을 읽어 generate-video.yml portraits_spec 스펙(scripts/portraits/aihaha-kf-<단계>.json)을 만든다.
단계: p:<id,…> 시범 / a 립싱크 컷 / b1·b2 나머지(실행 상한 때문에 반으로) / r<n>:<id,…> 재생성(컷당 2장)
이 작품 규칙: 참조 = aihaha-ref(고니감독님 승인 PHASE 2), 비립싱크 얼굴은 45° 셀 + GAZE(제19장 10①), 눈물·땀은 승인 기준 컷(제21장 11),
창이 보이는 컷은 비계 상태 고정(제21장 6), 손 인서트는 한 손 + 물건 하나(제19장 25), 부정문 대신 긍정문(제21장 10).
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
        bare = "" if k in GLASSES else " This person's ears and temples are bare — no eyewear arms."
        return f"Reference image {i} is the BACK VIEW of {PEOPLE[k]}: this person appears seen from behind exactly like this (hair, build); never show this person's face.{bare}"
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
    # r1 (시범 #1046 Kill Gate) — 손 개수·시선·두 사람 손 구분·구도
    "H0b": ("ONE HAND ONLY: her LEFT hand alone holds the tablet by its lower edge, tilted toward her; her right hand is out of frame, resting in her lap. "
            "Five separate fingers, the watch on that left wrist."),
    "H2b": ("ONE HAND ONLY: her LEFT hand alone lowers the tablet, tilted about 30 degrees above the low table with its glowing screen facing DOWN toward the wood, "
            "so the screen itself is hidden — only its plain black back and the cold light spilling onto the table are seen; her right hand is out of frame."),
    "H1": ("EYELINE LOCKED: her eyes look DOWN and toward the left edge of the frame at the tablet held below the frame at chest height; the lens sees her face from "
           "about 40 degrees to her right; her eyelids lowered toward the screen, the pupils never aimed at the lens."),
    "S01h": ("TWO DIFFERENT PEOPLE'S HANDS: from the LEFT, the mother's thin wrinkled 74-year-old hand in a lavender cardigan sleeve with the small brown-leather watch "
             "on her wrist; from the RIGHT, Yukiko's smooth 46-year-old hand in a beige knit sleeve, lying palm-down on the blanket underneath; the old hand rests on "
             "top of the younger hand. Exactly two hands, one from each side."),
    "S01b": ("ONE HAND ONLY: her RIGHT hand alone, pinching one small white pill between thumb and index finger just above an open compartment of the plain "
             "white weekly pill case on the low table; her left hand is out of frame. Five separate fingers."),
    "S01f": "PEOPLE LOCKED: exactly two people — the mother's blurred white-haired head and lavender shoulder at the near left edge, her thin hand pointing at the window; Yukiko beyond by the window.",
}
FRAMING_FIRST = {
    "S01f": "FRAMING LOCKED FIRST: MEDIUM SHOT from the waist up — Yukiko stands close to the window, her face at least one quarter of the frame height; NOT a full-body shot.",
}
GLASSES = {"yukiko": "thin silver wire-rim ROUND glasses", "shota": "thick black rectangular glasses"}
NAME = {"yukiko": "Yukiko", "sawako": "the mother (Sawako)", "tsuyoshi": "the uncle", "yoriko": "the aunt", "shota": "the cousin", "miyashita": "the detective",
        "ai-haha": "the AI mother"}


def eyewear_lock(keys):
    """안경 이동 방지(시범 #1046: 유키코 정면 셀의 안경이 어깨 너머 어머니로 옮겨 감 2/3컷, 유키코는 안경 소실)."""
    keys = [k for k in dict.fromkeys(keys) if k in NAME]
    if len(keys) < 2:
        return None
    wear = [f"{NAME[k]} wears {GLASSES[k]}" for k in keys if k in GLASSES]
    bare = [NAME[k] for k in keys if k not in GLASSES]
    if not wear or not bare:
        return None
    return ("EYEWEAR LOCKED: " + "; ".join(wear) + " — always, including in this frame; " + " and ".join(bare)
            + " ha" + ("s" if len(bare) == 1 else "ve") + " bare uncovered eyes and bare temples. The glasses belong only to "
            + " and ".join(NAME[k] for k in keys if k in GLASSES) + ".")
# 합격 컷 부분 편집(제7장 5 EDIT_FROM) — 시범 r1: H0a-1은 방·인물 합격, 창밖 타워만 실제 방 창과 다름 + 귀 장신구
EDIT = {
    "H0a": ("assets/portraits/aihaha-kf-r1/H0a-1.png", ["assets/portraits/aihaha-ref/cells/loc-window-view-finished-day.png"],
            "Edit image 1. Keep the elderly woman exactly unchanged — her face, smile, white hair, lavender cardigan and cream blouse — and keep the room, the beige "
            "wall, the armchair and the dark window frame exactly unchanged. Replace ONLY the view seen through the window glass with the view in image 2: the same "
            "pale tall apartment tower with horizontal balconies, its facade clean and finished, with the tiled-roof houses and green trees below it, overcast daylight. "
            "The tower stands just to the right of her head, its left edge partly hidden behind her hair. Her earlobes are bare skin: the small white stud on her "
            "left earlobe is gone. Same framing, same 16:9 size, photorealistic, no text."),
}
SEAT = "SEATED/FURNITURE LOCKED: seated people sit on zabuton or chairs pulled in to the table; no furniture passes through any body."


def build(sc):
    if sc["id"] in EDIT:
        base, extra, prompt = EDIT[sc["id"]]
        return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": [base] + extra, "prompt": prompt}
    refs = list(sc["refs"])
    people = [r for r in refs if who_of(os.path.basename(r))]
    is_back = bool(people) and os.path.basename(people[0]).endswith("-back.png") and sc["kind"] != "d"
    if len(refs) > MAX_REFS:
        refs = refs[:MAX_REFS]
    assert len(refs) <= MAX_REFS
    kp = sc["keyframe_prompt"]
    if sc["id"] == "H0a":
        # 극 중 AI 영상만 렌즈 정면(제21장 4) — PHASE 3 공통 립싱크 문장(30~40° 시선)과 충돌하므로 제거, 장소 판을 첫 참조로
        kp = kp.replace("Single speaker at 30 to 40 degrees from the camera axis, eyes toward the other person off-screen, NOT looking at the camera, "
                        "the face at least one third of the frame height, mouth closed. ", "")
        refs = [r for r in refs if not who_of(os.path.basename(r))] + [r for r in refs if who_of(os.path.basename(r))]
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
    if sc["kind"] == "d" and sc["id"] != "H0a":
        parts.append("FRAMING LOCKED FIRST: chest-up MEDIUM CLOSE-UP, the camera about one metre from the speaker, the speaker's face at least ONE THIRD of the "
                     "frame height, the top of the head near the top edge; NOT a wide shot, NO full body, NO room-wide view.")
    if sc["id"] in FRAMING_FIRST:
        parts.append(FRAMING_FIRST[sc["id"]])
    if sc["id"] == "H0a":
        parts.append("Reference image 1 is the BASE PLATE of the room: keep the same textured beige wall, the same dark-wood window frame and EXACTLY the same "
                     "finished pale tower with the same tiled-roof houses and green trees below it outside; the woman sits in the brown armchair in front of that window. "
                     "Nothing else in the room: no tablet, no devices, no frames.")
        parts += [describe(p, i + 1) for i, p in enumerate(refs) if i > 0]
    else:
        parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    ew = eyewear_lock([who_of(os.path.basename(r)) for r in refs])
    if ew:
        parts.append(ew)
    if sc["kind"] in ("face", "d", "pstill") and sc["id"] != "H0a":
        parts.append(GAZE_DEFAULT)
    if "phone" not in (sc["subject"] + " " + (sc.get("motion") or "")).lower():
        parts.append("Nobody holds a phone.")
    if sc["id"] in EMO_OVERRIDE:
        parts.append(EMO_OVERRIDE[sc["id"]])
    parts.append(kp)
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
