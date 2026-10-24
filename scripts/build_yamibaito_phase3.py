#!/usr/bin/env python3
"""『時給5万円の罠』(yamibaito-ja) PHASE 3 샷 리스트 Lock 생성기 — build_bento_phase3.py를 옮긴 것(내장 규칙 동일 + 제19·20장 보강).

이 작품에서 달라진 것:
  · 再現ドラマ·사스펜스: 얼굴 노출 인물 4명(健太·男·悠斗·店長), 다수 인물은 뒷모습·실루엣(kind face + who=[] = 「crowd」).
  · 健太 의상 3벌 = 셀 시트 3장(KEV 편의점 조끼 / KEH 회색 후드 / KEW 회색 작업복) — 장면별 의상 매핑을 생성기가 검사한다.
  · 외침(L15·L18)은 VO, 2.5초 이하 짧은 대사(L09·L10·L12·L13·L16·L20)는 VO(제12장 2), 립싱크는 가슴 위 CU·장소 참조 없음(제19장 8).
  · 손 조작(폰 탭·엎기·다이얼·수갑·바구니)은 한 동작 i2v 또는 정지, 달리기 전신 i2v 0컷(발·손·문·POV + 효과음).
  · 돌리줌 1회(S05i 철문이 닫히는 순간), 더치 1회(S07j 「消されるのか」), 눈물 흐름 1컷(S10l 悠斗, pro 1080p).
  · 시점 자막(「東京　深夜一時」「一日目」「三日目」「六日目」)·질문 카드·#9110 카드는 클립에 직접(.ass Caption 없음, 제15장 12).
입력: productions/yamibaito-ja/lock.json · 00_script_ja.md · assets/auditions/yamibaito-tts/lineNNN.mp3 · assets/portraits/yamibaito-cast/cells/
출력: scripts/storyboard/yamibaito.json · scripts/scenes/yamibaito.json · scripts/audio/yamibaito.json · subs/yamibaito.ass ·
      assets/audio-overrides/yamibaito/lineNNN.mp3 · productions/yamibaito-ja/07_샷리스트.md · 16_감정일치표.md · 17_의상대조.md
사용법: python3 scripts/build_yamibaito_phase3.py
"""
import collections, json, os, re, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "yamibaito-ja")
SKIT = "yamibaito"
TTS_DIR = "yamibaito-tts"
TITLE = "時給5万円の罠"
FPS = 24; HARD = 1 / FPS; OMNI_MAX = 7.9; LEAD = 0.3; MIN_SHOT = 1.1; STILL_MAX = 6.5; I2V_MAX = 10.0

C = "assets/portraits/yamibaito-cast/cells/"
KENTA = ("Saito Kenta, a slim Japanese man aged 24, thin tired face, large eyes with slightly drooping outer corners, LEFT ear sticking out a little, "
         "thick black hair with a fringe covering half the forehead, clean-shaven, bare eyes with no glasses, no earrings, no moles")
WHO = {
    "KEV": (KENTA, C + "kenta-conv-front.png"),
    "KEH": (KENTA, C + "kenta-hoodie-front.png"),
    "KEW": (KENTA, C + "kenta-work-front.png"),
    "OT": ("the watchman, a heavy-set Japanese man in his forties, square jaw, closely shaved head, thick neck, small cold eyes, expressionless, "
           "no glasses, no earrings", C + "otoko-front.png"),
    "YU": ("Yuto, a thin Japanese man aged 22, round face, short brown hair, quick restless eyes, a thin gap in his RIGHT eyebrow, no glasses, no earrings",
           C + "yuto-front.png"),
    "TE": ("the night shop manager, a gentle Japanese man in his fifties, slim oval face, thick black hair with a little grey, silver half-rim glasses, "
           "kind calm eyes, no earrings", C + "tencho-front.png"),
}
WARD = {
    "KEV": "a plain teal convenience-store staff vest over a plain white long-sleeve shirt, black trousers, no badge, no name tag",
    "KEH": "a plain light-grey hooded sweatshirt with no print, black trousers, worn white sneakers",
    "KEW": "a plain grey work jumpsuit with no logo and no badge, worn white sneakers",
    "OT": "a plain black zip-up jacket with no logo, black trousers, black gloves",
    "YU": "a plain grey work jumpsuit with no logo",
    "TE": "a plain navy convenience-store staff vest over a plain white long-sleeve shirt, no badge, no name tag",
}
EXPR = {  # PHASE 2 2차 Kill Gate 합격 셀(08_PHASE2_검수.md)
    ("KEV", "tired"): C + "kenta-conv-expr1.png", ("KEV", "uneasy"): C + "kenta-conv-expr2.png", ("KEV", "wet"): C + "kenta-conv-expr3.png",
    ("KEV", "back"): C + "kenta-conv-back.png", ("KEV", "full"): C + "kenta-conv-full.png", ("KEV", "side"): C + "kenta-conv-3q.png",
    ("KEH", "tired"): C + "kenta-hoodie-expr1.png", ("KEH", "uneasy"): C + "kenta-hoodie-expr2.png", ("KEH", "wet"): C + "kenta-hoodie-expr3.png",
    ("KEH", "back"): C + "kenta-hoodie-back.png", ("KEH", "full"): C + "kenta-hoodie-full.png", ("KEH", "side"): C + "kenta-hoodie-3q.png",
    ("KEW", "tired"): C + "kenta-work-expr1.png", ("KEW", "fear"): C + "kenta-work-expr2.png", ("KEW", "wet"): C + "kenta-work-expr3.png",
    ("KEW", "back"): C + "kenta-work-back.png", ("KEW", "full"): C + "kenta-work-full.png", ("KEW", "side"): C + "kenta-work-3q.png",
    ("OT", "cold"): C + "otoko-expr1.png", ("OT", "back"): C + "otoko-back.png", ("OT", "full"): C + "otoko-full.png",
    ("YU", "flat"): C + "yuto-expr1.png", ("YU", "dart"): C + "yuto-expr2.png", ("YU", "wet"): C + "yuto-expr3.png",
    ("YU", "back"): C + "yuto-back.png", ("YU", "side"): C + "yuto-3q.png",
    ("TE", "calm"): C + "tencho-expr1.png", ("TE", "warm"): C + "tencho-expr2.png", ("TE", "soft"): C + "tencho-expr3.png",
    ("TE", "back"): C + "tencho-back.png",
}
LOC = {
    "CONB": C + "loc-conbini.png", "ROOM": C + "loc-room.png", "STREET": C + "loc-street-van.png", "VAN": C + "loc-van-inside.png",
    "FACT": C + "loc-factory-ext.png", "WORK": C + "loc-workroom.png", "CORR": C + "loc-corridor.png", "STAIRS": C + "loc-stairs.png",
    "PAY": C + "loc-payphone.png", "PARK": C + "loc-park.png", "P_PHONES": C + "prop-phones.png", "P_BANK": C + "prop-bankbooks.png",
}
PRESET = ("Photorealistic live-action Japanese crime re-enactment drama, present-day Japan (Reiwa era), Arri Alexa cinematic color grade, "
          "Kodak 35mm film grain, 24fps, 16:9, restrained documentary-like mise-en-scene, practical light sources visible, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, "
            "signage lettering, screens with text, documents with writing, printed labels, brand logos, license plates with characters, watermarks, "
            "stamps, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, anime, 3d render, cartoon, thick glossy gel tears, "
            "cartoon sweat drops, multiple tear streams on both cheeks, pink eyeshadow, red irises, lipstick on men, blue police lights, "
            "left-hand-drive car, square-hole coins")
PLAIN = ("Every phone screen, monitor, paper, envelope, sign, bankbook cover, wall clock face and emergency-exit sign is completely blank and clean: "
         "no letters, numbers, icons or symbols anywhere in the frame (Japanese text is composited later).")
TEARS = ("Realistic tears as in a live-action film: glossy wet eyes catching the light, a small clear tear bead on the lower lashes, "
         "at most one thin translucent tear track on one cheek, natural skin tone around the eyes and nose, matte natural skin, NO makeup; "
         "natural dark brown irises, clear white sclera; no pink or red eyelids, no eyeshadow, no red nose, no glossy gel streams, no cartoon droplets.")
TEARS_POOL = ("Realistic tears as in a live-action film: glossy wet eyes brimming with tears pooled along the lower lids and lashes, catching the light, "
              "about to spill but NOT yet running — both cheeks still completely DRY, no tear track; natural skin tone, matte skin, NO makeup, no pink eyelids, "
              "natural dark brown irises, clear white sclera.")
SWEAT = ("Realistic sweat as in a live-action film: fine tiny beads of perspiration on the forehead and temples, damp hair at the hairline, a faint natural sheen, "
         "one thin line of sweat running from the temple toward the jaw; no large cartoon drops, no face-wide shine.")
WET_HOLD = " Eyes wet and glistening with tears welling on the lower lids but NOT running down — the tears stay pooled."
TEARS_FLOW = (" The key action of this shot: ONE clear tear wells up, slowly spills over the lower lid and visibly rolls down the cheek during the shot. "
              "The tear is crystal-clear and colorless like water, thin as a thread, catching only a tiny highlight — NOT yellow, NOT amber, NOT thick, NOT gel. "
              "NOT smiling at any moment, mouth corners turned down, chin trembling slightly; a slow blink, a trembling breath; only one tear line, thin and translucent.")
GLASSES = {"KEV": "He wears no glasses.", "KEH": "He wears no glasses.", "KEW": "He wears no glasses.", "OT": "He wears no glasses.",
           "YU": "He wears no glasses.", "TE": "He wears thin silver half-rim glasses."}
PRO_TEARS = {"S10l"}  # 悠斗 재회 눈물 흐름 — pro 1080p 2테이크(제19장 15)
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, the face fills at least half of the frame height",
    "ots": "50mm lens, f/2.0, over-the-shoulder three-quarter framing, the listener's blurred shoulder and back of the head in the near foreground edge, the speaker's face at least one third of the frame height",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds, the person's face at least one quarter of the frame height",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus",
}
LIGHT = {
    "conb": "late night inside a Japanese convenience store: cold even 5600K fluorescent ceiling light, bright white shelves, slightly greenish, faces readable",
    "back": "a cramped staff back room of a convenience store at night: one cold fluorescent tube, grey lockers, the phone screen's blue glow on the face, faces readable",
    "room": "a tiny one-room apartment at night: one dim warm desk lamp and the cold blue glow of a smartphone screen, deep shadows, faces readable",
    "street_n": "a quiet residential street at night: orange sodium streetlights, wet asphalt, deep blue shadows, no headlights, no moving cars",
    "van": "inside a dark van at night: low-light teal interior, passing streetlights sliding over the faces, faces readable",
    "fact": "an abandoned factory exterior at night: one flickering sodium lamp, cold blue moonlight on corrugated iron and concrete, deep shadows",
    "work": "an abandoned factory workroom: flickering greenish fluorescent tubes, long steel tables, a red CCTV dot in the ceiling corner, faces readable, average brightness kept above 40/255",
    "corr": "a long concrete corridor at night: one fluorescent tube far away, a single flashlight beam, dark end, average brightness kept above 40/255",
    "stairs": "a rusted outdoor emergency staircase at night: faint green emergency light, cold moonlight, deep shadows",
    "pay": "night outside a convenience store by a national road: the store's bright white light spilling onto wet asphalt, a green public phone, faces readable",
    "raid": "night at the factory gate: pulsing RED rotating police light (red only, never blue) reflected on the concrete wall, flashlight beams in haze",
    "park": "early morning in a small Japanese park: warm low 3800K sunlight through trees, long soft shadows, gentle, faces readable",
    "city": "a Tokyo night street out of focus: soft bokeh of neon and signs, no readable text",
    "news": "a bright plain TV news studio, blank blue backdrop, soft even light",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "SIDE": "eye-level from the side or behind", "POV": "handheld first-person point of view"}
SPK_KEYS = {"健太": ("KEV", "KEH", "KEW"), "男": ("OT",), "悠斗": ("YU",), "店長": ("TE",)}
SCENE_WARD = {"S01": "KEV", "S02": "KEV", "S02b": "KEH", "S03": "KEH", "S04": "KEH", "S05": "KEH", "S06": "KEW", "S07": "KEW", "S08": "KEW",
              "S09": "KEW", "S10": "KEW", "S11": "KEH"}  # 00_script_ja.md §7 의상 연속성 — 생성기 자동 검사(제18장 9 ⑥)
