#!/usr/bin/env python3
"""『明日から来なくていい』(ashita-kara) PHASE 3 샷 리스트 Lock 생성기 — 일본어판.

선례 build_yanagi_phase3.py를 이 작품의 Lock 형식(lock.json lines/scenes/ads)에 맞춰 옮긴 것.
입력(동결본, 손으로 옮겨 적지 않는다):
  productions/ashita-kara-ja/lock.json        PHASE 1 Lock(실측 음성 줄 타임코드·장면 경계·광고 지점)
  productions/ashita-kara-ja/00_script_ja.md  대본 v1.2(자막 원문)
  assets/auditions/ashita-tts/lineNNN.mp3 + assets/auditions/ashita-tts-add/PNN.mp3  확정 음성
출력:
  scripts/storyboard/ashita-kara.json   샷 스펙(PHASE 4 키프레임·PHASE 5 입력)
  scripts/scenes/ashita-kara.json       장면 생성 설정(i2v·override_required·budget_usd)
  scripts/audio/ashita-kara.json        조립·오디오(장면 길이·OmniHuman·BGM·현장음)
  subs/ashita-kara.ass                  일본어 자막(본편 88줄 + 화면 전용 카드)
  assets/audio-overrides/ashita-kara/lineNNN.mp3  시간 순 번호로 합친 음성(자막 줄 번호 = TTS 캐시 번호)
  productions/ashita-kara-ja/07_샷리스트.md  검토용 표 + 비용 추산 + 앵글 분포
규칙: CLAUDE.md 제0~9장, 02_카메라앵글설계.md, 00_script_ja 4-1(OMNI 12장면).
검사: 연속 같은 구도(A1)·돌리줌 1회·더치 2회 이하·OMNI 각도·화자-화면 일치·모든 대사 줄 사용·컷 길이(1.2초 이상, 정지 6.5초·i2v 10초 이하)·OMNI 8초.
사용법: python3 scripts/build_ashita_phase3.py
"""
import collections
import json
import os
import re
import shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "ashita-kara-ja")
SKIT = "ashita-kara"
FPS = 24
HARD = 1 / FPS
OMNI_MAX = 7.9
LEAD = 0.3
MIN_SHOT = 1.2
STILL_MAX = 6.5
I2V_MAX = 10.0
SHOT_TARGET = 1.6

# ---------- 고정 문장(PHASE 2 시트와 1:1) ----------
C1 = "assets/portraits/ashita-cast/cells/"
C2 = "assets/portraits/ashita-cast-2/cells/"  # Kill Gate 2차 합격 셀(인물 전원·사토 B·회의실·제어실·앵글·사옥 낮)
WHO = {
    "SATO": ("Sato Makoto, a Japanese man aged 48, square-jawed weathered face, calm deep-set eyes, short black hair heavily streaked with grey, "
             "thin rectangular silver-rimmed glasses, a small pale scar just above his LEFT eyebrow, clean-shaven", C2 + "sato-front.png"),
    "TANAKA": ("Tanaka Sho, a slim Japanese man aged 28, narrow smug face with sharp cheekbones, light-brown dyed two-block hair swept up and back, "
               "no glasses, no earrings, clean-shaven, a chunky gold wristwatch on his RIGHT wrist", C2 + "tanaka-front.png"),
    "YAMA": ("Yamamoto Tsuyoshi, a heavy-set Japanese man aged 63, round fleshy face, bald crown with white hair only at the sides, thin gold-rimmed glasses",
             C2 + "yamamoto-front.png"),
    "TAKA": ("Takahashi, a stocky Japanese man aged 55, stern square face, very short grey hair, thick dark eyebrows, no glasses", C2 + "takahashi-front.png"),
    "MORI": ("Mori Misaki, a slim Japanese woman aged 24, gentle earnest face with no makeup, straight black chin-length bob with full bangs, no glasses, "
             "a plain black hair tie on her LEFT wrist", C2 + "mori-front.png"),
    "YHANDS": ("a young man's hands only, no face, a plain grey sweatshirt sleeve (flashback)", None),
    "SUITS": ("several men in dark suits seen only as faceless backlit silhouettes", None),
}
WARD = {
    "SATO_A": "a plain navy-blue zip-up work jacket with no logo, a plain white collared shirt, a plain grey necktie, dark-grey work trousers",
    "SATO_B": "a charcoal-grey suit with no logo, a plain white shirt, a plain grey necktie",
    "TANAKA": "a glossy dark-navy three-piece luxury suit with no logo, white shirt, plain silver tie",
    "YAMA": "a black double-breasted suit, white shirt, plain burgundy necktie, no lapel pin",
    "TAKA": "a charcoal-grey suit with a plain dark-blue tie under a long plain black overcoat worn open",
    "MORI": "a plain light-blue work uniform jacket and trousers with no logo, patch or name tag, a white T-shirt underneath",
}
EXPR = {  # 표정 셀(키프레임에 감정 50~70% 선반영 — 규격 제2장 3)
    # PHASE 2 Kill Gate 2차 합격 셀(안경 일치·실사 눈물/땀). 타나카 「smug」는 45도 셀(옅은 비웃음),
    # 야마모토 「fear」는 2차 expr3 불합격(다른 얼굴·안경 없음) → 3차에서 정면 셀 참조로 재생성(ashita-cast-3).
    ("SATO", "cold"): C2 + "sato-expr2.png", ("SATO", "smile"): C2 + "sato-expr3.png",
    ("TANAKA", "smug"): C2 + "tanaka-45.png", ("TANAKA", "rage"): C2 + "tanaka-expr2.png", ("TANAKA", "sob"): C2 + "tanaka-expr3.png",
    ("YAMA", "cold"): C2 + "yamamoto-front.png", ("YAMA", "shock"): C2 + "yamamoto-expr2.png", ("YAMA", "fear"): "assets/portraits/ashita-cast-3/yamamoto-fear-1.png",  # 3차 재생성(고니감독님 지적)
    ("TAKA", "stern"): C2 + "takahashi-expr1.png", ("TAKA", "fury"): C2 + "takahashi-expr2.png",
    ("MORI", "smile"): C2 + "mori-expr1.png", ("MORI", "tears"): C2 + "mori-expr2.png", ("MORI", "firm"): C2 + "mori-expr3.png",
    ("SATO_B", "front"): C2 + "sato-b-front.png",
}
LOC = {
    "OFF_DAY": C1 + "loc-office-day.png", "OFF_NIGHT": C1 + "loc-office-night.png", "OFF_DESK": C1 + "loc-office-key1.png",
    "OFF_DOOR": C1 + "loc-office-key2.png", "OFF_REV": C2 + "loc-office-angles-day.png", "OFF_HIGH": C2 + "loc-office-angles-night.png",
    "OFF_LOW": C2 + "loc-office-angles-key1.png", "OFF_GLASS": C2 + "loc-office-angles-key2.png",
    "MEET": C2 + "loc-meeting-angles-key1.png", "MEET_NIGHT": C2 + "loc-meeting-night.png", "MEET_HEAD": C2 + "loc-meeting-angles-key1.png",
    "MEET_SIDE": C2 + "loc-meeting-key2.png", "MEET_REV": C2 + "loc-meeting-angles-day.png", "MEET_HIGH": C2 + "loc-meeting-angles-night.png",
    "MEET_LOW": C2 + "loc-meeting-angles-key1.png", "MEET_DOOR": C2 + "loc-meeting-angles-key2.png",
    "CTRL": C2 + "loc-control-day.png", "CTRL_RED": C2 + "loc-control-night.png", "CTRL_CONSOLE": C2 + "loc-control-key1.png",
    "YARD": C2 + "loc-control-key2.png", "CTRL_REV": C2 + "loc-control-angles-day.png", "CTRL_HIGH": C2 + "loc-control-angles-night.png",
    "CTRL_LOW": C2 + "loc-control-angles-key1.png", "CTRL_MON": C2 + "loc-control-angles-key2.png",
    "HQ_DAY": C2 + "loc-hq-day.png", "HQ_RAIN": C1 + "loc-hq-night.png", "ROOF": C1 + "loc-hq-key1.png", "NEWOFF": C1 + "loc-hq-key2.png",
    "LOUNGE": C1 + "loc-misc-day.png", "CORRIDOR": C1 + "loc-misc-night.png", "ALLEY": C1 + "loc-misc-key1.png", "BREAKER_RM": C1 + "loc-misc-key2.png",
    "P_HANKO": C1 + "props-hanko.png", "P_BREAKER": C1 + "props-breaker.png", "P_RELAY": C1 + "props-relay.png", "P_HELMET": C1 + "props-helmet.png",
}
PRESET = ("Photorealistic live-action Japanese workplace drama, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, "
          "restrained Japanese film mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, "
            "logo on shirt, signage lettering, posters with writing, documents with writing, screens with text, printed labels, brand logos, "
            "watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people, blood, gore, handcuffs, police")
PLAIN = "All papers, screens, signs, cards and labels are completely blank; no letters, numbers or symbols anywhere in the frame."
# 고니감독님 지시(2026-10-11): 눈물·땀은 실사 촬영처럼 자연스럽게(만화식 물방울 금지), 안경 착용은 인물별 고정
TEARS = ("Realistic tears as in a live-action film: reddened eye rims, glossy wet eyes, one or two thin clear tear tracks running naturally down "
         "the cheeks and catching the light, a small tear bead on the lower lashes, slightly reddened nose; no cartoon droplets.")
SWEAT = ("Realistic sweat as in a live-action film: fine tiny beads of perspiration on the forehead, temples and upper lip, a natural oily sheen, "
         "a few damp strands at the hairline; no large cartoon drops.")
