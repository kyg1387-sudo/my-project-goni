#!/usr/bin/env python3
"""『母が遺したビデオレター』(aihaha-ja) PHASE 3 샷 리스트 Lock 생성기 — build_hikikomori_phase3.py를 옮긴 것(손 수정 금지, 이 파일만 고친다).

이 작품에서 달라진 것:
  · 극 중 가짜 비디오레터(AI母)는 일부러 AI답게: H0a 립싱크 1컷을 만들어 태블릿(S04l)·TV(S09e)·창 확대(S05a)에 같은 영상으로 합성(제21장 4·9)
  · 증거 배경 = 창밖 비계: 7/25 전(S01) ROOM_SCAF, 후(가짜 영상·S05 이후) ROOM_FIN — 키프레임 맨 앞 상태 고정 문장(제19장 27·제21장 6)
  · 조명 전환 1회: S09 거실 3200K(LIV_WARM) → 형광등 끈 S09d 이후 5600K(LIV_COLD)
  · 권력 역전 앵글: 숙부 S02·S04·S08 LA → S09 후반 HA → S11j BE(버즈아이)
  · 인서트 16곳은 내레이션 아래(lock UNDER), 무언 컷은 펜 끝(S08i)·형광등(S09d)·翔太 핏기(S09p)·결정타 앞(S10j)·눈물(S13d)
  · 눈물 기준 = aihaha-ref/tear-standard-yukiko.png(고니감독님 승인), 땀 기준 = sweat-standard-tsuyoshi.png (10_눈물땀설계.md)
입력: productions/aihaha-ja/lock.json · 00_script_ja.md · assets/auditions/aihaha-tts-b/lineNNN.mp3 · assets/portraits/aihaha-ref/
출력: scripts/storyboard/aihaha.json · scripts/scenes/aihaha.json · scripts/audio/aihaha.json · subs/aihaha.ass ·
      assets/audio-overrides/aihaha/lineNNN.mp3 · productions/aihaha-ja/07_샷리스트.md · 16_감정일치표.md
사용법: python3 scripts/build_aihaha_phase3.py
"""
import collections, json, os, re, shutil, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "aihaha-ja")
sys.path.insert(0, PROD)
SKIT = "aihaha"
TTS_DIR = "aihaha-tts-b"
# 글자 합성 면이라 정지로 바꾼 긴 인서트 — 편집 카메라가 서류 3장을 차례로 훑거나(pan) 재생 버튼으로 다가가(pushto) 정지감을 깬다(제4장·제8장 6)
STILL_LONG_OK = {"S09i": 9.5, "S13a": 7.2}
FPS = 24; HARD = 1 / FPS; OMNI_MAX = 7.9; LEAD = 0.3; MIN_SHOT = 1.2; STILL_MAX = 6.5; I2V_MAX = 10.0

R = "assets/portraits/aihaha-ref/"
C = R + "cells/"
WHO = {
    "YUK": ("Saeki Yukiko, a Japanese woman aged 46, oval face with faint fine lines, shoulder-length straight black hair tied LOW in a single ponytail at the nape, "
            "thin silver wire-rim ROUND glasses, bare earlobes with no jewelry, natural minimal makeup", R + "yukiko-front.png"),
    "SAW": ("Saeki Sawako, a small Japanese woman aged 74, short soft WHITE permed hair, gentle crow's feet, exactly ONE small dark mole on her RIGHT cheek, "
            "bare face with her eyes uncovered, bare earlobes", R + "sawako-front.png"),
    "AIM": ("the SAME elderly woman rendered as an uncanny AI deepfake: unnaturally smooth airbrushed skin, perfect left-right symmetry, glassy fixed eyes "
            "staring straight into the lens, a stiff polite smile", R + "ai-haha.png"),
    "TSU": ("Ono Tsuyoshi, a heavy-set Japanese man aged 66, receding hairline with grey hair slicked straight back, thick jowls, a plain GOLD wristwatch on his LEFT wrist, "
            "bare face with his eyes uncovered, bare earlobes, clean-shaven", R + "tsuyoshi-front.png"),
    "YOR": ("Ono Yoriko, a Japanese woman aged 63, brown-dyed short wavy bob, ONE single strand pearl necklace, thin pencilled eyebrows, bare face, bare earlobes",
            R + "yoriko-front.png"),
    "SHO": ("Ono Shota, a slim Japanese man aged 36, two-block haircut with a longer side-swept black top, thick BLACK rectangular plastic-frame glasses, clean-shaven, bare earlobes",
            R + "shota-front.png"),
    "MIY": ("Detective Miyashita, a fit Japanese man aged 52, very short-cropped salt-and-pepper hair, square jaw, calm observant eyes, bare face, bare earlobes, clean-shaven",
            R + "miyashita-front.png"),
}
WARD = {
    "knit": "a plain beige crew-neck knit sweater and plain grey slacks, no logo",
    "mourn": "a plain black Japanese mourning dress with long sleeves, no ornaments",
    "coat": "a plain camel-beige wool coat over the beige knit and grey slacks",
    "lav": "a plain lavender (light purple) cardigan over a plain cream blouse",
    "fake": "the same plain lavender cardigan over a cream blouse",
    "tmourn": "a plain black Japanese mourning suit, white shirt, plain black tie, plain lapels",
    "golf": "a plain navy golf windbreaker jacket with no logo over a plain white polo shirt",
    "ymourn": "a plain black mourning dress and the single strand pearl necklace",
    "blouse": "a plain wine-red blouse and a plain black skirt, the single strand pearl necklace",
    "ssuit": "a plain black suit, white shirt, plain black tie",
    "hood": "a plain grey hoodie with no print under a plain black casual jacket",
    "navy": "a plain navy business suit with plain lapels and nothing pinned on them, white shirt, plain navy tie",
}
WATCH_Y = "the small old women's wristwatch with a worn brown leather strap and a plain cream dial (no numbers, no text) on her LEFT wrist"
WATCH_M = "the same small old brown-leather wristwatch on the mother's LEFT wrist (Yukiko's wrists are bare)"
WARD_REF = {("YUK", "mourn"): R + "yukiko-mourning.png", ("YUK", "coat"): R + "yukiko-coat.png", ("TSU", "golf"): R + "tsuyoshi-golf.png",
            ("YOR", "blouse"): R + "yoriko-blouse.png", ("SHO", "hood"): R + "shota-hoodie.png"}
EXPR = {  # PHASE 2 확정 참조(aihaha-ref) — 비립싱크 얼굴은 45° 셀로 시선 고정(제19장 10①), 눈물·땀은 승인 기준 컷
    ("YUK", "g45"): R + "yukiko-45.png", ("YUK", "tear"): R + "tear-standard-yukiko.png", ("TSU", "sweat"): R + "sweat-standard-tsuyoshi.png",
    ("YUK", "back"): C + "yukiko-back.png", ("SAW", "back"): C + "sawako-back.png", ("TSU", "back"): C + "tsuyoshi-back.png",
    ("YOR", "back"): C + "yoriko-back.png", ("SHO", "back"): C + "shota-back.png", ("MIY", "back"): C + "miyashita-back.png",
}
EXPR_TXT = {
    "calm": "calm, quietly tired eyes", "resolve": "quiet steely resolve, lips set, steady gaze, NOT smiling", "hold": "held-back pain, lips pressed, NOT smiling",
    "grief": "held-back grief, eyes wet, lips pressed, NOT smiling", "tear": "quietly crying, NOT smiling", "smile": "a gentle faint smile",
    "warm": "a warm loving smile with crow's feet", "chatty": "cheerful chatty expression, mid-sentence", "tender": "a tender slightly tired smile",
    "fake": "a stiff polite smile that never changes, glassy unblinking eyes", "smug": "smug, self-satisfied", "falsekind": "a false gentle smile, eyes not smiling",
    "press": "contemptuous pressure, chin raised, NOT shouting", "sneer": "a thin mocking half-smile, one corner of the mouth raised, NOT laughing",
    "dry": "fake sorrow, dabbing completely DRY eyes, no tears at all", "smirk": "an arrogant smirk", "bored": "bored indifference",
    "pale": "his face turning pale with shock, eyes wide, lips parted, NOT smiling", "panic": "panic, eyes wide, mouth tense, NOT smiling",
    "shout": "furious, face flushed, brows knotted, NOT smiling", "plead": "pleading, brows raised in the middle, NOT smiling",
    "listen": "calm attentive listening", "warn": "serious low-voiced warning, steady eyes", "nod": "the faintest approving smile at the corners of the eyes",
    "fear": "pale fear, lips trembling, NOT smiling", "stunned": "stunned, lips parted, NOT smiling", "back": "",
}
LOC = {
    "ROOM_SCAF": R + "loc-room-window-scaffold.png", "ROOM_FIN_D": R + "loc-room-window-finished-day.png", "ROOM_FIN_N": R + "loc-room-window-finished-night.png",
    "ROOM_D": R + "loc-room-wide-day.png", "ROOM_N": R + "loc-room-wide-night.png", "CHEST": R + "loc-room-chest.png",
    "LIV_W": R + "loc-living-warm.png", "LIV_C": R + "loc-living-cold.png", "HALL": R + "loc-hallway-camera.png",
    "RYO_A": C + "loc-ryotei-1.png", "RYO_T": C + "loc-ryotei-2.png", "RYO_L": C + "loc-ryotei-3.png",
    "POL_A": C + "loc-police-1.png", "POL_W": C + "loc-police-2.png", "POL_O": C + "loc-police-3.png", "POL_T": C + "loc-police-4.png",
    "RIVER": C + "loc-exterior-1.png", "STREET": C + "loc-exterior-4.png", "HOUSE_D": C + "loc-house-1.png", "HOUSE_E": C + "loc-house-2.png",
}
LOC_TXT = {
    "KITCHEN": "a small old Japanese kitchen of a modest wooden house: a two-burner stove, a small pot of simmered vegetables (nimono) steaming, plain cupboards, no labels",
    "GENKAN": "the raised genkan entrance of an old modest Japanese house seen from inside: a wooden step, a plain shoe cabinet, a frosted sliding door, shoes scattered on the concrete floor",
    "ALTAR": "a modest Japanese wake (tsuya) set up in the tatami living room of an old house: a white-draped altar with chrysanthemums, incense smoke, the framed portrait (the photo will be composited)",
    "NIGHT_DESK": "a dark tatami room at night lit only by one warm floor lamp, a low wooden table",
}
PRESET = ("Photorealistic live-action Japanese human drama, contemporary Japan (Reiwa era), a regional city in Chiba, Arri Alexa cinematic color grade, Kodak 35mm film grain, "
          "24fps, 16:9, restrained Japanese film mise-en-scene, no flat lighting, natural skin texture with pores")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, logo on shirt, signage lettering, documents with writing, "
            "screens with text, printed labels, brand logos, watermarks, stamps, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, anime, 3d render, "
            "illustration, plastic skin, thick glossy gel tears, cartoon sweat drops, tears on both cheeks, earrings, lapel pins, cranes, LED light strips")
