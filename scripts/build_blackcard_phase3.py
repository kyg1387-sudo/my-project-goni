#!/usr/bin/env python3
"""『ブラックカード』(第1話, blackcard-ja) PHASE 3 샷 리스트 Lock 생성기 — build_hikikomori_phase3.py를 옮긴 것.

이 작품에서 달라진 것:
  · 후크 = S01(Lock 장면 01, 0:00~0:36)이 본편 장면이다(별도 H 장면 없음). 질문 카드(S01k)·타이틀(S02a)은 클립에 직접(제15장 12·20).
  · 1인칭 회고 내레이션(켄지)은 전부 VO — 자막 스타일 KenjiN(66px). 대사는 어깨 너머 3/4(제10장 1), 2.5초 이하·보조 인물(店員·運転手·声)은 VO(제12장 2).
  · 콜백 3회 「判子は――ここ」: S02d(柴田) → S03h(美咲) → S08g·S10i(켄지) 같은 손동작(한 손가락 두 번).
  · 정점 정적(bgm_silence) 6곳: 택시 승인·시계점 승인·辞令 봉투·「ただ、静かだった」·離婚届 찢기·시계 0:00(제19장 14·26).
  · 돌리줌 1회 = S12i(카드 문양 → 정문 청동 문양), 더치 2회 = S08m(柴田 붕괴 5°)·S09a(문 부딪힘 7°)(제8장 4).
  · 재미나이 기획안 적용 항목(08_기획안대조-재미나이.md): 형광 플리커·+1 stop·붉은 점멸·냉색 전환은 finalize 로컬(스토리보드 lighting 필드).
입력: productions/blackcard-ja/lock.json · 00_script_ja.md · 05_톤연출표.md · assets/auditions/blackcard-tts/lineNNN.mp3 · assets/portraits/blackcard-cast/cells/
출력: scripts/storyboard/blackcard.json · scripts/scenes/blackcard.json · scripts/audio/blackcard.json · subs/blackcard.ass ·
      assets/audio-overrides/blackcard/lineNNN.mp3 · productions/blackcard-ja/07_샷리스트.md · 02_카메라앵글설계.md · 16_감정일치표.md
사용법: python3 scripts/build_blackcard_phase3.py
"""
import collections, json, os, re, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "blackcard-ja")
SKIT = "blackcard"
TTS_DIR = "blackcard-tts"
FPS = 24; HARD = 1 / FPS; OMNI_MAX = 7.9; LEAD = 0.3; MIN_SHOT = 1.2; STILL_MAX = 6.5; I2V_MAX = 10.0

LOCK = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
for _x in LOCK["lines"]:
    _x["scene"] = "S" + _x["scene"]
ROWS = {x["tag"]: x for x in LOCK["lines"]}
AD1, AD2 = (a["at"] for a in LOCK["ads"])


def B(tag, off=0.0):
    return round(ROWS[tag]["start"] + off, 3)


def E(tag, off=0.0):
    return round(ROWS[tag]["end"] + off, 3)


C = "assets/portraits/blackcard-cast/cells/"
KEN_ID = ("Takahashi Kenji, a lean Japanese man aged 43, gaunt tired face with hollow cheeks, short black hair with a little grey at the temples, "
          "short dark stubble, a small healing graze above the LEFT eyebrow, no glasses, no earrings")
WHO = {
    "KENW": (KEN_ID + ", hair soaked flat and dripping, rain on the skin", C + "kenji-wet-front.png"),
    "KENG": (KEN_ID + ", hair dry and neatly combed", C + "kenji-suit-front.png"),
    "KENS": (KEN_ID + ", hair dry and neatly combed back", C + "kenji-suit-front.png"),
    "SHI": ("Shibata, a Japanese man aged 45, broad confident face, slicked-back black hair, thin RIMLESS glasses, clean-shaven, no earrings, "
            "no lapel pin, no mole", C + "shibata-front.png"),
    "MIS": ("Misaki, a Japanese woman aged 40, chin-length straight black bob with bangs, exactly ONE small mole on the LEFT cheek, no glasses, "
            "no earrings, light natural makeup", C + "misaki-front-noglasses.png"),
    "PRE": ("the company president, a Japanese man aged 72, swept-back white hair, round thin silver-rimmed glasses, clean-shaven, no earrings",
            C + "president-front.png"),
    "GUARD": ("two security guards in plain navy uniforms and caps seen only from behind, no badges, no text", None),
    "GUARDF": ("a middle-aged Japanese security guard, square plain face, short grey hair under a plain navy cap with no insignia, "
               "plain navy uniform with no badge, no earrings", None),
    "TAXI": ("a Tokyo taxi driver seen only as a dark cap and white-gloved hands from the rear seat, no face", None),
    "CLERK": ("a young boutique clerk in a plain black suit and white gloves, seen only from behind or as hands", None),
    "MGR": ("the restaurant manager, a Japanese man aged 55, neat silver-grey short hair, black vest, white shirt, black bow tie, no glasses, "
            "no earrings", None),
    "EXEC": ("three executives in plain dark suits seen only from behind or out of focus, no faces readable", None),
    "CHAUF": ("a chauffeur in a plain black suit, black chauffeur cap and white gloves, seen only from behind or as hands, no face", None),
    "SUB": ("three junior employees in plain dark office wear seen only from behind, heads bent over their desks", None),
}


def base(key):
    return "KEN" if key.startswith("KEN") else key


WARD = {
    "wet": "a rain-soaked crumpled light-grey business suit darkened by water, white shirt, loosened plain dark necktie, no wristwatch, no badge",
    "wetw": ("a rain-soaked crumpled light-grey business suit, white shirt, loosened plain dark necktie, a plain brushed-steel luxury wristwatch "
             "with a completely blank dial on the LEFT wrist, no badge"),
    "grey": "a plain slightly worn light-grey business suit, white shirt, plain dark necktie, no badge, no pin, no wristwatch",
    "suit": ("a perfectly tailored plain black slim suit, crisp white shirt open at the collar with NO necktie, a plain brushed-steel luxury "
             "wristwatch with a completely blank dial on the LEFT wrist, no badge, no pin"),
    "shi": "a plain navy double-breasted suit, white shirt, plain grey necktie, no lapel pin, no badge",
    "mis": "a plain beige trench coat over a white shirt, dark trousers, no brooch, no necklace",
    "pre": "a plain dark-grey three-piece suit, white shirt, plain navy necktie, no pin",
    "mgr": "a black waistcoat over a white shirt, black bow tie, no name tag",
    "chauf": "a plain black suit, black chauffeur cap, white cotton gloves",
    "guard": "a plain navy security uniform and cap with no insignia, no badge",
}
EXPR = {  # PHASE 2 Kill Gate 합격 셀(03_마스터에셋.md). 会長 하단 가운데·오른쪽 셀 금지 → 문장만
    ("KENW", "stare"): C + "kenji-wet-exp1.png", ("KENW", "anger"): C + "kenji-wet-exp2.png", ("KENW", "tense"): C + "kenji-wet-exp3.png",
    ("KENW", "back"): C + "kenji-wet-full-back.png",
    ("KENG", "cold"): C + "kenji-suit-exp1.png", ("KENG", "calm"): C + "kenji-suit-exp2.png", ("KENG", "hard"): C + "kenji-suit-exp3.png",
    ("KENG", "back"): C + "kenji-suit-full-back.png",
    ("KENS", "cold"): C + "kenji-suit-exp1.png", ("KENS", "calm"): C + "kenji-suit-exp2.png", ("KENS", "hard"): C + "kenji-suit-exp3.png",
    ("KENS", "back"): C + "kenji-suit-full-back.png",
    ("SHI", "smug"): C + "shibata-exp1.png", ("SHI", "shock"): C + "shibata-exp2.png", ("SHI", "bow"): C + "shibata-exp3.png",
    ("SHI", "back"): C + "shibata-full-back.png",
    ("MIS", "cold"): C + "misaki-exp1.png", ("MIS", "worry"): C + "misaki-exp2.png", ("MIS", "plead"): C + "misaki-exp3.png",
    ("MIS", "back"): C + "misaki-full-back.png",
    ("PRE", "calm"): C + "president-front.png", ("PRE", "back"): C + "president-full-back.png",
}
EXPR_TXT = {  # 표정 문장(제15장 2) — 50% 반영
    "stare": "a hollow fixed stare, lips pressed together, NOT smiling", "anger": "cold restrained anger, brows drawn, jaw clenched, NOT smiling",
    "tense": "tense, eyes wide, lips slightly parted, breath held, NOT smiling", "cold": "icy calm, lips closed, eyes level and unreadable",
    "calm": "quiet calm, eyes soft, a long slow breath", "hard": "hard cold eyes, a thin tightening of the mouth, NOT smiling",
    "smug": "a light contemptuous half-smile, relaxed brows", "shock": "pale and shocked, eyes wide, lips parted, NOT smiling",
    "bow": "head lowered, eyes down, lips trembling, NOT smiling", "worry": "frightened, brows drawn together, lips parted, NOT smiling",
    "plead": "pleading, eyes wet and red-rimmed, inner brows raised, NOT smiling", "coldsmile": "a faint cold smile at one corner of the mouth, eyes hard",
    "back": "seen from behind",
}
LOC = {
    "BACK1": C + "loc-backdoor-1.png", "BACK2": C + "loc-backdoor-2.png", "BACK3": C + "loc-backdoor-3.png",
    "MEET1": C + "loc-meeting-1.png", "MEET2": C + "loc-meeting-2.png", "MEET3": C + "loc-meeting-3.png", "MEET4": C + "loc-meeting-4.png",
    "HOME1": C + "loc-home-1.png", "HOME2": C + "loc-home-2.png", "HOME3": C + "loc-home-3.png", "HOME4": C + "loc-home-4.png",
    "TAXI1": C + "loc-taxi-1.png", "TAXI2": C + "loc-taxi-2.png", "TAXI4": C + "loc-taxi-4.png",
    "BOUT1": C + "loc-boutique-1.png", "BOUT3": C + "loc-boutique-3.png", "BOUT4": C + "loc-boutique-4.png",
    "HOTEL1": C + "loc-hotel-1.png", "HOTEL2": C + "loc-hotel-2.png", "HOTEL3": C + "loc-hotel-3.png", "HOTEL4": C + "loc-hotel-4.png",
    "REST1": C + "loc-restaurant-1.png", "REST2": C + "loc-restaurant-2.png", "REST3": C + "loc-restaurant-3.png", "REST4": C + "loc-restaurant-4.png",
    "OFF2": C + "loc-office-2.png", "OFF3": C + "loc-office-3.png", "OFF4": C + "loc-office-4.png",
    "CAR1": C + "loc-car-1.png", "CAR2": C + "loc-car-2.png", "CAR3": C + "loc-car-3.png", "CAR4": C + "loc-car-4.png",
    "P_CARD": C + "props-card-1.png", "P_CARD2": C + "props-card-2.png", "P_NOTE": C + "props-card-3.png", "P_TRAY": C + "props-card-4.png",
    "P_LETTER": C + "props-4.png", "P_ENV": C + "props-5.png", "P_WATCH": C + "props-6.png", "EMBLEM": C + "emblem.png",
}
LOC_TXT = {  # 장소 참조를 뺀 컷은 글로만(후광 테두리 방지, 제18장 9④)
    "RAIN_ALLEY": ("the rear service alley of a Roppongi office tower at night in heavy rain: wet black asphalt, a concrete loading dock, "
                   "a red neon sign out of frame reflecting on the puddles, cold blue ambient light, no signage, no readable text"),
    "STREET_N": ("a rain-soaked Tokyo street at night, wet asphalt reflecting red and blue neon, passing headlights as soft bokeh, "
                 "no readable signage"),
    "TOWER": ("a tall dark glass office tower at night in the rain, one red aviation warning light pulsing at the top, blue city haze, "
              "no logos, no readable text"),
    "CORRIDOR": ("a long modern office corridor with frosted glass partitions and cold fluorescent light, grey carpet, no signage, "
                 "no posters, no readable text"),
    "GINZA_ST": "a Ginza street at night in the rain, luxury shop windows glowing gold, red neon reflections on wet pavement, no readable signage",
}
PRESET = ("Photorealistic live-action Japanese noir drama, contemporary Tokyo (Reiwa era), Arri Alexa cinematic color grade, Kodak 35mm film grain, "
          "24fps, 16:9, low-key high-contrast lighting, restrained Japanese film mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, "
            "signage lettering, documents with writing, screens with text, printed labels, brand logos, watermarks, stamps with characters, "
            "symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, blood, gore, anime, 3d render, illustration, "
            "thick glossy gel tears, cartoon sweat drops, multiple tear streams on both cheeks, earrings on men, LED light strips, lens flare text")
PLAIN = ("All papers, cards, passbooks, forms, envelopes, phone screens, terminals, meters, clocks and monitors are completely blank "
         "(screens show only a soft plain glow); no letters, numbers or symbols anywhere in the frame.")
TEARS = ("Realistic tears as in a live-action film: reddened eye rims, glossy wet eyes catching the light, a small clear tear bead on the lower lashes, "
         "at most one thin translucent tear track on one cheek, a slightly reddened nose tip, matte natural skin; no glossy gel streams, no cartoon droplets.")
