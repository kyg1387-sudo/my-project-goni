#!/usr/bin/env python3
"""『タワマンのボスママ』(tower) PHASE 3 샷 리스트 Lock 생성기 — 일본어판(美談ものがたり).

입력(동결본, 손으로 옮겨 적지 않는다):
  productions/tower-bossmom-ja/lock.json        PHASE 1 Lock(실측 줄 타임코드·장면 경계·광고 지점)
  productions/tower-bossmom-ja/00_script_ja.md  대본 v2.1(자막 원문)
  assets/auditions/tower-tts/lineNNN.mp3        확정 음성(앞뒤 무음을 잘라 assets/audio-overrides/tower/로 복사)
출력:
  scripts/storyboard/tower.json   샷 스펙(PHASE 4 키프레임·PHASE 5 입력)
  scripts/scenes/tower.json       장면 생성 설정(i2v·override_required·budget_usd)
  scripts/audio/tower.json        조립·오디오(장면 길이·OmniHuman·BGM·현장음)
  subs/tower.ass                  일본어 자막(대사 61줄 + 화면 전용 카드·강조 자막)
  productions/tower-bossmom-ja/07_샷리스트.md   검토용 표 + 비용 추산 + 앵글 분포
규칙: CLAUDE.md 제0~9장(build_yanagi_phase3.py 방식 계승). 아웃트로(진행자 4줄)는 PHASE 6 append_outro로 별도.
사용법: python3 scripts/build_tower_phase3.py
"""
import collections
import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROD = os.path.join(ROOT, "productions", "tower-bossmom-ja")
sys.path.insert(0, PROD)
from parse_script import load_lines  # noqa: E402
from build_tts import SPLIT          # noqa: E402

SKIT = "tower"
FPS = 24
HARD = 1 / FPS
OMNI_MAX = 7.9
LEAD = 0.3
MIN_SHOT = 1.2
STILL_MAX = 6.5
I2V_MAX = 10.0
SHOT_TARGET = 1.6
TRIM_PRE, TRIM_POST = 0.05, 0.12   # 음성 파일 앞뒤 무음 정리(배치 시 자동 배속 방지)

C = "assets/portraits/tower-cast/cells/"
T = "assets/portraits/tower-ja-cast/cells/"
WHO = {
    "YUMI": ("Yumi, a Japanese woman aged 42, slim, oval face, intelligent calm eyes, straight black chin-length bob with a soft side-swept fringe, "
             "thin plain silver-rimmed rectangular glasses", C + "yumi-front.png"),
    "REIKA": ("Reika, a glamorous Japanese woman aged 40, long voluminous wavy chestnut-brown hair, bold red lipstick, pearl stud earrings, NO glasses",
              C + "reika-front.png"),
    "RIKO": ("Riko, a Japanese girl aged 7, round cheeks, black hair in two low pigtails with plain yellow hair ties", C + "riko-front.png"),
    "ODAGIRI": ("Mr. Odagiri, a distinguished Japanese gentleman in his mid-70s, short combed-back white hair, a short neat white moustache, no glasses",
                C + "odagiri-front.png"),
    "TANTO": ("a Japanese property-management clerk in his early 30s, short neat black hair, clean-shaven, NO glasses", C + "tanto-front.png"),
    "MAMAA": ("Mama A, a Japanese woman in her mid-30s with a honey-brown curly bob", C + "mamaA-front.png"),
    "MAMAB": ("Mama B, a Japanese woman in her late 30s with a sleek long black high ponytail, NO glasses", C + "mamaB-front.png"),
    "MAMAC": ("Mama C, a Japanese woman around 40 with long loose light-brown hair", C + "mamaC-front.png"),
    "JUMIN": ("a Japanese man in his early 50s with short salt-and-pepper hair and light stubble", C + "jumin-front.png"),
    "CROWD": ("many ordinary Japanese residents of various ages seen from behind or far away, faces soft and unrecognizable", None),
    "KIDS": ("a few small children playing, seen far away and soft, faces unrecognizable", None),
}
WARD = {
    "YUMI": "a plain navy-blue fine-knit cardigan over a plain white collared blouse, plain charcoal-grey knee-length skirt, a slim plain silver wristwatch",
    "REIKA": "a tailored cream tweed jacket with no logo over a black silk camisole, cream wide-leg trousers, nude heels, a thin gold bangle on the right wrist",
    "RIKO": "a plain mustard-yellow cotton dress, white socks, plain pink sneakers",
    "ODAGIRI": "a charcoal three-piece suit, plain grey tie, white shirt, a plain dark wooden walking cane",
    "TANTO": "a plain mid-grey business suit, white shirt, plain navy tie, no badge, no lanyard",
    "MAMAA": "a plain pastel-pink knit sweater and white pleated skirt", "MAMAB": "a plain white blouse and black trousers",
    "MAMAC": "a plain beige knit dress with a camel cardigan", "JUMIN": "a plain navy polo shirt and khaki chinos",
}
EXPR = {
    ("YUMI", "firm"): C + "yumi-expr-firm.png", ("YUMI", "smile"): C + "yumi-expr-smile.png", ("YUMI", "q45"): C + "yumi-q45.png",
    ("REIKA", "smirk"): C + "reika-expr1.png", ("REIKA", "panic"): C + "reika-expr2.png", ("REIKA", "tears"): C + "reika-expr3.png",
    ("RIKO", "sad"): C + "riko-expr1.png", ("RIKO", "teary"): C + "riko-expr2.png", ("RIKO", "happy"): C + "riko-expr3.png",
    ("ODAGIRI", "calm"): C + "odagiri-expr1.png", ("ODAGIRI", "stern"): C + "odagiri-expr2.png", ("ODAGIRI", "smile"): C + "odagiri-expr3.png",
    ("TANTO", "nervous"): C + "tanto-expr1.png", ("TANTO", "resolute"): C + "tanto-expr3.png",
    ("MAMAA", "gossip"): C + "mamaA-expr2.png", ("MAMAA", "shock"): C + "mamaA-expr3.png", ("JUMIN", "angry"): C + "jumin-expr3.png",
}
LOC = {
    "EXT_LOW": C + "loc-exterior-p1.png", "EXT_ENT": C + "loc-exterior-p2.png", "EXT_FACADE": C + "loc-exterior-p3.png", "EXT_DUSK": C + "loc-exterior-p4.png",
    "LOBBY": C + "loc-lobby-p1.png", "EV_MAIN": C + "loc-lobby-p2.png", "EV_OPEN": C + "loc-lobby-p3.png", "EV_FREIGHT": C + "loc-lobby-p5.png",
    "KIDS_CORR": C + "loc-kidsroom-p1.png", "KIDS_DOOR": C + "loc-kidsroom-p2.png", "KIDS_IN": C + "loc-kidsroom-p4.png",
    "HOME_DINE": C + "loc-yumi-home-p1.png", "HOME_TABLE": C + "loc-yumi-home-p2.png", "HOME_SOFA": C + "loc-yumi-home-p3.png",
    "OFFICE": C + "loc-office-p1.png", "OFFICE_FILE": C + "loc-office-p4.png",
    "HALL_WIDE": T + "loc-hall-day-wide-back.png", "HALL_SCREEN": C + "loc-hall-p3.png", "HALL_LECTERN": C + "loc-hall-p4.png",
    "HALL_ROWS": C + "loc-hall-p5.png", "HALL_REV": C + "loc-hall-p2.png",
    "P_BAG": C + "prop-bag.png", "P_BOOK": C + "prop-passbook.png", "P_ENV": C + "prop-envelope.png", "P_BOX": C + "prop-box.png",
}
PRESET = ("Photorealistic live-action Japanese drama, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, "
          "modern Tokyo tower-condominium mise-en-scene, no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, "
            "logo on shirt, brand logos, monograms on bags, signage lettering, posters with writing, floor numbers, printed labels, "
            "watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, extra arms, duplicate people")
PLAIN = "All papers, screens, signs, plates and labels are completely blank; no letters, numbers or symbols anywhere in the frame."
LENS = {
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh, the subject fills more than 70 percent of the frame",
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait",
    "ch": "85mm prime lens, f/1.8, choker framing from forehead to chin, razor-sharp eyes, soft bokeh",
    "ms": "50mm lens, f/2.8, natural perspective, rule of thirds",
    "ws": "35mm lens, f/4.0, environmental storytelling, balanced composition",
    "ews": "24mm wide angle, deep focus, imposing perspective, sharp architectural lines",
}
LIGHT = {
    "lobby": "bright cool 5600K daylight through the tall lobby glass, polished marble reflections, crisp contrast",
    "lobby_cold": "cool 5600K daylight from above, hard reflections on steel, cold oppressive mood, chiaroscuro on faces",
    "kids": "soft diffuse daylight through the glass wall, cheerful warm tone, gentle contrast",
    "home": "warm 3200K pendant lamp at night, soft shadows, intimate quiet mood, dark window with distant lights",
    "laptop": "night, the cool glow of a laptop screen on the face, warm pendant lamp behind, deep shadows",
    "office": "cool fluorescent 5600K office light from above, flat-ish but with soft shadow under the brow",
    "hall": "cool crisp 5600K daylight from the tall windows on the left, soft overhead panel light, gentle rim light",
    "hall_press": "hard cold overhead fluorescent light pressing down, 6000K, dark eye sockets, oppressive chiaroscuro",
    "hall_reveal": "strong cool backlight from the windows, high-contrast chiaroscuro, rim light on hair, tense mood",
    "ext": "clear blue sky, crisp 5600K sunlight from the upper-left",
    "dusk": "golden-hour dusk, warm 3200K low sun, long soft shadows, warm rim light",
}
ANGLE = {"EL": "eye-level", "HA": "high-angle looking down", "LA": "low-angle looking up", "OH": "overhead straight down 90 degrees",
         "BE": "extreme bird's-eye view straight down from high above", "SIDE": "eye-level from the side or behind"}


