#!/usr/bin/env python3
"""『みすぼらしい老人は、財閥会長だった』(beggar-chairman-ja) PHASE 3 샷 리스트 Lock 생성기 — build_tsuki_phase3.py를 옮긴 것.

이 작품에서 달라진 것:
  · 권력 역전 앵글(02_카메라앵글설계.md 1절): 전반 岩城·間宮 LA / 源蔵 HA → S11 源蔵 첫 EL → S13~ 源蔵 LA / 岩城 HA → S14 土下座 BE
  · 흐르는 눈물·땀은 i2v로(제18장 1): 립싱크 컷은 「젖었지만 흐르지 않음」(WET_HOLD), 흐름은 앞뒤 리액션 i2v(TEARS_FLOW·SWEAT_FLOW)
  · 화면 카드(후크·중반 예고·다음 이야기·타이틀)는 클립에 직접 그리고 .ass Caption을 만들지 않는다(제15장 12)
  · 후크 줄(L01·L02·NA0)과 S10 콜드오픈 합류의 L01 재생(lock.json replay)도 음성 캐시에 넣는다
입력: productions/beggar-chairman-ja/lock.json · 00_script_ja.md · assets/auditions/beggar-tts/lineNNN.mp3 · assets/portraits/beggar-cast/cells/
출력: scripts/storyboard/beggar-chairman.json · scripts/scenes/beggar-chairman.json · scripts/audio/beggar-chairman.json · subs/beggar-chairman.ass ·
      assets/audio-overrides/beggar-chairman/lineNNN.mp3 · productions/beggar-chairman-ja/07_샷리스트.md · 16_감정일치표.md
사용법: python3 scripts/build_beggar_phase3.py
"""
import collections, json, os, re, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "beggar-chairman-ja")
SKIT = "beggar-chairman"
TTS_DIR = "beggar-tts"
FPS = 24; HARD = 1 / FPS; OMNI_MAX = 7.9; LEAD = 0.3; MIN_SHOT = 1.2; STILL_MAX = 6.5; I2V_MAX = 10.0

C = "assets/portraits/beggar-cast/cells/"
WHO = {
    "GEN": ("Takamiya Genzo, a lean Japanese man aged 78, angular weathered face with deep wrinkles, close-cropped white hair, a short neat white beard, "
            "one small dark mole above his LEFT eyebrow, no glasses, no earrings", C + "genzo-front.png"),
    "IWA": ("Iwaki, a Japanese man aged 45, slim oval face, black hair slicked back with pomade, a thin neat black moustache, no glasses, "
            "small black stud earrings in both ears (fixed trait from the approved sheet)", C + "iwaki-front.png"),
    "MAM": ("Mamiya, a stocky Japanese man aged 32, round face, reddish-brown hair cut short on the sides and longer on top, small silver stud earrings "
            "in both ears (fixed trait), no glasses", C + "mamiya-front.png"),
    "CHI": ("Harukawa Chihiro, a slim Japanese woman aged 21, oval face, straight blunt bangs, black hair in a low ponytail, no glasses, "
            "tiny black stud earrings (fixed trait from the approved sheet)", C + "chihiro-front.png"),
    "SKK": ("Sakaki, a Japanese man aged 64, neatly combed-back silver-white hair, a short grey moustache, thin SILVER-rimmed glasses, upright posture",
            C + "sakaki-front.png"),
    "BOY": ("a thin Japanese boy aged 8 in winter 1955, close-shaved head, chapped red cheeks (the chairman as a child)", C + "boy-front.png"),
    "OKA": ("an udon shop mistress of 1955 seen only as a warm backlit silhouette or her hands, face never visible", None),
    "GUARD": ("two hotel security guards in plain dark suits seen only from behind", None),
    "REG": ("a well-dressed regular customer seen only from behind", None),
}
WARD = {
    "GEN": "a plain faded grey zip-up jacket with frayed cuffs and no logo, plain worn beige cotton trousers, old scuffed white sneakers, an old wristwatch with a cracked leather strap",
    "IWA": "a black three-piece suit, white shirt, silver tie, a small blank brushed-metal name plate with no engraving",
    "MAM": "a plain cream knit sweater with no logo, a plain beige double-breasted overcoat, dark slacks, a thick silver wristwatch",
    "CHI": "a plain white long-sleeve blouse, a plain navy waist apron with no print, black slacks",
    "SKK": "a black three-piece suit, white shirt, dark grey tie, no pin or badge",
    "BOY": "a patched oversized dark wool jacket, thin worn trousers, straw sandals",
}
EXPR = {  # PHASE 2 Kill Gate 합격 셀 — 표정 50% 선반영
    ("GEN", "calm"): C + "genzo-expr1.png", ("GEN", "smile"): C + "genzo-expr2.png", ("GEN", "stern"): C + "genzo-expr3.png",
    ("GEN", "back"): C + "genzo-fullback.png", ("GEN", "full"): C + "genzo-full.png",
    ("IWA", "cold"): C + "iwaki-expr1.png", ("IWA", "fawn"): C + "iwaki-expr2.png", ("IWA", "sneer"): C + "iwaki-expr3.png", ("IWA", "full"): C + "iwaki-full.png",
    ("MAM", "arrogant"): C + "mamiya-expr1.png", ("MAM", "mock"): C + "mamiya-expr2.png", ("MAM", "panic"): C + "mamiya-expr3.png",
    ("CHI", "kind"): C + "chihiro-expr1.png", ("CHI", "smile"): C + "chihiro-expr2.png", ("CHI", "tears"): C + "chihiro-expr3.png", ("CHI", "full"): C + "chihiro-full.png",
    ("SKK", "calm"): C + "sakaki-expr1.png", ("SKK", "bow"): C + "sakaki-expr2.png", ("SKK", "back"): C + "sakaki-fullback.png",
    ("BOY", "hungry"): C + "boy-expr1.png", ("BOY", "grateful"): C + "boy-expr2.png", ("BOY", "tears"): C + "boy-expr3.png", ("BOY", "back"): C + "boy-fullback.png",
}
LOC = {
    "STEPS": C + "loc-hotel-afternoon-steps.png", "DRIVE": C + "loc-hotel-dusk-drive.png", "FRONT_N": C + "loc-hotel-night-front.png", "LOBBY": C + "loc-hotel-lobby.png",
    "HALL": C + "loc-hall-wide.png", "WIN": C + "loc-hall-window.png", "CORNER": C + "loc-hall-corner.png", "TABLE": C + "loc-hall-tablelevel.png",
    "REV": C + "loc-hall-angles-reverse.png", "BIRD": C + "loc-hall-angles-birdseye.png", "LOWF": C + "loc-hall-angles-lowfloor.png", "PILLAR": C + "loc-hall-angles-pillar.png",
    "ENT": C + "loc-entrance-front.png", "ENT_LOW": C + "loc-entrance-low-podium.png", "ENT_OVER": C + "loc-entrance-over-podium.png", "BOOK": C + "loc-entrance-book.png",
    "POT": C + "loc-kitchen-car-kitchen-pot.png", "PASS": C + "loc-kitchen-car-kitchen-pass.png", "CAR_D": C + "loc-kitchen-car-car-day.png", "CAR_N": C + "loc-kitchen-car-car-night.png",
    "U_EXT": C + "loc-udonya-1955-exterior.png", "U_CNT": C + "loc-udonya-1955-counter.png", "U_DOOR": C + "loc-udonya-1955-doorway.png", "U_BOWL": C + "loc-udonya-1955-bowl.png",
}
PRESET = ("Photorealistic live-action Japanese human drama, contemporary Tokyo, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, "
          "restrained Japanese film mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, "
            "signage lettering, menus with writing, documents with writing, screens with text, printed labels, brand logos, watermarks, stamps, "
            "symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, blood, gore, police, anime, 3d render, "
            "thick glossy gel tears, cartoon sweat drops, multiple tear streams on both cheeks")
PLAIN = "All papers, menus, screens, signs, cards and labels are completely blank; no letters, numbers or symbols anywhere in the frame."
# 제18장 1 — 실사 눈물·땀. 키프레임은 맺힘/젖음까지, 흐름은 i2v 동작 문장으로
TEARS = ("Realistic tears as in a live-action film: reddened eye rims, glossy wet eyes catching the light, a small clear tear bead on the lower lashes, "
         "at most one thin translucent tear track on one cheek, a slightly reddened nose tip, matte natural skin; no glossy gel streams, no cartoon droplets.")
SWEAT = ("Realistic sweat as in a live-action film: fine tiny beads of perspiration on the forehead, temples and upper lip, a faint natural oily sheen, "
         "one thin bead line near the temple, a few damp strands at the hairline; no large cartoon drops, no face-wide shine.")
WET_HOLD = " Eyes wet and glistening with tears welling on the lower lids but NOT running down — the tears stay pooled."
TEARS_FLOW = (" One clear tear slowly spills over the lower lid and runs down the cheek along its natural curve, catching the light; a slow blink, "
              "a trembling breath; only one tear line, thin and translucent.")
