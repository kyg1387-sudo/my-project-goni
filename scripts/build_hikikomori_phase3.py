#!/usr/bin/env python3
"""『引きこもりの息子』(hikikomori-ja) PHASE 3 샷 리스트 Lock 생성기 — build_beggar_phase3.py를 옮긴 것.

이 작품에서 달라진 것:
  · 프롬프트 5단 공식(제16장 1): 키프레임·i2v 모두 [CAMERA] → [CHARACTER] → [ACTION] → [SETTING] → [NEGATIVE] 순서로 조립(compose_kf·compose_motion)
  · 권력 역전 앵글(02_카메라앵글설계.md): 전반 亮介·真壁 LA / 健太郎 HA → S18 大樹 등장 LA·역광 → S20 真壁 HA·BE(더치 7°) → S21 健太郎 LA
  · 재생(replay) 립싱크: S05 「出ていけ！」 = 후크 L01 녹음, 같은 립싱크 컷(S05e)을 후크 H0이 재사용. 무대사 컷도 pin으로 시각 고정
  · 말하는 화자의 비립싱크 뒷모습은 kind=pstill(정지 + 편집 카메라, 제11장 9) — L03·L19·L40
  · 의상 상태 전환 고정(제18장 5③): 大樹 후드(S03~S06·S24) → 정장(S18~S22) → 흰 셔츠(S23), 健太郎 작업복(공장) / 집옷(자택)
입력: productions/hikikomori-ja/lock.json · 00_script_ja.md · build_tts_spec.py(TONE) · assets/auditions/hikikomori-tts/lineNNN.mp3 · assets/portraits/hikikomori-cast/cells/
출력: scripts/storyboard/hikikomori.json · scripts/scenes/hikikomori.json · scripts/audio/hikikomori.json · subs/hikikomori.ass ·
      assets/audio-overrides/hikikomori/lineNNN.mp3 · productions/hikikomori-ja/07_샷리스트.md · 16_감정일치표.md
사용법: python3 scripts/build_hikikomori_phase3.py
"""
import collections, json, os, re, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "hikikomori-ja")
SKIT = "hikikomori"
TTS_DIR = "hikikomori-tts"
FPS = 24; HARD = 1 / FPS; OMNI_MAX = 7.9; LEAD = 0.3; MIN_SHOT = 1.2; STILL_MAX = 6.5; I2V_MAX = 10.0

C = "assets/portraits/hikikomori-cast/cells/"
WHO = {
    "KEN": ("Seo Kentaro, a stocky Japanese man aged 52, square weathered face, short greying crew-cut hair, thick straight black eyebrows, "
            "a small old healed burn scar on the back of his RIGHT hand only (pale, smooth, barely visible, NOT red, NOT a wound), no glasses, no earrings, no beard", C + "kentaro-front.png"),
    "DAI": ("Seo Daiki, a slim Japanese man aged 26, pale indoor complexion, slightly long straight black hair with bangs just above the eyebrows, "
            "black thick-rimmed rectangular glasses, clean-shaven, NO earrings, a young MAN with short hair above the ears", C + "daiki-front0.png"),
    "YUM": ("Seo Yumiko, a Japanese woman aged 50, soft round face, shoulder-length dark-brown bob, small single pearl stud earrings, no glasses, "
            "light natural makeup", C + "yumiko-front0.png"),
    "SEI": ("Seo Seiji, a slightly chubby Japanese man aged 48, round face, slicked-back black hair, thin GOLD wire-rimmed glasses, clean-shaven, no earrings",
            C + "seiji-front.png"),
    "RYO": ("Seo Ryosuke, a lean Japanese man aged 28, clear smooth skin, short neat black side-parted two-block hair, no glasses, no earrings, clean-shaven",
            C + "ryosuke-front.png"),
    "MAK": ("Makabe, a gaunt stern Japanese man aged 60, slicked-back silver-white hair, slightly tired lower eyelids with fine wrinkles, no glasses, "
            "no earrings, clean-shaven", C + "makabe-front0.png"),
    "KAN": ("Kaneda, a veteran craftsman in his sixties, wavy black hair with a little grey, thin silver half-rim browline glasses, clean-shaven, no earrings "
            "(the SAME man as the reference photo)", C + "kaneda-front.png"),
    "SUB": ("a junior salaryman in a plain dark suit seen only from behind or out of focus", None),
    "CREW": ("several factory craftsmen in plain navy work jackets seen only from behind, small in the frame", None),
    "BANK": ("a bank clerk seen only as a blurred shape behind the counter", None),
    "KID": ("a Japanese boy aged 6 (young Daiki) and a Japanese man aged 30 (young Kentaro, crew-cut, navy work jacket)", None),
}
WARD = {
    "work": "a plain navy-blue factory work jacket and matching work trousers with no logo, no chest patch, no badge, a plain wristwatch",
    "home": "a plain charcoal-grey knit cardigan over a plain grey crew-neck T-shirt, dark trousers, no logo",
    "hood": "a plain heather-grey pullover hoodie with no print or logo, plain dark-grey sweatpants",
    "suit": "a well-fitted plain dark navy business suit, crisp white shirt with the top button closed and NO necktie, no badge, no pin",
    "shirt": "a plain white dress shirt with the sleeves rolled to the forearms, no necktie, dark navy suit trousers (the jacket is off)",
    "yum": "a plain beige knit cardigan over a plain white blouse, plain navy slacks",
    "sei": "a plain burgundy golf polo shirt with no logo, plain white trousers, a plain gold wristwatch with no markings",
    "ryo": "a plain slim charcoal-grey business suit, white shirt, plain dark-grey necktie with a small plain silver tie clip, no badge",
    "mak": "a plain black business suit, white shirt, plain black necktie, no lapel pin, no badge",
    "kan": "a plain navy-blue factory work jacket with a small plain BLANK silver name badge on the left chest (NO text), matching work trousers",
}
EXPR = {  # PHASE 2 Kill Gate 합격 셀(03_마스터에셋.md) — 표정 50% 선반영. 금지 셀(由美子 웃음+젤 눈물, 真壁 젤 땀, 大樹 후드 표정)은 없음
    ("KEN", "calm"): C + "kentaro-calm.png", ("KEN", "anger"): C + "kentaro-anger.png", ("KEN", "grief"): C + "kentaro-grief.png",
    ("KEN", "back"): C + "kentaro-fullback.png", ("KEN", "full"): C + "kentaro-full.png",
    ("DAI", "calm"): C + "daiki-resolute.png", ("DAI", "cool"): C + "daiki-cool.png", ("DAI", "smile"): C + "daiki-smile.png",
    ("DAI", "hoodback"): C + "daikih-hoodback.png", ("DAI", "hood"): C + "daikih-hood45.png", ("DAI", "suitback"): C + "daiki-suitback.png",
    ("YUM", "calm"): C + "yumiko-calm.png", ("YUM", "worry"): C + "yumiko-worry.png", ("YUM", "back"): C + "yumiko-fullback.png",
    ("SEI", "smug"): C + "seiji-smug.png", ("SEI", "sneer"): C + "seiji-sneer.png", ("SEI", "forced"): C + "seiji-forced.png",
    ("RYO", "cold"): C + "ryosuke-cold.png", ("RYO", "aside"): C + "ryosuke-aside.png", ("RYO", "shock"): C + "ryosuke-shock.png",
    ("MAK", "cold"): C + "makabe-cold.png", ("MAK", "stern"): C + "makabe-stern.png",
    ("KAN", "focus"): C + "kaneda-front.png", ("KAN", "concern"): C + "kaneda-concern.png", ("KAN", "smile"): C + "kaneda-smile.png",
    ("KAN", "back"): C + "kaneda-fullback.png", ("KAN", "side"): C + "kaneda-profile.png",
}
EXPR_TXT = {  # 표정 문장(제15장 2 — 셀이 약하면 문장으로). 50% 반영
    "calm": "calm, tired eyes", "anger": "grim restrained anger, furrowed brows, jaw clenched", "grief": "held-back grief, eyes wet, lips pressed, NOT smiling",
    "cool": "quiet cool confidence, lips closed", "smile": "a gentle faint smile", "worry": "worried, brows drawn together",
    "smug": "smug, self-satisfied", "sneer": "a sneering smirk, one corner of the mouth raised", "forced": "a nervous forced grin, tiny beads of sweat at the temple",
    "aside": "eyes averted, coolly dismissive", "shock": "pale and shocked, eyes wide, NOT smiling", "stern": "an intimidating stare, lips thin",
    "focus": "quietly focused", "concern": "concerned, brows slightly drawn", "panic": "panic, wide eyes, mouth tense, NOT smiling",
    "shout": "furious, face flushed, brows knotted, NOT smiling", "stunned": "stunned, lips parted, eyes wide, NOT smiling",
}
LOC = {
    "HOME_LIV": C + "loc-home-living-day.png", "HOME_DIN": C + "loc-home-dining-night.png", "HOME_HALL": C + "loc-home-hall-night.png",
    "GENKAN": C + "loc-home-genkan.png", "ROOM_N": C + "loc-room-desk-night.png", "ROOM_C": C + "loc-room-corner-night.png",
    "ROOM_M": C + "loc-room-monitor-night.png", "ROOM_D": C + "loc-room1-bed-day.png",
    "FAC_D": C + "loc-factory-floor-day.png", "FAC_N": C + "loc-factory-floor-night.png", "LATHE": C + "loc-factory-lathe.png", "FAC_EXT": C + "loc-factory-exterior.png",
    "OFF_D": C + "loc-office1-day-wide.png", "OFF_DESK": C + "loc-office1-day-desk.png", "OFF_N": C + "loc-office2-night-lamp.png",
    "MEET": C + "loc-meeting-wide.png", "MEET_T": C + "loc-meeting-table.png", "MEET_DOOR": C + "loc-meeting-door.png", "MEET_OPEN": C + "loc-meeting-door-open.png",
    "P_PASS": C + "props-passbook.png", "P_POSTIT": C + "props-postit.png", "P_TABLET": C + "props-tablet.png", "P_CONTRACT": C + "props-contract.png",
    "P_SUKI": C + "props-sukiyaki.png", "P_PHOTO": C + "props-photo.png",
}
LOC_TXT = {  # 장소 참조를 뺀 컷(NO_LOC)은 글로만 지정 — 후광 테두리 방지(제18장 9④)
    "BANK": "a plain modern Japanese bank counter, blurred, no signage, no screens with text",
    "STREET": "a narrow Japanese residential back street in Ota-ku at night, a single streetlight, utility poles, a tin-roofed small factory in the far distance, no signage",
    "RAIN": "a narrow Japanese residential street on a rainy evening, wet asphalt reflecting streetlights, no signage",
    "HOUSE_N": "the outside of a modest two-storey Japanese house at night, one upstairs window glowing cold blue, all other windows dark",
    "HALL_OPEN": "the narrow dark hallway of a modest Japanese house at night",
    "HALL": ("the narrow dark hallway of a modest Japanese house at night: plain beige walls, a worn wooden floor, the son's plain wooden door at the end; "
             "the ONLY blue light is a faint cold glow leaking from the thin gap under that door; NO LED strips, NO light lines along the walls or floor"),
}
PRESET = ("Photorealistic live-action Japanese human drama, contemporary Tokyo (Reiwa era), Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, "
          "restrained Japanese film mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, "
            "signage lettering, documents with writing, screens with text, printed labels, keyboard key letters, brand logos, watermarks, stamps, "
            "symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, blood, gore, anime, 3d render, illustration, "
            "thick glossy gel tears, cartoon sweat drops, multiple tear streams on both cheeks, earrings on men, apple logo, brand logo on monitors or laptops, "
            "LED light strips")
PLAIN = ("All papers, ledgers, screens, signs, cards, keyboards and labels are completely blank (monitors show only a soft plain glow); "
         "no letters, numbers or symbols anywhere in the frame.")
TEARS = ("Realistic tears as in a live-action film: reddened eye rims, glossy wet eyes catching the light, a small clear tear bead on the lower lashes, "
         "at most one thin translucent tear track on one cheek, a slightly reddened nose tip, matte natural skin; no glossy gel streams, no cartoon droplets.")
SWEAT = ("Realistic sweat as in a live-action film: a few tiny natural beads of perspiration on the forehead and temples, a faint natural sheen, "
         "one thin bead line near the temple; no large cartoon drops, no face-wide shine.")
WET_HOLD = " Eyes wet and glistening with tears welling on the lower lids but NOT running down — the tears stay pooled."
TEARS_FLOW = (" One clear tear slowly spills over the lower lid and runs down the cheek along its natural curve, catching the light; a slow blink, "
              "a trembling breath; only one tear line, thin and translucent.")
SWEAT_FLOW = " A thin bead of cold sweat slowly runs from the temple down toward the jaw; a shaky breath, a hard swallow."
NOSMILE = "NOT smiling at any moment: brows knotted, the corners of the mouth pulled down, chin trembling slightly. "
GLASSES = {"KEN": "Kentaro wears no glasses.", "DAI": "Daiki wears his black thick-rimmed rectangular glasses.", "YUM": "Yumiko wears no glasses.",
           "SEI": "Seiji wears his thin GOLD wire-rimmed glasses.", "RYO": "Ryosuke wears no glasses.", "MAK": "Makabe wears no glasses.",
           "KAN": "Kaneda wears his thin silver half-rim browline glasses."}