SWEAT = ("Realistic sweat as in a live-action film: a few tiny natural beads of perspiration on the forehead and temples, a faint natural sheen, "
         "one thin bead line near the temple; no large cartoon drops, no face-wide shine.")
RAINSKIN = "Real rain on the skin: fine water running in thin lines down the face, wet lashes, drops on the brow — not sweat, not oil, matte skin beneath."
WET_HOLD = " Eyes wet and glistening with tears welling on the lower lids but NOT running down — the tears stay pooled."
TEARS_FLOW = (" One clear tear slowly spills over the lower lid and runs down the cheek along its natural curve, catching the light; a slow blink, "
              "a trembling breath; only one tear line, thin and translucent.")
SWEAT_FLOW = " A thin bead of cold sweat slowly runs from the temple down toward the jaw; a shaky breath, a hard swallow."
NOSMILE = "NOT smiling at any moment: brows knotted, the corners of the mouth pulled down, chin trembling slightly. "
GLASSES = {"KENW": "Kenji wears no glasses.", "KENG": "Kenji wears no glasses.", "KENS": "Kenji wears no glasses.",
           "SHI": "Shibata wears thin RIMLESS glasses.", "MIS": "Misaki wears no glasses.", "PRE": "The president wears round thin silver-rimmed glasses."}
HANDS = {"KENW": "lean wet hands, no ring, no wristwatch", "KENG": "lean hands, no ring, no wristwatch",
         "KENS": "lean hands, no ring, a plain brushed-steel wristwatch with a blank dial on the LEFT wrist",
         "SHI": "a man's broad hands, a plain gold wedding band", "MIS": "a woman's slim hands, a plain gold wedding band",
         "PRE": "an old man's thin hands", "CLERK": "white-gloved hands", "CHAUF": "white-gloved hands", "TAXI": "white-gloved hands",
         "GUARD": "a security guard's hands"}
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, the face fills at least one third of the frame height",
    "ots": "50mm lens, f/2.0, over-the-shoulder three-quarter framing, the listener's blurred shoulder and back of the head in the near foreground edge, the speaker's face at least one third of the frame height",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds, the person's face at least one quarter of the frame height",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective",
}
LIGHT = {
    "rain_n": "night, heavy rain, low-key deep blue ambient light, a red neon glow out of frame reflecting on wet surfaces and skin, high contrast",
    "meet": "cold flat overhead fluorescent light 5600K with a faint green tint, grey window daylight, harsh shadows under the brows, a tense corporate mood",
    "home_n": "night, one bare cold fluorescent tube 5600K with a faint green tint, rain on the window, hard flat light, a cheap tired apartment",
    "taxi": "night inside a taxi, cold blue rain light through the windows, a green dashboard glow, passing neon sliding across the faces",
    "ginza": "warm gold key light from the showcases 3200K, a red neon rim light from the shop front, deep black shadows, luxurious",
    "street_n": "night, heavy rain, cold blue sodium ambient light, red neon reflections, a dark tower behind with one red pulsing light",
    "hotel_m": "early morning, warm 3200K tungsten lamps mixed with soft grey dawn light through sheer curtains, calm and expensive",
    "lobby": "morning, soft daylight through a tall glass entrance, bronze and dark stone surfaces, quiet",
    "rest": "noon, soft daylight from a floor-to-ceiling window over a white tablecloth, warm wood walls, a gentle warm table lamp, elegant",
    "rest_door": "the private room doorway: the corridor behind is dark warm wood, the figure half in shadow, the room beyond bright with window light",
    "office_n": "night, one cold white desk lamp as the only source, deep shadows, a faint red glow from an aviation warning light only on the window glass, high contrast",
    "car": "night in a luxury car rear seat, warm amber and magenta neon reflections sliding over black leather and skin, a soft reading light",
    "car_cold": "night in a luxury car rear seat, the neon reflections turned cold blue-white, a soft reading light, uneasy",
    "memory": "a clean bright morning in front of a glass office entrance, slightly desaturated like a memory, soft daylight",
    "macro": "a tight pool of light on the object, everything else falling into black",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "bird's-eye view straight down", "SIDE": "eye-level from the side or behind"}
