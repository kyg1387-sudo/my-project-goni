#!/usr/bin/env python3
"""『柳の葉と一杯の水』(yanagi) PHASE 3 샷 리스트 Lock 생성기 — 일본어판.

입력(동결본, 손으로 옮겨 적지 않는다):
  productions/willow-leaf-ja/lock.json         PHASE 1 Lock(실측 음성 줄 타임코드·장면 경계·광고 지점)
  productions/willow-leaf-ja/00_script_ja.md   대본 v3(자막 원문)
  assets/auditions/yanagi-tts/lineNNN.mp3      확정 음성(→ assets/audio-overrides/yanagi/로 복사)
출력:
  scripts/storyboard/yanagi.json   샷 스펙(PHASE 4 키프레임·PHASE 5 입력)
  scripts/scenes/yanagi.json       장면 생성 설정(i2v·override_required·budget_usd)
  scripts/audio/yanagi.json        조립·오디오(장면 길이·OmniHuman·BGM·현장음)
  subs/yanagi.ass                  일본어 자막(대사 74줄 + 화면 전용 카드)
  productions/willow-leaf-ja/07_샷리스트.md  검토용 표 + 비용 추산 + 앵글 분포
규칙: CLAUDE.md 제0~9장, 02_카메라앵글설계.md v3(앵글 A1~A16), 4-1 대사 촬영 지정(OMNI 14장면).
사용법: python3 scripts/build_yanagi_phase3.py
"""
import json
import math
import os
import re
import shutil
import collections

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "willow-leaf-ja")
SKIT = "yanagi"
FPS = 24
HARD = 1 / FPS
OMNI_MAX = 8.0
LEAD = 0.3            # 대사 컷은 발화 0.3초 전에 시작
MIN_SHOT = 1.2
STILL_MAX = 6.5
I2V_MAX = 10.0
SHOT_TARGET = 1.6     # 분배 목표 최소 길이(인서트 1.6초 이상)

# ---------- 고정 문장(PHASE 2 시트와 1:1, 모든 프롬프트에 그대로 반복) ----------
C1, C2 = "assets/portraits/yanagi-cast/cells/", "assets/portraits/yanagi-cast-2/cells/"
WHO = {
    "YUNA": ("Oki Yuna, a Japanese woman aged 21, slim, gentle face, long straight black hair in a low ponytail with wispy "
             "see-through bangs, exactly one small beauty mark under her LEFT eye, no glasses, a beige adhesive bandage on her RIGHT index finger",
             C2 + "yuna-front.png"),
    "OGATA": ("Ogata Ryuzo, a Japanese man aged 75, lean, full head of cropped snow-white hair (not bald), thick white eyebrows, "
              "round tortoiseshell glasses, a small pale scar on the right side of his chin", C1 + "ogata-a-front.png"),
    "SAKA": ("Sakamoto Kenji, a Japanese man with a lean face, glossy gel-slicked-back black hair, rectangular black-rimmed glasses, "
             "a thick gold wristwatch on his LEFT wrist", C2 + "sakamoto-front.png"),
    "HARUKO": ("Oki Haruko, an East Asian woman aged 80, small and thin, silver-white chin-length bob with a small pink hairpin on the right side, "
               "deep smile lines, a green jade ring on her LEFT ring finger, no glasses", C1 + "haruko-front.png"),
    "SATO": ("Sato, a Japanese man aged 52, neat side-parted black hair with silver temples, a clear coiled earpiece in his RIGHT ear, no glasses",
             C1 + "sato-front.png"),
    "MURASE": ("Murase, a Japanese woman aged 46, chin-length straight black bob with bangs, small pearl stud earrings", C1 + "murase-front.png"),
    "OLDHANDS": ("a woman in her sixties seen only from behind or as wrinkled hands, faded floral cotton blouse (no face)", None),
    "CHILD": ("a small girl about six seen only from behind or as small hands, yellow T-shirt, two low pigtails with mint-green hair ties (no face)", None),
}
WARD = {
    "YUNA": "a plain green-and-white vertically striped short-sleeve convenience-store uniform shirt over a white T-shirt, a small plain blank white name plate on the left chest, black slacks, white canvas sneakers",
    "YUNA_IZ": "a red rubber apron over a white T-shirt, yellow rubber gloves, hair in the same low ponytail",
    "OGATA_A": "a faded grey linen jacket over a wrinkled beige shirt, loose tan trousers, worn brown leather shoes",
    "OGATA_B": "a charcoal-navy three-piece suit, white shirt with the collar open and no tie, a small plain silver willow-leaf lapel pin",
    "SAKA": "a white short-sleeve dress shirt with a navy necktie under a green-and-white striped store vest worn open, a small plain blank white name plate on the left chest, grey slacks, black loafers",
    "HARUKO": "a light-blue striped hospital gown with a cream knitted cardigan over the shoulders",
    "SATO": "a black suit, white shirt, black necktie",
    "MURASE": "a light-grey pantsuit with a white bow blouse",
}
EXPR = {  # 표정 셀(키프레임에 감정 50~70% 선반영 — 규격 제2장 3)
    ("OGATA", "exhausted"): C2 + "ogata-a-expr-exhausted.png", ("OGATA", "cold"): C2 + "ogata-a-expr-cold.png",
    ("OGATA", "tears"): C2 + "ogata-a-expr-tears.png", ("OGATA_B", "front"): C2 + "ogata-b-front.png",
    ("SAKA", "smug"): C2 + "sakamoto-expr1.png", ("SAKA", "fawn"): C2 + "sakamoto-expr2.png", ("SAKA", "shock"): C2 + "sakamoto-expr3.png",
}
LOC = {
    "EXT_DAY": C1 + "loc-store-ext-day.png", "EXT_BENCH": C1 + "loc-store-ext-key1.png", "EXT_DOOR": C1 + "loc-store-ext-key2.png",
    "EXT_LOW": C1 + "loc-store-ext-angles-day.png", "EXT_ACROSS": C1 + "loc-store-ext-angles-night.png",
    "EXT_THROUGH": C1 + "loc-store-ext-angles-key1.png", "EXT_BLUE": C1 + "loc-store-ext-angles-key2.png",
    "INT_DAY": C1 + "loc-store-int-day.png", "INT_INSPECT": C1 + "loc-store-int-night.png", "INT_COUNTER": C1 + "loc-store-int-key1.png",
    "INT_STOCK": C1 + "loc-store-int-key2.png", "INT_REV": C1 + "loc-store-int-angles-day.png", "INT_CEIL": C1 + "loc-store-int-angles-night.png",
    "INT_LOW": C1 + "loc-store-int-angles-key1.png", "INT_AISLE": C1 + "loc-store-int-angles-key2.png",
    "OFFICE": C1 + "loc-backoffice-day.png", "OFFICE_DESK": C1 + "loc-backoffice-key1.png", "OFFICE_DOOR": C1 + "loc-backoffice-key2.png",
    "WELL_DAY": C1 + "loc-yanagi-well-day.png", "WELL_GOLD": C1 + "loc-yanagi-well-night.png", "WELL_WATER": C1 + "loc-yanagi-well-key1.png",
    "WELL_MIST": C1 + "loc-yanagi-well-key2.png",
    "HOSP6": C1 + "loc-hospital-day.png", "HOSP6_DUSK": C1 + "loc-hospital-night.png", "PRIV": C1 + "loc-hospital-key1.png", "PRIV_DUSK": C1 + "loc-hospital-key2.png",
    "IZAKAYA": C2 + "loc-misc-izakaya.png", "SEDAN": C2 + "loc-misc-sedan-night.png", "SEDAN_IN": C2 + "loc-misc-sedan-interior.png",
    "SEDANS": C2 + "loc-misc-sedans-day.png",
    "P_CUP": C2 + "props-cup.png", "P_NOTE": C2 + "props-notebook.png", "P_PHOTO": C2 + "props-photo.png", "P_BADGE": C2 + "props-badge-paper.png",
}
PRESET = ("Photorealistic live-action Japanese human drama, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, "
          "quiet restrained Japanese film mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, "
            "logo on shirt, signage lettering, posters with writing, price tags with numbers, printed labels, brand logos, car emblems, "
            "license plates, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people")