GLASSES = {"SATO": "He wears his thin silver-rimmed glasses.", "YAMA": "He wears his thin gold-rimmed glasses.",
           "TANAKA": "He wears no glasses.", "TAKA": "He wears no glasses.", "MORI": "She wears no glasses."}
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the object fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait",
    "ch": "85mm prime lens, f/1.8, choker framing from forehead to chin, razor-sharp eyes, soft bokeh",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective",
}
LIGHT = {
    "hq": "clear morning daylight on glass and concrete, crisp 5600K, soft long shadows",
    "lamp": "night office lit by a single warm 3200K tungsten desk lamp, subtle warm rim light on the subject, the rest of the room in soft darkness",
    "office": "hard cold fluorescent top light (5600K or cooler) falling straight down, dark shadows under brows and chin, faint cyan cast",
    "meeting": "hard cold fluorescent top light 5600K, high-contrast chiaroscuro, blinds half closed, deep cinematic shadows",
    "roof": "night rooftop, cool moonlit blue ambient with the warm glow of the Tokyo skyline behind, gentle rim light",
    "rain": "rainy night, sodium streetlights backlighting the falling rain, wet asphalt reflections, cold blue shadows",
    "lounge": "dim murky gold indirect light, greedy warm highlights on glass, deep shadows",
    "corridor": "cold fluorescent corridor light through frosted glass, sterile",
    "control": "cold 5600K console and ceiling light, monitors glowing, crisp and tense",
    "red": "blackout, only a red emergency lamp glowing, deep red shadows, high contrast",
    "red_door": "blackout control room lit by a red emergency lamp, plus a strong white backlight spilling in from the open doorway, faces readable, high contrast",
    "dawn": "pale blue dawn light over the substation yard, soft mist",
    "spark": "a blinding white-blue electrical flash lighting the yard for an instant",
    "backlit": "strong backlight from the open doorway, figures as hard silhouettes, haze in the light",
    "morning": "soft diffuse morning light through a large window, gentle golden rim light, airy and hopeful",
    "flash": "warm amber 3200K flashback, soft halation, lifted blacks like an old photo",
    "product": "soft even studio light, neutral",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}