def S(sid, scene, kind, lens, light, angle, who, loc, subject, line=None, fx="", motion="", expr=None):
    """kind: d(OMNI 대사) / react(리액션 정지) / ins(인서트 정지) / face(얼굴 i2v pro) / sil(실루엣·뒷모습 i2v lite) /
    empty(무인 i2v lite) / estill(무인 정지) / gfx(로컬 그래픽 합성, 무료) / reuse:<id> / card."""
    return dict(id=sid, scene=scene, kind=kind, lens=lens, light=light, angle=angle, who=who, loc=loc,
                subject=subject, line=line, fx=fx, motion=motion, expr=expr)


SHOTS = [
    # ① 후크 S01 — 로비
    S("S01a", "S01", "face", "ms", "lobby_cold", "LA", ["REIKA", "MAMAA"], "EV_OPEN",
      "Low angle from Yumi's height: inside the open mirrored passenger elevator Reika stands in the doorway blocking it, chin raised, cold smirk, burgundy quilted bag on her forearm; Mama A half behind her.",
      motion="Reika lifts her chin slightly and shifts her weight to block the doorway; Mama A stays still behind her. Nobody walks.", expr="smirk"),
    S("S01b", "S01", "d", "cu", "lobby_cold", "LA", ["REIKA"], "EV_OPEN",
      "Chest-up close-up of Reika from slightly below inside the elevator, condescending smirk, eyes looking down at someone, mirrored elevator wall soft behind her.", line="line001", expr="smirk"),
    S("S01c", "S01", "react", "cu", "lobby", "HA", ["YUMI"], "LOBBY",
      "High angle close-up of Yumi in the lobby looking up, composed but stung, lips pressed together, marble lobby soft behind."),
    S("S01d", "S01", "ins", "ecu", "lobby_cold", "EL", ["REIKA"], "EV_MAIN",
      "Insert: the brushed-steel elevator doors almost closed, a thin vertical sliver showing a woman's red-lipped smirk inside."),
    S("S01e", "S01", "ins", "ecu", "lobby", "HA", ["RIKO", "YUMI"], "LOBBY",
      "High angle insert: a little girl's small hand tightly clutching the hem of a woman's charcoal skirt, marble floor below.", line="line002"),
    S("S01f", "S01", "sil", "ms", "lobby", "SIDE", ["YUMI", "RIKO"], "EV_MAIN",
      "Side view medium: Yumi standing quietly in front of the closed steel elevator doors holding Riko's hand, both seen in profile from behind, mouths not visible.", line="line003", fx="pull",
      motion="Both stand still facing the closed doors; Riko leans against Yumi's side. Nobody walks or turns."),
    S("S01g", "S01", "react", "cu", "lobby_cold", "EL", ["YUMI"], "EV_MAIN",
      "Close-up of Yumi facing the closed steel doors, her expression slowly cooling into calm resolve, cold light from above.", line="line004", expr="firm"),
    S("S01h", "S01", "ins", "ecu", "lobby_cold", "EL", ["YUMI"], "EV_MAIN",
      "Macro insert: Yumi's eyes behind thin silver-rimmed glasses reflected in the polished steel elevator door, cold and determined.", line="line005", fx="push"),
    S("S01i", "S01", "card", "ews", "lobby", "EL", [], None, "Black title card 『タワマンのボスママ』."),
    # ② 발단
    S("S02a", "S02", "empty", "ews", "ext", "LA", [], "EXT_LOW", "No people. Very low angle up the full height of the 42-storey glass tower against a clear blue sky.", line="line006",
      motion="Clouds drift slowly; sunlight glints on the glass. No people."),
    S("S02a2", "S02", "sil", "ws", "lobby", "SIDE", ["YUMI", "RIKO"], "LOBBY", "Side wide: Yumi and Riko walking hand in hand across the marble lobby, small and ordinary.",
      motion="Mother and daughter walk slowly left to right across the frame, never toward the camera."),
    S("S02a3", "S02", "ins", "ecu", "home", "OH", ["YUMI"], "HOME_TABLE", "Overhead insert: a woman's quick fingers on a calculator beside a ledger and receipts, silver wristwatch (accountant's hands)."),
    S("S02b", "S02", "gfx", "ews", "ext", "EL", [], None, "Graphic: the tower silhouette sliced into floor bands (上層階 / 中層階 / 低層階 pyramid), composited locally.", line="line007"),
    S("S02b2", "S02", "estill", "ms", "ext", "EL", [], "EXT_ENT", "No people. The glossy glass entrance plaza of the tower, crisp and exclusive."),
    S("S02c", "S02", "sil", "ws", "lobby", "EL", ["JUMIN", "MAMAB", "MAMAC"], "LOBBY",
      "Wide lobby: an ordinary middle-aged resident steps aside from the elevator bank as two well-dressed women pass in front of him; all seen from the side and behind, faces small.", line="line008",
      motion="The man takes one small step back aside; the two women glide past. Faces stay small and turned away."),
    S("S02c2", "S02", "gfx", "ecu", "lobby", "EL", [], "LOBBY", "Insert, no people: a blank lounge reservation board on a stand in the lobby (「上層階優先」 composited)."),
    S("S02d", "S02", "sil", "ews", "lobby", "HA", ["REIKA", "MAMAA", "MAMAB"], "LOBBY",
      "High angle wide from the mezzanine: Reika crossing the gleaming marble lobby flanked by two mothers, heels reflected on the floor, tiny figures.", line="line009",
      motion="The three women walk slowly across the lobby away from the camera; reflections follow them."),
    S("S02e", "S02", "face", "ms", "lobby", "LA", ["REIKA"], "LOBBY",
      "Low angle medium: Reika pauses in the lobby, chin raised, a satisfied queenly smile, glass and light behind her.",
      motion="Reika tilts her head up slightly and smiles; she does not walk.", expr="smirk"),
    # S03 키즈룸
    S("S03a", "S03", "gfx", "ecu", "kids", "EL", [], "KIDS_DOOR", "Insert, no people: the blank white plaque beside the glass kids-room door (「40階以上の居住者専用」 composited)."),
    S("S03b", "S03", "sil", "ms", "kids", "SIDE", ["RIKO", "KIDS"], "KIDS_CORR",
      "From behind: Riko alone in the corridor looking through the glass wall at children playing inside on colourful mats (children far and soft).",
      motion="Riko stands still watching; the children inside move softly out of focus."),
    S("S03c", "S03", "sil", "ms", "kids", "EL", ["MAMAA", "RIKO"], "KIDS_CORR",
      "Mama A crouches in front of Riko with her back to the camera (her face not visible), Riko facing her, small and sad, by the glass door.", line="line010",
      motion="Mama A tilts her head with a fake sympathetic gesture, back to the camera; Riko lowers her eyes.", expr=None),
    S("S03d", "S03", "ins", "ecu", "kids", "EL", ["RIKO"], "KIDS_DOOR", "Insert: a little girl's small palm pressed flat against the glass door, colourful play mats blurred beyond."),
    S("S03e", "S03", "react", "cu", "kids", "HA", ["RIKO"], "KIDS_CORR", "High angle close-up of Riko looking down, lower lip trembling, eyes wet.", line="line011", expr="teary"),
    S("S03e2", "S03", "ins", "ecu", "kids", "EL", [], "KIDS_DOOR", "Insert, no people: colourful toys and play mats seen through the glass, softly blurred and out of reach."),
    S("S03f", "S03", "sil", "ws", "kids", "EL", ["YUMI", "RIKO"], "KIDS_CORR",
      "Wide down the corridor: Yumi seen from behind standing a few metres behind Riko at the glass, her hands clenched at her sides.", line="line012",
      motion="Yumi's clenched hands tighten slightly; she does not move forward. Riko stays at the glass."),
    # S03-2 집 거실(밤)
    S("S03-2a", "S03-2", "sil", "ws", "home", "EL", ["YUMI", "RIKO"], "HOME_SOFA",
      "Night, warm lamp: Yumi on the grey sofa holding Riko curled in her lap, seen from the side, faces soft, Riko's face buried in her cardigan.",
      motion="Yumi gently rocks once; Riko stays curled. Nobody stands."),
    S("S03-2b", "S03-2", "ins", "cu", "home", "EL", ["RIKO", "YUMI"], "HOME_SOFA",
      "Close insert: Riko's face buried against Yumi's navy cardigan, only her pigtails and a cheek visible, eyes closed; no mouth visible.", line="line013"),
    S("S03-2c", "S03-2", "ins", "ecu", "home", "OH", ["YUMI", "RIKO"], "HOME_SOFA",
      "Overhead insert: a woman's hand slowly stroking a little girl's black hair, a silver wristwatch, warm lamplight.", line="line014"),
    # S04 우편함·외벽
    S("S04a", "S04", "ins", "ecu", "lobby", "EL", ["YUMI"], "LOBBY",
      "Insert: a woman's hand pulls a blank white notice sheet out of a brushed-steel mailbox slot in the tower lobby."),
    S("S04b", "S04", "gfx", "ecu", "lobby", "OH", ["YUMI"], "LOBBY",
      "Overhead insert: the blank notice held in a woman's hands (修繕積立金 1.8倍 値上げ予定 composited).", line="line015"),
    S("S04b2", "S04", "sil", "ms", "lobby", "SIDE", ["YUMI"], "LOBBY", "Side medium: Yumi standing alone by the brushed-steel mailboxes reading the notice.",
      motion="Yumi holds the notice and reads; she does not move."),
    S("S04c", "S04", "react", "cu", "lobby", "EL", ["YUMI"], "LOBBY", "Close-up of Yumi reading the notice, eyes narrowing behind her glasses, lobby soft behind.", line="line016", expr="firm"),
    S("S04d", "S04", "estill", "ms", "ext", "LA", [], "EXT_FACADE", "No people. Low angle: clean, undamaged glass and metal facade panels of the six-year-old tower, crisp sunlight."),
    # S05 임시총회
    S("S05a", "S05", "sil", "ews", "hall", "HA", ["CROWD", "REIKA"], "HALL_WIDE",
      "High angle wide from the back: the assembly hall about half full of seated residents seen from behind, Reika standing small at the lectern by the blank screen.",
      motion="Residents shift slightly in their seats; Reika stays at the lectern."),
    S("S05b", "S05", "sil", "ws", "hall", "EL", ["CROWD", "REIKA"], "HALL_ROWS",
      "Over the heads of seated residents (backs of heads soft in the foreground): Reika at the lectern far away, small and slightly soft, gesturing grandly; her mouth not readable.", line="line017",
      motion="Reika spreads one hand in a grand gesture; the residents' heads stay still."),
    S("S05c", "S05", "ins", "ms", "hall", "EL", ["MAMAA", "MAMAB", "MAMAC"], "HALL_ROWS",
      "Insert at chest height: three mothers in the front row clapping eagerly, hands and torsos only, faces cropped out."),
    S("S05d", "S05", "face", "ms", "hall", "EL", ["YUMI", "CROWD"], "HALL_WIDE",
      "Medium: in the middle rows Yumi stands up among seated residents with her right hand raised, calm, residents' heads soft around her.",
      motion="Yumi holds her raised hand steady and breathes; residents around her turn their heads slightly. She does not walk."),
    S("S05e", "S05", "d", "cu", "hall", "EL", ["YUMI"], "HALL_WIDE",
      "Chest-up close-up of Yumi standing in the middle rows, polite and calm, looking just off-lens toward the lectern, the hall behind her reduced to soft out-of-focus colour shapes of seated people and tall windows.", line="line018", expr="firm"),
    S("S05f", "S05", "ins", "ecu", "hall_press", "LA", ["REIKA"], "HALL_LECTERN",
      "Low insert: on the stage a woman in cream wide-leg trousers slowly crosses her legs, nude heels, the lectern edge above."),
    # S06 모욕
    S("S06a", "S06", "sil", "ms", "hall_press", "SIDE", ["REIKA"], "HALL_LECTERN",
      "Side profile medium of Reika at the lectern holding a handheld microphone to her lips so her mouth is hidden, eyes half-lidded, condescending.", line="line019", fx="dutch5",
      motion="Reika lowers her eyelids lazily, the microphone stays covering her mouth. She does not turn."),
    S("S06b", "S06", "d", "cu", "hall_press", "LA", ["REIKA"], "HALL_LECTERN",
      "Chest-up close-up of Reika at the lectern from slightly below, contemptuous mocking smile, hard top light, blank screen soft behind.", line="line020", expr="smirk"),
    S("S06c", "S06", "ins", "ecu", "hall_press", "EL", ["REIKA"], "P_BAG",
      "Macro insert: the quilted burgundy handbag with a gold chain on Reika's arm, a thin gold bangle, glossy and expensive, no logo."),
    S("S06d", "S06", "sil", "ms", "hall", "SIDE", ["MAMAA", "MAMAB"], "HALL_ROWS",
      "Side-rear medium of the front row: Mama A leans toward Mama B laughing behind her hand, faces turned away from camera.", line="line021",
      motion="Mama A leans in and shakes with laughter, face turned away; Mama B nods."),
    S("S06e", "S06", "react", "ms", "hall_press", "HA", ["YUMI"], "HALL_WIDE",
      "High angle medium: Yumi slowly lowering her head among the seated residents, small and alone under the hard light."),
    S("S06-2a", "S06-2", "sil", "ws", "hall", "HA", ["CROWD"], "HALL_ROWS",
      "High angle: rows of residents averting their eyes, looking down at their laps, backs and side profiles only, faces unrecognizable.", line="line022",
      motion="A few residents look down or away; nobody stands."),
    S("S06-2b", "S06-2", "ins", "ecu", "hall", "EL", ["JUMIN"], "HALL_ROWS",
      "Insert: a man's hands clasped tightly on his khaki lap, knuckles pale."),
    # S07 냉정한 손(1차 광고 직전)
    S("S07a", "S07", "ins", "ecu", "hall", "OH", ["YUMI"], "HALL_ROWS",
      "Overhead macro under the table edge: a woman's hand writing fast in a small plain notebook, only the pen tip and blank lines visible, silver wristwatch.", line="line023"),
    S("S07a2", "S07", "sil", "ms", "hall", "SIDE", ["YUMI"], "HALL_ROWS", "Side medium: Yumi seated with her head bowed among the residents, one hand moving under the table edge.",
      motion="Yumi keeps her head bowed; her hand writes slowly below frame."),
    S("S07b", "S07", "react", "cu", "hall", "EL", ["YUMI"], "HALL_WIDE",
      "Close-up of Yumi with her head still bowed but her eyes raised, sharp and calculating behind her glasses.", line="line024", expr="firm"),
    S("S07c", "S07", "ins", "ecu", "hall_reveal", "EL", ["YUMI"], "HALL_WIDE",
      "Macro insert: Yumi's eye behind the glasses lens, the distant lectern reflected in the lens, cold resolve.", line="line025", fx="push"),
    S("S07c2", "S07", "ins", "ecu", "hall", "SIDE", ["YUMI"], "HALL_ROWS", "Side macro: the pen tip underlining twice on a blank notebook line, decisive."),
    # ③ S08 밤 식탁
    S("S08a", "S08", "sil", "ws", "home", "SIDE", ["YUMI", "RIKO"], "HOME_DINE",
      "Night: Yumi seen from behind at the small dining table under the pendant lamp with papers and a laptop; Riko asleep on the sofa in the soft background under a throw blanket.", line="line026",
      motion="Yumi turns a page slowly; Riko sleeps. No one stands."),
    S("S08a2", "S08", "ins", "ecu", "home", "EL", ["RIKO"], "HOME_SOFA", "Insert: Riko's small sleeping hand resting on a soft throw blanket on the sofa, warm lamplight."),
    S("S08b", "S08", "ins", "ecu", "home", "OH", [], "HOME_TABLE",
      "Overhead insert, no people: blank receipts, invoices and bank statements spread on the table, a red pen and a calculator with a blank display.", line="line027"),
    S("S08b2", "S08", "ins", "ecu", "laptop", "EL", ["YUMI"], "HOME_TABLE", "Insert: a woman's fingers typing fast on a laptop keyboard beside a calculator, cool screen glow."),
    # S09 관리사무소
    S("S09a", "S09", "sil", "ms", "office", "EL", ["TANTO", "YUMI"], "OFFICE",
      "Over the clerk's shoulder (back of his head soft in the foreground, his face not visible) toward Yumi at the service counter, serious.", line="line028",
      motion="The clerk's head lowers slightly; Yumi listens still."),
    S("S09a2", "S09", "react", "cu", "office", "LA", ["YUMI"], "OFFICE", "Slightly low close-up of Yumi at the counter listening intently, hands resting on the counter, calm.", expr="firm"),
    S("S09b", "S09", "ins", "ecu", "office", "EL", ["TANTO"], "OFFICE_FILE",
      "Insert: a man's hands in grey suit sleeves slide a thick plain grey binder across the counter, hesitating, then pushing it forward.", line="line029"),
    S("S09c", "S09", "react", "cu", "office", "EL", ["YUMI"], "OFFICE", "Close-up of Yumi receiving the file, a small grateful nod, determined eyes.", expr="firm"),
    # S10 장부
    S("S10a", "S10", "gfx", "ecu", "home", "OH", ["YUMI"], "HOME_TABLE",
      "Overhead macro: a red pen circling figures on a ledger page (外壁調査費 / 緊急補修費 composited).", line="line030"),
    S("S10a2", "S10", "gfx", "ecu", "home", "EL", [], "HOME_TABLE", "Insert, no people: a calculator on the table, display blank in the keyframe (24,000,000 composited)."),
    S("S10a3", "S10", "react", "cu", "laptop", "HA", ["YUMI"], "HOME_DINE", "High angle close-up of Yumi looking down at the ledger, lips tight, glasses reflecting the screen."),
    S("S10b", "S10", "react", "cu", "laptop", "EL", ["YUMI"], "HOME_DINE", "Close-up of Yumi at night lit by the laptop glow, eyes cold and focused.", line="line031", expr="firm"),
    S("S10b2", "S10", "estill", "ms", "office", "EL", [], None, "No people. A plain anonymous door in a dim rental-office corridor, completely blank nameplate, a single overhead light."),
    S("S10c", "S10", "gfx", "ecu", "laptop", "EL", [], "HOME_TABLE", "Insert: laptop screen (法人登記 代表者 西園寺 剛 composited), blank in the keyframe.", line="line032"),
    # S11 SNS
    S("S11a", "S11", "gfx", "ecu", "laptop", "EL", ["YUMI"], "HOME_TABLE",
      "Insert: a smartphone in a woman's hand, screen blank in the keyframe (fictional SNS feed of luxury bags composited).", line="line033"),
    S("S11a2", "S11", "gfx", "ecu", "laptop", "SIDE", [], "HOME_TABLE", "Low side insert: the smartphone propped on the table beside a bank statement, screen blank in the keyframe (SNS post of a new bag composited)."),
    S("S11b", "S11", "ins", "ecu", "home", "OH", [], "HOME_TABLE", "Overhead insert, no people: tall stacks of printouts with yellow highlighter strokes (no readable text), a cold mug of tea."),
    S("S11c", "S11", "react", "ms", "laptop", "HA", ["YUMI"], "HOME_DINE",
      "High angle medium: Yumi late at night at the table buried in papers, rubbing her eyes under her glasses, the laptop glowing.", line="line034"),
    S("S11c2", "S11", "ins", "ecu", "home", "SIDE", ["YUMI"], "HOME_TABLE", "Side macro: a yellow highlighter dragging across a line of a blank printout, then a tick mark."),
    S("S11c3", "S11", "react", "cu", "laptop", "EL", ["YUMI"], "HOME_DINE", "Close-up of Yumi at dawn-tired night, a faint grim smile of certainty, laptop glow.", expr="firm"),
    # S12 명부
    S("S12a", "S12", "gfx", "ecu", "office", "OH", ["YUMI"], "OFFICE_FILE",
      "Overhead macro: a residents' roster table, a woman's finger stops on one row (住民名簿 42階 composited).", line="line035"),
    S("S12b", "S12", "react", "ch", "laptop", "EL", ["YUMI"], "HOME_DINE", "Choker close-up of Yumi's eyes widening slightly behind her glasses in a quiet realization.", expr="firm"),
    S("S12-2a", "S12-2", "ins", "ecu", "home", "OH", ["YUMI"], "P_ENV",
      "Overhead insert at night: a woman's hands sealing a plain white envelope on the wooden table, the address side face down."),
    # S12-3 총회 당일
    S("S12-3a", "S12-3", "sil", "ews", "hall", "EL", ["CROWD"], "HALL_WIDE",
      "Wide: residents streaming into the assembly hall and filling almost every seat, seen from behind, faces unrecognizable.", line="line036",
      motion="Residents walk away from the camera to their seats and sit down. No one faces the camera."),
    S("S12-3a2", "S12-3", "ins", "ecu", "hall", "EL", ["CROWD"], "HALL_ROWS", "Insert: rows of residents' hands holding plain blank agenda sheets on their laps."),
    S("S12-3b", "S12-3", "sil", "ms", "lobby_cold", "SIDE", ["YUMI", "REIKA"], "LOBBY",
      "Over Yumi's shoulder (her shoulder soft in the foreground): Reika leaning close behind her ear with her face turned away from the camera, two mothers soft behind.", line="line037",
      motion="Reika leans in slightly, face turned away; Yumi does not move."),
    S("S12-3c", "S12-3", "ins", "ecu", "lobby", "EL", ["YUMI"], "LOBBY", "Insert: a woman's hand calmly adjusting the strap of a plain black laptop bag on her shoulder."),
    # S13 정기총회
    S("S13a", "S13", "sil", "ews", "hall", "HA", ["CROWD", "REIKA"], "HALL_WIDE",
      "High angle wide from the back: the hall packed with about a hundred seated residents seen from behind, Reika small at the lectern before the blank screen.",
      motion="Residents murmur and shift slightly; Reika stands at the lectern."),
    S("S13b", "S13", "d", "cu", "hall_press", "LA", ["REIKA"], "HALL_LECTERN",
      "Chest-up close-up of Reika at the lectern from slightly below, triumphant smile, chin raised, microphone on a stand below frame.", line="line038", expr="smirk"),
    S("S13c", "S13", "ins", "ecu", "hall", "EL", ["YUMI"], "HALL_ROWS", "Insert: a woman's hands plugging a plain cable into a slim laptop on her lap, silver wristwatch."),
    S("S13d", "S13", "d", "cu", "hall", "EL", ["YUMI"], "HALL_WIDE",
      "Chest-up close-up of Yumi standing in the packed middle rows, calm and resolute, looking just off-lens toward the lectern, the packed hall behind her reduced to soft out-of-focus colour shapes and tall windows.", line="line039", expr="firm"),
    S("S13e", "S13", "gfx", "ews", "hall_reveal", "EL", ["CROWD"], "HALL_SCREEN",
      "The large projector screen lights up above the lectern, residents' heads in silhouette below (bank statement graphic composited).", line="line040"),
    S("S13f", "S13", "sil", "ws", "hall_reveal", "LA", ["YUMI", "CROWD"], "HALL_WIDE", "Low angle from behind Yumi (her standing silhouette in the foreground, back to the camera) toward the glowing projector screen, residents' heads tilting up below.",
      motion="Yumi stands still with her back to the camera; residents' heads tilt up slowly toward the light. Nobody turns around."),
    # S14 통장 3쌍
    S("S14a", "S14", "gfx", "ws", "hall_reveal", "EL", [], "HALL_SCREEN", "Screen graphic pair 1: passbook row 2,000,000円 ⇄ SNS post 「主人からのサプライズ♡」 with a red arrow (local composite)."),
    S("S14b", "S14", "react", "ms", "hall", "EL", ["MAMAA", "MAMAB", "MAMAC"], "HALL_ROWS",
      "Medium of the three mothers in the front row exchanging uneasy glances, smiles fading.", expr=None),
    S("S14c", "S14", "gfx", "ws", "hall_reveal", "EL", [], "HALL_SCREEN", "Screen graphic pair 2: 2,500,000円 ⇄ 「冬休みはハワイのスイートで」."),
    S("S14d", "S14", "sil", "ws", "hall", "HA", ["CROWD"], "HALL_ROWS", "High angle: back rows of residents leaning to whisper to each other, faces unrecognizable.",
      motion="Residents lean toward each other and murmur; nobody stands."),
    S("S14e", "S14", "gfx", "ws", "hall_reveal", "EL", [], "HALL_SCREEN", "Screen graphic pair 3 frozen: 3,000,000円 ⇄ 「主人が買ってくれた新作♥」, ざわ…ざわ… overlay (BGM cut, heartbeat)."),
    S("S14f", "S14", "react", "cu", "hall", "EL", ["MAMAA"], "HALL_ROWS", "Close-up of Mama A frozen in shock, wide eyes, lips parted.", fx="split3", expr="shock"),
    S("S14g", "S14", "sil", "ws", "hall_reveal", "LA", ["CROWD"], "HALL_REV", "Low angle: silhouettes of residents rising one by one from their seats against the bright windows.", fx="split3",
      motion="Two or three silhouettes slowly stand up; the rest stay seated."),
    S("S14h", "S14", "react", "cu", "hall_press", "EL", ["REIKA"], "HALL_LECTERN", "Chest-up close-up of Reika at the lectern, smile frozen, a single bead of sweat running down her temple.", fx="split3", expr="panic"),
    S("S14i", "S14", "reuse:S14e", "ws", "hall_reveal", "EL", [], None, "Reuse of S14e (pair 3 frozen) under the killing line.", line="line041"),
    S("S14j", "S14", "sil", "ews", "hall_reveal", "HA", ["CROWD"], "HALL_REV",
      "From beside the lectern looking out over the packed hall: a hundred heads all turned toward the screen, backlit, faces unrecognizable.", line="line042",
      motion="The crowd stays frozen, staring; a faint stir."),
    S("S14k", "S14", "sil", "ms", "hall", "SIDE", ["JUMIN", "CROWD"], "HALL_ROWS",
      "Side-rear medium: a middle-aged man in a navy polo shirt stands up from his seat pointing at the screen, his face turned away.", line="line043",
      motion="The man thrusts his arm toward the screen once and holds it; his face stays turned away."),
    S("S14l", "S14", "d", "cu", "hall_press", "EL", ["REIKA"], "HALL_LECTERN",
      "Chest-up close-up of Reika at the lectern, panicked, eyes darting, forced denial, sweat on her temple.", line="line044", expr="panic"),
    S("S14m", "S14", "d", "cu", "hall_reveal", "EL", ["TANTO"], "HALL_ROWS",
      "Chest-up close-up of the young property-management clerk standing in the side aisle, resolute for the first time, the hall behind him reduced to soft out-of-focus colour shapes.", line="line045", expr="resolute"),
    S("S14n", "S14", "ins", "ecu", "hall", "EL", ["TANTO"], "P_BOOK", "Insert: a man's hand sets a plain dark-green passbook with a blank cover down firmly on the table."),
    S("S14n2", "S14", "react", "cu", "hall_press", "HA", ["REIKA"], "HALL_LECTERN", "High angle close-up of Reika staring at the passbook, color draining from her face.", expr="panic"),
    S("S14o", "S14", "sil", "ws", "hall", "HA", ["MAMAA", "MAMAB", "MAMAC"], "HALL_ROWS",
      "High angle: in the front row the three mothers quietly shift their chairs away from the empty seat beside the stage, faces turned down.", line="line046",
      motion="The three women shift sideways in their seats, away from the stage; faces down."),
    # S15 레이카 폭발(2차 광고 직전)
    S("S15a", "S15", "ins", "ecu", "hall_press", "EL", ["REIKA"], "HALL_LECTERN",
      "Insert: a woman's hand with a thin gold bangle gripping the microphone stand on the lectern hard, knuckles white.", fx="dutch7"),
    S("S15b", "S15", "d", "cu", "hall_press", "EL", ["REIKA"], "HALL_LECTERN",
      "Chest-up close-up of Reika at the lectern losing control, furious, hair slightly disheveled, hard top light.", line="line047", fx="hh", expr="panic"),
    S("S15c", "S15", "sil", "ms", "hall", "EL", ["CROWD"], "HALL_ROWS",
      "Medium of the front rows: residents flinching back in their seats at the outburst, faces soft and unrecognizable.",
      motion="Several residents lean back sharply in their seats once and freeze. Nobody stands."),
    # ④ S16 진짜 주인
    S("S16a", "S16", "sil", "ews", "hall_reveal", "LA", ["ODAGIRI", "CROWD"], "HALL_WIDE",
      "Low angle wide from the side of the hall: at the very back an elderly gentleman with a wooden cane slowly rising from his seat, backlit by the windows.",
      motion="The old gentleman straightens up with his cane, slowly; the seated residents stay still."),
    S("S16b", "S16", "d", "cu", "hall_reveal", "LA", ["ODAGIRI"], "HALL_REV",
      "Chest-up close-up of Mr. Odagiri from slightly below at the back of the hall, calm and dignified, strong backlight rim on his white hair.", line="line048", expr="calm"),
    S("S16c", "S16", "sil", "ws", "hall", "EL", ["CROWD"], "HALL_ROWS", "From the back row: residents turning their heads toward the back of the hall, faces partly in profile and soft.",
      motion="Residents turn their heads about 20 degrees toward the camera; nobody stands."),
    S("S16d", "S16", "react", "cu", "hall_press", "HA", ["REIKA"], "HALL_LECTERN", "High angle close-up of Reika at the lectern going pale, frozen.", fx="dollyzoom", expr="panic"),
    S("S16e", "S16", "reuse:S12-2a", "ecu", "home", "OH", [], None, "Reuse of S12-2a (sealing the envelope) as a flash under NA24.", line="line049"),
    S("S16f", "S16", "d", "cu", "hall_reveal", "LA", ["ODAGIRI"], "HALL_REV",
      "Chest-up close-up of Mr. Odagiri, stern judging gaze, measured, backlit rim.", line="line050", expr="stern"),
    S("S16g", "S16", "react", "cu", "hall_press", "HA", ["REIKA"], "HALL_LECTERN", "High angle close-up of Reika trembling, lips parted, eyes glassy.", expr="panic"),
    S("S16g2", "S16", "sil", "ms", "hall", "SIDE", ["CROWD"], "HALL_ROWS", "Side medium: residents exchanging stunned looks, faces soft and unrecognizable.",
      motion="Two residents turn to each other in disbelief; nobody stands."),
    S("S16h", "S16", "gfx", "ecu", "office", "OH", [], "OFFICE_FILE", "Overhead insert: a plain management-rules booklet open on the table (区分所有者 ⇔ 賃借人 contrast composited left and right).", line="line051"),
    S("S16h2", "S16", "sil", "ms", "hall_reveal", "SIDE", ["ODAGIRI"], "HALL_REV", "Medium from behind: Mr. Odagiri standing tall with his cane, back to the camera, facing the stage.",
      motion="Mr. Odagiri stands still, his back to the camera; only his shoulders move with breath."),
    S("S16i", "S16", "ins", "ecu", "hall_reveal", "EL", ["ODAGIRI"], "HALL_REV", "Insert: an old man's hand resting on the curved handle of a dark wooden cane, a white shirt cuff.", line="line052"),
    S("S16i2", "S16", "ins", "ecu", "hall_press", "EL", ["REIKA"], "P_BAG", "Insert: Reika's trembling fingers clutching the gold chain strap of the burgundy bag."),
    # S17 붕괴
    S("S17a", "S17", "ins", "ecu", "hall_press", "SIDE", ["REIKA"], "HALL_LECTERN", "Side insert: a woman's knees in cream wide-leg trousers buckling, nude heels wobbling on the stage floor."),
    S("S17b", "S17", "sil", "ews", "hall_press", "BE", ["REIKA"], "HALL_LECTERN",
      "Extreme bird's-eye from straight above: Reika already sitting collapsed on the pale wood floor beside the lectern, the burgundy bag spilled open beside her, tiny and broken.",
      motion="Reika's shoulders tremble; she stays sitting on the floor. Nothing else moves."),
    S("S17d", "S17", "d", "cu", "hall_press", "HA", ["REIKA"], "HALL_LECTERN",
      "High angle chest-up close-up of Reika sitting on the floor looking up, tearful and desperate, mascara slightly smudged.", line="line053", expr="tears"),
    S("S17c", "S17", "gfx", "ecu", "hall_press", "OH", [], "P_BAG", "Overhead macro: spilled contents of the burgundy bag on the floor, among them a plain envelope (家賃督促状 composited, appears with a delay)."),
    S("S17e", "S17", "d", "cu", "hall_reveal", "LA", ["ODAGIRI"], "HALL_REV",
      "Low angle chest-up close-up of Mr. Odagiri looking down, calm and unforgiving.", line="line054", expr="stern"),
    S("S17e2", "S17", "react", "cu", "hall_press", "HA", ["REIKA"], "HALL_LECTERN", "High angle close-up of Reika on the floor, the words hitting her, mouth falling open, tears welling.", expr="tears"),
    S("S17f", "S17", "sil", "ms", "hall_reveal", "SIDE", ["ODAGIRI"], "HALL_REV",
      "Medium from behind: Mr. Odagiri standing with his cane, his back to the camera, facing the stage; his face not visible.", line="line055",
      motion="Mr. Odagiri shifts his weight onto the cane; he stays standing with his back to the camera."),
    S("S17g", "S17", "react", "cu", "hall_press", "HA", ["REIKA"], "HALL_LECTERN", "High angle close-up of Reika on the floor looking up pleadingly toward the front row.", expr="tears"),
    S("S17h", "S17", "sil", "ms", "hall", "EL", ["MAMAA", "MAMAB", "MAMAC"], "HALL_ROWS", "The three mothers in the front row all turning their faces away at once, eyes down.",
      motion="The three women look away and down at the same time; nobody stands."),
    S("S17i", "S17", "sil", "ews", "hall_reveal", "HA", ["REIKA", "CROWD"], "HALL_WIDE",
      "High wide: the packed hall, residents standing, Reika a tiny figure sitting on the floor by the lectern.", line="line056",
      motion="Residents stand still; Reika stays small on the floor."),
    S("S17i2", "S17", "react", "cu", "hall", "EL", ["YUMI", "CROWD"], "HALL_WIDE", "Close-up of Yumi standing among the residents, watching quietly, no gloating, a calm sadness.", expr="firm"),
    S("S17-2a", "S17-2", "ins", "ecu", "hall", "EL", [], "P_BOOK", "Insert, no people: the plain dark-green passbook lying alone on the empty lectern, afternoon light."),
    S("S17-2b", "S17-2", "empty", "ews", "dusk", "LA", [], "EXT_DUSK", "No people. Low angle: the tower against a golden dusk sky.", line="line057",
      motion="The sky glows and clouds drift slowly. No people."),
    S("S17-2c", "S17-2", "estill", "ws", "dusk", "EL", [], "HALL_WIDE", "No people. The empty assembly hall at sunset, rows of empty chairs in warm light."),
    # S18 한 달 뒤
    S("S18a", "S18", "gfx", "ecu", "kids", "EL", [], "KIDS_DOOR", "Insert, no people: the plaque beside the kids-room door (「どなたでもご利用ください」 composited).", line="line058"),
    S("S18b", "S18", "sil", "ws", "kids", "EL", ["RIKO", "KIDS"], "KIDS_IN",
      "Wide inside the kids room: Riko playing on the colourful mats with other children, seen from the side, faces soft.", line="line059",
      motion="The children play gently; Riko waves both hands happily. No one runs toward the camera."),
    S("S18c", "S18", "face", "ms", "kids", "LA", ["RIKO"], "KIDS_IN", "Low angle medium of Riko laughing happily on the play mats, warm light.",
      motion="Riko laughs and bounces slightly in place.", expr="happy"),
    # S19 화물 엘리베이터 회수
    S("S19a", "S19", "sil", "ws", "lobby", "EL", ["REIKA", "YUMI"], "LOBBY",
      "Wide lobby: Reika in a plain coat (same hair) holding a tall stack of grey moving boxes in front of the passenger elevators; Yumi standing nearby, both seen from the side.",
      motion="Reika shifts the heavy boxes in her arms; Yumi stays still."),
    S("S19b", "S19", "ins", "ecu", "lobby", "EL", ["YUMI"], "EV_FREIGHT", "Insert: a woman's hand with a silver wristwatch politely gesturing, palm up, toward the open grey freight elevator."),
    S("S19c", "S19", "d", "cu", "lobby", "EL", ["YUMI"], "LOBBY",
      "Chest-up close-up of Yumi in the lobby, a graceful polite smile with steel underneath, looking just off-lens.", line="line060", expr="smile"),
    S("S19d", "S19", "react", "cu", "lobby_cold", "HA", ["REIKA"], "LOBBY", "High angle close-up of Reika clutching the boxes, jaw clenched in humiliation."),
    S("S19e", "S19", "sil", "ms", "lobby", "SIDE", ["REIKA"], "EV_FREIGHT", "From behind: Reika stepping into the padded grey freight elevator with her stack of boxes.",
      motion="Reika takes one step into the freight elevator, back to the camera."),
    S("S19f", "S19", "ins", "ecu", "lobby", "EL", [], "EV_FREIGHT", "Insert, no people visible: the grey freight elevator doors closing (match of S01d)."),
    S("S19g", "S19", "sil", "ws", "lobby", "HA", ["YUMI", "RIKO"], "LOBBY",
      "High angle wide: Yumi and Riko walking hand in hand away from the camera across the bright marble lobby toward the passenger elevators.", line="line061", fx="pull",
      motion="Yumi and Riko walk slowly away from the camera hand in hand."),
    S("S19h", "S19", "card", "ews", "lobby", "EL", [], None, "Black ending card 「見ていないところで、人は決まる。」."),
]

