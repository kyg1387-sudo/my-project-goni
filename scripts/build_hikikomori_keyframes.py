#!/usr/bin/env python3
"""『引きこもりの息子』 PHASE 4 키프레임 스펙 생성기 — build_beggar_keyframes.py를 옮긴 것(내장 규칙 동일).

scripts/storyboard/hikikomori.json(PHASE 3)을 읽어 generate-video.yml portraits_spec 스펙을 만든다. 손으로 스펙을 고치지 않는다.
단계: a 립싱크 컷 / b1·b2 나머지(90분 실행 상한 때문에 반으로) / r<n>:<id,…> 재생성(컷당 2장)
이 작품 차이: 앞 인물 뒷모습 셀은 PHASE 3 생성기가 이미 골라 둔다(kentaro-fullback·daikih-hoodback·daiki-suitback·yumiko-fullback·kaneda-fullback).
金田(카메오) 명찰은 무지 — 「金田」은 PHASE 4 합성. 귀걸이는 由美子 진주 스터드만(남성 전원 귀걸이 없음).
"""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "hikikomori.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "hikikomori-kf-{}.json")
FACE_DIR = "assets/portraits/hikikomori-faces"
CELLS = "assets/portraits/hikikomori-cast/cells"
PEOPLE = [
    ("kentaro", "Seo Kentaro (52, stocky, square weathered face, short greying crew-cut, thick black eyebrows, NO glasses, NO beard)"),
    ("daikih", "Seo Daiki (26, slim young man, pale, straight black hair with bangs, black thick-rimmed rectangular glasses, NO earrings)"),
    ("daiki", "Seo Daiki (26, slim young man, pale, straight black hair with bangs, black thick-rimmed rectangular glasses, NO earrings)"),
    ("yumiko", "Seo Yumiko (50, soft round face, shoulder-length dark-brown bob, small pearl stud earrings, NO glasses)"),
    ("seiji", "Seo Seiji (48, slightly chubby round face, slicked-back black hair, thin GOLD wire-rimmed glasses, NO earrings)"),
    ("ryosuke", "Seo Ryosuke (28, lean face, clear smooth skin, short neat black side-parted hair, NO glasses, NO earrings)"),
    ("makabe", "Makabe (60, gaunt stern face, slicked-back silver-white hair, NO glasses, NO earrings)"),
    ("kaneda", "Kaneda (sixties, wavy black hair with a little grey, thin silver half-rim browline glasses, NO earrings)"),
]
FACE_OF = {"daikih": "daiki"}
FACE_KINDS = ("face", "d")
MAX_REFS = 10
PILOT_DONE = set()
LOC_NOTE = {
    "loc-home": "The house has NO calendars, NO posters, NO notes with writing on the walls or fridge; all labels blank.",
    "loc-room": "The whiteboard holds only lines and arrows with NO writing; book spines are plain; monitors show only a soft plain glow; NO posters.",
    "loc-office": "NO wall calendars, NO notices, NO writing on files or ledgers; the workshop beyond the office window is EMPTY of people.",
    "loc-factory": "NO signs, NO labels or plates with writing on the machines, NO posters; plain metal and paint.",
    "loc-meeting": "NO signs, NO whiteboard writing, NO name plates; plain walls.",
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
    "tension": "LIGHTING OVERRIDES THE LOCATION REFERENCE: cold overhead fluorescent falling vertically, harsh shadows under the brows, high contrast.",
    "room_warm": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, a warm desk lamp mixed with a soft monitor glow, gentle and intimate.",
    "meet_door": "LIGHTING OVERRIDES THE LOCATION REFERENCE: a strong white backlight from the corridor through the open door, the figure edged with light, face readable.",
    "meet_turn": "LIGHTING OVERRIDES THE LOCATION REFERENCE: warmer daylight filling the room from the window, softer contrast.",
    "meet_power": "LIGHTING OVERRIDES THE LOCATION REFERENCE: cold overhead fluorescent, a hard window backlight behind the older man, high contrast.",
    "morning": "LIGHTING OVERRIDES THE LOCATION REFERENCE: clear early-morning golden light, long warm shadows.",
    "office_n": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, a single warm desk lamp in a dark office, faces readable.",
    "sukiyaki": "LIGHTING OVERRIDES THE LOCATION REFERENCE: warm pendant lamp over the table, steam glowing.",
    "room_d": "LIGHTING OVERRIDES THE LOCATION REFERENCE: daytime behind thick closed curtains, dim grey light at the curtain edges.",
    "fac_n": "LIGHTING OVERRIDES THE LOCATION REFERENCE: a deserted factory at night, one fluorescent tube, deep shadows, faces readable.",
}
SEAT = ("SEATED/FURNITURE LOCKED: seated persons sit ON chairs pulled in to the table, thighs under the table edge, forearms on the table; "
        "no chair passes through any body, no floating chair legs; correct solid furniture geometry.")
