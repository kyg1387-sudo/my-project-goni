# === #03 『老舗旅館の嫁』 PHASE 3 정의 블록 (build_ryokan_phase3.py에 삽입됨; 직접 실행하지 않음) ===
SKIT = "ryokan"
FPS = 24
HARD = 1 / FPS
OMNI_MAX = 7.9
LEAD = 0.3
MIN_SHOT = 1.2
STILL_MAX = 6.5
I2V_MAX = 10.0
SHOT_TARGET = 1.6
TRIM_PRE, TRIM_POST = 0.05, 0.12
N_LINES = 77  # 본편 줄 수(아웃트로 78~82 제외)
VILLAINS = ("MAI", "TOMIKO")
HERO_KEY = "WAKANA"
EXTRAS = ("CROWD", "GUESTS", "FAMILY", "WIFE")

C = "assets/portraits/ryokan-cast/cells/"
WHO = {
    "WAKANA": ("Wakana, a Japanese woman aged 33, slim, soft oval face, clear dark eyes, straight black hair combed back into a low neat chignon with NO bangs, small beauty marks below the LEFT eye, NO glasses", C + "wakana-front.png"),
    "WAKANA_B": ("Wakana, a Japanese woman aged 33, slim, soft oval face, clear dark eyes, straight black hair combed back into a low neat chignon with NO bangs, small beauty marks below the LEFT eye, NO glasses", C + "wakanab-front.png"),
    "TOMIKO": ("Tomiko, a Japanese woman aged 62, lean face with high cheekbones, silver-grey hair in a tight formal upswept bun, thin gold-rimmed oval glasses, small pearl stud earrings, upright rigid posture", C + "tomiko-front.png"),
    "MAI": ("Mai, a Japanese woman aged 38, slightly full round face, long loosely waved chestnut-brown hair, arched drawn eyebrows, glossy deep red lipstick, heavy mascara, NO glasses", C + "mai-front.png"),
    "TAKAYUKI": ("Takayuki, a Japanese man aged 35, round soft face, slightly heavy build, faint chin stubble, short unkempt black hair, tired eyes, NO glasses", C + "takayuki-full-front.png"),
    "SAKURAI": ("Sakurai, an elegant Japanese woman in her mid-50s, long elegant face, sleek chin-length silver bob with a side part, large single pearl earrings, NO glasses", C + "sakurai-front.png"),
    "REGULAR": ("an elderly Japanese man in his late 60s, a long-time regular guest, warm friendly face, hair mostly silver-grey neatly combed, medium build, NO glasses", C + "regular-expr-smile.png"),
    "CHEN": ("a Taiwanese businessman in his 40s seen ONLY from behind or over the shoulder, short black hair, face never visible", None),
    "WIFE": ("an elderly Japanese woman in her late 60s with short grey hair and a plain beige shawl, seen small or from the side, face soft", None),
    "GUESTS": ("hotel guests seen from behind or as soft out-of-focus shapes, faces unrecognizable", None),
    "FAMILY": ("a Western tourist family and a Japanese couple seen from behind or in soft focus, faces unrecognizable", None),
    "CROWD": ("a group of Taiwanese tour guests seen from behind or as soft out-of-focus shapes, faces unrecognizable", None),
}
WARD = {
    "WAKANA": "a plain navy-blue cotton samue work jacket with a plain white bib apron tied at the waist, plain navy work trousers, white tabi socks, no crest, no badge, no name tag",
    "WAKANA_B": "a formal plain navy-blue silk kimono with no pattern and a plain ivory obi sash, white tabi socks, no crest, no jewellery",
    "TOMIKO": "a plain deep plum-purple silk kimono with no pattern, a plain pale gold obi, white tabi socks, no crest",
    "MAI": "a brand-new bright soft-pink silk kimono with a scattered cherry-blossom print (flowers only, no writing), a plain cream obi, a thin gold bangle on the left wrist",
    "TAKAYUKI": "a plain charcoal-grey cotton samue jacket and trousers over a plain black crew-neck shirt, no crest",
    "SAKURAI": "a plain deep forest-green silk kimono with no pattern and a plain champagne-gold obi, white tabi socks, no crest",
    "REGULAR": "a plain brown knitted vest over a plain pale beige collared shirt, plain dark grey trousers, no logo, no watch",
}
EXPR = {
    ("WAKANA", "neutral"): C + "wakana-front.png", ("WAKANA", "hurt"): C + "wakana-expr-hurt.png", ("WAKANA", "resolve"): C + "wakana-expr-resolve.png",
    ("WAKANA_B", "smile"): C + "wakanab-front.png", ("WAKANA_B", "neutral"): C + "wakanab-expr-neutral.png", ("WAKANA_B", "faint"): C + "wakanab-expr-faint.png",
    ("TOMIKO", "smile"): C + "tomiko-expr-smile.png", ("TOMIKO", "stern"): C + "tomiko-front.png", ("TOMIKO", "plead"): C + "tomiko-front.png",
    ("MAI", "laugh"): C + "mai-expr-laugh.png", ("MAI", "panic"): C + "mai-expr-panic.png", ("MAI", "sulk"): C + "mai-expr-sulk.png", ("MAI", "sneer"): C + "mai-front.png",
    ("TAKAYUKI", "bored"): C + "takayuki-expr-bored.png", ("TAKAYUKI", "down"): C + "takayuki-expr-down.png", ("TAKAYUKI", "panic"): C + "takayuki-expr-panic.png",
    ("SAKURAI", "laugh"): C + "sakurai-expr-laugh.png", ("SAKURAI", "calm"): C + "sakurai-expr-calm.png", ("SAKURAI", "wink"): C + "sakurai-expr-wink.png",
    ("REGULAR", "smile"): C + "regular-expr-smile.png", ("REGULAR", "neutral"): C + "regular-expr-neutral.png", ("REGULAR", "fond"): C + "regular-expr-fond.png",
}
LOC = {
    "TSK_GENKAN": C + "loc-genkan-day-wide.png", "TSK_CORRIDOR": C + "loc-genkan-corridor-end.png", "TSK_COUNTER": C + "loc-genkan-counter-close.png",
    "TSK_GENKAN_REV": C + "angle-genkan-reverse.png", "TSK_GENKAN_THRU": C + "angle-genkan-through.png",
    "ZASHIKI": C + "loc-zashiki-day-wide.png", "ZASHIKI_HEAD": C + "loc-zashiki-head-seat.png", "ZASHIKI_DOOR": C + "loc-zashiki-door-seat.png", "ZASHIKI_TABLE": C + "loc-zashiki-table-close.png",
    "KITCHEN": C + "loc-kitchen-dawn.png", "KITCHEN_BOARD": C + "loc-kitchen-board.png", "TSK_OFFICE": C + "loc-kitchen-office-night.png",
    "ROOM_WINDOW": C + "loc-room-window.png", "ROOM_LAMP": C + "loc-room-lamp.png",
    "HGEN_WIDE": C + "loc-hgenkan-day-wide.png", "HGEN_DESK": C + "loc-hgenkan-front-desk.png", "HGEN_SOFAS": C + "loc-hgenkan-lobby-sofas.png", "HGEN_BUS": C + "loc-hgenkan-bus-bay.png",
    "HOFF": C + "loc-hoffice-night-wide.png", "HOFF_DESK": C + "loc-hoffice-desk-close.png", "HOFF_WINDOW": C + "loc-hoffice-window.png", "HOFF_DOOR": C + "loc-hoffice-door-lobby.png",
    "HOFF_REV": C + "angle-hoffice-reverse.png", "HOFF_HIGH": C + "angle-hoffice-high.png", "HOFF_LOW": C + "angle-hoffice-low.png",
    "TAIPEI": C + "loc-taipei-desk-behind.png", "TAIPEI_PHONE": C + "loc-taipei-phone.png", "TAIPEI_WINDOW": C + "loc-taipei-window.png",
    "ALLEY": C + "loc-alley-night-wide.png", "ALLEY_GATE": C + "loc-alley-gate.png", "ALLEY_TAXI": C + "loc-alley-taxi-end.png",
    "P_FILE": C + "prop-file.png", "P_FILE_OPEN": C + "prop-file-open.png", "P_HANDSET": C + "prop-handset.png", "P_TEA": C + "prop-teaset.png",
}
PRESET = ("Photorealistic live-action Japanese drama, authentic contemporary Japanese hot-spring inn (温泉旅館) mise-en-scene, Reiwa era, "
          "Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, quiet elegant realism, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, "
            "logo on shirt, brand logos, crest on noren, family emblem, signage lettering, posters with writing, paper notices on walls, printed labels, "
            "watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, anime, illustration")
