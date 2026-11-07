#!/usr/bin/env python3
"""『ブラックカード』第2話(blackcard2) PHASE 3 샷 리스트 Lock 생성기 — build_blackcard_phase3.py(1화)를 옮긴 것.

2화에서 달라진 것(2026-11-07):
  · Lock = productions/blackcard-ja-ep2/lock.json(결말 B안, 10:54.8). 음성 = assets/auditions/blackcard2-lock/(1.05배속).
  · 후크 S13: L201 레코더(S17h 재사용) → L202 액자 7개(S21f 재사용) → L203 1화 클립 몽타주(ep1clip, 새 생성 금지) → L204 카드 → L205 非通知.
  · 창업자 초상은 마지막 한 컷(S24j, 대사 없음·얼굴 비노출)만 — 2화 완결형(고니감독님 결정). 지하 복도 초상 컷은 두지 않는다.
  · 녹음(三好)·자동응답(柴田)·전화(声·美咲·案内音)·회상 대사는 전부 vo(입 비노출). 말하는 화자의 뒷모습·옆모습은 pstill(제11장 9).
  · 손이 소품에 닿는 컷은 접촉 직후 정지(제20장 14), 손 인서트는 HANDS LOCKED(제19장 25), 차 안은 우핸들·운전대 1(제20장 16).
  · 정점 정적(bgm_silence) = 09_정점효과음설계.md T1·T3·T4·T5·T6·T8·T10, 카메라 = 18_카메라줌설계.md(돌리줌 S21g 1회·더치 S18h 1회).
사용법: python3 scripts/build_blackcard2_phase3.py
"""
import collections, json, os, re, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "blackcard-ja-ep2")
SKIT = "blackcard2"
TTS_DIR = "blackcard2-lock"
FPS = 24; HARD = 1 / FPS; OMNI_MAX = 7.9; LEAD = 0.3; MIN_SHOT = 1.2; STILL_MAX = 6.5; I2V_MAX = 10.0

LOCK = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
ROWS = {x["tag"]: x for x in LOCK["lines"]}
AD1, AD2 = (a["at"] for a in LOCK["ads"])


def B(tag, off=0.0):
    return round(ROWS[tag]["start"] + off, 3)


def E(tag, off=0.0):
    return round(ROWS[tag]["end"] + off, 3)


C = "assets/portraits/blackcard-cast/cells/"
C2 = "assets/portraits/blackcard2-cast/cells/"
KEN_ID = ("Takahashi Kenji, a lean Japanese man aged 43, gaunt tired face with hollow cheeks, short black hair with a little grey at the temples, "
          "short dark stubble, a small healing graze above the LEFT eyebrow, no glasses, no earrings")
WHO = {
    "KENS": (KEN_ID + ", hair dry and neatly combed back", C + "kenji-suit-front.png"),
    "KENY": ("young Kenji fifteen years ago, a slim Japanese man aged 28, short neat black hair, seen only from behind", None),
    "MIS": ("Misaki, a Japanese woman aged 40, chin-length straight black bob with bangs, exactly ONE small mole on the LEFT cheek, no glasses, "
            "no earrings, almost no makeup, tired eyes", C + "misaki-front-noglasses.png"),
    "SHIY": ("young Shibata fifteen years ago, a Japanese man aged 30, slicked-back black hair, seen only from behind", None),
    "NAG": ("Nagase, a Japanese man aged 58, neatly side-parted SILVER-GREY hair, thin narrow face, thin gold metal-frame rectangular glasses, "
            "clean-shaven, no earrings", C2 + "nagase-front.png"),
    "SAG": ("Sagisuma, a sturdy Japanese man in his late sixties, thinning grey hair combed straight back, deep forehead lines, heavy-lidded tired eyes, "
            "short grey stubble, NO glasses, both earlobes bare", C2 + "sagisuma-front.png"),
    "KEIBI": ("the night security guard, a Japanese man about 55, greying temples under a plain navy cap, calm lined face, no glasses, clean-shaven",
              C2 + "keibi-front.png"),
    "MIYH": ("Miyoshi, a Japanese office worker aged 39, seen only as hands and grey suit sleeves", None),
    "CHAUF": ("a chauffeur in a plain black suit, black chauffeur cap and white gloves, seen only from behind or as hands, no face", None),
    "INTV": ("three interviewers seen only from behind at a long table and one young applicant seen only from behind, no faces", None),
}


def base(key):
    return "KEN" if key.startswith("KEN") else key


WARD = {
    "suit": ("a perfectly tailored plain black slim suit, crisp white shirt open at the collar with NO necktie, a plain brushed-steel luxury "
             "wristwatch with a completely blank dial on the BACK of the LEFT wrist, no badge, no pin"),
    "young": "a cheap new navy recruit suit, white shirt, plain navy tie",
    "mis2": "a plain grey knit long coat over a white blouse, dark trousers, a plain black handbag on the shoulder, no brooch, no necklace",
    "nag": "a charcoal grey three-piece suit with vest, white shirt, a plain burgundy tie, a plain silver tie bar without engraving, bare lapel",
    "sag": "a worn dark brown tweed jacket over a plain charcoal knit sweater and an open-collar white shirt, no tie",
    "guard": "a plain navy security uniform and cap with no insignia, no badge, no name tag",
    "chauf": "a plain black suit, black chauffeur cap, white cotton gloves",
    "miy": "a plain light grey suit sleeve",
}
EXPR = {  # PHASE 2 Kill Gate 합격 셀(03_마스터에셋.md). 永瀬 exp2·exp3 금지
    ("KENS", "cold"): C + "kenji-suit-exp1.png", ("KENS", "calm"): C + "kenji-suit-exp2.png", ("KENS", "hard"): C + "kenji-suit-exp3.png",
    ("KENS", "back"): C + "kenji-suit-full-back.png",
    ("MIS", "cold"): C + "misaki-exp1.png", ("MIS", "worry"): C + "misaki-exp2.png", ("MIS", "plead"): C + "misaki-exp3.png",
    ("MIS", "back"): C + "misaki-full-back.png",
    ("NAG", "cold"): C2 + "nagase-exp1.png", ("NAG", "back"): C2 + "nagase-full-back.png",
    ("SAG", "flat"): C2 + "sagisuma-exp1.png", ("SAG", "guilt"): C2 + "sagisuma-exp2.png", ("SAG", "weary"): C2 + "sagisuma-exp3.png",
    ("SAG", "back"): C2 + "sagisuma-full-back.png",
    ("KEIBI", "sorry"): C2 + "keibi-exp2.png", ("KEIBI", "hesit"): C2 + "keibi-exp3.png", ("KEIBI", "back"): C2 + "keibi-full-back.png",
    ("SHIY", "back"): C + "shibata-full-back.png", ("KENY", "back"): C + "kenji-suit-full-back.png",
}
EXPR_TXT = {
    "cold": "icy calm, lips closed, eyes level and unreadable", "calm": "quiet calm, eyes soft, a long slow breath",
    "hard": "hard cold eyes, a thin tightening of the mouth, NOT smiling", "tense": "tense, eyes wide, lips slightly parted, breath held, NOT smiling",
    "worry": "frightened, brows drawn together, lips parted, NOT smiling", "plead": "pleading, eyes wet and red-rimmed, inner brows raised, NOT smiling",
    "smugcold": "a thin composed polite smile that does not reach the eyes", "alarm": "eyes wavering in alarm behind the glasses, lips pressed, NOT smiling",
    "fall": "collapsed, eyes down, shoulders sunk, NOT smiling", "flat": "flat, tired, matter-of-fact, no smile",
    "guilt": "grave guilt, jaw set, eyes steady, no smile", "weary": "weary resignation, eyes half-lowered",
    "sorry": "apologetic, head slightly bowed, eyes lowered", "hesit": "hesitant, brows slightly raised, about to speak",
    "soft": "the corners of the eyes softening for the first time, eyes wet but NOT running, NOT smiling broadly", "back": "seen from behind",
}
LOC = {
    "BACK1": C + "loc-backdoor-1.png", "BACK3": C + "loc-backdoor-3.png",
    "MEET1": C + "loc-meeting-1.png", "MEET2": C + "loc-meeting-2.png", "MEET3": C + "loc-meeting-3.png",
    "CAR1": C + "loc-car-1.png", "CAR2": C + "loc-car-2.png", "CAR4": C + "loc-car-4.png", "EMBLEM": C + "emblem.png", "P_CARD": C + "props-card-1.png",
    "ARCH1": C2 + "loc-archive-r1c1.png", "ARCH2": C2 + "loc-archive-r1c2.png", "ARCH3": C2 + "loc-archive-r2c1.png",
    "APT_ROOM": C2 + "loc-miyoshi-apt-room.png", "APT_WIN": C2 + "loc-miyoshi-apt-window.png", "APT_DESK": C2 + "loc-miyoshi-apt-desk.png",
    "APT_EXT": C2 + "loc-miyoshi-apt-exterior.png",
    "BAR1": C2 + "loc-shimbashi-bar-r1c1.png", "BAR2": C2 + "loc-shimbashi-bar-r1c2.png", "BAR_EXT": C2 + "loc-shimbashi-bar-r2c2.png",
    "TOP1": C2 + "loc-topfloor-r1c1.png", "TOP2": C2 + "loc-topfloor-r1c2.png", "TOP3": C2 + "loc-topfloor-r2c1.png",
    "ELV1": C2 + "loc-elevator-r1c1.png", "ELV2": C2 + "loc-elevator-r1c2.png", "ELV3": C2 + "loc-elevator-r2c1.png", "ELV4": C2 + "loc-elevator-r2c2.png",
    "FB_INT": C2 + "loc-flashback-r1c1.png", "FB_LOBBY": C2 + "loc-flashback-r1c2.png", "FB_CANTEEN": C2 + "loc-flashback-r2c2.png",
    "P_HALF": C2 + "props2-halfcard.png", "P_REC": C2 + "props2-recorder.png", "P_ENV": C2 + "props2-envelope.png", "P_PEN": C2 + "props2-pen.png",
    "P_KEY": C2 + "props2-keycard.png", "P_CUP": C2 + "props2-coffee.png",
}
LOC_TXT = {
    "TOWER": ("a tall dark glass office tower in Roppongi at night after rain, wet plaza, a bronze ring-and-tower emblem above the main entrance, "
              "one red aviation light at the top, no logos, no readable text"),
    "B2_CORR": ("a dim concrete basement corridor of an office tower at night: on the wall one large formal portrait in a dark wooden frame whose glass "
                "reflects a white flashlight glare so strongly that the face is completely hidden behind the reflection, no plaque text, no readable text"),
    "CORRIDOR": "a long modern office corridor with frosted glass partitions and cold fluorescent light, grey carpet, no signage, no readable text",
}
PRESET = ("Photorealistic live-action Japanese noir drama, contemporary Tokyo (Reiwa era), Arri Alexa cinematic color grade, Kodak 35mm film grain, "
          "24fps, 16:9, low-key high-contrast lighting, restrained Japanese film mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, "
            "signage lettering, documents with writing, screens with text, printed labels, brand logos, watermarks, stamps with characters, "
            "symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, blood, gore, anime, 3d render, illustration, "
            "thick glossy gel tears, cartoon sweat drops, multiple tear streams on both cheeks, earrings on men, LED light strips, lens flare text")
PLAIN = ("All papers, cards, ledgers, forms, envelopes, phone screens, calendars, recorders, clocks and panels are completely blank "
         "(screens show only a soft plain glow); no letters, numbers or symbols anywhere in the frame.")
TEARS = ("Realistic tears as in a live-action film: reddened eye rims, glossy wet eyes catching the light, a small clear tear bead on the lower lashes, "
         "at most one thin translucent tear track on one cheek, matte natural skin; no glossy gel streams, no cartoon droplets.")
SWEAT = ("Realistic sweat as in a live-action film: a few tiny natural beads of perspiration on the forehead and temples, a faint natural sheen, "
         "one thin bead line near the temple; no large cartoon drops, no face-wide shine.")
RAINSKIN = ""
NOSMILE = "NOT smiling at any moment: brows knotted, the corners of the mouth pulled down. "
GLASSES = {"KENS": "Kenji wears no glasses.", "MIS": "Misaki wears no glasses.", "NAG": "Nagase wears thin gold metal-frame rectangular glasses.",
           "SAG": "Sagisuma wears NO glasses.", "KEIBI": "The guard wears no glasses."}
HANDS = {"KENS": "lean hands, no ring, a plain brushed-steel wristwatch with a blank dial on the back of the LEFT wrist",
         "MIS": "a woman's slim hands, no ring", "NAG": "a thin older man's hands, a plain gold wedding band",
         "SAG": "an old man's thick weathered hands, no ring", "KEIBI": "a security guard's hands", "CHAUF": "white-gloved hands",
         "MIYH": "a man's hands in a light grey suit sleeve"}
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, the face fills at least one third of the frame height",
    "ots": ("50mm lens, f/2.0, over-the-shoulder three-quarter framing, CAMERA CLOSE: 1.2 m behind the listener's shoulder, the listener's blurred shoulder "
            "and back of the head at the near foreground edge taking at most 25 percent of the frame width, the speaker's face at least one third of the frame height"),
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds, the person's face at least one quarter of the frame height",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective",
}
LIGHT = {
    "car": "night in a luxury car rear seat, warm amber and magenta neon reflections sliding over black leather and skin, a soft reading light",
    "car_cold": "night in a luxury car rear seat, the neon reflections cold blue-white, a soft reading light, uneasy",
    "street_n": "night after rain, cold blue ambient light, wet surfaces reflecting red and blue, a dark tower with one red light",
    "booth": "1 a.m. at a rear service entrance after rain, the warm yellow light of a guard booth window, cold blue night around, wet asphalt",
    "archive": ("night, the room lights OFF: a narrow cold white flashlight beam is the only key light, a very dim green emergency glow near the floor, "
                "deep shadows, dust floating in the beam"),
    "apt": "early morning 7:30, cool overcast daylight 5600K through a single window, soft and bleak, an empty room",
    "meet": "late morning, cold flat overhead fluorescent light 5600K with a faint green tint, grey window daylight, harsh shadows, a tense corporate mood",
    "backday": "1 p.m. overcast daylight at a rear service entrance, flat grey sky light, damp concrete, cold and quiet",
    "bar": "night 8 p.m., warm tungsten 3200K pendant bulbs, amber glow, smoke-softened air, deep brown shadows",
    "elev": "night, dim warm brass light in the elevator, a dark corridor outside",
    "top": ("night 11 p.m., the room dark except a low warm desk lamp and the city glow; a red aviation light only as a faint reflection on the window "
            "glass, no red lamp fixture indoors"),
    "memory": "memory look: warm faded amber 3200K, slightly overexposed highlights, soft halation, desaturated",
    "macro": "a tight pool of light on the object, everything else falling into black",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "bird's-eye view straight down", "SIDE": "eye-level from the side or behind"}
