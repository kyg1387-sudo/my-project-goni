#!/usr/bin/env python3
"""『地下倉庫の伝票』(chika) PHASE 3 샷 리스트 Lock 생성기 — 일본어판 #02 (build_tower_phase3.py 구조 계승).

입력(동결본, 손으로 옮겨 적지 않는다):
  productions/chika-souko-ja/lock.json        PHASE 1 Lock(실측 줄 타임코드·장면 경계·광고 지점)
  productions/chika-souko-ja/00_script_ja.md  대본 v2.1(자막 원문)
  assets/auditions/chika-tts/lineNNN.mp3      확정 음성(앞뒤 무음을 잘라 assets/audio-overrides/chika/로 복사)
출력:
  scripts/storyboard/chika.json   샷 스펙(PHASE 4 키프레임·PHASE 5 입력)
  scripts/scenes/chika.json       장면 생성 설정(i2v·override_required·budget_usd·히어로 컷)
  scripts/audio/chika.json        조립·오디오(장면 길이·OmniHuman·BGM·효과음)
  subs/chika.ass                  일본어 자막(대사 65줄 + 카드·강조 자막)
  productions/chika-souko-ja/07_샷리스트.md, 02_카메라앵글설계.md
규칙: CLAUDE.md 제0~9장, 03_시네마규격.json(B안), 제8장 자동 검사. 아웃트로(진행자 4줄)는 PHASE 6 append_outro로 별도.
사용법: python3 scripts/build_chika_phase3.py
"""
import collections
import json
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "chika-souko-ja")
sys.path.insert(0, PROD)
from build_tts import load_lines, SAME_AS  # noqa: E402

SKIT = "chika"
FPS = 24
HARD = 1 / FPS
OMNI_MAX = 7.9
LEAD = 0.3
MIN_SHOT = 1.2
STILL_MAX = 6.5
I2V_MAX = 10.0
SHOT_TARGET = 1.6
TRIM_PRE, TRIM_POST = 0.05, 0.12
N_LINES = 65  # 본편 줄 수(아웃트로 66~69 제외)

C = "assets/portraits/chika-cast/cells/"
WHO = {
    "SAORI": ("Saori, a Japanese woman aged 34, slim, soft oval face, straight black shoulder-length hair with bangs and the upper half tied back in a small knot, thin silver-rimmed glasses", C + "saori-front.png"),
    "SAORI_B": ("Saori, a Japanese woman aged 34, slim, soft oval face, straight black shoulder-length hair with bangs and the upper half tied back in a small knot, thin silver-rimmed glasses", C + "saori-b-front.png"),
    "SAORI_E": ("Saori, a Japanese woman aged 34, slim, soft oval face, straight black shoulder-length hair with bangs tied back in a low bun, thin silver-rimmed glasses", C + "saori-e-front.png"),
    "GONDO": ("Gondo, a heavyset Japanese man aged 52, fleshy face with a double chin, salt-and-pepper hair slicked straight back, thick gold-rimmed rectangular glasses, bare lapels with no pin", C + "gondo-front.png"),
    "MIYAMOTO": ("Miyamoto, a thin kindly Japanese man aged 64, short white hair, a full bushy white moustache, half-moon reading glasses hanging on a black cord around his neck (not on the face)", C + "miyamoto-front.png"),
    "KIRITANI": ("Kiritani, a lean Japanese man in his early 50s, hollow cheeks, short neatly parted black hair with grey temples, frameless rimless glasses, cold level gaze", C + "kiritani-front.png"),
    "OKOCHI": ("Okochi, a dignified Japanese company president in his mid-60s, square jaw, short silver hair, thick dark eyebrows, NO glasses", C + "okochi-front.png"),
    "AUDIT": ("five internal-audit staff in plain dark suits seen as backlit silhouettes or from behind, faces unrecognizable", None),
    "STAFF": ("a few office colleagues seen from behind or as soft out-of-focus shapes, faces unrecognizable", None),
    "CROWD": ("banquet guests in dark suits and dresses seen as soft out-of-focus shapes or from behind, faces unrecognizable", None),
    "GUARD": ("a uniformed security guard seen only from behind or by his hands, face unrecognizable", None),
}
WARD = {
    "SAORI": "a plain navy-blue tailored skirt suit over a plain white blouse, a slim black leather-strap wristwatch on the left wrist, bare lapels with no pin",
    "SAORI_B": "a plain light-grey crew-neck knit sweater, a plain navy canvas work apron, dark blue jeans, a slim black leather-strap wristwatch on the left wrist",
    "SAORI_E": "a plain charcoal-grey tailored pantsuit over a plain ivory silk blouse, a slim black leather-strap wristwatch on the left wrist",
    "GONDO": "a glossy navy double-breasted suit, white shirt, plain wine-red silk tie, a chunky plain gold wristwatch on the right wrist, bare lapels with no pin",
    "MIYAMOTO": "a plain beige wool cardigan over a plain grey shirt, grey cotton arm-sleeve protectors, plain dark grey trousers",
    "KIRITANI": "a plain black business suit, white shirt, plain silver-grey tie, bare lapels with no pin",
    "OKOCHI": "a charcoal three-piece suit, white shirt, plain dark grey tie, a plain white pocket square, bare lapels with no pin",
}
EXPR = {
    ("SAORI", "neutral"): C + "saori-expr1.png", ("SAORI", "anger"): C + "saori-expr2.png",
    ("SAORI_B", "focus"): C + "saori-b-expr1.png", ("SAORI_B", "fear"): C + "saori-b-expr2.png", ("SAORI_B", "resolve"): C + "saori-b-expr3.png",
    ("SAORI_E", "smile"): C + "saori-e-expr1.png", ("SAORI_E", "nostalgic"): C + "saori-e-expr2.png",
    ("GONDO", "sneer"): C + "gondo-expr1.png", ("GONDO", "laugh"): C + "gondo-expr2.png", ("GONDO", "panic"): C + "gondo-expr3.png",
    ("MIYAMOTO", "smile"): C + "miyamoto-expr1.png", ("MIYAMOTO", "wistful"): C + "miyamoto-expr3.png",
    ("KIRITANI", "stern"): C + "kiritani-expr2.png", ("KIRITANI", "doubt"): C + "kiritani-expr3.png",
    ("OKOCHI", "calm"): C + "okochi-expr1.png", ("OKOCHI", "stern"): C + "okochi-expr2.png", ("OKOCHI", "smile"): C + "okochi-expr3.png",
}
LOC = {
    "AUD_WIDE": C + "loc-aud-wide.png", "AUD_STAGE": C + "loc-aud-stage-side.png", "AUD_LAST": C + "loc-aud-lastrow.png", "AUD_SCREEN": C + "loc-aud-screen.png",
    "OFF_WIDE": C + "loc-off-wide.png", "OFF_PART": C + "loc-off-partition.png", "OFF_AISLE": C + "loc-off-wide2.png", "OFF_BIN": C + "loc-off-bin.png",
    "EV_HALL": C + "loc-ev-hall.png", "EV_OPEN": C + "loc-ev-open.png", "EV_GAP": C + "loc-ev-gap.png", "EV_IN": C + "loc-ev-inside.png",
    "ARC_WIDE": C + "loc-arc-wide.png", "ARC_DESK": C + "loc-arc-desk.png", "ARC_AISLE": C + "loc-arc-aisle.png", "ARC_LADDER": C + "loc-arc-ladder.png",
    "ARC_NDESK": C + "loc-arcv-night-desk.png", "ARC_NDOOR": C + "loc-arcv-night-door.png", "ARC_END": C + "loc-arcv-ending-wide.png", "ARC_BOX": C + "loc-arcv-ending-box.png",
    "ARC_REV": C + "angle-arc-reverse.png", "ARC_THRU": C + "angle-arc-through.png", "ARC_HIGH": C + "angle-arc-high.png", "ARC_LOW": C + "angle-arc-low.png",
    "COR_WIDE": C + "loc-cor-wide.png", "COR_BACK": C + "loc-cor-backlit.png", "COR_FLOOR": C + "loc-cor-floor.png", "COR_PIPES": C + "loc-cor-pipes.png",
    "BQ_WIDE": C + "loc-bq-wide.png", "BQ_STAGE": C + "loc-bq-stage.png", "BQ_DOORS": C + "loc-bq-doors.png", "BQ_TABLE": C + "loc-bq-table.png",
    "BQ_REV": C + "angle-bq-reverse.png", "BQ_HIGH": C + "angle-bq-high.png", "BQ_LOW": C + "angle-bq-low.png", "BQ_GLASS": C + "angle-bq-glasses.png",
    "P_CASE": C + "prop-case.png", "P_WATCH": C + "prop-watch.png", "P_TRIPOD": C + "prop-tripod.png",
}
PRESET = ("Photorealistic live-action Japanese corporate drama, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, "
          "mid-size Tokyo trading company mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, "
            "logo on shirt, brand logos, lapel pin, company badge, signage lettering, posters with writing, printed labels, "
            "watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people")