HANDS = {"KEN": "thick weathered hands; only the back of the RIGHT hand has a small old healed burn scar (pale, smooth, barely visible, NOT red, NOT a wound); the left hand and forearms are unmarked", "DAI": "slim pale young hands",
         "YUM": "a middle-aged woman's hands", "SEI": "plump hands, a plain gold wristwatch", "RYO": "lean young hands", "MAK": "thin old hands",
         "KAN": "weathered craftsman's hands"}
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, the face fills at least one third of the frame height",
    "ots": "50mm lens, f/2.0, over-the-shoulder three-quarter framing, the listener's blurred shoulder and back of the head in the near foreground edge, the speaker's face at least one third of the frame height",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds, the person's face at least one quarter of the frame height",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective",
}
LIGHT = {
    "fac_day": "morning daylight pouring through the open metal shutter, 5600K, dust and faint oil haze glowing in the light shafts, oily metal sheen",
    "office": "cool overhead fluorescent light mixed with grey window daylight, a slightly worn small-factory office",
    "tension": "cold overhead fluorescent light falling vertically, harsh shadows under the brows, high contrast",
    "office_n": "night, a single warm desk lamp 3200K in a dark office, deep shadows, faces readable",
    "home_day": "soft diffuse afternoon daylight from the balcony window, low contrast, a faint warm rim",
    "home_n": "night, a warm 3200K pendant lamp over the dining table, soft falloff into the dark room, faces readable",
    "hall_n": "a dark narrow hallway at night, a thin line of cold blue monitor light leaking from under a closed door, faint warm spill from the living room",
    "room_n": "a dark room lit only by the cold blue-white glow of three monitors and tiny green server LEDs, faces readable on a phone screen",
    "room_d": "daytime behind thick closed curtains, dim grey light leaking at the curtain edges",
    "room_warm": "night, a warm 3200K desk lamp mixed with the soft blue glow of a monitor, gentle and intimate",
    "fac_n": "a deserted factory at night, one fluorescent tube overhead, deep shadows between the machines, faces readable",
    "street_n": "night, a single sodium streetlight, cool blue ambient shadows",
    "rain": "overcast rainy evening, wet asphalt reflections, cool 5600K, falling rain visible against the light",
    "bank": "cool neutral even interior light, sterile",
    "meet": "cold flat overhead fluorescent light, grey window light, a tense quiet mood",
    "meet_power": "cold overhead fluorescent, a hard window backlight behind the seated older man, high contrast",
    "meet_door": "a strong white backlight from the corridor through the opening door, the figure edged with light, the face still readable, dramatic",
    "meet_turn": "warmer daylight now filling the room from the window, softer contrast",
    "sukiyaki": "warm 3200K pendant lamp over the table, steam glowing in the light",
    "morning": "clear early-morning golden light, long warm shadows, a hopeful glow",
    "screen": "a monitor screen glowing in a dark room",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}