EMO_OVERRIDE = {
    "S17a": "PEOPLE LOCKED: exactly FIVE people. Far side of the long grey table, seated facing the camera: Makabe (60, silver-white slicked hair, black suit) and Ryosuke (28, charcoal suit). Near side, seated with their backs to the camera: Kentaro (navy work jacket) and Yumiko (beige cardigan, bob). Seiji (burgundy polo, gold glasses) stands leaning against the RIGHT wall with arms folded. NOBODY else. " + SEAT,
    "S11h": "POSE LOCKED: Kentaro is sliding from the desk chair down onto his KNEES on the floor in front of the desk, hands reaching the floor; he is NOT lying down; the chair stays behind him.",
    "S11i": "POSE LOCKED: Kentaro is KNEELING on the floor (NOT seated on a chair), upper body upright, chest-up close-up.",
    "S11j": "POSE LOCKED: Kentaro is KNEELING on the floor, close-up profile.",
    "S11k": "POSE LOCKED: Kentaro sits on the floor, seen from behind, small in the frame; the desk chair is empty.",
    "S20f": "POSE LOCKED: Makabe is KNEELING on the carpet beside the long table — knees on the floor, upper body bent forward, both palms flat on the floor, head bowed so his face is hidden; he is NOT lying down. Seen from straight above.",
    "S21c": "POSE LOCKED: Makabe is ON HIS KNEES on the floor, lifting his head to look UP, stunned; high angle looking down at him.",
    "S21d": "POSE LOCKED: Kentaro is STANDING beside the table (he has risen), medium shot from the waist up.",
    "S18b": "WARDROBE LOCKED: Daiki wears the dark navy suit and white shirt with no tie (NOT a hoodie). He stands in the open doorway.",
    "S18c": "WARDROBE LOCKED: Daiki wears the dark navy suit and white shirt with no tie (NOT a hoodie).",
    "S22e": "PEOPLE LOCKED: exactly two people: Kentaro seated in the foreground at three-quarter angle, Daiki (dark navy suit, NOT a hoodie) standing by the window in the background.",
    "S24d": "PEOPLE LOCKED: exactly THREE people seated around the small dining table: Kentaro (charcoal cardigan), Yumiko (beige cardigan, bob), Daiki (grey hoodie, glasses); a steaming sukiyaki pot in the centre. " + SEAT,
    "S04a": "PEOPLE LOCKED: exactly TWO people seated at the small dining table, Kentaro and Yumiko; the third chair and its place setting are EMPTY. " + SEAT,
    "S13b": "Seiji appears only as a small blurred shape far behind Kentaro near the office door; Kentaro is in the foreground facing toward the camera side at three-quarter angle, NOT looking into the lens.",
    "S13c": "Seiji appears only as a small blurred shape far behind Kentaro near the office door; Kentaro is in the foreground at three-quarter angle, NOT looking into the lens.",
    "S14d": "The craftsmen are small distant figures seen from behind at their machines; Kentaro is a small figure seen from behind at the raised office window.",
    "S23h": "This is a PHOTOGRAPH inside a simple wooden frame standing on a desk: an old faded colour print of a small boy (about 6) and a young father (about 30, crew-cut, navy work jacket) standing in front of a lathe in a small factory, both smiling softly; NO text on the photo or frame.",
    "S12a": "The sedan has NO license plate characters, NO emblem lettering; headlights OFF; the factory shutter has NO sign.",
    "S10b": "Seen from behind over Kentaro's shoulder: the back of his greying crew-cut head and charcoal cardigan shoulder in the foreground, the glowing monitor beyond with a blank plain dashboard layout; his face is NOT visible.",
    "S06d": "Daiki is seen strictly from behind, walking away; NO face visible.",
    "S03c": "Daiki is asleep in the bed, face half hidden by the pillow and blanket; his glasses are folded on the shelf.",
}
ANGER_CLOSED = ("Fury shown only in the wide-open glaring eyes, furrowed brow, flared nostrils and clenched jaw: eyes OPEN and fixed on the listener, "
                "lips pressed together, mouth CLOSED, NOT shouting (speech is added later).")


