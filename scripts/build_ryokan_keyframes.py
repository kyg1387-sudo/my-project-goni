#!/usr/bin/env python3
"""『老舗旅館の嫁』 #03 PHASE 4 키프레임 스펙 생성기 (build_chika_keyframes.py 구조, 규격 제7장 1·5·7, 제11장 2·3·18, 제12장 1).

scripts/storyboard/ryokan.json(PHASE 3)을 읽어 generate_portraits.py 스펙을 만든다. 스펙을 손으로 고치지 않는다.
단계:
  pilot    scripts/portraits/ryokan-kf-pilot.json  파일럿 3장(S07e 마이 비웃음 로우앵글 · S07l 와카나 결정타 CU · S05c 타카유키 폰 조명)
  a        scripts/portraits/ryokan-kf-a.json      OMNI 대사 CU 25장 — 참조 = PHASE 2 셀(표정 셀 + 로케이션)
  b        scripts/portraits/ryokan-kf-b.json      나머지 — 얼굴이 보이는 컷은 A에서 승인한 인물별 기준 얼굴을 1번 참조로 추가
  collect  승인된 pilot/a/b 결과를 assets/portraits/ryokan-keyframes/<id>-1.png(스토리보드 경로)로 모은다
표정 리얼리즘(고니감독님 지시 2026-10-19 「시청자 몰입을 줄 수 있게 표정 연출을 최대한 실감나게」):
  얼굴이 보이는 모든 컷에 [ACTION] 선두로 감정별 미세 표정 문장(EXPR_REAL)을 넣는다 — 대사 컷은 톤 연출표(build_tts.T)의 감정 태그,
  무대사 컷은 샷 설명의 감정 단어로 자동 선택. 공통 ACTING 문장(비대칭·근육 긴장·피부 홍조·「포즈가 아닌 생각 중인 얼굴」)을 항상 붙인다.
generate-video.yml portraits_spec=<스펙> → assets/portraits/<스펙>/<id>-1.png
사용법: python3 scripts/build_ryokan_keyframes.py pilot|a|b[:ID,ID]|collect
"""
from prompt_format import compose_keyframe, check_order, check_motion, split_sections  # 제12장 1
import json
import os
import re
import shutil
import sys
from kf_letterbox_fix import fix as kf_fix

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "ryokan.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "ryokan-kf-{}.json")
KF_DIR = "assets/portraits/ryokan-keyframes"
STAGE_DIRS = tuple(f"assets/portraits/ryokan-kf-{s}" for s in ("pilot", "pilot-r", "a", "a-r", "b", "b-r"))
PILOT = ["S07e", "S07l", "S05c"]
KF_RATE = 0.04
sys.path.insert(0, os.path.join(ROOT, "productions", "ryokan-yome-ja"))
from build_tts import T as TONE   # 줄별 감정 태그(톤 연출표) → 표정 리얼리즘 문장 선택

