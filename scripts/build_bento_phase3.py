#!/usr/bin/env python3
"""『閉店間際の弁当屋』(bento-ja) PHASE 3 샷 리스트 Lock 생성기 — build_beggar_phase3.py를 옮긴 것.

이 작품에서 달라진 것:
  · 시대 두 개(1996 회상 = 따뜻한 3200K / 2026 현재 = 차가운 형광등), 같은 인물이 두 나이로 나온다(修三 43·73, 拓海 12·42).
    동일인 표식은 점·흉터가 아니라 눈매·귀·머리 모양(제19장 5).
  · 내레이션·VO 줄 앞 지문 컷은 그 목소리 아래에 깐다(build_lock.py VO_UNDER, 제19장 4) — 지문 컷이 그 줄을 「싣는다」.
  · 동전은 일본 50엔 5개(250엔, 은색·둥근 구멍, 제19장 6), 「tearful smile」 금지 → 「wet eyes, small closed-mouth smile」.
  · 편지 낭독(S12)은 전부 VO, 줄마다 회상 매치 컷·修三 리액션. S12 머리 질문 카드 2초(무언, 클립에 직접).
입력: productions/bento-ja/lock.json · 00_script_ja.md · assets/auditions/bento-tts/lineNNN.mp3 · assets/portraits/bento-cast/cells/
출력: scripts/storyboard/bento.json · scripts/scenes/bento.json · scripts/audio/bento.json · subs/bento.ass ·
      assets/audio-overrides/bento/lineNNN.mp3 · productions/bento-ja/07_샷리스트.md · 16_감정일치표.md
사용법: python3 scripts/build_bento_phase3.py
"""
import collections, json, os, re, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "bento-ja")
SKIT = "bento"
TTS_DIR = "bento-tts"
TITLE = "閉店間際の弁当屋"
FPS = 24; HARD = 1 / FPS; OMNI_MAX = 7.9; LEAD = 0.3; MIN_SHOT = 1.1; STILL_MAX = 6.5; I2V_MAX = 10.0

C = "assets/portraits/bento-cast/cells/"
WHO = {
    "SH96": ("Noguchi Shuzo in 1996, a Japanese man aged 43, square angular face with a strong jaw, thick straight black eyebrows, deep-set eyes, "
             "short cropped black hair with a little grey at the temples, clean-shaven, no glasses, no earrings", C + "shuzo1996-front.png"),
    "SH26": ("Noguchi Shuzo now, a Japanese man aged 73, the same square angular face and strong jaw, thick straight WHITE eyebrows, deep-set eyes, "
             "short cropped WHITE hair, deep wrinkles, clean-shaven, no glasses, no earrings", C + "shuzo2026-front.png"),
    "SH60": ("Noguchi Shuzo about ten years ago, a Japanese man aged 63, square angular face, thick greying eyebrows, short cropped grey hair, "
             "clean-shaven, no glasses, no earrings", C + "shuzo2026-front.png"),
    "SUM": ("Noguchi Sumie, a Japanese woman aged 40, round soft face with full cheeks, gentle down-turned eyes, black hair in a low bun, "
            "natural light makeup, no glasses, no earrings, no moles", C + "sumie-front.png"),
    "SUM50": ("Noguchi Sumie about ten years ago, a Japanese woman aged 53, the same round soft face, gentle down-turned eyes, black hair streaked "
              "with grey in a low bun, pale and thin from illness, no glasses, no earrings", C + "sumie-front.png"),
    "TB": ("Asakura Takumi as a boy, a thin Japanese boy aged 12, LARGE round dark eyes with double eyelids, ears that stick out slightly, "
           "messy straight black hair with a fringe, thin straight eyebrows, no glasses", C + "takumi12-front.png"),
    "TA": ("Asakura Takumi grown up, a slim Japanese man aged 42, the same LARGE round dark eyes with double eyelids, ears that stick out slightly, "
           "thin straight eyebrows, short neat black hair, clean-shaven, no glasses, no earrings", C + "takumi42-front.png"),
    "MIO": ("Asakura Mio, a small Japanese girl aged 6, round face, black bob with straight blunt bangs, round eyes, no glasses", C + "mio6-front.png"),
    "HINA": ("Asakura Hina, a Japanese girl aged 8, oval face, black hair in two low pigtails, round eyes, no glasses", C + "hina8-front.png"),
    "MIO36": ("Asakura Mio grown up, a Japanese woman aged 36, round face, black bob with straight blunt bangs, no glasses, no earrings", C + "mio36-front.png"),
    "KIDS": ("a few Japanese schoolchildren seen from behind or out of focus in the background, faces never in focus", None),
}
WARD = {
    "SH96": "a plain white cook's jacket, a plain navy-blue full apron with no print, a plain white cotton towel tied around the forehead as a headband",
    "SH26": "a faded plain navy-blue full apron with no print over a plain grey knitted cardigan and a plain white shirt",
    "SH60": "a plain grey knitted cardigan over a plain white shirt",
    "SUM": "a plain pale-pink triangle headscarf, a plain white full apron with no print over a plain beige long-sleeve top",
    "SUM50": "a plain pale-blue hospital gown",
    "TB": "a plain navy-blue zip jumper with sleeves a little too short for his wrists, a plain grey T-shirt, plain grey trousers",
    "TBW": "a plain navy-blue zip jumper soaked dark with rain, a plain white hand towel around his neck, wet hair",
    "TA": "a plain charcoal wool overcoat with no logo, a plain white shirt",
    "MIO": "a plain red knitted beanie and a plain yellow puffy jumper",
    "HINA": "a plain cream wool coat with round buttons and no logo",
    "MIO36": "a plain light-grey sweater under a plain navy apron with no print",
    "SH26A": "a plain navy apron with no print over a plain white shirt, a plain white bandana",
    "TAA": "a plain navy apron with no print over a plain white shirt",
}
EXPR = {  # PHASE 2 Kill Gate 합격 셀(08_PHASE2_검수.md) — 사용 금지 칸(SH26·TA 하단 가운데)은 넣지 않는다
    ("SH96", "gruff"): C + "shuzo1996-expr1.png", ("SH96", "soft"): C + "shuzo1996-expr2.png", ("SH96", "choke"): C + "shuzo1996-expr1.png",
    ("SH96", "back"): C + "shuzo1996-back.png", ("SH96", "full"): C + "shuzo1996-full.png",
    ("SH26", "calm"): C + "shuzo2026-expr1.png", ("SH26", "grief"): C + "shuzo2026-expr3.png", ("SH26", "back"): C + "shuzo2026-back.png",
    ("SH26", "full"): C + "shuzo2026-full.png",
    ("SUM", "smile"): C + "sumie-expr1.png", ("SUM", "worry"): C + "sumie-expr2.png", ("SUM", "teary"): C + "sumie-expr3.png", ("SUM", "back"): C + "sumie-back.png",
    ("TB", "shy"): C + "takumi12-expr1.png", ("TB", "smile"): C + "takumi12-expr2.png", ("TB", "tears"): C + "takumi12-expr3.png", ("TB", "back"): C + "takumi12-back.png",
    ("TA", "calm"): C + "takumi42-expr1.png", ("TA", "cry"): C + "takumi42-expr3.png", ("TA", "back"): C + "takumi42-back.png",
    ("MIO", "shy"): C + "mio6-expr1.png", ("MIO", "smile"): C + "mio6-expr2.png", ("MIO", "back"): C + "mio6-back.png",
    ("HINA", "curious"): C + "hina8-expr1.png", ("HINA", "smile"): C + "hina8-expr2.png",
    ("MIO36", "smile"): C + "mio36-expr2.png",
}
LOC = {
    "S96W": C + "loc-shop96-wide.png", "S96O": C + "loc-shop96-ots.png", "S96R": C + "loc-shop96-reverse.png", "S96H": C + "loc-shop96-high.png",
    "S96L": C + "loc-shop96-low.png", "S96C": C + "loc-shop96-curtain.png", "S96S": C + "loc-shop96-showcase.png", "S96X": C + "loc-shop96-outside.png",
    "S26W": C + "loc-shop26-wide.png", "S26O": C + "loc-shop26-ots.png", "S26R": C + "loc-shop26-reverse.png", "S26K": C + "loc-shop26-sticker.png",
    "FRONT": C + "loc-street-front.png", "SHUT": C + "loc-street-shutter.png", "RAIN": C + "loc-street-rain.png", "APT": C + "loc-street-apartment.png",
    "KIT": C + "loc-kitchen-wide.png", "NAIL": C + "loc-kitchen-nail.png", "MAIL": C + "loc-mailbox.png", "HOSP": C + "loc-hospital.png",
    "SHOKW": C + "loc-shokudo-wide.png", "SHOKC": C + "loc-shokudo-counter.png",
    "P_NORI": C + "prop-noribento.png", "P_KARA": C + "prop-karaage.png", "P_STK": C + "prop-sticker.png", "P_LET": C + "prop-letter.png",
    "P_TOWEL": C + "prop-towel.png", "P_FRAME": C + "prop-frame.png", "P_BAG": C + "prop-bag.png", "P_BIRD": C + "prop-origami.png",
}
PRESET = ("Photorealistic live-action Japanese human drama, a tiny bento shop by a local train station, Arri Alexa cinematic color grade, "
          "Kodak 35mm film grain, 24fps, 16:9, restrained Japanese film mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, "
            "signage lettering, menus with writing, price tags with writing, documents with writing, screens with text, printed labels, brand logos, "
            "watermarks, stamps, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, anime, 3d render, cartoon, "
            "thick glossy gel tears, cartoon sweat drops, multiple tear streams on both cheeks, glasses, earrings, piercings, pink eyeshadow, lipstick on men")
PLAIN = "All papers, price cards, notices, signs, envelopes and labels are completely blank; no letters, numbers or symbols anywhere in the frame."
COINS = ("EXACTLY FIVE Japanese 50-yen coins: silver cupronickel, each with a small ROUND hole in the center, engravings soft and out of focus; "
         "NOT square holes, NOT Chinese coins, NOT gold.")
TEARS = ("Realistic tears as in a live-action film: reddened eye rims, glossy wet eyes catching the light, a small clear tear bead on the lower lashes, "
         "at most one thin translucent tear track on one cheek, a slightly reddened nose tip, matte natural skin; no glossy gel streams, no cartoon droplets.")
SWEAT = ("Realistic sweat as in a live-action film: fine tiny beads of perspiration on the forehead and temples, a faint natural sheen; "
         "no large cartoon drops, no face-wide shine.")
