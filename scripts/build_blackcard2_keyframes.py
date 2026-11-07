#!/usr/bin/env python3
"""『ブラックカード』(第2話) PHASE 4 키프레임 스펙 생성기 — build_blackcard_keyframes.py(1화)를 옮긴 것(내장 규칙 동일).

scripts/storyboard/blackcard2.json(PHASE 3)을 읽어 generate-video.yml portraits_spec 스펙을 만든다. 손으로 스펙을 고치지 않는다.
단계: a 립싱크 컷 / b1·b2 나머지(90분 실행 상한 때문에 반으로) / p:<id,…> 시범 / r<n>:<id,…> 재생성(컷당 2장)
2화 차이: 셀 폴더 2개(blackcard2-cast 신규 인물·장소 + blackcard-cast 1화 켄지·美咲·장소), 얼굴 크롭 blackcard2-faces(1화 3명 복사 + 永瀬·鷺沼·警備員·三好 정면 셀 크롭),
시범도 얼굴 크롭을 넣는다(1화 시범은 크롭 생성 전). 조명은 PHASE 3 프롬프트 [SETTING]에 이미 있고, 1화 장소 셀을 다른 시간대로 쓰는 장면만 LIGHT_NOTE로 덮어쓴다.
모든 글자(非通知·住民票·명부·서류·휴대폰·명함)는 무지로 생성 → PHASE 4 합성. 창업자 초상(S24j)은 얼굴 비노출(유리 반사).
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "blackcard2.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "blackcard2-kf-{}.json")
FACE_DIR = "assets/portraits/blackcard2-faces"
CELLS = "assets/portraits/blackcard2-cast/cells"
CELLS1 = "assets/portraits/blackcard-cast/cells"  # 1화 셀(켄지·美咲·장소)


def in_cells(r):
    return r.startswith((CELLS + "/", CELLS1 + "/"))


PEOPLE = [
    ("kenji-wet", "Takahashi Kenji (43, lean gaunt face, short black hair with a little grey, short dark stubble, a small graze above the LEFT eyebrow, NO glasses, NO earrings) — rain-soaked"),
    ("kenji-suit", "Takahashi Kenji (43, lean gaunt face, short black hair with a little grey, short dark stubble, a small graze above the LEFT eyebrow, NO glasses, NO earrings)"),
    ("shibata", "Shibata (45, broad confident face, slicked-back black hair, thin RIMLESS glasses, clean-shaven, NO earrings, NO lapel pin, NO mole)"),
    ("misaki", "Misaki (40, chin-length straight black bob with bangs, exactly ONE small mole on the LEFT cheek, NO glasses, NO earrings)"),
    ("nagase", "Nagase (58, neatly side-parted SILVER-GREY hair, thin narrow face, thin GOLD metal-frame rectangular glasses, clean-shaven, NO earrings, NO lapel pin, NO badge)"),
    ("sagisuma", "Sagisuma (late sixties, sturdy, thinning grey hair combed straight back, deep forehead lines, heavy-lidded tired eyes, short grey stubble, NO glasses, BOTH EARLOBES COMPLETELY BARE AND SMOOTH — no earrings, no ear studs, no piercings)"),
    ("keibi", "the night security guard (about 55, greying temples under a plain navy cap, calm lined face, NO glasses, clean-shaven, NO badge, NO name tag)"),
    ("miyoshi", "Miyoshi (39, short neat black hair, gentle oval face, clean-shaven, NO glasses, NO earrings)"),
]
FACE_OF = {"kenji-wet": "kenji", "kenji-suit": "kenji"}
FACE_KINDS = ("face", "d")
MAX_REFS = 10
PILOT_DONE = set()
LOC_NOTE = {
    "loc-backdoor": "NO notices, posters or signs on the walls or the booth; NO readable text anywhere; wet reflections only.",
    "loc-meeting": "NO signs, NO whiteboard writing, NO name plates; the wall clock face is blank; all papers blank.",
    "loc-car": "RIGHT-hand drive, ONE steering wheel on the RIGHT, two front seats, a rear bench with a centre armrest; the dashboard screen and clock are blank dark panels with NO digits; NO logos.",
    "loc-archive": "NO labels on the shelves, boxes or binders; every file spine and box is plain and blank; NO signs, NO readable text; NO LED strips.",
    "loc-miyoshi-apt": "NO calendars, NO posters, NO notes with writing, NO name plate on the door; the room nearly empty.",
    "loc-shimbashi-bar": "NO menus with text, NO labels on bottles, NO signs, NO posters; plain wooden counter.",
    "loc-topfloor": "NO name plates, NO logos, NO framed text; all papers and screens blank; the city glow outside out of focus.",
    "loc-elevator": "The floor indicator and button panel are blank with NO numbers, NO letters; NO signs.",
    "loc-flashback": "NO signs, NO posters, NO name tags; all papers blank.",
    "props-card": "The card is matte black with ONE small engraved emblem (a tower inside a ring) and NO text, NO numbers, NO chip.",
    "props2-": "Copy only the object's shape and material; every surface of it is blank — NO text, NO numbers, NO logos.",
}
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
FACE13 = ("MEDIUM CLOSE-UP, the camera about 1.5 metres from the speaker: the speaker's head is near the top edge of the frame and the frame is cut at "
          "mid-chest, so the speaker's head and shoulders fill the centre of the frame and the face is about one third of the frame height (NOT a wide "
          "shot, NOT full body, the room is only a blurred background). Framing from mid-chest up: the speaker's head and shoulders fill the frame, the face about one third of the frame height and sharp, "
          "turned about 35 degrees toward the other person (never straight at the camera, never full profile); the speaker's hands and what "
          "they hold are visible at the bottom of the frame; 50mm lens, f/2.0, shallow depth of field.")
OTS = ("Over-the-shoulder two-shot composition: the listener is at the near foreground edge seen strictly from behind — only the back of the "
       "head, hair and one shoulder, soft and out of focus, occupying at most 25 percent of the frame width; the listener's face is NOT visible. "
       "The camera stands close (about 1.2 m) behind the listener so the SPEAKER is large: head and shoulders fill the centre, NOT a wide shot.")
INSERT = ("EXTREME CLOSE-UP INSERT: only the hands / object described fill the frame; NO face, NO head and NO shoulders anywhere in the frame — "
          "the person is out of frame except the hands, wrists and sleeves. Shallow depth of field.")
BACK = ("The person is seen strictly from behind — only the back of the head, hair, ears and shoulders are visible, the face turned away from "
        "the camera; the mouth is never visible.")
ANGLE = {"HA": "CAMERA: steep high angle, looking down from about 4 metres above.", "OH": "CAMERA: directly overhead, looking straight down.",
         "BE": "CAMERA: bird's-eye view straight down from the ceiling.", "LA": "CAMERA: low angle, looking up from about waist height.",
         "SIDE": "CAMERA: from the side or behind — the face in side profile or hidden, NOT facing the camera."}
BLANK = ("Every paper, document, form, envelope, phone screen and monitor surface is completely blank and clean: NO printed lines, NO characters, "
         "NO headings, NO tables, NO numerals, NO stamps with characters (Japanese text is composited later).")
LIGHT_NOTE = {  # 1화 장소 셀을 다른 시간대로 쓰는 장면·셀 조명이 장면과 다른 곳만(나머지는 프롬프트 [SETTING])
    "backday": "LIGHTING OVERRIDES THE LOCATION REFERENCE: 1 p.m. overcast DAYTIME, flat grey sky light, damp concrete; NOT night, NO rain falling, NO neon, the booth window unlit.",
    "archive": "LIGHTING OVERRIDES THE LOCATION REFERENCE: the room lights are OFF; a narrow cold white flashlight beam is the only key light, a very dim green glow near the floor, deep shadows, dust in the beam; faces readable in the spill.",
    "top": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, the room dark except a low warm desk lamp and the city glow through the window; faces readable.",
    "meet": "LIGHTING OVERRIDES THE LOCATION REFERENCE: late morning, cold overhead fluorescent light with a faint green tint and grey window daylight, harsh shadows.",
}
SEAT = ("SEATED/FURNITURE LOCKED: seated persons sit ON chairs pulled in to the table, thighs under the table edge, forearms on the table; "
        "no chair passes through any body, no floating chair legs; correct solid furniture geometry.")
EMO_OVERRIDE = {  # 상태 고정(00_script_ja.md·제19장 27) — Kill Gate 뒤에 재생성 고정 문장을 여기에 더한다
    "S24j": "STATE LOCKED: the framed portrait hangs on the wall, but its glass is covered by a bright white reflection glare: NO face, NO eyes, NO features of the person are visible — only the dark frame, the glare and a vague dark suit shape below it; the corridor is EMPTY.",
}
BACK_ONLY = {}  # 뒷모습으로만 나오는 인물 — PHASE 3 생성기가 expr=back 셀을 이미 넣는다
ANGER_CLOSED = ("Fury shown only in the wide-open glaring eyes, furrowed brow, flared nostrils and clenched jaw: eyes OPEN and fixed on the listener, "
                "lips pressed together, mouth CLOSED, NOT shouting (speech is added later).")


def who_of(name):
    return next(((k, v) for k, v in PEOPLE if name.startswith(k + "-")), (None, None))


def is_backcell(name):
    return name.endswith(("-full-back.png",))


def describe(path, i):
    name = os.path.basename(path)
    if path.startswith(FACE_DIR):
        who = dict(PEOPLE).get(name[:-4]) or next((v for k, v in PEOPLE if FACE_OF.get(k, k) == name[:-4]), "the character")
        return (f"Reference image {i} is a tight face crop of {who}: reproduce exactly this face, age, hairstyle and eyewear; identity ONLY — "
                "do NOT copy its camera angle, background or lighting.")
    k, v = who_of(name)
    if k and is_backcell(name):
        return f"Reference image {i} is the BACK VIEW of {v}: this person appears seen from behind exactly like this (hair, build, posture); the WARDROBE follows the [CHARACTER] text below; do not show this person's face."
    if k:
        return (f"Reference image {i} is the character sheet cell of {v}: copy this exact face, hairstyle, eyewear and age; the WARDROBE follows "
                "the [CHARACTER] text below (it changes by scene); ignore its background, framing and any sheet layout.")
    if name.startswith(("props-", "props2-", "emblem")):
        return f"Reference image {i} is the prop reference: copy the object's exact shape, size and material; ignore any background or labels."
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing and light direction; ignore any "
            "borders, labels or wall papers.")


NO_FACE = {}
EXTRA_REFS = {}  # 컷별 추가 참조(소품 문양 통일)
NO_LOC = set()  # 소품 시트(쿠션 위 시계)·장소 참조가 손에 쥔 기기를 부름(S08k 2회) — 글로만
LIGHT_INTEG = ("LIGHT INTEGRATION: the person is lit by the same light as the room, natural soft edges; NO glowing outline, NO halo or white rim "
               "around the body, NOT a pasted cut-out.")
# Kill Gate 1차(2026-10-29) 정면 응시 다발 → 립싱크가 아닌 얼굴 컷은 시선 방향을 화면 좌우로 고정하고 정면 셀 대신 45° 셀을 참조
GAZE_FIX = {}  # 자동 추출이 틀린 컷·립싱크인데 렌즈를 보는 컷(FORCE45)
FORCE45 = set()  # 립싱크 컷인데 정면 셀로 두 번 렌즈 응시(r1) → 45° 셀 참조 + GAZE 문장


def gaze_of(sc):
    """비립싱크 얼굴 컷의 시선: 샷 설명의 「screen LEFT/RIGHT」(제19장 10① — 정면 응시 방지, 45° 셀 참조)."""
    if sc["id"] in GAZE_FIX:
        return GAZE_FIX[sc["id"]]
    if sc["kind"] != "face" and sc["id"] not in FORCE45:
        return None
    m = re.search(r"\(screen (LEFT|RIGHT)[^)]*\)", sc["subject"]) or re.search(r"screen (LEFT|RIGHT)", sc["subject"])
    return (m.group(0).strip("()") if m else "away from the lens toward the other person")



def build(sc, stage):
    refs = list(sc["refs"]) + EXTRA_REFS.get(sc["id"], [])
    if sc["id"] in NO_LOC:
        refs = [r for r in refs if not os.path.basename(r).startswith("loc-")]
    people = [r for r in refs if who_of(os.path.basename(r))[0]]
    is_back = bool(people) and is_backcell(os.path.basename(people[0])) and sc["kind"] != "d"  # 주인물이 뒷모습
    if sc["kind"] in FACE_KINDS and not is_back:  # 배경 없는 얼굴 크롭을 1번 참조로(동일 인물)
        face = []
        for r in people:
            k, _ = who_of(os.path.basename(r))
            f = f"{FACE_DIR}/{FACE_OF.get(k, k)}.png"
            if k in NO_FACE.get(sc["id"], ()) or (sc.get("ots") and r == people[-1]) or (sc["kind"] == "d" and len(people) > 1 and r == people[1]):  # 뒷모습 화자(비립싱크 VO)는 얼굴 크롭 제외 — 정면을 끌어온다
                continue
            if os.path.exists(os.path.join(ROOT, f)) and f not in face and not is_backcell(os.path.basename(r)):
                face.append(f)
        refs = face + refs
    # 전경 인물 뒷모습 셀은 PHASE 3 생성기가 이미 넣었다
    for k in BACK_ONLY.get(sc["id"], ()):
        refs = [r for r in refs if not (who_of(os.path.basename(r))[0] == k or os.path.basename(r) == f"{k}.png")] + [f"{CELLS}/{k}-fullback.png"]
    if len(refs) > MAX_REFS:  # fal edit 모델은 참조 10장까지(S17a 5인 컷 422 실증) — 얼굴 크롭이 있는 인물의 시트 셀부터 뺀다
        has_face = {os.path.basename(r)[:-4] for r in refs if r.startswith(FACE_DIR)}
        refs = [r for r in refs if not (in_cells(r) and who_of(os.path.basename(r))[0]
                                        and FACE_OF.get(who_of(os.path.basename(r))[0], who_of(os.path.basename(r))[0]) in has_face
                                        and not is_backcell(os.path.basename(r)))]
    assert len(refs) <= MAX_REFS, f"{sc['id']}: 참조 {len(refs)}장 > {MAX_REFS}"
    gaze = gaze_of(sc)
    if gaze and not is_back:  # 정면 셀 → 45° 셀
        refs = [r.replace("-front-noglasses.png", "-45.png").replace("-front.png", "-45.png") if in_cells(r) else r for r in refs]
        if sc["id"] in FORCE45:  # 표정 셀도 45° 셀로(립싱크 컷의 렌즈 응시 재발 방지)
            refs = [f"{os.path.dirname(r)}/{who_of(os.path.basename(r))[0]}-45.png" if in_cells(r) and who_of(os.path.basename(r))[0] else r for r in refs]
        refs = [r if os.path.exists(os.path.join(ROOT, r)) else r.replace("-45.png", "-front.png") for r in refs]
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    if sc["kind"] == "d":  # 구도 문장은 맨 앞(제15장 3) — 1차에서 서 있는 미디엄·원경 립싱크 키프레임 다발
        parts.append("FRAMING LOCKED FIRST: chest-up MEDIUM CLOSE-UP, the speaker's face at least ONE THIRD of the frame height; NOT a wide shot, NO full body, NO legs.")
    if gaze and not is_back:
        parts.append(f"GAZE LOCKED: eyes look {gaze}, head turned 30 to 40 degrees away from the lens; the eyes NEVER look into the camera lens.")
    if sc["id"] in NO_LOC:
        parts.append(LIGHT_INTEG)
    if "phone" not in (sc["subject"] + " " + (sc.get("motion") or "")).lower():
        parts.append("Nobody holds a phone; NO smartphone in any hand.")
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
        parts.append("Mouth gently closed or barely parted (speech is added later); natural skin texture, both eyes sharp and symmetrical; NO earrings on any man.")
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
            if stage in ("b1", "b2"):
                bidx = [x["id"] for x in sb["scenes"] if x.get("keyframe") and not (x["kind"] == "d" and x.get("line"))]
                half = (bidx.index(sc["id"]) < len(bidx) // 2)
                if half != (stage == "b1"):
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
    json.dump({"_설명": f"blackcard2 PHASE 4 키프레임 {name} (build_blackcard2_keyframes.py 생성, 직접 수정 금지).", "_style_preset": sb["preset"], "characters": chars},
              open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(c["count"] for c in chars)
    print(f"{name} 키프레임 {len(chars)}컷 {n}장 → {path} (약 {n * 0.04:.2f}달러)")


if __name__ == "__main__":
    main()