PLAIN = ("All papers, forms, screens, calendars and labels are completely blank (screens show only a soft plain glow); no letters, numbers or symbols anywhere in the frame.")
TEARS = ("Realistic tears exactly like the approved reference: the rims of the eyes and the tip of the nose slightly pink, eyes glistening with a thin film of tears on the lower eyelids, "
         "at most ONE thin transparent tear track on ONE cheek catching a faint highlight only at its edge, the rest of the skin matte with pores; no gel, no droplets on both cheeks.")
SWEAT = ("Realistic sweat exactly like the approved reference: a few tiny natural beads on the forehead and temples, a faint natural oily sheen at the hairline, NOT glossy, no large drops.")
WET_HOLD = " Eyes wet and glistening with tears welling on the lower lids but NOT running down — the tears stay pooled."
TEARS_FLOW = (" NOT smiling at any moment. A single thin transparent tear slowly spills over her right lower eyelid and runs down along the natural curve of her cheek to about one third, "
              "catching a faint highlight of the window light; she blinks once slowly, her breath trembles, lips pressed together. Head still, no other tears.")
SWEAT_FLOW = " A single small bead of sweat slowly runs from his temple down toward the jawline; he swallows hard, eyes darting sideways. Head still."
NOSMILE = "NOT smiling at any moment: brows knotted, the corners of the mouth pulled down. "
GLASSES = {"YUK": "Yukiko wears her thin silver wire-rim ROUND glasses.", "SAW": "Sawako wears nothing on her face.", "AIM": "She wears nothing on her face.",
           "TSU": "Tsuyoshi wears nothing on his face.", "YOR": "Yoriko wears nothing on her face.", "SHO": "Shota wears his thick black rectangular glasses.",
           "MIY": "Miyashita wears nothing on his face."}
HANDS = {"YUK": "a middle-aged woman's slim hands", "SAW": "an elderly woman's thin wrinkled hands", "TSU": "plump hands with a plain gold wristwatch on the left wrist",
         "YOR": "a woman's hands with pale pink nails", "SHO": "a young man's slim hands", "MIY": "a fit man's hands"}
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, the face fills at least one third of the frame height",
    "ots": "50mm lens, f/2.0, over-the-shoulder three-quarter framing, the listener's blurred shoulder and back of the head in the near foreground edge, the speaker's face at least one third of the frame height",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds, the person's face at least one quarter of the frame height",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective",
}
LIGHT = {
    "morning": "soft diffuse morning daylight from the window, low contrast, a faint warm golden rim light, 3200K-warm memory grade",
    "grey": "overcast grey morning light from the window, quiet and colourless",
    "wake": "warm 3200K tungsten light of a home wake, faces half in shadow with no fill light, incense haze",
    "cctv": "a black-and-white night-vision security camera view, flat grey light",
    "ryotei": "cold top light 5600K from a plain ceiling panel mixed with soft shoji daylight, pressure",
    "night_lamp": "night, one warm 3200K floor lamp only, deep shadows, the face lit by the soft cold glow of a tablet screen",
    "analysis": "cool crisp 5600K daylight from the window, clean balanced tones, quiet focus",
    "police": "flat cool overhead fluorescent 5600K with striped daylight through window blinds",
    "dusk": "late summer dusk, warm sky fading, long soft shadows",
    "sep_day": "early autumn afternoon daylight from the living room window, slightly harsh",
    "warm_liv": "evening, warm 3200K table lamp, the round ceiling light OFF, heavy comfortable shadows, a false cosy mood",
    "cold_liv": "the round ceiling fluorescent light ON: cold flat 5600K white light from above, hard clinical shadows under the brows",
    "police_red": "cold 5600K ceiling fluorescent plus slow red and blue police light reflections sweeping across the window glass",
    "nov": "late-autumn morning 5000K soft daylight, clear and calm",
    "nov_room": "late-autumn morning sunlight through the window, a gentle warm backlight rim on her hair, low contrast",
    "screen": "a tablet screen glowing in a dark room",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}