GLASSES = {k: ("She wears no glasses." if k in ("SUM", "SUM50", "MIO", "HINA", "MIO36") else "He wears no glasses.") for k in
           ("SH96", "SH26", "SH60", "SUM", "SUM50", "TB", "TA", "MIO", "HINA", "MIO36")}
WET_HOLD = " Eyes wet and glistening with tears welling on the lower lids but NOT running down — the tears stay pooled."
TEARS_FLOW = (" NOT smiling at any moment, mouth corners turned down, chin trembling slightly. One clear tear slowly spills over the lower lid and "
              "runs down the cheek along its natural curve, catching the light; a slow blink, a trembling breath; only one tear line, thin and translucent.")
WET_SMILE = " wet eyes and a small closed-mouth smile (lips together, no teeth), natural skin, NO makeup."
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, the face fills at least half of the frame height",
    "ots": "50mm lens, f/2.0, over-the-shoulder three-quarter framing, the listener's blurred shoulder and back of the head in the near foreground edge, the speaker's face at least one third of the frame height",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds, the person's face at least one quarter of the frame height",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus",
}
LIGHT = {
    "s96": "night in 1996: the glass showcase's own warm 3200K light is the key light from below on the counter, a warm ceiling lamp, deep soft shadows, faces readable",
    "s96rain": "rainy night in 1996: warm 3200K showcase key light inside, cold blue wet street beyond the glass door, faces readable",
    "s26": "night now: cool 5600K fluorescent ceiling light and the showcase glow, faded walls, a lonely quiet mood, faces readable",
    "s26warm": "night now: the showcase's warm glow and one warm lamp, cool fluorescent turned low, intimate, faces readable",
    "kit96": "the small back kitchen at night in 1996: one warm 3200K bulb, steam glowing, soft contrast",
    "alley": "night in 1996: the cold white glow of a vending machine beside a small park bench, deep blue shadows, faces readable",
    "street_n": "night: warm shop light spilling onto wet asphalt, cool blue streetlights, no cars, no headlights",
    "spring_n": "a spring night in 1997: warm shop light, a cherry tree under a streetlight, petals glowing",
    "hosp": "a quiet hospital room about ten years ago: soft diffused afternoon window backlight, low contrast, gentle",
    "morning": "early morning now: soft cool daylight, long gentle shadows",
    "shokudo": "bright warm daytime in a small children's cafeteria, soft window light, cheerful",
    "letter": "night now in the shop: a warm desk lamp on the counter, the rest of the shop dim and cool, the face lit warmly from below and the side",
    "product": "soft warm light on a dark wooden counter",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "SIDE": "eye-level from the side or behind"}
