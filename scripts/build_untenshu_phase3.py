#!/usr/bin/env python3
"""『運転手のくせに』(untenshu) PHASE 3 샷 리스트 Lock 생성기 — 일본어판. build_ashita_phase3.py를 작품명만 바꿔 복사·수정.

입력(동결본, 손으로 옮겨 적지 않는다):
  productions/untenshu-ja/lock.json        PHASE 1 Lock(실측 음성 줄 타임코드·장면 경계·광고 지점, 무언 비트 포함)
  productions/untenshu-ja/00_script_ja.md  대본 v1.1(자막 원문)
  assets/auditions/untenshu-tts/lineNNN.mp3 + untenshu-tts-add/(PNN·보정 lineNNN)  확정 음성
  assets/portraits/untenshu-cast/cells/    PHASE 2 승인 시트 칸
출력:
  scripts/storyboard/untenshu.json · scripts/scenes/untenshu.json · scripts/audio/untenshu.json · subs/untenshu.ass
  assets/audio-overrides/untenshu/lineNNN.mp3 (자막 TTS 줄 번호 = 캐시 번호)
  productions/untenshu-ja/07_샷리스트.md · 16_감정일치표.md · 02_카메라앵글설계.md
연출 원칙(대본 4-2·4-3절, 고니감독님 지시):
  ① 말하는 사람의 비립싱크 컷 최소화 — 말하는 동안 화면은 립싱크(d) 또는 듣는 사람의 실제 반응(i2v, vo=True)·말하는 사람의 손(i2v).
     말하는 사람이 비립싱크로 나오면 입이 보이지 않는 정지 + 편집 카메라(react, 제11장 9).
  ② 정지는 글자 합성 면·무인 정물·편집 효과(돌리줌)·말하는 사람의 뒷모습뿐 → 사람 컷 정지 비율 보고.
  ③ 조명 장면별(LIGHT), 앵글 다양화(연속 같은 구도 금지·한 앵글 60% 이하), 왜곡: 돌리줌 1·더치 2(大塚만).
검사: 연속 같은 구도·돌리줌 1회·더치 2회 이하·OMNI 각도(정면~45°)·화자-화면 일치(vo 예외)·모든 대사 줄 사용·
      컷 길이(1.2초 이상, 정지 6.5초·i2v 10초 이하)·OMNI 8초·BGM 구간 간격 1.0초.
사용법: python3 scripts/build_untenshu_phase3.py
"""
import collections
import json
import os
import re
import shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "untenshu-ja")
SKIT = "untenshu"
FPS = 24
HARD = 1 / FPS
OMNI_MAX = 7.9
LEAD = 0.3
MIN_SHOT = 1.2
STILL_MAX = 6.5
I2V_MAX = 10.0

# ---------- 고정 문장(PHASE 2 승인 시트와 1:1) ----------
C = "assets/portraits/untenshu-cast/cells/"
WHO = {  # 키: (묘사, 정면 칸, 뒷모습 칸)
    "KURODA": ("Kuroda Soichiro, a lean upright Japanese man aged 67, a long calm dignified face with gentle deep-set eyes and fine wrinkles, "
               "thick white hair neatly swept straight back, a short neatly trimmed white moustache, one small dark mole on his RIGHT cheek, no glasses",
               C + "kuroda-sheet-v2-front.png", C + "kuroda-sheet-v2-back.png"),
    "KURODA_D": ("Kuroda Soichiro the taxi driver, a lean Japanese man aged 67, a long calm dignified face, thick white hair swept back under the cap, "
                 "a short neatly trimmed white moustache, one small dark mole on his RIGHT cheek, no glasses",
                 C + "kuroda-driver-sheet-front.png", C + "kuroda-driver-sheet-back.png"),
    "KURODA_60": ("Kuroda at sixty, seen only from behind: thick white hair swept back, lean shoulders", None, C + "kuroda-sheet-v2-back.png"),
    "YOUNG_K": ("a young taxi driver seen only from behind: short black hair under an old-fashioned driver's cap (flashback, no face)", None, None),
    "OTSUKA": ("Otsuka Koji, a thickset Japanese man aged 45, a broad ruddy face, thick heavy black eyebrows, black hair stiffly gelled with a hard side parting, "
               "clean-shaven, no glasses, a gold wristwatch on his LEFT wrist", C + "otsuka-sheet-v2-front.png", C + "otsuka-sheet-v2-back.png"),
    "OGAWA": ("Ogawa Yui, a slim Japanese woman aged 26, a kind gentle oval face with natural light makeup, soft brown shoulder-length hair tied in a low ponytail "
              "with soft side-swept bangs, no glasses", C + "ogawa-sheet-v2-front.png", C + "ogawa-sheet-v2-back.png"),
    "ISHII": ("Ishii, a Japanese man aged 60, a serious square face with deep nasolabial lines, short cropped grey-and-white hair, thick BLACK horn-rimmed glasses",
              C + "ishii-sheet-v2-front.png", C + "ishii-sheet-v2-back.png"),
    "MIURA": ("Miura, a slender Japanese woman aged 40, an elegant composed face, glossy black hair in a neat low bun, no glasses",
              C + "miura-sheet-v2-front.png", C + "miura-sheet-v2-back.png"),
    "CHIYOKO": ("Chiyoko, a small delicate Japanese woman aged 62, a gentle round face with soft kind eyes and laugh lines, soft white chin-length bob, no glasses",
                C + "chiyoko-sheet-v2-front.png", C + "chiyoko-sheet-v2-back.png"),
    "ROFUJIN": ("an elderly Japanese woman aged 80, small and slightly stooped, a kind wrinkled face, thin white hair in a small low bun, no glasses, a plain wooden cane",
                C + "rofujin-sheet-v2-front.png", C + "rofujin-sheet-v2-back.png"),
    "SILS": ("two middle-aged men in work jackets seen only as faceless dark silhouettes (flashback)", None, None),
}
WARD = {
    "CHAIR": "a perfectly tailored plain dark-navy suit, white shirt, a plain deep-purple silk necktie",
    "DRIVER": "a plain navy peaked driver's cap with no badge, plain white cotton gloves, a white shirt with a plain navy V-neck vest",
    "CARDI": "a plain grey cardigan over a white shirt",
    "OTSUKA": "a grey pinstripe business suit, a loud glossy red paisley necktie",
    "OTSUKA_N": "a grey pinstripe business suit with the loud red paisley necktie loosened, jacket rumpled and damp from the rain",
    "OGAWA": "a plain navy trouser suit and a plain white blouse",
    "OGAWA_T": "a plain beige trench coat over a plain navy trouser suit",
    "ISHII": "a plain black suit, white shirt and a plain charcoal-grey necktie",
    "MIURA": "a plain light-grey skirt suit and a plain white blouse",
    "CHIYO_H": "a soft lavender knitted cardigan draped over a plain pale-blue hospital gown",
    "CHIYO": "a soft lavender knitted cardigan over a plain cream blouse",
    "ROFU": "a plain grey knitted shawl over a dark-plum blouse",
    "OLD": "a 1980s plain navy driver's uniform",
}
EXPR = {  # 표정 칸(키프레임에 감정 50~70% 선반영 — 제2장 3)
    ("KURODA", "smile"): C + "kuroda-sheet-v2-expr1.png", ("KURODA", "calm"): C + "kuroda-sheet-v2-expr2.png",
    ("KURODA", "cold"): C + "kuroda-sheet-v2-expr3.png",
    ("KURODA_D", "smile"): C + "kuroda-driver-sheet-expr1.png", ("KURODA_D", "calm"): C + "kuroda-driver-sheet-expr2.png",
    ("KURODA_D", "tender"): C + "kuroda-driver-sheet-expr3.png",
    ("OTSUKA", "smug"): C + "otsuka-sheet-v2-expr1.png", ("OTSUKA", "anger"): C + "otsuka-sheet-v2-expr2.png",
    ("OTSUKA", "beg"): C + "otsuka-sheet-v2-expr3.png",
    ("OGAWA", "smile"): C + "ogawa-sheet-v2-expr1.png", ("OGAWA", "tears"): C + "ogawa-sheet-v2-expr2.png",
    ("OGAWA", "hurt"): C + "ogawa-sheet-v2-expr3.png",
    ("ISHII", "grave"): C + "ishii-sheet-v2-expr1.png", ("ISHII", "shock"): C + "ishii-sheet-v2-expr2.png",
    ("ISHII", "regret"): C + "ishii-sheet-v2-expr3.png",
    ("MIURA", "smile"): C + "miura-sheet-v2-expr1.png",
    ("CHIYOKO", "weak"): C + "chiyoko-sheet-v2-expr1.png", ("CHIYOKO", "smile"): C + "chiyoko-sheet-v2-expr2.png",
    ("CHIYOKO", "tears"): C + "chiyoko-sheet-v2-expr3.png",
    ("ROFUJIN", "grateful"): C + "rofujin-sheet-v2-expr1.png",
}
# R36: loc-taxi-angles c1·c2·c3은 실내 컷(라벨 불일치) → TAXI_OUT은 외부 c4, 보닛 카메라는 새 시트 loc-taxi-hood
LOC = {
    "STREET": C + "loc-street-night-c1.png", "RAMP": C + "loc-street-night-c2.png", "HOSP": C + "loc-street-night-c3.png",
    "MANSION": C + "loc-street-night-c4.png",
    "IZA_ST": C + "loc-izakaya-v2-c1.png", "IZA_SPOT": C + "loc-izakaya-v2-c2.png", "IZA_WARM": C + "loc-izakaya-v2-c4.png",
    "TAXI_REAR": C + "loc-taxi-c1.png", "TAXI_HEADREST": C + "loc-taxi-c2.png", "TAXI_DRIVER": C + "loc-taxi-c3.png",
    "MIRROR": C + "loc-taxi-c4.png",
    "TAXI_OUT": C + "loc-taxi-angles-c4.png", "TAXI_HOOD": C + "loc-taxi-hood.png", "TAXI_LOW": C + "loc-taxi-angles-c3.png",
    "TAXI_OVER": C + "loc-taxi-angles-c4.png",
    "OFFICE": C + "loc-office-c1.png", "MGR_DESK": C + "loc-office-c2.png", "OFF_REV": C + "loc-office-angles-c1.png",
    "OFF_HIGH": C + "loc-office-angles-c2.png", "OFF_GLASS": C + "loc-office-angles-c3.png", "OFF_ROW": C + "loc-office-angles-c4.png",
    "GARAGE": C + "loc-garage-past-c1.png", "GARAGE_PAST": C + "loc-garage-past-c2.png", "ALLEY_TAXI": C + "loc-garage-past-c3.png",
    "HOSP_ROOM": C + "loc-garage-past-c4.png",
    "LOBBY": C + "loc-hq-c1.png", "CORRIDOR": C + "loc-hq-c2.png", "MEET": C + "loc-hq-c3.png", "DOOR_BACKLIT": C + "loc-hq-c4.png",
    "MEET_REV": C + "loc-hq-angles-c1.png", "MEET_BE": C + "loc-hq-angles-c2.png", "MEET_LOW": C + "loc-hq-angles-c3.png",
    "MEET_THRU": C + "loc-hq-angles-c4.png",
    "P_METER": C + "props-sheet-c1.png", "P_TABLET": C + "props-sheet-c2.png", "P_PHOTO": C + "props-sheet-c3.png",
    "P_GLOVES": C + "props-sheet-c4.png", "P_FRAME": C + "props-frame.png",
}
PRESET = ("Photorealistic live-action Japanese TV drama, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, "
          "restrained Japanese film mise-en-scene, natural lived-in detail, no flat lighting")
