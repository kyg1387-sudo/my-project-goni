#!/usr/bin/env python3
"""EP4 「김씨의 크리스마스」 PHASE 3 스토리보드 Lock 생성기 (일본어 기준판).

입력(동결본): docs/EP4-PHASE1-대본동결-오디오앵커.md 의 Lock 타임라인(05:01.20)과
assets/audio-overrides/kim-christmas/lineNNN.mp3(실측 길이).
출력(손으로 옮겨 적지 않는다 — 고칠 때는 이 파일을 고치고 다시 돌린다):
  scripts/storyboard/kim-christmas.json   샷 스펙(PHASE 4 키프레임·PHASE 5 i2v 입력)
  scripts/scenes/kim-christmas.json       장면 생성 설정(i2v 프롬프트·키프레임 경로·생성 길이)
  scripts/audio/kim-christmas.json        조립·오디오 설정(장면 길이·디졸브·omnihuman·현장음·BGM 4구간)
  subs/kim-christmas.ass                  일본어 자막(대사 34줄 + 화면 전용 자막카드 8장)
  docs/EP4-PHASE3-샷리스트.md             검토용 샷 리스트 표

규칙 반영: CLAUDE.md 제1~6장. 대사 7장면 = 가슴 위 단독 CU 정지 키프레임 → OmniHuman.
리액션 = 정지 푸시인(립싱크 제외). 일본어 글자 합성 장면(S03·S07·S18·S22·S37·S38·S42·S43)은 카메라 고정.
S07·S42의 중복 자막카드는 사용자 승인(2026-10-04)으로 제거 — 화면 속 일본어 합성 글자만 남긴다.
사용법: python3 scripts/build_ep4_phase3.py
"""
import glob
import json
import os
import re

from mutagen.mp3 import MP3

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SKIT = "kim-christmas"
FPS = 24
HARD = 1 / FPS  # 파이프라인은 하드컷 경계도 1프레임 겹친다 → 하드컷 장면 길이에 1프레임을 더해 Lock 시각 유지

# ---------- 대사 34줄 (일본어 자막 = 대본 v3 일본어 문안, 음성은 가나 보정본) ----------
LINES = {
    1: ("Naration", "十二月二十四日。団地には、一日じゅう雪が降っていました。"),
    2: ("Naration", "年の瀬の郵便受けには、どこも請求書が一枚ずつ。"),
    3: ("Naration", "そして1801号室のドアには、赤い紙が一枚、貼られていました。"),
    4: ("Ren", "おじさん、サンタさんは…うちの部屋番号、知らないのかな？"),
    5: ("Mom", "レン、警備のおじさんを困らせないの。…うちのことは、構わないでください。"),
    6: ("Naration", "冷たい人だったわけではありません。"),
    7: ("Naration", "借金と暮らしに疲れ果てた母親に残っていたのは、小さな意地だけだったのです。"),
    8: ("Naration", "女手ひとつで子どもを育てて、三年。"),
    9: ("Naration", "昼は食堂、夜はスーパーで働いても、冬はいつも、お金が先に底をつきました。"),
    10: ("Naration", "母親が眠ったあと、男の子がこっそり下りてきました。"),
    11: ("Naration", "たどたどしい字で、男の子はこう書いていました。『うちは、十八階です。いい子にしていました』"),
    12: ("Ren", "サンタさん、お母さんが泣かないように、電気だけは消さないでください。"),
    13: ("Naration", "その日は、キムさんのひと月分のお給料日でした。"),
    14: ("Naration", "封筒の横には、七年前に先立った妻の、家計簿がありました。"),
    15: ("Naration", "手垢のついた最後のページの隅に、妻の字。"),
    16: ("Naration", "「わたしたちにも子どもがいたら…あなたに一度、サンタさんをやってほしかったな」"),
    17: ("Naration", "子どものいなかったふたりの、とうとう叶わなかった願いでした。"),
    18: ("Kim", "1801号室の…管理費、三か月分です。"),
    19: ("Kim", "わたしが払ったことは…決して、言わないでください。"),
    20: ("Kim", "あそこのお母さんが…傷つきますから。"),
    21: ("Naration", "封筒を差し出して残った、わずかなお札で、彼は小さなツリーをひとつ買いました。"),
    22: ("Naration", "引き出しの奥に、妻が生前、毛糸で編んでおいた星がひとつ。"),
    23: ("Naration", "七年ぶりに、その星がツリーのてっぺんに飾られました。"),
    24: ("Naration", "エレベーターの音で子どもが起きないように、彼は十八階まで、階段を上りました。"),
    25: ("Naration", "チャイムは、鳴らしませんでした。"),
    26: ("Naration", "足音を忍ばせて、来た階段を、そのまま下りていきました。"),
    27: ("Naration", "廊下の天井のカメラだけが、その背中を見ていました。"),
    28: ("Naration", "男の子の願いどおり、その家の明かりは、消えませんでした。"),
    29: ("Naration", "誰が払ったのか、佐藤主任は最後まで言いませんでした。"),
    30: ("Naration", "ただ黙って、明け方の廊下の映像を、見せてくれただけでした。"),
    31: ("Naration", "画面の中の年老いた警備員は、最後まで顔を見せませんでした。"),
    32: ("Naration", "けれど、あの少し丸い背中と古いダウンを、この団地で知らない人はいませんでした。"),
    33: ("Mom", "ごめんなさい…昨日、あんなことまで言ったのに…本当に、ありがとうございます…"),
    34: ("Kim", "……メリークリスマス。"),
}
STYLE_NAMES = {"Kim": "キム", "Ren": "レン", "Mom": "母", "Naration": "ナレーター"}

# ---------- 공통 프리셋 (PHASE 2 잠금) ----------
PRESET = ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, "
          "muted winter palette of a Japanese public housing complex (danchi), no flat lighting")
