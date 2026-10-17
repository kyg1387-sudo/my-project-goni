#!/usr/bin/env python3
"""『月に帰った契約社員』(tsuki-ja) PHASE 3 샷 리스트 Lock 생성기 — B안 자연 연기 표준(제10장·제11장 12) 첫 적용.

선례 build_ashita_phase3.py를 이 작품에 맞춰 옮긴 것. 이 작품에서 달라진 것:
  · 대사 컷(kind d) = 어깨 너머 3/4 립싱크(전경에 듣는 사람 흐린 어깨, 일하는 손, 얼굴 1/3 이상 — 휴대폰 기준 8절)
  · 짧은 대사(A안 절감형)는 듣는 사람 i2v 리액션 위에 목소리(vo=True) — 정지 화자 컷 0
  · 사람 컷은 전부 i2v(motion=), 정지는 일본어 합성 면·무인 정물뿐(estill/ins)
  · 현장음은 장면별 14그룹(7-2절), 사람 컷에도 효과음형만
입력: productions/tsuki-ja/lock.json · 00_script_ja.md · assets/auditions/tsuki-tts/lineNNN.mp3 · PHASE 2 셀(assets/portraits/tsuki-cast/cells/)
출력: scripts/storyboard/tsuki.json · scripts/scenes/tsuki.json · scripts/audio/tsuki.json · subs/tsuki.ass ·
      assets/audio-overrides/tsuki/lineNNN.mp3 · productions/tsuki-ja/07_샷리스트.md · 16_감정일치표.md
사용법: python3 scripts/build_tsuki_phase3.py
"""
import collections, json, os, re, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "tsuki-ja")
SKIT = "tsuki"
FPS = 24; HARD = 1 / FPS; OMNI_MAX = 7.9; LEAD = 0.3; MIN_SHOT = 1.2; STILL_MAX = 6.5; I2V_MAX = 10.0

C = "assets/portraits/tsuki-cast/cells/"
WHO = {
    "HIK": ("Takeuchi Hikaru, a slim Japanese man aged 26, fair skin, gentle oval face, calm dark eyes, short black hair with slightly long bangs, "
            "a small dark mole just below his LEFT eye, no glasses, no earrings, clean-shaven", C + "hikaru-front.png"),
    "WAS": ("Washio, a heavy-set Japanese man aged 59, thick jaw and jowls, greying black hair slicked straight back, thin round GOLD-rimmed glasses, "
            "bushy eyebrows, clean-shaven", C + "washio-front.png"),
    "HIN": ("Hino, a Japanese man aged 46, slightly sunken cheeks, black hair in a neat 7:3 side part, thick straight eyebrows, no glasses, clean-shaven",
            C + "hino-front.png"),
    "SAK": ("Mizutani Sakura, a slim Japanese woman aged 24, soft round earnest face with light natural makeup, straight black chin-length bob with "
            "side-swept bangs, no glasses, small pearl stud earrings (fixed trait from the approved sheet), no name tag", C + "sakura-front.png"),
    "SHI": ("Shinoda, a lean Japanese man aged 52, long calm face with fine lines, short black hair streaked with grey, thin rectangular BLACK "
            "plastic-framed glasses, clean-shaven", C + "shinoda-front.png"),
    "HAR": ("Takeuchi Haru, a small slightly stooped Japanese woman aged 83, deeply wrinkled kind face, white hair in a neat low bun, no glasses, tiny dark stud earrings (fixed trait from the approved sheet)",
            C + "haru-front.png"),
    "STAFF": ("two or three engineers seen only from behind as faceless silhouettes at consoles", None),
}
WARD = {
    "HIK_A": "a plain light-grey cotton work jacket with no logo over a plain white t-shirt, a plain white towel around the neck, dark-grey work trousers",
    "HIK_B": "a plain white shirt with a plain navy cardigan, dark trousers",
    "WAS": "a dark navy double-breasted suit with no pin, a plain white shirt, a plain crimson necktie, a plain gold wristwatch on the LEFT wrist",
    "HIN": "a plain mid-grey business suit, a plain white shirt, a plain blue necktie, a plain white handkerchief in hand",
    "SAK": "a plain navy office vest over a plain white blouse, a plain navy knee-length skirt",
    "SHI": "a plain beige trench coat worn open over a plain charcoal-grey suit, plain white shirt, plain dark-grey necktie",
    "HAR": "a plain dark-indigo cotton work apron over a plain grey long-sleeve work top, plain grey monpe trousers",
}
EXPR = {  # 표정 셀(감정 50% 선반영) — PHASE 2 Kill Gate 합격 셀 이름(불합격 시 재생성 후 경로만 바꾼다)
    ("HIK", "calm"): C + "hikaru-expr1.png", ("HIK", "smile"): C + "hikaru-expr2.png", ("HIK", "firm"): C + "hikaru-expr3.png",
    ("WAS", "smug"): C + "washio-expr1.png", ("WAS", "fury"): C + "washio-expr2.png", ("WAS", "fear"): C + "washio-expr3.png",
    ("HIN", "forced"): C + "hino-expr1.png", ("HIN", "fear"): C + "hino-expr2.png", ("HIN", "tears"): C + "hino-expr3.png",
    ("SAK", "smile"): C + "sakura-expr1.png", ("SAK", "worry"): C + "sakura-expr2.png", ("SAK", "tears"): C + "sakura-expr3.png",
    ("SHI", "calm"): C + "shinoda-expr1.png", ("SHI", "firm"): C + "shinoda-expr2.png", ("SHI", "moved"): C + "shinoda-expr3.png",
    ("HAR", "smile"): C + "haru-expr1.png", ("HAR", "proud"): C + "haru-expr2.png", ("HAR", "listen"): C + "haru-expr3.png",
    ("HIK", "back"): C + "hikaru-fullback.png", ("SAK", "back"): C + "sakura-fullback.png", ("SHI", "back"): C + "shinoda-fullback.png",
    ("WAS", "back"): C + "washio-fullback.png", ("HIN", "back"): C + "hino-fullback.png",
}
LOC = {
    "HQ_MORN": C + "loc-hq-morning.png", "HQ_GATE": C + "loc-hq-gate.png", "HQ_MOON": C + "loc-hq-moon.png", "HQ_DARK": C + "loc-hq-dark.png",
    "YARD_FENCE": C + "loc-yard-fence.png", "YARD_ROW": C + "loc-yard-row.png", "YARD_DAWN": C + "loc-yard-dawn.png", "YARD_HIGH": C + "loc-yard-high.png",
    "DEV_RED": C + "loc-dev-red.png", "DEV_GREEN": C + "loc-dev-green.png", "DEV_DESK": C + "loc-dev-desk.png", "DEV_DOOR": C + "loc-dev-door.png",
    "BOARD_DAY": C + "loc-board-day.png", "BOARD_HEAD": C + "loc-board-head.png", "BOARD_HIGH": C + "loc-board-high.png", "BOARD_NIGHT": C + "loc-board-night.png",
    "BOARD_REV": C + "loc-board-angles-rev.png", "BOARD_BIRD": C + "loc-board-angles-bird.png", "BOARD_LOW": C + "loc-board-angles-low.png", "BOARD_DOOR": C + "loc-board-angles-door.png",
    "EXEC_DAY": C + "loc-exec-day.png", "EXEC_LOW": C + "loc-exec-low.png", "EXEC_NIGHT": C + "loc-exec-night.png", "EXEC_DRAWER": C + "loc-exec-drawer.png",
    "CTRL": C + "loc-ctrl-normal.png", "CTRL_RED": C + "loc-ctrl-red.png", "CTRL_BLACK": C + "loc-ctrl-blackout.png", "CTRL_EMER": C + "loc-ctrl-emergency.png",
    "BAM_PATH": C + "loc-bamboo-path.png", "BAM_VER": C + "loc-bamboo-veranda.png", "BAM_DUSK": C + "loc-bamboo-dusk.png", "BAM_MOON": C + "loc-bamboo-moon.png",
    "BAM_REV": C + "loc-bamboo-angles-rev.png", "BAM_CANOPY": C + "loc-bamboo-angles-canopy.png", "BAM_THRU": C + "loc-bamboo-angles-through.png", "BAM_HIGH": C + "loc-bamboo-angles-high.png",
    "P_TONBO": C + "props-taketonbo.png", "P_ONIGIRI": C + "props-onigiri.png", "P_SEALS": C + "props-seals.png", "P_DOC": C + "props-document.png",
}
PRESET = ("Photorealistic live-action Japanese human drama, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, "
          "restrained Japanese film mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, "
            "signage lettering, posters with writing, documents with writing, screens with text, printed labels, brand logos, watermarks, stamps, "
            "symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, blood, gore, handcuffs, police, earrings")
PLAIN = "All papers, screens, signs, cards and labels are completely blank; no letters, numbers or symbols anywhere in the frame."
TEARS = ("Realistic tears as in a live-action film: reddened eye rims, glossy wet eyes, one or two thin clear tear tracks running naturally down "
         "the cheeks and catching the light, a small tear bead on the lower lashes, slightly reddened nose; no cartoon droplets.")
SWEAT = ("Realistic sweat as in a live-action film: fine tiny beads of perspiration on the forehead, temples and upper lip, a natural oily sheen, "
         "a few damp strands at the hairline; no large cartoon drops.")
GLASSES = {"WAS": "He wears his thin round gold-rimmed glasses.", "SHI": "He wears his thin rectangular black-framed glasses.",
           "HIK": "He wears no glasses.", "HIN": "He wears no glasses.", "SAK": "She wears no glasses.", "HAR": "She wears no glasses."}
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, the face fills at least half of the frame height",
    "ots": "50mm lens, f/2.0, over-the-shoulder three-quarter framing, the listener's blurred shoulder and back of the head in the near foreground edge, the speaker's face at least one third of the frame height",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds, the person's face at least one quarter of the frame height",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective",
}
LIGHT = {
    "hq_morn": "clear morning daylight on glass and concrete, crisp 5600K, soft long shadows", "hq_moon": "night, a huge full moon, cold blue moonlight and warm 3200K sodium lamps, wet pavement reflections",
    "yard": "night substation yard, warm 3200K sodium lamps, a cold blue full-moon rim light separating the subject from the dark, faces readable",
    "dawn": "pale blue dawn 4500K over the yard, thin mist", "dev": "hard cold fluorescent top light 5600K, monitors glowing, faint cyan cast",
    "dev_red": "the office washed in deep red monitor light pulsing, cold fluorescent overhead, faces readable", "dev_green": "dawn, pale daylight from the windows, the video wall glowing calm green",
    "board": "cold fluorescent top light 5600K, high-contrast chiaroscuro from the tall windows, blinds half closed", "board_morn": "clear cold morning light through the tall windows, 5600K, hard shadows",
    "board_night": "night, warm 3200K interior lights, city lights beyond the glass", "exec": "cold 5600K daylight through vertical blinds, strong stripes of light, chiaroscuro",
    "exec_night": "night executive office lit only by a single warm 3200K desk lamp, deep shadows, subtle rim", "ctrl": "cool 5600K monitor glow and ceiling light, crisp and tense",
    "ctrl_red": "every monitor solid red, deep red light on faces, high contrast", "ctrl_black": "blackout, only dim red emergency lamps, mid-tones kept visible, average brightness readable on a phone",
    "bamboo": "soft diffused natural daylight 5000K through bamboo leaves, dappled, a golden rim light", "dusk": "golden dusk 3200K, long shadows between bamboo stalks",
    "moon": "night, cold blue full-moon light over the bamboo, one warm 3200K window glow", "product": "soft even studio light, neutral",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}