SPK_KEY = {"高橋 健二": "KEN", "柴田": "SHI", "美咲": "MIS", "社長": "PRE"}


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, act="", vo=False, pin=None):
    """kind: d(OmniHuman 립싱크) / face(사람 i2v) / empty(무인 i2v) / estill(무인·합성 면 정지) / pstill(말하는 화자 뒷모습 정지 + 편집 카메라) /
    ins(손·소품 — motion 있으면 i2v, 없으면 정지) / reuse:<id> / card.  vo=True = 화자 화면 밖(듣는 사람·소품 위 목소리).
    who 항목 = "인물:의상". pin = 무대사 컷의 시작 시각 고정(초)."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc, subject=subject,
                line=line, fx=fx, motion=motion, expr=expr, act=act, vo=vo, pin=pin)


Kw, Kww, Kg, Ks = "KENW:wet", "KENW:wetw", "KENG:grey", "KENS:suit"
Sh, Mi, Pr, Mg, Ch, Gd = "SHI:shi", "MIS:mis", "PRE:pre", "MGR:mgr", "CHAUF:chauf", "GUARD:guard"
OB = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, keeps looking "
      "toward the other person at the same three-quarter angle, hands keep doing what they do in the first frame; no exaggerated motion, the same person throughout.")
HOLD = " Head stays at the same angle, never turns toward the camera; only body, hands and breath move. Mouth stays closed, lips still — this person is NOT speaking."
SEATED = " SEATED/FURNITURE LOCKED: seated on the chair pulled in to the table, thighs under the table edge, forearms on the table; the chair never passes through the body."
ONEHAND = " HANDS LOCKED: exactly ONE hand in the frame holding exactly ONE object, five clean fingers, seen from the side at hand height, the forearm continuing out of frame."
RAIN = " Rain keeps falling through the whole clip."

SHOTS = [
    # ── S01 후크(0:00~0:36): 빗속 뒷문 추방 → 카드 → 질문 카드. 0~3.5초 BGM 없음(드론+심장), 천둥 1.0초
    S("S01a", "S01", "estill", "ews", "rain_n", "LA", [], "BACK1", "Extreme low wide of the rear service exit of a Roppongi office tower at night in heavy rain: the open loading dock door, the lit guard booth, wet asphalt reflecting a red neon glow; EMPTY, nobody.", fx="push"),
    S("S01b", "S01", "face", "ws", "rain_n", "HA", [Kw, Gd], "BACK1", "High wide from the dock: two security guards seen from behind push Kenji out through the rear door into the rain; he stumbles one step onto the wet asphalt clutching a small plain cardboard box, hair already soaked.", line="L001",
      motion="The two guards each give one firm push on his shoulders; he stumbles one step forward and stops, hunched over the box; the guards stay turned away." + RAIN),
    S("S01c", "S01", "face", "cu", "rain_n", "HA", [Kw], None, "High close-up of Kenji's rain-soaked face lit by the red neon, eyes down at the wet asphalt (screen LEFT), jaw clenched, water running off his hair.", line="L002a", expr="stare",
      motion="Rain runs down his face; he blinks slowly; his jaw tightens; he never looks up or at the camera." + HOLD),
    S("S01d", "S01", "ins", "ecu", "rain_n", "EL", [Gd], "BACK3", "Side insert at the guard booth counter: ONE white-gloved hand holding a pair of steel scissors cuts a plain blank white plastic ID card in two with one snip; the second hand only holds the card edge below." + ONEHAND, line="L002b",
      motion="One snip: the scissors close and the card drops in two pieces onto the counter; nothing else moves."),
    S("S01e", "S01", "ins", "ecu", "rain_n", "HA", [], "BACK2", "High insert: a plain white envelope falling into a rain-filled gutter beside the kerb, red neon rippling on the water; no text on the envelope.", pin=E("L002b", -1.0),
      motion="The envelope hits the water, floats for a second and the current pulls it toward the drain grate; rain ripples the surface."),
    S("S01f", "S01", "face", "ews", "rain_n", "LA", [Kw], "BACK1", "Extreme low wide: Kenji standing alone in the pouring rain in the empty back alley, a dark silhouette against the red neon and the wet tower wall, the cardboard box at his feet, seen from behind.", line="L003", expr="back",
      motion="He stands still as the rain pours; his shoulders rise with one heavy breath; the neon flickers faintly; nothing else moves." + HOLD),
    S("S01g", "S01", "ins", "ecu", "macro", "HA", [], "BACK2", "Macro insert: a matte black card lying on the wet asphalt in a shallow puddle, red neon reflected across the water, raindrops striking the surface; the card is completely blank, no text.", line="L004",
      motion="Raindrops hit the puddle making small rings over the card; the red reflection shimmers; the card does not move."),
    S("S01h", "S01", "ins", "ecu", "rain_n", "EL", [Kw], "BACK2", "Side insert at ground level: ONE wet bare hand picks the black card up off the asphalt and turns it over, revealing a small engraved emblem on the back; the card is otherwise blank." + ONEHAND, line="L005",
      motion="The hand lifts the card and slowly turns it over once; water drips from the fingers; the emblem catches the red light."),
    S("S01i", "S01", "face", "cu", "rain_n", "LA", [Kw], None, "Low close-up: Kenji's wet face lit from below by the red neon reflection, eyes slowly lifting from the card in his hand toward the tower (screen RIGHT), a dangerous calm.", pin=B("L005", 3.0), expr="tense",
      motion="His eyes lift slowly from the card toward screen right; rain on his lashes; a slow blink; he never looks at the camera." + HOLD),
    S("S01j", "S01", "face", "cu", "rain_n", "EL", [Kw], None, "Close-up at eye level: Kenji's rain-streaked face, eyes narrowed with cold resolve toward the tower (screen RIGHT), red neon on one side of the face, cold blue on the other.", line="L006", expr="anger",
      motion="He breathes slowly; a drop of rain falls from his nose; his eyes stay fixed screen right; his mouth stays closed." + HOLD),
    S("S01k", "S01", "card", "cu", "rain_n", "EL", [], None, "Question card over the blurred last frame of S01j (no black): 「拾ったのは、カードだけじゃなかった。」", pin=E("L006", -0.9)),

    # ── S02 12층 유리 회의실(0:36~1:30): 타이틀 → 柴田 어깨 너머 → 판자 → 경비원 → 복도 뒷모습 → 빈 회의실
    S("S02a", "S02", "card", "ws", "meet", "EL", [], None, "Title card 「ブラックカード」 over the blurred last frame of S01k (no black). Corner caption 「その日の朝」 follows on S02b."),
    S("S02b", "S02", "d", "ots", "meet", "EL", [Sh, Kg], "MEET3", "Over Kenji's blurred shoulder (near LEFT foreground): Shibata seated across the white table at three-quarter angle, leaning back with a light contemptuous half-smile, one hand resting flat on a plain white document, speaking to Kenji.", line="L007a", expr="smug",
      act="Shibata speaks lightly, almost bored, a thin contemptuous smile, tapping the document once with two fingers; talking down to his old colleague across the table; at 高橋 a small lift of the chin." + SEATED + OB),
    S("S02c", "S02", "face", "cu", "meet", "HA", [Kg], "MEET1", "High close-up of Kenji seated, listening, eyes down on the document (screen LEFT), jaw tight, the fluorescent light flat on his face.", pin=E("L007a", -1.0), expr="cold",
      motion="He swallows; his eyes stay on the paper; a muscle in his jaw tightens; no head turn." + SEATED + HOLD),
    S("S02d", "S02", "d", "cu", "meet", "EL", [Sh], "MEET2", "Chest-up close-up of Shibata at three-quarter angle, pushing a small wooden seal (hanko) across the table with one finger toward Kenji (screen LEFT), then tapping the blank signature box of the document twice.", line="L007b", expr="smug",
      act="He says it flatly, pushes the hanko with one finger and taps the paper twice at ここ; eyes on Kenji screen LEFT; the smile never reaches the eyes." + SEATED + OB),
    S("S02e", "S02", "d", "cu", "meet", "LA", [Kg], "MEET2", "Low close-up: Kenji at three-quarter angle looking up at Shibata (screen RIGHT), face pale, eyes wet but not running, voice barely holding, both hands flat on the table.", line="L008", expr="hard",
      act="NOT smiling at any moment. Kenji speaks low and choked, holding back, brows drawn, eyes wet; answering Shibata directly, looking him in the eye." + SEATED + OB),
    S("S02f", "S02", "d", "ots", "meet", "LA", [Sh, Kg], "MEET3", "Over Kenji's blurred shoulder, low angle: Shibata leaning forward with his elbows on the table, a cold smile, speaking down to Kenji.", line="L009", expr="smug",
      act="He leans in and says it with a cold smirk, almost gently cruel, then sits back; talking to Kenji across the table; a small shrug at 評価." + SEATED + OB),
    S("S02g", "S02", "ins", "ecu", "meet", "HA", [Kg], "MEET4", "High side insert: Kenji's hand lifting the wooden hanko from the metal tray and pressing it onto the blank box of the white document; the grey suit sleeve continues out of frame." + ONEHAND, pin=E("L009", -0.8),
      motion="The hand presses the seal down firmly, holds for a moment, then lifts it away leaving a small red mark."),
    S("S02h", "S02", "d", "cu", "meet", "EL", ["GUARDF:guard"], "MEET1", "Chest-up close-up of a middle-aged security guard standing by the glass wall at three-quarter angle, cap on, holding up a plain blank white ID card in one hand, speaking in a flat polite tone to Kenji off-screen LEFT.", line="L010",
      act="He recites it politely and without any emotion, holding up the card, eyes on Kenji screen LEFT; a small formal nod at the end." + OB),
    S("S02i", "S02", "face", "ws", "meet", "SIDE", [Kg, Sh, "SUB"], "MEET1", "Side wide through the glass wall from the office floor: Kenji rising slowly from his chair inside the glass meeting room holding the document, Shibata still seated; in the near foreground the blurred backs of three employees at their desks pretending to work.", line="L011a",
      motion="Kenji stands up slowly and picks up the document; the foreground heads stay bent over their desks; nothing else moves." + HOLD),
    S("S02j", "S02", "ins", "ecu", "meet", "EL", [Kg], "MEET4", "Side insert: Kenji's hand sliding the stamped white document into a plain brown envelope on the table; paper and envelope blank." + ONEHAND, line="L011b",
      motion="The hand slides the paper into the envelope and presses the flap flat."),
    S("S02k", "S02", "face", "ms", "meet", "LA", [Sh], "MEET2", "Low medium: Shibata standing by the window with his back half turned to the camera, hands in his pockets, looking down at the city, not turning.", line="L012", expr="back",
      motion="He rocks slightly on his heels and looks down at the city; he does not turn around; the daylight shifts faintly." + HOLD),
    S("S02l", "S02", "face", "ws", "meet", "HA", [Kg], None, "High wide of a long office corridor: Kenji walking away from the camera carrying the small cardboard box, seen from behind, small in the frame, the fluorescent tubes cold.", line="L013", expr="back",
      motion="He walks slowly away down the corridor, shoulders down; the camera does not move; nobody else appears." + HOLD),
    S("S02m", "S02", "face", "ms", "meet", "SIDE", ["SUB"], "MEET1", "Through the glass: three employees at desks seen from behind, heads bent over blank glowing screens; one head glances a few degrees toward the meeting room, then back down.", line="L014",
      motion="One head turns a few degrees toward the glass and then back to the screen; fingers keep typing; nothing else moves." + HOLD),
    S("S02n", "S02", "estill", "ws", "meet", "EL", [], "MEET3", "Wide of the now-empty glass meeting room: the white table, the metal hanko tray, two chairs pushed back, a plain round wall clock with a blank white dial (hands composited); EMPTY.", line="L015", fx="push"),

    # ── S03 낡은 맨션 거실(1:30~2:28): 젖은 켄지 뒷모습 → 美咲 통장 → 離婚届 「判子は――ここ」 → 혼자 → 회상 재사용
    S("S03a", "S03", "face", "ms", "home_n", "SIDE", [Kw], "HOME3", "Medium from behind in the narrow entryway: Kenji standing in his soaked grey suit, water dripping onto the floor, a packed black suitcase waiting by the door; his face is not visible.", expr="back",
      motion="Water drips from his sleeves onto the floor; his shoulders rise and fall with one slow breath; he does not turn." + HOLD),
    S("S03b", "S03", "d", "ots", "home_n", "EL", [Mi, Kw], "HOME1", "Over Kenji's blurred wet shoulder (near RIGHT foreground): Misaki standing at the small kitchen table at three-quarter angle, holding an open bank passbook toward him, cold flat expression, under the bare fluorescent tube.", line="L016a", expr="cold",
      act="Misaki speaks with no warmth, businesslike, holding up the passbook and tilting it toward him at the number; eyes on Kenji screen RIGHT; no tears, no anger." + OB),
    S("S03c", "S03", "ins", "ecu", "home_n", "HA", [Mi], "HOME1", "High insert: the open passbook lying on the table under the hard fluorescent light, ONE slim finger pressing on the last printed row; the pages show only faint plain ruled rows, no characters (figures composited)." + ONEHAND, line="L016b", vo=True),
    S("S03d", "S03", "pstill", "cu", "home_n", "HA", [Kw], "HOME1", "High close-up from behind and above: the back of Kenji's soaked head and shoulders, water dripping, head bowed; his face and mouth are not visible.", line="L017", fx="handheld", expr="back"),
    S("S03e", "S03", "d", "cu", "home_n", "EL", [Mi], "HOME1", "Chest-up close-up of Misaki at three-quarter angle, cold, lips thin, the passbook lowered in one hand, speaking to Kenji screen RIGHT.", line="L018a", expr="cold",
      act="Flat and cold, each word placed; a tiny shake of the head at 無職; eyes steady on Kenji screen RIGHT." + OB),
    S("S03f", "S03", "ins", "ecu", "home_n", "EL", [Kw], "HOME1", "Side insert: Kenji's wet hand gripping the back of a cheap wooden chair, knuckles white, water dripping from the grey sleeve; no other hand." + ONEHAND, pin=E("L018a", -1.0),
      motion="The fingers tighten slowly on the chair back; a drop of water falls; a faint tremor."),
    S("S03g", "S03", "d", "ots", "home_n", "HA", [Mi, Kw], "HOME2", "Over Kenji's blurred wet shoulder (near LEFT), slightly high, under the green-tinted fluorescent tube: Misaki at three-quarter angle picking up a plain white form from the table, no emotion.", line="L018b", expr="cold",
      act="Businesslike and cold; she picks up the form while speaking, eyes down then up at him; no tears, no anger; talking to her husband." + OB),
    S("S03g2", "S03", "face", "cu", "home_n", "EL", [Kw], "HOME1", "Close-up of Kenji listening, wet hair plastered to the forehead, eyes on his wife (screen LEFT), lips pressed, the light flat and cold.", pin=E("L018b", -1.0), expr="stare",
      motion="He does not move; one slow blink; his throat moves with a swallow." + HOLD),
    S("S03h", "S03", "d", "ms", "home_n", "EL", [Mi, Kw], "HOME1", "Medium over Kenji's blurred shoulder (near RIGHT): Misaki laying the white divorce form flat on the table in front of him and pressing one finger on the empty RIGHT box; ONE red seal already in the LEFT box; the form otherwise blank (title composited).", line="L019", expr="cold",
      act="She lays the form down and taps the empty box twice at ここ, the same cadence as Shibata; eyes cold on Kenji screen RIGHT; no emotion." + OB),
    S("S03i", "S03", "estill", "ecu", "home_n", "OH", [], None, "Overhead insert: the divorce form on the cheap table under the fluorescent tube, ONE red seal impression in the LEFT box only, the RIGHT box EMPTY, a small wooden hanko beside it; the paper is otherwise blank (title and fields composited); no hands.", line="L020", fx="push"),
    S("S03j", "S03", "face", "ms", "home_n", "SIDE", [Mi], "HOME3", "Side medium by the front door: Misaki pulling the black suitcase handle up, trench coat on, not looking back; the door open to the dark corridor.", line="L021", expr="back",
      motion="She extends the suitcase handle, turns the suitcase and takes one step toward the door; she does not look back." + HOLD),
    S("S03k", "S03", "face", "cu", "home_n", "LA", [Kw], "HOME1", "Low close-up: Kenji standing alone in the kitchen, wet hair, staring down at the form on the table (screen LEFT), hollow eyes, the tube light harsh on his face.", line="L022", expr="stare",
      motion="His eyes stay on the table; a drop of water falls from his hair; his breathing is shallow; he never looks at the camera." + HOLD),
    S("S03l", "S03", "ins", "ecu", "home_n", "EL", [Kw], "HOME1", "Side insert: Kenji's wet fist on the table slowly clenching, knuckles white, a drop of water beside it on the laminate; the grey sleeve continues out of frame." + ONEHAND, line="L023",
      motion="The fist clenches slowly, trembling; the knuckles whiten; no other movement."),
    S("S03m", "S03", "face", "ws", "home_n", "HA", [Kw], "HOME4", "High wide: Kenji sitting on the floor with his back against the kitchen wall in the wet suit, knees up, the rain-streaked window above him, the apartment bare and cold.", line="L024", expr="stare",
      motion="He sits still; his chest rises slowly; rain streaks the window; the tube light flickers very faintly." + HOLD),
    S("S03n", "S03", "reuse:S01b", "ws", "rain_n", "HA", [], None, "Reuse of S01b (the guards pushing Kenji out into the rain) — the memory of the back door.", line="L025"),
    S("S03o", "S03", "reuse:S01g", "ecu", "macro", "HA", [], None, "Reuse of S01g (the black card in the puddle under red neon).", line="L026"),

    # ── S04 뒷문 카드 발견 → 택시(2:28~3:03): POV → 카드 앞뒤 → 경비실 등 돌림 → 택시 승인 「ピッ」 3초 정적
    S("S04a", "S04", "ins", "ecu", "rain_n", "LA", [], "BACK2", "Low insert at the kerb: the toe of a wet black leather shoe nudging the black card lying in the puddle, red neon on the water; no text.",
      motion="The shoe toe touches the card and stops; rain ripples the puddle."),
    S("S04b", "S04", "ins", "ecu", "rain_n", "EL", [Kw], "BACK2", "Side insert: ONE wet bare hand holding the black card up into the red neon light, the front completely blank — no name, no numbers, no text at all." + ONEHAND, line="L027a",
      motion="The hand tilts the card slowly in the light; raindrops hit it and run off."),
    S("S04c", "S04", "ins", "ecu", "macro", "HA", [Kw], "P_CARD", "Macro from above: the card turned over in the hand, the back showing ONE small engraved emblem (a tower inside a ring) catching the red light; no text." + ONEHAND, line="L027b",
      motion="The thumb rubs once across the emblem; the card tilts and the engraving catches the light."),
    S("S04d", "S04", "face", "cu", "rain_n", "EL", [Kw], "BACK3", "Close-up: Kenji looking across the rain toward the lit guard booth window (screen RIGHT), the card lowered in his hand, indecision on his wet face.", line="L028", expr="tense",
      motion="His eyes stay on the booth; he swallows; rain runs down his face; he does not look at the camera." + HOLD),
    S("S04e", "S04", "face", "ws", "rain_n", "LA", [Kw], "BACK3", "Low wide: the lit guard booth window at the back of the dock with a guard's dark silhouette inside; Kenji in the foreground seen from behind, turning his back on the booth and walking away toward screen LEFT.", line="L029", expr="back",
      motion="He turns away from the booth and takes two slow steps toward screen left, away from the camera; the silhouette inside the booth stays still; rain falls." + HOLD),
    S("S04f", "S04", "face", "ms", "street_n", "SIDE", [Kw], None, "Side medium on the rain-lit street: Kenji raising one arm toward approaching headlights, water streaming off his sleeve, the taxi's soft yellow light on his face.", expr="back",
      motion="He raises his arm; the headlights sweep across him; rain falls; he does not turn toward the camera." + HOLD),
    S("S04g", "S04", "face", "ms", "taxi", "SIDE", ["TAXI"], "TAXI1", "From the rear seat: the back of the taxi driver's cap and white-gloved hands on the wheel, rain streaming down the windshield, the green meter glow, wipers mid-sweep; no faces.", line="L030", vo=True,
      motion="The wipers sweep once; the green light flickers; the gloved hand turns the wheel slightly; rain streams on the glass."),
    S("S04h", "S04", "ins", "ecu", "taxi", "EL", [Kw], "TAXI1", "Side insert: ONE wet hand pressing the black card flat against a blank black payment terminal mounted on the seat back, a small green light beside the screen." + ONEHAND, pin=168.3,
      motion="The hand holds the card against the terminal and stays still; the small green light blinks once."),
    S("S04i", "S04", "face", "cu", "taxi", "HA", [Kw], "TAXI2", "High close-up from the front seat: Kenji in the rear seat staring at the terminal (screen LEFT, down), lips parted, cold rain light moving across his face.", line="L031a", vo=True, expr="tense",
      motion="His eyes widen slightly as the light changes; he exhales; passing neon slides across his face; he does not look at the camera." + HOLD),
    S("S04j", "S04", "estill", "ecu", "taxi", "EL", [], "TAXI1", "Insert: the taxi meter on the dashboard, a blank dark display (figures composited), a thin white receipt slip emerging below it; green glow; no hands.", line="L031b", vo=True, fx="push"),
    S("S04k", "S04", "face", "cu", "taxi", "EL", [Kw], "TAXI4", "Close-up: Kenji's face against the rain window in the rear seat, eyes closed, one hand pressed flat on his chest over the heart, neon passing over the glass.", line="L032", expr="tense",
      motion="His hand presses on his chest; his chest heaves; neon lights slide across the glass; his eyes stay closed." + HOLD),

    # ── S05 긴자 시계점(3:03~3:42): 입장 → 「あれを」 → 승인 「ピッ」 3초 정적 → 시계 → 나가며 상자 두고 감 → 1차 광고
    S("S05a", "S05", "face", "ws", "ginza", "EL", [Kw], "BOUT1", "Wide: the glass door of a Ginza watch boutique at night, red neon rim on the wet glass, the warm gold interior; Kenji in the soaked grey suit stepping in through the door seen from behind, leaving wet footprints.", expr="back",
      motion="He pushes the door and steps inside away from the camera; the door swings closed slowly behind him; the gold light spills on the wet floor." + HOLD),
    S("S05b", "S05", "face", "ms", "ginza", "HA", ["CLERK", Kw], "BOUT4", "High medium: the young clerk in a black suit seen from behind at the showcase in the foreground; beyond him Kenji's soaked figure standing at the red-lit showcase, water dripping on the marble; no faces readable.", line="L033", vo=True,
      motion="The clerk's shoulders stiffen; Kenji stands very still looking down at the showcase; water drips." + HOLD),
    S("S05c", "S05", "ins", "ecu", "ginza", "EL", [Kw], "BOUT3", "Side insert: Kenji's wet hand pointing one finger at a steel watch on a dark velvet cushion inside the glass showcase, red light on the glass; the dial is completely blank." + ONEHAND, line="L034", vo=True,
      motion="The finger taps the glass once and stays; the reflection shifts."),
    S("S05d", "S05", "face", "cu", "ginza", "LA", [Kw], "BOUT4", "Low close-up: Kenji's face lit gold from below by the showcase, a red neon rim on his wet hair, eyes on the watch (screen LEFT, down), unnervingly calm.", line="L035", vo=True, expr="stare",
      motion="He does not blink for a moment, then blinks slowly; the red reflection shifts on his cheek; he does not look at the camera." + HOLD),
    S("S05e", "S05", "ins", "ecu", "ginza", "HA", [Kw, "CLERK"], "P_CARD", "High insert on the marble counter: ONE wet bare hand laying the black card down; beside it a pair of white-gloved hands holding a blank receipt pad; no faces; the card blank. HANDS LOCKED: exactly one bare hand and two white-gloved hands, one card.", line="L036", vo=True,
      motion="The bare hand sets the card on the marble and withdraws; the gloved hands stay still."),
    S("S05f", "S05", "ins", "ecu", "ginza", "EL", ["CLERK"], "BOUT4", "Side insert: a white-gloved hand holding the black card against a blank payment terminal on the counter, a small green light; gold light; nothing else." + ONEHAND, pin=E("L036", 0.6),
      motion="The green light blinks once; nothing else moves for the whole clip."),
    S("S05g", "S05", "face", "cu", "ginza", "EL", [Kw], "BOUT1", "Close-up: Kenji's face in the silence, eyes on the terminal (screen RIGHT, down), a drop of water on his temple; then the faintest change in his eyes.", line="L037", vo=True, expr="tense",
      motion="Nothing moves for a second; then his eyes change, a slow blink, a breath out through the nose; the ceiling light on his face brightens slightly." + HOLD),
    S("S05h", "S05", "ins", "ecu", "ginza", "EL", [Kww, "CLERK"], "P_WATCH", "Side insert: the steel watch being closed on Kenji's wet LEFT wrist by white-gloved hands, the blank dial catching gold light; the grey wet sleeve pushed back; no faces. HANDS LOCKED: two white-gloved hands of the clerk, one bare wrist of Kenji, one watch.", line="L038",
      motion="The gloved hands close the clasp with a small click; the watch catches the light; the wrist turns slightly."),
    S("S05i", "S05", "face", "cu", "ginza", "LA", [Kww], "BOUT1", "Low close-up: Kenji's face under the brightening ceiling light, a faint cold smile forming at one corner of the mouth, eyes hard, looking toward the door (screen RIGHT).", pin=B("L038", 4.3), expr="coldsmile",
      motion="The corner of his mouth lifts slightly; his eyes stay hard on screen right; the light on his face brightens; a slow blink." + HOLD),
    S("S05j", "S05", "face", "ws", "ginza", "EL", [Kww, "CLERK"], "BOUT1", "Wide: Kenji walking toward the glass door seen from behind, the small dark watch box left behind on the marble counter, the clerk bowing deeply in the background with his face hidden.", line="L039", expr="back",
      motion="He walks steadily toward the door away from the camera; the clerk stays bowed; the box stays on the counter; nothing else." + HOLD),
    S("S05k", "S05", "face", "cu", "street_n", "EL", [Kww], None, "Close-up outside in the rain under red neon: Kenji's face alive, eyes narrowed with a cold thrill toward screen RIGHT, his LEFT wrist raised into the frame, rain bouncing off the steel watch.", line="L040", expr="anger",
      motion="He turns the wrist slowly; rain hits the watch; his eyes narrow; he does not look at the camera." + HOLD),
    S("S05l", "S05", "face", "ews", "street_n", "LA", [Kww], None, "Extreme low wide of the Ginza street at night in the rain, gold shop windows and red neon reflected on the wet pavement; Kenji a small dark figure walking away from the camera.", pin=AD1, expr="back",
      motion="He walks slowly away; rain falls; the neon reflections shimmer; nobody else appears." + HOLD),

    # ── S06 빗속의 비통지 전화(3:42~4:22): BGM 없음, 빗소리만. 声는 전부 VO, 켄지 L042·L046만 립싱크
    S("S06a", "S06", "estill", "ecu", "street_n", "EL", [Kww], None, "Insert: a smartphone buzzing in Kenji's wet hand, the screen a blank dark glow with no text (caller display composited), rain on the glass; one hand.", fx="push"),
    S("S06b", "S06", "face", "cu", "street_n", "EL", [Kww], None, "Close-up: Kenji holding the phone to his ear in the rain, eyes narrowing, looking into the dark toward screen LEFT, red neon on one cheek.", line="L041", vo=True, expr="stare",
      motion="He listens; his eyes narrow; rain runs down his face; his mouth stays closed." + HOLD),
    S("S06c", "S06", "d", "cu", "street_n", "LA", [Kww], None, "Low close-up: Kenji with the phone pressed to his ear, speaking low and wary into it, brows drawn, rain on his face, the tower dark behind.", line="L042", expr="anger",
      act="Low, wary, almost a growl; eyes darting toward screen LEFT; speaking into the phone; NOT smiling." + OB),
    S("S06d", "S06", "ins", "ecu", "street_n", "HA", [Kww], None, "High insert: raindrops striking the blank steel watch dial on Kenji's LEFT wrist, the knuckles of the hand holding the phone just in frame. HANDS LOCKED: one wrist, one watch.", line="L043a", vo=True,
      motion="Rain hits the dial and beads on the steel; the wrist turns slightly."),
    S("S06e", "S06", "face", "ws", "street_n", "LA", [Kww], None, "Low wide: Kenji small on the rain-soaked sidewalk with the phone at his ear, the dark office tower looming behind him, one red aviation light pulsing at its top.", line="L043b", vo=True, expr="back",
      motion="He stands still with the phone; rain falls; the red light at the top pulses slowly; nobody else." + HOLD),
    S("S06f", "S06", "pstill", "ecu", "street_n", "SIDE", [Kww], None, "Extreme close-up from behind: the phone pressed to Kenji's ear, wet hair, the jaw line; his mouth is not visible.", line="L044", fx="handheld", expr="back"),
    S("S06g", "S06", "face", "cu", "street_n", "HA", [Kww], None, "High close-up: Kenji's face, eyes closing slowly as rain streams over it, the phone still at his ear; a decision forming.", line="L045", vo=True, expr="tense",
      motion="His eyes close for two seconds and open again; rain runs down; his mouth stays closed." + HOLD),
    S("S06h", "S06", "d", "ms", "street_n", "EL", [Kww], None, "Medium at three-quarter angle: Kenji with the phone, lifting his eyes toward the tower (screen RIGHT) as he makes his demand, rain on his shoulders, the steel watch visible on the phone hand's wrist.", line="L046", expr="hard",
      act="He speaks slowly and deliberately, each word a decision, eyes lifting to the tower; a cold steadiness; a small nod at 全部; NOT smiling." + OB),
    S("S06i", "S06", "estill", "ecu", "street_n", "EL", [Kww], None, "Insert: the phone screen going dark in his wet hand, rain beading on the glass; no text; one hand.", line="L047", vo=True, fx="push"),
    S("S06j", "S06", "face", "ws", "street_n", "HA", [Kww], None, "High wide from behind: Kenji walking away down the rain-lit street toward the tower, small in the frame, the red light pulsing above.", line="L048a", expr="back",
      motion="He walks slowly away from the camera; rain falls; the red light pulses; nobody else appears." + HOLD),
    S("S06k", "S06", "face", "cu", "street_n", "LA", [Kww], None, "Low close-up: Kenji's rain-streaked face, eyes fixed up at the tower (screen RIGHT, up), a slow blink, the faintest hard smile.", line="L048b", expr="anger",
      motion="A slow blink; the corner of the mouth tightens; rain runs down; he never looks at the camera." + HOLD),

    # ── S07 호텔 아침 → 레스토랑 VIP룸(4:22~5:30): 정장과 메모 → 엘리베이터 → 로비 문양(복선) → 상석 → 柴田 정지 → 「座れ」
    S("S07a", "S07", "estill", "ws", "hotel_m", "EL", [], "HOTEL1", "Wide of a quiet luxury hotel room at dawn: grey light through sheer curtains, a warm bedside lamp, the crumpled wet grey suit thrown over a chair; EMPTY, nobody.", fx="push"),
    S("S07b", "S07", "ins", "ecu", "hotel_m", "EL", [Ks], "HOTEL1", "Side insert: ONE bare hand pressing down the brass lever handle of the hotel room door from inside; the forearm continues out of frame." + ONEHAND,
      motion="The hand presses the lever down and the door begins to open; soft corridor light enters."),
    S("S07c", "S07", "ins", "ecu", "hotel_m", "EL", [], "HOTEL1", "Insert: a tailored black suit on a wooden hanger hooked on the outside of the hotel room door, a small plain white card tucked into the breast pocket; no text; no people.", line="L049",
      motion="The sleeve sways very slightly in the corridor air; nothing else moves."),
    S("S07d", "S07", "estill", "ecu", "hotel_m", "HA", [Ks], "P_NOTE", "High insert: the small white card unfolded in Kenji's hand under the warm lamp — completely blank (handwritten note composited); the black suit sleeve at the frame edge; one hand.", line="L050", fx="push"),
    S("S07e", "S07", "ins", "ecu", "hotel_m", "EL", [Ks], "HOTEL1", "Insert: Kenji's hands buttoning the single button of the black suit jacket over the crisp white shirt, the steel watch on the left wrist; no face. HANDS LOCKED: two hands of one man, one button.", line="L051",
      motion="The fingers close the button and smooth the lapel once."),
    S("S07f", "S07", "estill", "ecu", "hotel_m", "LA", [], "HOTEL2", "Low insert: the brushed-steel elevator doors closing, the floor indicator a blank dark panel; no people.", fx="push"),
    S("S07g", "S07", "estill", "ecu", "hotel_m", "HA", [Ks], "HOTEL1", "High insert: a tablet lying on the room desk showing a blank light-grey news page (headline composited), Kenji's hand resting beside it; one hand.", line="L052", fx="push"),
    S("S07g2", "S07", "face", "cu", "hotel_m", "EL", [Ks], "HOTEL1", "Close-up: Kenji in the black suit reading the tablet (screen LEFT, down), the warm lamp on one side of his face, no expression at all.", pin=B("L052", 3.3), expr="cold",
      motion="His eyes move along one line of text and stop; one slow blink; nothing else." + HOLD),
    S("S07h", "S07", "face", "cu", "hotel_m", "LA", [Ks], "HOTEL2", "Low close-up inside the elevator: Kenji in the black suit, the steel watch, eyes forward on the doors (screen RIGHT), composed, the brushed-steel wall behind.", line="L053", expr="cold",
      motion="The elevator light moves slowly over his face; a slow blink; his eyes stay on screen right." + HOLD),
    S("S07i", "S07", "estill", "ws", "lobby", "LA", [], "HOTEL3", "Low wide of the tower's glass entrance in the morning, the bronze emblem (a tower inside a ring) mounted above the doors; EMPTY, nobody.", fx="push"),
    S("S07j", "S07", "face", "ws", "rest", "SIDE", [Ks, Mg], "REST4", "Wide: the manager in a black waistcoat leading Kenji down the dark wood-panelled corridor toward the private room, both seen from behind; warm light at the far door.", expr="back",
      motion="They walk slowly away from the camera toward the lit door; neither turns around." + HOLD),
    S("S07k", "S07", "estill", "ws", "rest", "EL", [], "REST1", "Wide of the empty private dining room at noon: the long white table set for eight, leather chairs, the Tokyo skyline through the window; EMPTY, nobody.", fx="push"),
    S("S07l", "S07", "face", "ms", "rest", "SIDE", [Ks], "REST2", "Medium from the side: Kenji seated at the head of the long table in the leather chair, hands folded on the white cloth, looking out at the skyline (screen LEFT), the window light on him.", expr="calm",
      motion="He breathes slowly; his thumb moves once over the steel watch; the light shifts faintly; he does not turn." + SEATED + HOLD),
    S("S07m", "S07", "face", "ws", "rest", "EL", [Mg, Ks], "REST1", "Wide from the doorway: the manager bowing deeply beside the table with his head down and face hidden; Kenji seated at the far head of the table, turning his head slightly toward him.", line="L054", vo=True,
      motion="The manager holds the deep bow; Kenji turns his head a few degrees toward him; nothing else moves." + HOLD),
    S("S07n", "S07", "d", "ms", "rest_door", "EL", [Sh], "REST4", "Medium: Shibata stopping dead in the doorway of the private room, mouth half open, a black briefcase in one hand, eyes on Kenji (screen LEFT); half of his face in the shadow of the corridor, the room bright beyond.", line="L055", expr="shock",
      act="He stammers, shocked, the voice breaking up, a nervous half-laugh that dies; eyes fixed on Kenji screen LEFT; NOT smiling." + OB),
    S("S07o", "S07", "face", "cu", "rest", "EL", [Ks], "REST2", "Close-up: Kenji seated, calm, not turning his head toward the door, lifting a glass of water slowly; eyes on screen RIGHT.", pin=E("L055", -1.0), expr="cold",
      motion="He lifts the glass, sips, sets it down; his eyes never leave screen right; no smile." + SEATED + HOLD),
    S("S07p", "S07", "d", "cu", "rest", "EL", [Mg], "REST1", "Chest-up close-up of the restaurant manager at three-quarter angle, one open hand extended politely toward the head of the table, speaking to Shibata (screen RIGHT) with a courteous composed expression.", line="L056",
      act="Polite, courteous, firm; a small gesture of the open hand toward the owner; talking to Shibata; a slight bow of the head at the end." + OB),
    S("S07q", "S07", "face", "ms", "rest", "EL", [Pr, "EXEC"], "REST1", "Medium: the white-haired president entering behind Shibata with executives behind him, stopping as his phone buzzes in his hand, looking down at the blank glowing screen, eyebrows rising.", pin=E("L056", 0.1), expr="calm",
      motion="He looks down at the phone; his eyebrows rise slowly; the executives behind him stop; nobody looks at the camera." + HOLD),
    S("S07r", "S07", "face", "cu", "rest", "EL", [Sh], "REST1", "Close-up: Shibata turning his head toward the president (screen LEFT), the colour draining from his face, a bead of sweat at the temple.", line="L057", vo=True, expr="shock",
      motion="His head turns about 15 degrees toward screen left; he swallows; a bead of sweat runs; NOT smiling." + HOLD),
    S("S07s", "S07", "d", "ots", "rest", "EL", [Ks, Sh], "REST1", "Over Shibata's blurred shoulder (near RIGHT foreground): Kenji at the head of the table, leaning back in the leather chair, speaking quietly, one hand resting on the cloth beside the water glass.", line="L058a", expr="cold",
      act="Quiet, level, almost polite, the cruelty in the calm; eyes on Shibata screen RIGHT; at 柴田 a tiny tilt of the head." + SEATED + OB),
    S("S07t", "S07", "ins", "ecu", "rest", "HA", [Ks], "REST2", "High insert: Kenji's hand on the white cloth pointing one finger at the empty leather chair at the near side of the table; the black sleeve, the steel watch." + ONEHAND, line="L058b", vo=True,
      motion="The finger points once and holds; nothing else moves."),

    # ── S08 辞令 봉투(5:30~6:51): 봉투 슬라이드(정적) → 콜백 립싱크 → 柴田 붕괴(더치 5°) → 「ただ、静かだった」(정적) → 예고 카드 → 2차 광고
    S("S08a", "S08", "ins", "ecu", "rest", "OH", [Ks], "REST3", "Overhead insert: a plain white envelope sliding across the white tablecloth from Kenji's hand toward the far side; ONE hand, the black sleeve, the steel watch; no text on the envelope." + ONEHAND,
      motion="The envelope slides across the cloth and stops; the hand withdraws out of frame."),
    S("S08b", "S08", "face", "ms", "rest", "HA", [Sh], "REST2", "High medium: Shibata now seated across the table, staring down at the envelope in front of him (screen LEFT, down), both hands flat on the cloth, sweat at the temple.", expr="shock",
      motion="He stares at the envelope; a swallow; his fingers twitch on the cloth; a bead of sweat; NOT smiling." + SEATED + HOLD),
    S("S08c", "S08", "face", "cu", "rest", "LA", [Ks], "REST1", "Low close-up: Kenji with his elbows on the table and fingers laced, waiting, cold calm, eyes on Shibata (screen RIGHT).", expr="cold",
      motion="He waits; one slow blink; his thumbs move once against each other." + SEATED + HOLD),
    S("S08d", "S08", "d", "ots", "rest", "EL", [Ks, Sh], "REST1", "Over Shibata's blurred shoulder (near LEFT foreground): Kenji at three-quarter angle speaking the same words with a quiet, almost gentle cruelty, one hand slowly turning the water glass on the cloth.", line="L059", expr="cold",
      act="He repeats Shibata's own words slowly, softly, with a faint cold smile only at the very end; eyes on Shibata screen LEFT; the glass turns once." + SEATED + OB),
    S("S08e", "S08", "d", "cu", "rest", "EL", [Sh], "REST2", "Chest-up close-up of Shibata at three-quarter angle, pleading, face pale and sweating, glasses slipping, hands gripping the table edge, eyes on Kenji (screen RIGHT).", line="L060", expr="shock",
      act="Pleading, voice cracking, trying to laugh it off and failing; NOT smiling; speaking to Kenji screen RIGHT; a hard swallow at 同期だろ." + SEATED + OB),
    S("S08f", "S08", "d", "ms", "rest", "LA", [Ks], "REST1", "Low medium: Kenji leaning forward on the table toward Shibata (screen LEFT), speaking the next line with ice, the Tokyo skyline bright behind him.", line="L061", expr="hard",
      act="Cold and exact, leaning in, a pause before 俺の評価が下がる; eyes locked on Shibata screen LEFT; NOT smiling." + SEATED + OB),
    S("S08g", "S08", "ins", "ecu", "rest", "HA", [Ks], "REST3", "High insert: Kenji's finger tapping twice on the blank signature box of a white document laid in front of Shibata, a wooden hanko beside it on the cloth; the black sleeve, the steel watch; the paper blank (title composited)." + ONEHAND, line="L062", vo=True,
      motion="The finger taps twice and stays on the box; nothing else moves."),
    S("S08h", "S08", "face", "cu", "rest", "HA", [Sh], "REST2", "High close-up: Shibata's eyes dropping to the document, his lips trembling, a drop of sweat falling from his temple toward the paper.", expr="bow",
      motion="His eyes drop; the lips tremble; a thin bead of sweat runs down from the temple; NOT smiling." + HOLD),
    S("S08i", "S08", "ins", "ecu", "rest", "EL", [Sh], "REST3", "Side insert: Shibata's trembling hand hovering over the wooden hanko on the white cloth, then picking it up; the navy sleeve; one hand." + ONEHAND,
      motion="The hand hovers, trembling, then closes around the seal and lifts it."),
    S("S08j", "S08", "face", "ws", "rest", "HA", [Ks, Sh, Pr, "EXEC"], "REST1", "High wide of the private room: Shibata hunched over the document at the near side of the table, Kenji upright at the head of the table, the president and three executives standing frozen along the wood wall; nobody moves.", line="L063",
      motion="Shibata's shoulders shake slightly as he presses the seal; nobody else moves; the window light is still." + SEATED + HOLD),
    S("S08k", "S08", "ins", "ecu", "rest", "EL", [Ks], "P_WATCH", "Side insert: the brushed-steel watch on Kenji's LEFT wrist resting on the white cloth, catching the window light, the dial completely blank; the black sleeve." + ONEHAND, line="L064",
      motion="The wrist turns slightly; light glints across the steel."),
    S("S08l", "S08", "ins", "ecu", "rest", "HA", [Sh], "REST3", "High insert: the single white sheet on the cloth with a fresh red seal impression in the lower box, Shibata's hand withdrawing from it; the paper otherwise blank (title composited); one hand." + ONEHAND, line="L065",
      motion="The hand withdraws slowly out of frame; the paper lies still."),
    S("S08m", "S08", "face", "ms", "rest", "SIDE", [Sh], "REST2", "Medium from the side: Shibata slumping back in the leather chair, the chair tilting back on its rear legs, his head falling back, arms hanging limp — still in the chair, NOT standing, NOT on the floor.", line="L066", fx="dutch5", expr="bow",
      motion="He slumps back; the chair tilts back and rocks; his head drops back; his arms hang; he stays in the chair." + HOLD),
    S("S08n", "S08", "face", "ws", "rest", "EL", [Ks], "REST1", "Wide: Kenji alone in sharp focus at the head of the long white table, very still, the skyline bright behind him, the room silent; the other chairs out of focus.", line="L067", expr="calm",
      motion="He is very still; one slow breath; nothing else moves in the room." + SEATED + HOLD),
    S("S08o", "S08", "ins", "ecu", "rest", "EL", [], "REST3", "Insert: an empty wine glass on the white cloth, a single clear drop sliding down the inside, the window light through the glass; no hands, no people.", pin=E("L067", 0.3),
      motion="The drop slides slowly down the inside of the glass; nothing else moves."),
    S("S08p", "S08", "face", "ms", "rest", "SIDE", [Pr, "EXEC"], "REST1", "Side medium: the president and two executives standing stiff along the wood wall, eyes on the table, faces frozen; nobody moves.", line="L068", expr="calm", fx="pan",
      motion="They do not move; one executive swallows; the president's hand tightens on his phone." + HOLD),
    S("S08q", "S08", "face", "cu", "rest", "EL", [Ks], "REST1", "Close-up: Kenji's face at three-quarter angle, eyes closed for a moment, then open, calm — a man hearing silence for the first time in fifteen years.", line="L069", expr="calm",
      motion="Eyes close, open; a long slow breath out; the faintest release in the brow; he does not look at the camera." + HOLD),
    S("S08r", "S08", "ins", "ecu", "rest", "EL", [Ks], "P_CARD", "Side insert: Kenji's hand sliding the black card into the inside breast pocket of the black jacket; one hand, one card; no text." + ONEHAND,
      motion="The hand slides the card into the pocket and smooths the lapel."),
    S("S08s", "S08", "face", "ms", "rest", "LA", [Ks], "REST4", "Low medium: Kenji walking away down the dark wood corridor from the private room, seen from behind, the far door bright; nobody else.", line="L070", expr="back",
      motion="He walks steadily away from the camera; the light at the far door grows on his shoulders." + HOLD),
    S("S08t", "S08", "estill", "ws", "office_n", "EL", [], "OFF3", "Wide of the dark former president's office at night: the glass wall with the city below, a single cold white desk lamp on the glass desk, the door at the right edge closed; EMPTY, nobody.", line="L071", fx="push"),
    S("S08u", "S08", "card", "ws", "office_n", "EL", [], None, "Preview card 「この後――妻が、ドアを叩き壊す」 over the blurred frame of S08t (no black), then the ad point.", pin=E("L071", 0.2)),

    # ── S09 구 사장실, 美咲 입장(6:51~7:18): 문 부딪힘(더치 7°) → 美咲 립싱크 → 켄지 창가 뒷모습 → 리버스숏 → 켄지 「ニュースは、早いな」
    S("S09a", "S09", "ins", "ecu", "office_n", "LA", [Mi], "OFF4", "Low insert: the heavy office door flung open, hitting the wall, ONE slim hand still on the lever handle, the beige trench sleeve; cold lamp light from inside." + ONEHAND, fx="dutch7",
      motion="The door swings open hard and hits the wall, bouncing back slightly; the hand stays on the handle."),
    S("S09b", "S09", "d", "ms", "office_n", "EL", [Mi], "OFF4", "Medium in the doorway: Misaki in her rain-wet trench coat, holding her phone up in one hand (a blank glowing screen — news composited), face white, speaking breathlessly toward Kenji (screen LEFT).", line="L072", expr="worry",
      act="Breathless, stunned, the voice shaking between disbelief and hope; eyes on Kenji screen LEFT; holding the phone up; NOT smiling." + OB),
    S("S09c", "S09", "pstill", "ms", "office_n", "SIDE", [Ks], "OFF3", "Medium from behind: Kenji standing at the glass wall with his back to the room, hands in his pockets, the city below, a faint red glow on the glass; his face is not visible.", line="L073", fx="push", expr="back"),
    S("S09d", "S09", "d", "ots", "office_n", "EL", [Mi, Ks], "OFF2", "Over Kenji's blurred shoulder (near RIGHT foreground, he has turned to face her): Misaki stepping closer under the cold white desk lamp, pleading, clutching her coat, tears welling, speaking fast.", line="L074", expr="plead",
      act="Pleading, fast, the words tumbling, voice breaking; NOT smiling; eyes wet on Kenji; one hand reaching slightly toward him." + OB),
    S("S09e", "S09", "face", "cu", "office_n", "LA", [Ks], "OFF3", "Low close-up: Kenji now seated behind the glass desk, half lit by the lamp, face unmoved, eyes on her (screen RIGHT), the red glow faint on the window behind.", pin=B("L074", 6.3), expr="cold",
      motion="Unmoving; one slow blink; the red light pulses faintly on his cheek; his mouth stays closed." + SEATED + HOLD),
    S("S09f", "S09", "d", "cu", "office_n", "EL", [Ks], "OFF3", "Chest-up close-up of Kenji seated behind the desk at three-quarter angle, fingertips together, quoting her words back in a flat quiet voice, eyes on Misaki (screen RIGHT).", line="L075a", expr="cold",
      act="Flat, quiet, each word placed like a stone; a faint tilt of the head; eyes on Misaki screen RIGHT; no anger in the voice." + SEATED + OB),
    S("S09g", "S09", "face", "cu", "office_n", "HA", [Mi], "OFF2", "High close-up: Misaki's face as the words land, lips parting, one tear spilling, the lamp light hard on her white skin.", line="L075b", vo=True, expr="plead",
      motion="A tear spills and runs down one cheek; her lips tremble and press together; NOT smiling; she does not look at the camera." + HOLD),

    # ── S10 증거 사진과 찢어지는 離婚届(7:18~8:24): 사진 탑다운 → 폴더 → 찢기(정적) → 세 번째 「判子は、ここ」 → 무너짐 → 창가
    S("S10a", "S10", "estill", "ecu", "office_n", "OH", [], "OFF3", "Overhead insert: a brown envelope tipped over on the glass desk under the lamp, several photographs spilled out across the desk — each photo a blank pale rectangle (contents composited); no hands, no people.", fx="push"),
    S("S10b", "S10", "estill", "ecu", "office_n", "EL", [Mi], None, "Side insert: Misaki's slim hand lifting one photograph from the desk (a blank pale rectangle — composited), the beige sleeve; one hand, one photo.", line="L076", vo=True, fx="handheld"),
    S("S10c", "S10", "d", "ots", "office_n", "EL", [Ks, Mi], "OFF3", "Over Misaki's blurred shoulder (near LEFT foreground): Kenji seated behind the glass desk under the lamp, sliding a thin plain folder across the desk toward her, speaking evenly.", line="L077a", expr="cold",
      act="Even, businesslike, no anger in the voice — which makes it colder; slides the folder across; eyes on her screen LEFT; NOT smiling." + SEATED + OB),
    S("S10d", "S10", "ins", "ecu", "office_n", "HA", [Mi], "OFF3", "High insert: Misaki's two hands gripping the edge of the glass desk, knuckles white, the beige sleeves; no objects; no face. HANDS LOCKED: two hands of one woman, nothing held.", line="L077b", vo=True,
      motion="Her fingers tighten on the desk edge; a tremor runs through the hands."),
    S("S10e", "S10", "d", "cu", "office_n", "EL", [Mi], "OFF2", "Chest-up close-up of Misaki leaning over the desk toward him, begging, a thin tear track on one cheek, one hand reaching across toward his, eyes on Kenji (screen RIGHT).", line="L078", expr="plead",
      act="Begging, the voice breaking, reaching her hand across the desk; NOT smiling; eyes wet on Kenji screen RIGHT; a catch of breath at 一度だけ." + OB),
    S("S10f", "S10", "d", "cu", "office_n", "LA", [Ks], "OFF3", "Low close-up of Kenji seated, very quiet, almost a whisper, lifting the white divorce form from the desk between two fingers — ONE red seal in the LEFT box, the RIGHT box empty, the paper otherwise blank (title composited).", line="L079", expr="cold",
      act="Almost a whisper, flat, quoting her; lifts the paper slowly; eyes on her screen RIGHT; NOT smiling." + SEATED + OB),
    S("S10g", "S10", "ins", "ecu", "office_n", "EL", [Ks], "OFF3", "Side insert at desk height: Kenji's two hands tearing the single white divorce form straight down the middle; HANDS LOCKED: exactly two hands of one man, ONE sheet of paper, the black sleeves and the steel watch; no face.", pin=E("L079", -0.6),
      motion="The paper tears slowly in one straight pull; the two halves drop onto the desk; nothing else moves."),
    S("S10h", "S10", "d", "ms", "office_n", "EL", [Ks, Mi], "OFF3", "Medium over Misaki's blurred shoulder (near RIGHT edge): Kenji seated, letting the two torn halves fall onto the desk, speaking with finality, the lamp on half his face.", line="L080a", expr="hard",
      act="Final, quiet, letting the torn halves drop; eyes on her screen RIGHT; a slight lift of the chin at 俺の条件; NOT smiling." + SEATED + OB),
    S("S10h2", "S10", "face", "cu", "office_n", "HA", [Mi], "OFF2", "High close-up: Misaki's face at the torn paper, eyes wide and wet, lips pressed white, not breathing.", pin=E("L080a", -1.0), expr="plead",
      motion="Her eyes stay on the desk; a tear spills; her lips press; NOT smiling." + HOLD),
    S("S10i", "S10", "d", "cu", "office_n", "EL", [Ks], "OFF3", "Chest-up close-up: Kenji seated, nearly whispering, one finger tapping twice on a new white document on the desk, eyes on her (screen RIGHT), the lamp cold on his face.", line="L080b", expr="cold",
      act="A near whisper, slow, the same cadence as Shibata and Misaki used; one finger taps twice; eyes on her screen RIGHT; NOT smiling." + SEATED + OB),
    S("S10j", "S10", "face", "ms", "office_n", "HA", [Mi], "OFF2", "High medium: Misaki sinking down onto her knees beside the glass desk, both hands over her face, the trench coat pooling on the floor; KNEELING, NOT lying down.", line="L081", expr="plead",
      motion="She sinks slowly down to her knees; her hands cover her face; her shoulders shake; she stays kneeling." + HOLD),
    S("S10k", "S10", "estill", "ecu", "office_n", "HA", [], "OFF3", "High insert: the thin folder and the two torn halves of the divorce form on the glass desk under the lamp; papers blank (titles composited); no hands.", line="L082", fx="push"),
    S("S10l", "S10", "estill", "ecu", "office_n", "EL", [], None, "Insert: one photograph lying on the glass desk under the lamp, a blank pale rectangle (composited: Shibata and Misaki at a hotel entrance); a corner of the torn form beside it; no hands.", line="L083", fx="push"),
    S("S10m", "S10", "face", "cu", "office_n", "LA", [Mi], "OFF2", "Low close-up: Misaki on her knees looking up at Kenji (screen RIGHT, up), wet face, lips pressed white and trembling, NOT speaking.", line="L084", expr="plead",
      motion="She looks up; a tear runs; her lips tremble but stay closed; NOT smiling." + HOLD),
    S("S10n", "S10", "face", "ws", "office_n", "HA", [Ks, Mi], "OFF3", "High wide: Kenji seated behind the glass desk under the single lamp, Misaki kneeling on the floor beside it with her head down, the red light pulsing faintly on the window; exactly two people.", line="L085",
      motion="Neither moves; the red glow on the window pulses twice; her shoulders shake once." + SEATED + HOLD),
    S("S10o", "S10", "face", "cu", "office_n", "LA", [Ks], "OFF3", "Low close-up: Kenji standing now at the glass wall, his face in three-quarter profile toward the city (screen LEFT), the red glow on his cheek, cold.", line="L086", expr="hard",
      motion="He looks out; a slow blink; the red light pulses on his cheek; he does not turn to the camera." + HOLD),
    S("S10p", "S10", "face", "ws", "office_n", "SIDE", [Ks, Mi], "OFF3", "Side wide: Kenji standing at the glass wall seen from behind, the city lights below, the lamp behind him; Misaki a small dark kneeling shape on the floor far behind him.", line="L087", expr="back",
      motion="He stands still; the red light pulses; her shape on the floor does not move." + HOLD),
    S("S10q", "S10", "ins", "ecu", "office_n", "EL", [Ks], None, "Insert: Kenji's hand pressed against the cold glass, the city lights blurred through his fingers, the steel watch on the wrist; no face." + ONEHAND, line="L088",
      motion="The fingers press slowly against the glass; the lights shimmer beyond."),
    S("S10r", "S10", "estill", "ews", "street_n", "LA", [], None, "Extreme low wide: the dark glass tower at night under rain, one red aviation light pulsing at the top, the city haze blue; EMPTY, nobody.", fx="push"),

    # ── S11 렉서스 LS 뒷좌석(8:24~8:42): 카드 돌리는 손 → 네온 위 켄지 → 운전사 뒷모습 → 「そう、思っていた」 첫 흔들림
    S("S11a", "S11", "ins", "ecu", "car", "HA", [Ks], "CAR1", "High insert: the black card turning slowly between Kenji's fingers over the black leather seat, amber neon sliding across it; one hand, one card; no text." + ONEHAND,
      motion="The card turns slowly once between the fingers; neon light slides over it."),
    S("S11b", "S11", "face", "ms", "car", "SIDE", [Ks], "CAR1", "Side medium in the rear seat: Kenji reclined on the black leather, warm neon reflections sliding over his face, eyes half closed, the city passing beyond the window.", line="L089", expr="calm",
      motion="Neon light slides across his face; he breathes slowly; his eyes stay half closed; he does not turn." + SEATED + HOLD),
    S("S11c", "S11", "face", "ws", "car", "EL", [Ch], "CAR2", "From the rear seat: the chauffeur's capped head and white-gloved hands on the wheel (RIGHT-hand drive), the neon street ahead through the windshield; no faces.", line="L090",
      motion="The gloved hands steer slightly; lights pass over the dashboard; the car glides."),
    S("S11d", "S11", "face", "cu", "car", "LA", [Ks], "CAR1", "Low close-up: Kenji's face, the faint smile fading, eyes opening fully — the first flicker of unease; neon passes.", line="L091", expr="tense",
      motion="His eyes open fully; the faint smile fades; a swallow; the light turns slightly colder." + HOLD),

    # ── S12 비통지 전화 → 候補者 No.7 → 카운트다운(8:42~10:28): 声 VO 위 켄지 얼굴·손, 문양 돌리줌, 사진 스탬프, 시계 0:00, CTA
    S("S12a", "S12", "estill", "ecu", "car_cold", "EL", [Ks], "CAR1", "Insert: the smartphone lighting up in Kenji's hand on the black leather seat, a blank dark glowing screen with no text (caller display composited); one hand.", fx="push"),
    S("S12b", "S12", "face", "cu", "car_cold", "EL", [Ks], "CAR1", "Close-up: Kenji with the phone to his ear, eyes on the passing lights (screen LEFT), the ease draining from his face, the neon turning cold.", line="L092a", vo=True, expr="tense",
      motion="He listens; his eyes stop moving; the light on his face turns colder; his mouth stays closed." + HOLD),
    S("S12c", "S12", "ins", "ecu", "car_cold", "HA", [Ks], "P_CARD", "High insert: the black card in his other hand on the leather, the thumb stopping on the engraved emblem." + ONEHAND, line="L092b", vo=True,
      motion="The thumb stops on the emblem; the card tilts; the engraving catches the cold light."),
    S("S12d", "S12", "estill", "ecu", "car_cold", "EL", [Ch], "CAR2", "Insert: the rear-view mirror from the back seat — only the chauffeur's eyes would be visible but they are hidden under the brim of the black cap; road lights streak past; no readable face.", line="L093", vo=True, fx="push"),
    S("S12e", "S12", "face", "ms", "car_cold", "HA", [Ks], "CAR1", "High medium: Kenji sitting up on the leather seat, the phone pressed to his ear, the other hand gripping the card, the city sliding past the window.", line="L094", vo=True, expr="hard",
      motion="He sits up slowly; his grip tightens on the card; the lights pass over him; his mouth stays closed." + SEATED + HOLD),
    S("S12f", "S12", "ins", "ecu", "car_cold", "EL", [Ks], "P_WATCH", "Side insert: the brushed-steel watch on Kenji's LEFT wrist, cold neon reflections across the blank dial; the black sleeve." + ONEHAND, line="L095", vo=True,
      motion="Cold light passes over the dial; the wrist turns slightly."),
    S("S12g", "S12", "face", "cu", "car_cold", "LA", [Ks], "CAR1", "Low close-up: Kenji's face frozen, the phone at his ear, eyes wide and dark, the neon reflections turned red.", line="L096", vo=True, expr="tense",
      motion="His eyes widen slowly; the red light grows on his face; he holds his breath, then breathes; his mouth stays closed." + HOLD),
    S("S12h", "S12", "estill", "ecu", "macro", "EL", [], "P_CARD2", "Macro: the engraved emblem on the back of the black card filling the frame — a tower inside a ring — in a tight pool of cold light, everything else black; no text.", line="L097", fx="push"),
    S("S12i", "S12", "estill", "ecu", "lobby", "EL", [], "HOTEL4", "Macro of the bronze emblem plaque above the tower's glass entrance — the SAME tower inside a ring — dark bronze on dark stone; no text.", line="L098a", fx="dollyzoom"),
    S("S12j", "S12", "face", "ws", "memory", "LA", [Kg], "HOTEL3", "Low wide like a memory: the glass entrance of the tower on a clean bright morning, the bronze emblem above the doors, a younger Kenji in the grey suit walking in seen from behind among a few salarymen from behind.", line="L098b", expr="back",
      motion="The figures walk slowly in through the doors away from the camera; nobody turns around; the light is soft." + HOLD),
    S("S12k", "S12", "face", "cu", "car_cold", "HA", [Ks], "CAR1", "High close-up: Kenji lowering the phone slowly from his ear, eyes unfocused on the seat in front (screen LEFT), the card still in the other hand.", line="L099", expr="tense",
      motion="He lowers the phone; his eyes stay unfocused; a swallow; the lights pass." + HOLD),
    S("S12l", "S12", "ins", "ecu", "car_cold", "EL", [Ch], "CAR4", "Side insert at the front: a white-gloved hand moving the gear lever as the car glides to a stop, the blank dark dashboard glow; no face." + ONEHAND,
      motion="The gloved hand pushes the lever and rests; the dashboard glow steadies as the car stops."),
    S("S12m", "S12", "ins", "ecu", "car_cold", "SIDE", [Ch, Ks], "CAR1", "Side insert between the front seats: a white-gloved hand reaching back over the seat holding a plain brown envelope toward the rear; Kenji's bare hand entering to take it; HANDS LOCKED: exactly one gloved hand and one bare hand, one envelope; no faces.", line="L100", vo=True,
      motion="The gloved hand holds the envelope steady; the bare hand takes it; both hands withdraw slowly."),
    S("S12n", "S12", "ins", "ecu", "car_cold", "EL", [Ks], "CAR1", "Side insert: Kenji's hands opening the brown envelope on his knee under the small reading light, the white edge of a photograph just emerging; the black sleeves, the steel watch; no face. HANDS LOCKED: two hands of one man, one envelope, one photograph.",
      motion="The fingers open the flap and slide the photograph a little way out; nothing else moves."),
    S("S12o", "S12", "estill", "ecu", "car_cold", "HA", [Ks], None, "High insert: a single photograph held in Kenji's hand under the reading light — a blank pale rectangle (composited: a young man in a suit on an interview day, fifteen years ago); the black sleeve; one hand.", line="L101", fx="push"),
    S("S12p", "S12", "estill", "ecu", "car_cold", "OH", [Ks], None, "Overhead insert: the photograph turned over on Kenji's knee, the back a plain pale surface (red stamp and handwritten date composited); the fingertips at the edge; one hand.", line="L102a", fx="push"),
    S("S12q", "S12", "face", "cu", "car_cold", "LA", [Ks], "CAR1", "Low close-up: Kenji's face lit from below by the reading light, eyes down on the photograph (screen LEFT, down), the first real fear.", line="L102b", expr="tense",
      motion="His eyes stay on the photo; his lips part slightly; a slow breath; the light flickers faintly." + HOLD),
    S("S12r", "S12", "estill", "ecu", "car_cold", "EL", [], "CAR4", "Insert: the dashboard clock, a blank dark panel in the leather dash (digits composited), the cold glow; no hands.", line="L103a", fx="push"),
    S("S12s", "S12", "face", "cu", "car_cold", "HA", [Ks], "CAR1", "High close-up: Kenji's eyes closing, jaw tight, the photograph in his hand lowered.", line="L103b", expr="hard",
      motion="His eyes close slowly; the jaw tightens; the hand lowers." + HOLD),
    S("S12t", "S12", "face", "ms", "car_cold", "SIDE", [Ks], "CAR1", "Side medium: Kenji leaning his head back against the leather headrest, eyes open to the ceiling, the photograph in his hand, cold neon passing.", line="L104", expr="tense",
      motion="He leans back slowly; his eyes open to the ceiling; the lights pass over his face; the hand with the photo rests." + SEATED + HOLD),
    S("S12u", "S12", "estill", "ecu", "car_cold", "EL", [], "CAR4", "Insert: the dashboard clock panel, blank dark (digits composited: 23:59 turning to 0:00), a faint cold glow; corner caption 「残り７日」 → 「残り６日」; no hands.", pin=B("L105", -1.6), fx="push"),
    S("S12v", "S12", "face", "cu", "car_cold", "EL", [Ks], "CAR1", "Close-up: Kenji's eyes reflecting the clock's faint glow, resolved and afraid at once, a slow blink, the city dark behind.", line="L105", expr="hard",
      motion="A slow blink; his eyes stay on the clock screen LEFT; his breath steadies; the light holds." + HOLD),
    S("S12w", "S12", "face", "ms", "car_cold", "SIDE", [Ks], "CAR1", "Side medium: Kenji in the rear seat looking out at the night through the window, the photograph in his hand on his knee, cold neon passing slowly.", line="L106", expr="tense",
      motion="He looks out; the lights pass; his thumb moves once over the photograph; he does not turn." + SEATED + HOLD),
    S("S12x", "S12", "ins", "ecu", "car_cold", "HA", [], "CAR1", "High insert: the black card lying on the black leather seat beside the torn brown envelope, the emblem up, cold neon sliding over them; no hands, no people.", line="L107",
      motion="Cold light slides slowly across the card and the leather; nothing else moves."),
    S("S12y", "S12", "face", "cu", "car_cold", "LA", [Ks], "CAR1", "Low close-up: Kenji looking out of the side window (screen RIGHT), the faint smile long gone, the red light of the tower reflected in his eye.", line="L108", expr="hard",
      motion="A slow blink; the red reflection pulses in his eye; he does not turn to the camera." + HOLD),
    S("S12z", "S12", "estill", "ews", "street_n", "LA", [], None, "Extreme low wide: the dark glass tower under rain at night, the red aviation light pulsing at the top, the city haze blue; EMPTY, nobody.", line="L109", fx="push"),
    S("S12zz", "S12", "card", "ews", "street_n", "LA", [], None, "Countdown card 「残り　６日」 over the blurred frame of S12z (no black), then the fade to the outro.", pin=B("L109", 3.3)),
]
SPK_WHO = {"柴田": Sh, "美咲": Mi, "社長": Pr}
KEN_WARD = {"S01": Kw, "S02": Kg, "S03": Kw, "S04": Kw, "S05": Kww, "S06": Kww}  # S07 이후 Ks
VO_OTS_SKIP = {"S07r"}  # 社長 VO 위 柴田 — 社長이 뒤에 서 있어 어깨 너머가 부자연스러움
# 재생성 컷 동작 고정 문장(맨 앞) — Kill Gate·1초 시트 검수 후 채운다
MOTION_FIX = {}
for _s in SHOTS:
    if _s["id"] in MOTION_FIX:
        _s["motion"] = MOTION_FIX[_s["id"]] + " " + _s["motion"]

CARDS = {"S01k": "拾ったのは、カードだけじゃなかった。", "S02a": "ブラックカード", "S08u": "この後――妻が、ドアを叩き壊す", "S12u": "残り　７日", "S12zz": "残り　６日"}
JA_OVERLAY = {
    "S02b": "구석 소자막 「その日の朝」", "S02n": "벽시계 바늘 10:45(무지 시계판 위)", "S03c": "통장 마지막 줄 「残高 3,218」 실글꼴", "S03h": "離婚届 표제·칸(무지 서류 위, 립싱크 키프레임에 합성)",
    "S03i": "離婚届 표제 + 「妻」 칸 인감(생성) / 「夫」 칸 비움", "S04j": "택시 미터 「2,340」(lcd)", "S06a": "휴대폰 「非通知」(lcd)",
    "S07d": "메모 손글씨 『本日十二時、最上階のレストラン。個室はご用意しております。』(KleeOne)", "S07g": "태블릿 뉴스 『六本木ルクスタワー、所有権移転』(lcd)",
    "S08g": "辞令 표제 「辞令」 + 서명란(i2v 매 프레임 합성)", "S08l": "같은 辞令(정지)", "S09b": "美咲 휴대폰 뉴스 화면(lcd, 립싱크 키프레임에 합성)",
    "S10a": "사진 4장 내용 = 본편 키프레임(柴田·美咲 호텔 입구) 합성", "S10b": "사진 1장(같은 합성)", "S10f": "離婚届 표제(립싱크 키프레임에 합성)",
    "S10k": "협의서·청구서 표제 「慰謝料請求書」「財産分与協議書」", "S10l": "사진 1장 합성", "S12a": "휴대폰 「非通知」(lcd)", "S12o": "사진 = 15년 전 켄지(정장, 면접 날) 합성",
    "S12p": "사진 뒷면 붉은 스탬프 『候補者 No.7』 + 손글씨 날짜", "S12r": "대시보드 시계 「23:59」(lcd)", "S12u": "대시보드 시계 23:59 → 0:00(lcd 애니메이션) + 구석 「残り７日」→「残り６日」",
}
G = {
    "rain_ext": "heavy rain on asphalt and concrete, water running in a gutter, distant traffic hiss, a far rumble of thunder",
    "meeting": "an air conditioner hum, a fluorescent tube buzzing faintly, a pen set on a table, distant office keyboards",
    "corridor": "a quiet office corridor, fluorescent hum, distant phones, footsteps on carpet",
    "home": "rain on a window, a bare fluorescent tube buzzing, a refrigerator hum, a wall clock ticking",
    "taxi": "inside a taxi in the rain, wipers sweeping, rain drumming on the roof, an engine idling, a meter clicking",
    "ginza": "a hushed luxury boutique, soft air conditioning, rain faintly outside the glass door",
    "street_rain": "heavy rain on a city sidewalk, water splashing, distant traffic, a rain-soaked quiet",
    "hotel": "a silent hotel room at dawn, faint city hum, air conditioning", "elevator": "an elevator humming, a soft chime",
    "lobby": "a quiet marble lobby, distant footsteps, a revolving door", "restaurant": "a hushed private dining room, faint cutlery, a distant city hum",
    "office_n": "a silent office at night, rain on glass, a faint electrical hum, a relay click every two seconds",
    "car": "a luxury car gliding, a smooth engine, tyres on wet asphalt, rain on the windshield",
    "phone": "a smartphone vibrating on wet skin, rain", "clock": "a single digital clock tick, a car cabin hum",
}
AMB_BY_SCENE = {"S01": "rain_ext", "S02": "meeting", "S03": "home", "S04": "rain_ext", "S05": "ginza", "S06": "street_rain", "S07": "restaurant",
                "S08": "restaurant", "S09": "office_n", "S10": "office_n", "S11": "car", "S12": "car"}
AMB_BY_SHOT = {"S02l": "corridor", "S03n": "rain_ext", "S03o": "rain_ext", "S04g": "taxi", "S04h": "taxi", "S04i": "taxi", "S04j": "taxi", "S04k": "taxi",
               "S05k": "street_rain", "S05l": "street_rain", "S06a": "phone", "S07a": "hotel", "S07b": "hotel", "S07c": "hotel", "S07d": "hotel", "S07e": "hotel",
               "S07f": "elevator", "S07g": "hotel", "S07g2": "hotel", "S07h": "elevator", "S07i": "lobby", "S10r": "rain_ext", "S12j": "lobby", "S12r": "clock",
               "S12u": "clock", "S12z": "rain_ext", "S12zz": "rain_ext"}
FOLEY = {  # 컷별 폴리(제12장 10·제15장 22) — 타임코드 자동 믹스(−18~−12 dBFS, 대사 구간 −6 dB)
    "S01a": "a single thunder crack rolling over a city", "S01b": "a cardboard box thudding on wet concrete, shoes slipping on wet asphalt",
    "S01d": "a steel scissors snip through a plastic card, two pieces dropping on a counter", "S01e": "paper hitting water, water running into a drain grate",
    "S01h": "a wet card lifted off asphalt, water dripping", "S02d": "a wooden seal pushed across a table, two finger taps on paper",
    "S02g": "a wooden seal pressed on paper", "S02j": "paper sliding into an envelope", "S02l": "slow footsteps on office carpet",
    "S03a": "water dripping on a wooden floor", "S03c": "a finger tapping a paper page", "S03h": "a sheet of paper laid on a table, two finger taps",
    "S03j": "a suitcase handle extended with a click, suitcase wheels on a floor", "S04a": "a shoe toe touching a card in a puddle",
    "S04f": "a taxi pulling up in the rain, a car door opening", "S04h": "a short electronic payment chime", "S04j": "a thermal receipt printer printing a short slip",
    "S05a": "a glass shop door opening, rain outside, the door closing softly", "S05f": "a short electronic payment chime", "S05g": "a thermal receipt printer printing",
    "S05h": "a steel watch clasp closing with a click", "S06a": "a smartphone vibrating in a hand", "S06i": "a phone call ending with a soft click",
    "S07b": "a hotel door lever pressed and a heavy door opening", "S07e": "fabric rustling, a suit button closing", "S07f": "elevator doors closing, a soft chime",
    "S07m": "a quiet bow, fabric", "S07q": "a smartphone vibrating in a hand", "S08a": "an envelope sliding across a tablecloth", "S08g": "two finger taps on paper on a tablecloth",
    "S08i": "a wooden seal lifted from a tablecloth", "S08l": "a wooden seal pressed on paper", "S08m": "a leather chair tilting and rocking back, a man slumping",
    "S08o": "a single drop in a wine glass", "S08r": "a card sliding into a jacket pocket", "S08s": "slow footsteps on a wooden corridor floor",
    "S09a": "a heavy office door flung open and hitting a wall hard, then a short echo", "S09c": "rain on glass, a low electrical hum",
    "S10c": "a thin folder sliding across a glass desk", "S10g": "a single sheet of paper torn slowly in half", "S10h": "a deep low cinematic impact",
    "S10i": "two finger taps on paper on a glass desk", "S10j": "knees sinking onto carpet, a muffled sob", "S10q": "a hand pressed against cold glass",
    "S11a": "a card turning between fingers, a car gliding", "S12a": "a smartphone vibrating on leather", "S12l": "a gear lever moved, a luxury car gliding to a stop",
    "S12m": "a paper envelope handed over between seats", "S12n": "an envelope flap opened, a photograph sliding out", "S12p": "a photograph turned over on fabric",
    "S12u": "a single digital clock tick, then one slow heavy heartbeat thump",
}
BGM = [  # (시작, 끝, 볼륨, 프롬프트) — 0~3.5초 BGM 없음(드론+심장 박동 가속은 PHASE 6 로컬 SFX). 구간 간격 1.0초 이상
    (3.5, 34.0, 0.36, "dark pulsing low drone with a slow heartbeat and a cold string swell, rain-soaked Tokyo noir cold open, instrumental, no vocals"),
    (36.5, 89.0, 0.36, "cold minimal piano with a soft ticking pulse and low strings, corporate cruelty in a glass meeting room, Japanese noir drama, instrumental, no vocals"),
    (90.5, 147.5, 0.38, "sorrowful solo cello and sparse piano, a cold empty apartment, a man losing everything, Japanese noir drama, instrumental, no vocals"),
    (149.0, 167.5, 0.38, "mysterious low synth pulse and pizzicato, a found object in the rain, quiet suspense, Japanese noir drama, instrumental, no vocals"),
    (177.5, 192.5, 0.40, "tense rising low pulse with a heartbeat, cold luxury, suspense before a decision, Japanese noir drama, instrumental, no vocals"),
    (198.0, 221.0, 0.42, "dark triumphant pulsing electronic bass at 100 bpm with cold strings, a surge of power and dopamine, Japanese noir thriller, instrumental, no vocals"),
    (252.5, 261.5, 0.40, "anticipation rising, low strings building to a cold confident theme, the night before revenge, Japanese noir drama, instrumental, no vocals"),
    (263.0, 299.0, 0.38, "elegant restrained piano and strings at dawn, quiet power, expensive calm, Japanese noir drama, instrumental, no vocals"),
    (300.0, 329.5, 0.38, "tense elegant strings with a slow pulse, a private dining room, a predator waiting, Japanese noir drama, instrumental, no vocals"),
    (338.5, 378.5, 0.40, "cold restrained revenge theme, low strings and a slow pulse, words returned exactly, Japanese noir drama, instrumental, no vocals"),
    (386.8, 410.5, 0.40, "low warm resolution rising into dark anticipation, silence after fifteen years, then a cliff, Japanese noir drama, instrumental, no vocals"),
    (412.0, 437.5, 0.38, "tense low strings and a pulsing heartbeat, a door bursts open at night, confrontation, Japanese noir drama, instrumental, no vocals"),
    (439.0, 459.0, 0.38, "cold confrontation, sparse piano over a low drone, evidence on a desk, Japanese noir drama, instrumental, no vocals"),
    (463.7, 503.5, 0.42, "dark triumphant revenge theme fully unleashed, pulsing bass and cold brass, Japanese noir thriller, instrumental, no vocals"),
    (505.0, 521.0, 0.40, "sleek night-drive bass and shimmering synth, neon Tokyo from a luxury car, the king of the city, Japanese noir thriller, instrumental, no vocals"),
    (522.5, 597.0, 0.38, "creeping unease, low strings and a cold pulse, a phone call that changes everything, slow revelation, Japanese noir thriller, instrumental, no vocals"),
    (600.0, None, 0.40, "cliffhanger countdown: a heavy heartbeat pulse under a rising dark drone and cold strings, Japanese noir thriller, instrumental, no vocals"),
]
for _a, _b in zip(BGM, BGM[1:]):
    assert _b[0] - _a[1] >= 1.0, f"BGM 구간 간격 {_b[0] - _a[1]:.1f}s < 1.0s"
# 긴박한 순간 = BGM을 빼고 정적 속 효과음만(제19장 14). 룸톤 −52 dBFS 유지(제15장 13). (컷 시작, 컷 끝, 효과음 세기 dB, 이유)
SILENCE = [("S04h", "S04i", +3, "택시 승인 「ピッ」 → 3초 정적(와이퍼·빗소리만)"),
           ("S05f", "S05g", +3, "시계점 승인 「ピッ」 → 3초 정적 → 영수증 인쇄음"),
           ("S08a", "S08d", +2, "辞令 봉투 슬라이드 — 테이블보 마찰음만"),
           ("S08n", "S08p", +2, "「ただ、静かだった」 — BGM·환경음 0, 와인잔 물방울만"),
           ("S10f", "S10h", +4, "離婚届 찢기 — 종이 찢는 소리만 → 다음 컷 저음 임팩트"),
           ("S12u", "S12v", +3, "시계 0:00 — 시계 틱 + 심장 박동 1회")]
FOLEY_TENSION = {
    "S04i": "wipers sweeping slowly in a silent taxi, rain on the roof, a held breath",
    "S05g": "a hushed boutique, air conditioning, a held breath, then a thermal printer printing",
    "S08b": "a held breath, fingers twitching on a tablecloth", "S08n": "a silent room, a faint city hum, one slow breath",
    "S10g": "a single sheet of paper torn slowly and loudly in half in a silent room", "S10h": "a deep low cinematic impact boom",
    "S12v": "a slow heavy heartbeat, then silence",
}
FOLEY.update(FOLEY_TENSION)

STYLE_OF = {("高橋 健二", "narration"): "KenjiN", ("高橋 健二", "dialogue"): "Kenji", ("柴田", "dialogue"): "Shibata", ("美咲", "dialogue"): "Misaki",
            ("声", "dialogue"): "Koe", ("社長", "dialogue"): "President"}
STYLE_JA = {"KenjiN": "健二（語り）", "Kenji": "健二", "Shibata": "柴田", "Misaki": "美咲", "Koe": "声", "President": "社長", "Staff": "スタッフ"}
STYLE_COLOR = {"KenjiN": "&H00DDDDDD", "Kenji": "&H00FFFFFF", "Shibata": "&H00B4D2FF", "Misaki": "&H00F0E6C8", "Koe": "&H00C8E6F0",
               "President": "&H00E6DCC8", "Staff": "&H00D0D0D0"}
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
    t = open(os.path.join(PROD, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 5.")[0]
    return {m.group(1): m.group(2) for m in re.finditer(r"^\s+(L\d+[ab]?|OUT\d)[^「\n]*「(.+)」", body, re.M)}


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
    scenes = {"S" + s["id"]: (s["start"], s["end"]) for s in LOCK["scenes"]}
    main_end = LOCK["body_end"]
    for s in SHOTS:
        spk = ROWS[s["line"]]["spk"] if s.get("vo") and s["line"] in ROWS else None
        sp = (KEN_WARD.get(s["scene"], Ks) if spk == "高橋 健二" else SPK_WHO.get(spk)) if spk else None
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
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/{SKIT}-keyframes/{sid}-1.png"
        kf_prompt = None
        if keyframe:
            low = (s["subject"] + " " + (s["act"] or "") + " " + (s["motion"] or "")).lower()
            real = " ".join(x for x, keys in ((TEARS, ("tear", "welling")), (SWEAT, ("sweat",)), (RAINSKIN, ("rain on", "rain-streaked", "rain-soaked face", "wet face")))
                            if any(k in low for k in keys) or (s["expr"] == "plead" and x == TEARS))
            glasses = " ".join(GLASSES[w.split(":")[0]] for w in s["who"] if w.split(":")[0] in GLASSES and s["kind"] not in ("ins", "estill"))
            face_expr = f" Expression of {ids[0].split(',')[0]}: {EXPR_TXT[s['expr']]} (about half intensity)." if s["expr"] in EXPR_TXT and s["expr"] != "back" and s["kind"] not in ("ins", "estill", "pstill") else ""
            setting = f"Lighting: {LIGHT[s['light']]}."
            if s["loc"] is None:
                setting += " Location: " + LOC_TXT["GINZA_ST" if s["scene"] == "S05" else "STREET_N" if s["light"] == "street_n" else "RAIN_ALLEY" if s["light"] in ("rain_n", "macro") else "CORRIDOR" if s["light"] == "meet" else "TOWER" if s["scene"] in ("S10", "S12") else "STREET_N"] + "."
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
    ass = ["[Script Info]", "Title: ブラックカード 第1話 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
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
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_blackcard_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT, "preset": PRESET,
               "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": LOCK["ads"], "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_blackcard_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, wardrobe, "
                         "props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_blackcard_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (ElevenLabs 확정본, 번호 = 타임라인 순).",
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
        "_후크": "0~3.5초 BGM 없음: 가속 심장 박동(60→90 bpm) + 천둥 1회(1.0초)를 PHASE 6 로컬 믹스(ElevenLabs SFX). S01k 질문 카드·S02a 타이틀·S08u 예고·S12u/S12zz 카운트다운 카드는 클립에 직접(암전 없음).",
        "_정점": "bgm_silence 6곳의 효과음은 ElevenLabs 전용 생성(택시·시계점 승인음, 테이블보 마찰, 종이 찢기, 시계 틱+심장) → finalize SFX 피크 −9 dBFS(제19장 26).",
        "_로컬": "형광 플리커(S02·S03 ±4%, 립싱크 절반), 승인 +1 stop(S05g→S05i), 항공장애등 붉은 점멸 2초(S09·S10, 립싱크 절반), 냉색 전환(S12b~), 더치 S08m 5°·S09a 7°, 돌리줌 S12i, L컷·점프 컷 크기 변환(제19장 17).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    warn = [p for p in problems if p.startswith("⚠")]
    md = ["# 『ブラックカード』(第1話) PHASE 3 샷 리스트 (B안 표준)", "",
          f"> `scripts/build_blackcard_phase3.py` 자동 생성(손 수정 금지). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " + ", ".join(f"{a['name']} {tc(a['at'])}" for a in LOCK['ads']) + ".",
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


SCENE_TITLE = {"S01": "후크 — 빗속의 블랙카드", "S02": "12층 유리 회의실", "S03": "낡은 맨션 거실", "S04": "뒷문 카드 발견 → 택시", "S05": "긴자 시계점",
               "S06": "빗속의 비통지 전화", "S07": "호텔 아침 → VIP룸", "S08": "辞令 봉투", "S09": "구 사장실, 美咲 입장", "S10": "증거 사진과 離婚届",
               "S11": "렉서스 뒷좌석", "S12": "비통지 전화 → No.7 → 카운트다운"}


def angle_doc(sb):
    md = ["# 『ブラックカード』(第1話) 카메라 앵글 설계 (CLAUDE.md 제8장, PHASE 3)", "",
          "> 샷 표의 원본은 `scripts/build_blackcard_phase3.py`(자동 검사 통과). 이 문서는 장면별 컷 순서와 앵글 의도를 정리한 것이다.", "",
          "## 1. 권력 역전 앵글 축", "", "| 구간 | 켄지 | 柴田 | 美咲 |", "|---|---|---|---|",
          "| S01~S03 추방·집 | 하이(무력, S01c·S02c·S03d·S03m) | 로우(S02f 권력) | 아이레벨·하이(S03g — 차가운 우위) |",
          "| S04~S06 카드 | 아이레벨 → 로우(S05d·S05i·S06k 상승) | — | — |",
          "| S07~S08 첫 복수 | 로우(S07h·S08c·S08f 권력) | 아이레벨 → 하이(S08b·S08h) → **더치 5°**(S08m 붕괴) | — |",
          "| S09~S10 아내 | 로우(S09e·S10f·S10o) | 사진 속 존재 | **더치 7°**(S09a 문) → 하이(S09g·S10j — 무릎) → 로우 올려다봄(S10m) |",
          "| S11~S12 반전 | 아이레벨 → 하이(S12e·S12k·S12s — 흔들림) | — | — |", "",
          "## 2. 장치·규칙 대조", "",
          "- 돌리줌 1회(S12i 정문 문양), 더치 2회(S08m 5°·S09a 7°) — 생성기 자동 검사.",
          "- 카메라 안정도(제8장 4-1): 켄지 복수 구간(S07~S10)은 고정·슬로우 푸시인, 비립싱크 화자 뒷모습(S03d·S06f)은 핸드헬드, 美咲 손(S10b) 핸드헬드.",
          "- 소품의 인격화(제8장 4-2): 카드(S01g·S01h·S04b·S04c·S12h)·판자(S02g)·離婚届(S03i·S10g)·봉투(S08a)·시계(S05h·S08k)·사진(S12o·S12p)·대시보드 시계(S12u) ECU 70% 이상.",
          "- 콜백 대구: S02d 柴田 손가락 두 번 ↔ S03h 美咲 ↔ S08g 켄지 ↔ S10i 켄지(속삭임). S01b 추방 ↔ S03n 회상. S04c 카드 문양 ↔ S07i 로비 문양(복선) ↔ S12h→S12i 일치.",
          "- 대사 = 어깨 너머 3/4(제10장 1), 듣는 사람 VO 컷은 리버스숏(제18장 8②). 말하는 화자 뒷모습(L017·L044·L073)은 정지 + 편집 카메라(제11장 9).",
          "- 앵글 분포는 `07_샷리스트.md`(최다 60% 이하 기준).", "",
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
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_blackcard_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않거나 부딪힘(연기 메모에 의도가 없으면 키프레임·동작 문장을 고친다). 👂 = 듣는 사람·소품 위 목소리(VO).", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 감정·세기·템포 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")


if __name__ == "__main__":
    main()
