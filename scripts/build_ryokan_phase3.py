#!/usr/bin/env python3
"""『老舗旅館の嫁』(ryokan) PHASE 3 샷 리스트 Lock 생성기 — 일본어판 #03 (build_ryokan_phase3.py 구조 계승).

입력(동결본, 손으로 옮겨 적지 않는다):
  productions/ryokan-yome-ja/lock.json        PHASE 1 Lock(실측 줄 타임코드·장면 경계·광고 지점)
  productions/ryokan-yome-ja/00_script_ja.md  대본 v2.1(자막 원문)
  assets/auditions/ryokan-tts/lineNNN.mp3      확정 음성(앞뒤 무음을 잘라 assets/audio-overrides/ryokan/로 복사)
출력:
  scripts/storyboard/ryokan.json   샷 스펙(PHASE 4 키프레임·PHASE 5 입력)
  scripts/scenes/ryokan.json       장면 생성 설정(i2v·override_required·budget_usd·히어로 컷)
  scripts/audio/ryokan.json        조립·오디오(장면 길이·OmniHuman·BGM·효과음)
  subs/ryokan.ass                  일본어 자막(대사 65줄 + 카드·강조 자막)
  productions/ryokan-yome-ja/07_샷리스트.md, 02_카메라앵글설계.md
규칙: CLAUDE.md 제0~9장, 03_시네마규격.json(B안), 제8장 자동 검사. 아웃트로(진행자 4줄)는 PHASE 6 append_outro로 별도.
사용법: python3 scripts/build_ryokan_phase3.py
"""
from prompt_format import compose_keyframe, compose_motion, check_motion  # 제12장 1
import collections
import json
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "ryokan-yome-ja")
sys.path.insert(0, PROD)
from build_tts import load_lines, SAME_AS  # noqa: E402

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
    S("S01f", "S01", "card", "ews", "genkan_night", "LA", [], "TSK_GENKAN", "Title card over the blurred night entrance."),
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
    S("S03b2", "S03", "sil", "ws", "day", "EL", ["WAKANA", "FAMILY"], "TSK_GENKAN_REV",
      "Wide view from the far end of the corridor: Wakana in apron walking away from the camera toward the bright entrance beside two guests seen from behind, suitcases rolling, her back to the camera.",
      motion="They walk slowly away toward the entrance light; no one turns around."),
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
    S("S05f2", "S05", "estill", "ecu", "room_night", "EL", [], "ROOM_LAMP",
      "Extreme close-up of the paper floor lamp glowing faintly in the dark room, its light fading as if being switched off."),
    # ── S06 현관 공개 굴욕
    S("S06a", "S06", "sil", "ews", "day", "EL", ["TOMIKO", "MAI", "GUESTS", "WAKANA"], "TSK_GENKAN_THRU",
      "Wide view through the doorway: in the foreground Tomiko in plum kimono and Mai in a pink cherry-blossom kimono bowing gracefully to a group of guests seen from behind; far down the corridor at the very back, tiny in frame, Wakana in apron on her knees wiping the floor.",
      motion="Mai completes a slow graceful bow; the guests stay with their backs to the camera; the tiny figure at the far end keeps wiping. Nobody walks toward the camera.", hero=True),
    S("S06b", "S06", "d", "cu", "day", "EL", ["TOMIKO"], "TSK_COUNTER",
      "Chest-up close-up of Tomiko with a polished hostess smile, gold-rimmed glasses, chin slightly raised, the counter and corridor blurred behind.", line="line019", expr="smile"),
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
    S("S07c2", "S07", "react", "cu", "press", "EL", ["MAI"], "ZASHIKI_HEAD",
      "Chest-up of Mai glancing sideways with a small smug smile, red lipstick, hard top light, the scroll soft behind.", expr="sulk"),
    S("S07d", "S07", "d", "cu", "press", "HA", ["WAKANA"], "ZASHIKI_DOOR",
      "High angle chest-up of Wakana at the lowest seat, brows drawn together, careful and uncertain, the sliding door soft behind.", line="line024", expr="hurt"),
    S("S07e", "S07", "d", "cu", "press", "LA", ["MAI"], "ZASHIKI_HEAD",
      "Low angle chest-up of Mai in the pink cherry-blossom kimono, red lips in a scornful sneer, eyes half-lidded, hard top light, hands out of frame.", line="line025", expr="sneer"),
    S("S07f", "S07", "d", "cu", "press", "EL", ["MAI"], "ZASHIKI_HEAD",
      "Low angle chest-up of Mai looking down at the camera with a lazy condescending smile, chin raised, red lipstick, the scroll soft behind.", line="line026", expr="sneer"),
    S("S07g", "S07", "ins", "ecu", "press", "HA", ["MAI"], "ZASHIKI_TABLE",
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
      motion="She lifts her head a few degrees and a faint calm smile forms slowly; one slow blink. No other movement (the slow zoom is added in editing).", hero=True),
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
    S("S08b2", "S08", "estill", "ecu", "day", "EL", [], "P_FILE",
      "Overhead extreme close-up: a plain white envelope lying beside the blank navy binder on the wooden desk, morning light, nothing written."),
    S("S08c", "S08", "ins", "ecu", "day", "OH", [], "P_FILE",
      "Overhead extreme close-up: a woman's hand lifting away from the blank navy binder cover, a plain white envelope laid beside it on the wood. No face.", line="line034"),
    S("S08c2", "S08", "empty", "ws", "day", "EL", [], "ROOM_WINDOW",
      "Wide view of the empty tatami room at morning: the small window with the curtain open, soft light on the mats, the desk with the binder at the frame edge. Completely unpopulated.",
      motion="Light shifts gently; a curtain edge stirs. No people."),
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
    S("S10a2", "S10", "gfx", "ecu", "day", "HA", [], "TSK_COUNTER",
      "High angle extreme close-up: a smartphone held over the dark counter, its screen glowing plain blank white, a woman's hand with a gold bangle holding it. No face."),
    S("S10b", "S10", "sil", "ws", "day", "EL", ["FAMILY", "MAI"], "TSK_GENKAN",
      "Wide view of the entrance hall: a Western family and a Japanese couple seen from behind and in soft focus facing each other across the raised step, one hand holding up a room key, Mai small behind the counter with her hands raised helplessly.", line="line038", fx="handheld",
      motion="The two groups gesture at each other with small movements; Mai raises her hands a little. Faces stay unrecognizable. No one approaches the camera.", hero=True),
    S("S10b2", "S10", "ins", "ecu", "day", "OH", [], "TSK_COUNTER",
      "Overhead extreme close-up: two different hands reaching for the same old-fashioned room key with a plain blank wooden tag on the dark counter. No faces."),
    S("S10c", "S10", "sil", "ms", "day", "SIDE", ["MAI", "FAMILY"], "TSK_COUNTER",
      "Over-the-shoulder medium shot from behind a guest's shoulder toward Mai behind the counter, her head bowed in a flustered apology, hair falling forward, her mouth hidden by the angle.", line="line039",
      motion="Mai bows her head a few degrees lower and lifts it; the shoulder in the foreground stays still."),
    S("S10d", "S10", "gfx", "ecu", "office_night", "EL", [], "TSK_OFFICE",
      "Extreme close-up of an open laptop screen on the small office desk glowing plain blank white-blue, the desk lamp beside it, the room dim. No people.", line="line040"),
    S("S10d2", "S10", "estill", "ecu", "office_night", "HA", [], "TSK_OFFICE",
      "High angle extreme close-up: a woman's hand with a gold bangle hovering uncertainly over a laptop keyboard, the screen glow on the keys. No face."),
    # ── S11 메밀차 사고 → 리뷰 → 고함 → 비
    S("S11a", "S11", "ins", "ecu", "day", "HA", [], "ZASHIKI_TABLE",
      "High angle extreme close-up: a steaming cup of brown tea placed on a lacquered meal tray beside small dishes, a female server's hand withdrawing. No face.", line="line041"),
    S("S11a2", "S11", "estill", "ecu", "day", "EL", [], "ZASHIKI_TABLE",
      "Overhead extreme close-up: a lacquered meal tray with small ceramic dishes, chopsticks and a steaming tea cup, soft daylight, nothing written."),
    S("S11b", "S11", "ins", "ecu", "day", "OH", [], "ZASHIKI_TABLE",
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
    S("S12c", "S12", "d", "cu", "hoff_day", "EL", ["SAKURAI"], "HOFF_DESK",
      "Chest-up close-up of Sakurai with a mischievous teasing half-smile, one eyebrow slightly raised, pearl earrings catching the light.", line="line048", expr="wink"),
    S("S12d", "S12", "react", "cu", "hoff_day", "HA", ["WAKANA_B"], "HOFF_DESK",
      "Chest-up close-up of Wakana in the navy kimono, lips pressed as if holding back a laugh, eyes glistening wet at the lower lids but no tears running, soft daylight.", line="line049", expr="faint"),
    S("S12d2", "S12", "ins", "ecu", "hoff_day", "HA", [], "P_TEA",
      "High angle extreme close-up: two celadon tea cups on a dark lacquered tray, steam rising, soft daylight. No hands."),
    # ── S13 성수기 초일: 천의 전화 → 수화기 낙하 → 2,000만 엔 → 휴지통의 인수인계서 → 빈 현관
    S("S13a", "S13", "sil", "ms", "day", "SIDE", ["TOMIKO"], "TSK_COUNTER",
      "Medium shot from the side at the reception counter: Tomiko in plum kimono lifting an old cream telephone handset to her ear, seen in profile from behind the shoulder, a second phone light blinking on the counter.", line="line050",
      motion="She lifts the handset to her ear and straightens; the small light on the phone keeps blinking. No turning to the camera."),
    S("S13a2", "S13", "estill", "ecu", "day", "HA", [], "TSK_COUNTER",
      "High angle extreme close-up: an old cream desk telephone on the dark counter, a small red light blinking, the brass bell beside it."),
    S("S13a3", "S13", "empty", "ws", "day", "EL", [], "TSK_CORRIDOR",
      "Wide view down the long polished corridor of the inn in daylight, every sliding door closed, completely unpopulated.",
      motion="Light shifts gently along the polished floor. No people."),
    S("S13b", "S13", "sil", "ms", "taipei", "SIDE", ["CHEN"], "TAIPEI",
      "Medium shot from directly behind an office chair: a man in a white shirt seen only from the back, holding a telephone handset to his ear, hard stripes of sunlight through venetian blinds across the desk and his shoulders. His face is never visible.", line="line051",
      motion="His shoulders rise slightly; he does not turn around at all.", hero=True),
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
      motion="He lowers the handset a few centimetres at the end; otherwise still. No turning."),
    S("S13g", "S13", "face", "ecu", "day", "HA", [], "TSK_COUNTER",
      "High angle extreme close-up: an old cream telephone handset slipping out of an aged woman's hand toward the dark wooden counter, the coiled cord pulling taut. Only the hand and handset are visible.", fx="dollyzoom",
      motion="Slow motion: the handset slips from the fingers, drops and swings on its coiled cord against the counter front. The hand stays open and still. No face.", hero=True),
    S("S13h", "S13", "gfx", "ecu", "office_night", "EL", [], "TSK_OFFICE",
      "Overhead extreme close-up: an open ledger book on the small office desk with plain blank ruled pages, a red pen laid across it, warm lamp light. Every page is blank.", line="line056"),
    S("S13i", "S13", "ins", "ecu", "office_night", "HA", [], "TSK_OFFICE",
      "High angle extreme close-up: an aged woman's hand pressing a red pen hard onto a blank ledger page, the pen tip bending, lamp light. No face, no written characters.", line="line057"),
    S("S13i2", "S13", "estill", "ecu", "office_night", "OH", [], "TSK_OFFICE",
      "Overhead extreme close-up: the open ledger on the desk with a red pen resting across blank ruled pages, lamp light pooling. No hands."),
    S("S13j", "S13", "face", "ecu", "office_night", "EL", [], "TSK_OFFICE",
      "High angle extreme close-up at night: an aged woman's hand in a plum kimono sleeve lifting a crumpled plain navy binder out of a steel wastebasket, the binder falling open to a page with a thick red marker band and soft illegible grey lines. No face.", line="line058",
      motion="The hand lifts the binder slowly out of the bin and holds it open; a page settles. No face appears. No readable letters.", hero=True),
    S("S13j2", "S13", "ins", "ecu", "office_night", "HA", [], "P_FILE_OPEN",
      "High angle extreme close-up: the navy binder lying open on the desk at a page of soft illegible grey lines with a thick red marker band, lamp light. No hands, no readable letters."),
    S("S13j3", "S13", "estill", "ecu", "office_night", "OH", [], "TSK_OFFICE",
      "Overhead extreme close-up: the empty steel wastebasket beside the desk leg, crumpled papers inside, dim lamp light."),
    S("S13k", "S13", "empty", "ews", "day", "EL", [], "TSK_GENKAN",
      "Wide view of the old inn's entrance hall in flat daylight, completely empty: the plain indigo noren stirring in the wind, the raised step, the dark counter with nobody behind it, the long corridor silent.", line="line059",
      motion="The noren sways slowly in the wind; the hall stays empty. No people.", hero=True),
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
      motion="The taxi is already driving AWAY from the camera, its rear and red tail lights facing us, shrinking slowly into the distance; it never turns, never comes toward the camera, no headlights toward the lens; nothing else moves."),
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
    S("S18d", "S18", "d", "cu", "office_night", "HA", ["TOMIKO"], "TSK_OFFICE",
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
DISSOLVE_INTO = {"S01f": ("fade", 0.5), "S01g": ("fade", 0.5), "S02a": ("fade", 0.5), "S03a": ("fade", 0.5), "S05a": ("fade", 0.5),
                 "S06a": ("fade", 0.6), "S08a": ("fade", 0.5), "S09c": ("fade", 0.5), "S10a": ("fade", 0.5), "S11g": ("fade", 0.6), "S12a": ("fade", 0.6),
                 "S13a": ("fade", 0.5), "S14a": ("fade", 0.5), "S15a": ("fade", 0.5), "S16a": ("fade", 0.6), "S17a": ("fade", 0.5),
                 "S18a": ("fade", 0.6)}
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
HERO_TAKES = 2
SINGLE_TAKE = {"S10b"}   # 재생성 시 복원된 take 파일이 재사용되는 것을 피하기 위해 1테이크(2026-10-19 실증: regen_scenes는 sceneNN.mp4만 지운다)
RATE = {"pro": 0.108, "lite": 0.036, "omni": 0.16, "kf": 0.04, "hero": 0.112}

def tc(sec):
    fr = int(round(sec * FPS)); s, f = divmod(fr, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}.{f:02d}"


def ass_t(sec):
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap(text, limit=19):
    NOHEAD = "…—、。!?？！』」"
    out, cur = [], ""
    for i, ch in enumerate(text):
        cur += ch
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if len(cur) >= limit and ch in "、。…!?？！』」" and nxt and nxt not in NOHEAD:
            out.append(cur); cur = ""
    if cur:
        out.append(cur)
    if len(out) > 2 or max(len(x) for x in out) > limit + 7:
        mid = len(text) // 2
        cands = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "、。…!?？！" and text[i + 1] not in NOHEAD]
        cut = min(cands, key=lambda i: abs(i - mid)) if cands else mid
        out = [text[:cut], text[cut:]]
        if len(out[1]) > limit + 7:
            sub = out[1]; m2 = len(sub) // 2
            c2 = [i + 1 for i, ch in enumerate(sub[:-1]) if ch in "、。…!?？！" and sub[i + 1] not in NOHEAD]
            k = min(c2, key=lambda i: abs(i - m2)) if c2 else m2
            out = [out[0], sub[:k], sub[k:]]
    return "\\N".join(out)