NEGATIVE = ("gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, "
            "text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, "
            "deformed eyes, extra fingers, cap, hat, badge, nametag, posters with writing, printed labels, brand logos")
PLAIN = ("All papers, signs, plates and labels are completely blank and unprinted; no letters, numbers or symbols "
         "anywhere in the frame.")

LENS = {
    "cu": "85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait",
    "insert": "85mm prime lens, f/2.0, shallow depth of field, creamy background bokeh, macro-like detail",
    "ecu": "100mm macro lens, f/2.8, very shallow depth of field, creamy bokeh",
    "medium": "50mm lens, f/2.8, natural perspective, cinematic composition, rule of thirds",
    "long": "35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, perfectly balanced composition",
    "xlong": "24mm wide angle, deep focus, sharp architectural lines, imposing perspective",
}
LIGHT = {
    "snow_day": "Overcast snowy afternoon, soft diffuse 5600K daylight from upper-left, cool crisp tones, gentle falling snow, subtle warm rim light",
    "snow_dusk": "Snowy dusk blue hour 6500K ambient, warm 3200K sodium streetlights as rim light, falling snow catching the light",
    "snow_night": "Snowy night, deep blue 6500K ambient, warm 3200K window glow from the guard booth, falling snow backlit",
    "booth_day": "Daylight 5600K through the booth window from camera-left, warm 3200K desk lamp practical, Chiaroscuro contrast, subtle warm rim light",
    "booth_night": "Night interior, single warm 3200K desk-lamp key from camera-left, orange glow of a kerosene heater, Chiaroscuro lighting, dramatic high-contrast shadows, warm rim light separating subject from dark background",
    "apt_night": "Night interior, one warm 3200K floor-lamp key from camera-left, Chiaroscuro lighting, deep cinematic shadows, cold blue moonlight from the window as rim",
    "dawn_corr": "Pre-dawn 4 a.m., dim cool 5600K moonlight through the corridor window, one warm 3200K motion-sensor ceiling light, deep shadows, cinematic volumetric side light",
    "dawn_dark": "Pre-dawn darkness, motion-sensor light switched off, faint cool 5600K moonlight only, deep shadows, low-key",
    "corr_day": "Overcast winter afternoon, soft cool 5600K daylight from the open side of the exterior corridor, gentle shadows, subtle warm rim light",
    "office": "Cool crisp 5600K fluorescent office light, soft window light from camera-left, clean balanced tones, subtle warm rim light",
    "morning": "Clear winter morning after snowfall, low-angle soft 5600K sunlight from camera-left, crisp clean tones, sparkling snow",
    "cctv": "Black-and-white CCTV security camera footage look, high-angle ceiling view, slight lens distortion, low-light video noise",
}
CAM = {
    "static": "Static, locked off",
    "push": "Extremely subtle slow push-in (zoom factor 1.05)",
    "push_fwd": "Very slow push forward following the subject (zoom factor 1.08), no shake",
    "pull": "Very slow pull-back (local zoom-out 1.08 to 1.00)",
}
# 장면 종류별 모션(규격 제2장 3 승인 목록만)
MOTION_D = ("Speaking: natural lip movement, single slow eye blink, micro chest breathing, maximum 5-degree head tilt, "
            "no head turn, no hand gestures. Lips close and stay still after the line ends.")
MOTION_R = "Still keyframe, slow push-in only (local, no i2v). No lip movement."