SPK_KEY = {"健二": "KEN", "美咲": "MIS", "永瀬": "NAG", "鷺沼": "SAG", "警備員": "KEIBI", "柴田": "SHIY"}


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, act="", vo=False, pin=None):
    """kind: d(OmniHuman) / face(사람 i2v) / empty(무인 i2v) / estill(무인·합성 면 정지) / pstill(말하는 화자 뒷모습 정지 + 편집 카메라) /
    ins(손·소품 — motion 있으면 i2v, 없으면 정지) / reuse:<id> / ep1clip(1화 완성본 재사용) / card."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc, subject=subject,
                line=line, fx=fx, motion=motion, expr=expr, act=act, vo=vo, pin=pin)


Ks, Mi, Na, Sa, Kb, Ch = "KENS:suit", "MIS:mis2", "NAG:nag", "SAG:sag", "KEIBI:guard", "CHAUF:chauf"
OB = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, keeps looking "
      "toward the other person at the same three-quarter angle, hands keep doing what they do in the first frame; no exaggerated motion, the same person throughout.")
HOLD = " Head stays at the same angle, never turns toward the camera; only body, hands and breath move. Mouth stays closed, lips still — this person is NOT speaking."
SEATED = " SEATED/FURNITURE LOCKED: seated on the chair or stool pulled in, thighs under the edge, forearms on the surface; the chair never passes through the body."
ONEHAND = " HANDS LOCKED: exactly ONE hand in the frame holding exactly ONE object, five clean fingers, seen from the side at hand height, the forearm continuing out of frame."
CARGEO = (" CAR GEOMETRY LOCKED: Japanese right-hand-drive sedan — exactly ONE steering wheel, in front of the RIGHT front seat; the chauffeur sits in the "
          "RIGHT front seat, only his cap and gloves ever seen; Kenji sits in the rear seat SEATED NORMALLY facing FORWARD.")
EYES = " Framing: only the eyes and brows fill the frame, the mouth is OUT of frame."
DRY = " NO water indoors, ceiling and lamps dry."
EMPTYS = " EMPTY: nobody in the room, no people anywhere."

SHOTS = [
    # ── S13 후크(0:00~0:29.5): 레코더 → 액자 7개 → 1화 몽타주 → 카드 → 非通知. 0~3.5초 BGM 없음(심장 박동 가속 + 드론)
    S("S13a", "S13", "reuse:S17h", "ecu", "macro", "HA", [], None, "Reuse of S17h: the IC recorder macro with only the small play LED glowing in the dark room.", line="L201", vo=True),
    S("S13b", "S13", "reuse:S21f", "ws", "top", "EL", [], None, "Reuse of S21f: slow pan along the seven gold frames, rack focus to the empty seventh frame plate (No.7 高橋健二 composited).", line="L202"),
    S("S13c", "S13", "ep1clip", "ews", "street_n", "EL", [], None, "Episode 1 final-cut montage, 1.2 s each: the black card in the rain / the payment terminal approval / Shibata collapsing in his chair / Misaki kneeling. Do not generate anew.", line="L203"),
    S("S13d", "S13", "ins", "ecu", "car", "EL", [Ks], "CAR1", "Side insert in the rear seat: Kenji's ONE hand holding the matte black card between thumb (front) and index finger (back) at its lower edge, at chest height, the emblem facing the camera; neon sliding over it. The card is otherwise blank." + ONEHAND, line="L204", fx="push", motion="Neon reflections slide slowly across the surfaces as the car glides; the hand and the object stay perfectly still in the same grip; nothing changes shape; nobody appears."),
    S("S13e", "S13", "ins", "ms", "car", "HA", [Ks], "CAR1", "High insert: a smartphone lying screen-up on the black leather seat, the screen a plain soft glow (「非通知」 composited), the corner of Kenji's knee in the frame; no hands touching it.", line="L205", fx="push"),

    # ── S14 경비원·지하 서고(0:29.5~1:51): 질문 카드 → 타이틀 → 차 → 경비원 → 명부 No.7 → 평가표 A→C → 회상
    S("S14a", "S14", "card", "cu", "car", "EL", [], None, "Question card over the blurred last frame of S13e (no black): 『消えた六人は、どこへ行ったのか。』"),
    S("S14b", "S14", "card", "ws", "car", "EL", [], None, "Title card 「ブラックカード　第二話」 over the blurred frame (no black)."),
    S("S14c", "S14", "ins", "ecu", "car", "EL", [Ks], "CAR1", "Side insert in the rear seat: Kenji's ONE hand holding an old printed interview photograph by its lower edge between thumb and index finger at chest height; the photograph surface is plain (content composited)." + ONEHAND + CARGEO, line="L206", vo=True, fx="push", motion="Neon reflections slide slowly across the surfaces as the car glides; the hand and the object stay perfectly still in the same grip; nothing changes shape; nobody appears."),
    S("S14d", "S14", "estill", "ews", "street_n", "LA", [], None, "Low wide through the wet car window: the dark glass tower approaching at night, the bronze ring-and-tower emblem above the main entrance catching the street light; EMPTY plaza.", line="L208", fx="push"),
    S("S14e", "S14", "face", "cu", "booth", "EL", [Ks], "BACK3", "Close-up of Kenji standing outside the lit guard booth window at night, three-quarter, eyes on the guard inside (screen LEFT), face hard and still.", line="L209", vo=True, expr="hard",
      motion="He breathes slowly, eyes on the guard screen LEFT; a slow blink." + HOLD),
    S("S14f", "S14", "face", "ms", "booth", "HA", [Kb], "BACK3", "High medium inside the booth window: the security guard lowering his eyes, cap brim shading his face, hands on the counter.", line="L210", vo=True, expr="sorry",
      motion="He lowers his eyes and gives a small bow of the head; his hands stay on the counter." + HOLD),
    S("S14g", "S14", "d", "ots", "booth", "EL", [Kb, Ks], "BACK3", "Over Kenji's blurred shoulder (near RIGHT foreground): the guard at the booth door at three-quarter angle, holding out a ring of keys in ONE hand, apologetic, speaking to Kenji.", line="L211", expr="sorry",
      act="He speaks quietly and formally, ashamed, head slightly bowed, holding the key ring out with one hand toward Kenji screen RIGHT; answering Kenji's request." + OB),
    S("S14h", "S14", "ins", "ecu", "booth", "EL", [Ks], "BACK3", "Side insert at hand height: Kenji's ONE hand closed around the key ring, the keys hanging below the fist, just taken; the guard's hand already withdrawn out of frame." + ONEHAND, line="L212", vo=True, fx="push"),
    S("S14i", "S14", "d", "cu", "booth", "EL", [Kb], "BACK3", "Chest-up close-up of the guard at three-quarter angle in the booth doorway, hesitating, eyes toward Kenji who is walking away (screen RIGHT), one hand half raised.", line="L213", expr="hesit",
      act="He calls out hesitantly, lowering his voice as if someone might hear, one hand half raised then stopping; speaking to Kenji's back screen RIGHT." + OB),
    S("S14j", "S14", "face", "ms", "booth", "SIDE", [Ks], "BACK1", "Medium from behind: Kenji stopped mid-step on the wet asphalt by the rear door, the key ring in his hand, his back to the camera, not turning.", line="L214", vo=True, expr="back",
      motion="He stands still mid-step; his shoulders rise with one breath; he does not turn." + HOLD),
    S("S14k", "S14", "estill", "ws", "archive", "EL", [], "ARCH1", "Wide of the second-basement archive aisle: grey steel shelves of plain grey file boxes, a white flashlight pool on the concrete floor, dust floating in the beam; EMPTY.", line="L215", fx="push"),
    S("S14l", "S14", "empty", "ecu", "archive", "HA", [], "ARCH1", "High insert: one plain grey file box pulled half out of the shelf in the flashlight beam, its blank label plate (「採用ファイル」 composited); no hands.", pin=B("L215", 2.6),  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S14m", "S14", "empty", "ecu", "archive", "OH", [], "ARCH2", "Overhead: a large open ledger on the grey metal table under the flashlight, blank ruled pages (seven black diamond marks and six brush-ink strike-throughs composited).", line="L216",  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S14n", "S14", "ins", "ecu", "archive", "EL", [Ks], "ARCH2", "Side insert at table height: Kenji's ONE index finger resting on a brush-ink stroke on the ledger page, the black suit sleeve continuing out of frame; page otherwise blank." + ONEHAND, line="L217", fx="push"),
    S("S14o", "S14", "empty", "ecu", "archive", "HA", [], "ARCH2", "Macro of one ledger row in the flashlight: a faded diamond mark beside a blank name field (「高橋健二」 and a crisp black 「No.7」 composited); no hands.", line="L219",  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S14p", "S14", "empty", "ecu", "macro", "EL", [], "ARCH2", "Extreme macro at a low raking angle across the paper: a fresh glossy black ink stroke catching the flashlight, the paper grain sharp, everything else black.", line="L220",  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S14q", "S14", "face", "cu", "archive", "LA", [Ks], "ARCH1", "Close-up of Kenji lit from below by the flashlight, eyes down on the ledger (screen LEFT), jaw tight, the shelves dark behind.", line="L221", expr="hard",
      motion="He breathes slowly; his eyes stay on the ledger screen LEFT; a muscle in his jaw tightens; he never looks at the camera." + HOLD),
    S("S14r", "S14", "ins", "ecu", "archive", "EL", [Ks], "ARCH2", "Side insert: Kenji's ONE hand holding a single plain evaluation sheet up at chest height by its lower edge in the flashlight beam (「総合 A」 composited)." + ONEHAND, line="L222", fx="push"),
    S("S14s", "S14", "empty", "ecu", "macro", "HA", [], "ARCH2", "Macro of the evaluation sheet: a printed grade box (「A」 struck through with a double line and 「C」 written beside it composited); no hands.", line="L223",  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S14t", "S14", "empty", "ecu", "macro", "OH", [], "EMBLEM", "Overhead macro: a red ink seal impression on the sheet (「指示あり」 composited) and below it the small ring-and-tower emblem stamp exactly like the card's; no hands.", line="L224", fx="punch", motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S14u", "S14", "pstill", "ws", "memory", "SIDE", ["SHIY:young", "KENY:young"], "FB_LOBBY", "Memory, from behind: two young men in new navy recruit suits among rows of folding chairs in a bright company lobby fifteen years ago; the one on the left claps the other's shoulder; both seen only from behind, no faces.", line="L225", vo=True, fx="push"),
    S("S14v", "S14", "ins", "ecu", "archive", "EL", [Ks], "ARCH2", "Side insert: Kenji's ONE hand gripping the single evaluation sheet hard, the paper creasing slightly, knuckles pale, in the flashlight." + ONEHAND, line="L226", fx="push"),

    # ── S15 퇴직 기록·三好(1:51~2:34)
    S("S15a", "S15", "empty", "ws", "archive", "OH", [], "ARCH2", "Overhead: six thin plain personnel files fanned out on the metal table under the flashlight, blank covers (「希望退職」 composited); no hands.", line="L227",  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S15b", "S15", "empty", "ecu", "macro", "HA", [], "ARCH2", "Macro of an approval box with a red personal seal impression (「永瀬」 composited), the paper edge of the next file beneath; no hands.", line="L228", fx="stampseq", motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S15c", "S15", "empty", "ecu", "archive", "EL", [], "ARCH2", "Low raking macro of the last page of a file: a blank date field and a small handwritten note slip (「退職日」 and 「所在不明」 composited); no hands.", line="L229",  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S15d", "S15", "ins", "ecu", "archive", "HA", [Ks], "ARCH2", "High side insert: Kenji's ONE index finger resting on one of six dates written down the edge of a sheet (dates composited)." + ONEHAND, line="L230", fx="push"),
    S("S15e", "S15", "empty", "ecu", "archive", "OH", [], "ARCH2", "Overhead: a photocopied official notice on the table in the flashlight (「住民票 職権消除」 composited); no hands.", line="L232",  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S15f", "S15", "ins", "ms", "archive", "SIDE", [Ks], "ARCH1", "Side medium insert from the hip down: Kenji's ONE hand holding a small black flashlight at waist height between the shelves, the beam on the files." + ONEHAND, line="L233",
      motion="The hand slowly lowers the flashlight; the beam slides down off the table onto the concrete floor; the brightness of the beam stays constant."),
    S("S15g", "S15", "empty", "ecu", "archive", "HA", [], "ARCH2", "High macro: the sixth file opened, a small ID photograph clipped inside (a smiling man's photo composited); no hands.", line="L234",  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S15h", "S15", "ins", "ecu", "archive", "EL", [Ks], "ARCH2", "Side insert: Kenji's ONE thumb resting at the edge of the small clipped ID photograph, not covering it." + ONEHAND, line="L235", fx="push"),
    S("S15i", "S15", "ins", "ecu", "archive", "EL", [Ks], "ARCH1", "Side insert: Kenji's ONE hand holding a smartphone at chest height, screen toward the camera as a plain soft glow (contact 「三好」 calling composited), the thumb resting beside the screen." + ONEHAND, line="L237", fx="push"),
    S("S15j", "S15", "face", "cu", "archive", "SIDE", [Ks], "ARCH1", "Close-up of Kenji's profile at three-quarter from the side, the smartphone PRESSED AGAINST HIS EAR, flashlight glow from below, eyes down.", line="L238", expr="tense",
      motion="He listens, still; a slow blink; his jaw tightens once." + HOLD),

    # ── S16 声 통화(2:34~3:27) — BGM 0, 공조음만
    S("S16a", "S16", "ins", "ecu", "archive", "EL", [Ks], "ARCH1", "Side insert: the smartphone in Kenji's ONE hand at chest height, the screen a plain soft glow (「非通知」 composited)." + ONEHAND, line="L239", vo=True, fx="push"),
    S("S16b", "S16", "pstill", "ms", "archive", "LA", [Ks], "ARCH3", "Low angle from behind Kenji's shoulder: the back of his head tilted up toward a small dome camera in the ceiling corner, its tiny red LED glowing; his face and mouth are not visible.", line="L240", fx="handheld", act="Body acting only (face hidden): the head tilts up toward the camera in the ceiling, shoulders rigid, a low quiet question — restrained, cold."),
    S("S16c", "S16", "estill", "ecu", "archive", "LA", [], "ARCH3", "Macro: the dome security camera lens with its tiny red LED, the concrete ceiling dark around it; EMPTY.", line="L241", fx="push"),
    S("S16d", "S16", "d", "cu", "archive", "EL", [Ks], "ARCH1", "Chest-up close-up of Kenji at three-quarter angle between the shelves, the smartphone PRESSED AGAINST HIS RIGHT EAR, the other hand holding a thin plain file at chest height, eyes on the ceiling camera off-screen (screen LEFT).", line="L242", expr="hard",
      act="He speaks low and firm into the phone, an order not a request; eyes on the ceiling camera screen LEFT; the hand with the file stays still." + OB),
    S("S16e", "S16", "face", "ws", "archive", "SIDE", [Ks], "ARCH1", "Wide from the end of the aisle: Kenji standing between the shelves seen from behind, the phone at his ear, the flashlight pool at his feet.", line="L243", vo=True, expr="back",
      motion="He stands listening; his shoulders rise with a breath; he does not turn." + HOLD),
    S("S16f", "S16", "estill", "ws", "archive", "LA", [], "ARCH3", "Low wide of the dark archive ceiling corner, the dome camera small in the frame, its red LED the only colour; EMPTY.", line="L244", fx="push"),
    S("S16g", "S16", "ins", "ecu", "macro", "EL", [Ks], "P_CARD", "Side insert: Kenji's ONE hand holding the matte black card with its plain back toward the camera, lower edge pinched between thumb and index finger, in the flashlight." + ONEHAND, line="L245", fx="push"),
    S("S16h", "S16", "empty", "ecu", "archive", "HA", [], "ARCH2", "High macro of the ledger: six brush-ink strike-throughs in a column (composited), the flashlight edge on them; no hands.", pin=B("L245", 3.0),  motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S16i", "S16", "face", "ecu", "archive", "EL", [Ks], None, "Extreme close-up of Kenji's eyes at three-quarter, lit from below, staring at the card (screen LEFT)." + EYES, line="L246", vo=True, expr="tense",
      motion="His eyes narrow slightly; a slow blink; he never looks at the camera."),
    S("S16j", "S16", "empty", "ecu", "archive", "OH", [], "ARCH2", "Overhead macro: the same six ink strike-throughs, focus drifting softly off them into darkness; no hands.", line="L247", fx="focusout", motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S16k", "S16", "empty", "ecu", "archive", "HA", [], "ARCH2", "Macro: the small clipped ID photograph in the opened file, the flashlight sliding away so the photo sinks into shadow (photo composited); no hands.", line="L248", fx="dimdown", motion="Dust drifts slowly through the flashlight beam; the beam edge trembles very slightly; the paper and the table do not move at all; nobody appears; the light level stays constant."),
    S("S16l", "S16", "face", "cu", "archive", "SIDE", [Ks], "ARCH1", "Close-up of Kenji's profile with the phone at his ear, breath held, frozen, the flashlight glow from below.", line="L249", vo=True, expr="tense",
      motion="He holds his breath; nothing moves but one slow blink; then a small exhale." + HOLD),
    S("S16m", "S16", "pstill", "ms", "archive", "SIDE", [Ks], "ARCH1", "Medium from behind his shoulder: Kenji with the phone at his ear, his face turned away into the dark; face and mouth not visible.", line="L250", fx="handheld", act="Body acting only (face hidden): the shoulders stiffen, one slow breath out, the free hand tightens — quiet, low, cold."),
    S("S16n", "S16", "estill", "ecu", "archive", "LA", [], "ARCH3", "Macro: the ceiling dome camera, its red LED now dark (unlit); EMPTY.", line="L251", fx="push"),
    S("S16o", "S16", "face", "ews", "archive", "HA", [Ks], "ARCH1", "High wide: Kenji a small dark silhouette between the tall shelves, only the flashlight pool at his feet lit, everything else black.", line="L252", expr="back",
      motion="He stands still; the flashlight pool trembles very slightly in his hand; the light level stays constant." + HOLD),

    # ── S17 三好의 방(3:27~5:06) — 녹음 재생은 BGM 0, 녹음 뒤 전철
    S("S16p", "S16", "estill", "ecu", "archive", "HA", [], "ARCH1", "High macro: the white flashlight pool on the bare concrete floor, dust drifting in the beam, the edge of a black shoe at the rim; nothing else.", pin=B("L252", 3.4), fx="push"),
    S("S17a", "S17", "ins", "ecu", "apt", "EL", [Ch], "APT_EXT", "Side insert by the rusty apartment mailboxes: ONE white-gloved hand holding out a single plain door key toward the camera side, a torn-off name-slot mark on the mailbox behind; no face." + ONEHAND, line="L253", vo=True, fx="push"),
    S("S17b", "S17", "face", "ms", "apt", "SIDE", [Ch], "APT_EXT", "Medium from behind: the chauffeur's back of the neck and cap brim at the foot of the steel stairs, standing still, not answering.", line="L254", vo=True, expr="back",
      motion="He stands perfectly still; only a slow breath moves his shoulders; he does not turn." + HOLD),
    S("S17c", "S17", "estill", "ws", "apt", "EL", [], "APT_ROOM", "Wide from the open doorway: the empty six-tatami room, bare tatami with pale rectangular marks where furniture stood, nothing on the floor, a window to the elevated railway; EMPTY.", line="L255", fx="push"),
    S("S17d", "S17", "ins", "ecu", "apt", "EL", [Ks], "APT_WIN", "Side insert at the window: Kenji's ONE index finger resting on the clean window sill, the fingertip lifted a little, perfectly clean, no dust." + ONEHAND, line="L256", fx="push"),
    S("S17e", "S17", "estill", "ms", "apt", "EL", [], "APT_DESK", "Medium of the wall above the small desk: a plain wall calendar with a blank grid (month and dates composited); EMPTY.", line="L257", fx="push"),
    S("S17f", "S17", "estill", "ecu", "apt", "EL", [], "APT_DESK", "Macro of the calendar grid: seven hand-drawn red circles on dates, the last one filled in black (composited); no hands.", line="L258", fx="push"),
    S("S17g", "S17", "estill", "ecu", "apt", "HA", [], "APT_DESK", "High macro of the low desk: a matte black card cut cleanly in half with scissors, the two halves side by side, and a small plain black IC voice recorder beside them; EMPTY, no hands.", line="L259", fx="push"),
    S("S17g2", "S17", "estill", "ecu", "macro", "EL", [], "P_REC", "Macro: the small plain black IC voice recorder on the low desk, its play button and tiny unlit LED, morning light; no hands.", pin=B("L259", 3.4), fx="push"),
    S("S17h", "S17", "ins", "ecu", "macro", "EL", [Ks], "P_REC", "Side insert: Kenji's ONE index finger resting on the play button of the small black IC recorder on the desk, the tiny LED lit; no text." + ONEHAND, line="L260", vo=True, fx="push"),
    S("S17i", "S17", "estill", "ecu", "macro", "EL", [], "P_HALF", "Macro of the cut edge of the half card, clean straight scissor cut, the emblem half visible; no hands.", line="L261", vo=True, fx="push"),
    S("S17j", "S17", "estill", "ecu", "apt", "EL", [], "APT_DESK", "Macro along the calendar's seven red circles (composited), soft morning light; no hands.", line="L262", vo=True, fx="pan"),
    S("S17j2", "S17", "face", "ms", "apt", "SIDE", [Ks], "APT_ROOM", "Medium from behind: Kenji kneeling on the bare tatami in front of the low desk, head bowed toward the recorder; face not visible.", pin=B("L262", 3.3), expr="back",
      motion="He kneels still; his shoulders rise with one slow breath; he does not turn." + HOLD),
    S("S17k", "S17", "face", "cu", "apt", "HA", [Ks], "APT_ROOM", "High close-up of Kenji kneeling on the tatami at three-quarter, looking down at the recorder on the low desk (screen LEFT), eyes wet but not running.", line="L263", vo=True, expr="calm",
      motion="He listens without moving; a slow blink; his throat moves once as he swallows; eyes stay on the recorder screen LEFT." + HOLD),
    S("S17l", "S17", "estill", "ecu", "macro", "EL", [], "P_REC", "Macro: the recorder's small dark counter window (digits composited), the LED lit; no hands.", pin=B("L263", 3.8), fx="push"),
    S("S17m", "S17", "empty", "ws", "apt", "EL", [], "APT_WIN", "Through the window: the concrete elevated railway outside, grey morning sky; a commuter train enters from the left; EMPTY room in front.", line="L264", vo=True,
      motion="A plain silver commuter train passes from left to right along the elevated track at an even speed and leaves the frame; the room stays still; no people inside the room."),
    S("S17n", "S17", "face", "cu", "apt", "EL", [Ks], "APT_ROOM", "Close-up of Kenji at eye level, three-quarter, eyes on the recorder (screen LEFT), wet with tears welling on the lower lids but NOT running.", pin=B("L264", 3.4), expr="soft",
      motion="NOT smiling at any moment. His eyes stay wet; a slow trembling breath; he does not look at the camera." + HOLD),
    S("S17o", "S17", "estill", "ecu", "macro", "EL", [], "P_REC", "Macro: the recorder's LED now unlit, the counter window dark; no hands.", line="L265", vo=True, fx="push"),
    S("S17p", "S17", "ins", "ecu", "memory", "HA", ["MIYH:miy"], "FB_CANTEEN", "Memory, high insert at a staff cafeteria table: ONE man's hand in a light grey sleeve placing one piece of karaage from his plate onto the other plastic tray; no face." + ONEHAND, line="L266",
      motion="The hand sets one piece of karaage onto the other tray and withdraws slowly out of frame."),
    S("S17q", "S17", "face", "cu", "apt", "EL", [Ks], "APT_ROOM", "Close-up of Kenji kneeling, eyes on the recorder (screen LEFT), wet but not running, very still.", line="L267", expr="soft",
      motion="NOT smiling. A slow blink; one tear stays on the lower lid; a long breath." + HOLD),
    S("S17r", "S17", "face", "ws", "apt", "SIDE", [Ks], "APT_ROOM", "Wide from behind: Kenji standing at the window, a dark backlit silhouette against the grey morning light and the elevated track.", line="L268", expr="back",
      motion="He stands still at the window; his shoulders rise with one breath; he does not turn." + HOLD),
    S("S17s", "S17", "face", "ms", "apt", "LA", [Ks], "APT_WIN", "Low medium profile at the window, backlit, Kenji's face in soft shadow looking out at the track (screen RIGHT).", line="L269", expr="hard",
      motion="He looks out; a slow blink; his jaw tightens." + HOLD),
    S("S17t", "S17", "ins", "ecu", "apt", "EL", [Ks], "APT_ROOM", "Side insert at chest height: Kenji's ONE hand having just slipped the small black recorder into the inner pocket of his black jacket, the fingers still at the pocket edge." + ONEHAND, line="L270", fx="push"),
    S("S17u", "S17", "face", "ws", "apt", "HA", [Ks], "APT_EXT", "High wide: Kenji seen from behind on the steep outdoor steel staircase of the old apartment, one step down, hand on the rail.", line="L271", expr="back",
      motion="He takes one slow step down and stops, hand sliding on the rail; he does not turn." + HOLD),
    S("S17v", "S17", "estill", "ws", "street_n", "EL", [], "CAR2", "Medium wide of the black luxury sedan by the kerb in grey morning light, the rear door closed, a shadowed figure inside, no driver face visible; nobody outside.", line="L272", fx="push"),

    # ── S18 12층 회의실·永瀬(5:06~6:15)
    S("S18a", "S18", "d", "ots", "meet", "EL", [Na, Ks], "MEET1", "Over Kenji's blurred shoulder (near LEFT foreground): Nagase entering the glass meeting room at three-quarter angle, a polite cautious half-bow, one hand on the back of a chair.", line="L273", expr="smugcold",
      act="He speaks with careful politeness, a beat of hesitation before さん; a thin smile that does not reach the eyes; addressing Kenji screen LEFT." + OB),
    S("S18b", "S18", "d", "ots", "meet", "EL", [Ks, Na], "MEET3", "Reverse over Nagase's blurred shoulder (near RIGHT foreground): Kenji seated at the white table at three-quarter angle, one hand flat beside a fan of plain approval forms.", line="L274", expr="cold",
      act="Kenji speaks flatly and precisely, not raising his voice, eyes on Nagase screen RIGHT; one finger touches the fan of forms." + SEATED + OB),
    S("S18c", "S18", "estill", "ecu", "meet", "OH", [], "MEET3", "Overhead: seven plain approval forms fanned on the white table, each with a red seal box (seals composited); no hands.", pin=E("L274", -0.9), fx="push"),
    S("S18d", "S18", "d", "cu", "meet", "LA", [Na], "MEET2", "Low chest-up close-up of Nagase at three-quarter angle, adjusting his gold-frame glasses with ONE hand, composed, eyes on Kenji (screen LEFT).", line="L275", expr="smugcold",
      act="He answers smoothly, almost bored, pushing his glasses up with one finger; a confident tilt of the head; to Kenji screen LEFT." + OB),
    S("S18e", "S18", "face", "cu", "meet", "EL", [Na], "MEET2", "Close-up of Nagase listening, eyes wavering behind the glasses toward Kenji (screen LEFT), lips pressed.", line="L276", vo=True, expr="alarm",
      motion="His eyes flick once and steady; he swallows; his fingers tighten on the chair back." + HOLD),
    S("S18f", "S18", "face", "cu", "meet", "EL", [Ks], "MEET1", "Close-up of Kenji seated at three-quarter, motionless, eyes level on Nagase (screen RIGHT).", line="L277", vo=True, expr="cold",
      motion="He does not move; one slow blink." + SEATED + HOLD),
    S("S18g", "S18", "d", "cu", "meet", "LA", [Na], "MEET2", "Low chest-up close-up: Nagase leaning forward with ONE hand pressed flat on the white table, counter-attacking, eyes on Kenji (screen LEFT).", line="L278", expr="smugcold", fx="dutch5",
      act="He leans in with a forced contemptuous smile, a quiet bluster of a threat, one palm flat on the table; to Kenji screen LEFT." + OB),
    S("S18h", "S18", "d", "ots", "meet", "EL", [Ks, Na], "MEET3", "Over Nagase's blurred shoulder: Kenji at three-quarter angle, seated, unmoved, voice low.", line="L279", expr="hard",
      act="Kenji answers without raising his voice, cold and steady, eyes on Nagase screen RIGHT; hands still on the table." + SEATED + OB),
    S("S18i", "S18", "face", "cu", "meet", "EL", [Na], "MEET2", "Close-up of Nagase, the thin smile gone, a hard swallow, eyes on Kenji (screen LEFT).", pin=E("L279", -1.0), expr="alarm",
      motion="The smile fades; he swallows; his eyes stay on Kenji." + HOLD),
    S("S18j", "S18", "d", "cu", "meet", "EL", [Ks], "MEET1", "Chest-up close-up of Kenji at three-quarter angle, his index finger resting on the seventh approval form, eyes on Nagase (screen RIGHT).", line="L280", expr="cold",
      act="He taps the seventh form once with one finger at 七枚目, then says the rest quietly, almost gently, eyes on Nagase screen RIGHT." + SEATED + OB),
    S("S18k", "S18", "face", "ecu", "meet", "EL", [Na], "MEET2", "Extreme close-up of Nagase's right temple and the gold frame arm of his glasses, a few tiny natural beads of sweat at the hairline; eye at the frame edge, mouth out of frame.", line="L281", vo=True, expr="alarm",
      motion="One thin bead of sweat slowly runs down from the temple; a tiny tremor of the jaw muscle."),
    S("S18l", "S18", "d", "ots", "meet", "HA", [Ks, Na], "MEET3", "Over Nagase's blurred shoulder, slightly high: Kenji seated, both hands still on the table, eyes on Nagase.", line="L282", expr="hard",
      act="Kenji states it plainly, like a fact, no anger; eyes on Nagase screen RIGHT; hands do not move." + SEATED + OB),
    S("S18m", "S18", "ins", "ecu", "meet", "EL", [Ks], "MEET3", "Side insert at table height: Kenji's ONE hand resting flat on a single blank white sheet that has just slid across the table to Nagase's side." + ONEHAND, line="L283", vo=True, fx="push"),
    S("S18n", "S18", "d", "ots", "meet", "EL", [Ks, Na], "MEET1", "Over Nagase's blurred shoulder, closer: Kenji leaning in a little, almost whispering, one finger on the blank sheet.", line="L284", expr="cold",
      act="An almost whisper, low and slow, exactly the old words thrown back; one finger taps the sheet twice at ここ; eyes on Nagase." + SEATED + OB),
    S("S18o", "S18", "ins", "ecu", "macro", "HA", [Na], "MEET3", "High insert: Nagase's ONE hand holding a pen, the nib just lifted from the white sheet after writing two shaky characters (「鷺沼」 composited in handwriting)." + ONEHAND, line="L285", vo=True, fx="push"),
    S("S18p", "S18", "face", "ms", "meet", "HA", [Na], "MEET2", "High medium: Nagase collapsed back into the chair, glasses slightly askew, eyes down at the table.", line="L286", vo=True, expr="fall",
      motion="He sinks back into the chair; his chest rises with a shaky breath; his hands lie limp on the armrests." + SEATED + HOLD),
    S("S18q", "S18", "pstill", "ms", "meet", "SIDE", [Na], "MEET1", "From behind Nagase's chair: the back of his silver-grey head and shoulders slumped in the chair, Kenji a blurred standing figure beyond; Nagase's face and mouth not visible.", line="L286b", fx="handheld", act="Body acting only (face hidden): the shoulders sag and tremble slightly, the head drops forward, a shaky breath — broken, sorry, confessing."),
    S("S18r", "S18", "estill", "ecu", "macro", "OH", [], "MEET3", "Overhead macro: a red seal impression on an approval form (composited), the edge of a plain cream envelope beside it; no hands.", line="L287", fx="punch"),
    S("S18s", "S18", "face", "ws", "meet", "SIDE", [Ks], None, "Wide of a long office corridor: Kenji walking away from the camera, small in the frame, seen from behind.", line="L289", expr="back",
      motion="He walks slowly away along the corridor at an even pace; nobody else appears; the camera does not move." + HOLD),
    S("S18t", "S18", "ins", "ecu", "meet", "EL", [Ks], None, "Side insert: Kenji's ONE hand holding a smartphone at chest height, the screen a plain soft glow (「不在着信 12件 美咲」 composited)." + ONEHAND, pin=B("L289", 3.2), fx="push"),

    # ── S19 뒷문·美咲(6:15~7:07)
    S("S19a", "S19", "d", "ots", "backday", "EL", [Mi, Ks], "BACK1", "Over Kenji's blurred shoulder (near RIGHT foreground): Misaki standing by the rear service door at three-quarter angle in overcast daylight, ONE hand gripping her handbag strap, no makeup, pleading.", line="L290", expr="worry",
      act="NOT smiling at any moment. She speaks fast and low, frightened, glancing once to the side; to Kenji screen RIGHT." + OB),
    S("S19b", "S19", "pstill", "ms", "backday", "SIDE", [Ks], "BACK1", "Side medium from slightly behind: Kenji walking past without stopping, his face turned away; mouth not visible.", line="L291", fx="handheld", act="Body acting only (face hidden): he keeps walking at an even pace, shoulders level, not turning — cold, flat, restrained."),
    S("S19c", "S19", "d", "ots", "backday", "HA", [Mi, Ks], "BACK1", "Over Kenji's blurred shoulder, slightly high: Misaki's ONE hand holding his black sleeve, her face at three-quarter looking up at him, desperate.", line="L292", expr="plead",
      act="NOT smiling at any moment. She blurts it out, holding his sleeve with one hand and not letting go; voice breaking but held back; to Kenji screen RIGHT." + OB),
    S("S19d", "S19", "ins", "ecu", "backday", "EL", [Mi], "P_ENV", "Side insert at chest height: Misaki's ONE hand holding up a crumpled cream envelope with a red emblem wax seal, just taken out of her handbag." + ONEHAND, line="L293", vo=True, fx="push"),
    S("S19e", "S19", "face", "cu", "backday", "EL", [Ks], "BACK1", "Close-up of Kenji listening, three-quarter, eyes on the envelope in her hand (screen LEFT), face unreadable.", pin=E("L293", -1.2), expr="cold",
      motion="He stays still; a slow blink; eyes on the envelope." + HOLD),
    S("S19f", "S19", "ins", "ecu", "backday", "EL", [Mi], "P_ENV", "Side insert: Misaki's ONE hand holding the opened cream envelope, the broken red wax seal with the ring-and-tower emblem, one folded sheet showing at the opening." + ONEHAND, line="L294", vo=True, fx="push"),
    S("S19g", "S19", "estill", "ecu", "macro", "EL", [], "P_ENV", "Macro: a single unfolded sheet with one short printed line (「任務終了」 composited); no hands.", line="L295", vo=True, fx="push"),
    S("S19h", "S19", "ins", "ecu", "backday", "EL", [Mi], "BACK1", "Side insert: Misaki's ONE hand holding out a smartphone at chest height, the screen a plain soft glow (「留守番電話 柴田 23:41」 composited)." + ONEHAND, line="L295b", vo=True, fx="push"),
    S("S19i", "S19", "face", "ecu", "backday", "EL", [Ks], None, "Extreme close-up of Kenji's eyes at three-quarter, fixed on the phone (screen LEFT)." + EYES, pin=B("L295b", 3.4), expr="tense",
      motion="His eyes narrow slightly; one slow blink."),
    S("S19j", "S19", "d", "ots", "backday", "HA", [Mi, Ks], "BACK1", "Over Kenji's blurred shoulder, slightly high: Misaki at three-quarter, lips trembling, eyes wet but not running, holding herself together.", line="L296", expr="plead",
      act="NOT smiling at any moment. She holds back the tears, voice trembling but controlled, no sobbing; the last question asked straight at Kenji screen RIGHT." + OB),
    S("S19k", "S19", "ins", "ecu", "backday", "EL", [Ks], "P_ENV", "Side insert: Kenji's ONE hand holding the crumpled cream envelope at chest height, just taken." + ONEHAND, line="L298", fx="push"),
    S("S19l", "S19", "estill", "ews", "backday", "LA", [], None, "Extreme low wide: the office tower rising into the grey afternoon sky from the rear service entrance; EMPTY.", line="L299", fx="pullback"),
    S("S19m", "S19", "card", "ews", "backday", "LA", [], None, "Preview card over the blurred frame of S19l (no black): 『この後――十五年前、俺を\"落とした\"男の告白』", pin=E("L299", 0.8)),

    # ── S20 新橋 바·鷺沼(7:07~8:20)
    S("S20a", "S20", "empty", "ecu", "bar", "EL", [], "BAR2", "Macro on the worn bar counter: an opened cream envelope with a broken red wax seal beside a whisky glass whose ice trembles faintly; EMPTY.", fx="push", motion="The ice in the glass trembles faintly as a train passes overhead; the envelope does not move; nobody appears; the light stays constant."),
    S("S20b", "S20", "d", "cu", "bar", "EL", [Sa], "BAR1", "Chest-up close-up of Sagisuma seated at the counter at three-quarter angle, eyes on his glass, not turning, flat and tired.", line="L300", expr="flat",
      act="He says it without looking up, flat and tired, as if he had been waiting a long time; eyes on the glass; a slow breath." + SEATED + OB),
    S("S20c", "S20", "ins", "ecu", "bar", "EL", [Sa], "BAR2", "Side insert: Sagisuma's ONE thick fingertip resting on the opened envelope on the counter, pushed a little toward the next stool, the sheet inside showing (「任務終了」 composited)." + ONEHAND, line="L301", vo=True, fx="push"),
    S("S20d", "S20", "face", "ms", "bar", "EL", [Ks], "BAR1", "Medium: Kenji seated on the stool next to him at the counter, three-quarter, eyes on Sagisuma (screen LEFT).", line="L302", vo=True, expr="cold",
      motion="He settles on the stool and stays still; a slow blink; eyes on Sagisuma." + SEATED + HOLD),
    S("S20e", "S20", "d", "ots", "bar", "EL", [Ks, Sa], "BAR1", "Over Sagisuma's blurred shoulder: Kenji at three-quarter angle at the counter, eyes level, voice low.", line="L303", expr="hard",
      act="Kenji asks it quietly and directly, a question that is almost an accusation; eyes on Sagisuma screen RIGHT." + SEATED + OB),
    S("S20f", "S20", "ins", "ecu", "bar", "EL", [Sa], "BAR2", "Side insert: Sagisuma's ONE hand lifting the whisky glass a few centimetres off the counter." + ONEHAND, line="L304", vo=True,
      motion="The hand lifts the glass slowly a few centimetres and the ice tilts; it does not leave the frame."),
    S("S20g", "S20", "pstill", "ms", "bar", "SIDE", [Ks], "BAR1", "From behind Kenji's shoulder at the counter: the back of his head turned toward Sagisuma; Kenji's mouth not visible.", line="L305", fx="push", act="Body acting only (face hidden): the head turns a little toward Sagisuma, shoulders still — low, quiet, cold."),
    S("S20h", "S20", "d", "ots", "bar", "EL", [Sa, Ks], "BAR1", "Over Kenji's blurred shoulder: Sagisuma at three-quarter angle, the glass in his hand, admitting it plainly.", line="L306", expr="guilt",
      act="He says it plainly, without excuse, then the second sentence lower; eyes go to Kenji screen LEFT at 私じゃない." + SEATED + OB),
    S("S20i", "S20", "face", "ws", "memory", "SIDE", ["INTV"], "FB_INT", "Memory: an interview room fifteen years ago seen from behind the interviewers: three backs at the long table and one young applicant seated beyond, seen only from behind; no faces.", line="L307", vo=True,
      motion="The interviewers sit still; one turns a page; the applicant sits upright; nobody turns to the camera."),
    S("S20j", "S20", "d", "cu", "bar", "EL", [Sa], "BAR1", "Chest-up close-up of Sagisuma at three-quarter, matter-of-fact, eyes half on his glass.", line="L308", expr="flat",
      act="Flat and matter-of-fact, almost reciting; eyes half on the glass; a small shrug at だけをな." + SEATED + OB),
    S("S20k", "S20", "reuse:S14m", "ecu", "archive", "OH", [], None, "Reuse of S14m: the ledger with the black ink strike-throughs.", line="L309", vo=True),
    S("S20l", "S20", "face", "ecu", "bar", "EL", [Ks], None, "Extreme close-up of Kenji's eyes at three-quarter in the warm bar light, fixed on Sagisuma (screen LEFT)." + EYES, line="L310", vo=True, expr="hard",
      motion="His eyes harden; one slow blink."),
    S("S20m", "S20", "d", "ots", "bar", "EL", [Sa, Ks], "BAR1", "Over Kenji's blurred shoulder: Sagisuma turning to look straight at Kenji for the first time, grave, at three-quarter (NOT into the lens).", line="L311", expr="guilt",
      act="Confessing: for the first time he turns and looks Kenji in the eye; slow, heavy and hoarse, sorry; the last words almost a whisper; to Kenji screen LEFT, never into the lens." + SEATED + OB),
    S("S20n", "S20", "d", "cu", "bar", "EL", [Ks], "BAR1", "Chest-up close-up of Kenji at three-quarter at the counter, his ONE hand around a whisky glass, eyes on Sagisuma (screen LEFT).", line="L312", expr="hard",
      act="He asks low and slow, the ice clicking once as his hand tightens on the glass; eyes on Sagisuma." + SEATED + OB),
    S("S20o", "S20", "ins", "ecu", "bar", "EL", [Sa], "BAR2", "Side insert: Sagisuma's ONE hand resting beside the whisky glass just set down on the worn counter." + ONEHAND, line="L313", vo=True, fx="push"),
    S("S20p", "S20", "pstill", "cu", "bar", "SIDE", [Ks], "BAR1", "Close from behind Kenji's shoulder: the side of his head toward Sagisuma, jaw set; mouth not visible.", line="L314", fx="push", act="Body acting only (face hidden): the jaw sets, the shoulders go still, a held breath — low, quiet, cold."),
    S("S20q", "S20", "d", "cu", "bar", "EL", [Sa], "BAR1", "Chest-up close-up of Sagisuma at three-quarter angle, sliding a plain matte black key card along the counter toward Kenji with ONE hand.", line="L315", expr="weary",
      act="Weary and final, sliding the key card with one hand at 最上階へ行け; eyes on Kenji screen LEFT; the last clause slower." + SEATED + OB),
    S("S20r", "S20", "ins", "ecu", "bar", "EL", [Ks], "P_KEY", "Side insert: Kenji's ONE hand holding the plain matte black key card lifted between thumb (front) and index finger (back) at its lower edge above the counter." + ONEHAND, line="L316", fx="push"),

    # ── S21 최상층(8:20~8:53) — BGM 0
    S("S20s", "S20", "empty", "ews", "bar", "LA", [], "BAR_EXT", "Low wide: the brick railway arch at night, warm light spilling from the bar doorway onto the wet pavement, a train passing overhead as a blur of lit windows; nobody outside.", pin=B("L316", 3.4), fx="push", motion="A train passes along the arch above as a soft blur of lit windows from left to right; the doorway light stays constant; nobody walks in or out."),
    S("S21a", "S21", "estill", "ws", "elev", "EL", [], "ELV1", "Inside the private elevator: dark walnut and brass, the doors closed; EMPTY.", fx="push"),
    S("S21b", "S21", "ins", "ecu", "elev", "EL", [Ks], "ELV2", "Side insert: Kenji's ONE hand holding the black card against the blank card reader plate, its small lamp glowing red." + ONEHAND, line="L317", fx="push"),
    S("S21c", "S21", "ins", "ecu", "elev", "HA", [Ks], "ELV2", "Side insert: Kenji's ONE hand holding the plain black key card against the reader plate, its small lamp now glowing green." + ONEHAND, line="L318", fx="push"),
    S("S21d", "S21", "estill", "ews", "top", "LA", [], "ELV4", "Low angle: the heavy dark walnut double door with plain brass lever handles, slightly open, a thin line of warm lamp light from inside; EMPTY.", pin=E("L318", 0.3), fx="push"),
    S("S21e", "S21", "estill", "ews", "top", "LA", [], "TOP1", "Low wide from the doorway: the long dark walnut desk, the empty high-backed black leather chair, the Tokyo night through floor-to-ceiling windows; EMPTY." + DRY, line="L319", fx="push"),
    S("S21f", "S21", "estill", "ws", "top", "EL", [], "TOP3", "The wall of seven identical gold frames in one row, six holding half-cut black cards on black matte, the seventh empty, small blank brass plates (names composited); EMPTY.", pin=B("L319", 3.0), fx="pan"),
    S("S21g", "S21", "estill", "ms", "top", "EL", [], "TOP3", "Straight on: the seventh gold frame, empty black matte board, its small brass plate (「No.7 高橋健二」 composited); the room depth behind reflected faintly in the glass; EMPTY.", line="L320", fx="dollyzoom"),
    S("S21h", "S21", "empty", "ecu", "top", "EL", [], "P_CUP", "Macro on the walnut desk: a white porcelain coffee cup on a saucer, a thin wisp of steam rising; EMPTY room behind in soft focus.", line="L321",
      motion="A thin wisp of steam rises steadily from the coffee; nothing else moves; the light stays constant; nobody appears."),
    S("S21i", "S21", "face", "ms", "top", "EL", [Ks], "TOP1", "Medium: Kenji standing by the desk at three-quarter, turning his head a little to look around the empty dark room (screen RIGHT).", pin=E("L321", -0.1), expr="tense",
      motion="He turns his head about 15 degrees to the right and back; his eyes search the dark; nobody else appears." + HOLD + DRY),
    S("S21j", "S21", "estill", "ecu", "top", "HA", [], "P_ENV", "High macro: a cream envelope beside the coffee saucer on the walnut desk, sealed with the red emblem wax seal (「高橋健二様」 composited); no hands.", line="L322", fx="push"),

    # ── S22 계약서(8:53~9:28)
    S("S22a", "S22", "ins", "ecu", "top", "EL", [Ks], "P_ENV", "Side insert: Kenji's ONE hand holding a folded thick contract half drawn out of the opened cream envelope, the broken wax seal visible." + ONEHAND, fx="push"),
    S("S22b", "S22", "estill", "ws", "top", "OH", [], "TOP1", "Overhead: a thick plain contract laid flat on the walnut desk under the lamp (title 「所有権継承契約書」 composited); no hands.", line="L323", fx="push"),
    S("S22c", "S22", "estill", "ecu", "macro", "HA", [], "TOP1", "High macro of one contract clause, the lamp light raking across the paper (clause text composited and highlighted); no hands.", line="L324", fx="push"),
    S("S22d", "S22", "estill", "ecu", "macro", "EL", [], "TOP1", "Low raking macro of the next clause (text composited and highlighted), the rest of the page out of focus; no hands.", line="L325", fx="push"),
    S("S22e", "S22", "estill", "ms", "top", "EL", [], "TOP2", "Straight on: the empty high-backed black leather chair behind the desk, the night city beyond; EMPTY.", line="L326", fx="push"),
    S("S22g", "S22", "face", "cu", "top", "SIDE", [Ks], "TOP1", "Close-up profile of Kenji at three-quarter from the side, standing at the desk, eyes on the empty chair (screen RIGHT).", line="L327", expr="hard",
      motion="He looks at the chair; a slow breath; his jaw tightens." + HOLD),
    S("S22f", "S22", "estill", "ms", "top", "EL", [], "TOP3", "The sixth gold frame with its half card, the small brass plate below (「No.6 三好達也」 composited); EMPTY.", pin=E("L327", -1.2), fx="push"),
    S("S22h", "S22", "estill", "ecu", "macro", "HA", [], "TOP1", "High macro of the contract's signature fields: one field with a printed name, one field empty (「高橋健二」 and 「次の候補者：」 composited); no hands.", line="L329", fx="push"),
    S("S22i", "S22", "ep1clip", "ecu", "macro", "HA", [], None, "Episode 1 flashback 0.5 s: the divorce form on the kitchen table with the husband's field empty (episode 1 final clip, desaturated).", line="L330", vo=True),

    # ── S23 차 안(9:28~9:52) — 우핸들·운전대 1
    S("S23a", "S23", "face", "ws", "car", "EL", [Ks, Ch], "CAR1", "Medium from the front-left of the rear cabin: Kenji SEATED NORMALLY facing FORWARD in the right rear seat, the chauffeur's cap and shoulder in the right front seat in the foreground (face never visible), neon sliding past.", line="L337", vo=True, expr="cold",
      motion="Kenji sits still facing forward; neon slides over him; the chauffeur's cap does not move." + CARGEO + HOLD),
    S("S23a2", "S23", "empty", "ws", "car", "SIDE", [], "CAR2", "Through the rear side window: the night city sliding past, neon streaks on the wet glass; no people visible.", pin=B("L337", 3.0), fx="pan", motion="The night city lights slide past outside the glass at an even speed; the cabin stays dark and still; nobody appears."),
    S("S23b", "S23", "face", "ecu", "car", "EL", [Ks], "CAR4", "Extreme close-up of the rear-view mirror: only Kenji's eyes reflected in it, cold, looking at the chauffeur." + EYES, line="L338", vo=True, expr="hard",
      motion="His eyes in the mirror narrow; one slow blink." + CARGEO),
    S("S23c", "S23", "ins", "ms", "car", "EL", [Ch], "CAR4", "Side insert: ONE white-gloved hand resting on the single steering wheel in front of the RIGHT front seat." + ONEHAND + CARGEO, line="L339", vo=True,
      motion="The gloved hand turns the wheel a few degrees and back, smooth and calm."),
    S("S23d", "S23", "ins", "ecu", "car", "HA", [Ks], "CAR1", "High insert on Kenji's knee: the contract's signature field with a fountain pen just lifted from the paper in his ONE hand, the ink still wet (handwritten 「高橋健二」 composited)." + ONEHAND + CARGEO, line="L340a", fx="push", motion="Neon reflections slide slowly across the surfaces as the car glides; the hand and the object stay perfectly still in the same grip; nothing changes shape; nobody appears."),
    S("S23e", "S23", "face", "cu", "car", "SIDE", [Ks], "CAR1", "Close-up profile of Kenji in the rear seat, looking out of the side window at the passing night (screen RIGHT).", line="L340b", expr="calm",
      motion="He breathes out slowly; a slow blink; neon slides over his face." + CARGEO + HOLD),

    # ── S24 정산 취소·마지막 컷(9:52~10:25) — BGM 0(전화), 마지막에 따뜻한 해소
    S("S24b", "S24", "face", "cu", "car", "EL", [Ks], "CAR1", "Close-up of Kenji at three-quarter in the rear seat, the smartphone PRESSED AGAINST HIS RIGHT EAR, listening, eyes forward.", line="L340c", vo=True, expr="cold",
      motion="He listens; a slow blink; his free hand rests on his knee." + CARGEO + HOLD),
    S("S24c", "S24", "empty", "ecu", "macro", "EL", [], "P_CARD", "Macro: the black card lying on the contract on Kenji's knee, the emblem catching the neon (it will be dimmed in the edit); no hands.", line="L340d", fx="dimdown", motion="Neon reflections slide slowly across the card and the paper as the car glides; nothing moves or changes shape; no hands appear; nobody appears."),
    S("S24d", "S24", "ins", "ecu", "car", "EL", [Ks], "CAR1", "Side insert: Kenji's ONE hand holding the smartphone, the screen a plain soft glow (incoming call 「美咲」 composited)." + ONEHAND, line="L340e", vo=True, fx="push"),
    S("S24e", "S24", "face", "ms", "car", "SIDE", [Ks], "CAR2", "Medium through the side window: Kenji's face reflected faintly over the passing night city, the phone at his ear, motionless.", line="L340f", vo=True, expr="calm",
      motion="The night lights slide across the glass; Kenji does not move." + CARGEO + HOLD),
    S("S24e2", "S24", "ins", "ecu", "car", "HA", [Ks], "CAR1", "High insert: Kenji's ONE free hand resting still on the signed contract on his knee, the fountain pen capped beside it." + ONEHAND + CARGEO, pin=B("L340f", 3.2), fx="push", motion="Neon reflections slide slowly across the surfaces as the car glides; the hand and the object stay perfectly still in the same grip; nothing changes shape; nobody appears."),
    S("S24f", "S24", "d", "cu", "car", "EL", [Ks], "CAR1", "Chest-up close-up of Kenji at three-quarter angle in the rear seat, the smartphone PRESSED AGAINST HIS RIGHT EAR, eyes toward the front seats (screen LEFT).", line="L340g", expr="calm",
      act="Very quiet, almost tender, a small pause before 自分の; eyes lowered toward the front; no smile; answering Misaki on the phone." + CARGEO + OB),
    S("S24g", "S24", "face", "ecu", "car", "EL", [Ks], None, "Extreme close-up of Kenji's eyes at three-quarter, the corners softening for the first time, wet but not running." + EYES, line="L340h", vo=True, expr="soft",
      motion="NOT smiling broadly. The corners of his eyes soften; one slow blink; the eyes stay wet but no tear falls."),
    S("S24h", "S24", "empty", "ecu", "car", "HA", [], "P_CARD", "High macro: the black card on the contract on his knee, plain and dull now, no shine; no hands.", line="L340i", fx="pullback", motion="Neon reflections slide slowly across the card and the paper as the car glides; nothing moves or changes shape; no hands appear; nobody appears."),
    S("S24i", "S24", "empty", "ws", "car", "EL", [], "CAR2", "Through the rear window: the night city lights opening up as the car leaves a tunnel, the cabin dark; no people visible.", pin=E("L340i", 0.3), fx="pullback", motion="The night city lights slide past outside the glass at an even speed; the cabin stays dark and still; nobody appears."),
    S("S24j", "S24", "estill", "ms", "archive", "EL", [], None, "Final cut, no dialogue: the large formal portrait in the dark basement corridor, the glass reflecting a white glare so the face is completely hidden; EMPTY corridor.", pin=E("L340i", 1.6), fx="push"),
]
SPK_WHO = {"美咲": Mi, "永瀬": Na, "鷺沼": Sa, "警備員": Kb}
KEN_WARD = {}
VO_OTS_SKIP = {"S14j", "S16e", "S16l", "S17b", "S17k", "S18p", "S23a", "S24b", "S24e", "S20d", "S14e", "S14f"}
MOTION_FIX = {}
for _s in SHOTS:
    if _s["id"] in MOTION_FIX:
        _s["motion"] = MOTION_FIX[_s["id"]] + " " + _s["motion"]

CARDS = {"S14a": "消えた六人は、どこへ行ったのか。", "S14b": "ブラックカード　第二話", "S19m": "この後――十五年前、俺を\"落とした\"男の告白"}
JA_OVERLAY = {
    "S13e": "휴대폰 「非通知」(lcd) + 구석 「残り６日」", "S14c": "면접 사진(15년 전 켄지, 1화 S12o 재사용 합성)", "S14e": "구석 소자막 「午前一時　六本木ルクスタワー」",
    "S14l": "상자 라벨 「採用ファイル」", "S14m": "명부: ◆ 7개 + 6줄 붓 먹칠", "S14n": "먹칠 줄(S14m과 같은 면)", "S14o": "「高橋健二」 + 선명한 「No.7」",
    "S14r": "평가표 「総合 A」", "S14s": "「A」 이중선 + 「C」", "S14t": "붉은 인 「指示あり」 + 문양", "S15a": "「希望退職」 표지 6", "S15b": "승인란 「永瀬」 인(편집에서 6연속)",
    "S15c": "「退職日」·「所在不明」 메모(KleeOne)", "S15d": "퇴직일 6개", "S15e": "「住民票　職権消除」 통지", "S15g": "증명사진 = miyoshi-idphoto", "S15h": "같은 증명사진",
    "S15i": "휴대폰 연락처 「三好」 발신(lcd)", "S16a": "휴대폰 「非通知」 착신(lcd)", "S16g": "카드 뒷면 무지(합성 없음)", "S16h": "먹칠 6줄", "S16j": "먹칠 6줄", "S16k": "증명사진",
    "S17a": "구석 소자막 「午前七時半　江東区」", "S17e": "달력 2년 전 3월(월·날짜)", "S17f": "붉은 동그라미 7개(마지막 검정)", "S17j": "같은 달력", "S17l": "레코더 카운터 숫자(lcd)",
    "S18a": "구석 소자막 「午前十一時　蓮見商事　十二階」", "S18c": "승인서 7장 붉은 인", "S18m": "흰 종이 무지(합성 없음)", "S18o": "손글씨 「鷺沼」(KleeOne, 떨림)",
    "S18r": "붉은 인", "S18t": "휴대폰 「不在着信 12件 美咲」(lcd)", "S19a": "구석 소자막 「午後一時」", "S19g": "「任務終了」", "S19h": "휴대폰 「留守番電話　柴田　23:41」(lcd)",
    "S20a": "구석 소자막 「午後八時　新橋」", "S20c": "「任務終了」", "S21a": "구석 소자막 「午後十一時」", "S21f": "액자 명판 No.1~No.6 이름(三好達也 포함)", "S21g": "명판 「No.7　高橋健二」",
    "S21j": "봉투 「高橋健二様」(KleeOne)", "S22b": "「所有権継承契約書」", "S22c": "조항 1 「期限の日、候補者は、現所有者のすべてを継承する」", "S22d": "조항 2 「次の候補者を一人指名すること」",
    "S22f": "명판 「No.6　三好達也」", "S22h": "서명란 인쇄 「高橋健二」 + 빈칸 「次の候補者：」", "S23d": "서명란 손글씨 「高橋健二」(KleeOne, 젖은 잉크)",
    "S24d": "휴대폰 「美咲」 착신(lcd)",
}
G = {
    "car": "a luxury car gliding at night, a smooth engine, tyres on wet asphalt", "booth": "a quiet rear service entrance after rain, dripping water, a distant highway hum",
    "archive": "a silent basement archive, a low air-conditioning hum, a faint electrical buzz, an old wall clock ticking", "apt": "an empty old apartment room in the morning, distant crows, a far train",
    "meeting": "an air conditioner hum, a fluorescent tube buzzing faintly, distant office keyboards", "corridor": "a quiet office corridor, fluorescent hum, distant phones",
    "backday": "a rear service entrance in the afternoon, a ventilation fan, distant traffic, pigeons", "bar": "a tiny old bar under railway tracks, ice in a glass, a muffled train passing overhead every few seconds",
    "elev": "a quiet elevator humming", "top": "a silent top-floor office at night, faint wind pressure on the windows, a far city hum", "memory": "a soft muffled room tone",
}
AMB_BY_SCENE = {"S13": "archive", "S14": "archive", "S15": "archive", "S16": "archive", "S17": "apt", "S18": "meeting", "S19": "backday", "S20": "bar",
                "S21": "top", "S22": "top", "S23": "car", "S24": "car"}
AMB_BY_SHOT = {"S13c": "memory", "S13d": "car", "S13e": "car", "S14a": "car", "S14b": "car", "S14c": "car", "S14d": "car", "S14e": "booth", "S14f": "booth",
               "S14g": "booth", "S14h": "booth", "S14i": "booth", "S14j": "booth", "S14u": "memory", "S17p": "memory", "S17v": "car", "S18s": "corridor",
               "S18t": "corridor", "S20i": "memory", "S21a": "elev", "S21b": "elev", "S21c": "elev", "S22i": "memory", "S24j": "archive"}
FOLEY = {  # 손이 물건에 닿는 순간마다 폴리 1개(최우선 원칙 6③)
    "S13a": "a small plastic click of a recorder play button, faint tape hiss", "S14c": "a photograph lifted between fingers", "S14g": "a ring of keys jingling as it is held out",
    "S14h": "keys closed in a fist", "S14l": "a cardboard file box slid out of a steel shelf", "S14n": "a fingertip on paper", "S14r": "a single sheet drawn out from under a ledger",
    "S14v": "a sheet of paper crumpling in a fist", "S15d": "a fingertip tapping paper", "S15f": "a flashlight handle shifting in a hand", "S15g": "a file cover turned",
    "S15i": "a phone screen tap, a dial tone", "S16a": "a smartphone vibrating in a hand", "S16b": "a small security camera servo whirring", "S16g": "a card drawn out of a pocket",
    "S16n": "a phone call ending with a soft click", "S17a": "a key handed over in a gloved hand", "S17d": "a fingertip sliding on a wooden sill", "S17h": "a small plastic click of a recorder play button",
    "S17o": "a tiny click as a recorder stops", "S17p": "a plastic tray, chopsticks", "S17t": "a recorder slipped into a jacket pocket", "S17u": "a slow footstep on a steel stair",
    "S17v": "a heavy car door closing", "S18c": "papers fanned on a table", "S18d": "glasses pushed up a nose", "S18g": "a palm pressed on a table", "S18j": "one finger tap on paper",
    "S18m": "a single sheet sliding across a table and stopping", "S18n": "two finger taps on paper", "S18o": "a pen nib scratching paper unevenly", "S18p": "a chair creaking as a man slumps back",
    "S18r": "a seal pressed on paper, a deep low impact", "S18t": "a smartphone vibrating", "S19c": "a hand grabbing a jacket sleeve", "S19d": "a crumpled envelope pulled from a handbag",
    "S19f": "an envelope flap opened", "S19h": "a phone voicemail beep", "S19k": "an envelope taken from a hand", "S20a": "ice shifting in a glass, a train rumbling overhead",
    "S20c": "an envelope pushed along a wooden counter", "S20f": "a glass lifted, ice clinking", "S20n": "ice clicking in a glass", "S20o": "a glass set down on wood",
    "S20q": "a key card sliding across a wooden counter and stopping", "S20r": "a key card lifted off wood", "S21b": "a card tapped on a reader, a low error buzz",
    "S21c": "a card tapped on a reader, a short high beep, an elevator starting to rise", "S21d": "a heavy door latch clacking open", "S21j": "an envelope touched on wood",
    "S22a": "a thick envelope opened, paper drawn out", "S23c": "a gloved hand on a steering wheel", "S23d": "a fountain pen lifted from paper", "S24a": "a smartphone vibrating in a hand",
    "S24d": "a smartphone vibrating in a hand", "S24j": "one slow heavy heartbeat",
}
BGM = [  # (시작, 끝, 볼륨, 프롬프트) — 정적 큐(09) 구간은 비운다. 간격 1.0초 이상
    (3.5, 79.5, 0.36, "dark low drone with a slow heartbeat pulse and cold strings, a night return to an office tower, Japanese noir thriller, instrumental, no vocals"),
    (98.7, 138.5, 0.38, "tense discovery, low pizzicato and cold strings rising, files in a dark archive, Japanese noir thriller, instrumental, no vocals"),
    (201.2, 207.0, 0.36, "a single low string note swelling into dread, Japanese noir thriller, instrumental, no vocals"),
    (208.5, 239.5, 0.36, "sorrowful solo cello and sparse piano, an empty apartment in grey morning light, Japanese noir drama, instrumental, no vocals"),
    (276.0, 301.0, 0.38, "single gentle piano notes over soft strings, grief turning into resolve, Japanese drama, instrumental, no vocals"),
    (302.3, 341.5, 0.38, "cold confrontation, sparse piano over a low pulse, a glass meeting room, Japanese noir thriller, instrumental, no vocals"),
    (361.0, 390.5, 0.38, "uneasy low strings, a frightened wife at a back door, Japanese noir drama, instrumental, no vocals"),
    (406.4, 427.5, 0.38, "restrained aching strings rising to a cliff, Japanese noir drama, instrumental, no vocals"),
    (428.7, 483.0, 0.34, "slow smoky noir jazz bass and brushed drums, an old bar under railway tracks, a confession, instrumental, no vocals"),
    (486.5, 501.5, 0.38, "low strings resolving into resolve, a key card on a counter, Japanese noir thriller, instrumental, no vocals"),
    (535.4, 563.8, 0.40, "building taiko-like low drums and dark strings, a contract revealed, Japanese noir thriller, instrumental, no vocals"),
    (615.5, None, 0.40, "warm release: soft piano and strings, a weight finally lifted, quiet night drive, Japanese drama, instrumental, no vocals"),
]
for _a, _b in zip(BGM, BGM[1:]):
    assert _b[0] - _a[1] >= 1.0, f"BGM 구간 간격 {_b[0] - _a[1]:.1f}s < 1.0s"
SILENCE = [("S14o", "S14t", +3, "T1 No.7 발견 — 손전등 버즈·초침·숨 → 붉은 인 펀치 인"),
           ("S15g", "S16o", +2, "T2·T3 三好 사진 → 声 통화(BGM 0, 공조음·서보·진동·통화 종료)"),
           ("S17h", "S17p", +2, "T4 녹음 재생 — 테이프 히스·전철·「プツッ」"),
           ("S18m", "S18r", +3, "T5 「判子は――ここ」 — 종이 정지음·초침·펜 끝"),
           ("S19f", "S19j", +2, "T6 任務終了·留守電 — 환풍기·저주파"),
           ("S21a", "S22b", +3, "T8 최상층 — 엘리베이터 버저·카드키·문 래치·김"),
           ("S23a", "S24g", +2, "T10 차 안·전화 — 엔진·노면·진동")]
FOLEY_TENSION = {"S14p": "a flashlight buzzing faintly, an old clock ticking, a held breath", "S16f": "an air-conditioning hum, a small LED relay click",
                 "S18n": "a wall clock ticking in a silent meeting room, a hard swallow", "S21h": "wind pressure on tall windows, a clock ticking", "S24c": "an engine hum, tyres on wet road"}
FOLEY.update(FOLEY_TENSION)

STYLE_OF = {("高橋 健二(N)", "narration"): "KenjiN", ("健二", "dialogue"): "Kenji", ("美咲", "dialogue"): "Misaki", ("声", "dialogue"): "Koe",
            ("永瀬", "dialogue"): "Nagase", ("鷺沼", "dialogue"): "Sagisuma", ("三好", "dialogue"): "Miyoshi", ("柴田", "dialogue"): "Shibata"}
STYLE_JA = {"KenjiN": "健二（語り）", "Kenji": "健二", "Misaki": "美咲", "Koe": "声", "Nagase": "永瀬", "Sagisuma": "鷺沼", "Miyoshi": "三好", "Shibata": "柴田", "Staff": "スタッフ"}
STYLE_COLOR = {"KenjiN": "&H00DDDDDD", "Kenji": "&H00FFFFFF", "Misaki": "&H00F0E6C8", "Koe": "&H00C8E6F0", "Nagase": "&H00C8C8F0", "Sagisuma": "&H00B4DCE6",
               "Miyoshi": "&H00D2F0D2", "Shibata": "&H00B4D2FF", "Staff": "&H00D0D0D0"}
RATE = {"lite": 0.036, "omni": 0.16, "kf": 0.04}
BANNED_MOTION = (("slam", "큰 동작"), ("spin", "회전"), ("tracking camera", "편집 전용 무빙"), ("dolly", "편집 전용 무빙"), ("zoom", "편집 전용 무빙"),
                 ("crane", "편집 전용 무빙"), ("dialogue", "오디오 지시"), ("says", "오디오 지시"), ("sound of", "오디오 지시"))

def tc(sec):
    fr = int(round(sec * FPS)); s, f = divmod(fr, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}.{f:02d}"


def ass_t(sec):
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap_lines(text, limit=20):
    """휴대폰 기준(제13장 1·제17장 2): 줄당 20자 이내. 끊는 자리는 구두점 > 조사 뒤 > 글자 종류 경계 순(낱말 중간 금지), 줄 길이는 고르게."""
    n = len(text)
    if n <= limit:
        return [text]
    NOHEAD = "…—、。!?？！』」ーぁぃぅぇぉっゃゅょゎァィゥェォッャュョ"
    def kind(c):
        return "h" if "ぁ" <= c <= "ゖ" else "k" if "ァ" <= c <= "ヺ" or c == "ー" else "p" if c in "、。…!?？！』」「『\"" else "c"
    def cost(i):
        a, b = text[i - 1], text[i]
        if b in NOHEAD or a in "「『\"":
            return 99
        if a in "、。!?？！』」" or (a == "…" and b != "…") or (a == "―" and b != "―"):
            return 0
        if a in "はがをにでともへやねよ" and kind(b) != "h":
            return 3
        if kind(a) != kind(b) and kind(b) != "h":
            return 6
        return 30
    def solve(lines):
        best = {0: (0, [])}
        for _ in range(lines):
            nxt = {}
            for st, (c0, br) in best.items():
                for e in range(st + 1, min(n, st + limit) + 1):
                    c = c0 + (0 if e == n else cost(e)) + abs((e - st) - n / lines) * 0.4
                    if e not in nxt or c < nxt[e][0]:
                        nxt[e] = (c, br + [e])
            best = nxt
        return best.get(n)
    lo = -(-n // limit)
    sols = [(r[0] + 12 * (k - lo), r[1]) for k in (lo, lo + 1) for r in [solve(k)] if r]
    br = [0] + min(sols)[1]
    return [text[br[k]:br[k + 1]] for k in range(len(br) - 1)]


WRAP_FIX = {}


def chunks(text, limit=20):
    """한 이벤트 2줄 이내(제15장 21): 3줄 이상이면 2줄씩 조각."""
    ls = WRAP_FIX.get(text) or wrap_lines(text, limit)
    if len(ls) == 3 and ls[0][-1] in "、。…!?？！』」" and ls[1][-1] not in "、。…!?？！』」":
        return [ls[0], "\\N".join(ls[1:])]
    return ["\\N".join(ls[i:i + 2]) for i in range(0, len(ls), 2)]


def script_texts():
    return {x["tag"]: x["ja"] for x in LOCK["lines"]}


def tone_table():
    """05_톤연출표.md → {tag: (emo, inten, tempo, memo)} (음성·표정·동작의 단일 출처, 제10장 7)."""
    out = {}
    for l in open(os.path.join(PROD, "05_톤연출표.md"), encoding="utf-8"):
        c = [x.strip() for x in l.split("|")]
        if len(c) > 9 and c[1].startswith("line"):
            out[c[2]] = (c[6], c[7], c[8], c[9])
    return out


def check_rules(shots):
    errs = []
    prev = None
    for s in shots:
        if s["kind"] == "d" and s["angle"] in ("SIDE", "BE", "OH"):
            errs.append(f"{s['id']}: OMNI 대사 컷 각도 {s['angle']} 금지")
        if s["kind"] == "d" and s["line"] and not s["act"]:
            errs.append(f"{s['id']}: 립싱크 컷에 연기 지시(act) 없음")
        if prev and prev["scene"] == s["scene"] and not s["kind"].startswith("reuse") and not prev["kind"].startswith("reuse") and "card" not in (s["kind"], prev["kind"]):
            if prev["lens"] == s["lens"] and prev["angle"] == s["angle"] and prev["loc"] == s["loc"] and prev["who"] == s["who"]:
                errs.append(f"{prev['id']}→{s['id']}: 연속 같은 구도(A1)")
        if s["line"]:
            spk = ROWS[s["line"]]["spk"]
            on = [base(w.split(":")[0]) for w in s["who"]]
            if spk in SPK_KEY and ROWS[s["line"]]["type"] == "dialogue" and SPK_KEY[spk] not in on and not s["vo"]:
                errs.append(f"{s['id']}: {s['line']} 화자 {spk}가 화면에 없음(화자-화면 일치) — 의도면 vo=True")
            if spk in SPK_KEY and s["kind"] == "d" and (not on or SPK_KEY[spk] != on[0]):
                errs.append(f"{s['id']}: 립싱크 대상(who[0])이 화자 {spk}와 다름")
            if s["kind"] == "d" and ROWS[s["line"]]["type"] == "narration":
                errs.append(f"{s['id']}: 내레이션 줄 {s['line']}을 립싱크로 지정")
            if s["kind"] in ("face", "ins", "empty", "estill") and ROWS[s["line"]]["type"] == "dialogue" and spk in SPK_KEY and not s["vo"]:
                errs.append(f"{s['id']}: 대사 줄 {s['line']} 위 화자가 보이는 비립싱크 컷 — vo=True(입 안 보임) 또는 pstill")
        low = (s["motion"] or "").lower()
        for w, why in BANNED_MOTION:
            if w in low:
                errs.append(f"{s['id']}: 동작 문장 금지어 「{w}」({why})")
        if s["kind"] == "ins" and re.search(r"(?<!no )\bfaces?\b", s["subject"].lower()):
            errs.append(f"{s['id']}: 인서트에 얼굴 묘사(제15장 3 — NO FACE)")
        if s["kind"] == "ins" and "hand" in s["subject"].lower() and "HANDS LOCKED" not in s["subject"] and "no hands" not in s["subject"].lower():
            errs.append(f"{s['id']}: 손 인서트에 HANDS LOCKED 없음(제19장 25)")
        prev = s
    dz = sum(1 for s in shots if "dollyzoom" in s["fx"]); dutch = sum(1 for s in shots if "dutch" in s["fx"])
    if dz != 1:
        errs.append(f"돌리줌 {dz}회(1회만)")
    if dutch > 2:
        errs.append(f"더치 {dutch}회(최대 2회)")
    scenes = collections.OrderedDict()
    for s in shots:
        scenes.setdefault(s["scene"], []).append(s)
    for sc, ss in scenes.items():
        sizes = {x["lens"] for x in ss}
        if len(ss) >= 5 and len(sizes) < 4:
            errs.append(f"{sc}: 사이즈 종류 {len(sizes)} < 4(영화처럼 다양하게)")
        ds = [x for x in ss if x["kind"] == "d"]
        for a, b in zip(ds, ds[1:]):
            ia, ib = ss.index(a), ss.index(b)
            if ib - ia == 1 and base(a["who"][0].split(":")[0]) == base(b["who"][0].split(":")[0]):
                errs.append(f"{sc}: {a['id']}→{b['id']} 같은 화자 립싱크 연속(리액션 컷 없음)")
    return errs


def main():
    texts = script_texts()
    scenes = {s["id"]: (s["start"], s["end"]) for s in LOCK["scenes"]}
    main_end = LOCK["body_end"]
    for s in SHOTS:
        spk = ROWS[s["line"]]["spk"] if s.get("vo") and s["line"] in ROWS else None
        sp = (KEN_WARD.get(s["scene"], Ks) if spk == "健二" else SPK_WHO.get(spk)) if spk else None
        s["ots"] = bool(sp and s["id"] not in VO_OTS_SKIP and s["kind"] == "face" and len(s["who"]) == 1 and base(sp.split(":")[0]) != base(s["who"][0].split(":")[0]))
        if s["ots"]:
            s["who"] = s["who"] + [sp]
    errs = check_rules(SHOTS)
    body_tags = {t for t, x in ROWS.items() if x.get("start") is not None}
    used = [s["line"] for s in SHOTS if s["line"]]
    if sorted(used) != sorted(body_tags):
        errs.append(f"대사 줄 사용 불일치: 빠짐 {sorted(body_tags - set(used))}, 중복·초과 {sorted(set(u for u in used if used.count(u) > 1) | (set(used) - body_tags))}")
    for s in SHOTS:
        for w in s["who"]:
            key = w.split(":")[0]
            if key not in WHO:
                errs.append(f"{s['id']}: 인물 키 {key} 없음")
            if s["expr"] and (key, s["expr"]) in EXPR and not os.path.exists(os.path.join(ROOT, EXPR[(key, s["expr"])])):
                errs.append(f"{s['id']}: 셀 없음 {EXPR[(key, s['expr'])]}")
        if s["loc"] and s["loc"] not in LOC:
            errs.append(f"{s['id']}: 장소 키 {s['loc']} 없음")
        if s["loc"] in LOC and not os.path.exists(os.path.join(ROOT, LOC[s["loc"]])):
            errs.append(f"{s['id']}: 셀 없음 {LOC[s['loc']]}")
        if s["kind"].startswith("reuse") and s["kind"].split(":")[1] not in {x["id"] for x in SHOTS}:
            errs.append(f"{s['id']}: 재사용 원본 {s['kind']} 없음")
    if errs:
        raise SystemExit("규칙 위반:\n  " + "\n  ".join(sorted(set(errs))))

    starts = {}
    by_scene = collections.OrderedDict()
    for s in SHOTS:
        by_scene.setdefault(s["scene"], []).append(s)
    for sc, shots in by_scene.items():
        a, b = scenes[sc]
        pins = {0: a, len(shots): b}
        for k, s in enumerate(shots):
            if s["line"] and k:
                pins[k] = max(a, ROWS[s["line"]]["start"] - LEAD)
            elif s.get("pin") is not None and k:
                pins[k] = max(a, s["pin"] - LEAD if s["line"] else s["pin"])
        keys = sorted(pins)
        for k1, k2 in zip(keys, keys[1:]):
            t1, t2 = pins[k1], pins[k2]; n = k2 - k1
            for j in range(k1, k2):
                starts[shots[j]["id"]] = t1 + (t2 - t1) * (j - k1) / n
    order_ids = [s["id"] for s in SHOTS]
    ends = {sid: (starts[order_ids[k + 1]] if k + 1 < len(order_ids) else main_end) for k, sid in enumerate(order_ids)}
    for k, s in enumerate(SHOTS):
        if s["kind"] == "d" and s["line"] and ends[s["id"]] - starts[s["id"]] > OMNI_MAX:
            nxt = order_ids[k + 1]; starts[nxt] = starts[s["id"]] + OMNI_MAX; ends[s["id"]] = starts[nxt]
    problems = []
    for s in SHOTS:
        d = ends[s["id"]] - starts[s["id"]]
        if d < MIN_SHOT:
            problems.append(f"{s['id']} {d:.2f}s < {MIN_SHOT}")
        still = s["kind"] in ("estill", "pstill") or (s["kind"] == "ins" and not s["motion"])
        if still and d > STILL_MAX:
            problems.append(f"{s['id']} 정지 {d:.2f}s > {STILL_MAX}")
        if s["kind"] in ("face", "empty") and d > I2V_MAX:
            problems.append(f"{s['id']} i2v {d:.2f}s > {I2V_MAX}")
        if d > 5.0 and s["kind"] not in ("d",) and not s["kind"].startswith("reuse") and s["kind"] != "card":
            problems.append(f"⚠ {s['id']} 한 구도 {d:.2f}s > 5.0(제4장 — finalize 인서트·줌으로 깬다)") if d > 6.5 else None
    hard = [p for p in problems if not p.startswith("⚠")]
    if hard:
        raise SystemExit("컷 길이 위반:\n  " + "\n  ".join(hard))

    durations, sb, scene_items, omni_prompts, live, foley = [], [], [], {}, {}, {}
    cost = collections.Counter()
    for s in SHOTS:
        sid = s["id"]; d = ends[sid] - starts[sid]
        durations.append(round(d + HARD, 4))
        refs, ids = [], []
        for j, w in enumerate(s["who"]):
            key, _, ward = w.partition(":")
            desc, cell = WHO[key]
            if s["kind"] in ("ins", "estill") and key in HANDS:  # 인서트 = 손·소매만(얼굴 묘사 금지, 제15장 3)
                ids.append(f"only the hands and sleeves of {desc.split(',')[0]}: {HANDS[key]}" + (f", sleeves of {WARD[ward]}" if ward else ""))
            else:
                ids.append(desc + (f", wearing {WARD[ward]}" if ward else ""))
            if s["kind"] in ("ins", "estill") or not cell:
                continue
            fg = (s["kind"] == "d" and j == 1) or (s.get("ots") and j == len(s["who"]) - 1)  # 흐린 앞 어깨 = 뒷모습 셀(제18장 8②)
            if fg:
                if (key, "back") in EXPR:
                    refs.append(EXPR[(key, "back")])
            elif s["expr"] and (key, s["expr"]) in EXPR and j == 0:
                refs.append(EXPR[(key, s["expr"])])
            else:
                refs.append(cell)
        if s["loc"] in LOC:
            refs.append(LOC[s["loc"]])
        n = len(s["who"])
        if s["kind"] == "d" and n > 1:
            comp = ("Over-the-shoulder two-shot: the listener's blurred shoulder and back of the head at the near foreground edge (FOREGROUND IDENTITY LOCKED: "
                    f"that blurred person is {ids[1].split(',')[0]} — {GLASSES.get(s['who'][1].split(':')[0], '')}), the speaker beyond facing the listener at 30 to 40 degrees from the camera axis, the speaker's face "
                    "at least one third of the frame height, the speaker's mouth closed, hands visible doing the described work. SPEAKER LOCKED: the speaker is "
                    f"{ids[0].split(',')[0]}. Exactly two people, no extra people.")
        elif s["kind"] == "d":
            comp = ("Single speaker at 30 to 40 degrees from the camera axis, eyes toward the other person off-screen, NOT looking at the camera, the face at least one third "
                    "of the frame height, mouth closed. NO foreground person, no other people.")
        elif s.get("ots"):
            comp = ("Over-the-shoulder reverse shot: the SPEAKER's blurred back of the head and shoulder at the near foreground edge (face and mouth NOT visible; "
                    f"FOREGROUND IDENTITY LOCKED: that is {ids[-1].split(',')[0]} — {GLASSES.get(s['who'][-1].split(':')[0], '')}); the LISTENER beyond faces the speaker at 30 to 40 degrees from the camera axis, "
                    "eyes on the speaker, NOT looking at the camera, the listener's face at least one third of the frame height, mouth closed. Exactly two people.")
        elif (s["kind"] in ("empty", "estill") and not s["who"]) or (s["kind"] == "ins" and not s["who"]):
            comp = "Completely unpopulated: no people, no hands, no faces. EMPTY."
        elif s["kind"] in ("ins", "estill"):
            comp = "Insert: only the hands and the object, NO FACE visible, no other people."
        elif s["kind"] == "pstill":
            comp = f"Exactly {n} person seen from behind, the face and mouth NOT visible, no other people."
        else:
            comp = f"Exactly {n} {'person' if n == 1 else 'people'} as described, no extra people. GAZE LOCKED: nobody looks at the camera."
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] in ("card", "ep1clip") else f"assets/portraits/{SKIT}-keyframes/{sid}-1.png"
        kf_prompt = None
        if keyframe:
            low = (s["subject"] + " " + (s["act"] or "") + " " + (s["motion"] or "")).lower()
            real = " ".join(x for x, keys in ((TEARS, (r"tears? (spill|bead|track|run|well)", "eyes wet", "wet eyes", "welling")), (SWEAT, ("sweat",)), (RAINSKIN, ("rain on", "rain-streaked", "rain-soaked face", "wet face")))
                            if any(re.search(k, low) for k in keys) or (s["expr"] == "plead" and x == TEARS))
            glasses = " ".join(GLASSES[w.split(":")[0]] for w in s["who"] if w.split(":")[0] in GLASSES and s["kind"] not in ("ins", "estill"))
            face_expr = f" Expression of {ids[0].split(',')[0]}: {EXPR_TXT[s['expr']]} (about half intensity)." if s["expr"] in EXPR_TXT and s["expr"] != "back" and s["kind"] not in ("ins", "estill", "pstill") else ""
            setting = f"Lighting: {LIGHT[s['light']]}."
            if s["loc"] is None:
                lt = {"S24j": "B2_CORR", "S14d": "TOWER", "S19l": "TOWER", "S18s": "CORRIDOR", "S18t": "CORRIDOR"}.get(sid)
                setting += (" Location: " + LOC_TXT[lt] + ".") if lt else " Background: the same location as the surrounding shots, out of focus."
            kf_prompt = " ".join(x for x in [
                f"[CAMERA] {ANGLE[s['angle']]}, {LENS[s['lens']]}. {comp} {PRESET}.",
                ("[CHARACTER] IDENTITY FIRST — " + " | ".join(ids) + ". " + glasses) if ids else "[CHARACTER] none.",
                f"[ACTION] {s['subject']}{face_expr} {real}".rstrip(),
                f"[SETTING] {setting} {PLAIN}",
                f"[NEGATIVE] {NEGATIVE}."] if x).strip()
            cost["kf"] += 1
        tier = {"d": "omni", "face": "lite", "empty": "lite", "estill": "still", "pstill": "still", "card": "card"}.get(s["kind"], "reuse")
        if s["kind"] == "ins":
            tier = "lite" if s["motion"] else "still"
        gen = 10 if d > 5.0 else 5
        item = {"prompt": "", "duration": gen}
        if tier == "lite":
            item["prompt"] = ("[CAMERA] Static locked-off camera, no camera movement. [CHARACTER] Keep the exact faces, glasses, wardrobe and props of the first frame; "
                              "the same people only. [ACTION] " + (s["motion"] or "Subtle natural motion only: breathing, one blink.") +
                              " Head turns under 20 degrees. [SETTING] The same location and lighting as the first frame; the brightness and colour of the light stay constant. "
                              "[NEGATIVE] No walking toward the camera, no new people, no text, no morphing, no flicker, no exposure change.")
            item["image"] = keyframe; cost["lite"] += gen; live[sid] = s["motion"]
        else:
            item["prompt"] = f"(override) {tier}: {s['subject'][:80]}"; item["override_required"] = True
            if keyframe:
                item["image"] = keyframe
        if tier == "omni":
            cost["omni"] += min(d, OMNI_MAX) + 0.8; omni_prompts[sid] = s["act"]
        scene_items.append(item)
        amb = AMB_BY_SHOT.get(sid, AMB_BY_SCENE.get(s["scene"], ""))
        if sid in FOLEY:
            foley[sid] = FOLEY[sid]
        sb.append({"id": sid, "scene": s["scene"], "kind": s["kind"], "tier": tier, "timecode": f"{tc(starts[sid])} - {tc(ends[sid])}",
                   "assembled_s": round(d, 3), "generate_s": gen, "size": s["lens"], "lens": LENS[s["lens"]], "angle": s["angle"],
                   "lighting": s["light"], "edit_fx": s["fx"], "refs": refs, "ots": s.get("ots", False), "subject": s["subject"], "line": s["line"], "vo": s["vo"], "foley": FOLEY.get(sid, ""),
                   "motion": item["prompt"] if tier == "lite" else "", "act": s["act"], "keyframe": keyframe, "keyframe_prompt": kf_prompt,
                   "ja_overlay": JA_OVERLAY.get(sid, ""), "caption": CARDS.get(sid, ""), "ambience": G.get(amb, "")})
    budget = round(cost["lite"] * RATE["lite"] * 1.25, 2)

    tts_order = sorted([dict(x) for x in LOCK["lines"] if x.get("start") is not None], key=lambda x: x["start"])
    dst = os.path.join(ROOT, "assets", "audio-overrides", SKIT); os.makedirs(dst, exist_ok=True)
    mapping = []
    for i, x in enumerate(tts_order, 1):
        shutil.copyfile(os.path.join(ROOT, "assets", "auditions", TTS_DIR, x["id"] + ".mp3"), os.path.join(dst, f"line{i:03d}.mp3"))
        mapping.append((f"line{i:03d}", x["tag"], x["id"]))

    events = []
    for x in tts_order:
        st = STYLE_OF.get((x["spk"], x["type"]), "Staff")
        s0 = x["start"] - x["lead"]; e0 = x["end"] + 0.2
        parts = chunks(texts[x["tag"]])
        tot = sum(len(q) for q in parts); t = s0
        for k, q in enumerate(parts):  # 조각은 「<스타일>_c」(silent) — TTS 줄 수 유지(제15장 21)
            t1 = e0 if k == len(parts) - 1 else t + (e0 - s0) * len(q) / tot
            events.append((t, t1, st if k == 0 else st + "_c", STYLE_JA[st], q)); t = t1
    events.sort(key=lambda e: e[0])
    st_lines = "\n".join(
        f"Style: {n}{suf},Noto Sans CJK JP,{66 if n == 'KenjiN' else 70},{c},&H000000FF,&H00000000,&H80000000,-1,{-1 if n == 'KenjiN' else 0},0,0,100,100,0,0,1,6,2,2,120,120,90,1"
        for n, c in STYLE_COLOR.items() for suf in ("", "_c"))
    ass = ["[Script Info]", "Title: ブラックカード 第2話 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           st_lines,
           "Style: Caption,Noto Sans CJK JP,84,&H001E1EFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,160,160,80,1",
           "Style: Title,Noto Serif CJK JP,110,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,5,160,160,80,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:
        assert e[4].count("\\N") <= 1 and max(len(q) for q in e[4].split("\\N")) <= 20, f"자막 규격 위반(2줄·20자): {e[4]}"
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{e[4]}")
    os.makedirs(os.path.join(ROOT, "subs"), exist_ok=True)
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    for p in ("storyboard", "scenes", "audio"):
        os.makedirs(os.path.join(ROOT, "scripts", p), exist_ok=True)
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_blackcard2_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT, "preset": PRESET,
               "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": LOCK["ads"], "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_blackcard2_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, wardrobe, "
                         "props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_blackcard2_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (ElevenLabs 확정본, 번호 = 타임라인 순).",
        "default_voice": "cached-typecast", "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["KenjiN"], "silent_styles": ["Caption", "Title"] + [n + "_c" for n in STYLE_COLOR],
        "output_size": [1920, 1080], "fit": "crop", "scene_durations": durations, "transitions": [0.0] * len(durations),
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d" and s["line"]],
        "omnihuman_prompts": {str(idx[k]): v for k, v in omni_prompts.items()},
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0, "legacy_lipsync": False,
        "foley_prompts": {str(idx[k]): v for k, v in foley.items()},
        "bgm_silence": [{"start": round(starts[a], 2), "end": round(starts[b], 2), "sfx_boost_db": g, "why": w} for a, b, g, w in SILENCE],
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35, "duck_db": 8, "ambience_prompts": [x["ambience"] for x in sb],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": s, "end": round(main_end, 2) if e is None else e, "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_후크": "0~3.5초 BGM 없음: 레코더 클릭 + 테이프 히스 + 심장 박동 가속(1화 heartbeat-accel 파일) + 드론. S13a(S17h)·S13b(S21f) 재사용, S13c·S22i는 1화 완성본 클립(ep1clip). S14a 질문 카드·S14b 타이틀·S19m 예고 카드는 클립에 직접(암전 없음).",
        "_정점": "bgm_silence 7곳(09_정점효과음설계.md T1~T10) 효과음은 blackcard2-sfx 잠정 선택 + 1화 콜백 파일(stamp-press·paper-slide·impact-low·heartbeat·clock-tick-heart) → finalize SFX 피크 기준(제19장 26).",
        "_로컬": "플리커 금지(제20장 11). 펀치 인 6회(S14t·S16n·S18r·S19g·S24c 제외→S22h·S24h 대체는 18_카메라줌설계.md), 돌리줌 S21g, 더치 S18g 5°, 승인 인 6연속 S15b, 랙 포커스 S16j, 감정 정점 슬로 줌, 결말 카드 광택 디졸브 S24c, 마지막 컷 S24j(얼굴 비노출) 3.0초.",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    gen_n = sum(v for k, v in tiers.items() if k in ("still", "lite", "omni"))
    still_ratio = tiers["still"] / gen_n if gen_n else 0
    if still_ratio > 0.45:
        raise SystemExit(f"정지 컷 비율 {still_ratio:.0%} > 45% — 슬라이드쇼처럼 보인다(2화 실증 7-2): 무인 문서·차 안 컷을 미세 i2v로 바꾼다")
    total_cost = cost["kf"] * RATE["kf"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    warn = [p for p in problems if p.startswith("⚠")]
    md = ["# 『ブラックカード』(第2話) PHASE 3 샷 리스트 (2화 완결형 B안)", "",
          f"> `scripts/build_blackcard2_phase3.py` 자동 생성(손 수정 금지). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 정지 비율 {still_ratio:.0%}(상한 45%), 광고 " + ", ".join(f"{a['name']} {tc(a['at'])}" for a in LOCK['ads']) + ".",
          "> 자동 검사 통과: 연속 같은 구도 0 · 같은 화자 립싱크 연속 0(리액션 컷) · 장면당 사이즈 4종 이상 · 돌리줌 1회 · 더치 2회 · OMNI 정면~45° · 화자-화면 일치(vo 제외) · 대사 줄 전부 배치 · 컷 길이 · OMNI 8초 이하 · 손 인서트 HANDS LOCKED · 내레이션 줄 립싱크 금지.", ""]
    if warn:
        md += ["> ⚠ 6.5초 넘는 한 구도(finalize 인서트·줌으로 깬다): " + ", ".join(w[2:] for w in warn), ""]
    md += ["## 비용 추산 (실측 단가)", "", "| 항목 | 수량 | 단가 | 금액 |", "|---|---|---|---|",
           f"| 키프레임 | {cost['kf']}장 | 0.04 | {cost['kf'] * RATE['kf']:.2f} |",
           f"| 키프레임 재생성 여유(×1.35, 제15장 10) | | | {cost['kf'] * RATE['kf'] * 0.35:.2f} |",
           f"| i2v lite (사람·손·배경 전부) | {cost['lite']}초 | 0.036 | {cost['lite'] * RATE['lite']:.2f} |",
           f"| OmniHuman (8초 상한 + 앞뒤 0.8초) | {cost['omni']:.1f}초 | 0.16 | {cost['omni'] * RATE['omni']:.2f} |",
           f"| **1차 합계** (키프레임 여유 제외) | | | **{total_cost:.2f}** |", f"| i2v 예산 상한 `budget_usd` (여유 25%) | | | {budget:.2f} |", "",
           "## 생성 방식 분포", "", "| 방식 | 컷 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in tiers.most_common()] + [
           "", f"## 앵글 분포 — 최다 {top[0]} {top[1] / sum(ang.values()) * 100:.0f}% (60% 이하 기준)", "", "| 앵글 | 컷 |", "|---|---|"] + [
           f"| {k} | {v} |" for k, v in ang.most_common()] + [
           "", "## 화면 속 일본어 (무지 → 합성, PHASE 4 마감 체크)", ""] + [f"- {k}: {v}" for k, v in JA_OVERLAY.items()] + [
           "", "## 화면 카드(클립에 직접, .ass Caption 없음)", ""] + [f"- {k}: {v}" for k, v in CARDS.items()] + [
           "", "## 정적 구간(bgm_silence)", ""] + [f"- {a}→{b} ({tc(starts[a])}~{tc(starts[b])}) +{g} dB: {w}" for a, b, g, w in SILENCE] + [
           "", "## 컷별 폴리 (자동 믹스)", ""] + [f"- {k}: {v}" for k, v in FOLEY.items()] + [
           "", "## 샷 표", "", "| 컷 | 타임코드 | 길이 | 방식 | 사이즈 | 앵글 | 조명 | 편집 효과 | 대사 | 현장음 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in sb:
        md.append(f"| {x['id']} | {x['timecode']} | {x['assembled_s']:.2f}s | {x['tier']} | {x['size']} | {x['angle']} | {x['lighting']} | {x['edit_fx']} | {(x['line'] or '') + (' (vo)' if x['vo'] else '')} | {x['ambience'][:30]} |")
    md += ["", "## 음성 번호 대응", "", "| 캐시 | 대본 | 원본 녹음 |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in mapping]
    open(os.path.join(PROD, "07_샷리스트.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    angle_doc(sb)
    emotion_table(sb, live)
    print(f"완료: 컷 {len(SHOTS)}개, 본편 {tc(main_end)}, 방식 {dict(tiers)}, 1차 비용 약 {total_cost:.2f}달러 (i2v budget {budget}), 앵글 {dict(ang)}")


SCENE_TITLE = {"S13": "후크", "S14": "경비원·지하 서고 No.7", "S15": "퇴직 기록·三好", "S16": "声 통화", "S17": "三好의 방·녹음", "S18": "永瀬", "S19": "美咲·留守電",
               "S20": "新橋 바·鷺沼", "S21": "최상층", "S22": "계약서", "S23": "차 안·서명", "S24": "정산 취소·마지막 컷"}


def angle_doc(sb):
    md = ["# 『ブラックカード』(第2話) 카메라 앵글 설계 (CLAUDE.md 제8장, PHASE 3)", "",
          "> 샷 표의 원본은 `scripts/build_blackcard2_phase3.py`(자동 검사 통과). 긴장 설계는 `18_카메라줌설계.md`, 소리는 `09_정점효과음설계.md`.", "",
          "## 1. 권력 축", "", "| 구간 | 켄지 | 상대 |", "|---|---|---|",
          "| S14~S16 서고 | 아이레벨·언더라이트(S14q), 감시카메라 로우(S16b·S16c) | 경비원 하이(S14f 사죄) |",
          "| S18 永瀬 | 아이레벨 고정(트라이포드) | 로우(S18d·S18g 권위, 더치 5°) → 하이(S18p 붕괴) |",
          "| S20 鷺沼 | 아이레벨 | 아이레벨 나란히(고백), L311에서 처음 정면 리버스 |",
          "| S21~S24 최상층·결말 | 로우(S21d·S21e 공간의 압박) → 차 안 아이레벨 → 눈 ECU(S24g 해소) | 빈 의자 정면(S22e) |", "",
          "## 2. 장치", "",
          "- 돌리줌 1회(S21g 일곱 번째 액자), 더치 1회(S18g 永瀬 반격) — 생성기 자동 검사.",
          "- 말하는 화자 뒷모습은 정지 + 편집 카메라(S16b·S16m·S18q·S19b·S20g·S20p, 제11장 9). 녹음·전화·회상 대사는 전부 vo.",
          "- 소품의 인격화: 명부(S14m)·평가표(S14r·S14s)·인(S14t·S18r)·증명사진(S15g)·레코더(S17h)·반쪽 카드(S17i)·액자(S21f·S21g)·계약서(S22b~S22h)·카드(S24c·S24h).",
          "- 마지막 컷 S24j = 창업자 초상(얼굴 비노출, 대사 없음) — 2화 완결형 결정.", "",
          "## 3. 장면별 컷 순서", "", "| 장면 | 컷(사이즈·앵글·방식, 대사) |", "|---|---|"]
    by = collections.OrderedDict()
    for x in sb:
        by.setdefault(x["scene"], []).append(x)
    for sc, xs in by.items():
        md.append(f"| {sc} {SCENE_TITLE.get(sc, '')} | " + " → ".join(f"{x['id']}({x['size']}·{x['angle']}·{x['tier']}" + (f", {x['line']}" + (" vo" if x["vo"] else "") if x["line"] else "") + (f", {x['edit_fx']}" if x["edit_fx"] and x["edit_fx"] != "push" else "") + ")" for x in xs) + " |")
    open(os.path.join(PROD, "02_카메라앵글설계.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")


EMO_OK = {"angry": ("anger", "fury", "rage", "glare", "furious", "shout", "jaw", "fist", "growl", "hard", "cold"),
          "happy": ("smile", "smirk", "sneer", "laugh", "grin", "mock", "pleased", "satisf", "proud", "warm", "tease"),
          "sad": ("sob", "tear", "cry", "beg", "plea", "sad", "tremb", "break", "wet", "pale", "frighten", "stammer", "confess", "hoarse", "fear", "apolog", "sorry", "worr", "choked", "holding back"),
          "tonedown": ("cold", "quiet", "calm", "restrain", "low", "icy", "earnest", "silence", "gentle", "steady", "firm", "plain", "precise", "contempt", "narrow", "flat", "level", "whisper", "even"),
          "toneup": ("alarm", "panic", "shock", "excite", "fright", "urgent", "mock", "dismiss", "scoff", "bluster", "forced", "fake", "stammer", "breathless", "contemptuous", "bored", "smirk"),
          "whisper": ("whisper", "quiet", "low", "flat", "soft", "near whisper"),
          "normal": ()}
EMO_BAD = {"angry": ("sob", "gentle", "peaceful", "tender"), "happy": ("sob", "fury", "rage"), "sad": ("smirk", "sneer", "grin"),
           "tonedown": ("shout", "laugh", "scream"), "whisper": ("shout", "laugh", "scream")}
INTENDED = ("비웃", "즐기", "깔보", "억누른", "서늘", "냉정", "차갑", "예외", "눈물 섞인 웃음", "울먹", "속삭")


def emotion_table(sb, live):
    tone = tone_table()
    rows, warn = [], 0
    for x in sb:
        tag = x["line"]
        if not tag or tag not in tone or ROWS[tag]["type"] == "narration":
            continue
        emo, inten, tempo, memo = tone[tag]
        act = x["act"] or live.get(x["id"]) or ""
        seen = " ".join([x["subject"], act]).lower()
        ok = not EMO_OK.get(emo) or any(k in seen for k in EMO_OK[emo])
        bad = [k for k in EMO_BAD.get(emo, ()) if k in seen]
        intended = any(k in memo for k in INTENDED)
        state = "👂" if x["vo"] else ("✅" if ok and (not bad or intended) else "⚠️")
        warn += state == "⚠️"
        how = "립싱크" if x["tier"] == "omni" else ("목소리만" if x["vo"] else "정지(뒷모습)" if x["tier"] == "still" else "i2v")
        rows.append(f"| {state} | {x['id']} | {tag} | {how} | {emo} {inten} · {tempo} | {memo} | {x['subject'][:70]} | {act[:90]} |")
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_blackcard2_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않거나 부딪힘(연기 메모에 의도가 없으면 키프레임·동작 문장을 고친다). 👂 = 듣는 사람·소품 위 목소리(VO).", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 감정·세기·템포 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")


if __name__ == "__main__":
    main()