WARD_EXC = {"S02j", "S02be", "S02bf", "S02bg", "S02bh", "S02bj", "S11e", "S11f", "H1"}  # S02 원룸 회상 = 후드, S11 「同じコンビニ」 = 조끼


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, act="", vo=False):
    """kind: d(OmniHuman 립싱크) / face(사람 i2v, who=[]면 실루엣 군중) / empty(무인 i2v) / estill(무인·합성 면 정지) /
    ins(손·소품 — motion 있으면 i2v, 없으면 정지) / reuse:<id> / card.  vo=True = 화자 화면 밖 또는 입이 안 보임(목소리만)."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc, subject=subject,
                line=line, fx=fx, motion=motion, expr=expr, act=act, vo=vo)


KV, KH, KW, OT, YU, TE = "KEV:KEV", "KEH:KEH", "KEW:KEW", "OT:OT", "YU:YU", "TE:TE"
OB = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, keeps looking "
      "toward the other person at the same three-quarter angle; no exaggerated motion, the same person throughout.")
HOLD = " Head stays at the same angle, never turns toward the camera; only body, hands and breath move. Mouth stays closed, lips still — this person is NOT speaking."
NS = " NOT smiling at any moment."
STILLCAR = " The van stays perfectly still with its headlights OFF; no moving cars, no headlights anywhere."
NOFACE = " No face, no head and no shoulders in the frame."

SHOTS = [
    # ① 후크 0:00~0:20 (HOOK_LEN 합 20초)
    S("H0", "H", "estill", "ecu", "room", "HA", [], None, "Insert, ABSOLUTELY NO PEOPLE: a smartphone lying flat on a dark bedsheet, its lock screen glowing but completely blank for three composited notification banners." ),
    S("H1", "H", "ins", "ecu", "room", "HA", [KH], None, "Insert: a young man's thumb hovering motionless just above a smartphone screen held in his other hand, the screen blank for a composited red 「応募する」 button; dark room, screen glow on the fingers." + NOFACE,
      line="NA0", motion="The thumb hovers and trembles very slightly above the screen, never touching it; the screen glow flickers once; nothing else moves."),
    S("H2a", "H", "ins", "ecu", "stairs", "HA", [KW], "STAIRS", "Insert, handheld, dark outdoor emergency staircase at night: a hand in a grey work-jumpsuit sleeve gripping a rusted green steel railing, below it worn white sneakers stepping down two steps at a time, motion-blurred; faint green emergency light." + NOFACE,
      line="NA1", fx="handheld", motion="The sneakers take one fast step down two stairs; the hand slides along the railing; the camera shakes handheld; nothing else."),
    S("H2b", "H", "empty", "ms", "fact", "LA", [], "FACT", "Low angle, ABSOLUTELY NO PEOPLE: a heavy rusted iron gate of an old factory half closed, strong cold backlight from inside pouring through the narrowing gap, haze, silhouettes of nothing but the door frame.",
      line="L00", vo=True, motion="The iron gate swings slowly shut, the slit of backlight narrowing to nothing; dust in the light; nothing else moves."),
    S("H3", "H", "card", "ecu", "room", "EL", [], None, "Question card over a blurred dark still of the half-closed iron gate (composited: centre serif line + small fiction notice at the bottom)."),
    S("H4", "H", "empty", "ws", "city", "EL", [], None, "Tokyo night street completely out of focus: soft round bokeh of neon lights and signs, no readable text, no people, no cars. Title composited.",
      motion="The bokeh lights shimmer very slightly; nothing else moves."),

    # S01 편의점 심야 (조끼)
    S("S01a", "S01", "face", "ws", "conb", "HA", [KV], "CONB", "High angle like a security camera inside an empty Japanese convenience store at night: Kenta in a teal staff vest seen from behind at the register, straightening a row of goods on the counter, no customers, bright white shelves. Corner caption composited.",
      line="NA2", motion="He straightens the goods with one slow hand movement; the fluorescent light hums steady; nothing else moves." + HOLD, expr="back"),
    S("S01b", "S01", "face", "ms", "conb", "EL", [KV], "CONB", "Medium, inside the store behind the register: Kenta in the teal vest at three-quarter angle, hands resting on the counter, staring at the empty aisle, tired.",
      line="NA3", motion="A slow tired breath, one slow blink; his eyes stay on the empty aisle." + HOLD, expr="tired"),
    S("S01c", "S01", "ins", "ecu", "conb", "HA", [KV], "CONB", "Insert, high angle over a bright store shelf: a young man's hands in white shirt sleeves and the edge of a teal vest lining up plain unlabeled rice balls on the shelf, every wrapper blank." + NOFACE,
      line="NA4", motion="The hands slide one rice ball into line and stop; nothing else moves."),
    S("S01d", "S01", "face", "cu", "conb", "SIDE", [KV], "CONB", "Close-up profile of Kenta behind the register, eyes heavy and red with fatigue, jaw tightening to hold back a yawn, cold fluorescent light.",
      line="NA8", motion="He presses his lips together to swallow a yawn, a slow heavy blink; head stays in profile." + HOLD, expr="side"),

    # S02 DM — 휴게실 (조끼) + 원룸 회상 인서트 (후드)
    S("S02a", "S02", "ins", "ecu", "back", "HA", [KV], None, "Insert, high angle: a smartphone lying face up on a grey steel table in a cramped staff back room, its screen lit but blank for a composited DM notification; a young man's hand in a white shirt sleeve reaching for it." + NOFACE,
      line="NA9", motion="The phone buzzes once, a tiny vibration; the hand picks it up slowly and lifts it a few centimetres; nothing else moves."),
    S("S02b", "S02", "estill", "ecu", "back", "EL", [], None, "Insert, ABSOLUTELY NO PEOPLE: a smartphone screen filling 70 percent of the frame, held upright, the screen completely blank white-grey for a composited chat message; the dark back room blurred around it.", line="NA10"),
    S("S02c", "S02", "face", "cu", "back", "EL", [KV], None, "Close-up of Kenta in the teal vest leaning against grey lockers in the back room, face lit from below by the phone screen, reading at three-quarter angle, eyes moving across the screen, skeptical.",
      line="NA11", motion="His eyes track across the screen line by line; one slow blink; a small frown." + HOLD, expr="uneasy"),
    S("S02d", "S02", "ins", "ecu", "back", "HA", [KV], None, "Insert: a young man's thumb hesitating above the blank glowing phone screen, the other fingers holding the phone, white shirt cuff and teal vest edge visible." + NOFACE,
      line="NA12", motion="The thumb hovers and twitches slightly, never touching the screen; nothing else moves."),
    S("S02e", "S02", "face", "ws", "back", "HA", [KV], None, "Wide, slightly high: the cramped staff back room, Kenta in the teal vest small in the frame leaning against the lockers with the phone, a plastic chair and a steel table, a single fluorescent tube, lonely.",
      line="NA13", motion="He shifts his weight slightly and gives a tiny shake of his head at the phone; the light hums." + HOLD, expr="full"),
    S("S02f", "S02", "d", "cu", "back", "EL", [KV], None, "Close-up chest-up: Kenta in the teal vest leaning on the lockers at three-quarter angle, looking down at the phone below the frame edge, lips barely parting, whispering to himself in disbelief; the phone is below the frame.", line="L01",
      act="Kenta whispers to himself in disbelief, almost without voice, looking down at the phone out of frame, that it can't be true, 250,000 yen in one night. Speaking to nobody, barely moving his lips." + NS + OB, expr="uneasy"),
    S("S02g", "S02", "estill", "ecu", "back", "EL", [], None, "Insert, ABSOLUTELY NO PEOPLE: the same smartphone screen upright filling the frame, blank for a composited banking-app balance; cold blue glow. (match-dissolve pair with the DM screen)", line="NA6", fx="matchdissolve"),
    S("S02h", "S02", "estill", "ecu", "room", "HA", [], "ROOM", "Insert, high angle, ABSOLUTELY NO PEOPLE: a plain white envelope lying on the floor beside a low bed in a tiny dim apartment, its front blank for a composited rent-reminder title; a dim lamp above.", line="NA5"),
    S("S02i", "S02", "estill", "ecu", "room", "EL", [], "ROOM", "Insert, ABSOLUTELY NO PEOPLE: a plain white envelope and a blank folded document on a small cluttered desk under a dim lamp, blank for a composited scholarship-repayment title.", line="NA7a"),
    S("S02j", "S02", "face", "ms", "room", "HA", [KH], "ROOM", "Medium, slightly high: Kenta in a grey hoodie sitting on the edge of a low bed in his tiny dim apartment at night, a blank document in his hands, head bowed, the lamp behind him.",
      line="NA7b", motion="He stares at the paper, a slow breath, his shoulders sag a little." + HOLD, expr="tired"),
    S("S02k", "S02", "ins", "ecu", "back", "HA", [KV], None, "Insert: a thumb scrolling a smartphone screen held in a white shirt sleeve with a teal vest edge, the screen blank for a composited social feed; dim back room." + NOFACE,
      line="NA7", motion="The thumb swipes up once, slowly; the screen glow shifts; nothing else moves."),
    S("S02l", "S02", "face", "cu", "back", "LA", [KV], None, "Close-up, slightly low: back in the store's back room, Kenta in the teal vest lowers the phone and stares at nothing, jaw set, eyes hollow under the fluorescent tube.",
      line="NA14", motion="His eyes lose focus, a slow swallow, jaw tightens; head stays still." + HOLD, expr="uneasy"),

    # S02b 조건 3가지 — 원룸 (후드)
    S("S02ba", "S02b", "estill", "ecu", "room", "EL", [], None, "Insert, ABSOLUTELY NO PEOPLE: a smartphone screen upright filling the frame, blank for a composited list of three conditions; dim room glow.", line="NA16"),
    S("S02bb", "S02b", "estill", "ecu", "work", "HA", [], "P_PHONES", "Insert, ABSOLUTELY NO PEOPLE: a grey plastic crate on a steel table holding a dozen smartphones piled face down, all screens dark and blank, harsh fluorescent light.", line="NA17"),
    S("S02bc", "S02b", "estill", "ecu", "van", "HA", [], "VAN", "Insert, ABSOLUTELY NO PEOPLE: a plain black sleep eye mask lying flat on a dark grey van seat, its elastic strap loose, dim teal interior light.", line="NA18"),
    S("S02bd", "S02b", "ins", "ecu", "room", "HA", [KH], None, "Insert, high angle: a completely blank sheet of white paper lying flat on a desk (composited pledge text later), a young man's right hand in a grey hoodie sleeve holding a black ballpoint pen just above the signature area, not yet writing." + NOFACE,
      line="NA19"),
    S("S02be", "S02b", "face", "cu", "room", "EL", [KH], "ROOM", "Close-up: Kenta in the grey hoodie sitting on his bed at night, the phone glow on his face, frowning at the screen at three-quarter angle, uneasy.",
      line="NA20", motion="His frown deepens, he bites the inside of his lip, one slow blink." + HOLD, expr="uneasy"),
    S("S02bf", "S02b", "face", "ecu", "room", "EL", [KH], None, "Extreme close-up of Kenta's two eyes only, the blank phone screen's blue-white light reflected in both pupils, lashes, the fringe above; the eyes fixed downward on the screen.",
      line="NA21", motion="One slow blink; the reflected glow brightens slightly; nothing else moves." + HOLD, expr="uneasy"),
    S("S02bg", "S02b", "face", "ws", "room", "HA", [KH], "ROOM", "Wide from above: the whole tiny one-room apartment at night, Kenta in the grey hoodie lying on his back on the low bed, the dark phone resting on his chest, staring at the ceiling, the desk lamp the only light.",
      motion="The phone screen on his chest lights up again by itself, casting glow on the ceiling; he does not move except breathing." + HOLD, expr="full"),
    S("S02bh", "S02b", "d", "cu", "room", "LA", [KH], None, "Close-up chest-up, slightly low: Kenta in the grey hoodie sitting up on the bed at three-quarter angle, looking at the phone below the frame edge, speaking low to himself, dim lamp behind.", line="L02",
      act="Kenta tells himself in a low flat voice, eyes on the phone out of frame, that it's not like he's going to die, it's only one week. Convincing himself, not smiling, jaw tight." + NS + OB, expr="uneasy"),
    S("S02bi", "S02b", "ins", "ecu", "room", "HA", [KH], None, "Insert, the SAME framing as the hook: a young man's thumb above a smartphone screen blank for a composited red button, grey hoodie sleeve, dark room." + NOFACE,
      line="NA22", fx="matchcut", motion="The thumb comes down and presses the screen once, then lifts a little; the screen flashes brighter; nothing else moves."),
    S("S02bj", "S02b", "face", "ms", "room", "EL", [KH], "ROOM", "Medium: Kenta in the grey hoodie sitting on the bed right after pressing, face lit by the screen, eyes wide and still, swallowing, three-quarter angle, NOT looking at the camera.",
      line="NA15", motion="He swallows once; his eyes stay fixed on the screen; a long held breath." + HOLD, expr="uneasy"),

    # S03 출발 전날 밤 — #9110·어머니 전화·왕박스카 (후드)
    S("S03a", "S03", "face", "ms", "room", "EL", [KH], "ROOM", "Medium: Kenta in the grey hoodie sitting on the bed at night, elbows on knees, the phone in both hands, glancing at the dark window, restless.",
      line="NA23", motion="He glances at the window and back to the phone; a restless breath; one knee bounces slightly." + HOLD, expr="uneasy"),
    S("S03b", "S03", "estill", "ecu", "room", "EL", [], None, "Insert, ABSOLUTELY NO PEOPLE: a smartphone screen upright filling the frame, blank for a composited search result; dim room.", line="NA24"),
    S("S03c", "S03", "ins", "ecu", "room", "EL", [KH], None, "Insert: a young man's thumb trembling just above a blank phone screen where a composited green call button will be, grey hoodie sleeve, the phone held in the other hand." + NOFACE,
      line="NA24a", motion="The thumb hovers, trembles, lowers a millimetre and stops without touching; nothing else moves."),
    S("S03d", "S03", "ins", "ecu", "room", "HA", [KH], None, "Insert, high angle: a hand in a grey hoodie sleeve turning a smartphone face down onto a rumpled bedsheet, the phone lying flat on the bed." + NOFACE,
      line="NA24b", motion="The hand turns the phone over and lays it face down on the sheet, then withdraws; the phone stays on the bed."),
    S("S03e", "S03", "ins", "ecu", "room", "SIDE", [KH], None, "Insert, high angle: a smartphone lying face down on the bedsheet, a faint glow leaking around its edges, a hand in a grey hoodie sleeve reaching for it." + NOFACE,
      line="L03", vo=True, motion="The phone vibrates, shivering against the sheet; the hand picks it up and turns it over, its blank screen glowing; nothing else moves."),
    S("S03f", "S03", "d", "cu", "room", "EL", [KH], None, "Close-up chest-up: Kenta in the grey hoodie at three-quarter angle holding the phone to his far ear (the phone hidden behind his head, away from the camera), forcing a light tone, eyes not smiling, dim lamp.", line="L04",
      act="Kenta answers his mother on the phone with a forced light voice, saying yes he's fine, he found a part-time job; his mouth smiles slightly but his eyes do not. Speaking into the phone at his far ear." + OB, expr="uneasy"),
    S("S03g", "S03", "face", "cu", "room", "SIDE", [KH], None, "Close-up from the side: Kenta listening to the phone at his far ear, eyes closing slowly, the lamp behind him; his mouth is hidden by the angle.",
      line="L05", vo=True, motion="His eyes close slowly, a swallow, a small nod; head stays in profile." + HOLD, expr="side"),
    S("S03h", "S03", "face", "ms", "room", "HA", [KH], "ROOM", "Medium from above: Kenta in the grey hoodie lying on his back on the bed, the phone resting on his chest under his hand, staring at the ceiling.",
      line="NA25a", motion="A slow breath lifts the phone on his chest; one slow blink; nothing else moves." + HOLD, expr="full"),
    S("S03i", "S03", "ins", "ecu", "room", "HA", [KH], None, "Insert, high angle: a small black backpack open on the bed, a young man's hands in grey hoodie sleeves putting a folded plain white T-shirt inside, two more folded shirts beside it on the bed." + NOFACE,
      line="NA25d", motion="The hands lower the folded shirt into the backpack and let go; nothing else moves."),
    S("S03j", "S03", "estill", "ecu", "room", "EL", [], "ROOM", "Insert, ABSOLUTELY NO PEOPLE: a small black backpack standing on the floor by the apartment door next to a pair of worn white sneakers, dim lamp light.", line="NA25e"),
    S("S03k", "S03", "face", "ws", "street_n", "EL", [KH], "STREET", "Wide, night, a quiet residential street: a black Japanese one-box van (right-hand drive, sliding door) parked at the kerb with all lights off; Kenta in the grey hoodie with a small backpack seen strictly from behind, walking slowly toward it." + STILLCAR,
      line="NA25b", motion="He walks slowly away from the camera toward the van, back to the camera the whole time, never turning around; the van does not move." + HOLD, expr="back"),
    S("S03l", "S03", "empty", "ms", "street_n", "LA", [], "STREET", "Low angle, ABSOLUTELY NO PEOPLE: the black one-box van parked under a sodium streetlight, its dark sliding door and tinted windows, lights off, the blank number plate out of focus." + STILLCAR,
      line="NA25c", motion="Nothing moves; the streetlight flickers faintly once."),
    S("S03m", "S03", "empty", "ecu", "street_n", "EL", [], "STREET", "Insert, ABSOLUTELY NO PEOPLE: the black van's sliding door seen from the kerb, the dark gap of the open door, no one visible inside." + STILLCAR,
      line="NA25", motion="The sliding door slides shut slowly in one motion and closes with a soft thud; nothing else moves."),

    # S04 승합차 — 우핸들, 반대편 뒷좌석에서 옆으로 (후드)
    S("S04a", "S04", "face", "ms", "van", "EL", [KH], "VAN", "Medium from the opposite rear seat of a dark Japanese van (RIGHT-hand drive, two front seats, a rear bench): Kenta in the grey hoodie by the window, beside him and in the row ahead three young men with heads bowed, only their backs and bowed heads visible, faces never visible; passing streetlights slide over them.",
      line="NA26", motion="Streetlights slide slowly across the faces and seats; nobody moves except breathing." + HOLD, expr="tired"),
    S("S04b", "S04", "face", "cu", "van", "SIDE", [KH], None, "Close-up profile of Kenta against the dark van window, a passing light crossing his face, lips pressed shut, hood down.",
      line="NA27", motion="A passing light crosses his face from left to right; one slow blink; head stays in profile." + HOLD, expr="side"),
    S("S04c", "S04", "face", "ms", "van", "EL", [OT], "VAN", "Medium from the rear bench of the right-hand-drive van: the back of the watchman's shaved head and black jacket collar in the LEFT front passenger seat, the headrest, the dark windscreen beyond; he does not turn around; his face is not visible.",
      line="L06", vo=True, motion="His head stays perfectly still facing forward; passing light slides over the headrest; nothing else moves." + HOLD, expr="back"),
    S("S04d", "S04", "ins", "ecu", "van", "HA", [OT, KH], None, "Insert, high angle over the seat back: a black-gloved hand holding a grey plastic basket back over the seat toward the camera, and a young man's hands in grey hoodie sleeves laying a smartphone and a plastic card into the bottom of the basket." + NOFACE,
      line="L06a", vo=True, motion="The hands set the phone and the card down on the bottom of the basket and withdraw; the gloved hand holds the basket still."),
    S("S04e", "S04", "ins", "ecu", "van", "EL", [], None, "Insert: a young man's hand resting on the knee of dark trousers in a dark van seat, the fingers trembling, a grey sleeve, passing light." + NOFACE,
      line="NA27a", motion="Only the fingers tremble finely; a passing light slides over the hand; nothing else moves."),
    S("S04f", "S04", "face", "cu", "van", "EL", [KH], None, "Close-up: Kenta in the van at three-quarter angle pulling a plain black eye mask down over his eyes with one hand, the elastic over his hair, in the last moment his eyes disappear under it.",
      line="NA27b", motion="He pulls the black eye mask down over his eyes in one slow movement and lowers his hand; his head stays still." + HOLD, expr="uneasy"),
    S("S04g", "S04", "face", "cu", "van", "HA", [KH], None, "Close-up, slightly high: Kenta with the black eye mask over his eyes, head bowed, lips pressed tight, passing light on his hair.",
      line="NA27c", motion="His lips press tighter; a slow controlled breath; a passing light crosses." + HOLD, expr="uneasy"),
    S("S04h", "S04", "empty", "ecu", "van", "EL", [], "VAN", "Insert, ABSOLUTELY NO PEOPLE: the dark tinted van window from inside, blurred orange lights thinning out into black, rain-less, no readable signs.",
      line="NA28", motion="The blurred lights outside slide past slower and slower and fade into darkness."),
    S("S04i", "S04", "face", "ws", "van", "HA", [KH], "VAN", "Wide from above and behind inside the dark van: four young men in eye masks with bowed heads in the rear seats, seen from behind, Kenta's grey hood among them, the two front seats and the driver's hands on the right-hand-drive wheel in shadow, faces never visible.",
      line="NA29", motion="A single passing light slides over the bowed heads; nobody moves except breathing." + HOLD, expr="back"),
    S("S04j", "S04", "face", "cu", "van", "EL", [KH], None, "Close-up: Kenta in the eye mask, head tilted slightly as the van comes to a stop, total darkness outside, only a faint teal interior light on his face.",
      line="NA30", motion="His head lifts slightly as the motion stops; a held breath; nothing else moves." + HOLD, expr="uneasy"),

    # S05 폐공장 철문 (후드)
    S("S05a", "S05", "empty", "ews", "fact", "LA", [], "FACT", "Extreme wide, low angle, ABSOLUTELY NO PEOPLE: an old concrete factory at night with a tall brick chimney, barred windows, a heavy rusted iron gate, one flickering sodium lamp, no sign, no vehicles.",
      line="NA31", motion="The sodium lamp flickers faintly; nothing else moves."),
    S("S05b", "S05", "face", "cu", "fact", "EL", [KH], None, "Close-up: a hand from above lifting the black eye mask off Kenta's eyes; his eyes open and blink at the darkness, the rusted gate and barred windows blurred behind him.",
      line="NA32", motion="The mask is lifted away upward; his eyes open and blink twice, adjusting to the dark; head stays still." + HOLD, expr="uneasy"),
    S("S05c", "S05", "face", "ws", "fact", "EL", [KH], "FACT", "Wide: four young men seen strictly from behind walking through the open iron gate into the factory, backlit silhouettes against a cold light inside, Kenta's grey hood and small backpack among them, faces never visible.",
      motion="They walk slowly away from the camera into the gate, backs to the camera the whole time, never turning around." + HOLD, expr="back"),
    S("S05e", "S05", "ins", "ecu", "corr", "EL", [KH], None, "Insert: a young man's fingertips in a grey hoodie sleeve brushing a cold rusted steel wall in a dark corridor, flakes of rust, a flashlight beam grazing it." + NOFACE,
      line="NA33", motion="The fingertips slide a few centimetres along the rusted steel and stop; the light grazes; nothing else moves."),
    S("S05f", "S05", "d", "cu", "corr", "EL", [OT], None, "Close-up chest-up: the watchman in the black jacket, shaved head, standing in the dark corridor lit by a flashlight from below and the side, expressionless, speaking slowly at three-quarter angle toward the young men out of frame.", line="L07",
      act="The watchman tells the young men flatly, slowly, in a low voice without any emotion, that from now on all contact with the outside is cut. Looking at them with dead eyes, head perfectly still, no gestures." + OB, expr="cold"),
    S("S05g", "S05", "face", "cu", "corr", "HA", [KH], None, "Close-up, slightly high: Kenta listening in the dark corridor, a flashlight beam on half his face, swallowing hard, eyes on the watchman out of frame to the left.",
      motion="He swallows; his eyes stay on the man to the left; a shallow breath." + HOLD, expr="uneasy"),
    S("S05h", "S05", "d", "cu", "corr", "LA", [OT], None, "Close-up chest-up, slightly low: the watchman in the black jacket, only his eyes shifting to look at one young man, the rest of his face dead still, flashlight from below.", line="L08",
      act="The watchman says in a quiet low voice, slower, that there is no exit here, then after a pause tells them to work; only his eyes move to Kenta, no smile, no gesture." + NS + OB, expr="cold"),
    S("S05i", "S05", "face", "cu", "corr", "EL", [KH], None, "Close-up: Kenta turning his head to look back over his shoulder toward the gate behind him, fear dawning, flashlight edge light. (dolly zoom in editing)",
      fx="dollyzoom", motion="He turns his head slowly about 20 degrees to look back over his shoulder, eyes widening; nothing else moves." + HOLD, expr="uneasy"),
    S("S05j", "S05", "empty", "ecu", "fact", "EL", [], "FACT", "Insert from inside, ABSOLUTELY NO PEOPLE: the heavy rusted iron gate, the last slit of night light between the two halves, rust and chain.",
      motion="The two halves of the iron gate close the last gap in one slow motion and shut; dust falls; nothing else moves."),
    S("S05k", "S05", "face", "ms", "corr", "HA", [KH], "CORR", "Medium from above and behind: Kenta in the grey hoodie standing frozen in the corridor, seen from behind, looking at the closed iron gate at the far end, the flashlight gone, one weak fluorescent tube.",
      line="NA34", motion="He stands completely still looking at the gate; the fluorescent tube flickers once." + HOLD, expr="back"),

    # S06 작업실 一日目 (작업복)
    S("S05k2", "S05", "estill", "ecu", "fact", "EL", [], None, "Insert from inside, ABSOLUTELY NO PEOPLE: a thick rusted chain and a heavy padlock on the inside of the closed iron gate, a sliver of cold light, rust flakes."),
    S("S06a", "S06", "empty", "ws", "work", "HA", [], "WORK", "Wide, high angle, ABSOLUTELY NO PEOPLE: an abandoned factory workroom under flickering greenish fluorescent tubes, long steel tables stacked with plain blank bankbooks and cardboard parcels, a CCTV camera with a red dot in the ceiling corner. Corner caption composited.",
      line="NA35", motion="The fluorescent tubes flicker irregularly; the red CCTV dot blinks; nothing else moves."),
    S("S06b", "S06", "face", "ms", "work", "EL", [KW], "WORK", "Medium from behind: a row of young men in grey work jumpsuits seated at a long steel table with heads bowed, seen from behind, Kenta nearest the camera, hands moving over piles of blank bankbooks, faces never visible.",
      line="NA36", motion="Hands move slowly over the bankbooks; heads stay bowed; the light flickers." + HOLD, expr="back"),
    S("S06c", "S06", "ins", "ecu", "work", "HA", [KW], "P_BANK", "Insert, high angle looking down at a steel table: stacks of plain blank Japanese vertical bankbooks lying flat ON THE TABLE, a young man's hands in grey jumpsuit sleeves from the top edge sorting them into piles." + NOFACE,
      line="NA37", motion="The hands lift one bankbook and set it flat on the next pile; everything stays resting on the table."),
    S("S06d", "S06", "ins", "ecu", "work", "HA", [KW], None, "Insert, high angle: a plain brown cardboard parcel lying ON THE STEEL TABLE, a young man's hands in grey jumpsuit sleeves smoothing a strip of tape over its blank top." + NOFACE,
      line="NA38", motion="The hands press the tape flat along the parcel in one slow movement; the parcel stays on the table."),
    S("S06e", "S06", "face", "cu", "work", "HA", [KW], None, "Close-up, slightly high: Kenta in the grey work jumpsuit at three-quarter angle under the flickering fluorescent light, dark circles under his eyes, exhausted, eyes half closed, looking down at the table.",
      line="NA39", motion="His eyelids droop and lift, a slow exhausted breath; the light flickers over his face." + HOLD, expr="tired"),
    S("S06e2", "S06", "face", "ws", "work", "HA", [KW], "WORK", "High wide from the ceiling corner like the CCTV: the long steel tables, a dozen young men in grey jumpsuits bowed over them seen from above and behind, Kenta among them, faces never visible, flickering light.",
      motion="Hands move slowly over the tables; the fluorescent light flickers; nobody lifts a head." + HOLD, expr="back"),
    S("S06f", "S06", "face", "ms", "work", "EL", [OT], "WORK", "Medium: the watchman in the black jacket seen strictly from behind, walking slowly away between the long tables of bowed young men, black gloves clasped behind his back, his face never visible.",
      line="L08a", vo=True, motion="He walks slowly away from the camera between the tables, back to the camera the whole time, never turning around." + HOLD, expr="back"),
    S("S06g", "S06", "estill", "ecu", "work", "HA", [], None, "Insert, high angle, ABSOLUTELY NO PEOPLE: a dented aluminium tray lying flat on the steel table with a small mound of plain white rice and a single slice of yellow pickled radish, nothing else, harsh fluorescent light.", line="NA39a"),
    S("S06h", "S06", "empty", "ecu", "work", "LA", [], "WORK", "Insert, low angle, ABSOLUTELY NO PEOPLE: a dusty white CCTV dome camera in the corner of a stained ceiling, its small red indicator light, a flickering fluorescent tube beside it.",
      line="NA39b", motion="The red indicator blinks steadily; the fluorescent tube flickers; nothing else moves."),
    S("S06i", "S06", "ins", "ecu", "work", "EL", [KW], None, "Insert: two pairs of hands in grey jumpsuit sleeves passing a plain brown cardboard carton from one to the other along the steel table, the carton resting on the table edge." + NOFACE,
      motion="One pair of hands slides the carton along the table to the other pair, which takes hold of it; the carton stays on the table."),
    S("S06j", "S06", "face", "ms", "work", "HA", [KW], "WORK", "Medium from above: under a long steel work table, a young man in a grey jumpsuit curled on his side on a single thin blanket on the concrete floor, seen from behind, his face hidden, the fluorescent light dim.",
      line="NA39c", motion="Only his back rises and falls with slow breathing; nothing else moves." + HOLD, expr="back"),
    S("S06k", "S06", "face", "cu", "work", "SIDE", [YU], None, "Close-up from the side and slightly behind: Yuto, a young man with short brown hair in a grey jumpsuit, head bowed over the table, his hands sorting blank bankbooks, his face half hidden by the angle, mouth not visible.",
      line="NA39d", motion="His hands keep sorting slowly; his head stays bowed; one blink." + HOLD, expr="side"),
    S("S06k2", "S06", "face", "cu", "work", "EL", [KW], None, "Close-up: Kenta at the table at three-quarter angle, head low, his eyes sliding sideways toward the young man on his left without turning his head, fluorescent light.",
      motion="His eyes slide slowly to the left and back down; his head does not turn; a quiet breath." + HOLD, expr="tired"),
    S("S06l", "S06", "face", "cu", "work", "HA", [YU], None, "Close-up, slightly high: Yuto beside Kenta at the table, head still bowed over the bankbooks, speaking without raising his head, his mouth hidden by the angle and his fringe, eyes glancing sideways.",
      line="L09", vo=True, motion="His eyes glance sideways once toward the right; his head stays bowed; his hands keep moving slowly." + HOLD, expr="dart"),
    S("S06m", "S06", "face", "cu", "work", "HA", [KW], None, "Close-up, high: Kenta with his head bowed low over the table, his face hidden by his black fringe, only his nose tip and jaw visible, his hands still on the bankbooks; he answers without lifting his head.",
      line="L10", vo=True, motion="His jaw moves very slightly as he murmurs; his head stays bowed; the hands stop." + HOLD),
    S("S06n", "S06", "d", "ots", "work", "EL", [YU, KW], None, "Over Kenta's blurred grey shoulder (right foreground, from behind): Yuto at three-quarter angle at the table, barely lifting his head, speaking in a low voice with a bitter half-smile that does not reach his eyes, fluorescent light.", line="L11",
      act="Yuto tells Kenta in a low self-mocking voice, barely moving his head, that he was told the same thing, then after a pause, three weeks ago. Speaking sideways to Kenta next to him, eyes darting once toward the CCTV." + OB, expr="dart"),
    S("S06o", "S06", "ins", "ecu", "work", "HA", [KW], "P_BANK", "Insert, high angle: a young man's hands in grey jumpsuit sleeves stopped dead on a stack of blank bankbooks lying flat ON THE TABLE, fingers trembling." + NOFACE,
      line="NA40", motion="Only the fingers tremble finely on the bankbooks; nothing else moves."),

    # S07 三日目 → 六日目 — 실종·폰 더미·「消されるのか」 (작업복)
    S("S06o2", "S06", "face", "cu", "work", "LA", [KW], None, "Close-up, slightly low: Kenta's face under the flickering fluorescent tube, eyes hollow and fixed on the table, lips parted slightly, the colour drained from his face.",
      motion="The light flickers over his face; a slow swallow; his eyes stay fixed down." + HOLD, expr="fear"),
    S("S07a", "S07", "estill", "ecu", "work", "HA", [], "P_PHONES", "Insert, high angle, ABSOLUTELY NO PEOPLE: a grey plastic basket on the steel table now full of smartphones piled face down, screens dark and blank, fluorescent light. Corner caption composited.", line="NA41"),
    S("S07b", "S07", "estill", "ecu", "work", "EL", [], None, "Insert, ABSOLUTELY NO PEOPLE: dozens of smartphones heaped in the corner of a steel table against a concrete wall, screens dark and blank, a few with cracked glass, harsh fluorescent light."),
    S("S07c", "S07", "estill", "ws", "work", "HA", [], None, "High angle, ABSOLUTELY NO PEOPLE, grainy security-camera look: hundreds of smartphones heaped on a dusty concrete warehouse floor, a single flashlight circle lighting part of the pile, the rest in darkness."),
    S("S07d", "S07", "estill", "ecu", "work", "EL", [], "WORK", "Insert, ABSOLUTELY NO PEOPLE: an empty steel chair at the long table under the fluorescent light, a dented aluminium tray with leftover rice sitting on the seat.", line="NA42"),
    S("S07e", "S07", "empty", "ms", "corr", "LA", [], "CORR", "Low angle, night, ABSOLUTELY NO PEOPLE: the far end of the dark concrete corridor, a rusted iron door, a flashlight beam sweeping across it from the side.",
      motion="A flashlight beam sweeps slowly across the iron door from left to right and passes; nothing else moves."),
    S("S07f", "S07", "face", "cu", "work", "EL", [KW], None, "Close-up: Kenta at the table at three-quarter angle, head down, eyes shifting toward Yuto on his left as he hears the whisper; fluorescent light.",
      line="L12", vo=True, motion="His eyes shift slowly to the left toward the whisper and stop; his hands stay still." + HOLD, expr="fear"),
    S("S07g", "S07", "face", "cu", "work", "SIDE", [YU], None, "Close-up from the side: Yuto at the table, head bowed low, speaking even lower without moving his lips visibly, his mouth hidden by the angle, eyes flicking toward the ceiling camera.",
      line="L13", vo=True, motion="His eyes flick up toward the camera in the corner and back down; head stays bowed." + HOLD, expr="side"),
    S("S07h", "S07", "d", "ots", "work", "HA", [YU, KW], None, "Over Kenta's blurred shoulder (left foreground, from behind), slightly high: Yuto at three-quarter angle, eyes lowered to the table, speaking low and hopeless, fluorescent light.", line="L13a",
      act="Yuto tells Kenta in a low hopeless whisper, eyes lowered to the table, that they hold his family's address, then after a pause, that there is no running away. Not looking up, no smile, lips barely moving." + NS + OB, expr="flat"),
    S("S07i", "S07", "ins", "ecu", "work", "HA", [KW], None, "Insert: a young man's hand gripping the grey sleeve of his own work jumpsuit at the forearm, knuckles white, fluorescent light." + NOFACE,
      motion="The hand tightens its grip on the sleeve, the knuckles whitening; a fine tremor; nothing else moves."),
    S("S07i2", "S07", "face", "cu", "work", "HA", [KW], None, "Close-up, slightly high: Kenta at the table, eyes down, lips pressed white, the fluorescent tube buzzing above, a bead of sweat at his temple.",
      motion="His lips press tighter; the light flickers; a sweat bead slides slowly down his temple; his eyes stay down." + HOLD, expr="fear"),
    S("S07j", "S07", "d", "cu", "work", "EL", [KW], None, "Close-up chest-up (5-degree dutch tilt in editing): Kenta in the grey jumpsuit at three-quarter angle, eyes wet but not running, jaw trembling, whispering to himself under the flickering fluorescent light, NOT smiling.", line="L14", fx="dutch",
      act="NOT smiling at any moment. Kenta whispers to himself in a trembling voice, barely audible, that he too will be erased here; eyes wet, chin trembling, mouth corners down, a swallowed breath. Speaking to nobody." + WET_HOLD + OB, expr="wet"),
    S("S07k", "S07", "ins", "ecu", "work", "HA", [KW], None, "Insert, high angle: a young man's rough chapped hands with cracked knuckles and small cuts resting on the steel table, grey jumpsuit sleeves, fluorescent light." + NOFACE,
      line="NA43a", motion="The fingers flex slightly once and go still; nothing else moves."),
    S("S07k2", "S07", "face", "cu", "work", "SIDE", [KW], None, "Close-up profile: Kenta's blank exhausted face in the flickering fluorescent light, eyes unfocused, a thin line of sweat at the temple.",
      motion="One slow blink; the light flickers across his profile; nothing else moves." + HOLD, expr="side"),
    S("S07l", "S07", "face", "ws", "work", "EL", [OT], "WORK", "Wide through a dusty glass window into a small office: the watchman in the black jacket seen strictly from behind walking out of the office door with a cigarette pack in his gloved hand, a round wall clock with a blank face on the wall above, a desk and ashtray.",
      line="NA43b", motion="He walks out through the door away from the camera, back to the camera the whole time, and is gone; the clock stays still." + HOLD, expr="back"),
    S("S07m", "S07", "empty", "ecu", "work", "LA", [], None, "Insert, low angle, ABSOLUTELY NO PEOPLE: a plain round wall clock with a BLANK white face and black hands on a stained office wall, filling the frame, fluorescent light (3:00 composited).", line="NA43c",
      motion="The fluorescent light flickers faintly over the clock face; the hands stay perfectly still; nothing else moves."),
    S("S07n", "S07", "estill", "ms", "corr", "EL", [], "CORR", "ABSOLUTELY NO PEOPLE: the end of the dark corridor, a rusted iron door with a plain green emergency-exit sign box above it, completely blank with no pictogram or text, one dim fluorescent tube.", line="NA43d"),
    S("S07o", "S07", "face", "cu", "work", "LA", [KW], None, "Close-up, slightly low: Kenta at the table, eyes fixed on something far down the corridor to the right, a flicker of resolve hardening his jaw, fluorescent light.",
      line="NA43", motion="A slow blink, his jaw sets, his eyes stay fixed on the far right; a long steady breath." + HOLD, expr="fear"),

    # S08 六日目の夜 — 탈출 (작업복)
    S("S08a", "S08", "estill", "ecu", "work", "EL", [], None, "Insert, ABSOLUTELY NO PEOPLE: the plain round wall clock with a BLANK white face filling the frame in near darkness, one weak light (2:58 composited).", line="NA44"),
    S("S08b", "S08", "face", "cu", "work", "HA", [KW], None, "Close-up from above: Kenta lying under the work table in near darkness, eyes wide open and fixed, holding his breath, a faint green glow on his face.",
      line="NA45", motion="One slow blink; his eyes stay fixed; he holds his breath, then a tiny controlled exhale." + HOLD, expr="fear"),
    S("S08c", "S08", "estill", "ecu", "work", "EL", [], None, "Insert through dusty office glass, ABSOLUTELY NO PEOPLE: an empty steel chair and a full glass ashtray on a desk, a thin trail of smoke, one desk lamp.", line="NA45a"),
    S("S08d", "S08", "ins", "ecu", "corr", "EL", [KW], None, "Insert: a young man's hand in a grey jumpsuit sleeve slowly pressing down the steel lever handle of a corridor door, dark, a sliver of fluorescent light." + NOFACE,
      line="NA45b", motion="The hand presses the lever down slowly in one motion and holds; the door cracks open a few centimetres; nothing else moves."),
    S("S08e", "S08", "empty", "ms", "corr", "POV", [], "CORR", "Handheld first-person view, ABSOLUTELY NO PEOPLE: the long dark concrete corridor ahead lit by a single fluorescent tube, at the far end the iron door with a blank green emergency-exit sign box.",
      fx="handheld", motion="The camera moves slowly forward down the corridor like a person creeping, handheld sway; nothing else moves."),
    S("S08f", "S08", "ins", "ecu", "stairs", "HA", [KW], "STAIRS", "Insert, high angle: a worn white sneaker stepping onto the first rusted steel step of an outdoor emergency staircase at night, grey jumpsuit cuff, faint green light." + NOFACE,
      motion="The sneaker steps down onto the step and shifts weight; nothing else moves."),
    S("S08g", "S08", "ins", "ecu", "stairs", "EL", [KW], "STAIRS", "Insert: a young man's hand in a grey jumpsuit sleeve gripping a rusted green steel railing on the dark emergency stairs, knuckles white, cold moonlight." + NOFACE,
      line="L15", vo=True, motion="The hand tightens on the railing and slides down it a little; nothing else moves."),
    S("S08h", "S08", "reuse:H2a", "ecu", "stairs", "HA", [], None, "Reuse of H2a (sneakers taking the stairs two at a time, hand on the railing, handheld).", line="NA46"),
    S("S08i", "S08", "empty", "ecu", "stairs", "LA", [], "STAIRS", "Low angle, ABSOLUTELY NO PEOPLE: the concrete wall beside the rusted emergency stairs at night, a flashlight beam sweeping across it from above.",
      motion="A flashlight beam sweeps fast across the wall from top to bottom and away; nothing else moves."),
    S("S08j", "S08", "empty", "ms", "fact", "EL", [], "FACT", "ABSOLUTELY NO PEOPLE: a small rusted steel emergency-exit door at the foot of the outdoor stairs, the dark industrial yard and a sodium lamp beyond.",
      motion="The steel door swings open outward in one motion, night air and faint light coming in; nothing else moves."),
    S("S08k", "S08", "ins", "ecu", "street_n", "HA", [KW], None, "Insert, high angle: worn white sneakers mid-stride on wet dark asphalt under a sodium lamp, grey jumpsuit cuffs, motion blur." + NOFACE,
      line="NA47", motion="One running stride: the near foot lands and pushes off, splashing a little; motion blur; nothing else."),
    S("S08l", "S08", "empty", "ws", "fact", "POV", [], None, "Handheld first-person view, ABSOLUTELY NO PEOPLE: an empty industrial road at night rushing past, sodium lamps, corrugated warehouse walls, no cars, no readable signs.",
      line="NA48", fx="handheld", motion="The camera races forward along the road, handheld shaking hard, lamps streaking past."),
    S("S08m", "S08", "face", "cu", "street_n", "SIDE", [KW], None, "Close-up from the side: Kenta stopped under a sodium lamp, bent forward with his hands on his knees, gasping, hair soaked with sweat, mouth open for breath, face in profile.",
      line="NA48a", motion="His shoulders heave with gasping breaths; sweat drips from his hair; head stays in profile." + HOLD, expr="side"),
    S("S08n", "S08", "empty", "ws", "pay", "EL", [], "PAY", "Wide, night, ABSOLUTELY NO PEOPLE: a brightly lit Japanese convenience store by an empty national road seen from the dark, its white light on the wet asphalt, a green public phone beside the entrance, the signboard blank.",
      line="NA48b", motion="The store light flickers faintly; nothing else moves; no cars."),

    # S09 공중전화 #110·店長 (작업복)
    S("S09a", "S09", "ins", "ecu", "pay", "EL", [KW], "PAY", "Insert: a sweaty trembling hand in a grey jumpsuit sleeve lifting the handset of a green Japanese public telephone outside a convenience store at night, the store light behind." + NOFACE,
      line="NA49", motion="The hand lifts the handset off the cradle in one motion and brings it up out of frame; nothing else moves."),
    S("S09b", "S09", "estill", "ecu", "pay", "HA", [], "PAY", "Insert, high angle, ABSOLUTELY NO PEOPLE: the keypad of a green Japanese public telephone, all keys completely blank, the handset cord hanging, store light (the pressed keys composited).", line="NA50"),
    S("S09c", "S09", "face", "cu", "pay", "EL", [KW], None, "Close-up: Kenta at three-quarter angle outside the store at night, the green handset pressed to his face covering his mouth, breathless, hair soaked, eyes wet and desperate, store light on half his face.",
      line="L16", vo=True, motion="His shoulders heave; his eyes squeeze shut once and open; the handset stays over his mouth." + WET_HOLD + HOLD, expr="wet"),
    S("S09d", "S09", "face", "ms", "pay", "HA", [KW], "PAY", "Medium from above and behind: Kenta in the grey jumpsuit at the green public phone, head bowed into the handset, one hand braced on the phone box, the store's white light spilling around him, his face not visible.",
      line="L16a", vo=True, motion="His bowed head and shoulders tremble; his braced hand grips the box; he does not turn." + HOLD, expr="back"),
    S("S09e", "S09", "ins", "ecu", "conb", "EL", [TE], "CONB", "Insert inside the store: a middle-aged man's hand in a white shirt sleeve with a navy vest edge holding out a plain unlabeled bottle of water across the counter toward the camera." + NOFACE,
      motion="The hand holds the bottle out and sets it down on the counter edge gently; nothing else moves."),
    S("S09f", "S09", "ins", "ecu", "pay", "EL", [KW], None, "Insert: a young man's hand in a grey jumpsuit sleeve gripping the green handset, knuckles white, trembling hard, the coiled cord." + NOFACE,
      line="NA50a", motion="The hand trembles visibly around the handset and cannot stop; nothing else moves."),
    S("S09g", "S09", "d", "ots", "conb", "EL", [TE, KW], None, "Over Kenta's blurred grey shoulder (left foreground, from behind): the night shop manager behind the counter at three-quarter angle, silver half-rim glasses, calm warm eyes, speaking quietly, bright store light.", line="L17",
      act="The shop manager tells the trembling young man quietly and warmly, in a low steady voice, that it's all right, speak slowly. Looking at him kindly across the counter, a small nod, no big gestures." + OB, expr="soft"),
    S("S09h", "S09", "face", "cu", "conb", "HA", [KW], None, "Close-up, slightly high: Kenta in the grey jumpsuit on the customer side of the counter, head bowed, a plain water bottle gripped in both hands, listening, wet hair, store light.",
      motion="His bowed head nods very slightly; the bottle trembles in his hands; a shaky breath." + WET_HOLD + HOLD, expr="wet"),
    S("S09i", "S09", "d", "cu", "conb", "EL", [TE], None, "Close-up chest-up: the shop manager behind the counter at three-quarter angle, glancing once toward the store door on his right and back, calm and firm, silver half-rim glasses, bright store light.", line="L17a",
      act="The shop manager glances once toward the door and back to the young man and tells him calmly and firmly to stay here, nobody will be let in. Protective, low voice, small nod." + OB, expr="calm"),
    S("S09j", "S09", "ins", "ecu", "conb", "HA", [KW], None, "Insert, high angle: a young man's two hands in grey jumpsuit sleeves wrapped around a plain unlabeled water bottle, knuckles white, a drop of water on the bottle, the counter edge." + NOFACE,
      motion="The hands tighten around the bottle and tremble; nothing else moves."),
    S("S09k", "S09", "d", "ots", "conb", "LA", [TE, KW], None, "Over Kenta's blurred shoulder (right foreground, from behind), slightly low: the shop manager looking past him out of the dark store window toward the night, thinking aloud, then his eyes return, silver half-rim glasses.", line="L17b",
      act="The shop manager looks out the dark window toward the night and says slowly, half to himself, a chimney, that would be the closed factory up the road; then his eyes come back to the young man, serious." + OB, expr="calm"),
    S("S09l", "S09", "face", "ms", "conb", "EL", [KW], "CONB", "Medium: Kenta in the grey jumpsuit standing at the counter inside the bright store, the water bottle held in both hands against his chest, head bowed so his face and mouth are hidden, shoulders shaking.",
      line="NA50b", motion="His shoulders shake with silent sobs; his head stays bowed; the bottle trembles." + HOLD, expr="full"),
    S("S09m", "S09", "empty", "ews", "pay", "HA", [], "PAY", "Extreme wide, high angle, ABSOLUTELY NO PEOPLE: the lone bright convenience store by the dark empty national road before dawn, the sky barely greying, no cars.",
      line="NA51", motion="The store light flickers faintly; the sky brightens almost imperceptibly; nothing else moves."),

    # S10 급습·구출 (작업복) — 赤色灯만
    S("S10a", "S10", "empty", "ws", "raid", "EL", [], "FACT", "Wide, ABSOLUTELY NO PEOPLE, NO VEHICLES: the concrete wall and rusted iron gate of the old factory at night washed by a pulsing RED rotating light reflected from off screen (red only, never blue), haze.",
      motion="The red light pulses rhythmically across the wall and gate; nothing else moves."),
    S("S10b", "S10", "face", "ms", "raid", "LA", [], "FACT", "Low angle: several dark silhouettes of investigators seen strictly from behind in front of the iron gate, flashlight beams cutting through haze toward the gate, red light pulsing, faces never visible.",
      line="L18", vo=True, motion="The flashlight beams sweep onto the gate; the silhouettes stay in place; the red light pulses."),
    S("S10c", "S10", "empty", "ms", "raid", "EL", [], "FACT", "ABSOLUTELY NO PEOPLE: the heavy rusted iron gate from inside, flashlight beams and red pulsing light bursting through the widening gap as it opens inward.",
      line="NA52", motion="The iron gate swings open inward in one motion; flashlight beams and red light pour in; dust; nothing else moves."),
    S("S10d", "S10", "ins", "ecu", "raid", "HA", [OT], None, "Insert, high angle from behind: the watchman's black-gloved hands pulled together behind his back over his black jacket, steel handcuffs being closed on his wrists by an investigator's hands in a dark sleeve." + NOFACE,
      line="NA53", motion="The handcuffs close on the wrists in one motion with a click; the hands go still."),
    S("S10e", "S10", "face", "ws", "work", "HA", [], "WORK", "High wide: the workroom under flickering fluorescent light, a dozen young men in grey jumpsuits seen from behind and above with heads bowed, flashlight beams sweeping across them, faces never visible.",
      line="NA54", motion="Flashlight beams sweep slowly across the bowed heads; nobody moves except breathing."),
    S("S10f", "S10", "face", "ms", "raid", "EL", [], "FACT", "Medium: young men wrapped in silver emergency blankets filing out through the iron gate seen strictly from behind, heads bowed, red light pulsing on the blankets, faces never visible.",
      line="NA54b", motion="They walk slowly away from the camera out through the gate, backs to the camera the whole time; the red light pulses."),
    S("S10g", "S10", "face", "cu", "raid", "HA", [], None, "Close-up from above and behind: one small thin figure under a silver emergency blanket, head bowed so low only the top of his black hair shows, thin hands holding the blanket closed, red light pulsing; the face is never visible.",
      line="NA54a", motion="The thin shoulders tremble under the blanket; the red light pulses; he does not look up."),
    S("S10h", "S10", "face", "ms", "raid", "EL", [YU], None, "Medium: Yuto with a silver emergency blanket over his grey jumpsuit standing by the gate, red light pulsing on his face, slowly raising his eyes and seeing something across the yard to the right.",
      line="NA55", motion="He raises his eyes slowly toward the right; they widen; a breath catches." + HOLD, expr="flat"),
    S("S10i", "S10", "face", "ws", "raid", "EL", [KW, YU], None, "Wide two-shot on a single axis: Kenta in the grey jumpsuit on the LEFT, a few metres from Yuto in a silver blanket on the RIGHT, facing each other across the dark yard, red light pulsing, nobody else between them.",
      motion="They stand facing each other; their chests rise and fall; the red light pulses; neither moves closer." + HOLD, expr="full"),
    S("S10j", "S10", "d", "cu", "raid", "EL", [YU], None, "Close-up chest-up: Yuto with the silver blanket on his shoulders at three-quarter angle, red light pulsing on his wet face, eyes brimming with pooled tears, throat tight, speaking with a cracked voice, NOT smiling.", line="L19",
      act="NOT smiling at any moment. Yuto, throat tight and eyes brimming, says in a cracked low voice to Kenta in front of him that he really came back; chin trembling, a swallowed breath, looking straight at Kenta." + WET_HOLD + OB, expr="wet"),
    S("S10k", "S10", "face", "cu", "raid", "LA", [YU], None, "Close-up, slightly low: Yuto listening, red light pulsing, tears pooled and glistening, lips pressed together, eyes on Kenta in front of him.",
      line="L20", vo=True, motion="His lips press tighter; a breath shudders; his eyes stay on Kenta." + WET_HOLD + HOLD, expr="wet"),
    S("S10l", "S10", "face", "cu", "raid", "EL", [YU], None, "Close-up: Yuto's face in the pulsing red light, eyes brimming, looking slightly down to the right at Kenta (NOT at the camera), lips pressed, chin trembling, NOT smiling.",
      motion="NOT smiling at any moment." + TEARS_FLOW + HOLD, expr="wet"),
    S("S10m", "S10", "estill", "ws", "news", "EL", [], None, "ABSOLUTELY NO PEOPLE: a bright plain TV news studio desk with an empty chair and a completely blank blue backdrop, no text, no logos (headline caption composited).", line="NA56"),

    # S11 아침 공원 (후드) + 「同じコンビニ」(조끼)
    S("S11a", "S11", "face", "ws", "park", "EL", [KH], "PARK", "Wide, early morning: Kenta in the grey hoodie seen strictly from behind sitting on a park bench under trees in warm low sunlight, a plain unlabeled can of coffee beside him, reaching for a smartphone lying on the bench.",
      line="L21", vo=True, motion="The phone on the bench buzzes; he picks it up in one slow motion and brings it to his far ear; his back stays to the camera." + HOLD, expr="back"),
    S("S11b", "S11", "d", "cu", "park", "EL", [KH], None, "Close-up chest-up: Kenta in the grey hoodie on the bench at three-quarter angle in warm morning light, the phone at his far ear hidden behind his head, eyes wet but not running, speaking quietly, NOT smiling.", line="L22",
      act="NOT smiling at any moment. Kenta answers his mother quietly into the phone, eyes wet, a small swallow, that yes, he is coming home now; voice soft and steady, chin trembling slightly." + WET_HOLD + OB, expr="wet"),
    S("S11c", "S11", "face", "cu", "park", "SIDE", [KH], None, "Close-up from the side: Kenta lowering the phone from his ear and looking up at the morning sky through the trees, eyes wet and glistening, lips pressed.",
      line="NA57", motion="He lowers the phone slowly and lifts his eyes to the sky; a long breath; one blink." + WET_HOLD + HOLD, expr="side"),
    S("S11d", "S11", "face", "ms", "park", "HA", [KH], "PARK", "Medium, slightly high: Kenta in the grey hoodie on the park bench, head bowed, the phone resting on his knee under his hand, warm sunlight on his hair.",
      line="NA58", motion="His head stays bowed; a slow breath; a leaf shadow moves across his shoulder." + HOLD, expr="tired"),
    S("S11e", "S11", "face", "ms", "conb", "EL", [KV], "CONB", "Medium: Kenta in the teal staff vest behind the register of the same convenience store, now with soft daylight through the glass front, wiping the counter, calm.",
      line="NA58a", motion="He wipes the counter slowly in small circles; a calm breath." + HOLD, expr="tired"),
    S("S11f", "S11", "face", "cu", "conb", "SIDE", [KV], None, "Close-up profile: Kenta in the teal vest at the register looking out through the glass front at the daylight street, a quiet unreadable look.",
      line="NA58b", motion="One slow blink; his eyes stay on the street outside; head stays in profile." + HOLD, expr="side"),
    S("S11g", "S11", "ins", "ecu", "park", "HA", [KH], None, "Insert, high angle: a young man's rough hands with healing cuts holding a plain unlabeled can of coffee on his knee, grey hoodie sleeves, warm morning sunlight." + NOFACE,
      line="NA59"),
    S("S11h", "S11", "reuse:S07c", "ws", "work", "HA", [], None, "Reuse of S07c (hundreds of phones on the warehouse floor in a flashlight circle).", line="NA60"),
    S("S11i", "S11", "reuse:S02b", "ecu", "back", "EL", [], None, "Reuse of S02b (the DM on the phone screen).", line="NA61"),
    S("S11j", "S11", "face", "cu", "park", "EL", [KH], None, "Close-up: Kenta in the grey hoodie on the bench at three-quarter angle, looking into the distance in warm morning light, calm but hollow, eyes dry now.",
      line="NA62", motion="One slow blink; his gaze stays far away; a slow breath." + HOLD, expr="tired"),
    S("S11k", "S11", "empty", "ws", "park", "LA", [], "PARK", "Low angle, ABSOLUTELY NO PEOPLE: morning sunlight through the leaves of park trees, an empty bench below, long soft shadows.",
      line="NA63", motion="Leaves sway gently in a breeze; light flickers through them; nothing else moves."),
    S("S11l", "S11", "face", "cu", "park", "HA", [KH], None, "Close-up, slightly high: Kenta looking down at the dark phone in his hand, then closing his eyes briefly, warm light.",
      line="NA64", motion="He looks down at the phone, closes his eyes slowly for a moment and opens them; nothing else moves." + HOLD, expr="tired"),
    S("S11m", "S11", "card", "ecu", "park", "EL", [], None, "Information card over a blurred warm still of the park (composited: 「警察相談専用電話　#9110」, 3 seconds visible).", line="NA65", vo=True),
    S("S11n", "S11", "empty", "ws", "park", "EL", [], "PARK", "Wide, ABSOLUTELY NO PEOPLE: a quiet park path in warm morning sun, trees, an empty bench, soft long shadows.",
      line="NA66", motion="A gentle breeze moves the leaves; light shifts slowly; nothing else moves."),
    S("S11o", "S11", "face", "ws", "park", "EL", [KH], "PARK", "Wide: Kenta in the grey hoodie seen strictly from behind walking slowly away from the bench along the park path into the low warm morning sun, backlit, a long shadow behind him.",
      line="NA67", motion="He walks slowly away from the camera into the sunlight, back to the camera the whole time, never turning around." + HOLD, expr="back"),
]

CARDS = {"H3": "彼は、なぜ消えたのか", "H4": TITLE, "S01a": "東京　深夜一時", "S06a": "一日目", "S07a": "三日目", "S07f": "六日目",
         "S11m": "警察相談専用電話　#9110"}
JA_OVERLAY = {"H0": "잠금화면 알림 3개 「即日現金」「面接なし」「時給50,000円」(애니메이션)", "H1": "「時給 50,000円」 붉은 점멸 + 「応募する」 버튼",
              "H3": "중앙 질문 카드 + 하단 「この物語は、実際の手口をもとにした再現ドラマ（フィクション）です」", "H4": "타이틀 『時給5万円の罠』",
              "S01a": "구석 시점 소자막 「東京　深夜一時」", "S02a": "DM 알림 배너", "S02b": "DM 전문(폰 70%)", "S02g": "은행 앱 残高 ¥3,217 ↔ DM 「週給　百五十万円」 매치 디졸브",
              "S02h": "봉투 「家賃のお支払いについて（再通知）」", "S02i": "봉투 「奨学金返還のご案内」", "S02k": "SNS 피드(해변·야경, 인물 뒷모습만)",
              "S02ba": "DM 조건 3가지 목록", "S02bd": "서약서 「誓約書 … 口外した場合、本人および家族が責任を負う」", "S02bi": "「応募する」 버튼(H1 매치)",
              "S03b": "검색 화면 「警察相談専用電話　#9110」", "S03c": "발신 버튼(녹색)", "S03e": "착신 화면 「母」", "S06a": "시점 소자막 「一日目」",
              "S07a": "시점 소자막 「三日目」", "S07f": "시점 소자막 「六日目」", "S07m": "벽시계 3:00", "S08a": "벽시계 2:58", "S09b": "공중전화 키패드 「１１０」",
              "S10m": "뉴스 자막 「若者二十七人を保護　闇バイト組織を一斉摘発」", "S11a": "착신 화면 「母」(벤치 폰)", "S11m": "중앙 카드 「警察相談専用電話　#9110」"}
G = {
    "conb": "a quiet Japanese convenience store at night, refrigerator hum, fluorescent light buzz, a distant automatic door chime, no voices",
    "back": "a cramped staff room at night, a fluorescent tube buzzing, a distant refrigerator hum, no voices",
    "room": "a tiny apartment at night, a ticking clock, a distant train, faint traffic far away, no voices",
    "street": "a quiet residential street at night, a distant car far away, light wind, a power line hum, no voices",
    "van": "inside a moving van on a highway at night, low engine drone, tyre roar, occasional passing cars, no voices",
    "fact": "an abandoned factory yard at night, wind through corrugated iron, a distant freight train, creaking metal, no voices",
    "work": "an abandoned factory workroom, fluorescent tubes buzzing and flickering, a ventilation fan, distant dripping water, no voices",
    "corr": "a long concrete corridor at night, a single fluorescent tube buzzing, dripping water, a distant metal creak, no voices",
    "stairs": "an outdoor steel staircase at night, cold wind, distant dogs barking, metal creaking, no voices",
    "pay": "outside a convenience store by a national road at night, store hum, a distant truck passing, crickets, no voices",
    "raid": "a factory yard at night, a distant police siren, radio static crackle, wind, no voices",
    "park": "a quiet park in the early morning, birdsong, leaves rustling, a distant train, no voices",
    "news": "a quiet TV studio room tone, air conditioning hum, no voices",
}
AMB_BY_SCENE = {"S01": "conb", "S02": "back", "S02b": "room", "S03": "room", "S04": "van", "S05": "fact", "S06": "work", "S07": "work",
                "S08": "corr", "S09": "pay", "S10": "raid", "S11": "park"}
AMB_BY_SHOT = {"H0": "room", "H1": "room", "H2a": "stairs", "H2b": "fact", "H3": "room", "H4": "street",
               "S02h": "room", "S02i": "room", "S02j": "room", "S02k": "room", "S02bb": "work", "S02bc": "van",
               "S03k": "street", "S03l": "street", "S03m": "street", "S05d": "corr", "S05e": "corr", "S05f": "corr", "S05g": "corr", "S05h": "corr",
               "S05i": "corr", "S05k": "corr", "S07e": "corr", "S07n": "corr", "S08f": "stairs", "S08g": "stairs", "S08h": "stairs", "S08i": "stairs",
               "S08j": "fact", "S08k": "street", "S08l": "fact", "S08m": "street", "S08n": "pay",
               "S09e": "conb", "S09g": "conb", "S09h": "conb", "S09i": "conb", "S09j": "conb", "S09k": "conb", "S09l": "conb",
               "S10e": "work", "S10m": "news", "S11e": "conb", "S11f": "conb", "S11h": "work", "S11i": "back"}
BGM = []  # main()에서 lock.json 장면 시각으로 계산(03_템포-오디오가이드.md 2절)

STYLE = {"NA": "Narration", "健太": "Kenta", "悠斗": "Yuto", "男": "Otoko", "店長": "Tencho", "母": "Haha", "警察官": "Keisatsu"}
STYLE_JA = {"Narration": "ナレーター", "Kenta": "健太", "Yuto": "悠斗", "Otoko": "男", "Tencho": "店長", "Haha": "母", "Keisatsu": "警察官"}
STYLE_COLOR = {"Narration": "&H00DDDDDD", "Kenta": "&H00FFFFFF", "Yuto": "&H00F0E6C8", "Otoko": "&H00C8C8E6", "Tencho": "&H00D2E6FF",
               "Haha": "&H00E6D2F0", "Keisatsu": "&H00C8C8E6"}
RATE = {"lite": 0.036, "pro": 0.108, "omni": 0.16, "kf": 0.04}
HOOK_LEN = {"H0": 2.0, "H1": 4.0, "H2a": 3.0, "H2b": 3.0, "H3": 5.0, "H4": 3.0}


def tc(sec):
    fr = int(round(sec * FPS)); s, f = divmod(fr, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}.{f:02d}"


def ass_t(sec):
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap_lines(text, limit=20):
    """휴대폰 기준(제13장 1·제17장 2): 줄당 20자 이내. libass 일본어 자동 줄바꿈 불가 → 수동 분할.
    줄 수는 최소로, 끊는 자리는 구두점 > 조사 뒤 > 글자 종류 경계 순(낱말 중간 금지), 줄 길이는 고르게."""
    n = len(text)
    if n <= limit:
        return [text]
    NOHEAD = "…—、。!?？！』」ーぁぃぅぇぉっゃゅょゎァィゥェォッャュョ"
    def kind(c):
        return "h" if "ぁ" <= c <= "ゖ" else "k" if "ァ" <= c <= "ヺ" or c == "ー" else "p" if c in "、。…!?？！』」「『" else "c"
    def cost(i):
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
    sols = [(r[0] + 12 * (k - lo), r[1]) for k in (lo, lo + 1) for r in [solve(k)] if r]
    br = [0] + min(sols)[1]
    return [text[br[k]:br[k + 1]] for k in range(len(br) - 1)]


WRAP_FIX = {}  # 자동 분할이 구절 중간에서 끊는 줄(눈 검수 후 수동 지정)


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
    for m in re.finditer(r"^(OUT\d)\b[^「\n]*「(.+)」", body, re.M):
        out[m.group(1)] = m.group(2)
    return out


def check_rules(shots, rows):
    errs = []
    prev = None
    for s in shots:
        if s["kind"] == "d" and s["angle"] in ("SIDE", "BE", "OH", "POV"):
            errs.append(f"{s['id']}: OMNI 대사 컷 각도 {s['angle']} 금지")
        if s["kind"] == "d" and s["line"] and not s["act"]:
            errs.append(f"{s['id']}: 립싱크 컷에 연기 지시(act) 없음")
        if s["kind"] == "d" and s["loc"]:
            errs.append(f"{s['id']}: 립싱크 컷에 장소 참조 — 배경은 글로(제19장 8)")
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
            if s["kind"] == "d" and rows[s["line"]]["dur"] <= 2.5 and s["id"] not in SHORT_OMNI_OK:
                errs.append(f"{s['id']}: {s['line']} {rows[s['line']]['dur']:.1f}s 짧은 대사는 VO(제12장 2)")
        # 의상 연속성(제18장 9 ⑥): 장면별 健太 의상 키 대조
        for w in s["who"]:
            k = w.split(":")[0]
            if k.startswith("KE") and s["scene"] in SCENE_WARD and k != SCENE_WARD[s["scene"]] and s["id"] not in WARD_EXC:
                errs.append(f"{s['id']}: 健太 의상 {k} ≠ 장면 {s['scene']} 기준 {SCENE_WARD[s['scene']]}")
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
        for a, b in zip(lines, lines[1:]):
            ia, ib = ss.index(a), ss.index(b)
            if ib - ia == 1 and a["kind"] == "d" and b["kind"] == "d" and a["who"][0] == b["who"][0]:
                errs.append(f"{sc}: {a['id']}→{b['id']} 같은 화자 립싱크 연속(리액션 컷 없음)")
    return errs


# 컷별 폴리 — 그 컷 영상의 동작에 맞춰 mmaudio가 소리를 만든다(제12장 10 ★42·제19장 10). 03_템포-오디오가이드 3절은 sfx_timeline.json(화면 밖 소리)
FOLEY = {
    "H1": "a thumb hovering over a phone screen, a faint electric hum", "H2a": "sneakers pounding down rusted steel stairs fast, a hand sliding on a metal railing, hard breathing",
    "H2b": "a heavy iron gate swinging shut with a deep metallic boom and a long rattle", "S01a": "goods being straightened on a shelf, a soft plastic rustle",
    "S01c": "plastic-wrapped rice balls being lined up on a shelf, soft crinkles", "S02a": "a smartphone vibrating once on a steel table, then picked up",
    "S02d": "a faint phone screen tap sound, a hum", "S02k": "a thumb swiping on a glass phone screen", "S02bi": "a single soft phone button tap",
    "S03c": "a finger hovering above glass, silence, a faint hum", "S03d": "a smartphone being turned face down onto a bedsheet, a soft thud",
    "S03e": "a smartphone vibrating against a bedsheet, picked up", "S03i": "a folded T-shirt being put into a backpack, soft cloth and zipper",
    "S03k": "slow footsteps on a quiet night street, sneakers on asphalt", "S03m": "a van sliding door slammed shut, a heavy thud and latch",
    "S04a": "inside a van on a highway at night, low engine drone and tyre roar", "S04d": "a smartphone and a plastic card set down into a plastic basket",
    "S04f": "an elastic eye mask being pulled on, cloth rustle", "S05a": "wind over a factory yard at night, a sodium lamp buzzing",
    "S05c": "several people walking slowly over gravel toward a gate", "S05d": "footsteps echoing in a long concrete corridor, dripping water",
    "S05e": "fingertips brushing rusted metal, flakes falling", "S05j": "a heavy iron gate closing with a deep boom, a chain rattling, then a low drone",
    "S06a": "fluorescent tubes buzzing and flickering in a large empty room", "S06c": "small paper bankbooks being sorted on a steel table",
    "S06d": "packing tape being pressed onto a cardboard parcel", "S06f": "slow heavy footsteps walking away on concrete", "S06i": "a cardboard carton sliding along a steel table",
    "S06j": "slow breathing on a concrete floor, a fluorescent hum", "S07e": "a flashlight beam passing, distant footsteps in a corridor",
    "S07l": "a door opening and a man walking out, a wall clock ticking", "S08d": "a steel door lever pressed down slowly, a faint click",
    "S08e": "very slow careful footsteps in a dark corridor, a fluorescent tube buzzing", "S08f": "a sneaker stepping onto a rusted steel step, a creak",
    "S08g": "a hand gripping a rusted metal railing, a creak", "S08i": "a flashlight beam sweeping, distant shouting far away", "S08j": "a steel emergency door swinging open, night wind",
    "S08k": "running sneakers splashing on wet asphalt", "S08l": "running fast along an empty road at night, heavy breathing, wind rushing",
    "S08m": "gasping for breath after running, a sodium lamp buzzing", "S09a": "a public telephone handset lifted off its cradle, a dial tone",
    "S09e": "a plastic water bottle set down on a counter", "S09f": "a trembling hand on a telephone handset, breathing", "S09l": "quiet sobbing breaths inside a store, a refrigerator hum",
    "S10a": "a police siren pulsing far away, wind", "S10b": "flashlight beams, radio static crackle, boots on gravel", "S10c": "an iron gate swinging open, boots rushing in, radio static",
    "S10d": "steel handcuffs clicking shut", "S10f": "many people walking slowly on gravel, emergency blankets rustling", "S11a": "a smartphone vibrating on a wooden bench, picked up, birdsong",
    "S11k": "leaves rustling in a morning breeze, birdsong", "S11o": "slow footsteps walking away on a gravel park path, birdsong",
}

BGM_GAIN = 2.3  # bento 1차 검수 실측(배경 −32dB → ×2.3) 계승


def build_bgm(lock):
    """03_템포-오디오가이드.md 2절 감정 곡선(탐욕→불안→공포→흥분→카타르시스→여운) — 장면 경계, 구간 간격 1.0초 이상(제11장 5).
    후크 0~3.5초는 BGM 없음(드론·알림·심장 박동은 sfx_timeline). 공포 구간 곡 사이 공백은 드론(sfx)이 메운다."""
    sc = {s["id"]: s["start"] for s in lock["scenes"]}; ad1, ad2 = (a["at"] for a in lock["ads"])
    segs = [
        (3.5, 19.0, 0.30, "dark mysterious electronic pulse, low synth drone with a ticking clock texture, slow, suspenseful, Japanese crime documentary opening, instrumental, no vocals"),
        (20.0, sc["S02"] - 0.6, 0.34, "cold urban ambient, sparse single piano notes over a soft synth pad, late night city loneliness, minimal, instrumental, no vocals"),
        (sc["S02"] + 0.5, sc["S03"] - 0.6, 0.36, "cold urban ambient with a slowly growing low pulse, temptation and unease, sparse piano, minimal electronic, instrumental, no vocals"),
        (sc["S03"] + 0.5, ad1 - 0.8, 0.30, "low string tremolo with a slow heartbeat-like pulse, quiet dread, suspense, sparse, instrumental, no vocals"),
        (ad1 + 1.0, sc["S06"] - 0.6, 0.38, "deep sub-bass drone with slow metallic scraping textures and a distant low hit, claustrophobic dread, dark ambient, no melody, instrumental, no vocals"),
        (sc["S06"] + 0.5, ad2 - 0.8, 0.40, "rising dark drone with irregular electric buzz pulses and low string swells, fear and despair, slowly intensifying, dark ambient, instrumental, no vocals"),
        (ad2 + 1.0, sc["S09"] - 0.6, 0.42, "accelerating heartbeat percussion building into hard hybrid trailer drums, an escape chase at night, relentless, instrumental, no vocals"),
        (sc["S09"] + 0.5, sc["S10"] - 0.6, 0.32, "percussion fading into a single low sustained string note, trembling breath, fragile hope, sparse, instrumental, no vocals"),
        (sc["S10"] + 0.5, sc["S11"] - 0.6, 0.42, "radio static texture into pounding percussion hits, then resolving into a warm rising orchestral chord of relief, rescue, instrumental, no vocals"),
        (sc["S11"] + 0.5, None, 0.34, "warm gentle solo piano theme with soft strings, early morning light, quiet relief and lingering sadness, Japanese drama ending, instrumental, no vocals"),
    ]
    for a, b in zip(segs, segs[1:]):
        assert b[0] - a[1] >= 1.0, f"BGM 구간 간격 {b[0] - a[1]:.1f}s < 1.0s"
    return segs


def spk_who(spk, s):
    """VO 컷 어깨 너머 앞 인물 = 화자(健太는 장면 의상으로)."""
    if spk == "健太":
        return SCENE_WARD.get(s["scene"], "KEH") + ":" + SCENE_WARD.get(s["scene"], "KEH")
    return {"男": OT, "悠斗": YU, "店長": TE}.get(spk)


VO_OFFSCREEN_OK = {"H2b", "S08g", "S10b"}  # 男 L00(철문 실루엣)·L15(멀리서 고함)·警察官 L18(빛줄기 너머) — 의도된 화면 밖 외침(제18장 7 ②)
PROP_HELD_OK = set()
VO_OTS_SKIP = {"S03e", "S03g", "S04c", "S04d", "S06f", "S06l", "S06m", "S07g", "S09c", "S09d", "S11a"}
SHORT_OMNI_OK = {"S10j"}  # L19 「本当に、来たんだな」 2.4s — 감정 정점이라 얼굴 립싱크 유지(웃음 변환 시 S10i 투샷 위 VO로 교체, 제18장 4 ③)
# 화자가 화면 안에서 입을 가린 컷(뒷모습·고개 숙임·수화기·옆모습)·전화 VO(母)는 어깨 너머 리버스숏을 만들지 않는다


def main():
    global BGM
    lock = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
    BGM = build_bgm(lock)
    assert len(FOLEY) >= 20, "컷별 폴리(FOLEY)가 비었다 — 효과음표를 생성 설정으로 옮길 것(제15장 22·제19장 10)"
    assert os.path.exists(os.path.join(PROD, "sfx_timeline.json")), "효과음 타임라인(sfx_timeline.json) 없음 — PHASE 6 믹스 소스(제19장 10)"
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
    for s in SHOTS:
        t = s["subject"].lower()
        if s.get("vo") and s["line"] in rows and s["id"] not in VO_OFFSCREEN_OK:
            sp = spk_who(rows[s["line"]]["spk"], s)
            if sp and sp.split(":")[0] not in {w.split(":")[0] for w in s["who"]}:
                errs.append(f"{s['id']}: VO 화자 {rows[s['line']]['spk']}가 화면에 없음 — 화자(입 가림)·화자 어깨 너머 컷으로(제19장 13 ②)")
        if s["kind"] == "ins" and s["who"] and s["id"] not in PROP_HELD_OK and re.search(r"\b(bowl|bento|box|tray|plate|basket|parcel|carton)\b", t) and not re.search(r"\b(on the|lying|rests|sits on|bottom of)\b", t):
            errs.append(f"{s['id']}: 사람 참조 + 받침면 없는 소품 인서트 — 공중 부양 위험(인물 참조 빼고 받침면 부감, 제19장 13 ①)")
        if re.search(r"walk(s|ing)? (out|away)|walk(s|ing)? out through|filing out", t) and s.get("expr") not in ("back",) and s["who"]:
            errs.append(f"{s['id']}: 나가는 컷은 expr='back'(등이 카메라 쪽 키프레임, 제19장 13 ③)")
        if s["kind"] in ("face", "d") and s["who"] and re.search(r"\b(runs|running|sprint)\b", t.replace("not running", "")) and "stopped" not in t:
            errs.append(f"{s['id']}: 사람 달리기 i2v 금지 — 발·손·문·POV로(02 §6 경고 5)")
        if s["kind"] == "face" and not s["who"] and not re.search(r"silhouette|from behind|never visible|hidden", t):
            errs.append(f"{s['id']}: 군중 컷(who=[])은 실루엣·뒷모습·얼굴 비노출 문장 필수")
    body_tags = {t for t, x in rows.items() if x["scene"].startswith("S") and x.get("start") is not None}
    used = [s["line"] for s in SHOTS if s["line"] and s["scene"] != "H"]
    if sorted(used) != sorted(body_tags):
        errs.append(f"대사 줄 사용 불일치: 빠짐 {sorted(body_tags - set(used))}, 중복·초과 {sorted(set(u for u in used if used.count(u) > 1) | (set(used) - body_tags))}")
    for s in SHOTS:
        for w in s["who"]:
            key = w.split(":")[0]
            if s["expr"] and (key, s["expr"]) in EXPR and not os.path.exists(os.path.join(ROOT, EXPR[(key, s["expr"])])):
                errs.append(f"{s['id']}: 셀 없음 {EXPR[(key, s['expr'])]}")
            if s["expr"] and w == s["who"][0] and (key, s["expr"]) not in EXPR and s["expr"] not in ("full",):
                errs.append(f"{s['id']}: 표정 칸 없음 ({key}, {s['expr']})")
        if s["loc"] and not os.path.exists(os.path.join(ROOT, LOC[s["loc"]])):
            errs.append(f"{s['id']}: 셀 없음 {LOC[s['loc']]}")
    ids_all = [s["id"] for s in SHOTS]
    assert len(ids_all) == len(set(ids_all)), "컷 ID 중복"
    for s in SHOTS:
        if s["kind"].startswith("reuse:") and s["kind"][6:] not in ids_all:
            errs.append(f"{s['id']}: 재사용 원본 {s['kind'][6:]} 없음")
    if errs:
        raise SystemExit("규칙 위반:\n  " + "\n  ".join(sorted(set(errs))))

    starts, t = {}, 0.0
    for s in SHOTS:
        if s["scene"] == "H":
            starts[s["id"]] = t; t += HOOK_LEN[s["id"]]
    assert abs(t - lock["hook"]) < 1e-6, f"후크 길이 {t} ≠ lock {lock['hook']}"
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
            if s["lens"] == "ots":
                comp = ("Over-the-shoulder two-shot: the listener's blurred shoulder and back of the head at the near foreground edge, the speaker beyond "
                        "facing the listener at 30 to 40 degrees from the camera axis, the speaker's face at least one third of the frame height, "
                        "the speaker's mouth closed. Exactly two people, no extra people. FOREGROUND IDENTITY LOCKED: the foreground person is the listener described.")
            else:
                comp = ("FRAMING FIRST — TIGHT MEDIUM CLOSE-UP from mid-chest up, the speaker alone, head near the top edge, face about one third of the "
                        "frame height, turned 30 to 40 degrees from the camera axis (never straight at the camera, never full profile), mouth closed, "
                        "the background only a blurred suggestion of the place. Exactly ONE person, no foreground person, no extra people.")
        elif s.get("ots"):
            comp = ("Over-the-shoulder reverse shot: the SPEAKER's blurred back of the head and shoulder at the near foreground edge (face and mouth "
                    "NOT visible); the LISTENER beyond faces the speaker at 30 to 40 degrees from the camera axis, eyes on the speaker, NOT looking "
                    "at the camera, the listener's face at least one third of the frame height, mouth closed. Exactly two people, no extra people. "
                    "FOREGROUND IDENTITY LOCKED: the foreground person is the speaker described.")
        elif s["kind"] == "face" and not s["who"]:
            comp = "Several people only as dark silhouettes, backs or bowed heads — faces NEVER visible, no recognizable features, no extra detail on them."
        elif s["kind"] in ("empty", "estill") or (s["kind"] == "ins" and not s["who"]):
            comp = "Completely unpopulated: no people, no hands, no faces."
        else:
            comp = f"Exactly {n} {'person' if n == 1 else 'people'} (or their hands) as described, no extra people."
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/{SKIT}-keyframes/{sid}-1.png"
        kf_prompt = None
        if keyframe:
            low = (s["subject"] + " " + (s["act"] or "")).lower()
            real = " ".join(x for x, keys in ((TEARS, ("tear", "sob", "cry", "wet eyes", "eyes wet", "wet face", "brimming", "wet and", "desperate")), (SWEAT, ("sweat", "gasping")))
                            if any(k in low for k in keys) or (s["expr"] == "wet" and x == TEARS))
            if TEARS in real and "spills over" in (s.get("motion") or ""):
                real = real.replace(TEARS, TEARS_POOL)
            glasses = " ".join(GLASSES[w.split(":")[0]] for w in s["who"] if w.split(":")[0] in GLASSES)
            kf_prompt = " ".join([PRESET + ".", s["subject"], ("Characters (IDENTITY FIRST): " + " | ".join(ids) + ".") if ids else "", glasses, real,
                                  f"Camera: {ANGLE[s['angle']]}, {LENS[s['lens']]}.", f"Lighting: {LIGHT[s['light']]}.", comp, PLAIN,
                                  f"Negative: {NEGATIVE}."]).strip()
            cost["kf"] += 1
        tier = {"d": "omni", "face": "lite", "empty": "lite", "estill": "still", "card": "card"}.get(s["kind"], "reuse")
        if s["kind"] == "ins":
            tier = "lite" if s["motion"] else "still"
        if s["kind"] == "d" and not s["line"]:
            tier = "lite"
        gen = 10 if d > 5.0 else 5
        item = {"prompt": "", "duration": gen}
        if tier == "lite":
            item["prompt"] = ("Static, locked off camera. Motion: " + (s["motion"] or "Subtle natural motion only: breathing, one blink.") +
                              " Keep the exact faces, wardrobe, props and lighting of the first frame. Head turns under 20 degrees. "
                              "No walking toward the camera, no new people, no text, no readable signs.")
            item["image"] = keyframe; live[sid] = s["motion"]
            if sid in PRO_TEARS:
                item["i2v_model"] = "fal-ai/bytedance/seedance/v1/pro/image-to-video"; item["i2v_resolution"] = "1080p"; item["hero_takes"] = 2
                cost["pro"] += gen * 2
            else:
                cost["lite"] += gen
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
    budget = round((cost["lite"] * RATE["lite"] + cost["pro"] * RATE["pro"]) * 1.25, 2)

    tts_order = [dict(x) for x in lock["lines"] if x.get("start") is not None and x["scene"] != "OUT"]
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
        parts = chunks(texts[x["tag"]])
        tot = sum(len(q) for q in parts); t = s0
        for k, q in enumerate(parts):
            t1 = e0 if k == len(parts) - 1 else t + (e0 - s0) * len(q) / tot
            events.append((t, t1, st if k == 0 else st + "_c", STYLE_JA[st], q)); t = t1
    events.sort(key=lambda e: e[0])
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
    for e in events:
        assert e[4].count("\\N") <= 1 and max(len(q) for q in e[4].split("\\N")) <= 20, f"자막 규격 위반(2줄·20자): {e[4]}"
    for e in events:
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{e[4]}")
    os.makedirs(os.path.join(ROOT, "subs"), exist_ok=True)
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    os.makedirs(os.path.join(ROOT, "scripts", "storyboard"), exist_ok=True)
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_yamibaito_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT, "preset": PRESET,
               "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"], "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_yamibaito_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, wardrobe, "
                         "props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_yamibaito_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (ElevenLabs 확정본, 제20장 7 발성 디렉션).",
        "default_voice": "cached-typecast", "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Narration"], "silent_styles": ["Caption", "HookLine", "Title"] + [n + "_c" for n in STYLE_COLOR],
        "output_size": [1920, 1080], "fit": "crop", "scene_durations": durations, "transitions": [0.0] * len(durations),
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d" and s["line"]],
        "omnihuman_prompts": {str(idx[k]): v for k, v in omni_prompts.items()},
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0, "legacy_lipsync": False,
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.6, "duck_db": 5, "voice_reverb": 0.08, "ambience_prompts": [x["ambience"] for x in sb],
        "foley_prompts": {str(idx[k]): v for k, v in FOLEY.items() if k in idx}, "foley_model": "fal-ai/mmaudio-v2", "foley_volume": 0.6,
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": s, "end": round(main_end, 2) if e is None else e, "volume": round(v * BGM_GAIN, 3), "prompt": p} for s, e, v, p in BGM],
        "_발성디렉션": "제20장 7 ②: 장면별 리버브(실내 S01·S04~S07 0.14 + 근접 EQ / 원룸 S02·S03 0.08 / 야외 S08·S09·S11 0.04 + 바람 베드) · 母 전화 로우패스 3.4kHz는 finalize_yamibaito.py에서 장면 구간별로 적용(generate_audio voice_reverb는 전역 0.08).",
        "_후크": "0~3.5초 BGM 없음: 알림음 3연타·심장 박동·드론은 sfx_timeline.json(finalize 믹스). L00 = L08 녹음 재사용(build_tts SAME_AS).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["lite"] * RATE["lite"] + cost["pro"] * RATE["pro"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    md = [f"# 『{TITLE}』 PHASE 3 샷 리스트 (B안 표준)", "",
          f"> `scripts/build_yamibaito_phase3.py` 자동 생성(손 수정 금지). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " + ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock['ads']) + ".",
          "> 자동 검사 통과: 연속 같은 구도 0 · 같은 화자 립싱크 연속 0 · 장면당 사이즈 4종 이상 · 돌리줌 1회 · 더치 ≤2회 · OMNI 정면~45°·장소 참조 없음 · 짧은 대사(≤2.5s) VO · 화자-화면 일치 · VO 화자 화면 안(외침 3줄 예외) · 소품 부양 · 나가는 컷 뒷모습 · 달리기 전신 0 · 健太 의상 연속성 · 대사 줄 전부 배치 · 컷 길이 · OMNI 8초 이하.", "",
          "## 비용 추산 (실측 단가)", "", "| 항목 | 수량 | 단가 | 금액 |", "|---|---|---|---|",
          f"| 키프레임 | {cost['kf']}장 | 0.04 | {cost['kf'] * RATE['kf']:.2f} |",
          f"| i2v lite (사람·손·배경) | {cost['lite']}초 | 0.036 | {cost['lite'] * RATE['lite']:.2f} |",
          f"| i2v pro 1080p (悠斗 눈물 2테이크) | {cost['pro']}초 | 0.108 | {cost['pro'] * RATE['pro']:.2f} |",
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
    wardrobe_table(sb)
    emotion_table(sb, live)
    print(f"완료: 컷 {len(SHOTS)}개, 본편 {tc(main_end)}, 방식 {dict(tiers)}, 1차 비용 약 {total_cost:.2f}달러 (i2v budget {budget}), 앵글 {dict(ang)}")


def wardrobe_table(sb):
    """제18장 9 ⑥ 의상 대조 시트 — 인물별 컷 의상 키를 장면 순으로."""
    rows = []
    for x in sb:
        who = [r.split("/")[-1].rsplit("-", 1)[0] for r in x["refs"] if "/loc-" not in r and "/prop-" not in r]
        if who:
            rows.append(f"| {x['scene']} | {x['id']} | {', '.join(who)} | {x['tier']} |")
    md = ["# 의상·인물 참조 대조 (build_yamibaito_phase3.py 생성)", "", "> 健太 의상: kenta-conv(조끼) S01·S02·S11e·f / kenta-hoodie(후드) S02 원룸·S02b~S05·S11 / kenta-work(작업복) S06~S10. 어긋나면 생성기가 멈춘다.", "",
          "| 장면 | 컷 | 참조 셀 | 방식 |", "|---|---|---|---|"] + rows
    open(os.path.join(PROD, "17_의상대조.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")


EMO_WORDS = {"sad": ("tear", "cry", "sad", "weak", "chok", "break", "holding back", "trembl", "grief", "crack", "afraid", "fear", "despair", "hopeless", "wet"),
             "happy": ("smil", "laugh", "bright", "warm", "happy", "cheer", "light"),
             "tonedown": ("low", "cold", "flat", "quiet", "calm", "steady", "firm", "hushed", "whisper", "menace", "detached", "slow", "self-mocking", "bitter", "forced")}
EMO_OK = {"sad": ("tear", "wet", "cry", "tremb", "chok", "crack", "swallow", "fear", "hopeless", "squeeze", "brimming", "desperate", "shudder"),
          "happy": ("smile", "warm", "kind", "light", "nod"),
          "tonedown": ("low", "flat", "quiet", "calm", "steady", "firm", "whisper", "slow", "dead", "cold", "bitter", "forced", "barely", "murmur", "half to himself", "self-mocking"),
          "normal": ()}
EMO_BAD = {"sad": ("grin", "laughs"), "happy": ("sob", "grief"), "tonedown": ("shout", "laughs loudly")}


def emo_of(tone):
    t = (tone if isinstance(tone, str) else " ".join(map(str, tone))).lower()
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
        rows.append(f"| {state} | {x['id']} | {tag} | {how} | {tone} → {emo} | {memo} | {x['subject'][:70]} | {act[:90]} |")
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_yamibaito_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않음(키프레임·동작 문장을 고친다). 👂 = 목소리만(듣는 사람·손 컷), 리액션이 들은 말에 맞는지 키프레임 검수에서 본다.", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 톤 → 감정 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")
    assert warn == 0, "감정 일치표 경고가 있다 — 키프레임·동작 문장을 고친 뒤 생성 진행(제10장 7)"
    return warn


if __name__ == "__main__":
    main()