CARDS = {"S01i": "タワマンのボスママ", "S18a": "一か月後", "S19h": "見ていないところで、人は決まる。"}
GFX = {
    "S02b": "층별 피라미드(上層階/中層階/低層階) — 타워 실루엣(S02a 키프레임) 위 반투명 띠",
    "S03a": "안내판 「40階以上の居住者専用」",
    "S04b": "통지서 「修繕積立金 来月より1.8倍に値上げ予定 / 臨時総会にて承認」",
    "S10a": "장부 「外壁調査費 / 緊急補修費」 + 빨간 동그라미",
    "S10c": "노트북 「法人登記 / 代表者 西園寺 剛 / 所在地 レンタルオフィス / 従業員 0名」",
    "S11a": "휴대폰 가상 SNS 피드(로고·실명 서비스명 없음)",
    "S12a": "주민 명부 「42階 所有者 小田切」(이름 칸은 흐리게)",
    "S13e": "스크린 점등 + 통장 내역 표(시험 장면 make_insert.py 방식)",
    "S14a": "스크린 쌍 ① 2025/11/10 2,000,000円 ⇄ 11/11 「主人からのサプライズ♡ 新作のハイブランドバッグ」 + ドン",
    "S14c": "스크린 쌍 ② 2026/01/20 2,500,000円 ⇄ 01/21 「冬休みはハワイのスイートで家族時間」 + ドン",
    "S14e": "스크린 쌍 ③ 2026/04/15 3,000,000円 ⇄ 04/16 「主人が買ってくれた新作♥」 + ざわ…ざわ… + 3분할(S14f/g/h)",
    "S16h": "관리규약 「区分所有者」 ⇔ 「賃借人」 좌우 대비",
    "S17c": "봉투 「家賃督促状」 시간차 등장",
    "S18a": "안내판 「どなたでもご利用ください」",
}
EMPH = [  # 화면 전용 강조 자막(silent_styles) — (기준 줄, 줄 시작 후 초, 길이, 스타일, 문구)
    ("line030", 3.6, 2.4, "Emph", "二千四百万円"),
    ("line051", 0.3, 4.5, "LR", "区分所有者　　⇔　　賃借人"),
    ("line052", 0.6, 2.8, "Stamp", "家賃滞納"),
]
# 화면 속 일본어 표기(사용자 지시 2026-10-07 「명찰·명판은 장면에 맞게」): 키프레임은 무지 자리만 → 로컬 실글꼴·원근 합성(ja_text_overlay.py)
TOWER = "グランタワー東京ベイ"
SIGN_BY_LOC = {
    "EXT_ENT": ("Beside the glass entrance a long blank polished-stone name plaque is mounted on the wall.", f"입구 석재 명판 「{TOWER}」"),
    "LOBBY": ("On the stone wall behind the reception counter a blank brushed-brass name plaque.", f"리셉션 뒤 금속 명판 「{TOWER}」"),
    "EV_FREIGHT": ("On the wall right beside the freight elevator a small blank brushed-steel sign plate at eye level.", "화물 엘리베이터 옆 표지판 「荷物用エレベーター」"),
    "OFFICE": ("On the service counter a small blank white desk sign plate faces the visitor.", "카운터 명판 「管理事務室」"),
    "HALL_SCREEN": ("A long blank white banner hangs above the projector screen.", "현수막 장면별(S05 「グランタワー東京ベイ管理組合 臨時総会」 / S13~ 「グランタワー東京ベイ管理組合 通常総会」)"),
    "HALL_LECTERN": ("A small blank white nameplate is fixed to the front of the lectern.", "단상 명패 「理事長」"),
    "HALL_WIDE": ("A long blank white banner hangs above the projector screen at the front of the hall.", "현수막"),
}
SIGN_SIZES = ("ms", "ws", "ews")  # 클로즈업에는 명판 자리를 만들지 않는다(배경 보케 속 가짜 판 방지) — 화물 EV 표지판만 예외
BANNER_BY_SCENE = {"S05": "グランタワー東京ベイ管理組合　臨時総会", "S06": "グランタワー東京ベイ管理組合　臨時総会"}
BANNER_DEFAULT = "グランタワー東京ベイ管理組合　通常総会"
NAMEPLATE = {"TANTO": ("A small plain white name badge is clipped on the left chest of his suit jacket.", "명찰 「グランタワー管理　木村」")}
MAILBOX = {"S04a": "우편함 이름표 「505　高橋」"}
# 장면 전환(규격 제6장 5: 시간·장소 전환 디졸브 0.5~1.0초). 값은 이전 장면 끝에서 겹치는 길이 — 겹친 만큼 앞 컷을 늘려 Lock 타임라인을 유지한다.
DISSOLVE_INTO = {"S01i": 0.8, "S02a": 0.8, "S03-2a": 0.8, "S04a": 0.6, "S08a": 0.0, "S09a": 0.6, "S10a": 0.6, "S12-2a": 0.6,
                 "S12-3a": 0.8, "S17-2a": 0.8, "S18a": 1.0, "S19a": 0.6, "S19h": 1.0}
