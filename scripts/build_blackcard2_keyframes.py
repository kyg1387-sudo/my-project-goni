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
INSERT_ONE = ("EXTREME CLOSE-UP INSERT: exactly ONE hand (the other hand is completely OUT of frame) and the object fill the frame; NO face, "
              "NO chin, NO head and NO shoulders anywhere in the frame — the person is out of frame except this one hand, wrist and sleeve. Shallow depth of field.")
BACK = ("The person is seen strictly from behind — only the back of the head, hair, ears and shoulders are visible, the face turned away from "
        "the camera; the mouth is never visible.")
ANGLE = {"HA": "CAMERA: steep high angle, looking down from about 4 metres above.", "OH": "CAMERA: directly overhead, looking straight down.",
         "BE": "CAMERA: bird's-eye view straight down from the ceiling.", "LA": "CAMERA: low angle, looking up from about waist height.",
         "SIDE": "CAMERA: from the side or behind — the face in side profile or hidden, NOT facing the camera."}
BLANK = ("Every paper, document, form, envelope, phone screen and monitor surface is completely blank and clean: NO printed lines, NO characters, "
         "NO headings, NO tables, NO numerals, NO stamps with characters; every surface stays empty.")
LIGHT_NOTE = {  # 1화 장소 셀을 다른 시간대로 쓰는 장면·셀 조명이 장면과 다른 곳만(나머지는 프롬프트 [SETTING])
    "backday": "LIGHTING OVERRIDES THE LOCATION REFERENCE: 1 p.m. overcast DAYTIME, flat grey sky light, damp concrete; NOT night, NO rain falling, NO neon, the booth window unlit.",
    "archive": "LIGHTING OVERRIDES THE LOCATION REFERENCE: the room lights are OFF; a narrow cold white flashlight beam is the only key light, a very dim green glow near the floor, deep shadows, dust in the beam; faces readable in the spill.",
    "top": "LIGHTING OVERRIDES THE LOCATION REFERENCE: night, the room dark except a low warm desk lamp and the city glow through the window; faces readable.",
    "meet": "LIGHTING OVERRIDES THE LOCATION REFERENCE: late morning, cold overhead fluorescent light with a faint green tint and grey window daylight, harsh shadows.",
}
SEAT = ("SEATED/FURNITURE LOCKED: seated persons sit ON chairs pulled in to the table, thighs under the table edge, forearms on the table; "
        "no chair passes through any body, no floating chair legs; correct solid furniture geometry.")