NAT = ("People look like real Japanese drama actors photographed on set: real skin texture with visible pores and fine lines, subtle asymmetry, "
       "natural matte skin, restrained believable expressions, bare unadorned earlobes and no jewellery.")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, "
            "logo on shirt, signage lettering, kanji on lanterns, posters with writing, documents with writing, screens with text, printed labels, "
            "brand logos, characters on license plates, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, "
            "duplicate people, blood, gore, police")
PLAIN = ("All papers, screens, signs, cards and labels are completely blank; no letters, numbers or symbols anywhere in the frame. "
         "Any car license plate is a plain green plate with a thin white border and no characters; any taxi roof lamp is a plain white dome with no characters.")
# 고니감독님 지적(R17·R20): 눈물은 배우의 실제 울음처럼, 맑고 색 없게. 땀은 옅은 광택만. 해당 표정 컷에만 넣는다.
TEARS = ("Natural crying exactly like a real film actor: eyes glassy and moist with a thin film of tears along the lower lash line, one or two thin tear tracks "
         "running down one cheek, clear and colorless as water, barely catching the light; only a faint natural pinkness at the inner eye corners, natural skin "
         "around the eyes; trembling chin, brows knitted upward.")
SWEAT = "A faint natural sheen of perspiration on the forehead and temples, clear and colorless, only visible as a slight shine."
GLASSES = {"ISHII": "He wears his thick black horn-rimmed glasses."}
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the subject fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh",
    "ch": "85mm prime lens, f/1.8, choker framing from forehead to chin, razor-sharp eyes, soft bokeh",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective",
}
LIGHT = {  # 대본 4-2절 조명표
    "rain": "rainy Tokyo night, wet asphalt mirroring teal traffic lights and amber sodium street lamps, rain streaks backlit, mid-tones readable",
    "hosp_night": "rainy night under a hospital entrance canopy lit by a warm 3200K lamp, cool rain beyond",
    "izakaya": "red paper lanterns and warm neon backlight, rain streaks rim-lit, wet ground reflections",
    "taxi": "inside a taxi at night: soft teal and amber street-light stripes sliding across the faces, a faint dashboard glow from below, faces clearly readable",
    "taxi_red": "inside a taxi at night: harsh red brake-light reflection from the car ahead flooding the cabin, teal shadows, tension",
    "office": "hard cold fluorescent top light 5600K falling straight down, dark shadows under brows and chin, faint cyan cast",
    "garage": "early morning in a small garage, golden sunlight beaming through the gap under a half-raised shutter, floating dust, warm rim light",
    "sepia": "warm amber 3200K tungsten flashback, soft halation, lifted blacks like an old photograph",
    "hosp_gold": "quiet hospital room, late-afternoon golden sun through the window, soft low-contrast warmth, gentle rim light",
    "lobby": "calm neutral daylight through tall windows on polished marble, soft reflections",
    "backlit": "the doorway flooded with blinding white backlight, the figure a hard silhouette, haze in the light",
    "chiaro": "meeting room with strong side light from tall windows, deep chiaroscuro shadows, cool and tense",
    "top_cold": "a cold hard top light falling straight down in the meeting room, the rest falling off into shadow",
    "warm_win": "soft warm window light wrapping the subject, gentle golden rim, the cold room turning warm",
    "rain_cold": "cold blue rainy night, light trails of passing cars, lonely and harsh",
    "amber": "soft rainy night lit by warm amber street lamps, gentle and kind",
    "product": "soft even studio light, neutral",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}