PLAIN = "All papers, screens, signs, plates and labels are completely blank; no letters, numbers or symbols anywhere in the frame."
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait",
    "ch": "85mm prime lens, f/1.8, choker framing from forehead to chin, razor-sharp eyes, soft bokeh",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective",
}
LIGHT = {
    "sun": "harsh 2 p.m. midsummer sunlight, bleached highlights, visible heat haze over the asphalt, 5600K",
    "shade": "soft natural diffused light in dappled willow shade, low warm backlight rim on hair and shoulders, gentle contrast",
    "store": "bright soft daylight through the glass storefront, cool fluorescent fill, gentle contrast",
    "kitchen": "flat greenish fluorescent kitchen light, rising steam, tired night mood",
    "ward": "soft daylight diffused through a thin white curtain, pale mint walls, gentle contrast",
    "ward_gold": "low golden-hour sun through the window behind the bed, warm 3200K backlight, glowing rim light, soft lifted shadows",
    "flash": "warm amber 3200K golden dusk flashback, soft halation, lifted blacks like an old family photo, low sun backlight",
    "office": "a single cold fluorescent tube directly overhead (5600K or cooler), hard top light, dark shadows under brows and chin, faint cyan cast, chiaroscuro",
    "blue": "blue-hour dusk, deep blue ambient with a warm orange sodium streetlight, the store glowing",
    "car": "dark car interior lit only by orange streetlight through the side window, deep shadows",
    "well_gold": "golden hour at the old well, low warm sun behind the willows, glowing rim light on leaves and figure, long soft shadows",
    "inspect": "crisp 10 a.m. daylight blasting through the glass door behind the entrance, strong backlight and silhouettes, interior darker, mirror-polished floor reflections, high contrast",
    "confront": "cool crisp daylight inside the store, high-contrast chiaroscuro, polished floor reflections",
    "mist": "misty early morning, soft green and pale gold light, silver mist over the water",
    "cctv": "high-angle security-camera view, slightly cool flat video look, faint lens distortion",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}