EMO_OVERRIDE = {  # 상태 고정(00_script_ja.md·제19장 27) — Kill Gate 뒤에 재생성 고정 문장을 여기에 더한다
    # Kill Gate a(2026-11-07, 22장 중 8장): 경비원 가슴 가짜 명찰 글자(S14g)·벽 공지(S14i), 화자 얼굴 1/6 이하 원경(S14i·S18a·S18g·S19a·S19j),
    # 어깨 너머 앞 인물이 검은 머리 남자(S18b, 永瀬=은발), 안경 만지는 손(S18d, 립싱크 얼굴 변형 위험), 낮 장면에 비·밤(S19j)
    "S14g": "CAMERA CLOSE: the camera is 1.2 m behind Kenji's black-suited shoulder (near RIGHT edge, blurred, at most 25 percent of the frame width); the guard's head and shoulders fill the centre, his face at least ONE THIRD of the frame height; he holds a ring of keys out in ONE hand at chest height; ashamed, eyes lowered then toward Kenji screen RIGHT, NOT smiling, NEVER into the lens. UNIFORM LOCKED: the navy uniform chest is completely plain — NO name tag, NO badge, NO patch, NO label, NO pocket card.",
    "S14i": "CAMERA CLOSE: chest-up, the guard standing in the booth doorway fills the centre-left, his face at least ONE THIRD of the frame height, three-quarter toward screen RIGHT, one hand half raised; NOT smiling. UNIFORM LOCKED: the uniform chest plain, NO name tag, NO badge. The booth walls and window have NO notices, NO papers, NO signs.",
    "S18a": "CAMERA CLOSE: the camera is 1.2 m behind Kenji's seated black-suited shoulder (near LEFT edge, blurred, at most 25 percent of the frame width); Nagase stands just inside the glass door framed from the WAIST UP, his head and shoulders large in the centre, face at least ONE THIRD of the frame height, a slight polite half-bow, ONE hand on the back of a chair; eyes on Kenji screen LEFT, NEVER into the lens; NOT a wide shot, NO full body, NO legs.",
    "S18b": "FOREGROUND IDENTITY LOCKED: the blurred foreground back at the near RIGHT edge is Nagase — SILVER-GREY side-parted hair, the thin GOLD glasses temple arm visible at the ear, charcoal grey suit shoulder; NOT dark hair, NOT a young man. Kenji seated beyond at three-quarter, his face at least ONE THIRD of the frame height, eyes on Nagase screen RIGHT, NEVER into the lens.",
    "S18d": "POSE LOCKED: both of Nagase's hands are DOWN, resting out of frame — NO hand near the face, NOT touching the glasses. GAZE LOCKED: head turned 35 degrees toward screen LEFT, eyes on Kenji off-screen LEFT, NEVER into the lens; composed, a thin polite non-smile, lips closed.",
    "S18g": "CAMERA CLOSE, low angle: chest-up, Nagase leaning forward over the white table, his head and shoulders fill the centre, face at least ONE THIRD of the frame height, ONE hand pressed flat on the table at the bottom edge; eyes on Kenji screen LEFT, NEVER into the lens; NOT a wide shot; NO other person, NO foreground shoulder.",
    "S19a": "CAMERA CLOSE: the camera is 1.2 m behind Kenji's black-suited shoulder (near LEFT edge, blurred, at most 25 percent of the frame width); Misaki chest-up fills the centre, her face at least ONE THIRD of the frame height, ONE hand gripping her handbag strap at the shoulder; eyes on Kenji screen LEFT, pleading, NEVER into the lens. Overcast DAYTIME, dry grey concrete, NO rain, NO signs with text.",
    "S19j": "CAMERA CLOSE, slightly high: the camera is 1.2 m behind Kenji's black-suited shoulder (near LEFT edge, blurred, at most 25 percent of the frame width); Misaki chest-up fills the centre, face at least ONE THIRD of the frame height, lips trembling, eyes wet but NOT running, NOT smiling, one hand at her coat collar, holding NO paper; eyes on Kenji screen LEFT. Overcast DAYTIME, NOT night, NO rain falling.",
    # Kill Gate b1·b2(2026-11-07) 컷별
    "S13d": "INSERT ONLY: Kenji's head and face are OUT of frame (cut at the shoulder); the card is matte black with ONE small engraved ring-and-tower emblem and NO letters.",
    "S13e": "Seen from above the REAR seat only: the phone on the black leather, the corner of a knee; NO steering wheel, NO dashboard, NO front seats, NO hands, NO face.",
    "S14c": "The other hand and Kenji's face are OUT of frame.",
    "S14d": "The plaza and the building have NO posters, NO billboards, NO signs, NO illuminated panels; only the bronze emblem above the doors.",
    "S14e": "The person inside the booth is the night security guard in a plain navy uniform and navy cap (NOT a man in a white shirt), seen dimly through the glass; Kenji's eyes are on the booth screen LEFT, NEVER into the lens.",
    "S14l": "The label plate on the box is a completely blank metal plate.",
    "S15h": "Kenji's ONE thumb rests at the edge of a small rectangular ID photo clipped inside an open file lying on the table (the photo shows a plain pale blank surface); the file stays on the table; NO second hand, NO glowing object.",
    "S15i": "Kenji's ONE hand holds ONLY the smartphone (screen a plain soft glow); NO paper, NO second hand.",
    "S16a": "Kenji's ONE hand holds ONLY the smartphone (screen a plain soft glow); NO folder, NO file, NO second hand.",
    "S17m": "The SAME empty six-tatami room: bare tatami floor, NO table, NO chairs, NO furniture, NO tablet.",
    "S17t": "NOTHING in the air; no falling or floating object.",
    "S17v": "Grey overcast MORNING daylight on a quiet residential street beside the old apartment; NOT night, NO neon, NO rain falling, NO city towers.",
    "S18i": "GAZE LOCKED: head turned 35 degrees toward screen LEFT, eyes on Kenji off-screen LEFT, NEVER into the lens; bare lapel, NO pin.",
    "S18m": "Kenji's ONE hand rests FLAT on the single blank sheet; the hand holds NOTHING, NO phone.",
    "S19b": "Kenji is seen from BEHIND and slightly to the side, walking away; his face is turned AWAY from the camera — NO face, NO mouth visible.",
    "S19i": "FRAMING LOCKED: only Kenji's eyes and brows fill the frame; NO hands, NO phone, NO mouth in the frame.",
    "S19k": "The other hand is OUT of frame.",
    "S20f": "INSERT ONLY: Sagisuma's face is OUT of frame (cut below the chin); exactly ONE hand lifts the glass; the other hand is out of frame.",
    "S20g": "Seen strictly from BEHIND Kenji's shoulder: the back of his head turned toward Sagisuma; NO face, NO mouth, NO profile visible.",
    "S20o": "INSERT ONLY: Sagisuma's face is OUT of frame (cut below the chin); exactly ONE hand rests beside the glass; the other hand is out of frame.",
    "S20p": "Seen strictly from BEHIND Kenji's shoulder: the back and side of his head toward Sagisuma; NO face, NO mouth visible.",
    "S21c": "Exactly ONE hand holds the card against the reader; the other hand is out of frame.",
    "S21f": "EXACTLY SEVEN gold frames in one row: frames one to six each hold ONE half-cut matte black card (half a card, cut vertically) on black matte; the seventh frame is EMPTY black matte; a small BLANK brass plate under each frame.",
    "S21g": "Straight-on frontal: ONE single gold frame fills the centre of the frame — EMPTY black matte board — with a small BLANK brass plate below it; no other frames visible.",
    "S22f": "Straight-on frontal: ONE single gold frame holding ONE half-cut matte black card on black matte, a small BLANK brass plate below; no other frames visible.",
    "S23a": "The chauffeur sits in the RIGHT FRONT seat behind the steering wheel, seen only as the back of his cap; Kenji is ALONE in the rear seat; nobody sits beside Kenji.",
    "S23a2": "Only the rear side window glass and the city beyond fill the frame; NO dashboard, NO steering wheel, NO front seats visible.",
    "S23c": "ONLY the white-gloved hand on the steering wheel; NO faces, NO passengers, NO other people in frame.",
    "S24e2": "Kenji's ONE free hand rests flat and still on the contract; the capped pen lies beside it; the hand holds NOTHING — NO phone, NO card; the front seats out of frame.",
    "S24g": "FRAMING LOCKED: only Kenji's eyes and brows fill the frame; Kenji is ALONE in the rear seat; NO other person anywhere.",
    "S24d": "Exactly ONE hand holds the phone; the other hand and the face are out of frame.",
    "S24j": "STATE LOCKED: the framed portrait hangs on the wall, but its glass is covered by a bright white reflection glare: NO face, NO eyes, NO features of the person are visible — only the dark frame, the glare and a vague dark suit shape below it; the corridor is EMPTY.",
}
SUBJ_FIX = {"S19a": ("near RIGHT foreground", "near LEFT foreground")}  # 장면 축 통일(S19c 합격본이 켄지 왼쪽) — PHASE 3 문장 치환
# Kill Gate b1·b2(2026-11-07) 근본 원인: PHASE 3 프롬프트의 합성 예정 문구(「非通知」「総合 A」 등)를 이미지 모델이 그대로 가짜 글자로 그림(63장 중 약 30장)
# → 「…composited…」 괄호를 통째로 지우고, 글자·기호를 그리게 하는 서술은 무지 서술로 바꾼다(합성은 PHASE 4 ja_overlay).
TEXT_FIX = {
    "S14m": [("blank ruled pages", "blank pages with only faint thin ruled lines, NO marks, NO strokes, NO crosses")],
    "S14n": [("resting on a brush-ink stroke on the ledger page", "resting on one blank ruled row of the ledger page")],
    "S14p": [("a fresh glossy black ink stroke", "ONE short straight horizontal fresh glossy black ink line (a single straight line, NOT a curve, NOT a letter, NOT a cross)")],
    "S14s": [("a printed grade box", "one small empty blank square box")],
    "S15d": [("one of six dates written down the edge of a sheet", "the blank margin of a plain sheet")],
    "S16h": [("six brush-ink strike-throughs in a column", "a column of blank faintly ruled rows")],
    "S16j": [("the same six ink strike-throughs", "the same column of blank faintly ruled rows")],
    "S18o": [("after writing two shaky characters", "above a completely blank area of the sheet")],
    "S19g": [("with one short printed line", "completely blank, NO print")],
    "S22h": [("one field with a printed name, one field empty", "two empty blank signature lines")],
}


