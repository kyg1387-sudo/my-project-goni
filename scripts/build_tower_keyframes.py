#!/usr/bin/env python3
"""『タワマンのボスママ』 PHASE 4 키프레임 스펙 생성기 (build_yanagi_keyframes.py 구조, 규격 제7장 1·7).

scripts/storyboard/tower.json(PHASE 3)을 읽어 generate_portraits.py 스펙을 만든다. 스펙을 손으로 고치지 않는다.
단계:
  pilot  scripts/portraits/tower-kf-pilot.json  파일럿 3장(S01b 레이카 엘리베이터 OMNI · S13d 유미 총회 OMNI · S17b 레이카 바닥 부감)
  a      scripts/portraits/tower-kf-a.json      OMNI 대사 CU 13장 — 참조 = PHASE 2 셀(표정 셀 + 로케이션)
  b      scripts/portraits/tower-kf-b.json      나머지 — 얼굴이 보이는 컷은 A에서 승인한 인물별 기준 얼굴을 1번 참조로 추가
generate-video.yml portraits_spec=<스펙> → assets/portraits/<스펙>/<id>-1.png
사용법: python3 scripts/build_tower_keyframes.py pilot|a|b[:ID,ID]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "tower.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "tower-kf-{}.json")
KF_A = "assets/portraits/tower-kf-a"
PILOT = ["S01b", "S13d", "S17b"]

PEOPLE = {
    "yumi": "Yumi (42, chin-length black bob with side-swept fringe, thin silver-rimmed glasses, navy cardigan)",
    "reika": "Reika (40, long wavy chestnut hair, red lips, pearl earrings, cream tweed jacket, NO glasses)",
    "riko": "Riko (7-year-old girl, two low pigtails, mustard-yellow dress)",
    "odagiri": "Mr. Odagiri (mid-70s gentleman, combed-back white hair, white moustache, charcoal three-piece suit)",
    "tanto": "the property-management clerk (early 30s, short black hair, grey suit, NO glasses)",
    "mamaA": "Mama A (honey-brown curly bob, pink sweater)", "mamaB": "Mama B (sleek black high ponytail, white blouse, NO glasses)",
    "mamaC": "Mama C (long light-brown hair, beige dress)", "jumin": "the middle-aged resident (salt-and-pepper hair, navy polo shirt)",
}
FACE_KF = {"reika": "S06b", "yumi": "S13d", "odagiri": "S16f", "tanto": "S14m"}  # 인물별 기준 얼굴(A단계 승인 후 B에 1번 참조)
FACE_KINDS = ("face", "react", "d")
# 구도 참조(사용자 승인 시험 장면 CU): 가슴 위 CU 프레이밍이 넓게 빠지는 컷에 추가(파일럿 S13d 실증: 미디엄으로 생성됨)
FRAMING_REF = "assets/portraits/tower-ja-kf-test/S5-yumi-cu-1.png"
HALL_BG = "assets/portraits/tower-ja-cast/cells/loc-hall-day-wide-back.png"
REIKA_FACE = "assets/portraits/tower-kf-a/S01b-1.png"   # A단계 승인 레이카 얼굴(파일럿 합격)
ODA_FACE = "assets/portraits/tower-cast/cells/odagiri-front.png"
REIKA_HALL = "assets/portraits/tower-kf-a/S06b-1.png"   # A단계 2차 승인: 회의실(주민 착석) 배경의 레이카 — 얼굴+배경 기준
ODA_APPROVED = "assets/portraits/tower-kf-a/S16f-1.png"  # A단계 2차 승인: 풍성한 흰 콧수염의 오다기리(S16b와 동일 인물)
EXTRA_REFS = {"S13d": [FRAMING_REF], "S05e": [FRAMING_REF], "S19c": [FRAMING_REF],
              # A단계 1차 검수(2026-10-07): 구도 넓음·손 노출·배경 이탈·얼굴 불일치 → 승인 얼굴 + 구도 참조
              "S06b": [REIKA_FACE, FRAMING_REF], "S16b": [ODA_FACE, FRAMING_REF], "S16f": [ODA_FACE, FRAMING_REF],
              # A단계 3차: S01b 참조가 엘리베이터 배경·무표정을 끌고 옴(실증) → 회의실 승인 컷 S06b, 오다기리는 승인 컷 S16f
              "S13b": [REIKA_HALL], "S14l": [REIKA_HALL], "S15b": [REIKA_HALL], "S17e": [ODA_APPROVED, FRAMING_REF]}

TIGHT = ("Tight chest-up close-up: head and shoulders fill the frame, the top of the head near the top edge, the frame cut at mid-chest; "
         "the face occupies about one third of the frame height; hands NOT visible. Full-frame 16:9 image, no black bars.")
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
LOC_NOTE = {
    "loc-lobby": "The lobby walls and elevator surrounds are polished stone and brushed steel: NO paper notices, NO posters, NO floor-number displays with digits; any plaque or sign plate is completely blank.",
    "loc-hall": "The assembly-hall walls are plain white with no posters or papers; the projector screen, any banner and any nameplate are completely blank white.",
    "loc-kidsroom": "The kids-room walls have NO posters or papers with writing; the plaque beside the door is plain blank white.",
    "loc-office": "Binder spines and labels are completely blank; no papers with readable writing.",
    "prop-bag": "The burgundy quilted bag has NO logo, NO monogram, NO metal emblem — only plain quilting and a gold chain.",
}
COMPOSITION = {
    "S01b": TIGHT + (" Setting: inside the open mirrored passenger elevator of the luxury tower lobby, brushed steel and mirror soft behind her. "
                     "Expression at about 60 percent: a condescending, polite-but-cruel smirk, chin raised, eyes looking down; NOT a friendly smile."),
    "S13d": ("FRAMING FIRST: a tight single-person portrait close-up — Yumi's head and shoulders fill the frame, cut at mid-chest. " + TIGHT) + (" CAMERA DISTANCE: about one metre from her face with an 85mm lens — her head and shoulders fill the frame; "
                     "NOT a medium shot, NOT a full-body shot, her hands and waist are NOT visible. Setting: standing in the middle rows of the packed residents' assembly hall; behind her many seated residents are "
                     "only creamy out-of-focus colour blobs (NO recognizable faces, NO sharp people anywhere), the tall windows on the left. Expression: calm, resolute, "
                     "about 50 percent firmness; NOT smiling."),
    "S17b": (FULL + " Extreme bird's-eye view from directly above the stage floor: Reika is ALREADY sitting collapsed on the pale wood floor "
             "beside the lectern, legs folded to one side, shoulders slumped, her long chestnut hair falling forward, the open burgundy "
             "bag lying on the floor next to her with a few items spilled (a lipstick, a compact, a plain white envelope). She is small in "
             "the frame; her face is mostly hidden by her hair. Image upright."),
}



FIX_A = {
    "S05e": "FRAMING FIRST: tight chest-up portrait close-up of Yumi standing in the middle rows. Behind the subject the assembly hall is FULL of seated residents rendered only as creamy out-of-focus colour blobs (no recognizable faces), tall windows on the left, the blank projector screen soft in the background; NOT an empty room, NOT a plain studio wall.",
    "S06b": "FRAMING FIRST: tight chest-up close-up of Reika from slightly below, mocking smile. NO hands, NO arms, NO cane and NO lectern top visible in the frame. Behind the subject the assembly hall is FULL of seated residents rendered only as creamy out-of-focus colour blobs (no recognizable faces), tall windows on the left, the blank projector screen soft in the background; NOT an empty room, NOT a plain studio wall.",
    "S13b": "Same framing as the approved hall shot: tight chest-up close-up of Reika, a triumphant arrogant smile, chin raised high, eyes looking down. NO hands. The hall behind her is PACKED with seated residents as soft blurred shapes.",
    "S14l": "Same framing as the approved hall shot: tight chest-up close-up of Reika, now PANICKED — eyes wide and darting, eyebrows raised in alarm, lips parted, a bead of sweat on her temple, face slightly pale. NO hands. NOT smiling. NOT in an elevator.",
    "S15b": "Same framing as the approved hall shot: tight chest-up close-up of Reika, FURIOUS and losing control — brows drawn down hard, eyes blazing, teeth slightly bared, a few strands of hair out of place, flushed. NO hands. NOT smiling. NOT in an elevator.",
    "S16b": "FRAMING FIRST: tight chest-up close-up of Mr. Odagiri from slightly below, calm and dignified, strong window backlight rim on his white hair. NO hands, NO arms, NO cane and NO lectern top visible in the frame. He has a full neat WHITE moustache and deep wrinkles, mid-70s. Behind the subject the assembly hall is FULL of seated residents rendered only as creamy out-of-focus colour blobs (no recognizable faces), tall windows on the left, the blank projector screen soft in the background; NOT an empty room, NOT a plain studio wall.",
    "S16f": "FRAMING FIRST: tight chest-up close-up of Mr. Odagiri from slightly below, stern judging gaze. NO hands, NO arms, NO cane and NO lectern top visible in the frame. He has a full neat WHITE moustache and deep wrinkles, mid-70s — the same man as reference image 1. Behind the subject the assembly hall is FULL of seated residents rendered only as creamy out-of-focus colour blobs (no recognizable faces), tall windows on the left, the blank projector screen soft in the background; NOT an empty room, NOT a plain studio wall.",
    "S17e": "FRAMING FIRST: tight chest-up close-up of Mr. Odagiri from slightly below, looking down, calm and unforgiving. He MUST have the same FULL BUSHY WHITE MOUSTACHE (white mustache, thick and wide) as reference image 1 — never clean-shaven, never a thin moustache. NO hands, NO cane. Behind him the hall with soft blurred seated residents.",
}


# B단계 1차 검수(2026-10-07) 재생성: 레이카 기준 얼굴 S06b(미소)가 표정까지 끌고 옴 → 표정별 승인 컷을 기준 얼굴로
REIKA_BY_EXPR = {"panic": "assets/portraits/tower-kf-a/S14l-1.png", "tears": "assets/portraits/tower-kf-a/S17d-1.png"}
FIX_B = {
    "S01d": "Insert: the brushed-steel passenger elevator doors are almost fully closed, leaving only a narrow vertical gap of about a hand's width; through the gap we glimpse ONE slice of Reika's face with a red-lipped smirk. The steel door surfaces are matte brushed metal with NO reflections of faces. Exactly one person.",
    "S05f": "Low insert at knee height ONLY: on the stage a woman's knees in cream wide-leg trousers crossing one over the other, nude heels; her face and upper body are NOT in frame. NOT a full-body shot.",
    "S14h": "Eye-level tight chest-up close-up of Reika at the lectern, her face frozen in shock: eyes fixed and frightened, mouth slightly open, a single bead of sweat running down her temple, face pale. NO smile at all. No hands.",
    "S14n2": "High angle close-up of Reika (chest-up) staring down at something off-frame below, colour draining from her face, lips parted in fear. Her hands are NOT visible and she holds NOTHING.",
    "S16g": "Camera ABOVE her eye line looking DOWN (high angle), tight close-up of head and shoulders only — NOT a medium shot, the lectern is NOT visible. Reika trembling, lips parted, eyes glassy with fear, face pale. NOT smiling. No hands.",
    "S17a": "ONE single frame (NOT two panels, NOT a split screen): side insert at floor level of a woman's knees in cream wide-leg trousers buckling, nude heels wobbling on the pale wood stage floor; her upper body NOT in frame.",
    "S17e2": "High angle tight close-up of Reika SITTING ON THE FLOOR, devastated: mouth falling open, tears welling and running, mascara slightly smudged. NOT smiling. No hands.",
    "S17g": "High angle close-up of Reika SITTING ON THE FLOOR beside the lectern, looking up pleadingly with wet eyes toward the front row, desperate. NOT standing, NOT smiling.",
    "S19d": "High angle tight close-up of Reika in the lobby clutching a stack of moving boxes against her chest (box edges at the bottom of frame), jaw clenched, eyes lowered in humiliation, lips pressed tight. NOT smiling, NOT surprised.",
    "S14e": "", "S14a": "", "S14c": "",
    # 감독님 지적(완성본 검수 2026-10-07): 멀리 선 아이가 앞쪽 엄마 손을 잡는 원근 모순·아이가 3~4살로 보임 → 설계대로 손 ECU(얼굴 없음)
    "S01e": "EXTREME CLOSE-UP from directly above and slightly behind, ONE single frame: ONLY the small hand of a 7-year-old girl tightly gripping the hem of a woman's charcoal-grey wool skirt; the girl's mustard-yellow dress sleeve cuff at the wrist; the woman's navy cardigan hem at the top edge. NO faces, NO heads, NO full bodies — hands and fabric fill the frame. Polished marble lobby floor softly out of focus below. The child's fingers clearly separate, exactly five, small knuckles white from gripping.",
    # 감독님 지적(완성본 2026-10-07, 1:21): S03d가 설계(손바닥 인서트)와 달리 리코 전신 단독 컷 → 대사 중 마마A가 사라짐
    "S03d": "EXTREME CLOSE-UP, ONE single frame: ONLY the small open palm and fingers of a 7-year-old girl pressed flat against a clear glass door, seen from the corridor side; a mustard-yellow dress sleeve cuff at the wrist; beyond the glass the colourful play mats and toys of a bright kids room are softly blurred. NO face, NO head, NO full body — the hand fills the frame. Exactly five small fingers, natural child proportions.",
    # 감독님 지적(완성본 1:28): 굵고 반짝이는 젤 같은 눈물 줄기 4개 → 현재 컷을 편집해 눈물만 자연스럽게
    "S03e": "EDIT the reference image: keep EXACTLY the same girl, face, pigtails, framing, camera angle, lighting and kids-room background. "
            "ONLY change the tears: remove the thick glossy gel-like streaks completely. Instead: eyes brimming with tears that pool along the lower lids, "
            "eye rims and the tip of the nose slightly reddened, ONE thin, barely visible wet trail on one cheek only, natural skin texture, "
            "lips pressed and trembling. Realistic, subtle, matte skin — NO shiny liquid lines.",
    "S16h2": "Seen STRICTLY FROM BEHIND: Mr. Odagiri's back fills the right third of the frame — white hair from behind, charcoal suit back, dark wooden cane in his right hand; his face is NOT visible at all. He faces the stage at the far end of the packed hall.",
    # 크롭으로 못 고치는 인서트(얼굴을 자르면 4배 확대, 핸드 마이크라 스탠드를 쥔 손이 없음)
    "S05c": "Close insert of clapping hands at chest height: the camera is low and close, the top edge of the frame cuts across the three seated women's collarbones, so only their torsos and clapping hands are in the picture (pink sweater, white blouse, beige cardigan) with blurred seated residents behind. Do NOT draw heads; NO masks, NO circles, NO blur patches, NO stickers. Hands with exactly five fingers each.",
    # B 재생성 2차(2026-10-07): S14l(굳은 미소) 참조가 미소를 끌고 옴 → 재생성 합격 공포 얼굴, 빈 의자 배경 → 주민 뒷머리 전경(S16d)
    "S15c": "Medium of the front rows of seated residents (men in suits, women in blouses) startled by a shout: they lean back slightly in their chairs with wide eyes, a few cover their mouths with one hand. Arms stay DOWN — nobody raises arms, nobody throws hands up, nobody stands. Faces soft and unrecognizable.",
    "S15a": "Macro insert, ONE hand only: a woman's hand with a thin gold bangle and cream tweed sleeve cuff tightly gripping the vertical chrome shaft of a microphone stand on the wooden lectern, knuckles white with tension. The microphone is mounted on the stand (NOT handheld). Her face is NOT in frame. Exactly five fingers.",
}


FEAR_FACE = {"S14h": "assets/portraits/tower-cast/cells/reika-fear-3.png", "S16g": "assets/portraits/tower-cast/cells/reika-fear-3.png",
             "S14n2": "assets/portraits/tower-cast/cells/reika-fear-1.png"}
FEAR_HALL = "assets/portraits/tower-cast/cells/reika-fear-3.png"  # B 재생성 2차 합격 S14n2: 공포 얼굴 + 주민 배경(3차 기준)
HALL_FRONT = "assets/portraits/tower-kf-b/S16d-1.png"  # 승인 B: 단상의 레이카, 전경에 주민 뒷머리
BG_FRONT = ("Background geometry: the camera is among the seated audience facing the stage, so behind Reika are only the white wall, "
            "the window band and the pale projection screen, softly out of focus; the blurred backs of residents' heads fill the lower "
            "foreground edge. NO empty chairs anywhere.")


# 감독님 지적(회의장 일관성 2026-10-07): 빈 회의장 장소 셀(loc-hall-p*)을 참조한 컷이 빈 의자·다른 방·현수막 없음으로 나옴
# → 승인 컷(합성 전 원본: 현수막 무지)을 방 기준으로. 임시총회 = S05d(약 40명), 통상총회 = S13a(만석 100명 이상)
ROOM_RINJI = "assets/portraits/tower-kf-raw/S05d-1.png"
ROOM_TSUJO = "assets/portraits/tower-kf-raw/S13a-1.png"
ROOM_FIX = {**{k: ROOM_RINJI for k in ("S05a", "S05b", "S05c", "S06a", "S06d", "S06-2a")},
            **{k: ROOM_TSUJO for k in ("S14b", "S14f", "S14g", "S14k", "S14o", "S16g2", "S16h2", "S17f", "S17h")}}
CROWD = {ROOM_RINJI: "The hall is moderately filled: about forty residents seated in the rows (no large empty areas), matching the reference.",
         ROOM_TSUJO: "The hall is PACKED: every chair in every row is occupied by seated residents (over a hundred people), NO empty chairs anywhere in view."}


def describe(path, i):
    name = os.path.basename(path)
    if path in (ROOM_RINJI, ROOM_TSUJO):
        return (f"Reference image {i} is the APPROVED shot of this SAME assembly hall: copy exactly its room — floor-to-ceiling windows with the "
                "city view on the left wall, the long white banner (keep it plain, NO letters), the projection screen, the wooden lectern, grey "
                "chairs, pale wood floor, lighting and colour — and its audience density. Ignore the people's poses; the camera position is "
                "described below.")
    if path == "assets/portraits/tower-kf-b/S03e-1.png":
        return f"Reference image {i} is the image to EDIT."
    if name == "mamas-s14o.png":
        return (f"Reference image {i} shows the SAME three women (pink sweater + white pleated skirt, white blouse + black trousers, "
                "beige cardigan + cream skirt) seated in the hall: copy exactly their wardrobe and body types; the framing is described "
                "below (their heads are above the top edge of the frame).")
    if path == HALL_FRONT:
        return (f"Reference image {i} is the room: a modest 30-seat meeting room on a high floor with floor-to-ceiling windows on the "
                "left, a white wall and a pale projection screen. Use exactly this room — NOT an auditorium, NO balcony, NO tiered seating.")
    if path == FEAR_HALL:
        return (f"Reference image {i} is the APPROVED shot of Reika frightened in the packed assembly hall: copy exactly this face, hair, "
                "makeup, earrings, jacket, the frightened expression (NO smile) and the hall background with seated residents; change ONLY "
                "the camera angle and framing as described.")
    if path in FEAR_FACE.values():
        return (f"Reference image {i} is the APPROVED face of Reika frightened: copy exactly this face, hair, makeup, pearl earrings, "
                "jacket and the frightened expression (NO smile); ignore its background completely.")
    if path == REIKA_FACE:
        return (f"Reference image {i} is the APPROVED face of Reika: reproduce exactly this face, hair, makeup, pearl earrings and cream tweed "
                "jacket; ignore its elevator background.")
    if path in REIKA_BY_EXPR.values():
        return (f"Reference image {i} is the APPROVED face of Reika in this emotional state: copy exactly this face, hair, makeup, jacket "
                "and the frightened/tearful expression; ignore its framing if the description differs.")
    if path == REIKA_HALL:
        return (f"Reference image {i} is the APPROVED shot of Reika in the assembly hall: keep exactly this face, hair, makeup, jacket, "
                "framing and the hall background full of seated residents; ONLY change her facial expression as described.")
    if path == ODA_APPROVED:
        return (f"Reference image {i} is the APPROVED face of Mr. Odagiri: exactly this face with the FULL BUSHY WHITE MOUSTACHE, "
                "deep wrinkles and combed-back white hair; ignore its background.")
    if path == FRAMING_REF:
        return (f"Reference image {i} is a FRAMING reference only: copy its tight chest-up close-up framing, camera distance and shallow "
                "depth of field exactly (head and shoulders filling the frame); ignore its background, hair fringe and the empty room.")
    if "/tower-kf-a/" in path:
        who = next((v for k, v in PEOPLE.items() if FACE_KF.get(k) == name.split("-")[0]), "the character")
        return f"Reference image {i} is the APPROVED face of {who}: reproduce exactly this face, age and hairstyle; ignore its background, framing and pose."
    for k, v in PEOPLE.items():
        if name.startswith(k + "-"):
            return (f"Reference image {i} is the character sheet cell of {v}: copy this exact face, hairstyle, wardrobe and age; "
                    "ignore its background, framing and any sheet layout.")
    if name.startswith("prop-"):
        return f"Reference image {i} is the prop reference: copy the object's exact shape, colour and material; ignore the white background."
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


def build(sc, face_refs):
    refs = list(face_refs) + sc["refs"] + EXTRA_REFS.get(sc["id"], [])
    if sc["id"] in ROOM_FIX:
        refs = [r for r in refs if "loc-hall" not in os.path.basename(r)] + [ROOM_FIX[sc["id"]]]
    if sc["id"] == "S03e":   # 편집: 현재 승인 컷 1장만 참조
        refs = ["assets/portraits/tower-kf-b/S03e-1.png"]
    if sc["id"] in ("S01e", "S03d"):  # 얼굴 셀이 얼굴·전신을 끌어옴(S05c 실증) → 장소 셀만, 옷은 문장으로
        refs = [r for r in refs if "/cells/loc-" in r]
    if sc["id"] == "S05c":  # 얼굴 셀이 얼굴을 그리게 한 뒤 동그라미로 가림(B 2차) → 얼굴 셀 빼면 다른 엄마들(B 3차) → 승인 S14o(세 엄마 착석)
        refs = ["assets/portraits/tower-cast/cells/mamas-s14o.png"] + [r for r in refs if "/cells/loc-" in r or r == ROOM_RINJI]
    if sc["id"] in FEAR_FACE:
        refs = [FEAR_FACE[sc["id"]]] + ([HALL_FRONT] if FEAR_FACE[sc["id"]] == FEAR_HALL else
                                        [HALL_FRONT if r.endswith(("loc-hall-p4.png", "loc-hall-p2.png")) else r for r in sc["refs"]])
    if sc["id"] in FIX_A or (sc["kind"] in ("face", "react", "sil", "d") and sc["size"] != "ecu"):  # 단상·후면 셀은 흰 벽만 찍혀 배경이 스튜디오처럼 나옴(A단계 실증) → 스크린·창이 보이는 회의실 셀
        refs = [HALL_BG if r.endswith(("loc-hall-p4.png", "loc-hall-p2.png")) else r for r in refs]
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    parts.append(sc["keyframe_prompt"])
    parts += notes(refs)
    if FIX_B.get(sc["id"]):
        parts.insert(1, FIX_B[sc["id"]])
    if sc["id"] in ROOM_FIX:
        parts.insert(1, CROWD[ROOM_FIX[sc["id"]]])
    if sc["id"] in FEAR_FACE and FEAR_FACE[sc["id"]] != FEAR_HALL:
        parts.insert(2, BG_FRONT)
    if sc["id"] in FIX_A:
        parts.insert(1, FIX_A[sc["id"]])
        parts.append(TIGHT)
    elif sc["id"] in COMPOSITION:
        parts.append(COMPOSITION[sc["id"]])
    elif sc["kind"] == "d":
        parts.append(TIGHT)
    else:
        parts.append(FULL)
    if sc["kind"] == "d":
        parts.append("Mouth gently closed or barely parted (speech is added later); natural skin texture, both eyes sharp and symmetrical.")
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": " ".join(parts)}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    stage, _, only = arg.partition(":")
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    shots = [s for s in sb["scenes"] if s["keyframe"]]
    if stage == "pilot":
        pick = [s for s in shots if s["id"] in PILOT]
        items = [build(s, []) for s in pick]
    elif stage == "a":
        pick = [s for s in shots if s["kind"] == "d"]
        items = [build(s, []) for s in pick]
    elif stage == "b":
        pick = [s for s in shots if s["kind"] != "d"]
        items = []
        for s in pick:
            face = []
            if s["kind"] in FACE_KINDS:
                for r in s["refs"]:
                    k = os.path.basename(r).split("-")[0]
                    if k in FACE_KF:
                        p = f"{KF_A}/{FACE_KF[k]}-1.png"
                        if k == "reika":
                            ex = next((e for e, cell in (("panic", "reika-expr2"), ("tears", "reika-expr3")) if any(cell in x for x in s["refs"])), None)
                            if ex or s["id"] in ("S14h", "S16g", "S19d"):
                                p = REIKA_BY_EXPR[ex or "panic"]
                        if not os.path.exists(os.path.join(ROOT, p)):
                            raise SystemExit(f"{s['id']}: 기준 얼굴 {p} 없음 — A단계 먼저")
                        face.append(p)
            items.append(build(s, face))
    else:
        raise SystemExit("단계: pilot|a|b")
    if only:
        ids = set(only.split(","))
        items = [x for x in items if x["id"] in ids]
        stage += "-r"
    spec = {"_설명": f"tower PHASE 4 키프레임 {stage}(build_tower_keyframes.py 생성, 직접 수정 금지). {len(items)}장 약 {len(items) * 0.04:.2f}달러.",
            "_style_preset": sb["preset"], "characters": items}
    path = OUT.format(stage)
    json.dump(spec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(items)}장")


if __name__ == "__main__":
    main()