# 인물 식별 특징(PHASE 2 마스터 시트에서 잠근 것, 08_PHASE2_검수.md) — 참조 셀 설명과 함께 글로 한 번 더 못 박는다(제7장 7)
PEOPLE = {
    "wakana": "Wakana (33, slim, soft oval face, clear dark eyes, straight black hair in a low neat chignon with NO bangs, two small beauty marks below the LEFT eye, NO glasses; navy samue work jacket + white bib apron)",
    "wakanab": "Wakana (33, slim, soft oval face, clear dark eyes, straight black hair in a low neat chignon with NO bangs, two small beauty marks below the LEFT eye, NO glasses; plain dark-navy kimono with an ivory obi)",
    "tomiko": "Tomiko (68, thin, lined face, silver hair in a tight bun, thin gold-rimmed glasses, plum-coloured kimono)",
    "mai": "Mai (38, slightly full round face, long loosely waved chestnut-brown hair, arched drawn eyebrows, glossy deep-red lipstick, heavy mascara, NO glasses, bright pink cherry-blossom kimono)",
    "takayuki": "Takayuki (36, soft doughy face, unkempt black hair, faint stubble, NO glasses, wrinkled grey cardigan over a white shirt)",
    "sakurai": "Sakurai (late 50s, elegant, sleek silver-grey chin-length bob, pearl earrings, NO glasses, forest-green kimono)",
    "regular": "the regular guest (late 60s, Japanese man, salt-and-pepper short hair, kind lined face, NO glasses, brown knit vest over a checked shirt)",
    "cameo": "the regular guest (late 60s, Japanese man, salt-and-pepper short hair, kind lined face, NO glasses)",
}
PERSON_KEYS = ("wakanab", "wakana", "tomiko", "mai", "takayuki", "sakurai", "regular", "cameo")
# 인물별 기준 얼굴 = A단계 승인 OMNI 컷(제7장 7, 제11장 2: 표정별). 타카유키·레귤러(카메오)는 대사 컷이 하나/없음.
FACE_KF = {"wakana": "S07l", "wakanab": "S16b", "tomiko": "S07b", "mai": "S07e", "takayuki": "S05c", "sakurai": "S12b"}   # regular(카메오)은 대사 컷이 없어 셀(cameo-front) 참조 유지
FACE_KINDS = ("face", "react", "d", "sil")
ANCHOR_FALLBACK = {"wakana": "S03d", "wakanab": "S16c", "tomiko": "S07i", "mai": "S07f"}
FACE_KF_BY_EXPR = {"wakana-expr-hurt": "S05b", "wakana-expr-resolve": "S07l", "wakana-front": "S03d",
                   "wakanab-expr-faint": "S16d", "wakanab-expr-neutral": "S16b", "wakanab-front": "S16b",
                   "tomiko-expr-smile": "S06b", "tomiko-front": "S07b", "tomiko-office": "S11d",
                   "mai-expr-panic": "S11e", "mai-front": "S07e", "mai-expr-sulk": "S07e", "mai-expr-laugh": "S07e",
                   "sakurai-expr-laugh": "S12b", "sakurai-expr-wink": "S12c", "sakurai-expr-calm": "S12c",
                   "takayuki-expr-bored": "S05c", "takayuki-expr-down": "S05c", "takayuki-expr-panic": "S05c"}
# 시트 검수(08_PHASE2_검수.md): 비웃음·엄격·애원 셀이 미소/안경 누락 → 정면 셀로 치환하고 표정은 글로(제11장 1)
REF_SWAP = {"*": {"tomiko-expr-stern.png": "tomiko-front.png", "tomiko-expr-plead.png": "tomiko-front.png"}}

TIGHT = ("FRAMING FIRST: a tight single-person chest-up close-up — head and shoulders fill the frame, the top of the head near the top edge, "
         "the frame cut at mid-chest; the face occupies about one third of the frame height; hands NOT visible; NOT a medium shot, NOT a full-body shot. "
         "Full-frame 16:9 image, no black bars.")
TEARS_RE = re.compile(r"\btear|teary|weep|sob|wet eye|brimming|welling|glisten|moist", re.I)
TEARS = ("TEARS RULE: tears must look like real human tears — eyes brimming with a thin film of water that pools along the lower lids and catches "
         "a tiny highlight, the eye rims and the tip of the nose slightly reddened, lashes a little damp; at most ONE thin, barely visible wet trail "
         "on one cheek, following the natural curve from the inner corner of the eye; matte natural skin elsewhere. NO thick glossy gel-like streaks, "
         "NO multiple parallel lines, NO shiny drawn-on drops, NO tears on both cheeks at once.")
TEARS_DRY = "The eyes are glistening and wet but NO tear runs down the cheek — the emotion is held back."
INSERT_FIRST = ("INSERT SHOT — NO FACE: this frame contains ONLY the hands, object or body part described below; NO face, NO head, NO eyes, "
                "NO full body anywhere in the frame; the frame is cut at the wrist or forearm; the camera is within one metre of the subject.")
BE_FIRST = ("CAMERA DIRECTLY OVERHEAD, pointing STRAIGHT DOWN at 90 degrees (bird's-eye): the floor fills the entire frame, the top of the head and "
            "shoulders are seen from above, no walls or ceiling visible, no horizon.")
CHOKER_FIRST = ("CHOKER CLOSE-UP: the face fills the ENTIRE frame from just above the eyebrows to just below the lower lip; the top of the head, "
                "chin, neck and shoulders are cut off by the frame edges; 85mm lens, extremely shallow depth of field.")