SPK_KEYS = {"修三": ("SH96", "SH26", "SH60"), "澄江": ("SUM", "SUM50"), "拓海(少年)": ("TB",), "拓海(大人)": ("TA",), "美緒": ("MIO",), "陽菜": ("HINA",)}


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, act="", vo=False):
    """kind: d(OmniHuman 어깨 너머 3/4 립싱크) / face(사람 i2v) / empty(무인 i2v) / estill(무인·합성 면 정지) /
    ins(손·소품 — motion 있으면 i2v, 없으면 정지) / reuse:<id> / card.  vo=True = 화자 화면 밖 또는 입이 안 보임(목소리만)."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc, subject=subject,
                line=line, fx=fx, motion=motion, expr=expr, act=act, vo=vo)


H96, H26, H60, SU, SU50 = "SH96:SH96", "SH26:SH26", "SH60:SH60", "SUM:SUM", "SUM50:SUM50"
TB_, TBW, TA_, MI, HI, MI36 = "TB:TB", "TB:TBW", "TA:TA", "MIO:MIO", "HINA:HINA", "MIO36:MIO36"
OB = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, keeps looking "
      "toward the other person at the same three-quarter angle, hands keep doing what they do in the first frame; no exaggerated motion, the same person throughout.")
HOLD = " Head stays at the same angle, never turns toward the camera; only body, hands and breath move. Mouth stays closed, lips still — this person is NOT speaking."
NS = " NOT smiling at any moment."

SHOTS = [
    # ① 후크 0:00~0:20
    S("H0", "H", "ins", "ecu", "letter", "HA", [H26], "P_LET", "Insert: old wrinkled hands slowly unfolding a sheet of plain white letter paper on a worn wooden counter, the hands trembling slightly, no face.",
      motion="The hands unfold the paper slowly, a slight tremble; nothing else moves."),
    S("H1", "H", "estill", "ecu", "letter", "EL", [], "P_LET", "Close-up of the plain white letter paper on the counter under a warm lamp, blank for one composited vertical handwritten line.", line="L01", vo=True),
    S("H2", "H", "face", "cu", "letter", "EL", [H26], "S26O", "Close-up of old Shuzo at the counter, eyes red-rimmed and wet, holding back tears, looking down at a letter out of frame.",
      line="NA0", motion="He looks down at the letter." + TEARS_FLOW + HOLD, expr="grief"),
    S("H3", "H", "empty", "ws", "street_n", "EL", [], "FRONT", "The tiny bento shop at night by the station, warm light through the glass door, a blank signboard above for a composited shop name. Title composited.",
      motion="The warm light flickers faintly, a light drizzle; the building stays perfectly still; no cars, no headlights."),

    # S01 현재 — 폐업 안내
    S("S01a", "S01", "face", "ws", "s26", "EL", [H26], "S26R", "Seen through the glass front door from the dark street: a blank white notice taped on the glass in the foreground, beyond it old Shuzo alone wiping the counter.",
      line="NA1", motion="He wipes the counter slowly in small circles; the notice stays still." + HOLD, expr="calm"),
    S("S01b", "S01", "face", "ms", "s26", "HA", [H26], "S26O", "Medium: old Shuzo behind the counter wiping it with a cloth, tired and quiet, the near-empty showcase in front.",
      line="NA2", motion="He wipes the counter slowly, a tired breath." + HOLD, expr="calm"),
    S("S01c", "S01", "ins", "ecu", "s26", "HA", [H26], "S26K", "Insert: an old fingertip slowly tracing one faded small round red sticker stuck on the corner of the worn counter, no face.",
      line="NA3", motion="The fingertip traces the faded sticker once, slowly."),
    S("S01d", "S01", "ins", "ecu", "s26", "EL", [H26], "P_KARA", "Insert: old hands pressing one bright red round blank sticker onto the clear lid of a fresh karaage bento, no face.",
      line="NA3a", motion="The thumb presses the sticker flat onto the lid, slowly."),
    S("S01e", "S01", "estill", "ecu", "s26", "EL", [], "P_BIRD", "Insert: a small faded origami robin folded from red paper sitting alone in the corner of a dusty shelf."),
    S("S01f", "S01", "face", "cu", "s26", "SIDE", [H26], "S26W", "Close-up profile of old Shuzo looking toward the glass door, lost in memory.",
      line="NA4", motion="He looks toward the door, a slow blink, a long breath." + HOLD, expr="calm"),

    # S02 1996 — 첫 만남
    S("S02a", "S02", "ins", "ecu", "s96", "EL", [H96], "S96S", "Insert, 1996: a man's hands sticking a bright red round blank sticker onto a blank paper price card on the showcase, no face.",
      line="NA5", motion="The hands press the red sticker onto the card."),
    S("S02b", "S02", "face", "ms", "s96", "EL", [TB_], "S96R", "Medium, 1996: a thin boy in a short-sleeved navy jumper stepping in through the glass sliding door, the small brass bell above, the dark wet street behind.",
      motion="The boy steps in and stops just inside the door, glancing at the showcase; the bell sways." + HOLD, expr="shy"),
    S("S02c", "S02", "ins", "ecu", "s96", "HA", [TB_], "S96S", "Insert: a boy's small open palm over the showcase glass holding coins. " + COINS + " No face.",
      motion="The small fingers count the coins one by one, slowly."),
    S("S02d", "S02", "d", "ots", "s96", "HA", [TB_, H96], "S96O", "Over Shuzo's blurred shoulder (right foreground), slightly high: the boy at three-quarter angle across the showcase, looking up shyly, coins in his palm.", line="L02",
      act="The boy asks shyly for one nori bento, looking up at the shop owner across the showcase, coins held in his palm, quietly, voice small. Answering nobody yet — speaking first." + OB, expr="shy"),
    S("S02e", "S02", "d", "ots", "s96", "LA", [H96, TB_], "S96C", "Over the boy's blurred shoulder (left foreground), slightly low: Shuzo at three-quarter angle behind the counter, pulling out a plastic bag, not looking at the boy.", line="L03",
      act="Shuzo tells the boy the price curtly, pulling out a plastic bag, eyes on his hands, gruff but not unkind. Answering the boy's shy order." + OB, expr="gruff"),
    S("S02f", "S02", "face", "ws", "s96", "HA", [H96, TB_], "S96W", "Wide, 1996: the boy at the showcase receiving a small bag, Shuzo behind the counter, the lit showcase between them, three bento left.",
      line="NA6", motion="The boy takes the bag carefully with both hands; Shuzo turns back to his work." + HOLD),

    # S03 주방
    S("S03a", "S03", "face", "ws", "kit96", "HA", [SU, H96], "KIT", "Wide, 1996: the small back kitchen, Sumie washing a pot at the sink and glancing toward the shop, Shuzo washing rice in a bowl beside her.",
      motion="Sumie washes the pot and glances toward the shop; Shuzo's hands wash rice steadily." + HOLD, expr="worry"),
    S("S03b", "S03", "d", "ots", "kit96", "EL", [SU, H96], "KIT", "Over Shuzo's blurred shoulder (right foreground): Sumie at three-quarter angle drying her wet hands on her apron, talking to him.", line="L04",
      act="Sumie tells her husband that the boy came again tonight, two weeks now, drying her wet hands on her apron, brightly but with concern." + OB, expr="smile"),
    S("S03c", "S03", "face", "cu", "kit96", "EL", [SU], "KIT", "Close-up of Sumie looking at her husband, waiting for an answer, a little worried.", line="L05", vo=True,
      motion="She looks at him, waiting, a small breath." + HOLD, expr="worry"),
    S("S03d", "S03", "d", "ots", "kit96", "EL", [SU, H96], "KIT", "Over Shuzo's blurred shoulder: Sumie lowering her voice, worried.", line="L06",
      act="Sumie lowers her voice, quiet and worried, wondering whether the boy is eating properly, always buying the cheapest one." + OB, expr="worry"),
    S("S03e", "S03", "ins", "ecu", "kit96", "HA", [H96], "KIT", "Insert: a man's hands in a bowl of rice and water, stopping still, no face.",
      line="NA7", motion="The hands stop moving in the rice water; ripples settle."),
    S("S03f", "S03", "face", "cu", "kit96", "SIDE", [H96], "KIT", "Close-up side view of Shuzo staring down at his still hands, thinking, jaw set.",
      line="NA8", motion="He stares down, a slow breath, jaw set." + HOLD, expr="gruff"),

    # S03b 골목 — 반씩
    S("S03ba", "S03b", "face", "ws", "alley", "EL", [SU], None, "Wide from behind a dark tree in a back alley at night: Sumie holding a garbage bag, stopping to look toward a small park bench under a vending machine's glow.",
      line="L06a", vo=True, motion="She stops and looks toward the bench, the garbage bag in her hand." + HOLD, expr="worry"),
    S("S03bb", "S03b", "face", "ms", "alley", "EL", [TB_, MI], None, "Medium three-quarter from the side, night: on a park bench under a vending machine glow, the boy scooping rice from a nori bento onto the plastic lid for his little sister beside him, his mouth hidden as he leans over.",
      line="L06b", vo=True, motion="He scoops rice onto the lid and pushes it toward her, leaning over; his face stays turned down toward the food." + HOLD),
    S("S03bd", "S03b", "face", "ms", "alley", "EL", [TB_], None, "Medium: the boy pressing a hand to his stomach and smiling at his sister, pretending to be full.",
      line="NA8a", motion="He pats his stomach lightly and smiles, lips together." + HOLD, expr="smile"),
    S("S03be", "S03b", "face", "cu", "alley", "SIDE", [SU], None, "Close-up of Sumie behind the tree, a hand rising to her mouth, eyes wet.",
      line="NA8b", motion="Her hand rises to her mouth." + WET_HOLD + HOLD, expr="teary"),
    S("S03bf", "S03b", "d", "ots", "kit96", "EL", [SU, H96], "KIT", "Back in the kitchen, over Shuzo's blurred shoulder: Sumie with wet eyes, speaking quietly to him.", line="L06c",
      act="Sumie tells him quietly, eyes wet, that the boy shared it with his sister and pretended he had already eaten. Speaking to her husband who is washing rice." + WET_HOLD + OB, expr="teary"),
    S("S03bg", "S03b", "face", "cu", "kit96", "EL", [SU], "KIT", "Close-up of Sumie hearing his answer, a small relieved smile through wet eyes.", line="L06d", vo=True,
      motion="Her face softens into a small relieved smile, lips together." + WET_HOLD + HOLD, expr="teary"),

    # S04 비 오는 밤
    S("S04a", "S04", "face", "ms", "s96rain", "EL", [TBW], "S96R", "Medium, rainy night 1996: the boy stepping in through the glass door soaked, hair dripping, rain behind him.",
      motion="He steps in, drips of rain falling from his hair, shoulders hunched." + HOLD, expr="shy"),
    S("S04b", "S04", "d", "ots", "s96rain", "LA", [H96, TBW], "S96C", "Over the wet boy's blurred shoulder, slightly low: Shuzo holding out a plain white hand towel across the counter, gruff.", line="L07",
      act="Shuzo holds out a towel across the counter and tells the boy curtly to wipe himself, the floor is getting wet, gruff but caring. Speaking to the soaked boy." + OB, expr="gruff"),
    S("S04c", "S04", "face", "ms", "s96rain", "HA", [TBW], "S96O", "Medium, slightly high: the boy taking the towel and bowing his head deeply, face hidden by his wet hair.", line="L08", vo=True,
      motion="He takes the towel and bows his head; his face stays hidden." + HOLD),
    S("S04d", "S04", "ins", "ecu", "s96rain", "HA", [H96], "P_NORI", "Insert: tongs quietly placing two pieces of fried karaage onto an open nori bento, no face.",
      motion="The tongs set the karaage down, one then the other."),
    S("S04e", "S04", "d", "ots", "s96rain", "LA", [H96, TBW], "S96C", "Over the boy's blurred shoulder: Shuzo holding out the bag, eyes averted.", line="L09",
      act="Shuzo holds out the bag, avoiding the boy's eyes, telling him the karaage was left over, just leftovers. Gruff, embarrassed." + OB, expr="gruff"),
    S("S04f", "S04", "d", "ots", "s96rain", "HA", [TBW, H96], "S96O", "Over Shuzo's blurred shoulder: the boy hugging the bag to his chest with both hands, eyes shining, the towel around his neck.", line="L10",
      act="The boy thanks him brightly, hugging the bag to his chest, eyes shining. Answering the shop owner who just gave him extra." + OB, expr="smile"),
    S("S04g", "S04", "d", "ots", "s96rain", "LA", [H96, TBW], "S96C", "Over the boy's blurred shoulder: Shuzo wiping the counter, eyes on the cloth, pretending not to care.", line="L10a",
      act="Shuzo asks offhandedly whether the boy goes to school properly, eyes on the cloth he wipes with." + OB, expr="gruff"),
    S("S04h", "S04", "d", "ots", "s96rain", "HA", [TBW, H96], "S96O", "Over Shuzo's blurred shoulder: the boy with the towel around his neck, a little proud.", line="L10b",
      act="The boy answers a little proudly that he is the best in his class at arithmetic. Answering the shop owner's question." + OB, expr="smile"),
    S("S04i", "S04", "face", "cu", "s96rain", "HA", [TBW], "S96O", "Close-up of the boy smiling shyly after the answer.", line="L10c", vo=True,
      motion="He smiles shyly, lips together, the towel around his neck." + HOLD, expr="smile"),
    S("S04j", "S04", "face", "ws", "s96rain", "EL", [TBW], "S96X", "Wide from outside in the rain: the boy leaving with the bag held to his chest, the warm shop glowing behind him.",
      line="NA9", motion="He walks out into the rain away from the camera, the bag held close." + HOLD, expr="back"),

    # S05 반전 ①
    S("S05a", "S05", "estill", "ecu", "s96", "EL", [], "S96S", "Insert: inside the lit showcase, the empty slot where a karaage bento was, its blank paper price card with a red round sticker on it.", line="NA10"),
    S("S05b", "S05", "ins", "ecu", "s96", "HA", [H96], "S96S", "Insert: a man's hands taking coins from a small worn brown coin purse and placing them into the open cash register drawer, no face.",
      line="NA11", motion="The coins drop one by one into the drawer."),
    S("S05c", "S05", "face", "cu", "s96", "EL", [H96], "S96C", "Close-up of Shuzo at the register, quietly counting, the half-shutter behind him.",
      line="NA11a", motion="He counts quietly, a small breath." + HOLD, expr="gruff"),
    S("S05d", "S05", "face", "ms", "kit96", "EL", [SU], "S96C", "Medium through the kitchen doorway frame: Sumie with folded arms watching him, a small knowing smile.",
      motion="She folds her arms and smiles a little, shaking her head once." + HOLD, expr="smile"),
    S("S05e", "S05", "d", "ots", "s96", "EL", [SU, H96], "S96C", "Over Shuzo's blurred shoulder: Sumie in the doorway, arms folded, teasing.", line="L11",
      act="Sumie teases him with a small laugh, arms folded, saying he is doing it again and the shop will go under." + OB, expr="smile"),
    S("S05f", "S05", "d", "ots", "s96", "EL", [H96, SU], "S96R", "Over Sumie's blurred shoulder: Shuzo closing the drawer, half-turned away at three-quarter angle, embarrassed.", line="L12",
      act="Shuzo closes the drawer and half turns away, telling her it was leftovers, let's leave it at that, embarrassed and gruff." + OB, expr="gruff"),
    S("S05g", "S05", "face", "ws", "s96", "HA", [H96, SU], "S96H", "High wide: the shop at closing, Shuzo at the register and Sumie in the kitchen doorway, the showcase light between them.",
      line="NA12", motion="Sumie smiles and goes back into the kitchen; Shuzo wipes the counter." + HOLD),

    # S06 단서 — 오지 않은 밤
    S("S06a", "S06", "estill", "ecu", "s96", "EL", [], None, "Insert: a plain round wall clock with a BLANK face (no numerals) in the shop at night, the hands just past the top.", line="NA13"),
    S("S06b", "S06", "face", "cu", "s96", "EL", [H96], "S96C", "Close-up of Shuzo behind the counter glancing toward the glass door on screen left, waiting.",
      line="NA14", motion="He glances toward the door on the left, then back, then toward the door again." + HOLD, expr="gruff"),
    S("S06c", "S06", "empty", "ws", "s96", "LA", [], "S96R", "Wide: the glass sliding door from inside, the bell still, the dark street empty.",
      motion="Nothing moves except a faint flicker of the street light; the bell stays still."),

    # S07 기다림
    S("S07a", "S07", "face", "ms", "street_n", "LA", [H96], "SHUT", "Medium from outside, night: Shuzo holding the half-lowered shutter, stopped, looking out at the wet empty street.",
      line="NA15", motion="He holds the shutter and looks out, a slow breath." + HOLD, expr="gruff"),
    S("S07b", "S07", "face", "ws", "street_n", "EL", [H96], "APT", "Wide from behind: Shuzo standing in front of an old two-storey wooden apartment at night, holding a small plastic bag, looking up.",
      line="NA15a", motion="He stands still looking up, the bag hanging from his hand." + HOLD, expr="back"),
    S("S07c", "S07", "empty", "ms", "street_n", "LA", [], "APT", "Medium low angle: the dark corner window on the second floor of the old apartment, no light inside.",
      line="NA15b", motion="Nothing moves; a faint breeze stirs a curtain edge behind the dark glass."),
    S("S07d", "S07", "d", "ots", "s96", "EL", [SU, H96], "S96R", "Back in the shop, over Shuzo's blurred shoulder at the shutter: Sumie beside him, speaking quietly.", line="L13",
      act="Sumie says quietly, standing beside her husband at the shutter, that he is waiting for the boy, isn't he." + OB, expr="worry"),
    S("S07e", "S07", "d", "ots", "s96", "EL", [H96, SU], "S96R", "Over Sumie's blurred shoulder: Shuzo still holding the shutter, looking out at the street at three-quarter angle.", line="L14",
      act="Shuzo answers without letting go of the shutter, looking out at the street, that he just hates to waste the leftovers, quiet and steady, covering his feelings." + OB, expr="gruff"),
    S("S07f", "S07", "estill", "ecu", "s96", "EL", [], "P_KARA", "Insert: inside the showcase one karaage bento with a red round blank sticker on its lid, slowly going cold.", line="NA16"),

    # S08 재회 — 출세하면 갚아
    S("S08a", "S08", "face", "ws", "s96", "EL", [TB_, MI], "S96R", "Wide, night: the boy at the glass door holding his little sister's hand, his eyes red.",
      motion="They stand at the door; the boy grips his sister's hand; the bell sways." + HOLD, expr="tears"),
    S("S08b", "S08", "d", "ots", "s96", "HA", [TB_, H96], "S96O", "Over Shuzo's blurred shoulder, slightly high: the boy holding his sister's hand, holding back a trembling voice.", line="L15",
      act="The boy asks, holding back a trembling voice, whether the shop is already closed, gripping his little sister's hand." + WET_HOLD + NS + OB, expr="tears"),
    S("S08c", "S08", "d", "ots", "s96", "LA", [H96, TB_], "S96C", "Over the boy's blurred shoulder, low: Shuzo raising the half-lowered shutter back up.", line="L16",
      act="Shuzo tells him shortly that it is not closed yet, come in, pushing the shutter back up." + OB, expr="gruff"),
    S("S08d", "S08", "face", "ms", "s96", "EL", [MI], "S96S", "Medium from behind and to the side: the little girl in the red beanie pressing her hands on the showcase glass, staring at the bento, face turned away.",
      line="L17", vo=True, motion="She presses her hands on the glass and stares at the bento." + HOLD),
    S("S08e", "S08", "face", "cu", "s96", "HA", [TB_], "S96O", "Close-up, slightly high: the boy with his head bowed low, coins in his hand, face hidden by his fringe.",
      line="L18", vo=True, motion="He keeps his head bowed; his shoulders shake slightly." + HOLD),
    S("S08f", "S08", "ins", "ecu", "s96", "HA", [TB_], "S96S", "Insert: the boy's small palm over the showcase glass holding coins, the same framing as the first night. " + COINS + " No face.",
      motion="The small hand trembles slightly."),
    S("S08g", "S08", "ins", "ecu", "s96", "HA", [H96], "P_BAG", "Insert: a man's hands silently putting two bento boxes into a plastic bag, adding an extra piece of karaage to one, no face.",
      motion="The hands place the bento into the bag, one then the other."),
    S("S08h", "S08", "d", "ots", "s96", "LA", [H96, TB_], "S96C", "Over the boy's blurred shoulder: Shuzo holding out two bags, looking him in the eye.", line="L19",
      act="Shuzo holds out two bags and tells the boy both are leftovers, the money is fine, looking him in the eye, firm and gentle." + OB, expr="gruff"),
    S("S08i", "S08", "face", "cu", "s96", "LA", [H96], "S96C", "Close-up of Shuzo hearing the boy refuse, eyes softening.", line="L20", vo=True,
      motion="His eyes soften, a slow breath." + HOLD, expr="gruff"),
    S("S08j", "S08", "d", "ots", "s96", "EL", [H96, TB_], "S96C", "Over the boy's blurred shoulder, eye level: Shuzo leaning over the counter on both hands to meet the boy's eyes.", line="L21",
      act="Shuzo leans on the counter with both hands to meet the boy's eye level and tells him, gruff but warm, then pay me back when you've made it, come back when you grow up." + OB, expr="soft"),
    S("S08k", "S08", "ins", "ecu", "s96", "EL", [TB_], "P_BAG", "Insert: the boy's small hands slowly taking the two plastic bags with both hands across the counter, no face.",
      line="L22", vo=True, motion="The small hands close around the bag handles and hold on tight."),
    S("S08l", "S08", "ins", "ecu", "kit96", "HA", [SU], "P_BAG", "Insert: a woman's hands slipping a small plain thermos container into the plastic bag, no face.",
      motion="The hands slip the thermos into the bag gently."),
    S("S08m", "S08", "d", "ots", "s96", "EL", [SU, TB_], "S96O", "Over the boy's blurred shoulder: Sumie crouching in front of him at eye level, gentle.", line="L22a",
      act="Sumie crouches to the boy's eye level and tells him gently with a warm smile that the porridge is for his mother, she can eat it at the hospital." + OB, expr="smile"),
    S("S08n", "S08", "face", "cu", "s96", "HA", [TB_], "S96O", "Close-up of the boy biting his lips and nodding.", line="L22b", vo=True,
      motion="He bites his lips and nods once." + WET_HOLD + NS + HOLD, expr="tears"),
    S("S08o", "S08", "face", "ws", "street_n", "EL", [TB_, MI], "FRONT", "Wide from behind, winter night: the boy and his little sister walking away holding two bags, their breath white.",
      line="NA17", motion="They walk away slowly along the street; their breath fogs." + HOLD),

    # S09 이별 — 世界一です
    S("S09a", "S09", "empty", "ws", "spring_n", "LA", [], "FRONT", "Wide, spring night: a cherry tree beside the shop front under a streetlight, petals falling.",
      motion="Petals fall slowly; nothing else moves; no cars, no headlights."),
    S("S09b", "S09", "d", "ots", "s96", "HA", [TB_, H96], "S96O", "Over Shuzo's blurred shoulder: the boy at the counter holding a neat stack of folded plastic bags, sad.", line="L23",
      act="The boy sets the folded bags on the counter and tells him they are moving to his mother's hometown, today is the last time, sad." + OB, expr="shy"),
    S("S09c", "S09", "ins", "ecu", "s96", "HA", [H96], "P_KARA", "Insert: a man's hands stopping on the lid of a karaage bento, no face.",
      line="L24", vo=True, motion="The hands stop on the lid and stay still."),
    S("S09d", "S09", "ins", "ecu", "s96", "EL", [H96], "P_KARA", "Insert: tongs adding one more karaage and then another onto a bento already full, the clear lid unable to close.",
      motion="The tongs add one karaage, then another; the lid lifts."),
    S("S09e", "S09", "d", "ots", "s96", "EL", [SU, H96], "S96C", "Over Shuzo's blurred shoulder: Sumie coming out of the kitchen laughing, wiping the corner of her eye.", line="L25",
      act="Sumie laughs, wiping the corner of one eye, scolding him that he put in too much again and the lid won't close." + WET_SMILE + OB, expr="teary"),
    S("S09f", "S09", "face", "ms", "s96", "EL", [TB_], "S96W", "Medium: the boy holding the bag, stepping back from the counter and bowing deeply.",
      motion="He steps back and bows deeply, holding the bag." + HOLD, expr="shy"),
    S("S09g", "S09", "d", "ots", "s96", "HA", [TB_, H96], "S96O", "Over Shuzo's blurred shoulder: the boy raising his head, wet eyes, smiling.", line="L26",
      act="The boy raises his head and tells him, with wet eyes and a smile, that his bento is the best in the world." + WET_HOLD + OB, expr="smile"),
    S("S09h", "S09", "ins", "ecu", "s96", "EL", [MI], "P_BIRD", "Insert: a little girl's small hand placing a small origami robin folded from red paper onto the wooden counter, no face.",
      line="L26a", vo=True, motion="The small hand sets the paper bird on the counter and withdraws."),
    S("S09i", "S09", "d", "ots", "s96", "LA", [H96, TB_], "S96C", "Over the boy's blurred shoulder: Shuzo holding the small red paper bird in his palm, choked up.", line="L26b",
      act="Shuzo holds the paper bird in his palm and thanks her shortly, his voice catching." + WET_HOLD + OB, expr="choke"),
    S("S09j", "S09", "face", "cu", "s96", "HA", [TB_], "S96O", "Close-up of the boy listening, gripping the bag.", line="L26c", vo=True,
      motion="He grips the bag tighter, eyes wet." + WET_HOLD + NS + HOLD, expr="tears"),
    S("S09k", "S09", "d", "ots", "s96", "HA", [TB_, H96], "S96O", "Over Shuzo's blurred shoulder: the boy gripping the bag, smiling through held-back tears.", line="L26d",
      act="The boy grips the bag and, holding back tears with a smile, asks him to keep the shop going forever." + WET_HOLD + OB, expr="smile"),
    S("S09l", "S09", "face", "ms", "s96", "EL", [TB_, MI], "S96R", "Medium from behind: the boy and his sister walking out through the glass door into the spring night, the bell swaying.",
      line="L26e", vo=True, motion="They walk out the door away from the camera; the bell sways." + HOLD),
    S("S09m", "S09", "face", "ms", "s96", "SIDE", [H96], "S96R", "Medium from behind: Shuzo standing still behind the counter, looking at the closed door for a long time.",
      motion="He stands still looking at the door, a slow breath." + HOLD, expr="back"),
    S("S09n", "S09", "d", "ots", "s96", "EL", [SU, H96], "S96R", "Over Shuzo's blurred shoulder: Sumie beside him looking at the door too, soft.", line="L26f",
      act="Sumie says softly that it will feel lonely now, looking at the door beside him." + OB, expr="worry"),
    S("S09o", "S09", "face", "cu", "s96", "EL", [SU], "S96R", "Close-up of Sumie looking at her husband's profile as he answers, a knowing smile beginning.", line="L26g", vo=True,
      motion="A knowing smile begins, lips together." + HOLD, expr="smile"),
    S("S09p", "S09", "d", "ots", "s96", "EL", [SU, H96], "S96R", "Over Shuzo's blurred shoulder: Sumie laughing softly, wiping her eye.", line="L26h",
      act="Sumie laughs softly at him, wiping her eye, saying he is always lying." + WET_SMILE + OB, expr="teary"),
    S("S09q", "S09", "empty", "ws", "spring_n", "LA", [], "FRONT", "Wide: the shop front at night, the glass door closed, petals drifting past the warm light.",
      line="NA18", motion="Petals drift past; the building stays perfectly still; no cars."),

    # S10 30년 몽타주
    S("S10a", "S10", "empty", "ews", "street_n", "HA", [], None, "Extreme wide at night: a small station square years later, the cool bright glow of convenience stores in the distance, no readable signs, no people.",
      line="NA19", motion="Lights shimmer faintly; nothing else moves; no cars."),
    S("S10b", "S10", "ins", "ecu", "kit96", "EL", [SU], "KIT", "Insert: a woman's hands tying a plain white apron string behind her back, no face.",
      line="NA19a", motion="The hands tie the apron string slowly."),

    # S10b 병실
    S("S10ba", "S10b", "face", "ws", "hosp", "EL", [SU50, H60], "HOSP", "Wide: a quiet hospital room, Sumie propped up in bed by the window, Shuzo in his sixties on a chair beside her peeling an apple.",
      motion="He peels the apple slowly; she watches the window." + HOLD),
    S("S10bb", "S10b", "d", "ots", "hosp", "EL", [SU50, H60], "HOSP", "Over Shuzo's blurred shoulder: Sumie in the hospital bed turning from the window to him, a weak smile.", line="L26i",
      act="Sumie, weak but gentle, tired eyes glistening, wonders aloud whether the boy is doing well, turning from the window to her husband." + OB, expr="smile"),
    S("S10bc", "S10b", "d", "ots", "hosp", "EL", [H60, SU50], "HOSP", "Over Sumie's blurred shoulder: Shuzo stopping the knife on the apple.", line="L26j",
      act="Shuzo stops peeling and answers her shortly that surely he is." + OB, expr="calm"),
    S("S10bd", "S10b", "face", "cu", "hosp", "EL", [H60], "HOSP", "Close-up of Shuzo listening to his wife, eyes glistening, the apple still in his hands.", line="L26k", vo=True,
      motion="His eyes glisten, he swallows." + WET_HOLD + NS + HOLD, expr="calm"),
    S("S10be", "S10b", "ins", "ecu", "hosp", "HA", [H60], None, "Insert: a half-peeled apple and a small knife resting still in an old man's hands, no face.",
      line="NA20", motion="The hands stay still; a faint tremble."),
    S("S10bf", "S10b", "face", "ms", "s26", "EL", [H26], "S26W", "Medium, years later: old Shuzo alone switching on the shop's showcase light at night.",
      line="NA21", motion="He reaches and switches on the light; the showcase glows." + HOLD, expr="calm"),
    S("S10bg", "S10b", "empty", "ecu", "s26", "EL", [], "NAIL", "Insert: a plain pale-pink triangle headscarf hanging from a nail on the quiet kitchen wall.", line="NA21a",
      motion="Soft light shifts very slowly across the wall; the headscarf stays still; nothing else moves."),

    # S11 봉투
    S("S11a", "S11", "empty", "ws", "morning", "LA", [], "MAIL", "Wide, early morning: the old metal mailbox beside the shop door, flyers sticking out, one plain white envelope among them.",
      line="NA22", motion="Soft morning light shifts slightly; nothing else moves."),
    S("S11b", "S11", "ins", "ecu", "morning", "EL", [H26], "MAIL", "Insert: an old hand pulling a plain white envelope out from between the flyers, the front blank for a composited handwritten address.",
      line="NA23", motion="The hand slides the envelope out slowly."),
    S("S11c", "S11", "ins", "ecu", "morning", "HA", [H26], "P_LET", "Insert: the old hand turning the envelope over, the sender area covered by the thumb.",
      line="NA24", motion="The hand turns the envelope over and stops still."),

    # S12 편지 — 반전 ②
    S("S12q", "S12", "card", "ecu", "letter", "EL", [], None, "Question card over a blurred still of the old hands holding the envelope (composited)."),
    S("S12a", "S12", "estill", "ecu", "letter", "HA", [], "P_LET", "Insert: the back of the plain white envelope on the counter under a warm lamp, blank for a composited handwritten sender name.", line="L27", vo=True),
    S("S12b", "S12", "face", "cu", "letter", "EL", [H26], "S26O", "Close-up of old Shuzo realizing who sent the letter, eyes widening, frozen.", line="L27a", vo=True, fx="dollyzoom",
      motion="His eyes widen slowly, he stops breathing for a moment." + HOLD, expr="calm"),
    S("S12c", "S12", "reuse:S02c", "ecu", "s96", "HA", [], None, "Flashback reuse of S02c (the boy counting five coins).", line="L28", vo=True),
    S("S12d", "S12", "face", "ms", "letter", "HA", [H26], "S26O", "Medium, slightly high: old Shuzo reading the letter at the counter under the warm lamp, the shutter half down behind him.",
      line="L29", vo=True, motion="He reads, his hands trembling slightly." + HOLD, expr="calm"),
    S("S12e", "S12", "reuse:S05b", "ecu", "s96", "HA", [], None, "Flashback reuse of S05b (coins into the register).", line="L30", vo=True),
    S("S12f", "S12", "face", "cu", "s96", "EL", [TB_], "S96X", "Flashback 1996: the boy outside the shop at night, seen through the glass door, watching something inside, eyes wet.",
      line="L30a", vo=True, motion="He watches through the glass, eyes wet, breath fogging the glass faintly." + WET_HOLD + NS + HOLD, expr="tears"),
    S("S12g", "S12", "face", "cu", "letter", "EL", [H26], "S26O", "Close-up of old Shuzo, the letter trembling in his hands, tears welling.", line="L31", vo=True,
      motion="He reads." + TEARS_FLOW + HOLD, expr="grief"),
    S("S12h", "S12", "reuse:S08l", "ecu", "kit96", "HA", [], None, "Flashback reuse of S08l (the thermos into the bag).", line="L31a", vo=True),
    S("S12i", "S12", "ins", "ecu", "letter", "HA", [H26], "P_LET", "Insert: the letter paper held in trembling old hands, one drop falling onto the paper, blank paper.",
      line="L31b", vo=True, motion="A single clear drop falls onto the paper; the hands tremble."),
    S("S12j", "S12", "face", "ms", "letter", "SIDE", [H26], "S26W", "Medium side view: old Shuzo alone at the counter in the dim shop, the letter in his hands, head bowed.",
      line="L31c", vo=True, motion="His head bows lower, shoulders shaking slightly." + HOLD, expr="grief"),
    S("S12k", "S12", "face", "cu", "letter", "EL", [H26], "S26O", "Close-up of old Shuzo crying silently, NOT smiling, one thin tear on his cheek.",
      line="NA25", motion="He cries silently, a trembling breath." + TEARS_FLOW + HOLD, expr="grief"),
    S("S12l", "S12", "face", "ws", "letter", "SIDE", [H26], "S26R", "Wide from behind the counter: old Shuzo's back as he sits with the letter, his shoulders shaking, his face not visible.",
      line="L31d", vo=True, motion="His shoulders shake as if laughing and crying at once; his head stays turned away." + HOLD, expr="back"),
    S("S12m", "S12", "face", "ws", "street_n", "EL", [TA_], "FRONT", "Wide, night a few years ago: a man in a charcoal overcoat seen from behind across the street, looking at the lit bento shop, face not visible.",
      line="L32a", vo=True, motion="He stands looking at the shop, then lowers his head." + HOLD, expr="back"),
    S("S12n", "S12", "face", "ms", "street_n", "SIDE", [TA_], "FRONT", "Medium from behind: the man in the charcoal overcoat turning away from the shop and walking off, face not visible.",
      line="L32b", vo=True, motion="He turns slowly and walks away from the camera." + HOLD, expr="back"),
    S("S12o", "S12", "estill", "ecu", "letter", "HA", [], "P_LET", "Insert: a small photograph lying on the counter beside the letter, its image area blank for a composited photo of a children's cafeteria.", line="L32", vo=True),
    S("S12p", "S12", "ins", "ecu", "letter", "EL", [H26], "S26K", "Insert: an old hand setting the photograph down next to the faded round red sticker on the worn counter.",
      line="L33", vo=True, motion="The hand sets the photo down beside the sticker and rests there."),
    S("S12r", "S12", "face", "cu", "letter", "HA", [H26], "S26O", "Close-up, slightly high: old Shuzo looking at the last line of the letter, eyes wet, still.",
      line="NA26", motion="He looks at the letter, a slow blink." + WET_HOLD + NS + HOLD, expr="grief"),
    S("S12s", "S12", "face", "cu", "letter", "EL", [H26], "S26O", "Close-up: old Shuzo raising his eyes from the letter toward the glass door, resolved.", line="L34", vo=True,
      motion="He raises his eyes slowly toward the door." + WET_HOLD + NS + HOLD, expr="grief"),
    S("S12t", "S12", "estill", "ecu", "letter", "EL", [], "P_BIRD", "Insert: the faded red origami robin on the shelf corner, lit by the warm lamp."),

    # S13 재회 — 半額の弁当、まだありますか
    S("S13a", "S13", "ins", "ecu", "s26warm", "EL", [H26], "P_KARA", "Insert: old hands holding a red round blank sticker, hesitating, then pressing it onto a fresh karaage bento lid.",
      motion="The hands hesitate a moment, then press the sticker onto the lid."),
    S("S13b", "S13", "estill", "ecu", "s26warm", "LA", [], None, "Insert: the plain round wall clock with a BLANK face, both hands pointing straight up."),
    S("S13c", "S13", "face", "ms", "s26warm", "EL", [TA_, HI], "S26R", "Over old Shuzo's blurred shoulder (left foreground): the man in the charcoal overcoat standing in the doorway holding a little girl's hand, the bell swaying.",
      motion="They stand in the doorway; the bell sways; the man's eyes are wet." + WET_HOLD + HOLD, expr="calm"),
    S("S13d", "S13", "d", "ots", "s26warm", "EL", [TA_, H26], "S26R", "Over old Shuzo's blurred shoulder: Takumi in the doorway at three-quarter angle, wet eyes, smiling, looking straight at him.", line="L35",
      act="Takumi, standing in the doorway, smiling with wet eyes, asks whether there is still a half-price bento, looking straight at the old man." + WET_SMILE + OB, expr="calm"),
    S("S13e", "S13", "face", "cu", "s26warm", "EL", [H26], "S26O", "Close-up of old Shuzo, lips trembling, swallowing once.",
      motion="His lips tremble; he swallows once." + WET_HOLD + NS + HOLD, expr="grief"),
    S("S13f", "S13", "d", "ots", "s26warm", "EL", [H26, TA_], "S26O", "Over Takumi's blurred shoulder: old Shuzo with one hand resting on the last bento on the showcase, choked up.", line="L36",
      act="Shuzo rests his hand on the last bento and answers, choked up and short, only if it is a leftover." + WET_HOLD + NS + OB, expr="grief"),
    S("S13g", "S13", "face", "ms", "s26warm", "SIDE", [TA_, H26], "S26W", "Medium side two-shot across the counter: Takumi and old Shuzo breathing out a laugh mixed with tears, not speaking.",
      line="L37", vo=True, motion="Both let out a breath, half laugh and half tears; they look at each other." + HOLD),
    S("S13h", "S13", "face", "cu", "s26warm", "EL", [TA_], "S26O", "Close-up of Takumi looking past the old man toward the kitchen on screen right, at something on the wall.",
      motion="His gaze settles on the kitchen wall on the right; his eyes soften." + HOLD, expr="calm"),
    S("S13i", "S13", "d", "ots", "s26warm", "EL", [TA_, H26], "S26R", "Over old Shuzo's blurred shoulder: Takumi turning from the kitchen wall back to him, careful.", line="L37a",
      act="Takumi turns from the headscarf on the wall to the old man and says carefully that he wanted to thank his wife too." + OB, expr="calm"),
    S("S13j", "S13", "d", "ots", "s26warm", "EL", [H26, TA_], "S26O", "Over Takumi's blurred shoulder: old Shuzo glancing toward the headscarf then back to him, a small smile.", line="L37b",
      act="Shuzo glances toward the headscarf and back, telling him with a small smile that Sumie wanted to see him too." + WET_SMILE + OB, expr="calm"),
    S("S13k", "S13", "ins", "ecu", "s26warm", "EL", [TA_], "S26K", "Insert: a man's hand placing a thick plain white envelope on the worn wooden counter, no face.",
      motion="The hand lays the envelope flat on the counter and withdraws."),
    S("S13l", "S13", "d", "ots", "s26warm", "EL", [TA_, H26], "S26R", "Over old Shuzo's blurred shoulder: Takumi pushing the envelope forward with both hands, bowing his head.", line="L38",
      act="Takumi pushes the envelope forward with both hands and bows his head, asking earnestly that he accept thirty years' worth of bento money." + OB, expr="calm"),
    S("S13m", "S13", "ins", "ecu", "s26warm", "EL", [H26], "S26K", "Insert: old hands pushing the envelope back across the counter and picking up the small photograph instead.",
      motion="The hands slide the envelope back, then pick up the photograph."),
    S("S13n", "S13", "d", "ots", "s26warm", "EL", [H26, TA_], "S26O", "Over Takumi's blurred shoulder: old Shuzo holding up the photograph, wet eyes.", line="L39",
      act="Shuzo holds up the photograph and tells him, voice breaking, that the debt is already paid, this is enough." + WET_SMILE + OB, expr="calm"),
    S("S13o", "S13", "ins", "ecu", "s26warm", "HA", [H26], "P_BAG", "Insert: old hands putting a bento into a small plastic bag and adding one more piece of karaage.",
      motion="The hands add one more karaage and place the bento in the bag."),
    S("S13p", "S13", "d", "ots", "s26warm", "HA", [H26, HI], "S26O", "Over the little girl's blurred head: old Shuzo leaning down to her, holding out the bag, gruff but kind.", line="L40",
      act="Shuzo leans down to the little girl and tells her gruffly but kindly the karaage was left over, holding out the bag." + OB, expr="calm"),
    S("S13q", "S13", "face", "ms", "s26warm", "EL", [TA_, H26], "S26W", "Medium: Takumi bowing his head and crying, old Shuzo reaching across the counter to rest a hand on his shoulder.",
      motion="Takumi's shoulders shake; the old hand rests on his shoulder." + HOLD, expr="cry"),
    S("S13r", "S13", "d", "ots", "s26warm", "EL", [TA_, H26], "S26R", "Over old Shuzo's blurred shoulder: Takumi wiping his eyes, glancing toward the half-lowered shutter.", line="L41",
      act="Takumi wipes his wet eyes and asks softly whether he is really closing the shop." + OB, expr="calm"),
    S("S13s", "S13", "d", "ots", "s26warm", "EL", [H26, TA_], "S26O", "Over Takumi's blurred shoulder: old Shuzo looking back at the empty kitchen, calm.", line="L42",
      act="Shuzo looks back at the empty kitchen and answers calmly, yes, alone it's too much now." + OB, expr="calm"),
    S("S13t", "S13", "d", "ots", "s26warm", "EL", [TA_, H26], "S26R", "Over old Shuzo's blurred shoulder: Takumi leaning on the counter with both hands, earnest.", line="L43",
      act="Takumi leans on the counter with both hands and asks earnestly whether he would fry karaage at his place, the best karaage in the world, for the children." + OB, expr="calm"),
    S("S13u", "S13", "d", "ots", "s26warm", "EL", [H26, TA_], "S26O", "Over Takumi's blurred shoulder: old Shuzo staring for a moment, then a wry snort of a laugh.", line="L44",
      act="Shuzo stares for a moment, then asks with a wry snort whether the salary will be paid when he makes it." + WET_SMILE + OB, expr="calm"),

    # S14 에필로그
    S("S14a", "S14", "empty", "ws", "street_n", "LA", [], "SHUT", "Wide: the bento shop at night with its metal shutter pulled all the way down, warm light gone, wet asphalt.",
      line="NA27", motion="The building stays perfectly still; a faint breeze; no cars, no headlights."),
    S("S14b", "S14", "face", "ws", "shokudo", "HA", [H26 + "A", TA_ + "A", "KIDS"], "SHOKW", "Wide, daytime: a small children's cafeteria, old Shuzo in an apron serving karaage at the counter and Takumi beside him scooping rice, children's backs in the foreground out of focus.",
      line="NA28", motion="They serve food with small smiles; the children's backs move slightly." + HOLD),
    S("S14c", "S14", "face", "ms", "shokudo", "EL", [MI36], "SHOKC", "Medium: grown-up Mio in a plain apron at the end of the serving counter, handing out trays with a warm smile.",
      line="NA28a", motion="She hands a tray forward with a warm smile." + HOLD, expr="smile"),
    S("S14d", "S14", "ins", "ecu", "shokudo", "EL", [H26], "P_BIRD", "Insert: an old hand placing the faded red origami robin onto a little girl's small open palm, no faces.",
      line="NA29", motion="The old hand sets the paper bird into the small palm."),
    S("S14e", "S14", "face", "cu", "shokudo", "EL", [H26 + "A"], "SHOKC", "Close-up of old Shuzo smiling warmly at the children, eyes wet, a small closed-mouth smile.",
      line="NA30", motion="He watches the children with a warm small smile, a slow blink." + HOLD, expr="calm"),
    S("S15a", "S15", "estill", "ecu", "shokudo", "EL", [], "P_FRAME", "Insert: a small plain wooden frame on the cafeteria wall holding one faded round red sticker, warm daylight."),
]

CARDS = {"H2": "毎晩ひとつだけ弁当を買った少年は、誰だったのか", "H3": TITLE, "S12q": "三十年後の手紙に、書かれていたのは――",
         "S01a": "令和八年　秋", "S02a": "三十年前　平成八年"}
JA_OVERLAY = {"H1": "편지 세로쓰기 한 줄(실글꼴)", "H2": "중앙 질문 카드", "H3": "타이틀 + 간판 「こまどり弁当」", "S01a": "유리문 안내문 「閉店のお知らせ…」 + 구석 소자막",
              "S01c": "빛바랜 스티커 「半額」", "S01d": "스티커 「半額」", "S02a": "스티커 「半額」 + 시점 소자막", "S05a": "가격표 「唐揚げ弁当　五百円」 + 「半額」",
              "S07f": "스티커 「半額」", "S11b": "봉투 앞 「こまどり弁当　野口修三様」", "S12q": "중앙 질문 카드", "S12a": "봉투 뒤 「朝倉拓海」",
              "S12o": "사진 속 식당 간판 「子ども食堂こまどり」", "S12p": "빛바랜 스티커 「半額」", "S13a": "스티커 「半額」", "S15a": "액자 속 「半額」"}
G = {
    "shop": "a refrigerated showcase humming softly, a wall clock ticking, a quiet small shop at night", "rain": "steady rain outside a glass door, drips on a shop awning",
    "kitchen": "rice being washed in a bowl, water running, a pot lid clinking, a small kitchen at night", "alley": "a vending machine humming, distant crickets, a quiet back alley at night",
    "street": "a quiet street at night, a distant train passing, light wind", "spring": "a soft spring night breeze, leaves rustling, distant crickets",
    "hosp": "a quiet hospital room, an air conditioner hum, distant birds outside", "morning": "early morning birdsong, a quiet street, a distant train",
    "letter": "a quiet shop at night, a wall clock ticking, paper rustling", "shokudo": "a cheerful cafeteria kitchen, frying oil sizzling, dishes clinking, no voices",
}
AMB_BY_SCENE = {"S01": "shop", "S02": "shop", "S03": "kitchen", "S03b": "alley", "S04": "rain", "S05": "shop", "S06": "shop", "S07": "street",
                "S08": "shop", "S09": "spring", "S10": "street", "S10b": "hosp", "S11": "morning", "S12": "letter", "S13": "letter", "S14": "shokudo", "S15": "shokudo"}
AMB_BY_SHOT = {"H0": "letter", "H1": "letter", "H2": "letter", "H3": "street", "S03bf": "kitchen", "S03bg": "kitchen", "S04j": "rain", "S05d": "kitchen",
               "S07d": "shop", "S07e": "shop", "S07f": "shop", "S08o": "street", "S10b": "kitchen", "S10bf": "shop", "S10bg": "kitchen",
               "S12c": "shop", "S12e": "shop", "S12f": "street", "S12h": "kitchen", "S12m": "street", "S12n": "street", "S14a": "street"}
BGM = []  # main()에서 lock.json 장면 시각으로 계산(03_템포-오디오가이드.md 2절)

STYLE = {"NA": "Narration", "修三": "Shuzo", "澄江": "Sumie", "拓海(少年)": "TakumiBoy", "拓海(大人)": "Takumi", "美緒": "Mio", "陽菜": "Hina"}
STYLE_JA = {"Narration": "ナレーター", "Shuzo": "修三", "Sumie": "澄江", "TakumiBoy": "拓海", "Takumi": "拓海", "Mio": "美緒", "Hina": "陽菜"}
STYLE_COLOR = {"Narration": "&H00DDDDDD", "Shuzo": "&H00FFFFFF", "Sumie": "&H00D2E6FF", "TakumiBoy": "&H00F0E6C8", "Takumi": "&H00F0E6C8",
               "Mio": "&H00C8F0F0", "Hina": "&H00C8F0F0"}
RATE = {"lite": 0.036, "omni": 0.16, "kf": 0.04}
HOOK_LEN = {"H0": 4.0, "H1": 5.0, "H2": 6.0, "H3": 5.0}


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
        if s["kind"] == "d" and s["line"] and not s["act"]:
            errs.append(f"{s['id']}: 립싱크 컷에 연기 지시(act) 없음")
        if prev and prev["scene"] == s["scene"] and not s["kind"].startswith("reuse") and not prev["kind"].startswith("reuse"):
            if prev["lens"] == s["lens"] and prev["angle"] == s["angle"] and prev["loc"] == s["loc"] and prev["who"] == s["who"]:
                errs.append(f"{prev['id']}→{s['id']}: 연속 같은 구도(A1)")
        if s["line"]:
            spk = rows[s["line"]]["spk"]
            on = [w.split(":")[0] for w in s["who"]]
            if spk in SPK_KEYS and not set(SPK_KEYS[spk]) & set(on) and not s["vo"]:
                errs.append(f"{s['id']}: {s['line']} 화자 {spk}가 화면에 없음(화자-화면 일치) — 의도면 vo=True")
            if spk in SPK_KEYS and s["kind"] == "d" and on[0] not in SPK_KEYS[spk]:
                errs.append(f"{s['id']}: 립싱크 대상(who[0]={on[0]})이 화자 {spk}와 다름")
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


def build_bgm(lock):
    """03_템포-오디오가이드.md 2절 감정 곡선 — 장면 경계에 맞춰 8구간, 구간 간격 1.0초 이상(제11장 5)."""
    sc = {s["id"]: s["start"] for s in lock["scenes"]}; ad1, ad2 = (a["at"] for a in lock["ads"]); end = lock["body_end"]
    segs = [
        (3.5, 19.0, 0.34, "a single soft solo piano motif, intimate, tender, a letter being read, Japanese human drama, instrumental, no vocals"),
        (20.0, sc["S02"] - 0.6, 0.36, "cool lonely solo piano, an old man alone in a closing shop at night, quiet melancholy, instrumental, no vocals"),
        (sc["S02"] + 0.5, sc["S06"] - 0.6, 0.38, "warm nostalgic acoustic guitar and soft piano, a small kind shop in the 1990s, gentle strings rising softly, Japanese human drama, instrumental, no vocals"),
        (sc["S06"] + 0.5, ad1 - 0.6, 0.34, "a single low sustained cello note with a ticking clock feel, worry, quiet, instrumental, no vocals"),
        (ad1 + 1.0, sc["S09"] - 0.6, 0.38, "melancholic solo piano in the rain turning into warm hopeful strings, kindness to a poor child, Japanese drama, instrumental, no vocals"),
        (sc["S09"] + 0.5, sc["S11"] - 0.6, 0.38, "bittersweet farewell theme with celesta and strings, spring night, then sparse sad piano, loss, instrumental, no vocals"),
        (sc["S11"] + 0.5, ad2 - 0.6, 0.34, "soft mysterious pulse with light piano, morning, an unexpected letter, suspense, instrumental, no vocals"),
        (ad2 + 1.0, sc["S13"] - 0.6, 0.40, "the letter theme: tender piano slowly joined by building strings, a long-held secret revealed, deeply moving, Japanese human drama, instrumental, no vocals"),
        (sc["S13"] + 3.0, None, 0.42, "the main theme on piano blooming into a full warm orchestra, a tearful reunion after thirty years, gratitude, hopeful resolution, instrumental, no vocals"),
    ]
    for a, b in zip(segs, segs[1:]):
        assert b[0] - a[1] >= 1.0, f"BGM 구간 간격 {b[0] - a[1]:.1f}s < 1.0s"
    return segs


def main():
    global BGM
    lock = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
    BGM = build_bgm(lock)
    rows = {x["tag"]: x for x in lock["lines"]}
    texts = script_texts()
    scenes = {s["id"]: (s["start"], s["end"]) for s in lock["scenes"]}
    main_end = lock["body_end"]
    for s in SHOTS:
        sp = spk_who(rows[s["line"]]["spk"], s) if s.get("vo") and s["line"] in rows else None
        s["ots"] = bool(sp and s["id"] not in VO_OTS_SKIP and s["kind"] == "face" and len(s["who"]) == 1 and sp.split(":")[0] != s["who"][0].split(":")[0])
        if s["ots"]:
            s["who"] = s["who"] + [sp]
    errs = check_rules(SHOTS, rows)
    body_tags = {t for t, x in rows.items() if x["scene"].startswith("S") and x.get("start") is not None}
    used = [s["line"] for s in SHOTS if s["line"] and s["scene"] != "H"]  # 후크 줄(L01·NA0)은 HOOK_AT 고정 시각
    if sorted(used) != sorted(body_tags):
        errs.append(f"대사 줄 사용 불일치: 빠짐 {sorted(body_tags - set(used))}, 중복·초과 {sorted(set(u for u in used if used.count(u) > 1) | (set(used) - body_tags))}")
    for s in SHOTS:  # 참조 셀 존재 검사(PHASE 2 셀 분할 후)
        for w in s["who"]:
            key = w.split(":")[0]
            if s["expr"] and (key, s["expr"]) in EXPR and not os.path.exists(os.path.join(ROOT, EXPR[(key, s["expr"])])):
                errs.append(f"{s['id']}: 셀 없음 {EXPR[(key, s['expr'])]}")
        if s["loc"] and not os.path.exists(os.path.join(ROOT, LOC[s["loc"]])):
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
        keys = sorted(pins)
        for k1, k2 in zip(keys, keys[1:]):
            t1, t2 = pins[k1], pins[k2]; n = k2 - k1
            for j in range(k1, k2):
                starts[shots[j]["id"]] = t1 + (t2 - t1) * (j - k1) / n
    order_ids = [s["id"] for s in SHOTS]
    ends = {sid: (starts[order_ids[k + 1]] if k + 1 < len(order_ids) else main_end) for k, sid in enumerate(order_ids)}
    for k, s in enumerate(SHOTS):
        if s["kind"] == "d" and ends[s["id"]] - starts[s["id"]] > OMNI_MAX:
            nxt = order_ids[k + 1]; starts[nxt] = starts[s["id"]] + OMNI_MAX; ends[s["id"]] = starts[nxt]
    problems = []
    for s in SHOTS:
        d = ends[s["id"]] - starts[s["id"]]
        if d < MIN_SHOT:
            problems.append(f"{s['id']} {d:.2f}s < {MIN_SHOT}")
        still = s["kind"] in ("estill",) or (s["kind"] == "ins" and not s["motion"])
        if still and d > STILL_MAX:
            problems.append(f"{s['id']} 정지 {d:.2f}s > {STILL_MAX}")
        if s["kind"] in ("face", "empty") and d > I2V_MAX:
            problems.append(f"{s['id']} i2v {d:.2f}s > {I2V_MAX}")
    if problems:
        raise SystemExit("컷 길이 위반:\n  " + "\n  ".join(problems))

    durations, sb, scene_items, omni_prompts, live = [], [], [], {}, {}
    cost = collections.Counter()
    for s in SHOTS:
        sid = s["id"]; d = ends[sid] - starts[sid]
        durations.append(round(d + HARD, 4))
        refs, ids = [], []
        for w in s["who"]:
            key, _, ward = w.partition(":")
            desc, cell = WHO[key]
            ids.append(desc + (f", wearing {WARD[ward]}" if ward else ""))
            if s["expr"] and (key, s["expr"]) in EXPR:
                refs.append(EXPR[(key, s["expr"])])
            elif cell:
                refs.append(cell)
        if s["loc"]:
            refs.append(LOC[s["loc"]])
        n = len(s["who"])
        if s["kind"] == "d":
            comp = ("Over-the-shoulder two-shot: the listener's blurred shoulder and back of the head at the near foreground edge, the speaker beyond "
                    "facing the listener at 30 to 40 degrees from the camera axis, the speaker's face at least one third of the frame height, "
                    "the speaker's mouth closed, hands visible doing the described work. Exactly two people, no extra people.")
        elif s.get("ots"):
            comp = ("Over-the-shoulder reverse shot: the SPEAKER's blurred back of the head and shoulder at the near foreground edge (face and mouth "
                    "NOT visible); the LISTENER beyond faces the speaker at 30 to 40 degrees from the camera axis, eyes on the speaker, NOT looking "
                    "at the camera, the listener's face at least one third of the frame height, mouth closed. Exactly two people, no extra people.")
        elif s["kind"] in ("empty", "estill") or (s["kind"] == "ins" and not s["who"]):
            comp = "Completely unpopulated: no people, no hands, no faces."
        else:
            comp = f"Exactly {n} {'person' if n == 1 else 'people'} (or their hands) as described, no extra people."
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/{SKIT}-keyframes/{sid}-1.png"
        kf_prompt = None
        if keyframe:
            low = (s["subject"] + " " + (s["act"] or "")).lower()
            real = " ".join(x for x, keys in ((TEARS, ("tear", "sob", "cry", "wet")), (SWEAT, ("sweat",))) if any(k in low for k in keys)
                            or (s["expr"] in ("tears",) and x == TEARS) or (s["expr"] in ("fear",) and x == SWEAT))
            glasses = " ".join(GLASSES[w.split(":")[0]] for w in s["who"] if w.split(":")[0] in GLASSES)
            kf_prompt = " ".join([PRESET + ".", s["subject"], ("Characters: " + " | ".join(ids) + ".") if ids else "", glasses, real,
                                  f"Camera: {ANGLE[s['angle']]}, {LENS[s['lens']]}.", f"Lighting: {LIGHT[s['light']]}.", comp, PLAIN,
                                  f"Negative: {NEGATIVE}."]).strip()
            cost["kf"] += 1
        tier = {"d": "omni", "face": "lite", "empty": "lite", "estill": "still", "card": "card"}.get(s["kind"], "reuse")
        if s["kind"] == "ins":
            tier = "lite" if s["motion"] else "still"
        if s["kind"] == "d" and not s["line"]:  # 대사 없는 어깨 너머 리액션(vo 상대) → i2v
            tier = "lite"
        gen = 10 if d > 5.0 else 5
        item = {"prompt": "", "duration": gen}
        if tier == "lite":
            item["prompt"] = ("Static, locked off camera. Motion: " + (s["motion"] or "Subtle natural motion only: breathing, one blink.") +
                              " Keep the exact faces, wardrobe, props and lighting of the first frame. Head turns under 20 degrees. "
                              "No walking toward the camera, no new people, no text.")
            item["image"] = keyframe; cost["lite"] += gen; live[sid] = s["motion"]
        else:
            item["prompt"] = f"(override) {tier}: {s['subject'][:80]}"; item["override_required"] = True
            if keyframe:
                item["image"] = keyframe
        if tier == "omni":
            cost["omni"] += min(d, OMNI_MAX) + 0.8; omni_prompts[sid] = s["act"]
        scene_items.append(item)
        amb = AMB_BY_SHOT.get(sid, AMB_BY_SCENE.get(s["scene"], ""))
        sb.append({"id": sid, "scene": s["scene"], "kind": s["kind"], "tier": tier, "timecode": f"{tc(starts[sid])} - {tc(ends[sid])}",
                   "assembled_s": round(d, 3), "generate_s": gen, "size": s["lens"], "lens": LENS[s["lens"]], "angle": s["angle"],
                   "lighting": s["light"], "edit_fx": s["fx"], "refs": refs, "ots": s.get("ots", False), "subject": s["subject"], "line": s["line"], "vo": s["vo"],
                   "motion": item["prompt"] if tier == "lite" else "", "act": s["act"], "keyframe": keyframe, "keyframe_prompt": kf_prompt,
                   "ja_overlay": JA_OVERLAY.get(sid, ""), "caption": CARDS.get(sid, ""), "ambience": G.get(amb, "")})
    budget = round(cost["lite"] * RATE["lite"] * 1.25, 2)

    tts_order = [dict(x) for x in lock["lines"] if x.get("start") is not None and x["scene"] != "OUT"]
    for rp in lock.get("replay", []):  # S10 콜드오픈 합류 — 후크 L01을 같은 녹음으로 한 번 더
        src = dict(rows[rp["tag"]]); src["start"] = rp["start"]; src["end"] = rp["start"] + src["dur"]; src["tag"] = rp["tag"] + "r"
        tts_order.append(src)
    tts_order.sort(key=lambda x: x["start"])
    dst = os.path.join(ROOT, "assets", "audio-overrides", SKIT); os.makedirs(dst, exist_ok=True)
    mapping = []
    for i, x in enumerate(tts_order, 1):
        shutil.copyfile(os.path.join(ROOT, "assets", "auditions", TTS_DIR, x["audio"] + ".mp3"), os.path.join(dst, f"line{i:03d}.mp3"))
        mapping.append((f"line{i:03d}", x["tag"], x["audio"]))

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
        f"Style: {n}{suf},Noto Sans CJK JP,{70 if n != 'Narration' else 66},{c},&H000000FF,&H00000000,&H80000000,-1,{-1 if n == 'Narration' else 0},0,0,100,100,0,0,1,6,2,2,120,120,90,1"
        for n, c in STYLE_COLOR.items() for suf in ("", "_c"))
    ass = ["[Script Info]", f"Title: {TITLE} 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
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
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_bento_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT, "preset": PRESET,
               "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"], "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_bento_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, wardrobe, "
                         "props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_bento_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (Typecast 확정본).",
        "default_voice": "cached-typecast", "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Narration"], "silent_styles": ["Caption", "HookLine", "Title"] + [n + "_c" for n in STYLE_COLOR],
        "output_size": [1920, 1080], "fit": "crop", "scene_durations": durations, "transitions": [0.0] * len(durations),
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d" and s["line"]],
        "omnihuman_prompts": {str(idx[k]): v for k, v in omni_prompts.items()},
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0, "legacy_lipsync": False,
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35, "duck_db": 8, "ambience_prompts": [x["ambience"] for x in sb],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": s, "end": round(main_end, 2) if e is None else e, "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_후크": "0~3.5초 BGM 없음: 저음 드론 + 종이 펴는 소리를 PHASE 6 로컬 믹스. H1 음성 L01 = 편지 낭독 L29 녹음 재사용(build_tts SAME_AS). 음성은 ElevenLabs·Typecast 확정본(Shino 1.15·Chiemi 1.12 배속 적용본).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    md = [f"# 『{TITLE}』 PHASE 3 샷 리스트 (B안 표준)", "",
          f"> `scripts/build_bento_phase3.py` 자동 생성(손 수정 금지). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " + ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock['ads']) + ".",
          "> 자동 검사 통과: 연속 같은 구도 0 · 같은 화자 립싱크 연속 0(리액션 컷) · 장면당 사이즈 4종 이상 · 돌리줌 1회 · 더치 2회 · OMNI 정면~45° · 화자-화면 일치(vo 제외) · 대사 줄 전부 배치 · 컷 길이 · OMNI 8초 이하.", "",
          "## 비용 추산 (실측 단가)", "", "| 항목 | 수량 | 단가 | 금액 |", "|---|---|---|---|",
          f"| 키프레임 | {cost['kf']}장 | 0.04 | {cost['kf'] * RATE['kf']:.2f} |",
          f"| i2v lite (사람·손·배경 전부) | {cost['lite']}초 | 0.036 | {cost['lite'] * RATE['lite']:.2f} |",
          f"| OmniHuman (8초 상한 + 앞뒤 0.8초) | {cost['omni']:.1f}초 | 0.16 | {cost['omni'] * RATE['omni']:.2f} |",
          f"| **1차 합계** (재생성 여유 제외) | | | **{total_cost:.2f}** |", f"| i2v 예산 상한 `budget_usd` (여유 25%) | | | {budget:.2f} |", "",
          "## 생성 방식 분포", "", "| 방식 | 컷 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in tiers.most_common()] + [
          "", f"## 앵글 분포 — 최다 {top[0]} {top[1] / sum(ang.values()) * 100:.0f}% (60% 이하 기준)", "", "| 앵글 | 컷 |", "|---|---|"] + [
          f"| {k} | {v} |" for k, v in ang.most_common()] + [
          "", "## 화면 속 일본어 (무지 → 합성)", ""] + [f"- {k}: {v}" for k, v in JA_OVERLAY.items()] + [
          "", "## 샷 표", "", "| 컷 | 타임코드 | 길이 | 방식 | 사이즈 | 앵글 | 조명 | 편집 효과 | 대사 | 현장음 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in sb:
        md.append(f"| {x['id']} | {x['timecode']} | {x['assembled_s']:.2f}s | {x['tier']} | {x['size']} | {x['angle']} | {x['lighting']} | {x['edit_fx']} | {(x['line'] or '') + (' (vo)' if x['vo'] else '')} | {x['ambience'][:30]} |")
    md += ["", "## 음성 번호 대응", "", "| 캐시 | 대본 | 원본 녹음 |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in mapping]
    open(os.path.join(PROD, "07_샷리스트.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    emotion_table(sb, live)
    print(f"완료: 컷 {len(SHOTS)}개, 본편 {tc(main_end)}, 방식 {dict(tiers)}, 1차 비용 약 {total_cost:.2f}달러 (i2v budget {budget}), 앵글 {dict(ang)}")



def spk_who(spk, s):
    """VO 컷 어깨 너머 앞 인물 = 화자(시대·나이·옷차림을 그 컷 조명으로 판정)."""
    now = s["light"] in ("s26", "s26warm", "letter", "shokudo", "morning")
    return {"修三": H60 if s["light"] == "hosp" else (H26 if now else H96), "澄江": SU50 if s["light"] == "hosp" else SU,
            "拓海(少年)": TBW if s["light"] == "s96rain" else TB_, "拓海(大人)": TA_, "美緒": MI, "陽菜": HI}.get(spk)


VO_OTS_SKIP = {"S03bb", "S08d", "S08e", "S12b", "S12d", "S12f", "S12g", "S12j", "S12l", "S12m", "S12n", "S12r", "S12s", "S13g", "S04c", "S09l"}
# 편지 낭독 VO(拓海 화면 밖)·화자가 화면 안에서 입을 가린 컷·뒷모습 컷은 어깨 너머 리버스숏을 만들지 않는다

EMO_WORDS = {"sad": ("tear", "cry", "sad", "weak", "chok", "break", "holding back", "trembl", "grief", "apolog", "regret", "sorrow", "wet"),
             "happy": ("smil", "laugh", "teas", "bright", "warm", "happy", "delight", "chuckl", "fond", "proud", "cheer"),
             "tonedown": ("gruff", "curt", "deadpan", "flat", "quiet", "low", "calm", "soft", "steady", "firm", "pretend", "careful", "earnest")}
EMO_OK = {"sad": ("tear", "wet", "cry", "tremb", "chok", "grief", "bow", "bit", "hold back", "glisten", "sad", "lower"),
          "happy": ("smile", "laugh", "teas", "warm", "proud", "shin", "bright", "grin"),
          "tonedown": ("gruff", "curt", "calm", "quiet", "steady", "firm", "eyes on", "avert", "short", "careful", "earnest", "gentle", "soft"),
          "normal": ()}
EMO_BAD = {"sad": ("grin", "laugh brightly"), "happy": ("sob", "grief"), "tonedown": ("shout", "laugh loudly")}


def emo_of(tone):
    if isinstance(tone, tuple):
        return {"sad": "sad", "happy": "happy"}.get(tone[0], "tonedown" if tone[0] == "normal" else "normal")
    t = tone.lower()
    for k in ("sad", "happy", "tonedown"):
        if any(w in t for w in EMO_WORDS[k]):
            return k
    return "normal"


def emotion_table(sb, live):
    import sys
    sys.path.insert(0, PROD)
    from build_tts import T as TONE
    rows, warn = [], 0
    for x in sb:
        tag = x["line"]
        if not tag or tag not in TONE or tag.startswith(("NA", "OUT")):
            continue
        tone, memo = TONE[tag]
        emo = emo_of(tone)
        act = x["act"] or live.get(x["id"]) or ""
        seen = " ".join([x["subject"], act]).lower()
        ok = not EMO_OK.get(emo) or any(k in seen for k in EMO_OK[emo])
        bad = [k for k in EMO_BAD.get(emo, ()) if k in seen]
        state = "👂" if x["vo"] else ("✅" if ok and not bad else "⚠️")
        warn += state == "⚠️"
        how = "립싱크" if x["tier"] == "omni" else ("목소리만(VO)" if x["vo"] else "i2v")
        tone_s = tone if isinstance(tone, str) else f"{tone[0]} {tone[1]} · {tone[2]}"
        rows.append(f"| {state} | {x['id']} | {tag} | {how} | {tone_s} → {emo} | {memo} | {x['subject'][:70]} | {act[:90]} |")
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_bento_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않음(키프레임·동작 문장을 고친다). 👂 = 목소리만(듣는 사람·손 컷), 리액션이 들은 말에 맞는지 키프레임 검수에서 본다.", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 톤 → 감정 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")
    return warn


if __name__ == "__main__":
    main()