def who_of(name):
    return next(((k, v) for k, v in PEOPLE if name.startswith(k + "-")), (None, None))


def is_backcell(name):
    return name.endswith(("-fullback.png", "-hoodback.png", "-suitback.png"))


def describe(path, i):
    name = os.path.basename(path)
    if path.startswith(FACE_DIR):
        who = dict(PEOPLE).get(name[:-4], "the character")
        return (f"Reference image {i} is a tight face crop of {who}: reproduce exactly this face, age, hairstyle and eyewear; identity ONLY — "
                "do NOT copy its camera angle, background or lighting.")
    k, v = who_of(name)
    if k and is_backcell(name):
        return f"Reference image {i} is the BACK VIEW of {v}: this person appears seen from behind exactly like this (hair, wardrobe); do not show this person's face."
    if k:
        return (f"Reference image {i} is the character sheet cell of {v}: copy this exact face, hairstyle, eyewear and age; the WARDROBE follows "
                "the [CHARACTER] text below (it changes by scene); ignore its background, framing and any sheet layout.")
    if name.startswith("props-"):
        return f"Reference image {i} is the prop reference: copy the object's exact shape, size and material; ignore any background or labels."
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing and light direction; ignore any "
            "borders, labels or wall papers.")


NO_FACE = {}
NO_LOC = set()  # 장소 참조가 원경·후광을 만들면 여기에(제18장 9④)


def build(sc, stage):
    refs = list(sc["refs"])
    if sc["id"] in NO_LOC:
        refs = [r for r in refs if not os.path.basename(r).startswith("loc-")]
    people = [r for r in refs if who_of(os.path.basename(r))[0]]
    is_back = bool(people) and is_backcell(os.path.basename(people[0])) and sc["kind"] != "d"  # 주인물이 뒷모습
    if stage != "p" and sc["kind"] in FACE_KINDS and not is_back:  # 배경 없는 얼굴 크롭을 1번 참조로(동일 인물)
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
    if len(refs) > MAX_REFS:  # fal edit 모델은 참조 10장까지(S17a 5인 컷 422 실증) — 얼굴 크롭이 있는 인물의 시트 셀부터 뺀다
        has_face = {os.path.basename(r)[:-4] for r in refs if r.startswith(FACE_DIR)}
        refs = [r for r in refs if not (r.startswith(CELLS + "/") and who_of(os.path.basename(r))[0]
                                        and FACE_OF.get(who_of(os.path.basename(r))[0], who_of(os.path.basename(r))[0]) in has_face
                                        and not is_backcell(os.path.basename(r)))]
    assert len(refs) <= MAX_REFS, f"{sc['id']}: 참조 {len(refs)}장 > {MAX_REFS}"
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
    json.dump({"_설명": f"hikikomori PHASE 4 키프레임 {name} (build_hikikomori_keyframes.py 생성, 직접 수정 금지).", "_style_preset": sb["preset"], "characters": chars},
              open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(c["count"] for c in chars)
    print(f"{name} 키프레임 {len(chars)}컷 {n}장 → {path} (약 {n * 0.04:.2f}달러)")


if __name__ == "__main__":
    main()