SPK_KEY = {"由紀子": "YUK", "母": "SAW", "AI母": "AIM", "叔父": "TSU", "叔母": "YOR", "翔太": "SHO", "宮下": "MIY"}
SCAF = "WINDOW STATE LOCKED FIRST: through the window the tall tower is COMPLETELY wrapped in metal scaffolding and green safety mesh (before 25 July). "
FIN = "WINDOW STATE LOCKED FIRST: through the window the same tall tower is FINISHED — clean facade, NO scaffolding, NO green mesh, NO cranes (after 25 July). "


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, act="", vo=False, pin=None, replay=None):
    """kind: d(OmniHuman 립싱크) / face(사람 i2v) / empty / estill(무인·합성 면 정지) / pstill(말하는 화자 뒷모습 정지 + 편집 카메라) /
    ins(손·소품 — motion 있으면 i2v, 없으면 정지) / reuse:<id> / card.  vo=True = 화자 화면 밖. who = "인물:의상"."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc, subject=subject,
                line=line, fx=fx, motion=motion, expr=expr, act=act, vo=vo, pin=pin, replay=replay)


Yk, Ym, Yc, Sl, Af, Tm, Tg, Om, Ob, Hs, Hh, Mn = ("YUK:knit", "YUK:mourn", "YUK:coat", "SAW:lav", "AIM:fake", "TSU:tmourn", "TSU:golf", "YOR:ymourn", "YOR:blouse",
                                                  "SHO:ssuit", "SHO:hood", "MIY:navy")
OB = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, keeps looking "
      "toward the other person at the same three-quarter angle, hands keep doing what they do in the first frame; no exaggerated motion, the same person throughout.")
HOLD = " Head stays at the same angle, never turns toward the camera; only body, hands and breath move. Mouth stays closed, lips still — this person is NOT speaking."
SEATED = " SEATED/FURNITURE LOCKED: seated on the zabuton or chair pulled in to the low table, legs under the table edge, forearms on the table; no furniture passes through the body."
ONEHAND = "HANDS LOCKED: exactly ONE hand and ONE object in frame, seen from the side, the arm continuing to the sleeve and shoulder at the frame edge (BODY CONTINUITY LOCKED). "

SHOTS = [
    # ① 후크 0:00~0:25 — 가짜 비디오레터는 H0a 한 번만 만들고 S04l·S05a·S09e에 같은 영상으로 재사용
    S("H0a", "H", "d", "cu", "screen", "EL", [Af], "ROOM_FIN_D", FIN + "Full-frame still of a home video letter: the elderly woman seated on a chair in the tatami room, "
      "facing the lens dead-centre, the window behind her showing the finished tower in daylight. Flat even lighting, slightly over-sharpened video look.", line="L01",
      act="She speaks slowly in an even monotone while staring straight into the lens without blinking even once; her face and shoulders stay perfectly still, the stiff polite smile never changes; "
          "only the lips move, slightly lagging the words.", expr="fake"),
    S("H0b", "H", "ins", "ecu", "night_lamp", "HA", [Ym], "ROOM_N", ONEHAND + "Insert from the side and slightly above: Yukiko's hand holding a plain black tablet in the dark tatami room at night, "
      "the screen glowing (the video letter will be composited onto the screen), the lamp light pooling on the tatami. " + WATCH_Y + ".", line="L02", vo=True,
      motion="The hand holds the tablet still; only the screen glow flickers softly on the fingers; nothing else moves."),
    S("H1", "H", "face", "cu", "night_lamp", "EL", [Ym], "ROOM_N", "Close-up at 45 degrees: Yukiko's face lit only by the cold glow of the tablet she is watching (screen off-frame below), "
      "the dark room behind, she has stopped breathing, eyes fixed on the screen.", line="NA0",
      motion="She holds her breath; her eyes move slightly across the screen; one slow blink; the cold screen light flickers faintly on her glasses." + HOLD, expr="g45"),
    S("H2a", "H", "reuse:S01e", "ots", "morning", "EL", [], None, "Reuse of S01e (the real mother smiling in the window chair, scaffolded tower behind) — 1.8 seconds, warm memory."),
    S("H2b", "H", "ins", "ecu", "night_lamp", "HA", [Ym], "ROOM_N", ONEHAND + "Insert from the side: Yukiko's hand slowly laying the glowing tablet screen-side down on the low wooden table, " + WATCH_Y + ".",
      line="NA1", motion="The hand slowly lowers the tablet screen-side down onto the table and stays resting on it; the glow is cut off underneath."),
    S("H3", "H", "card", "ws", "night_lamp", "EL", [], None, "Title card over the blurred last frame of H2b (no black)."),

    # ② 발단·갈등 — S01 간병의 날들(비계 있음, 엄마 손목에 시계)
    S("S01a", "S01", "face", "ews", "morning", "SIDE", [Yk, Sl], "RIVER", "Extreme wide from behind on the riverside embankment path in autumn: Yukiko slowly pushing her mother in a plain wheelchair, "
      "fallen leaves, the distant steel railway bridge; both seen only from behind, small in the frame.", motion="They move slowly away along the path; leaves drift; their backs stay to the camera.", expr="back"),
    S("S01b", "S01", "ins", "ecu", "morning", "HA", [Yk], "ROOM_D", ONEHAND + "Insert from the side: Yukiko's hand dropping small white pills one by one into a plain blank weekly pill case on a low table; "
      "her wrists are bare (no watch).", line="NA2", motion="The fingers drop pills one by one into the compartments and close a lid."),
    S("S01c", "S01", "face", "ms", "morning", "EL", [Yk], "KITCHEN", "Medium at three-quarter angle: Yukiko in the small old kitchen ladling simmered vegetables (nimono) from a pot into a small bowl, "
      "steam rising in the morning light, a quiet tired smile.", line="NA3", motion="She ladles slowly into the bowl, steam rises; small natural movements." + HOLD, expr="smile"),
    S("S01d", "S01", "face", "cu", "morning", "EL", [Yk], "ROOM_SCAF", SCAF + "Close-up: Yukiko kneeling at the low table, watching her mother eat the nimono, smiling softly, the bright window behind out of focus.",
      line="L03c", vo=True, motion="She watches with a soft smile and a small laugh of breath; one blink." + HOLD, expr="smile"),
    S("S01e", "S01", "d", "ots", "morning", "EL", [Sl, Yk], "ROOM_SCAF", SCAF + "Over Yukiko's blurred shoulder: the mother seated in the window-side armchair, a blanket over her knees, " + WATCH_M +
      ", looking up at her daughter, the scaffolded tower clearly visible through the window behind her.", line="L03",
      act="Looking up warmly at her daughter, she says thank you with deep crow's-feet wrinkles and a gentle smile, her hand resting on the blanket; breathes softly." + OB, expr="warm"),
    S("S01f", "S01", "face", "ms", "morning", "EL", [Yk], "ROOM_SCAF", SCAF + "Medium: Yukiko turning her gaze to the window where her mother is pointing, the scaffolded tower outside, the mother's thin hand pointing in the near foreground.",
      line="L03a", vo=True, motion="She looks out at the scaffolded tower and back, a small amused smile; the pointing hand stays still." + HOLD, expr="smile"),
    S("S01g", "S01", "d", "ots", "morning", "EL", [Yk, Sl], "ROOM_SCAF", SCAF + "Over the mother's blurred white-haired shoulder: Yukiko tucking the blanket around her mother's knees, answering her with a gentle smile.",
      line="L03b", act="Tucking the blanket in with both hands, she answers her mother gently with a small promise in her voice, a soft smile; glances at the window once." + OB, expr="smile"),
    S("S01h", "S01", "ins", "ecu", "morning", "EL", [Sl, Yk], "ROOM_SCAF", "Insert: the mother's thin wrinkled hand, " + WATCH_M + ", gently patting her daughter's hand on the blanket.",
      line="NA4", motion="The old hand pats the younger hand twice, slowly, and rests on it."),
    S("S01i", "S01", "ins", "ecu", "grey", "EL", [Yk], "ROOM_D", ONEHAND + "Insert on an overcast grey morning beside an empty care bed with a neatly folded white cover: Yukiko's hand fastening "
      "the small old brown-leather wristwatch onto her own LEFT wrist.", line="NA5", motion="Her fingers slowly fasten the worn leather strap buckle and then rest still."),
    S("S01j", "S01", "estill", "ws", "grey", "EL", [], "ROOM_SCAF", SCAF + "The empty window-side armchair with the folded blanket on the seat, the scaffolded tower outside, grey morning, no people.", line="NA5a"),

    # S02 통야(3200K, 반 그림자) — 영정 매치컷, 숙부 일가 로우
    S("S02a", "S02", "estill", "ws", "wake", "EL", [], "ALTAR", "The white-draped wake altar with chrysanthemums and incense smoke, the framed portrait at the centre in the same position as the empty armchair (match cut).", fx="matchcut"),
    S("S02b", "S02", "face", "ws", "wake", "LA", [Tm, Om, Hs], "LIV_W", "Low-angle medium-wide: the uncle, aunt and cousin seated at the low table with beer glasses after the wake, "
      "the uncle's eyes slowly scanning the old wooden pillars and ceiling of the house.", line="NA6", motion="The uncle looks up at the pillars appraisingly; the others drink; small natural movements." + HOLD, expr="smug"),
    S("S02c", "S02", "d", "ots", "wake", "LA", [Tm, Ym], "LIV_W", "Low angle over Yukiko's blurred mourning shoulder: the uncle pouring beer from a plain brown bottle into a glass, talking down to her.",
      line="L04", act="Pouring beer with a relaxed condescending manner, he tells Yukiko to leave the land to him, chin slightly raised; breathes between phrases." + OB, expr="smug"),
    S("S02d", "S02", "d", "ms", "wake", "EL", [Om], "LIV_W", "Medium: the aunt pushing a small plate of sushi across the low table with her fingertips, sneering at Yukiko off-screen.",
      line="L05", act="Pushing the plate aside, she sneers at Yukiko with a thin mocking half-smile, her voice light and cutting; never laughs out loud." + OB, expr="sneer"),
    S("S02e", "S02", "face", "cu", "wake", "HA", [Ym], "LIV_W", "High-angle close-up: Yukiko kneeling in her mourning dress, her hands clenched on her knees, swallowing the insult.",
      line="L06", vo=True, motion="Her hands tighten on her knees; she swallows; her eyes stay lowered." + HOLD + WET_HOLD, expr="hold"),
    S("S02f", "S02", "d", "cu", "wake", "EL", [Ym], "LIV_W", "Close-up: Yukiko lifting her eyes toward her relatives, restraining herself, eyes wet but not flowing.",
      line="L07", act=NOSMILE + "Quietly and firmly she asks them to stop in front of her mother, her voice held down, her hands still clenched; a tight breath before speaking." + OB + WET_HOLD, expr="hold"),
    S("S02g", "S02", "face", "ews", "wake", "HA", [Ym, Tm, Om, Hs], "LIV_W", "High extreme wide of the wake room: the relatives drinking and chatting at the table, Yukiko small and alone kneeling by the altar.",
      line="NA7", motion="The relatives drink and gesture; Yukiko stays still by the altar; incense smoke drifts." + HOLD),

    # S03 실인 실종 — 돌봄 카메라(흑백 어안은 마무리 효과)
    S("S03a", "S03", "face", "ws", "cctv", "HA", [Om], "HALL", "High-angle wide from a small ceiling care camera: the narrow wooden hallway at night, the aunt in her mourning dress stepping out of the mother's room, "
      "slipping a small black box into her black handbag, her face only half visible.", line="NA8", motion="She steps out, puts the small box into the handbag, glances down the hallway and walks away to the left." + HOLD),
    S("S03b", "S03", "estill", "ecu", "grey", "EL", [], "CHEST", "The open drawer of the old paulownia chest, the empty velvet spot where the seal case used to be, no people.", line="NA8a"),

    # S04 49재(요정 개인실, 탑 라이트) — 차용증·가짜 영상·모멸, 숙부 로우
    S("S04a", "S04", "ins", "ecu", "ryotei", "HA", [Tm], "RYO_T", ONEHAND + "Insert from the side: the uncle's plump hand laying three blank cream sheets of paper side by side on the lacquered table, one by one.",
      motion="The hand lays the sheets down one at a time and taps the last one flat."),
    S("S04b", "S04", "d", "ots", "ryotei", "LA", [Tm, Ym], "RYO_A", "Low angle over Yukiko's blurred mourning shoulder: the uncle at the head of the long table, leaning forward over the papers.",
      line="L08", act="Leaning forward with a grave, rehearsed face, he tells Yukiko not to be surprised and reveals the debt, one hand flat on the papers; slow deliberate delivery." + OB, expr="press"),
    S("S04c", "S04", "estill", "ecu", "ryotei", "OH", [], "RYO_T", "Overhead: three blank cream sheets of paper side by side on the dark lacquered table (amounts and red seals will be composited), no hands.", line="NA9"),
    S("S04d", "S04", "face", "cu", "ryotei", "HA", [Ym], "RYO_A", "High-angle close-up: Yukiko staring down at the papers, frozen, the colour leaving her face.",
      motion="She stares down, breath held, a small swallow." + HOLD, expr="stunned"),
    S("S04e", "S04", "estill", "ecu", "ryotei", "EL", [], "RYO_T", "Macro of the corner of one cream sheet where a red seal impression will be composited, shallow focus, no hands.", line="NA10"),
    S("S04f", "S04", "face", "cu", "ryotei", "EL", [Ym], "RYO_A", "Close-up at 45 degrees: Yukiko's eyes behind her silver glasses narrowing slightly at the papers — the eyes of a twenty-year bank loan officer.",
      line="NA10a", motion="Her eyes move along the papers and narrow slightly; a slow blink." + HOLD, expr="g45"),
    S("S04g", "S04", "d", "ots", "ryotei", "EL", [Ym, Tm], "RYO_A", "Over the uncle's blurred shoulder: Yukiko looking down at the papers, stiff with disbelief.",
      line="L09a", act=NOSMILE + "Looking from the papers to the uncle, in shock she asks in a stiff low voice whether her mother really had debts, then says she never heard of it; hands still on her lap." + OB, expr="stunned"),
    S("S04h", "S04", "d", "ms", "ryotei", "EL", [Tm], "RYO_A", "Medium: the uncle lowering his voice with a false gentle face, one hand open toward Yukiko off-screen.",
      line="L09b", act="Softening his voice into fake kindness, he says her mother did not want to worry her, a sad little head tilt, eyes not matching the smile." + OB, expr="falsekind"),
    S("S04i", "S04", "face", "cu", "ryotei", "EL", [Om], "RYO_A", "Close-up: the aunt watching Yukiko with a satisfied glance, sipping tea.",
      motion="She sips tea and watches over the cup rim; small satisfied blink." + HOLD, expr="smug"),
    S("S04j", "S04", "d", "ots", "ryotei", "LA", [Tm, Ym], "RYO_A", "Low angle over Yukiko's blurred shoulder: the uncle tapping the papers with his fingertip.",
      line="L09", act="Tapping the papers twice with a fingertip, jaw hard, he says the debts become hers if she inherits and orders her to renounce, chin raised, pressing." + OB, expr="press"),
    S("S04k", "S04", "d", "ms", "ryotei", "EL", [Hs, Ym], "RYO_A", "Over Yukiko's blurred shoulder: the cousin in a black suit holding out a plain black tablet toward her with a casual smirk.",
      line="L10", act="Holding out the tablet casually, he says he has a video his aunt left with him, a smug little smirk." + OB, expr="smirk"),
    S("S04l", "S04", "ins", "ecu", "ryotei", "EL", [Hs], "RYO_T", ONEHAND + "Insert: the cousin's hand holding the plain black tablet upright toward the camera across the table, the screen glowing (the video letter will be composited).",
      line="L11", vo=True, motion="The hand holds the tablet still; only a tiny natural hand drift."),
    S("S04m", "S04", "face", "cu", "ryotei", "EL", [Ym], "RYO_A", "Close-up: Yukiko staring at the tablet screen off-frame, her face lit faintly by it, unease rising.",
      line="L12", vo=True, motion="She stares, a tiny frown; one blink." + HOLD, expr="stunned"),
    S("S04n", "S04", "face", "ms", "ryotei", "EL", [Om], "RYO_A", "Medium: the aunt pressing a plain white handkerchief to her completely DRY eyes, a performance of grief, no tears at all.",
      line="NA11", motion="She dabs the handkerchief under her dry eyes twice and peeks over it; no tears appear." + HOLD, expr="dry"),
    S("S04o", "S04", "d", "cu", "ryotei", "HA", [Ym], "RYO_A", "High-angle close-up: Yukiko with her eyes lowered, hands on her lap.",
      line="L13", act=NOSMILE + "Eyes lowered, she asks in a small worn voice to let her think a little; a short breath before speaking." + OB + WET_HOLD, expr="hold"),
    S("S04p", "S04", "d", "ms", "ryotei", "EL", [Om, Ym], "RYO_A", "Over Yukiko's blurred shoulder: the aunt leaning back with a sneer.", fx="dutch5",
      line="L14", act="With a mocking sneer she repeats 'think?' and scoffs at the jobless daughter holding valuable land, a small flick of the hand; never laughs out loud." + OB, expr="sneer"),
    S("S04q", "S04", "d", "ms", "ryotei", "LA", [Tm], "RYO_A", "Low-angle medium: the uncle setting down his beer glass with leisurely confidence.",
      line="L15", act="Setting the glass down slowly, he states the deadline with false generosity, smug, satisfied and relaxed, a small lift of the hand on 'November'." + OB, expr="smug"),
    S("S04r", "S04", "face", "cu", "ryotei", "HA", [Ym], "RYO_A", "High-angle close-up: Yukiko nodding once, slowly, defeated, alone.",
      line="NA12", motion="She nods once slowly and keeps her eyes down." + HOLD + WET_HOLD, expr="hold"),
    S("S04s", "S04", "face", "ms", "night_lamp", "SIDE", [Ym], "ROOM_N", "Night, side view: Yukiko alone at the low table in her mother's dark room, the floor lamp on, turning the tablet back on, its cold glow on her face.",
      line="NA13", motion="She taps the tablet awake and leans in; the glow brightens on her face; she freezes." + HOLD),

    # ③ 전개·위기 — S05 비계(돌리줌 1회)
    S("S05a", "S05", "reuse:H0a", "ecu", "screen", "EL", [], None, "Reuse of H0a (the video letter) — slow push-in past the mother's shoulder to the window: the finished tower, no scaffolding.", fx="pushin", line="NA14"),
    S("S05b", "S05", "face", "cu", "night_lamp", "EL", [Ym], "ROOM_N", "Close-up: Yukiko frozen in front of the glowing tablet, realisation.", fx="dollyzoom",
      line="NA15", motion="Her breath stops; her eyes widen very slightly; nothing else moves." + HOLD, expr="stunned"),
    S("S05c", "S05", "estill", "ws", "night_lamp", "EL", [], "ROOM_FIN_N", FIN + "The real window of the mother's room at night: the finished tower outside with scattered lit apartment windows, the brown armchair, no people.", line="NA16"),
    S("S05d", "S05", "face", "ms", "night_lamp", "SIDE", [Ym], "ROOM_FIN_N", FIN + "Medium from behind at three-quarters: Yukiko standing at the window, looking out at the finished tower at night.",
      motion="She stands still looking out; her shoulders rise with one deep breath." + HOLD, expr="back"),
    S("S05e", "S05", "face", "cu", "night_lamp", "EL", [Ym], "ROOM_FIN_N", FIN + "Close-up at 45 degrees: Yukiko's face reflected faintly in the dark window glass, certainty settling in her eyes.",
      line="NA17", motion="Her eyes steady; a slow blink; the reflection trembles faintly." + HOLD, expr="g45"),
    S("S05f", "S05", "ins", "ecu", "night_lamp", "EL", [Ym], "ROOM_N", ONEHAND + "Insert: Yukiko's right hand closing over the old brown-leather wristwatch on her left wrist, trembling slightly.",
      line="L16", vo=True, motion="The hand closes slowly over the watch and trembles once."),
    S("S05g", "S05", "face", "ws", "night_lamp", "HA", [Ym], "ROOM_N", "High wide: Yukiko small and alone in the dark tatami room, the tablet glowing on the low table, the window beyond.",
      line="NA17a", motion="She sits very still; the tablet glow pulses softly." + HOLD),

    # S06 스무 해의 눈(거실 식탁, 5600K 분석광)
    S("S06a", "S06", "ins", "ecu", "analysis", "EL", [Yk], "LIV_C", ONEHAND + "Insert from the side: Yukiko's hand turning over one blank cream loan paper on the table, a magnifier-free practised movement. " + WATCH_Y + ".",
      line="NA18", motion="The hand turns the sheet over and smooths it flat."),
    S("S06b", "S06", "estill", "ecu", "analysis", "HA", [Yk], "LIV_C", ONEHAND + "Insert: Yukiko's index finger pointing at the empty top-right corner of the blank cream paper where a revenue stamp should be.", line="NA18b"),
    S("S06c", "S06", "face", "cu", "analysis", "EL", [Yk], "LIV_C", "Close-up at 45 degrees: Yukiko's eyes sharp behind her silver glasses, cool daylight, quiet certainty.",
      motion="Her eyes move once across the paper and settle; she breathes out slowly through her nose." + HOLD, expr="g45"),
    S("S06d", "S06", "face", "ms", "analysis", "EL", [Yk], "LIV_C", "Medium: Yukiko at the table with a small stack of plain household account notebooks and bankbooks with blank covers, turning pages.",
      line="NA18a", motion="She turns a page and runs a finger down a column; small natural movements." + HOLD + SEATED, expr="calm"),
    S("S06e", "S06", "ins", "ecu", "analysis", "EL", [Yk], "LIV_C", ONEHAND + "Insert from the side: Yukiko's hands typing on a plain silver laptop keyboard with blank keys, the screen a soft plain glow.",
      line="NA19", motion="The fingers type steadily and stop."),
    S("S06f", "S06", "estill", "ecu", "analysis", "EL", [], "LIV_C", "The plain silver laptop screen filling the frame (a credit report will be composited), no hands.", line="NA20"),
    S("S06g", "S06", "face", "ots", "analysis", "SIDE", [Yk], "LIV_C", "Over Yukiko's shoulder from behind: the laptop screen glowing in front of her (the second and third reports will be composited).",
      motion="She scrolls slowly; her head stays still facing the screen." + HOLD, expr="back"),
    S("S06h", "S06", "face", "cu", "analysis", "EL", [Yk], "LIV_C", "Close-up: Yukiko leaning back slightly, a cold quiet certainty in her eyes.",
      line="NA21", motion="She leans back a little and exhales; eyes steady." + HOLD, expr="resolve"),
    S("S06i", "S06", "estill", "ecu", "analysis", "EL", [], "LIV_C", "The plain laptop screen filling the frame (the black-and-white care-camera playback will be composited), no hands.", line="NA22"),
    S("S06j", "S06", "ins", "ecu", "analysis", "EL", [Yk], "LIV_C", ONEHAND + "Insert: Yukiko's finger tapping the laptop trackpad once to pause.",
      motion="The finger taps once and stays still."),
    S("S06k", "S06", "reuse:S03a", "ecu", "cctv", "HA", [], None, "Reuse of S03a paused — punch-in on the aunt's hand holding the small black seal case, grainy.", fx="punchin", line="NA23"),

    # S07 千葉県警 상담실 — 숏-리버스숏 180° 축 고정
    S("S07a", "S07", "face", "ws", "police", "EL", [Yk, Mn], "POL_A", "Wide of the small police consultation room: Yukiko and Detective Miyashita seated across the grey steel table, a plain brown envelope and a tablet on the table.",
      motion="They sit facing each other; Miyashita opens the envelope; small natural movements." + HOLD + SEATED),
    S("S07b", "S07", "d", "ots", "police", "EL", [Yk, Mn], "POL_O", "Over Miyashita's blurred shoulder: Yukiko sliding the tablet and the envelope across the table toward him.",
      line="L17", act="Sliding the tablet and the envelope across, she asks him politely and firmly to examine them, looking him in the eye." + OB, expr="resolve"),
    S("S07c", "S07", "d", "ots", "police", "EL", [Mn, Yk], "POL_O", "Over Yukiko's blurred shoulder (reverse angle): Miyashita stopping the video on the tablet and looking up at her.",
      line="L17a", act="Pausing the video, he looks up at her with quiet respect and says she investigated well; a small nod." + OB, expr="nod"),
    S("S07d", "S07", "d", "cu", "police", "EL", [Yk], "POL_O", "Close-up: Yukiko with her right hand resting over the old watch on her left wrist.",
      line="L17b", act="Holding the watch, eyes wet, she says simply that the way her mother called her was different, her voice trembling slightly but steady." + OB, expr="resolve"),
    S("S07e", "S07", "d", "ms", "police", "EL", [Mn], "POL_W", "Medium: Miyashita holding up one blank cream loan paper between two fingers.",
      line="L17c", act="Holding up the paper, he explains calmly: if real it is just debt, if fake it is evidence of a crime; measured, precise." + OB, expr="warn"),
    S("S07f", "S07", "face", "cu", "police", "EL", [Yk], "POL_O", "Close-up: Yukiko listening, absorbing every word.", motion="She listens, a small nod." + HOLD, expr="listen"),
    S("S07g", "S07", "d", "cu", "police", "EL", [Mn], "POL_W", "Close-up: Miyashita setting the paper down and speaking lower, from experience.",
      line="L17d", act="Setting the paper down, he says in a low knowing voice that people who force renunciation with fake debts usually have real debts; looks straight at her." + OB, expr="warn"),
    S("S07h", "S07", "ins", "ecu", "police", "EL", [Mn], "POL_T", ONEHAND + "Insert: Miyashita's hand turning the pages of a plain file on the steel table.",
      line="L18", vo=True, motion="The hand turns two pages and stops."),
    S("S07i", "S07", "d", "cu", "police", "EL", [Mn], "POL_W", "Close-up: Miyashita lifting his eyes and looking straight at Yukiko off-screen.",
      line="L19", act="Lifting his eyes, he asks in a quiet steady voice whether she can pretend to notice nothing until then; serious, unblinking." + OB, expr="warn"),
    S("S07j", "S07", "d", "ots", "police", "EL", [Yk, Mn], "POL_O", "Over Miyashita's blurred shoulder: Yukiko with the smallest smile.",
      line="L20", act="With a small quiet smile — her only smile in the story — she answers yes, she trained for twenty years at the counter." + OB, expr="smile"),
    S("S07k", "S07", "face", "ews", "dusk", "SIDE", [Yk], "HOUSE_E", "Extreme wide at dusk: Yukiko walking home toward the old two-storey house, seen from behind, small in the frame, a warm light in one window.",
      line="NA20a", motion="She walks slowly toward the house; her back stays to the camera." + HOLD, expr="back"),

    # S08 압박과 바닥(9월) — 숙부 로우 + 미세 핸드헬드(편집)
    S("S08a", "S08", "face", "ws", "sep_day", "SIDE", [Tg, Ob, Hh], "GENKAN", "Wide from inside the genkan: the uncle, aunt and cousin stepping in without arranging their shoes, seen from behind.",
      motion="They step up into the house, shoes left scattered; their backs stay to the camera." + HOLD, expr="back"),
    S("S08b", "S08", "d", "ms", "sep_day", "LA", [Tg], "LIV_W", "Low-angle medium: the uncle in a golf jacket patting a wooden pillar of the living room with his palm.", fx="handheld",
      line="L21", act="Patting the pillar hard, jaw set, he asks impatiently whether she still hasn't stamped it, chin raised." + OB, expr="press"),
    S("S08c", "S08", "face", "cu", "sep_day", "HA", [Yk], "LIV_W", "High-angle close-up: Yukiko standing with her hands folded, eyes lowered, enduring.",
      line="L21a", vo=True, motion="She keeps her eyes lowered; her folded hands tighten." + HOLD, expr="hold"),
    S("S08d", "S08", "d", "ots", "sep_day", "LA", [Tg, Yk], "LIV_W", "Low angle over Yukiko's blurred shoulder: the uncle leaning his face close to her, threatening in a low voice.", fx="handheld",
      line="L21b", act="Leaning in close, jaw tight, he says in a low threatening voice that the Hidamari people said they will come to collect, only the corners of his mouth smiling." + OB, expr="press"),
    S("S08e", "S08", "d", "ms", "sep_day", "EL", [Hh], "LIV_W", "Medium: the cousin in a grey hoodie filming the living room with his smartphone held up, appraising.",
      line="L22", act="Filming the room with his phone, he wonders aloud how much it would fetch as an empty lot, casual and smug." + OB, expr="smirk"),
    S("S08f", "S08", "d", "ms", "sep_day", "LA", [Ob], "LIV_W", "Low-angle medium: the aunt in a wine-red blouse adjusting the plain black handbag on her arm.", fx="handheld",
      line="L23", act="Adjusting her handbag, she says lightly she told the neighbours a jobless daughter is squatting here, a thin sneer." + OB, expr="sneer"),
    S("S08g", "S08", "face", "ms", "sep_day", "HA", [Yk], "LIV_W", "High-angle medium: Yukiko silently bowing her head to them.",
      line="NA24", motion="She bows her head slowly and holds it." + HOLD, expr="hold"),
    S("S08h", "S08", "ins", "ecu", "night_lamp", "EL", [Yk], "ROOM_N", ONEHAND + "Insert at night: Yukiko's hand holding a smartphone at chest height, the screen glowing (a chat thread with the same video thumbnails will be composited).",
      line="NA24a", motion=""),
    S("S08i", "S08", "ins", "ecu", "night_lamp", "SIDE", [Yk], "ROOM_N", ONEHAND + "Insert from the side at night: Yukiko's hand holding a ballpoint pen, its tip touching the name box of a blank cream form on the low table. " + WATCH_Y + ".",
      line="NA24b", motion="The pen tip trembles on the paper, then stops completely and lifts a few millimetres."),
    S("S08j", "S08", "face", "cu", "night_lamp", "EL", [Yk], "ROOM_N", "Close-up at night: Yukiko exhausted, the lamp light on half her face, eyes wet but not flowing.",
      line="NA24c", motion=NOSMILE + "A tired breath; her eyes glisten; one slow blink." + HOLD + WET_HOLD, expr="grief"),
    S("S08k", "S08", "pstill", "ots", "night_lamp", "SIDE", [Yk], "ALTAR", "From behind Yukiko's shoulder: her back and slightly trembling shoulder in the near foreground, the small altar with her mother's smiling portrait in focus beyond.",
      line="L24a", expr="back"),
    S("S08l", "S08", "face", "ws", "night_lamp", "EL", [Yk], "ROOM_N", "Wide at night: Yukiko sitting alone in the dark tatami room before the small altar, only the floor lamp.",
      motion="She sits motionless; only her breathing." + HOLD, expr="back"),
    S("S08m", "S08", "ins", "ecu", "night_lamp", "EL", [Yk], "ROOM_N", "Macro: the old wristwatch on Yukiko's left wrist, the thin second hand moving, the cream dial plain with no numbers.",
      line="NA25", motion="Only the second hand moves, tick by tick."),
    S("S08n", "S08", "face", "cu", "night_lamp", "EL", [Yk], "ROOM_N", "Close-up at 45 degrees: Yukiko lifting her eyes in the dark, resolve forming.",
      line="NA26", motion="Her eyes lift slowly; she breathes in." + HOLD, expr="g45"),
    S("S08o", "S08", "estill", "ecu", "night_lamp", "EL", [], "ROOM_N", "Macro of an open thick law book with blank pages on the low table, lamp light (the article text will be composited).", line="NA27"),
    S("S08p", "S08", "estill", "ecu", "night_lamp", "HA", [], "ROOM_N", "Macro of a small desk calendar with blank pages on the low table (the date October 3rd circled will be composited).", line="NA28"),
    S("S08q", "S08", "card", "ws", "night_lamp", "EL", [], None, "Preview card over the blurred calendar frame (no black)."),

    # ④ 절정 — S09 대면(3200K → 형광등 5600K)
    S("S09a", "S09", "ins", "ecu", "warm_liv", "HA", [Tg], "LIV_W", ONEHAND + "Insert: the uncle's plump hand placing a blank cream form and a ballpoint pen on the low table.",
      motion="The hand sets the form down and places the pen on it."),
    S("S09b", "S09", "d", "ots", "warm_liv", "LA", [Tg, Yk], "LIV_W", "Low angle over Yukiko's blurred shoulder: the uncle holding out the pen with a satisfied smile, warm lamp light.",
      line="L24", act="Holding out the pen, he praises her decision and points to where to stamp, smug and relaxed." + OB, expr="smug"),
    S("S09c", "S09", "d", "ots", "warm_liv", "EL", [Yk, Tg], "LIV_W", "Over the uncle's blurred shoulder: Yukiko holding the TV remote control, calm and composed.",
      line="L25", act="Holding up the remote, she says first she wants to see her mother's video once more; calm, deliberate." + OB, expr="resolve"),
    S("S09d", "S09", "ins", "ecu", "cold_liv", "LA", [Yk], "LIV_C", ONEHAND + "Insert from below: Yukiko's hand pulling the cord of the round ceiling light, the fluorescent tube flickering on.",
      motion="The hand pulls the cord once; the light flickers and comes on cold."),
    S("S09e", "S09", "estill", "ws", "cold_liv", "EL", [], "LIV_C", "The TV on its low cabinet in the cold-lit living room, the screen glowing (the video letter will be composited).", line="L26", vo=True),
    S("S09f", "S09", "d", "ots", "cold_liv", "LA", [Yk, Tg], "LIV_C", "Low angle over the uncle's blurred shoulder: Yukiko pointing at the TV with the remote, cold light.",
      line="L27", act="Pausing the video and pointing at the screen, she says the window has no scaffolding, clear and calm, each word placed." + OB, expr="resolve"),
    S("S09g", "S09", "face", "cu", "cold_liv", "HA", [Tg], "LIV_C", "High-angle close-up: the uncle's smile fading, the first tiny beads of sweat at his temples.",
      motion="His smile fades; he swallows; his eyes dart to the TV." + HOLD, expr="sweat"),
    S("S09h", "S09", "d", "ms", "cold_liv", "LA", [Yk], "LIV_C", "Low-angle medium: Yukiko standing straight in the cold light.",
      line="L30", act="She states that the scaffolding came off three weeks after her mother died, steady and quiet." + OB, expr="resolve"),
    S("S09i", "S09", "ins", "ecu", "cold_liv", "HA", [Yk], "LIV_C", ONEHAND + "Insert: Yukiko's hand placing printed blank report sheets on top of the blank loan papers on the low table.",
      line="L31", vo=True, motion="The hand lays the sheets down and squares them neatly."),
    S("S09j", "S09", "d", "ms", "cold_liv", "EL", [Ob], "LIV_C", "Medium: the aunt raising her voice, leaning forward from the sofa.",
      line="L32", act=NOSMILE + "Leaning forward, furious, she snaps at Yukiko, voice rising, asking what a jobless woman could know." + OB, expr="shout"),
    S("S09k", "S09", "d", "cu", "cold_liv", "LA", [Yk], "LIV_C", "Close-up: Yukiko pushing her glasses up with one finger, calm.",
      line="L33", act="Pushing her glasses up, she says calmly that until three years ago she was a loan officer at a credit union for twenty years." + OB, expr="resolve"),
    S("S09l", "S09", "d", "ms", "cold_liv", "EL", [Hh], "LIV_C", "Medium: the cousin half-risen from his chair, both hands on the table, flustered.",
      line="L34", act=NOSMILE + "Half rising, he blurts out in panic that it must be an AI error, voice cracking." + OB, expr="panic"),
    S("S09m", "S09", "d", "cu", "cold_liv", "EL", [Yk], "LIV_C", "Close-up: Yukiko slowly turning her face toward the cousin.", fx="punchin",
      line="L35", act="Slowly turning her face to the cousin, she repeats quietly that he just said 'AI'; very still." + OB, expr="resolve"),
    S("S09n", "S09", "face", "ms", "cold_liv", "EL", [Tg, Ob], "LIV_C", "Medium two-shot: the uncle and aunt turning their heads toward their son.",
      motion="They turn their heads slowly toward their son, frozen." + HOLD, expr="stunned"),
    S("S09o", "S09", "d", "ots", "cold_liv", "EL", [Yk, Hh], "LIV_C", "Over the cousin's blurred shoulder: Yukiko facing him.",
      line="L36", act="Facing him, she says she never said a word about AI; calm, final." + OB, expr="resolve"),
    S("S09p", "S09", "face", "cu", "cold_liv", "EL", [Hh], "LIV_C", "Close-up: the cousin's face turning pale, his hand losing its grip on the back of the chair.",
      motion="His face drains; his hand slips off the chair back; he swallows." + HOLD + SWEAT_FLOW, expr="pale"),
    S("S09q", "S09", "d", "cu", "cold_liv", "EL", [Yk], "LIV_C", "Close-up at 40 degrees: Yukiko looking toward her mother's portrait off-screen.",
      line="L37", act="Glancing toward her mother's portrait, she says her mother never called her Yukiko; soft but certain." + OB + WET_HOLD, expr="hold"),
    S("S09r", "S09", "d", "ms", "cold_liv", "EL", [Tg], "LIV_C", "Medium: the uncle leaning both hands on the low table, furious.", fx="dutch7",
      line="L38", act=NOSMILE + "Leaning on the table with both hands, he roars whether she doubts family, him, her mother's own brother; face flushed." + OB, expr="shout"),

    # S10 93일 — 숙부 하이 앵글로 역전
    S("S10a", "S10", "d", "ms", "cold_liv", "HA", [Tg], "LIV_C", "High-angle medium: the uncle's palm flat on the low table after striking it, breathing hard.",
      line="L39", act=NOSMILE + "Palm down hard on the table, he shouts that it's enough, just stamp it and it's over; breathing hard." + OB, expr="shout"),
    S("S10b", "S10", "d", "cu", "cold_liv", "LA", [Yk], "LIV_C", "Low-angle close-up: Yukiko unmoved.",
      line="L40", act="Unmoved, she says even if she stamped it, it would mean nothing." + OB, expr="resolve"),
    S("S10c", "S10", "ins", "ecu", "cold_liv", "EL", [Yk], "LIV_C", "Macro: Yukiko lifting her left wrist to glance at the old watch.",
      line="L41", vo=True, motion="The wrist turns up slowly; the second hand ticks."),
    S("S10d", "S10", "face", "cu", "cold_liv", "LA", [Yk], "LIV_C", "Close-up: Yukiko waiting for the answer, eyes on the uncle.",
      line="L42", vo=True, motion="She waits, eyes steady." + HOLD, expr="resolve"),
    S("S10e", "S10", "d", "ots", "cold_liv", "LA", [Yk, Tg], "LIV_C", "Over the uncle's blurred shoulder: Yukiko.",
      line="L43", act="She says it has been ninety-three days since her mother died, each number placed slowly." + OB, expr="resolve"),
    S("S10f", "S10", "face", "ms", "cold_liv", "EL", [Ob, Hh], "LIV_C", "Medium two-shot: the aunt and cousin exchanging an uneasy glance.",
      motion="They glance at each other uneasily; the aunt's hand tightens on her bag." + HOLD, expr="fear"),
    S("S10g", "S10", "d", "cu", "cold_liv", "LA", [Yk], "LIV_C", "Low-angle close-up: Yukiko explaining calmly.",
      line="L44", act="She explains calmly that the deadline to renounce is three months from the day one learns of the death." + OB, expr="resolve"),
    S("S10h", "S10", "face", "cu", "cold_liv", "HA", [Tg], "LIV_C", "High-angle close-up: the uncle's eyes widening as he understands.",
      motion="His eyes widen; his mouth opens slightly." + HOLD, expr="sweat"),
    S("S10i", "S10", "d", "ms", "cold_liv", "LA", [Yk], "LIV_C", "Low-angle medium: Yukiko.",
      line="L45", act="She adds that it does not count from the forty-ninth day; quiet, exact." + OB, expr="resolve"),
    S("S10j", "S10", "face", "ecu", "cold_liv", "HA", [Tg], "LIV_C", "Extreme close-up: the uncle's frozen face, a bead of sweat at his temple.",
      motion=SWEAT_FLOW + HOLD, expr="sweat"),
    S("S10k", "S10", "d", "cu", "cold_liv", "LA", [Yk], "LIV_C", "Low-angle close-up: Yukiko after a beat, the decisive line.", fx="slowpush",
      line="L46", act="After a beat, she says quietly and clearly that the deadline ended yesterday; no smile, absolute calm." + OB, expr="resolve"),
    S("S10l", "S10", "ins", "ecu", "cold_liv", "EL", [Yk], "LIV_C", "Macro: the old wristwatch on Yukiko's left wrist, the second hand ticking.", line="NA30", motion="Only the second hand moves."),
    S("S10m", "S10", "d", "ms", "cold_liv", "HA", [Tg], "LIV_C", "High-angle medium: the uncle sinking onto the sofa, trembling.",
      line="L47", act=NOSMILE + "Sinking down in shock, trembling, he mutters in horror about the house mortgaged for twenty-six million; eyes unfocused." + OB, expr="sweat"),
    S("S10n", "S10", "d", "ms", "cold_liv", "EL", [Ob, Tg], "LIV_C", "Over the uncle's blurred shoulder: the aunt gripping her husband's arm, shocked.",
      line="L48", act=NOSMILE + "Gripping his arm, she cries out asking what that means." + OB, expr="fear"),
    S("S10o", "S10", "ins", "ecu", "cold_liv", "EL", [Ob], "LIV_C", ONEHAND + "Insert: the aunt's hand gripping the sleeve of her husband's navy golf jacket.",
      line="NA31", motion="The hand keeps gripping the sleeve and pulls twice, never letting go."),

    # S11 응징 — 인터폰·경광등 반사·버즈아이
    S("S11a", "S11", "estill", "ecu", "police_red", "EL", [], "LIV_C", "The small intercom monitor on the wall glowing (the detective and two uniformed officers will be composited).", fx="intercom"),
    S("S11b", "S11", "d", "ms", "police_red", "LA", [Mn], "LIV_C", "Low-angle medium: Detective Miyashita stepping in from the hallway into the living room doorway.",
      line="L49", act="Standing in the doorway, he announces Chiba Prefectural Police and that the video was an AI fabrication; calm authority." + OB, expr="warn"),
    S("S11c", "S11", "face", "cu", "police_red", "EL", [Ob], "LIV_C", "Close-up: the aunt freezing, red and blue light sweeping across the window behind her.",
      motion="She freezes, lips trembling; the police light sweeps slowly." + HOLD, expr="fear"),
    S("S11d", "S11", "d", "cu", "police_red", "EL", [Mn], "LIV_C", "Close-up: Miyashita turning his eyes to the aunt.",
      line="L51", act="Turning to the aunt, he names her and says the footage from the night of the wake was checked too; level and cold." + OB, expr="warn"),
    S("S11e", "S11", "ins", "ecu", "police_red", "HA", [Ob], "LIV_C", ONEHAND + "Insert: the aunt's fingers clenching the plain black handbag on her knee.",
      line="L52", vo=True, motion="The fingers clench the handbag tighter and tremble."),
    S("S11f", "S11", "d", "cu", "police_red", "HA", [Tg], "LIV_C", "High-angle close-up: the uncle pleading for the first time.",
      line="L53", act=NOSMILE + "For the first time pleading, he says Yukiko's name and that they are family; voice breaking." + OB, expr="plead"),
    S("S11g", "S11", "d", "cu", "police_red", "LA", [Yk], "LIV_C", "Low-angle close-up: Yukiko answering quietly.",
      line="L54", act="Quietly she says the mother in the video told her to leave everything to her uncle." + OB, expr="resolve"),
    S("S11h", "S11", "face", "ms", "police_red", "HA", [Hh], "LIV_C", "High-angle medium: the cousin slumped, staring at the floor.",
      motion="He stares at the floor, motionless." + HOLD, expr="pale"),
    S("S11i", "S11", "d", "ms", "police_red", "LA", [Yk], "LIV_C", "Low-angle medium: Yukiko, the callback.",
      line="L55", act="Ending low, she says that is why she, too, left everything — to the police." + OB, expr="resolve"),
    S("S11j", "S11", "face", "ews", "police_red", "BE", [Tg, Ob, Hh], "LIV_C", "Bird's-eye view straight down: the uncle's family slumped on the sofa, small, the police light sweeping across the floor.",
      motion="They sit slumped, motionless; the red light sweeps slowly." + HOLD),

    # ⑤ 결말 — S12 그 후 · S13 진짜 목소리
    S("S12a", "S12", "face", "ews", "nov", "SIDE", [Yc], "STREET", "Extreme wide on a late-autumn morning: Yukiko in a camel coat walking along the street of yellow ginkgo leaves, seen from behind.",
      line="NA32", motion="She walks slowly away; ginkgo leaves drift." + HOLD, expr="back"),
    S("S12b", "S12", "estill", "ws", "nov", "EL", [], "HOUSE_D", "An old empty two-storey wooden house in the late-autumn morning, its curtains closed, nobody there.", line="NA33"),
    S("S13a", "S13", "ins", "ecu", "nov_room", "EL", [Yk], "ROOM_FIN_D", ONEHAND + "Insert: Yukiko's hand holding her mother's smartphone at chest height, about 35 cm away, the screen glowing (a chat screen with one voice message will be composited), her thumb tapping play.",
      line="NA34", motion="The thumb taps once and the hand stays still."),
    S("S13b", "S13", "face", "cu", "nov_room", "EL", [Yk], "ROOM_FIN_D", "Close-up at 45 degrees in morning light: Yukiko listening to her mother's voice, eyes welling.",
      line="L56", vo=True, motion=NOSMILE + "She listens without moving; her eyes fill; a trembling breath." + HOLD + WET_HOLD, expr="tear"),
    S("S13c", "S13", "ins", "ecu", "nov_room", "EL", [Yk], "ROOM_FIN_D", ONEHAND + "Insert: Yukiko's right hand closing gently over the old wristwatch on her left wrist.",
      line="L57", vo=True, motion="The hand closes over the watch slowly and holds it."),
    S("S13d", "S13", "face", "cu", "nov_room", "EL", [Yk], "ROOM_FIN_D", "Close-up at 30 degrees, morning window light from the left: Yukiko crying quietly in a restrained, real way.",
      motion=TEARS_FLOW + HOLD, expr="tear"),
    S("S13e", "S13", "pstill", "ws", "nov_room", "SIDE", [Yk], "ROOM_FIN_D", FIN + "From behind: Yukiko standing at the window in the morning light, her shoulders trembling slightly with a held breath, the finished tower outside, her face not visible.",
      line="L57a", expr="back"),
    S("S13f", "S13", "estill", "ecu", "nov_room", "EL", [], "ROOM_FIN_D", "Macro: the plain black tablet lying dark and switched off on the low table, morning light, no people.", line="NA35"),
    S("S13g", "S13", "face", "ms", "nov_room", "EL", [Yk], "ROOM_FIN_D", FIN + "Medium: Yukiko turning slightly from the window, a small wet smile, the morning light on her face.",
      line="NA36", motion="She turns a little and smiles softly through wet eyes; one slow blink." + HOLD + WET_HOLD, expr="tear"),
    S("S13h", "S13", "estill", "ews", "nov_room", "EL", [], "ROOM_FIN_D", FIN + "Wide of the mother's room in the morning light: the empty armchair by the window, the finished tower outside.", fx="pullback"),
]

# ── 생성 직전 보정(설계 검토에서 정한 컷 추가·고정) ──
def _ins_after(after_id, shot):
    i = next(k for k, s in enumerate(SHOTS) if s["id"] == after_id); SHOTS.insert(i + 1, shot)
_ins_after("S07k", S("S07l", "S07", "estill", "ws", "dusk", "EL", [], "HOUSE_E", "The old two-storey wooden house at dusk, warm light glowing in one ground-floor window, nobody outside."))
# 펜 끝 무언 2.5초(BGM 0)는 줄 없는 컷으로 NA24a 끝에 고정, NA24b는 다른 구도(위에서 펜 끝)로
for _s in SHOTS:
    if _s["id"] == "S08i":
        _s["line"] = None; _s["pin"] = 374.1
_ins_after("S08i", S("S08i2", "S08", "ins", "ecu", "night_lamp", "OH", [Yk], "ROOM_N", ONEHAND + "Top-down macro: the ballpoint pen tip resting on the name box of the blank cream form, the hand trembling slightly.",
                     line="NA24b", motion="The pen tip trembles on the paper, then stops and lifts away a few millimetres."))
_ins_after("S08p", S("S08p2", "S08", "face", "ms", "night_lamp", "EL", [Yk], "ROOM_N", "Medium at night: Yukiko rising from the low table, resolve set in her face, the calendar beside her.",
                     motion="She rises slowly to her feet and stands still, looking at the calendar." + HOLD, expr="resolve"))
for _s in SHOTS:
    if _s["id"] == "S08q": _s["pin"] = 418.4
    if _s["id"] == "S09d": _s["pin"] = 434.3
    if _s["id"] == "S09p": _s["pin"] = 486.1
    if _s["id"] == "S08h": _s["motion"] = "The hand holds the phone still; only a faint natural tremor; the screen glow stays constant."

SPK_WHO = {"由紀子": Yk, "母": Sl, "AI母": Af, "叔父": Tm, "叔母": Om, "翔太": Hs, "宮下": Mn}
SCENE_SPK_WARD = {sc: {"叔父": Tg, "叔母": Ob, "翔太": Hh, "由紀子": Yk} for sc in ("S08", "S09", "S10", "S11")}
SCENE_SPK_WARD.update({sc: {"由紀子": Ym} for sc in ("S02", "S04")})
VO_OTS_SKIP = {"S13b"}  # 어머니 목소리는 휴대폰 속 — 앞 어깨에 어머니를 두지 않는다
EMPTY_STILL = set()   # 무인 컷은 처음부터 estill로 설계(제19장 16)
# 일본어 글자 합성 면(서류·노트북·휴대폰·태블릿 화면)을 쥔 손 인서트는 정지 + 편집 카메라(제10장 3·제7장 2 — i2v는 화면·종이 글자를 뭉갠다)
INS_STILL = {"S06b", "S06a", "S06e", "S08h", "S08i", "S08i2", "S09a", "S09i", "S13a", "H0b", "S04l"}
MOTION_FIX = {}
for _s in SHOTS:
    if _s["id"] in EMPTY_STILL:
        _s["kind"] = "estill"
    if _s["id"] in INS_STILL:
        _s["motion"] = ""
    if _s["id"] in MOTION_FIX:
        _s["motion"] = MOTION_FIX[_s["id"]] + " " + _s["motion"]

CARDS = {"H2b": "この動画は、誰が作ったのか。", "H3": "母が遺したビデオレター", "S08q": "この後――母の動画が、もう一度流れる"}
JA_OVERLAY = {
    "H0a": "가짜 영상 효과(배럴 왜곡 2%·색수차 1px·입 12프레임 지연·눈 깜빡임 없음) + 창밖 = 완공 창 낮(aihaha-ref) 합성",
    "H0b": "태블릿 화면 = H0a 영상(lcd, 재생바 2:14)", "H2b": "중앙 카드(굵은 명조)", "H3": "타이틀(직전 컷 블러)",
    "S01a": "구석 소자막 「三年前」", "S02a": "구석 소자막 「七月三日　通夜」 + 영정 사진 = 佐和子 정면(점 1개)", "S03a": "흑백·어안·15fps·압축 노이즈 + 「07/03 23:41」",
    "S04a": "구석 소자막 「八月十九日　四十九日」", "S04c": "차용증 3장: 貸主 ひだまりファイナンス株式会社 / 借主 佐伯佐和子 / 金額 合計4,700万円 / 붉은 인영(실인) — 수입인지 칸 비어 있음",
    "S04e": "붉은 인영(佐伯) 확대", "S04l": "태블릿 화면 = H0a 영상(L11 구간)", "S05a": "H0a 정지 프레임 창 확대(완공 타워)",
    "S06a": "같은 차용증 뒷면 비침", "S06b": "차용증 오른쪽 위 수입인지 자리 빈칸(실글꼴 「収入印紙」 점선 테두리)", "S06e": "노트북 신용정보 개시 신청 화면(lcd)",
    "S06f": "개시 결과서 CIC 「該当なし」(lcd)", "S06g": "JICC·KSC 「該当なし」 차례로(lcd)", "S06i": "돌봄 카메라 앱 재생 화면(S03a, 「07/03 23:41」, 일시정지)",
    "S07a": "구석 소자막 「千葉県警」", "S08a": "구석 소자막 「九月」", "S08h": "LINE 대화: 翔太 → 같은 동영상 썸네일 날짜별(8/25·9/2·9/10…)",
    "S08i": "相続放棄申述書(실양식·申述人 칸 공란)", "S08i2": "같은 신술서 申述人 칸", "S08o": "民法第915条 「自己のために相続の開始があったことを知った時から三箇月以内」",
    "S08p": "탁상 달력 10月 · 3日 빨간 동그라미", "S08q": "예고 카드", "S09a": "相続放棄申述書(날짜 令和8年10月3日)", "S09e": "TV = H0a 영상(L26 구간)",
    "S09i": "개시 결과서 3장(該当なし)", "S11a": "인터폰 모니터: 宮下 + 제복 경찰 2명(본편 인물 합성·어안·주사선)", "S12a": "구석 소자막 「十一月」",
    "S13a": "어머니 휴대폰 LINE: 6/30 음성 메시지 1개(0:12) · 재생 버튼",
}
G = {
    "morning": "morning sparrows outside, a kettle faintly simmering, a quiet old house", "kitchen": "a pot simmering softly, a ladle touching a ceramic bowl",
    "river": "a gentle riverside wind, dry leaves rustling, a distant train crossing a steel bridge", "wake": "incense crackling softly, a wall clock ticking, glasses set on a table",
    "cctv": "analog security camera white noise hiss", "room_n": "a quiet room at night, an air conditioner hum, a wall clock ticking",
    "ryotei": "a quiet private dining room, an air conditioner hum, chopsticks on ceramic, distant cicadas outside", "living": "a wall clock ticking, an old refrigerator hum",
    "living_cold": "a fluorescent tube humming, a wall clock ticking", "police": "a fluorescent tube humming, papers rustling, an air conditioner",
    "dusk": "evening crickets, a distant train", "sep": "a distant car passing, a wall clock ticking", "night_sep": "autumn bell crickets outside, a wall clock ticking",
    "siren": "a distant police siren approaching, a quiet room", "street": "a late-autumn street, sparrows, ginkgo leaves skittering", "nov_room": "morning sparrows, a quiet room",
}
AMB_BY_SCENE = {"S01": "morning", "S02": "wake", "S03": "cctv", "S04": "ryotei", "S05": "room_n", "S06": "living", "S07": "police", "S08": "sep",
                "S09": "living", "S10": "living_cold", "S11": "siren", "S12": "street", "S13": "nov_room"}
AMB_BY_SHOT = {"S01a": "river", "S01c": "kitchen", "S03b": "room_n", "S04s": "room_n", "S07k": "dusk", "S07l": "dusk",
               "S08h": "night_sep", "S08i": "night_sep", "S08i2": "night_sep", "S08j": "night_sep", "S08k": "night_sep", "S08l": "night_sep", "S08m": "night_sep",
               "S08n": "night_sep", "S08o": "night_sep", "S08p": "night_sep", "S08p2": "night_sep", "S08q": "night_sep",
               "S09d": "living_cold", "S09e": "living_cold", "S09f": "living_cold", "S09g": "living_cold", "S09h": "living_cold", "S09i": "living_cold",
               "S09j": "living_cold", "S09k": "living_cold", "S09l": "living_cold", "S09m": "living_cold", "S09n": "living_cold", "S09o": "living_cold",
               "S09p": "living_cold", "S09q": "living_cold", "S09r": "living_cold", "H0a": "", "H0b": "", "H1": "", "H2a": "", "H2b": "", "H3": ""}
# 효과음 = PHASE 1 확정 20종(assets/sfx/aihaha/<id>.mp3, 09_효과음확정.md) — 컷 시작에 자동 믹스(일반 −18~−12, 정점 −9 dBFS)
FOLEY = {"H0a": "sfx:glitch", "H0b": "sfx:tablet_tap", "H3": "sfx:sub_hit", "S01i": "sfx:watch_tick", "S02b": "sfx:mokugyo", "S02c": "sfx:glass_clink",
         "S03a": "sfx:cctv_switch", "S03b": "sfx:drawer_slide", "S04a": "sfx:paper_drop", "S04b": "sfx:glass_clink", "S04i": "sfx:chopsticks", "S04l": "sfx:glitch",
         "S04s": "sfx:tablet_tap", "S05b": "sfx:sub_hit", "S06j": "sfx:cctv_switch", "S08h": "sfx:line_play_tap", "S08i": "sfx:watch_tick", "S08m": "sfx:watch_tick",
         "S08p": "sfx:page_flip", "S08q": "sfx:sub_hit", "S09a": "sfx:paper_drop", "S09d": "sfx:pull_cord", "S09e": "sfx:glitch", "S09m": "sfx:sub_hit",
         "S10a": "sfx:table_slam", "S10c": "sfx:watch_tick", "S10k": "sfx:sub_hit", "S11a": "sfx:intercom_chime", "S11b": "sfx:siren_far", "S11d": "sfx:radio_squelch",
         "S13a": "sfx:line_play_tap", "S13f": "sfx:screen_off", "S05a": "sfx:drone", "S09p": "sfx:heartbeat"}
BGM = [  # (시작, 끝, 볼륨, 프롬프트) — 07_연출설계 2절 8구간, 구간 간격 1.0초 이상. 0~3.5초 BGM 없음(드론·심장 박동만)
    (3.5, 24.0, 0.30, "dark sub-bass drone with a distant slow heartbeat, no melody, cinematic suspense, Japanese drama cold open, instrumental, no vocals"),
    (25.5, 72.0, 0.40, "gentle warm solo felt piano, nostalgic home, a daughter caring for her mother, Japanese human drama, instrumental, no vocals"),
    (75.5, 196.0, 0.36, "low dark strings, slow tension, sparse cello, an ominous family drama, greed at a funeral, Japanese drama score, instrumental, no vocals"),
    (205.0, 290.0, 0.36, "minimal mystery pulse, soft synth arpeggio at 90 bpm, quiet investigation, Japanese drama score, instrumental, no vocals"),
    (292.5, 371.0, 0.38, "rising low strings with a ticking clock texture, building dread and pressure, Japanese drama score, instrumental, no vocals"),
    (424.0, 520.0, 0.30, "very minimal tense drone with high string harmonics, a confrontation, Japanese drama score, instrumental, no vocals"),
    (557.0, 592.0, 0.45, "triumphant restrained orchestral reversal, rising strings and timpani, cathartic justice, Japanese drama score, instrumental, no vocals"),
    (626.0, None, 0.36, "tender solo piano, bittersweet, a mother's love remembered, a gentle morning, Japanese human drama finale, instrumental, no vocals"),
]
for _a, _b in zip(BGM, BGM[1:]):
    assert _b[0] - _a[1] >= 1.0, f"BGM 구간 간격 {_b[0] - _a[1]:.1f}s < 1.0s"
SILENCE = [("S08i", "S08i2", +4, "펜 끝이 떨림 — 손목시계 초침·숨만"),
           ("S08l", "S08n", +3, "혼자 남은 밤 — 손목시계 초침만(원안: 시계 초침 + 심장 박동)"),
           ("S09n", "S09p", +3, "「AI」 실언 뒤 정적 — 룸톤·심장 박동만"),
           ("S10j", "S10l", +4, "결정타 앞 한 박자 — 벽시계 초침만, 「期限は」에서 저음 임팩트"),
           ("S11a", "S11b", +3, "인터폰 단음 → 역전 테마"),
           ("S13b", "S13f", +2, "어머니 음성·3초 정적 — 방 공기음만, 피아노는 NA35부터")]
FOLEY_TENSION = {"S08i": "a wristwatch second hand ticking loudly in a silent room, a shaky breath", "S09p": "a slow heavy heartbeat thump twice in silence",
                 "S10j": "a wall clock second hand ticking in a silent room", "S10k": "a deep low cinematic impact"}
FOLEY.update({k: v for k, v in FOLEY_TENSION.items() if k not in FOLEY})

STYLE = {"NA": "Naration", "由紀子": "Yukiko", "母": "Sawako", "AI母": "AIHaha", "叔父": "Tsuyoshi", "叔母": "Yoriko", "翔太": "Shota", "宮下": "Miyashita"}
STYLE_JA = {"Naration": "由紀子（語り）", "Yukiko": "由紀子", "Sawako": "佐和子", "AIHaha": "動画の母", "Tsuyoshi": "剛", "Yoriko": "頼子", "Shota": "翔太", "Miyashita": "宮下"}
STYLE_COLOR = {"Naration": "&H00DDDDDD", "Yukiko": "&H00FFFFFF", "Sawako": "&H00F0D8E6", "AIHaha": "&H00E6E6C8", "Tsuyoshi": "&H00B4D2FF",
               "Yoriko": "&H00C8C8F0", "Shota": "&H00C8E6F0", "Miyashita": "&H00E6DCC8"}
RATE = {"lite": 0.036, "omni": 0.16, "kf": 0.04}
HOOK_LEN = {"H0a": 4.0, "H0b": 5.2, "H1": 5.0, "H2a": 1.8, "H2b": 6.5, "H3": 2.491}
BANNED_MOTION = (("slam", "큰 동작"), ("spin", "회전"), ("tracking camera", "편집 전용 무빙"), ("dolly", "편집 전용 무빙"), ("zoom", "편집 전용 무빙"),
                 ("crane", "편집 전용 무빙"), ("dialogue", "오디오 지시"), ("says", "오디오 지시"), ("sound of", "오디오 지시"))


def emo_class(tag_text):
    t = tag_text.lower()
    for cls, keys in (("angry", ("angry", "furious", "shout", "irritated", "threatening", "pressuring", "snap", "roar")),
                      ("toneup", ("panic", "fluster", "shock", "stunned", "alarm")),
                      ("sad", ("sad", "weary", "apolog", "tired", "plead", "trembl", "whisper", "hushed", "broken", "uneasy")),
                      ("happy", ("warm", "smil", "playful", "loving", "chatty", "cheer", "smug", "mock", "sneer", "teas", "delight", "tender")),
                      ("tonedown", ("calm", "quiet", "firm", "cold", "low", "decisive", "certain", "knowing", "flat", "crisp", "sharp", "steady", "reflective"))):
        if any(k in t for k in keys):
            return cls
    return "normal"


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
    used = [s["line"] for s in SHOTS if s["line"] and s["scene"] != "H"]  # 후크 줄은 lock 고정 시각(HOOK_LEN)
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
        if still and d > STILL_LONG_OK.get(s["id"], STILL_MAX):
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
                if (key, ward) in WARD_REF and j == 0:  # 의상 변형 참조(상복·코트·골프 점퍼·블라우스·후드)
                    refs.append(WARD_REF[(key, ward)])
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
    ass = ["[Script Info]", "Title: 母が遺したビデオレター 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
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
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_aihaha_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT, "preset": PRESET,
               "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"], "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_aihaha_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, wardrobe, "
                         "props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_aihaha_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (ElevenLabs 확정본 · B안 템포 적용).",
        "default_voice": "cached-typecast", "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Naration"], "silent_styles": ["Caption", "HookLine", "Title"] + [n + "_c" for n in STYLE_COLOR],
        "output_size": [1920, 1080], "fit": "crop", "scene_durations": durations, "transitions": [0.0] * len(durations),
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d" and (s["line"] or s["replay"])],
        "omnihuman_prompts": {str(idx[k]): v for k, v in omni_prompts.items()},
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0, "legacy_lipsync": False,
        "foley_prompts": {str(idx[k]): v for k, v in foley.items()},
        "bgm_silence": [{"start": round(starts[a], 2), "end": round(starts[b], 2), "sfx_boost_db": g, "why": w} for a, b, g, w in SILENCE],
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35, "duck_db": 8, "ambience_prompts": [x["ambience"] for x in sb],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": s, "end": round(main_end, 2) if e is None else e, "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_후크": "0~3.5초 BGM 없음: 저음 드론 + 심장 박동(PHASE 6 로컬). H0a = 가짜 비디오레터 립싱크(L01, 가짜 영상 효과), H0b = 태블릿 화면 합성(L02), H1 = 由紀子 옆얼굴(NA0), H2a = 진짜 어머니 회상 1.8초(S01e 재사용), H2b = 태블릿 내려놓기(NA1 + 중앙 카드), H3 타이틀(직전 컷 블러, 암전 없음).",
        "_공간음": "요정 개인실(S04)·경찰 상담실(S07)은 작은 방 잔향, 어머니 LINE 음성(S13 L56·L57)은 휴대폰 스피커 대역 제한 + 방 공기음, 가짜 영상(AI母)은 무잔향 건조 — PHASE 6 로컬.",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    md = ["# 『母が遺したビデオレター』 PHASE 3 샷 리스트 (B안 표준)", "",
          f"> `scripts/build_aihaha_phase3.py` 자동 생성(손 수정 금지). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " + ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock['ads']) + ".",
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
        tagtxt, inten, tempo, memo = TONE[tag]; emo = emo_class(tagtxt)
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
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_aihaha_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않거나 부딪힘(연기 메모에 의도가 없으면 키프레임·동작 문장을 고친다). 감정 격차(9절)는 샷 표의 장면 순서로 확인.", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 감정·세기·템포 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")


if __name__ == "__main__":
    main()