MOBILE = ("MOBILE-FIRST COMPOSITION: this will be watched on a 6-inch phone screen — the key subject (face, hand or object) is LARGE and centred "
          "in the middle 60 percent of the frame, high local contrast between subject and background, nothing important near the frame edges or "
          "in tiny far-off detail; the lower fifth of the frame stays visually simple (subtitles will sit there).")
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
REAL = ("REAL PHOTOGRAPH ONLY: a frame from a live-action Japanese drama shot on a cinema camera — real human skin with pores and fine lines, "
        "real fabric weave, real wood grain; NOT an illustration, NOT anime, NOT a painting, NOT CGI.")
WALL = ("WALL RULE: every wall is completely bare — NO paper notices, NO posters, NO calendars, NO framed writing; "
        "NO noren curtain and NO hanging cloth unless the location reference shows one, and then it is plain solid indigo with NO circular crest.")

# ---- 표정 리얼리즘(고니감독님 지시 2026-10-19) ----
# 배우의 실제 연기처럼: 감정은 「한 표정」이 아니라 눈·눈썹·입·피부·호흡의 미세 신호 조합. 모델이 흔히 내는 「스톡 포즈」(이 드러난 웃음, 과장된 찡그림)를 막는다.
ACTING = ("ACTING REALISM: this is a real actor caught mid-thought, not a posed portrait — a subtle NATURAL ASYMMETRY between the two sides of the "
          "face, the emotion held mainly in the EYES and the tiny muscles around them (lower eyelids, inner brows, nostrils, the corners of the mouth), "
          "the skin reacting (faint flush or pallor where the emotion demands), a believable breath in the chest; NO exaggerated theatrical grimace, "
          "NO stock smile with teeth, NO blank mannequin stare, NO perfectly symmetrical frozen face.")