AMBIENCE = {"S02a": "high wind around a tall building, distant city hum", "S04d": "soft wind, distant city traffic",
            "S17-2b": "evening city ambience, distant crows", "S19f": "heavy freight elevator doors sliding shut with a thud"}
STYLE = {"NA": "Naration", "由美": "Yumi", "麗華": "Reika", "莉子": "Riko", "小田切": "Odagiri", "担当者": "Tanto", "ママA": "MamaA", "住民": "Jumin"}
STYLE_JA = {"Naration": "由美(語り)", "Yumi": "由美", "Reika": "麗華", "Riko": "莉子", "Odagiri": "小田切", "Tanto": "担当者", "MamaA": "ママ友", "Jumin": "住民"}
# 내레이션 흰색(외부 제안), 악역 붉은 기, 그 밖은 옅은 색 — ASS는 &HBBGGRR
STYLE_COLOR = {"Naration": "&H00FFFFFF", "Yumi": "&H00F0E6C8", "Reika": "&H00B4B4FF", "Riko": "&H00B4F0FF", "Odagiri": "&H00DCDCDC",
               "Tanto": "&H00E6F0DC", "MamaA": "&H00DCC8FF", "Jumin": "&H00C8DCE6"}
PRO_MODEL = "fal-ai/bytedance/seedance/v1/pro/image-to-video"
RATE = {"pro": 0.108, "lite": 0.036, "omni": 0.16, "kf": 0.04}


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
        if len(out[1]) > limit + 7:  # 긴 줄(오다기리 14초)은 세 줄 허용
            sub = out[1]; m2 = len(sub) // 2
            c2 = [i + 1 for i, ch in enumerate(sub[:-1]) if ch in "、。…!?？！" and sub[i + 1] not in NOHEAD]
            k = min(c2, key=lambda i: abs(i - m2)) if c2 else m2
            out = [out[0], sub[:k], sub[k:]]
    return "\\N".join(out)