# ---------- 장면 표 (Lock 순서 53컷) ----------
# id, kind, lens, light, cam, refs, subject, environment, expression/action
S = [
    ("S01", "reuse", "insert", "cctv", "static", [], "Reuse of S44 (CCTV monitor footage) — same clip, trimmed.", "", ""),
    ("S02", "react", "cu", "office", "push", [], "Reuse of S45 keyframe (mother's tearful face lit by the monitor).", "", ""),
    ("S03", "card", "long", "dawn_dark", "static", ["LOC@corridor-18f-night"],
     "No people. The dark 18th-floor interior corridor of an old Japanese apartment block at 4 a.m., the motion-sensor ceiling light off, faint moonlight from the window at the far end, the steel door of unit 1801 at frame right with a small blank metal number plate beside it (plate faces camera, blank).",
     "Long narrow interior corridor, beige textured walls, identical steel doors on both sides, window at the far end with snow outside, dome camera on the ceiling", "Stillness"),
    ("S04", "card", "xlong", "snow_night", "static", ["LOC@apt-gate-winter-night"],
     "No people. Extreme long shot of a snow-covered Japanese public housing complex at night, many apartment windows glowing warm, snow falling.",
     "Several mid-rise concrete apartment blocks, snowy courtyard, bare trees, streetlights", "Peaceful, lonely"),
    ("S05", "n", "long", "snow_day", "static", ["LOC@apt-gate-winter-day", "LOC@guard-booth-winter-day"],
     "No people. The complex entrance gate and the small guard booth on a snowy afternoon, snow falling steadily.",
     "Gate pillars without any lettering, small booth with a lit window, snow piling on the roof", "Calm winter air"),
    ("S06", "n", "medium", "snow_day", "push", ["LOC@stairwell-day"],
     "No people. Ground-floor wall of steel mailboxes; from every slot sticks out one plain white unprinted envelope.",
     "Old grey steel mailbox wall in the stairwell entrance, concrete floor with melted snow, cool daylight from the door", "Quiet year-end"),
    ("S07", "n", "insert", "corr_day", "static", ["LOC@corridor-18f-day"],
     "No people. Insert of the steel front door of unit 1801: one plain red A4 sheet taped at eye level, perfectly flat and facing the camera squarely, completely blank.",
     "Grey steel door, blank door frame, shallow depth of field", "Ominous"),
    ("S08", "v", "medium", "booth_day", "static", ["REN@fullbody-front", "LOC@guard-booth-winter-day"],
     "Ren, a 7-year-old Japanese boy (reference: REN sheet), bowl haircut, round red cheeks, plain mustard knit sweater, stands on tiptoe outside the guard booth window, both small hands holding the window ledge, breathing white puffs, peering inside. Kim is only a blurred silhouette inside the booth.",
     "Exterior of the guard booth, frosted window, snow on the ledge", "Curious, innocent"),
    ("S09", "d", "cu", "booth_day", "static", ["REN@expr-curious", "LOC@guard-booth-winter-day"],
     "SINGLE PORTRAIT: Ren alone, chest-up close-up in front of the booth window, round red cheeks, eyes wide looking up slightly off-camera-left at the adult inside, white breath, lips parted mid-sentence; no hands in frame.",
     "Out-of-focus snowy courtyard behind him", "Innocent curiosity 50%"),
    ("S10", "react", "cu", "booth_day", "push", ["KIMW@expr-neutral", "LOC@guard-booth-winter-day"],
     "SINGLE PORTRAIT: Kim (reference: KIMW sheet) alone, chest-up, inside the booth, worn pilled navy padded jacket over a thin guard uniform, lips closed — he was about to answer and stopped; looking down-right at the child outside.",
     "Booth interior, window frame edge, soft winter light", "Held-back words, gentle sadness 50%"),
    ("S11", "d", "cu", "snow_day", "static", ["MOM@expr-neutral", "LOC@guard-booth-winter-day"],
     "SINGLE PORTRAIT: Ren's mother (reference: MOM sheet), early-to-mid 30s, long black hair tied low, tired face without makeup, plain beige long padded coat, chest-up, alone, eyes avoiding the camera (looking down-left), lips parted mid-sentence; no hands in frame.",
     "Out-of-focus booth window and snowy courtyard", "Tired curtness 50% (not anger)"),
    ("S12", "n", "insert", "snow_day", "static", ["MOM@fullbody-front", "REN@fullbody-front"],
     "Insert on hands only: the mother's hand, also holding a heavy plain grocery bag, takes the boy's small hand and gently pulls him away. Faces out of frame.",
     "Snowy pavement, blurred background", "Cut-away"),
    ("S13", "n", "medium", "booth_day", "static", ["KIMW@side", "LOC@guard-booth-winter-day"],
     "Kim inside the booth seen in profile, sitting still; through the window, the mother and the boy walk away into the snow carrying a heavy grocery bag (backs to camera, small in frame).",
     "Booth interior: plain desk, kettle, window; snowy courtyard outside", "Silent watching"),
    ("S14", "n", "medium", "apt_night", "static", ["MOM@side", "PROP@kettle", "LOC@apt-1801-night"],
     "Night, the small living room of unit 1801: the mother has fallen asleep slumped over a low table, still holding the blank red sheet; behind her, the boy sleeps under a futon (blurred).",
     "Cramped Japanese apartment, one floor lamp, low table, futon, old curtains; no framed pictures with text", "Exhaustion"),
    ("S14b", "v", "insert", "apt_night", "static", ["LOC@apt-1801-night"],
     "Insert: the sleeping mother's hand on the low table loosely holding the blank red A4 sheet, fingers relaxed.",
     "Warm lamp light, dark background", "Silent insert"),
    ("S15", "n", "long", "snow_night", "static", ["LOC@guard-booth-winter-night"],
     "No people. Night exterior of the guard booth in falling snow, warm yellow light in the window.",
     "Snowy courtyard, footpath, streetlight", "Hushed"),
    ("S16", "v", "long", "snow_night", "static", ["REN@fullbody-front", "LOC@guard-booth-winter-night"],
     "Full shot: Ren in a plain navy padded vest over grey pajama pants stands on tiptoe outside the booth and slides a folded sheet of paper through the gap under the service window.",
     "Booth exterior at night, snow, warm window light", "Secret, careful"),
    ("S17", "n", "medium", "booth_night", "static", ["KIMW@45", "LOC@guard-booth-winter-v1-key1"],
     "Kim at the booth desk slowly unfolds a small folded sheet of notebook paper with both hands (paper back faces camera).",
     "Plain desk, desk lamp, kerosene heater glow", "Tender attention"),
    ("S18", "vo", "ecu", "booth_night", "static", [],
     "No people. Extreme close-up, top-down: a sheet of children's notebook paper lying flat on the desk, facing the camera squarely, with faint ruled lines only and NO writing (handwriting is composited later).",
     "Desk surface, warm lamp light", "Stillness (child's voice off-screen)"),
    ("S19", "react", "cu", "booth_night", "push", ["KIMW@expr-moved", "LOC@guard-booth-winter-v1-key1"],
     "SINGLE PORTRAIT: Kim alone, chest-up, holding still after reading, eyes glistening, lips closed.",
     "Dark booth, warm lamp rim", "Frozen emotion 50%"),
    ("S20", "n", "medium", "booth_night", "static", ["KIMW@front", "LOC@guard-booth-winter-v1-key1"],
     "Kim takes a plain white unprinted pay envelope out of the inner pocket of his worn pilled navy padded jacket and lays it on the desk.",
     "Plain desk, lamp", "Meaningful"),
    ("S21", "n", "insert", "booth_night", "static", ["PROP@envelope-notebook"],
     "No people. Insert: on the desk, the plain white envelope next to his late wife's worn floral-cover household account notebook (cover label out of frame).",
     "Warm lamp light, shallow depth of field", "Longing"),
    ("S22", "n", "ecu", "booth_night", "static", ["PROP@envelope-notebook"],
     "No people. Extreme close-up: the last page of the worn notebook lying flat, facing camera squarely, fingerprint-worn paper corner, faint ruled lines only, NO writing (wife's handwriting is composited later).",
     "Warm lamp light", "Wistful"),
    ("S23", "react", "cu", "booth_night", "push", ["KIMW@expr-moved", "LOC@guard-booth-winter-v1-key1"],
     "SINGLE PORTRAIT: Kim alone, chest-up, wet eyes slowly turning into quiet resolve, lips closed.",
     "Dark booth, warm lamp rim", "Grief → resolve 50%"),
    ("S24", "v", "long", "snow_dusk", "static", ["KIMW@fullbody-side", "GMA@front", "CART@side", "LOC@apt-gate-winter-day"],
     "Long shot: on a snowy path in the complex at dusk, Kim walks toward the management office; the elderly paper-collecting grandmother (reference: GMA sheet, EP3) passes from the opposite direction pulling her handcart (Kim's work gloves on the grip). They exchange a slight bow as they pass. No speech.",
     "Snowy path, streetlights, apartment blocks", "Warm recognition"),
    ("S25", "v", "insert", "office", "static", ["LOC@mgmt-office-counter"],
     "Insert on hands: two weathered hands respectfully slide a plain white envelope across the granite counter of the management office window.",
     "Granite counter, sliding glass window, shallow depth of field", "Respectful"),
    ("S26", "d", "cu", "office", "static", ["KIMW@front", "LOC@mgmt-office-counter"],
     "SINGLE PORTRAIT: Kim alone, chest-up at the office counter window, calm, looking straight ahead slightly camera-right, lips parted mid-sentence; no hands.",
     "Out-of-focus office wall behind", "Calm composure"),
    ("S27", "react", "cu", "office", "push", ["CLERK@expr-surprised", "LOC@mgmt-office-counter"],
     "SINGLE PORTRAIT: Sato, the female clerk in her 40s (reference: CLERK sheet), short bob, black-rimmed glasses, plain navy cardigan over a white blouse, chest-up behind the glass, looking up in surprise, lips closed.",
     "Office interior bokeh", "Surprise 50%, silent"),
    ("S28", "d", "cu", "office", "static", ["KIMW@expr-neutral", "LOC@mgmt-office-counter"],
     "SINGLE PORTRAIT: Kim alone, chest-up, gaze lowered, head bowed slightly, lips parted mid-sentence; no hands.",
     "Out-of-focus office wall", "Earnest humility 50%"),
    ("S29", "react", "cu", "office", "push", ["CLERK@expr-neutral", "LOC@mgmt-office-counter"],
     "SINGLE PORTRAIT: the clerk alone, chest-up, solemn, a slow small nod held in the keyframe, lips closed.",
     "Office interior bokeh", "Solemn understanding"),
    ("S30", "d", "cu", "office", "static", ["S28 keyframe reuse"],
     "Reuse of the S28 keyframe (Kim, gaze lowered); new audio-driven performance only.", "", "Quiet loneliness 50%"),
    ("S31", "n", "insert", "booth_day", "static", ["KIMW@front"],
     "Insert on hands: weathered hands put a thin worn leather wallet back into the pocket of the pilled navy padded jacket.",
     "Close on jacket texture, worn cuffs", "Modest"),
    ("S32", "v", "medium", "booth_night", "static", ["KIMW@45", "PROP@tree", "LOC@guard-booth-winter-v1-key1"],
     "Night booth: next to a small tabletop Christmas tree on the desk, Kim takes an old wooden box from the back of the drawer and opens the lid.",
     "Desk, lamp, heater glow", "Reverent"),
    ("S33", "n", "ecu", "booth_night", "static", ["PROP@star"],
     "Extreme close-up: a small hand-knitted red-and-white yarn star resting on a rough, weathered palm.",
     "Warm lamp light, dark background", "Longing"),
    ("S34", "n", "insert", "booth_night", "static", ["PROP@star", "PROP@tree"],
     "Insert: weathered fingers place the knitted yarn star on the top of the small tabletop tree with one string of tiny warm lights.",
     "Warm bokeh", "Moved"),
    ("S35", "card", "long", "dawn_dark", "static", ["LOC@stairwell-night"],
     "No people. Dark concrete stairwell at 4 a.m., motion-sensor light off.",
     "Concrete stairs, steel handrail, small window with snow", "Stillness"),
    ("S36", "n", "long", "dawn_corr", "push_fwd", ["KIMW@fullbody-back", "PROP@tree", "LOC@stairwell-key1"],
     "Full shot from behind: Kim climbs the stairs slowly, hugging the small tree to his chest; the motion-sensor light on the floor above clicks on. Slow steady steps only.",
     "Concrete stairwell", "Hushed determination"),
    ("S37", "n", "long", "dawn_corr", "static", ["KIMW@fullbody-back", "PROP@tree", "LOC@corridor-18f-night"],
     "Static rear full shot in the 18th-floor interior corridor: Kim sets the small lit tree down in front of the steel door of unit 1801 (blank metal number plate beside the door), stands still for a moment, then turns away (head turn within 15 degrees) toward the stairs.",
     "Narrow interior corridor, window at the far end, dim", "Silent gift"),
    ("S38", "v", "insert", "dawn_dark", "static", ["PROP@tree", "LOC@corridor-18f-night"],
     "No people. Insert: the small tree on the floor at the door, knitted star on top, tiny lights glowing; the sensor light goes off and only the tree lights remain. Blank metal plate visible beside the door.",
     "Dark corridor", "Afterglow"),
    ("S39", "n", "insert", "dawn_dark", "static", ["LOC@corridor-18f-key2"],
     "No people. Insert: a dome security camera on the corridor ceiling with a tiny red light, no logo.",
     "Concrete ceiling", "Watching"),
    ("S40", "n", "xlong", "morning", "static", ["LOC@apt-gate-winter-key2"],
     "No people. Extreme long shot of an apartment block facade on a clear snowy Christmas morning; one window on the 18th floor glows brightly.",
     "Blue sky, snow on rooftops", "Warm relief"),
    ("S41", "v", "medium", "morning", "static", ["MOM@expr-neutral", "REN@expr-happy", "PROP@tree", "LOC@corridor-18f-day"],
     "The mother (plain grey cardigan) and Ren open the door of 1801 and discover the small tree at their feet: the boy beams with his mouth closed and points at it, the mother freezes.",
     "Corridor in morning light", "Wonder / disbelief"),
    ("S42", "card", "insert", "morning", "static", ["LOC@corridor-18f-day"],
     "No people. Insert of the same steel door: a new plain white A4 sheet taped at eye level, perfectly flat, facing camera squarely, completely blank (Japanese notice is composited later).",
     "Grey steel door, morning light", "Relief"),
    ("S43", "n", "medium", "office", "static", ["MOM@fullbody-back2", "CLERK@front", "LOC@mgmt-office-counter"],
     "At the management office window: over the mother's back (face not visible), the clerk quietly shakes her head and turns the monitor toward the mother. The blank brown wooden plate above the window faces camera.",
     "Office counter, sliding glass window", "Silent discretion"),
    ("S44", "n", "insert", "cctv", "static", ["KIMW@fullbody-back", "PROP@tree", "LOC@corridor-18f-night"],
     "Black-and-white CCTV footage on a monitor: the dawn 18th-floor corridor from a high ceiling angle; an old guard in a worn padded jacket sets down a small tree at a door and turns away, face never visible.",
     "Monitor screen fills the frame, no on-screen text or timestamp", "Revelation"),
    ("S45", "react", "cu", "office", "push", ["MOM@expr-tearful", "LOC@mgmt-office-counter"],
     "SINGLE PORTRAIT: the mother alone, chest-up, face lit by the cool glow of the monitor, tears welling, lips closed.",
     "Office bokeh", "Tears welling 50%"),
    ("S46", "v", "medium", "booth_day", "static", ["MOM@fullbody-front", "LOC@guard-booth-winter-day"],
     "From inside the booth looking at the door: the door opens and the out-of-breath mother stands in the falling snow.",
     "Booth door frame, snowy courtyard", "Urgency"),
    ("S47", "d", "cu", "booth_day", "static", ["MOM@expr-tearful", "LOC@guard-booth-winter-day"],
     "SINGLE PORTRAIT: the mother alone, chest-up, eyes brimming with tears, lips trembling, parted mid-sentence; no hands.",
     "Snowy doorway bokeh", "Choked tearful gratitude 50%"),
    ("S48", "v", "medium", "booth_day", "static", ["MOM@side", "LOC@guard-booth-winter-day"],
     "Side view: the mother bows deeply, face hidden by her hair. Cut-away.",
     "Booth doorway, snow", "Deep bow"),
    ("S49", "v", "insert", "booth_day", "static", ["PROP@kettle", "LOC@guard-booth-winter-v1-key2"],
     "Insert: Kim's weathered hand fiddles with the handle of an old aluminium kettle on the kerosene heater, steam rising.",
     "Heater glow", "Shy kindness"),
    ("S50", "d", "cu", "booth_day", "static", ["KIMW@expr-smile", "LOC@guard-booth-winter-day"],
     "SINGLE PORTRAIT: Kim alone, chest-up inside the booth, a faint kind smile already in the keyframe (50%), lips just parted; no hands.",
     "Warm booth bokeh", "Gentle smile 50%"),
    ("S51", "v", "insert", "booth_day", "static", ["LOC@guard-booth-winter-v1-key2"],
     "Insert: a hand quietly sets a steaming plain paper cup of barley tea on the window ledge toward the mother.",
     "Window ledge, steam, warm light", "Action instead of words"),
    ("S52", "card", "long", "snow_night", "pull", ["LOC@guard-booth-winter-night"],
     "Night exterior of the booth window in falling snow: inside, two silhouettes in the orange heater glow; the camera slowly pulls away.",
     "Snowy courtyard", "Warm afterglow"),
    ("S53", "card", "medium", "morning", "static", ["LOC@guard-booth-winter-day"],
     "No people. Morning inside the guard booth: an empty chair and a switched-off desk lamp.",
     "Booth interior, cold morning light", "Absence (next-episode teaser)"),
]