EXPR_REAL = {
    "plead": ("Expression — DESPERATE PLEADING: inner brows pulled up and together forming a soft wrinkle between them, eyes wide and wet with the "
              "lower lids tensed, lips parted a little and trembling at one corner, chin dimpled, the whole face leaning slightly toward the listener."),
    "firm": ("Expression — QUIET RESOLVE: brows level and still, eyes steady and fully open looking straight into the lens without blinking, "
             "the mouth closed in a soft calm line, jaw relaxed not clenched, a stillness that reads as strength; NO smile, NO anger."),
    "sad": ("Expression — HELD-BACK SORROW: inner brows lifted, the lower eyelids slightly puffed and tensed, eyes shining wet along the lower rim, "
            "the corners of the mouth pulled minutely down, the lips pressed together as if swallowing something, nostrils faintly flared on a held breath."),
    "hurt": ("Expression — SILENT HURT: eyes lowered or just lifting, brows slightly drawn, the lower lids tight, the mouth closed and the lips pressed "
             "flat with a faint downward tug at one corner, a small swallow visible at the throat; the face of someone absorbing an insult without replying."),
    "sneer": ("Expression — COLD CONTEMPT: the mouth CLOSED with one corner lifted into a thin sneer, the upper lip faintly raised on that side, "
              "eyelids half lowered, chin raised to look down the nose, one brow a touch higher than the other; a bored, superior, cruel face — NOT a smile."),
    "stern": ("Expression — ICY SEVERITY: brows lowered and drawn together, a hard vertical crease between them, eyes narrowed and cold behind the "
              "glasses, the mouth clamped shut with the lips thinned and the jaw set, nostrils pinched; the face of someone passing judgement."),
    "smug": ("Expression — SMUG SATISFACTION: a closed-lip half smile pulled a little more to one side, cheeks lifted so the lower lids crease, "
             "eyes sliding sideways with a glint, chin slightly tucked; pleased with herself, lips together, NO teeth."),
    "laugh": ("Expression — SUPPRESSED LAUGH: cheeks lifted, crow's-feet at the eye corners, the lips pressed together fighting a grin so the "
              "mouth bows and one corner twitches up, eyes bright and narrowed; the laugh is held in, mouth closed."),
    "panic": ("Expression — DAWNING PANIC: eyes wide with the whites showing above the iris, brows raised and pulled together, the lower lids "
              "tensed, lips parted and the lower lip drawn slightly back, skin gone pale, a visible tightness in the neck; fear arriving in real time."),
    "guilt": ("Expression — SHAME: head lowered, eyes down and unable to meet anyone's, brows soft and slightly raised in the middle, the mouth "
              "slack and closed, a faint flush on the cheeks and ears, shoulders rounded inward; the face of a man who knows he is wrong."),
    "bored": ("Expression — DULL INDIFFERENCE: heavy eyelids, eyes fixed on the phone glow below the frame, brows flat, the mouth slightly open "
              "and slack, no muscle engaged anywhere in the face; the blue phone light hollowing the cheeks."),
    "broken": ("Expression — COLLAPSE: the face crumpled — brows pulled up in the middle and wrinkled, eyes squeezed and wet with the rims reddened, "
               "the mouth pulled down and open in a silent sob, the chin trembling, deep lines around the nose; the mask of authority gone."),
    "warm": ("Expression — QUIET WARMTH: a gentle closed-lip smile that reaches the eyes — the lower lids softly raised, fine lines at the "
             "outer corners, brows relaxed, the gaze unfocused and kind; a face at peace, NO wide grin, NO teeth."),
    "moved": ("Expression — DEEPLY MOVED GRATITUDE: eyes closed or nearly closed, brows raised softly in the middle, the lips pressed together "
              "and pulled slightly down at the corners while the cheeks lift, the eye rims and nose tip faintly reddened; joy and tears meeting."),
    "calm": ("Expression — COMPOSED NEUTRAL: a settled, unreadable professional face — eyes level and clear, brows relaxed, the mouth closed "
             "and soft, a hint of fatigue in the lower lids; thinking rather than reacting."),
    "polite": ("Expression — PRACTISED HOSTESS SMILE: a polished closed-lip smile that does NOT reach the eyes — cheeks lifted, lips curved, "
               "but the eyes cool and appraising, brows perfectly still; courtesy as a mask."),
    "tease": ("Expression — MISCHIEVOUS TEASING: one brow arched higher, eyes narrowed with a knowing glint, a lopsided closed-lip smile, "
              "head tilted a few degrees; playful intelligence, lips together."),
    "cool": ("Expression — QUIET, FAINTLY COLD COMPOSURE: a still face with NO smile — the mouth closed in a level line, eyes steady and a little "
             "narrowed, brows relaxed, chin level; calm satisfaction kept entirely inside, read only in the steadiness of the gaze."),
    "shock": ("Expression — SHOCK: eyes suddenly wide and fixed, brows shot up, the mouth slightly open and frozen mid-word, the face gone still "
              "and pale, the hand with the handset tightening; the instant the ground drops away."),
    "liberated": ("Expression — RELEASE: the tension draining from the face — brows lifting and smoothing, the eyes clearing and opening a "
                  "little wider, the lips just beginning to curve at one corner; the first instant of freedom, not yet a full smile."),
}
# 톤 연출표의 ElevenLabs 감정 태그/메모 → EXPR_REAL 키 (앞에서부터 첫 일치)
STRONG_MAP = [("sob", "broken"), ("broken", "broken"), ("crumbl", "broken"), ("panic", "panic"), ("shock", "shock"), ("stammer", "shock"),
              ("plead", "plead"), ("sneer", "sneer"), ("mock", "sneer")]
MEMO_MAP = [("해방", "liberated"), ("통쾌", "cool"), ("통보", "stern"), ("절제", "hurt"), ("농담", "tease"), ("놀림", "tease"), ("결정타", "firm"), ("애원", "plead"), ("비웃음", "sneer"), ("패닉", "panic"), ("붕괴", "broken"), ("오열", "broken"),
            ("귀찮", "bored"), ("죄책", "guilt"), ("감격", "moved"), ("따뜻", "warm"), ("엄격", "stern"), ("득의", "smug"), ("장난", "tease")]
TONE_MAP = [("plead", "plead"), ("tearful", "sad"), ("sob", "broken"), ("crumbl", "broken"), ("broken", "broken"), ("panic", "panic"), ("fear", "panic"),
            ("sneer", "sneer"), ("contempt", "sneer"), ("mock", "sneer"), ("scorn", "sneer"), ("cold", "stern"), ("stern", "stern"), ("harsh", "stern"),
            ("angry", "stern"), ("sharp", "stern"), ("smug", "smug"), ("gloat", "smug"), ("tease", "tease"), ("playful", "tease"), ("laugh", "laugh"),
            ("amused", "laugh"), ("firm", "firm"), ("resolute", "firm"), ("steady", "firm"), ("moved", "moved"), ("grateful", "moved"), ("warm", "warm"),
            ("gentle", "warm"), ("soft", "warm"), ("relieved", "liberated"), ("sad", "sad"), ("hurt", "hurt"), ("uncertain", "hurt"), ("hesitant", "hurt"), ("ominous", "stern"), ("decisive", "stern"), ("formal", "stern"), ("bored", "bored"), ("flat", "bored"),
            ("guilt", "guilt"), ("ashamed", "guilt"), ("polite", "polite"), ("hostess", "polite"), ("calm", "calm"), ("neutral", "calm")]