SPK_KEY = {"光": "HIK", "鷲尾": "WAS", "日野": "HIN", "さくら": "SAK", "篠田": "SHI", "ハル": "HAR"}


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, act="", vo=False):
    """kind: d(OmniHuman 어깨 너머 3/4 립싱크) / face(사람 i2v, 듣는 사람·손·뒷모습) / empty(무인 i2v) / estill(무인·합성 면 정지) /
    ins(인서트: 손·소품 i2v — motion 있으면 i2v, 없으면 정지) / reuse:<id> / card.
    line = 대본 태그 — 그 줄의 발화가 이 컷에서 시작. vo=True면 화자가 화면 밖(듣는 사람 리액션 위 목소리, L컷)."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc, subject=subject,
                line=line, fx=fx, motion=motion, expr=expr, act=act, vo=vo)


HA_, HB, W, N, K, D, R = "HIK:HIK_A", "HIK:HIK_B", "WAS:WAS", "HIN:HIN", "SAK:SAK", "SHI:SHI", "HAR:HAR"
OB = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, keeps looking "
      "toward the other person at the same three-quarter angle, hands keep doing what they do in the first frame; no exaggerated motion, the same person throughout.")
HOLD = " Head stays at the same angle, never turns toward the camera; only body, hands and breath move. Mouth stays closed, lips still — this person is NOT speaking."
SHOTS = [
    # ① 도입 후크 0:00~0:20 (H0a·H0b·H1 재사용 = 추가 생성 0, H2 1컷 생성)
    S("H0a", "H", "reuse:S18b", "ews", "ctrl_black", "OH", [], None, "Reuse of S18b (monitor wall going dark one panel at a time, overhead). Caption composited."),
    S("H0b", "H", "reuse:S18c", "ecu", "ctrl_black", "EL", [], None, "Reuse of S18c (Hino's hand wiping sweat)."),
    S("H1", "H", "reuse:S14c", "ots", "exec", "LA", [], None, "Reuse of S14c (Washio: 'Trash from the moon, what are you saying!'). Voice = L26 mixed locally."),
    S("H2", "H", "empty", "ms", "moon", "EL", [], "DEV_DESK", "No people. Moonlight through a window falls on an empty office desk; a single hand-made bamboo dragonfly toy lies on the blank desk; a thin curtain at the edge.",
      motion="The curtain sways gently in a night breeze; moonlight shifts slightly; the bamboo dragonfly stays still. No people."),
    S("H3", "H", "card", "ews", "moon", "EL", [], None, "Black title card 『月に帰った契約社員』 with subtitle."),
    # ② 발단·갈등
    S("S01a", "S01", "empty", "ews", "hq_morn", "LA", [], "HQ_MORN", "No people. Low angle on the glass-and-steel headquarters tower of an electric-power company on the Tokyo waterfront at sunrise, blank facade.", line="NA1", fx="pullback",
      motion="Clouds drift slowly across the glass; distant seagulls; no people, no text."),
    S("S01b", "S01", "empty", "ws", "hq_morn", "EL", [], "HQ_GATE", "No people. The empty plaza and blank steel front gate at eye level in cool morning light.", line="NA2", fx="tiltdown",
      motion="A few leaves skitter across the plaza; a flag-less pole; no people."),
    S("S02a", "S02", "empty", "ews", "yard", "EL", [], "YARD_FENCE", "No people. Night substation yard seen through a chain-link fence in the foreground, tall transformers, sodium lamps, a full moon.", line="NA3",
      motion="Moths flicker around the sodium lamp; the fence stays still; no people."),
    S("S02b", "S02", "face", "ms", "yard", "HA", [HA_], "YARD_ROW", "High angle from behind: Hikaru kneels on the concrete in front of a blank grey switchgear cabinet wiping the floor with a wet cloth, a bucket beside him, an old closed laptop on the cabinet; his back to the camera.",
      motion="His hands wipe the floor in slow steady arcs, wring the cloth into the bucket once; his back stays to the camera." + HOLD, expr="back"),
    S("S02c", "S02", "ins", "ecu", "yard", "OH", [HA_], "YARD_ROW", "Insert from above: a young man's hands wringing a grey cloth over a bucket, water dripping, grey work-jacket cuffs.",
      motion="Water drips from the wrung cloth; the hands squeeze once more and set the cloth down."),
    S("S02d", "S02", "face", "cu", "yard", "SIDE", [HA_], "YARD_ROW", "Side close-up of Hikaru's face in profile lit by the sodium lamp and the moon, the white towel at his neck covering his mouth, eyes calm and tired, looking at the closed laptop.",
      motion="He blinks slowly once, breathes, the towel stays over his mouth; the moonlight flickers faintly on his hair." + HOLD, expr="calm"),
    S("S03a", "S03", "face", "ws", "yard", "EL", [K], "YARD_FENCE", "Wide: Sakura in her navy office vest walks along the yard path toward the camera's far side carrying a plain white plastic bag, seen from behind, small in the frame.", line="L01",
      motion="Sakura walks three slow steps away from the camera along the path holding the bag, her back to the camera, hair moving slightly in the night wind.", expr="back", vo=True),
    S("S03b", "S03", "face", "cu", "yard", "EL", [HA_], "YARD_ROW", "Close-up of Hikaru looking up from the floor toward the plastic bag held out to him, eyes widening a little, the towel slipping from his mouth, a shy grateful look.",
      motion="His eyes widen slightly and soften, a small breath, a tiny nod; head stays within 10 degrees.", expr="smile"),
    S("S03c", "S03", "d", "ots", "yard", "EL", [HA_, K], "YARD_ROW", "Over Sakura's blurred shoulder (her bob hair, right foreground): Hikaru standing by the cabinet at three-quarter angle, wiping his hands on the towel, speaking to her with shy gratitude, face lit by the lamp.", line="L02",
      act="Hikaru speaks shyly and gratefully, lowering his head a little on 'sumimasen', wiping his hands with the towel, a small shy smile. Replying to Sakura who just handed him the rice balls, glancing at her." + OB, expr="smile"),
    S("S03d", "S03", "d", "ots", "yard", "EL", [K, HA_], "YARD_ROW", "Reverse over Hikaru's blurred shoulder (grey jacket, left foreground): Sakura at three-quarter angle glancing sideways at the closed laptop with curiosity, holding the bag, head tilted slightly.", line="L03",
      act="Sakura asks with curiosity, a small playful tilt of the head, glancing at the laptop then back at him. Asking Hikaru what he keeps writing." + OB, expr="smile"),
    S("S03e", "S03", "d", "ots", "yard", "EL", [HA_, K], "YARD_ROW", "Over Sakura's blurred shoulder (right foreground): Hikaru at three-quarter angle, drying his hands with the towel, a faint smile, eyes lifting to the moon for a moment and back to her.", line="L04",
      act="Hikaru answers softly with a faint smile, his hands still drying on the towel, eyes lifting briefly toward the sky on 'tsuki no ko' then back to Sakura. Answering her question gently." + OB, expr="smile"),
    S("S03f", "S03", "d", "cu", "yard", "EL", [K], "YARD_ROW", "Close-up of Sakura, three-quarter toward Hikaru, puzzled and curious, eyebrows up, the bag held against her chest.", line="L05",
      act="Sakura repeats the words with a puzzled little smile, head tilting, eyes on Hikaru." + OB, expr="smile"),
    S("S03g", "S03", "d", "ots", "yard", "EL", [HA_, K], "YARD_ROW", "Over Sakura's blurred shoulder (right foreground): Hikaru at three-quarter angle looking out at the yard then turning his eyes to her, calm and matter-of-fact, the towel in his hands.", line="L06",
      act="Hikaru speaks calmly, matter-of-fact, no self-pity, looking out at the yard then turning his eyes to Sakura on 'akanbou no toki ni', a small shrug. Confiding to Sakura." + OB, expr="calm"),
    S("S03h", "S03", "face", "cu", "yard", "EL", [K], "YARD_ROW", "Close-up of Sakura, breath caught, lips parting slightly, eyes on him, moved and surprised.",
      motion="Her breath catches, a slow blink, her fingers tighten on the plastic bag; she does not speak." + HOLD, expr="worry"),
    S("S03i", "S03", "face", "ews", "yard", "LA", [HA_, K], "YARD_HIGH", "Low wide: the two small figures standing by the cabinets under the huge full moon, seen from behind as silhouettes.",
      motion="Thin clouds pass over the moon; the two figures stay still, backs to camera.", expr="back"),
    S("S04a", "S04", "estill", "ecu", "product", "EL", [], None, "An old faded photo print in a plain wooden frame: in front of a bamboo-craft workshop, an elderly Japanese couple in work aprons and a small boy of about five holding a bamboo dragonfly, warm faded colors, slightly blurred, no text.", line="NA5", fx="pushin"),
    S("S04aa", "S04", "ins", "cu", "yard", "HA", [HA_], "YARD_ROW", "Insert from above: the small framed photo resting on a young man's open palms, grey jacket cuffs, lamp light, no face.",
      motion="The palms tilt the photo slightly toward the light; the hands hold still."),
    S("S04b", "S04", "ins", "ecu", "yard", "EL", [HA_], "YARD_ROW", "Insert: Hikaru's hands holding the small framed photo, a thumb brushing the glass, grey jacket cuffs, lamp light.", line="NA6",
      motion="His thumb slowly brushes dust from the glass of the photo; the hands hold still."),
    S("S05a", "S05", "empty", "ws", "dev_red", "EL", [], "DEV_RED", "No people. The development office at night seen past a glass partition in the foreground: the huge video wall glowing solid red, desks empty.", line="NA7",
      motion="The red light on the video wall pulses slowly; nothing else moves; no people."),
    S("S05b", "S05", "face", "ms", "dev_red", "HA", [N], "DEV_RED", "High angle: Hino standing in front of the red video wall wiping his temple with a white handkerchief, shoulders tense, seen from the side-back so his mouth is hidden.", line="L07", vo=True,
      motion="He dabs his temple with the handkerchief twice, shoulders rising with a tense breath; back stays to camera." + HOLD, expr="back"),
    S("S05c", "S05", "d", "ots", "dev_red", "EL", [N, "STAFF"], "DEV_RED", "Over a seated engineer's blurred shoulder (foreground left, back of head): Hino standing at three-quarter angle, handkerchief clutched, red light on his face, frightened and urgent.", line="L08",
      act="Hino speaks low and frightened, clutching the handkerchief, a glance at the red wall and back to the engineer. Warning his subordinate what is at stake." + OB, expr="fear"),
    S("S05d", "S05", "ins", "ecu", "dev_red", "EL", [N], "DEV_DESK", "Insert: beads of sweat on a man's temple reflecting red monitor light, a white handkerchief rising to wipe them, no full face.",
      motion="The handkerchief wipes the temple slowly; red light pulses on the skin."),
    S("S06a", "S06", "face", "ews", "dev_green", "HA", [HA_], "DEV_GREEN", "High wide at dawn: the video wall now glowing calm green; a small figure, Hikaru in his grey work jacket, sits on the edge of a chair in front of it holding a grey cloth, seen from behind.",
      motion="Hikaru slowly starts to rise from the chair, back to camera; the green light holds steady." + HOLD, expr="back"),
    S("S06b", "S06", "face", "ms", "dev_green", "EL", [N], "DEV_DOOR", "Medium: Hino stands in the office doorway backlit by the corridor light, a hand on the door frame, staring in disbelief, mouth closed.", line="L09", vo=False,
      motion="Hino's hand grips the door frame, he leans in slightly, eyes narrowing in disbelief, mouth closed; head within 10 degrees.", expr="forced"),
    S("S06c", "S06", "face", "cu", "dev_green", "EL", [HA_], "DEV_GREEN", "Close-up of Hikaru caught, hiding the cloth behind his back, head bowed halfway, eyes up toward the door, apologetic.",
      motion="He hides the cloth behind him, bows his head halfway, a nervous swallow, then his eyes lift to the door." + HOLD, expr="calm"),
    S("S06d", "S06", "d", "ots", "dev_green", "EL", [HA_, N], "DEV_GREEN", "Over Hino's blurred shoulder (grey suit, left foreground): Hikaru at three-quarter angle, head slightly bowed, apologizing quietly, the cloth behind his back.", line="L10",
      act="Hikaru apologizes quietly after a short hesitation, head bowed halfway, eyes lifting to Hino, a small apologetic smile at the end. Answering Hino's question honestly." + OB, expr="calm"),
    S("S06e", "S06", "d", "ots", "dev_green", "EL", [N, HA_], "DEV_GREEN", "Reverse over Hikaru's blurred shoulder (right foreground): Hino at three-quarter angle pointing at the green video wall with the handkerchief hand, probing, eyes on Hikaru.", line="L11",
      act="Hino asks tersely, pointing at the wall with the hand holding the handkerchief, then fixes his eyes on Hikaru, probing. Asking the program's name." + OB, expr="forced"),
    S("S06f", "S06", "d", "cu", "dev_green", "EL", [HA_], "DEV_GREEN", "Close-up of Hikaru at three-quarter angle, calm, answering with the single word, eyes steady, dawn light on his face.", line="L12",
      act="Hikaru answers simply and clearly with the one word, a calm steady gaze, a tiny nod. Answering Hino." + OB, expr="calm"),
    S("S06g", "S06", "face", "cu", "dev_green", "EL", [N], "DEV_DOOR", "Close-up of Hino in the doorway, swallowing, eyes flicking to the green wall and back, a calculating look forming, handkerchief tightening in his fist.",
      motion="He swallows, eyes flick to the wall and back, the fist tightens on the handkerchief; a slow calculating blink." + HOLD, expr="forced"),
    S("S07a", "S07", "face", "ews", "board", "LA", [W], "BOARD_HEAD", "Low angle from table level toward the head seat: Washio seated at the head of the long glossy table, gold glasses catching the light, imposing, hands folded.", line="L13", vo=True,
      motion="Washio's fingers slowly interlace, his chin lifts a degree, light moves on the glasses; he stays seated and still otherwise." + HOLD, expr="smug"),
    S("S07b", "S07", "d", "ots", "board", "EL", [N, D], "BOARD_DAY", "Over Shinoda's blurred shoulder (beige coat, right foreground): Hino standing at three-quarter angle beside a blank grey screen holding a plain remote, presenting with forced confidence.", line="L13b" if False else None,
      act="", expr="forced",
      motion="Hino gestures once toward the blank screen with the remote and nods to himself, a forced confident smile; head stays at the same angle." + HOLD),
    S("S07c", "S07", "d", "ots", "board", "EL", [D, N], "BOARD_REV", "Reverse over Hino's blurred shoulder (left foreground): Shinoda seated at three-quarter angle turning a page in a document folder, looking up impressed, black-framed glasses.", line="L14",
      act="Shinoda speaks with genuine admiration, eyebrows lifting, closing the folder gently, looking at Hino then at Washio. Praising the system." + OB, expr="calm"),
    S("S07d", "S07", "d", "ots", "board", "LA", [W, D], "BOARD_HEAD", "Over Shinoda's blurred shoulder (right foreground), slightly low angle: Washio at the head seat at three-quarter angle lifting a white teacup, a satisfied smile, gold glasses.", line="L15",
      act="Washio speaks with proud satisfaction, lifting the teacup slowly, a small self-satisfied nod, a smile at one corner. Replying to Shinoda's praise, taking the credit." + OB, expr="smug"),
    S("S07e", "S07", "ins", "ecu", "board", "EL", [W], "BOARD_HEAD", "Insert: a white teacup set down on its saucer on the glossy black table, a gold wristwatch on the wrist.", line="NA8",
      motion="The cup is set down slowly, a faint ripple in the tea, the hand withdraws."),
    S("S07f", "S07", "estill", "ws", "board", "EL", [], "BOARD_DAY", "No people. The far end of the long boardroom table and one empty black chair, cold light.", fx="pushin"),
    S("S08a", "S08", "face", "ws", "dev", "EL", [N, HA_], "DEV_DESK", "Through a glass partition in the foreground: Hino seated at his desk and Hikaru standing before it in his grey work jacket, both seen from the side, a single sheet of paper on the desk between them.",
      motion="Hino slides the sheet an inch forward with two fingers; Hikaru stays standing still; the glass reflection shifts slightly." + HOLD, expr="back"),
    S("S08b", "S08", "estill", "ecu", "dev", "OH", [N], "P_DOC", "Insert from above: a blank white document with an empty red-ringed stamp box slid across a desk by a man's hand with a pen (Japanese title composited later).", fx="pushin"),
    S("S08c", "S08", "d", "ots", "dev", "EL", [N, HA_], "DEV_DESK", "Over Hikaru's blurred shoulder (grey jacket, right foreground): Hino seated at three-quarter angle holding out a pen with a too-friendly forced smile, the handkerchief under his other hand.", line="L16",
      act="Hino speaks with a fake friendly warmth, holding out the pen and wagging it a little, a forced smile, eyes watching Hikaru's reaction. Tempting Hikaru with a permanent job." + OB, expr="forced"),
    S("S08d", "S08", "face", "cu", "dev", "EL", [HA_], "DEV_DESK", "Close-up of Hikaru looking down at the pen, then the paper, then up, quiet and unmoving, not taking the pen.",
      motion="His eyes move from the pen to the paper to Hino's face, one slow breath; his hands stay at his sides." + HOLD, expr="calm"),
    S("S08e", "S08", "d", "ots", "dev", "EL", [HA_, N], "DEV_DESK", "Reverse over Hino's blurred shoulder (left foreground): Hikaru standing at three-quarter angle, eyes on the document, speaking quietly, hands at his sides not taking the pen.", line="L17",
      act="Hikaru speaks quietly and plainly, eyes on the document, not reaching for the pen, a small pause before 'go-nen kakete'. Explaining to Hino where the program came from." + OB, expr="calm"),
    S("S08f", "S08", "face", "cu", "dev", "HA", [N], "DEV_DESK", "Close-up of Hino, the hand holding the pen freezing in mid-air, the forced smile stiffening.",
      motion="The pen hand freezes, the smile stiffens, a slow blink, the other hand reaches for the handkerchief." + HOLD, expr="forced"),
    S("S08g", "S08", "d", "ots", "dev", "EL", [HA_, N], "DEV_DESK", "Over Hino's blurred shoulder (left foreground): Hikaru lifts his head and meets Hino's eyes, calm and without a tremor, refusing politely, hands at his sides.", line="L18",
      act="Hikaru lifts his head and meets Hino's eyes, takes a small breath before 'sumimasen', then refuses calmly and politely with no tremor, a slight bow at the end. Answering Hino's demand directly." + OB, expr="firm"),
    S("S08h", "S08", "face", "cu", "dev", "EL", [N], "DEV_DESK", "Close-up of Hino wiping his neck with the handkerchief, eyes dropping away, jaw working.",
      motion="He wipes his neck slowly with the handkerchief, eyes dropping to the desk, jaw tightening." + HOLD, expr="fear"),
    S("S08i", "S08", "estill", "ws", "dev", "HA", [], "DEV_DESK", "No people. High angle of the desk: the blank document and the pen lying between two empty places.", fx="pushin"),
    S("S09a", "S09", "ins", "ecu", "exec", "EL", [W], "EXEC_DAY", "Insert: thin round gold-rimmed glasses being slowly removed by a heavy hand, striped blind light across them, no full face.",
      motion="The hand slowly removes the glasses and folds them; light stripes move on the lenses."),
    S("S09b", "S09", "d", "ots", "exec", "LA", [W, N], "EXEC_LOW", "Over Hino's blurred shoulder (left foreground), slightly low angle: Washio behind his desk at three-quarter angle, glasses in hand, eyes narrowed, speaking low with contempt, blind stripes on his face.", line="L18a",
      act="Washio speaks low and contemptuous, glasses in hand, eyes narrowed, a scoff on 'joudan ja nai'. Reacting to Hino's report about the contract worker." + OB, expr="smug"),
    S("S09ba", "S09", "face", "cu", "exec", "EL", [N], "EXEC_DAY", "Close-up of Hino listening with his head bowed slightly, eyes darting, the handkerchief at his lips.",
      motion="His eyes dart once, the handkerchief presses to his lips, a shallow breath." + HOLD, expr="fear"),
    S("S09c", "S09", "d", "ots", "exec", "EL", [W, N], "EXEC_DAY", "Over Hino's blurred shoulder (left foreground): Washio leaning forward, fingers tapping the desk, a greedy half-smile at one corner, glasses back on, striped light.", line="L18b",
      act="Washio speaks with greed held at half, fingers tapping the desk on each demand, a half-smile at one corner, 'ore no mono da' slow and savored. Giving Hino his orders." + OB, expr="smug"),
    S("S09d", "S09", "face", "cu", "exec", "EL", [N], "EXEC_DAY", "Close-up of Hino swallowing and nodding once, eyes down, handkerchief in his fist.", line="NA9",
      motion="He swallows, nods once slowly, eyes down, the fist tightening on the handkerchief." + HOLD, expr="fear"),
    S("S09e", "S09", "face", "ms", "exec", "LA", [W], "EXEC_DAY", "Low angle: Washio standing at the window with his back to the camera, a dark silhouette against the striped blinds, hands clasped behind him.", line="NA10",
      motion="His clasped hands tighten behind his back, shoulders rise with a slow breath; he stays facing the window." + HOLD, expr="back"),
    S("S09f", "S09", "ins", "ecu", "exec", "EL", [W], "EXEC_DAY", "Insert: a thick finger tapping slowly on a dark-wood desk, a gold wristwatch, striped light.",
      motion="The finger taps four times slowly, then stops flat on the desk."),
    # ③ 전개·위기
    S("S10a", "S10", "face", "ws", "exec", "LA", [HA_, W], "EXEC_LOW", "Low wide: Hikaru in his grey work jacket stands before the big desk seen from behind; Washio seated beyond, a stack of papers under his hand.", line="NA11",
      motion="Washio's hand lifts the top sheet; Hikaru stands perfectly still, back to camera." + HOLD, expr="back"),
    S("S10b", "S10", "ins", "ecu", "exec", "OH", [W], "EXEC_DAY", "Insert from above: a blank sheet of paper slapped down onto the desk by a heavy hand, a gold watch, striped light.", fx="handheld",
      motion="The hand slaps the sheet down hard and withdraws; the paper settles."),
    S("S10c", "S10", "ins", "ecu", "exec", "EL", [W], "EXEC_DAY", "Insert: a thick finger stabbing down onto a blank sheet, crumpling its corner.", fx="handheld",
      motion="The finger stabs the paper twice, the corner crumples."),
    S("S10d", "S10", "face", "cu", "exec", "HA", [HA_], "EXEC_DAY", "High-angle close-up of Hikaru's face looking down at the papers, eyes lowered, calm, lips closed.",
      motion="His eyes lower to the papers, a slow breath, no other movement." + HOLD, expr="calm"),
    S("S10e", "S10", "d", "ots", "exec", "LA", [W, HA_], "EXEC_LOW", "Over Hikaru's blurred shoulder (grey jacket, right foreground), low angle: Washio at three-quarter angle jabbing a finger at each sheet as he lists the demands, jaw set, blind stripes.", line="L19",
      act="Washio lists the demands fast and hard, jabbing a finger at a sheet on each item, jaw set, not pausing for breath. Dictating impossible tasks to Hikaru." + OB, expr="fury"),
    S("S10f", "S10", "face", "cu", "exec", "EL", [HA_], "EXEC_DAY", "Close-up of Hikaru's eyes lifting slowly from the papers to the man, calm, a single blink.",
      motion="His eyes lift slowly from the papers, a single blink, no other movement." + HOLD, expr="calm"),
    S("S10g", "S10", "d", "ots", "exec", "LA", [W, HA_], "EXEC_LOW", "Over Hikaru's blurred shoulder (right foreground): Washio sliding the last sheet forward with two fingers, a mocking smile spreading, leaning back.", line="L20",
      act="Washio slides the last sheet forward slowly, a mocking smile spreading, leaning back in the chair, savoring 'ima no mama da'. Delivering the fifth demand to Hikaru with a sneer." + OB, expr="smug"),
    S("S10h", "S10", "ins", "ecu", "exec", "EL", [W], "EXEC_DAY", "Insert: the corner of a mouth lifting in a sneer beneath gold glasses, extreme close-up, striped light, no full face.",
      motion="The mouth corner lifts slowly into a sneer and holds."),
    S("S10i", "S10", "d", "ots", "exec", "EL", [HA_, W], "EXEC_DAY", "Over Washio's blurred shoulder (navy suit, left foreground): Hikaru at three-quarter angle gathering the five sheets from the desk, calm face, answering with a single word, eye level.", line="L21",
      act="Hikaru gathers the five sheets calmly, looks at Washio, answers with quiet acceptance and no resentment, a small bow of the head. Accepting the demands." + OB, expr="calm"),
    S("S10j", "S10", "face", "ws", "exec", "HA", [HA_], "EXEC_DAY", "High wide: Hikaru walks away from the desk toward the door carrying the sheets, seen from behind, small in the striped light.",
      motion="He walks three slow steps toward the door, back to the camera, the sheets held against his chest.", expr="back"),
    S("S11a", "S11", "ins", "ecu", "dev", "EL", [HA_], "DEV_DESK", "Insert: a young man's hands typing fast on a keyboard at night, a monitor glow with abstract blue diagrams and no text, grey jacket cuffs.", line="NA12",
      motion="The hands type steadily; the monitor light flickers faintly."),
    S("S11b", "S11", "face", "ms", "dev", "SIDE", [HA_, "STAFF"], "DEV_DESK", "Side medium: Hikaru standing beside a seated engineer (back of head only) pointing at a monitor with abstract diagrams, his face in profile turned toward the screen, mouth hidden by the angle.",
      motion="Hikaru points at the screen and traces a line with his finger, the engineer nods; Hikaru's head stays in profile." + HOLD, expr="back"),
    S("S11c", "S11", "ins", "ecu", "dawn", "OH", [HA_], "YARD_DAWN", "Insert from above at dawn: the hands wring a grey cloth over the bucket in pale blue light.",
      motion="Water drips from the cloth; the hands wring once more slowly."),
    S("S11d", "S11", "empty", "ews", "dawn", "LA", [], "YARD_DAWN", "No people. The substation yard at first light, pale blue sky, thin mist over the transformers.",
      motion="Mist drifts slowly; the sky brightens a little; no people.", fx="dissolve"),
    S("S12a", "S12", "face", "ms", "yard", "EL", [K], "YARD_FENCE", "Medium past a transformer edge in the foreground: Sakura approaching along the yard path with the plastic bag, seen from the side-back.", line="L22", vo=True,
      motion="She walks two slow steps along the path with the bag, her back to the camera." + HOLD, expr="back"),
    S("S12b", "S12", "d", "ots", "yard", "EL", [K, HA_], "YARD_ROW", "Over Hikaru's blurred shoulder (right foreground): Sakura at three-quarter angle holding out the bag, worried, eyebrows drawn together, lamp light.", line=None,
      act="", expr="worry", motion="Sakura holds the bag out a little further, eyebrows drawn together, a worried breath; head stays at the same angle." + HOLD),
    S("S12c", "S12", "face", "cu", "yard", "EL", [HA_], "YARD_ROW", "Close-up of Hikaru's tired face, dark circles under his eyes, the cloth still in his hands, looking at her with a small weary smile.",
      motion="He keeps wringing the cloth slowly, a weary smile forming, a slow blink." + HOLD, expr="smile"),
    S("S12d", "S12", "d", "ots", "yard", "EL", [HA_, K], "YARD_ROW", "Over Sakura's blurred shoulder (left foreground): Hikaru at three-quarter angle taking the rice-ball bag with one hand, a small weary smile, eyes lifting to the moon on the last words.", line="L23",
      act="Hikaru takes the bag with a small weary smile, says it is fine, and on 'tsuki ga mitemasu kara' his eyes lift to the moon for a moment and come back to her. Reassuring Sakura gently." + OB, expr="smile"),
    S("S12e", "S12", "d", "cu", "yard", "LA", [K], "YARD_ROW", "Slightly low close-up of Sakura looking up at him, puzzled, repeating the word, the empty hand half raised.", line="L24",
      act="Sakura repeats the word softly with a puzzled frown, looking up at Hikaru." + OB, expr="worry"),
    S("S12f", "S12", "empty", "ews", "yard", "LA", [], "YARD_HIGH", "No people. The full moon above the dark transformers, thin clouds, the yard lamps below.",
      motion="Thin clouds drift across the moon slowly; no people."),
    S("S13a", "S13", "face", "ws", "exec_night", "EL", [W, N], "EXEC_NIGHT", "Wide night office: Washio stands at the window with his back to the camera; Hino seated at the desk under the single lamp, bent over a drawer, both backs to the camera.", line="NA13",
      motion="Hino's shoulders shift as he reaches into the drawer; Washio at the window stays motionless; the lamp flickers faintly." + HOLD, expr="back"),
    S("S13b", "S13", "ins", "ecu", "exec_night", "EL", [N], "EXEC_DRAWER", "Insert: a drawer sliding open under lamp light revealing a small cheap round plastic seal and a red ink pad, a man's hand reaching in.",
      motion="The drawer slides open; the hand lifts the small seal out slowly."),
    S("S13c", "S13", "ins", "ecu", "exec_night", "OH", [N], "P_DOC", "Insert from above: the small plastic seal pressed down into the empty red-ringed box of a blank document, the hand trembling slightly, lamp light.", line="NA14", fx="dutch5",
      motion="The hand presses the seal down firmly, holds, trembles slightly, lifts; a red mark remains."),
    S("S13d", "S13", "ins", "cu", "exec_night", "EL", [N], "EXEC_NIGHT", "Insert: a man's hand setting the seal down beside the stamped document, fingers trembling, a white handkerchief nearby.",
      motion="The fingers tremble as they set the seal down and withdraw."),
    S("S13e", "S13", "face", "ms", "exec_night", "LA", [W], "EXEC_NIGHT", "Low angle: Washio's broad back in silhouette against the night window, city lights beyond, hands clasped behind him.",
      motion="City lights shimmer; his clasped hands squeeze once; he stays facing the window." + HOLD, expr="back"),
    S("S14a", "S14", "face", "ws", "exec", "LA", [HA_, W, N], "EXEC_LOW", "Low wide morning: Hikaru in his grey work jacket stands before the desk with his back to the camera; Washio seated beyond waving a sheet of paper; Hino standing behind him.", line="L25", vo=True,
      motion="Washio waves the sheet once; Hino dabs his brow; Hikaru stands still, back to camera." + HOLD, expr="back"),
    S("S14b", "S14", "face", "cu", "exec", "EL", [HA_], "EXEC_DAY", "Close-up of Hikaru not looking at the waved paper, eyes steady on the man, calm.",
      motion="His eyes stay steady, a slow breath, no other movement." + HOLD, expr="calm"),
    S("S14c", "S14", "d", "ots", "exec", "LA", [W, HA_], "EXEC_LOW", "Over Hikaru's blurred shoulder (right foreground), low angle: Washio half-rising, one fist on the desk, face red with fury behind the gold glasses, brow knotted, lips closed between words.", line="L26", fx="handheld",
      act="Washio explodes in fury, slamming his fist on the desk as he starts, half-rising, veins at the temple, brow knotted, spitting 'tsuki kara kita gomi'. Shouting at Hikaru across the desk." + OB, expr="fury"),
    S("S14d", "S14", "face", "cu", "exec", "EL", [HA_], "EXEC_DAY", "Close-up of Hikaru, shoulders flinching slightly at the shout but eyes not leaving the man, calm.",
      motion="His shoulders flinch once at the shout, then settle; his eyes do not leave the man; a slow breath." + HOLD, expr="calm"),
    S("S14e", "S14", "d", "ots", "exec", "LA", [W, HA_], "EXEC_LOW", "Over Hikaru's blurred shoulder (right foreground): Washio leaning back in the leather chair with a sneer, gold glasses, dismissing him with a flick of the hand.", line="L27",
      act="Washio leans back with a cruel sneer, a lazy flick of the hand on 'kaere', enjoying himself. Firing Hikaru with contempt." + OB, expr="smug"),
    S("S14f", "S14", "face", "cu", "exec", "EL", [N], "EXEC_DAY", "Close-up of Hino behind, dabbing sweat with the handkerchief, eyes flicking between the two, uneasy.",
      motion="He dabs his temple, eyes flick to Washio and back, a nervous swallow." + HOLD, expr="fear"),
    S("S14g", "S14", "d", "ots", "exec", "EL", [HA_, W], "EXEC_DAY", "Over Washio's blurred shoulder (navy suit, left foreground): Hikaru at three-quarter angle, after a silence, speaking quietly, eyes on the man, hands at his sides.", line="L28",
      act="Hikaru waits a beat in silence, then speaks quietly with a small nod on 'hai', eyes steady, no fear. Accepting the dismissal, then asking for one thing." + OB, expr="calm"),
    S("S14ga", "S14", "face", "cu", "exec", "LA", [W], "EXEC_LOW", "Low close-up of Washio frowning at the words 'hitotsu dake', gold glasses, lips closed.",
      motion="His frown deepens, the head tilts a degree, lips stay closed; a hard breath through the nose." + HOLD, expr="smug"),
    S("S14h", "S14", "d", "ots", "exec", "LA", [HA_, W], "EXEC_LOW", "Over Washio's blurred shoulder (left foreground): Hikaru looking Washio straight in the eye, speaking clearly word by word, calm authority.", line="L29",
      act="Hikaru speaks clearly, word by word, looking Washio in the eye, a slight emphasis and a pause on 'juu-ni-jou', no tremor. Reminding Washio of the contract clause." + OB, expr="firm"),
    S("S14i", "S14", "face", "cu", "exec", "EL", [W], "EXEC_DAY", "Close-up of Washio pushing his gold glasses up with one finger, a flicker of unease behind the arrogance.",
      motion="One finger pushes the glasses up; the eyes flicker once with unease then harden." + HOLD, expr="smug"),
    S("S14j", "S14", "d", "ots", "exec", "EL", [N, HA_], "EXEC_DAY", "Over Hikaru's blurred shoulder (right foreground): Hino at three-quarter angle folding the handkerchief with a scoff, dismissive, chin up.", line="L30",
      act="Hino scoffs, folding the handkerchief, chin up, dismissive on 'dete ike'. Brushing off Hikaru's warning." + OB, expr="forced"),
    S("S14k", "S14", "face", "ews", "exec", "HA", [HA_], "EXEC_DAY", "High wide: Hikaru turns and walks toward the door, seen from behind, the two men blurred beyond the desk.",
      motion="He turns his shoulders away and walks two slow steps toward the door, back to the camera.", expr="back"),
    S("S15a", "S15", "empty", "ews", "hq_moon", "LA", [], "HQ_MOON", "No people. The blank front gate of the headquarters at night under a huge full moon, wet pavement reflecting the lamps.",
      motion="Thin clouds drift past the moon; a puddle ripples in the wind; no people."),
    S("S15b", "S15", "face", "ms", "hq_moon", "SIDE", [HA_], "HQ_MOON", "Medium from behind: Hikaru walks slowly out through the gate carrying a single cardboard box, moonlight on his back.",
      motion="He walks three slow steps away from the camera carrying the box; his back stays to the camera.", expr="back"),
    S("S15c", "S15", "face", "ms", "hq_moon", "EL", [K], "HQ_GATE", "Medium: Sakura runs out through the gate toward the camera's far side in her office vest, seen from behind, hair flying, one hand reaching forward.", line="L31", vo=True,
      motion="She runs three quick steps away from the camera, hair flying, one hand reaching out; her back stays to the camera.", expr="back"),
    S("S15f", "S15", "ins", "ecu", "hq_moon", "EL", [HA_], "P_TONBO", "Insert: a hand takes a small hand-made bamboo dragonfly toy from a jacket pocket, moonlight on the pale bamboo.",
      motion="The hand draws the bamboo dragonfly out of the pocket and holds it out."),
    S("S15g", "S15", "d", "ots", "hq_moon", "EL", [HA_, K], "HQ_MOON", "Over Sakura's blurred shoulder (left foreground): Hikaru at three-quarter angle holding out the bamboo dragonfly, the box under his other arm, a warm quiet smile, moonlight.", line="L32",
      act="Hikaru holds out the bamboo dragonfly with a warm quiet smile, a small bow of the head on 'arigatou gozaimashita'. Saying goodbye to Sakura, thanking her for the rice balls." + OB, expr="smile"),
    S("S15h", "S15", "face", "cu", "hq_moon", "EL", [K], "HQ_MOON", "Close-up of Sakura taking the bamboo dragonfly, tears welling realistically, lips pressed.",
      motion="Her fingers close around the toy, tears well and one spills, her lips press together." + HOLD, expr="tears"),
    S("S15i", "S15", "d", "ots", "hq_moon", "EL", [K, HA_], "HQ_MOON", "Over Hikaru's blurred shoulder (right foreground): Sakura at three-quarter angle, the dragonfly clutched to her chest, tears on her cheeks, voice breaking.", line="L33",
      act="Sakura speaks through tears, voice breaking on 'zurui desu yo', clutching the bamboo dragonfly to her chest, looking at him. Protesting his goodbye." + OB, expr="tears"),
    S("S15j", "S15", "ins", "ecu", "hq_moon", "EL", [K], "P_TONBO", "Insert: the bamboo dragonfly held tight in a young woman's hand against a navy vest, moonlight.",
      motion="The fingers tighten around the toy; the hand trembles slightly."),
    S("S15k", "S15", "face", "ews", "hq_moon", "LA", [HA_], "HQ_MOON", "Low wide: the small figure of Hikaru walking away under the huge full moon with the box, seen from far behind.", line="NA15",
      motion="The small figure walks slowly away; clouds pass the moon.", expr="back"),
    S("S16a", "S16", "empty", "ws", "board_night", "EL", [], "BOARD_NIGHT", "No people. The boardroom at night seen through the window glass from outside, city lights reflected, two glasses on the table.",
      motion="City lights shimmer in the reflection; no people."),
    S("S16b", "S16", "ins", "ecu", "board_night", "EL", [W, N], "BOARD_NIGHT", "Insert: two whisky glasses clinking together over the glossy table, ice, warm light, a gold watch on one wrist.", line="L34", vo=True,
      motion="The glasses clink once and part; ice turns in the whisky."),
    S("S16c", "S16", "d", "ots", "board_night", "EL", [W, N], "BOARD_NIGHT", "Over Hino's blurred shoulder (left foreground): Washio at three-quarter angle raising his glass with a broad laugh, gold glasses, warm light.", line=None,
      act="", expr="smug", motion="Washio raises the glass higher with a broad silent laugh, shoulders shaking once; head stays at the same angle." + HOLD),
    S("S16d", "S16", "d", "ots", "board_night", "EL", [N, W], "BOARD_NIGHT", "Reverse over Washio's blurred shoulder (right foreground): Hino at three-quarter angle holding his glass with a stiff forced smile, eyes flickering away.", line="L35",
      act="Hino reports with a stiff forced smile, eyes flickering away and back, the glass held still, hiding his unease. Reassuring Washio about the key." + OB, expr="forced"),
    S("S16e", "S16", "ins", "cu", "board_night", "HA", [], "BOARD_NIGHT", "Insert: ice slowly melting in a whisky glass on the glossy table, warm light, no people.", line="NA16",
      motion="The ice turns slowly and melts; a drop runs down the glass."),
    S("S16ba", "S16b", "estill", "ecu", "dev_red", "EL", [], "DEV_RED", "A blank dark monitor corner (red countdown numerals composited later), red glow.", fx="handheld"),
    S("S16bb", "S16b", "estill", "ms", "dev_red", "HA", [], "DEV_RED", "A blank red-pulsing monitor panel (Japanese 'authentication failed' composited later).", fx="pushin"),
    S("S16bc", "S16b", "face", "ms", "dev_red", "LA", [W], "DEV_DOOR", "Low angle: Washio bursts in through the office doorway, coat flaring, seen from the side-back, red light beyond.", fx="handheld",
      motion="Washio strides one step in through the doorway, coat flaring; his face stays turned away." + HOLD, expr="back"),
    S("S16bd", "S16b", "d", "ots", "dev_red", "LA", [W, N], "DEV_RED", "Over Hino's blurred shoulder (right foreground), low angle: Washio both hands planted on the desk, leaning in, eyes bloodshot with fear-driven fury, red light, gold glasses.", line="L35a", fx="handheld",
      act="Washio shouts with fear-driven fury, both hands planted on the desk, leaning in, eyes bloodshot, 'ashita made ni' spat out. Screaming at Hino." + OB, expr="fury"),
    S("S16be", "S16b", "face", "cu", "dev_red", "EL", [N], "DEV_RED", "Close-up of Hino with a smartphone pressed to his ear, pale, the handkerchief in his other hand, red light.",
      motion="He presses the phone closer, his face pales, his lips part; the handkerchief hand trembles." + HOLD, expr="fear"),
    S("S16bf", "S16b", "d", "ots", "dev_red", "EL", [N, W], "DEV_RED", "Over Washio's blurred shoulder (left foreground): Hino at three-quarter angle, phone at his ear, trembling as he reports, red light.", line="L35b",
      act="Hino reports in a trembling voice, phone still at his ear, eyes wide, the handkerchief hand shaking. Telling Washio the number is dead." + OB, expr="fear"),
    S("S16bg", "S16b", "face", "cu", "dev_red", "EL", [W], "DEV_RED", "Extreme close-up of Washio's eyes behind the gold glasses, the first flicker of real fear, red light.",
      motion="His eyes waver for the first time, a slow swallow, the pupils shifting; no other movement." + HOLD, expr="fear"),
    S("S16bh", "S16b", "face", "ws", "dev_red", "HA", ["STAFF"], "DEV_RED", "High wide: a row of engineers with heads bowed at their desks under the red video wall, all seen from behind.", line="NA16b",
      motion="The engineers stay bowed; one rubs his neck; the red wall pulses." + HOLD),
    S("S17a", "S17", "estill", "ecu", "dev", "EL", [], "DEV_DESK", "A smartphone lying face up on a desk, screen blank (caller name composited later), cold light.", fx="handheld"),
    S("S17b", "S17", "face", "ms", "dev", "EL", [N], "DEV_DESK", "Medium: Hino snatching the phone up from the desk and raising it to his ear, seen from the side-back, mouth hidden.",
      motion="He snatches the phone and raises it to his ear, shoulders tense; his face stays turned away." + HOLD, expr="back"),
    S("S17c", "S17", "face", "ms", "board_morn", "EL", [D], "BOARD_DAY", "Medium: Shinoda at a plain office desk holding a document, a desk phone receiver at his ear, calm and cold, black-framed glasses, seen at three-quarter angle, mouth hidden by the receiver.", line="L36",
      motion="Shinoda lowers the document slowly, eyes narrowing, the receiver steady at his ear; mouth hidden behind the receiver." + HOLD, expr="firm"),
    S("S17d", "S17", "face", "cu", "dev", "EL", [N], "DEV_DESK", "Close-up of Hino listening, sweat beading realistically on his temple, eyes wide.",
      motion="Sweat beads on his temple, his eyes widen, a shaky breath." + HOLD, expr="fear"),
    S("S17e", "S17", "d", "ots", "dev", "EL", [N, "STAFF"], "DEV_DESK", "Close-up of Hino at three-quarter angle, phone at his ear, stammering, the handkerchief crushed in his fist.", line="L37",
      act="Hino stammers into the phone, the handkerchief crushed in his fist, eyes darting, voice thin. Answering Shinoda's question, lying badly." + OB, expr="fear"),
    S("S17f", "S17", "face", "cu", "board_morn", "EL", [D], "BOARD_DAY", "Close-up of Shinoda silent, the receiver at his ear, eyes steady behind the black glasses, saying nothing.", line="NA17",
      motion="He says nothing, a slow blink, the jaw sets; the receiver stays still." + HOLD, expr="firm"),
    S("S17g", "S17", "empty", "ews", "dev", "HA", [], "DEV_RED", "No people. High wide of the development office at night, the video wall dark except a few red panels.", line="NA18",
      motion="The few red panels flicker and one more goes dark; no people.", fx="dissolve"),
    # ④ 절정·결말
    S("S18a", "S18", "estill", "ecu", "ctrl_red", "EL", [], "CTRL_RED", "A blank red-pulsing control monitor panel filling the frame (Japanese 'license expired' composited later).", line="NA19", fx="pushin"),
    S("S18b", "S18", "empty", "ews", "ctrl_black", "OH", [], "CTRL_BLACK", "No people. Overhead view of the control room: the wall of monitors going dark one panel at a time, consoles as dim shapes.",
      motion="Monitor panels switch off one after another from left to right; the room darkens; no people."),
    S("S18c", "S18", "ins", "ecu", "ctrl_black", "EL", [N], "CTRL_EMER", "Insert: a man's hand with a white handkerchief wiping sweat from a temple under dim red emergency light, no full face.",
      motion="The handkerchief wipes slowly; red light pulses on the skin."),
    S("S18d", "S18", "face", "ms", "ctrl_black", "EL", [N], "CTRL_EMER", "Medium: Hino at a console under dim red emergency light, face lit from below by a dying monitor, frozen, hands on the keys (dolly zoom in the edit).", fx="dollyzoom",
      motion="His hands freeze on the keys; his face slackens; the monitor light dies a little." + HOLD, expr="fear"),
    S("S18e", "S18", "d", "ots", "ctrl_black", "EL", [N, "STAFF"], "CTRL_EMER", "Over an engineer's blurred shoulder (left foreground): Hino at three-quarter angle, hands on the dead keyboard, red emergency light, terror.", line="L38", fx="handheld",
      act="Hino whispers then rises to a frightened cry, hands pressing the dead keys, eyes wide. Realizing everything is stopping." + OB, expr="fear"),
    S("S18g", "S18", "d", "cu", "ctrl_black", "EL", [W], "CTRL_EMER", "Close-up of Washio at three-quarter angle under dim red emergency light, gold glasses, face cracked with fear, voice gone hoarse, sweat.", line="L38a",
      act="Washio speaks hoarse and broken, barely above a whisper, swallowing between phrases, sweat on his brow, eyes pleading at no one. Ordering them to bring Hikaru back." + OB, expr="fear"),
    S("S18h", "S18", "empty", "ews", "ctrl_black", "HA", [], "CTRL_BLACK", "No people. The dark control room from a ceiling corner, only red emergency lamps.", line="NA19b",
      motion="The red lamps pulse slowly; nothing else moves; no people."),
    S("S19a", "S19", "face", "ws", "board_morn", "EL", [D], "BOARD_DOOR", "Through the half-open boardroom door: Shinoda in his beige trench coat walks in carrying a black folder, seen from behind, morning light.", 
      motion="He walks two steady steps into the room, back to the camera, the coat moving.", expr="back"),
    S("S19b", "S19", "ins", "ecu", "board_morn", "OH", [D], "BOARD_HIGH", "Insert from above: two blank document folders set down side by side on the glossy table by a hand in a beige coat sleeve.",
      motion="The hand sets the two folders down, squares them, withdraws."),
    S("S19c", "S19", "d", "ots", "board_morn", "EL", [D, W], "BOARD_REV", "Over Washio's blurred shoulder (navy suit, right foreground): Shinoda standing at three-quarter angle sliding the first folder across the table, calm, black-framed glasses.", line="L39",
      act="Shinoda speaks calmly and precisely, sliding the folder across with two fingers, eyes on Washio. Presenting Hikaru's patent certificate." + OB, expr="calm"),
    S("S19d", "S19", "face", "cu", "board_morn", "EL", [W], "BOARD_HEAD", "Close-up of Washio pushing his gold glasses up, bluster forming over unease.",
      motion="He pushes the glasses up, nostrils flare, a hard breath; no other movement." + HOLD, expr="smug"),
    S("S19e", "S19", "d", "ots", "board_morn", "EL", [W, D], "BOARD_HEAD", "Over Shinoda's blurred shoulder (left foreground): Washio seated at three-quarter angle thrusting a single blank sheet forward with bluster, gold glasses.", line="L40",
      act="Washio blusters, thrusting the sheet forward, chin up, forced confidence, 'hora' with a jab of the finger. Claiming the assignment is valid." + OB, expr="smug"),
    S("S19f", "S19", "face", "cu", "board_morn", "EL", [D], "BOARD_REV", "Close-up of Shinoda taking the sheet and studying the red seal mark through his black-framed glasses, silent.",
      motion="He takes the sheet, tilts it to the light, eyes studying the seal mark, silent; a slow blink." + HOLD, expr="firm"),
    S("S19g", "S19", "d", "ots", "board_morn", "EL", [D, W], "BOARD_REV", "Over Washio's blurred shoulder (right foreground): Shinoda at three-quarter angle laying a second sheet beside the first, pushing his glasses up, quiet and precise.", line="L41",
      act="Shinoda lays the second sheet beside the first, pushes his glasses up with one finger, and speaks quietly and precisely, a slight pause before 'chigaimasu ne'. Exposing the forged seal to Washio." + OB, expr="firm"),
    S("S19h", "S19", "estill", "ecu", "board_morn", "OH", [], "P_SEALS", "Insert from above: two red seal impressions side by side on two blank sheets, one small and crude, one larger and finely carved (composited later), no text.", fx="pushin"),
    S("S19i", "S19", "d", "ots", "board_morn", "HA", [D, W], "BOARD_HIGH", "Over Washio's blurred shoulder (right foreground), slightly high angle: Shinoda standing tall at three-quarter angle looking down at him, firm, the coat closed, delivering the verdict.", line="L42",
      act="Shinoda stands and delivers the verdict firmly, looking down at Washio, each item clear, 'ni-hyaku-oku-en' spoken slowly and distinctly. Terminating the contract." + OB, expr="firm"),
    S("S19j", "S19", "face", "ms", "board_morn", "HA", [W], "BOARD_HEAD", "High angle: Washio half-rising then collapsing back into the chair, one arm flung out pointing toward the door, gold glasses askew, face grey.", line="L43", fx="dutch7", vo=True,
      motion="He half-rises, legs fail, he collapses back into the chair, arm flung out pointing, glasses slipping askew." + HOLD, expr="fear"),
    S("S19k", "S19", "d", "ots", "board_morn", "EL", [N, W], "BOARD_DAY", "Over Washio's blurred shoulder (right foreground): Hino backed against the wall at three-quarter angle, hands raised, face wet, near-screaming.", line="L44", fx="handheld",
      act="Hino cries out near a scream, backing against the wall, hands half raised, face wet, pointing back at Washio. Blaming Washio." + OB, expr="tears"),
    S("S19l", "S19", "d", "ots", "board_morn", "HA", [W, D], "BOARD_HIGH", "Over Shinoda's blurred coat (left foreground), high angle: Washio on his knees on the floor beside the chair, looking up, gold glasses, begging, tears and sweat.", line="L44a",
      act="Washio begs on his knees, voice cracking, looking up at Shinoda, hands clasped then reaching, tears and sweat, 'nan demo' broken. Pleading for Hikaru to be asked back." + OB, expr="fear"),
    S("S19m", "S19", "d", "ots", "board_morn", "LA", [D, W], "BOARD_LOW", "Over the kneeling Washio's blurred head (bottom foreground), low angle: Shinoda standing at three-quarter angle closing his coat, cold and calm, black-framed glasses.", line="L44b",
      act="Shinoda closes his coat and speaks coldly and calmly, quoting the words slowly and clearly, eyes on the kneeling man. Relaying Hikaru's refusal." + OB, expr="firm"),
    S("S19n", "S19", "ins", "ecu", "board_morn", "EL", [W], "BOARD_LOW", "Insert: a heavy hand slipping from the hem of a beige coat and dropping to the carpet, fingers spreading, a gold watch.",
      motion="The hand slips from the coat hem, drops to the carpet, fingers spread and go still."),
    S("S19o", "S19", "d", "ots", "board_morn", "EL", [N, D], "BOARD_DAY", "Over Shinoda's blurred shoulder (left foreground): Hino slumped against the wall at three-quarter angle, tears, confessing, eyes on the floor.", line="L44c",
      act="Hino confesses through tears, eyes on the floor then lifting, voice small, a broken nod on 'kiroku shite arimasu'. Confessing to Shinoda." + OB, expr="tears"),
    S("S19p", "S19", "face", "cu", "board_morn", "EL", [W], "BOARD_HEAD", "Close-up of Washio on the floor lifting his head slowly toward Hino, betrayal in his eyes, glasses askew.",
      motion="His head lifts slowly within 15 degrees toward Hino, eyes widening with betrayal, mouth closed." + HOLD, expr="fear"),
    S("S19q", "S19", "empty", "ews", "board_morn", "BE", [], "BOARD_BIRD", "No people. Bird's-eye view straight down on the boardroom: the long table, an overturned chair, two folders, morning light.", line="NA20",
      motion="Light shifts slowly across the table; nothing moves; no people."),
    S("S19r", "S19", "estill", "ecu", "board_morn", "EL", [], "BOARD_DAY", "No people. An overturned black leather chair on the carpet beside the glossy table, morning light.", fx="pushin"),
    S("S20a", "S20", "estill", "ecu", "product", "EL", [], None, "A folded newspaper page with a plunging line graph and blank headline blocks (Japanese headline composited later), no readable text.", line="NA21", fx="handheld"),
    S("S20b", "S20", "estill", "ms", "product", "LA", [], None, "A blank white official notice on a glass door (Japanese notice composited later), no readable text.", fx="pushin"),
    S("S20c", "S20", "estill", "ecu", "product", "OH", [], None, "A plain cream envelope on a desk beside a red seal (Japanese title composited later), no readable text.", fx="pushin"),
    S("S20d", "S20", "empty", "ws", "board", "EL", [], "BOARD_DAY", "No people. The empty boardroom, chairs pushed out, cold light.", line="NA22",
      motion="Dust drifts in a shaft of light; no people.", fx="dissolve"),
    S("S21a", "S21", "face", "ews", "bamboo", "LA", [D], "BAM_PATH", "Low wide: a narrow path through dense green bamboo, dappled sunlight; Shinoda in his beige trench coat walks up the path toward the camera's far side, seen from behind.",
      motion="He walks three slow steps up the path, back to the camera, the bamboo leaves swaying.", expr="back"),
    S("S21b", "S21", "face", "ms", "bamboo", "EL", [HB, R], "BAM_VER", "Medium of the workshop veranda: Hikaru in a white shirt and navy cardigan sits shaving a bamboo strip with a small knife; the old woman Haru sits further along the veranda in her indigo apron.",
      motion="Hikaru's knife shaves the bamboo in slow strokes; Haru's hands sort strips; neither looks up." + HOLD, expr="calm"),
    S("S21c", "S21", "ins", "ecu", "bamboo", "EL", [HB], "BAM_VER", "Insert: a young man's hands shaving a thin bamboo strip with a small knife, pale curls of bamboo falling.",
      motion="The knife shaves off a thin curl of bamboo which falls; the hands continue steadily."),
    S("S21d", "S21", "d", "ots", "bamboo", "EL", [D, HB], "BAM_REV", "Over Hikaru's blurred shoulder (navy cardigan, right foreground): Shinoda standing in the yard at three-quarter angle removing an imaginary-free hat gesture — simply lowering his head slightly, a tired relieved smile, coat open, dappled light.", line="L45",
      act="Shinoda speaks with tired relief and a small smile, lowering his head slightly in greeting, hands loose. Greeting Hikaru after the long search." + OB, expr="moved"),
    S("S21e", "S21", "face", "cu", "bamboo", "EL", [HB], "BAM_VER", "Close-up of Hikaru setting the knife down on the veranda and looking up, calm, dappled light.",
      motion="He sets the knife down slowly, looks up within 15 degrees, a calm breath." + HOLD, expr="calm"),
    S("S21f", "S21", "d", "ots", "bamboo", "EL", [HB, D], "BAM_VER", "Over Shinoda's blurred shoulder (beige coat, left foreground): Hikaru rising to stand on the veranda at three-quarter angle, calm and quiet, speaking plainly, bamboo strips in one hand.", line="L46",
      act="Hikaru rises and speaks calmly and plainly, a slight pause after each of the three places, quiet firmness on 'saisho kara', eyes steady on Shinoda. Telling Shinoda what he never stopped." + OB, expr="firm"),
    S("S21g", "S21", "face", "cu", "bamboo", "EL", [D], "BAM_REV", "Close-up of Shinoda letting out a breath, eyes slightly wet behind the black glasses, a restrained smile.",
      motion="He lets out a slow breath, eyes glisten, a restrained smile forms." + HOLD, expr="moved"),
    S("S21h", "S21", "d", "ots", "bamboo", "EL", [D, HB], "BAM_REV", "Over Hikaru's blurred shoulder (right foreground): Shinoda at three-quarter angle, eyes wet, speaking softly, one hand on his chest.", line="L47",
      act="Shinoda speaks softly with wet eyes, a small nod, one hand briefly on his chest. Telling Hikaru he knows." + OB, expr="moved"),
    S("S21ha", "S21", "ins", "ecu", "bamboo", "EL", [D], "BAM_REV", "Insert: a hand in a beige coat sleeve drawing a plain cream envelope from an inner pocket, dappled light.",
      motion="The hand draws the envelope out slowly and holds it with both hands."),
    S("S21i", "S21", "d", "ots", "bamboo", "LA", [D, HB], "BAM_CANOPY", "Over Hikaru's blurred shoulder (right foreground): Shinoda holding out a plain cream envelope with both hands, earnest, dappled light.", line="L48",
      act="Shinoda holds out the envelope with both hands, earnest and respectful, a small bow on 'modotte kite kuremasen ka'. Asking Hikaru to come back." + OB, expr="moved"),
    S("S21j", "S21", "face", "cu", "bamboo", "EL", [R], "BAM_VER", "Close-up of old Haru on the veranda, a serene smile with deep laugh lines, listening, bamboo strips in her lap.",
      motion="Her smile deepens, she nods once very slowly, her hands rest on the strips." + HOLD, expr="smile"),
    S("S21k", "S21", "d", "ots", "bamboo", "EL", [HB, D], "BAM_VER", "Over Shinoda's blurred shoulder (left foreground): Hikaru at three-quarter angle glancing toward Haru on the veranda then back, gentle, not taking the envelope.", line="L49",
      act="Hikaru glances toward his grandmother and back, speaks gently, a soft smile on 'baachan no soba ni', hands at his sides not taking the envelope. Answering Shinoda's offer." + OB, expr="smile"),
    S("S21l", "S21", "d", "ots", "bamboo", "EL", [R, HB], "BAM_VER", "Over Hikaru's blurred shoulder (right foreground): old Haru on the veranda at three-quarter angle, a wrinkled proud smile, speaking slowly, bamboo strips in her lap.", line="L50",
      act="Haru speaks slowly and warmly with a proud wrinkled smile, a small nod to Hikaru, her hands on the bamboo strips. Telling her grandson the moon-child works at night anywhere." + OB, expr="proud"),
    S("S21m", "S21", "face", "cu", "bamboo", "EL", [HB], "BAM_VER", "Close-up of Hikaru smiling at his grandmother's words, eyes soft, dappled light.",
      motion="A smile spreads slowly, eyes soften, a quiet exhale; head within 10 degrees." + HOLD, expr="smile"),
    S("S21n", "S21", "d", "ots", "bamboo", "EL", [D, HB], "BAM_REV", "Over Hikaru's blurred shoulder (right foreground): Shinoda smiling, bending to set the envelope down on the veranda edge, coat open.", line="L51",
      act="Shinoda smiles warmly, bends to set the envelope on the veranda, straightens with a relieved breath. Telling Hikaru to work from here." + OB, expr="moved"),
    S("S21o", "S21", "face", "ews", "bamboo", "HA", [HB, D, R], "BAM_HIGH", "High wide of the yard and veranda: the three figures small among the bamboo, wind in the leaves.",
      motion="The bamboo sways in the wind; the three figures stay where they are; dappled light moves.", expr="back"),
    S("S22a", "S22", "face", "ews", "dusk", "EL", [K], "BAM_DUSK", "Wide at golden dusk: the bamboo path with long shadows; far away Sakura in a plain beige coat walks up the path toward the camera, a small figure, a plastic bag in one hand, the other hand holding something small.",
      motion="The small figure walks slowly up the path toward the camera; her face is too far to read; the bamboo sways in golden light."),
    S("S22b", "S22", "face", "cu", "dusk", "EL", [HB], "BAM_THRU", "Close-up through bamboo stalks in the foreground: Hikaru on the veranda lifting his head toward the path, golden light, surprise softening into a smile.",
      motion="His head lifts within 15 degrees toward the path, surprise softening into a smile, a slow blink.", expr="smile"),
    S("S22c", "S22", "ins", "ecu", "dusk", "EL", [K], "P_TONBO", "Insert: a young woman's hand holding the bamboo dragonfly toy up in golden dusk light.",
      motion="The hand lifts the bamboo dragonfly a little higher; golden light flares through its blades."),
    S("S22d", "S22", "d", "ots", "dusk", "EL", [K, HB], "BAM_DUSK", "Over Hikaru's blurred shoulder (right foreground): Sakura at three-quarter angle holding up the plastic bag, tears and a laugh together, golden dusk light in her hair.", line="L52",
      act="Sakura speaks with a tearful laugh, holding up the bag, the same teasing line as the first night, eyes shining. Greeting Hikaru again." + OB, expr="tears"),
    S("S22e", "S22", "face", "cu", "dusk", "EL", [HB], "BAM_THRU", "Close-up of Hikaru laughing silently, eyes wet, golden light, no words.",
      motion="He laughs silently, shoulders shaking once, eyes wet, a slow happy exhale; head within 10 degrees." + HOLD, expr="smile"),
    S("S23a", "S23", "empty", "ews", "moon", "LA", [], "BAM_MOON", "No people. Low wide: a huge full moon over the swaying bamboo, cold blue light.", line="NA24",
      motion="The bamboo sways slowly in the night wind; thin clouds cross the moon; no people."),
    S("S23aa", "S23", "empty", "ecu", "moon", "LA", [], "BAM_MOON", "No people. Extreme close-up of the full moon's surface behind a few swaying bamboo leaves in silhouette.",
      motion="Bamboo leaves sway slowly across the moon; thin clouds drift; no people."),
    S("S23b", "S23", "empty", "ws", "moon", "EL", [], "BAM_MOON", "No people. The little workshop house under the moon with one warm window light, bamboo around.", line="NA25", fx="tiltdown",
      motion="The window light flickers warmly; leaves move; no people."),
    S("S24a", "S24", "reuse:S03c", "ots", "yard", "EL", [], None, "Reuse of S03c frame (rice balls handed over), still push-in for the closing question.", line="NA26"),
]
SHOTS = [s for s in SHOTS if s["id"] != "S07b"]  # (S07b는 L13 vo 처리로 S07a에 흡수)

# A안 절감형(고니감독님 승인 2026-10-15): 짧은 대사 18줄은 화자 대신 「듣는 사람」의 i2v 리액션 위에 목소리(L컷). 립싱크는 감정·반전 대사 32컷.
VO = {  # line: (who, lens, angle, subject, motion, expr)
 "L03": ([HA_], "cu", "EL", "Close-up of Hikaru glancing at the closed laptop then back at her, a shy half-smile, the towel in his hands.", "He glances at the laptop and back, a shy half-smile, the towel turning in his hands." + HOLD, "smile"),
 "L05": ([HA_], "cu", "EL", "Close-up of Hikaru hearing her repeat the words, a faint amused breath, eyes on her.", "A faint amused breath, eyes steady on her, the towel still; one blink." + HOLD, "smile"),
 "L11": ([HA_], "cu", "EL", "Close-up of Hikaru looking at the green wall Hino points to, then back to Hino, calm.", "His eyes follow the pointing hand to the wall and return to Hino, calm; a small breath." + HOLD, "calm"),
 "L12": ([N], "cu", "EL", "Close-up of Hino in the doorway hearing the name, a slow blink, the handkerchief tightening in his fist.", "He hears the name, a slow blink, the fist tightens on the handkerchief; lips stay closed." + HOLD, "forced"),
 "L14": ([N, D], "ms", "EL", "Medium past Shinoda's blurred coat: Hino standing by the blank screen with the remote, listening to the praise with a forced modest smile, eyes flicking to Washio.", "Hino's forced modest smile widens, eyes flick toward the head seat and back; the remote hand lowers slowly." + HOLD, "forced"),
 "L15": ([D], "cu", "EL", "Close-up of Shinoda nodding politely at Washio's words, black-framed glasses, a courteous smile, closing the folder.", "He nods politely twice, a courteous smile, closes the folder gently." + HOLD, "calm"),
 "L17": ([N], "cu", "EL", "Close-up of Hino listening, the pen still held out, the forced smile slowly fading as he hears the words.", "The forced smile fades slowly, the pen hand lowers an inch, a swallow." + HOLD, "forced"),
 "L20": ([HA_], "cu", "HA", "High-angle close-up of Hikaru looking down at the last sheet slid toward him, calm, lips closed.", "His eyes drop to the last sheet, a slow breath, no other movement." + HOLD, "calm"),
 "L21": ([W], "cu", "LA", "Low close-up of Washio watching him gather the papers, a satisfied sneer, gold glasses.", "The sneer settles, he leans back a degree, fingers lace on the desk." + HOLD, "smug"),
 "L24": ([HA_], "cu", "EL", "Close-up of Hikaru's tired smile at her puzzlement, the rice-ball bag in his hand, moonlight.", "His tired smile deepens a little, he looks down at the bag, a soft exhale." + HOLD, "smile"),
 "L28": ([W], "cu", "EL", "Close-up of Washio leaning back, gold glasses, waiting with contempt as the young man speaks quietly.", "He leans back, contempt in the set of his mouth, fingers tapping once on the armrest." + HOLD, "smug"),
 "L35": ([W], "cu", "EL", "Close-up of Washio lowering his glass, listening to Hino's report, the smile thinning slightly.", "He lowers the glass slowly, the smile thins, one slow blink behind the gold glasses." + HOLD, "smug"),
 "L37": ([D], "cu", "EL", "Close-up of Shinoda listening on the receiver, eyes narrowing behind the black glasses, the document lowered.", "His eyes narrow, the document lowers to the desk, the receiver stays steady." + HOLD, "firm"),
 "L40": ([D], "cu", "EL", "Close-up of Shinoda watching the sheet thrust toward him, calm, black-framed glasses, no reaction.", "He watches the sheet, calm, a single slow blink, then reaches for it." + HOLD, "calm"),
 "L45": ([HB], "cu", "EL", "Close-up of Hikaru on the veranda looking up at the visitor, the knife in his hand pausing, calm recognition.", "The knife pauses mid-stroke, he looks up within 15 degrees, calm recognition, a small breath." + HOLD, "calm"),
 "L47": ([HB], "cu", "EL", "Close-up of Hikaru hearing 'I know', eyes softening, a bamboo strip in his hand.", "His eyes soften, a slow blink, the bamboo strip turns once in his fingers." + HOLD, "calm"),
 "L49": ([D], "cu", "EL", "Close-up of Shinoda listening, the envelope still held out, his expression gentling as he hears the answer.", "His expression gentles, the envelope lowers an inch, a slow nod begins." + HOLD, "moved"),
 "L51": ([HB, R], "ms", "EL", "Medium of the veranda: Hikaru and old Haru watching Shinoda set the envelope down, Hikaru's hand resting on the veranda edge, both faces calm.", "Haru nods slowly; Hikaru's hand rests on the veranda edge; both watch the envelope, still." + HOLD, "smile"),
}
for _s in SHOTS:
    if _s["line"] in VO:
        who, lens, angle, subj, mot, ex = VO[_s["line"]]
        _s.update(kind="face", who=who, lens=lens, angle=angle, subject=subj, motion=mot, expr=ex, act="", vo=True)


CARDS = {"H0a": "契約社員をクビにした大企業の、三十日後。", "H2": "なぜ、たった三十日で――", "H3": "月に帰った契約社員", "S16ba": "期限まで、あと一日"}
TITLE_SUB = "〜「月から来たゴミ」と笑った役員たちの、三十日後〜"
JA_OVERLAY = {"S05a": "모니터 「負荷分散 失敗」", "S06a": "모니터 「負荷分散 正常」", "S08b": "양도증 「特許譲渡証」", "S16ba": "붉은 숫자 「期限まで、あと一日」",
              "S16bb": "모니터 「認証失敗」", "S17a": "휴대폰 「篠田室長」", "S18a": "모니터 「ライセンス期限切れ」", "S18f": "휴대폰 「社長」",
              "S19h": "인영 2개 비교(인감 대조)", "S20a": "신문 「月浦エナジー 株価急落」", "S20b": "공고 「解散のお知らせ」", "S20c": "봉투 「告訴状」"}
# 현장음 14그룹(대본 7-2절) — 같은 프롬프트 = 생성 1회 공유. 사람 컷에도 효과음형만(룸톤·웅성거림 금지)
G = {
 "srv": "server fans spinning down one by one, low electrical hum fading, a distant alarm beep", "hq": "distant city traffic, seagulls, morning harbor wind",
 "yard": "low transformer hum, night crickets, light wind, an occasional metal creak", "cloth": "a wet cloth wiping a concrete floor, water wrung into a bucket",
 "dev": "mechanical keyboard typing, PC fan hum, fluorescent light buzz", "board": "quiet air conditioning hum, paper pages turning, a teacup set on a saucer",
 "exec": "fingers tapping on a wooden desk, papers slapped onto a desk, a leather chair creak", "seal": "a rubber stamp pressed firmly onto paper, a drawer sliding",
 "gate": "night wind, a distant highway, footsteps on wet pavement, a cardboard box shifting", "glass": "two glasses clinking, whisky poured over ice",
 "phone": "a smartphone vibrating on a desk, then picked up", "bamboo": "bamboo being shaved with a knife, wind through bamboo leaves, birds, a wind chime",
 "bam_night": "bamboo leaves rustling in night wind, crickets, a distant owl", "paper": "newspaper pages rustling, an envelope torn open",
}
AMB_BY_SCENE = {"S01": "hq", "S02": "yard", "S03": "yard", "S04": "", "S05": "dev", "S06": "dev", "S07": "board", "S08": "dev", "S09": "exec",
                "S10": "exec", "S11": "dev", "S12": "yard", "S13": "seal", "S14": "exec", "S15": "gate", "S16": "glass", "S16b": "dev", "S17": "phone",
                "S18": "srv", "S19": "board", "S20": "paper", "S21": "bamboo", "S22": "bamboo", "S23": "bam_night", "S24": "yard"}
AMB_BY_SHOT = {"S02c": "cloth", "S11c": "cloth", "S11a": "dev", "S18d": "srv", "H0a": "srv", "H0b": "srv", "H1": "", "H2": "bam_night", "H3": ""}
BGM = [  # (시작, 끝, 볼륨, 프롬프트) — 0~3.5초 BGM 없음(서버 정지 드론+심장 박동은 PHASE 6 로컬 믹스). 구간 간격 1.0초 이상
    (3.5, 19.5, 0.36, "low ominous synth drone with a slow heartbeat pulse rising to a sharp hit, Japanese drama cold open, instrumental, no vocals"),
    (20.5, 208.0, 0.38, "gentle nocturnal piano with soft strings, warm loneliness under a full moon, slowly tinged with unease, Japanese human drama, instrumental, no vocals"),
    (210.0, 395.0, 0.40, "tense low strings and muted piano ostinato, greed and pressure, a quiet countdown feeling, Japanese drama score, instrumental, no vocals"),
    (397.0, 418.0, 0.40, "dark pulsing suspense, ticking percussion and low brass swells, dread rising, Japanese drama score, instrumental, no vocals"),
    (420.0, 525.0, 0.42, "ominous drone breaking into a cold powerful reveal, strings and timpani, judgment and collapse, Japanese drama score, instrumental, no vocals"),
    (527.0, None, 0.40, "warm hopeful piano and soft strings resolving in a bamboo grove under the moon, tender Japanese drama finale, instrumental, no vocals"),
]
for _a, _b in zip(BGM, BGM[1:]):
    assert _b[0] - _a[1] >= 1.0, f"BGM 구간 간격 {_b[0] - _a[1]:.1f}s < 1.0s"

STYLE = {"NA": "Naration", "光": "Hikaru", "鷲尾": "Washio", "日野": "Hino", "さくら": "Sakura", "篠田": "Shinoda", "ハル": "Haru"}
STYLE_JA = {"Naration": "ナレーター", "Hikaru": "光", "Washio": "鷲尾", "Hino": "日野", "Sakura": "さくら", "Shinoda": "篠田", "Haru": "ハル"}
STYLE_COLOR = {"Naration": "&H00DDDDDD", "Hikaru": "&H00FFFFFF", "Washio": "&H00B4D2FF", "Hino": "&H00C8C8F0", "Sakura": "&H00F0E6C8",
               "Shinoda": "&H00E6DCC8", "Haru": "&H00D8F0E6"}
RATE = {"lite": 0.036, "omni": 0.16, "kf": 0.04}
HOOK_LEN = {"H0a": 2.0, "H0b": 1.5, "H1": 4.5, "H2": 7.0, "H3": 5.0}
NA0_AT = 1.0


def tc(sec):
    fr = int(round(sec * FPS)); s, f = divmod(fr, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}.{f:02d}"


def ass_t(sec):
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap(text, limit=18):
    """휴대폰 기준(8절): 1줄 18자 이내·2줄. libass 일본어 자동 줄바꿈 불가 → 구두점에서 수동 \\N."""
    NOHEAD = "…—、。!?？！』」"
    out, cur = [], ""
    for i, ch in enumerate(text):
        cur += ch
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if len(cur) >= limit and ch in "、。…!?？！』」" and nxt and nxt not in NOHEAD:
            out.append(cur); cur = ""
    if cur:
        out.append(cur)
    if len(out) > 2 or max(len(x) for x in out) > limit + 6:
        mid = len(text) // 2
        cands = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "、。…!?？！" and text[i + 1] not in NOHEAD]
        cut = min(cands, key=lambda i: abs(i - mid)) if cands else mid
        out = [text[:cut], text[cut:]]
    return "\\N".join(out)


def script_texts():
    t = open(os.path.join(PROD, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 5.")[0]
    out = {m.group(1): m.group(2) for m in re.finditer(r"^\s+((?:NA|L)\d+[a-c]?)[^「\n]*「(.+)」", body, re.M)}
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

    tts_order = sorted([x for x in lock["lines"] if (x["scene"].startswith("S") and x.get("start") is not None) or x["tag"] == "NA0"],
                       key=lambda x: (x["start"] if x.get("start") is not None else NA0_AT))
    dst = os.path.join(ROOT, "assets", "audio-overrides", SKIT); os.makedirs(dst, exist_ok=True)
    mapping = []
    for i, x in enumerate(tts_order, 1):
        shutil.copyfile(os.path.join(ROOT, "assets", "auditions", "tsuki-tts", x["id"] + ".mp3"), os.path.join(dst, f"line{i:03d}.mp3"))
        mapping.append((f"line{i:03d}", x["tag"], x["id"]))

    events = []
    for x in tts_order:
        st = STYLE["NA" if x["spk"] == "NA" else x["spk"]]
        s0 = (NA0_AT - x["lead"]) if x["tag"] == "NA0" else (x["start"] - x["lead"])
        e0 = (NA0_AT + x["dur"] + 0.2) if x["tag"] == "NA0" else (x["end"] + 0.2)
        events.append((s0, e0, st, STYLE_JA[st], wrap(texts[x["tag"]])))
    for sid, cap in CARDS.items():
        if sid == "H3":
            continue
        c0 = starts[sid] + (0.5 if sid == "H0a" else 0.3)
        events.append((c0, min(ends[sid] - 0.2, c0 + 3.5), "Caption", "", cap))
    events.append((starts["H3"] + 0.6, ends["H3"] - 0.3, "Title", "", CARDS["H3"] + "\\N{\\fs44}" + TITLE_SUB))
    h1 = rows["L26"]
    events.append((starts["H1"] + 0.4, starts["H1"] + 0.4 + h1["dur"] + 0.3, "HookLine", "鷲尾", wrap(texts["L26"])))
    events.sort(key=lambda e: e[0])
    # 휴대폰 기준(8절): 대사 66px·외곽선 6, 내레이션 60px
    st_lines = "\n".join(
        f"Style: {n},Noto Sans CJK JP,{66 if n != 'Naration' else 60},{c},&H000000FF,&H00000000,&H80000000,-1,{-1 if n == 'Naration' else 0},0,0,100,100,0,0,1,6,2,2,200,200,90,1"
        for n, c in STYLE_COLOR.items())
    ass = ["[Script Info]", "Title: 月に帰った契約社員 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           st_lines,
           "Style: HookLine,Noto Sans CJK JP,66,&H00B4D2FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,200,200,90,1",
           "Style: Caption,Noto Sans CJK JP,84,&H001E1EFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,160,160,80,1",
           "Style: Title,Noto Serif CJK JP,110,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,5,160,160,80,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{e[4]}")
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    os.makedirs(os.path.join(ROOT, "scripts", "storyboard"), exist_ok=True)
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_tsuki_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT, "preset": PRESET,
               "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"], "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_tsuki_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, wardrobe, "
                         "props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_tsuki_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (Typecast 확정본).",
        "default_voice": "cached-typecast", "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Naration"], "silent_styles": ["Caption", "HookLine", "Title"],
        "output_size": [1920, 1080], "fit": "crop", "scene_durations": durations, "transitions": [0.0] * len(durations),
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d" and s["line"]],
        "omnihuman_prompts": {str(idx[k]): v for k, v in omni_prompts.items()},
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0, "legacy_lipsync": False,
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35, "duck_db": 8, "ambience_prompts": [x["ambience"] for x in sb],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": s, "end": round(main_end, 2) if e is None else e, "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_후크": "0~3.5초 BGM 없음: 서버 팬 정지 드론 + 심장 박동 1회(자막 등장 순간)를 PHASE 6 로컬 믹스. H1 화면은 S14c 재사용, 음성은 L26 원본을 로컬 믹스. NA0은 자막 1번 줄(1.0초).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    md = ["# 『月に帰った契約社員』 PHASE 3 샷 리스트 (B안 표준)", "",
          f"> `scripts/build_tsuki_phase3.py` 자동 생성(손 수정 금지). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " + ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock['ads']) + ".",
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
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_tsuki_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않거나 부딪힘(연기 메모에 의도가 없으면 키프레임·동작 문장을 고친다). 감정 격차(9절)는 샷 표의 장면 순서로 확인.", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 감정·세기·템포 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")


if __name__ == "__main__":
    main()