PLAIN = "All papers, screens, signs, banners, box labels and plates are completely blank; no letters, numbers or symbols anywhere in the frame."
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the subject fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait",
    "ch": "85mm prime lens, f/1.8, choker framing from forehead to chin, razor-sharp eyes, soft bokeh",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective, sharp architectural lines",
}
LIGHT = {
    "aud": "dim auditorium, the big screen's cool white-blue glow as key light, warm stage downlight on the podium, deep shadows in the seats",
    "office": "cold even fluorescent ceiling light 5600K from directly above, faint cool cast, soft shadows under the brow",
    "office_press": "hard cold fluorescent top light pressing down, 5600K, dark eye sockets and chin shadow, oppressive chiaroscuro",
    "ev": "cool fluorescent light, hard cold reflections on brushed steel, cold oppressive mood",
    "arc": "cold flickering fluorescent tubes overhead casting hard top light, dust in the air, deep shadows between the racks",
    "arc_lamp": "one warm 3200K tungsten desk lamp making a pool of warm light, cold dim fluorescent fill far behind, dust motes, Rembrandt shadow on the face",
    "arc_night": "night, the cool blue glow of a laptop screen on the face and glasses, a warm desk lamp pool beside it, everything else black",
    "arc_fear": "night, a single cold fluorescent tube far away, blinding cold light pouring through the open steel door behind the figure, strong backlight silhouette, darker interior",
    "arc_end": "warm soft orange practical light strung along the racks, low contrast, gentle glow, dust in the air",
    "cor": "night corridor, one cold fluorescent tube far down, deep shadows, cold cyan cast",
    "bq": "warm 3200K crystal chandeliers, golden ambient fill, specular highlights on crystal glasses, subtle warm rim light on hair",
    "bq_press": "warm chandelier light but a hard key from above on the face, dark eye sockets, tense chiaroscuro, specular glass highlights",
    "bq_cold": "the chandelier glow dimmed, a colder blue-white key from the stage screen, high-contrast chiaroscuro, rim light on hair",
    "bq_proj": "a cold blue projector beam cutting through floating dust motes from behind the figure, strong backlight, the face in shadow, warm chandeliers dim",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "extreme bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None, hero=False):
    """kind: d(OMNI 대사) / react(리액션 정지) / ins(인서트 정지) / face(얼굴 i2v pro) / sil(실루엣·뒷모습 i2v lite) /
    empty(무인 i2v lite) / estill(무인 정지) / gfx(로컬 그래픽 합성, 무료) / reuse:<id> / card.  hero=True: 상위 모델 3테이크(B안)."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc,
                subject=subject, line=line, fx=fx, motion=motion, expr=expr, hero=hero)


OMNI_COMMON = "Static camera. Keep the exact face, hair, wardrobe and background. Natural lip movement matching the Japanese speech, subtle breathing, natural blinks. Head turns stay under 15 degrees, hands stay out of frame. "
OMNI_PROMPTS = {
    "S01b": "Cold and composed: level unblinking gaze, almost no movement, one slow blink.",
    "S02b": "Theatrical self-congratulation: chin raised, a proud smile, a small sweeping glance across the audience.",
    "S03c": "Suppressed anger: jaw tight, voice trembling slightly, eyes glistening but dry, a small shake of the head at the end.",
    "S03d": "Condescending lecture: half-lidded eyes, a thin sneer, one slow dismissive nod.",
    "S03f": "Stunned disbelief: eyebrows raised, lips parted, a small confused tilt of the head.",
    "S03g": "Cold threat: low voice, eyes narrowed, a slow lean toward the camera within 10 degrees, no smile at the end.",
    "S05b": "Mocking contempt: a wide sneer that widens on the last phrase, chin raised, eyes looking down.",
    "S06c": "Warm weary kindness: a gentle smile, slow speech, a small nod of greeting.",
    "S08b": "Quiet long-suppressed confession: eyes lowered then raised, slow speech, a faint bitter smile.",
    "S08c": "Bitter resignation: a small shrug of the shoulders, a tired half-smile, eyes distant.",
    "S08e": "Quiet steel: steady eyes forward, a slow deliberate pace, a small firm nod at the end.",
    "S11c": "Fear held in check: wide steady eyes, a swallow before speaking, minimal movement, voice controlled.",
    "S12b": "Drunken triumph: flushed grin, chin up, a loud laugh in the eyes, small excited head movements.",
    "S12c": "Greedy relish: half-lidded eyes, a slow satisfied smile, a small nod on the money line.",
    "S13b": "Drunk mockery right after laughing: a broad sneer, eyes glittering, chin thrust forward.",
    "S14b": "Bluster covering panic: raised eyebrows, a forced angry frown, quick shallow breaths, no head turning.",
    "S14c": "Cold formal verdict: expressionless, level gaze, one word at a time, almost no movement.",
    "S14e": "Dry recital of charges: same cold stillness, a single slow blink.",
    "S15a": "Desperate accusation: wide furious eyes, the face reddening, small sharp head jerks, sweat at the temples.",
    "S15b": "Breaking down while shouting: eyes wild, voice cracking, trembling jaw, no laughing.",
    "S15e": "Calm unshakable correction: steady eyes straight into the camera, a slow blink, no smile.",
    "S15f": "Precise and composed: level gaze, measured pace, the faintest lift of the chin.",
    "S15g": "Quiet stern rebuke: lowered brows, slow speech, a small disappointed shake of the head.",
    "S15h": "Callback delivered softly: a faint cool smile, eyes steady, a brief pause before the last phrase.",
    "S15j": "Low final warning: unhurried, eyes fixed, no smile, a slow nod at the end.",
    "S16b": "Calm commanding authority: steady unblinking gaze, slow heavy speech, dignified stillness.",
    "S16c": "Probing question: one eyebrow slightly raised, a small forward lean within 10 degrees, pause at the end.",
    "S16f": "Clear and proud: steady eyes, confident pace, a small nod on the numbers.",
    "S16g": "Cool callback: a faint smile that does not reach the eyes, measured pace, a brief pause before the last phrase.",
    "S16h": "First warm approving smile: eyes crinkling, a slow nod, relaxed authority.",
    "S16j": "The final blow, quiet and precise: eyes looking slightly down at the camera, a long pause before the last phrase, no smile, absolute stillness.",
    "S18b": "Playful warm greeting: a broad smile, a small welcoming nod.",
    "S18c": "Gentle laugh then wistful: a soft smile, eyes glancing up at the racks then back, relaxed.",
    "S18e": "Wistful confession: eyes drifting to the distance, a slow sad-sweet smile, a long exhale.",
}

SHOTS = [
    # ── ① 후크 S01 (플래시포워드, 연회장 밤)
    S("S01a", "S01", "sil", "ws", "bq_cold", "LA", ["AUDIT"], "BQ_DOORS",
      "Low angle from the red carpet: the double doors of the banquet hall have just burst open, five internal-audit staff stand backlit in the doorway as dark silhouettes, cold light flooding past them, chandeliers above.",
      motion="The silhouettes take two slow steps forward into the hall; the doors stay open. No one else enters.", hero=True),
    S("S01b", "S01", "d", "cu", "bq_cold", "EL", ["KIRITANI"], "BQ_WIDE",
      "Chest-up close-up of Kiritani just inside the doorway, expressionless, rimless glasses catching a cold glint, blurred chandeliers and guests far behind.", line="line001", expr="stern"),
    S("S01c", "S01", "face", "ecu", "bq_press", "HA", [], "BQ_TABLE",
      "High angle extreme close-up: a crystal wine glass slipping from a fat hand with a gold wristwatch, red wine arcing out, the glass about to shatter on the red carpet. Only the hand is visible.",
      motion="Slow motion: the glass tumbles, hits the carpet and shatters, wine splashing outward. The hand does not move. No face.", hero=True),
    S("S01d", "S01", "react", "cu", "bq_press", "LA", ["GONDO"], "BQ_STAGE",
      "Low angle chest-up of Gondo frozen mid-sneer, the smile collapsing, gold glasses, blurred chandeliers above.", line="line002", expr="panic"),
    S("S01e", "S01", "react", "ms", "bq_cold", "EL", ["SAORI_B"], "BQ_WIDE",
      "Medium shot of Saori standing alone among the tables in a grey knit and jeans, a folded navy apron in one hand at her side, calm face, guests blurred around her.", line="line003", expr="resolve"),
    S("S01f", "S01", "ins", "ecu", "arc_lamp", "OH", [], "ARC_DESK",
      "Overhead extreme close-up: a single old yellowed voucher sheet lying under a warm desk lamp on a worn wooden desk, a faded red seal ring on it, dust motes in the beam.", line="line004"),
    S("S01g", "S01", "card", "ews", "arc", "EL", [], "ARC_WIDE", "Title card over the dark archive."),
    S("S01h", "S01", "card", "ews", "arc", "HA", [], "ARC_WIDE", "Caption card: 二か月前."),
    # ── ② S02 대강당
    S("S02a", "S02", "empty", "ews", "aud", "EL", ["STAFF"], "AUD_WIDE",
      "Wide view from the back of the company auditorium over rows of seated employees (dark shapes from behind) toward the stage: a podium and a very large blank glowing screen.",
      motion="Almost still; a faint shimmer of the screen light over the seated heads. Nobody stands or turns.", hero=True),
    S("S02b", "S02", "d", "cu", "aud", "LA", ["GONDO"], "AUD_STAGE",
      "Low angle chest-up of Gondo at the podium, proud smile, chin raised, gold glasses reflecting the screen glow, the blank screen soft behind.", line="line005", expr="sneer"),
    S("S02c", "S02", "gfx", "ecu", "aud", "EL", [], "AUD_SCREEN",
      "Extreme close-up of the lower right corner of the glowing blank presentation screen, slightly out of focus at the edges."),
    S("S02d", "S02", "gfx", "ecu", "aud", "LA", [], "AUD_SCREEN",
      "Extreme close-up of the centre of the blank glowing presentation screen."),
    S("S02e", "S02", "sil", "ws", "aud", "HA", ["STAFF"], "AUD_LAST",
      "High angle over the last rows: many employees applauding seen from behind, hands raised in soft motion, faces unrecognizable, the bright screen far ahead.",
      motion="Hands clap softly, a few heads nod. Nobody turns around."),
    S("S02f", "S02", "react", "cu", "aud", "EL", ["SAORI"], "AUD_LAST",
      "Chest-up close-up of Saori in the last row, not clapping, cold steady eyes fixed on the stage, glasses reflecting the screen, seats blurred around her.", line="line006", expr="neutral"),
    S("S02g", "S02", "ins", "ecu", "aud", "HA", ["SAORI"], "AUD_LAST",
      "High angle extreme close-up: a woman's hands clasped tightly in her lap on a navy skirt, knuckles white, a thin black leather watch strap, seat edges blurred."),
    # ── S03 기획부 사무실 (공개 굴욕)
    S("S03a", "S03", "empty", "ws", "office", "EL", ["STAFF"], "OFF_WIDE",
      "Wide view down the central aisle of the planning department, colleagues at their desks seen as soft shapes, cold fluorescent panels above.", line="line007",
      motion="A colleague far away shifts slightly in a chair; otherwise still. Nobody walks."),
    S("S03b", "S03", "ins", "ecu", "office", "HA", ["GONDO"], "OFF_WIDE",
      "High angle extreme close-up: a fat right hand with a chunky gold wristwatch resting on a grey desk, fingers drumming, a blank document under it."),
    S("S03b2", "S03", "estill", "ecu", "office", "OH", [], "OFF_PART",
      "Overhead extreme close-up: a neat stack of blank white documents on a grey desk, a plain black pen laid across them, cold fluorescent light."),
    S("S03c", "S03", "d", "cu", "office", "EL", ["SAORI"], "OFF_PART",
      "Chest-up close-up of Saori standing at a desk, jaw tight, eyes glistening but dry, the frosted partition and blurred colleagues behind.", line="line008", expr="anger"),
    S("S03d", "S03", "d", "cu", "office_press", "LA", ["GONDO"], "OFF_WIDE",
      "Low angle chest-up of Gondo seated at his desk looking up with a thin sneer, hard top light making dark eye sockets behind the gold glasses, desks blurred behind.", line="line009", expr="sneer"),
    S("S03e", "S03", "ins", "ecu", "office", "HA", [], "OFF_BIN",
      "High angle extreme close-up: a thick stack of blank papers studded with blank yellow sticky notes dropping into a steel wastebasket beside a desk leg."),
    S("S03e2", "S03", "sil", "ms", "office", "SIDE", ["STAFF"], "OFF_AISLE",
      "Medium from the side: three colleagues at their desks turning their faces away toward their monitors, seen from behind and in soft focus, no faces.", line="line010",
      motion="The colleagues lower their heads slightly and keep typing. Nobody looks up or walks."),
    S("S03f", "S03", "react", "cu", "office", "HA", ["SAORI"], "OFF_PART",
      "High angle chest-up of Saori, eyebrows raised in disbelief, lips slightly parted, the frosted partition behind.", line="line011", expr="neutral"),
    S("S03g", "S03", "d", "cu", "office_press", "LA", ["GONDO"], "OFF_WIDE",
      "Low angle chest-up of Gondo leaning slightly forward, eyes narrowed behind gold glasses, hard top light, cold threat, no smile.", line="line012", expr="sneer"),
    S("S03h", "S03", "react", "cu", "office", "HA", ["SAORI"], "OFF_PART",
      "High angle chest-up of Saori looking down, face rigid, only her eyes trembling, glasses catching the cold light.", expr="anger"),
    # ── S04 발령·USB
    S("S04a", "S04", "gfx", "ecu", "office", "EL", [], "OFF_PART",
      "Extreme close-up of a blank dark monitor screen on a desk, a faint blue-white glow, the office dim around it."),
    S("S04b", "S04", "sil", "ms", "office", "SIDE", ["SAORI"], "OFF_AISLE",
      "Side view medium: Saori seen from behind reading something on her monitor, shoulders still, the office empty and dim.", line="line013",
      motion="She sits motionless, then slowly lowers her head a few centimetres. No turning."),
    S("S04c", "S04", "ins", "ecu", "office", "HA", [], "OFF_BIN",
      "High angle extreme close-up in a dark office at night: one hand passing a small plain black USB memory stick to another hand across a desk, a single desk lamp glow, no faces."),
    # ── S05 엘리베이터 홀
    S("S05a", "S05", "sil", "ws", "ev", "SIDE", ["SAORI", "GONDO"], "EV_HALL",
      "Wide from the side: Saori seen from behind holding a plain cardboard box in front of the steel elevators, Gondo's bulky figure approaching from the far right as a soft shape.", fx="dutch5 handheld",
      motion="Gondo walks two slow steps closer and stops; Saori stays still facing the elevators. No one turns to the camera."),
    S("S05b", "S05", "d", "cu", "ev", "LA", ["GONDO"], "EV_HALL",
      "Low angle chest-up of Gondo sneering widely, gold glasses, cold steel doors blurred behind him.", line="line014", expr="sneer"),
    S("S05c", "S05", "react", "cu", "ev", "EL", ["SAORI"], "EV_OPEN",
      "Chest-up close-up of Saori inside the open mirrored elevator holding a box against her chest (only the box top visible), face rigid, eyes steady.", expr="anger"),
    S("S05d", "S05", "face", "ecu", "ev", "EL", ["SAORI"], "EV_GAP",
      "Extreme close-up of the brushed-steel elevator doors closing, a narrow vertical gap showing a slice of Saori's rigid face and glasses inside.",
      motion="The steel doors slide shut slowly until the gap of light disappears. Nothing else moves.", hero=True),
    # ── S06 지하 문서관리실
    S("S06a", "S06", "empty", "ews", "arc", "EL", [], "ARC_WIDE",
      "Wide from the steel door down the central aisle of the basement archive: racks converging to a vanishing point, one fluorescent tube flickering on with a stutter, dust in the air.",
      motion="The tube flickers twice then stays on; dust drifts. No people.", hero=True),
    S("S06b", "S06", "sil", "ms", "arc_lamp", "SIDE", ["MIYAMOTO"], "ARC_DESK",
      "Medium from the side: Miyamoto at the corner desk under the warm lamp lowering his half-moon glasses, seen in profile, a flatbed scanner beside him.",
      motion="He lowers the glasses from his nose and lets them hang on the cord, then looks up slightly. No standing up."),
    S("S06c", "S06", "d", "cu", "arc_lamp", "EL", ["MIYAMOTO"], "ARC_DESK",
      "Chest-up close-up of Miyamoto, warm lamp light on one side of his face, a gentle smile under the bushy white moustache, racks dark behind.", line="line015", expr="smile"),
    S("S06d", "S06", "sil", "ws", "arc", "HA", ["SAORI_B"], "ARC_HIGH",
      "High angle from the top of a rack: Saori, small in the frame in a grey knit and navy apron, standing in the aisle looking up at the racks, a box in her arms.",
      motion="She turns her head slowly to look along the shelves, then stands still. No walking."),
    S("S06e", "S06", "ins", "ecu", "arc_lamp", "HA", [], "ARC_DESK",
      "High angle extreme close-up: the flatbed scanner lid lifting, a yellowed blank voucher sheet laid on the glass, a bar of light sweeping underneath.", line="line016"),
    S("S06f", "S06", "ins", "ecu", "arc_lamp", "EL", [], "P_TRIPOD",
      "Extreme close-up: a woman's hands setting a plain black smartphone on a small black mini tripod on the wooden desk, the lens pointing at the scanner, lamp light warm."),
    S("S06g", "S06", "react", "cu", "arc_lamp", "EL", ["SAORI_B"], "ARC_DESK",
      "Chest-up close-up of Saori at the desk, glasses reflecting the lamp, a quiet knowing look, racks dark behind.", line="line017", expr="focus"),
    S("S06g2", "S06", "ins", "ecu", "arc", "HA", ["SAORI_B"], "ARC_AISLE",
      "High angle extreme close-up: a woman's hands lifting the dusty lid of a yellowed cardboard archive box on a shelf, a blank white label on its side, dust rising in the cold light."),
    S("S06h", "S06", "sil", "ms", "arc", "SIDE", ["MIYAMOTO"], "ARC_AISLE",
      "Medium from behind: Miyamoto walking slowly away down a narrow rack aisle, one hand trailing along the boxes, back to the camera.", line="line018",
      motion="He walks slowly away from the camera between the racks without turning around. No one else."),
    S("S06i", "S06", "react", "cu", "arc", "HA", ["SAORI_B"], "ARC_AISLE",
      "High angle chest-up of Saori in the aisle looking up after him, the apron strap on her shoulder, a thoughtful frown behind the glasses, boxes blurred around.", expr="focus"),
    # ── S07 3주 후, 전표 발견 (1차 광고 직전)
    S("S07a", "S07", "ins", "ecu", "arc_lamp", "HA", [], "ARC_DESK",
      "High angle extreme close-up: the scanner's bar of light sweeping under the glass, another yellowed sheet, the pile beside it shorter."),
    S("S07b", "S07", "estill", "ws", "arc", "EL", [], "ARC_LADDER",
      "Wide: the steel step-ladder against the rack, the top shelf half emptied of boxes, dust in the fluorescent light."),
    S("S07c", "S07", "ins", "ecu", "arc_lamp", "OH", ["SAORI_B"], "ARC_DESK",
      "Overhead extreme close-up: a woman's hand holding a yellowed voucher sheet under the lamp suddenly stopping, fingertips pressed on a faded red seal ring, the paper otherwise blank."),
    S("S07d", "S07", "gfx", "ecu", "arc_lamp", "EL", [], "ARC_DESK",
      "Extreme close-up of one old yellowed voucher sheet with faint blank ruled boxes held up to the lamp, a soft red seal ring in one box, no writing.", line="line019"),
    S("S07e", "S07", "ins", "ecu", "arc_lamp", "OH", [], "ARC_DESK",
      "Overhead extreme close-up: ten identical yellowed voucher sheets fanned out across the wooden desk under the lamp, each with the same faded red seal ring in the same corner, no writing.", hero=True),
    S("S07f", "S07", "react", "cu", "arc_lamp", "EL", ["SAORI_B"], "ARC_DESK",
      "Chest-up close-up of Saori staring down at the desk, lamp light from below her face, eyes widening slowly behind the glasses.", expr="focus"),
    # ── ③ S08 미야모토의 고백 (1차 광고 뒤)
    S("S08a", "S08", "sil", "ms", "arc", "SIDE", ["MIYAMOTO"], "ARC_THRU",
      "Seen through a gap between boxes on a shelf, boxes blurred in the foreground: Miyamoto approaching the corner desk slowly, seen from the side.",
      motion="He takes three slow steps toward the desk and stops. No turning to the camera."),
    S("S08b", "S08", "d", "cu", "arc_lamp", "EL", ["MIYAMOTO"], "ARC_DESK",
      "Chest-up close-up of Miyamoto, eyes lowered then lifting, warm lamp light, the bushy white moustache, a quiet grave look.", line="line020", expr="wistful"),
    S("S08b2", "S08", "react", "cu", "arc_lamp", "HA", ["SAORI_B"], "ARC_DESK",
      "Chest-up close-up of Saori listening, lips pressed, the voucher held low out of frame, lamp light on her glasses.", expr="focus"),
    S("S08b2b", "S08", "estill", "ws", "arc", "LA", [], "ARC_LOW",
      "Low angle from the floor looking up between two towering racks of yellowed boxes, one cold tube glaring, dust drifting, no people."),
    S("S08c", "S08", "sil", "ms", "arc", "SIDE", ["MIYAMOTO"], "ARC_AISLE",
      "Medium from the side and slightly behind: Miyamoto turning toward the dark racks with one hand resting on a yellowed box, his face away from the camera, cold tube light above.", line="line021",
      motion="He rests his hand on the box and lowers his head slowly. He does not turn to the camera."),
    S("S08b3", "S08", "ins", "ecu", "arc_lamp", "OH", ["SAORI_B"], "ARC_DESK",
      "Overhead extreme close-up: a woman's fingertips resting on a yellowed voucher on the desk under the lamp, the red seal ring beside them, the paper otherwise blank."),
    S("S08d", "S08", "ins", "ecu", "arc", "LA", ["SAORI_B"], "ARC_DESK",
      "Low angle extreme close-up: a woman's hand holding a yellowed voucher up against the fluorescent tube, the paper glowing translucent, the red seal ring showing through."),
    S("S08e", "S08", "d", "cu", "arc_lamp", "EL", ["SAORI_B"], "ARC_DESK",
      "Chest-up close-up of Saori, quiet steel in her eyes, a small firm set of the jaw, lamp light warm on one side.", line="line022", expr="resolve"),
    # ── S09 심야 몽타주, 3,000만 엔, 주소
    S("S09a", "S09", "card", "ews", "arc_night", "EL", [], "ARC_NDESK", "Countdown card: 廃棄まで、あと二十日."),
    S("S09b", "S09", "gfx", "ecu", "arc_night", "EL", [], "ARC_NDESK",
      "Extreme close-up of an open laptop screen glowing blue in the dark archive, a blank spreadsheet-like grid of empty cells, lamp light warm at the edge."),
    S("S09c", "S09", "ins", "ecu", "arc_night", "HA", [], "ARC_NDESK",
      "High angle extreme close-up at night: a yellow highlighter marking a blank line on a yellowed sheet, a stack of sheets beside it, blue screen glow and warm lamp."),
    S("S09d", "S09", "ins", "ecu", "arc_night", "EL", ["MIYAMOTO"], "ARC_NDESK",
      "Extreme close-up: an old man's hand setting down a steaming paper cup of coffee on the wooden desk beside the laptop, lamp light warm."),
    S("S09e", "S09", "sil", "ws", "arc", "LA", ["MIYAMOTO"], "ARC_LADDER",
      "Low angle wide: Miyamoto on the steel step-ladder reaching for an old box on the top shelf, seen from below and behind, the fluorescent tube glaring above.",
      motion="He pulls the box a few centimetres toward himself on the shelf. No climbing down."),
    S("S09f", "S09", "react", "cu", "arc_night", "EL", ["SAORI_B"], "ARC_NDESK",
      "Chest-up close-up of Saori at night, the laptop's blue glow on her face and glasses, lips moving silently as she counts, lamp warm behind.", line="line023", expr="focus"),
    S("S09g", "S09", "gfx", "ecu", "arc_night", "EL", [], "ARC_NDESK",
      "Extreme close-up of the laptop screen: a blank dark window with a single empty bright rectangle in the centre, blue glow."),
    S("S09h", "S09", "gfx", "ecu", "arc_night", "OH", [], "ARC_NDESK",
      "Overhead extreme close-up: a plain white official-looking blank document lying on the desk beside a yellowed blank sheet, both with faint empty ruled boxes, lamp light.", line="line024"),
    S("S09i", "S09", "gfx", "ecu", "arc_night", "HA", [], "ARC_NDESK",
      "Overhead extreme close-up: the same two blank documents side by side on the desk, a red pen lying between them, lamp light.", hero=True),
    S("S09j", "S09", "react", "cu", "arc_night", "EL", ["SAORI_B"], "ARC_NDESK",
      "Chest-up close-up of Saori at night, eyes wide behind the glasses, the blue screen glow, a slow exhale.", line="line025", expr="fear"),
    S("S09k", "S09", "estill", "ws", "arc_night", "EL", [], "ARC_NDOOR",
      "Wide of the dark archive at night: the steel door at the end of the aisle, a thin line of cold light under it, the desk lamp a small warm glow at the edge."),
    # ── S10 로그·영수증·송신
    S("S10a", "S10", "ins", "ecu", "arc_night", "HA", [], "ARC_NDESK",
      "High angle extreme close-up: a woman's hand pushing a small plain black USB stick into the side of the laptop, blue glow, lamp warm."),
    S("S10b", "S10", "gfx", "ecu", "arc_night", "EL", [], "ARC_NDESK",
      "Extreme close-up of the laptop screen: a dark blank log window, a single empty highlighted row, blue glow.", line="line026"),
    S("S10b2", "S10", "react", "cu", "arc_night", "EL", ["SAORI_B"], "ARC_NDESK",
      "Chest-up close-up of Saori reading the screen at night, the blue glow sliding across her glasses, lips pressed, lamp warm behind.", expr="focus"),
    S("S10c", "S10", "gfx", "ecu", "arc_night", "OH", [], "ARC_NDESK",
      "Overhead extreme close-up: a small blank thermal receipt slip stapled to a blank expense form on the desk, the laptop's blue glow at the edge.", line="line027", hero=True),
    S("S10d", "S10", "react", "cu", "arc_night", "EL", ["SAORI_B"], "ARC_NDESK",
      "Chest-up close-up of Saori, eyes narrowing, a slow nod, blue screen glow on her glasses.", expr="resolve"),
    S("S10e", "S10", "gfx", "ecu", "arc_night", "EL", [], "ARC_NDESK",
      "Extreme close-up of the laptop screen: a plain blank form window with an empty attachment box and a single blank button, blue glow."),
    S("S10f", "S10", "ins", "ecu", "arc_night", "HA", [], "ARC_NDESK",
      "High angle extreme close-up: a woman's index finger pressing the laptop trackpad, the screen glow brightening for a moment."),
    S("S10g", "S10", "card", "ews", "arc_night", "EL", [], "ARC_NDOOR", "Countdown card: 廃棄まで、あと十四日."),
    S("S10h", "S10", "estill", "ws", "arc_night", "EL", [], "ARC_NDOOR",
      "Wide of the dark archive at night: the steel door at the end of the aisle, a thin line of cold light under it, everything else black.", line="line028"),
    # ── S11 지하의 밤 (공포)
    S("S11a", "S11", "card", "ews", "cor", "HA", [], "COR_WIDE", "Countdown card: 廃棄まで、あと三日."),
    S("S11b", "S11", "empty", "ews", "cor", "EL", [], "COR_WIDE",
      "Wide: the empty concrete basement corridor at night receding to the steel door, one cold tube lit, pipes along the ceiling, nobody in sight.",
      motion="Completely still corridor; the far tube flickers once. No people appear.", hero=True),
    S("S11b2", "S11", "empty", "ws", "cor", "LA", [], "COR_FLOOR",
      "Low angle along the concrete floor of the corridor toward the door, cold light, long shadows, no people.",
      motion="A faint shadow passes across the far wall. Nobody enters the frame."),
    S("S11c0", "S11", "ins", "ecu", "arc_night", "HA", [], "ARC_NDESK",
      "High angle extreme close-up: a woman's hands closing the laptop lid quickly, the blue glow snapping off, lamp light left."),
    S("S11d", "S11", "sil", "ws", "arc_fear", "LA", ["GONDO"], "ARC_REV",
      "Low angle from the archive floor: the steel door swung open, Gondo's bulky figure standing in the doorway as a pure black silhouette against blinding cold light, no facial detail.",
      motion="The silhouette stands still, then takes one slow heavy step inside. No face visible.", hero=True),
    S("S11d2", "S11", "sil", "ms", "arc_fear", "LA", ["GONDO"], "ARC_REV",
      "Low angle medium of the backlit silhouette of Gondo in the doorway, the outline of gold glasses glinting once, face in total shadow.", line="line029",
      motion="The silhouette tilts its head slightly; the glasses glint. No walking."),
    S("S11c", "S11", "d", "cu", "arc_lamp", "EL", ["SAORI_B"], "ARC_DESK",
      "Chest-up close-up of Saori at the desk, lamp light on one side, eyes wide and steady, a swallow, apron strap visible.", line="line030", expr="fear"),
    S("S11e", "S11", "ins", "ecu", "arc_fear", "HA", ["GONDO"], "ARC_AISLE",
      "High angle extreme close-up: a polished black leather shoe kicking a cardboard archive box, blank yellowed sheets spilling across the concrete floor. Only the shoe and the box."),
    S("S11f", "S11", "sil", "ms", "arc_fear", "LA", ["GONDO"], "ARC_REV",
      "Low angle medium: the silhouette of Gondo in the doorway half turned to leave, one hand on the door edge, face in shadow.", line="line031",
      motion="The silhouette turns its shoulders slightly toward the door and stops. No face detail."),
    S("S11g", "S11", "ins", "ecu", "arc_lamp", "HA", ["SAORI_B"], "ARC_DESK",
      "High angle extreme close-up: a woman's trembling hand flat on the wooden desk beside the lamp, a yellowed sheet under her fingertips."),
    S("S11h", "S11", "sil", "ms", "arc", "SIDE", ["MIYAMOTO", "SAORI_B"], "ARC_AISLE",
      "Medium from behind Saori's shoulder: Miyamoto standing in the dark aisle between racks, half lit, holding a cardboard box, his face soft and turned slightly away.", line="line032",
      motion="Miyamoto lifts the box a few centimetres as if showing it, then lowers it. No one walks."),
    # ── S12 15층 축배
    S("S12a", "S12", "ins", "ecu", "office", "EL", [], "OFF_WIDE",
      "Extreme close-up: a champagne cork popping from a dark green bottle, foam bursting, blurred office lights behind."),
    S("S12a2", "S12", "sil", "ws", "office", "LA", ["GONDO", "STAFF"], "OFF_WIDE",
      "Low angle wide: Gondo's bulky figure raising a glass high in the centre of the office, colleagues around him as soft shapes with raised glasses, faces blurred.", fx="handheld",
      motion="Glasses rise together; Gondo rocks slightly on his heels. Nobody walks toward the camera."),
    S("S12b", "S12", "d", "cu", "office", "LA", ["GONDO"], "OFF_WIDE",
      "Low angle chest-up of Gondo flushed and grinning, chin up, gold glasses, blurred colleagues and office lights behind.", line="line033", expr="laugh"),
    S("S12b2", "S12", "sil", "ecu", "office", "HA", ["GONDO"], "OFF_WIDE",
      "High angle extreme close-up: a champagne flute being filled to overflowing by a fat hand with a gold wristwatch, foam running over.", line="line034",
      motion="Champagne pours and foams over the rim onto the desk; the hand with the gold watch tilts the bottle. No faces."),
    S("S12d", "S12", "sil", "ms", "office", "SIDE", ["GONDO", "STAFF"], "OFF_AISLE",
      "Medium over a colleague's shoulder: Gondo's bulky back and salt-and-pepper hair as he talks, one arm waving a glass, the colleague's head in soft focus in the foreground.", line="line035", fx="handheld",
      motion="Gondo's shoulders shake with a laugh; the glass waves once. He does not turn around."),
    # ── S13 연회장 입장 (2차 광고 직전)
    S("S13a", "S13", "empty", "ews", "bq", "LA", [], "BQ_LOW",
      "Very low angle from the red carpet looking up toward the stage of the banquet hall, three chandeliers blazing, a plain blank cream banner above the stage, crystal glasses on the tables.",
      motion="Chandelier light shimmers; nothing else moves. No people.", hero=True),
    S("S13a2", "S13", "gfx", "ws", "bq", "EL", [], "BQ_STAGE",
      "Wide of the stage and head table: a long plain blank cream cloth banner hung above a blank projection screen, chandeliers warm."),
    S("S13a3", "S13", "react", "cu", "bq", "EL", ["OKOCHI"], "BQ_TABLE",
      "Chest-up close-up of Okochi seated at the head table, expressionless, a crystal glass blurred in the foreground, chandelier warmth on his silver hair.", expr="calm"),
    S("S13a4", "S13", "face", "ws", "bq", "EL", ["SAORI_B", "CROWD"], "BQ_DOORS",
      "Wide from inside the hall: the double doors opening and Saori stepping in alone in a grey knit and jeans, a folded navy apron in one hand, guests as soft shapes at the tables.",
      motion="She steps through the doorway and stops after two steps, the doors settling behind her. The guests stay seated.", hero=True),
    S("S13b", "S13", "d", "cu", "bq_press", "LA", ["GONDO"], "BQ_STAGE",
      "Low angle chest-up of Gondo flushed with drink, a broad sneer, gold glasses, chandeliers blurred above.", line="line036", expr="laugh"),
    S("S13c", "S13", "sil", "ms", "bq_press", "SIDE", ["GONDO", "SAORI_B"], "BQ_WIDE",
      "Medium over Saori's shoulder from behind: Gondo's bulky figure a few steps away holding a wine glass, his face soft, guests blurred.", line="line037",
      motion="Gondo tips the glass slightly; Saori's shoulder stays still. Nobody walks."),
    S("S13d", "S13", "ins", "ecu", "bq_press", "HA", [], "BQ_TABLE",
      "High angle extreme close-up: red wine splashing onto the red carpet beside a pair of plain black flat shoes, drops spreading."),
    S("S13e", "S13", "react", "cu", "bq_cold", "EL", ["SAORI_B"], "BQ_WIDE",
      "Chest-up close-up of Saori with her eyes lowered, perfectly still, a faint tremor at the lips, chandeliers blurred behind.", expr="fear"),
    S("S13f", "S13", "reuse:S01a", "ws", "bq_cold", "LA", ["AUDIT"], "BQ_DOORS", "Reuse: the doors burst open, audit team silhouettes."),
    S("S13g", "S13", "reuse:S01b", "cu", "bq_cold", "EL", ["KIRITANI"], "BQ_WIDE", "Reuse: Kiritani 「そこまでにしてください」.", line="line038"),
    # ── ④ S14 백지 철회 (2차 광고 뒤)
    S("S14a", "S14", "sil", "ws", "bq_cold", "LA", ["AUDIT", "MIYAMOTO"], "BQ_LOW",
      "Very low angle from the red carpet: five audit staff in dark suits walking slowly toward the camera as dark shapes, Miyamoto behind them carrying a grey steel document case with both hands, faces soft.",
      motion="Slow motion: they walk steadily toward the camera, feet on the carpet, no one looks into the lens.", hero=True),
    S("S14b", "S14", "d", "cu", "bq_press", "LA", ["GONDO"], "BQ_STAGE",
      "Low angle chest-up of Gondo blustering, eyebrows raised, a forced angry frown, gold glasses, chandeliers blurred.", line="line039", expr="panic"),
    S("S14c", "S14", "d", "cu", "bq_cold", "EL", ["KIRITANI"], "BQ_WIDE",
      "Chest-up close-up of Kiritani, expressionless, rimless glasses, the cold key light, guests blurred behind.", line="line040", expr="stern"),
    S("S14c2", "S14", "sil", "ws", "bq_cold", "SIDE", ["AUDIT", "CROWD"], "BQ_WIDE",
      "Wide from the side: the five audit staff in dark suits fanning out between the round tables, guests frozen in their seats, all faces soft, chandeliers warm above.",
      motion="The staff take slow steps apart between the tables; the guests stay still. No one looks at the camera."),
    S("S14d", "S14", "react", "ms", "bq_cold", "EL", ["GONDO"], "BQ_STAGE",
      "Medium shot of Gondo frozen in front of the stage, the sneer gone, mouth slightly open, the blank banner and chandeliers behind him.", line="line041", fx="dollyzoom", expr="panic", hero=True),
    S("S14d2", "S14", "ins", "ecu", "bq_press", "HA", ["GONDO"], "BQ_TABLE",
      "High angle extreme close-up: a fat hand with a gold wristwatch holding a crystal wine glass that trembles, red wine shivering inside, white tablecloth below."),
    S("S14f", "S14", "reuse:S01c", "ecu", "bq_press", "HA", ["GONDO"], "BQ_TABLE", "Reuse: the wine glass slips and shatters."),
    S("S14g", "S14", "gfx", "ws", "bq_proj", "EL", [], "BQ_STAGE",
      "Wide of the stage: the large projection screen above the head table just switched on, glowing plain blank blue-white, a cold beam cutting through dust from the back of the hall.", line="line042", fx="flash"),
    S("S14h", "S14", "sil", "ms", "bq_proj", "LA", ["GONDO"], "BQ_STAGE",
      "Low angle medium: Gondo standing in front of the glowing screen with the projector beam behind him, his face in deep shadow, only the outline of his bulk and the glint of gold glasses.",
      motion="The beam's dust drifts; Gondo's shoulders sag slightly. He does not turn.", hero=True),
    S("S14i", "S14", "sil", "ws", "bq_cold", "HA", ["GONDO", "CROWD"], "BQ_HIGH",
      "High angle from the balcony: Gondo alone in a widening circle of red carpet as the guests around him step back, all faces soft.",
      motion="The surrounding guests take one slow step backward together; Gondo stays rooted."),
    S("S14j", "S14", "react", "cu", "bq_cold", "EL", ["SAORI_B"], "BQ_WIDE",
      "Chest-up close-up of Saori, eyes lifting, a long slow breath, chandeliers blurred behind.", line="line043", expr="resolve"),
    S("S14k", "S14", "ins", "ecu", "bq_cold", "HA", ["SAORI_B"], "BQ_WIDE",
      "High angle extreme close-up: a woman's hand at her side slowly unclenching, a folded navy apron held loosely in the other hand, red carpet below."),
    S("S14l", "S14", "sil", "ms", "bq_cold", "SIDE", ["MIYAMOTO", "AUDIT"], "BQ_WIDE",
      "Medium from the side: Miyamoto standing among the dark-suited audit staff with the grey steel case held against his chest, his face half turned, guests blurred.",
      motion="Miyamoto gives one slow nod; the staff stay still. Nobody walks."),
    # ── S15 역공과 반격
    S("S15a", "S15", "d", "cu", "bq_press", "LA", ["GONDO"], "BQ_STAGE",
      "Low angle chest-up of Gondo red-faced and shouting, eyes wide, sweat at the temples, gold glasses askew, no hands.", line="line044", expr="panic"),
    S("S15b", "S15", "d", "cu", "bq_press", "EL", ["GONDO"], "BQ_STAGE",
      "Low angle chest-up of Gondo breaking down mid-shout, trembling jaw, eyes wild, gold glasses, chandeliers blurred.", line="line045", expr="panic"),
    S("S15b2", "S15", "sil", "ws", "bq_cold", "SIDE", ["GONDO", "CROWD"], "BQ_REV",
      "From the stage looking back across the tables: Gondo's bulky back in the near foreground thrusting a thick arm and pointing down the aisle, all the guests' heads turning the same way toward the far doors, faces soft, chandeliers warm.", fx="dutch7 handheld",
      motion="Gondo's arm jabs forward once; heads turn together along the aisle. Nobody walks."),
    S("S15c", "S15", "react", "ms", "bq_cold", "EL", ["KIRITANI"], "BQ_WIDE",
      "Medium shot of Kiritani turning his head slightly toward Saori with a faint narrowing of the eyes, rimless glasses, hands clasped behind his back, guests blurred.", line="line046", expr="doubt"),
    S("S15e", "S15", "d", "cu", "bq_cold", "EL", ["SAORI_B"], "BQ_WIDE",
      "Chest-up close-up of Saori looking straight into the camera, calm and unshakable, glasses catching a cold glint, guests blurred.", line="line047", expr="resolve"),
    S("S15e2", "S15", "reuse:S06f", "ecu", "arc_lamp", "EL", [], "P_TRIPOD", "Reuse: the phone set on the mini tripod."),
    S("S15f2", "S15", "ins", "ecu", "bq_cold", "HA", ["GONDO"], "BQ_TABLE",
      "High angle extreme close-up: a fat hand with a gold wristwatch gripping the edge of a white tablecloth, knuckles white.", line="line048"),
    S("S15f3", "S15", "react", "cu", "bq_cold", "HA", ["KIRITANI"], "BQ_WIDE",
      "High angle chest-up of Kiritani listening with a slow single nod, rimless glasses, expressionless, guests blurred.", expr="stern"),
    S("S15g", "S15", "d", "cu", "bq_cold", "EL", ["MIYAMOTO"], "BQ_WIDE",
      "Chest-up close-up of Miyamoto in his beige cardigan among the suits, lowered brows, the bushy white moustache, chandeliers blurred.", line="line049", expr="wistful"),
    S("S15h", "S15", "d", "cu", "bq_cold", "LA", ["SAORI_B"], "BQ_WIDE",
      "Chest-up close-up of Saori with a faint cool smile, eyes steady, guests blurred.", line="line050", expr="resolve"),
    S("S15i", "S15", "ins", "ecu", "bq_cold", "HA", ["MIYAMOTO"], "P_CASE",
      "High angle extreme close-up: an old man's hands unlatching and lifting the lid of a grey steel document case on a white tablecloth, a thick stack of yellowed blank sheets inside."),
    S("S15j", "S15", "d", "cu", "bq_cold", "EL", ["MIYAMOTO"], "BQ_WIDE",
      "Chest-up close-up of Miyamoto, eyes fixed, no smile, the white moustache, a slow nod.", line="line051", expr="wistful"),
    S("S15k", "S15", "sil", "ws", "bq_cold", "BE", ["GONDO", "CROWD"], "BQ_HIGH",
      "Extreme bird's-eye view straight down: Gondo on his knees on the red carpet, small in the frame, a ring of empty carpet around him, guests' heads at the edges.",
      motion="Slow motion: his shoulders slump and his head bows lower. Nobody approaches.", hero=True),
    # ── S16 오코치, 최종 결정타
    S("S16a", "S16", "ins", "ecu", "bq", "HA", ["OKOCHI"], "BQ_TABLE",
      "High angle extreme close-up: a large composed hand setting a crystal glass down on the white tablecloth, a plain dark grey sleeve and a white pocket square at the edge."),
    S("S16a2", "S16", "sil", "ms", "bq", "LA", ["OKOCHI"], "BQ_LOW",
      "Low angle medium: Okochi rising slowly from the head table, silver hair catching chandelier light, seen from slightly below and to the side, face half turned.",
      motion="He straightens up fully and stands still, shoulders square. No walking."),
    S("S16b", "S16", "d", "cu", "bq", "LA", ["OKOCHI"], "BQ_STAGE",
      "Low angle chest-up of Okochi, calm commanding gaze, thick dark eyebrows, silver hair, warm chandelier rim light, NO glasses.", line="line052", expr="calm"),
    S("S16b2", "S16", "react", "ms", "bq_cold", "HA", ["GONDO"], "BQ_STAGE",
      "High angle medium: Gondo kneeling on the carpet looking up, pale, mouth open, gold glasses crooked, the blank banner above.", line="line053", expr="panic"),
    S("S16d", "S16", "sil", "ms", "bq_cold", "BE", ["GONDO"], "BQ_HIGH",
      "Bird's-eye view from directly above: the top of Gondo's slicked salt-and-pepper head as he kneels, shoulders hunched, the red carpet around him.", line="line054",
      motion="His head sways slightly and bows lower. No face visible."),
    S("S16e", "S16", "react", "cu", "bq", "EL", ["OKOCHI"], "BQ_TABLE",
      "Chest-up close-up of Okochi turning his gaze toward Saori, a flicker of interest in the dark eyebrows, NO glasses.", expr="calm"),
    S("S16f", "S16", "d", "cu", "bq_cold", "EL", ["SAORI_B"], "BQ_WIDE",
      "Chest-up close-up of Saori speaking clearly, steady eyes, a small nod, glasses catching a cold glint.", line="line055", expr="resolve"),
    S("S16f2", "S16", "react", "ms", "bq_cold", "HA", ["GONDO"], "BQ_STAGE",
      "High angle medium: Gondo on his knees staring at the floor, shoulders shaking, gold glasses slipping down his nose.", expr="panic"),
    S("S16g", "S16", "d", "cu", "bq_cold", "LA", ["SAORI_B"], "BQ_WIDE",
      "Low angle chest-up of Saori, a faint cool smile, eyes steady, chandeliers above her, the camera looking up at her.", line="line056", expr="resolve"),
    S("S16h", "S16", "d", "cu", "bq", "LA", ["OKOCHI"], "BQ_STAGE",
      "Low angle chest-up of Okochi with his first warm approving smile, eyes crinkling, silver hair, NO glasses.", line="line057", expr="smile"),
    S("S16h2", "S16", "sil", "ws", "bq", "EL", ["OKOCHI", "SAORI_B", "CROWD"], "BQ_REV",
      "From the stage: Okochi extending his hand toward Saori across the aisle, both seen from the side at a distance, guests soft around them.",
      motion="Okochi's hand extends slowly; Saori takes one step forward. Nobody else moves."),
    S("S16i", "S16", "react", "ch", "bq_cold", "LA", ["SAORI_B"], "BQ_WIDE",
      "Low angle choker close-up of Saori's face from forehead to chin, eyes looking slightly down at the camera, absolute calm, glasses catching a glint.", expr="resolve"),
    S("S16j", "S16", "d", "cu", "bq_cold", "LA", ["SAORI_B"], "BQ_WIDE",
      "Low angle chest-up of Saori looking slightly down at the camera, perfectly still, no smile, the chandeliers above her.", line="line058", expr="resolve"),
    S("S16k", "S16", "react", "ms", "bq_cold", "BE", ["GONDO"], "BQ_HIGH",
      "Bird's-eye view straight down: Gondo collapsed forward on his hands and knees on the red carpet, small, alone, the glass shards glittering near him.", expr="panic"),
    # ── S17 처벌(화면으로)
    S("S17a", "S17", "gfx", "ws", "bq_cold", "LA", [], "BQ_STAGE",
      "Low angle wide of the stage: the long cream cloth banner above the stage sagging at one end, one of its cords slipping, the blank screen behind."),
    S("S17b", "S17", "ins", "ecu", "bq_cold", "EL", ["GUARD", "GONDO"], "BQ_TABLE",
      "Extreme close-up: a uniformed guard's hands lifting a plain blank lanyard ID card from around a thick neck in a navy suit collar; no faces."),
    S("S17c", "S17", "sil", "ews", "bq_cold", "EL", ["GONDO", "GUARD", "CROWD"], "BQ_REV",
      "Long shot from the stage: Gondo's bulky back being led toward the far doors by a guard, the guests at the tables all turned away with their backs to him, chandeliers warm above.", line="line059",
      motion="Gondo and the guard walk slowly away toward the doors; the guests stay turned away. No one looks back.", hero=True),
    S("S17d", "S17", "estill", "ecu", "bq_cold", "HA", [], "BQ_TABLE",
      "High angle extreme close-up: broken crystal shards and a dark wine stain on the empty red carpet, a single chandelier reflection in a shard, no people.", line="line060"),
    S("S17d2", "S17", "estill", "ms", "bq_cold", "EL", [], "BQ_TABLE",
      "Medium of the empty head table: an overturned chair, a half-full wine glass, the blank banner sagging above, chandeliers dimmed, no people."),
    S("S17e", "S17", "card", "ews", "arc_end", "EL", [], "ARC_END", "Caption card: 一か月後."),
    # ── ⑤ S18 엔딩 (한 달 뒤, 지하)
    S("S18a", "S18", "face", "ws", "arc_end", "EL", ["SAORI_E"], "ARC_END",
      "Wide of the archive in warm orange light: Saori in a charcoal pantsuit coming down the last steps inside the doorway holding a small bouquet of white flowers, the racks glowing warm.",
      motion="She descends the last two steps slowly and stops just inside, looking around. Nothing else moves."),
    S("S18a2", "S18", "sil", "ms", "arc_end", "SIDE", ["MIYAMOTO"], "ARC_BOX",
      "Medium from the side: Miyamoto placing a sealed cardboard archive box onto a shelf, seen in profile in warm light, half-moon glasses on the cord.",
      motion="He slides the box into place on the shelf and rests a hand on it. No turning to the camera."),
    S("S18b", "S18", "d", "cu", "arc_end", "EL", ["MIYAMOTO"], "ARC_END",
      "Chest-up close-up of Miyamoto with a broad playful smile under the bushy white moustache, warm orange light, racks glowing behind.", line="line061", expr="smile"),
    S("S18d", "S18", "ins", "ecu", "arc_end", "EL", [], "ARC_BOX",
      "Extreme close-up: a sealed cardboard archive box on a shelf with a plain blank white label, brown tape, warm orange light.", line="line062"),
    S("S18e", "S18", "d", "cu", "arc_end", "EL", ["MIYAMOTO"], "ARC_END",
      "Chest-up close-up of Miyamoto, eyes drifting to the distance, a slow sad-sweet smile, warm light.", line="line063", expr="wistful"),
    S("S18f", "S18", "gfx", "ecu", "arc_end", "HA", [], "ARC_DESK",
      "High angle extreme close-up: a plain blank certificate sheet in a simple dark frame propped on the wooden desk beside the lamp, warm light."),
    S("S18g", "S18", "sil", "ws", "arc_end", "EL", ["SAORI_E", "MIYAMOTO"], "ARC_END",
      "Wide in warm light: Saori and Miyamoto facing each other in the aisle and bowing slightly to one another, both seen from the side at a distance.", line="line064",
      motion="Both bow slowly a few degrees and straighten. Nobody walks."),
    S("S18g2", "S18", "ins", "ecu", "arc_end", "HA", [], "ARC_DESK",
      "High angle extreme close-up: a small bouquet of white flowers laid on the worn wooden desk beside the warm lamp, a yellowed blank sheet under it."),
    S("S18h", "S18", "empty", "ews", "arc_end", "HA", ["SAORI_E", "MIYAMOTO"], "ARC_HIGH",
      "High angle from above the racks: the two small figures standing together in the warm-lit aisle far below, the racks receding, dust glowing.", line="line065", fx="pull",
      motion="Nearly still; the two figures remain standing. Dust drifts in the warm light. The camera does not move.", hero=True),
]

CARDS = {"S01g": "地下倉庫の伝票", "S01h": "二か月前", "S09a": "廃棄まで、あと二十日", "S10g": "廃棄まで、あと十四日", "S11a": "廃棄まで、あと三日", "S17e": "一か月後"}
GFX = {
    "S02c": "PPT 작성자 태그 「作成者：森川沙織（最終更新 03:42）」 2초 줌인",
    "S02d": "PPT 「P.42 サプライチェーン再構築案」",
    "S04a": "인트라넷 인사 발령 「【異動】企画部 森川沙織 → 総務部付 文書管理室（地下二階）」",
    "S07d": "지출결의서 「株式会社サンライズ企画 ／ コンサルタント料 250,000円」 + 인영(합성)",
    "S09b": "전표 데이터베이스 화면(스프레드시트, 사라이즈 행 노랑 하이라이트)",
    "S09g": "三千万円 카운트업(자막 Emph, 250,000 → 30,000,000円)",
    "S09h": "등기부 「代表取締役 / 住所」 + 弔慰金 申請書 「申請者 権藤 / 義父 / 住所」",
    "S09i": "두 서류의 주소를 잇는 빨간 선 애니메이션",
    "S10b": "로그 「承認 23:48 ／ 社外リモート接続」 하이라이트",
    "S10c": "클럽 영수증 「銀座 ／ 23:41」 ↔ 로그 23:48 일치 하이라이트",
    "S10e": "감사실 핫라인 「添付：証拠資料一式.zip」 → 「送信完了」",
    "S13a2": "현수막 「祝 権藤常務取締役 就任内定」 합성",
    "S14g": "프로젝터 스크린: 사라이즈 전표 + 자금 흐름도(25万円×120＝3,000万円 → 妻の実家) + 빔 광선",
    "S17a": "현수막 글자 합성 + 한쪽이 떨어지는 애니메이션",
    "S18f": "표창장 「表彰状 宮本殿」",
}
GFX_PLATE = {
    "S14g": "The large projection screen above the head table glowing plain blank blue-white, a cold beam from the back of the hall cutting through dust, the stage and chandeliers dim around it; no people.",
    "S13a2": "The stage and head table of the banquet hall with a long plain blank cream cloth banner hung above a blank screen, chandeliers warm; no people.",
    "S17a": "Low angle wide of the stage: a long plain blank cream cloth banner sagging at one end above the stage, the blank screen behind; no people.",
}
EMPH = [  # (기준 줄, 줄 시작 후 초, 길이, 스타일, 문구) — 三千万円 카운트업
    ("line023", 0.9, 0.4, "Emph", "二十五万円"),
    ("line023", 1.3, 0.4, "Emph", "三百万円"),
    ("line023", 1.7, 0.4, "Emph", "一千五百万円"),
    ("line023", 2.1, 2.6, "Emph", "三千万円"),
]
SIGN_BY_LOC = {
    "BQ_STAGE": ("A long plain blank cream cloth banner hangs above the stage.", "현수막 「祝 権藤常務取締役 就任内定」"),
    "BQ_LOW": ("A long plain blank cream cloth banner hangs above the stage.", "현수막 「祝 権藤常務取締役 就任内定」"),
    "BQ_REV": ("", ""),
}
SIGN_SIZES = ("ms", "ws", "ews")
# 장면 전환: 기본 하드컷, 시간·장소 전환 디졸브 0.5~0.8, 막 종료 딥 투 블랙 1.0, 폭로 순간 화이트 플래시 0.2
DISSOLVE_INTO = {"S01g": ("fadeblack", 1.0), "S01h": ("fadeblack", 0.6), "S02a": ("fadeblack", 0.8), "S04a": ("fade", 0.5), "S06a": ("fade", 0.6),
                 "S07a": ("fade", 0.5), "S07b": ("fade", 0.5), "S08a": ("fade", 0.5), "S09a": ("fade", 0.6), "S09c": ("fade", 0.5), "S09d": ("fade", 0.5),
                 "S10g": ("fade", 0.5), "S11a": ("fade", 0.6), "S13a": ("fade", 0.6), "S14g": ("fadewhite", 0.2),
                 "S17e": ("fadeblack", 1.0), "S18a": ("fade", 0.8)}
AD_MAX_DISSOLVE = 0.5
AMBIENCE = {"S06a": "fluorescent tube buzzing and flickering, deep basement room tone", "S11b": "slow heavy footsteps approaching on concrete, distant fluorescent hum",
            "S11b2": "slow heavy footsteps on concrete getting closer, a door handle turning", "S05d": "steel elevator doors sliding shut, a descending elevator hum"}
STYLE = {"NA": "Naration", "沙織": "Saori", "権藤": "Gondo", "宮本": "Miyamoto", "桐谷": "Kiritani", "大河内": "Okochi"}
STYLE_JA = {"Naration": "沙織(語り)", "Saori": "沙織", "Gondo": "権藤", "Miyamoto": "宮本", "Kiritani": "桐谷", "Okochi": "大河内"}
STYLE_COLOR = {"Naration": "&H00FFFFFF", "Saori": "&H00F0E6C8", "Gondo": "&H00B4B4FF", "Miyamoto": "&H00DCDCDC", "Kiritani": "&H00E6F0DC", "Okochi": "&H00C8DCE6"}
PRO_MODEL = "fal-ai/bytedance/seedance/v1/pro/image-to-video"
HERO_MODEL = "fal-ai/kling-video/v3/pro/image-to-video"  # B안 히어로 컷(3테이크) — PHASE 5 실행 전 fal 모델 ID·응답 형식 확인
HERO_TAKES = 3
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
        if s["kind"] == "d" and len([w for w in s["who"] if w not in ("CROWD", "STAFF", "AUDIT", "GUARD")]) != 1:
            errs.append(f"{s['id']}: OMNI 컷은 1인 단독")
        if "GONDO" in s["who"] and s["lens"] in ("ch", "ecu") and s["kind"] in ("react", "d", "face"):
            errs.append(f"{s['id']}: 악역 근접 CU 금지(가슴 위까지) — 손·소품 인서트(ins)만 허용")
        if s["lens"] == "ch" and not (s["who"] and s["who"][0].startswith("SAORI")):
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
    if any(any(w.startswith("SAORI") for w in s["who"]) and "GONDO" not in s["who"] for s in dutch):
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
    if n == 36:  # S13 폭소 SFX + 대사(확정 B안 믹스)
        return os.path.join(ROOT, "assets", "auditions", "chika-gondo-laugh", "mix_B_bellow+happy.mp3")
    return os.path.join(ROOT, "assets", "auditions", "chika-tts", f"line{SAME_AS.get(n, n):03d}.mp3")


def copy_voice(dst, n):
    out = os.path.join(dst, f"line{n:03d}.mp3")
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
        named = [w for w in s["who"] if w not in ("CROWD", "STAFF", "AUDIT", "GUARD")]
        comp = ("Exactly one person in sharp focus, no foreground shoulder, hands out of frame, chest-up single close-up, facing the camera within 30 degrees."
                if s["kind"] == "d" else
                ("Completely unpopulated: no people, no hands." if s["kind"] in ("empty", "estill") and not s["who"] or (s["kind"] in ("gfx",) and not s["who"]) else
                 f"Only the people described ({len(named)} named{', plus soft unrecognizable background people' if len(named) != len(s['who']) else ''}), no extra sharp faces."))
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/chika-keyframes/{sid}-1.png"
        kf_prompt = None
        sign_txt, signage = [], []
        if s["loc"] in SIGN_BY_LOC and s["lens"] in SIGN_SIZES and SIGN_BY_LOC[s["loc"]][0]:
            sign_txt.append(SIGN_BY_LOC[s["loc"]][0]); signage.append(SIGN_BY_LOC[s["loc"]][1])
        if keyframe:
            subj = s["subject"]
            if s["kind"] == "gfx":
                subj = GFX_PLATE.get(sid) or re.sub(r"\s*\([^)]*\)|「[^」]*」|[0-9,]+円", "", subj)
                subj += " Every surface that will carry writing is completely blank and evenly lit."
            kf_prompt = " ".join([
                PRESET + ".", subj, ("Characters: " + " | ".join(ids) + ".") if ids else "",
                f"Camera: {ANGLE[s['angle']]}, {LENS[s['lens']]}.", f"Lighting: {LIGHT[s['light']]}.", comp, " ".join(sign_txt), PLAIN,
                f"Negative: {NEGATIVE}."]).strip()
            cost["kf"] += 1
        tier = {"d": "omni", "react": "still", "ins": "still", "estill": "still", "gfx": "gfx", "face": "pro", "sil": "lite",
                "empty": "lite", "card": "card"}.get(s["kind"], "reuse")
        if s["hero"] and tier in ("pro", "lite"):
            tier = "hero"
        gen = 10 if d > 5.0 else 5
        item = {"prompt": "", "duration": gen}
        if tier in ("pro", "lite", "hero"):
            motion = s["motion"] or "Subtle natural motion only, micro movements, no new people."
            item["prompt"] = ("Static, locked off camera. Motion: " + motion +
                              " Keep the exact faces, wardrobe, props and lighting of the first frame. Head turns under 20 degrees. "
                              "No walking toward the camera unless described, no new people, no text.")
            item["image"] = keyframe
            if tier == "pro":
                item["i2v_model"], item["i2v_resolution"] = PRO_MODEL, "1080p"; cost["pro"] += gen
            elif tier == "hero":
                item["i2v_model"], item["i2v_resolution"], item["hero_takes"] = HERO_MODEL, "1080p", HERO_TAKES; cost["hero"] += gen * HERO_TAKES
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

    events = []
    for i, x in enumerate(script, 1):
        r = rows[f"line{i:03d}"]
        st = STYLE[x[3] if x[3] != "NA" else "NA"]
        events.append((r["start"] - TRIM_PRE, r["end"] + 0.25, st, STYLE_JA[st], wrap(x[5])))
    for sid, cap in CARDS.items():
        c0 = starts[sid] + DISSOLVE_INTO.get(sid, ("", 0.2))[1] + 0.1
        events.append((c0, min(ends[sid] - 0.2, c0 + 3.5), "Caption", "", cap))
    for lid, off, ln, style, txt in EMPH:
        t0 = rows[lid]["start"] + off
        events.append((t0, t0 + ln, style, "", txt))
    events.sort(key=lambda e: e[0])
    fmt = "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
    # 2:1 레터박스 안쪽 하단에 자막(MarginV 150), 내레이션은 명조(03_시네마규격)
    st_lines = "\n".join(
        f"Style: {n},{'Noto Serif CJK JP' if n == 'Naration' else 'Noto Sans CJK JP'},{54 if n == 'Naration' else 56},{c},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{2 if n == 'Naration' else 3},1,2,200,200,150,1"
        for n, c in STYLE_COLOR.items())
    ass = ["[Script Info]", "Title: 地下倉庫の伝票 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]", fmt, st_lines,
           "Style: Caption,Noto Serif CJK JP,66,&H00FFF3C4,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,5,200,200,80,1",
           "Style: Emph,Noto Sans CJK JP,150,&H0000E6FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,10,3,5,100,100,80,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:
        txt = e[4]
        if e[2] == "Emph":
            txt = "{\\fscx130\\fscy130\\t(0,120,\\fscx100\\fscy100)}" + txt
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{txt}")
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    # BGM 7곡: 곡 사이 숨 1.5초 이상, 숨은 내레이션·대사가 흐르는 시점에(제7장 8), 광고 경계 앞뒤 분리
    t_ad1, t_ad2 = ad_times
    BGM = [
        (0.0, starts["S01g"] - 0.3, 0.40, "tense low strings and a slow heartbeat pulse, Japanese drama cold open, cold and ominous, instrumental, no vocals"),
        (starts["S02a"] + 0.8, t_ad1 - 0.2, 0.38, "nervous pizzicato strings and muted piano, quiet injustice and social pressure, Japanese corporate drama score, instrumental, no vocals"),
        (t_ad1 + 1.6, rows["line025"]["end"] + 0.5, 0.38, "steady minimal beat with soft synth, clock ticking, focused investigation, clever detective mood, instrumental, no vocals"),
        (rows["line026"]["start"] + 0.4, starts["S12a"] - 0.3, 0.40, "low ominous drone with sparse piano, dread in a dark basement, rising suspense, instrumental, no vocals"),
        (starts["S12a"] + 1.2, t_ad2 - 0.2, 0.38, "brassy drunken celebration turning uneasy, swing rhythm with dark undertone, Japanese drama score, instrumental, no vocals"),
        (t_ad2 + 1.6, starts["S16j"] - 0.3, 0.44, "slow powerful reversal strings and taiko drums, justice closing in, satisfying comeback, instrumental, no vocals"),
        (starts["S16j"] + 1.5, round(main_end, 2), 0.40, "warm hopeful piano and light strings, gentle resolution, Japanese drama ending, instrumental, no vocals"),
    ]
    SFX = [{"at": round(starts[s] + o, 2), "kind": k} for s, o, k in
           (("S01c", 0.6, "glass_shatter"), ("S07e", 0.2, "stamp"), ("S07e", 0.9, "stamp"), ("S07e", 1.4, "stamp"), ("S09i", 0.3, "heartbeat1"), ("S09i", 0.9, "ding"),
            ("S10c", 0.4, "bassdrop"), ("S10f", 0.1, "click"), ("S12a", 0.1, "cork"), ("S14f", 0.6, "glass_shatter"), ("S14g", 0.0, "flash"), ("S05d", 0.3, "elevator_close"))]
    SFX.append({"at": round(rows["line023"]["start"] + 2.1, 2), "kind": "bass_hit"})

    os.makedirs(os.path.join(ROOT, "scripts", "storyboard"), exist_ok=True)
    json.dump({"_설명": "chika PHASE 3 스토리보드 Lock(build_chika_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT,
               "preset": PRESET, "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"],
               "scenes": sb}, open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"_설명": "chika 장면 설정(build_chika_phase3.py 생성). override_required 장면(정지 푸시인·OMNI 정지 프레임·그래픽·재사용·카드)은 video-overrides로 먼저 넣는다. hero_takes 컷은 B안 상위 모델 3테이크.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, "
                         "wardrobe, props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": "chika 조립·오디오(build_chika_phase3.py 생성). 음성 65줄 = assets/audio-overrides/chika/ (Typecast 확정본, 발화 구간만, line036은 폭소 SFX 포함 믹스).",
        "default_voice": "cached-typecast",
        "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Naration"], "silent_styles": ["Caption", "Emph"],
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
        "_마스터링": "-14 LUFS / TP -1.0 dBTP, 지하 = 드라이 슬랩백 + 50Hz 험, 연회장 = 홀 리버브(말소리 없는 룸 베드)",
        "_아웃트로": "진행자 4줄(line066~069)은 본편에 넣지 않는다 — PHASE 6 append_outro + outro_cta_overlay(美談ものがたり 공통).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = (cost["kf"] * RATE["kf"] + cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"] + cost["hero"] * RATE["hero"])
    md = ["# 『地下倉庫の伝票』 PHASE 3 샷 리스트", "",
          f"> `scripts/build_chika_phase3.py` 자동 생성(손 수정 금지). 타임코드 분:초.프레임(24fps). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " +
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
    cam = ["# 『地下倉庫の伝票』 카메라 앵글 설계 (CLAUDE.md 제8장 7)", "",
           f"> `scripts/build_chika_phase3.py`의 샷 표에서 자동 생성. 자동 검사 통과: 연속 같은 구도 0 · 더치 {len(du)}회({', '.join(f'{a} {b}' for a, b in du)} — 악역만, 비립싱크) · 돌리줌 1회({dz[0]}) · 립싱크 컷 정면~45° · 악역 근접 CU 없음 · 초커는 사오리만.", "",
           "## 앵글 설계 원칙 (이 작품)", "",
           "- **권력 역전**: 곤도는 전반 로우앵글(S02b·S03d·S03g·S05b·S12b) → 백지 철회 뒤 하이앵글·버즈아이(S14i·S15k·S16d·S16k). 오코치는 로우앵글(S16b·S16h).",
           "- **사오리**: 전반 아이레벨·하이(S03h 무력) → 지하에서 하이(S06d, 작게) → 반격부터 아이레벨 정면(S15e) → 결정타 로우앵글+초커(S16i·S16j). 카메라는 고정·슬로 푸시인만(주인공 안정도 축).",
           "- **악역 불안**: S05a 더치 5°+핸드헬드(조롱) · S15b2 더치 7°+핸드헬드(「主犯だ」 직후 시선 쏠림) · S12 핸드헬드(축배).",
           "- **매치 컷**: S01c(와인잔 파열) ↔ S14f(재사용) · S05d(엘리베이터 문틈 사오리) ↔ S11d(문 열림 곤도 실루엣).",
           "- **소품 인격화(ECU 70%)**: 전표(S01f·S07c·S07d·S07e) · 금시계(S03b·S12b2·S15f2) · 보관함(S15i) · 삼각대(S06f→S15e2).",
           "- **전경 프레이밍(A7)**: S08a 랙 너머 · S13a3 잔 너머 · S03e2 동료 어깨 너머 · S12d 어깨 너머 · S16a 손 너머.", "",
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