# 자막카드(화면 전용, silent). S07·S42 중복 카드는 사용자 승인으로 제거.
CARDS = {
    "S03": "無口なあの人が、\\Nなぜ明け方四時の廊下にいたのでしょうか",
    "S04": "キムさんのクリスマス",
    "S05": "12月24日",
    "S15": "その夜",
    "S35": "午前4時",
    "S40": "クリスマスの朝",
    "S52": "サンタは煙突からではなく、\\N警備室からやって来る",
    "S53": "次回 ― あの人が、初めて出勤しなかった",
}
# 일본어 글자 합성 장면(카메라 고정 필수) — docs/EP4-일본어글자합성-계획.md
JA_OVERLAY = {"S03": "1801 plate", "S07": "停電予告", "S18": "child letter", "S22": "wife note",
              "S37": "1801 plate", "S38": "1801 plate", "S42": "お知らせ/完納", "S43": "管理事務所 plate"}
AMBIENCE = {  # 무인 컷만 효과음형(제6장 4: 사람 있는 장면·quiet/tense 금지)
    "S03": "low fluorescent hum in an empty concrete corridor at night, faint wind",
    "S04": "distant winter wind over a snowy housing complex at night",
    "S05": "soft wind and snowfall, distant muffled traffic",
    "S06": "faint metallic creak of a mailbox door, soft wind from the entrance",
    "S07": "empty concrete corridor room tone, distant elevator chime",
    "S15": "soft wind and snowfall at night",
    "S18": "gentle paper rustle, faint kerosene heater hiss",
    "S22": "slow page turn, faint kerosene heater hiss",
    "S35": "empty concrete stairwell room tone, faint wind",
    "S38": "very faint electric hum of tiny christmas lights",
    "S39": "faint servo whir of a security camera",
    "S40": "morning birds chirping, distant soft wind",
    "S42": "empty concrete corridor room tone, distant birds",
    "S49": "kettle simmering on a kerosene heater, soft crackle",
    "S53": "morning birds chirping outside a small booth",
}
BGM = [  # 톤연출표 4구간(0초부터 전편, 볼륨 0.36~0.45, 구간 사이 숨은 2초 미만)
    (0.0, 80.0, 0.42, "sparse melancholic solo piano in a minor key, Japanese human drama (ninjo) film score, winter loneliness, slow tempo, instrumental only, no vocals, no lyrics"),
    (81.5, 141.0, 0.40, "tender piano and solo cello, nostalgic longing, Japanese family drama film score, slow tempo, instrumental only, no vocals, no lyrics"),
    (142.0, 235.5, 0.38, "delicate celesta and music box over soft piano, quiet gradual rise, hopeful night, Japanese drama score, slow, instrumental only, no vocals, no lyrics"),
    (236.5, None, 0.42, "warm strings with small sleigh bells and piano, gentle emotional resolution, heartwarming Japanese Christmas drama finale, slow, instrumental only, no vocals, no lyrics"),
]