SUB_ROW, SUB_ROWS = 16, 2


def _chunks(text, limit=SUB_ROW):
    """문장 호흡(、。…!?)에서 limit자 이하 조각으로 자른다. 구두점이 없으면 limit에서 강제 분할."""
    NOHEAD = "…—、。!?？！』」"
    out, cur = [], ""
    for i, ch in enumerate(text):
        cur += ch
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if ch in "、。…!?？！』」" and nxt and nxt not in NOHEAD and len(cur) >= 6:
            out.append(cur); cur = ""
    if cur:
        out.append(cur)
    res = []
    PART = "はがをにでとのもへやばて"
    for c in out:
        while len(c) > limit:
            cands = [k for k in range(6, limit + 1) if c[k - 1] in PART and c[k] not in NOHEAD]
            # 남은 길이가 2줄 안이면 가운데에 가까운 조사 뒤에서, 더 길면 한도에 가장 가까운 조사 뒤에서 자른다
            k = (min(cands, key=lambda q: abs(q - len(c) / 2)) if len(c) <= 2 * limit else cands[-1]) if cands else limit
            res.append(c[:k]); c = c[k:]
        res.append(c)
    return res


def split_events(text, t0, t1, min_s=1.0):
    """자막 이벤트 분할: 조각을 2줄×16자 안에 채워 넣고, 이벤트 시간은 글자 수 비례(최소 1.0초)."""
    pieces = _chunks(text)
    groups, g = [], []
    for pc in pieces:
        if len(g) < SUB_ROWS and (not g or len(g[-1]) + len(pc) > SUB_ROW):
            g.append(pc)
        elif g and len(g[-1]) + len(pc) <= SUB_ROW:
            g[-1] += pc
        else:
            groups.append(g); g = [pc]
    if g:
        groups.append(g)
    if len(groups) == 1:
        return [(t0, t1, "\\N".join(groups[0]))]
    total = sum(len("".join(x)) for x in groups); span = t1 - t0
    # 글자 수 비례, 최소 길이 보장
    durs = [max(min_s, span * len("".join(x)) / total) for x in groups]
    k = span / sum(durs); durs = [d * k for d in durs]
    out, t = [], t0
    for x, d in zip(groups, durs):
        out.append((round(t, 3), round(t + d, 3), "\\N".join(x))); t += d
    return out