SPK_KEY = {"父": "KEN", "母": "YUM", "大樹": "DAI", "叔父": "SEI", "亮介": "RYO", "真壁": "MAK"}


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, act="", vo=False, pin=None, replay=None):
    """kind: d(OmniHuman 립싱크) / face(사람 i2v) / empty(무인 i2v) / estill(무인·합성 면 정지) / pstill(말하는 화자 뒷모습 정지 + 편집 카메라) /
    ins(손·소품 — motion 있으면 i2v, 없으면 정지) / reuse:<id> / card.  vo=True = 화자 화면 밖(듣는 사람 리액션 위 목소리).
    who 항목 = "인물:의상". pin = 무대사 컷의 시작 시각 고정(초). replay = 같은 녹음을 다시 립싱크하는 줄(L01)."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc, subject=subject,
                line=line, fx=fx, motion=motion, expr=expr, act=act, vo=vo, pin=pin, replay=replay)


Kw, Kh, Dh, Ds, Dw, Y_, Se, R_, M_, Ka = ("KEN:work", "KEN:home", "DAI:hood", "DAI:suit", "DAI:shirt", "YUM:yum", "SEI:sei", "RYO:ryo", "MAK:mak", "KAN:kan")
OB = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, keeps looking "
      "toward the other person at the same three-quarter angle, hands keep doing what they do in the first frame; no exaggerated motion, the same person throughout.")
HOLD = " Head stays at the same angle, never turns toward the camera; only body, hands and breath move. Mouth stays closed, lips still — this person is NOT speaking."
SEATED = " SEATED/FURNITURE LOCKED: seated on the chair pulled in to the table, thighs under the table edge, forearms on the table; the chair never passes through the body."
MEET5 = (" PEOPLE LOCKED (meeting room seating): Makabe and Ryosuke seated on the far side of the long table, Kentaro and Yumiko seated on the near side, "
         "Seiji standing against the wall on the right; nobody else in the room.")

SHOTS = [
    # ① 후크 0:00~0:20 — 전부 본편 재사용(추가 생성 0), H3 타이틀은 직전 컷 블러 위(암전 없음)
    S("H0", "H", "reuse:S05e", "cu", "hall_n", "LA", [], None, "Reuse of S05e (Kentaro in the doorway shouting, handheld). L01 audio."),
    S("H1", "H", "reuse:S09g", "cu", "room_n", "EL", [], None, "Reuse of S09g (Kentaro's face washed by monitor light, eyes widening). Corner caption composited."),
    S("H2a", "H", "reuse:S11g", "ecu", "room_n", "EL", [], None, "Reuse of S11g (his hand slipping off the mouse)."),
    S("H2b", "H", "reuse:S11h", "ws", "room_n", "HA", [], None, "Reuse of S11h (high angle, Kentaro collapsing to his knees). NA0 audio + centre card."),
    S("H3", "H", "card", "ws", "room_n", "EL", [], None, "Title card over the blurred last frame of H2b (no black)."),

    # ② 발단·갈등 0:20~3:30
    S("S01a", "S01", "empty", "ews", "fac_day", "LA", [], "FAC_EXT", "Low wide of a narrow Ota-ku back alley in the morning: a small tin-roofed machine shop with its metal shutter half raised, utility poles, no signage.",
      motion="Thin steam drifts from a wall vent, morning light slowly brightens; nothing else moves."),
    S("S01b", "S01", "ins", "ecu", "fac_day", "LA", [], "LATHE", "Insert: an oily lathe chuck spinning, a bright curl of metal swarf peeling off the workpiece, coolant glistening.",
      motion="The chuck rotates steadily, the metal curl grows and falls away; coolant drips."),
    S("S01c", "S01", "ins", "ecu", "fac_day", "EL", [Kw], "LATHE", "Insert: Kentaro's thick weathered hands on the lathe handwheel, the small faded pale burn scar on the back of his RIGHT hand, no face.",
      motion="The hands turn the handwheel slowly and precisely; swarf curls in the background.", line="NA1"),
    S("S01d", "S01", "face", "ws", "fac_day", "SIDE", [Ka], "FAC_D", "Medium side view at the neighbouring lathe: Kaneda in profile, quietly focused on his work, silver browline glasses catching the light.",
      motion="He leans in slightly toward the work, a slow blink, hands adjusting the tool rest." + HOLD, expr="side"),
    S("S01e", "S01", "face", "ms", "fac_day", "EL", [Kw], "FAC_D", "Medium: Kentaro at three-quarter angle checking a machined part with a micrometer under the light, focused, proud.",
      motion="He turns the part slowly in his fingers, reads the micrometer, a small satisfied nod." + HOLD, line="NA2", expr="calm"),

    S("S02a", "S02", "face", "ms", "office", "EL", [Y_], "OFF_D", "Medium: Yumiko standing in the office doorway at three-quarter angle, holding a plain blank folder to her chest, watching her husband worriedly.",
      motion="She watches, her fingers tighten on the folder, a small worried breath." + HOLD, expr="worry"),
    S("S02b", "S02", "d", "ms", "office", "EL", [Kw], "OFF_DESK", "Chest-up medium: Kentaro seated at the steel office desk, an old cream desk phone receiver held to his ear, his other hand pressing on a closed blank ledger, three-quarter angle, swallowing humiliation.", line="L02",
      act="Kentaro listens on the phone and answers with a stiff restrained voice, jaw tight, his hand pressing harder on the ledger, swallowing the humiliation; breathes at each pause." + OB, expr="anger"),
    S("S02c", "S02", "face", "cu", "office", "HA", [Kw], "OFF_D", "High close-up: Kentaro slowly lowering the receiver onto the cradle and closing his eyes.",
      motion="He lowers the receiver slowly and closes his eyes, a long breath out through the nose." + HOLD, expr="grief"),
    S("S02d", "S02", "ins", "ecu", "office", "EL", [Kw], "OFF_DESK", "Insert: Kentaro's scarred hand gripping the edge of the closed blank ledger, knuckles whitening, a calculator beside it.",
      motion="The fingers tighten slowly on the ledger edge, then loosen." , line="NA3"),

    S("S03a", "S03", "empty", "ws", "hall_n", "LA", [], "HALL", "Wide of the dark hallway at night, the closed door at the end with a thin line of cold blue light leaking from underneath.",
      motion="The blue line under the door flickers faintly as if from a screen; nothing else moves."),
    S("S03b", "S03", "ins", "ecu", "hall_n", "EL", [], "HALL", "Insert at floor level: the gap under the closed wooden door, cold blue light flickering on the floorboards.",
      motion="The blue light flickers and shifts softly on the floor.", line="NA4"),
    S("S03c", "S03", "face", "ews", "room_d", "HA", [Dh], "ROOM_D", "High wide in the daytime: the curtained room, Daiki asleep under a blanket on the bed, face half hidden by the pillow, glasses folded on the shelf.",
      motion="He sleeps, the blanket rising and falling slowly with his breath; a thin line of daylight at the curtain edge." + HOLD, line="NA5", expr="hood"),
    S("S03d", "S03", "ins", "ecu", "hall_n", "HA", [Dh], "HALL", "Insert at night: a hand in a grey hoodie sleeve reaching out from the door gap and taking a plain tray with a covered rice bowl left on the hallway floor, no face.",
      motion="The hand slides the tray slowly in through the door gap."),
    S("S03e", "S03", "pstill", "ms", "hall_n", "SIDE", [Kh], "HALL", "From behind: Kentaro standing in the dark hallway in front of the closed door with a quiet low sigh, shoulders dropping, his face not visible, blue light at his feet.", line="L03", fx="pushin", expr="back"),

    S("S04a", "S04", "face", "ws", "home_n", "HA", [Kh, Y_], "HOME_DIN", "Wide of the small dining table at night under the pendant lamp: Kentaro and Yumiko eating in silence, a third chair and an untouched place setting empty.",
      motion="They eat slowly in silence, chopsticks moving; steam from the bowls." + SEATED + HOLD, expr="calm"),
    S("S04b", "S04", "d", "ots", "home_n", "EL", [Y_, Kh], "HOME_DIN", "Over Kentaro's blurred shoulder (left foreground): Yumiko at three-quarter angle scooping rice into a bowl with a rice paddle, a light uneasy smile.", line="L04",
      act="Yumiko mentions it lightly while scooping rice, a small uneasy smile, glancing at her husband to read his mood. Talking to her husband across the table." + SEATED + OB, expr="calm"),
    S("S04c", "S04", "face", "cu", "home_n", "EL", [Kh], "HOME_DIN", "Close-up of Kentaro hearing about the neighbour's son, his jaw tightening, eyes on his bowl.", line="L05", vo=True,
      motion="His jaw tightens, his eyes stay on the bowl, the chopsticks stop in his hand." + HOLD, expr="anger"),
    S("S04d", "S04", "ins", "ecu", "home_n", "EL", [Kh], "HOME_DIN", "Insert: Kentaro's scarred hand setting his chopsticks down across the rice bowl with a small click.",
      motion="The hand lays the chopsticks down across the bowl and stays still."),
    S("S04e", "S04", "face", "ms", "home_n", "SIDE", [Kh], "HOME_DIN", "Side medium: Kentaro seated at the table staring at his bowl, his wife only a blurred shape beyond, unmoved by her soothing words.", line="L06", vo=True,
      motion="He keeps staring at the bowl, his jaw working, a short breath through the nose." + SEATED + HOLD, expr="anger"),
    S("S04f", "S04", "d", "ms", "home_n", "LA", [Kh, Y_], "HOME_DIN", "Low medium past Yumiko's blurred shoulder: Kentaro setting his bowl down hard and raising his voice, brows knotted.", line="L07",
      act="NOT smiling. Kentaro puts the bowl down hard and raises his voice in frustration, brows knotted, pointing toward the hallway. Answering his wife." + SEATED + OB, expr="anger"),

    S("S05a", "S05", "ins", "ecu", "hall_n", "EL", [Kh], "HALL", "Insert: a scarred hand grabbing the doorknob of the closed door and yanking it open, blue light spilling out.",
      motion="The hand turns the knob and pushes the door open in one firm move; blue light spills over the hand."),
    S("S05b", "S05", "d", "ots", "room_n", "LA", [Kh, Dh], "ROOM_N", "Over Daiki's blurred grey hood (seated, right foreground), low angle: Kentaro standing in the doorway at three-quarter angle, chest-up, leaning forward, hallway light behind him.", line="L08",
      act="NOT smiling. Kentaro leans forward in the doorway and shouts at his son, face flushed, brows knotted, pointing at him. Shouting at his son at the desk." + OB, expr="anger"),
    S("S05c", "S05", "face", "ms", "room_n", "HA", [Dh], "ROOM_N", "High medium from the doorway: Daiki seated at the desk with his back half turned, monitor glow on his cheek, not turning around.",
      motion="He keeps his eyes on the screen, fingers resting on the keyboard, a slow breath; he does not turn." + HOLD, expr="hoodback"),
    S("S05d", "S05", "ins", "ecu", "room_n", "SIDE", [Dh], "ROOM_M", "Side close insert at desk height: Daiki's hands in grey hoodie sleeves resting on the black keyboard, fingers frozen mid-typing just above the keys, wrists on the desk edge, his arms continuing out of frame; the monitors behind are only a soft dim blue glow, out of focus.", line="L09", vo=True,
      motion="The fingers stop typing and stay frozen just above the keys; a faint tremble."),
    S("S05e", "S05", "d", "cu", "room_n", "LA", [Kh], "ROOM_N", "Extreme low chest-up close-up, handheld: Kentaro in the doorway at three-quarter angle, finger pointing out to the hallway, furious, a vein on his temple.", replay="L01", pin=101.205, fx="handheld",
      act="NOT smiling at any moment. Kentaro explodes, pointing out to the hallway, shouting at his son to get out, face twisted with rage, brows knotted, a vein on his temple. Shouting at his son." + OB, expr="anger"),
    S("S05f", "S05", "ins", "ecu", "room_n", "HA", [Dh], "ROOM_M", "Insert: Daiki's hands in grey hoodie sleeves quietly closing the laptop lid, the blue light vanishing from his fingers.", pin=106.3,
      motion="The hands close the laptop lid slowly and rest on it; the glow shrinks to darkness."),
    S("S05g", "S05", "d", "ots", "room_n", "EL", [Dh, Kh], "ROOM_N", "Over Kentaro's blurred shoulder (left foreground, in the doorway): Daiki seated at the desk turned toward his father at three-quarter angle, expressionless, one hand still on the closed laptop.", line="L10",
      act="Daiki answers in a low, flat voice without expression, his hand still on the closed laptop, holding back his feelings. Answering his father in the doorway." + OB, expr="hood"),
    S("S05h", "S05", "face", "cu", "room_n", "EL", [Kh], "ROOM_N", "Close-up of Kentaro in the doorway, caught off guard by the calm answer, silent, the anger faltering.",
      motion="He stands silent, his jaw working, a breath catches; eyes stay on his son." + HOLD, expr="anger"),
    S("S05i", "S05", "d", "cu", "room_n", "EL", [Dh], "ROOM_N", "Chest-up close-up: Daiki having just stood up beside the desk, at three-quarter angle looking straight at his father, steady sad eyes behind the glasses.", line="L11",
      act="Daiki looks straight at his father and says it quietly after a pause, steady eyes hiding sadness, voice calm. Speaking to his father in the doorway." + OB, expr="hood"),

    S("S06a", "S06", "ins", "ecu", "home_n", "HA", [Dh], "GENKAN", "Insert: hands in grey hoodie sleeves tying the laces of worn sneakers on the entryway step, one canvas bag beside them.",
      motion="The hands pull the laces tight and finish the knot."),
    S("S06b", "S06", "face", "ms", "home_n", "EL", [Dh], "GENKAN", "Medium at the front door: Daiki with a bag on his shoulder pausing at the open door, hearing his mother call.", line="L12", vo=True,
      motion="He stops, his shoulders tense, he lowers his eyes; he does not step out yet." + HOLD, expr="hood"),
    S("S06c", "S06", "face", "cu", "home_n", "EL", [Dh, Y_], "GENKAN", "Medium: Daiki at three-quarter angle giving his mother a small bow, Yumiko blurred in the foreground with her hand at her mouth.",
      motion="He bows his head slightly once to his mother and straightens; she trembles." + HOLD, expr="hood"),
    S("S06d", "S06", "face", "ws", "street_n", "EL", [Dh], None, "Wide: Daiki seen from behind walking away down the night street under one streetlight, a single bag on his shoulder, wind moving his hood.",
      motion="He walks slowly away from the camera; at the streetlight he turns his head slightly left toward the far factory, face never visible, then walks on." + HOLD, line="NA6", expr="hoodback"),
    S("S06e", "S06", "pstill", "ws", "home_n", "SIDE", [Kh], "HOME_LIV", "From behind: Kentaro sitting alone on the living-room sofa in the dark, only the dining lamp on, his face not visible.", fx="pushin", expr="back"),
    S("S06f", "S06", "ins", "ms", "home_n", "SIDE", [Kh], "HOME_LIV", "Side insert framed below the chin: Kentaro seated on the dark sofa seen from the side, his chest, cardigan and arms continuous down to his scarred hands resting on his knees, trembling slightly, gripping the trouser fabric; no face.", line="L13", vo=True,
      motion="The hands tremble slightly and grip the fabric, then loosen."),
    S("S06g", "S06", "empty", "ws", "hall_n", "LA", [], "HALL", "Low wide from the floor of the dark hallway: the son's door left ajar, the blue monitor light still glowing inside the empty room.",
      motion="The blue light inside glows steadily; a faint flicker; nothing else moves.", line="NA7"),
    S("S06h", "S06", "ins", "ecu", "hall_n", "LA", [], "HALL", "Insert: the old brass doorknob of the son's door, cold blue light reflected on it.",
      motion="The reflected light on the knob shifts very slightly.", line="NA8"),

    S("S07a", "S07", "ins", "ecu", "home_day", "HA", [Se], "HOME_LIV", "Insert: a plain gift box with a premium melon set down on the low wooden living-room table by a hand with a gold wristwatch, no face.",
      motion="The hand sets the box down and taps its lid twice."),
    S("S07b", "S07", "d", "ots", "home_day", "EL", [Se, Kh], "HOME_LIV", "Over Kentaro's blurred shoulder (left foreground): Seiji sitting down on the sofa at three-quarter angle, a mocking grin.", line="L14",
      act="Seiji sits down and says it with mocking glee, the corners of his mouth up, leaning back. Talking to his older brother across the table." + OB, expr="smug"),
    S("S07c", "S07", "face", "cu", "home_day", "HA", [Kh], "HOME_LIV", "High close-up of Kentaro seated, eyes down, enduring his brother's lecture, jaw tight.", line="L15", vo=True,
      motion="He keeps his eyes down, his jaw tightens, a slow breath." + HOLD, expr="anger"),
    S("S07d", "S07", "ins", "ms", "home_day", "EL", [Se], "HOME_LIV", "Medium insert on Seiji's chest and hands below the chin: leaning forward on the sofa, one hand with a gold wristwatch gesturing proudly, no face.", line="L16", vo=True,
      motion="The hand gestures proudly in small circles, then taps the knee."),
    S("S07e", "S07", "face", "ms", "home_day", "EL", [Y_], "HOME_LIV", "Medium: Yumiko standing at the kitchen side with a tray of tea, frozen, eyes lowered, hearing who Ryosuke works for.", line="L17", vo=True,
      motion="She freezes with the tray, her eyes lower, her fingers tighten on the tray." + HOLD, expr="worry"),
    S("S07f", "S07", "d", "ots", "home_day", "EL", [Se, Kh], "HOME_LIV", "Over Kentaro's blurred shoulder (left foreground): close shot of Seiji pushing up his gold-rimmed glasses with one finger, eyes narrowed, sneering.", line="L18",
      act="Seiji pushes up his glasses with one finger and sneers in a mocking, dismissive tone, eyes narrowed with contempt, the corner of his mouth raised. Looking down on his brother." + OB, expr="sneer"),
    S("S07g", "S07", "ins", "ecu", "home_day", "EL", [Kh], "HOME_LIV", "Insert: Kentaro's scarred fist slowly clenching on his knee.",
      motion="The fist clenches slowly and trembles."),

    S("S08a", "S08", "face", "ws", "home_n", "EL", [Kh], "HOME_DIN", "Wide: late at night, Kentaro sitting alone at the dark dining table with a glass of water, unable to sleep, only the pendant lamp on.",
      motion="He turns the glass slowly on the table, a long breath, eyes unfocused." + SEATED + HOLD, expr="calm"),
    S("S08b", "S08", "empty", "ws", "hall_n", "LA", [], "HALL", "Wide from the end of the dark hallway: the son's door at the far end, blue light still leaking from the gap, a low fan hum.",
      motion="The blue light flickers faintly; nothing else moves.", line="NA9"),
    S("S08c", "S08", "pstill", "ms", "hall_n", "SIDE", [Kh], "HALL", "From behind: Kentaro walking slowly down the dark hallway toward the son's door, his face not visible.", line="L19", fx="handheld", expr="back"),
    S("S08d", "S08", "ins", "ecu", "hall_n", "EL", [Kh], "HALL", "Insert: Kentaro's scarred hand resting on the son's doorknob, hesitating.",
      motion="The hand rests on the knob, hesitates, then slowly turns it.", line="NA10"),

    S("S09a", "S09", "empty", "ws", "room_n", "EL", [], "ROOM_N", "POV from the doorway: the door swinging slowly open into the dark room, revealing the glow of three monitors.",
      motion="The door swings slowly open; the monitor glow widens across the floor."),
    S("S09b", "S09", "face", "ms", "room_n", "SIDE", [Kh], "ROOM_N", "Low medium: Kentaro standing in the doorway, the cold monitor glow on his face, surprised.",
      motion="He stands still, his eyes move across the room, a slow breath." + HOLD, expr="calm"),
    S("S09c", "S09", "empty", "ws", "room_n", "EL", [], "ROOM_C", "Wide of the room, unexpectedly tidy: an organised desk with three monitors in sleep glow, a small humming server with blinking green LEDs, thick plain-covered books, "
      "a whiteboard with only line diagrams and arrows, a few empty plastic bottles in the corner.", motion="The server LEDs blink, the monitors glow softly; nothing else moves.", line="NA11"),
    S("S09d", "S09", "face", "cu", "room_n", "EL", [Kh], "ROOM_N", "Close-up of Kentaro leaning toward the monitor, squinting at something small on the bezel, puzzled.",
      motion="He leans in slightly and squints, a puzzled breath." + HOLD, expr="calm"),
    S("S09e", "S09", "ins", "ecu", "screen", "EL", [], "P_POSTIT", "Insert: a small yellow sticky note on the black bezel of a monitor (note blank; handwriting composited).", line="L20", vo=True),
    S("S09f", "S09", "ins", "ecu", "room_n", "OH", [Kh], "ROOM_M", "Overhead insert: rough scarred fingers pressing keys one by one on a black keyboard with blank keys, monitor glow.",
      motion="One finger presses a key, then another, slowly and carefully, eight times."),
    S("S09g", "S09", "face", "cu", "room_n", "EL", [Kh], "ROOM_N", "Close-up of Kentaro as the screen unlocks: cold blue-white light washing over his face, eyes widening.",
      motion="The light on his face brightens, his eyes widen slowly, his lips part." + HOLD, line="NA12", expr="stunned"),
    S("S09h", "S09", "face", "ecu", "room_n", "EL", [Kh], "ROOM_N", "Extreme close-up of Kentaro's eyes reflecting the glowing monitor, not blinking.",
      motion="The reflection in his eyes flickers, a single slow blink." + HOLD, expr="stunned"),

    # ③ 전개·위기 3:40~7:00
    S("S10a", "S10", "estill", "ms", "screen", "EL", [], "ROOM_M", "Full-screen monitor in the dark: a sales dashboard layout with plain panels (all Japanese UI text composited, lcd mode).", fx="pushin"),
    S("S10b", "S10", "pstill", "ots", "room_n", "SIDE", [Kh], "ROOM_N", "From directly behind Kentaro's desk chair, the camera low behind him: the glowing dashboard monitor in front of him, his face not visible, a quiet stunned murmur.", line="L21", fx="pushin", expr="back"),
    S("S10c", "S10", "estill", "ecu", "screen", "EL", [], "ROOM_M", "Extreme close-up on the monitor: a large monthly sales figure panel (figure composited).", line="L22", vo=True, fx="pushin"),
    S("S10d", "S10", "estill", "ms", "screen", "EL", [], "ROOM_M", "Monitor: a client list panel (company names composited).", line="NA13", fx="pan"),
    S("S10e", "S10", "estill", "ecu", "screen", "HA", [], "ROOM_M", "Monitor: a calendar panel with the same 2:00 AM meeting repeated every day (composited).", fx="tilt"),
    S("S10f", "S10", "d", "cu", "room_n", "LA", [Kh], "ROOM_N", "Low close-up of Kentaro at three-quarter angle, lips trembling, eyes beginning to wet, the realisation landing.", line="L23",
      act="NOT smiling. Kentaro speaks haltingly as the realisation lands, lips trembling, eyes beginning to wet." + WET_HOLD + OB, expr="grief"),
    S("S10g", "S10", "empty", "ews", "street_n", "LA", [], "HOUSE_N", "Low wide from the street at night: the modest two-storey house, only one upstairs window glowing cold blue at 2 AM.",
      motion="The blue window glows steadily, a faint flicker; clouds drift; nothing else moves.", line="NA14"),
    S("S10h", "S10", "ins", "ecu", "room_n", "EL", [Dh], "ROOM_M", "Insert (memory): Daiki's hands in grey hoodie sleeves typing fast on the blank keyboard at night, a headset cable, cold blue light.",
      motion="The fingers type quickly and steadily; the light flickers.", line="NA15"),

    S("S11a", "S11", "face", "ms", "room_n", "SIDE", [Kh], "ROOM_N", "Medium side view: Kentaro seated in his son's desk chair, small in front of the three glowing monitors, hand on the mouse.",
      motion="He moves the mouse slowly, his eyes scanning the screen, a slow breath." + HOLD, expr="calm"),
    S("S11b", "S11", "estill", "ms", "screen", "EL", [], "ROOM_M", "Monitor: a plain dark desktop with a single folder icon in the corner (label composited).", line="NA16", fx="pushin"),
    S("S11c", "S11", "estill", "ecu", "screen", "HA", [], "ROOM_M", "Extreme close-up of the single folder icon (folder name composited).", line="NA17", fx="pushin"),
    S("S11d", "S11", "face", "cu", "room_n", "EL", [Kh], "ROOM_N", "Close-up of Kentaro reading the screen, eyes moving line by line, lips parted.",
      motion="His eyes move slowly across the screen line by line, his lips part, his breath shortens." + HOLD, expr="stunned"),
    S("S11e", "S11", "estill", "ms", "screen", "EL", [], "ROOM_M", "Monitor: a plain memo window and a dependency graph panel (Japanese memo text and graph composited).", line="L24", vo=True, fx="pan"),
    S("S11f", "S11", "face", "ecu", "room_n", "EL", [Kh], "ROOM_N", "Extreme close-up of Kentaro's eyes welling as he reads the last memo line.", line="L25", vo=True,
      motion="NOT smiling. His eyes well up, a trembling breath, one slow blink." + WET_HOLD + HOLD, expr="grief"),
    S("S11g", "S11", "ins", "ecu", "room_n", "EL", [Kh], "ROOM_M", "Insert: Kentaro's scarred hand slipping off the mouse and dropping limply off the edge of the desk.",
      motion="The hand slides off the mouse and drops slowly off the desk edge."),
    S("S11h", "S11", "face", "ws", "room_n", "HA", [Kh], "ROOM_N", "High wide: Kentaro sliding down from the chair onto his knees on the floor in front of the glowing monitors.", fx="dollyzoom",
      motion="NOT smiling. He slides slowly down from the chair onto his knees, his hands landing on the floor, shoulders dropping; the chair stays in place." + HOLD, expr="grief"),
    S("S11i", "S11", "d", "cu", "room_n", "EL", [Kh], "ROOM_N", "Close-up: Kentaro kneeling on the floor at three-quarter angle, face toward the monitors, eyes wet but not flowing, throat tight.", line="L26",
      act="NOT smiling at any moment: brows knotted, the corners of the mouth pulled down, chin trembling. Kentaro chokes the words out in a restrained, strangled voice, holding back tears, speaking to himself about his son." + WET_HOLD + OB, expr="grief"),
    S("S11j", "S11", "face", "cu", "room_n", "SIDE", [Kh], "ROOM_N", "Close-up profile of Kentaro on the floor, the monitor glow on his cheek, a single tear finally running.",
      motion=NOSMILE + "His lips press tight." + TEARS_FLOW + HOLD, expr="grief"),
    S("S11k", "S11", "face", "ews", "room_n", "HA", [Kh], "ROOM_C", "High extreme wide from the corner: Kentaro small and alone on the floor of his son's room, from behind, the monitors glowing.",
      motion="He sits still on the floor, his shoulders shaking slightly with a breath; the monitors glow." + HOLD, line="NA18", expr="back"),

    S("S12a", "S12", "empty", "ws", "fac_day", "SIDE", [], "FAC_EXT", "Side wide in the morning: a black luxury sedan parked still in front of the small factory shutter, no people, the building still.",
      motion="The sedan stays parked and still, no headlights; morning light shifts slightly on the paint; the building does not move."),
    S("S12b", "S12", "face", "ms", "office", "SIDE", [R_, "SUB"], "OFF_D", "Side medium: Ryosuke entering the office from the left with a junior salaryman behind him, a plain document folder under his arm, cold face.",
      motion="He steps in from the left at the same distance, stops beside the desk; the junior follows behind; nobody walks toward the camera." + HOLD, expr="cold"),
    S("S12c", "S12", "d", "ots", "tension", "LA", [R_, Kw], "OFF_D", "Over Kentaro's blurred shoulder (seated, left foreground), low angle, dutch 5 degrees: Ryosuke standing at three-quarter angle opening a blank document folder, businesslike, no emotion.", line="L27", fx="dutch5",
      act="Ryosuke opens the folder and announces it in a flat, businesslike tone, no emotion in his eyes. Speaking to his uncle." + OB, expr="cold"),
    S("S12d", "S12", "face", "cu", "tension", "HA", [Kw], "OFF_D", "High close-up of Kentaro seated, hearing that all orders are cut, stunned.", line="L28", vo=True,
      motion="He freezes, his eyes widen, his breath stops." + HOLD, expr="stunned"),
    S("S12e", "S12", "d", "ots", "tension", "EL", [Kw, R_], "OFF_D", "Over Ryosuke's blurred shoulder (right foreground): Kentaro half-risen from his chair, both hands pressing on the desk, chest-up, betrayal and anger.", line="L29",
      act="NOT smiling. Kentaro pushes himself up with both hands on the desk and protests with anger and betrayal, voice rising. Answering his nephew." + OB, expr="anger"),
    S("S12f", "S12", "ins", "ecu", "tension", "EL", [R_], "OFF_DESK", "Insert: two fingers in a charcoal suit sleeve sliding a blank document across the steel desk, stopping in front of Kentaro's scarred hand.", line="L30", vo=True,
      motion="The paper slides smoothly across the desk under two fingers and stops in front of the other hand; the hand twitches."),
    S("S12h", "S12", "d", "cu", "tension", "LA", [R_], "OFF_D", "Low close-up of Ryosuke tapping the blank document with the tip of a pen, a faint cold smirk.", line="L31",
      act="Ryosuke taps the paper with his pen tip and states the price clearly in a dismissive, mocking tone, a faint cynical smirk. Speaking to his uncle." + OB, expr="aside"),
    S("S12i", "S12", "d", "cu", "tension", "HA", [Kw], "OFF_D", "High close-up of Kentaro, disbelieving, face twisting, trembling voice.", line="L32",
      act="NOT smiling. Kentaro asks in a trembling voice in disbelief, his face twisting, his breath ragged. Asking his nephew." + OB, expr="grief"),
    S("S12j", "S12", "d", "cu", "tension", "EL", [R_], "OFF_D", "Close-up of Ryosuke with his eyes on the document, not meeting his uncle's gaze.", line="L33",
      act="Ryosuke keeps his eyes on the papers and answers briefly and coldly, not meeting his uncle's eyes." + OB, expr="aside"),

    S("S13a", "S13", "d", "ots", "office", "EL", [Se, Kw], "OFF_D", "Over Kentaro's blurred shoulder (left foreground): Seiji at three-quarter angle patting his brother's shoulder with a fake sympathetic smile.", line="L34",
      act="Seiji pats his brother's shoulder and says it with fake sympathy, a sneering smile. Talking to his brother." + OB, expr="sneer"),
    S("S13b", "S13", "face", "ms", "office", "EL", [Kw], "OFF_D", "Medium: Kentaro having turned his back on his brother, facing the window toward camera at three-quarter angle, jaw clenched; Seiji only a blurred shape far behind him.", line="L35", vo=True,
      motion="He stands rigid, his jaw clenches, a breath through the nose; he does not turn back." + HOLD, expr="anger"),
    S("S13c", "S13", "d", "cu", "office", "EL", [Kw], "OFF_D", "Chest-up close-up: Kentaro with his back to his brother (who is blurred far behind), three-quarter angle toward camera, rigid shoulders, low voice.", line="L35a",
      act="NOT smiling. Kentaro says it low and clipped without turning around, restrained anger, rigid shoulders." + OB, expr="anger"),
    S("S13d", "S13", "d", "ms", "office", "LA", [Se], "OFF_D", "Low medium: Seiji in the office doorway, already turned back over his shoulder toward his brother, a sneering grin.", line="L35b",
      act="Seiji looks back from the doorway and says it lightly in a mocking tone with a sneering grin, pronouncing the deadline clearly. Talking to his brother." + OB, expr="sneer"),
    S("S13e", "S13", "face", "ws", "fac_day", "EL", [Kw, Ka], "FAC_D", "Wide on the factory floor: Kentaro standing silent, staring at the lathe in the foreground; behind him Kaneda stops working and watches him with concern.",
      motion="Kentaro stares at the lathe without moving; Kaneda lowers his hands from the machine and looks at him with concern." + HOLD, expr="concern"),

    S("S14a", "S14", "face", "ws", "bank", "EL", [Kw, "BANK"], None, "Wide, far: Kentaro bowing low at a plain bank counter, small in the frame.",
      motion="He bows low and holds the bow; the clerk shape shakes its head slightly." + HOLD, expr="back"),
    S("S14b", "S14", "face", "ws", "rain", "SIDE", [Kw], None, "Wide from behind: Kentaro walking home in the rain without an umbrella, shoulders hunched.",
      motion="He walks slowly away from the camera in the rain, shoulders hunched; rain falls steadily." + HOLD, line="NA19", expr="back"),
    S("S14c", "S14", "face", "ms", "fac_day", "SIDE", [Ka, "CREW"], "FAC_D", "Medium from behind and the side: Kaneda and two craftsmen silently wiping down their lathes, backs to camera.",
      motion="They wipe the machines slowly with cloths, in silence." + HOLD, expr="back"),
    S("S14d", "S14", "face", "ews", "fac_day", "HA", [Kw, "CREW"], "FAC_D", "High extreme wide of the factory floor: twelve small figures of craftsmen at their machines, Kentaro standing alone at the office window above, from behind.",
      motion="The craftsmen work slowly at their machines; Kentaro stands still at the window." + HOLD, line="NA19a", expr="back"),
    S("S14e", "S14", "ins", "ecu", "office", "LA", [], "OFF_D", "Insert: a plain round office wall clock with NO numerals and NO markings, the thin second hand moving.",
      motion="The second hand ticks forward steadily."),

    S("S15a", "S15", "face", "ws", "office_n", "HA", [Y_, Kw], "OFF_N", "High wide of the dark office at night: Yumiko seated at the desk under the single lamp closing a thick blank ledger, Kentaro seated across from her, head lowered.",
      motion="She closes the ledger slowly and rests her hands on it; he does not move." + SEATED + HOLD, expr="worry"),
    S("S15b", "S15", "face", "cu", "office_n", "HA", [Kw], "OFF_N", "High close-up of Kentaro seated at the desk under the lamp, head lowered, hearing his wife's worry about next week's payments.", line="L36", vo=True,
      motion="He keeps his head lowered, eyes closed for a moment, a long tired breath." + SEATED + HOLD, expr="grief"),
    S("S15c", "S15", "face", "cu", "office_n", "EL", [Y_], "OFF_N", "Close-up of Yumiko hearing her husband's curt answer, hesitating, her hand moving toward the desk drawer.", line="L37", vo=True,
      motion="She hesitates, bites her lip, her hand moves slowly toward the drawer." + HOLD, expr="worry"),
    S("S15d", "S15", "ins", "ecu", "office_n", "EL", [Y_], "OFF_N", "Insert: Yumiko's trembling hands sliding a plain bank passbook across the desk under the lamp, no face.", line="L38", vo=True,
      motion="The trembling hands slide the passbook slowly across the desk and stop, then pull back."),
    S("S15e", "S15", "ins", "ecu", "office_n", "OH", [Kw], "OFF_N", "Overhead insert: an open bank passbook page with plain ruled rows (entries composited), a scarred finger resting on the rows."),
    S("S15f", "S15", "d", "cu", "office_n", "EL", [Y_], "OFF_N", "Close-up of Yumiko at three-quarter angle, tears welling but not falling, voice trembling.", line="L39",
      act=NOSMILE + "Yumiko tells him with tears welling and a trembling voice, stretching the word for 'all along'." + WET_HOLD + OB, expr="worry"),
    S("S15g", "S15", "d", "ots", "office_n", "HA", [Kw, Y_], "OFF_N", "Over Yumiko's blurred shoulder (right foreground), high angle: Kentaro gripping the passbook at three-quarter angle, wet eyes, his voice fading.", line="L39a",
      act=NOSMILE + "Kentaro grips the passbook with trembling hands, his voice fading away, wet eyes on the page." + WET_HOLD + OB, expr="grief"),
    S("S15h", "S15", "estill", "ecu", "office_n", "EL", [], "OFF_N", "Extreme close-up: the repeated deposit rows on the passbook page (composited), lamp light.", line="NA20", fx="tilt"),
    S("S15i", "S15", "face", "ecu", "office_n", "SIDE", [Kw], "OFF_N", "Choker extreme close-up of Kentaro's eyes and brow, his breath stopping.",
      motion=NOSMILE + "His breath stops, his eyes fill, one slow blink." + WET_HOLD + HOLD, expr="grief"),

    S("S16a", "S16", "empty", "ews", "fac_n", "HA", [], "FAC_N", "Extreme wide of the deserted factory at night, machines silent, one fluorescent tube lit.",
      motion="The single fluorescent tube flickers faintly once; nothing else moves."),
    S("S16b", "S16", "face", "ms", "fac_n", "HA", [Kw], "FAC_N", "Medium: Kentaro standing among the silent machines with a phone held to his ear, waiting, three-quarter angle, mouth closed.",
      motion="He waits with the phone at his ear, eyes lowered, a slow breath; nobody answers." + HOLD, expr="grief"),
    S("S16c", "S16", "ins", "ecu", "fac_n", "EL", [Kw], "FAC_N", "Insert: Kentaro's scarred hand slowly lowering the phone, the screen dark.",
      motion="The hand lowers the phone slowly to his side.", line="NA20a"),
    S("S16d", "S16", "pstill", "ws", "fac_n", "SIDE", [Kw], "LATHE", "From behind: Kentaro with his hand resting on the silent lathe, shoulders trembling, his face not visible.", line="L40", fx="handheld", expr="back"),
    S("S16e", "S16", "ins", "ecu", "fac_n", "LA", [], "OFF_D", "Insert: the plain round wall clock with NO numerals, the second hand moving in the dark.", pin=408.2,
      motion="The second hand ticks forward steadily."),
    S("S16f", "S16", "empty", "ews", "street_n", "LA", [], "FAC_EXT", "Low extreme wide of the small factory in the dark back alley at night, one light in the window.",
      motion="The one window light glows; a faint wind; nothing else moves.", line="NA21"),
    S("S16g", "S16", "estill", "ms", "meet", "LA", [], "MEET_DOOR", "The closed meeting-room door in cold light, empty (preview card composited).", fx="pushin"),

    # ④ 절정·결말 7:10~10:20
    S("S17a", "S17", "face", "ews", "meet_power", "EL", [M_, R_, Kw, Y_, Se], "MEET", "Wide of the meeting room: Makabe and Ryosuke seated on the far side of the long table, Kentaro and Yumiko on the near side from behind, Seiji leaning against the right wall.",
      motion="They sit still; Makabe taps a finger once; Seiji folds his arms." + MEET5 + HOLD, expr="cold"),
    S("S17b", "S17", "ins", "ecu", "meet", "HA", [], "MEET_T", "Insert: a stapled sale contract (title composited) and a black fountain pen on the grey table.", fx="pushin"),
    S("S17c", "S17", "d", "ots", "meet_power", "LA", [M_, Kw], "MEET_T", "Over Kentaro's blurred shoulder (left foreground), low angle: Makabe at three-quarter angle leaning back deep in his chair, one finger tapping the table, looking down.", line="L41",
      act="Makabe leans back and says it low and intimidating, tapping the table with one finger, looking down at Kentaro." + SEATED + OB, expr="cold"),
    S("S17d", "S17", "ins", "ms", "meet", "HA", [Kw], "MEET_T", "Medium insert on Kentaro's chest and arms at the table, his scarred hand holding the fountain pen over the contract, trembling, no face (framed below the chin).",
      motion="The hand trembles, the pen tip wavers over the paper."),
    S("S17e", "S17", "ins", "ecu", "meet", "OH", [Kw], "MEET_T", "Overhead insert: the pen tip descending to within a centimetre of the signature line.", line="L42", vo=True,
      motion="The pen tip slowly descends and stops just above the paper."),

    S("S18a", "S18", "ins", "ecu", "meet", "LA", [], "MEET_DOOR", "Insert: the meeting-room door handle turning from outside.",
      motion="The handle turns slowly down; the door begins to open."),
    S("S18b", "S18", "face", "ws", "meet_door", "LA", [Ds], "MEET_OPEN", "Low wide: the door open, Daiki in a dark navy suit standing in the doorway, backlit by the corridor light, glasses catching the light.",
      motion="He takes two slow steps into the room at the same distance and stops; the backlight edges his shoulders; head steady." + HOLD, expr="calm"),
    S("S18c", "S18", "face", "cu", "meet_door", "LA", [Ds], "MEET_OPEN", "Low close-up of Daiki, backlit, calm resolute eyes behind the glasses scanning the room.",
      motion="His eyes move across the room and settle, a calm breath." + HOLD, expr="calm"),
    S("S18d", "S18", "d", "ms", "meet", "EL", [R_], "MEET", "Medium: Ryosuke half-rising from his chair at three-quarter angle, flustered, eyes wide.", line="L43",
      act=NOSMILE + "Ryosuke half-rises from his chair, flustered, eyes wide, asking his cousin why he is here." + OB, expr="shock"),
    S("S18e", "S18", "face", "cu", "meet_door", "SIDE", [Ds], "MEET", "Low close-up of Daiki standing, unbothered by his uncle's sneer, calm eyes on his father only.", line="L44", vo=True,
      motion="He ignores the sneer, his eyes stay calm and steady, one slow blink." + HOLD, expr="cool"),
    S("S18f", "S18", "face", "cu", "meet", "HA", [Kw], "MEET_T", "High close-up of Kentaro seated, the pen still in his hand, staring at his son in disbelief.",
      motion="He stares at his son, his lips part, the pen still in his hand." + SEATED + HOLD, expr="stunned"),
    S("S18g", "S18", "d", "ots", "meet_door", "LA", [Ds, Kw], "MEET", "Over Kentaro's blurred shoulder (seated, left foreground), low angle: Daiki standing at the table edge at three-quarter angle looking only at his father, quiet and firm.", line="L45",
      act="Daiki looks only at his father and tells him quietly and firmly, a flicker of feeling in his eyes for the first time. Speaking to his father." + OB, expr="calm"),

    S("S19a", "S19", "d", "ots", "meet", "EL", [Ds, M_], "MEET", "Over Makabe's blurred shoulder (right foreground): Daiki at three-quarter angle turning his gaze to Makabe, calm certainty.", line="L46",
      act="Daiki turns to Makabe and speaks clearly and calmly, a pause before the key point, quiet certainty. Speaking to Makabe." + OB, expr="cool"),
    S("S19b", "S19", "ins", "ecu", "meet", "EL", [M_], "MEET_T", "Insert: Makabe's hand on the table, fingers stopping mid-tap and gripping into a fist.", line="L47", vo=True,
      motion="The tapping finger stops; the hand slowly closes into a tight fist."),
    S("S19c", "S19", "ins", "ms", "meet", "EL", [Ds], "MEET_T", "Medium insert on Daiki's chest and hands below the chin: taking a slim tablet out of a plain black bag at the table, no face.", line="L48", vo=True,
      motion="The hands draw the tablet out of the bag smoothly and hold it."),
    S("S19d", "S19", "face", "cu", "meet", "HA", [M_], "MEET", "High close-up of Makabe seated, the colour draining from his face as he listens, a bead of sweat at the temple.", line="L49", vo=True,
      motion=NOSMILE + "He listens rigidly, the colour draining from his face." + SWEAT_FLOW + SEATED + HOLD, expr="stern"),
    S("S19e", "S19", "ins", "ecu", "meet_turn", "OH", [Ds], "P_TABLET", "Overhead insert: a tablet set down on the grey table by Daiki's hand (letter of intent screen composited).",
      motion="The hand sets the tablet down flat on the table and slides it forward a little."),
    S("S19f", "S19", "d", "cu", "meet_turn", "LA", [Ds], "MEET", "Low medium: Daiki standing at the table at three-quarter angle, one hand on the tablet, stressing the company name.", line="L50",
      act="Daiki rests his hand on the tablet and says it with quiet emphasis on the company name. Speaking to Makabe." + OB, expr="cool"),
    S("S19g", "S19", "face", "ms", "meet_turn", "EL", [R_], "MEET", "Medium: Ryosuke seated, flipping through papers in his folder in a panic, pale.",
      motion=NOSMILE + "He flips the pages quickly back and forth, pale, breath short." + SEATED + HOLD, expr="shock"),

    S("S20a", "S20", "face", "cu", "meet_turn", "SIDE", [M_], "MEET", "High chest-up close-up of Makabe, pale, a thin line of cold sweat running down from the temple.",
      motion=NOSMILE + "He swallows hard." + SWEAT_FLOW + SEATED + HOLD, expr="stern"),
    S("S20b", "S20", "ins", "ecu", "meet_turn", "SIDE", [Ds], "MEET_T", "Side insert at table height: Daiki's hand in a navy suit sleeve setting a thick plain file binder down flat on the grey table, tabs without writing, his arm continuing out of frame; no face.", line="L51", vo=True,
      motion="The hand sets the thick binder down flat and pushes it forward a little."),
    S("S20c", "S20", "face", "cu", "meet_turn", "EL", [Y_], "MEET", "Close-up of Yumiko seated, a hand at her mouth, eyes wet, watching her son.",
      motion="Her hand stays at her mouth, her eyes wet, a trembling breath." + WET_HOLD + SEATED + HOLD, expr="worry"),
    S("S20d", "S20", "d", "ots", "meet_turn", "EL", [Ds, Kw], "MEET", "Over Kentaro's blurred shoulder (left foreground): Daiki turning to his father at three-quarter angle, softer eyes, trust.", line="L52",
      act="Daiki turns to his father and says it gently, trusting eyes. Speaking to his father." + OB, expr="smile"),
    S("S20e", "S20", "d", "cu", "meet_turn", "HA", [M_], "MEET", "High chest-up close-up: Makabe having sprung up from his chair, panicked, sweat on his forehead, NOT smiling.", line="L53",
      act=NOSMILE + "Makabe has jumped up and pleads urgently, panic in his eyes, sweat on his forehead, both hands raised slightly. Pleading to Kentaro." + OB, expr="panic"),
    S("S20f", "S20", "face", "ews", "meet_turn", "BE", [M_], "MEET", "Bird's-eye view straight down, dutch 7 degrees: Makabe kneeling on the floor beside the long table, head bowed so his face is hidden, hands on the floor.", line="L54", vo=True, fx="dutch7",
      motion="KNEELING, NOT lying down: he stays on his knees with his head bowed, his shoulders trembling; his face stays hidden." + HOLD, expr="stern"),
    S("S20g", "S20", "face", "cu", "meet_turn", "LA", [Kw], "MEET", "Low close-up of Kentaro seated, looking down at the kneeling man with firm, quiet eyes.",
      motion="He looks down steadily, a slow breath, his jaw set." + SEATED + HOLD, expr="calm"),

    S("S21a", "S21", "ins", "ecu", "meet_turn", "EL", [Kw], "MEET_T", "Insert: Kentaro's scarred hands tearing the stapled contract in half.",
      motion="Both hands grip the contract firmly and tear it cleanly in half all the way down, never letting go."),
    S("S21b", "S21", "d", "cu", "meet_turn", "LA", [Kw], "MEET", "Low close-up of Kentaro at three-quarter angle, the torn halves set down, calm and firm.", line="L55",
      act="Kentaro says it calmly and firmly without raising his voice, resolved steady eyes. Speaking to Makabe." + OB, expr="calm"),
    S("S21c", "S21", "face", "cu", "meet_turn", "HA", [M_], "MEET", "High close-up of Makabe on his knees looking up, stunned.",
      motion=NOSMILE + "He looks up, stunned, his mouth half open, frozen." + HOLD, expr="stern"),
    S("S21d", "S21", "d", "cu", "meet_turn", "EL", [Kw], "MEET", "Medium: Kentaro standing at three-quarter angle beginning a dignified slight bow, hands at his sides.", line="L56",
      act="Kentaro thanks them politely and with dignity, then lowers his head slightly in a small bow within 15 degrees, voice steady and quiet." + OB, expr="calm"),

    S("S22a", "S22", "face", "cu", "meet_turn", "HA", [R_], "MEET", "High close-up of Ryosuke looking down at his vibrating phone, the colour draining from his face.",
      motion=NOSMILE + "He stares down at the phone, his face going pale, his breath stopping." + HOLD, expr="shock"),
    S("S22b", "S22", "d", "cu", "meet_turn", "EL", [Se, Ds], "MEET", "Medium: Seiji approaching his nephew with a servile forced grin, hands rubbing together, sweat at the temple.", line="L57",
      act="Seiji approaches with a servile forced grin, rubbing his hands, stammering flattery, sweat at the temple. Fawning over his nephew." + OB, expr="forced"),
    S("S22c", "S22", "d", "ots", "meet_turn", "EL", [Ds, Se], "MEET", "Over Seiji's blurred shoulder (right foreground): Daiki at three-quarter angle looking straight at his uncle, calm faint smile.", line="L58",
      act="Daiki looks straight at his uncle and says it quietly and clearly, a calm faint smile. Speaking to his uncle." + OB, expr="smile"),
    S("S22d", "S22", "face", "ms", "meet_turn", "SIDE", [Se], "MEET", "High medium of Seiji standing frozen, the forced grin stuck on his face.",
      motion="The forced grin freezes and fades, his eyes dart." + HOLD, expr="forced"),
    S("S22e", "S22", "face", "ws", "meet_turn", "EL", [Kw, Ds], "MEET", "Wide: Kentaro seated in the foreground at three-quarter angle looking across the room at his son standing by the window, eyes softening with pride.",
      motion="His eyes soften, a slow breath, a faint tremble at the lips." + WET_HOLD + HOLD, expr="calm"),

    S("S23a", "S23", "ins", "ecu", "hall_n", "EL", [Kh], "HALL", "Insert: Kentaro's scarred knuckles knocking gently twice on the son's closed door, warm light from under it.",
      motion="The knuckles knock twice gently and rest on the door."),
    S("S23b", "S23", "d", "cu", "hall_n", "EL", [Kh], "HALL", "Close-up: Kentaro at the closed door at three-quarter angle, hand resting on the wood, hesitant, warm light leaking from under the door.", line="L59",
      act="Kentaro asks quietly through the door, voice trembling slightly, awkward and hesitant, his hand resting on the wood. Speaking to his son through the door." + OB, expr="grief"),
    S("S23c", "S23", "face", "cu", "hall_n", "LA", [Kh], "HALL", "Low close-up of Kentaro at the closed door hearing his son's small laugh through it, his tense face loosening.", line="L60", vo=True,
      motion="His tense face loosens, a breath of relief, his hand stays on the door." + HOLD, expr="grief"),
    S("S23d", "S23", "face", "ws", "room_warm", "EL", [Kh, Dw], "ROOM_N", "Wide inside the room: Kentaro bowing deeply to his seated son in silence, Daiki turned in his chair.",
      motion="Kentaro bows deeply and holds the bow; Daiki looks at him without moving." + HOLD, expr="grief"),
    S("S23e", "S23", "d", "cu", "room_warm", "HA", [Kh], "ROOM_N", "High close-up: Kentaro with his head still lowered about 15 degrees, face visible, eyes wet, throat tight.", line="L61",
      act=NOSMILE + "Kentaro apologises with his head still lowered, his voice catching in his throat, holding back tears. Apologising to his son." + WET_HOLD + OB, expr="grief"),
    S("S23f", "S23", "face", "cu", "room_warm", "EL", [Dw], "ROOM_N", "Close-up of Daiki seated, listening to his father, eyes wetting behind the glasses.", line="L62", vo=True,
      motion="His eyes wet, he swallows, a slow breath." + WET_HOLD + HOLD, expr="calm"),
    S("S23g", "S23", "d", "ms", "room_warm", "EL", [Dw, Kh], "ROOM_N", "Medium: Daiki seated at three-quarter angle shrugging slightly, a faint smile, answering his father.", line="L63",
      act="Daiki shrugs slightly and answers plainly, a faint smile. Speaking to his father." + OB, expr="smile"),
    S("S23h", "S23", "estill", "ecu", "room_warm", "EL", ["KID"], "P_PHOTO", "Insert: an old faded framed photograph beside the monitor: a small boy and a young father standing in front of a lathe in a small factory, warm faded colours.", line="L64", vo=True, fx="pushin"),
    S("S23j", "S23", "face", "cu", "room_warm", "SIDE", [Kh], "ROOM_N", "High close-up of Kentaro listening, eyes wet, a trembling small smile.",
      motion="His eyes wet, his lips tremble into a small smile." + TEARS_FLOW + HOLD, expr="grief"),
    S("S23k", "S23", "d", "ots", "room_warm", "EL", [Dw, Kh], "ROOM_N", "Over Kentaro's blurred shoulder (left foreground): Daiki at three-quarter angle looking at his father with a faint smile.", line="L65",
      act="Daiki looks at his father and smiles faintly, saying it gently. Speaking to his father." + OB, expr="smile"),

    S("S24a", "S24", "ins", "ecu", "sukiyaki", "HA", [], "P_SUKI", "Insert: a cast-iron sukiyaki pot bubbling on the table, marbled beef, tofu and leeks, steam rising.",
      motion="The broth bubbles and sizzles, steam rises."),
    S("S24b", "S24", "d", "ots", "sukiyaki", "EL", [Y_, Dh], "HOME_DIN", "Over Daiki's blurred grey hood (left foreground): Yumiko at the table at three-quarter angle, smiling with wet eyes, steam between them.", line="L66",
      act="Yumiko says it brightly with a smile and wet eyes, steam rising in front of her. Speaking to her son." + SEATED + OB, expr="calm"),
    S("S24c", "S24", "ins", "ecu", "sukiyaki", "HA", [Kh], "HOME_DIN", "Insert: Kentaro's scarred hand with chopsticks placing the first piece of beef into his son's bowl.",
      motion="The chopsticks lift a piece of beef from the pot and lay it gently in the other bowl."),
    S("S24d", "S24", "face", "ws", "sukiyaki", "EL", [Kh, Y_, Dh], "HOME_DIN", "Wide: the three of them around the small dining table with the steaming pot, the third chair finally taken.",
      motion="They eat slowly; steam rises; Yumiko laughs softly." + SEATED + HOLD, line="NA22", expr="calm"),
    S("S24e", "S24", "empty", "ws", "room_warm", "LA", [], "HALL", "Wide of the hallway: the son's door now left wide open, warm light flowing out into the hall.",
      motion="Warm light glows steadily from the open door; nothing else moves.", line="NA23"),
    S("S24f", "S24", "ins", "ecu", "morning", "EL", [Ka], "LATHE", "Insert in the morning: Kaneda's hands starting the lathe again, the chuck beginning to spin, golden light.",
      motion="The hands press the start lever, the chuck begins to rotate, swarf curls.", line="NA24"),
    S("S24g", "S24", "face", "cu", "morning", "EL", [Ka], "FAC_D", "Close-up of Kaneda at his lathe in the morning, a quiet warm smile, glasses catching the golden light.",
      motion="He smiles quietly, a slow nod, his hands on the machine." + HOLD, expr="smile"),
    S("S24h", "S24", "face", "ews", "morning", "LA", [Kw, Ds], "FAC_EXT", "Low extreme wide from behind: father and son standing side by side in front of the factory shutter in the morning light.", fx="pullback",
      motion="They stand side by side looking at the factory; the shutter rises slowly; their backs stay to the camera." + HOLD, expr="back"),
]

SPK_WHO = {"父": "KEN:work", "母": Y_, "大樹": Ds, "叔父": Se, "亮介": R_, "真壁": M_}
# 듣는 사람 VO 컷의 앞 화자 어깨(ots 자동)를 쓰지 않는 컷 — 화자가 뒤에 있거나 화면 밖이 자연스러운 구도
VO_OTS_SKIP = {"S06b", "S13b", "S07e", "S19d", "S23f", "S11f", "S12d", "S23c", "S18e", "S04e"}  # S23c 문 너머·S18e 앞 인물 뒤바뀜(Kill Gate 1차)
SCENE_SPK_WARD = {"S04": {"父": Kh}, "S05": {"父": Kh, "大樹": Dh}, "S06": {"大樹": Dh, "父": Kh}, "S07": {"父": Kh}, "S15": {"父": Kw},
                  "S23": {"父": Kh, "大樹": Dw}, "S24": {"大樹": Dh}}

CARDS = {"H2b": "息子は、ずっと隠していた。", "H3": "引きこもりの息子", "S13e": "契約まで　あと３日", "S14e": "契約まで　あと２日",
         "S16e": "契約まで　あと１日", "S16g": "この後――会議室の扉が開く"}
JA_OVERLAY = {
    "H1": "구석 소자막 「翌日の夜」 (대본 「三日後」를 줄거리 정합으로 교정 — S07 翌日 → S08 その夜)", "H2b": "중앙 카드(굵은 명조)", "H3": "타이틀",
    "S01a": "구석 소자막 「その日の朝」", "S07a": "구석 소자막 「翌日」", "S12a": "구석 소자막 「翌朝」",
    "S01d": "金田 명찰 「金田」", "S13e": "金田 명찰 + 카드", "S14c": "金田 명찰", "S24f": "—", "S24g": "金田 명찰 「金田」",
    "S09e": "포스트잇 손글씨 「パス：工場の創業日」", "S10a": "대시보드(lcd) 月間売上 ¥12,500,000 · 「瀬尾大樹 — リードセキュリティアーキテクト」",
    "S10c": "대시보드 숫자 확대 「¥12,500,000」(lcd)", "S10d": "고객 목록 ノースゲート・システムズ / 東証プライム上場IT企業 / ヴァイスベルク研究所(lcd)",
    "S10e": "일정표 「午前2:00 オンライン会議（現地時間 午前10:00）」 매일 반복(lcd)", "S11b": "바탕화면 폴더 1개(lcd)", "S11c": "폴더명 「父さんの工場」(lcd)",
    "S11e": "메모 「鳳凰の値下げ、あと一年で限界。新しい取引先を、必ず見つける」「父さんには、決まってから話す」 + 의존도 그래프 87%(lcd)",
    "S15e": "통장 실물 양식(年月日/摘要/お支払金額/お預り金額/差引残高, 「06-10-25 振込 セオ ダイキ 200,000」 8줄 이상)", "S15h": "같은 통장 줄 확대",
    "S17b": "계약서 표제 「事業譲渡契約書」", "S17d": "같은 계약서", "S17e": "같은 계약서 서명란 「署名」", "S19e": "태블릿 「ヴァイスベルク研究所 × 瀬尾精工　直接取引　意向書」(lcd)",
    "S21a": "같은 계약서(찢김)", "S16g": "예고 카드", "S13e_": "",
}
JA_OVERLAY.pop("S13e_")
G = {
    "factory": "lathes whirring, metal swarf clinking into a tray, a distant air compressor", "office": "a wall clock ticking, a fluorescent tube humming, a ledger page turning",
    "home_n": "a refrigerator humming, a wall clock ticking, chopsticks touching a ceramic bowl", "hall": "a low computer fan hum behind a closed door, muffled rapid keyboard typing",
    "room": "computer server fans humming, an electric hum, a mouse click", "street": "a night street, distant traffic, light wind, footsteps on asphalt",
    "living": "a wall clock ticking, a cardboard box set on a wooden table", "rain": "steady rain on asphalt, water running in a gutter, distant traffic",
    "bank": "a ticket machine chime, paper rustling at a counter", "fac_n": "an empty factory at night, a fluorescent tube buzzing, wind rattling a metal shutter",
    "meet": "an air conditioner hum, a wall clock ticking, papers slid on a table", "sukiyaki": "sukiyaki sizzling and bubbling in an iron pot, chopsticks on bowls",
    "morning": "morning sparrows, a lathe motor starting up, a metal shutter rolling up", "car": "a car door shutting outside, an engine idling",
    "clock": "a single clock tick, echoing", "door": "a door handle turning, a heavy door opening, measured footsteps on vinyl floor",
    "phone": "a phone ringing out unanswered, a ring tone repeating", "keys": "keyboard keys pressed one by one, an unlock chime",
}
AMB_BY_SCENE = {"S01": "factory", "S02": "office", "S03": "hall", "S04": "home_n", "S05": "room", "S06": "street", "S07": "living", "S08": "home_n",
                "S09": "room", "S10": "room", "S11": "room", "S12": "office", "S13": "office", "S14": "rain", "S15": "office", "S16": "fac_n",
                "S17": "meet", "S18": "meet", "S19": "meet", "S20": "meet", "S21": "meet", "S22": "meet", "S23": "home_n", "S24": "sukiyaki"}
AMB_BY_SHOT = {"S03b": "hall", "S03c": "room", "S06a": "home_n", "S06b": "home_n", "S06c": "home_n", "S06e": "home_n", "S06f": "home_n", "S06g": "hall",
               "S06h": "hall", "S08b": "hall", "S08c": "hall", "S08d": "hall", "S09f": "keys", "S10g": "street", "S12a": "car", "S13e": "factory",
               "S14a": "bank", "S14c": "factory", "S14d": "factory", "S14e": "clock", "S16b": "phone", "S16e": "clock", "S16f": "street", "S16g": "clock",
               "S17d": "clock", "S17e": "clock", "S18a": "door", "S23a": "hall", "S24e": "home_n", "S24f": "morning", "S24g": "morning", "S24h": "morning",
               "H0": "", "H1": "", "H2a": "", "H2b": "", "H3": ""}
FOLEY = {  # 컷별 폴리(제12장 10 foley_prompts·제15장 22) — 타임코드 자동 믹스(−18~−12 dBFS, 대사 구간 −6 dB)
    "S05a": "a doorknob yanked and a door flung open against a wall", "S05f": "a laptop lid closing softly", "S06a": "sneaker laces pulled tight",
    "S04d": "chopsticks set down on a ceramic bowl with a small click", "S04f": "a rice bowl put down hard on a wooden table", "S07a": "a gift box set down on a wooden table",
    "S09f": "eight single keyboard key presses, then a soft unlock chime", "S10a": "a deep low cinematic impact boom", "S11g": "a computer mouse sliding off a desk",
    "S11h": "knees hitting a wooden floor softly, a sharp breath", "S12g": "a sheet of paper sliding sharply across a steel desk, then a rough breath",
    "S13a": "a hand patting a work jacket shoulder twice", "S13e": "a single clock tick", "S14e": "a single clock tick", "S16e": "a single clock tick",
    "S16c": "a phone call ringing out and cutting off", "S17d": "a fountain pen trembling against paper", "S18a": "a metal door handle turning, a door opening",
    "S19b": "fingers stopping on a table, a tight grip", "S19e": "a tablet set down on a table", "S20b": "a thick binder dropped flat on a table",
    "S20f": "knees dropping onto a carpeted floor", "S21a": "a thick stapled contract torn in half, a sharp paper rip, an orchestral hit",
    "S22a": "a smartphone vibrating on a table", "S23a": "two gentle knocks on a wooden door", "S24a": "sukiyaki sizzling loudly in an iron pot",
    "S24h": "a metal shutter rolling up",
}
BGM = [  # (시작, 끝, 볼륨, 프롬프트) — 0~3.5초 BGM 없음(드론+심장 박동은 PHASE 6 로컬). 구간 간격 1.0초 이상
    (3.5, 19.0, 0.36, "low ominous drone with a single heartbeat hit and a tense string swell, Japanese family drama cold open, instrumental, no vocals"),
    (20.0, 171.0, 0.38, "gentle melancholic piano with soft strings, a struggling small family factory, quiet hurt between father and son, Japanese human drama, instrumental, no vocals"),
    (172.0, 213.0, 0.38, "mysterious soft pizzicato and low piano at night, a secret behind a closed door, quiet suspense, Japanese drama score, instrumental, no vocals"),
    (218.0, 286.0, 0.40, "slow emotional piano and swelling strings, a father's realisation and regret, restrained tears, Japanese human drama, instrumental, no vocals"),
    (287.5, 360.0, 0.40, "cold tense pulsing low strings and ticking percussion, betrayal and pressure, a countdown, Japanese drama score, instrumental, no vocals"),
    (361.5, 417.0, 0.38, "sorrowful solo cello and piano, a lonely night of regret, a mother's secret, Japanese human drama, instrumental, no vocals"),
    (419.0, 435.0, 0.40, "tense minimal ticking clock rhythm with a held low string note, a contract about to be signed, Japanese drama score, instrumental, no vocals"),
    (437.0, 506.0, 0.42, "powerful orchestral reveal with timpani and brass rising into calm dignified judgment, cathartic, Japanese drama score, instrumental, no vocals"),
    (507.5, 534.0, 0.42, "triumphant yet restrained orchestral resolution, dignity restored, Japanese drama score, instrumental, no vocals"),
    (535.5, None, 0.40, "warm emotional piano and strings, father and son reconciled, gentle hopeful morning, Japanese human drama finale, instrumental, no vocals"),
]
for _a, _b in zip(BGM, BGM[1:]):
    assert _b[0] - _a[1] >= 1.0, f"BGM 구간 간격 {_b[0] - _a[1]:.1f}s < 1.0s"

STYLE = {"NA": "Naration", "父": "Kentaro", "母": "Yumiko", "大樹": "Daiki", "叔父": "Seiji", "亮介": "Ryosuke", "真壁": "Makabe"}
STYLE_JA = {"Naration": "ナレーター", "Kentaro": "健太郎", "Yumiko": "由美子", "Daiki": "大樹", "Seiji": "誠二", "Ryosuke": "亮介", "Makabe": "真壁"}
STYLE_COLOR = {"Naration": "&H00DDDDDD", "Kentaro": "&H00FFFFFF", "Yumiko": "&H00F0E6C8", "Daiki": "&H00C8E6F0", "Seiji": "&H00B4D2FF",
               "Ryosuke": "&H00C8C8F0", "Makabe": "&H00E6DCC8"}
RATE = {"lite": 0.036, "omni": 0.16, "kf": 0.04}
HOOK_LEN = {"H0": 5.4, "H1": 3.0, "H2a": 2.5, "H2b": 5.1, "H3": 4.0}
BANNED_MOTION = (("slam", "큰 동작"), ("spin", "회전"), ("tracking camera", "편집 전용 무빙"), ("dolly", "편집 전용 무빙"), ("zoom", "편집 전용 무빙"),
                 ("crane", "편집 전용 무빙"), ("dialogue", "오디오 지시"), ("says", "오디오 지시"), ("sound of", "오디오 지시"))


def tc(sec):
    fr = int(round(sec * FPS)); s, f = divmod(fr, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}.{f:02d}"


def ass_t(sec):
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap_lines(text, limit=20):
    """휴대폰 기준(제13장 1·제17장 2): 줄당 20자 이내. libass 일본어 자동 줄바꿈 불가 → 수동 분할.
    줄 수는 최소로, 끊는 자리는 구두점 > 조사 뒤 > 글자 종류 경계 순(낱말 중간 「告げま/した」 금지), 줄 길이는 고르게."""
    n = len(text)
    if n <= limit:
        return [text]
    NOHEAD = "…—、。!?？！』」ーぁぃぅぇぉっゃゅょゎァィゥェォッャュョ"
    def kind(c):
        return "h" if "ぁ" <= c <= "ゖ" else "k" if "ァ" <= c <= "ヺ" or c == "ー" else "p" if c in "、。…!?？！』」「『" else "c"
    def cost(i):  # text[:i] | text[i:]
        a, b = text[i - 1], text[i]
        if b in NOHEAD or a in "「『":
            return 99
        if a in "、。!?？！』」" or (a == "…" and b != "…"):
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
    # 낱말 중간에서 끊느니 한 줄 더(3줄째는 다음 조각으로 넘어감) — 줄 하나 늘 때 비용 12
    sols = [(r[0] + 12 * (k - lo), r[1]) for k in (lo, lo + 1) for r in [solve(k)] if r]
    br = [0] + min(sols)[1]
    return [text[br[k]:br[k + 1]] for k in range(len(br) - 1)]


WRAP_FIX = {  # 자동 분할이 구절 중간에서 끊는 줄(눈 검수 후 수동 지정)
    "榊、今日からこの店のメニューに、かけうどんを載せなさい。腹を空かせた人からは、お代はもらわんように":
        ["榊、今日からこの店のメニューに、", "かけうどんを載せなさい。", "腹を空かせた人からは、", "お代はもらわんように"],
    "知らなかったから申し訳ない、か……。知っておったら、しなかったということじゃな":
        ["知らなかったから申し訳ない、か……。", "知っておったら、", "しなかったということじゃな"],
}


def chunks(text, limit=20):
    """한 이벤트 2줄 이내(제15장 21): 3줄 이상이면 2줄씩 조각."""
    ls = WRAP_FIX.get(text) or wrap_lines(text, limit)
    if len(ls) == 3 and ls[0][-1] in "、。…!?？！』」" and ls[1][-1] not in "、。…!?？！』」":
        return [ls[0], "\\N".join(ls[1:])]
    return ["\\N".join(ls[i:i + 2]) for i in range(0, len(ls), 2)]


def script_texts():
    t = open(os.path.join(PROD, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 5.")[0]
    out = {m.group(1): m.group(2) for m in re.finditer(r"^\s+((?:NA|L)\d+[a-z]?)[^「\n]*「(.+)」", body, re.M)}
    for m in re.finditer(r"^(OUT[234])\b[^\n]*\n\s*「(.+)」", body, re.M):
        out[m.group(1)] = m.group(2)
    return out


def check_rules(shots, rows):
    errs = []
    order = ["ecu", "cu", "ots", "ms", "ws", "ews"]
    prev = None
    for s in shots:
        if s["kind"] == "d" and s["angle"] in ("SIDE", "BE", "OH"):
            errs.append(f"{s['id']}: OMNI 대사 컷 각도 {s['angle']} 금지")
        if s["kind"] == "d" and (s["line"] or s["replay"]) and not s["act"]:
            errs.append(f"{s['id']}: 립싱크 컷에 연기 지시(act) 없음")
        if prev and prev["scene"] == s["scene"] and not s["kind"].startswith("reuse") and not prev["kind"].startswith("reuse"):
            if prev["lens"] == s["lens"] and prev["angle"] == s["angle"] and prev["loc"] == s["loc"] and prev["who"] == s["who"]:
                errs.append(f"{prev['id']}→{s['id']}: 연속 같은 구도(A1)")
        if s["line"]:
            spk = rows[s["line"]]["spk"]
            on = [w.split(":")[0] for w in s["who"]]
            if spk in SPK_KEY and SPK_KEY[spk] not in on and not s["vo"]:
                errs.append(f"{s['id']}: {s['line']} 화자 {spk}가 화면에 없음(화자-화면 일치) — 의도면 vo=True")
            if spk in SPK_KEY and s["kind"] == "d" and SPK_KEY[spk] != on[0]:
                errs.append(f"{s['id']}: 립싱크 대상(who[0]={on[0]})이 화자 {spk}와 다름")
        low = (s["motion"] or "").lower()
        for w, why in BANNED_MOTION:  # 제16장 1: 큰 동작·편집 전용 무빙·오디오 지시는 i2v 문장에 쓰지 않는다
            if w in low:
                errs.append(f"{s['id']}: 동작 문장 금지어 「{w}」({why})")
        if s["kind"] == "ins" and re.search(r"(?<!no )\bfaces?\b", s["subject"].lower()):
            errs.append(f"{s['id']}: 인서트에 얼굴 묘사(제15장 3 — NO FACE)")
        prev = s
    dz = sum(1 for s in shots if "dollyzoom" in s["fx"]); dutch = sum(1 for s in shots if "dutch" in s["fx"])
    if dz != 1:
        errs.append(f"돌리줌 {dz}회(1회만)")
    if dutch > 2:
        errs.append(f"더치 {dutch}회(최대 2회)")
    scenes = collections.OrderedDict()
    for s in shots:
        if s["scene"] != "H":
            scenes.setdefault(s["scene"], []).append(s)
    for sc, ss in scenes.items():
        sizes = {x["lens"] for x in ss}
        if len(ss) >= 5 and len(sizes) < 4:
            errs.append(f"{sc}: 사이즈 종류 {len(sizes)} < 4(영화처럼 다양하게)")
        lines = [x for x in ss if x["line"] and not x["line"].startswith("NA")]
        for a, b in zip(lines, lines[1:]):  # 「서로 대화하듯」: 대사 2줄 사이 리액션 컷
            ia, ib = ss.index(a), ss.index(b)
            if ib - ia == 1 and a["kind"] == "d" and b["kind"] == "d" and a["who"][0] == b["who"][0]:
                errs.append(f"{sc}: {a['id']}→{b['id']} 같은 화자 립싱크 연속(리액션 컷 없음)")
    return errs


def main():
    lock = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
    rows = {x["tag"]: x for x in lock["lines"]}
    texts = script_texts()
    scenes = {s["id"]: (s["start"], s["end"]) for s in lock["scenes"]}
    main_end = lock["body_end"]
    for s in SHOTS:
        spk = rows[s["line"]]["spk"] if s.get("vo") and s["line"] in rows else None
        sp = (SCENE_SPK_WARD.get(s["scene"], {}).get(spk) or SPK_WHO.get(spk)) if spk else None
        s["ots"] = bool(sp and s["id"] not in VO_OTS_SKIP and s["kind"] == "face" and len(s["who"]) == 1 and sp.split(":")[0] != s["who"][0].split(":")[0])
        if s["ots"]:
            s["who"] = s["who"] + [sp]
    errs = check_rules(SHOTS, rows)
    body_tags = {t for t, x in rows.items() if x["scene"].startswith("S") and x.get("start") is not None}
    used = [s["line"] for s in SHOTS if s["line"]]
    if sorted(used) != sorted(body_tags):
        errs.append(f"대사 줄 사용 불일치: 빠짐 {sorted(body_tags - set(used))}, 중복·초과 {sorted(set(u for u in used if used.count(u) > 1) | (set(used) - body_tags))}")
    for s in SHOTS:  # 참조 셀 존재 검사(PHASE 2 셀 분할 후)
        for w in s["who"]:
            key = w.split(":")[0]
            if s["expr"] and (key, s["expr"]) in EXPR and not os.path.exists(os.path.join(ROOT, EXPR[(key, s["expr"])])):
                errs.append(f"{s['id']}: 셀 없음 {EXPR[(key, s['expr'])]}")
        if s["loc"] in LOC and not os.path.exists(os.path.join(ROOT, LOC[s["loc"]])):
            errs.append(f"{s['id']}: 셀 없음 {LOC[s['loc']]}")
    if errs:
        raise SystemExit("규칙 위반:\n  " + "\n  ".join(sorted(set(errs))))

    starts, t = {}, 0.0
    for s in SHOTS:
        if s["scene"] == "H":
            starts[s["id"]] = t; t += HOOK_LEN[s["id"]]
    by_scene = collections.OrderedDict()
    for s in SHOTS:
        if s["scene"] != "H":
            by_scene.setdefault(s["scene"], []).append(s)
    for sc, shots in by_scene.items():
        a, b = scenes[sc]
        pins = {0: a, len(shots): b}
        for k, s in enumerate(shots):
            if s["line"] and k:
                pins[k] = max(a, rows[s["line"]]["start"] - LEAD)
            elif s.get("pin") and k:  # 재생 립싱크·무대사 컷 시각 고정
                pins[k] = max(a, s["pin"] - LEAD)
        keys = sorted(pins)
        for k1, k2 in zip(keys, keys[1:]):
            t1, t2 = pins[k1], pins[k2]; n = k2 - k1
            for j in range(k1, k2):
                starts[shots[j]["id"]] = t1 + (t2 - t1) * (j - k1) / n
    order_ids = [s["id"] for s in SHOTS]
    ends = {sid: (starts[order_ids[k + 1]] if k + 1 < len(order_ids) else main_end) for k, sid in enumerate(order_ids)}
    for k, s in enumerate(SHOTS):
        if s["kind"] == "d" and (s["line"] or s["replay"]) and ends[s["id"]] - starts[s["id"]] > OMNI_MAX:
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
    if problems:
        raise SystemExit("컷 길이 위반:\n  " + "\n  ".join(problems))

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
            if s["kind"] in ("ins", "estill") or not cell:  # 인서트는 인물 참조 금지(제15장 3)
                continue
            fg = (s["kind"] == "d" and j == 1) or (s.get("ots") and j == len(s["who"]) - 1)  # 흐린 앞 어깨 = 뒷모습 셀(얼굴 크롭 제외, 제18장 8②)
            if fg:
                if (key, "back") in EXPR or (key, "hoodback") in EXPR:
                    refs.append(EXPR.get((key, "back")) or EXPR[(key, "hoodback" if ward == "hood" else "suitback")])
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
        elif s["kind"] in ("empty", "estill") and not s["who"] or (s["kind"] == "ins" and not s["who"]):
            comp = "Completely unpopulated: no people, no hands, no faces. EMPTY."
        elif s["kind"] == "ins":
            comp = f"Insert: only the hands and the object, NO FACE visible, no other people."
        elif s["kind"] == "pstill":
            comp = f"Exactly {n} person seen from behind, the face and mouth NOT visible, no other people."
        else:
            comp = f"Exactly {n} {'person' if n == 1 else 'people'} as described, no extra people. GAZE LOCKED: nobody looks at the camera."
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/{SKIT}-keyframes/{sid}-1.png"
        kf_prompt = None
        if keyframe:
            low = (s["subject"] + " " + (s["act"] or "") + " " + (s["motion"] or "")).lower()
            real = " ".join(x for x, keys in ((TEARS, ("tear", "wet", "welling")), (SWEAT, ("sweat",))) if any(k in low for k in keys)
                            or (s["expr"] == "grief" and x == TEARS))
            glasses = " ".join(GLASSES[w.split(":")[0]] for w in s["who"] if w.split(":")[0] in GLASSES and s["kind"] not in ("ins",))
            face_expr = f" Expression of {ids[0].split(',')[0]}: {EXPR_TXT[s['expr']]} (about half intensity)." if s["expr"] in EXPR_TXT and s["kind"] not in ("ins", "pstill") else ""
            setting = f"Lighting: {LIGHT[s['light']]}." + (f" Location: {LOC_TXT[s['loc']]}." if s["loc"] in LOC_TXT else "")
            if s["loc"] is None and s["who"]:
                setting += " " + LOC_TXT["STREET" if s["light"] == "street_n" else "RAIN" if s["light"] == "rain" else "BANK" if s["light"] == "bank" else "HALL_OPEN"] + "."
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
        if s["kind"] == "d" and not s["line"] and not s["replay"]:  # 대사 없는 어깨 너머 리액션(vo 상대) → i2v
            tier = "lite"
        gen = 10 if d > 5.0 else 5
        item = {"prompt": "", "duration": gen}
        if tier == "lite":
            item["prompt"] = ("[CAMERA] Static locked-off camera, no camera movement. [CHARACTER] Keep the exact faces, glasses, wardrobe and props of the first frame; "
                              "the same people only. [ACTION] " + (s["motion"] or "Subtle natural motion only: breathing, one blink.") +
                              " Head turns under 20 degrees. [SETTING] The same location and lighting as the first frame. "
                              "[NEGATIVE] No walking toward the camera, no new people, no text, no morphing, no flicker.")
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
                   "lighting": s["light"], "edit_fx": s["fx"], "refs": refs, "ots": s.get("ots", False), "subject": s["subject"], "line": s["line"] or s["replay"], "vo": s["vo"], "foley": FOLEY.get(sid, ""),
                   "motion": item["prompt"] if tier == "lite" else "", "act": s["act"], "keyframe": keyframe, "keyframe_prompt": kf_prompt,
                   "ja_overlay": JA_OVERLAY.get(sid, ""), "caption": CARDS.get(sid, ""), "ambience": G.get(amb, "")})
    budget = round(cost["lite"] * RATE["lite"] * 1.25, 2)

    tts_order = [dict(x) for x in lock["lines"] if x.get("start") is not None and x["scene"] != "OUT"]
    for rp in lock.get("replay", []):  # S05 「出ていけ！」 — 후크 L01을 같은 녹음으로 한 번 더
        src = dict(rows[rp["tag"]]); src["start"] = rp["start"]; src["end"] = rp["start"] + src["dur"]; src["tag"] = rp["tag"] + "r"
        tts_order.append(src)
    tts_order.sort(key=lambda x: x["start"])
    dst = os.path.join(ROOT, "assets", "audio-overrides", SKIT); os.makedirs(dst, exist_ok=True)
    mapping = []
    for i, x in enumerate(tts_order, 1):
        shutil.copyfile(os.path.join(ROOT, "assets", "auditions", TTS_DIR, x["id"] + ".mp3"), os.path.join(dst, f"line{i:03d}.mp3"))
        mapping.append((f"line{i:03d}", x["tag"], x["id"]))

    events = []
    for x in tts_order:
        st = STYLE["NA" if x["spk"] == "NA" else x["spk"]]
        s0 = x["start"] - x["lead"]
        e0 = x["end"] + 0.2
        parts = chunks(texts[x["tag"].rstrip("r") if x["tag"].endswith("r") and x["tag"][:-1] in texts else x["tag"]])
        tot = sum(len(q) for q in parts); t = s0
        for k, q in enumerate(parts):  # 조각은 「<스타일>_c」(silent) — TTS 줄 수 유지(제15장 21)
            t1 = e0 if k == len(parts) - 1 else t + (e0 - s0) * len(q) / tot
            events.append((t, t1, st if k == 0 else st + "_c", STYLE_JA[st], q)); t = t1
    # 화면 카드(후크·중반 예고·메뉴판·다음 이야기·타이틀)는 클립에 직접 그린다 — .ass Caption 없음(제15장 12)
    events.sort(key=lambda e: e[0])
    # 휴대폰 기준(제13장 1): 대사 70px·내레이션 66px·외곽선 6, 좌우 여백 120px. 조각 스타일 _c도 같은 모양
    st_lines = "\n".join(
        f"Style: {n}{suf},Noto Sans CJK JP,{70 if n != 'Naration' else 66},{c},&H000000FF,&H00000000,&H80000000,-1,{-1 if n == 'Naration' else 0},0,0,100,100,0,0,1,6,2,2,120,120,90,1"
        for n, c in STYLE_COLOR.items() for suf in ("", "_c"))
    ass = ["[Script Info]", "Title: 引きこもりの息子 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           st_lines,
           "Style: HookLine,Noto Sans CJK JP,66,&H00B4D2FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,200,200,90,1",
           "Style: Caption,Noto Sans CJK JP,84,&H001E1EFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,160,160,80,1",
           "Style: Title,Noto Serif CJK JP,110,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,5,160,160,80,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:  # 휴대폰 자막 자동 검사(지속 개선 원칙 4: 두 작품 반복 오류 → 도구 검사)
        assert e[4].count("\\N") <= 1 and max(len(q) for q in e[4].split("\\N")) <= 20, f"자막 규격 위반(2줄·20자): {e[4]}"
    for e in events:
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{e[4]}")
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    os.makedirs(os.path.join(ROOT, "scripts", "storyboard"), exist_ok=True)
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_hikikomori_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT, "preset": PRESET,
               "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"], "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_hikikomori_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, wardrobe, "
                         "props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_hikikomori_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (Typecast 확정본).",
        "default_voice": "cached-typecast", "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Naration"], "silent_styles": ["Caption", "HookLine", "Title"] + [n + "_c" for n in STYLE_COLOR],
        "output_size": [1920, 1080], "fit": "crop", "scene_durations": durations, "transitions": [0.0] * len(durations),
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d" and (s["line"] or s["replay"])],
        "omnihuman_prompts": {str(idx[k]): v for k, v in omni_prompts.items()},
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0, "legacy_lipsync": False,
        "foley_prompts": {str(idx[k]): v for k, v in foley.items()},
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35, "duck_db": 8, "ambience_prompts": [x["ambience"] for x in sb],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": s, "end": round(main_end, 2) if e is None else e, "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_후크": "0~3.5초 BGM 없음: 저음 드론 + 심장 박동 1회를 PHASE 6 로컬 믹스. H0 = S05e 립싱크 재사용(L01), H1 = S09g, H2 = S11g·S11h(NA0 + 중앙 카드), H3 타이틀(직전 컷 블러, 암전 없음). S05에서 L01을 같은 녹음으로 한 번 더(lock.json replay).",
        "_공간음": "L24·L25(메모 낭독)는 옅은 리버브, 회의실(S17~S22)은 작은 방 잔향, 공장(S01·S16)은 금속 반사 짧은 잔향 — PHASE 6 로컬(발성 디렉션 2. 음향·마이크 거리).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    md = ["# 『引きこもりの息子』 PHASE 3 샷 리스트 (B안 표준)", "",
          f"> `scripts/build_hikikomori_phase3.py` 자동 생성(손 수정 금지). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " + ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock['ads']) + ".",
          "> 자동 검사 통과: 연속 같은 구도 0 · 같은 화자 립싱크 연속 0(리액션 컷) · 장면당 사이즈 4종 이상 · 돌리줌 1회 · 더치 2회 · OMNI 정면~45° · 화자-화면 일치(vo 제외) · 대사 줄 전부 배치 · 컷 길이 · OMNI 8초 이하.", "",
          "## 비용 추산 (실측 단가)", "", "| 항목 | 수량 | 단가 | 금액 |", "|---|---|---|---|",
          f"| 키프레임 | {cost['kf']}장 | 0.04 | {cost['kf'] * RATE['kf']:.2f} |",
          f"| i2v lite (사람·손·배경 전부) | {cost['lite']}초 | 0.036 | {cost['lite'] * RATE['lite']:.2f} |",
          f"| OmniHuman (8초 상한 + 앞뒤 0.8초) | {cost['omni']:.1f}초 | 0.16 | {cost['omni'] * RATE['omni']:.2f} |",
          f"| **1차 합계** (재생성 여유 제외) | | | **{total_cost:.2f}** |", f"| i2v 예산 상한 `budget_usd` (여유 25%) | | | {budget:.2f} |", "",
          "## 생성 방식 분포", "", "| 방식 | 컷 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in tiers.most_common()] + [
          "", f"## 앵글 분포 — 최다 {top[0]} {top[1] / sum(ang.values()) * 100:.0f}% (60% 이하 기준)", "", "| 앵글 | 컷 |", "|---|---|"] + [
          f"| {k} | {v} |" for k, v in ang.most_common()] + [
          "", "## 화면 속 일본어 (무지 → 합성, PHASE 4 마감 체크)", ""] + [f"- {k}: {v}" for k, v in JA_OVERLAY.items()] + [
          "", "## 컷별 폴리 (자동 믹스)", ""] + [f"- {k}: {v}" for k, v in FOLEY.items()] + [
          "", "## 샷 표", "", "| 컷 | 타임코드 | 길이 | 방식 | 사이즈 | 앵글 | 조명 | 편집 효과 | 대사 | 현장음 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in sb:
        md.append(f"| {x['id']} | {x['timecode']} | {x['assembled_s']:.2f}s | {x['tier']} | {x['size']} | {x['angle']} | {x['lighting']} | {x['edit_fx']} | {(x['line'] or '') + (' (vo)' if x['vo'] else '')} | {x['ambience'][:30]} |")
    md += ["", "## 음성 번호 대응", "", "| 캐시 | 대본 | 원본 녹음 |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in mapping]
    open(os.path.join(PROD, "07_샷리스트.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    emotion_table(sb, live)
    print(f"완료: 컷 {len(SHOTS)}개, 본편 {tc(main_end)}, 방식 {dict(tiers)}, 1차 비용 약 {total_cost:.2f}달러 (i2v budget {budget}), 앵글 {dict(ang)}")


EMO_OK = {"angry": ("anger", "fury", "rage", "glare", "furious", "shout", "jaw", "jab", "slam", "fist", "spit", "scream", "hard"),
          "happy": ("smile", "smirk", "sneer", "laugh", "grin", "mock", "pleased", "satisf", "proud", "warm", "tease"),
          "sad": ("sob", "tear", "cry", "beg", "plea", "sad", "tremb", "break", "wet", "pale", "frighten", "stammer", "confess", "hoarse", "fear", "apolog", "sorry", "worr"),
          "tonedown": ("cold", "quiet", "calm", "restrain", "low", "icy", "earnest", "silence", "gentle", "steady", "firm", "plain", "precise", "contempt", "narrow"),
          "toneup": ("alarm", "panic", "shock", "excite", "fright", "urgent", "mock", "dismiss", "scoff", "bluster", "forced", "fake"),
          "normal": ()}
EMO_BAD = {"angry": ("sob", "gentle", "peaceful", "tender"), "happy": ("sob", "fury", "rage"), "sad": ("smirk", "sneer", "grin"),
           "tonedown": ("shout", "laugh", "slam", "scream")}
INTENDED = ("비웃", "즐기", "깔보", "억누른", "서늘", "냉정", "차갑", "예외", "눈물 섞인 웃음", "울먹")


def emotion_table(sb, live):
    import sys
    sys.path.insert(0, PROD)
    from build_tts_spec import TONE
    rows, warn = [], 0
    for x in sb:
        tag = x["line"]
        if not tag or tag not in TONE or tag.startswith(("NA", "OUT")):
            continue
        emo, inten, tempo, memo = TONE[tag]
        act = x["act"] or live.get(x["id"]) or ""
        seen = " ".join([x["subject"], act]).lower()
        ok = not EMO_OK.get(emo) or any(k in seen for k in EMO_OK[emo])
        bad = [k for k in EMO_BAD.get(emo, ()) if k in seen]
        intended = any(k in memo for k in INTENDED)
        if x["vo"]:  # 듣는 사람 리액션 위 목소리 — 화자 표정 대조 대상 아님(리액션이 「방금 들은 말」에 맞는지는 동작 문장으로 검수)
            state = "👂"
        else:
            state = "✅" if ok and (not bad or intended) else "⚠️"
        warn += state == "⚠️"
        how = "립싱크" if x["tier"] == "omni" else ("i2v(목소리만)" if x["vo"] else "i2v")
        rows.append(f"| {state} | {x['id']} | {tag} | {how} | {emo} {inten} · {tempo} | {memo} | {x['subject'][:70]} | {act[:90]} |")
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_hikikomori_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않거나 부딪힘(연기 메모에 의도가 없으면 키프레임·동작 문장을 고친다). 감정 격차(9절)는 샷 표의 장면 순서로 확인.", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 감정·세기·템포 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")


if __name__ == "__main__":
    main()