SPK_KEY = {"黒田": "KURODA", "大塚": "OTSUKA", "小川": "OGAWA", "石井": "ISHII", "三浦": "MIURA", "千代子": "CHIYOKO", "老婦人": "ROFUJIN"}
TAXI_LOCS = ("STREET", "HOSP", "MANSION", "IZA_WARM", "IZA_ST", "TAXI_OUT", "TAXI_HOOD", "TAXI_OVER", "ALLEY_TAXI", "GARAGE")


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, vo=False, fg="", lead=None, pin=None):
    """kind: d(OMNI 립싱크) / live(사람 i2v lite) / face(사람 i2v pro 1080p) / react(사람 정지 + 편집 카메라, 말하는 사람 비립싱크 = 입 안 보임) /
    ins(손·소품 정지) / empty(무인 i2v lite) / estill(무인 정지) / reuse:<id> / card.
    who 항목 = "KEY:WARD" 또는 "KEY:WARD:back"(뒷모습 칸 참조, 제10장 2).
    line = 그 줄의 발화가 이 컷에서 시작. vo=True면 화자가 화면 밖(듣는 사람 반응·손·차 밖)이어도 된다(4-2절 ①).
    fg = 립싱크 어깨 너머 전경 쪽(L/R, 180° 축). pin=(태그, 초) = 줄 없는 컷의 시작을 그 줄 시작 + 초에 고정(긴 립싱크 뒤 듣는 사람 L컷)."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc, subject=subject, line=line,
                fx=fx, motion=motion, expr=expr, vo=vo, fg=fg, lead=lead, pin=pin)


K, KD, O, ON, G, GT, I, M = "KURODA:CHAIR", "KURODA_D:DRIVER", "OTSUKA:OTSUKA", "OTSUKA:OTSUKA_N", "OGAWA:OGAWA", "OGAWA:OGAWA_T", "ISHII:ISHII", "MIURA:MIURA"
SHOTS = [
    # ① 도입 후크 (0:00~0:20) — 후반 컷 재사용(추가 생성 0)
    S("H0a", "H", "reuse:S20a", "ews", "top_cold", "BE", [], None, "Reuse of S20a (Otsuka sliding to his knees, bird's-eye)."),
    S("H0b", "H", "reuse:S20e", "ecu", "top_cold", "OH", [], None, "Reuse of S20e (a drop of sweat hits the floor)."),
    S("H1", "H", "reuse:S06e", "cu", "taxi_red", "EL", [], None, "Reuse of S06e (Otsuka: 'Just a driver—don't tell me what to do!'). Voice = L11 mixed locally."),
    S("H2", "H", "reuse:S17b", "ws", "backlit", "LA", [], None, "Reuse of S17b (the meeting-room door opens, a backlit silhouette). NA0 over it."),
    S("H3", "H", "card", "ews", "rain", "EL", [], None, "Title card 『運転手のくせに』 with subtitle over dark rain."),
    # ② 발단·갈등
    S("S01a", "S01", "empty", "ews", "rain", "LA", [], "STREET", "No people visible. A wide rainy Tokyo avenue at night, a black private taxi with a plain white dome roof lamp gliding away, red tail lights smeared on wet asphalt.",
      line="NA1", motion="The taxi glides slowly away down the avenue; rain falls; traffic lights reflect and shimmer. No people."),
    S("S01b", "S01", "live", "ecu", "taxi", "SIDE", [KD], "TAXI_DRIVER", "Insert: white-gloved hands on the steering wheel of a taxi at night, turning it gently, street-light stripes sliding over the gloves. No face.",
      line="NA2", motion="The white-gloved hands turn the wheel smoothly a few degrees and settle; light stripes slide across them."),
    S("S01c", "S01", "face", "ms", "taxi", "EL", [KD], "TAXI_HOOD", "Camera OUTSIDE the car on the hood, looking straight back through the windshield glass into the cabin; the rain-beaded glass and wipers are in front of the driver, between him and the camera; right-hand-drive Japanese taxi: the driver sits on the LEFT side of the frame as seen from outside, the empty front passenger seat on the right; no dashboard or steering wheel in the camera's foreground — the dashboard is behind the glass. Through the rain-beaded windshield from the hood: Kuroda in his cap at the wheel, calm and attentive, wipers mid-sweep.", expr="calm",
      motion="The wipers sweep once across the glass; Kuroda blinks slowly and checks the road with calm eyes; his head barely moves."),
    S("S02a", "S02", "empty", "ecu", "taxi", "EL", [], "P_FRAME", "No hands. Extreme close-up of a small plain silver photo frame on the dashboard holding a snapshot of a smiling elderly woman in a lavender cardigan; the shadow of a wiper passes over it.",
      line="NA3", motion="The shadow of the wiper sweeps across the frame once; rain light flickers softly. Nothing else moves."),
    S("S02b", "S02", "live", "ecu", "taxi", "EL", [KD], "MIRROR", "Extreme close-up of the rear-view mirror: Kuroda's gentle eyes reflected in it, glancing down toward the dashboard photo.", expr="tender",
      motion="His eyes glance down toward the photo and soften; one slow blink; street light slides across the mirror."),
    S("S03a", "S03", "react", "ws", "hosp_night", "SIDE", ["ROFUJIN:ROFU:back", KD], "HOSP", "Wide under the hospital canopy in the rain: Kuroda's glossy black sedan taxi (plain white dome roof lamp) with its rear door open, the elderly woman seen from behind stepping out with her cane and bowing her head gratefully, Kuroda's white-gloved hand holding the door.",
      line="L01", fx="pushin"),
    S("S03b", "S03", "d", "cu", "hosp_night", "EL", [KD, "ROFUJIN:ROFU:back"], "HOSP", "Over the elderly woman's shoulder (soft in the foreground, left): Kuroda in his cap holding the taxi door open with a white-gloved hand, a warm gentle smile, rain beyond.",
      line="L02", expr="smile", fg="L"),
    S("S03c", "S03", "live", "ws", "hosp_night", "EL", ["ROFUJIN:ROFU"], "HOSP", "The elderly woman under the canopy turns and bows gratefully toward the taxi, leaning on her cane.", line="NA4", expr="grateful",
      motion="She bows slowly and gratefully, leaning on her cane; rain falls beyond the canopy."),
    S("S03d", "S03", "live", "ms", "hosp_night", "SIDE", ["KURODA_D:DRIVER:back"], "HOSP", "Kuroda in his cap seen from the side-back beside the taxi in the rain, bowing deeply toward the hospital entrance.",
      motion="Kuroda bows deeply and slowly straightens; rain beads on his cap. His face stays turned away."),
    S("S03e", "S03", "empty", "ews", "hosp_night", "HA", [], "HOSP", "No people visible. High angle: the black taxi pulls away from the hospital canopy into the rain.",
      motion="The taxi pulls slowly away into the rain; the canopy lamp glows. No people."),
    S("S04a", "S04", "live", "ews", "izakaya", "EL", [ON, GT], "IZA_ST", "Wide of the rainy izakaya street at 11 pm: two office workers under the plain red lanterns, the man raising a hand to hail a glossy black sedan taxi with a plain white dome roof lamp pulling up to the curb, the woman holding her bag over her head; small in frame.",
      line="NA6", motion="The man waves his raised hand impatiently; the woman shields her head with her bag; rain falls; lanterns sway slightly."),
    S("S04b", "S04", "face", "ms", "izakaya", "LA", [ON, GT], "IZA_SPOT", "Low angle medium: Otsuka, tie loosened and face flushed from drinking, arm raised impatiently; Ogawa beside him in her beige trench coat, rain on her hair.", expr="smug",
      motion="Otsuka flaps his raised hand impatiently with a drunken scowl; Ogawa glances at him uneasily and blinks; rain falls. No one walks toward the camera."),
    S("S05a", "S05", "live", "ws", "rain", "SIDE", ["OTSUKA:OTSUKA_N:back", "OGAWA:OGAWA_T:back"], "TAXI_OUT", "From outside through the rain-beaded rear side window: two blurred figures dropping into the back seat of the taxi, neon bokeh.",
      line="L03", vo=True, motion="Raindrops run down the window; the two blurred figures settle into the seat. Faces stay blurred behind the wet glass."),
    S("S05b", "S05", "react", "ecu", "taxi", "EL", [KD], "MIRROR", "Rear-view mirror close-up: Kuroda in his plain navy peaked cap with no badge, his calm eyes reflected, looking back politely at the passengers; his mouth is outside the mirror; soft even light on his face.",
      line="L04", fx="pushin"),
    S("S05c", "S05", "live", "ms", "taxi", "EL", [GT], "TAXI_REAR", "In the back seat at night: Ogawa dabbing her wet hair with a plain handkerchief, glancing sideways at her boss, uneasy.", line="L05", vo=True,
      motion="Ogawa dabs her wet hair, then glances sideways uneasily; light stripes slide across her; she does not speak."),
    S("S05d", "S05", "live", "ecu", "taxi", "OH", [GT], "TAXI_REAR", "Insert from above: a woman's hands in a beige trench coat flipping through blank documents on her lap.", line="L06",
      motion="Her hands turn a page of the blank documents carefully and smooth it down."),
    S("S05e", "S05", "d", "cu", "taxi", "EL", [ON, GT + ":profile"], "TAXI_REAR", "Camera low in the front of the cabin, looking back diagonally at the rear bench seat: Otsuka and Ogawa sit SIDE BY SIDE on the same rear bench, both bodies facing forward; Ogawa is a soft out-of-focus side profile at the left edge of the frame, at the same depth as him, NOT in front of him; Otsuka sprawled on the right of the bench, his head turned about 30 degrees toward her, tie loosened, a smug grin, one hand stroking his chin, city light sliding across his face.",
      line="L07", expr="smug", fg="R"),
    S("S06a", "S06", "empty", "ews", "rain", "EL", [], "RAMP", "No people. An expressway on-ramp closed for construction at night: striped barriers, flashing amber warning lamps smeared by heavy rain.",
      line="L08", vo=True, motion="The amber warning lamps flash in rhythm; rain falls. No people, no cars."),
    S("S06b", "S06", "react", "ms", "rain", "EL", [KD], "TAXI_HOOD", "Camera OUTSIDE the car on the hood, looking straight back through the windshield glass into the cabin; the rain-beaded glass and wipers are in front of the driver, between him and the camera; right-hand-drive Japanese taxi: the driver sits on the LEFT side of the frame as seen from outside, the empty front passenger seat on the right; no dashboard or steering wheel in the camera's foreground — the dashboard is behind the glass. Through the rain-streaked windshield: Kuroda in his cap at the wheel, his face softened by the running water, mouth not readable, the wipers frozen mid-sweep.",
      fx="pushin"),
    S("S06c", "S06", "live", "ecu", "taxi", "EL", [KD], "MIRROR", "Rear-view mirror close-up: Kuroda's eyes reflected, steady and patient, listening.", line="L09", vo=True, expr="calm",
      motion="Kuroda's eyes stay steady and patient in the mirror; one slow blink; light slides across the glass."),
    S("S06d", "S06", "face", "ms", "taxi_red", "LA", [ON], "TAXI_LOW", "Low angle from dashboard height: Otsuka leaning forward from the back seat, glaring at the driver, red brake light washing over his face.", line="L10", vo=True, expr="anger",
      motion="Otsuka leans forward a little more, his jaw tightening, nostrils flaring; red light pulses. His mouth stays closed."),
    S("S06e", "S06", "d", "cu", "taxi_red", "LA", [ON, "KURODA_D:DRIVER:profile"], "TAXI_REAR", "Camera on the dashboard at the passenger side looking back into the rear seat: Otsuka in the back seat leaning forward into the gap between the two front seats, one hand gripping the top of the front passenger seat, glaring toward the driver, red brake light on his face; at the left edge of the frame the driver is seen in side profile, eyes on the road ahead through the windshield, NOT looking at Otsuka.",
      line="L11", expr="anger", fx="dutch5,handheld", fg="L"),
    S("S07a", "S07", "ins", "ecu", "taxi_red", "EL", [], "P_FRAME", "Insert: the small silver photo frame tipping over on the dashboard from the jolt, frozen mid-fall.", line="NA8", fx="slowfall"),
    S("S07b", "S07", "estill", "ecu", "taxi", "OH", [], "P_FRAME", "No people. From above: the small silver photo frame lying face up on the dark floor mat, the photo of the smiling elderly woman, raindrops of light on the glass."),
    S("S07c", "S07", "live", "ecu", "taxi", "EL", [], "TAXI_REAR", "Insert: a young woman's slender hand in a beige trench-coat sleeve gripping a man's grey pinstripe suit sleeve to stop him, on the back seat of a taxi at night. Hands and sleeves only, no faces.", line="L12", vo=True,
      motion="Her hand grips the sleeve urgently and tugs it once, trembling; his arm jerks away."),
    S("S07d", "S07", "live", "cu", "taxi", "SIDE", [GT], "TAXI_REAR", "Close-up of Ogawa shrinking back against the seat, stunned and hurt, eyes lowered.", line="L13", vo=True, expr="hurt",
      motion="Ogawa flinches back and lowers her eyes, her breath catching; her lips stay pressed together."),
    S("S07e", "S07", "d", "cu", "taxi", "EL", [ON, GT + ":profile"], "TAXI_REAR", "Camera low in the front of the cabin, looking back diagonally at the rear bench seat: Otsuka and Ogawa sit SIDE BY SIDE on the same rear bench, both bodies facing forward; Ogawa is a soft out-of-focus side profile at the left edge of the frame, at the same depth as him, NOT in front of him; Otsuka leaning back on the right of the bench, looking forward toward the driver at a three-quarter angle, with a slow contemptuous sneer, chin raised.",
      line="L14", expr="smug", fg="R"),
    S("S08a", "S08", "react", "ecu", "taxi", "EL", [KD], "MIRROR", "Rear-view mirror close-up: Kuroda in his plain navy peaked cap with no badge, his eyes reflected, calm and unreadable, not angry; his mouth is outside the mirror; soft even light on his face, no colored stripes across it.", line="L15", fx="pushin", expr="calm"),
    S("S08b", "S08", "live", "ecu", "taxi", "SIDE", [KD], "P_GLOVES", "Insert: white-gloved hands holding the steering wheel steady, wiper shadows passing.", line="NA9",
      motion="The gloved hands hold the wheel steady, fingers tightening once and relaxing; wiper shadows pass."),
    S("S08c", "S08", "empty", "ews", "rain", "BE", [], "TAXI_OVER", "No people visible. Bird's-eye from high above: the black taxi turning through a wet rainy intersection, light trails.",
      motion="The taxi turns slowly through the intersection; light trails streak; rain falls."),
    S("S09a", "S09", "empty", "ws", "rain", "EL", [], "MANSION", "No people visible. The black taxi stopped at the entrance of an upscale residential tower at night in the rain.", line="L16", vo=True,
      motion="Rain falls on the taxi roof; the lobby light glows. No people."),
    S("S09b", "S09", "ins", "ecu", "taxi", "EL", [], "P_METER", "Insert: the taxi fare meter's blank glowing display (fare composited later)."),
    S("S09c", "S09", "live", "ecu", "taxi", "HA", [], "TAXI_DRIVER", "Insert from above: a thick man's hand in a grey pinstripe sleeve with a gold wristwatch tossing a crumpled plain pale banknote onto the front passenger seat of a taxi. Hand and seat only, no face.",
      motion="The hand flicks the crumpled note onto the seat; it bounces and settles."),
    S("S09d", "S09", "d", "cu", "taxi", "EL", [KD], "TAXI_DRIVER", "From the front passenger seat at a three-quarter angle: Kuroda in his cap at the wheel, calm and dignified, answering quietly, white gloves on the wheel.",
      line="L17", expr="calm", fg="R"),
    S("S09e", "S09", "react", "ms", "rain", "SIDE", ["OTSUKA:OTSUKA_N:back"], "TAXI_OUT", "Outside in the rain: Otsuka seen from behind climbing out of Kuroda's glossy black sedan taxi (plain white dome roof lamp) and slamming the rear door.", line="L18", fx="handheld"),
    S("S10a", "S10", "live", "ecu", "taxi", "OH", [GT], "TAXI_REAR", "Insert from above: a woman's hands picking up the small silver photo frame from the floor mat and wiping the rain off the glass with a plain handkerchief.",
      line="L19", motion="Her hands wipe the glass of the frame gently and apologetically with the handkerchief, trembling slightly."),
    S("S10b", "S10", "d", "cu", "taxi", "EL", [GT, "KURODA_D:DRIVER:profile"], "P_FRAME", "Taxi cabin layout (right-hand drive): the driver in the FRONT right seat, Ogawa in the REAR seat behind the front passenger seat; lace covers on every headrest. Camera on the dashboard at the front passenger side looking back between the two front seats into the rear seat: Ogawa in the back seat leaning slightly forward into the gap between the front seats, holding the small plain silver photo frame (exactly the frame in the reference image, palm-sized) out toward the driver with both hands, gentle and apologetic; at the left edge of the frame the driver is seen in side profile, the car parked, his head turned only slightly toward her.",
      line="L20", expr="hurt", fg="L"),
    S("S10c", "S10", "live", "ecu", "taxi", "EL", [], "P_FRAME", "Warm grateful moment, insert in the gap between the two lace-covered front seats of the taxi, seen from the side: from the back seat a young woman's slender hands in beige trench-coat sleeves hold out the small plain silver photo frame (exactly the frame in the reference image, palm-sized); from the driver's seat white-gloved hands in a white shirt sleeve gently receive it, the gloved fingers trembling slightly, tender. Hands, sleeves and frame only, no faces.", line="L21", vo=True,
      motion="The gloved hands take the frame gently; the woman's hands let go."),
    S("S10d", "S10", "react", "ms", "rain", "SIDE", ["OGAWA:OGAWA_T:back"], "TAXI_OUT", "Outside the open rear door of Kuroda's glossy black sedan taxi (plain white dome roof lamp, plain black doors) in the rain: Ogawa seen from behind, bowing politely toward the driver with a shy warm gesture before leaving.", line="L22", fx="pushin"),
    S("S10e", "S10", "live", "ms", "taxi", "SIDE", ["KURODA_D:DRIVER:back"], "TAXI_DRIVER", "Kuroda seen from behind in the driver's seat, setting the small photo frame back on the dashboard with both gloved hands.", line="NA10",
      motion="Kuroda places the frame back upright on the dashboard and rests his hand beside it for a moment. His head stays still."),
    S("S10f", "S10", "empty", "ews", "rain", "LA", [], "STREET", "No people visible. Low angle: the black taxi's tail lights receding down the long wet avenue in the rain.",
      motion="The taxi drives slowly away into the rain; reflections ripple. No people."),
    # ③ 전개·위기 (1차 광고 뒤)
    S("S11a", "S11", "live", "ws", "office", "HA", [O], "OFF_HIGH", "High angle over the sales floor in the morning: rows of white desks, Otsuka at his large desk by the window in the distance, fixing his tie, pleased.",
      line="NA11", motion="Otsuka adjusts his tie and leans back, pleased; the fluorescent light hums. No other people."),
    S("S11b", "S11", "live", "ms", "office", "SIDE", ["OGAWA:OGAWA:back"], "OFFICE", "Ogawa seen from behind walking between the desks toward her boss's desk, holding blank documents to her chest.",
      motion="Ogawa walks slowly away from the camera between the desks, holding the documents. She never turns."),
    S("S11c", "S11", "live", "ms", "office", "EL", [O], "MGR_DESK", "Otsuka at his desk looking up, irritated, as someone reports to him, cold fluorescent top light.", line="L23", vo=True, expr="anger",
      motion="Otsuka's brows draw together in irritation, he exhales sharply through his nose; mouth closed."),
    S("S11d", "S11", "d", "cu", "office", "EL", [O, G], "MGR_DESK", "Over Ogawa's shoulder (soft in the foreground, right): Otsuka at his desk tossing documents onto it, scolding with contempt, cold top light.",
      line="L24", expr="anger", fg="R"),
    S("S11e", "S11", "live", "cu", "office", "EL", [G], "OFF_GLASS", "Close-up of Ogawa standing before the desk, holding the documents tightly, absorbing the scolding, eyes lowered.", line="L25", vo=True, expr="hurt",
      motion="Ogawa's fingers tighten on the documents; she swallows and keeps her eyes lowered; lips pressed."),
    S("S11f", "S11", "react", "ch", "office", "EL", [G], "OFF_GLASS", "Choker close-up of Ogawa with her head bowed, eyes down, her mouth hidden by the angle of her bowed head.", line="L26", expr="hurt", lead=0.5),
    S("S11g", "S11", "live", "ms", "office", "SIDE", [G], "OFF_ROW", "Ogawa sitting down at her own desk in the row, setting the documents down, staring at nothing.", line="P1", expr="hurt",
      motion="Ogawa sets the documents down slowly and sits still, staring ahead, a slow breath."),
    S("S11g2", "S11", "live", "ecu", "office", "EL", [G], "OFF_ROW", "Insert: Ogawa's hand on the desk slowly letting go of the blank documents, fingers trembling slightly. Hand only.",
      motion="Her fingers loosen from the documents and tremble slightly, then rest still."),
    S("S11h", "S11", "d", "cu", "office", "EL", [O], "MGR_DESK", "Otsuka leaning back in his leather chair with a smartphone with a dark blank screen at his ear, smug grin, feet up, three-quarter view.",
      line="P2", expr="smug"),
    S("S11i", "S11", "live", "cu", "office", "SIDE", [G], "OFF_ROW", "Close-up of Ogawa at her desk overhearing the phone call, her face tightening with quiet disgust, eyes lowered.", expr="hurt",
      motion="Ogawa's jaw tightens and her eyes close for a moment in quiet disgust; her head stays still."),
    S("S12a", "S12", "d", "cu", "office", "EL", [I, O], "MGR_DESK", "Over Otsuka's shoulder (soft in the foreground, left): Executive Director Ishii holding a plain document folder, earnest and grave.",
      line="L27", expr="grave", fg="L"),
    S("S12b", "S12", "live", "ms", "office", "LA", [O], "OFF_REV", "Otsuka standing up from his chair, nodding eagerly with a confident grin, listening to the director.", expr="smug", pin=("L27", 7.6),
      motion="Otsuka nods eagerly twice and straightens his tie, grinning; his mouth stays closed."),
    S("S12c", "S12", "live", "ms", "office", "EL", [I], "OFFICE", "Ishii nodding slowly, pleased but cautious, holding the folder.", line="L28", vo=True, expr="grave",
      motion="Ishii nods slowly once and taps the folder with two fingers; his mouth stays closed."),
    S("S13a", "S13", "live", "ws", "garage", "SIDE", ["KURODA_D:DRIVER:back"], "GARAGE", "In a small garage at dawn: Kuroda seen from the side-back stepping out of the black taxi and slowly removing his driver's cap, golden light beaming through the shutter gap.",
      line="NA12", motion="Kuroda removes his cap slowly and holds it at his side; dust floats in the golden beam. His face stays turned away."),
    S("S13b", "S13", "react", "ms", "garage", "SIDE", ["KURODA_D:DRIVER:back"], "GARAGE", "Over Kuroda's shoulder from behind: his hands holding the small silver photo frame, the photo of his late wife, golden morning light.",
      line="P3", fx="pushin"),
    S("S13c", "S13", "ins", "ecu", "garage", "EL", [], "P_FRAME", "Macro insert: the corner of the small silver photo frame with a fresh tiny dent and scratch in the metal, golden light.", line="P4"),
    S("S14a", "S14", "live", "ms", "sepia", "SIDE", ["YOUNG_K:OLD"], "GARAGE_PAST", "Flashback, sepia: a young taxi driver seen from behind at the wheel of an old 1980s boxy taxi at night.", line="NA13",
      motion="The young driver turns the wheel slowly; old street lights pass. He never turns around."),
    S("S14b", "S14", "live", "ms", "sepia", "EL", ["SILS"], "GARAGE_PAST", "Flashback, sepia: the back seat of the old taxi with two faceless silhouetted factory owners slumped, sighing.", line="NA14",
      motion="The silhouettes' shoulders sink with a sigh; light passes over them. No faces."),
    S("S14c", "S14", "live", "ecu", "sepia", "EL", [], "GARAGE_PAST", "Flashback insert: a man's and a woman's hands together turning the handle of a small old lathe, metal shavings curling, warm tungsten light. Hands only.",
      line="NA15", motion="The two pairs of hands turn the lathe handle together; a metal shaving curls off."),
    S("S14d", "S14", "estill", "ws", "sepia", "EL", [], "GARAGE_PAST", "No people. Flashback: the corner of the old garage with the small lathe on a workbench and an old 1980s taxi parked, sepia.", fx="pushin"),
    S("S15a", "S15", "d", "cu", "hosp_gold", "EL", ["CHIYOKO:CHIYO_H", "KURODA_60:CARDI:back"], "HOSP_ROOM", "Over Kuroda's shoulder (his white hair soft in the foreground, left): Chiyoko in the hospital bed holding her husband's hand, a weak warm smile, golden window light.",
      line="L29", expr="weak", fg="L"),
    S("S15b", "S15", "live", "ch", "hosp_gold", "HA", ["CHIYOKO:CHIYO_H"], "HOSP_ROOM", "Close-up of Chiyoko on the pillow, smiling tenderly with tears in her eyes, listening to her husband's promise.", line="L30", vo=True, expr="tears",
      motion="Chiyoko smiles tenderly, a tear gathering; she blinks slowly; her lips stay softly closed."),
    S("S15c", "S15", "live", "ecu", "hosp_gold", "EL", [], "HOSP_ROOM", "Insert: an old woman's thin hand held between a man's two hands on a pale-blue blanket, golden light. Hands only.", line="P5",
      motion="The man's hands tighten gently around hers; her fingers loosen slowly."),
    S("S15d", "S15", "estill", "ws", "hosp_gold", "EL", [], "HOSP_ROOM", "No people. The same hospital room, the bed neatly made and empty, a beam of golden sunlight across it.", fx="pushin"),
    S("S15e", "S15", "face", "ms", "rain", "EL", [KD], "TAXI_HOOD", "Camera OUTSIDE the car on the hood, looking straight back through the windshield glass into the cabin; the rain-beaded glass and wipers are in front of the driver, between him and the camera; right-hand-drive Japanese taxi: the driver sits on the LEFT side of the frame as seen from outside, the empty front passenger seat on the right; no dashboard or steering wheel in the camera's foreground — the dashboard is behind the glass. Present-day night: through the rainy windshield from the hood, Kuroda clearly visible in the driver's seat on the left of the frame, in his plain navy peaked cap and white gloves, both hands on the wheel, calm, the wipers sweeping.", line="NA16", expr="calm",
      motion="The wipers sweep; Kuroda's eyes move calmly to the mirror and back; he does not speak."),
    S("S15f", "S15", "empty", "ecu", "taxi", "EL", [], "P_FRAME", "No hands. The small silver photo frame on the dashboard at night, wiper shadows and street light passing over it.",
      motion="Street light slides across the frame; a wiper shadow passes. Nothing else moves."),
    S("S15g", "S15", "live", "ecu", "taxi", "EL", [KD], "MIRROR", "Rear-view mirror close-up: Kuroda's eyes glancing at the empty back seat reflected behind him.", line="NA17", expr="calm",
      motion="His eyes glance toward the back seat in the mirror, thoughtful; one slow blink."),
    S("S16a", "S16", "d", "cu", "lobby", "EL", [M, O], "LOBBY", "Over Otsuka's shoulder (soft in the foreground, right): Secretary Miura in the marble lobby greeting the visitors politely, one hand gesturing toward the corridor.",
      line="L31", expr="smile", fg="R"),
    S("S16b", "S16", "live", "cu", "lobby", "SIDE", [G], "LOBBY", "Close-up of Ogawa walking through the lobby, hearing her boss's smug whisper beside her, uneasy, eyes sliding toward the wall.", line="L32", vo=True, expr="hurt",
      motion="Ogawa's eyes slide toward the wall and she slows a little, uneasy; her mouth stays closed."),
    S("S16c", "S16", "ins", "ecu", "lobby", "EL", [], "P_PHOTO", "Insert: the large black-and-white framed photograph on the lobby wall — an old taxi parked in front of a small garage, no people."),
    S("S16d", "S16", "d", "cu", "lobby", "EL", [G, O], "LOBBY", "Over Otsuka's shoulder (soft in the foreground, left): Ogawa stopping in front of the framed photograph, turning to her boss with a puzzled look, pointing at the photo.",
      line="P6", expr="hurt", fg="L"),
    S("S16e", "S16", "live", "ms", "lobby", "SIDE", [G], "CORRIDOR", "Ogawa glancing back over her shoulder at the photograph as she is hurried along the corridor.", line="P7", vo=True, expr="hurt",
      motion="Ogawa glances back once toward the lobby, then faces forward again; she keeps walking slowly."),
    S("S17a", "S17", "d", "cu", "chiaro", "EL", [O, G], "MEET", "Over Ogawa's shoulder (soft in the foreground, right): Otsuka in the meeting room adjusting his tie in his reflection in the tall window, smug and lecturing.",
      line="P8", expr="smug", fg="R"),
    S("S17b", "S17", "live", "ws", "backlit", "LA", ["KURODA:CHAIR"], "DOOR_BACKLIT", "Low angle from inside: the tall meeting-room doors swing open, a man in a suit stands in blinding white backlight, a hard silhouette, face completely black.",
      line="L33", motion="The doors swing open slowly; the silhouette stands perfectly still in the light; haze drifts. The face stays completely black."),
    S("S17c", "S17", "d", "cu", "chiaro", "LA", [K, O], "MEET_LOW", "Slightly low angle over Otsuka's shoulder (soft in the foreground, left): Chairman Kuroda in his dark-navy suit, looking straight at Otsuka, quiet and still, a cold calm.",
      line="L34", expr="cold", fg="L"),
    S("S17d", "S17", "react", "cu", "chiaro", "EL", [O], "MEET", "Close-up of Otsuka frozen with a business card held out, the color draining from his face, eyes wide.", line="NA18", expr="beg", fx="dollyzoom"),
    S("S17e", "S17", "live", "ecu", "chiaro", "EL", [O], "MEET", "Insert: a thick hand with a gold wristwatch holding out a blank white business card, trembling. Hand only.",
      motion="The hand holding the card trembles; the card shakes."),
    S("S17f", "S17", "d", "cu", "chiaro", "EL", [O, K], "MEET_REV", "Over Kuroda's shoulder (soft in the foreground, right): Otsuka stammering in panic, sweating, the business card shaking in his hand.",
      line="L35", expr="beg", fg="R"),
    S("S17g", "S17", "live", "ecu", "chiaro", "HA", [K], "MEET", "Insert: an elderly man's hand in a dark-navy sleeve setting a black tablet down on the dark wooden table and sliding it forward. Hand only.",
      line="NA19", motion="The hand sets the tablet down and slides it slowly forward, then withdraws."),
    S("S17h", "S17", "estill", "ecu", "chiaro", "EL", [], "P_TABLET", "No people. The black tablet lying on the dark meeting table, its screen dark.", fx="pushin"),
    # ④ 절정·결말 (2차 광고 뒤) — S18 첫머리 5.0초 = 드라이브 레코더 재생(L11 원음, 태블릿 스피커 필터)
    S("S18a", "S18", "ins", "ecu", "chiaro", "EL", [], "P_TABLET", "Insert: the tablet screen playing dashcam footage of a taxi's back seat at night (footage and REC indicator composited later)."),
    S("S18b", "S18", "live", "cu", "chiaro", "EL", [I], "MEET", "Close-up of Ishii slowly taking off his black horn-rimmed glasses, pale, stunned by what he hears.", line="NA20", expr="shock",
      motion="Ishii lowers his glasses slowly from his face, his eyes fixed on the tablet; his mouth stays closed."),
    S("S18c", "S18", "live", "ecu", "chiaro", "EL", [O], "MEET", "Extreme close-up from the side in the bright marble meeting room (blurred windows behind): Otsuka's temple, ear and jaw filling the frame, a faint sheen of sweat, a muscle twitching in his jaw.",
      motion="A bead of sweat slides slowly down his temple; his jaw muscle twitches."),
    S("S18d", "S18", "live", "cu", "chiaro", "SIDE", [G], "MEET", "Close-up of Ogawa holding her breath, eyes on the tablet, still.", expr="hurt",
      motion="Ogawa holds her breath, her eyes widening slightly; her lips stay pressed together."),
    S("S18e", "S18", "react", "ms", "chiaro", "EL", [I], "MEET_REV", "Ishii holding his removed glasses in one hand, his other hand pressed to his mouth in disbelief, looking at Otsuka.", line="L36", expr="shock", fx="pushin"),
    S("S18f", "S18", "d", "cu", "chiaro", "EL", [O, I], "MEET", "Over Ishii's shoulder (soft in the foreground, left): Otsuka leaning forward with both palms pressed flat on the table, sweating, eyes wide in panic, desperate excuses.", line="L37", expr="beg", fg="L"),
    S("S19a", "S19", "live", "ecu", "chiaro", "HA", [K], "P_TABLET", "Insert: an elderly man's two hands folded calmly on top of the black tablet on the dark table. Hands only.", line="L38",
      motion="The folded hands rest still, then one thumb taps the tablet once."),
    S("S19b", "S19", "d", "cu", "chiaro", "LA", [K, O], "MEET_LOW", "Low angle over Otsuka's shoulder (soft in the foreground, left): Chairman Kuroda, hands folded on the tablet, firm and quiet, side light carving his face.",
      line="L39", expr="cold", fg="L"),
    S("S19c", "S19", "face", "cu", "chiaro", "EL", [O], "MEET_REV", "Close-up of Otsuka, sweat on his forehead, his face collapsing as he hears the verdict.", line="L40", vo=True, expr="beg",
      motion="Otsuka's face slackens and his eyes go wide, a slow shaky breath; his mouth stays slightly open but silent."),
    S("S19d", "S19", "react", "ms", "chiaro", "SIDE", [I], "MEET", "Ishii half-rising from his chair in profile, one hand reaching out across the table, pleading, face turned away.", line="P9", fx="pushin"),
    S("S19e", "S19", "d", "cu", "chiaro", "EL", [K, I], "MEET_REV", "Over Ishii's shoulder (soft in the foreground, right): Chairman Kuroda looking at Ishii calmly, not moving, closing the way out.",
      line="P10", expr="cold", fg="R"),
    S("S20a", "S20", "live", "ews", "top_cold", "BE", [O], "MEET_BE", "Bird's-eye from straight above: Otsuka sliding off his chair onto his knees on the marble floor beside the table, small and crushed.",
      fx="dutch7", expr="beg", motion="Otsuka sinks onto his knees and bows his head; his shoulders shake."),
    S("S20b", "S20", "d", "cu", "top_cold", "HA", [O], "MEET_BE", "Slightly high angle: Otsuka on his knees looking up, begging, real tears and a faint sheen of sweat, hands clasped.",
      line="L41", expr="beg"),
    S("S20c", "S20", "d", "cu", "chiaro", "LA", [K, O], "MEET_LOW", "Low angle over the kneeling Otsuka's head (soft in the foreground, left): Chairman Kuroda looking down quietly, unmoved.",
      line="L42", expr="cold", fg="L"),
    S("S20d", "S20", "live", "ws", "top_cold", "BE", [O], "MEET_BE", "From straight above: Otsuka kneeling, his hands trembling on the marble floor.", line="L43", vo=True,
      motion="His hands tremble on the floor and his shoulders shake; he does not look up."),
    S("S20e", "S20", "ins", "ecu", "top_cold", "OH", [], "MEET_BE", "Insert: a single drop of sweat falling onto the polished marble floor."),
    S("S20f", "S20", "d", "cu", "chiaro", "LA", [K, O], "MEET_LOW", "Low angle over the kneeling Otsuka (soft in the foreground, right): Chairman Kuroda delivering the final words, cold and calm.",
      line="L44", expr="cold", fg="R"),
    S("S21a", "S21", "face", "cu", "warm_win", "EL", [G], "MEET", "Close-up of Ogawa holding documents to her chest, warm window light wrapping her, her eyes beginning to fill as the chairman speaks of the photo.", line="L45", vo=True, expr="tears",
      motion="Ogawa's eyes fill with tears and she blinks them back; her fingers tighten on the documents; mouth closed."),
    S("S21b", "S21", "d", "cu", "warm_win", "EL", [K, G], "MEET_REV", "Over Ogawa's shoulder (soft in the foreground, left): Chairman Kuroda turned toward her, a gentle warm smile, the cold room turning warm.",
      line="L46", expr="smile", fg="L"),
    S("S21c", "S21", "d", "cu", "warm_win", "EL", [G, K], "MEET", "Over the chairman's shoulder (soft in the foreground, right): Ogawa with tears in her eyes, stunned and moved, documents held to her chest.",
      line="L47", expr="tears", fg="R"),
    S("S21d", "S21", "react", "ms", "chiaro", "SIDE", [I], "MEET_THRU", "Through the half-open door frame: Ishii bowing deeply toward the chairman, his face hidden by the bow.", line="L48", fx="pushin"),
    S("S21e", "S21", "live", "ws", "top_cold", "HA", [O], "MEET", "High angle: Otsuka still kneeling alone by the table, slumped, abandoned.",
      motion="Otsuka's shoulders slump further; he stays kneeling, head down."),
    S("S22a", "S22", "live", "ecu", "warm_win", "OH", [G], "MEET", "Insert from above: Ogawa's hand signing a blank contract with a fountain pen. Hand only.", line="NA21",
      motion="The pen moves across the blank signature line in a short flowing stroke and lifts."),
    S("S22b", "S22", "live", "ws", "lobby", "HA", ["OTSUKA:OTSUKA:back"], "CORRIDOR", "High angle: Otsuka seen from behind walking alone down the long quiet corridor, small.", line="NA22",
      motion="Otsuka walks slowly away from the camera down the corridor, shoulders sagging. He never turns."),
    S("S22c", "S22", "estill", "ms", "office", "EL", [], "MGR_DESK", "No people. The manager's empty desk by the window, the leather chair pushed back, a blank brass nameplate lying face down.", fx="pushin"),
    S("S22d", "S22", "live", "ews", "rain_cold", "HA", ["OTSUKA:OTSUKA_N:back"], "IZA_ST", "High angle over the same rainy izakaya street at night: Otsuka small and alone at the curb, soaked, raising his hand to hail.",
      line="P11", motion="Otsuka raises his hand again and again; light trails of taxis pass without stopping; rain falls. He never turns."),
    S("S22e", "S22", "empty", "ws", "rain_cold", "EL", [], "STREET", "No people visible. Black taxis with lit roof lamps streaking past through the rain without stopping, light trails.",
      motion="Taxis streak past one after another without slowing; rain spray. No people."),
    S("S22f", "S22", "live", "ms", "rain_cold", "SIDE", ["OTSUKA:OTSUKA_N:back"], "IZA_SPOT", "Otsuka seen from behind at the curb, slowly lowering his hand, soaked, under a plain red lantern.", line="NA23",
      motion="Otsuka lowers his hand slowly and his shoulders sink; rain pours. His face stays turned away."),
    S("S23a", "S23", "live", "ws", "amber", "EL", [GT], "IZA_WARM", "A week later, the same curbside spot in soft rain and warm amber light: Ogawa under an umbrella raising her hand; the black taxi glides to a stop and its rear door opens.",
      motion="The taxi glides to a stop and the rear door swings open; Ogawa lowers her hand and smiles. No one walks toward the camera."),
    S("S23b", "S23", "react", "ecu", "amber", "EL", [KD], "MIRROR", "Rear-view mirror close-up: Kuroda's eyes reflected, crinkling into a warm smile, warm amber street light.", line="L49", expr="smile", fx="pushin"),
    S("S23c", "S23", "live", "ecu", "amber", "EL", [GT], "TAXI_OUT", "Insert: a woman's hands folding a wet umbrella at the open rear door, amber light. Hands only.", line="L50",
      motion="Her hands fold the wet umbrella lightly and cheerfully with a gentle happy rhythm and shake off the rain."),
    S("S23d", "S23", "empty", "ecu", "amber", "EL", [], "P_FRAME", "No hands. The small silver photo frame standing on the dashboard again, warm amber light, the photo of the smiling woman.", line="NA24",
      motion="Warm street light glides across the frame; rain glitters beyond the windshield."),
    S("S23e", "S23", "empty", "ews", "amber", "HA", [], "IZA_WARM", "No people visible. High angle: the black taxi with its roof lamp glowing pulls away down the warm rainy street.",
      motion="The taxi drives slowly away down the street; lanterns glow; rain glitters."),
]

CARDS = {"H0a": "タクシー運転手を怒鳴りつけた部長の、翌朝。", "H3": "運転手のくせに", "S23e": "後ろの席で、あなたは、どんな顔をしていますか。"}
TITLE_SUB = "〜タクシーで怒鳴った部長が、翌朝ひれ伏した相手〜"
JA_OVERLAY = {"S09b": "요금 미터 「3,860円」", "S18a": "드라이브 레코더 화면(뒷좌석 영상 + 「● REC」 시각)"}
AMBIENCE = {  # 사람이 나오는 컷은 현장음 금지(제6장 4) — 무인 컷만
    "S01a": "heavy rain on a city avenue at night, distant traffic hiss", "S02a": "rain on a car roof, a windshield wiper's soft rhythm",
    "S03e": "rain, a car pulling away on a wet road", "S06a": "heavy rain, a construction warning lamp ticking",
    "S08c": "rain on a wet intersection, tires hissing", "S09a": "rain on a car roof at night", "S10f": "a car driving away in the rain",
    "S07b": "a small object thudding onto a car floor mat", "S15d": "faint hospital room tone, distant birds", "S15f": "rain on a windshield, wiper rhythm",
    "S17h": "quiet room tone", "S20e": "a tiny drop on a hard floor", "S22e": "taxis rushing past in the rain, tire spray",
    "S23d": "soft rain on a car roof", "S23e": "a car driving off in soft rain",
}
BGM = [  # (시작, 끝, 볼륨, 프롬프트) — 0~4초는 BGM 없음(빗소리·와이퍼·심장 박동 1회는 PHASE 6 로컬 믹스). 구간 사이 1.0초 이상(생성기 검사)
    (4.0, 19.0, 0.36, "tense low strings and a slow heartbeat pulse building to a sharp hit, Japanese drama cold open, instrumental, no vocals"),
    (20.5, 120.0, 0.38, "gentle melancholic piano with soft rain atmosphere turning uneasy, Japanese night drama, instrumental, no vocals"),
    (121.5, 215.0, 0.40, "dark tense strings and low piano pulses, injustice and anger, Japanese drama score, instrumental, no vocals"),
    (217.5, 296.0, 0.40, "brooding office tension, muted piano ostinato, Japanese TV drama score, instrumental, no vocals"),
    (297.5, 381.0, 0.40, "nostalgic warm piano and soft strings, bittersweet memory, Japanese drama score, instrumental, no vocals"),
    (382.5, 386.0, 0.40, "smug light pizzicato tension, instrumental, no vocals"),
    (393.0, 501.5, 0.42, "rising suspense to a dramatic reveal, deep drums and cold strings, Japanese drama score, instrumental, no vocals"),
    (503.0, None, 0.40, "cold strings resolving into warm hopeful piano and gentle strings, Japanese drama finale, instrumental, no vocals"),
]
for _a, _b in zip(BGM, BGM[1:]):
    assert _b[0] - _a[1] >= 1.0, f"BGM 구간 간격 {_b[0] - _a[1]:.1f}s < 1.0s ({_a[1]}→{_b[0]})"

# 립싱크 연기 지시(OmniHuman prompt, 제10장 7·8): 톤연출표 감정·몸짓·강조 낱말 + 누구에게 무엇에 대답하는지.
OMNI_BASE = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, "
             "keeps looking toward the other person at the same three-quarter angle, hands stay where they are in the first frame; "
             "no exaggerated motion, the face and body stay the same person.")
OMNI_ACT = {
    "S03b": "Kuroda reassures the elderly passenger with a warm gentle smile, a small courteous nod, holding the door. Answering her apology kindly." + OMNI_BASE,
    "S05e": "Otsuka boasts lazily with a smug grin, stroking his chin, leaning back, savoring 「取締役」. Talking to Ogawa beside him, showing off." + OMNI_BASE,
    "S06e": "Otsuka explodes in rage, leaning forward between the front seats, his hand stays gripping the seat back, sharp short head movements, brow knotted, hardest on 「運転手のくせに」. Shouting at the back of the driver's head; the driver keeps facing the road and never turns." + OMNI_BASE,
    "S07e": "Otsuka sneers slowly with contempt, chin raised, leaning back, a slow dismissive shake of the head on 「負け組」. Mocking the driver after silencing Ogawa." + OMNI_BASE,
    "S09d": "Kuroda answers quietly and politely, eyes forward then to the mirror, a calm pause before 「会社は、ございません」, hands still on the wheel. Replying to Otsuka's threat without any anger." + OMNI_BASE,
    "S10b": "Ogawa speaks gently and apologetically, holding out the wiped photo frame with both hands, a small concerned tilt of the head. Speaking to the driver after her boss has left." + OMNI_BASE,
    "S11d": "Otsuka scolds with irritated contempt, tossing the documents down, a sharp jab of the finger, jaw tight. Answering Ogawa's report about paying the taxi fare." + OMNI_BASE,
    "S11h": "Otsuka boasts on the phone with a smug grin, feet up, lazily waving his free hand, a mocking laugh on 「しつけてやったよ」. Talking to a friend on the phone about last night's driver." + OMNI_BASE,
    "S12a": "Ishii speaks earnestly and gravely, holding the folder, a slow emphatic nod on 「人」. Warning Otsuka face to face before the meeting." + OMNI_BASE,
    "S15a": "Chiyoko speaks softly and weakly with a loving smile, squeezing her husband's hand, eyes glistening. Asking her husband for a promise." + OMNI_BASE,
    "S16a": "Miura greets the visitors politely with a professional smile, a small bow, hands stay folded in front of her. Welcoming the three guests." + OMNI_BASE,
    "S16d": "Ogawa asks hesitantly, pointing at the framed photograph, puzzled, glancing between the photo and her boss. Speaking to Otsuka beside her." + OMNI_BASE,
    "S17a": "Otsuka lectures smugly while straightening his tie in the window reflection, a self-satisfied smile, chin up. Instructing Ogawa just before the door opens." + OMNI_BASE,
    "S17c": "Kuroda speaks very quietly and coldly, almost motionless, eyes fixed on Otsuka, one slow blink. Greeting the man who insulted him last night." + OMNI_BASE,
    "S17f": "Otsuka stammers in panic, sweating, the business card trembling, eyes darting, a forced nervous half-smile. Making excuses to the chairman." + OMNI_BASE,
    "S18f": "Otsuka pleads in panic, leaning forward, palms stay pressed on the table, sweating, voice rising. Desperately answering Ishii's question." + OMNI_BASE,
    "S19b": "Kuroda speaks firmly and quietly, hands folded on the tablet, a slight emphasis and pause on 「金額では」. Telling Otsuka his standard, looking him in the eye." + OMNI_BASE,
    "S19e": "Kuroda answers Ishii calmly and coldly, unmoving, a single slow blink. Closing Ishii's attempt to settle it with a punishment." + OMNI_BASE,
    "S20b": "Otsuka begs desperately on his knees, looking up, hands clasped and shaking, real tears, voice breaking. Begging the chairman standing over him." + OMNI_BASE,
    "S20c": "Kuroda speaks quietly, looking down at the kneeling man, motionless, letting 「運転手のくせに」 land. Turning Otsuka's own words back on him." + OMNI_BASE,
    "S20f": "Kuroda delivers the final words coldly and calmly, a slight forward lean on 「その運転手」. Looking down at Otsuka." + OMNI_BASE,
    "S21b": "Kuroda speaks warmly and gently to Ogawa, a soft smile, his hands stay still where they rest in the first frame. Offering her the contract." + OMNI_BASE,
    "S21c": "Ogawa answers in a trembling voice, tears welling, holding the documents to her chest, eyes wide in disbelief. Answering the chairman's offer." + OMNI_BASE,
}
# 사람 i2v(live·face)는 동작 문장(motion)을 그대로 쓴다. 말하지 않는 사람·손·뒷모습만 i2v(제11장 9).
STYLE = {"NA": "Naration", "黒田": "Kuroda", "大塚": "Otsuka", "小川": "Ogawa", "石井": "Ishii", "三浦": "Miura", "千代子": "Chiyoko", "老婦人": "Rofujin"}
STYLE_JA = {"Naration": "ナレーター", "Kuroda": "黒田", "Otsuka": "大塚", "Ogawa": "小川", "Ishii": "石井", "Miura": "三浦", "Chiyoko": "千代子", "Rofujin": "老婦人"}
STYLE_COLOR = {"Naration": "&H00DDDDDD", "Kuroda": "&H00FFFFFF", "Otsuka": "&H00B4D2FF", "Ogawa": "&H00F0E6C8", "Ishii": "&H00C8C8F0",
               "Miura": "&H00E6DCC8", "Chiyoko": "&H00DCC8F0", "Rofujin": "&H00C8E6E6"}
PRO_MODEL = "fal-ai/bytedance/seedance/v1/pro/image-to-video"
RATE = {"pro": 0.108, "lite": 0.036, "omni": 0.16, "kf": 0.04}
HOOK_LEN = {"H0a": 2.0, "H0b": 2.0, "H1": 5.0, "H2": 6.0, "H3": 5.0}


def tc(sec):
    fr = int(round(sec * FPS)); s, f = divmod(fr, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}.{f:02d}"


def ass_t(sec):
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap(text, limit=19):
    """libass 일본어 자동 줄바꿈 불가 → 19자 기준 구두점에서 수동 \\N (선례와 동일)."""
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
    return "\\N".join(out)


def script_texts():
    t = open(os.path.join(PROD, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 4-1.")[0]
    return {m.group(1): m.group(2) for m in re.finditer(r"^\s+((?:NA|L|OUT|P)\d+)[^「\n]*「(.+?)」", body, re.M)}


def who_keys(s):
    return [w.split(":")[0] for w in s["who"]]


def check_rules(shots, rows, silent):
    errs = []
    order = ["ecu", "ch", "cu", "ms", "ws", "ews"]
    prev = None
    for s in shots:
        if s["kind"] == "d" and s["angle"] in ("SIDE", "BE", "OH"):
            errs.append(f"{s['id']}: OMNI 대사 컷 각도 {s['angle']} 금지(정면~45°만)")
        if s["kind"] == "d" and len(s["who"]) > 1 and s["fg"] not in ("L", "R") and not s["who"][1].endswith(":profile"):
            errs.append(f"{s['id']}: 어깨 너머 립싱크인데 전경 쪽(fg L/R) 미지정")
        if prev and prev["scene"] == s["scene"] and not s["kind"].startswith("reuse") and not prev["kind"].startswith("reuse"):
            if order.index(prev["lens"]) == order.index(s["lens"]) and prev["angle"] == s["angle"] and prev["loc"] == s["loc"]:
                errs.append(f"{prev['id']}→{s['id']}: 연속 같은 구도(A1)")
        if s["line"]:
            spk = rows[s["line"]]["spk"]
            if spk in SPK_KEY and not s["vo"] and not any(k.startswith(SPK_KEY[spk]) for k in who_keys(s)):
                errs.append(f"{s['id']}: {s['line']} 화자 {spk}가 화면에 없음(vo 표시 없이)")
            if s["vo"] and spk in SPK_KEY and s["kind"] in ("live", "face") and any(k.startswith(SPK_KEY[spk]) and ":back" not in w
                                                                                   for k, w in zip(who_keys(s), s["who"])) and "Hand" not in s["subject"] and "hand" not in s["subject"][:40]:
                errs.append(f"{s['id']}: vo 컷에 화자 {spk}의 얼굴이 i2v로 나옴(말하는 사람 비립싱크 = 정지·입 가림)")
        prev = s
    dz = sum(1 for s in shots if "dollyzoom" in s["fx"])
    dutch = sum(1 for s in shots if "dutch" in s["fx"])
    if dz != 1:
        errs.append(f"돌리줌 {dz}회(1회만)")
    if dutch > 2:
        errs.append(f"더치 {dutch}회(최대 2회)")
    for s in shots:
        if "dutch" in s["fx"] and "OTSUKA" not in who_keys(s):
            errs.append(f"{s['id']}: 더치는 악역(大塚) 장면에만")
    scenes = collections.OrderedDict()
    for s in shots:
        if s["scene"] != "H":
            scenes.setdefault(s["scene"], []).append(s)
    for sc, ss in scenes.items():
        if not ss[0]["line"] and not silent.get(sc):
            errs.append(f"{sc}: 첫 컷({ss[0]['id']})에 대사·내레이션 앵커 없음")
    return errs


def main():
    lock = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
    rows = {x["tag"]: x for x in lock["lines"]}
    texts = script_texts()
    scenes = {s["id"]: (s["start"], s["end"]) for s in lock["scenes"]}
    silent = {s["id"]: s["silent_cuts"] for s in lock["scenes"]}
    main_end = lock["body_end"]

    errs = check_rules(SHOTS, rows, silent)
    body_tags = {t for t, x in rows.items() if x["scene"].startswith("S")}
    used = [s["line"] for s in SHOTS if s["line"]]
    if sorted(used) != sorted(body_tags):
        errs.append(f"대사 줄 사용 불일치: 빠짐 {sorted(body_tags - set(used))}, 중복·초과 {sorted(set(u for u in used if used.count(u) > 1) | (set(used) - body_tags))}")
    if errs:
        raise SystemExit("규칙 위반:\n  " + "\n  ".join(errs))

    # ---------- 샷 타이밍: 대사 앵커 + 앵커 사이 균등 분배 ----------
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
                pins[k] = max(a, rows[s["line"]]["start"] - (s["lead"] or LEAD))
            elif s["pin"] and k:
                pins[k] = rows[s["pin"][0]]["start"] + s["pin"][1]
        keys = sorted(pins)
        for k1, k2 in zip(keys, keys[1:]):
            t1, t2 = pins[k1], pins[k2]
            n = k2 - k1
            for j in range(k1, k2):
                starts[shots[j]["id"]] = t1 + (t2 - t1) * (j - k1) / n
    order_ids = [s["id"] for s in SHOTS]
    ends = {sid: (starts[order_ids[k + 1]] if k + 1 < len(order_ids) else main_end) for k, sid in enumerate(order_ids)}
    for k, s in enumerate(SHOTS):  # OMNI 8초 상한 → 다음 컷 시작을 당김(듣는 사람 반응으로 넘어감)
        if s["kind"] == "d" and ends[s["id"]] - starts[s["id"]] > OMNI_MAX:
            nxt = order_ids[k + 1]
            starts[nxt] = starts[s["id"]] + OMNI_MAX; ends[s["id"]] = starts[nxt]
    problems = []
    for s in SHOTS:
        d = ends[s["id"]] - starts[s["id"]]
        if d < MIN_SHOT:
            problems.append(f"{s['id']} {d:.2f}s < {MIN_SHOT}")
        if s["kind"] in ("react", "ins", "estill") and d > STILL_MAX:
            problems.append(f"{s['id']} 정지 {d:.2f}s > {STILL_MAX}")
        if s["kind"] in ("face", "live", "empty") and d > I2V_MAX:
            problems.append(f"{s['id']} i2v {d:.2f}s > {I2V_MAX}")
        if s["kind"] == "d" and s["line"] and d < rows[s["line"]]["dur"] * 0.6:
            problems.append(f"{s['id']} 립싱크 컷 {d:.2f}s가 대사 {rows[s['line']]['dur']:.2f}s의 60% 미만(다음 컷 배치 확인)")
    if problems:
        raise SystemExit("컷 길이 위반:\n  " + "\n  ".join(problems))

    # ---------- 출력 데이터 ----------
    durations, sb, scene_items = [], [], []
    cost = collections.Counter()
    for s in SHOTS:
        sid = s["id"]; d = ends[sid] - starts[sid]
        durations.append(round(d + HARD, 4))
        refs, ids = [], []
        for wi, w in enumerate(s["who"]):
            parts = w.split(":")
            key, ward = parts[0], (parts[1] if len(parts) > 1 else "")
            view = parts[2] if len(parts) > 2 else ("back" if s["kind"] == "d" and wi > 0 else "")  # 립싱크 컷의 둘째 인물 = 전경 듣는 사람(뒷모습)
            if view == "profile":   # 차 안 운전자: 늘 앞(전면 유리)을 보므로 옆모습으로 화면 가장자리(운전석 공간 문법, R33)
                desc, front, _ = WHO[key]
                drv = key == "KURODA_D"
                ids.append(desc + (f", wearing {WARD[ward]}" if ward else "") + (", seen in side profile at the frame edge facing forward toward the windshield" if drv else
                           ", a soft side profile at the frame edge sitting BESIDE the speaker on the same rear bench seat, body facing forward (R37: 뒷좌석은 나란히 앉음)"))
                refs.append(C + ("kuroda-driver-sheet-profile.png" if drv else front.split("/")[-1].replace("-front", "-profile")))
                continue
            back = view == "back"
            desc, front, backcell = WHO[key]
            ids.append(desc + (f", wearing {WARD[ward]}" if ward else "") +
                       ((", the listener in the soft blurred foreground seen only from behind (back of the head and one shoulder), face not visible" if s["kind"] == "d" and wi > 0
                         else ", seen only from behind, face not visible") if back else ""))
            if back and backcell:
                refs.append(backcell)
            elif s["expr"] and (key, s["expr"]) in EXPR and w == s["who"][0]:
                refs.append(EXPR[(key, s["expr"])])
            elif front:
                refs.append(front)
        if s["loc"]:
            refs.append(LOC[s["loc"]])
        n = len(s["who"])
        if s["kind"] == "d" and n > 1 and s["who"][1].endswith(":profile"):
            comp = ("Car-interior geometry: the driver always faces forward toward the windshield; the passenger in the back seat speaks toward the driver from behind. "
                    "The speaker's face at least one quarter of the frame height at a three-quarter angle, sharp focus on the speaker's eyes; the driver only a soft side profile at the frame edge.")
        elif s["kind"] == "d" and n > 1:
            side = {"L": "left", "R": "right"}[s["fg"]]
            comp = (f"Over-the-shoulder conversation shot: the listener's blurred shoulder and back of the head fill the {side} edge of the foreground; "
                    f"the speaker faces the listener at a three-quarter angle (30 to 40 degrees from the camera), the speaker's face at least one quarter of the frame height, "
                    "sharp focus on the speaker's eyes, hands doing the described action.")
        elif s["kind"] == "d":
            comp = "Exactly one person in frame, a three-quarter (30 to 40 degrees) chest-up shot, the face at least one quarter of the frame height, hands doing the described action."
        elif s["kind"] in ("empty", "estill") or (s["kind"] in ("ins",) and not s["who"]):
            comp = "Completely unpopulated: no people, no hands, no faces."
        elif "Hand" in s["subject"][:12] or "hands only" in s["subject"].lower() or "hand only" in s["subject"].lower():
            comp = "A true insert: only the hands and the object fill the frame; no face, no head, no extra arms."
        else:
            comp = f"Exactly {n} {'person' if n == 1 else 'people'} as described, no extra people."
        if any(":back" in w for w in s["who"]) or s["kind"] == "react":
            comp += " The speaker's mouth is never visible (back view, bowed head, mirror crop, silhouette or angle)."
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/{SKIT}-keyframes/{sid}-1.png"
        kf_prompt = None
        if keyframe:
            low = (s["subject"] + " " + (s["expr"] or "")).lower()
            real = " ".join(x for x, keys in ((TEARS, ("tear", "beg", "cry")), (SWEAT, ("sweat",))) if any(k in low for k in keys))
            glasses = " ".join(GLASSES[k] for k in who_keys(s) if k in GLASSES)
            plate = ("The taxi has a plain green license plate with no characters and a plain white dome roof lamp with no characters."
                     if s["loc"] in TAXI_LOCS else "")
            kf_prompt = " ".join(x for x in [PRESET + ".", s["subject"], ("Characters: " + " | ".join(ids) + ".") if ids else "", NAT if ids else "",
                                             glasses, real, plate, f"Camera: {ANGLE[s['angle']]}, {LENS[s['lens']]}.", f"Lighting: {LIGHT[s['light']]}.",
                                             comp, PLAIN, f"Negative: {NEGATIVE}."] if x).strip()
            cost["kf"] += 1
        tier = {"d": "omni", "react": "still", "ins": "still", "estill": "still", "face": "pro", "live": "lite", "empty": "lite", "card": "card"}.get(s["kind"], "reuse")
        gen = 10 if d > 5.0 else 5
        item = {"prompt": "", "duration": gen}
        if tier in ("pro", "lite"):
            item["prompt"] = ("Static, locked off camera. Motion: " + (s["motion"] or "Subtle natural motion only.") +
                              " Keep the exact faces, wardrobe, props and lighting of the first frame. Head turns under 15 degrees. "
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
                   "size": s["lens"], "lens": LENS[s["lens"]], "angle": s["angle"], "lighting": s["light"], "edit_fx": s["fx"],
                   "refs": refs, "subject": s["subject"], "line": s["line"], "vo": s["vo"], "fg": s["fg"],
                   "motion": item["prompt"] if tier in ("pro", "lite") else "", "keyframe": keyframe, "keyframe_prompt": kf_prompt,
                   "ja_overlay": JA_OVERLAY.get(sid, ""), "plate_andon": s["loc"] in TAXI_LOCS, "caption": CARDS.get(sid, "")})
    budget = round((cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"]) * 1.25, 2)

    # ---------- 음성: 시간 순 번호로 합치기(자막 TTS 줄 번호 = 캐시 번호, 보정 재녹음 우선) ----------
    tts_order = sorted([x for x in lock["lines"] if x["scene"].startswith("S") or x["tag"] == "NA0"],
                       key=lambda x: (x["start"] if x["start"] is not None else 9.5))
    dst = os.path.join(ROOT, "assets", "audio-overrides", SKIT)
    os.makedirs(dst, exist_ok=True)
    mapping = []
    for i, x in enumerate(tts_order, 1):
        add = os.path.join(ROOT, "assets", "auditions", "untenshu-tts-add", x["id"] + ".mp3")
        src = add if os.path.exists(add) else os.path.join(ROOT, "assets", "auditions", "untenshu-tts", x["id"] + ".mp3")
        shutil.copyfile(src, os.path.join(dst, f"line{i:03d}.mp3"))
        mapping.append((f"line{i:03d}", x["tag"], os.path.relpath(src, ROOT)))

    # ---------- 자막(ASS) ----------
    events = []
    for i, x in enumerate(tts_order, 1):
        st = STYLE["NA" if x["spk"] == "NA" else x["spk"]]
        s0 = (9.5 - x["lead"]) if x["tag"] == "NA0" else (x["start"] - x["lead"])
        e0 = (9.5 + x["dur"] + 0.2) if x["tag"] == "NA0" else (x["end"] + 0.2)
        events.append((s0, e0, st, STYLE_JA[st], wrap(texts[x["tag"]])))
    for sid, cap in CARDS.items():
        if sid == "H3":
            continue
        c0 = starts[sid] + 0.3
        events.append((c0, min(ends[sid] - 0.2, c0 + 4.0), "Caption", "", cap))
    events.append((starts["H3"] + 0.6, starts["H3"] + HOOK_LEN["H3"] - 0.3, "Title", "", "運転手のくせに\\N{\\fs44}" + TITLE_SUB))
    h1 = rows["L11"]
    events.append((starts["H1"] + 0.4, starts["H1"] + 0.4 + h1["dur"] + 0.3, "HookLine", "大塚", wrap(texts["L11"])))
    events.sort(key=lambda e: e[0])
    st_lines = "\n".join(
        f"Style: {n},Noto Sans CJK JP,{58 if n != 'Naration' else 52},{c},&H000000FF,&H00000000,&H80000000,-1,{-1 if n == 'Naration' else 0},0,0,100,100,0,0,1,5,2,2,200,200,80,1"
        for n, c in STYLE_COLOR.items())
    ass = ["[Script Info]", "Title: 運転手のくせに 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           st_lines,
           "Style: HookLine,Noto Sans CJK JP,58,&H00B4D2FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1",
           "Style: Caption,Noto Sans CJK JP,84,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,160,160,80,1",
           "Style: Title,Noto Serif CJK JP,110,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,5,160,160,80,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{e[4]}")
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    # ---------- 스토리보드·장면·오디오 ----------
    os.makedirs(os.path.join(ROOT, "scripts", "storyboard"), exist_ok=True)
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_untenshu_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT,
               "preset": PRESET, "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"],
               "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_untenshu_phase3.py 생성). override_required 장면은 정지·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, "
                         "wardrobe, props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_untenshu_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (Typecast 확정본, 보정 재녹음 우선).",
        "default_voice": "cached-typecast", "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Naration"], "silent_styles": ["Caption", "HookLine", "Title"],
        "output_size": [1920, 1080], "fit": "crop",
        "scene_durations": durations, "transitions": [0.0] * len(durations),
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d"],
        "omnihuman_prompts": {str(idx[k]): v for k, v in OMNI_ACT.items() if k in idx},
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0,
        "legacy_lipsync": False,
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35,
        "ambience_prompts": [AMBIENCE.get(sid, "") for sid in order_ids],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": s, "end": round(main_end, 2) if e is None else e, "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_후크": "0~4초 BGM 없음: 빗소리·와이퍼 + 심장 박동 1회를 PHASE 6에서 로컬 믹스(−60dB 2초 무음 금지 충족). "
                 "H1 화면은 S06e 재사용, 음성은 L11 원본을 로컬 믹스. H2 내레이션 NA0은 자막 1번 줄(TTS 캐시 line001).",
        "_레코더": "S18 첫머리 5.0초(무언 비트) = L11 원음을 태블릿 스피커 필터(대역 300~3400Hz·약한 왜곡)로 로컬 믹스, BGM 정지(4-3절 B-2).",
        "_정지": "P8 끝(약 6:29) BGM 정지 0.8초 → 문손잡이 효과음 → S17b(4-3절 A-9).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---------- 검토 문서 ----------
    gen_shots = [s for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card"]
    ang = collections.Counter(s["angle"] for s in gen_shots)
    tiers = collections.Counter(x["tier"] for x in sb)
    people = [x for x in sb if x["kind"] in ("d", "live", "face", "react", "ins") and SHOTS[order_ids.index(x["id"])]["who"]]
    people_still = [x for x in people if x["tier"] == "still"]
    total_cost = cost["kf"] * RATE["kf"] + cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    if top[1] / sum(ang.values()) > 0.6:
        raise SystemExit(f"앵글 쏠림: {top[0]} {top[1] / sum(ang.values()) * 100:.0f}% > 60%")
    md = ["# 『運転手のくせに』 PHASE 3 샷 리스트", "",
          f"> `scripts/build_untenshu_phase3.py` 자동 생성(손 수정 금지). 타임코드는 분:초.프레임(24fps). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " +
          ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock["ads"]) + ".",
          f"> 자동 검사 통과: 연속 같은 구도 0 · 돌리줌 1회 · 더치 2회(大塚만) · OMNI 정면~45°·어깨 너머 전경 지정 · 화자-화면 일치(vo 예외) · 대사 {len(used)}줄 전부 배치 · 컷 길이(1.2초 이상, 정지 6.5초·i2v 10초 이하) · OMNI 8초 · BGM 간격 1.0초.",
          f"> **움직임**: 사람이 나오는 컷 {len(people)}개 중 정지 {len(people_still)}개({len(people_still) / len(people) * 100:.0f}%) — 정지는 말하는 사람의 입 가림 컷(뒷모습·백미러·고개 숙임)과 손·소품 글자 합성 면뿐(4-2절 ①). 립싱크 {tiers['omni']}컷.", "",
          "## 비용 추산 (실측 단가)", "",
          "| 항목 | 수량 | 단가 | 금액 |", "|---|---|---|---|",
          f"| 키프레임 | {cost['kf']}장 | 0.04 | {cost['kf'] * RATE['kf']:.2f} |",
          f"| i2v pro 1080p (얼굴 반응) | {cost['pro']}초 | 0.108 | {cost['pro'] * RATE['pro']:.2f} |",
          f"| i2v lite 720p (사람·손·무인) | {cost['lite']}초 | 0.036 | {cost['lite'] * RATE['lite']:.2f} |",
          f"| OmniHuman (8초 상한 + 앞뒤 0.8초) | {cost['omni']:.1f}초 | 0.16 | {cost['omni'] * RATE['omni']:.2f} |",
          f"| **1차 합계** (재생성 여유 제외) | | | **{total_cost:.2f}** |",
          f"| i2v 예산 상한 `budget_usd` (여유 25%) | | | {budget:.2f} |", "",
          "## 생성 방식 분포", "", "| 방식 | 컷 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in tiers.most_common()] + [
          "", f"## 앵글 분포 (생성 컷) — 최다 {top[0]} {top[1] / sum(ang.values()) * 100:.0f}% (60% 이하 기준 충족)", "", "| 앵글 | 컷 |", "|---|---|"] + [
          f"| {k} | {v} |" for k, v in ang.most_common()] + [
          "", "## 화면 속 일본어·번호판 (키프레임은 무지 → 로컬 합성, PHASE 4 마감 전)", ""] + [f"- {k}: {v}" for k, v in JA_OVERLAY.items()] + [
          "- 번호판 「東都 500 あ 37-08」·행등 「個人」(`plate_overlay.py`): " + ", ".join(x["id"] for x in sb if x["plate_andon"]),
          "", "## 샷 표", "", "| 컷 | 타임코드 | 길이 | 방식 | 사이즈 | 앵글 | 조명 | 편집 효과 | 대사 | 화면 | 참조 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in sb:
        md.append(f"| {x['id']} | {x['timecode']} | {x['assembled_s']:.2f}s | {x['tier']} | {x['size']} | {x['angle']} | {x['lighting']} | {x['edit_fx']} | "
                  f"{x['line'] or ''}{' (vo)' if x['vo'] else ''} | {x['subject'][:60]} | {len(x['refs'])}장 |")
    md += ["", "## 음성 번호 대응 (자막 TTS 줄 = 캐시 파일)", "", "| 캐시 | 대본 | 원본 녹음 |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in mapping]
    open(os.path.join(PROD, "07_샷리스트.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    angle_doc(sb, order_ids)
    emotion_table(sb)
    print(f"완료: 컷 {len(SHOTS)}개, 본편 {tc(main_end)}, 방식 {dict(tiers)}, 사람 정지 {len(people_still)}/{len(people)}, "
          f"1차 비용 약 {total_cost:.2f}달러 (i2v budget {budget}), 앵글 {dict(ang)}")


def angle_doc(sb, order_ids):
    """02_카메라앵글설계.md — 장면별 컷 순서(사이즈·앵글·조명·방식) 요약(제8장 7). Lock 입력이 아니다."""
    KO = {"EL": "아이레벨", "HA": "하이", "LA": "로우", "OH": "오버헤드", "BE": "버즈아이", "SIDE": "측면·뒷모습"}
    by = collections.OrderedDict()
    for x in sb:
        by.setdefault(x["scene"], []).append(x)
    md = ["# 『運転手のくせに』 카메라 앵글 설계 (PHASE 3 생성기 산출물, 제8장 7)", "",
          "> 장면별 컷 순서: 사이즈/앵글/조명/방식. 권력 반전 — 차 안 大塚 로우 → 회의실 大塚 버즈아이·黒田 로우(제8장 3·4-3).", "",
          "| 장면 | 컷 순서 |", "|---|---|"]
    for sc, xs in by.items():
        md.append(f"| {sc} | " + " → ".join(f"{x['id']}({x['size']}/{KO[x['angle']]}/{x['lighting']}/{x['tier']})" for x in xs) + " |")
    open(os.path.join(PROD, "02_카메라앵글설계.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")


# ---------- 감정 일치표(제10장 7) ----------
EMO_OK = {
    "angry": ("anger", "rage", "glare", "furious", "shout", "jaw", "contempt", "sneer", "irritat", "scold", "flick", "jab", "slam", "scowl", "explod", "dismiss"),
    "happy": ("smile", "grate", "smirk", "sneer", "laugh", "grin", "mock", "pleased", "satisf", "smug", "warm", "boast", "gentle"),
    "sad": ("sob", "tear", "cry", "beg", "plea", "sad", "tremb", "hurt", "weak", "apolog", "lower", "bow", "disbelief", "pale", "stunned", "hold", "promise"),
    "tonedown": ("cold", "quiet", "calm", "restrain", "grave", "low", "icy", "earnest", "silence", "gentle", "steady", "firm", "unmov", "still", "bow", "patient", "lectur", "smug"),
    "toneup": ("alarm", "panic", "shock", "excite", "fright", "urgent", "puzzl", "hesit", "plead", "reach", "stammer", "eager", "boast"),
    "whisper": ("whisper", "lean", "smug"),
    "normal": (),
}
EMO_BAD = {"angry": ("sob", "peaceful"), "happy": ("sob", "fury", "rage"), "sad": ("laugh", "grin", "sneer"), "tonedown": ("shout", "laugh", "slam")}
REACT = ("flinch", "uneasy", "patient", "steady", "hurt", "lower", "glance", "tighten", "swallow", "nod", "fill", "tremb", "slack", "wide",
         "breath", "jaw", "glare", "irritat", "tender", "tear", "stunned", "blur", "settle", "flash", "rain falls", "glows")   # 차 밖·무인 컷은 장면 분위기로 대신(blur·rain)
INTENDED = ("비웃", "즐기", "깔보", "억누른", "서늘", "냉정", "차갑", "아이러니", "반성 없")


def emotion_table(sb):
    import sys
    sys.path.insert(0, PROD)
    from build_tts_spec import TONE
    rows, warn = [], 0
    for x in sb:
        tag = x["line"]
        if not tag or tag not in TONE or tag.startswith(("NA", "OUT")) or (tag.startswith("P") and x["vo"] is False and tag in ("P1", "P4", "P5", "P11")):
            continue
        emo, inten, tempo, memo = TONE[tag]
        act = OMNI_ACT.get(x["id"]) or x.get("motion") or ""
        seen = " ".join([x["subject"], act]).lower()
        if x["vo"]:   # 듣는 사람 반응 컷: 화면은 그 대사를 「듣고 반응」해야 한다(말하는 사람의 감정을 흉내 내지 않음)
            ok = any(k in seen for k in REACT)
            bad = []
        else:
            ok = not EMO_OK.get(emo) or any(k in seen for k in EMO_OK[emo])
            bad = [k for k in EMO_BAD.get(emo, ()) if k in seen]
        intended = any(k in memo for k in INTENDED)
        state = "✅" if ok and (not bad or intended) else "⚠️"
        if state == "⚠️":
            warn += 1
        how = "립싱크" if x["tier"] == "omni" else (("듣는 사람 반응 " if x["vo"] else "") + ("i2v" if x["tier"] in ("lite", "pro") else "정지"))
        rows.append(f"| {state} | {x['id']} | {tag} | {how} | {emo} {inten} · {tempo} | {memo} | {x['subject'][:70]} | {act[:90]} |")
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_untenshu_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않거나 부딪힘. 「듣는 사람 반응」 컷은 화면의 반응이 그 대사에 맞는지 본다.", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 감정·세기·템포 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")
    if warn:
        raise SystemExit("감정 일치표 경고가 있습니다 — 동작·표정 문장을 고친 뒤 다시 실행")


if __name__ == "__main__":
    main()