MOTION_D = ("Speaking: natural lip movement, single slow eye blink, micro chest breathing, maximum 5-degree head tilt, no head turn, "
            "hands out of frame. Lips close and stay still after the line ends.")


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, still=False):
    """샷 1개. kind: d(OMNI 대사) / react(리액션 정지) / ins(인서트·손·정물 정지) / face(인물 얼굴 i2v pro) /
    sil(실루엣·뒷모습·원경 i2v lite) / empty(무인 i2v lite) / estill(무인 정지) / reuse:<id> / card."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc,
                subject=subject, line=line, fx=fx, motion=motion, expr=expr)


# ---------- 샷 표 (02_카메라앵글설계.md v3 → 구조화) ----------
SHOTS = [
    # ① 도입 후크 (0:00~0:20) — 후반 컷 재사용(추가 생성 0)
    S("H0", "H", "reuse:S27e", "ews", "confront", "BE", [], None, "Reuse of S27e (dogeza from above, sweat on the polished floor)."),
    S("H1", "H", "reuse:S24b", "cu", "inspect", "LA", [], None, "Reuse of S24b (chairman: 'where is she'). Hook voice = line047 mixed locally."),
    S("H2", "H", "reuse:S26h", "ecu", "ward", "OH", [], None, "Reuse of S26h (a tear falls on the pressed leaf)."),
    S("H3", "H", "card", "ews", "store", "EL", [], None, "Black title card 『柳の葉と一杯の水』."),
    # ② 발단·갈등
    S("S01a", "S01", "empty", "ews", "sun", "LA", [], "EXT_LOW", "No people. Very low angle from the hot asphalt toward the small convenience store and the great weeping willow, heat haze shimmering.", line="line001",
      motion="Heat haze shimmers over the asphalt, willow branches hang almost still. No people, no cars."),
    S("S01b", "S01", "estill", "ws", "sun", "HA", [], "EXT_THROUGH", "No people. High angle from a second-floor height down the narrow alley, the glass door seen through hanging willow branches."),
    S("S02a", "S02", "face", "ws", "store", "HA", ["OGATA:OGATA_A", "SAKA:SAKA"], "INT_DAY",
      "High angle over Sakamoto's shoulder (only his shoulder and back in the foreground, out of focus) looking down at Ogata collapsed on the tile floor just inside the glass door, sweat on his face, glasses askew, one trembling hand raised.",
      motion="Ogata's raised hand trembles slightly, his chest heaves with shallow breaths. Sakamoto's back stays still. No one walks.", expr="exhausted"),
    S("S02b", "S02", "d", "cu", "store", "EL", ["OGATA:OGATA_A"], "INT_DAY", "Chest-up close-up of Ogata on the floor, exhausted, dry lips, sweat, warm rim light, looking up.", line="line002", expr="exhausted"),
    S("S03a", "S03", "sil", "ms", "store", "LA", ["SAKA:SAKA"], "INT_DAY",
      "Low angle medium shot of Sakamoto seen from the side and behind, a silhouette against the ceiling fluorescent light, jabbing a finger toward the door; his mouth is not visible.", line="line003",
      motion="Sakamoto jabs his finger toward the door twice, his head stays turned away from the camera."),
    S("S03b", "S03", "ins", "ecu", "store", "EL", ["OGATA:OGATA_A"], "INT_DAY", "Insert: an old man's wrinkled hand pressed on the white tile floor, grey linen cuff."),
    S("S04a", "S04", "ins", "ecu", "sun", "EL", ["OGATA:OGATA_A"], "EXT_DOOR", "Insert: outside, an old man's wrinkled hand slides down the sunlit glass door, the street reflected in the glass, grey linen sleeve."),
    S("S05a", "S05", "ins", "ecu", "store", "OH", ["YUNA:YUNA"], "INT_COUNTER", "Insert from above: a plain white paper cup filling with water at the dispenser, a young woman's hand with a beige bandage on the right index finger."),
    S("S06a", "S06", "sil", "ms", "sun", "SIDE", ["YUNA:YUNA"], "EXT_DOOR", "Yuna seen from behind pushes out through the glass door into the blazing sun holding the paper cup.",
      motion="Yuna walks two steps forward away from the camera through the door, her ponytail swaying; she never turns around."),
    S("S06b", "S06", "ins", "ms", "sun", "LA", ["YUNA:YUNA"], "EXT_BENCH", "Low angle insert against the bright sky: a young woman's bandaged hand plucks a single long narrow willow leaf from a hanging branch."),
    S("S07a", "S07", "ins", "ecu", "shade", "OH", [], "P_CUP", "Insert from above: a single long narrow willow leaf lands on the water in the plain white paper cup and floats."),
    S("S08a", "S08", "sil", "ws", "shade", "HA", ["YUNA:YUNA", "OGATA:OGATA_A"], "EXT_ACROSS", "High angle wide from across the road: in the willow shade beside the store, a young woman kneels beside an old man slumped against the wall; willow branches frame the foreground. Faces small, no detail.",
      motion="Willow branches sway gently in the foreground; the two figures stay still in the shade."),
    S("S08b", "S08", "face", "ms", "shade", "LA", ["YUNA:YUNA", "OGATA:OGATA_A"], "EXT_BENCH", "Knee-level two-shot in profile: Yuna kneels and holds the paper cup with both hands up to Ogata; their eyes meet. No one speaks.",
      motion="Yuna slowly tilts the cup toward Ogata's lips; Ogata's hands rise to hold it. Both stay in profile, mouths closed."),
    S("S08c", "S08", "d", "cu", "shade", "EL", ["YUNA:YUNA"], "EXT_BENCH", "Chest-up close-up of Yuna in the willow shade, gentle and slightly urgent, soft rim light, looking at the old man just off camera.", line="line004"),
    S("S09a", "S09", "react", "cu", "shade", "EL", ["OGATA:OGATA_A"], "P_CUP", "Close-up: the paper cup with the floating willow leaf sharp in the lower foreground, Ogata's face soft behind it.", line="line005", fx="rack"),
    S("S09a2", "S09", "ins", "ecu", "shade", "OH", ["OGATA:OGATA_A"], "P_CUP", "Macro insert from above: one long narrow willow leaf floating on the clear water in a plain white paper cup held in wrinkled hands, faint ripples."),
    S("S09a3", "S09", "ins", "ecu", "shade", "SIDE", ["OGATA:OGATA_A"], "P_CUP", "Side macro insert: an old man's wrinkled fingers trembling around the plain white paper cup, a drop of water on his knuckle, grey linen cuff."),
    S("S09b", "S09", "react", "ch", "shade", "EL", ["OGATA:OGATA_A"], "EXT_BENCH", "Choker close-up of Ogata's eyes behind the tortoiseshell glasses widening, deep wrinkles, a catchlight of the sky.", line="line006", fx="push", expr="tears"),
    S("S09c", "S09", "sil", "ws", "shade", "SIDE", ["OGATA:OGATA_A", "YUNA:YUNA"], "EXT_BENCH", "Side wide from across the alley: the old man on the bench in the willow shade and the young clerk crouching beside him, both backlit silhouettes, their mouths not visible, the sunlit street beyond.",
      motion="Willow branches sway gently, the old man slowly lowers the cup, the clerk stays crouched. No one stands up or walks."),
    S("S10a", "S10", "face", "ms", "shade", "LA", ["OGATA:OGATA_A"], "EXT_BENCH", "Low angle from below the bench: Ogata sits alone under the willow holding the paper cup, branches and sky above.", line="line007",
      motion="Ogata stares into the cup, breathing slowly; the willow sways. He does not turn his head."),
    S("S10b", "S10", "ins", "ecu", "shade", "EL", ["OGATA:OGATA_A"], "EXT_BENCH", "Insert: an old man's hand slides a worn brown leather notebook back into the inner pocket of a grey linen jacket without opening it."),
    S("S10c", "S10", "sil", "ews", "shade", "HA", ["OGATA:OGATA_A"], "EXT_DAY", "Wide high view: a small old man alone on the bench under the great willow beside the store.", line="line008", fx="pull",
      motion="Willow branches sway; the old man stays still on the bench."),
    S("S11a", "S11", "face", "ms", "kitchen", "HA", ["YUNA:YUNA_IZ"], "IZAKAYA", "High angle medium: Yuna scrubbing a pot at a stainless sink piled with dishes in an izakaya back kitchen at night, tired.", line="line009", fx="pan",
      motion="Yuna scrubs the pot with slow tired strokes; steam rises; water runs. She keeps looking down."),
    S("S11b", "S11", "ins", "ecu", "kitchen", "OH", ["YUNA:YUNA_IZ"], "IZAKAYA", "Insert from above: a folded blank sheet of paper in an open locker and a smartphone lighting up with a blank notification panel; a gloved hand pauses at the edge.", line="line010"),
    S("S11c", "S11", "react", "cu", "kitchen", "EL", ["YUNA:YUNA_IZ"], "IZAKAYA", "Close-up of Yuna in the dim back corner of the izakaya kitchen, her worried face lit by a phone screen held below frame, steam behind her."),
    S("S12a", "S12", "sil", "ws", "ward", "EL", ["HARUKO:HARUKO", "YUNA:YUNA"], "HOSP6", "Wide through a gap in the pale mint privacy curtains: the window bed of a six-bed ward, Haruko sitting up, Yuna on the chair beside her; faces small.",
      motion="The curtain edge stirs slightly in the foreground; the two figures stay still."),
    S("S12b", "S12", "d", "cu", "ward", "EL", ["HARUKO:HARUKO"], "HOSP6", "Chest-up close-up of Haruko leaning back against raised pillows by the window, warm worried smile, window light behind her.", line="line011"),
    S("S12c", "S12", "face", "ms", "ward", "EL", ["YUNA:YUNA", "HARUKO:HARUKO"], "HOSP6", "Over Yuna's shoulder from behind (her ponytail in the foreground, her mouth not visible) toward Haruko in bed, smiling.", line="line012",
      motion="Haruko smiles and nods slightly; Yuna's head stays still with her back to the camera."),
    S("S12d", "S12", "ins", "ecu", "ward", "OH", ["HARUKO:HARUKO", "YUNA:YUNA"], "HOSP6", "Insert from above: an old woman's thin hand with a green jade ring clasping a young woman's bandaged hand on a white blanket.", line="line013"),
    S("S13a", "S13", "sil", "ews", "flash", "LA", ["OLDHANDS", "CHILD"], "WELL_GOLD", "Flashback: low angle from beside the stone well, the backs of an older woman and a small girl crouching at the water's edge, silhouetted against the low golden sun through willows. No faces.", line="line014",
      motion="The two figures stay crouched with their backs to the camera; willow branches sway in the golden light."),
    S("S13a2", "S13", "ins", "ecu", "flash", "LA", [], "WELL_WATER", "Flashback insert, no people: moss on the rim of the old stone well and a hanging willow branch against the low amber sun."),
    S("S13a3", "S13", "ins", "cu", "flash", "SIDE", ["OLDHANDS"], "WELL_WATER", "Flashback insert from the side: the older woman's wrinkled hand and floral sleeve lowering a dried gourd dipper into the dark well water; no face."),
    S("S13b", "S13", "ins", "ecu", "flash", "OH", ["OLDHANDS"], "WELL_WATER", "Flashback insert from above: wrinkled hands scoop clear water with a dried gourd dipper and float a single long narrow willow leaf on it.", line="line015"),
    S("S13b2", "S13", "ins", "ms", "flash", "BE", ["OLDHANDS", "CHILD"], "WELL_GOLD", "Flashback from above and behind: the small girl's two low pigtails and the older woman's floral blouse shoulder beside the well as she bends to the dipper; no faces."),
    S("S13b3", "S13", "ins", "ecu", "flash", "SIDE", [], "WELL_WATER", "Flashback side macro, no people: a long narrow willow leaf drifting down onto the clear water in the gourd dipper."),
    S("S13c", "S13", "ins", "ecu", "flash", "EL", ["CHILD"], "WELL_WATER", "Flashback insert: a small child's hands receive the gourd dipper with the willow leaf floating on the water.", line="line016"),
    S("S13c2", "S13", "estill", "ws", "flash", "HA", [], "WELL_GOLD", "Flashback, no people: high angle of the old stone well and the weeping willow, the water surface glinting in amber dusk, soft vignette."),
    S("S14a", "S14", "sil", "ews", "office", "HA", ["SAKA:SAKA", "YUNA:YUNA"], "OFFICE_DOOR", "High angle from the ceiling corner of the cramped back office: Sakamoto with his back to the camera on the phone, bowing slightly; Yuna stiff by the door.", line="line017",
      motion="Sakamoto bobs his head slightly as he talks on the phone, back to the camera; Yuna stays still."),
    S("S14b", "S14", "ins", "ecu", "office", "EL", ["SAKA:SAKA"], "OFFICE_DESK", "Insert: a finger with a thick gold wristwatch taps a small CCTV monitor showing a grainy grey image of a young woman giving a cup to an old man outside.", line="line018"),
    S("S14b2", "S14", "ins", "ecu", "office", "OH", [], "OFFICE_DESK", "Insert from above, no people: on the cluttered desk a blank printed photo sheet, a red ink pad and a blank form under the hard top light."),
    S("S14c", "S14", "face", "ms", "office", "SIDE", ["YUNA:YUNA"], "OFFICE", "Side medium of Yuna by the office door, head bowed, cold top light on her hair, her mouth hidden.", line="line019",
      motion="Yuna keeps her head bowed and fiddles with the hem of her uniform; she does not look up."),
    S("S14d", "S14", "sil", "ms", "office", "LA", ["SAKA:SAKA"], "OFFICE", "Low angle side-rear medium of Sakamoto stepping toward the camera side, a silhouette under the overhead tube; mouth not visible.", line="line020", fx="dutch5+hh",
      motion="Sakamoto leans forward and gestures sharply once; his face stays turned away from the camera."),
    S("S14d2", "S14", "ins", "ecu", "office", "SIDE", ["YUNA:YUNA"], "OFFICE_DOOR", "Side macro insert: a young woman's hands clenched on the hem of her striped uniform shirt, knuckles white, trembling."),
    S("S14e", "S14", "ins", "ecu", "office", "OH", ["SAKA:SAKA"], "P_BADGE", "Insert from above: a blank white sheet of paper is slapped onto a grey desk, other papers scatter; a hand with a gold watch pulls away.", line="line021"),
    S("S14f", "S14", "ins", "ecu", "office", "EL", ["YUNA:YUNA"], "OFFICE_DESK", "Insert: a smartphone on the desk vibrates and lights up with a blank notification panel; a man's eyes (glasses edge) glance at it in the soft background."),
    S("S14g", "S14", "d", "cu", "office", "LA", ["SAKA:SAKA"], "OFFICE", "Chest-up close-up of Sakamoto from slightly below, smug cold menace, hard top light leaving shadows under his brows.", line="line022", expr="smug"),
    S("S14h", "S14", "d", "ch", "office", "EL", ["YUNA:YUNA"], "OFFICE", "Choker close-up of Yuna biting her lower lip, eyes glistening, holding back tears.", line="line023"),
    S("S14i", "S14", "sil", "ws", "office", "SIDE", ["YUNA:YUNA"], "OFFICE_DESK", "From behind: Yuna alone hunched over the desk writing on a blank sheet, the fluorescent tube flickering above.", line="line024",
      motion="Yuna writes slowly with her back to the camera; the overhead light flickers once."),
    S("S14j", "S14", "ins", "ecu", "office", "EL", [], "OFFICE_DESK", "Insert, no people: a laptop screen showing a blank grey form panel with an attached scanned page (all blank).", line="line025"),
    S("S14j2", "S14", "react", "cu", "office", "HA", ["YUNA:YUNA"], "OFFICE_DESK", "High angle close-up of Yuna at the desk, head bowed, holding back tears under the cold top light."),
    S("S14k", "S14", "sil", "ws", "office", "SIDE", ["YUNA:YUNA"], "OFFICE_DOOR", "From the doorway: the small back office, Yuna's back at the desk under the lonely tube.", line="line026",
      motion="Yuna stays still with her back to the camera; the light hums."),
    # ③ 전개·위기
    S("S15a", "S15", "sil", "ws", "blue", "HA", ["YUNA:YUNA"], "EXT_BLUE", "Blue-hour high angle from a second-floor height across the road, through willow branches: Yuna placing a water bottle on the bench beside the glowing store.", line="line027",
      motion="Yuna bends and sets the bottle on the bench, then straightens up; branches sway."),
    S("S15b", "S15", "ins", "ecu", "blue", "EL", [], "EXT_BENCH", "Insert: an unopened water bottle on the wooden bench with a small blank paper note taped to it, the note fluttering, dusk light."),
    S("S16a", "S16", "empty", "ews", "blue", "LA", [], "SEDAN", "No people visible. Low angle from the asphalt: a glossy black sedan with no emblem parked under an orange streetlight, the rear window sliding down.",
      motion="The rear window slowly slides down; the streetlight flickers faintly. Nobody gets out."),
    S("S16b", "S16", "sil", "ms", "car", "SIDE", ["SATO:SATO"], "SEDAN_IN", "Inside the dark sedan: Sato in the front passenger seat seen from behind and the side, turning slightly back; his mouth is not visible.", line="line028",
      motion="Sato turns his head a few degrees toward the back seat; streetlight slides across his shoulder."),
    S("S16c", "S16", "sil", "cu", "car", "SIDE", ["OGATA:OGATA_B"], "SEDAN_IN", "Close side view of Ogata in the back seat in his suit, a shoulder-up silhouette against the orange-lit window.", line="line029",
      motion="Ogata sits still looking out of the window, breathing slowly."),
    S("S16d", "S16", "sil", "ws", "car", "SIDE", ["OGATA:OGATA_B"], "SEDAN_IN", "From inside the car over Ogata's shoulder (soft foreground) through the open window: across the road the water bottle on the bench under the willow, lit by the store.", line="line030", fx="tilt",
      motion="Almost still; the bottle and willow outside glow; Ogata's shoulder stays still."),
    S("S16d2", "S16", "ins", "ecu", "blue", "EL", [], "EXT_ACROSS", "Telephoto insert, no people: a plain water bottle standing on the bench under the willow, the store glow and orange streetlight melting into bokeh."),
    S("S16e", "S16", "sil", "cu", "car", "SIDE", ["OGATA:OGATA_B"], "SEDAN_IN", "Ogata's face in side silhouette reflected in the dark window glass.", line="line031",
      motion="Ogata blinks slowly; the reflection stays steady."),
    S("S17a", "S17", "face", "ms", "store", "HA", ["SAKA:SAKA"], "EXT_BENCH", "High angle medium in the morning: Sakamoto picks up the water bottle from the bench and tosses it into a trash bin with a sneer.", line="line032", expr="smug",
      motion="Sakamoto picks up the bottle and drops it into the bin with a flick of his wrist; he turns his head less than 15 degrees."),
    S("S17b", "S17", "face", "ms", "blue", "LA", ["YUNA:YUNA"], "EXT_BENCH", "Low angle from bench height past a new water bottle in the foreground: Yuna at dusk setting it down gently.", line="line033",
      motion="Yuna lets go of the bottle and straightens slowly, a small calm look; branches sway."),
    S("S18a", "S18", "sil", "ws", "ward_gold", "SIDE", ["HARUKO:HARUKO", "YUNA:YUNA"], "HOSP6_DUSK", "Sunset by the ward window: Haruko in bed and Yuna on the chair as backlit silhouettes, mouths not visible.", line="line034",
      motion="The two silhouettes stay still; dust motes float in the golden light."),
    S("S18b", "S18", "sil", "cu", "ward_gold", "SIDE", ["HARUKO:HARUKO"], "HOSP6_DUSK", "Haruko's side profile in silhouette against the orange window, looking far away.", line="line035",
      motion="Haruko gazes out of the window, breathing slowly; her lips stay soft and still."),
    S("S18c", "S18", "face", "ms", "ward_gold", "HA", ["YUNA:YUNA"], "HOSP6_DUSK", "High angle from the head of the bed: Yuna on the chair looking up, curious, golden light on her face.", line="line036",
      motion="Yuna tilts her head slightly, curious; her mouth stays closed."),
    S("S18d", "S18", "face", "ms", "ward_gold", "SIDE", ["HARUKO:HARUKO"], "HOSP6_DUSK", "Side medium of Haruko shaking her head gently with a small smile.", line="line037",
      motion="Haruko shakes her head slowly once with a soft smile; lips closed."),
    S("S19a", "S19", "sil", "ews", "well_gold", "LA", ["OGATA:OGATA_B"], "WELL_GOLD", "Low angle extreme wide: Ogata alone at the old stone well at golden hour, small under the glowing willows.", line="line038",
      motion="Willow branches sway in the golden light; Ogata stands still at the water's edge."),
    S("S19b", "S19", "ins", "ecu", "well_gold", "EL", ["SATO:SATO", "OGATA:OGATA_B"], "WELL_GOLD", "Insert: Sato's hand hands a plain black leather folder to Ogata's hand, golden light.", line="line039"),
    S("S19c", "S19", "ins", "ecu", "well_gold", "EL", ["OGATA:OGATA_B"], "P_NOTE", "Insert: an old man's hand closes the worn brown leather notebook; the well and willows soft behind.", line="line040"),
    S("S19d", "S19", "d", "cu", "well_gold", "LA", ["OGATA:OGATA_B"], "WELL_GOLD", "Chest-up close-up of Ogata from slightly below, resolute, golden rim light, the willows soft behind.", line="line041", expr="cold"),
    S("S20a", "S20", "face", "ms", "inspect", "LA", ["SAKA:SAKA"], "INT_LOW", "Low angle from the mirror-polished floor: Sakamoto unrolls a long plain burgundy mat at the entrance, pleased with himself.",
      motion="Sakamoto pushes the rolled mat forward so it unrolls flat; he does not stand up."),
    S("S20b", "S20", "sil", "ms", "inspect", "SIDE", ["SAKA:SAKA", "YUNA:YUNA"], "INT_STOCK", "From behind Sakamoto at the grey stockroom door; Yuna inside the doorway, head bowed.", line="line042",
      motion="Sakamoto points into the stockroom; Yuna steps back half a step. His head stays turned away."),
    S("S20c", "S20", "ins", "ecu", "inspect", "EL", ["YUNA:YUNA"], "INT_STOCK", "Insert: the grey stockroom door swings shut, a young woman's bandaged hand letting go of the handle."),
    S("S20d", "S20", "ins", "ecu", "inspect", "EL", ["SAKA:SAKA"], "EXT_DOOR", "Insert: Sakamoto's reflection in the glass door as his hands straighten his navy tie, pleased.", line="line043"),
    S("S21a", "S21", "empty", "ews", "sun", "LA", [], "SEDANS", "No people. Low angle from the asphalt: three glossy black sedans with no emblems and no plates stop in a row on the sunlit narrow street.",
      motion="The third sedan rolls to a stop; heat haze; no one gets out yet."),
    S("S21b", "S21", "ins", "ecu", "sun", "LA", ["OGATA:OGATA_B"], "SEDANS", "Insert at ground level: a polished black oxford shoe and a charcoal-navy trouser hem step down onto sunlit asphalt from a car door.", fx="jib"),
    S("S22a", "S22", "sil", "ws", "inspect", "EL", ["SAKA:SAKA", "MURASE:MURASE", "SATO:SATO", "OGATA:OGATA_B"], "INT_REV",
      "Wide from behind the counter toward the entrance: the glass door open, Murase and Sato entering first and Ogata behind them as backlit silhouettes against the blinding daylight; Sakamoto bowing 90 degrees on the burgundy mat in the foreground right.",
      motion="The three figures take one slow step inside, backlit; Sakamoto holds his deep bow. No faces visible."),
    S("S22b", "S22", "d", "cu", "inspect", "EL", ["SAKA:SAKA"], "INT_INSPECT", "Chest-up close-up of Sakamoto standing upright, over-eager fawning smile.", line="line044", expr="fawn"),
    S("S22c", "S22", "sil", "ms", "inspect", "HA", ["SAKA:SAKA"], "INT_INSPECT", "High angle: Sakamoto bowing deeply on the burgundy mat, the top of his slick head toward the camera.",
      motion="Sakamoto holds the deep bow, perfectly still except for breathing."),
    S("S23a", "S23", "face", "ms", "inspect", "EL", ["SAKA:SAKA"], "INT_INSPECT", "Medium (chest up, not closer): Sakamoto lifting his head from the bow, frozen recognition, eyes widening, the store shelves behind him.", fx="dollyzoom", expr="shock",
      motion="Sakamoto slowly raises his head from the bow and freezes; his glasses slip slightly. No other movement."),
    S("S23b", "S23", "ins", "ecu", "inspect", "EL", ["SAKA:SAKA"], "INT_INSPECT", "Insert: a trembling hand with a gold watch gripping the navy necktie."),
    S("S23c", "S23", "reuse:S04a", "ecu", "sun", "EL", [], None, "0.5-second flash of S04a (the hand sliding down the glass)."),
    S("S23d", "S23", "d", "cu", "inspect", "LA", ["OGATA:OGATA_B"], "INT_INSPECT", "Chest-up close-up of Ogata from slightly below, calm and cold, bright backlight rim on his white hair.", line="line045", expr="cold"),
    S("S23e", "S23", "ins", "ecu", "inspect", "EL", ["SAKA:SAKA"], "INT_INSPECT", "Insert: a bead of sweat runs down Sakamoto's temple past the rim of his rectangular glasses.", line="line046"),
    S("S24a", "S24", "face", "ms", "confront", "HA", ["SAKA:SAKA"], "INT_INSPECT", "High angle from Ogata's point of view: Sakamoto sweating, shrinking, eyes darting.", expr="shock",
      motion="Sakamoto swallows and his eyes dart sideways; he stays where he is."),
    S("S24b", "S24", "d", "cu", "confront", "LA", ["OGATA:OGATA_B"], "INT_INSPECT", "Chest-up close-up of Ogata from slightly below, quiet and heavy, looking around the store.", line="line047", expr="cold"),
    S("S24c", "S24", "sil", "ms", "confront", "HA", ["SAKA:SAKA"], "INT_INSPECT", "High angle on the top of Sakamoto's slick head as he bows his head, stammering; mouth not visible.", line="line048",
      motion="Sakamoto lowers his head further, shoulders hunched."),
    S("S25a", "S25", "sil", "ews", "cctv", "BE", ["SAKA:SAKA", "MURASE:MURASE", "SATO:SATO", "OGATA:OGATA_B"], "INT_CEIL", "High angle from the ceiling corner like a security camera: four small figures frozen in the aisle; nobody moves.", line="line049",
      motion="Completely still figures; only the refrigerator light flickers faintly."),
    S("S25b", "S25", "ins", "ecu", "confront", "EL", [], "INT_STOCK", "Insert, no people: the handle of the grey stockroom door in silence.", line="line050"),
    S("S25c", "S25", "estill", "ws", "confront", "HA", [], "INT_AISLE", "No people. High angle down the empty store aisle toward the closed grey stockroom door, polished floor reflections, stillness."),
    # ④ 절정·결말
    S("S26a", "S26", "face", "ms", "store", "EL", ["OGATA:OGATA_B", "YUNA:YUNA"], "INT_STOCK", "Ogata's shoulder and white hair soft in the left foreground; the stockroom door open on the right with Yuna stepping out, surprised.", fx="rack",
      motion="Yuna steps out of the doorway and stops, eyes widening; Ogata's shoulder stays still."),
    S("S26b", "S26", "d", "cu", "store", "EL", ["YUNA:YUNA"], "INT_AISLE", "Chest-up close-up of Yuna, worried and relieved at once, soft diffused light.", line="line051"),
    S("S26c", "S26", "react", "ecu", "store", "EL", ["OGATA:OGATA_B"], "INT_AISLE", "Close-up of Ogata's eyes softening behind his glasses, a faint smile.", line="line052", fx="push"),
    S("S26d", "S26", "face", "ms", "store", "EL", ["OGATA:OGATA_B", "YUNA:YUNA"], "INT_AISLE", "Over Ogata's shoulder from behind (his white hair foreground, mouth not visible) toward Yuna listening.", line="line053",
      motion="Yuna listens and blinks; Ogata's head stays still with his back to the camera."),
    S("S26e", "S26", "face", "cu", "store", "EL", ["YUNA:YUNA", "OGATA:OGATA_B"], "INT_AISLE", "Tighter over Yuna's shoulder from behind (her ponytail soft at the frame edge, mouth not visible): close-up of Ogata listening.", line="line054",
      motion="Ogata listens, nodding very slightly; Yuna's head stays still with her back to the camera."),
    S("S26e2", "S26", "react", "ch", "store", "EL", ["OGATA:OGATA_B"], "INT_AISLE", "Choker close-up of Ogata frozen, eyes widening behind his glasses as the words sink in."),
    S("S26f", "S26", "ins", "ecu", "store", "OH", ["OGATA:OGATA_B"], "P_NOTE", "Insert from above: an old hand opens the worn leather notebook to a yellowed pressed long narrow willow leaf under clear film."),
    S("S26g", "S26", "d", "cu", "store", "EL", ["OGATA:OGATA_B"], "INT_AISLE", "Chest-up close-up of Ogata, voice thickening, eyes wet behind the glasses.", line="line055", expr="tears"),
    S("S26h", "S26", "ins", "ecu", "store", "OH", ["OGATA:OGATA_B"], "P_NOTE", "Macro insert: a single tear drops onto the pressed willow leaf in the open notebook."),
    S("S26h2", "S26", "ins", "ecu", "store", "SIDE", ["OGATA:OGATA_B"], "P_NOTE", "Side macro insert: an old thumb gently brushing the edge of the pressed long narrow willow leaf under the clear film."),
    S("S26i", "S26", "sil", "ms", "ward_gold", "SIDE", ["OGATA:OGATA_B"], "INT_REV", "Side silhouette of Ogata against the bright glass front, holding the open notebook to his chest.", line="line056",
      motion="Ogata lowers his head slightly and holds the notebook still."),
    S("S26j", "S26", "react", "cu", "store", "HA", ["YUNA:YUNA"], "INT_AISLE", "Slight high angle close-up of Yuna holding back tears, eyes brimming.", line="line057", fx="push"),
    S("S27a", "S27", "sil", "ms", "confront", "SIDE", ["OGATA:OGATA_B"], "INT_REV", "From behind: Ogata standing still, not turning around.", line="line058",
      motion="Ogata stands perfectly still with his back to the camera."),
    S("S27b", "S27", "ins", "ecu", "confront", "EL", ["MURASE:MURASE"], "INT_REV", "Insert: a black tablet in a woman's hands shows grainy black-and-white security footage of a man pushing an old man out of a glass door.", fx="dutch7"),
    S("S27c", "S27", "face", "ms", "confront", "LA", ["MURASE:MURASE"], "INT_REV", "Low angle medium of Murase holding the tablet, crisp and official, seen three-quarter from the side.", line="line059",
      motion="Murase lowers the tablet slightly and looks straight ahead; she does not walk."),
    S("S27c2", "S27", "ins", "ecu", "confront", "OH", ["MURASE:MURASE"], "INT_REV", "Insert from above: a woman's finger swipes the black tablet to a blank grey official document panel."),
    S("S27c3", "S27", "react", "ms", "confront", "HA", ["SAKA:SAKA"], "INT_REV", "High angle medium of Sakamoto standing stiff with hunched shoulders, eyes darting, cold daylight.", expr="shock"),
    S("S27d", "S27", "face", "ms", "confront", "EL", ["SAKA:SAKA", "OGATA:OGATA_B"], "INT_REV", "Over Sakamoto's shoulder from behind (his slick head foreground, pleading hands at frame edge, mouth not visible) toward Ogata, unmoved.", line="line060", fx="hh",
      motion="Sakamoto's hands shake as he pleads; Ogata stays perfectly still."),
    S("S27e", "S27", "sil", "ews", "confront", "BE", ["SAKA:SAKA"], "INT_LOW", "Bird's-eye view straight down: Sakamoto prostrate in dogeza on the mirror-polished floor, his reflection beneath him.", fx="pull",
      motion="Sakamoto stays prostrate; his shoulders tremble slightly."),
    S("S27f", "S27", "ins", "ecu", "confront", "EL", [], "INT_LOW", "Macro insert: a drop of sweat falls onto the mirror-polished floor."),
    S("S27g", "S27", "d", "cu", "confront", "LA", ["OGATA:OGATA_B"], "INT_REV", "Chest-up close-up of Ogata from slightly below, calm and steely, delivering the verdict.", line="line061", fx="push", expr="cold"),
    S("S27h", "S27", "reuse:S27e", "ews", "confront", "BE", [], None, "B-roll reuse of S27e under the rest of line061."),
    S("S27i", "S27", "face", "ms", "confront", "SIDE", ["MURASE:MURASE"], "INT_REV", "Side medium of Murase announcing, tablet against her chest.", line="line062",
      motion="Murase speaks seen from the side, her mouth not visible behind the angle; she stays still."),
    S("S27i2", "S27", "ins", "ecu", "confront", "EL", ["SAKA:SAKA"], "INT_REV", "Macro insert: a bead of sweat drips from a man's jaw onto the mirror-polished floor."),
    S("S27j", "S27", "face", "ms", "confront", "SIDE", ["MURASE:MURASE", "YUNA:YUNA"], "INT_AISLE", "Side medium: Murase bows respectfully to Yuna; Yuna bows back deeply.", line="line063",
      motion="Murase bows slightly; Yuna answers with a deep bow. No one walks."),
    S("S27k", "S27", "ins", "ecu", "confront", "EL", ["SAKA:SAKA"], "INT_REV", "Insert: trembling fingers with a gold watch unclip the blank white name plate from the striped vest."),
    S("S27l", "S27", "ins", "ecu", "confront", "OH", ["SAKA:SAKA"], "INT_LOW", "Macro: Sakamoto's own blurred face reflected in the mirror-polished floor.", line="line064"),
    S("S27m", "S27", "sil", "ws", "inspect", "SIDE", ["SAKA:SAKA"], "INT_REV", "From behind: Sakamoto walks away across the burgundy mat and out through the glass door into the blinding glare.",
      motion="Sakamoto walks slowly away from the camera across the mat and out of the door, growing smaller; he never turns around."),
    S("S28a", "S28", "sil", "ws", "ward_gold", "EL", ["HARUKO:HARUKO", "OGATA:OGATA_B", "YUNA:YUNA"], "PRIV_DUSK", "Wide through a gap in the curtain: a private hospital room at golden hour, Haruko in bed, Ogata on the chair, Yuna at the foot of the bed; faces small.",
      motion="Golden light; the three stay still; the curtain edge stirs."),
    S("S28b", "S28", "sil", "ms", "ward_gold", "SIDE", ["OGATA:OGATA_B"], "PRIV_DUSK", "Side-rear medium of Ogata leaning toward the bed, humble; his mouth not visible.", line="line065",
      motion="Ogata bows his head slightly toward the bed and stays still."),
    S("S28b2", "S28", "react", "cu", "ward_gold", "EL", ["HARUKO:HARUKO"], "PRIV_DUSK", "Close-up of Haruko against the raised pillows, puzzled and searching his face, golden backlight in her silver hair."),
    S("S28b3", "S28", "ins", "ecu", "ward_gold", "SIDE", ["HARUKO:HARUKO"], "PRIV_DUSK", "Side macro insert: Haruko's thin hand with the green jade ring tightening on the cream blanket, golden light."),
    S("S28c", "S28", "ins", "ecu", "ward_gold", "OH", ["HARUKO:HARUKO", "OGATA:OGATA_B"], "PRIV_DUSK", "Insert from above: Haruko's thin hands with the jade ring hold an old man's hand on the white blanket.", line="line066", fx="tilt"),
    S("S28d", "S28", "ins", "ecu", "ward_gold", "OH", ["HARUKO:HARUKO"], "P_PHOTO", "Insert from above: the open leather notebook on the blanket with the pressed willow leaf and a small faded black-and-white photo of a teenage girl at a stone well; an old finger with a green jade ring stops on the photo."),
    S("S28e", "S28", "d", "cu", "ward_gold", "EL", ["HARUKO:HARUKO"], "PRIV_DUSK", "Chest-up close-up of Haruko, trembling recognition, tears welling, golden backlight.", line="line067"),
    S("S28f", "S28", "sil", "cu", "ward_gold", "SIDE", ["OGATA:OGATA_B"], "PRIV_DUSK", "Ogata in side silhouette against the golden window, stunned.", line="line068",
      motion="Ogata freezes, then his head lowers a few degrees."),
    S("S28g", "S28", "face", "ms", "ward_gold", "SIDE", ["HARUKO:HARUKO"], "PRIV_DUSK", "Side medium of Haruko looking down at the photo, finger on it, remembering.", line="line069",
      motion="Haruko looks down at the photo, her finger resting on it; lips soft."),
    S("S28h", "S28", "d", "ch", "ward_gold", "EL", ["OGATA:OGATA_B"], "PRIV_DUSK", "Choker close-up of Ogata breaking down, tears behind the glasses, golden rim light.", line="line070", expr="tears"),
    S("S28i", "S28", "ins", "ecu", "ward_gold", "EL", ["YUNA:YUNA"], "PRIV_DUSK", "Insert: a young woman's bandaged hand covers her mouth, a tear on her cheek edge."),
    S("S28j", "S28", "face", "ms", "ward_gold", "EL", ["OGATA:OGATA_B", "YUNA:YUNA"], "PRIV_DUSK", "Over Ogata's shoulder from behind (white hair foreground, mouth not visible) toward Yuna, tearful.", line="line071",
      motion="Yuna's lips tremble and tears fall; Ogata's head stays still."),
    S("S28j2", "S28", "ins", "ecu", "ward_gold", "OH", ["HARUKO:HARUKO", "YUNA:YUNA"], "P_PHOTO", "Insert from above: a young hand and an old hand with a green jade ring clasped over an old faded photograph on the blanket."),
    S("S28k", "S28", "react", "ch", "ward_gold", "EL", ["YUNA:YUNA"], "PRIV_DUSK", "Choker close-up of Yuna crying, her bandaged hand over her mouth, nodding.", line="line072", fx="push"),
    S("S29a", "S29", "sil", "ews", "mist", "LA", ["YUNA:YUNA", "HARUKO:HARUKO", "OGATA:OGATA_B"], "WELL_MIST", "Low angle from water level in the morning mist: the backs of Yuna pushing Haruko in a wheelchair and Ogata beside them at the stone well, reflected in the water.", line="line073",
      motion="Mist drifts over the water; the three stay still with their backs to the camera."),
    S("S29b", "S29", "ins", "ecu", "mist", "OH", [], "WELL_WATER", "Overhead macro: two long narrow willow leaves float side by side on the clear spring water and drift slowly.", fx="pan"),
    S("S29b2", "S29", "ins", "ecu", "mist", "SIDE", [], "WELL_WATER", "Side macro insert, no people: a drop of water falls from the tip of a willow leaf into the misty spring, a ring of ripples."),
    S("S29c", "S29", "empty", "ews", "mist", "HA", [], "WELL_MIST", "Extreme wide from high above: the old stone well, the willows and the quiet town in morning mist; three tiny figures at the edge.", line="line074", fx="pull",
      motion="Mist drifts slowly; willow branches sway; the tiny figures stay still."),
]

CARDS = {"H3": "柳の葉と一杯の水", "S01a": "八月　鎌倉", "S21a": "土曜日"}
JA_OVERLAY = {"S11b": "休学届 + 病院未納通知", "S14b": "CCTV(그림만)", "S14e": "始末書", "S14f": "病院未納通知(2回目)",
              "S14j": "在庫ロス原因報告", "S15b": "喉の渇いた方、どうぞお持ちください(Klee One)", "S27b": "CCTV + 帳簿 + 始末書",
              "S20a": "—", "S27k": "店長代理 坂本(명찰)", "S02a": "店長代理 坂本(명찰, 작게)"}
# 화면 속 가상 표기(사용자 확정 2026-10-05): 키프레임은 무지로 생성 → 로컬 실글꼴·원근 합성
SIGN_STORE = "간판 「やなぎマート 鎌倉店」+측면 「24H」(scripts/yanagi_signage.py)"
SIGN_DOOR = "문 옆 판 「やなぎマート 鎌倉店 / 運営:緒方ホールディングス株式会社」"
SIGN_PLATE = "번호판 「品川 300 あ ・・・1」(뒤차 ・・・2·・・・3), 엠블럼 없음"
SIGNAGE_BY_LOC = {"EXT_DAY": [SIGN_STORE, SIGN_DOOR], "EXT_BENCH": [SIGN_STORE], "EXT_DOOR": [SIGN_STORE, SIGN_DOOR],
                  "EXT_LOW": [SIGN_STORE], "EXT_ACROSS": [SIGN_STORE], "EXT_THROUGH": [SIGN_STORE, SIGN_DOOR], "EXT_BLUE": [SIGN_STORE],
                  "SEDAN": [SIGN_PLATE], "SEDANS": [SIGN_PLATE]}
NAMEPLATE = {"SAKA": "店長代理 坂本", "YUNA": "沖"}  # 명찰 실글꼴 합성(사용자 지시 2026-10-04: 상황에 맞게 새김)
AMBIENCE = {
    "S01a": "loud cicadas in a hot summer street, distant scooter", "S01b": "cicadas, faint air conditioner hum",
    "S04a": "dull thud against glass, cicadas", "S07a": "tiny water drop", "S13b": "trickling spring water, evening cicadas",
    "S14j": "laptop fan hum", "S15b": "evening crickets, soft breeze", "S16a": "electric car window motor, crickets",
    "S21a": "tires rolling on asphalt, engines cutting off", "S25b": "refrigerator motor hum", "S27f": "tiny drop on a hard floor",
    "S29b": "trickling spring water, early birds", "S29c": "early morning birds, soft breeze over water",
}
BGM = [
    (0.0, 40.0, 0.40, "tense low cello pulse and sparse piano, Japanese drama cold open, heartbeat-like rhythm, instrumental, no vocals"),
    (41.0, 172.0, 0.40, "gentle melancholic solo piano, Japanese human drama (ninjo) film score, summer nostalgia, slow, instrumental, no vocals"),
    (173.0, 330.0, 0.38, "dry tense strings and muted piano, quiet injustice, suspense under the surface, slow, instrumental, no vocals"),
    (331.0, 416.0, 0.42, "rising suspense, low drums and strings building to a reveal, Japanese drama score, instrumental, no vocals"),
    (417.5, 508.0, 0.40, "tender piano and solo cello, emotional revelation, Japanese family drama film score, slow, instrumental, no vocals"),
    (509.0, None, 0.42, "warm strings and piano, heartfelt resolution with gentle hope, Japanese drama finale, slow, instrumental, no vocals"),
]
STYLE = {"NA": "Naration", "緒方": "Ogata", "坂本": "Sakamoto", "結菜": "Yuna", "春子": "Haruko", "佐藤": "Sato", "村瀬": "Murase"}
STYLE_JA = {"Naration": "ナレーター", "Ogata": "緒方", "Sakamoto": "坂本", "Yuna": "結菜", "Haruko": "春子", "Sato": "佐藤", "Murase": "村瀬"}
STYLE_COLOR = {"Naration": "&H00DDDDDD", "Ogata": "&H00FFFFFF", "Sakamoto": "&H00B4D2FF", "Yuna": "&H00C8F0FF",
               "Haruko": "&H00D2E6C8", "Sato": "&H00E6E6E6", "Murase": "&H00E6DCF0"}
PRO_MODEL = "fal-ai/bytedance/seedance/v1/pro/image-to-video"
RATE = {"pro": 0.108, "lite": 0.036, "omni": 0.16, "kf": 0.04}


def tc(sec):
    fr = int(round(sec * FPS)); s, f = divmod(fr, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}.{f:02d}"


def ass_t(sec):
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap(text, limit=19):
    """libass는 일본어 자동 줄바꿈 불가 → 19자 기준으로 구두점에서 수동 \\N (EP3 실증)."""
    out, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= limit and ch in "、。…!?？！』」":
            out.append(cur); cur = ""
    if cur:
        out.append(cur)
    if len(out) > 2:  # 3줄 이상이면 둘로 다시 나눔
        mid = len(text) // 2
        cands = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "、。…"]
        cut = min(cands, key=lambda i: abs(i - mid)) if cands else mid
        out = [text[:cut], text[cut:]]
    return "\\N".join(out)


def script_lines():
    t = open(os.path.join(PROD, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 4-1.")[0]
    out, cur = [], None
    for l in body.split("\n"):
        s = l.strip()
        m = re.match(r"^(NA\d+|[^\s:「→]{1,6}):(【OMNI】)?(\([^)]*\))?「(.*)$", s)
        if m:
            cur = {"spk": m.group(1), "text": m.group(4)}
            out.append(cur)
            if s.endswith("」"):
                cur["text"] = cur["text"][:-1]; cur = None
        elif cur and s and not s.startswith("→"):
            cur["text"] += s
            if s.endswith("」"):
                cur["text"] = cur["text"][:-1]; cur = None
    return [x for x in out if x["spk"] != "진행자"][1:]


def check_rules(shots):
    """규격 제8장 7 자동 검사: 연속 같은 구도(A1)·왜곡 횟수(A9)·OMNI 측면 금지·사이즈/렌즈 필수·8초."""
    errs = []
    order = ["ecu", "ch", "cu", "ms", "ws", "ews"]
    prev = None
    for s in shots:
        if not s["lens"] or not s["angle"]:
            errs.append(f"{s['id']}: 사이즈·앵글 비어 있음")
        if s["kind"] == "d" and s["angle"] in ("SIDE", "BE", "OH"):
            errs.append(f"{s['id']}: OMNI 대사 컷 각도 {s['angle']} 금지(정면~45°만)")
        if prev and prev["scene"] == s["scene"] and not s["kind"].startswith("reuse") and not prev["kind"].startswith("reuse"):
            same_size = abs(order.index(prev["lens"]) - order.index(s["lens"])) < 1
            if same_size and prev["angle"] == s["angle"] and prev["loc"] == s["loc"]:
                errs.append(f"{prev['id']}→{s['id']}: 연속 같은 구도(A1)")
        prev = s
    dz = sum(1 for s in shots if "dollyzoom" in s["fx"])
    dutch = sum(1 for s in shots if "dutch" in s["fx"])
    if dz != 1:
        errs.append(f"돌리줌 {dz}회(1회만)")
    if dutch > 2:
        errs.append(f"더치 {dutch}회(최대 2회)")
    return errs


def main():
    lock = json.load(open(os.path.join(PROD, "lock.json")))
    rows = {r["id"]: r for r in lock["rows"]}
    texts = script_lines()
    assert len(texts) == len(rows) == 74, (len(texts), len(rows))
    scenes = {s[0]: (s[1], s[2]) for s in lock["scenes"]}
    ad_times = [a[1] for a in lock["ads"]]
    main_end = lock["main_end"]

    errs = check_rules(SHOTS)
    if errs:
        raise SystemExit("앵글 규칙 위반:\n  " + "\n  ".join(errs))
    used = [s["line"] for s in SHOTS if s["line"]]
    assert sorted(used) == sorted(rows), set(rows) ^ set(used)

    # ---------- 샷 타이밍: 대사 앵커 + 앵커 사이 균등 분배 ----------
    hook = [s for s in SHOTS if s["scene"] == "H"]
    hook_len = {"H0": 2.0, "H1": 7.0, "H2": 4.0, "H3": 7.0}
    starts = {}
    lag_report = []
    t = 0.0
    for s in hook:
        starts[s["id"]] = t; t += hook_len[s["id"]]
    by_scene = collections.OrderedDict()
    for s in SHOTS:
        if s["scene"] != "H":
            by_scene.setdefault(s["scene"], []).append(s)
    for sc, shots in by_scene.items():
        a, b = scenes[sc]
        anchors = []
        for k, s in enumerate(shots):
            if s["line"]:
                st = max(a, rows[s["line"]]["start"] - LEAD)
                for ad in ad_times:  # 광고 지점을 넘어 당겨지지 않게
                    if rows[s["line"]]["start"] >= ad - 1e-6 and st < ad:
                        st = ad
                anchors.append((k, st))
        pts = [(0, a)] + [x for x in anchors if x[0] != 0] if not anchors or anchors[0][0] != 0 else anchors
        if pts[0][0] != 0:
            pts = [(0, a)] + pts
        pts.append((len(shots), b))
        # 광고 지점에서 시작하는 인서트(S26f) — 앵커 없는 컷이 광고 시각에 시작하도록
        ad_pins = {}
        for ad in ad_times:
            if a < ad < b:
                k_ad = next((k for k, s in enumerate(shots) if s["line"] and rows[s["line"]]["start"] >= ad - 1e-6), None)
                if k_ad is not None:
                    k0 = k_ad
                    while k0 > 0 and not shots[k0 - 1]["line"] and shots[k0 - 1]["kind"] in ("ins",):
                        k0 -= 1
                    if k0 < k_ad:
                        ad_pins[k0] = ad
                        pts = [p for p in pts if p[0] != k0] + [(k0, ad)]
                        pts.sort()
        want = [0.0] * len(shots)
        for (k1, t1), (k2, t2) in zip(pts, pts[1:]):
            n = max(1, k2 - k1)
            for j in range(k1, k2):
                want[j] = t1 + (t2 - t1) * (j - k1) / n
        # 최소 길이 보장: 앵커 컷은 대사 시작보다 늦게 들어가도 된다(앞 컷 위로 소리 선행 = J컷).
        # 광고 지점에서 시작하는 컷과 장면 시작은 고정한다.
        pins = {0: a, len(shots): b}
        pins.update(ad_pins)
        for k, t0 in pts:  # 광고 지점에서 시작하는 대사 컷(앞에 인서트가 없을 때)
            if k not in pins and any(abs(t0 - ad) < 1e-6 for ad in ad_times) and not any(abs(v - t0) < 1e-6 for v in ad_pins.values()):
                pins[k] = t0
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
    ends = {}
    for k, sid in enumerate(order_ids):
        ends[sid] = starts[order_ids[k + 1]] if k + 1 < len(order_ids) else main_end
    # OMNI 8초 상한: 넘으면 다음 컷(B롤)이 시작되도록 경계를 당긴다
    for k, s in enumerate(SHOTS):
        if s["kind"] == "d" and ends[s["id"]] - starts[s["id"]] > OMNI_MAX:
            nxt = order_ids[k + 1]
            new = starts[s["id"]] + OMNI_MAX
            starts[nxt] = new; ends[s["id"]] = new
    bad = [(sid, ends[sid] - starts[sid]) for sid in order_ids if ends[sid] - starts[sid] < MIN_SHOT and sid not in ("S23c",)]
    if bad:
        raise SystemExit("너무 짧은 컷: " + ", ".join(f"{a}={b:.2f}s" for a, b in bad))
    # 너무 긴 컷: 정지성 컷 6.5초(제4장 시각 환기·제6장 리액션 7초), i2v 10초(생성 상한)
    STILL_KINDS, I2V_KINDS = ("react", "ins", "estill"), ("face", "sil", "empty")
    long_ = [(s["id"], ends[s["id"]] - starts[s["id"]]) for s in SHOTS
             if (s["kind"] in STILL_KINDS and ends[s["id"]] - starts[s["id"]] > STILL_MAX)
             or (s["kind"] in I2V_KINDS and ends[s["id"]] - starts[s["id"]] > I2V_MAX)]
    if long_:
        raise SystemExit("너무 긴 컷: " + ", ".join(f"{a}={b:.2f}s" for a, b in long_))

    # ---------- 출력 데이터 ----------
    durations, sb, scene_items = [], [], []
    cost = collections.Counter()
    for s in SHOTS:
        sid = s["id"]; d = ends[sid] - starts[sid]
        durations.append(round(d + HARD, 4))
        refs, ids = [], []
        for w in s["who"]:
            key, _, ward = w.partition(":")
            desc, cell = WHO[key]
            ids.append(f"{desc}" + (f", wearing {WARD[ward]}" if ward else ""))
            if s["expr"] and (key, s["expr"]) in EXPR:
                refs.append(EXPR[(key, s["expr"])])
            elif ward == "OGATA_B":
                refs.append(EXPR[("OGATA_B", "front")])
            elif cell:
                refs.append(cell)
        if s["loc"]:
            refs.append(LOC[s["loc"]])
        n_people = len([w for w in s["who"]])
        comp = ("Exactly one person in frame, no foreground shoulder, hands out of frame, chest-up single close-up, facing the camera within 30 degrees."
                if s["kind"] == "d" else
                ("Completely unpopulated: no people, no hands." if s["kind"] in ("empty", "estill") or (s["kind"] == "ins" and not s["who"]) else
                 f"Exactly {n_people} {'person' if n_people == 1 else 'people'} (or their hands) as described, no extra people."))
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/yanagi-keyframes/{sid}-1.png"
        kf_prompt = None
        if keyframe:
            kf_prompt = " ".join([
                PRESET + ".", s["subject"], ("Characters: " + " | ".join(ids) + ".") if ids else "",
                f"Camera: {ANGLE[s['angle']]}, {LENS[s['lens']]}.", f"Lighting: {LIGHT[s['light']]}.", comp, PLAIN,
                "Name plates on uniforms stay completely blank (Japanese lettering is composited later).",
                f"Negative: {NEGATIVE}."]).strip()
            cost["kf"] += 1
        tier = {"d": "omni", "react": "still", "ins": "still", "estill": "still", "face": "pro", "sil": "lite", "empty": "lite", "card": "card"}.get(s["kind"], "reuse")
        gen = 10 if d > 5.0 else 5
        item = {"prompt": "", "duration": gen}
        if tier in ("pro", "lite"):
            motion = s["motion"] or "Subtle natural motion only, micro movements, no new people."
            item["prompt"] = ("Static, locked off camera. Motion: " + motion +
                              " Keep the exact faces, wardrobe, props and lighting of the first frame. Head turns under 20 degrees. "
                              "No walking toward the camera, no new people, no text.")
            item["image"] = keyframe
            if tier == "pro":
                item["i2v_model"], item["i2v_resolution"] = PRO_MODEL, "1080p"
                cost["pro"] += gen
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
        sb.append({"id": sid, "scene": s["scene"], "kind": s["kind"], "tier": tier,
                   "timecode": f"{tc(starts[sid])} - {tc(ends[sid])}", "assembled_s": round(d, 3), "generate_s": gen,
                   "size": s["lens"], "lens": LENS[s["lens"]], "angle": s["angle"], "lighting": LIGHT[s["light"]], "edit_fx": s["fx"],
                   "refs": refs, "subject": s["subject"], "line": s["line"], "motion": item["prompt"] if tier in ("pro", "lite") else "",
                   "keyframe": keyframe, "keyframe_prompt": kf_prompt,
                   "nameplates": [NAMEPLATE[w.split(':')[0]] for w in s["who"] if w.split(':')[0] in NAMEPLATE and s["kind"] in ("face", "d", "sil")],
                   "ja_overlay": JA_OVERLAY.get(sid, ""), "signage": SIGNAGE_BY_LOC.get(s["loc"], []), "caption": CARDS.get(sid, "")})
    budget = round((cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"]) * 1.25, 2)

    # ---------- 음성 복사(override) ----------
    src = os.path.join(ROOT, "assets", "auditions", "yanagi-tts")
    dst = os.path.join(ROOT, "assets", "audio-overrides", SKIT)
    os.makedirs(dst, exist_ok=True)
    for i in range(1, 75):
        shutil.copyfile(os.path.join(src, f"line{i:03d}.mp3"), os.path.join(dst, f"line{i:03d}.mp3"))

    # ---------- 자막(ASS): 줄 순서 = lineNNN 순서 (TTS 캐시 번호와 일치해야 함) ----------
    events = []
    for i, x in enumerate(texts, 1):
        r = rows[f"line{i:03d}"]
        key = "NA" if x["spk"].startswith("NA") else x["spk"]
        st = STYLE[key]
        events.append((r["start"] - r["lead"], r["end"] + 0.2, st, STYLE_JA[st], wrap(x["text"])))
    for sid, cap in CARDS.items():
        c0 = starts[sid] + 0.4
        events.append((c0, min(ends[sid] - 0.3, c0 + 3.5), "Caption", "", cap))
    # 후크 대사(line047 음성 재사용) — 화면 전용 스타일(TTS 번호에 영향 없음), 음성은 PHASE 6에서 로컬 믹스
    events.append((starts["H1"] + 0.5, starts["H1"] + 6.5, "HookLine", "緒方", wrap(texts[46]["text"])))
    events.sort(key=lambda e: e[0])
    st_lines = "\n".join(
        f"Style: {n},Noto Sans CJK JP,{58 if n != 'Naration' else 52},{c},&H000000FF,&H00000000,&H80000000,-1,{-1 if n == 'Naration' else 0},0,0,100,100,0,0,1,5,2,2,200,200,80,1"
        for n, c in STYLE_COLOR.items())
    ass = ["[Script Info]", "Title: 柳の葉と一杯の水 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           st_lines,
           "Style: HookLine,Noto Sans CJK JP,58,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1",
           "Style: Caption,Noto Serif CJK JP,64,&H00FFF3C4,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,5,200,200,80,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{e[4]}")
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    # ---------- 스토리보드·장면·오디오 ----------
    os.makedirs(os.path.join(ROOT, "scripts", "storyboard"), exist_ok=True)
    json.dump({"_설명": "yanagi PHASE 3 스토리보드 Lock(build_yanagi_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT,
               "preset": PRESET, "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"],
               "scenes": sb}, open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"_설명": "yanagi 장면 설정(build_yanagi_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, "
                         "wardrobe, props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": "yanagi 조립·오디오(build_yanagi_phase3.py 생성). 음성 74줄 = assets/audio-overrides/yanagi/ (Typecast 확정본, 배속 없음).",
        "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Naration"], "silent_styles": ["Caption", "HookLine"],
        "output_size": [1920, 1080], "fit": "crop",
        "scene_durations": durations, "transitions": [0.0] * len(durations),
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d"],
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": OMNI_MAX,
        "legacy_lipsync": False,
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35,
        "ambience_prompts": [AMBIENCE.get(sid, "") for sid in order_ids],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": s, "end": round(main_end, 2) if e is None else e, "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_후크": "H1 화면은 S24b 재사용, 음성은 line047을 0:02.5에 로컬 믹스(PHASE 6).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)

    # ---------- 검토 문서 ----------
    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    md = ["# 『柳の葉と一杯の水』 PHASE 3 샷 리스트", "",
          f"> `scripts/build_yanagi_phase3.py` 자동 생성(손 수정 금지). 타임코드는 분:초.프레임(24fps). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " +
          ", ".join(f"{a[0]} {tc(a[1])}" for a in lock["ads"]) + ".", "",
          "## 비용 추산 (실측 단가)", "",
          "| 항목 | 수량 | 단가 | 금액 |", "|---|---|---|---|",
          f"| 키프레임 | {cost['kf']}장 | 0.04 | {cost['kf'] * RATE['kf']:.2f} |",
          f"| i2v pro 1080p (얼굴) | {cost['pro']}초 | 0.108 | {cost['pro'] * RATE['pro']:.2f} |",
          f"| i2v lite 720p (실루엣·무인) | {cost['lite']}초 | 0.036 | {cost['lite'] * RATE['lite']:.2f} |",
          f"| OmniHuman (8초 상한 + 앞뒤 0.8초) | {cost['omni']:.1f}초 | 0.16 | {cost['omni'] * RATE['omni']:.2f} |",
          f"| **1차 합계** (재생성 여유 제외) | | | **{total_cost:.2f}** |",
          f"| i2v 예산 상한 `budget_usd` (여유 25%) | | | {budget:.2f} |", "",
          "## 생성 방식 분포", "", "| 방식 | 컷 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in tiers.most_common()] + [
          "", "## 앵글 분포 (생성 컷)", "", "| 앵글 | 컷 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in ang.most_common()] + [
          "", "## 화면 속 가상 표기 (키프레임은 무지 → 로컬 합성)", ""] + [
          f"- {x['id']}: " + " / ".join(x["signage"]) for x in sb if x["signage"]] + [
          "", "## 샷 표", "", "| 컷 | 타임코드 | 길이 | 방식 | 사이즈 | 앵글 | 조명 | 편집 효과 | 대사 | 참조 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in sb:
        light = next(k for k, v in LIGHT.items() if v == x["lighting"])
        md.append(f"| {x['id']} | {x['timecode']} | {x['assembled_s']:.2f}s | {x['tier']} | {x['size']} | {x['angle']} | {light} | {x['edit_fx']} | {x['line'] or ''} | {len(x['refs'])}장 |")
    open(os.path.join(PROD, "07_샷리스트.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    if lag_report:
        print("J컷(대사가 앞 컷 위에서 먼저 시작):", ", ".join(f"{a}+{b}s" for a, b in lag_report))
    print(f"완료: 컷 {len(SHOTS)}개, 본편 {tc(main_end)}, 방식 {dict(tiers)}, 1차 비용 약 {total_cost:.2f}달러 (i2v budget {budget})")


if __name__ == "__main__":
    main()