def check_rules(shots):
    errs = []
    order = ["ecu", "ch", "cu", "ms", "ws", "ews"]
    prev = None
    for s in shots:
        if not s["lens"] or not s["angle"]:
            errs.append(f"{s['id']}: 사이즈·앵글 비어 있음")
        if s["kind"] == "d" and s["angle"] in ("SIDE", "BE", "OH"):
            errs.append(f"{s['id']}: OMNI 대사 컷 각도 {s['angle']} 금지(정면~45°만)")
        if s["kind"] == "d" and len([w for w in s["who"] if w != "CROWD"]) != 1:
            errs.append(f"{s['id']}: OMNI 컷은 1인 단독")
        if "REIKA" in s["who"] and s["lens"] in ("ch", "ecu") and s["kind"] in ("react", "d", "face"):
            errs.append(f"{s['id']}: 악역 근접 CU 금지(가슴 위까지)")
        if s["lens"] == "ch" and s["who"] and s["who"][0] != "YUMI":
            errs.append(f"{s['id']}: 초커는 주인공 감정 정점에만")
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
    if any("dutch" in s["fx"] and "YUMI" in s["who"] for s in shots):
        errs.append("더치는 주인공 장면 금지")
    return errs


def speech_span(path):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    return idx[0] / 16000, idx[-1] / 16000