SUBJECT_MAP = [("sneer", "sneer"), ("scorn", "sneer"), ("contempt", "sneer"), ("smug", "smug"), ("hostess smile", "polite"), ("professional smile", "polite"),
               ("teasing", "tease"), ("mischiev", "tease"), ("holding back a laugh", "laugh"), ("laugh", "laugh"), ("panic", "panic"), ("wide wet eyes", "panic"),
               ("guilty", "guilt"), ("head lowered", "guilt"), ("crumpl", "broken"), ("sobbing", "broken"), ("grateful", "moved"), ("moved", "moved"),
               ("liberated", "liberated"), ("tension gone", "liberated"), ("warm smile", "warm"), ("faint smile", "warm"), ("faintest", "warm"),
               ("hard behind", "stern"), ("brows down", "stern"), ("chin lifted", "stern"), ("eyes hard", "stern"), ("bored", "bored"), ("pleading", "plead"),
               ("hesitant", "sad"), ("head bowed", "hurt"), ("lips pressed", "hurt"), ("trembling", "sad"), ("composed", "calm"), ("unreadable", "calm"),
               ("clear-eyed", "firm"), ("calm", "calm")]


def expr_key(sc):
    """대사 컷은 톤 연출표(감정 태그+메모), 그 외는 샷 설명에서 감정을 고른다."""
    if sc.get("line"):
        n = int(sc["line"][4:])
        tag, memo = (TONE.get(n) or ("", ""))[:2]
        tag = tag.lower()
        for k, v in STRONG_MAP:          # 강한 감정 태그는 메모보다 우선(sobbing > 애원)
            if k in tag:
                return v
        for k, v in MEMO_MAP:
            if k in memo:
                return v
        for word in re.findall(r"[a-z]+", tag):   # 태그의 단어 순서대로(첫 단어가 주 감정)
            for k, v in TONE_MAP:
                if word.startswith(k):
                    return v
    subj = sc["subject"].lower()
    for k, v in SUBJECT_MAP:
        if k in subj:
            return v
    return "calm" if sc["kind"] in ("d", "react", "face") else None


LOC_NOTE = {
    "loc-genkan": "Inn entrance hall: the counter top, the guest book and the shoe shelf are plain; the noren is plain solid indigo with NO crest; no notices.",
    "angle-genkan": "Inn entrance hall: the counter top, the guest book and the shoe shelf are plain; the noren is plain solid indigo with NO crest; no notices.",
    "loc-zashiki": "Tatami banquet room: the hanging scroll in the alcove is a plain blank ink-wash, no calligraphy; lacquer trays and cups plain.",
    "loc-kitchen": "Inn kitchen / back office: whiteboards, labels, the wall calendar and every paper are completely blank; no notices on the walls.",
    "loc-room": "Couple's private room: bare walls, NO noren, NO posters, no phone on the floor; only the futon, the paper lamp and the window.",
    "loc-hgenkan": "Hanaikada lobby: the front desk plate, brochures and the wall behind the desk are blank; no signage lettering anywhere.",
    "loc-hoffice": "Hanaikada office: binders, papers and the desk calendar are blank; the laptop screen is a plain soft glow; bare walls, NO noren.",
    "angle-hoffice": "Hanaikada office: binders, papers and the desk calendar are blank; the laptop screen is a plain soft glow; bare walls, NO noren.",
    "loc-taipei": "Taipei travel-agency office: monitors show a plain glow, every paper and wall is blank; NO noren, no Chinese characters anywhere.",
    "loc-alley": "Night back alley: the gate plate and any lanterns are blank; no shop signs with writing.",
    "prop-file": "The navy binder is plain: a grey ruled sheet with a red band, no readable text.",
    "prop-handset": "The old cream telephone has no brand name or numerals readable.",
    "prop-teaset": "The tea set is plain glazed ceramic with no pattern or writing.",
}

