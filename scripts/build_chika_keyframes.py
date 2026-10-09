#!/usr/bin/env python3
"""『地下倉庫の伝票』 PHASE 4 키프레임 스펙 생성기 (build_tower_keyframes.py 구조, 규격 제7장 1·5·7).

scripts/storyboard/chika.json(PHASE 3)을 읽어 generate_portraits.py 스펙을 만든다. 스펙을 손으로 고치지 않는다.
단계:
  pilot    scripts/portraits/chika-kf-pilot.json  파일럿 3장(S03d 곤도 OMNI CU · S15e 사오리 OMNI CU · S11d 곤도 역광 실루엣)
  a        scripts/portraits/chika-kf-a.json      OMNI 대사 CU 27장 — 참조 = PHASE 2 셀(표정 셀 + 로케이션)
  b        scripts/portraits/chika-kf-b.json      나머지 — 얼굴이 보이는 컷은 A에서 승인한 인물별 기준 얼굴을 1번 참조로 추가
  collect  승인된 pilot/a/b 결과를 assets/portraits/chika-keyframes/<id>-1.png(스토리보드 경로)로 모은다
generate-video.yml portraits_spec=<스펙> → assets/portraits/<스펙>/<id>-1.png
사용법: python3 scripts/build_chika_keyframes.py pilot|a|b[:ID,ID]|collect
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "chika.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "chika-kf-{}.json")
KF_DIR = "assets/portraits/chika-keyframes"
STAGE_DIRS = ("assets/portraits/chika-kf-pilot", "assets/portraits/chika-kf-pilot-r", "assets/portraits/chika-kf-a", "assets/portraits/chika-kf-a-r",
              "assets/portraits/chika-kf-b", "assets/portraits/chika-kf-b-r")
PILOT = ["S03d", "S15e", "S11d"]
KF_RATE = 0.04

# 인물 식별 특징(PHASE 2 마스터 시트에서 잠근 것) — 참조 셀 설명과 함께 글로 한 번 더 못 박는다(제7장 7)
PEOPLE = {
    "saori": "Saori (34, straight black shoulder-length hair with bangs, upper half tied back in a small knot, thin silver-rimmed oval glasses)",
    "saori-b": "Saori (34, straight black shoulder-length hair with bangs, upper half tied back in a small knot, thin silver-rimmed oval glasses, light-grey knit sweater + navy canvas apron)",
    "saori-e": "Saori (34, black hair with bangs tied back in a low bun, thin silver-rimmed oval glasses)",
    "gondo": "Gondo (52, heavyset, double chin, salt-and-pepper hair slicked straight back, thick gold-rimmed rectangular glasses, glossy navy double-breasted suit, wine-red tie)",
    "miyamoto": "Miyamoto (64, thin, short white hair, full bushy white moustache, half-moon reading glasses hanging on a black cord around the neck, not on the face)",
    "kiritani": "Kiritani (early 50s, lean, hollow cheeks, short neatly parted black hair with grey temples, frameless rimless glasses)",
    "okochi": "Okochi (mid-60s, square jaw, short silver hair, thick dark eyebrows, NO glasses)",
}
# 인물별 기준 얼굴 = A단계 승인 OMNI 컷(제7장 7: 기준 얼굴은 대사 키프레임). 사오리 엔딩(saori-e)은 대사 컷이 없어 셀 유지.
FACE_KF = {"saori": "S03c", "saori-b": "S15e", "gondo": "S03d", "miyamoto": "S06c", "kiritani": "S01b", "okochi": "S16b"}
FACE_KINDS = ("face", "react", "d", "sil")
ANCHOR_FALLBACK = {"saori": "S15e"}
# 표정별 기준 얼굴(A단계 2차 실증: 미소 기준 S06c로 만든 S15j가 「무표정」 지시에도 미소를 유지) — 표정 셀이 있으면 같은 표정의 승인 컷을 기준으로
FACE_KF_BY_EXPR = {"miyamoto-expr2": "S15g", "miyamoto-expr3": "S08b", "gondo-expr3": "S14b", "gondo-expr2": "S12b",
                   "saori-b-expr2": "S11c", "saori-expr2": "S03c", "okochi-expr3": "S16h", "kiritani-expr2": "S14c"}   # 자기 자신이 기준 얼굴인 컷을 재생성할 때 쓸 같은 인물의 다른 기준(사무실 사오리 → 지하 사오리 얼굴)   # sil: 실루엣이라도 체형·머리 윤곽은 기준 얼굴 컷을 따른다

TIGHT = ("FRAMING FIRST: a tight single-person chest-up close-up — head and shoulders fill the frame, the top of the head near the top edge, "
         "the frame cut at mid-chest; the face occupies about one third of the frame height; hands NOT visible; NOT a medium shot, NOT a full-body shot. "
         "Full-frame 16:9 image, no black bars.")
# 눈물 규칙(고니감독님 확정 2026-10-08, #01 S03e 실증: 굵고 반짝이는 젤 같은 눈물 줄기 → 불합격)
TEARS_RE = re.compile(r"\btear|teary|weep|sob|wet eye|brimming|welling|glisten|moist", re.I)
TEARS = ("TEARS RULE: tears must look like real human tears — eyes brimming with a thin film of water that pools along the lower lids and catches "
         "a tiny highlight, the eye rims and the tip of the nose slightly reddened, lashes a little damp; at most ONE thin, barely visible wet trail "
         "on one cheek, following the natural curve from the inner corner of the eye; matte natural skin elsewhere. NO thick glossy gel-like streaks, "
         "NO multiple parallel lines, NO shiny drawn-on drops, NO tears on both cheeks at once.")
TEARS_DRY = "The eyes are glistening and wet but NO tear runs down the cheek — the emotion is held back."
# B단계 1차 검수(2026-10-08): 손·소품 인서트 12컷이 인물 얼굴·미디엄으로 생성됨(프롬프트의 Characters 문장이 얼굴을 그리게 함)
INSERT_FIRST = ("INSERT SHOT — NO FACE: this frame contains ONLY the hands, object or body part described below; NO face, NO head, NO eyes, "
                "NO full body anywhere in the frame; the frame is cut at the wrist or forearm; the camera is within one metre of the subject.")
BE_FIRST = ("CAMERA DIRECTLY OVERHEAD, pointing STRAIGHT DOWN at 90 degrees (bird's-eye): the floor fills the entire frame, the top of the head and "
            "shoulders are seen from above, no walls or ceiling visible, no horizon.")
CHOKER_FIRST = ("CHOKER CLOSE-UP: the face fills the ENTIRE frame from just above the eyebrows to just below the lower lip; the top of the head, "
                "chin, neck and shoulders are cut off by the frame edges; 85mm lens, extremely shallow depth of field.")
BANNER_FIRST = ("The long banner above the stage is a PLAIN BLANK white cloth with NO printing, NO characters, NO logo — completely empty; "
                "the projection screen is a plain glowing rectangle.")
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
LOC_NOTE = {
    "loc-aud": "The auditorium walls and stage are plain; the projection screen, the stage banner and any lectern plate are completely blank.",
    "loc-off": "Open-plan office: monitors show only a blank blue-grey glow, every paper, binder spine, partition label and whiteboard is completely blank; no posters with writing.",
    "loc-ev": "Elevator hall: the floor indicator is a plain dark panel with no digits; wall plates are blank brushed steel.",
    "loc-arc": "Basement archive: cardboard box labels, binder spines and the door plate are completely blank; no readable writing on any paper.",
    "loc-arcv": "Basement archive: cardboard box labels, binder spines and the door plate are completely blank; no readable writing on any paper.",
    "angle-arc": "Basement archive: cardboard box labels, binder spines and the door plate are completely blank; no readable writing on any paper.",
    "loc-cor": "Basement corridor: pipe tags and the door plates are blank; no stencilled letters on walls or pipes.",
    "loc-bq": "Banquet hall: the stage banner and the projection screen are completely blank; table cards and name tags are blank white.",
    "angle-bq": "Banquet hall: the stage banner and the projection screen are completely blank; table cards and name tags are blank white.",
    "prop-case": "The attaché case has NO logo, NO monogram, NO tag — plain leather and brass only.",
    "prop-tripod": "The tripod and camera have NO brand logo or lettering.",
}


# 파일럿 1차 검수(2026-10-08) 결과 보정 문장 — 프롬프트 맨 앞에 넣어 참조 셀(흰 배경·플랫 조명)보다 우선시킨다
FIX = {
    # S03d: 미디엄(노트북·손 노출)·플랫 밝은 조명·친절한 미소·아이레벨로 생성됨 → 설계(로우앵글 CU·압박 형광등·비웃음)
    "S03d": ("LIGHTING AND FRAMING NEXT. The office is dim at the edges: the only strong light is a hard, cold fluorescent panel directly above "
             "Gondo, pressing straight down — bright forehead and nose bridge, deep dark eye sockets behind the gold-rimmed glasses, a hard shadow under "
             "the chin and nose, the far desks fading into cool shadow; NO bright even daylight, NO flat lighting. Camera is BELOW his eye line "
             "looking UP at him (low angle), tight chest-up close-up: head and shoulders fill the frame, cut at mid-chest; NO laptop, NO desk, NO hands "
             "in the frame. Expression: a thin one-sided SNEER — lips pressed with one corner pulled up, eyes narrowed, chin raised, looking down his nose "
             "at the camera with contempt; NOT a friendly smile, NOT warm."),
    # A단계 1차 검수(2026-10-08): S03g는 S03d와 같은 장면·같은 압박 조명이어야 함(밝은 대낮 사무실로 생성됨)
    "S03g": ("LIGHTING FIRST. The office is dim at the edges: the only strong light is a hard, cold fluorescent panel directly above Gondo, pressing "
             "straight down — bright forehead, deep dark eye sockets behind the gold-rimmed glasses, hard shadow under the chin, the far desks fading "
             "into cool shadow; NO bright daylight, NO flat lighting. Camera BELOW his eye line looking up. He leans slightly toward the lens, eyes "
             "narrowed, mouth closed in a hard line — cold threat, NOT smiling."),
    # S03c: 기준 얼굴(지하 사오리 S15e)에서 얼굴만 가져오고 의상은 사무실 정장으로
    "S03c": ("WARDROBE: a plain navy-blue tailored skirt suit over a plain white blouse — NOT the grey sweater, NOT the apron of reference image 1; "
             "only the face, hair and glasses come from reference image 1."),
    # 2차 재생성 검수: S12b 이 드러난 웃음(OmniHuman 입 다묾 위반) → 입 다문 득의의 웃음, S15j 미소+지하 창고 배경 → 무표정·연회장
    "S12b": "A flushed, triumphant GRIN with the lips CLOSED — corners of the mouth pulled wide, cheeks raised, eyes narrowed with glee; NO teeth, mouth not open.",
    "S15j": ("He is standing in the BANQUET HALL among guests in dark suits (chandeliers and the blank stage screen blurred behind) — NOT in the archive, "
             "NO desk lamp, NO shelves. Expression: NO smile — mouth set in a firm straight line, eyes fixed on the camera, brows level, grave and steady."),
    # 감독님 지적(2026-10-08): S17b 손이 뒤통수 뒤에서 나와 카드를 쥔 기이한 자세·검은 머리(곤도 아님)·현수막 글자 → 측면 구도로 재설계
    # S03e(감독님 지적 2026-10-09): 「떨어지는 순간」을 정지 컷으로 써서 서류가 5초간 공중에 떠 있음 → 「떨어진 뒤」로 재설계(정지 푸시인은 정지 상태만, 제11장 16)
    "S03e": ("PHYSICS FIRST: nothing is in mid-air. The moment AFTER the drop: a thick stack of blank white papers studded with blank yellow sticky notes "
             "has already landed and lies crumpled and tilted INSIDE a steel wire-mesh wastebasket on a grey office carpet, the top sheets fanned up over "
             "the rim and one corner of the stack hanging over the edge, two blank yellow sticky notes fallen flat on the carpet beside the bin. "
             "Everything rests on a surface and obeys gravity. High angle extreme close-up at knee height, the wastebasket fills the lower right third, "
             "a grey desk leg and a black office chair base behind it, cold fluorescent office light. No hands, no people, no readable text anywhere."),
    # S13d(자동 경고, 제11장 16): 와인이 튀는 순간이 정지 → 「쏟아진 뒤」 상태
    "S13d": ("PHYSICS FIRST: nothing is in mid-air, no flying droplets, no splash frozen in time. The moment AFTER the spill: a dark red wine stain has "
             "already soaked into the red banquet carpet in an irregular wet patch beside a pair of WOMEN'S plain black flat ballet shoes with dark-blue JEANS hems (Saori's feet; NOT men's leather dress shoes, NOT suit trousers) seen from the side at floor "
             "level, a toppled empty wine glass lying on its side at the edge of the stain, a few settled drops glistening on the carpet pile. "
             "High angle extreme close-up at floor level, shallow depth of field, warm chandelier light from above, banquet tables as soft bokeh. "
             "Shoes point to the right in profile, ankles and dark trouser hems only. No faces, no readable text."),
    # S06d(감독님 지적 2026-10-09 「구도가 이상」): 선반 꼭대기 부감이 공간 붕괴(책상이 벽에 매달림, 인물이 큼) → 통로 끝 천장 높이에서 긴 통로를 내려다보는 명료한 기하
    "S06d": ("GEOMETRY FIRST: a long straight basement aisle seen from a camera mounted at ceiling height at the near end of the aisle, looking down "
             "and along the aisle. Two tall grey steel racks run from the bottom corners of the frame to a vanishing point near the top centre, loaded "
             "with yellow archive boxes with blank labels; the concrete floor is clearly visible as a bright strip down the middle. Saori stands on that "
             "floor far down the aisle, SMALL in the frame (about one fifth of the frame height), facing the camera and tilting her head up to look at the "
             "upper shelves, a cardboard box held in both arms at her waist. No desk, no printer, no lamp in this frame. Hard cold fluorescent tubes "
             "overhead, dust in the beams, deep shadows between the racks. Single coherent perspective, straight vertical racks, no tilt."),
    # S14i(감독님 지적 2026-10-09): 역광 림라이트를 인물 윤곽선(푸른 테두리 발광)으로 그려 오려 붙인 듯 보임 → 테두리 금지, 자연광만
    "S14i": ("IDENTITY FIRST: the man standing alone in the centre IS GONDO — a HEAVYSET Japanese man aged 52 with a fleshy face and double chin, "
             "SALT-AND-PEPPER hair slicked straight back, THICK GOLD-RIMMED rectangular glasses, glossy navy double-breasted suit, white shirt, "
             "wine-red tie, chunky gold wristwatch; a wide, bulky silhouette, NOT a slim young man, NOT bareheaded of glasses (1차 생성: 날씬한 젊은 남성·안경 없음 → 다른 사람). "
             "LIGHTING SECOND: NO outline, NO glow, NO halo, NO luminous edge around any person — the figures are lit only by the warm chandeliers above "
             "and the cool projector screen behind, with soft natural falloff; edges of the dark suit blend naturally into the dim room. "
             "High angle from the balcony: Gondo stands alone in the middle of a widening empty circle of red carpet, head slightly bowed, arms at his "
             "sides, face dim and unreadable; the guests have stepped back to the edges of the circle as soft dark shapes with faces out of focus. "
             "Banquet tables with white cloths around, a blank white projector screen far behind, chandelier bokeh top right. No readable text."),
    "S17b": ("STAGING: side view at shoulder height, very close. On the LEFT edge, the back of a heavyset man's head and thick neck with SLICKED-BACK "
             "SALT-AND-PEPPER hair and a navy suit collar, face turned away and NOT visible. From the RIGHT, two hands in dark security-guard uniform sleeves "
             "lift a plain blank white ID card on a black lanyard up and over the top of his head, the lanyard loop stretched open above the hair. "
             "Hands have exactly five fingers each, natural wrists. Background: the banquet hall dissolved into creamy bokeh — no readable banner, "
             "no faces, only soft warm lights."),
    # B단계 3차: S12b2 가죽끈 시계·라벨 글자 → 곤도의 금속 금시계, 무지 병
    "S12b2": ("The hand is a FAT man's hand with thick fingers wearing a CHUNKY GOLD METAL BRACELET WATCH (no leather strap), a navy suit cuff and white shirt cuff; "
              "the champagne bottle has a completely BLANK dark label with no printing; foam runs over the rim of the flute."),
    # B단계 2차: S10f 뒷모습 미디엄 → 손만, S16d 수직 부감
    "S10f": "ONLY a woman's hand and index finger on the laptop trackpad fill the frame, the keyboard edge and the glowing screen bottom at the top edge; the camera is 40 cm above the hand.",
    "S16d": ("Seen from DIRECTLY ABOVE at 90 degrees: the frame shows only the red carpet floor and, in the centre, the top of a heavyset man's head with "
             "slicked salt-and-pepper hair, his navy-suited shoulders hunched as he kneels; no face visible, no walls, no ceiling, no tables."),
    # S11c: 책상 3/4 미디엄·손 노출·담담한 표정으로 생성됨 → 정면 CU + 공포
    "S11c": ("Saori faces the camera directly, seated at the desk but framed chest-up so the desk and her hands are NOT visible; the warm desk lamp lights "
             "one side of her face, the other side falls into cool shadow. Expression: FEAR held in — eyes wide and fixed, pupils large, lips pressed "
             "together, a tense throat as she swallows; NOT calm, NOT smiling."),
    # S16f: 입을 벌리고 이가 보임 → OmniHuman용 입 다묾
    "S16f": "Her mouth is CLOSED with the lips gently together, chin level, steady eyes looking into the lens; no teeth visible.",
    # S18b: 입 벌린 웃음·미디엄 → 입 다문 장난스러운 미소
    "S18b": "A broad PLAYFUL smile with the lips CLOSED (no teeth), eyes crinkled, looking into the lens.",
    # S18e: 옆을 보는 미디엄 → 정면 CU, 시선만 살짝 먼 곳
    "S18e": ("Miyamoto's face is turned toward the camera (within 15 degrees of frontal); only his EYES drift slightly up and away to the distance, "
             "a slow sad-sweet closed-mouth smile under the moustache. Chest-up close-up, hands not visible."),
    # S11d: 아이레벨로 생성되고 하단에 흰 띠(레터박스) → 바닥 높이 극단 로우앵글, 전체 화면
    "S11d": ("CAMERA FIRST: the camera sits on the concrete floor of the archive (lens about 30 cm above the floor) looking UP: the open steel door and "
             "the backlit figure tower above the lens, the floor runs away from the bottom edge of the frame toward the door, the fluorescent tube and "
             "ceiling converge upward. Extreme low angle, 35mm lens. Full-frame 16:9 image with NO white or black strip at any edge."),
}


# 파일럿 2차: 시트 표정 셀 1(「비웃음」)이 실제로는 옅은 미소라 친절한 얼굴을 끌고 옴 → 정면 중립 셀 + 표정은 글로 지시
# 파일럿 2차 합격 → 곤도 「비웃음」 컷 전부에 적용(gondo-expr1 참조 시 자동 치환 + 표정 문장)
REF_SWAP = {"*": {"gondo-expr1.png": "gondo-front.png"}}
SNEER = ("EXPRESSION FIRST: Gondo is NOT smiling. His face shows cold CONTEMPT — mouth closed with the lips pressed into a thin line and ONE corner "
         "pulled slightly up into a sneer, nostrils a little flared, eyelids half lowered, brows slightly raised as he looks DOWN his nose "
         "while his chin is raised; a cruel, bored, superior look.")


# 2차 재생성 검수: 얼굴이 없어야 하는 비-ins 컷(실루엣 ECU 등)도 인서트 규칙 적용
NOFACE = {"S12b2", "S16d"}
NO_LOC_REF = {"S16d"}   # 장소 셀이 원근을 강제해 수직 부감이 안 나옴 → 바닥·정수리만 글로


def person_key(path):
    b = os.path.basename(path).rsplit(".", 1)[0]
    for k in ("saori-b", "saori-e", "saori", "gondo", "miyamoto", "kiritani", "okochi"):
        if b == k or b.startswith(k + "-"):
            return k
    return None


def describe(path, i):
    name = os.path.basename(path).rsplit(".", 1)[0]
    if path.startswith(STAGE_DIRS) or path.startswith(KF_DIR):
        k = person_key(path) or next((k for k, v in FACE_KF.items() if name.startswith(v)), "")
        who = PEOPLE.get(k, "this character")
        return (f"Reference image {i} is the APPROVED keyframe face of {who}: reproduce exactly this face, hair, eyewear and wardrobe; "
                "ignore its background and framing unless the description below says otherwise.")
    k = person_key(path)
    if k:
        who = PEOPLE[k]
        hair = "facial hair" if k in ("miyamoto", "gondo", "kiritani", "okochi") else "clean face with NO facial hair"
        if "expr" in name:
            return (f"Reference image {i} is the expression cell of {who}: copy exactly this face, hair, eyewear, {hair} and wardrobe, and this "
                    "emotional expression (about 60 percent intensity); ignore its plain background and any borders or labels.")
        if "full" in name:
            return (f"Reference image {i} is the full-body wardrobe cell of {who}: copy exactly the body type, wardrobe and shoes; ignore its plain background.")
        return (f"Reference image {i} is the master face cell of {who}: copy exactly this face, hair, eyewear, {hair} and wardrobe; "
                "ignore its plain background and any borders or labels.")
    if name.startswith("angle-"):
        return (f"Reference image {i} is the SAME location seen from this camera angle: match its architecture, colours, set dressing, light direction and depth; "
                "people in it are only a placement guide; ignore any borders or labels.")
    if name.startswith("prop-"):
        return f"Reference image {i} is the prop: reproduce exactly its shape, material and colour."
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing and light direction; "
            "ignore any borders or labels.")


def notes(refs):
    out = []
    for r in refs:
        b = os.path.basename(r)
        for k, v in LOC_NOTE.items():
            if b.startswith(k) and v not in out:
                out.append(v)
    return out


def build(sc, face_refs, drop_expr=False):
    """drop_expr: 기준 얼굴이 있으면 작은 표정 셀을 빼고(얼굴형 드리프트 원인, A단계 정밀 대조 실증) 표정은 글로만 지시"""
    refs = list(face_refs) + [r for r in sc["refs"] if r not in face_refs]
    if drop_expr and face_refs:
        refs = [r for r in refs if "-expr" not in os.path.basename(r)]
    if sc["id"] in NO_LOC_REF:
        refs = [r for r in refs if not os.path.basename(r).startswith(("loc-", "angle-"))]
    if sc["kind"] == "ins" or sc["id"] in NOFACE:   # 인서트는 인물 셀을 참조하면 얼굴을 그린다(B단계 실증) → 장소·소품 셀만, 손·의상은 글로
        refs = [r for r in refs if not person_key(r) and not r.startswith(STAGE_DIRS) and not r.startswith(KF_DIR)]
    swap = {**REF_SWAP["*"], **REF_SWAP.get(sc["id"], {})}
    sneer = any(os.path.basename(r) == "gondo-expr1.png" for r in refs)
    refs = [os.path.join(os.path.dirname(r), swap.get(os.path.basename(r), os.path.basename(r))) for r in refs]
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    if drop_expr and face_refs:
        loc_i = next((i + 1 for i, r in enumerate(refs) if os.path.basename(r).startswith(("loc-", "angle-"))), None)
        if loc_i:   # 2차 재생성 실증(S15j): 기준 얼굴 컷의 배경(지하 창고)이 연회장 컷으로 새어 들어옴
            parts.insert(1, f"SETTING: the place is reference image {loc_i} ONLY; the background, furniture, lamps and lighting of reference image 1 "
                            "must NOT appear.")
        parts.insert(1, "IDENTITY FIRST: the person is EXACTLY the one in reference image 1 — same face shape, jaw, cheekbones, nose, eyes, eyebrows, "
                        "skin tone, age, hairstyle and eyewear; only the expression, lighting and framing described below change.")
    if sc["kind"] == "d":
        parts.insert(1, TIGHT + " Mouth CLOSED (lips together, no teeth visible); facing the camera, looking into the lens.")
    if sneer:
        parts.insert(1, SNEER)
    if sc["id"] in FIX:
        parts.insert(1 + sneer, FIX[sc["id"]])
    kp = sc["keyframe_prompt"]
    if sc["kind"] == "ins" or sc["id"] in NOFACE:
        kp = re.sub(r" Characters: .*?(?= Camera:)", " No person's face is visible.", kp)
        parts.insert(1, INSERT_FIRST)
    if sc["angle"] == "BE":
        parts.insert(1, BE_FIRST)
    if sc["size"] == "ch":
        parts.insert(1, CHOKER_FIRST)
    if any(os.path.basename(r).startswith(("loc-bq", "angle-bq", "loc-aud")) for r in refs):
        parts.insert(1, BANNER_FIRST)
    parts.append(kp)
    parts += notes(refs)
    if sc["kind"] == "d":
        parts.append(TIGHT)
        parts.append("Soft fill light keeps the mouth and jaw readable (lip-sync cut). Mouth gently closed or barely parted (speech is added later); "
                     "natural skin texture, both eyes sharp and symmetrical.")
    else:
        parts.append(FULL)
    if TEARS_RE.search(sc["subject"]):
        parts.append(TEARS_DRY if re.search(r"but dry|held back|no tear", sc["subject"], re.I) else TEARS)
    if sc["kind"] == "sil":
        parts.append("The figure is a true backlit silhouette: no facial features readable, only outline, hair shape and body mass.")
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": " ".join(parts)}


def face_refs_for(sc):
    out = []
    if sc["kind"] not in FACE_KINDS:
        return out
    for r in sc["refs"]:
        k = person_key(r)
        if k and k in FACE_KF:
            cell = os.path.basename(r).rsplit(".", 1)[0]
            kf_id = FACE_KF_BY_EXPR.get(cell, FACE_KF[k])
            if kf_id == sc["id"]:
                kf_id = FACE_KF[k]
            p = f"{KF_DIR}/{kf_id}-1.png"   # collect 뒤의 승인 키프레임(파일럿·A·재생성 포함)
            if sc["id"] == FACE_KF[k]:
                if k not in ANCHOR_FALLBACK:
                    continue
                p = f"{KF_DIR}/{ANCHOR_FALLBACK[k]}-1.png"
            if not os.path.exists(os.path.join(ROOT, p)):
                raise SystemExit(f"{sc['id']}: 기준 얼굴 {p} 없음 — A단계 먼저")
            if p not in out:
                out.append(p)
    return out


def done(sc):
    """앞 단계(파일럿 등)에서 이미 생성·승인된 컷은 유료 재생성하지 않는다."""
    return any(os.path.exists(os.path.join(ROOT, d, f"{sc['id']}-1.png")) for d in STAGE_DIRS)


def collect(shots):
    os.makedirs(os.path.join(ROOT, KF_DIR), exist_ok=True)
    n, missing = 0, []
    for s in shots:
        dst = os.path.join(ROOT, s["keyframe"])
        src = next((os.path.join(ROOT, d, f"{s['id']}-1.png") for d in STAGE_DIRS[::-1]
                    if os.path.exists(os.path.join(ROOT, d, f"{s['id']}-1.png"))), None)
        if src is None:
            missing.append(s["id"])
            continue
        if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
            shutil.copy2(src, dst)
            n += 1
    print(f"{KF_DIR}: {n}장 복사, 누락 {len(missing)}장" + (f" → {', '.join(missing)}" if missing else ""))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    stage, _, only = arg.partition(":")
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    shots = [s for s in sb["scenes"] if s.get("keyframe")]
    if stage == "collect":
        return collect(shots)
    if stage == "pilot":
        items = [build(s, []) for s in shots if s["id"] in PILOT]
    elif stage == "a":
        # 재생성(only)은 승인 기준 얼굴을 1번 참조로 + 표정 셀 제거(정밀 대조 2026-10-08: 25장 중 11장 얼굴형 드리프트)
        items = [build(s, face_refs_for(s) if only else [], drop_expr=bool(only)) for s in shots if s["kind"] == "d" and (only or not done(s))]
    elif stage == "b":
        items = [build(s, face_refs_for(s), drop_expr=True) for s in shots if s["kind"] != "d" and (only or not done(s))]
    else:
        raise SystemExit("단계: pilot|a|b[:ID,ID]|collect")
    if only:
        ids = set(only.split(","))
        items = [x for x in items if x["id"] in ids]
        stage += "-r"
    for x in items:
        for r in x["refs"]:
            if not os.path.exists(os.path.join(ROOT, r)):
                raise SystemExit(f"{x['id']}: 참조 없음 {r}")
    spec = {"_설명": f"chika PHASE 4 키프레임 {stage}(build_chika_keyframes.py 생성, 직접 수정 금지). {len(items)}장 약 {len(items) * KF_RATE:.2f}달러.",
            "_style_preset": sb["preset"], "characters": items}
    path = OUT.format(stage)
    json.dump(spec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(items)}장 약 {len(items) * KF_RATE:.2f}달러")


if __name__ == "__main__":
    main()