def check_rules(shots):
    """제8장 자동 검사: A1 연속 같은 구도, OMNI 각도·단독, 악역 근접 CU, 초커, 돌리줌 1회, 더치 ≤2(악역만, 립싱크 컷 금지)."""
    errs = []
    order = ["ecu", "ch", "cu", "ms", "ws", "ews"]
    prev = None
    for s in shots:
        if not s["lens"] or not s["angle"]:
            errs.append(f"{s['id']}: 사이즈·앵글 비어 있음")
        if s["kind"] == "d" and s["angle"] in ("SIDE", "BE", "OH"):
            errs.append(f"{s['id']}: OMNI 대사 컷 각도 {s['angle']} 금지(정면~45°만)")
        if s["kind"] == "d" and len([w for w in s["who"] if w not in EXTRAS]) != 1:
            errs.append(f"{s['id']}: OMNI 컷은 1인 단독")
        if any(w in VILLAINS for w in s["who"]) and s["lens"] in ("ch", "ecu") and s["kind"] in ("react", "d", "face"):
            errs.append(f"{s['id']}: 악역 근접 CU 금지(가슴 위까지) — 손·소품 인서트(ins)만 허용")
        if s["lens"] == "ch" and not (s["who"] and s["who"][0].startswith(HERO_KEY)):
            errs.append(f"{s['id']}: 초커는 주인공 감정 정점에만")
        if "dutch" in s["fx"] and s["kind"] == "d":
            errs.append(f"{s['id']}: 더치는 립싱크 컷에 금지")
        if "handheld" in s["fx"] and s["kind"] == "d":
            errs.append(f"{s['id']}: 핸드헬드는 립싱크 컷에 금지")
        if prev and prev["scene"] == s["scene"] and not s["kind"].startswith("reuse") and not prev["kind"].startswith("reuse"):
            same_size = abs(order.index(prev["lens"]) - order.index(s["lens"])) < 1
            if same_size and prev["angle"] == s["angle"] and prev["loc"] == s["loc"]:
                errs.append(f"{prev['id']}→{s['id']}: 연속 같은 구도(A1)")
        prev = s
    dz = sum(1 for s in shots if "dollyzoom" in s["fx"])
    dutch = [s for s in shots if "dutch" in s["fx"]]
    if dz != 1:
        errs.append(f"돌리줌 {dz}회(1회만)")
    if len(dutch) > 2:
        errs.append(f"더치 {len(dutch)}회(최대 2회)")
    if any(not any(w in VILLAINS for w in s["who"]) for s in dutch):
        errs.append("더치는 악역 장면에만")
    return errs