# 파일럿·검수 결과 보정 문장(컷 ID → 문장). 검수 후 여기에 추가한다(손으로 스펙 수정 금지).
FIX = {
    "S07e": ("LIGHTING AND FRAMING NEXT. The banquet room is dim at the edges: the only strong light is a hard cold overhead source pressing straight "
             "down on Mai — bright forehead and cheekbones, dark eye sockets, a hard shadow under the chin; NO soft daylight, NO flat lighting. "
             "Camera BELOW her eye line looking up at her; tight chest-up close-up, NO hands, NO table in the frame. Her eyes look DOWN at the lens "
             "with the eyelids half lowered and the chin raised; the sneer is unmistakable."),
    "S05c": ("NO smartphone and NO hands anywhere in the frame — the phone is BELOW the bottom edge, out of shot; the frame is cut at mid-chest. "
             "The ONLY light on his face is the cold blue-white glow of the smartphone held below the frame, lighting him from beneath the chin; "
             "the paper lamp is a faint warm dot far behind; the rest of the room is near black."),
}
# A단계 1차 검수(2026-10-19): S09a 벽 공지 종이, S11e 입 벌림·치아·굵은 눈물 2줄, S16c 통쾌 → 따뜻한 미소, S18d 눈 감음·젤 눈물
FIX.update({
    "S09a": "The wall behind her is completely BARE — NO whiteboard, NO pinned papers, NO notices, NO calendar; only plain wall and the dark window.",
    "S11e": ("Mouth CLOSED — the lips pressed together and trembling, NO open mouth, NO teeth; the panic is in the wide eyes and raised brows only. "
             "Eyes wet along the lower rim but NO tear trail on the cheeks."),
    "S16c": "NO smile at all — the mouth is a closed level line; the face is still and faintly cold.",
    "S09a": "The scene is the small inn back office at NIGHT (desk, laptop, dark window) — NOT the tatami banquet room. The wall is completely bare.",
    "S18d": ("She wears NO glasses (they have been taken off). The scene is the small dim back office at night — NOT the tatami room. Her eyes are OPEN — red-rimmed, swimming with water, looking just below the lens; NOT closed. The face is crumpling: brows pulled up "
             "and wrinkled in the middle, mouth closed and pulled down, chin trembling. One thin wet trail at most on one cheek, no shiny drops."),
})
HEAD = {"S16c": "NO SMILE: the mouth is closed in a straight level line, corners NOT lifted.",
        "S18d": "EYES OPEN (wet, red-rimmed), NO glasses on the face.",
        "S09a": "SETTING: a small cramped inn back office at night, NOT a tatami room."}
NOFACE = set()
NO_LOC_REF = set()


def person_key(path):
    b = os.path.basename(path).rsplit(".", 1)[0]
    for k in PERSON_KEYS:
        if b == k or b.startswith(k + "-"):
            return k
    return None