def copy_voice(src_dir, dst, n):
    """확정 음성을 발화 구간만 잘라(앞 0.05·뒤 0.12초) 복사. 3분할 줄은 0.35초 숨으로 이어 붙인다."""
    out = os.path.join(dst, f"line{n:03d}.mp3")
    if n in SPLIT:
        parts = [os.path.join(src_dir, f"line{n:03d}{s}.mp3") for s, *_ in SPLIT[n]]
        inputs, filt = [], []
        for k, p in enumerate(parts):
            a, b = speech_span(p)
            inputs += ["-i", p]
            filt.append(f"[{k}:a]atrim={max(0, a - TRIM_PRE):.3f}:{b + TRIM_POST:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=44100:channel_layouts=mono[p{k}]")
        gaps = "".join(f"[p{k}]" + (f"[g{k}]" if k < len(parts) - 1 else "") for k in range(len(parts)))
        for k in range(len(parts) - 1):
            filt.append(f"anullsrc=r=44100:cl=mono,atrim=0:0.35[g{k}]")
        filt.append(f"{gaps}concat=n={2 * len(parts) - 1}:v=0:a=1[o]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[o]", "-b:a", "192k", out], check=True)
    else:
        p = os.path.join(src_dir, f"line{n:03d}.mp3")
        a, b = speech_span(p)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-af", f"atrim={max(0, a - TRIM_PRE):.3f}:{b + TRIM_POST:.3f},asetpts=PTS-STARTPTS",
                        "-b:a", "192k", out], check=True)
    return out