PLAIN = "All papers, screens, signs, scrolls, plates and the noren curtain are completely blank and plain; no letters, numbers, crests or symbols anywhere in the frame; every wall is bare."
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the subject fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait",
    "ch": "85mm prime lens, f/1.8, choker framing from forehead to chin, razor-sharp eyes, soft bokeh",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective, sharp architectural lines",
}
LIGHT = {
    "day": "soft diffused daylight through paper shoji, warm wooden tones, low contrast, gentle shadows",
    "press": "hard cold light from directly above, 5600K, dark eye sockets and chin shadow, oppressive high-contrast chiaroscuro",
    "dawn": "pre-dawn darkness, one cold fluorescent tube just switched on, steam catching the light, deep shadows",
    "office_night": "night, a single warm 3200K desk lamp making a pool of light on the desk, everything else dark, Rembrandt shadow on the face",
    "room_night": "night, the cold blue-white glow of a smartphone screen on the face, a faint warm paper lamp far behind, darkness around",
    "genkan_night": "night, warm paper-lantern light, dark blue dusk outside the entrance, polished wood reflections",
    "hoff_night": "night, a warm desk lamp and the soft lantern lights of the hot-spring town through the window, gentle low contrast",
    "hoff_day": "soft daylight through the window, warm neutral tones, gentle and relaxed",
    "hgen_day": "bright airy natural light through tall windows, golden late-afternoon sun, warm light wood, uplifting and generous",
    "taipei": "hard sunlight through venetian blinds casting bright stripes, cool neutral office tones",
    "alley": "night, one sodium street lamp making a warm orange pool, cold blue shadows, wet asphalt reflections, red tail lights",
    "rain": "overcast grey daylight, rain falling, water dripping from roof tiles, cold desaturated tones",
    "ending": "warm golden interior light, soft rim light on hair, low contrast, hopeful glow",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "extreme bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}


# 눈물 규칙(제7장 5-1): 눈물이 나오는 컷의 i2v 동작은 실제 눈물처럼 — 한 줄기가 천천히, 젤 같은 줄기 금지
TEAR_MOTION = (" Tears: at most one thin tear slowly forms at the lower lid and runs down one cheek along its natural curve; "
               "no thick glossy streaks, no sudden multiple lines, the skin stays matte.")
TEAR_RE = re.compile(r"\btear|teary|weep|sob|wet eye|brimming|welling|glistening", re.I)


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, hero=False):
    """kind: d(OMNI 대사) / react(리액션 정지) / ins(인서트 정지) / face(얼굴·손 i2v pro) / sil(실루엣·뒷모습 i2v lite) /
    empty(무인 i2v lite) / estill(무인 정지) / gfx(로컬 그래픽 합성, 무료) / reuse:<id> / card.  hero=True: 상위 모델 3테이크."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc,
                subject=subject, line=line, fx=fx, motion=motion, expr=expr, hero=hero)


OMNI_COMMON = "Static camera. Keep the exact face, hair, wardrobe and background. Natural lip movement matching the Japanese speech, subtle breathing, natural blinks. Head turns stay under 15 degrees, hands stay out of frame. "
OMNI_PROMPTS = {
    "S03d": "Warm professional hospitality: a gentle genuine smile, a small welcoming nod at the end.",
    "S04a": "Cold dismissal: level unblinking gaze, one eyebrow lifts slightly on the question, almost no movement.",
    "S05b": "Hesitant plea: eyes lowered then lifted, lips pressed between phrases, a small swallow.",
    "S05c": "Bored indifference: eyes drifting down toward a phone below the frame, a small tired sigh at the end.",
    "S06b": "Polished hostess smile: chin slightly raised, a gracious small bow of the head at the end.",
    "S07b": "Formal announcement: still, composed, reading out a decision, no smile.",
    "S07d": "Careful objection: brows drawn together, voice trailing off, lips part and close.",
    "S07e": "Sneering mockery: one corner of the mouth lifts, eyes half-lidded, a short scornful exhale on the first word.",
    "S07f": "Slow condescension: a lazy smile, chin raised, looking down at the camera, a tiny shake of the head.",
    "S07i": "Cold decisiveness: the chin lifts, eyes hard, no smile, a slight narrowing of the eyes.",
    "S07l": "Calm clarity after the decision: steady eyes, a faint peaceful smile, a small deep nod at the end.",
    "S09a": "Smug dismissal: a flick of the hair, half-lidded eyes, an airy careless smile.",
    "S11d": "Furious shouting: brows down hard, eyes wide, the jaw tight, a small forward jolt of the head within 10 degrees.",
    "S11e": "Panicked excuse: wide wet eyes, brows raised, stammering, a small shake of the head.",
    "S12b": "Warm playful invitation: crinkled eyes, a gentle amused smile, a small tilt of the head.",
    "S12c": "Teasing warmth: a mischievous smile on the joke, then a kind steady look.",
    "S13d": "Shock: eyes widen, lips part, a small startled pull-back of the head within 10 degrees.",
    "S16b": "Calm composure: level eyes, no smile, a measured slow blink.",
    "S16c": "Quiet firmness: still face, eyes steady and slightly cold, no anger.",
    "S16d": "Gentle finality: the faintest smile, a slow blink, a small nod at the end.",
    "S18c": "Tearful pleading: brows drawn up, eyes wet and shining but cheeks dry, lips trembling, a swallow between phrases.",
    "S18d": "Broken sobbing plea: eyes squeezed then opened, wet and shining, one thin tear at most, the voice breaking.",
    "S18f": "Gentle steadiness: calm warm eyes, no anger, a soft measured delivery, the faintest smile at the end.",
    "S18g": "Quiet closing line: the eyes lift slightly on the final question, a faint peaceful smile, a slow blink.",
    "S01b": "Quiet closing line: the eyes lift slightly on the final question, a faint peaceful smile, a slow blink.",
}

SHOTS = [
    # ── ① 후크 S01 (플래시포워드: 하나이카다 사무실 밤 ↔ 쓰키미소 사무실 밤)
    S("S01a", "S01", "face", "ecu", "office_night", "HA", [], "P_HANDSET",
      "High angle extreme close-up: an old cream-colored telephone handset gripped in two thin aged female hands with pearl-white trembling knuckles, a wooden counter below, warm lamp light. Only the hands and handset are visible, no face.", line="line001",
      motion="The hands tremble slightly and tighten on the handset; nothing else moves. No face appears.", hero=True),
    S("S01b", "S01", "d", "cu", "hoff_night", "EL", ["WAKANA_B"], "HOFF_WINDOW",
      "Chest-up close-up of Wakana in a navy kimono holding a smartphone to her ear just below the frame edge, calm level eyes, the lantern-lit town soft through the window behind.", line="line002", expr="neutral"),
    S("S01c", "S01", "face", "ecu", "hoff_night", "HA", [], "HOFF_DESK",
      "High angle extreme close-up: a woman's hand in a navy kimono sleeve slowly placing a smartphone face down on a dark wooden desk beside a warm lamp. Only the hand and phone are visible.",
      motion="The hand lowers the phone gently until it rests face down, then withdraws out of frame. No face.", hero=True),
    S("S01d", "S01", "react", "cu", "hoff_night", "EL", ["WAKANA_B"], "HOFF_WINDOW",
      "Chest-up close-up of Wakana looking down after the call, a quiet unreadable face, the warm lamp on one side, town lights blurred behind.", line="line003", expr="neutral"),
    S("S01e", "S01", "empty", "ews", "genkan_night", "EL", [], "TSK_GENKAN",
      "Wide view of the old inn's entrance at night: a plain indigo noren curtain stirring in the wind under a paper lantern, the polished wooden floor empty, the long corridor dark beyond. Completely unpopulated.", line="line004",
      motion="The noren curtain sways slowly in the wind; the lantern flame flickers. No people appear.", hero=True),
    S("S01f", "S01", "card", "ews", "genkan_night", "EL", [], "TSK_GENKAN", "Title card over the blurred night entrance."),
    S("S01g", "S01", "card", "ews", "dawn", "EL", [], "KITCHEN", "Caption card: 三か月前 (small corner caption over the first kitchen frame)."),
    # ── ② S02 새벽 주방
    S("S02a", "S02", "empty", "ws", "dawn", "EL", [], "KITCHEN",
      "Wide view of the dark inn kitchen before dawn: one cold fluorescent tube just switched on, a large iron rice pot on the stove with steam rising into the light, stainless counters. Completely unpopulated.", line="line005",
      motion="Steam rises slowly from the pot into the fluorescent light; the tube flickers once. No people.", hero=True),
    S("S02b", "S02", "estill", "ecu", "dawn", "HA", [], "KITCHEN",
      "High angle extreme close-up: the iron lid of the rice pot with steam escaping around its rim, beads of condensation, cold light.", line="line006"),
    S("S02c", "S02", "ins", "ecu", "dawn", "OH", [], "KITCHEN_BOARD",
      "Overhead extreme close-up: a wooden cutting board with a plain kitchen knife, fresh green vegetables neatly cut, a woman's hand resting at the edge. No face."),
    S("S02d", "S02", "sil", "ms", "office_night", "SIDE", ["WAKANA"], "TSK_OFFICE",
      "Medium shot from the side: Wakana in the samue and apron seated at the small office desk, a closed laptop open now showing only a soft blank glow, a telephone handset held between her ear and shoulder, writing on a blank notepad. Face in profile, mouth not visible.", line="line007",
      motion="She writes slowly on the notepad and nods once while listening; no turning toward the camera."),
    # ── S03 현관 낮: 외국인 응대, 단골 노부부 셋업
    S("S03a", "S03", "sil", "ws", "day", "EL", ["WAKANA", "FAMILY"], "TSK_GENKAN",
      "Wide view of the sunlit entrance: Wakana in samue and apron bowing to a Western tourist family seen from behind at the raised step, suitcases beside them, warm wood all around.", line="line008",
      motion="Wakana completes a slow polite bow and straightens; the family stays still with their backs to the camera. No one walks toward the camera."),
    S("S03b", "S03", "react", "cu", "day", "EL", ["WAKANA"], "TSK_COUNTER",
      "Chest-up close-up of Wakana behind the dark wooden counter, a composed professional smile, soft daylight, the corridor blurred behind.", line="line009", expr="neutral"),
    S("S03c", "S03", "sil", "ws", "day", "EL", ["REGULAR", "WIFE"], "TSK_GENKAN",
      "Wide two-shot at the entrance step: an elderly regular couple, the silver-haired husband in a brown knitted vest and his wife in a beige shawl, slipping off their shoes at the raised step and looking up with warm smiles toward the counter; seen at a slight distance, their mouths not clearly visible.", line="line010",
      motion="The husband finishes slipping off a shoe and looks up with a smile; the wife nods. No walking toward the camera.", hero=True),
    S("S03d", "S03", "d", "cu", "day", "EL", ["WAKANA"], "TSK_CORRIDOR",
      "Chest-up close-up of Wakana at the edge of the corridor, a warm genuine smile of welcome, hands out of frame, polished wood soft behind.", line="line011", expr="neutral"),
    # ── S04 주방 뒷문: 「家族なんだから当然」
    S("S04a", "S04", "d", "cu", "day", "EL", ["TOMIKO"], "KITCHEN_BOARD",
      "Chest-up close-up of Tomiko at the kitchen back door, gold-rimmed glasses, a cold dismissive look with one eyebrow slightly raised, the grey morning yard soft behind her.", line="line012", expr="stern"),
    S("S04b", "S04", "sil", "ms", "day", "SIDE", ["TOMIKO"], "KITCHEN_BOARD",
      "Medium shot from behind: Tomiko in the plum kimono turning away through the open back door, her upswept silver bun and straight back to the camera, the yard beyond.", line="line013",
      motion="She takes one slow step out through the door and does not look back."),
    S("S04c", "S04", "ins", "ecu", "day", "HA", [], "KITCHEN_BOARD",
      "High angle extreme close-up: a woman's hand setting a kitchen knife down gently on a wooden cutting board, the fingers releasing it, cut vegetables beside. No face.", line="line014"),
    S("S04d", "S04", "react", "cu", "day", "HA", ["WAKANA"], "KITCHEN_BOARD",
      "High angle chest-up of Wakana with her head bowed, eyes down, lips pressed together, dry eyes, the steel counter soft behind.", expr="hurt"),
    # ── S05 부부의 방 밤
    S("S05a", "S05", "sil", "ms", "room_night", "SIDE", ["TAKAYUKI"], "ROOM_LAMP",
      "Medium shot from the side in a dark tatami room: Takayuki in a charcoal samue lying propped on a futon, his face lit only by a smartphone held above him, the paper lamp faint behind. His face is turned to the phone, mouth not visible.",
      motion="His thumb taps the phone screen; the glow flickers on his face. No turning toward the camera."),
    S("S05b", "S05", "d", "cu", "room_night", "EL", ["WAKANA"], "ROOM_WINDOW",
      "Chest-up close-up of Wakana kneeling beside the futon, lit faintly by the phone glow and the paper lamp, hesitant eyes, hands out of frame.", line="line015", expr="hurt"),
    S("S05c", "S05", "d", "cu", "room_night", "LA", ["TAKAYUKI"], "ROOM_LAMP",
      "Low angle chest-up of Takayuki, his face lit cold blue-white from below by the phone screen (out of frame), eyes down toward it, bored and tired.", line="line016", expr="bored"),
    S("S05d", "S05", "gfx", "ecu", "room_night", "HA", [], "ROOM_LAMP",
      "High angle extreme close-up: a man's thumb on a smartphone whose screen glows plain blank blue-white, the dark tatami around. No face.", line="line017"),
    S("S05e", "S05", "react", "cu", "room_night", "SIDE", ["WAKANA"], "ROOM_WINDOW",
      "Profile close-up of Wakana in the dark room, only her eyes trembling, the faint lamp behind, utterly still.", expr="hurt"),
    S("S05f", "S05", "estill", "ecu", "office_night", "EL", [], "TSK_OFFICE",
      "Extreme close-up at night: a hand closing a thick ledger book on the small office desk under the lamp, the other hand reaching for the lamp switch. No face.", line="line018"),
    # ── S06 현관 공개 굴욕
    S("S06a", "S06", "sil", "ews", "day", "EL", ["TOMIKO", "MAI", "GUESTS", "WAKANA"], "TSK_GENKAN_THRU",
      "Wide view through the doorway: in the foreground Tomiko in plum kimono and Mai in a pink cherry-blossom kimono bowing gracefully to a group of guests seen from behind; far down the corridor at the very back, tiny in frame, Wakana in apron on her knees wiping the floor.", line="line019",
      motion="Mai completes a slow graceful bow; the guests stay with their backs to the camera; the tiny figure at the far end keeps wiping. Nobody walks toward the camera.", hero=True),
    S("S06b", "S06", "d", "cu", "day", "EL", ["TOMIKO"], "TSK_COUNTER",
      "Chest-up close-up of Tomiko with a polished hostess smile, gold-rimmed glasses, chin slightly raised, the counter and corridor blurred behind.", line="line019x", expr="smile"),
    S("S06c", "S06", "sil", "ms", "day", "SIDE", ["TOMIKO"], "TSK_GENKAN_REV",
      "Over-the-shoulder medium shot from behind Tomiko's silver bun looking down the long polished corridor toward a small kneeling figure at the far end, the guests' shoulders soft at the frame edge.", line="line020",
      motion="Tomiko's head turns a few degrees toward the corridor and back; the far figure keeps wiping. No one walks."),
    S("S06d", "S06", "ins", "ecu", "day", "HA", [], "TSK_CORRIDOR",
      "High angle extreme close-up: a woman's hand holding a wet white cloth on the polished dark wooden floor, the hand frozen mid-wipe, water sheen on the wood. No face.", line="line021"),
    S("S06e", "S06", "react", "cu", "day", "HA", ["WAKANA"], "TSK_CORRIDOR",
      "High angle chest-up of Wakana kneeling in the corridor, head bowed, eyes on the floor, lips pressed, dry eyes, the long corridor stretching behind.", expr="hurt"),
    # ── S07 가족회의 (분노 정점 → 해방)
    S("S07a", "S07", "sil", "ws", "press", "HA", ["TOMIKO", "MAI", "TAKAYUKI", "WAKANA"], "ZASHIKI",
      "High angle wide of the tatami meeting room: Tomiko seated at the head in front of the blank scroll, Mai beside her in pink, Takayuki in grey samue in a corner with his head down, and Wakana in apron kneeling at the lowest seat by the sliding door; a long lacquered table between them, all faces small.",
      motion="Almost still; Tomiko lifts a tea cup a few centimetres and sets it down. Nobody stands or turns."),
    S("S07b", "S07", "d", "cu", "press", "LA", ["TOMIKO"], "ZASHIKI_HEAD",
      "Low angle chest-up of Tomiko at the head seat, hard top light on her gold-rimmed glasses, composed and cold, the blank scroll soft behind.", line="line022", expr="stern"),
    S("S07c", "S07", "ins", "ecu", "press", "HA", [], "ZASHIKI_TABLE",
      "High angle extreme close-up: an aged woman's hand setting a celadon tea cup down on the lacquered table with a small click, a folded paper fan beside it. No face.", line="line023"),
    S("S07d", "S07", "d", "cu", "press", "HA", ["WAKANA"], "ZASHIKI_DOOR",
      "High angle chest-up of Wakana at the lowest seat, brows drawn together, careful and uncertain, the sliding door soft behind.", line="line024", expr="hurt"),
    S("S07e", "S07", "d", "cu", "press", "LA", ["MAI"], "ZASHIKI_HEAD",
      "Low angle chest-up of Mai in the pink cherry-blossom kimono, red lips in a scornful sneer, eyes half-lidded, hard top light, hands out of frame.", line="line025", expr="sneer"),
    S("S07f", "S07", "d", "cu", "press", "LA", ["MAI"], "ZASHIKI_HEAD",
      "Low angle chest-up of Mai looking down at the camera with a lazy condescending smile, chin raised, red lipstick, the scroll soft behind.", line="line026", expr="sneer"),
    S("S07g", "S07", "ins", "ecu", "press", "HA", [], "ZASHIKI_TABLE",
      "High angle extreme close-up: a woman's hand with a thin gold bangle snapping a paper folding fan open on the lacquered table, cherry-blossom pink silk sleeve. No face.", fx="dutch5 handheld"),
    S("S07h", "S07", "react", "cu", "press", "HA", ["TAKAYUKI"], "ZASHIKI_DOOR",
      "High angle chest-up of Takayuki in the corner, head lowered, eyes fixed on a tea cup below the frame, guilty and silent, hard top light on his unkempt hair.", expr="down"),
    S("S07i", "S07", "d", "cu", "press", "LA", ["TOMIKO"], "ZASHIKI_HEAD",
      "Low angle chest-up of Tomiko, chin lifted, eyes hard behind the gold-rimmed glasses, no smile, decisive.", line="line027", expr="stern"),
    S("S07j", "S07", "sil", "ms", "press", "SIDE", ["TOMIKO"], "ZASHIKI_HEAD",
      "Medium shot from behind Tomiko's rigid shoulders and silver bun at the head seat, her chin raised toward the low seat by the door where a small figure in an apron kneels.", line="line028",
      motion="Tomiko's shoulders stay rigid; her head lifts a few degrees. Nobody moves otherwise."),
    S("S07k", "S07", "face", "ch", "day", "EL", ["WAKANA"], "ZASHIKI_DOOR",
      "Choker close-up of Wakana slowly lifting her head, the tension gone from her face, eyes clear, the faintest liberated smile beginning at the corners of her mouth, soft light.", line="line029", expr="resolve",
      motion="Slow cinematic push-in: she lifts her head a few degrees and a faint calm smile forms slowly; one slow blink. No other movement.", hero=True),
    S("S07l", "S07", "d", "cu", "day", "EL", ["WAKANA"], "ZASHIKI_DOOR",
      "Chest-up close-up of Wakana, composed and clear-eyed, a calm faint smile, the sliding door soft behind.", line="line030", expr="resolve"),
    S("S07m", "S07", "react", "ms", "day", "HA", ["WAKANA"], "ZASHIKI_DOOR",
      "High angle medium shot of Wakana bowing deeply on the tatami at the low seat, both hands on the mat, the long table and the family's knees soft at the top of the frame.", line="line031", expr="resolve"),
    # ── ③ S08 아침 빈 방 (1차 광고 뒤)
    S("S08a", "S08", "empty", "ws", "day", "EL", [], "ROOM_WINDOW",
      "Wide view through a sliding door frame into a small tatami room at morning: the futon folded away, a small low desk by the window with a thick plain navy binder and a plain white envelope on it, soft daylight, sparrows outside. Completely unpopulated.", line="line032",
      motion="Slow push forward through the doorway toward the desk; light shifts gently. No people.", hero=True),
    S("S08b", "S08", "ins", "ecu", "day", "HA", [], "P_FILE",
      "High angle extreme close-up: a thick plain navy-blue binder about fifty pages thick on a low wooden desk, completely blank cover, soft morning light. No hands.", line="line033"),
    S("S08c", "S08", "ins", "ecu", "day", "OH", [], "P_FILE",
      "Overhead extreme close-up: a woman's hand lifting away from the blank navy binder cover, a plain white envelope laid beside it on the wood. No face.", line="line034"),
    # ── S09 마이, 인수인계서 투척
    S("S09a", "S09", "d", "cu", "office_night", "LA", ["MAI"], "TSK_OFFICE",
      "Low angle chest-up of Mai in the small inn office, flicking her chestnut hair back with an airy careless smile, red lipstick, the desk lamp soft behind.", line="line035", expr="sneer"),
    S("S09b", "S09", "ins", "ecu", "office_night", "HA", [], "TSK_OFFICE",
      "High angle extreme close-up: a thick plain navy binder lying crumpled at the bottom of a steel wastebasket beside a desk leg, a corner bent, lamp light from above. No hands.", line="line036"),
    S("S09c", "S09", "estill", "ecu", "office_night", "OH", [], "TSK_OFFICE",
      "Overhead extreme close-up into the steel wastebasket: the blank navy binder resting on crumpled papers, dim lamp light."),
    # ── S10 프런트 붕괴
    S("S10a", "S10", "sil", "ms", "day", "SIDE", ["MAI", "FAMILY"], "TSK_COUNTER",
      "Medium shot from the side at the reception counter: Mai in the pink kimono holding a smartphone out toward a Western couple seen from behind, her face turned to the phone, flustered, the counter between them.", line="line037",
      motion="Mai lifts the phone a little higher and tilts it toward the guests; the guests lean in slightly. Nobody walks."),
    S("S10b", "S10", "sil", "ws", "day", "EL", ["FAMILY", "MAI"], "TSK_GENKAN",
      "Wide view of the entrance hall: a Western family and a Japanese couple seen from behind and in soft focus facing each other across the raised step, one hand holding up a room key, Mai small behind the counter with her hands raised helplessly.", line="line038", fx="handheld",
      motion="The two groups gesture at each other with small movements; Mai raises her hands a little. Faces stay unrecognizable. No one approaches the camera.", hero=True),
    S("S10c", "S10", "sil", "ms", "day", "SIDE", ["MAI", "FAMILY"], "TSK_COUNTER",
      "Over-the-shoulder medium shot from behind a guest's shoulder toward Mai behind the counter, her head bowed in a flustered apology, hair falling forward, her mouth hidden by the angle.", line="line039",
      motion="Mai bows her head a few degrees lower and lifts it; the shoulder in the foreground stays still."),
    S("S10d", "S10", "gfx", "ecu", "office_night", "EL", [], "TSK_OFFICE",
      "Extreme close-up of an open laptop screen on the small office desk glowing plain blank white-blue, the desk lamp beside it, the room dim. No people.", line="line040"),
    # ── S11 메밀차 사고 → 리뷰 → 고함 → 비
    S("S11a", "S11", "ins", "ecu", "day", "HA", [], "ZASHIKI_TABLE",
      "High angle extreme close-up: a steaming cup of brown tea placed on a lacquered meal tray beside small dishes, a female server's hand withdrawing. No face.", line="line041"),
    S("S11b", "S11", "ins", "ecu", "day", "HA", [], "ZASHIKI_TABLE",
      "High angle extreme close-up: an elderly woman's wrinkled hand stopped just above the tea cup, fingers frozen, a beige shawl edge at the frame corner. No face.", line="line042"),
    S("S11c", "S11", "gfx", "ecu", "office_night", "EL", [], "TSK_OFFICE",
      "Extreme close-up of a laptop screen glowing plain blank white, slightly off-axis, the dim office around it. No people."),
    S("S11d", "S11", "d", "cu", "press", "LA", ["TOMIKO"], "TSK_OFFICE",
      "Low angle chest-up of Tomiko in the small office, brows down hard, eyes wide behind the gold-rimmed glasses, furious, hard top light.", line="line043", expr="stern"),
    S("S11e", "S11", "d", "cu", "press", "HA", ["MAI"], "TSK_OFFICE",
      "High angle chest-up of Mai, wide wet eyes, brows raised in panic, red lips parted, hair disheveled, the desk lamp soft behind.", line="line044", expr="panic"),
    S("S11f", "S11", "sil", "ms", "press", "SIDE", ["TOMIKO"], "TSK_OFFICE",
      "Over-the-shoulder medium shot from behind Tomiko's silver bun, one aged hand pushing the gold-rimmed glasses up at the frame edge, Mai a soft blurred shape beyond.", line="line045", fx="dutch7 handheld",
      motion="Tomiko's hand pushes the glasses up and drops out of frame; her shoulders stay rigid. No turning."),
    S("S11g", "S11", "empty", "ws", "rain", "EL", [], "TSK_GENKAN",
      "Wide view of the old inn entrance in the rain: water dripping from the roof tiles, the plain indigo noren hanging wet and still, puddles on the stone step. Completely unpopulated.",
      motion="Rain falls steadily; drops run off the tiles; the noren barely moves. No people."),
    # ── S12 하나이카다 사무실 낮: 사쿠라이의 제안
    S("S12a", "S12", "empty", "ws", "hoff_day", "EL", [], "HOFF",
      "Wide view of a bright modern manager's office of a fine inn in daylight: a neat dark desk, a tea tray with two celadon cups, the hot-spring town visible through the window, bare walls. Completely unpopulated.", line="line046",
      motion="Daylight shifts gently; steam rises from the tea cups. No people."),
    S("S12b", "S12", "d", "cu", "hoff_day", "EL", ["SAKURAI"], "HOFF_WINDOW",
      "Chest-up close-up of Sakurai in a forest-green kimono, sleek silver bob, large pearl earrings, crinkled warm amused eyes, soft daylight from the window.", line="line047", expr="laugh"),
    S("S12c", "S12", "d", "cu", "hoff_day", "EL", ["SAKURAI"], "HOFF_WINDOW",
      "Chest-up close-up of Sakurai with a mischievous teasing half-smile, one eyebrow slightly raised, pearl earrings catching the light.", line="line048", expr="wink"),
    S("S12d", "S12", "react", "cu", "hoff_day", "EL", ["WAKANA_B"], "HOFF_DESK",
      "Chest-up close-up of Wakana in the navy kimono, lips pressed as if holding back a laugh, eyes glistening wet at the lower lids but no tears running, soft daylight.", line="line049", expr="faint"),
    # ── S13 성수기 초일: 천의 전화 → 수화기 낙하 → 2,000만 엔 → 휴지통의 인수인계서 → 빈 현관
    S("S13a", "S13", "sil", "ms", "day", "SIDE", ["TOMIKO"], "TSK_COUNTER",
      "Medium shot from the side at the reception counter: Tomiko in plum kimono lifting an old cream telephone handset to her ear, seen in profile from behind the shoulder, a second phone light blinking on the counter.", line="line050",
      motion="She lifts the handset to her ear and straightens; the small light on the phone keeps blinking. No turning to the camera."),
    S("S13b", "S13", "sil", "ms", "taipei", "SIDE", ["CHEN"], "TAIPEI",
      "Medium shot from directly behind an office chair: a man in a white shirt seen only from the back, holding a telephone handset to his ear, hard stripes of sunlight through venetian blinds across the desk and his shoulders. His face is never visible.", line="line051",
      motion="His shoulders rise slightly as he speaks; he does not turn around at all.", hero=True),
    S("S13c", "S13", "sil", "ecu", "taipei", "HA", ["CHEN"], "TAIPEI_PHONE",
      "High angle extreme close-up: a man's hand holding the base of a desk telephone, the coiled cord stretched toward the top of the frame, blind-stripe light across the desk. No face.", line="line052",
      motion="The fingers tighten slightly on the phone base; nothing else moves."),
    S("S13d", "S13", "d", "cu", "day", "EL", ["TOMIKO"], "TSK_COUNTER",
      "Chest-up close-up of Tomiko with the handset held to her ear just below the frame edge, eyes wide in shock behind the gold-rimmed glasses, lips parted.", line="line053", expr="stern"),
    S("S13e", "S13", "sil", "ms", "taipei", "SIDE", ["CHEN"], "TAIPEI_WINDOW",
      "Medium shot from behind: the man in the white shirt turned toward the venetian blinds with the handset at his ear, the bright blurred city beyond the slats, only the back of his head and shoulder visible.", line="line054",
      motion="He turns his head a few degrees further toward the window; the blinds stay still. His face never shows."),
    S("S13f", "S13", "sil", "ms", "taipei", "SIDE", ["CHEN"], "TAIPEI",
      "Medium shot from behind the office chair, slightly closer: the man's back and the handset at his ear, blind stripes sharp on his shoulders.", line="line055",
      motion="Very slow push-in toward his back; he lowers the handset a few centimetres at the end. No turning."),
    S("S13g", "S13", "face", "ecu", "day", "HA", [], "TSK_COUNTER",
      "High angle extreme close-up: an old cream telephone handset slipping out of an aged woman's hand toward the dark wooden counter, the coiled cord pulling taut. Only the hand and handset are visible.",
      motion="Slow motion: the handset slips from the fingers, drops and swings on its coiled cord against the counter front. The hand stays open and still. No face.", hero=True),
    S("S13h", "S13", "gfx", "ecu", "office_night", "OH", [], "TSK_OFFICE",
      "Overhead extreme close-up: an open ledger book on the small office desk with plain blank ruled pages, a red pen laid across it, warm lamp light. Every page is blank.", line="line056"),
    S("S13i", "S13", "ins", "ecu", "office_night", "HA", [], "TSK_OFFICE",
      "High angle extreme close-up: an aged woman's hand pressing a red pen hard onto a blank ledger page, the pen tip bending, lamp light. No face, no written characters.", line="line057"),
    S("S13j", "S13", "face", "ecu", "office_night", "HA", [], "TSK_OFFICE",
      "High angle extreme close-up at night: an aged woman's hand in a plum kimono sleeve lifting a crumpled plain navy binder out of a steel wastebasket, the binder falling open to a page with a thick red marker band and soft illegible grey lines. No face.", line="line058",
      motion="The hand lifts the binder slowly out of the bin and holds it open; a page settles. No face appears. No readable letters.", hero=True),
    S("S13k", "S13", "empty", "ews", "day", "EL", [], "TSK_GENKAN",
      "Wide view of the old inn's entrance hall in flat daylight, completely empty: the plain indigo noren stirring in the wind, the raised step, the dark counter with nobody behind it, the long corridor silent.", line="line059",
      motion="Slow crane up as the noren sways; the hall stays empty. No people.", hero=True),
    # ── ④ S14 하나이카다: 대만 버스 (2차 광고 뒤)
    S("S14a", "S14", "sil", "ws", "hgen_day", "EL", ["CROWD", "WAKANA_B"], "HGEN_BUS",
      "Wide view from inside the bright lobby through the glass doors: a white tour bus has pulled up outside, its door open, Taiwanese guests stepping down seen from behind and in soft focus, and Wakana in the navy kimono standing at the glass doors bowing to them, small in the frame.", line="line060",
      motion="Guests step down from the bus one at a time; Wakana holds a deep bow then straightens. Faces stay unrecognizable. No one walks toward the camera.", hero=True),
    S("S14b", "S14", "sil", "ms", "hgen_day", "SIDE", ["WAKANA_B", "CROWD"], "HGEN_WIDE",
      "Medium shot from the side: Wakana in the navy kimono greeting a group of guests seen from behind, her head inclined in a gracious bow, her mouth hidden by the angle, sunlight on the light-wood lobby.", line="line061",
      motion="Wakana bows and straightens with a warm expression; the guests stay turned away from the camera. No walking."),
    # ── S15 로비 소파: 단골 노부부 (카메오)
    S("S15a", "S15", "sil", "ms", "hgen_day", "EL", ["REGULAR", "WIFE", "WAKANA_B"], "HGEN_SOFAS",
      "Medium two-shot over Wakana's kimono shoulder in the foreground: the elderly regular couple seated on a lobby sofa by the tall windows, the silver-haired husband in a brown knitted vest looking up with a warm fond smile, his wife beside him in a beige shawl, afternoon sun behind them; the husband's mouth is relaxed and closed.", line="line062",
      motion="The husband's smile deepens and he gives a small nod; the wife tilts her head toward him. Nobody stands."),
    S("S15b", "S15", "sil", "ms", "hgen_day", "SIDE", ["REGULAR", "WIFE"], "HGEN_SOFAS",
      "Medium shot from the side: the elderly husband on the sofa leaning slightly forward, seen in three-quarter profile from behind his wife's shoulder, his hand resting on his knee, warm sun on his silver hair; his mouth not clearly visible.", line="line063",
      motion="He leans a few centimetres forward and settles back; the wife nods slowly. No standing."),
    S("S15c", "S15", "react", "cu", "hgen_day", "HA", ["WAKANA_B"], "HGEN_SOFAS",
      "High angle chest-up of Wakana in the navy kimono bowing her head deeply, eyes closed, a grateful moved expression, sunlight on her hair, the sofa soft behind.", expr="smile"),
    # ── S16 마이의 구직 전화 → 「では、どうぞ、代わりの方と」
    S("S16a", "S16", "gfx", "ecu", "hoff_night", "HA", [], "HOFF_DESK",
      "High angle extreme close-up: a smartphone lying on the dark office desk, its screen glowing plain blank white-blue as if ringing, the warm lamp beside it. No hands."),
    S("S16b", "S16", "d", "cu", "hoff_night", "EL", ["WAKANA_B"], "HOFF_LOW",
      "Chest-up close-up of Wakana in the navy kimono at the night office, the phone at her ear just below the frame edge, level calm eyes, the lamp warm on one side.", line="line064", expr="neutral"),
    S("S16c", "S16", "d", "cu", "hoff_night", "EL", ["WAKANA_B"], "HOFF_WINDOW",
      "Chest-up close-up of Wakana, a still composed face, eyes steady and faintly cold, the town lights blurred behind.", line="line065", expr="neutral"),
    S("S16d", "S16", "d", "cu", "hoff_night", "EL", ["WAKANA_B"], "HOFF_LOW",
      "Chest-up close-up of Wakana with the faintest gentle smile, calm eyes, the lamp glow soft on her cheek.", line="line066", expr="faint"),
    S("S16e", "S16", "face", "ecu", "hoff_night", "HA", [], "HOFF_DESK",
      "High angle extreme close-up: a woman's hand in a navy kimono sleeve setting a smartphone down gently on the dark desk beside the lamp, the screen going dark. Only the hand and phone.",
      motion="The hand lowers the phone, the screen fades to black, the hand rests a moment and withdraws. No face.", hero=True),
    # ── S17 마이 도주, 홀로 남은 도미코
    S("S17a", "S17", "sil", "ws", "alley", "HA", ["MAI", "TAKAYUKI"], "ALLEY",
      "High angle wide of the wet back alley at night: Mai in a coat dragging a suitcase toward a waiting taxi with its roof light on, Takayuki in grey samue running out of the wooden back gate behind her, both small in the frame, faces unrecognizable, steam from a drain.", line="line067",
      motion="Mai climbs into the taxi; its door closes; Takayuki stops a few steps out of the gate and stands still. Faces stay unrecognizable.", hero=True),
    S("S17b", "S17", "empty", "ws", "alley", "EL", [], "ALLEY_TAXI",
      "Wide view down the wet alley at night: a taxi's red tail lights receding between stone walls, wet asphalt reflecting them, no people.", line="line068",
      motion="The taxi drives slowly away down the alley until its tail lights shrink; nothing else moves."),
    S("S17c", "S17", "sil", "ms", "alley", "SIDE", ["TAKAYUKI"], "ALLEY_GATE",
      "Medium shot from behind: Takayuki in charcoal samue standing alone under the orange street lamp by the wooden gate, his back to the camera, head hanging, a smartphone glowing in his lowered hand.", line="line069",
      motion="His shoulders sag; the phone glow flickers in his hand. He does not turn around."),
    S("S17d", "S17", "sil", "ws", "genkan_night", "BE", ["TOMIKO"], "TSK_COUNTER",
      "Extreme bird's-eye view straight down from high above the dark entrance hall at night: Tomiko in plum kimono seated alone behind the reception counter under a single paper lantern, tiny in the frame, an open ledger before her, the hall empty around her.", line="line070",
      motion="Almost still; her head lowers very slowly. No one else appears.", hero=True),
    # ── S18 도미코 애원 → 이중 회수 → 끊음 → 복도 → 절
    S("S18a", "S18", "gfx", "ecu", "hoff_night", "HA", [], "HOFF_DESK",
      "High angle extreme close-up: a smartphone face up on the dark office desk, its screen glowing plain blank white, vibrating, the lamp beside it. No hands."),
    S("S18b", "S18", "react", "cu", "hoff_night", "EL", ["WAKANA_B"], "HOFF_WINDOW",
      "Chest-up close-up of Wakana looking down at the phone below the frame, taking a slow breath, composed, the town lights soft behind.", expr="neutral"),
    S("S18c", "S18", "d", "cu", "office_night", "EL", ["TOMIKO"], "TSK_OFFICE",
      "Chest-up close-up of Tomiko in the small dim office at night, the handset held to her ear below the frame, NO glasses on her face now, eyes wet and shining but cheeks dry, brows drawn up in pleading, lamp light on one side.", line="line071", expr="plead"),
    S("S18d", "S18", "d", "cu", "office_night", "EL", ["TOMIKO"], "TSK_OFFICE",
      "Chest-up close-up of Tomiko without her glasses, face crumpling, eyes wet, a single thin tear track on one cheek at most, lips trembling, the lamp warm.", line="line072", expr="plead"),
    S("S18e", "S18", "sil", "ms", "office_night", "SIDE", ["TAKAYUKI", "TOMIKO"], "TSK_OFFICE",
      "Over-the-shoulder medium shot from behind Takayuki's unkempt hair as he reaches to grab the handset from Tomiko beside him in the dim office, his face turned away from the camera, her silver bun and plum kimono soft beyond.", line="line073", fx="handheld",
      motion="Takayuki's hand closes on the handset and pulls it toward himself; Tomiko's shoulders flinch. His face never turns to the camera."),
    S("S18f", "S18", "d", "cu", "hoff_night", "EL", ["WAKANA_B"], "HOFF_WINDOW",
      "Chest-up close-up of Wakana in the navy kimono with the phone at her ear below the frame, calm warm eyes, no anger, the lamp soft on her face.", line="line074", expr="neutral"),
    S("S18g", "S18", "d", "cu", "hoff_night", "EL", ["WAKANA_B"], "HOFF_LOW",
      "Chest-up close-up of Wakana, eyes lifting slightly, the faintest peaceful smile, the lantern-lit town blurred behind.", line="line075", expr="faint"),
    S("S18h", "S18", "face", "ecu", "hoff_night", "HA", [], "HOFF_DESK",
      "High angle extreme close-up: a woman's hand in a navy kimono sleeve turning a smartphone face down on the dark desk beside the lamp. Only the hand and phone.",
      motion="The hand turns the phone over and lays it face down, then rests flat on the desk beside it. No face.", hero=True),
    S("S18i", "S18", "react", "cu", "ending", "EL", ["WAKANA_B"], "HOFF_WINDOW",
      "Chest-up close-up of Wakana in the navy kimono looking toward the window with a quiet warm smile, golden interior light, soft rim light on her hair.", expr="smile"),
    S("S18j", "S18", "sil", "ms", "ending", "SIDE", ["WAKANA_B"], "HOFF_DOOR",
      "Medium shot from behind: Wakana in the navy kimono walking away from the camera down a warmly lit corridor toward the bright lobby, her low chignon and straight back to the camera, the doorway light ahead.", line="line076",
      motion="She walks slowly away down the corridor toward the light, never turning back; the camera stays still."),
    S("S18k", "S18", "sil", "ws", "hgen_day", "EL", ["WAKANA_B", "GUESTS"], "HGEN_DESK",
      "Wide view of the bright Hanaikada front desk: Wakana in the navy kimono standing behind the long light-wood desk bowing deeply toward the camera, a few guests seen from behind at the frame edges, warm golden light through the windows.", line="line077",
      motion="Wakana holds a deep bow, then slowly straightens with a warm smile; the guests stay turned away. No one walks toward the camera."),
]
CARDS = {"S01f": "老舗旅館の嫁", "S01g": "三か月前"}
CAPTIONS_SMALL = {"S10a": "繁忙期まで、あと三日", "S13a": "繁忙期、初日"}   # 다음 장면 첫 프레임 위 좌하단 소자막(제11장 20)
GFX = {
    "S05d": "휴대폰 게임 화면(흐린 UI, 글자 없음) 발광 lcd",
    "S10d": "노트북 메일함 화면: 영어 메일 제목이 쌓인 목록(글자는 흐림, 미답장 굵게) lcd",
    "S11c": "예약사이트 리뷰 화면: 별점 4.8 → 3.1 애니메이션 + 「Staff couldn't speak English at all」「最悪の対応」 lcd",
    "S13h": "장부 위 「−２，０００万円」 빨간 카운트업(실글꼴, 종이 질감)",
    "S16a": "휴대폰 착신 화면 「麻衣」 lcd",
    "S18a": "휴대폰 착신 화면 「義母」 lcd",
}
GFX_PLATE = {}
EMPH = [  # (기준 줄, 줄 시작 후 초, 길이, 스타일, 문구)
    ("line056", 0.6, 0.4, "Emph", "−５００万円"),
    ("line056", 1.0, 0.4, "Emph", "−１，２００万円"),
    ("line056", 1.4, 2.2, "Emph", "−２，０００万円"),
]
SIGN_BY_LOC = {
    "TSK_GENKAN": ("A small plain blank wooden plate hangs beside the entrance; the noren is plain solid indigo.", "현관 목판 「月見荘」(와이드 1컷만)"),
    "HGEN_WIDE": ("A small plain blank wooden plate stands on the front desk.", "데스크 명판 「花筏」"),
    "HGEN_DESK": ("A small plain blank wooden plate stands on the front desk.", "데스크 명판 「花筏　フロント」"),
    "HGEN_BUS": ("The tour bus side is plain white with no lettering.", "버스 측면 「台北観光」(흐리게, 선택)"),
}
SIGN_BY_SHOT = {}
SIGN_SIZES = ("ms", "ws", "ews")
# 장면 전환: 기본 하드컷, 시간·장소 전환 디졸브 0.5~0.8, 광고 경계 하드컷, 타이틀·카드 암전 금지(제11장 20)
DISSOLVE_INTO = {"S01f": ("fade", 0.5), "S01g": ("fade", 0.5), "S02a": ("fade", 0.5), "S03a": ("fade", 0.5), "S05a": ("fade", 0.5), "S05f": ("fade", 0.5),
                 "S06a": ("fade", 0.6), "S08b": ("fade", 0.5), "S09c": ("fade", 0.5), "S10a": ("fade", 0.5), "S11g": ("fade", 0.6), "S12a": ("fade", 0.6),
                 "S13a": ("fade", 0.5), "S13k": ("fade", 0.5), "S15a": ("fade", 0.5), "S16a": ("fade", 0.6), "S17a": ("fade", 0.5), "S17d": ("fade", 0.6),
                 "S18a": ("fade", 0.6), "S18j": ("fade", 0.5), "S18k": ("fade", 0.5)}
AD_MAX_DISSOLVE = 0.5
# 현장음은 효과음형·무인 컷에만(제6장 4): 사람 있는 컷은 빈 문자열
AMBIENCE = {"S01e": "night wind through a cloth curtain, a paper lantern creaking, distant hot-spring water flowing", "S02a": "gas burner hiss and a rice pot simmering, steam, a fluorescent tube buzzing",
            "S08a": "morning sparrows outside, a soft breeze through paper screens", "S11g": "steady rain on roof tiles, water dripping, cloth flapping wet",
            "S13k": "wind through an empty wooden hall, a cloth curtain flapping, a distant wind chime", "S17b": "a taxi engine receding down a wet alley, crickets, dripping water",
            "S09c": "quiet room tone with a faint lamp hum"}
STYLE = {"NA": "Naration", "若菜": "Wakana", "富子": "Tomiko", "麻衣": "Mai", "隆之": "Takayuki", "桜井": "Sakurai", "陳": "Chen", "常連客": "Regular"}
STYLE_JA = {"Naration": "若菜(語り)", "Wakana": "若菜", "Tomiko": "富子", "Mai": "麻衣", "Takayuki": "隆之", "Sakurai": "桜井", "Chen": "陳", "Regular": "常連客"}
STYLE_COLOR = {"Naration": "&H00FFFFFF", "Wakana": "&H00F0E6C8", "Tomiko": "&H00C8B4E6", "Mai": "&H00B4B4FF", "Takayuki": "&H00DCDCDC", "Sakurai": "&H00C8E6DC", "Chen": "&H00E6DCC8", "Regular": "&H00DCE6F0"}
PRO_MODEL = "fal-ai/bytedance/seedance/v1/pro/image-to-video"
HERO_MODEL = "fal-ai/kling-video/v3/pro/image-to-video"  # 히어로 컷(3테이크) — PHASE 5 실행 전 fal 모델 ID·응답 형식 확인
HERO_TAKES = 3
RATE = {"pro": 0.108, "lite": 0.036, "omni": 0.16, "kf": 0.04, "hero": 0.112}