def describe(path, i):
    name = os.path.basename(path).rsplit(".", 1)[0]
    if path.startswith(STAGE_DIRS) or path.startswith(KF_DIR):
        k = next((k for k, v in FACE_KF.items() if name.startswith(v)), "")
        who = PEOPLE.get(k, "this character")
        return (f"Reference image {i} is the APPROVED keyframe face of {who}: reproduce exactly this face, hair, eyewear and wardrobe; "
                "ignore its background and framing unless the description below says otherwise.")
    k = person_key(path)
    if k:
        who = PEOPLE[k]
        hair = "faint stubble" if k == "takayuki" else "clean face with NO facial hair"
        if k == "cameo":
            return (f"Reference image {i} is a real photograph of the actor playing {who}: copy exactly this face, age, hairline and skin; "
                    "wardrobe is described below; ignore the photo's background.")
        if "expr" in name:
            return (f"Reference image {i} is the expression cell of {who}: copy exactly this face, hair, eyewear, {hair} and wardrobe, and use this "
                    "emotional expression only as a starting point (about 60 percent intensity) — the detailed expression text below overrides it; "
                    "ignore its plain background and any borders or labels.")
        if "full" in name:
            return (f"Reference image {i} is the full-body wardrobe cell of {who}: copy exactly the body type, wardrobe and footwear; ignore its plain background.")
        if "kimono-close" in name:
            return f"Reference image {i} is the wardrobe detail of {who}: copy exactly the kimono fabric, colour and obi."
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
    """drop_expr: 기준 얼굴이 있으면 작은 표정 셀을 빼고(얼굴형 드리프트 원인, #02 A단계 실증) 표정은 글로만 지시"""
    refs = list(face_refs) + [r for r in sc["refs"] if r not in face_refs]
    if drop_expr and face_refs:
        refs = [r for r in refs if "-expr" not in os.path.basename(r)]
        kf_ids = {os.path.basename(f).split("-")[0] for f in face_refs}
        kf_people = {k for k, v in FACE_KF.items() if v in kf_ids} | {person_key(c) for c, v in FACE_KF_BY_EXPR.items() if v in kf_ids}
        kf_people.discard(None)
        refs = [r for r in refs if not (person_key(r) in kf_people and "-full" not in os.path.basename(r) and not r.startswith(KF_DIR))]   # 기준 얼굴이 있는 인물의 정면 셀은 중복 → 제외(참조 9장 실증)
    if sc["id"] in NO_LOC_REF:
        refs = [r for r in refs if not os.path.basename(r).startswith(("loc-", "angle-"))]
    noface = sc["kind"] == "ins" or sc["id"] in NOFACE or (sc["kind"] == "face" and sc["size"] == "ecu" and not any(person_key(r) for r in sc["refs"]))
    if noface:   # 인서트는 인물 셀을 참조하면 얼굴을 그린다(#02 B단계 실증) → 장소·소품 셀만, 손·의상은 글로
        refs = [r for r in refs if not person_key(r) and not r.startswith(STAGE_DIRS) and not r.startswith(KF_DIR)]
    swap = {**REF_SWAP["*"], **REF_SWAP.get(sc["id"], {})}
    refs = [os.path.join(os.path.dirname(r), swap.get(os.path.basename(r), os.path.basename(r))) for r in refs]
    seen, uniq = set(), []
    for r in refs:
        if r not in seen:
            seen.add(r); uniq.append(r)
    refs = uniq
    # 제12장 1 5단 공식: 스타일 → [CAMERA] → [CHARACTER] → [ACTION] → [SETTING] → [NEGATIVE]
    style = ("Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions. "
             + REAL)
    camera, character, action, setting = [], [], [], []
    camera.append(MOBILE)
    if sc["size"] == "ch":
        camera.append(CHOKER_FIRST)
    if sc["angle"] == "BE":
        camera.append(BE_FIRST)
    kp = sc["keyframe_prompt"]
    if noface:
        kp = re.sub(r"\[CHARACTER\][^\[]*", "[CHARACTER] No person's face is visible. ", kp)
        camera.append(INSERT_FIRST)
    if sc["kind"] == "d":
        camera.append(TIGHT + " Mouth CLOSED (lips together, no teeth visible); facing the camera, looking into the lens.")
    character += [describe(p, i + 1) for i, p in enumerate(refs)]
    if drop_expr and face_refs:
        character.append("IDENTITY FIRST: the person is EXACTLY the one in reference image 1 — same face shape, jaw, cheekbones, nose, eyes, eyebrows, "
                         "skin tone, age, hairstyle and eyewear; only the expression, lighting and framing described below change.")
    ek = None if noface or sc["kind"] in ("sil", "empty", "estill", "gfx", "card") else expr_key(sc)
    if sc["id"] in HEAD:
        style += " " + HEAD[sc["id"]]
    if ek:   # 파일럿 1차(2026-10-19): [ACTION] 안에 두면 참조 셀의 중립 얼굴이 이김 → 스타일 바로 뒤, 카메라 앞에 선두 배치 + 강도 명시
        strong = ek in ("sneer", "stern", "smug", "panic", "broken", "shock", "plead", "laugh")
        style += (" EXPRESSION FIRST — the face must read clearly at a glance on a phone screen, at about "
                  + ("75" if strong else "60") + " percent intensity, overriding the neutral expression of any reference image: "
                  + EXPR_REAL[ek] + " " + ACTING)
    if sc["id"] in FIX:
        action.append(FIX[sc["id"]])
    secs = split_sections(kp)
    if "CAMERA" in secs or "ACTION" in secs:
        if secs.get("_pre"):
            style += " " + secs["_pre"]
        camera.append(secs.get("CAMERA", "")); character.append(secs.get("CHARACTER", ""))
        action.append(secs.get("ACTION", "")); setting.append(secs.get("SETTING", ""))
        extra_neg = secs.get("NEGATIVE", "")
    else:
        action.append(kp); extra_neg = ""
    if TEARS_RE.search(sc["subject"]):
        action.append(TEARS_DRY if re.search(r"but dry|held back|no tear|dry eyes|not running|no tears running", sc["subject"], re.I) else TEARS)
    if sc["kind"] == "sil":
        action.append("The figure is a true backlit silhouette: no facial features readable, only outline, hair shape and body mass.")
    if drop_expr and face_refs:
        loc_i = next((i + 1 for i, r in enumerate(refs) if os.path.basename(r).startswith(("loc-", "angle-"))), None)
        if loc_i:   # #02 실증(S15j)·#03 a-r(S09a·S18d): 기준 얼굴 컷의 배경이 다른 장소 컷으로 새어 들어옴 → 선두에도 명시
            style += (f" LOCATION FIRST: the scene takes place in the location of reference image {loc_i}; the room, furniture and background "
                      f"of reference image 1 must NOT appear — only its face is used.")
            setting.append(f"SETTING: the place is reference image {loc_i} ONLY; the background, furniture, lamps and lighting of reference image 1 "
                           "must NOT appear.")
    setting.append(WALL)
    setting += notes(refs)
    if sc["kind"] == "d":
        setting.append(TIGHT)
        setting.append("Soft fill light keeps the mouth and jaw readable (lip-sync cut). Mouth gently closed or barely parted (speech is added later); "
                       "natural skin texture, both eyes sharp and symmetrical in focus.")
    else:
        setting.append(FULL)
    prompt = compose_keyframe(" ".join(camera), " ".join(character), " ".join(action), " ".join(setting),
                              ("Absolutely no text, letters, numbers, logos or symbols anywhere in the image. " + extra_neg).strip(), style=style)
    for w in check_order(prompt) + check_motion(prompt, sc["id"]):
        print("  [경고 제12장 1] " + w)
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": prompt, "_expr": ek or ""}