def sanitize(sid, kp):
    for old, new in TEXT_FIX.get(sid, ()):
        assert old in kp, (sid, old)
        kp = kp.replace(old, new)
    kp = re.sub(r"\s*\([^()]*composited[^()]*\)", "", kp)
    kp = re.sub(r"「[^」]*」", "", kp)
    return kp


TWO_TAKES = {"S14g"}  # 립싱크 시범 컷
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
    kp = sanitize(sc["id"], sc["keyframe_prompt"])
    if sc["id"] in SUBJ_FIX:
        assert SUBJ_FIX[sc["id"]][0] in kp, sc["id"]
        kp = kp.replace(*SUBJ_FIX[sc["id"]])
    parts.append(kp)
    for r in sc["refs"]:
        b = os.path.basename(r)
        for k, v in LOC_NOTE.items():
            if b.startswith(k) and v not in parts:
                parts.append(v)
    if sc.get("lighting") in LIGHT_NOTE:
        parts.append(LIGHT_NOTE[sc["lighting"]])
    if sc["kind"] == "ins" and people:  # 「ONE hand」 컷은 손 하나(두 손 생성 다발 — Kill Gate b 7컷)
        parts.append(INSERT_ONE if "ONE hand" in sc["subject"] or "ONE index finger" in sc["subject"] or "ONE thumb" in sc["subject"] else INSERT)
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
        if only and stage != "p":  # 재생성: 사람이 나오는 컷 2장, 사물·무지 면 1장(글자 원인 제거만으로 충분)
            c["count"] = 2 if sc["id"] in TWO_TAKES else 1  # 승인 예산(약 8.4달러) 안: 원인 문장을 고쳤으므로 1장, 시범 컷만 2장
        chars.append(c)
    if (stage == "p" or stage.startswith("r")) and len(chars) != len(only):
        raise SystemExit(f"컷 일부 없음: {sorted(only - {c['id'] for c in chars})}")
    leak = [c["id"] for c in chars if "「" in c["prompt"] or "composited" in c["prompt"]]
    if leak:  # Kill Gate 1차 근본 원인 — 합성 문구가 프롬프트에 남으면 가짜 글자가 그려진다(실증 10절)
        raise SystemExit("합성 예정 문구가 프롬프트에 남음: " + ", ".join(leak))
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