def speech_span(path):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    return idx[0] / 16000, idx[-1] / 16000


def voice_src(n):
    return os.path.join(ROOT, "assets", "auditions", "ryokan-tts", f"line{SAME_AS.get(n, n):03d}.mp3")


def copy_voice(dst, n):
    out = os.path.join(dst, f"line{n:03d}.mp3")
    # 수정 9(2026-10-09): 감정 재녹음으로 채택한 줄(orig/ 보관본이 있는 줄)은 재생성 때 원본으로 되돌리지 않는다
    if os.path.exists(os.path.join(dst, "orig", f"line{n:03d}.mp3")) and os.path.exists(out):
        return out
    p = voice_src(n)
    a, b = speech_span(p)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-af", f"atrim={max(0, a - TRIM_PRE):.3f}:{b + TRIM_POST:.3f},asetpts=PTS-STARTPTS",
                    "-b:a", "192k", out], check=True)
    return out


def main():
    lock = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
    main_end = lock["main_end"]
    rows = {r["id"]: r for r in lock["lines"] if r["spk"] != "진행자"}
    script = [x for x in load_lines() if x[3] != "진행자"]
    assert len(script) == len(rows) == N_LINES, (len(script), len(rows))
    scenes = {s["id"]: (s["start"], s["end"]) for s in lock["scenes"] if not s["id"].startswith("OUT")}
    ad_times = [a["at"] for a in lock["ads"]]

    errs = check_rules(SHOTS)
    if errs:
        raise SystemExit("앵글 규칙 위반:\n  " + "\n  ".join(errs))
    used = [s["line"] for s in SHOTS if s["line"]]
    dup = [x for x, c in collections.Counter(used).items() if c > 1]
    assert not dup, f"한 줄이 여러 컷에 고정됨: {dup}"
    assert sorted(used) == sorted(rows), set(rows) ^ set(used)
    assert [s for s in scenes] == list(collections.OrderedDict.fromkeys(s["scene"] for s in SHOTS)), "장면 순서 불일치"
    ids_all = [s["id"] for s in SHOTS]
    assert len(ids_all) == len(set(ids_all)), "컷 ID 중복"

    starts, lag_report = {}, []
    by_scene = collections.OrderedDict()
    for s in SHOTS:
        by_scene.setdefault(s["scene"], []).append(s)
    for sc, shots in by_scene.items():
        a, b = scenes[sc]
        anchors = [(k, max(a, rows[s["line"]]["start"] - LEAD)) for k, s in enumerate(shots) if s["line"]]
        pts = [(0, a)] + [x for x in anchors if x[0] != 0]
        if anchors and anchors[0][0] == 0:
            pts = [(0, a)] + anchors[1:]
        pts.append((len(shots), b))
        want = [0.0] * len(shots)
        for (k1, t1), (k2, t2) in zip(pts, pts[1:]):
            n = max(1, k2 - k1)
            for j in range(k1, k2):
                want[j] = t1 + (t2 - t1) * (j - k1) / n
        pins = {0: a, len(shots): b}
        keys = sorted(pins)
        for k1, k2 in zip(keys, keys[1:]):
            tt = {k1: pins[k1]}
            for j in range(k1 + 1, k2):
                tt[j] = max(want[j], tt[j - 1] + SHOT_TARGET)
            tt[k2] = pins[k2]
            for j in range(k2 - 1, k1, -1):
                tt[j] = min(tt[j], tt[j + 1] - SHOT_TARGET)
            for j in range(k1, k2):
                starts[shots[j]["id"]] = tt[j]
                if shots[j]["line"]:
                    late = tt[j] - (rows[shots[j]["line"]]["start"] - LEAD)
                    if late > 0.05:
                        lag_report.append((shots[j]["id"], round(late, 2)))
    order_ids = [s["id"] for s in SHOTS]
    ends = {sid: (starts[order_ids[k + 1]] if k + 1 < len(order_ids) else main_end) for k, sid in enumerate(order_ids)}
    for k, s in enumerate(SHOTS):  # OMNI 8초 상한 → 다음 컷(B롤·리액션)이 이어받는다
        if s["kind"] == "d" and ends[s["id"]] - starts[s["id"]] > OMNI_MAX:
            nxt = order_ids[k + 1]
            assert SHOTS[k + 1]["scene"] == s["scene"], f"{s['id']}: 8초 초과분을 받을 다음 컷이 같은 장면에 없음"
            new = starts[s["id"]] + OMNI_MAX
            starts[nxt] = new; ends[s["id"]] = new
    for ad in ad_times:
        assert any(abs(starts[sid] - ad) < 1e-3 for sid in order_ids), f"광고 지점 {ad:.2f}에 컷 경계 없음"
    bad = [(sid, ends[sid] - starts[sid]) for sid in order_ids if ends[sid] - starts[sid] < MIN_SHOT]
    if bad:
        raise SystemExit("너무 짧은 컷: " + ", ".join(f"{a}={b:.2f}s" for a, b in bad))
    STILL_KINDS, I2V_KINDS = ("react", "ins", "estill", "gfx"), ("face", "sil", "empty")
    long_ = [(s["id"], ends[s["id"]] - starts[s["id"]]) for s in SHOTS
             if (s["kind"] in STILL_KINDS and ends[s["id"]] - starts[s["id"]] > STILL_MAX)
             or (s["kind"] in I2V_KINDS and ends[s["id"]] - starts[s["id"]] > I2V_MAX)]
    if long_:
        for sc in os.environ.get("DEBUG", "").split(","):
            for s_ in SHOTS:
                if s_["scene"] == sc:
                    print(f"  {s_['id']:7s} {s_['kind']:6s} {starts[s_['id']]:8.2f} {ends[s_['id']]:8.2f} {ends[s_['id']]-starts[s_['id']]:5.2f} {s_['line'] or ''} {rows[s_['line']]['start'] if s_['line'] else ''}")
        raise SystemExit("너무 긴 컷: " + ", ".join(f"{a}={b:.2f}s" for a, b in long_))

    durations, sb, scene_items = [], [], []
    cost = collections.Counter()
    for s in SHOTS:
        sid = s["id"]; d = ends[sid] - starts[sid]
        durations.append(round(d + HARD, 4))
        refs, ids = [], []
        for key in s["who"]:
            desc, cell = WHO[key]
            ids.append(desc + (f", wearing {WARD[key]}" if key in WARD else ""))
            if s["expr"] and (key, s["expr"]) in EXPR:
                refs.append(EXPR[(key, s["expr"])])
            elif cell:
                refs.append(cell)
        if s["loc"]:
            refs.append(LOC[s["loc"]])
        named = [w for w in s["who"] if w not in EXTRAS]
        comp = ("Exactly one person in sharp focus, no foreground shoulder, hands out of frame, chest-up single close-up, facing the camera within 30 degrees."
                if s["kind"] == "d" else
                ("Completely unpopulated: no people, no hands." if s["kind"] in ("empty", "estill") and not s["who"] or (s["kind"] in ("gfx",) and not s["who"]) else
                 f"Only the people described ({len(named)} named{', plus soft unrecognizable background people' if len(named) != len(s['who']) else ''}), no extra sharp faces."))
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/ryokan-keyframes/{sid}-1.png"
        kf_prompt = None
        sign_txt, signage = [], []
        if s["loc"] in SIGN_BY_LOC and s["lens"] in SIGN_SIZES and SIGN_BY_LOC[s["loc"]][0]:
            sign_txt.append(SIGN_BY_LOC[s["loc"]][0]); signage.append(SIGN_BY_LOC[s["loc"]][1])
        if sid in SIGN_BY_SHOT:
            sign_txt.append(SIGN_BY_SHOT[sid][0]); signage.append(SIGN_BY_SHOT[sid][1])
        if keyframe:
            subj = s["subject"]
            if s["kind"] == "gfx":
                subj = GFX_PLATE.get(sid) or re.sub(r"\s*\([^)]*\)|「[^」]*」|[0-9,]+円", "", subj)
                subj += " Every surface that will carry writing is completely blank and evenly lit."
            # 제12장 1(2026-10-12): 5단 공식 — 구도 → 인물 → 행동·표정 → 배경·조명 → 네거티브(오디오·대사 없음)
            kf_prompt = compose_keyframe(
                camera=f"{ANGLE[s['angle']]}, {LENS[s['lens']]}. {comp}".strip(),
                character=(" | ".join(ids) + ".") if ids else "",
                action=subj,
                setting=f"Lighting: {LIGHT[s['light']]}. {' '.join(sign_txt)} {PLAIN}".strip(),
                negative=f"{NEGATIVE}.", style=PRESET + ".")
            cost["kf"] += 1
        tier = {"d": "omni", "react": "still", "ins": "still", "estill": "still", "gfx": "gfx", "face": "pro", "sil": "lite",
                "empty": "lite", "card": "card"}.get(s["kind"], "reuse")
        if s["hero"] and tier in ("pro", "lite"):
            tier = "hero"
        gen = 10 if d > 5.0 else 5
        item = {"prompt": "", "duration": gen}
        if tier in ("pro", "lite", "hero"):
            motion = s["motion"] or "Subtle natural motion only, micro movements, no new people."
            if TEAR_RE.search(s["subject"] + " " + motion):
                motion += TEAR_MOTION
            item["prompt"] = compose_motion(
                action=motion,
                character="Keep the exact faces, wardrobe, props and lighting of the first frame.",
                locks="Head turns under 20 degrees. No walking toward the camera unless described, no new people, no text.")
            _bad = check_motion(item["prompt"], sid)
            if _bad:
                print("  [경고 제12장 1] " + "; ".join(_bad))
            item["image"] = keyframe
            if tier == "pro":
                item["i2v_model"], item["i2v_resolution"] = PRO_MODEL, "1080p"; cost["pro"] += gen
            elif tier == "hero":
                tk = 1 if sid in SINGLE_TAKE else HERO_TAKES
                item["i2v_model"], item["i2v_resolution"], item["hero_takes"] = HERO_MODEL, "1080p", tk; cost["hero"] += gen * tk
            else:
                cost["lite"] += gen
        else:
            item["prompt"] = f"(override) {tier}: {s['subject'][:80]}"
            item["override_required"] = True
            if keyframe:
                item["image"] = keyframe
        if tier == "omni":
            cost["omni"] += min(d, OMNI_MAX) + 0.8
        scene_items.append(item)
        sb.append({"id": sid, "scene": s["scene"], "kind": s["kind"], "tier": tier, "hero": s["hero"],
                   "timecode": f"{tc(starts[sid])} - {tc(ends[sid])}", "start": round(starts[sid], 3), "assembled_s": round(d, 3), "generate_s": gen,
                   "size": s["lens"], "lens": LENS[s["lens"]], "angle": s["angle"], "light": s["light"], "lighting": LIGHT[s["light"]], "edit_fx": s["fx"],
                   "refs": refs, "subject": s["subject"], "line": s["line"], "motion": item["prompt"] if tier in ("pro", "lite", "hero") else "",
                   "keyframe": keyframe, "keyframe_prompt": kf_prompt, "gfx": GFX.get(sid, ""), "caption": CARDS.get(sid, ""),
                   "signage": signage, "transition_in": DISSOLVE_INTO.get(sid, ("", 0.0))})
    budget = round((cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"] + cost["hero"] * RATE["hero"]) * 1.25, 2)
    transitions, ttypes = [0.0] * len(SHOTS), ["fade"] * len(SHOTS)
    for k, s_ in enumerate(SHOTS):
        tt, o = DISSOLVE_INTO.get(s_["id"], ("fade", 0.0))
        if o and k > 0:
            transitions[k - 1], ttypes[k - 1] = o, tt
            durations[k - 1] = round(durations[k - 1] + o - HARD, 4)
    for ad in ad_times:
        k = next(i for i, sid in enumerate(order_ids) if abs(starts[sid] - ad) < 1e-3)
        assert transitions[k - 1] <= AD_MAX_DISSOLVE, f"광고 경계 {order_ids[k]} 전환 {transitions[k - 1]}초 > {AD_MAX_DISSOLVE}"
    in_trans = []
    for k, s_ in enumerate(SHOTS):
        o = DISSOLVE_INTO.get(s_["id"], ("fade", 0.0))[1]
        if o:
            t0 = starts[s_["id"]]
            in_trans += [(s_["id"], lid) for lid, r in rows.items() if t0 - 1e-3 <= r["start"] < t0 + o]

    dst = os.path.join(ROOT, "assets", "audio-overrides", SKIT)
    os.makedirs(dst, exist_ok=True)
    for n in range(1, N_LINES + 1):
        copy_voice(dst, n)

    # 제11장 16(2026-10-09): 정지 푸시인(still) 컷의 설명에 순간 동작 단어가 있으면 경고(정지 키프레임은 그 순간을 얼린다)
    _motion = ("dropping", "drops", "falling", "falls", "thrown", "throws", "tossing", "tosses", "swinging", "splash", "mid-air", "in the air")
    for s_ in sb:
        if s_.get("tier") == "still" and any(w_ in s_.get("subject", "").lower() for w_ in _motion):
            print(f"[경고] still 컷 {s_['id']}: 설명에 순간 동작 단어 — 「동작 직후 상태」로 바꾸거나 i2v로(제11장 16)")
    events = []
    for i, x in enumerate(script, 1):
        r = rows[f"line{i:03d}"]
        st = STYLE[x[3] if x[3] != "NA" else "NA"]
        # 제11장 21(2026-10-09): 한 이벤트 = 최대 2줄×16자. 넘치면 문장 호흡에서 조각내 글자 수 비례로 시간을 나눠 연속 표시
        for k_, (c0, c1, txt) in enumerate(split_events(x[5], r["start"] - TRIM_PRE, r["end"] + 0.25)):
            # 첫 조각만 TTS 줄(스타일 그대로), 이어지는 조각은 「<스타일>_c」(silent_styles) — generate_audio가 TTS 줄로 세지 않게(#02 burn 146 실증: 123줄로 세어 TTS 실패)
            events.append((c0, c1, st if k_ == 0 else st + "_c", STYLE_JA[st], txt, f"line{i:03d}"))   # Effect 칸 = 줄 번호(한글 검수 자막 묶음용)
    # 제11장 12(2026-10-09): 카드 컷(S01g 등)은 build_ryokan_overrides.py가 글자를 클립에 직접 그리므로
    # Caption 자막을 겹쳐 굽지 않는다(#02 1차 조립 실증: 카드 글자 + 자막 글자가 중앙에 이중으로 겹침).
    CARD_TEXT_IN_CLIP = True
    for sid, cap in CARDS.items():
        if CARD_TEXT_IN_CLIP:
            continue
        c0 = starts[sid] + DISSOLVE_INTO.get(sid, ("", 0.2))[1] + 0.1
        events.append((c0, min(ends[sid] - 0.2, c0 + 3.5), "Caption", "", cap))
    for lid, off, ln, style, txt in EMPH:
        t0 = rows[lid]["start"] + off
        events.append((t0, t0 + ln, style, "", txt))
    events.sort(key=lambda e: e[0])
    fmt = "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
    # 2:1 레터박스 안쪽 하단에 자막(MarginV 150), 내레이션은 명조(03_시네마규격)
    st_lines = "\n".join(
        f"Style: {n}{suf},{'Noto Serif CJK JP' if n == 'Naration' else 'Noto Sans CJK JP'},{58 if n == 'Naration' else 60},{c},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{2 if n == 'Naration' else 3},1,2,200,200,150,1"
        for n, c in STYLE_COLOR.items() for suf in ("", "_c"))
    ass = ["[Script Info]", "Title: 老舗旅館の嫁 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]", fmt, st_lines,
           "Style: Caption,Noto Serif CJK JP,66,&H00FFF3C4,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,5,200,200,80,1",
           "Style: Emph,Noto Sans CJK JP,150,&H0000E6FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,10,3,5,100,100,80,1",
           "Style: Emph2,Noto Serif CJK JP,92,&H0040E6FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,100,100,80,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:
        txt = e[4]
        if e[2] == "Emph":
            txt = "{\\fscx130\\fscy130\\t(0,120,\\fscx100\\fscy100)}" + txt
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,{e[5] if len(e) > 5 else ''},{txt}")
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    # BGM 4곡(사운드 설계서 B1~B4): 곡 사이 숨 1.5초 이상, 광고 경계 앞뒤 분리, S13 수화기 낙하에서 절단 2초(룸톤 위)
    t_ad1, t_ad2 = ad_times
    BGM = [
        (0.0, t_ad1 - 0.2, 0.38, "slow Japanese ryokan drama score, solo shamisen single plucks over a soft koto drone, sparse, melancholic, restrained, cinematic, instrumental, no vocals"),
        (t_ad1 + 1.6, starts["S13g"] - 0.05, 0.40, "driving suspense score, pulsing low strings, ticking percussion, taiko accent hits, building to a dramatic reveal, Japanese drama, instrumental, no vocals"),
        (starts["S13h"] + 0.3, t_ad2 - 0.2, 0.40, "low ominous drone with sparse piano, a heavy loss sinking in, cold and hollow, Japanese drama score, instrumental, no vocals"),
        (t_ad2 + 1.6, round(main_end, 2), 0.42, "warm uplifting cinematic piano and strings, gentle hopeful progression, koto accent, resolution and relief, emotional Japanese drama ending, instrumental, no vocals"),
    ]
    SFX = [{"at": round(starts[s] + o, 2), "kind": k} for s, o, k in
           (("S01a", 0.3, "handset_creak"), ("S01c", 0.8, "phone_set_down"), ("S02a", 0.2, "fluorescent_on"), ("S04c", 0.4, "knife_on_board"), ("S05f", 0.9, "lamp_switch"),
            ("S06d", 0.2, "wiping_stop"), ("S07c", 0.3, "teacup_click"), ("S07g", 0.2, "fan_snap"), ("S09b", 0.1, "binder_drop"), ("S10a", 0.5, "phone_notify"),
            ("S11c", 0.1, "notify_triple"), ("S11c", 0.4, "bass_hit"), ("S13a", 0.0, "phone_ring"), ("S13g", 0.5, "handset_drop"), ("S13i", 0.3, "pen_scratch"),
            ("S14a", 0.1, "bus_airbrake"), ("S16a", 0.2, "phone_vibrate2"), ("S16e", 0.6, "phone_set_down"), ("S17a", 1.5, "taxi_door"), ("S18a", 0.2, "phone_vibrate3"),
            ("S18h", 0.5, "phone_face_down"), ("S18i", 0.6, "distant_laughter_no_words"))]
    SFX.append({"at": round(rows["line056"]["start"] + 0.6, 2), "kind": "bass_hit"})

    os.makedirs(os.path.join(ROOT, "scripts", "storyboard"), exist_ok=True)
    json.dump({"_설명": "ryokan PHASE 3 스토리보드 Lock(build_ryokan_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT,
               "preset": PRESET, "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"],
               "scenes": sb}, open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"_설명": "ryokan 장면 설정(build_ryokan_phase3.py 생성). override_required 장면(정지 푸시인·OMNI 정지 프레임·그래픽·재사용·카드)은 video-overrides로 먼저 넣는다. hero_takes 컷은 B안 상위 모델 3테이크.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, "
                         "wardrobe, props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": "ryokan 조립·오디오(build_ryokan_phase3.py 생성). 음성 77줄 = assets/audio-overrides/ryokan/ (ElevenLabs 확정본, 발화 구간만).",
        "default_voice": "cached-elevenlabs",
        "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Naration"], "silent_styles": ["Caption", "Emph", "Emph2"] + [n + "_c" for n in STYLE_COLOR],
        "output_size": [1920, 1080], "fit": "crop", "letterbox": "2:1",
        "scene_durations": durations, "transitions": transitions, "transition_types": ttypes,
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d"],
        "omnihuman_prompts": {str(idx[k]): OMNI_COMMON + v for k, v in OMNI_PROMPTS.items() if k in idx},
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0,
        "legacy_lipsync": False,
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35,
        "ambience_prompts": [AMBIENCE.get(sid, "") for sid in order_ids],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": round(s, 2), "end": round(e, 2), "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_효과음": SFX,
        "_마스터링": "-14 LUFS / TP -1.0 dBTP, 료칸 실내 = 나무 마루 짧은 잔향, 하나이카다 로비 = 밝은 홀 잔향, −52dBFS 룸톤 베드 전편(제11장 13)",
        "_아웃트로": "진행자 5줄(line078~082)은 본편에 넣지 않는다 — PHASE 6 append_outro + outro_cta_overlay(美談ものがたり 공통).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = (cost["kf"] * RATE["kf"] + cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"] + cost["hero"] * RATE["hero"])
    md = ["# 『老舗旅館の嫁』 PHASE 3 샷 리스트", "",
          f"> `scripts/build_ryokan_phase3.py` 자동 생성(손 수정 금지). 타임코드 분:초.프레임(24fps). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " +
          ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock["ads"]) + ".", "",
          "## 비용 추산 (실측 단가, B안)", "", "| 항목 | 수량 | 단가 | 금액 |", "|---|---|---|---|",
          f"| 키프레임 | {cost['kf']}장 | 0.04 | {cost['kf'] * RATE['kf']:.2f} |",
          f"| i2v pro 1080p (얼굴) | {cost['pro']}초 | 0.108 | {cost['pro'] * RATE['pro']:.2f} |",
          f"| i2v lite 720p (실루엣·무인) | {cost['lite']}초 | 0.036 | {cost['lite'] * RATE['lite']:.2f} |",
          f"| 히어로 컷 Kling 3.0 Pro × {HERO_TAKES}테이크 | {cost['hero']}초 | 0.112 | {cost['hero'] * RATE['hero']:.2f} |",
          f"| OmniHuman (컷 길이 + 0.8초) | {cost['omni']:.1f}초 | 0.16 | {cost['omni'] * RATE['omni']:.2f} |",
          f"| **1차 합계** (재생성 여유 제외) | | | **{total_cost:.2f}** |",
          f"| i2v 예산 상한 `budget_usd` (여유 25%) | | | {budget:.2f} |", "",
          "## 생성 방식 분포", "", "| 방식 | 컷 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in tiers.most_common()] + [
          "", "## 앵글 분포 (생성 컷)", "", "| 앵글 | 컷 | 비율 |", "|---|---|---|"] + [
          f"| {k} | {v} | {v / sum(ang.values()) * 100:.0f}% |" for k, v in ang.most_common()] + [
          "", "## 히어로 컷 (B안 상위 모델 3테이크)", ""] + [f"- {x['id']}: {x['subject'][:70]}" for x in sb if x["hero"]] + [
          "", "## 로컬 그래픽·글자 합성 (키프레임은 무지)", ""] + [f"- {k}: {v}" for k, v in GFX.items()] + [
          "", "## 화면 속 일본어 표기 — 명판·현수막·라벨 (무지 생성 후 로컬 합성, 장면별)", ""] + [
          f"- {x['id']} ({x['scene']}): " + " / ".join(x["signage"]) for x in sb if x["signage"]] + [
          "", "## 장면 전환 (기본 하드컷)", ""] + [f"- {x['id']} 앞: {x['transition_in'][0]} {x['transition_in'][1]}초" for x in sb if x["transition_in"][1]] + [
          "", "## 샷 표", "", "| 컷 | 타임코드 | 길이 | 방식 | 사이즈 | 앵글 | 조명 | 편집 효과 | 대사 | 내용 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in sb:
        md.append(f"| {x['id']} | {x['timecode']} | {x['assembled_s']:.2f}s | {x['tier']} | {x['size']} | {x['angle']} | {x['light']} | {x['edit_fx']} | {x['line'] or ''} | {x['subject'][:60]} |")
    open(os.path.join(PROD, "07_샷리스트.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    # 02_카메라앵글설계.md (제8장 7)
    KIND_KO = {"d": "립싱크", "react": "리액션(정지 줌)", "ins": "인서트(정지 줌)", "face": "얼굴 영상", "sil": "실루엣·원경 영상", "empty": "무인 영상",
               "estill": "무인 정지", "gfx": "그래픽 합성", "card": "카드"}
    SIZE_KO = {"ecu": "ECU", "ch": "CH", "cu": "CU", "ms": "MS", "ws": "WS", "ews": "EWS"}
    dz = [s["id"] for s in SHOTS if "dollyzoom" in s["fx"]]; du = [(s["id"], s["fx"]) for s in SHOTS if "dutch" in s["fx"]]
    cam = ["# 『老舗旅館の嫁』 카메라 앵글 설계 (CLAUDE.md 제8장 7)", "",
           f"> `scripts/build_ryokan_phase3.py`의 샷 표에서 자동 생성. 자동 검사 통과: 연속 같은 구도 0 · 더치 {len(du)}회({', '.join(f'{a} {b}' for a, b in du)} — 악역만, 비립싱크) · 돌리줌 1회({dz[0]}) · 립싱크 컷 정면~45° · 악역 근접 CU 없음 · 초커는 사오리만.", "",
           "## 앵글 설계 원칙 (이 작품)", "",
           "- **권력 역전**: 도미코·마이는 전반 로우앵글(S07b·S07e·S07f·S07i·S11d) → 붕괴 뒤 하이앵글·부감(S11e 마이, S17d 도미코 버즈아이). 사쿠라이는 아이레벨 정면(조력자).",
           "- **와카나**: 전반 하이앵글(S04d·S06e·S07d 무력) → 해방의 미소에서 아이레벨 초커(S07k, 작품 내 1회) → 후반 아이레벨 정면 고정(S16·S18). 카메라는 고정·슬로 푸시인만(주인공 안정도 축).",
           "- **악역 불안**: S07g 더치 5°+핸드헬드(부채 인서트, 마이) · S11f 더치 7°+핸드헬드(도미코 어깨 너머) · S10b 핸드헬드(프런트 혼란) · S18e 핸드헬드(남편이 수화기를 빼앗음).",
           "- **돌리줌 1회**: S13g 수화기 낙하 직전 도미코 — 편집 구현(제8장 6).",
           "- **매치 컷·수미상관**: S01a(수화기 손) ↔ S13g(수화기 낙하) ↔ S18c · S01c(전화 내려놓는 손) ↔ S16e·S18h · S01e(빈 현관 노렌) ↔ S13k(크레인 업).",
           "- **소품 인격화(ECU 70%)**: 수화기(S01a·S13c·S13g) · 인수인계서(S08b·S08c·S09b·S13j) · 식칼(S02c·S04c) · 찻잔(S07c·S11a) · 부채(S07g) · 걸레(S06d).",
           "- **전경 프레이밍(A7)**: S06a 문틀 너머 · S06c·S07j·S10c·S11f·S18e 어깨 너머 · S15a 와카나 어깨 너머 · S08a 문틀 푸시.", "",
           "## 장면별 컷 순서", "", "| 장면 | 컷 순서 (사이즈·앵글·방식) |", "|---|---|"]
    for sc, shots in by_scene.items():
        cam.append(f"| {sc} | " + " → ".join(f"{s['id']} {SIZE_KO[s['lens']]}/{s['angle']} {('재사용' if s['kind'].startswith('reuse') else KIND_KO[s['kind']])}{'★' if s['hero'] else ''}" for s in shots) + " |")
    open(os.path.join(PROD, "02_카메라앵글설계.md"), "w", encoding="utf-8").write("\n".join(cam) + "\n")
    if in_trans:
        print("전환 중 시작하는 대사(자막이 전환 위에 뜸):", in_trans)
    if lag_report:
        print("J컷(대사가 앞 컷 위에서 먼저 시작):", ", ".join(f"{a}+{b}s" for a, b in lag_report))
    top = ang.most_common(1)[0]
    print(f"완료: 컷 {len(SHOTS)}개, 본편 {tc(main_end)}, 방식 {dict(tiers)}, 1차 비용 약 {total_cost:.2f}달러 (i2v budget {budget}), 최다 앵글 {top[0]} {top[1] / sum(ang.values()) * 100:.0f}%")


if __name__ == "__main__":
    main()