SWEAT_FLOW = " A thin bead of cold sweat slowly runs from the temple down toward the jaw; a shaky breath, a hard swallow."
GLASSES = {"SKK": "He wears his thin silver-rimmed glasses.", "GEN": "He wears no glasses.", "IWA": "He wears no glasses.",
           "MAM": "He wears no glasses.", "CHI": "She wears no glasses.", "BOY": "He wears no glasses."}
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, the face fills at least half of the frame height",
    "ots": "50mm lens, f/2.0, over-the-shoulder three-quarter framing, the listener's blurred shoulder and back of the head in the near foreground edge, the speaker's face at least one third of the frame height",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds, the person's face at least one quarter of the frame height",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective",
}
LIGHT = {
    "steps": "clear afternoon daylight 5600K on glass and granite, crisp shadows", "dusk": "golden hour 3200K, long warm shadows, glowing glass",
    "night": "night, warm entrance lights and cool city glow, faces readable", "lobby": "warm 3200K lobby downlights reflecting on marble",
    "hall": "warm 3200K amber pendant lamps, a cool 5600K window light from the left, dark wood walls, soft contrast",
    "corner": "the dim cramped corner by the restroom corridor: cold flat fluorescent spill from the corridor, the warm pendants far away, a lonely mood, faces readable",
    "ent": "warm 3200K entrance spotlights from above, hard shadows on the podium",
    "tension": "cold overhead light falling vertically, harsh shadows under the brows, the warm pendants dimmed, high contrast",
    "reveal": "a strong warm backlight rim from the tall window behind, the old man's silhouette edged with light, faces still readable, dramatic",
    "kitchen": "warm steamy kitchen light 3200K, steam glowing", "car": "afternoon daylight through tinted windows, cool and quiet",
    "car_n": "night, Tokyo city lights streaking across the window, warm interior glow, average brightness readable on a phone",
    "sepia": "winter night 1955, warm 2700K bare bulb glow from inside, cold blue snow light outside, sepia period tone, film grain",
    "product": "soft even studio light, neutral",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}