def tc(sec):
    fr = int(round(sec * FPS))
    s, f = divmod(fr, FPS)
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}.{f:02d}"


def ass_t(sec):
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap(text, limit=26):
    """자막 한 줄 최대 약 26자(52px·여백 200 기준 약 29자 수용): 가운데에 가장 가까운 。、…』 뒤에서 한 번 줄바꿈."""
    if len(text) <= limit:
        return text
    mid = len(text) / 2
    cands = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "。、…』"]
    cands = [i for i in cands if text[i:i + 1] not in "…、。"] or cands
    cut = min(cands, key=lambda i: abs(i - mid)) if cands else int(mid)
    return text[:cut] + "\\N" + text[cut:]


def parse_lock():
    """PHASE 1 문서의 1-4 표(장면 시작·조립 길이·겹침)와 1-3 표(줄 시작)를 읽는다."""
    doc = open(os.path.join(ROOT, "docs", "EP4-PHASE1-대본동결-오디오앵커.md"), encoding="utf-8").read()

    def norm(sid):  # 문서 표기 S1·S14b → S01·S14b
        m = re.match(r"S(\d+)(b?)$", sid)
        return f"S{int(m.group(1)):02d}{m.group(2)}"

    def sec(t):
        m, rest = t.split(":")
        s, f = rest.split(".")
        return int(m) * 60 + int(s) + int(f) / FPS
    rows = []
    for m in re.finditer(r"^\| (S\d+b?) \| (\d\d:\d\d\.\d\d) \| ([\d.]+)s \| (\d+)s \| ([\d.]+) \| (.+?) \|$", doc, re.M):
        rows.append({"id": norm(m.group(1)), "start": sec(m.group(2)), "len": float(m.group(3)),
                     "gen": int(m.group(4)), "ov": float(m.group(5)), "kind_ko": m.group(6)})
    starts = {}
    for m in re.finditer(r"^\| (\d+) \| (S\d+b?) \| (\d\d:\d\d\.\d\d) \| (\d\d:\d\d\.\d\d) \|", doc, re.M):
        starts[int(m.group(1))] = (norm(m.group(2)), sec(m.group(3)))
    return rows, starts