OFFICE_ANCHOR = {"S18c": "S11d", "S18d": "S11d", "S09a": "S07e"}   # 같은 장소의 승인 컷을 기준으로(배경 유출 완화)


def face_refs_for(sc):
    out = []
    if sc["id"] in OFFICE_ANCHOR:
        p = f"{KF_DIR}/{OFFICE_ANCHOR[sc['id']]}-1.png"
        if os.path.exists(os.path.join(ROOT, p)):
            return [p]
    if sc["kind"] not in FACE_KINDS:
        return out
    for r in sc["refs"]:
        k = person_key(r)
        if k and k in FACE_KF:
            cell = os.path.basename(r).rsplit(".", 1)[0]
            kf_id = FACE_KF_BY_EXPR.get(cell, FACE_KF[k])
            if kf_id == sc["id"]:
                kf_id = FACE_KF[k]
            p = f"{KF_DIR}/{kf_id}-1.png"
            if sc["id"] == kf_id:
                if k not in ANCHOR_FALLBACK:
                    continue
                p = f"{KF_DIR}/{ANCHOR_FALLBACK[k]}-1.png"
            if not os.path.exists(os.path.join(ROOT, p)):
                raise SystemExit(f"{sc['id']}: 기준 얼굴 {p} 없음 — A단계 먼저")
            if p not in out:
                out.append(p)
    return out


def done(sc):
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
            if kf_fix(dst):
                print(f"  {s['id']}: 레터박스 크롭")
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
    exprs = {x["id"]: x.pop("_expr") for x in items}
    spec = {"_설명": f"ryokan PHASE 4 키프레임 {stage}(build_ryokan_keyframes.py 생성, 직접 수정 금지). {len(items)}장 약 {len(items) * KF_RATE:.2f}달러.",
            "_표정": {k: v for k, v in exprs.items() if v}, "_style_preset": sb["preset"], "characters": items}
    path = OUT.format(stage)
    json.dump(spec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(items)}장 약 {len(items) * KF_RATE:.2f}달러 | 표정: " + ", ".join(f"{k}={v}" for k, v in exprs.items() if v))


if __name__ == "__main__":
    main()
