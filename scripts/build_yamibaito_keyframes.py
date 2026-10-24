#!/usr/bin/env python3
"""『時給5万円の罠』(yamibaito) PHASE 4 키프레임 스펙 생성기 — build_bento_keyframes.py를 옮긴 것(내장 규칙 동일).

scripts/storyboard/yamibaito.json(PHASE 3)을 읽어 generate-video.yml portraits_spec 스펙을 만든다. 손으로 스펙을 고치지 않는다.
단계: p:<id,…> 시범(컷당 2장) / a 립싱크 컷 / b 나머지 / r<n>:<id,…> 재생성(컷당 2장)
이 작품 차이: 健太 의상 3벌은 셀 시트 3장(kenta-work/conv/hoodie)이지만 얼굴 크롭은 하나(kenta-face). 店長은 고니감독님 카메오 —
실제 사진(goni-front-1.jpg)을 추가 참조. 립싱크 컷은 장소 참조 없이 글로(제19장 8). 고증: 赤色灯만·우핸들·녹색 공중전화·세로 通帳(제20장 4).
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "yamibaito.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "yamibaito-kf-{}.json")
FACE_DIR = "assets/portraits/yamibaito-faces"
CELLS = "assets/portraits/yamibaito-cast/cells"
KENTA = "Saito Kenta (24, slim tired face, large eyes with slightly drooping outer corners, LEFT ear sticking out a little, thick black hair with a fringe over half the forehead, clean-shaven, bare eyes with NO glasses, plain bare earlobes with nothing on them, NO moles)"
PEOPLE = [
    ("kenta-work", KENTA + " in a plain light-grey work jumpsuit"),
    ("kenta-conv", KENTA + " in a teal convenience-store vest over a white shirt"),
    ("kenta-hoodie", KENTA + " in a plain light-grey hoodie"),
    ("otoko", "the watchman (40s, heavy-set, square jaw, closely shaved head, thick neck, small cold eyes, black zip jacket, black gloves, NO glasses)"),
    ("yuto", "Yuto (22, round face, short brown hair, quick restless eyes, charcoal work jumpsuit, NO glasses, plain bare earlobes)"),
    ("tencho", "the night shop manager (50s, slim oval face, thick slightly wavy BLACK hair with a side part, thin round silver-rimmed glasses, kind calm eyes, navy store vest over a white shirt)"),
]
FACE_OF = {"kenta-work": "kenta-face", "kenta-conv": "kenta-face", "kenta-hoodie": "kenta-face", "otoko": "otoko-face", "yuto": "yuto-face", "tencho": "tencho-face"}
CAMEO = "assets/portraits/yamibaito-cameo/goni-front-1.jpg"
FACE_KINDS = ("face", "d")
PILOT_DONE = {"S02f", "S05h", "S09g"}  # 시범 승인(2026-10-24, 고니감독님 「진행해줘」) → assets/portraits/yamibaito-kf-pilot-ok/
LOC_NOTE = {
    "loc-conbini": "Japanese convenience store interior: every shelf label, poster, price tag and sign is completely BLANK; no brand logos.",
    "loc-street-van": "The black van is a Japanese right-hand-drive one-box van with a sliding door; headlights OFF; number plate blank; NO readable signs.",
    "loc-van-inside": "Japanese RIGHT-hand-drive van interior: steering wheel on the RIGHT, two front seats, a rear bench; nothing on the dashboard is readable.",
    "loc-factory-ext": "Abandoned Japanese factory: corrugated iron, concrete, a brick chimney, barred windows, NO sign, NO vehicles, NO headlights.",
    "loc-workroom": "Abandoned factory workroom: long steel tables, flickering fluorescent tubes, a CCTV dome with a red dot; every bankbook and paper is BLANK.",
    "loc-corridor": "Long concrete corridor: the emergency-exit sign box is a plain green rectangle with NO pictogram and NO text.",
    "loc-stairs": "Rusted outdoor steel emergency staircase with green railings at night; NO text anywhere.",
    "loc-payphone": "A GREEN Japanese public telephone (NTT style, no logo, blank keypad) outside a convenience store whose signboard is BLANK.",
    "loc-park": "A small Japanese park in early morning light; NO signs with text.",
    "prop-bankbooks": "Japanese vertical bankbooks (通帳) with completely BLANK plain covers, no text.",
    "prop-phones": "Smartphones piled face down in a grey plastic crate, screens dark and blank.",
}
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
FACE13 = ("MEDIUM CLOSE-UP, the camera about 1.5 metres from the speaker: the speaker's head is near the top edge of the frame and the frame is cut at "
          "mid-chest, so the speaker's head and shoulders fill the centre of the frame and the face is about one third of the frame height (NOT a wide "
          "shot, NOT full body, the room is only a blurred background). The face is turned about 35 degrees toward the other person (never straight at the camera, never full profile); "
          "50mm lens, f/2.0, shallow depth of field.")
OTS = ("Over-the-shoulder two-shot composition: the listener is at the near foreground edge seen strictly from behind — only the back of the "
       "head, hair and one shoulder, soft and out of focus; the listener's face is NOT visible.")
INSERT = ("EXTREME CLOSE-UP INSERT: only the hands / object described fill the frame; NO face, NO head and NO shoulders anywhere in the frame — "
          "the person is out of frame except the hands, wrists and sleeves. Shallow depth of field.")
BACK = ("The person is seen strictly from behind — only the back of the head, hair, ears and shoulders are visible, the face turned away from "
        "the camera; the mouth is never visible.")
ANGLE = {"HA": "CAMERA: high angle, looking down from above.", "OH": "CAMERA: directly overhead, looking straight down.",
         "BE": "CAMERA: bird's-eye view straight down from the ceiling.", "LA": "CAMERA: low angle, looking up from about waist height.",
         "SIDE": "CAMERA: from the side or behind — the face in side profile or hidden, NOT facing the camera.",
         "POV": "CAMERA: handheld first-person point of view, slightly tilted, nobody in frame."}
BLANK = ("Every paper, document, envelope, phone screen, monitor, clock face, keypad and sign surface is completely blank and clean: NO printed lines, NO characters, "
         "NO headings, NO numerals, NO icons (Japanese text is composited later).")
LIGHT_NOTE = {}
REAL = ("REAL PHOTOGRAPH, live-action Japanese film still: natural skin texture with visible pores and fine lines, no airbrushed or plastic skin, "
        "no beauty filter, natural colour, real fabric texture; NOT an illustration, NOT 3D, NOT CGI.")
EMO_OVERRIDE = {  # 립싱크 컷별 고정 문장(시범·Kill Gate 후 추가)
}
_EMO_BENTO = {
    "S08j": "SPEAKER LOCKED: Shuzo in 1996 (black hair greying at the temples, white headband towel, white cook's jacket, navy apron) leans on the counter with both hands, the face at three-quarter angle toward the boy, gruff but warm, a faint softening around the eyes; the boy appears ONLY as a blurred back of messy black hair and navy jumper shoulder at the near LEFT edge, shorter than the counter edge. The lit glass showcase between them. It is NIGHT: the window behind him is dark night, NO daylight. His ears are bare: NO earrings, NO ear piercing, NO stud. His cheeks are clean: NO scar, NO cut, NO wound mark. The counter front and the wall below the counter are plain, NO papers or notes pinned anywhere.",
    "S13d": "SPEAKER LOCKED: grown-up Takumi (42, LARGE round dark eyes, slightly protruding ears, short neat black hair, charcoal overcoat) stands just inside the shop doorway (his daughter's small hand in his, below the frame edge, NOT visible), the face at three-quarter angle toward the old man, eyes red-rimmed and wet with tears pooled but NOT running, a small closed-mouth smile with lips together; at most ONE thin clear tear track on ONE cheek only, the other cheek completely dry, no droplet chains; the old man appears ONLY as a blurred back of short WHITE hair and grey cardigan shoulder at the near RIGHT edge. Behind Takumi: the glass sliding door and the dark night street.",
    "S13f": "SPEAKER LOCKED: old Shuzo (73, short WHITE hair, white eyebrows, deep wrinkles, grey cardigan under a faded navy apron) behind the counter with one hand resting on the ONE single remaining bento box on the counter top (no other bentos on the counter), the face at three-quarter angle toward Takumi, choked up: eyes red and wet with tears pooled but NOT running, mouth corners pulled down, chin trembling, NOT smiling; grown-up Takumi appears ONLY as a blurred back of short black hair and charcoal coat shoulder at the near LEFT edge.",
}
# 키프레임 1차 Kill Gate(2026-10-20) 컷별 고정 문장 — 맨 앞(구도 다음)에 넣는다
_PINK = ""
_DRY = "Both cheeks are completely DRY: tears only pooled along the lower lids, NO tear track, NO streak running down either cheek."
SHOT_FIX = {  # 시범 1차(2026-10-24): 전 컷 눈물(네거티브 오검출)·健太 귀걸이·명찰·店長 백발·정면 응시 / 1차 a(10컷 중 8 재생성): 원경·정면 응시·귀걸이·흐르는 눈물·백발
    "S02bh": "GAZE LOCKED: he looks DOWN at the phone held below the frame edge, eyes lowered, NOT at the camera. Framing cut at mid-chest, sitting up on the edge of the bed, the dim lamp a blur behind.",
    "S05f": "GAZE LOCKED: he looks slightly to the RIGHT of the camera at the young men off frame, dead eyes, NOT into the lens. Framing cut at mid-chest; the flashlight is held low out of frame, lighting his face from below.",
    "S06n": "GAZE LOCKED: Yuto's eyes are turned sideways to the RIGHT toward Kenta's blurred shoulder, NOT at the camera; his head stays low over the table. His earlobes are plain and bare.",
    "S07h": "GAZE LOCKED: Yuto's eyes are lowered to the table, NOT at the camera; Kenta's foreground jumpsuit sleeve is completely plain with NO patch, NO badge. Yuto's earlobes are plain and bare.",
    "S07j": "GAZE LOCKED: his eyes are lowered, looking at nothing, slightly to the LEFT, NOT at the camera. " + _DRY,
    "S09i": "HAIR LOCKED: JET-BLACK hair exactly as in the photograph and the approved keyframe, thick and slightly wavy, with NO grey and NO white hair at all; thin round silver-rimmed glasses. GAZE LOCKED: he glances toward the store door on the RIGHT, NOT at the camera.",
    "S10j": "GAZE LOCKED: he looks slightly to the LEFT at Kenta off frame, NOT into the lens; his earlobes are plain and bare. " + _DRY + " The red light is a reflected rotating police light, red ONLY (never blue).",
    "S11b": "PEOPLE LOCKED: exactly ONE person, Kenta, seated on the bench; NO second figure anywhere in the park behind him. GAZE LOCKED: his eyes are lowered toward the ground to the LEFT, listening to the phone at his far ear, NOT at the camera. " + _DRY,
    # b1 Kill Gate(2026-10-24, 69장 중 20 재생성): 폰 화면 단독 컷에 사람이 생김 / 단독 CU가 원경·어안·전신 / 같은 인물 2명 / 군중 수 부족 / 통장 가짜 글자
    "H4": "ABSOLUTELY NO PEOPLE, NO FACES: only out-of-focus bokeh circles of city lights filling the whole frame, no readable signs.",
    "S02b": "ABSOLUTELY NO PEOPLE, NO HANDS: a smartphone lying FLAT on a dark steel table, shot straight down from above (top-down macro), its lit screen a completely blank pale panel filling about 70 percent of the frame.",
    "S02ba": "ABSOLUTELY NO PEOPLE, NO HANDS: a smartphone lying FLAT on a rumpled bedsheet, shot straight down from above (top-down macro), its lit screen a completely blank pale panel filling about 70 percent of the frame.",
    "S02g": "ABSOLUTELY NO PEOPLE, NO HANDS: a smartphone lying FLAT on a dark steel table, shot straight down from above (top-down macro), its lit screen a completely blank pale panel filling about 70 percent of the frame.",
    "S03b": "ABSOLUTELY NO PEOPLE, NO HANDS: a smartphone lying FLAT on a rumpled bedsheet, shot straight down from above (top-down macro), its LIT screen a completely blank pale panel filling about 70 percent of the frame; nothing else in the frame, NO signs, NO cards, NO clocks.",
    "S02d": "INSERT: only a hand holding a phone and a thumb hovering above its blank lit screen, seen from above the shoulder; NO face, NO head in the frame; the thumb is NOT pointing at the camera.",
    "S02be": "FRAMING FIRST — CLOSE-UP, head and shoulders only, the face one third of the frame height or larger, the phone glow on his face from below the frame; NOT a wide shot of the room.",
    "S02bf": "EXTREME CLOSE-UP of the two eyes only, the frame cut at the eyebrows and the bridge of the nose; NO second person, NO figure in the background, NO body — only the eyes and the phone's glow.",
    "S04a": "PEOPLE LOCKED: Kenta appears exactly ONCE, by the window on the RIGHT; the three other young men are seen ONLY as bowed heads and backs (different hair, dark jackets), their faces never visible; nobody looks at the camera.",
    "S04h": "ABSOLUTELY NO PEOPLE, NO OBJECTS inside: only the dark tinted van window glass from inside, blurred orange lights outside fading to black; NO camera, NO lens, NO equipment.",
    "S04i": "PEOPLE LOCKED: exactly FOUR young men seen from above and behind, all wearing black eye masks, heads bowed, Kenta's grey hood among them; the backs of the two front seats ahead; faces never visible.",
    "S04j": "WARDROBE LOCKED: Kenta WEARS a plain black sleep eye mask covering both eyes (he cannot see); his head tilts slightly up; his mouth closed; NOT looking at the camera (eyes are covered).",
    "S05b": "The black sleep eye mask is a plain solid cloth band with NO eye holes, being lifted UP and away from his face by a hand from above, so his bare eyes are just uncovered and blinking; PEOPLE LOCKED: exactly ONE person, Kenta, no second figure in the background.",
    "S05c": "PEOPLE LOCKED: exactly FOUR young men seen strictly from BEHIND walking through the open iron gate, Kenta's grey hood and small backpack nearest the camera, the others in dark jackets; NO faces visible; backlit by cold light from inside.",
    "S05g": "FRAMING FIRST — CLOSE-UP from slightly above: head and shoulders only, the face one third of the frame height or larger; NOT full body, NOT a high wide shot; his eyes turned to the LEFT toward the man off frame.",
    "S05i": "FRAMING FIRST — CLOSE-UP: head and shoulders only, the face one third of the frame height or larger, his head turned about 20 degrees to look back over his RIGHT shoulder toward the gate behind him; NOT full body.",
    "S06b": "POSE LOCKED: a ROW of four young men in grey jumpsuits SEATED on steel chairs at the long table, seen from BEHIND, heads bowed over the table, hands on blank booklets; Kenta nearest the camera; NO faces visible; nobody sits ON the table.",
    "S06c": "The booklets are plain pastel-coloured paper booklets with completely BLANK covers — NO printing, NO characters, NO lines, NO stamps on any of them; hands and grey sleeves only from the top edge.",
    "S06e": "FRAMING FIRST — CLOSE-UP with a normal 85mm perspective, head and shoulders only, the face one third of the frame height or larger, his eyes half closed looking DOWN at the table, NOT at the camera; NOT fisheye, NOT full body.",
    "S06e2": "PEOPLE LOCKED: about a DOZEN young men in grey jumpsuits SEATED at the long tables with heads bowed, seen from the ceiling corner above and behind; NO faces visible; nobody standing.",
    "S02f": "The vest chest is completely plain: NO name tag, NO badge, NO card, NO pin. His earlobes are plain and bare. His eyes are DRY — no tears at all; he looks down at the phone, NOT at the camera.",
    "S05h": "His face is completely DRY — no tears, no sweat; dead-still expressionless face, only the eyes aimed at the young man off frame to the LEFT, NOT at the camera. Light: a single flashlight from below and the side, the corridor behind dark.",
    "S09g": "HAIR LOCKED: the manager's hair is exactly as in the photograph — thick, slightly wavy, BLACK hair with a natural side part, same length and volume. His glasses are the same thin round silver-rimmed glasses as in the photograph. His face is DRY, no tears. GAZE LOCKED: he looks at the young man in the foreground on the LEFT, NOT into the camera.",
}
_SHOT_FIX_BENTO = {
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
    # 2차 검수(2026-10-21): 등록기 서랍이 도시락처럼 그려져 「도시락에서 동전을 집어 지갑에 넣는」 장면이 됨(7:26 회상 재사용)
    "S05b": "The drawer is clearly a CASH REGISTER drawer (grey metal coin cups and bill slots), attached to the register body above it; the coin moves FROM the purse INTO the drawer.",
    "S13c": "PEOPLE LOCKED: exactly THREE people — old Shuzo ONLY as a blurred back at the near left edge, Takumi entering through the half-open glass door, and his little daughter holding his hand; they are ENTERING (mid-step at the threshold), NOT standing still in the middle of the shop; the girl looks at the counter, NOT at the camera.",
    "S04j": "POSE LOCKED: the boy is LEAVING — seen strictly from behind (back of head, NO face), facing OUT toward the rainy darkness beyond the door, NOT walking into the shop; exactly ONE person.",
    "S05c": "The small worn brown coin purse is clearly visible, held open in his left palm with fingers wrapped around it; his ears are bare with nothing on the earlobes (plain natural earlobes); the register drawer is open and close in front of him.",
    "S13r": "PEOPLE LOCKED: exactly TWO people facing each other across the counter INSIDE the shop at night — old Shuzo ONLY as the blurred back of white hair and grey cardigan shoulder at the near RIGHT edge, close to the camera and NOT walking away; Takumi looks at him, NOT at the camera. NO train, NO platform, NO one in the background. Cheeks dry, eyes wet only.",
    "S13a": "GRAVITY LOCKED: the bento lies flat on the wooden counter inside the shop; both hands belong to ONE old man standing behind the counter at the top of the frame (sleeves enter from the top edge only, NOT from the left and right sides); NO train, NO platform.",
    "S12k": "GAZE LOCKED: his eyes look DOWN toward the letter below the frame edge, NOT at the camera; tears pooled along the lower lids only, both cheeks completely DRY, natural skin around the eyes (no pink, no red).",
    "S12f": "FRAMING FIRST — TIGHT CLOSE-UP: the boy's head and shoulders fill the frame, the face one third of the frame height or larger; NOT a medium or full-body shot, NOT inside the shop; he stands OUTSIDE in the dark night, the camera is inside behind the glass. GAZE LOCKED: the boy looks toward screen LEFT into the shop, eyes NOT on the camera; tears pooled on the lower lids only, both cheeks completely dry.",
    "S03bd": "WARDROBE LOCKED: the boy wears the SAME navy zip jacket over a grey shirt as the reference, long sleeves; he is SEATED on the bench, NOT standing; the little sister in a red knit hat and yellow padded jacket sits beside him.",
}
ANGER_CLOSED = ("Fury shown only in the wide-open glaring eyes, furrowed brow, flared nostrils and clenched jaw: eyes OPEN and fixed on the listener, "
                "lips pressed together, mouth CLOSED, NOT shouting (speech is added later).")


def who_of(name):
    if name == os.path.basename(CAMEO):
        return ("tencho", dict(PEOPLE)["tencho"])
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
    if path.startswith("assets/portraits/yamibaito-kf-pilot-ok/S09g"):
        return (f"Reference image {i} is the APPROVED keyframe of the same night shop manager in this same store: reproduce exactly this face, hair, "
                "glasses and vest; identity and wardrobe ONLY — the framing and gaze follow the description below.")
    if path == CAMEO:
        return (f"Reference image {i} is a REAL PHOTOGRAPH of the night shop manager: reproduce exactly this man's face, bone structure, hairline, "
                "his thick slightly wavy BLACK hair, his thin round silver-rimmed glasses and his age; identity ONLY — do NOT copy its background, T-shirt, camera angle or lighting.")
    if path.startswith(FACE_DIR):
        who = next((v for k, v in PEOPLE if FACE_OF[k] == name[:-4]), "the character").split(" in a ")[0]
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
PROP_ADD = {"S09i": "assets/portraits/yamibaito-kf-pilot-ok/S09g-1.png", "S09k": "assets/portraits/yamibaito-kf-pilot-ok/S09g-1.png"}  # 店長 나머지 립싱크 컷은 합격판 S09g를 기준 얼굴로 추가 참조
_PROP_ADD_BENTO = {"S03e": "assets/portraits/bento-kf-r9/S03e-1.png",  # r9 싱크·그릇 구도는 합격, 손만 빠짐 → 그 판에 손을 넣는 편집
            "S09i": CELLS + "/prop-origami.png",  # 소품 참조 없는 「paper bird」가 2회 연속 종이학 → 울새 소품 셀 참조
            "S06a": CELLS + "/loc-shop96-curtain.png", "S13b": CELLS + "/loc-shop26-ots.png"}  # 참조 없는 t2i 시계 인서트에 사람 얼굴 2회 → 무인 장소 판 참조(edit)  # 소품 참조 없는 「paper bird」가 2회 연속 종이학 → 울새 소품 셀 참조
ONE_TAKE = {"H4", "S02b", "S02ba", "S02g", "S03b", "S04h", "S06c"}  # 무인·소품 단순 컷은 1장  # 재생성 중 단순 결함 컷은 1장(승인 예산 안, 2026-10-20)
NO_BACKCELL = set()  # 뒷모습 전신 셀이 원경 전신 구도를 끌어옴 — 앞 인물은 글로만
NO_LOC = set()  # 장소 참조가 원경·후광(오려 붙인 테두리)을 만든 컷 — 장소는 글로만
# 시범 1차(2026-10-20): 립싱크 3컷 6장 모두 장소 참조를 따라 원경(얼굴 1/6)으로 나옴 → 립싱크 컷은 장소 참조를 기본으로 뺀다(제18장 4)
KEEP_LOC = set()
DRY_ONLY = {"S10j", "S11b"}
TEARS_POOL_TXT = ("Realistic tears as in a live-action film: glossy wet eyes brimming with tears pooled along the lower lids and lashes, catching the light, "
                  "about to spill but NOT yet running — both cheeks still completely DRY, no tear track; natural skin tone, matte skin, NO makeup, no pink eyelids, "
                  "natural dark brown irises, clear white sclera.")
FACE_CU = ("FRAMING FIRST — CLOSE-UP with a normal 85mm perspective: the head and shoulders fill the frame, the face one third of the frame height or larger, "
           "cut at the chest; NOT a wide shot, NOT full body, NOT fisheye, NOT distorted, no floor or feet visible; the place is only a soft blurred background.")
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
    if sc["id"] in NO_LOC or sc["kind"] == "d" or (sc["kind"] == "face" and sc.get("size") in ("cu", "ecu") and sc["id"] not in KEEP_LOC):
        refs = [r for r in refs if not os.path.basename(r).startswith("loc-")]
    people = [r for r in refs if who_of(os.path.basename(r))[0]]
    if any(os.path.basename(r).startswith("tencho-") and not os.path.basename(r).endswith("-back.png") for r in people) and sc["kind"] in FACE_KINDS:
        # 店長 = 고니감독님 카메오: 실제 사진을 1번 참조. 시범 r2 실증: 시트 셀·얼굴 크롭(흰머리 섞임)이 백발을 끌어옴 → 정체 참조는 사진만
        refs = [CAMEO] + [r for r in refs if not (os.path.basename(r).startswith("tencho-") and not os.path.basename(r).endswith("-back.png"))]
        people = [CAMEO] + [r for r in people if not os.path.basename(r).startswith("tencho-")]
    is_back = any(os.path.basename(r).endswith("-back.png") for r in refs) and sc["kind"] != "d"
    if sc["kind"] in FACE_KINDS and not is_back:  # 시범에도 얼굴 크롭(동일 인물 — 제19장 7 ①)  # 배경 없는 얼굴 크롭을 1번 참조로(동일 인물)
        face = []
        for r in people:
            k, _ = who_of(os.path.basename(r))
            if r == CAMEO:
                continue
            f = f"{FACE_DIR}/{FACE_OF[k]}.png"
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
    elif sc["kind"] == "face" and sc.get("size") == "cu":
        parts.append(FACE_CU)
    if sc["kind"] in ("face", "d") and len([r for r in refs if who_of(os.path.basename(r))[0] and not os.path.basename(r).endswith("-back.png")]) == 1 and not sc.get("ots"):
        parts.append("PEOPLE LOCKED: exactly ONE person in the whole frame — this person appears only ONCE, no second copy of him in the background, no reflection, no other people.")
    if sc["id"] in SHOT_FIX:
        parts.append(SHOT_FIX[sc["id"]])
    if sc["kind"] == "d" and sc["id"] not in EMO_OVERRIDE and len(people) >= 2:
        parts.append(speaker_close(sc, people))
    elif sc["kind"] == "d" and sc["id"] not in EMO_OVERRIDE:
        parts.append(f"SPEAKER CLOSE: {short(people[0]) if people else 'the speaker'} is about one metre from the camera, head and shoulders filling about half of the frame width, "
                     "the face one third of the frame height or larger, cut at mid-chest; NO legs, NO feet, NO floor, NO bed visible; the room is only a soft blur behind the head.")
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
        parts.append("Mouth gently closed or barely parted (speech is added later); natural skin texture, both eyes sharp and symmetrical; plain bare earlobes. GAZE LOCKED: the eyes look toward the other person at the three-quarter angle, NEVER into the camera lens.")
    parts.append(REAL)
    parts.append(FULL)
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    if sc["id"] in DRY_ONLY:  # r4 실증: 「고인 눈물」 문장이 있으면 2회 연속 뺨에 줄기 → 눈물 문장 자체를 뺀다(젖은 눈은 i2v·립싱크 앞뒤 컷으로)
        parts = [x for x in parts if not x.startswith("Realistic tears")]
        parts = [x.replace(TEARS_POOL_TXT, "").replace("eyes brimming with pooled tears, ", "").replace("eyes wet but not running, ", "").replace("eyes brimming", "eyes glistening") for x in parts]
        parts.insert(2, "EYES: slightly glossy from exhaustion, otherwise normal; both cheeks completely DRY and clean — NO tear, NO tear track, NO drop anywhere on the face.")
    prompt = " ".join(parts)
    for a, b in EYE_FIX:
        prompt = prompt.replace(a, b)
    if sc["id"] not in DRY_ONLY and (re.search(r"\btears?\b|wet eyes|eyes wet|brimming", " ".join([sc["subject"], sc.get("act") or "", sc.get("motion") or ""]).lower()) or sc.get("expr") == "wet"):  # 시범 1차: 네거티브 「tear streams」가 검출돼 6장 전부 눈물 → 컷 문장만 본다
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
            is_d = sc["kind"] == "d" and bool(sc.get("line"))
            if stage.startswith("b") and is_d:
                continue
            if stage == "a" and not is_d:
                continue
            if only and sc["id"] not in only:
                continue
            if stage in ("b1", "b2"):  # 90분 상한(제19장 9 ⑧) → 비립싱크 컷을 앞·뒤 절반으로
                rest = [x["id"] for x in sb["scenes"] if x.get("keyframe") and not (x["kind"] == "d" and x.get("line"))]
                half = len(rest) // 2
                if (stage == "b1") != (rest.index(sc["id"]) < half):
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
    json.dump({"_설명": f"yamibaito PHASE 4 키프레임 {name} (build_yamibaito_keyframes.py 생성, 직접 수정 금지). seedream v4 edit 2560x1440, 약 0.03달러/장.", "_style_preset": sb["preset"], "characters": chars},
              open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(c["count"] for c in chars)
    print(f"{name} 키프레임 {len(chars)}컷 {n}장 → {path} (약 {n * 0.03:.2f}달러)")


if __name__ == "__main__":
    main()