def main():
    rows, starts = parse_lock()
    assert len(rows) == len(S) == 54, (len(rows), len(S))
    assert len(starts) == 34
    dur = {int(os.path.basename(f)[4:7]): MP3(f).info.length
           for f in glob.glob(os.path.join(ROOT, "assets", "audio-overrides", SKIT, "line*.mp3"))}
    assert sorted(dur) == list(range(1, 35)), sorted(dur)

    # Lock 시각을 그대로 유지하도록 파이프라인 길이(하드컷은 +1프레임)를 만든다
    durations, transitions = [], []
    for k, r in enumerate(rows):
        last = k == len(rows) - 1
        ov = 0.0 if last else r["ov"]
        durations.append(round(r["len"] + (HARD if ov == 0 and not last else 0.0), 4))
        transitions.append(ov)
    # generate_audio.rebuild_with_lipsync 와 같은 규칙으로 장면 경계를 계산
    eff = [o if o >= HARD else HARD for o in transitions]
    eff[-1] = 0.0
    t, bounds = 0.0, []
    for d, o in zip(durations, eff):
        bounds.append((t, t + d))
        t += d - o
    total = bounds[-1][1]
    for r, (b0, _b1) in zip(rows, bounds):
        assert abs(b0 - r["start"]) < 0.05, (r["id"], b0, r["start"])  # 표의 타임코드는 프레임 반올림

    idx = {r["id"]: k for k, r in enumerate(rows)}
    sb_scenes, scene_items, events = [], [], []
    for k, (sid, kind, lens, light, cam, refs, subject, env, expr) in enumerate(S):
        r = rows[k]
        assert r["id"] == sid, (r["id"], sid)
        b0, b1 = bounds[k]
        vis_end = b1 - eff[k]
        lines = sorted(i for i, (s, _t) in starts.items() if s == sid)
        if sid in JA_OVERLAY:
            cam = "static"  # 글자 합성 장면은 카메라 고정
        motion = {"d": MOTION_D, "react": MOTION_R}.get(kind)
        if motion is None:
            motion = ("Subtle natural motion only: " + expr.lower() + ". "
                      "Micro movements, no fast motion, no new people, props stay rigid and unchanged.")
            if kind in ("card", "n", "v", "vo") and "No people" in subject:
                motion = "Almost still: faint ambient motion only (light flicker, drifting snow or steam). Objects stay rigid and unchanged."
            if sid in JA_OVERLAY:
                motion += " Camera completely locked off; the blank surface for composited Japanese text must not move or warp."
        edit = []
        for i in lines:
            st = starts[i][1]
            edit.append(f"{tc(st)}~{tc(st + dur[i])} line {i} ({STYLE_NAMES[LINES[i][0]]})")
        if kind == "d" and lines:
            edit.append(f"{tc(starts[lines[-1]][1] + dur[lines[-1]])}~{tc(vis_end)} hold: lips closed, reaction only")
        trans = "Hard cut" if transitions[k] == 0 else f"Dissolve {transitions[k]:.1f}s"
        if k == len(rows) - 1:
            trans = "Fade to black → outro"
        keyframe = None
        if kind not in ("reuse",) and sid not in ("S02", "S30"):
            keyframe = f"assets/portraits/ep4-keyframes/{sid}-1.png"
        sb_scenes.append({
            "id": sid, "kind": kind, "timecode": f"{tc(b0)} - {tc(vis_end)}", "assembled_s": round(r["len"], 3),
            "generate_s": r["gen"], "shot": lens, "lens": LENS[lens], "lighting": LIGHT[light], "camera": CAM[cam],
            "transition_out": trans, "refs": refs, "subject": subject, "environment": env,
            "expression": expr, "motion": motion, "edit": " → ".join(edit) if edit else "",
            "lines": lines, "caption": CARDS.get(sid, "").replace("\\N", ""), "ja_overlay": JA_OVERLAY.get(sid, ""),
            "keyframe": keyframe,
        })
        prompt = f"{CAM[cam]}. Motion: {motion}"
        item = {"id": sid, "prompt": prompt, "duration": r["gen"]}
        if keyframe:
            item["image"] = keyframe
        scene_items.append(item)
        if sid in CARDS:
            c0 = b0 + (0.4 if sid != "S52" else 1.0)
            c1 = min(vis_end - 0.3, c0 + (3.0 if sid in ("S05", "S15", "S40") else 99))
            events.append((c0, c1, "Caption", "", CARDS[sid]))
    for i in range(1, 35):
        style, text = LINES[i]
        st = starts[i][1]
        events.append((st, st + dur[i], style, STYLE_NAMES[style], wrap(text)))
    events.sort(key=lambda e: e[0])

    # ---------- 자막 ----------
    ass = ["[Script Info]", "Title: EP4 キムさんのクリスマス (日本語版) 字幕", "ScriptType: v4.00+",
           "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Naration,Noto Sans CJK JP,52,&H00DDDDDD,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,5,2,2,200,200,80,1",
           "Style: Caption,Noto Serif CJK JP,56,&H00FFF3C4,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,5,200,200,80,1",
           "Style: Kim,Noto Sans CJK JP,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1",
           "Style: Ren,Noto Sans CJK JP,60,&H0096E6FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1",
           "Style: Mom,Noto Sans CJK JP,60,&H00C8C8FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in events:
        ass.append(f"Dialogue: 0,{ass_t(e[0])},{ass_t(e[1])},{e[2]},{e[3]},0,0,0,,{e[4]}")
    with open(os.path.join(ROOT, "subs", f"{SKIT}.ass"), "w", encoding="utf-8") as f:
        f.write("\n".join(ass) + "\n")

    # ---------- 스토리보드 ----------
    ref_map = {
        "KIMW": "assets/portraits/ep4-cast/cells/kimw-<cell>.png",
        "MOM": "assets/portraits/ep4-cast/cells/mom-<cell>.png",
        "REN": "assets/portraits/ep4-cast/cells/ren-<cell>.png",
        "CLERK": "assets/portraits/ep4-cast/cells/clerk-<cell>.png",
        "PROP": "assets/portraits/ep4-cast/cells/prop-<cell>.png",
        "LOC": "assets/portraits/ep4-cast/cells/loc-<place>.png",
        "GMA": "assets/portraits/ep3-cast/grandma-sheet-1.png",
        "CART": "assets/portraits/ep3-cart/cart-sheet-1.png",
    }
    sb = {"_설명": "EP4 PHASE 3 스토리보드 Lock 데이터(일본어 기준판). scripts/build_ep4_phase3.py가 생성 — 직접 수정 금지.",
          "skit": SKIT, "preset": PRESET, "negative": NEGATIVE, "plain_props": PLAIN, "ref_map": ref_map,
          "total_s": round(total, 3), "scenes": sb_scenes}
    with open(os.path.join(ROOT, "scripts", "storyboard", f"{SKIT}.json"), "w", encoding="utf-8") as f:
        json.dump(sb, f, ensure_ascii=False, indent=1)

    # ---------- 장면 생성 설정 ----------
    scenes_cfg = {
        "_설명": "EP4 일본어 기준판 장면 설정(build_ep4_phase3.py 생성). 키프레임(PHASE 4) 승인 후 i2v. 재사용·정지 푸시인 컷은 video-overrides로 대체.",
        "ratio": "16:9",
        "style": ("Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, keep the exact look, "
                  "faces, wardrobe, props and lighting of the first frame; natural slow motion only; no text, no captions, no logos, "
                  "no sudden movement, no new people entering"),
        "durations": [r["gen"] for r in rows],
        "scenes": [{"prompt": it["prompt"], "duration": it["duration"], **({"image": it["image"]} if "image" in it else {})}
                   for it in scene_items],
    }
    with open(os.path.join(ROOT, "scripts", "scenes", f"{SKIT}.json"), "w", encoding="utf-8") as f:
        json.dump(scenes_cfg, f, ensure_ascii=False, indent=1)

    # ---------- 조립·오디오 설정 ----------
    n = lambda sid: idx[sid] + 1
    audio = {
        "_설명": "EP4 일본어 기준판(build_ep4_phase3.py 생성). 음성 34줄은 assets/audio-overrides/kim-christmas/ (Typecast·EL 확정본, 배속 없음).",
        "tts_model": "fal-ai/minimax/speech-02-hd", "language_boost": "Japanese", "speed": 1.0,
        "default_voice": "Deep_Voice_Man",
        "style_voices": {"Naration": "Deep_Voice_Man", "Kim": "Imposing_Manner", "Ren": "Lively_Girl", "Mom": "Calm_Woman"},
        "style_names": STYLE_NAMES,
        "narration_styles": ["Naration"],
        "silent_styles": ["Caption"],
        "scene_durations": durations,
        "transitions": transitions,
        "omnihuman_scenes": [n(s) for s in ("S09", "S11", "S26", "S28", "S30", "S47", "S50")],
        "omnihuman_models": ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"],
        "lipsync_skip_scenes": [n("S18")],
        "lipsync_models": ["fal-ai/sync-lipsync", "fal-ai/latentsync"],
        "ambience_model": "fal-ai/mmaudio-v2", "ambience_volume": 0.35,
        "ambience_prompts": [AMBIENCE.get(r["id"], "") for r in rows],
        "bgm_model": "fal-ai/lyria2", "bgm_volume": 0.42,
        "bgm_prompt": BGM[0][3],
        "bgm_segments": [{"start": s, "end": round(total, 2) if e is None else e, "volume": v, "prompt": p} for s, e, v, p in BGM],
        "_전환": "transitions[k] = 장면 k→k+1 디졸브 초(0=하드컷, 파이프라인이 1프레임 겹침 → scene_durations에 +1프레임 반영해 Lock 시각 유지)",
    }
    with open(os.path.join(ROOT, "scripts", "audio", f"{SKIT}.json"), "w", encoding="utf-8") as f:
        json.dump(audio, f, ensure_ascii=False, indent=1)

    # ---------- 검토 문서 ----------
    kind_ko = {"reuse": "재사용", "react": "리액션(정지 푸시인)", "card": "자막카드", "n": "내레이션", "v": "무언",
               "d": "대사(OmniHuman)", "vo": "편지 목소리"}
    md = ["# EP4 「김씨의 크리스마스」 — PHASE 3 정밀 샷 리스트 (일본어 기준판)", "",
          f"규격서 PHASE 3 산출물. `scripts/build_ep4_phase3.py` 자동 생성(손 수정 금지). 총 **{tc(total)}**, 54컷(대본 53 + S14b), "
          f"디졸브 {sum(1 for o in transitions if o > 0)}곳, 자막카드 {len(CARDS)}장(S07·S42 중복 카드 제거 — 사용자 승인 2026-10-04).",
          "", "- 데이터: `scripts/storyboard/kim-christmas.json` · 장면 `scripts/scenes/kim-christmas.json` · 오디오 `scripts/audio/kim-christmas.json` · 자막 `subs/kim-christmas.ass`",
          "- 대사 7장면(S09·S11·S26·S28·S30·S47·S50) = 가슴 위 단독 CU 정지 키프레임 → OmniHuman. S30은 S28 키프레임 재사용.",
          "- 리액션 7컷(S02·S10·S19·S23·S27·S29·S45, S02는 S45 재사용) = 정지 푸시인, 립싱크 제외. S18(아이 편지 목소리)은 화면 밖 → 립싱크 제외.",
          "- 일본어 글자 합성 장면(카메라 고정): " + ", ".join(f"{k} {v}" for k, v in JA_OVERLAY.items()),
          "", "| 장면 | 타임코드 | 조립/생성 | 종류 | 샷 | 조명 | 카메라 | 전환 | 대사·카드 | 참조 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for s in sb_scenes:
        lc = ", ".join(f"L{i}" for i in s["lines"])
        if s["caption"]:
            lc = (lc + " / " if lc else "") + f"【{s['caption']}】"
        light_key = next(k for k, v in LIGHT.items() if v == s["lighting"])
        cam_key = next(k for k, v in CAM.items() if v == s["camera"])
        md.append(f"| {s['id']} | {s['timecode']} | {s['assembled_s']:.2f}/{s['generate_s']}s | {kind_ko[s['kind']]} | {s['shot']} | "
                  f"{light_key} | {cam_key} | {s['transition_out']} | {lc} | {', '.join(s['refs'])} |")
    md += ["", "## 오디오", f"- BGM 4구간: " + " · ".join(f"{s:.1f}~{('끝' if e is None else f'{e:.1f}')}s 볼륨 {v}" for s, e, v, _p in BGM)
           + " (구간 사이 숨 1.0~1.5초, −60dB 2초 무음 금지)",
           "- 현장음(무인 컷만): " + ", ".join(AMBIENCE), "- 사람 있는 장면·대화 블록은 BGM만(제6장 4).", ""]
    with open(os.path.join(ROOT, "docs", "EP4-PHASE3-샷리스트.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"완료: 54컷, 총 {tc(total)} ({total:.2f}s), 자막 {len(events)}개(카드 {len(CARDS)}), "
          f"디졸브 {sum(1 for o in transitions if o > 0)}곳")


if __name__ == "__main__":
    main()