def main():
    lock = json.load(open(os.path.join(PROD, "lock.json"), encoding="utf-8"))
    main_end = lock["main_end"]
    rows = {r["id"]: r for r in lock["lines"] if r["spk"] != "진행자"}
    script = [x for x in load_lines() if x["spk"] != "진행자"]
    assert len(script) == len(rows) == 61, (len(script), len(rows))
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
    for ad in ad_times:  # 광고 지점 = 컷 경계
        assert any(abs(starts[sid] - ad) < 1e-3 for sid in order_ids), f"광고 지점 {ad:.2f}에 컷 경계 없음"
    bad = [(sid, ends[sid] - starts[sid]) for sid in order_ids if ends[sid] - starts[sid] < MIN_SHOT]
    if bad:
        raise SystemExit("너무 짧은 컷: " + ", ".join(f"{a}={b:.2f}s" for a, b in bad))
    STILL_KINDS, I2V_KINDS = ("react", "ins", "estill", "gfx"), ("face", "sil", "empty")
    long_ = [(s["id"], ends[s["id"]] - starts[s["id"]]) for s in SHOTS
             if (s["kind"] in STILL_KINDS and ends[s["id"]] - starts[s["id"]] > STILL_MAX)
             or (s["kind"] in I2V_KINDS and ends[s["id"]] - starts[s["id"]] > I2V_MAX)]
    if long_:
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
        named = [w for w in s["who"] if w not in ("CROWD", "KIDS")]
        comp = ("Exactly one person in sharp focus, no foreground shoulder, hands out of frame, chest-up single close-up, facing the camera within 30 degrees."
                if s["kind"] == "d" else
                ("Completely unpopulated: no people, no hands." if s["kind"] in ("empty", "estill") or (s["kind"] in ("ins", "gfx") and not s["who"]) else
                 f"Only the people described ({len(named)} named{', plus soft unrecognizable background people' if len(named) != len(s['who']) else ''}), no extra sharp faces."))
        keyframe = None if s["kind"].startswith("reuse") or s["kind"] == "card" else f"assets/portraits/tower-keyframes/{sid}-1.png"
        kf_prompt = None
        sign_txt, signage = [], []
        if s["loc"] in SIGN_BY_LOC and (s["lens"] in SIGN_SIZES or s["loc"] == "EV_FREIGHT"):
            sign_txt.append(SIGN_BY_LOC[s["loc"]][0])
            sg = SIGN_BY_LOC[s["loc"]][1]
            if s["loc"] in ("HALL_SCREEN", "HALL_WIDE"):
                sg = f"현수막 「{BANNER_BY_SCENE.get(s['scene'], BANNER_DEFAULT)}」"
            signage.append(sg)
        for key in s["who"]:
            if key in NAMEPLATE and s["kind"] in ("d", "face", "react", "sil"):
                sign_txt.append(NAMEPLATE[key][0]); signage.append(NAMEPLATE[key][1])
        if sid in MAILBOX:
            sign_txt.append("Each mailbox door has a small blank white name card slot."); signage.append(MAILBOX[sid])
        if keyframe:
            kf_prompt = " ".join([
                PRESET + ".", s["subject"], ("Characters: " + " | ".join(ids) + ".") if ids else "",
                f"Camera: {ANGLE[s['angle']]}, {LENS[s['lens']]}.", f"Lighting: {LIGHT[s['light']]}.", comp, " ".join(sign_txt), PLAIN,
                f"Negative: {NEGATIVE}."]).strip()
            cost["kf"] += 1
        tier = {"d": "omni", "react": "still", "ins": "still", "estill": "still", "gfx": "gfx", "face": "pro", "sil": "lite",
                "empty": "lite", "card": "card"}.get(s["kind"], "reuse")
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
                   "timecode": f"{tc(starts[sid])} - {tc(ends[sid])}", "start": round(starts[sid], 3), "assembled_s": round(d, 3), "generate_s": gen,
                   "size": s["lens"], "lens": LENS[s["lens"]], "angle": s["angle"], "light": s["light"], "lighting": LIGHT[s["light"]], "edit_fx": s["fx"],
                   "refs": refs, "subject": s["subject"], "line": s["line"], "motion": item["prompt"] if tier in ("pro", "lite") else "",
                   "keyframe": keyframe, "keyframe_prompt": kf_prompt, "gfx": GFX.get(sid, ""), "caption": CARDS.get(sid, ""),
                   "signage": signage, "dissolve_in": DISSOLVE_INTO.get(sid, 0.0)})
    budget = round((cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"]) * 1.25, 2)
    transitions = [0.0] * len(SHOTS)
    for k, s_ in enumerate(SHOTS):
        o = DISSOLVE_INTO.get(s_["id"], 0.0)
        if o and k > 0:
            transitions[k - 1] = o
            durations[k - 1] = round(durations[k - 1] + o, 4)  # 앞 컷이 겹침만큼 길어져 다음 컷 시작 시각은 Lock 그대로
    for ad in ad_times:  # 광고 경계는 하드컷(디졸브 금지 — 광고 삽입 지점이 흐려짐)
        k = next(i for i, sid in enumerate(order_ids) if abs(starts[sid] - ad) < 1e-3)
        assert transitions[k - 1] == 0.0, f"광고 경계 {order_ids[k]}에 디졸브 금지"

    # 음성 복사(override): 발화 구간만, 3분할은 이어 붙임
    src = os.path.join(ROOT, "assets", "auditions", "tower-tts")
    dst = os.path.join(ROOT, "assets", "audio-overrides", SKIT)
    os.makedirs(dst, exist_ok=True)
    for n in range(1, 62):
        copy_voice(src, dst, n)

    # 자막: 줄 순서 = lineNNN(TTS 캐시 번호) 순서, 시작 = 실제 발화 시작 - 0.05초(잘라 낸 파일 앞 여백)
    events = []
    for i, x in enumerate(script, 1):
        r = rows[f"line{i:03d}"]
        key = "NA" if x["spk"].startswith("NA") else x["spk"]
        st = STYLE[key]
        events.append((r["start"] - TRIM_PRE, r["end"] + 0.25, st, STYLE_JA[st], wrap(x["text"])))
    for sid, cap in CARDS.items():
        c0 = starts[sid] + 0.3
        events.append((c0, min(ends[sid] - 0.2, c0 + 3.5), "Caption", "", cap))
    for lid, off, ln, style, txt in EMPH:
        t0 = rows[lid]["start"] + off
        events.append((t0, t0 + ln, style, "", txt))
    zawa = starts["S14e"]
    events.append((zawa + 0.3, ends["S14h"] - 0.1, "Zawa", "", "ざわ…　ざわ…"))
    events.sort(key=lambda e: e[0])
    fmt = "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
    st_lines = "\n".join(
        f"Style: {n},Noto Sans CJK JP,{54 if n == 'Naration' else 58},{c},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{3 if n == 'Naration' else 5},1,2,200,200,70,1"
        for n, c in STYLE_COLOR.items())
    ass = ["[Script Info]", "Title: タワマンのボスママ 字幕", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]", fmt, st_lines,
           "Style: Caption,Noto Serif CJK JP,66,&H00FFF3C4,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,5,200,200,80,1",
           "Style: Emph,Noto Sans CJK JP,150,&H0000E6FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,10,3,5,100,100,80,1",
           "Style: Stamp,Noto Serif CJK JP,140,&H002020E0,&H000000FF,&H00FFFFFF,&H80000000,-1,0,0,0,100,100,0,-8,1,6,2,5,100,100,80,1",
           "Style: LR,Noto Sans CJK JP,96,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,2,8,100,100,160,1",
           "Style: Zawa,Noto Serif CJK JP,110,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,6,0,1,6,2,7,120,120,120,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:
        txt = e[4]
        if e[2] == "Stamp":  # 도장 쾅: 크게 → 원래 크기(0.15초) 애니메이션
            txt = "{\\fscx180\\fscy180\\t(0,150,\\fscx100\\fscy100)}" + txt
        if e[2] == "Emph":
            txt = "{\\fscx130\\fscy130\\t(0,120,\\fscx100\\fscy100)}" + txt
        ass.append(f"Dialogue: 0,{ass_t(max(0, e[0]))},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{txt}")
    open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")

    # BGM: 정적(S14e 직전 페이드아웃 → 심장 박동 → NA22 뒤 역전곡) — 곡 사이 숨 1.5초 이상, 겹침 없음
    t_cut = starts["S14e"] - 0.2
    t_rev = rows["line042"]["end"] + 0.6
    t_ad2 = ad_times[1]
    t_end_sec = starts["S17-2a"]
    BGM = [
        (0.0, starts["S02a"] - 1.6, 0.40, "tense low strings and sparse piano, Japanese drama cold open, cold and ominous, instrumental, no vocals"),
        (starts["S02a"], ad_times[0] - 0.2, 0.38, "nervous pizzicato strings and muted piano, quiet injustice and social pressure, Japanese drama score, instrumental, no vocals"),
        (ad_times[0] + 1.4, rows["line037"]["end"] + 1.0, 0.38, "steady minimal beat with soft synth and piano, focused investigation, clever detective mood, instrumental, no vocals"),
        (rows["line037"]["end"] + 2.6, t_cut, 0.40, "rising suspense, low drums and strings building toward a reveal, Japanese drama score, instrumental, no vocals"),
        (t_rev, t_ad2 - 0.2, 0.44, "fast triumphant reversal strings and taiko drums, satisfying comeback, Japanese drama score, instrumental, no vocals"),
        (t_ad2 + 1.4, t_end_sec - 0.5, 0.42, "grand dramatic strings and piano, the tables turn, justice served, instrumental, no vocals"),
        (t_end_sec + 1.2, round(main_end, 2), 0.40, "warm hopeful piano and light strings, gentle resolution, Japanese drama ending, instrumental, no vocals"),
    ]
    SFX = [{"at": round(starts[s] + 0.15, 2), "kind": k} for s, k in
           (("S14a", "don"), ("S14c", "don"), ("S14e", "heartbeat2"), ("S14e", "don"), ("S10a", "pen"), ("S16i", "stamp"), ("S01d", "elevator_close"))]
    SFX.append({"at": round(rows["line030"]["start"] + 3.6, 2), "kind": "don"})

    os.makedirs(os.path.join(ROOT, "scripts", "storyboard"), exist_ok=True)
    json.dump({"_설명": "tower PHASE 3 스토리보드 Lock(build_tower_phase3.py 생성 — 직접 수정 금지).", "skit": SKIT,
               "preset": PRESET, "negative": NEGATIVE, "plain_props": PLAIN, "total_s": round(main_end, 3), "ads": lock["ads"],
               "scenes": sb}, open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"_설명": "tower 장면 설정(build_tower_phase3.py 생성). override_required 장면(정지 푸시인·OMNI 정지 프레임·그래픽·재사용·카드)은 video-overrides로 먼저 넣는다.",
               "ratio": "16:9", "budget_usd": budget,
               "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, faces, "
                         "wardrobe, props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, no sudden movement, no new people entering"),
               "durations": [it["duration"] for it in scene_items], "scenes": scene_items},
              open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)
    idx = {sid: k + 1 for k, sid in enumerate(order_ids)}
    audio = {
        "_설명": "tower 조립·오디오(build_tower_phase3.py 생성). 음성 61줄 = assets/audio-overrides/tower/ (Typecast 확정본, 발화 구간만, 배속 없음).",
        "default_voice": "cached-typecast",
        "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "style_names": STYLE_JA, "narration_styles": ["Naration"], "silent_styles": ["Caption", "Emph", "Stamp", "LR", "Zawa"],
        "output_size": [1920, 1080], "fit": "crop",
        "scene_durations": durations, "transitions": transitions,
        "omnihuman_scenes": [idx[s["id"]] for s in SHOTS if s["kind"] == "d"],
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"], "omnihuman_max_s": 8.0,
        "legacy_lipsync": False,
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35,
        "ambience_prompts": [AMBIENCE.get(sid, "") for sid in order_ids],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.40, "bgm_prompt": BGM[1][3],
        "bgm_segments": [{"start": round(s, 2), "end": round(e, 2), "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_효과음": SFX,
        "_아웃트로": "진행자 4줄(line062~065)은 본편에 넣지 않는다 — PHASE 6 append_outro + outro_cta_overlay(美談ものがたり 공통).",
    }
    json.dump(audio, open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w"), ensure_ascii=False, indent=1)

    ang = collections.Counter(s["angle"] for s in SHOTS if not s["kind"].startswith("reuse") and s["kind"] != "card")
    tiers = collections.Counter(x["tier"] for x in sb)
    total_cost = cost["kf"] * RATE["kf"] + cost["pro"] * RATE["pro"] + cost["lite"] * RATE["lite"] + cost["omni"] * RATE["omni"]
    md = ["# 『タワマンのボスママ』 PHASE 3 샷 리스트", "",
          f"> `scripts/build_tower_phase3.py` 자동 생성(손 수정 금지). 타임코드 분:초.프레임(24fps). 본편 {tc(main_end)}, 컷 {len(SHOTS)}개, 광고 " +
          ", ".join(f"{a['name']} {tc(a['at'])}" for a in lock["ads"]) + ".", "",
          "## 비용 추산 (실측 단가)", "", "| 항목 | 수량 | 단가 | 금액 |", "|---|---|---|---|",
          f"| 키프레임 | {cost['kf']}장 | 0.04 | {cost['kf'] * RATE['kf']:.2f} |",
          f"| i2v pro 1080p (얼굴) | {cost['pro']}초 | 0.108 | {cost['pro'] * RATE['pro']:.2f} |",
          f"| i2v lite 720p (실루엣·무인) | {cost['lite']}초 | 0.036 | {cost['lite'] * RATE['lite']:.2f} |",
          f"| OmniHuman (컷 길이 + 0.8초) | {cost['omni']:.1f}초 | 0.16 | {cost['omni'] * RATE['omni']:.2f} |",
          f"| **1차 합계** (재생성 여유 제외) | | | **{total_cost:.2f}** |",
          f"| i2v 예산 상한 `budget_usd` (여유 25%) | | | {budget:.2f} |", "",
          "## 생성 방식 분포", "", "| 방식 | 컷 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in tiers.most_common()] + [
          "", "## 앵글 분포 (생성 컷)", "", "| 앵글 | 컷 | 비율 |", "|---|---|---|"] + [
          f"| {k} | {v} | {v / sum(ang.values()) * 100:.0f}% |" for k, v in ang.most_common()] + [
          "", "## 로컬 그래픽·글자 합성 (키프레임은 무지)", ""] + [f"- {k}: {v}" for k, v in GFX.items()] + [
          "", "## 화면 속 일본어 표기 (명판·명찰 — 무지 생성 후 로컬 합성)", ""] + [
          f"- {x['id']}: " + " / ".join(x["signage"]) for x in sb if x["signage"]] + [
          "", "## 장면 전환 (디졸브)", ""] + [f"- {x['id']} 앞 {x['dissolve_in']}초" for x in sb if x["dissolve_in"]] + [
          "", "## 샷 표", "", "| 컷 | 타임코드 | 길이 | 방식 | 사이즈 | 앵글 | 조명 | 편집 효과 | 대사 | 내용 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in sb:
        md.append(f"| {x['id']} | {x['timecode']} | {x['assembled_s']:.2f}s | {x['tier']} | {x['size']} | {x['angle']} | {x['light']} | {x['edit_fx']} | {x['line'] or ''} | {x['subject'][:60]} |")
    open(os.path.join(PROD, "07_샷리스트.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    if lag_report:
        print("J컷(대사가 앞 컷 위에서 먼저 시작):", ", ".join(f"{a}+{b}s" for a, b in lag_report))
    top = ang.most_common(1)[0]
    print(f"완료: 컷 {len(SHOTS)}개, 본편 {tc(main_end)}, 방식 {dict(tiers)}, 1차 비용 약 {total_cost:.2f}달러 (i2v budget {budget}), 최다 앵글 {top[0]} {top[1] / sum(ang.values()) * 100:.0f}%")


if __name__ == "__main__":
    main()