SPK_KEY = {"佐藤": "SATO", "田中": "TANAKA", "山本": "YAMA", "高橋": "TAKA", "森": "MORI"}


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None):
    """kind: d(OMNI 대사) / react(정지 푸시인, 입 비노출 대사 포함) / ins(인서트 정지) / face(얼굴 i2v pro) /
    sil(실루엣·뒷모습·측면 i2v lite) / empty(무인 i2v lite) / estill(무인 정지) / reuse:<id> / card.
    line = 대본 태그(NA3, L14, P5 …) — 그 줄의 발화가 이 컷에서 시작한다(화자는 who에 있어야 함)."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc,
                subject=subject, line=line, fx=fx, motion=motion, expr=expr)


T, Y, SA, SB, M, K = "TANAKA:TANAKA", "YAMA:YAMA", "SATO:SATO_A", "SATO:SATO_B", "MORI:MORI", "TAKA:TAKA"
SHOTS = [
    # ① 도입 후크 (0:00~0:20) — 후반 컷 재사용(추가 생성 0)
    S("H0a", "H", "reuse:S25b", "ews", "red", "BE", [], None, "Reuse of S25b (Tanaka kneeling under the red emergency lamp, from above)."),
    S("H0b", "H", "reuse:S25c", "ecu", "red", "OH", [], None, "Reuse of S25c (a drop of sweat hits the floor)."),
    S("H1", "H", "reuse:S12c", "cu", "meeting", "EL", [], None, "Reuse of S12c (Tanaka: 'Don't come to the company from tomorrow!'). Voice = L22 mixed locally."),
    S("H2", "H", "reuse:S19b", "ms", "red", "EL", [], None, "Reuse of S19b (control monitors flashing red, ACCESS DENIED composited)."),
    S("H3", "H", "card", "ews", "red", "EL", [], None, "Black title card 『明日から来なくていい』 with subtitle."),
    # ② 발단·갈등
    S("S01a", "S01", "empty", "ews", "hq", "LA", [], "HQ_DAY", "No people. Low angle on the clean glass-and-concrete headquarters of a mid-sized engineering company on a clear morning, blank facade.", line="NA1",
      motion="Clouds drift slowly across the sky reflected in the glass. No people, no cars."),
    S("S01b", "S01", "estill", "ws", "hq", "HA", [], "HQ_DAY", "No people. High angle over the empty forecourt in front of the headquarters entrance.", line="NA2", fx="pullback"),
    S("S01c", "S01", "estill", "ecu", "hq", "EL", [], "HQ_DAY", "No people. Detail of the blank glass facade reflecting drifting clouds."),
    S("S02a", "S02", "ins", "ecu", "lamp", "OH", ["SATO:SATO_A"], "OFF_DESK", "Insert from above: a man's weathered hands turn a large blank engineering drawing under a warm desk lamp, navy work-jacket cuffs.", line="NA3"),
    S("S02b", "S02", "react", "cu", "lamp", "EL", ["SATO:SATO_A"], "OFF_NIGHT", "Close-up profile of Sato reading the drawing late at night, glasses catching the lamp light, warm rim light, calm and focused."),
    S("S02c", "S02", "sil", "ws", "lamp", "EL", ["SATO:SATO_A"], "OFF_GLASS", "Through the glass partition: the dark empty office, Sato alone at the only lit desk, small in frame.", line="NA4",
      motion="Sato slowly turns a page of the drawing; everything else is still."),
    S("S03a", "S03", "sil", "ws", "lamp", "EL", ["MORI:MORI", "SATO:SATO_A"], "OFF_DOOR", "Wide from the office entrance: Mori seen from behind walks in holding two canned coffees; Sato far away at his lit desk.", line="L01",
      motion="Mori takes two slow steps toward Sato's desk, her back to the camera, a worried but bright little tilt of the head as she holds up the coffee cans with a gentle smile in her posture; Sato stays seated."),
    S("S03b", "S03", "react", "ms", "lamp", "SIDE", ["SATO:SATO_A"], "OFF_DESK", "Side medium of Sato leaning over the drawing, his face turned down to the paper so his mouth is not visible, warm lamp light.", line="L02"),
    S("S03c", "S03", "ins", "ecu", "lamp", "OH", ["SATO:SATO_A"], "OFF_DESK", "Insert: Sato's finger traces a line on the blank drawing beside a canned coffee with no label.", line="L03"),
    S("S03d", "S03", "react", "ms", "lamp", "EL", ["MORI:MORI", "SATO:SATO_A"], "OFF_NIGHT", "Over Mori's shoulder (her back and bob hair soft in the foreground) toward Sato, who glances up with a faint kind look.", line="L04"),
    S("S04a", "S04", "face", "ms", "office", "LA", [T], "OFF_DOOR", "Low angle medium at the office entrance: Tanaka strides in holding a takeaway coffee cup with no logo, chin raised, arrogant smirk, cold fluorescent backlight.", line="NA5",
      motion="Tanaka takes one slow arrogant step forward and sips the coffee; head turns under 15 degrees; he does not walk toward the camera.", expr="smug"),
    S("S04b", "S04", "ins", "ecu", "office", "LA", [T], "OFF_LOW", "Insert at floor level: polished brown leather shoes stepping on the office floor, a chunky gold wristwatch on the right wrist of the swinging hand.", line="NA6"),
    S("S04c", "S04", "react", "cu", "office", "SIDE", [T], "OFF_DAY", "Close-up of Tanaka glancing sideways at the engineers with contempt as he passes, mouth closed.", expr="smug"),
    S("S05a", "S05", "sil", "ms", "office", "EL", ["SATO:SATO_A", T], "OFF_DESK", "Over Sato's shoulder (soft in the foreground): Tanaka arrives at the desk and perches on its corner, smug.", line="L05",
      motion="Tanaka, seen from behind, leans on the desk corner and tilts his head mockingly with a breezy, careless excite in his shoulders, keeping his back to the camera; Sato stays seated."),
    S("S05b", "S05", "react", "ms", "office", "SIDE", [T], "OFF_DAY", "Side medium of Tanaka sitting on the desk corner, waving the coffee cup dismissively, face in profile turned away so his mouth is hidden.", line="L06"),
    S("S05ba", "S05", "ins", "ecu", "office", "OH", ["SATO:SATO_A"], "OFF_DESK", "Insert: Sato's hand stops still on the blank drawing."),
    S("S05c", "S05", "react", "ms", "office", "HA", ["SATO:SATO_A"], "OFF_DESK", "High angle side view of Sato seated, looking up from his drawings, firm and unafraid, mouth hidden by the angle.", line="L07"),
    S("S05ca", "S05", "ins", "ecu", "office", "EL", [T], "OFF_DAY", "Insert: a finger with a gold wristwatch tapping impatiently on a takeaway coffee cup with no logo."),
    S("S05d", "S05", "d", "cu", "office", "LA", [T], "OFF_DAY", "Chest-up close-up of Tanaka, slightly low angle, sneering mockingly with a raised eyebrow, cold top light.", line="L08", expr="smug"),
    S("S06a", "S06", "ins", "ecu", "office", "OH", [T], "P_HANKO", "Insert from above: a gold wristwatch on a wrist beside a blank government subsidy approval document and a red ink pad.", line="NA7"),
    S("S06b", "S06", "sil", "ws", "office", "EL", [T], "OFF_GLASS", "Through half-open blinds: the office, Tanaka far away in silhouette strutting between desks."),
    S("S06ba", "S06b", "sil", "ws", "corridor", "EL", [T], "CORRIDOR", "Through a frosted-glass wall in a corridor: Tanaka seen from the side-back, phone to his ear, pacing slowly.", line="P1",
      motion="Tanaka paces one slow step with the phone at his ear, shoulders bouncing with smug excite and a silent laugh; his back stays to the camera."),
    S("S06bb", "S06b", "ins", "ecu", "corridor", "EL", [T], "CORRIDOR", "Insert: a hand with a chunky gold wristwatch holding a smartphone with a dark blank screen to an ear."),
    S("S06bc", "S06b", "react", "ms", "corridor", "SIDE", [T], "CORRIDOR", "Side medium of Tanaka grinning greedily into the phone, face turned so his mouth is hidden.", line="P2", expr="smug"),
    S("S07a", "S07", "sil", "ms", "office", "HA", [M, T], "OFF_DAY", "High angle: Mori seated at her desk, Tanaka standing over her from behind so his shadow falls across her desk; Tanaka seen from the back.", line="L09",
      motion="Tanaka keeps his back to the camera and taps the desk once with his finger; Mori shrinks slightly. No one walks."),
    S("S07b", "S07", "react", "ch", "office", "SIDE", [M], "OFF_DAY", "Choker profile of Mori, eyes lowered, hesitant and afraid, lips pressed, cold top light.", line="L10", expr="tears"),
    S("S07c", "S07", "sil", "ms", "office", "LA", [T], "OFF_LOW", "Low angle side silhouette of Tanaka against the ceiling fluorescent tubes, leaning down toward someone off-frame; his mouth is not visible.", line="L11",
      motion="Tanaka leans down slowly and taps a document twice; his face stays in silhouette and turned away."),
    S("S07d", "S07", "ins", "ecu", "office", "OH", [], "P_HANKO", "Insert: the empty red-ringed stamp box on a blank document, a red ink pad beside it."),
    S("S08a", "S08", "ins", "ecu", "office", "OH", [M], "P_HANKO", "Insert from above: a small round hanko seal pressed down onto the blank document, a woman's hand.", line="NA8"),
    S("S08b", "S08", "ins", "ecu", "office", "EL", [M], "OFF_DAY", "Insert: Mori's trembling hand still holding the hanko, a black hair tie on her left wrist."),
    S("S08c", "S08", "react", "ws", "office", "SIDE", [M], "OFF_GLASS", "Through the glass partition: Mori sitting alone at her desk in profile, shoulders slumped.", line="NA9"),
    S("S08d", "S08", "ins", "ecu", "office", "EL", [], "P_HANKO", "Insert: the hanko set down beside the stamped blank document, a red mark on the paper."),
    S("S09a", "S09", "sil", "ws", "office", "EL", ["SATO:SATO_A"], "OFF_DAY", "Past a monitor in the foreground (abstract grey diagram, no text): Sato walks toward Tanaka's desk holding a sheet of paper.", line="L12",
      motion="Sato walks slowly away from the camera toward the far desk, holding the paper; his back stays to the camera."),
    S("S09b", "S09", "ins", "ecu", "office", "EL", [], "OFF_DESK", "Insert: a monitor showing a blank change-history table with highlighted rows and no readable text."),
    S("S09c", "S09", "react", "ms", "office", "SIDE", [T], "OFF_DAY", "Side medium of Tanaka lounging in his chair, shrugging, face in profile so his mouth is hidden.", line="L13"),
    S("S09d", "S09", "d", "cu", "office", "EL", ["SATO:SATO_A"], "OFF_DAY", "Chest-up close-up of Sato, restrained anger, eyes hard behind silver glasses, cold top light.", line="L14", expr="cold"),
    S("S09e", "S09", "d", "cu", "office", "LA", [T], "OFF_DAY", "Chest-up close-up of Tanaka, slightly low angle, condescending smirk.", line="L15", expr="smug"),
    S("S10a", "S10", "sil", "ws", "roof", "SIDE", ["SATO:SATO_A"], "ROOF", "Night rooftop: Sato seen from behind, both hands on the plain metal railing, looking at the Tokyo skyline.", line="NA10", fx="craneup",
      motion="Sato's coat edge moves in the night wind; he stays still, back to camera."),
    S("S10b", "S10", "ins", "ecu", "lamp", "OH", [], "OFF_DESK", "Insert from above: three blank formal documents stacked on a desk under a lamp."),
    S("S10c", "S10", "sil", "ews", "roof", "HA", ["SATO:SATO_A"], "ROOF", "Very high wide: a tiny figure on the rooftop against the vast night city.", line="NA11",
      motion="City lights twinkle; the tiny figure stays still."),
    # ③ 전개·위기
    S("S11a", "S11", "estill", "ews", "meeting", "HA", [Y, T, "SATO:SATO_A"], "MEET_HIGH", "High angle from a ceiling corner: the long black meeting table, Yamamoto at the head, Tanaka beside him, Sato small on the opposite side; tense stillness.", line="NA12"),
    S("S11b", "S11", "react", "ms", "meeting", "SIDE", [Y], "MEET_HEAD", "Side medium of Yamamoto at the head of the table, leaning back, condescending, face turned so his mouth is hidden.", line="L16", expr="cold"),
    S("S11ba", "S11", "ins", "ecu", "meeting", "EL", [Y], "MEET_HEAD", "Insert: Yamamoto's thick fingers drumming slowly on the glossy table."),
    S("S11c", "S11", "react", "ms", "meeting", "SIDE", ["SATO:SATO_A"], "MEET_SIDE", "Side medium of Sato sitting upright, a document under his hand, face in profile, mouth hidden.", line="L17"),
    S("S11ca", "S11", "ins", "ecu", "meeting", "OH", ["SATO:SATO_A"], "MEET_SIDE", "Insert from above: Sato's hand pressing flat on a blank document on the table."),
    S("S11d", "S11", "d", "cu", "meeting", "EL", ["SATO:SATO_A"], "MEET_SIDE", "Chest-up close-up of Sato, resolute, lips firm, eyes unwavering, chiaroscuro top light.", line="L18", expr="cold"),
    S("S11e", "S11", "react", "ms", "meeting", "SIDE", [Y], "MEET_HEAD", "Side medium close-up of Yamamoto looking over his gold glasses, the lenses catching the light, mouth hidden.", line="L19", expr="cold"),
    S("S11f", "S11", "ins", "ecu", "meeting", "OH", [Y], "MEET_LOW", "Insert from above: a stack of blank papers slammed onto the glossy black table, sheets scattering, a heavy hand withdrawing."),
    S("S12a", "S12", "sil", "ms", "meeting", "LA", [T], "MEET_LOW", "Low angle from the side-back: Tanaka shoves his chair back and stands up, face red, pointing across the table.", line="L20", fx="dutch5,handheld",
      motion="Tanaka, back to the camera, jabs his pointing arm forward once in explosive fury, shoulders heaving; his face stays turned away from the camera.", expr="rage"),
    S("S12b", "S12", "d", "cu", "meeting", "LA", [T], "MEET", "Chest-up close-up of Tanaka shouting in fury, veins on his forehead, low angle, cold top light.", line="L21", expr="rage"),
    S("S12c", "S12", "d", "cu", "meeting", "EL", [T], "MEET", "Chest-up close-up of Tanaka with a slow cruel sneer, eyes narrowed, savoring the moment.", line="L22", expr="smug"),
    S("S12d", "S12", "react", "ms", "meeting", "SIDE", [Y], "MEET_HEAD", "Side medium of Yamamoto sliding a blank envelope across the table with two fingers, cold, mouth hidden.", line="L23", expr="cold"),
    S("S12e", "S12", "react", "ch", "meeting", "EL", ["SATO:SATO_A"], "MEET_SIDE", "Choker close-up of Sato in silence, jaw tight, eyes calm and cold behind the glasses.", expr="cold"),
    S("S13a", "S13", "d", "cu", "meeting", "EL", ["SATO:SATO_A"], "MEET_SIDE", "Chest-up close-up of Sato speaking quietly after a long silence, cold restraint.", line="L24", expr="cold"),
    S("S13b", "S13", "react", "ms", "meeting", "SIDE", [T], "MEET", "Side medium of Tanaka scoffing, arms crossed, face turned so his mouth is hidden.", line="P3", expr="smug"),
    S("S13c", "S13", "sil", "ws", "meeting", "EL", ["SATO:SATO_A"], "MEET_DOOR", "Through the half-open door frame: Sato stands up from the table and turns toward the door, his back to camera.",
      motion="Sato rises slowly and squares his shoulders; he does not walk toward the camera."),
    S("S14a", "S14", "sil", "ws", "lamp", "EL", ["SATO:SATO_A", M], "OFF_NIGHT", "Night office: Sato packs a cardboard box at his desk; Mori approaches from behind, seen from the back.", line="L25",
      motion="Sato places a folder into the box; Mori stops two steps behind him, her shoulders trembling as she holds back tears, one hand rising to her eyes. No head turns."),
    S("S14b", "S14", "react", "ms", "lamp", "SIDE", [M], "OFF_NIGHT", "Side medium of Mori holding back tears, lip trembling, warm lamp rim light.", expr="tears"),
    S("S14c", "S14", "react", "ms", "lamp", "SIDE", ["SATO:SATO_A"], "OFF_DESK", "Side medium of Sato pausing over the box, a gentle sad look, face turned down so his mouth is hidden.", line="L26"),
    S("S14d", "S14", "d", "cu", "lamp", "EL", ["SATO:SATO_A"], "OFF_NIGHT", "Chest-up close-up of Sato, earnest and grave, asking a final favor, warm lamp light.", line="L27"),
    S("S14e", "S14", "react", "cu", "lamp", "SIDE", [M], "OFF_NIGHT", "Close-up from the side-back of Mori nodding firmly, tears in her eyes, mouth not visible.", line="L28", expr="firm"),
    S("S15a", "S15", "sil", "ws", "rain", "SIDE", ["SATO:SATO_A"], "HQ_RAIN", "Static rear shot: Sato walks out of the glass revolving door into heavy rain, carrying a cardboard box.", line="NA13",
      motion="Sato walks slowly away from the camera into the rain; rain falls; he never turns around."),
    S("S15b", "S15", "sil", "ws", "rain", "HA", ["SATO:SATO_A"], "HQ_RAIN", "From a second-floor window streaked with raindrops: the small figure of Sato crossing the wet forecourt with the box.", line="NA14",
      motion="Raindrops run down the glass in the foreground; the small figure keeps walking away."),
    S("S15c", "S15", "ins", "ecu", "rain", "LA", ["SATO:SATO_A"], "HQ_RAIN", "Insert at ground level: black work shoes stepping into a puddle on wet asphalt, rain splashing."),
    S("S15ba", "S15b", "sil", "ws", "rain", "SIDE", ["SATO:SATO_A"], "ALLEY", "A narrow rainy back street at night: Sato walks away from the camera carrying the box.", line="P4",
      motion="Sato walks steadily and calm away down the wet street, quiet and unhurried; rain falls."),
    S("S15bb", "S15b", "ins", "ecu", "rain", "OH", [], "ALLEY", "Insert from above: raindrops falling on the lid of a plain cardboard box."),
    S("S16a", "S16", "sil", "ms", "rain", "SIDE", ["SATO:SATO_A"], "ALLEY", "Under a shop awning with no lettering: Sato seen from the side-back, phone at his ear, rain beyond.", line="L29",
      motion="Sato stands still with the phone at his ear; rain falls beyond the awning."),
    S("S16b", "S16", "ins", "ecu", "rain", "EL", ["SATO:SATO_A"], "ALLEY", "Insert: Sato's hand holding a smartphone with a dark blank screen, rain bokeh behind.", line="L30"),
    S("S16c", "S16", "react", "cu", "rain", "SIDE", ["SATO:SATO_A"], "ALLEY", "Close-up side profile of Sato with a faint restrained smile, rain light on his glasses.", expr="smile"),
    S("S17a", "S17", "sil", "ms", "lounge", "LA", [T, Y], "LOUNGE", "Low angle two-shot in silhouette: Tanaka and Yamamoto raise champagne glasses in a dim gold executive lounge, faces in shadow.", line="L31", fx="handheld",
      motion="They clink their glasses once and laugh silently; their faces stay in shadow."),
    S("S17b", "S17", "react", "ms", "lounge", "SIDE", [Y], "LOUNGE", "Side medium of Yamamoto smiling with satisfaction, glass in hand, face in profile, mouth hidden.", line="L32"),
    S("S17ba0", "S17", "estill", "ecu", "lounge", "OH", [], "LOUNGE", "No people. From above: a champagne bottle in a silver ice bucket in murky gold light."),
    S("S17c", "S17", "ins", "ecu", "lounge", "EL", [Y], "LOUNGE", "Insert: a heavy hand raising a champagne glass, golden bubbles rising.", line="P5"),
    S("S17ca", "S17", "react", "ms", "lounge", "LA", [Y], "LOUNGE", "Low angle side of Yamamoto raising his glass, pleased, mouth hidden."),
    S("S17d", "S17", "react", "ms", "lounge", "SIDE", [T], "LOUNGE", "Side-back medium of Tanaka holding a champagne glass, greedy grin seen only at the cheek.", line="P6", expr="smug"),
    S("S17da", "S17", "estill", "ws", "lounge", "HA", [], "LOUNGE", "No people. High angle of the dim gold lounge, two half-empty glasses on the side table."),
    S("S17ba", "S17b", "sil", "ws", "office", "EL", [M, T], "BREAKER_RM", "Through the door frame of a small substation room: Mori stands by an old grey breaker cabinet; Tanaka in the doorway in foreground silhouette.", line="L33",
      motion="Tanaka keeps his back to the camera and gestures toward the cabinet; Mori stays still by the cabinet."),
    S("S17bb", "S17b", "react", "ms", "office", "SIDE", [M], "BREAKER_RM", "Side medium of Mori standing in front of the breaker cabinet, firm, mouth hidden.", line="L34", expr="firm"),
    S("S17bc", "S17b", "sil", "ws", "office", "SIDE", [T], "BREAKER_RM", "Wide from inside the room: Tanaka in the doorway seen from behind, turning away dismissively.", line="L35",
      motion="Tanaka turns his shoulders away with a cold, low click-of-the-tongue shrug and steps out of the doorway; his face is not visible."),
    S("S17bd", "S17b", "react", "cu", "office", "SIDE", [M], "BREAKER_RM", "Close-up side of Mori alone, her hand resting on the cabinet, eyes determined, mouth hidden.", line="P7", expr="firm"),
    S("S17be", "S17b", "ins", "ecu", "office", "EL", [], "P_BREAKER", "Insert: the large black lever of the old grey mechanical breaker, scuffed metal, no labels."),
    S("S18a", "S18", "empty", "ews", "dawn", "LA", [], "YARD", "No people. Low wide of the substation yard at dawn, huge grey transformers behind yellow safety rails.", line="NA15",
      motion="Thin mist drifts over the yard. No people."),
    S("S18b", "S18", "react", "ms", "control", "SIDE", [M], "CTRL_CONSOLE", "Side medium of Mori at the control console, monitors lit, alarmed, mouth hidden.", line="L36"),
    S("S18c", "S18", "sil", "ms", "control", "LA", [T], "CTRL_LOW", "Low angle from the side-back: Tanaka storms in through the control room door.", line="L37",
      motion="Tanaka strides one step in and throws a hand up in irritated anger, panicking; his face stays turned away."),
    S("S18d", "S18", "react", "cu", "control", "SIDE", [M], "CTRL_CONSOLE", "Close-up side of Mori lit by the monitor glow, frightened, mouth hidden.", line="L38", expr="tears"),
    S("S18e", "S18", "sil", "ms", "control", "SIDE", [T], "CTRL", "Side medium of Tanaka slamming his palm on the console, panicking, face turned away.", line="P8", fx="handheld",
      motion="Tanaka slams his palm down on the console once; his face stays turned away."),
    S("S18f", "S18", "react", "ms", "control", "HA", [M], "CTRL_MON", "High angle over Mori's shoulder toward a wall of monitors flashing red with no text.", line="P9"),
    S("S19a", "S19", "sil", "ws", "meeting", "EL", [Y], "MEET_NIGHT", "Wide of the executive office: Yamamoto in profile shouting into a desk phone receiver.", line="P10",
      motion="Yamamoto grips the receiver and leans forward; his face stays in profile."),
    S("S19b", "S19", "ins", "ms", "red", "EL", [], "CTRL_MON", "Monitors flashing solid red with a blank warning panel (Japanese warning text composited later)."),
    S("S19c", "S19", "react", "ms", "meeting", "SIDE", [Y], "MEET_NIGHT", "Medium close-up of Yamamoto frozen with the receiver, eyes wide, sweat on his forehead, profile so his mouth is hidden.", line="L39", fx="dutch7", expr="shock"),
    S("S19d", "S19", "ins", "ecu", "meeting", "EL", [Y], "MEET_NIGHT", "Insert: a desk-phone receiver slipping from a heavy trembling hand."),
    S("S20a", "S20", "estill", "ms", "office", "EL", [], "OFF_DESK", "No people. Sato's empty desk in desaturated black and white, a scratched old white safety helmet left on it.", line="NA16", fx="pushin,bw"),
    # ④ 절정·결말
    S("S20b", "S20", "ins", "ecu", "office", "EL", [], "P_HELMET", "Insert: the scratched old white safety helmet in extreme close-up, shallow focus, black and white.", fx="bw"),
    S("S21a", "S21", "ins", "ecu", "flash", "EL", ["YHANDS"], None, "Flashback insert: young hands soldering a small circuit board in a cramped room at night, warm amber light, no face.", line="NA17"),
    S("S21b", "S21", "ins", "ecu", "flash", "OH", [], None, "Flashback insert from above: a notebook page of hand-drawn circuit diagrams with no readable text, a pencil."),
    S("S21c", "S21", "empty", "ews", "dawn", "LA", [], "YARD", "No people. The substation's huge transformers from a low angle, mist.", line="NA18",
      motion="Mist drifts slowly; no people."),
    S("S21d", "S21", "sil", "ws", "morning", "SIDE", ["SATO:SATO_B"], "NEWOFF", "A small bright new office: Sato in a charcoal suit stands at the window, seen from behind.",
      motion="Sato stands still at the window; morning light; he does not turn."),
    S("S21e", "S21", "ins", "ecu", "morning", "OH", [], "NEWOFF", "Insert from above: a blank contract document with an empty signature line on a wooden desk.", line="NA19"),
    S("S21f", "S21", "ins", "ms", "morning", "EL", ["SATO:SATO_B"], "NEWOFF", "Medium insert: Sato's hands closing a plain document folder on the desk."),
    S("S21g", "S21", "ins", "ecu", "control", "OH", [], None, "Insert from above: a blank official registration form with a red seal impression and no readable text."),
    S("S21h", "S21", "estill", "ews", "control", "HA", [], "CTRL_HIGH", "No people. The empty control room from a ceiling corner, monitors dark."),
    S("S22a", "S22", "sil", "ws", "control", "LA", [M, T], "CTRL_REV", "Low wide of the control room: Mori at the console in the foreground side, Tanaka behind her by the start button, staff silhouettes.", line="L40",
      motion="Mori keeps her back to the camera and turns her shoulders slightly toward Tanaka (under 15 degrees), urgent, her hand raised in a tense warning gesture; Tanaka stays still with a jaw-set glare."),
    S("S22b", "S22", "react", "cu", "control", "SIDE", [T], "CTRL", "Close-up side of Tanaka sweating, chest-up distance, forcing a brave face, mouth hidden.", line="L41", expr="smug"),
    S("S22c", "S22", "ins", "ecu", "control", "EL", [T], "CTRL_CONSOLE", "Insert: a finger with a gold wristwatch hovering over a large unlabeled start button."),
    S("S22d", "S22", "react", "ms", "control", "SIDE", [M], "CTRL_CONSOLE", "Side medium of Mori shutting her eyes tight.", expr="tears"),
    S("S23a", "S23", "empty", "ws", "spark", "EL", [], "YARD", "No people. A huge transformer erupts in a blinding white-blue electrical flash and sparks.", line="NA20",
      motion="A burst of bright sparks flies from the transformer and fades; no fire spreading, no people."),
    S("S23b", "S23", "estill", "ews", "red", "LA", [], "YARD", "No people. The substation yard plunged into darkness, only distant red lamps."),
    S("S23c", "S23", "estill", "ws", "red", "HA", [], "CTRL_RED", "No people. High angle of the control room in blackout, red emergency lamp, an overturned chair.", line="NA21"),
    S("S23d", "S23", "ins", "ecu", "red", "EL", [], "P_BREAKER", "Insert: the old breaker's black lever now snapped down in the tripped position."),
    S("S23e", "S23", "react", "ms", "red", "SIDE", [M], "CTRL_RED", "Side medium of Mori exhaling in relief in the red light, hand on her chest.", expr="tears"),
    S("S24a", "S24", "sil", "ws", "backlit", "EL", ["TAKA:TAKA", "SUITS"], "CTRL_LOW", "The control room door swings open: Takahashi strides in, hard backlit silhouette, faceless suited silhouettes behind him.", line="L42",
      motion="Takahashi takes one step in from the doorway and stops; the silhouettes behind stay still."),
    S("S24b", "S24", "sil", "ms", "backlit", "LA", ["TAKA:TAKA"], "CTRL_LOW", "Low angle medium of Takahashi against the bright doorway, coat open, face mostly in shadow.", line="L43",
      motion="Takahashi stands still as a backlit silhouette, his coat stirring slightly; his face stays in black shadow."),
    S("S24c", "S24", "d", "cu", "red_door", "LA", ["TAKA:TAKA"], "CTRL_REV", "Chest-up close-up of Takahashi, slightly low angle, condemning glare.", line="L44", expr="fury"),
    S("S24d", "S24", "react", "ms", "red_door", "SIDE", [Y], "CTRL", "Side medium of Yamamoto trembling, sweat on his face, hands shaking, mouth hidden.", line="L45", expr="fear"),
    S("S24e", "S24", "react", "ms", "red_door", "SIDE", ["TAKA:TAKA"], "CTRL_REV", "Side medium of Takahashi turning his head slightly toward Yamamoto, stern, mouth hidden.", line="L46", expr="stern"),
    S("S24f", "S24", "react", "cu", "red_door", "EL", [T], "CTRL", "Close-up of Tanaka recognizing someone at the door, face draining of color (dolly zoom in the edit).", fx="dollyzoom", expr="sob"),
    S("S24g", "S24", "face", "ms", "backlit", "LA", ["SATO:SATO_B"], "CTRL_LOW", "Low angle medium of Sato in a charcoal suit standing in the bright doorway, calm and composed.",
      motion="Sato stands still in the doorway, a slow single blink; head turn under 10 degrees.", expr="cold"),
    S("S25a", "S25", "d", "cu", "red", "EL", [T], "CTRL_RED", "Chest-up close-up of Tanaka on his knees, sobbing and begging, tears and sweat, red emergency light.", line="L47", expr="sob"),
    S("S25b", "S25", "react", "ews", "red", "BE", [T], "CTRL_HIGH", "Bird's-eye view straight down: Tanaka kneeling small on the control room floor under the red lamp.", expr="sob"),
    S("S25c", "S25", "ins", "ecu", "red", "OH", [], "CTRL_RED", "Insert: a drop of sweat falls onto the hard floor."),
    S("S26a", "S26", "d", "cu", "backlit", "LA", ["SATO:SATO_B"], "CTRL_LOW", "Chest-up close-up of Sato, low angle, looking down coldly at the kneeling man.", line="L48", expr="cold"),
    S("S26b", "S26", "ins", "ecu", "red", "OH", [], "CTRL_RED", "Insert: a single blank white business card lands on the floor (Japanese text composited later)."),
    S("S26c", "S26", "d", "cu", "backlit", "EL", ["SATO:SATO_B"], "CTRL_LOW", "Chest-up close-up of Sato with an icy faint smile.", line="L49", expr="smile"),
    S("S26d", "S26", "react", "ews", "red", "OH", ["SATO:SATO_B", T], "CTRL_HIGH", "From straight above: Sato's polished shoes in front of the kneeling Tanaka."),
    S("S27a", "S27", "ins", "ms", "office", "EL", [], None, "Insert: a monitor showing a plunging stock-price line graph with no numbers or text (Japanese labels composited later).", line="NA22"),
    S("S27b", "S27", "estill", "ws", "meeting", "EL", [], "MEET", "No people. The empty executive meeting room, chairs pushed out."),
    S("S27c", "S27", "empty", "ws", "hq", "EL", [], "HQ_RAIN", "No people. The headquarters entrance on a clear morning after the rain, wet ground drying.", line="NA23",
      motion="A light breeze; puddles shimmer; no people."),
    S("S27d", "S27", "ins", "ecu", "office", "OH", [], None, "Insert from above: a blank official envelope and claim document on a desk (Japanese title composited later).", line="NA24"),
    S("S27e", "S27", "ins", "ecu", "office", "EL", [], "OFF_DAY", "Insert: a chunky gold wristwatch left lying on an empty desk."),
    S("S28a", "S28", "face", "ws", "morning", "EL", ["SATO:SATO_B", M], "NEWOFF", "The bright new office: Sato at the window with a white coffee cup; Mori steps into the doorway in her light-blue uniform.", line="L50",
      motion="Mori stands in the doorway with her back to the camera and bows slightly; Sato lowers his cup and smiles. No walking toward the camera."),
    S("S28b", "S28", "react", "ms", "morning", "SIDE", [M], "NEWOFF", "Side medium of Mori, hopeful and earnest, golden rim light.", expr="smile"),
    S("S28c", "S28", "react", "cu", "morning", "SIDE", ["SATO:SATO_B"], "NEWOFF", "Side close-up of Sato with a warm restrained smile, face turned so his mouth is hidden.", line="L51", expr="smile"),
    S("S28d", "S28", "sil", "ws", "morning", "EL", ["SATO:SATO_B", M], "NEWOFF", "From outside the window: the two figures inside the bright office, the Tokyo skyline reflected on the glass.", line="NA25",
      motion="Reflections drift slowly on the glass; the two figures stay still."),
    S("S28e", "S28", "react", "cu", "morning", "SIDE", ["SATO:SATO_B"], "NEWOFF", "Close-up side profile of Sato looking out at the city in morning light, peaceful.", line="NA26"),
    S("S28f", "S28", "card", "ews", "morning", "EL", [], None, "Black ending card in centered Mincho: 「本当に失ったのは、どちらだったのか。」"),
]

CARDS = {"H0a": "社員をクビにした上司の、七日後。", "H3": "明日から来なくていい", "S12c": "明日から会社に来るな！",
         "S28f": "本当に失ったのは、どちらだったのか。"}
TITLE_SUB = "〜クビにした男が、百億円の鍵だった〜"
JA_OVERLAY = {"S09b": "변경 이력 표(継電器 型番 変更)", "S19b": "アクセス拒否 ／ 使用許諾 失効", "H2": "アクセス拒否",
              "S26b": "명함 「株式会社 佐藤電設技術研究所 代表 佐藤誠」", "S27a": "주가 폭락 그래프(朝凪テクノロジー 株価)",
              "S27d": "봉투 「損害賠償請求書」", "S06a": "결재 서류(補助金交付申請書)"}
AMBIENCE = {  # 사람이 나오는 컷은 현장음 금지(제6장 4) — 무인 컷만
    "S01a": "morning birds, distant city traffic", "S10b": "quiet room tone with a distant clock", "S15bb": "heavy rain on cardboard",
    "S18a": "low transformer hum, dawn wind", "S21c": "low transformer hum, wind", "S23a": "loud electrical explosion crack and sparks",
    "S23b": "power-down whine fading to silence, distant alarm", "S23d": "a heavy mechanical clunk", "S25c": "tiny drop on a hard floor",
    "S26b": "a small card landing on the floor", "S27c": "morning birds after rain, dripping water",
}
BGM = [  # (시작, 끝, 볼륨, 프롬프트) — 0~4초는 BGM 없음(결정 ①: 경보 저음 드론 + 심장 박동 1회는 PHASE 6에서 로컬 믹스)
    (4.0, 19.5, 0.36, "low ominous synth drone and a slow heartbeat pulse building to a sharp hit, Japanese thriller cold open, instrumental, no vocals"),
    (20.5, 205.0, 0.40, "tense modern office drama score, muted piano ostinato and low strings, quiet unease, Japanese TV drama, instrumental, no vocals"),
    (207.0, 300.0, 0.40, "dark brooding strings and heavy low piano, injustice and anger, Japanese drama score, instrumental, no vocals"),
    (301.5, 411.5, 0.40, "melancholic rain piano turning into suspense pulses and rising strings, Japanese drama score, instrumental, no vocals"),
    (414.0, 505.0, 0.42, "rising suspense to a dramatic reveal, powerful drums and brass, triumphant turn, Japanese drama score, instrumental, no vocals"),
    (506.5, None, 0.40, "cold victorious strings resolving into warm hopeful piano, Japanese drama finale, instrumental, no vocals"),
]
# PHASE 6 실증(2026-10-11): 구간 간격 0.5초 → generate_audio.py가 「겹쳐 들림」으로 생성 중단. 간격 1.0초 이상을 생성기에서 미리 검사
for _a, _b in zip(BGM, BGM[1:]):
    assert _b[0] - _a[1] >= 1.0, f"BGM 구간 간격 {_b[0] - _a[1]:.1f}s < 1.0s ({_a[1]}→{_b[0]})"

# B안(제10장 3·7): 사람이 나오는 정지 컷을 i2v로 — 실제 배우처럼 작고 자연스러운 연기(숨·눈 깜빡임·손의 일), 톤연출표 감정에 맞춘 크기.
# 입이 보이면 안 되는 컷은 「등·옆을 유지, 고개 15° 이내, 입 안 보임」을 붙인다. 글자 합성 면·무인 정물·편집 효과(흑백·돌리줌)는 정지 유지.
HIDE = " The speaker keeps the same back or profile angle to the camera, head turns under 15 degrees, the mouth is never visible."
LIVE = {
    "S01c": "Clouds drift slowly across the sky reflected in the glass panels. No people.",
    "S02a": "His weathered hands slowly smooth the drawing flat and turn its corner, unhurried, careful.",
    "S02b": "Sato reads intently, eyes moving along a line, one slow blink, the lamp light flickering faintly on his glasses; tiny breathing.",
    "S03b": "Sato leans closer over the drawing, his pencil tapping once, a small thoughtful exhale." + HIDE,
    "S03c": "His finger slowly traces along a line on the drawing and stops; steam rises faintly from the coffee can.",
    "S03d": "Mori shifts her weight shyly in the foreground; Sato glances up and gives a small tired nod." + HIDE,
    "S04b": "The polished shoes take one slow arrogant step across the floor; the gold watch glints.",
    "S04c": "Tanaka's eyes slide sideways with contempt, chin slightly raised, a slow breath out through the nose; mouth stays closed.",
    "S05b": "Tanaka waves the paper cup lazily once with a mocking, condescending shrug, shoulders loose and smug." + HIDE,
    "S05ba": "Sato's hand freezes on the drawing, fingers tensing slightly, then still.",
    "S05c": "Sato looks up from the drawings and holds still, a slow steady breath, unafraid." + HIDE,
    "S05ca": "The finger with the gold watch taps impatiently on the cup three times.",
    "S06bb": "The hand presses the phone closer to the ear, the gold watch catching the light; small shift.",
    "S06bc": "Tanaka's shoulders shake with a silent greedy laugh, phone at his ear." + HIDE,
    "S07b": "Mori lowers her eyes, hesitant and afraid, swallows, her trembling fingers twisting together; lips pressed; one slow blink.",
    "S08a": "A woman's hand presses the hanko down firmly once and lifts it slowly.",
    "S08b": "Mori's hand trembles slightly, still holding the hanko, fingers tightening.",
    "S08c": "Mori sits motionless, then her shoulders sink with a slow heavy breath.",
    "S09c": "Tanaka shrugs lazily with a dismissive, mocking toss of the hand and swivels the chair a few degrees." + HIDE,
    "S11a": "Very subtle: Yamamoto taps a pen once; the others sit still; faint air from the vent.",
    "S11b": "Yamamoto leans back slowly in the chair, condescending, fingers interlaced." + HIDE,
    "S11ba": "Thick fingers drum slowly on the glossy table, one-two-three-four, then stop.",
    "S11c": "Sato sits upright, his hand pressing the document; a slow controlled breath." + HIDE,
    "S11ca": "Sato's hand presses flat on the document, knuckles whitening slightly.",
    "S11e": "Yamamoto lowers his chin and looks over his gold glasses, the lenses catching light; a slow cold blink." + HIDE,
    "S11f": "The stack of papers settles after the slam, a few sheets sliding apart.",
    "S12d": "Yamamoto slides the envelope across the table with two fingers, slowly, coldly." + HIDE,
    "S12e": "Sato stays silent, jaw tightening, eyes calm; a single slow blink; barely perceptible breathing.",
    "S13b": "Tanaka scoffs, tightening his crossed arms, head tilting slightly." + HIDE,
    "S14b": "Mori's eyes glisten, her lips tremble as she holds back tears, a shaky breath; one tear forms.",
    "S14c": "Sato pauses over the box, then gently places a folder inside; a quiet sigh." + HIDE,
    "S14e": "Mori nods firmly twice, a tear sliding down her cheek." + HIDE,
    "S15bb": "Raindrops fall and splash on the cardboard lid, darkening the surface.",
    "S15c": "The black work shoe steps into the puddle, water rippling and splashing; rain keeps falling.",
    "S16b": "Rain falls in the bokeh behind; his hand grips the phone a little tighter, calm and steady.",
    "S16c": "Rain light shimmers on his glasses; a faint restrained smile deepens slightly; a slow blink.",
    "S17b": "Yamamoto swirls the champagne glass slowly, satisfied." + HIDE,
    "S17c": "The heavy hand raises the glass slowly; golden bubbles rise.",
    "S17ca": "Yamamoto lifts his glass a little higher, pleased, then sips." + HIDE,
    "S17d": "Tanaka turns the champagne glass in his fingers, shoulders relaxed with greed." + HIDE,
    "S17bb": "Mori stands firm, her hand rising to rest on the cabinet door; a determined breath." + HIDE,
    "S17bd": "Her hand presses gently on the cabinet, a sad but firm quiet resolve, a small trembling breath." + HIDE,
    "S18b": "Mori's hands move quickly over the console keys, then freeze in alarm; monitor glow flickers." + HIDE,
    "S18d": "Mori's breath quickens, her hand rising toward her mouth, monitor light flickering on her face." + HIDE,
    "S18f": "The wall of monitors flashes red in pulses; Mori's shoulders sag in despair, her hands trembling on the console." + HIDE,
    "S19c": "Yamamoto freezes, the receiver pressed to his ear, his free hand trembling slightly." + HIDE,
    "S19d": "The heavy hand trembles and the receiver slips slowly from the fingers.",
    "S21f": "Sato's hands close the folder slowly and rest on it.",
    "S22b": "Tanaka dabs his mouth with the handkerchief, sweat glistening, eyes darting once, a calm mask forced over panic; steady breathing.",
    "S22c": "The finger hovers, trembles once, then presses down on the red button.",
    "S22d": "Mori squeezes her eyes shut tighter, her shoulders tensing.",
    "S23e": "Mori exhales slowly in relief, her hand pressed to her chest, shoulders dropping.",
    "S24d": "Yamamoto trembles, wiping sweat from his forehead with a shaking hand." + HIDE,
    "S24e": "Takahashi turns his head slightly toward Yamamoto with a stern condemning glare, jaw set." + HIDE,
    "S25b": "From straight above: Tanaka's shoulders shake as he sobs, kneeling; red light pulses faintly.",
    "S26d": "From straight above: Sato's polished shoes stay still; Tanaka's hands tremble on the floor.",
    "S28b": "Mori smiles hopefully, eyes shining, a small earnest nod; golden light." + HIDE,
    "S28c": "Sato lowers the cup slightly, a warm smile in his eyes; the cup still covers his mouth.",
    "S28e": "Sato looks out at the city, a slow peaceful breath, the morning light shifting softly on his face." + HIDE,
}

# B안 립싱크 연기 지시(OmniHuman prompt, 제10장 7): 톤연출표 감정에 맞춘 실제 배우 같은 작은 몸짓. 고개는 상대 쪽 3/4 유지.
OMNI_BASE = (" Natural, realistic acting like a real film actor: subtle breathing, natural blinks, small head movements under 15 degrees, "
             "keeps looking toward the other person at the same three-quarter angle, hands stay where they are in the first frame; "
             "no exaggerated motion, the face and body stay the same person.")
OMNI_ACT = {
    "S05d": "Tanaka speaks with a lazy mocking smile, one eyebrow up, a small dismissive tilt of the head, the cup held loosely." + OMNI_BASE,
    "S09d": "Sato speaks with restrained anger, jaw tight, his finger pressing the drawing for emphasis on the last words." + OMNI_BASE,
    "S09e": "Tanaka speaks with a condescending smirk, a lazy open-palm gesture, leaning back in the chair." + OMNI_BASE,
    "S11d": "Sato speaks firmly with restrained anger and resolve, jaw set, hands flat on the folder, a small forward lean and a harder glare on 「絶対に」." + OMNI_BASE,
    "S12b": "Tanaka shouts in fury, leaning over the table on his fist, sharp short head movements, brow knotted." + OMNI_BASE,
    "S12c": "Tanaka delivers the firing slowly, savoring it, a cruel smile spreading, leaning on the table." + OMNI_BASE,
    "S13a": "Sato speaks low and quiet after a long silence, slow and controlled, eyes steady, minimal movement." + OMNI_BASE,
    "S14d": "Sato speaks earnestly and gently, word by word, a slight nod as he asks, his hand resting on the box." + OMNI_BASE,
    "S24c": "Takahashi condemns coldly and precisely, chin slightly down, the folder held at his side, a slow deliberate rhythm." + OMNI_BASE,
    "S25a": "Tanaka sobs and begs, face crumpling, shoulders shaking, clasped hands trembling, tears running." + OMNI_BASE,
    "S26a": "Sato speaks coldly and quietly, looking down, almost motionless, one slow blink." + OMNI_BASE,
    "S26c": "Sato speaks with an icy faint smile, adjusting his cuff once, unhurried." + OMNI_BASE,
}
STYLE = {"NA": "Naration", "佐藤": "Sato", "田中": "Tanaka", "山本": "Yamamoto", "高橋": "Takahashi", "森": "Mori"}
STYLE_JA = {"Naration": "ナレーター", "Sato": "佐藤", "Tanaka": "田中", "Yamamoto": "山本", "Takahashi": "高橋", "Mori": "森"}
STYLE_COLOR = {"Naration": "&H00DDDDDD", "Sato": "&H00FFFFFF", "Tanaka": "&H00B4D2FF", "Yamamoto": "&H00C8C8F0",
               "Takahashi": "&H00E6DCC8", "Mori": "&H00F0E6C8"}
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
    """대본 §4의 태그 → 자막 원문(한자 그대로)."""
    t = open(os.path.join(PROD, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 4-1.")[0]
    return {m.group(1): m.group(2) for m in re.finditer(r"^\s+((?:NA|L|OUT|P)\d+)[^「\n]*「(.+?)」", body, re.M)}


def check_rules(shots, rows):
    errs = []
    order = ["ecu", "ch", "cu", "ms", "ws", "ews"]
    prev = None
    for s in shots:
        if s["kind"] == "d" and s["angle"] in ("SIDE", "BE", "OH"):
            errs.append(f"{s['id']}: OMNI 대사 컷 각도 {s['angle']} 금지(정면~45°만)")
        if prev and prev["scene"] == s["scene"] and not s["kind"].startswith("reuse") and not prev["kind"].startswith("reuse"):
            if order.index(prev["lens"]) == order.index(s["lens"]) and prev["angle"] == s["angle"] and prev["loc"] == s["loc"]:
                errs.append(f"{prev['id']}→{s['id']}: 연속 같은 구도(A1)")
        if s["line"]:
            spk = rows[s["line"]]["spk"]
            if spk in SPK_KEY and SPK_KEY[spk] not in [w.split(":")[0] for w in s["who"]]:
                errs.append(f"{s['id']}: {s['line']} 화자 {spk}가 화면에 없음(화자-화면 일치)")
        prev = s
    dz = sum(1 for s in shots if "dollyzoom" in s["fx"])
    dutch = sum(1 for s in shots if "dutch" in s["fx"])
    if dz != 1:
        errs.append(f"돌리줌 {dz}회(1회만)")
    if dutch > 2:
        errs.append(f"더치 {dutch}회(최대 2회)")
    scenes = collections.OrderedDict()
    for s in shots:
        if s["scene"] != "H":
            scenes.setdefault(s["scene"], []).append(s)
    for sc, ss in scenes.items():
        if not ss[0]["line"]:
            errs.append(f"{sc}: 첫 컷({ss[0]['id']})에 대사·내레이션 앵커 없음 — 무언 시간이 없는 장면은 첫 컷이 줄로 시작해야 함")
    return errs


def main():
    lock = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
    rows = {x["tag"]: x for x in lock["lines"]}
    texts = script_texts()
    scenes = {s["id"]: (s["start"], s["end"]) for s in lock["scenes"]}
    ad_times = [a["at"] for a in lock["ads"]]
    main_end = lock["body_end"]

    errs = check_rules(SHOTS, rows)
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
    lag = []
    for sc, shots in by_scene.items():
        a, b = scenes[sc]
        pins = {0: a, len(shots): b}
        for k, s in enumerate(shots):
            if s["line"] and k:
                pins[k] = max(a, rows[s["line"]]["start"] - LEAD)
        keys = sorted(pins)
        for k1, k2 in zip(keys, keys[1:]):
            t1, t2 = pins[k1], pins[k2]
            n = k2 - k1
            for j in range(k1, k2):
                starts[shots[j]["id"]] = t1 + (t2 - t1) * (j - k1) / n
    order_ids = [s["id"] for s in SHOTS]
    ends = {sid: (starts[order_ids[k + 1]] if k + 1 < len(order_ids) else main_end) for k, sid in enumerate(order_ids)}
    for k, s in enumerate(SHOTS):  # OMNI 8초 상한 → 다음 컷 시작을 당김(컷어웨이)
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
        if s["kind"] in ("face", "sil", "empty") and d > I2V_MAX:
            problems.append(f"{s['id']} i2v {d:.2f}s > {I2V_MAX}")
    if problems:
        raise SystemExit("컷 길이 위반:\n  " + "\n  ".join(problems))

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
            ids.append(desc + (f", wearing {WARD[ward]}" if ward else ""))
            if s["expr"] and (key, s["expr"]) in EXPR and (ward != "SATO_B"):
                refs.append(EXPR[(key, s["expr"])])
            elif ward == "SATO_B":
                refs.append(EXPR[("SATO_B", "front")])
            elif cell:
                refs.append(cell)
        if s["loc"]:
            refs.append(LOC[s["loc"]])
        n = len(s["who"])
        comp = ("Exactly one person in frame, no foreground shoulder, hands out of frame, chest-up single close-up, facing the camera within 30 degrees."
                if s["kind"] == "d" else
                ("Completely unpopulated: no people, no hands." if s["kind"] in ("empty", "estill") or (s["kind"] == "ins" and not s["who"]) else
                 f"Exactly {n} {'person' if n == 1 else 'people'} (or their hands) as described, no extra people."))
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/{SKIT}-keyframes/{sid}-1.png"
        kf_prompt = None
        if keyframe:
            low = s["subject"].lower()
            real = " ".join(x for x, keys in ((TEARS, ("tear", "sob", "cry")), (SWEAT, ("sweat",))) if any(k in low for k in keys)
                            or (s["expr"] in ("sob",) and x == TEARS) or (s["expr"] in ("sob", "fear", "shock") and x == SWEAT))
            glasses = " ".join(GLASSES[w.split(":")[0]] for w in s["who"] if w.split(":")[0] in GLASSES)
            kf_prompt = " ".join([PRESET + ".", s["subject"], ("Characters: " + " | ".join(ids) + ".") if ids else "", glasses, real,
                                  f"Camera: {ANGLE[s['angle']]}, {LENS[s['lens']]}.", f"Lighting: {LIGHT[s['light']]}.", comp, PLAIN,
                                  f"Negative: {NEGATIVE}."]).strip()
            cost["kf"] += 1
        tier = {"d": "omni", "react": "still", "ins": "still", "estill": "still", "face": "pro", "sil": "lite", "empty": "lite", "card": "card"}.get(s["kind"], "reuse")
        if sid in LIVE:   # B안(고니감독님 승인 2026-10-12): 사람 정지 컷 → i2v 일반 화질, 실제 배우 같은 미세 연기
            tier = "lite"
            s = dict(s, motion=LIVE[sid])
        gen = 10 if d > 5.0 else 5
        item = {"prompt": "", "duration": gen}
        if tier in ("pro", "lite"):
            item["prompt"] = ("Static, locked off camera. Motion: " + (s["motion"] or "Subtle natural motion only.") +
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
                   "size": s["lens"], "lens": LENS[s["lens"]], "angle": s["angle"], "lighting": s["light"], "edit_fx": s["fx"],
                   "refs": refs, "subject": s["subject"], "line": s["line"],
                   "motion": item["prompt"] if tier in ("pro", "lite") else "", "keyframe": keyframe, "keyframe_prompt": kf_prompt,
                   "ja_overlay": JA_OVERLAY.get(sid, ""), "caption": CARDS.get(sid, "")})
    budget = round((cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"]) * 1.25, 2)

    # ---------- 음성: 시간 순 번호로 합치기(자막 TTS 줄 번호 = 캐시 번호) ----------
    tts_order = sorted([x for x in lock["lines"] if x["scene"].startswith("S") or x["tag"] == "NA0"],
                       key=lambda x: (x["start"] if x["start"] is not None else 9.5))
    dst = os.path.join(ROOT, "assets", "audio-overrides", SKIT)
    os.makedirs(dst, exist_ok=True)
    mapping = []
    for i, x in enumerate(tts_order, 1):
        src = os.path.join(ROOT, "assets", "auditions", "ashita-tts-add" if x["id"].startswith("P") else "ashita-tts", x["id"] + ".mp3")
        fit = os.path.join(ROOT, "assets", "auditions", "ashita-tts-fit", x["id"] + ".mp3")   # 회사명 재녹음을 Lock 슬롯에 맞춘 판(R45)
        if os.path.exists(fit):
            src = fit
        shutil.copyfile(src, os.path.join(dst, f"line{i:03d}.mp3"))
        mapping.append((f"line{i:03d}", x["tag"], x["id"]))

    # ---------- 자막(ASS) ----------
    events = []
    for i, x in enumerate(tts_order, 1):
        st = STYLE["NA" if x["spk"] == "NA" else x["spk"]]
        s0 = (9.5 - x["lead"]) if x["tag"] == "NA0" else (x["start"] - x["lead"])
        e0 = (9.5 + x["dur"] + 0.2) if x["tag"] == "NA0" else (x["end"] + 0.2)
        events.append((s0, e0, st, STYLE_JA[st], wrap(texts[x["tag"]])))
    for sid, cap in CARDS.items():
        c0 = starts[sid] + (0.3 if sid != "S12c" else 1.2)
        events.append((c0, min(ends[sid] - 0.2, c0 + 3.5), "Caption", "", cap))
    events.append((starts["H3"] + 0.6, ends["H3"] - 0.3, "Title", "", texts.get("TITLE", "明日から来なくていい") + "\\N{\\fs44}" + TITLE_SUB))
    events = [e for e in events if not (e[2] == "Caption" and e[4] == "明日から来なくていい")]  # 타이틀은 Title 스타일로
    h1 = rows["L22"]
    events.append((starts["H1"] + 0.6, starts["H1"] + 0.6 + h1["dur"] + 0.3, "HookLine", "田中", wrap(texts["L22"])))
    events.sort(key=lambda e: e[0])
    st_lines = "\n".join(
        f"Style: {n},Noto Sans CJK JP,{58 if n != 'Naration' else 52},{c},&H000000FF,&H00000000,&H80000000,-1,{-1 if n == 'Naration' else 0},0,0,100,100,0,0,1,5,2,2,200,200,80,1"
        for n, c in STYLE_COLOR.items())
    ass = ["[Script Info]", "Title: 明日から来なくていい 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           st_lines,
           "Style: HookLine,Noto Sans CJK JP,58,&H00B4D2FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1",
           "Style: Caption,Noto Sans CJK JP,84,&H001E1EFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,160,160,80,1",
           "Style: Title,Noto Serif CJK JP,110,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,5,160,160,80,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{e[4]}")
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    # ---------- 스토리보드·장면·오디오 ----------
    os.makedirs(os.path.join(ROOT, "scripts", "storyboard"), exist_ok=True)
    json.dump({"_설명": f"{SKIT} PHASE 3 스토리보드 Lock(build_ashita_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT,
               "preset": PRESET, "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"],
               "audio_map": mapping, "scenes": sb},
              open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"_설명": f"{SKIT} 장면 설정(build_ashita_phase3.py 생성). override_required 장면은 정지 푸시인·OMNI 정지 프레임·재사용·카드를 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, "
                         "wardrobe, props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": f"{SKIT} 조립·오디오(build_ashita_phase3.py 생성). 음성 {len(tts_order)}줄 = assets/audio-overrides/{SKIT}/ (Typecast 확정본, 배속 없음).",
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
        "_후크": "0~4초 BGM 없음: 경보 저음 드론(끊김 없이) + 심장 박동 1회를 PHASE 6에서 로컬 믹스(−60dB 2초 무음 금지 충족). "
                 "H1 화면은 S12c 재사용, 음성은 L22 원본을 0:04.6에 로컬 믹스. H2 내레이션 NA0은 자막 1번 줄(TTS 캐시 line001).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---------- 검토 문서 ----------
    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    top = ang.most_common(1)[0]
    md = ["# 『明日から来なくていい』 PHASE 3 샷 리스트", "",
          f"> `scripts/build_ashita_phase3.py` 자동 생성(손 수정 금지). 타임코드는 분:초.프레임(24fps). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " +
          ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock["ads"]) + ".",
          "> 자동 검사 통과: 연속 같은 구도 0 · 돌리줌 1회 · 더치 2회 · OMNI 정면~45° · 화자-화면 일치 · 대사 88줄 전부 배치 · 컷 길이(1.2초 이상, 정지 6.5초·i2v 10초 이하) · OMNI 8초 이하.", "",
          "## 비용 추산 (실측 단가)", "",
          "| 항목 | 수량 | 단가 | 금액 |", "|---|---|---|---|",
          f"| 키프레임 | {cost['kf']}장 | 0.04 | {cost['kf'] * RATE['kf']:.2f} |",
          f"| i2v pro 1080p (얼굴) | {cost['pro']}초 | 0.108 | {cost['pro'] * RATE['pro']:.2f} |",
          f"| i2v lite 720p (실루엣·무인) | {cost['lite']}초 | 0.036 | {cost['lite'] * RATE['lite']:.2f} |",
          f"| OmniHuman (8초 상한 + 앞뒤 0.8초) | {cost['omni']:.1f}초 | 0.16 | {cost['omni'] * RATE['omni']:.2f} |",
          f"| **1차 합계** (재생성 여유 제외) | | | **{total_cost:.2f}** |",
          f"| i2v 예산 상한 `budget_usd` (여유 25%) | | | {budget:.2f} |", "",
          "## 생성 방식 분포", "", "| 방식 | 컷 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in tiers.most_common()] + [
          "", f"## 앵글 분포 (생성 컷) — 최다 {top[0]} {top[1] / sum(ang.values()) * 100:.0f}% (60% 이하 기준 충족)", "", "| 앵글 | 컷 |", "|---|---|"] + [
          f"| {k} | {v} |" for k, v in ang.most_common()] + [
          "", "## 화면 속 일본어 (키프레임은 무지 → `ja_text_overlay.py` 합성)", ""] + [f"- {k}: {v}" for k, v in JA_OVERLAY.items()] + [
          "", "## 샷 표", "", "| 컷 | 타임코드 | 길이 | 방식 | 사이즈 | 앵글 | 조명 | 편집 효과 | 대사 | 참조 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in sb:
        md.append(f"| {x['id']} | {x['timecode']} | {x['assembled_s']:.2f}s | {x['tier']} | {x['size']} | {x['angle']} | {x['lighting']} | {x['edit_fx']} | {x['line'] or ''} | {len(x['refs'])}장 |")
    md += ["", "## 음성 번호 대응 (자막 TTS 줄 = 캐시 파일)", "", "| 캐시 | 대본 | 원본 녹음 |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in mapping]
    open(os.path.join(PROD, "07_샷리스트.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    emotion_table(sb)
    print(f"완료: 컷 {len(SHOTS)}개, 본편 {tc(main_end)}, 방식 {dict(tiers)}, 1차 비용 약 {total_cost:.2f}달러 (i2v budget {budget}), 앵글 {dict(ang)}")


# ---------- 감정 일치표(제10장 7) ----------
# 음성 감정(톤연출표) ↔ 키프레임 표정(expr·subject) ↔ 동작(i2v LIVE / 립싱크 OMNI_ACT)이 어긋나면 경고.
EMO_OK = {   # 감정 → 화면에 있어야 할 신호(하나 이상)
    "angry": ("anger", "fury", "rage", "glare", "condemn", "furious", "shout", "jaw", "restrained", "sneer", "cruel", "slam", "fist", "panick"),
    "happy": ("smile", "smirk", "sneer", "laugh", "grin", "mock", "pleased", "satisf", "condescend", "scoff"),
    "sad": ("sob", "tear", "cry", "beg", "plea", "sad", "tremb"),
    "tonedown": ("cold", "quiet", "calm", "restrain", "grave", "low", "icy", "earnest", "silence", "gentle", "steady", "firm"),
    "toneup": ("alarm", "panic", "shock", "excite", "fright", "urgent", "mock", "breezy", "careless", "dismiss"),
    "normal": (),
}
EMO_BAD = {   # 감정과 정면으로 부딪히는 신호(연기 메모에 의도가 없으면 경고)
    "angry": ("sob", "tear", "gentle", "peaceful"),
    "happy": ("sob", "tear", "fury", "rage"),
    "sad": ("smile", "smirk", "laugh", "grin", "sneer"),
    "tonedown": ("shout", "laugh", "slam"),
}
INTENDED = ("비웃", "즐기", "깔보", "억누른", "서늘", "냉정", "차갑")   # 연기 메모의 의도된 예외(분노+비웃음 등)


def emotion_table(sb):
    import sys
    sys.path.insert(0, PROD)
    from build_tts_spec import TONE
    rows, warn = [], 0
    for x in sb:
        tag = x["line"]
        if not tag or tag not in TONE or tag.startswith(("NA", "OUT")):
            continue
        emo, inten, tempo, memo = TONE[tag]
        act = OMNI_ACT.get(x["id"]) or LIVE.get(x["id"]) or x.get("motion") or ""
        seen = " ".join([x["subject"], act]).lower()
        ok = not EMO_OK.get(emo) or any(k in seen for k in EMO_OK[emo])
        bad = [k for k in EMO_BAD.get(emo, ()) if k in seen]
        intended = any(k in memo for k in INTENDED)
        state = "✅" if ok and (not bad or intended) else "⚠️"
        if state == "⚠️":
            warn += 1
        how = "립싱크" if x["tier"] == "omni" else ("i2v" if x["tier"] in ("lite", "pro") else "정지")
        rows.append(f"| {state} | {x['id']} | {tag} | {how} | {emo} {inten} · {tempo} | {memo} | {x['subject'][:70]} | {act[:90]} |")
    md = ["# 감정 일치표 — 음성 톤 · 표정 · 동작 (CLAUDE.md 제10장 7, build_ashita_phase3.py 생성)", "",
          f"> 대사 컷 {len(rows)}개 · 경고 {warn}개. ⚠️ = 음성 감정과 화면 표정·동작이 맞지 않거나 부딪힘(연기 메모에 의도가 없으면 키프레임·동작 문장을 고친다).", "",
          "| 판정 | 컷 | 대사 | 방식 | 음성 감정·세기·템포 | 연기 메모 | 화면(표정·구도) | 동작·연기 지시 |", "|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(PROD, "16_감정일치표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"감정 일치표: 대사 컷 {len(rows)}개, 경고 {warn}개 → 16_감정일치표.md")


if __name__ == "__main__":
    main()