SPK_KEY = {"源蔵": "GEN", "岩城": "IWA", "間宮": "MAM", "ちひろ": "CHI", "榊": "SKK"}


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, act="", vo=False):
    """kind: d(OmniHuman 어깨 너머 3/4 립싱크) / face(사람 i2v) / empty(무인 i2v) / estill(무인·합성 면 정지) /
    ins(손·소품 — motion 있으면 i2v, 없으면 정지) / reuse:<id> / card.  vo=True = 화자 화면 밖(듣는 사람 리액션 위 목소리)."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc, subject=subject,
                line=line, fx=fx, motion=motion, expr=expr, act=act, vo=vo)


G_, I_, M_, C_, K_, B_ = "GEN:GEN", "IWA:IWA", "MAM:MAM", "CHI:CHI", "SKK:SKK", "BOY:BOY"
OB = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, keeps looking "
      "toward the other person at the same three-quarter angle, hands keep doing what they do in the first frame; no exaggerated motion, the same person throughout.")
HOLD = " Head stays at the same angle, never turns toward the camera; only body, hands and breath move. Mouth stays closed, lips still — this person is NOT speaking."

SHOTS = [
    # ① 후크 0:00~0:20 — H0·H1은 S10 재사용(추가 생성 0)
    S("H0", "H", "reuse:S10r", "ms", "tension", "LA", [], None, "Reuse of S10r (Iwaki yanking the old man's frayed sleeve, dutch 5 degrees). L01 audio."),
    S("H1", "H", "reuse:S10m", "ms", "hall", "LA", [], None, "Reuse of S10m (Mamiya filming with his phone, grinning). L02 audio."),
    S("H2", "H", "face", "cu", "corner", "EL", [G_], "CORNER", "Close-up of Genzo sitting alone at the dim corner table, looking up calmly without anger, dignified, quiet eyes.",
      motion="He looks up calmly, one slow blink, a quiet breath; no other movement." + HOLD, expr="calm"),
    S("H3", "H", "empty", "ews", "dusk", "LA", [], "STEPS", "Low wide of the glass hotel tower at golden hour, empty granite steps, no signage. Title composited.",
      motion="Clouds drift slowly, the glass glints; nothing else moves."),

    # ② 발단·갈등
    S("S01a", "S01", "ins", "ecu", "steps", "LA", [G_], "STEPS", "Insert: a pair of old scuffed white sneakers stopping on the bottom granite step, worn beige trouser hems, no face.",
      motion="The sneakers settle on the step, a small shift of weight; nothing else moves.", line="NA1"),
    S("S01b", "S01", "face", "ws", "steps", "LA", [G_], "STEPS", "Wide low angle from behind: the old man in the faded grey jacket looking up at the towering glass hotel, small against it.",
      motion="He stands still looking up, his jacket stirs in the breeze, a slow breath; he does not turn." + HOLD, line="NA2", expr="back"),
    S("S02o", "S02", "empty", "ews", "sepia", "HA", [], "U_EXT", "Sepia high wide: a narrow snowy post-war Tokyo alley at night, one warm window of a tiny udon shop glowing, snow falling.",
      motion="Snow falls steadily, the warm window glows; nothing else moves."),
    S("S02a", "S02", "face", "ws", "sepia", "EL", [B_], "U_EXT", "Sepia winter night 1955: a thin boy shivering under the snowy eaves of a tiny wooden udon shop, hugging himself, snow falling.",
      motion="Snow falls, the boy shivers and rubs his arms, breath fogging; he stays under the eaves." + HOLD, line="NA3", expr="hungry"),
    S("S02b", "S02", "face", "ms", "sepia", "EL", [], "U_DOOR", "Sepia: in the warm doorway behind rising steam, the shop mistress as a backlit silhouette beckoning with her hand, face not visible.",
      motion="Steam rises, the silhouette's hand beckons slowly twice; the face stays in shadow.", line="NA4"),
    S("S02c", "S02", "ins", "ecu", "sepia", "EL", [], "U_BOWL", "Sepia insert: small cold hands receiving a steaming bowl of plain kake udon from a woman's hands over the wooden counter.",
      motion="The bowl passes from the woman's hands into the small hands, steam curling; a gentle tremble."),
    S("S02d", "S02", "face", "cu", "sepia", "EL", [B_], "U_CNT", "Sepia close-up of the boy holding the bowl to his chest, eyes filling with tears, steam on his face.",
      motion="He holds the bowl close, steam rising." + TEARS_FLOW + HOLD, line="NA5", expr="tears"),
    S("S03a", "S03", "ins", "ecu", "dusk", "EL", [G_], "STEPS", "Insert: an old wrinkled hand slowly brushing over the smooth polished granite of the hotel wall, golden light.",
      motion="The hand slides slowly across the stone, fingers spreading; golden light shifts.", line="NA6"),
    S("S03b", "S03", "face", "cu", "dusk", "SIDE", [G_], "STEPS", "Close-up profile of Genzo gazing at the wall with longing, a warm golden-hour rim light on his white beard.",
      motion="He gazes at the wall, a slow blink, a long breath; head still." + HOLD, line="NA7", expr="calm"),
    S("S04a", "S04", "empty", "ws", "ent", "EL", [], "ENT", "Wide of the restaurant entrance: plain indigo noren, a wooden reception podium with a closed blank book, stone floor.",
      motion="The noren sways gently; nothing else moves."),
    S("S04b", "S04", "face", "ms", "ent", "LA", [I_], "ENT_LOW", "Low angle medium: Iwaki behind the podium at three-quarter angle, turned toward the doorway on the left, looking the arriving old man up and down with cold contempt.",
      motion="His eyes travel down and up slowly, a faint sneer; hands rest on the podium." + HOLD, expr="cold"),
    S("S04c", "S04", "d", "ots", "ent", "LA", [I_, G_], "ENT_LOW", "Over Genzo's blurred shoulder (left foreground), low angle: Iwaki stepping into the doorway at three-quarter angle, arm stretched across the entrance with the palm raised, blocking the old man.", line="L03",
      act="Iwaki blocks the old man at the door, arm stretched out with the palm raised, keeping the arm up while he speaks, telling him dismissively that he cannot come in here, eyes looking him up and down. Answering the old man who has just stepped in." + OB, expr="cold"),
    S("S04d", "S04", "d", "ots", "ent", "HA", [G_, I_], "ENT_OVER", "Over Iwaki's blurred shoulder (right foreground), high angle: Genzo at three-quarter angle, hands folded in front, calm and polite.", line="L04",
      act="Genzo answers gently and politely, hands folded in front of him, looking up at Iwaki, asking for a simple bowl of kake udon." + OB, expr="calm"),
    S("S04e", "S04", "d", "ots", "ent", "LA", [I_, G_], "ENT_LOW", "Over Genzo's blurred shoulder, low angle: Iwaki scoffing, eyebrows raised, one hand on the podium.", line="L05",
      act="Iwaki scoffs mockingly, eyebrows raised, tapping the podium, telling him the cheapest course is thirty thousand yen." + OB, expr="sneer"),
    S("S04f", "S04", "face", "cu", "ent", "LA", [I_], "ENT_LOW", "Low close-up of Iwaki at three-quarter angle facing screen left toward the old man, hearing him say he has money, a contemptuous half-smile.", line="L06", vo=True,
      motion="A contemptuous half-smile spreads slowly, one eyebrow lifts; lips stay closed." + HOLD, expr="sneer"),
    S("S04g", "S04", "d", "ots", "ent", "HA", [G_, I_], "ENT_OVER", "Over Iwaki's blurred shoulder: Genzo looking past him into the restaurant with longing.", line="L06a",
      act="Genzo asks quietly, looking past Iwaki into the restaurant with longing, about the old shop that stood here." + OB, expr="calm"),
    S("S04h", "S04", "ins", "ecu", "ent", "EL", [I_], "BOOK", "Insert: a hand in a black suit sleeve slapping the blank leather reservation book shut, no face.",
      motion="The hand slaps the book shut and presses it flat; a small bounce.", line="L06b", vo=True),
    S("S04i", "S04", "d", "ms", "ent", "LA", [I_, G_], "ENT", "Low medium: Iwaki sighing and jerking his chin toward the back of the hall, the old man's blurred shoulder at the edge.", line="L07",
      act="Iwaki sighs with dismissive irritation and jerks his chin toward the back corner, directing the old man to the seat by the restroom." + OB, expr="cold"),
    S("S05a", "S05", "face", "ws", "hall", "HA", [G_], "REV", "High wide: the old man walking alone between white-clothed tables toward the dim corner, seen from behind.",
      motion="He walks slowly away from the camera toward the corner; diners' heads turn slightly." + HOLD, expr="back"),
    S("S05b", "S05", "face", "ms", "hall", "EL", [M_], "PILLAR", "Peeking past a blurred pillar: diners at the bright window tables glancing toward the corner, Mamiya in a beige coat with a wine glass.",
      motion="Mamiya swirls the wine glass and glances sideways with a smirk; others glance." + HOLD, expr="arrogant"),
    S("S05c", "S05", "d", "ms", "hall", "LA", [M_], "WIN", "Low medium: Mamiya setting down his wine glass and calling out loudly, wrinkling his nose.", line="L08",
      act="Mamiya complains loudly and dismissively, mocking the old man, setting down his wine glass and wrinkling his nose, gesturing toward the corner." + OB, expr="arrogant"),
    S("S05d", "S05", "d", "ms", "hall", "EL", [I_, M_], "WIN", "Medium past Mamiya's blurred shoulder: Iwaki bowing low with an exaggerated fawning smile.", line="L09",
      act="Iwaki apologizes with an exaggerated fawning smile, bowing low to Mamiya, hands together. Promising to clear it away." + OB, expr="fawn"),
    S("S05e", "S05", "d", "ots", "hall", "LA", [M_, I_], "WIN", "Over Iwaki's blurred bowed back, low angle: Mamiya swirling his glass, chin raised arrogantly.", line="L09a",
      act="Mamiya brags arrogantly, swirling the glass, chin raised, reminding Iwaki how much his father spends here." + OB, expr="arrogant"),
    S("S05f", "S05", "d", "ms", "hall", "EL", [I_, M_], "TABLE", "Medium: Iwaki bowing even deeper beside the table, servile smile.", line="L09b",
      act="Iwaki bows even deeper with a servile smile, murmuring that he is fully aware." + OB, expr="fawn"),
    S("S05g", "S05", "face", "cu", "corner", "HA", [G_], "CORNER", "High close-up of Genzo at the corner table, hearing it all, eyes lowered, dignified.",
      motion="His eyes lower to the tablecloth, a slow breath, his hands rest still." + HOLD, expr="calm"),
    S("S05h", "S05", "d", "cu", "tension", "EL", [I_], "TABLE", "Chest-up close-up of Iwaki turning away from the table, voice low and cold, eyes hard.", line="L10",
      act="Iwaki turns and orders the waitress in a low cold voice, eyes hard, barely moving his lips' surroundings. Ordering deodorant spray." + OB, expr="cold"),
    S("S05i", "S05", "d", "ots", "hall", "EL", [C_, I_], "TABLE", "Over Iwaki's blurred shoulder: Chihiro holding a tray, hesitating, eyes flicking toward the old man.", line="L11",
      act="Chihiro hesitates, holding the tray to her chest, glancing toward the old man, protesting softly." + OB, expr="kind"),
    S("S05j", "S05", "d", "ots", "tension", "HA", [I_, G_], "CORNER", "Over Genzo's blurred shoulder (left foreground): Iwaki leaning down over the corner table, hissing a threat.", line="L12",
      act="Iwaki leans over the table and tells the old man in a low hiss to drink his water and leave, contempt barely hidden." + OB, expr="sneer"),
    S("S05k", "S05", "face", "cu", "corner", "EL", [G_], "CORNER", "Close-up of Genzo turning his gaze to the window, silent, the city light on his face.",
      motion="He turns his eyes toward the window within 15 degrees, silent, a slow breath." + HOLD, expr="calm"),
    S("S05l", "S05", "ins", "ecu", "corner", "EL", [], "CORNER", "Insert: a hand placing a black leather check presenter on the white tablecloth with a sharp tap, no face.",
      motion="The hand sets the folder down flat on the white tablecloth with a small tap, then slowly withdraws out of frame; the folder stays lying flat on the tabletop, never on a chair, its size unchanged.", line="L12a", vo=True),
    S("S05m", "S05", "ins", "ecu", "corner", "EL", [G_], "CORNER", "Insert: old hands opening a worn brown leather wallet; tucked inside, a small faded black-and-white photograph of a tiny wooden udon shop with a woman in an apron and a small boy, no writing anywhere.",
      motion="The old fingers open the wallet slowly; the photo comes into view.", line="L12b", vo=True),
    S("S05n", "S05", "d", "ots", "corner", "HA", [G_, I_], "CORNER", "Over Iwaki's blurred shoulder: Genzo stroking the old photo with his thumb, a faint smile.", line="L12c",
      act="Genzo says quietly that it is his treasure, stroking the photograph with his thumb, eyes soft." + OB, expr="smile"),
    S("S05o", "S05", "face", "ews", "corner", "HA", [G_], "BIRD", "High wide: the old man alone and small at the corner table, the bright hall beyond.",
      motion="He sits still, the wallet in his hands; diners move in the distance." + HOLD, line="NA7a", expr="calm"),
    S("S06a", "S06", "empty", "ws", "dusk", "EL", [], "DRIVE", "Wide: a black luxury sedan gliding to a stop at the empty hotel driveway, golden hour.",
      motion="The sedan glides in and stops; reflections slide over the paint.", line="NA8"),
    S("S06a2", "S06", "face", "ws", "dusk", "EL", [K_], "CAR_D", "Wide from outside the sedan: through the half-lowered tinted rear window, Sakaki in the back seat checking his wristwatch, the hotel entrance reflected in the glass.",
      motion="He lifts his wrist and checks the watch, then lowers it; composed." + HOLD, expr="calm"),
    S("S06b", "S06", "d", "ms", "car", "EL", [K_], "CAR_D", "Medium in the sedan's back seat: Sakaki at three-quarter angle with a phone to his ear, glancing at his watch.", line="L13",
      act="Sakaki speaks quietly and formally into the phone, glancing at his wristwatch, confirming he will not go in yet." + OB, expr="calm"),
    S("S06c", "S06", "ins", "ecu", "car", "EL", [], "CAR_D", "Insert: a smartphone screen in a gloved hand showing a shaky video of an old man's back in a restaurant (screen composited).",
      motion="The thumb scrolls slightly; the screen glows."),
    S("S06d", "S06", "d", "cu", "car", "EL", [K_], "CAR_D", "Close-up of Sakaki staring at the phone, face hardening behind silver glasses.", line="L13a",
      act="Sakaki murmurs with restrained anger, staring at the phone, jaw tightening behind his silver glasses." + OB, expr="calm"),
    S("S06e", "S06", "face", "ms", "car", "EL", [K_], "CAR_D", "Medium: Sakaki lowering the phone and looking toward the hotel entrance through the tinted window, waiting.",
      motion="He lowers the phone and looks out the window, still, waiting." + HOLD, line="NA9", expr="calm"),
    S("S06f", "S06", "ins", "ecu", "corner", "EL", [G_], "CORNER", "Insert: an old wristwatch with a cracked leather strap on a thin wrist, the hand resting on the tablecloth.",
      motion="The second hand ticks; the wrist turns slightly.", line="NA10"),
    S("S06g", "S06", "empty", "ws", "hall", "EL", [], "HALL", "Wide of the hall, diners and waiters moving quietly, the corner in shadow.",
      motion="Two small waiters far in the background cross slowly from left to right at the same distance; nobody walks toward the camera; pendant lamps glow softly.", line="NA11"),

    # ③ 전개·위기
    S("S07a", "S07", "ins", "ecu", "corner", "EL", [C_], "TABLE", "Insert: a young woman's hand setting a steaming cup of green tea gently in front of an old man's hands.",
      motion="The cup is set down gently, steam rising; the old hands move toward it."),
    S("S07b", "S07", "d", "ots", "corner", "EL", [C_, G_], "CORNER", "Over Genzo's blurred shoulder (left foreground): Chihiro at three-quarter angle, sliding the tea toward him, kind smile.", line="L14",
      act="Chihiro speaks kindly, sliding the tea toward the old man, a warm small smile, telling him to drink slowly." + OB, expr="smile"),
    S("S07c", "S07", "d", "ots", "corner", "EL", [G_, C_], "CORNER", "Over Chihiro's blurred shoulder (right foreground): Genzo cupping the tea in both hands, a first faint smile.", line="L15",
      act="Genzo thanks her warmly, cupping the tea in both hands, a first faint smile, asking how long she has worked here." + OB, expr="smile"),
    S("S07d", "S07", "d", "ots", "corner", "EL", [C_, G_], "CORNER", "Over Genzo's blurred shoulder: Chihiro holding the tray to her chest, shy.", line="L16",
      act="Chihiro answers shyly, the tray hugged to her chest, saying three months, working for her tuition." + OB, expr="smile"),
    S("S07e", "S07", "d", "ots", "corner", "EL", [G_, C_], "CORNER", "Over Chihiro's blurred shoulder: Genzo looking up with interest, the tea in his hands.", line="L16a",
      act="Genzo asks with gentle interest what she is studying, looking up at her, the tea in his hands." + OB, expr="calm"),
    S("S07f", "S07", "d", "cu", "corner", "EL", [C_], "CORNER", "Close-up of Chihiro smiling shyly, eyes bright with her dream.", line="L16b",
      act="Chihiro answers with a shy bright smile, a little embarrassed, saying nutrition science and that she wants to open a children's cafeteria someday." + OB, expr="smile"),
    S("S07g", "S07", "face", "cu", "corner", "EL", [G_], "CORNER", "Close-up of Genzo listening, his eyes softening with warmth.",
      motion="His eyes soften, a small nod, the tea held still." + HOLD, expr="smile"),
    S("S07h", "S07", "d", "ots", "corner", "EL", [C_, G_], "CORNER", "Over Genzo's blurred shoulder: Chihiro glancing around, then speaking softly.", line="L17",
      act="Chihiro glances around and speaks softly and fondly about her grandfather who struggled long ago." + OB, expr="kind"),
    S("S07i", "S07", "face", "cu", "corner", "EL", [C_], "CORNER", "Close-up of Chihiro smiling at the old man's words.", line="L18", vo=True,
      motion="She smiles warmly, a small nod, the tray against her chest." + HOLD, expr="smile"),
    S("S07j", "S07", "d", "ms", "corner", "HA", [G_, C_], "CORNER", "Medium, slight high angle: Genzo setting down the tea and looking up at her earnestly.", line="L19",
      act="Genzo sets down the tea and asks earnestly, looking up at her, why she is kind to someone like him." + OB, expr="calm"),
    S("S07k", "S07", "d", "cu", "corner", "EL", [C_], "CORNER", "Close-up of Chihiro thinking a moment, then answering with a simple smile.", line="L20",
      act="Chihiro thinks a moment, then answers simply with a warm smile that clothes do not matter to someone who is hungry." + OB, expr="smile"),
    S("S07l", "S07", "face", "cu", "corner", "EL", [G_], "CORNER", "Close-up of Genzo moved, eyes glistening, a long breath.",
      motion="His eyes glisten, a long breath, lips press together." + WET_HOLD + HOLD, expr="calm"),
    S("S07m", "S07", "d", "ots", "corner", "EL", [C_, G_], "CORNER", "Over Genzo's shoulder: Chihiro glancing toward the kitchen, then whispering with resolve.", line="L21",
      act="Chihiro glances toward the kitchen, then whispers with quiet resolve that she will ask the kitchen for kake udon." + OB, expr="kind"),
    S("S08a", "S08", "ins", "ecu", "kitchen", "EL", [], "POT", "Insert: a ladle lifting clear broth from a large steaming staff-meal stockpot.",
      motion="The ladle lifts, broth pours back, steam billows.", line="NA12"),
    S("S08b", "S08", "ins", "ms", "kitchen", "EL", [C_], "PASS", "Medium: Chihiro quietly pouring broth over noodles in a plain white bowl at the serving pass, glancing over her shoulder.",
      motion="She pours carefully, glances over her shoulder, steam rising." + HOLD, expr="kind"),
    S("S09a", "S09", "face", "ms", "hall", "LA", [I_], "WIN", "Low medium: Iwaki bowing deeply to a well-dressed regular customer seen from behind at the window table.",
      motion="He bows deeply and holds it, hands together." + HOLD, line="NA13", expr="fawn"),
    S("S09b", "S09", "face", "cu", "hall", "LA", [I_], "WIN", "Close-up: still half-bowed, Iwaki turns his eyes toward the corner and scoffs. Mid-story card composited.",
      motion="His eyes slide toward the corner, a scoff curls his lip; the bow holds." + HOLD, expr="sneer"),
    S("S10a", "S10", "ins", "ecu", "corner", "EL", [], "TABLE", "Insert: a steaming bowl of plain kake udon in a simple white bowl on the white tablecloth, chopsticks resting on it, steam curling.",
      motion="Steam curls up slowly from the bowl."),
    S("S10b", "S10", "face", "cu", "corner", "HA", [G_], "CORNER", "Close-up of Genzo looking down at the steaming bowl, eyes wet, steam on his face.",
      motion="Steam drifts across his face, his eyes glisten." + WET_HOLD + HOLD, expr="calm"),
    S("S10c", "S10", "d", "ots", "hall", "LA", [M_, G_], "CORNER", "Over Genzo's blurred shoulder, low angle: Mamiya standing over the table, phone in hand, sneering.", line="L22",
      act="Mamiya sneers down at the old man in a mocking, dismissive tone, phone in hand, telling him this is no place for him and to go home." + OB, expr="mock"),
    S("S10d", "S10", "d", "ots", "corner", "HA", [G_, M_], "CORNER", "Over Mamiya's blurred shoulder: Genzo not looking up from the bowl, speaking quietly.", line="L23",
      act="Genzo answers quietly without looking away from the bowl, saying this place is dear to him." + OB, expr="calm"),
    S("S10e", "S10", "face", "ms", "sepia", "EL", [], "U_DOOR", "Sepia flashback through steam: the backlit silhouette of the shop mistress leaning toward the counter, warm.",
      motion="Steam rises across the silhouette, a gentle nod; the face stays in shadow.", line="L23a", vo=True),
    S("S10f", "S10", "ins", "ecu", "sepia", "EL", [], "U_BOWL", "Sepia insert: steam rising from a bowl on the old wooden counter of 1955.",
      motion="Steam rises and slowly dissolves.", line="NA13a"),
    S("S10g", "S10", "d", "ms", "tension", "LA", [I_, C_], "TABLE", "Low medium: Iwaki striding in, glaring at the waitress, handheld feel.", line="L24", fx="handheld",
      act="Iwaki snaps angrily at Chihiro, striding in, glaring, jabbing a finger at the bowl. Scolding her for serving staff food." + OB, expr="sneer"),
    S("S10h", "S10", "d", "ots", "tension", "HA", [C_, I_], "TABLE", "Over Iwaki's blurred shoulder, high angle: Chihiro shrinking back, voice trembling.", line="L25",
      act="NOT smiling: frightened and trembling. Chihiro answers in a trembling voice, shrinking back, explaining the old man wanted kake udon." + OB, expr="kind"),
    S("S10i", "S10", "d", "ots", "tension", "LA", [I_, C_], "TABLE", "Over Chihiro's blurred shoulder, low angle: Iwaki looking down coldly.", line="L26",
      act="Iwaki looks down at her coldly, jaw tight, telling her not to overstep and that she is fired as of today." + OB, expr="cold"),
    S("S10j", "S10", "face", "cu", "tension", "HA", [C_], "TABLE", "High close-up of Chihiro stunned, eyes welling.",
      motion="She freezes, eyes welling, a shaky breath." + WET_HOLD + HOLD, expr="tears"),
    S("S10k", "S10", "d", "ms", "tension", "LA", [I_, C_], "TABLE", "Low medium: Iwaki holding out his hand, demanding.", line="L26a",
      act="Iwaki holds out his hand and demands coldly that she take off her apron right now." + OB, expr="cold"),
    S("S10l", "S10", "ins", "ecu", "tension", "EL", [C_], "TABLE", "Insert: trembling young hands untying the strings of a plain navy apron at the waist.",
      motion="The fingers tremble as they pull the apron strings loose."),
    S("S10m", "S10", "face", "ms", "hall", "LA", [M_], "TABLE", "Low medium: Mamiya filming with his phone held up, grinning.", line="L27", vo=True,
      motion="He holds the phone up filming, grinning wider, shoulders shaking with a laugh." + HOLD, expr="mock"),
    S("S10n", "S10", "ins", "ms", "tension", "EL", [C_], "TABLE", "Medium on Chihiro's hands clutching the removed apron, head bowed, face hidden by her bangs.", line="L27a", vo=True,
      motion="Her hands clutch the apron tighter, head bowed, shoulders trembling."),
    S("S10o", "S10", "ins", "ecu", "hall", "EL", [], "TABLE", "Insert: a smartphone screen showing an upload with a rising like counter (screen composited).",
      motion="The counter ticks up; the screen glows."),
    S("S10p", "S10", "d", "ms", "hall", "LA", [M_, C_], "TABLE", "Low medium: Mamiya waving his phone, laughing.", line="L27b",
      act="Mamiya laughs gleefully, waving the phone, boasting the video passed a thousand views." + OB, expr="mock"),
    S("S10q", "S10", "d", "ots", "tension", "EL", [C_, M_], "TABLE", "Over Mamiya's blurred shoulder: Chihiro turning to face him, eyes wet but steady.", line="L27c",
      act="NOT smiling at any moment: crying while shouting, brows knotted, the corners of the mouth pulled down between words, eyes wet. Chihiro turns and protests in a trembling but steady voice, eyes wet, telling him to stop mocking people." + WET_HOLD + OB, expr="tears"),
    S("S10q2", "S10", "face", "cu", "hall", "LA", [M_], "TABLE", "Low close-up of Mamiya shrugging with a smirk.", line="L27d", vo=True,
      motion="He shrugs with a smirk, rolling his eyes." + HOLD, expr="mock"),
    S("S10r", "S10", "face", "ms", "tension", "LA", [I_, G_], "CORNER", "Low medium, dutch 5 degrees: Iwaki yanking the old man's frayed grey jacket sleeve, the old man calm.", fx="dutch5 handheld",
      motion="Iwaki keeps gripping the sleeve the whole time and tugs it hard twice, never letting go, staying right beside the old man; the old man sways slightly but stays calm; Iwaki's mouth stays closed." + HOLD, expr="sneer"),
    S("S10s", "S10", "d", "ots", "tension", "EL", [C_, I_], "CORNER", "Over Iwaki's blurred shoulder: Chihiro stepping between them, eyes brimming with tears.", line="L28",
      act="NOT smiling at any moment: crying while shouting, brows knotted, the corners of the mouth pulled down between words, eyes wet. Chihiro pleads, stepping in front of the old man, voice shaking, offering to pay for the udon herself." + WET_HOLD + OB, expr="tears"),
    S("S10t", "S10", "face", "cu", "tension", "EL", [C_], "CORNER", "Close-up of Chihiro, a tear finally running down her cheek, lips pressed.",
      motion="NOT smiling at any moment: her lips press tight and the corners of the mouth pull down, chin trembling, brows knotted in held-back pain." + TEARS_FLOW + HOLD, expr="tears"),
    S("S10u", "S10", "d", "ms", "tension", "LA", [I_, C_], "CORNER", "Low medium: Iwaki exploding, a vein on his temple, leaning forward, handheld.", line="L29", fx="handheld",
      act="Iwaki explodes, leaning forward, a vein on his temple, shouting for both of them to get out now." + OB, expr="sneer"),
    S("S11a", "S11", "face", "ms", "reveal", "EL", [G_], "CORNER", "Eye-level medium: the old man slowly rising from his chair for the first time, steady, the window light behind him.",
      motion="He rises slowly from the chair to his full height, steady, hands at his sides." + HOLD, expr="stern"),
    S("S11b", "S11", "d", "ots", "reveal", "EL", [G_, I_], "CORNER", "Over Iwaki's blurred shoulder, eye level: Genzo standing, calm and firm.", line="L30",
      act="Genzo says quietly and firmly that he will pay for the udon, standing tall, eyes steady on Iwaki." + OB, expr="stern"),
    S("S11c", "S11", "ins", "ecu", "corner", "EL", [G_], "CORNER", "Insert: an old thumb pressing one button on a worn silver flip phone, screen dark.",
      motion="The thumb presses the button once and lifts."),
    S("S11d", "S11", "ins", "ecu", "car", "EL", [], "CAR_D", "Insert: a smartphone vibrating once on a cream leather car seat.",
      motion="The phone buzzes once, a small rattle on the leather."),
    S("S11e", "S11", "d", "ms", "car", "EL", [K_], "CAR_D", "Medium: Sakaki opening the car door, speaking briefly toward the driver.", line="L30a",
      act="Sakaki says quietly and briefly that it is the signal, opening the door with resolve." + OB, expr="calm"),
    S("S11f", "S11", "ins", "ecu", "lobby", "LA", [K_], "LOBBY", "Low insert: polished black shoes striding across the marble lobby floor.",
      motion="The shoes stride steadily across the marble, reflections sliding."),
    S("S11g", "S11", "d", "ots", "tension", "HA", [I_, G_], "CORNER", "Over Genzo's blurred shoulder: Iwaki looking down with a mocking smile, unaware.", line="L30b",
      act="Iwaki smirks, unaware, telling the old man it's useless and that he will call security." + OB, expr="sneer"),
    S("S11h", "S11", "face", "ws", "tension", "EL", [], "HALL", "Wide: two security guards in plain dark suits approaching the corner from behind, reaching for the old man's arm.",
      motion="The guards walk in and reach out; diners stand to watch."),
    S("S11i", "S11", "d", "ots", "tension", "EL", [C_, G_], "CORNER", "Over the old man's blurred shoulder: Chihiro spreading her arms in front of him, crying out.", line="L30c",
      act="NOT smiling at any moment: crying while shouting, brows knotted, the corners of the mouth pulled down between words, eyes wet. Chihiro spreads her arms in front of the old man and shouts fiercely for them not to touch him, jaw set hard, voice shaking but loud." + WET_HOLD + OB, expr="tears"),
    S("S11j", "S11", "empty", "ws", "hall", "EL", [], "HALL", "Wide of the whole hall frozen, every diner watching the corner, silence.",
      motion="Everyone stays frozen; only the pendant lamps sway slightly.", line="NA14"),
    S("S11k", "S11", "face", "cu", "reveal", "LA", [G_], "CORNER", "Low close-up of Genzo standing calm and dignified, backlit.", line="NA14a",
      motion="He stands calm, a slow breath, eyes steady." + HOLD, expr="stern"),

    # ④ 절정·결말
    S("S12a", "S12", "empty", "ws", "hall", "EL", [], "REV", "Wide: the heavy wooden door at the far end of the hall swinging open, light spilling in.",
      motion="The door swings open slowly, light spills across the floor."),
    S("S12b", "S12", "face", "ms", "reveal", "EL", [K_], "HALL", "Medium: Sakaki walking into the hall in a black three-piece suit, silver glasses, composed. Dolly zoom applied in edit.", fx="dollyzoom",
      motion="He walks steadily forward, composed, eyes fixed ahead." + HOLD, expr="calm"),
    S("S12c", "S12", "ins", "ecu", "hall", "LA", [K_], "LOWF", "Low insert at floor level: polished black shoes taking three measured steps on the wooden floor.",
      motion="Three measured steps toward the camera, then stop."),
    S("S12d", "S12", "face", "ms", "reveal", "SIDE", [K_, G_], "CORNER", "Side two-shot: Sakaki bowing deeply before the old man, who stands calm.",
      motion="Sakaki lowers into a deep bow and holds it; the old man stands still." + HOLD, expr="bow"),
    S("S12e", "S12", "d", "ots", "reveal", "EL", [K_, G_], "CORNER", "Over Genzo's blurred shoulder: Sakaki rising from the bow, speaking respectfully.", line="L31",
      act="Sakaki rises from the bow and reports respectfully that the car is ready, addressing him as Chairman." + OB, expr="calm"),
    S("S12f", "S12", "d", "cu", "tension", "LA", [I_], "CORNER", "Close-up of Iwaki gone pale, lips trembling, cold sweat, dutch 7 degrees.", line="L32", fx="dutch7 handheld",
      act="NOT smiling: shock and fear. Iwaki stammers in shock, gone pale, lips trembling, cold sweat on his brow, repeating 'Chairman' in disbelief." + OB, expr="cold"),
    S("S12g", "S12", "d", "ots", "reveal", "EL", [K_, I_], "CORNER", "Over Iwaki's blurred shoulder: Sakaki standing upright beside the chairman, announcing clearly.", line="L33",
      act="Sakaki announces clearly and coldly, looking at Iwaki, that this is the founder Takamiya Genzo, the owner of this hotel." + OB, expr="calm"),
    S("S12h", "S12", "ins", "ms", "hall", "EL", [M_], "TABLE", "Medium on Mamiya's hand slowly lowering his phone, his face going slack behind it.",
      motion="The phone lowers slowly, his face goes slack." + HOLD, expr="panic"),
    S("S13a", "S13", "d", "ots", "tension", "HA", [I_, G_], "CORNER", "Over Genzo's blurred shoulder, high angle: Iwaki forcing a smile, sweat on his face.", line="L34",
      act="Iwaki makes excuses with a forced smile, sweat beading, wringing his hands, blaming the restaurant rules." + OB, expr="fawn"),
    S("S13b", "S13", "face", "cu", "tension", "HA", [I_], "CORNER", "High close-up of Iwaki, a bead of cold sweat running down his temple.",
      motion="He swallows hard." + SWEAT_FLOW + HOLD, expr="cold"),
    S("S13c", "S13", "d", "ots", "reveal", "LA", [G_, I_], "CORNER", "Over Iwaki's blurred shoulder, low angle: Genzo backlit, looking straight at him.", line="L35",
      act="Genzo says quietly and firmly, looking straight into Iwaki's eyes, that he made the rules." + OB, expr="stern"),
    S("S13d", "S13", "face", "cu", "tension", "HA", [I_], "CORNER", "High close-up of Iwaki's eyes widening, mouth slightly open.",
      motion="His eyes widen, his mouth opens slightly, a sharp breath." + HOLD, expr="cold"),
    S("S13e", "S13", "d", "ms", "reveal", "LA", [G_], "HALL", "Low medium: Genzo looking slowly around the hall, speaking with quiet authority.", line="L36",
      act="Genzo looks slowly around the hall and states with quiet authority the one rule he set on opening day: never turn away a hungry customer." + OB, expr="stern"),
    S("S13f", "S13", "d", "ots", "reveal", "EL", [K_, I_], "CORNER", "Over Iwaki's blurred shoulder: Sakaki speaking coolly, adjusting his silver glasses.", line="L36a",
      act="Sakaki speaks coolly and ironically to Iwaki, adjusting his silver glasses, quoting his evaluation that always praised 'high spend per customer'." + OB, expr="calm"),
    S("S13g", "S13", "d", "cu", "reveal", "EL", [G_], "CORNER", "Close-up of Genzo gazing into the distance, remembering.", line="L37",
      act="Genzo remembers aloud, gazing into the distance with a gentle sad look, telling of the small udon shop seventy years ago and the orphan boy fed for free." + OB, expr="calm"),
    S("S13h", "S13", "ins", "ecu", "sepia", "EL", [], "CORNER", "Insert flash: the faded black-and-white photograph of the udon shop mistress and the small boy, in the old wallet, no writing.",
      motion="A slow push toward the photograph; a faint tremble of the old hand holding it."),
    S("S13i", "S13", "d", "cu", "reveal", "EL", [G_], "CORNER", "Choker close-up of Genzo, eyes wet, after a long silence.", line="L38",
      act="After a long silence Genzo says softly that the boy was him, eyes wet and glistening, voice low." + WET_HOLD + OB, expr="calm"),
    S("S13j", "S13", "face", "cu", "tension", "HA", [I_], "CORNER", "High close-up of Iwaki frozen, the color draining from his face.",
      motion="He stands frozen, his lips part, a shaky breath." + HOLD, expr="cold"),
    S("S13k", "S13", "d", "ms", "reveal", "LA", [G_, I_], "CORNER", "Low medium: Genzo speaking firmly, the hall behind him.", line="L39",
      act="Genzo states firmly, each phrase measured, that a shop that turns away the hungry has no right to bear the Takamiya name." + OB, expr="stern"),
    S("S14a", "S14", "face", "ms", "tension", "HA", [I_], "CORNER", "High medium: Iwaki sinking to his knees on the floor.",
      motion="He sinks slowly to his knees, hands trembling." + HOLD, expr="cold"),
    S("S14b", "S14", "face", "ews", "tension", "BE", [I_], "BIRD", "Bird's-eye view straight down: Iwaki prostrate in dogeza on the wooden floor between the tables, forehead to the floor.",
      motion="He presses his forehead to the floor, shoulders trembling; he does not look up."),
    S("S14c", "S14", "d", "ots", "tension", "HA", [I_, G_], "CORNER", "Over Genzo's blurred legs, high angle: Iwaki on the floor lifting only his head, begging, tears and sweat.", line="L40",
      act="NOT smiling at any moment: desperate, brows knotted upward, mouth pulled down. Iwaki begs desperately from the floor, lifting only his head, voice breaking, tears and sweat on his face, apologizing for not recognizing him." + WET_HOLD + OB, expr="cold"),
    S("S14d", "S14", "d", "ots", "reveal", "LA", [G_, I_], "CORNER", "Over Iwaki's blurred head, low angle: Genzo looking down with bitter calm.", line="L41",
      act="Genzo answers bitterly and calmly, looking down, that being sorry for not knowing means he would not have done it had he known." + OB, expr="stern"),
    S("S14e", "S14", "face", "cu", "tension", "HA", [I_], "LOWF", "High close-up of Iwaki on the floor, sweat dripping, eyes darting.",
      motion="His eyes dart, his breath shakes." + SWEAT_FLOW + HOLD, expr="cold"),
    S("S14f", "S14", "d", "cu", "reveal", "EL", [G_], "CORNER", "Close-up of Genzo at three-quarter angle, delivering the dismissal quietly and politely.", line="L42",
      act="Genzo says quietly in calm polite Japanese, without raising his voice, that Iwaki need not come in from tomorrow." + OB, expr="stern"),
    S("S14g", "S14", "d", "ms", "hall", "EL", [M_, G_], "TABLE", "Medium: Mamiya half-rising awkwardly, forced smile, sweat.", line="L43",
      act="Mamiya stammers awkwardly, half-rising, a forced panicked smile and sweat, mentioning his father is a Takamiya supplier." + OB, expr="panic"),
    S("S14h", "S14", "d", "ots", "reveal", "EL", [K_, M_], "TABLE", "Over Mamiya's blurred shoulder: Sakaki speaking with cold courtesy.", line="L44",
      act="Sakaki tells him with cold courtesy that the chairman will personally call his father tonight." + OB, expr="calm"),
    S("S14i", "S14", "estill", "ecu", "hall", "EL", [], "TABLE", "Insert: a thumb deleting a video on a dark smartphone screen (screen composited, dim)."),
    S("S14j", "S14", "face", "cu", "hall", "EL", [M_], "TABLE", "Close-up of Mamiya frozen, the phone lowered, face slack.", line="L45", vo=True,
      motion="He stays frozen, a hard swallow, eyes lowered." + HOLD, expr="panic"),
    S("S15a", "S15", "estill", "ecu", "corner", "EL", [], "TABLE", "Insert: the bowl of kake udon now cold on the tablecloth, no steam, chopsticks untouched."),
    S("S15b", "S15", "d", "ots", "hall", "HA", [G_, C_], "CORNER", "Over Chihiro's blurred shoulder: Genzo sitting back down, looking up at her warmly.", line="L46",
      act="Genzo sits back down and asks her warmly, looking up with a gentle smile, to warm up another bowl." + OB, expr="smile"),
    S("S15c", "S15", "d", "cu", "hall", "EL", [C_], "CORNER", "Close-up of Chihiro answering brightly through wet eyes.", line="L47",
      act="Chihiro answers brightly through wet eyes, nodding quickly, promising to warm it right away." + WET_HOLD + OB, expr="smile"),
    S("S15d", "S15", "ins", "ecu", "hall", "EL", [], "TABLE", "Insert: a fresh steaming bowl of kake udon set down, steam rising strongly.",
      motion="Steam rises strongly from the fresh bowl."),
    S("S15e", "S15", "ins", "ecu", "hall", "EL", [G_], "TABLE", "Insert: old hands lifting noodles with chopsticks, steam swirling.",
      motion="The chopsticks lift the noodles slowly, steam swirling."),
    S("S15f", "S15", "face", "cu", "hall", "EL", [G_], "CORNER", "Close-up of Genzo chewing slowly, a tear escaping.",
      motion="He chews slowly, eyes closing." + TEARS_FLOW + HOLD, expr="calm"),
    S("S15g", "S15", "d", "ots", "hall", "EL", [G_, C_], "CORNER", "Over Chihiro's blurred shoulder (right foreground): Genzo holding the chopsticks, voice trembling with emotion, eyes wet.", line="L48",
      act="Genzo says with a trembling voice that it is the first time in seventy years and tastes the same, eyes wet, a faint smile." + WET_HOLD + OB, expr="smile"),
    S("S15h", "S15", "d", "ots", "hall", "EL", [C_, G_], "CORNER", "Over Genzo's blurred shoulder: Chihiro with hands clasped, choking up.", line="L49",
      act="NOT smiling at any moment: crying while shouting, brows knotted, the corners of the mouth pulled down between words, eyes wet. Chihiro chokes up, hands clasped at her chest, saying she truly knew nothing." + WET_HOLD + OB, expr="tears"),
    S("S15i", "S15", "d", "ots", "hall", "EL", [G_, C_], "CORNER", "Over Chihiro's blurred shoulder: Genzo shaking his head gently with a kind smile.", line="L50",
      act="Genzo shakes his head gently with a kind smile, saying it was good precisely because she did not know." + OB, expr="smile"),
    S("S15j", "S15", "face", "cu", "hall", "EL", [C_], "CORNER", "Close-up of Chihiro listening, eyes brimming.",
      motion="Her eyes brim, she breathes in shakily." + WET_HOLD + HOLD, expr="tears"),
    S("S15k", "S15", "d", "ms", "hall", "EL", [G_, C_], "CORNER", "Medium: Genzo telling her kindly about the scholarship.", line="L51",
      act="Genzo tells her kindly that from next year she is a Takamiya scholar and need not worry about tuition, a warm smile." + OB, expr="smile"),
    S("S15l", "S15", "face", "cu", "hall", "EL", [C_], "CORNER", "Close-up of Chihiro covering her mouth with both hands, tears running.",
      motion="She covers her mouth with both hands." + TEARS_FLOW + HOLD, expr="tears"),
    S("S15m", "S15", "d", "ms", "reveal", "EL", [G_, K_], "CORNER", "Medium: Genzo turning to Sakaki, speaking firmly and warmly.", line="L52",
      act="Genzo turns to Sakaki and instructs him firmly and warmly to put kake udon on the menu and never charge the hungry." + OB, expr="stern"),
    S("S15n", "S15", "face", "cu", "reveal", "EL", [K_], "CORNER", "Close-up of Sakaki bowing his head slightly in acknowledgment, a faint smile.",
      motion="He bows his head slightly, a faint smile." + HOLD, expr="calm"),
    S("S16a", "S16", "face", "cu", "car_n", "SIDE", [G_], "CAR_N", "Night, back seat of the sedan: Genzo's peaceful profile as Tokyo lights slide across the window.",
      motion="City lights slide across his face, a slow peaceful blink." + HOLD, line="NA15", expr="calm"),
    S("S16b", "S16", "estill", "ecu", "hall", "EL", [], "TABLE", "Insert: a plain cream menu card on a wooden table, its last line blank for a composited line."),
    S("S16c", "S16", "face", "ms", "hall", "EL", [C_], "PASS", "Medium: Chihiro carrying a steaming bowl from the pass, smiling, a few months later.",
      motion="She carries the bowl carefully, smiling, steam rising." + HOLD, line="NA15a", expr="smile"),
    S("S16d", "S16", "ins", "ecu", "car_n", "EL", [G_], "CAR_N", "Insert: an old hand writing with a fountain pen on cream paper under a reading light, no legible writing.",
      motion="The pen moves slowly across the paper.", line="NA16"),
    S("S16e", "S16", "face", "cu", "car_n", "EL", [G_], "CAR_N", "Close-up of Genzo setting down the pen, looking out at the night with quiet resolve.",
      motion="He sets the pen down and looks out the window, a slow breath." + HOLD, line="NA17", expr="calm"),
    S("S16f", "S16", "empty", "ews", "night", "LA", [], "FRONT_N", "Low wide of the hotel entrance glowing at night.",
      motion="The building stays perfectly still and unchanged; only a faint shimmer of the warm entrance lights; no cars arrive, no headlights, no glare.", line="NA18"),
    S("S17a", "S17", "empty", "ews", "night", "EL", [], "FRONT_N", "Wide of the Tokyo night skyline beyond the hotel. Next-story card composited.",
      motion="Lights twinkle, a slow cloud drift."),
]

# 절감형(「月に帰った」 A안과 같은 방식, 제12장 2): 짧거나 정보 전달 위주의 대사는 화자 대신 「듣는 사람」 i2v 리액션 위에 목소리(L컷).
# 립싱크는 감정·반전·명대사 위주로 남긴다.
VO = {  # line: (who, lens, angle, loc, subject, motion, expr)
 "L13": ([K_], "ws", "EL", "DRIVE", "Wide from outside: the black sedan parked at the entrance, Sakaki visible through the tinted glass with a phone to his ear, mouth not visible.", "Reflections slide over the glass; the figure inside sits still with the phone." + HOLD, "calm"),
 "L25": ([I_], "cu", "LA", "TABLE", "Low chest-up close-up of Iwaki glaring down at her excuse, nostrils flaring.", "His nostrils flare, the glare hardens; lips stay pressed. Both arms stay down at his sides out of frame, hands never rise, no fists, no gestures." + HOLD, "sneer"),
 "L27b": ([C_], "cu", "EL", "TABLE", "Close-up of Chihiro hearing the boast, hurt, eyes welling.", "Her eyes well, her lips tremble." + WET_HOLD + HOLD, "tears"),
 "L34": ([G_], "cu", "LA", "CORNER", "Low close-up of Genzo, backlit, watching the manager's excuses in silence.", "He watches in silence, eyes steady, a slow breath." + HOLD, "stern"),
 "L09a": ([I_], "cu", "LA", "WIN", "Close-up of Iwaki half-bowed, nodding servilely at the young customer's boast.", "He nods servilely twice, the fawning smile fixed." + HOLD, "fawn"),
 "L09b": ([M_], "cu", "LA", "WIN", "Low close-up of Mamiya smirking, satisfied, swirling his wine.", "He smirks, satisfied, swirls the wine once." + HOLD, "arrogant"),
 "L10": ([C_], "cu", "EL", "TABLE", "Close-up of Chihiro hearing the order, startled, the tray tightening against her chest.", "Her eyes widen, the tray tightens against her chest, a small breath." + HOLD, "kind"),
 "L11": ([I_], "cu", "EL", "TABLE", "Chest-up close-up of Iwaki glaring sideways at the waitress, jaw tight.", "He glares sideways, jaw tightening, one slow blink." + HOLD, "cold"),
 "L12": ([G_], "cu", "HA", "CORNER", "High close-up of Genzo enduring the hissed words, eyes lowered, dignified.", "He keeps his eyes lowered, a slow breath, hands still on the table." + HOLD, "calm"),
 "L13a": ([K_], "cu", "EL", "CAR_D", "Close-up of Sakaki staring at the phone, face hardening behind silver glasses.", "His jaw tightens, eyes narrow behind the glasses, the phone held still." + HOLD, "calm"),
 "L16": ([G_], "cu", "EL", "CORNER", "Close-up of Genzo listening to her, a gentle nod, the tea in his hands.", "He nods gently, the tea held in both hands, eyes warm." + HOLD, "smile"),
 "L16a": ([C_], "ms", "EL", "CORNER", "Medium of Chihiro with the tray, surprised by the kind question, a shy smile beginning.", "A shy smile begins, she lowers her eyes then looks back." + HOLD, "smile"),
 "L17": ([G_], "ms", "EL", "CORNER", "Medium of Genzo listening, touched, the tea steaming in front of him.", "He listens, a slow nod, steam rising from the tea." + HOLD, "calm"),
 "L21": ([G_], "cu", "HA", "CORNER", "High close-up of Genzo watching her hurry toward the kitchen, eyes glistening.", "His eyes follow her toward the kitchen, glistening, a long breath." + WET_HOLD + HOLD, "calm"),
 "L26a": ([C_], "ms", "HA", "TABLE", "High medium of Chihiro staring at the outstretched hand, frozen.", "She stares at the hand, frozen, a trembling breath." + WET_HOLD + HOLD, "tears"),
 "L30a": ([K_], "ws", "EL", "DRIVE", "Wide: Sakaki stepping out of the black sedan at the hotel entrance, buttoning his jacket.", "He steps out and buttons his jacket, then walks toward the entrance." + HOLD, "calm"),
 "L30b": ([G_], "cu", "LA", "CORNER", "Low close-up of Genzo standing calm, unmoved by the threat, backlit.", "He stands unmoved, a slow breath, eyes steady." + HOLD, "stern"),
 "L36a": ([I_], "cu", "HA", "CORNER", "High close-up of Iwaki flinching at his own evaluation being quoted, sweat on his brow.", "He flinches, eyes darting." + SWEAT_FLOW + HOLD, "cold"),
 "L43": ([G_], "cu", "LA", "CORNER", "Low close-up of Genzo listening to the young man's excuse without a flicker of expression.", "He listens without expression, one slow blink." + HOLD, "stern"),
 "L44": ([M_], "cu", "EL", "TABLE", "Close-up of Mamiya going pale as he hears it, the forced smile collapsing, sweat.", "The forced smile collapses, he swallows hard." + SWEAT_FLOW + HOLD, "panic"),
 "L28": ([G_], "cu", "EL", "CORNER", "Close-up of Genzo seated, looking up at the young waitress as she steps in to defend him, deeply moved, eyes glistening.", "His eyes soften and glisten, a slow breath, lips stay closed, hands still." + WET_HOLD + HOLD, "calm"),
 "L30": ([I_], "cu", "LA", "CORNER", "Low chest-up close-up of Iwaki freezing as the old man calmly offers to pay, eyes narrowing in disbelief.", "He freezes, eyes narrow in disbelief, a sharp breath; lips stay pressed; both arms stay down, hands never rise." + HOLD, "cold"),
 "L47": ([G_], "cu", "EL", "CORNER", "Close-up of Genzo smiling warmly at her bright answer, eyes wet.", "He smiles warmly, a small nod." + WET_HOLD + HOLD, "smile"),
}
for _s in SHOTS:
    if _s["line"] in VO:
        who, lens, angle, loc, subj, mot, ex = VO[_s["line"]]
        _s.update(kind="face", who=who, lens=lens, angle=angle, loc=loc, subject=subj, motion=mot, expr=ex, act="", vo=True)

CARDS = {"H2": "三十分後、この支配人は土下座することになる", "H3": "みすぼらしい老人は、財閥会長だった", "S09b": "この後――支配人の顔が、真っ青に",
         "S16b": "かけうどん　お代は、お気持ちで", "S17a": "次回――会長の最後の配達", "S01a": "一時間前"}
TITLE_SUB = ""
JA_OVERLAY = {"H2": "화면 중앙 카드(굵은 명조)", "H3": "타이틀", "S01a": "구석 소자막 「一時間前」", "S06c": "휴대폰 업로드 영상(lcd)", "S09b": "중앙 예고 카드",
              "S10o": "휴대폰 「物乞いジジイ、高級店で門前払いｗ」·いいね(lcd)", "S14i": "휴대폰 영상 삭제 화면(lcd, 어둡게)", "S16b": "메뉴판 마지막 줄",
              "S17a": "다음 이야기 카드"}
G = {
    "city": "distant Tokyo traffic, light wind, footsteps on stone", "snow": "soft snowfall, a crackling stove inside, distant wooden clacks, winter wind",
    "hall": "porcelain bowls set on tablecloth, chopsticks clicking, a teacup on a saucer", "ent": "a leather book slapped shut, footsteps on stone floor",
    "kitchen": "a ladle in a stockpot, bubbling broth, steam hiss", "car": "luxury car interior hush, a soft engine idle", "car_n": "car interior hush, faint passing traffic at night",
    "phone": "a smartphone vibrating on leather", "lobby": "footsteps on marble, a distant revolving door", "door": "a heavy wooden door swinging open, measured footsteps",
    "steam": "steam hissing softly, a bowl set down", "night": "night city ambience, distant traffic",
}
AMB_BY_SCENE = {"S01": "city", "S02": "snow", "S03": "city", "S04": "ent", "S05": "hall", "S06": "car", "S07": "hall", "S08": "kitchen", "S09": "hall",
                "S10": "hall", "S11": "hall", "S12": "door", "S13": "", "S14": "", "S15": "steam", "S16": "car_n", "S17": "night"}
AMB_BY_SHOT = {"S06a": "city", "S06f": "hall", "S06g": "hall", "S10e": "snow", "S10f": "snow", "S11d": "phone", "S11e": "car", "S11f": "lobby",
               "S13h": "snow", "S16b": "hall", "S16c": "kitchen", "H2": "", "H3": "city"}
BGM = [  # (시작, 끝, 볼륨, 프롬프트) — 0~3.5초 BGM 없음(드론+심장 박동은 PHASE 6 로컬). 구간 간격 1.0초 이상
    (3.5, 19.0, 0.36, "low ominous drone with a single heartbeat hit and a tense string swell, Japanese drama cold open, instrumental, no vocals"),
    (20.0, 158.0, 0.38, "gentle melancholic piano with soft strings, nostalgia and loneliness, a quiet hurt, Japanese human drama, instrumental, no vocals"),
    (159.0, 200.0, 0.40, "mysterious pizzicato strings and low piano, a hidden plan unfolding, quiet suspense, Japanese drama score, instrumental, no vocals"),
    (202.0, 345.0, 0.38, "warm tender piano turning tense with low strings, kindness under pressure, rising unease, Japanese drama score, instrumental, no vocals"),
    (346.0, 399.0, 0.42, "dark pulsing suspense, heavy low strings and ticking percussion, anger and humiliation peaking, Japanese drama score, instrumental, no vocals"),
    (403.0, 516.0, 0.42, "powerful orchestral reveal with timpani and brass swelling into dignified judgment, cathartic, Japanese drama score, instrumental, no vocals"),
    (517.0, None, 0.40, "warm emotional piano and strings, tears of gratitude, a gentle hopeful resolution, Japanese human drama finale, instrumental, no vocals"),
]
for _a, _b in zip(BGM, BGM[1:]):
    assert _b[0] - _a[1] >= 1.0, f"BGM 구간 간격 {_b[0] - _a[1]:.1f}s < 1.0s"

STYLE = {"NA": "Naration", "源蔵": "Genzo", "岩城": "Iwaki", "間宮": "Mamiya", "ちひろ": "Chihiro", "榊": "Sakaki", "おかみ": "Okami"}
STYLE_JA = {"Naration": "ナレーター", "Genzo": "源蔵", "Iwaki": "岩城", "Mamiya": "間宮", "Chihiro": "ちひろ", "Sakaki": "榊", "Okami": "おかみ"}
STYLE_COLOR = {"Naration": "&H00DDDDDD", "Genzo": "&H00FFFFFF", "Iwaki": "&H00B4D2FF", "Mamiya": "&H00C8C8F0", "Chihiro": "&H00F0E6C8",
               "Sakaki": "&H00E6DCC8", "Okami": "&H00C8E6F0"}
RATE = {"lite": 0.036, "omni": 0.16, "kf": 0.04}
HOOK_LEN = {"H0": 4.0, "H1": 3.0, "H2": 8.0, "H3": 5.0}
NA0_AT = 7.6


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
            if spk in SPK_KEY and SPK_KEY[spk] not in on and not s["vo"]:
                errs.append(f"{s['id']}: {s['line']} 화자 {spk}가 화면에 없음(화자-화면 일치) — 의도면 vo=True")
            if spk in SPK_KEY and s["kind"] == "d" and SPK_KEY[spk] != on[0]:
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


def main():
    lock = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
    rows = {x["tag"]: x for x in lock["lines"]}
    texts = script_texts()
    scenes = {s["id"]: (s["start"], s["end"]) for s in lock["scenes"]}
    main_end = lock["body_end"]
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
                   "lighting": s["light"], "edit_fx": s["fx"], "refs": refs, "subject": s["subject"], "line": s["line"], "vo": s["vo"],
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
    ass = ["[Script Info]", "Title: みすぼらしい老人は、財閥会長だった 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
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
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_beggar_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT, "preset": PRESET,
               "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"], "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_beggar_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, wardrobe, "
                         "props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_beggar_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (Typecast 확정본).",
        "default_voice": "cached-typecast", "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Naration"], "silent_styles": ["Caption", "HookLine", "Title"] + [n + "_c" for n in STYLE_COLOR],
        "output_size": [1920, 1080], "fit": "crop", "scene_durations": durations, "transitions": [0.0] * len(durations),
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d" and s["line"]],
        "omnihuman_prompts": {str(idx[k]): v for k, v in omni_prompts.items()},
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0, "legacy_lipsync": False,
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35, "duck_db": 8, "ambience_prompts": [x["ambience"] for x in sb],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": s, "end": round(main_end, 2) if e is None else e, "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_후크": "0~3.5초 BGM 없음: 저음 드론 + 심장 박동 1회를 PHASE 6 로컬 믹스. H0·H1 화면은 S10r·S10m 재사용(음성 L01·L02는 캐시 줄로 포함). S10 콜드오픈 합류에서 L01을 한 번 더 재생(lock.json replay).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    md = ["# 『みすぼらしい老人は、財閥会長だった』 PHASE 3 샷 리스트 (B안 표준)", "",
          f"> `scripts/build_beggar_phase3.py` 자동 생성(손 수정 금지). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " + ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock['ads']) + ".",
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
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_beggar_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않거나 부딪힘(연기 메모에 의도가 없으면 키프레임·동작 문장을 고친다). 감정 격차(9절)는 샷 표의 장면 순서로 확인.", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 감정·세기·템포 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")


if __name__ == "__main__":
    main()
