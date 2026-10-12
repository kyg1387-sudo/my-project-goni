#!/usr/bin/env python3
"""『明日から来なくていい』 PHASE 4 키프레임 스펙 생성기 (build_yanagi_keyframes.py 구조, 규격 제7장 1·7).

scripts/storyboard/ashita-kara.json(PHASE 3, build_ashita_phase3.py 생성)을 읽어 generate_portraits.py 스펙을 만든다.
스토리보드를 고치면 이 스크립트를 다시 돌릴 뿐, 스펙을 손으로 고치지 않는다.

단계:
  p:<id,id,…>  시범(파일럿) — scripts/portraits/ashita-kf-pilot.json
  a            OMNI 대사 CU 12장 — 참조 = PHASE 2 셀(표정 셀 + 로케이션)
  b            나머지 — 얼굴이 보이는 컷은 A에서 승인한 인물별 기준 얼굴 키프레임을 1번 참조로 추가(FACE_KF, A 검수 후 확정)
generate-video.yml portraits_spec=<스펙> → assets/portraits/<스펙>/<id>-1.png
  r<n>:<id,…>  검수 불합격 재생성(단계 무관, 컷당 후보 2장) — scripts/portraits/ashita-kf-r<n>.json
사용법: python3 scripts/build_ashita_keyframes.py p:S25a,S24d,S14a | a | b | a:S12c,S25a(재생성분만 -r) | r1:S24c,S01b
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "ashita-kara.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "ashita-kf-{}.json")
KF_A = "assets/portraits/ashita-kf-a"

PEOPLE = [  # (셀 파일 접두어, 설명) — 더 긴 접두어를 먼저(sato-b가 sato보다 먼저)
    ("sato-b", "Sato (48, engineer, thin silver-rimmed glasses, charcoal suit)"),
    ("sato", "Sato (48, engineer, thin silver-rimmed glasses, navy work jacket)"),
    ("tanaka", "Tanaka (28, arrogant manager, light-brown swept-up hair, NO glasses, NO earrings)"),
    ("yamamoto", "Yamamoto (63, executive, bald crown, thin gold-rimmed glasses)"),
    ("takahashi", "Takahashi (55, client division head, very short grey hair, NO glasses, black overcoat)"),
    ("mori", "Mori (24, young female engineer, black bob with bangs, NO glasses)"),
]
# B단계 인물별 기준 얼굴 = A단계 대사 키프레임 (A 검수 2026-10-11 확정: 밝고 중립에 가까운 정면 컷)
FACE_KF = {"sato": "S09d", "sato-b": "S26c", "tanaka": "S05d", "takahashi": "S24c"}
FACE_KINDS = ("face", "react", "d")
# B단계(2026-10-11) 교훈 ⑨: 기준 얼굴 키프레임을 통째로 참조하면 그 배경(사무실)·정면 구도가 다른 장소·측면 컷에 새어 들어감
# (S12e·S13b 회의실→사무실, S28c·S28e 측면→정면) → 기준 얼굴은 배경 없는 얼굴 크롭(assets/portraits/ashita-faces/<인물>.png)으로 참조
FACE_DIR = "assets/portraits/ashita-faces"
PILOT_DONE = {"S14a", "S24d"}  # 시범에서 승인·보정 완료(assets/portraits/ashita-kf-pilot/*-fixed 사용) → B에서 제외

LOC_NOTE = {  # 로케이션별 고정 문장(PHASE 2 Kill Gate 잔여 결함 대응)
    "loc-control": ("All control-room walls are completely bare: NO papers, notices, charts or signs on the walls; consoles have plain "
                    "unlabeled buttons; monitors show only abstract shapes or are dark."),
    "loc-meeting": "The meeting room walls are completely bare: no posters, no signs, no plaques; the table is long glossy black lacquer.",
    "loc-office": "Office walls are bare: no posters, no exit signs, no notices; drawings and screens show only lines with no lettering.",
    "loc-misc": "No shop signs, posters or labels with writing anywhere; any awning or sign surface is plain.",
    "props-breaker": "The breaker unit has NO stickers or labels at all, only scuffed grey metal.",
}
TIGHT = ("Tight chest-up close-up: head and shoulders fill the frame, the top of the head near the top edge, the frame cut at mid-chest; "
         "the face occupies about one third of the frame height; hands, wrists and wristwatch NOT visible anywhere; no earrings. "
         "Full-frame 16:9 image, no black bars, no letterbox.")
# 시범(2026-10-11) 교훈: ① 립싱크 CU 지시에도 미디엄으로 나와 손·시계가 들어옴 → 위 문장 강화 + 생성 후 가슴 위 재구도(무료)
# ② 위아래 검은 띠가 생김 → 생성 직후 kf_letterbox_fix.py ③ 콘솔·기기의 작은 가짜 글자 → 해당 영역 얕은 심도 처리(무료)
# ④ 타나카 귀걸이가 생김(시트 표정 칸에서 전이) → 인물 문장에 'no earrings' 고정
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
COMPOSITION = {
    "S25a": TIGHT + " Tanaka is on his knees, face crumpled in sobbing despair, looking up toward someone just off camera.",
    "S24d": ("Medium shot from the side: Yamamoto stands frozen in terror in the dark control room, face drenched with fine realistic "
             "perspiration, gold-rimmed glasses slightly fogged at the edges, a trembling hand half raised. " + FULL),
    "S14a": ("Wide night shot of the open-plan office: Sato in the navy work jacket and silver-rimmed glasses stands at his lamp-lit desk "
             "placing a folder into a cardboard box, seen in three-quarter view; Mori in the light-blue uniform stands two steps behind him, "
             "seen from behind. Only one warm desk lamp lights the scene. " + FULL),
}
# A단계(2026-10-11) 교훈: ⑤ 대사 CU가 소리 지르는 입으로 나옴(S12b) → 분노는 눈·이마·턱으로, 입은 닫힘
# ⑥ 낮 로케이션 시트를 참조하면 암전 장면이 낮 조명으로 나옴(S24c) → 조명 고정 문장을 참조보다 우선
# ⑦ '무릎 꿇은' 지시가 있으면 미디엄으로 넓어짐(S25a 2회) → 자세는 화면 밖, 머리·어깨만
COMPOSITION["S12b"] = ("Fury shown only in the eyes, furrowed brow, flared nostrils and clenched jaw: lips pressed tightly together, "
                       "mouth CLOSED, NOT shouting, NOT yelling. " + TIGHT)
COMPOSITION["S25a"] = (TIGHT + " Only Tanaka's head and the top of his shoulders are visible, seen from slightly above; his kneeling "
                       "posture is NOT shown. Face crumpled in sobbing despair, looking up toward someone just off camera; the background "
                       "is dark and out of focus with no consoles or wall papers in frame.")
LIGHT_NOTE = {  # 장면 조명 고정 — 로케이션 참조의 낮 조명을 덮어쓴다
    "red_door": ("LIGHTING OVERRIDES THE LOCATION REFERENCE: the control room is in a power blackout — NO daylight, windows dark, ceiling "
                 "lights off; lit only by a red emergency lamp and a strong white backlight from the open doorway behind; deep shadows."),
    "red": ("LIGHTING OVERRIDES THE LOCATION REFERENCE: blackout, NO daylight, ceiling lights off; only red emergency light, deep shadows."),
    "lamp": ("LIGHTING OVERRIDES THE LOCATION REFERENCE: late at night, windows black with distant city lights, ceiling lights off; "
             "the only light is one warm desk lamp."),
}
# B단계 교훈 ⑩ 인물 참조가 있는 손·소품 인서트가 얼굴 미디엄으로 나옴(S03c·S04b·S08b·S11ca·S16b·S19d) → 인서트 고정 문장
INSERT = ("EXTREME CLOSE-UP INSERT: only the hands / object described fill the frame; NO face, NO head and NO shoulders anywhere in "
          "the frame — the person is out of frame except the hands, wrists and sleeves. Shallow depth of field.")
# ⑪ 같은 로케이션 참조의 연속 무인·원경 컷이 같은 구도로 나옴(S01a~c, S15a·b) → 앵글 고정 문장
ANGLE = {
    "HA": "CAMERA: steep high angle, looking down from about 6 metres above.",
    "OH": "CAMERA: directly overhead, looking straight down.",
    "BE": "CAMERA: bird's-eye view straight down from the ceiling.",
    "SIDE": "CAMERA: from the side — the face in clear side profile or three-quarter profile, NOT facing the camera.",
}
# ⑫ 일본어 글자를 합성할 문서·화면에 가짜 글자가 빽빽이 나옴(S21e·S21g·S27d·S09b) → 무지 면 고정 문장
BLANK = ("Every paper, document, form, envelope and screen surface is completely blank and clean: NO printed lines, NO characters, "
         "NO headings, NO tables of text, NO stamps with characters (Japanese text is composited later).")
COMPOSITION.update({
    "S01b": ("No people. Steep high angle from a third-floor window looking DOWN onto the wide paved forecourt in front of the entrance; "
             "the revolving door small at the top of the frame; long morning shadows. " + FULL),
    "S01c": ("No people. Extreme close-up detail of the glass curtain-wall panels only, filling the whole frame, reflecting drifting white "
             "clouds and blue sky; NO door, NO ground visible. " + FULL),
    "S15b": ("Steep high angle from a second-floor window: raindrops streaking down the glass in the foreground, and far below a tiny "
             "Sato walks away across the wet forecourt carrying a cardboard box. " + FULL),
    "S19b": ("A wall of control-room monitors all glowing solid red; in the centre one large monitor shows a plain blank white rectangular "
             "warning panel with a thin red border and nothing written on it. Dark room. " + FULL),
    "S21e": ("Insert from above: one sheet of completely blank white paper on a warm wooden desk, a single thin grey signature line near "
             "the bottom and nothing else printed. " + FULL),
    "S21g": ("Insert from above: one sheet of plain blank white paper with only a faint ruled grid and one round red seal mark with no "
             "characters, on a grey desk; background softly out of focus with NO signs or labels. " + FULL),
    "S27d": ("Insert from above: a plain beige envelope and one sheet of completely blank white paper on a grey desk under cold "
             "fluorescent light; nothing printed anywhere. " + FULL),
    "S09b": ("Insert: a monitor showing a plain spreadsheet-like table of empty grey cells, two rows highlighted in pale yellow, "
             "every cell empty with no characters. Background out of focus. " + FULL),
    "S28c": ("Side close-up: Sato in three-quarter profile facing screen-left toward Mori off camera, a warm restrained smile, mouth hidden "
             "by the angle; golden morning window light rims his face. " + FULL),
    "S28e": ("Close-up true side profile of Sato facing screen-right, looking out of the window at the city skyline in morning light, "
             "peaceful; the window and city soft in the background. " + FULL),
})
# A단계 재생성(2026-10-11) 교훈: ⑧ 조명 고정 문장만으로는 낮 로케이션 참조·낮 배경의 얼굴 참조를 못 이김(S24c 2장 모두 낮)
# → 암전 장면은 낮 로케이션 참조를 빼고, 같은 장면의 승인 컷(시범 S24d)을 조명·공간 참조로 쓴다. 얼굴은 시트 셀로만.
# ⑮ 조명 참조 컷 속 인물(山本)이 옮겨 붙음(S24e 2장·S24b 1장이 山本로) → 조명 참조는 인물을 잘라낸 판(S24-light: S24d 좌·우만 이어 붙임)
LIGHT_REF = {"S24": "assets/portraits/ashita-kf-pilot/S24-light.png"}  # 장면 → 같은 장면 승인 컷의 무인 조명·공간 참조
DAY_LOCS = ("loc-control-day", "loc-control-angles-day", "loc-control-key", "loc-control-angles-key")
# ⑬ 소품만 참조한 인서트가 엉뚱한 장소(사무실)에 놓임(S17be) → 같은 장면 로케이션 참조 추가
COMPOSITION["S24e"] = ("Side medium of Takahashi ONLY (55, very short grey hair, NO glasses, black overcoat, stern) — NOT a bald man, "
                       "NOT wearing glasses; he turns his head slightly toward someone off screen-left, mouth hidden by the angle, hands down. " + FULL)
# ⑯ 「mouth hidden」 지시를 무시하고 화자의 입이 또렷이 보임(비-OMNI 대사 시작 컷 48개 중 27개) → 컷별 가림 방법을 구체적으로 고정
#    (뒷모습·어깨 너머 / 손수건·컵·수화기로 가림 / 역광 실루엣). 규격 조명카메라앵글 §AI 한계: 측면·뒷모습은 입이 안 보이는 대사 처리에만.
NO_MOUTH = "The speaking character's mouth and lips are NOT visible anywhere in the frame."
BACK = "seen strictly from behind — only the back of the head, hair, ears and shoulders are visible, the face turned away from the camera"
MOUTH_HIDE = {
    "S05a": f"Tanaka in the foreground {BACK}, perching on the corner of Sato's desk; beyond him Sato sits at the desk looking up, calm.",
    "S05b": f"Tanaka sitting on the desk corner {BACK}, raising a white paper coffee cup dismissively; the office stretches out in front of him.",
    "S05c": f"High angle from behind Sato's shoulder: Sato seated {BACK}, his hands on the drawings, looking up toward a blurred figure across the desk.",
    "S06bc": f"Tanaka in the corridor {BACK}, phone pressed to his ear by a hand wearing a chunky gold wristwatch, shoulders shaking with a laugh.",
    "S07a": f"High angle: Tanaka stands in the foreground {BACK}, looming over Mori seated at her desk beyond him; his shadow falls across her drawing.",
    "S09a": f"Past a monitor in the foreground: Sato walks away from the camera toward a desk across the office, {BACK}, a sheet of paper in his hand.",
    "S09c": f"Tanaka lounging in his office chair {BACK}, the high chair back and the back of his head filling the left of the frame, one hand raised in a shrug.",
    "S11c": f"Over-the-shoulder from behind Sato: Sato sits upright {BACK}, his hand flat on a blank document on the long black table; Yamamoto blurred at the far end.",
    "S12a": f"Low angle: Tanaka has shoved his chair back and stands {BACK}, his arm thrust out pointing across the long meeting table.",
    "S12d": f"From behind Yamamoto's shoulder: Yamamoto {BACK}, his hand sliding a blank white envelope across the black table with two fingers.",
    "S13b": f"Tanaka stands with arms crossed {BACK}, in the meeting room, his head tilted in a scoff.",
    "S14c": f"From behind and slightly above Sato's shoulder: Sato {BACK}, head bowed over the open cardboard box, his hands placing a folder inside; warm lamp light.",
    "S14e": ("Close-up from behind Mori's shoulder: the back of her black bob and her ear, only the edge of her cheek with one tear catching the lamp "
             "light; her face turned away from the camera."),
    "S17a": ("Low angle two-shot: Tanaka and Yamamoto as pure black silhouettes against a bright warm gold window glow, raising champagne glasses; "
             "their faces completely dark with NO facial features visible."),
    "S17d": f"Tanaka {BACK} — only the edge of his cheek and ear visible — holding a champagne glass, the gold lounge and night city beyond.",
    "S17ba": (f"Through the door frame of a small concrete substation room: Tanaka in the foreground doorway {BACK} as a dark silhouette; "
              "beyond him Mori stands by the old grey breaker cabinet facing him."),
    "S17bb": f"Mori stands facing the old grey breaker cabinet {BACK}, her hand near the cabinet, firm posture; bare concrete room, one bulb.",
    "S17bc": f"Wide from inside the concrete room: Tanaka in the bright doorway {BACK}, walking out, one hand flicked dismissively.",
    "S17bd": "Close-up from behind Mori's shoulder: the back of her black bob and her ear, her hand resting on the grey cabinet; her face turned away.",
    "S18e": f"Tanaka {BACK}, slamming his palm down on the control console, monitors and the substation window beyond.",
    "S18f": "High angle over Mori's shoulder from behind: the back of her black bob in the foreground, a wall of monitors flashing solid red beyond.",
    "S19c": ("Medium close-up of Yamamoto frozen, the telephone receiver pressed against his face so it COVERS his mouth and chin, eyes wide, "
             "fine realistic sweat on his forehead, gold-rimmed glasses."),
    "S22a": (f"Low wide of the control room: Mori in the foreground at the console {BACK}; beyond her Tanaka stands by the start button, "
             "staff silhouettes at the back."),
    "S22b": ("Close-up side of Tanaka sweating, pressing a white handkerchief against his mouth and chin with one hand so the mouth is "
             "COVERED, eyes forcing a brave look."),
    "S24b": ("Low angle medium of Takahashi as a hard backlit silhouette against the bright doorway, coat open; his face completely in black "
             "shadow with NO facial features visible."),
    "S28a": (f"The bright new office: Mori in the foreground doorway {BACK} in her light-blue uniform; beyond her Sato in a charcoal suit "
             "stands at the window holding a white coffee cup, facing her with a gentle look."),
    "S28c": ("Side close-up of Sato raising a white coffee cup to his lips so the cup COVERS his mouth, a warm restrained smile in his eyes; "
             "golden morning window light."),
}
# ⑰ r3에서도 8컷은 측면·돌아보는 얼굴로 나옴(얼굴 크롭·정면 셀 참조가 얼굴을 끌어냄) → 인물 참조를 시트의 「뒷모습 전신」 칸으로
#    바꾸고 얼굴 크롭을 빼며, 가림 방법을 모두 뒷모습으로 통일
BACK_ONLY = {"S05a": "tanaka", "S05b": "tanaka", "S11c": "sato", "S13b": "tanaka", "S14e": "mori", "S17d": "tanaka",
             "S17bd": "mori", "S19c": "yamamoto"}  # 컷 → 뒷모습으로 바꿀 화자
MOUTH_HIDE.update({
    "S05a": f"Camera directly behind Tanaka: Tanaka {BACK}, perched on the corner of the desk, filling the left foreground; Sato sits beyond, facing the camera.",
    "S05b": f"Camera directly behind Tanaka: Tanaka {BACK}, sitting on the desk corner, one hand raising a white paper cup; the bright office beyond.",
    "S11c": f"Camera directly behind Sato: Sato {BACK}, sitting upright at the long black table, his hand flat on a blank document; the far end of the table empty.",
    "S13b": f"Camera directly behind Tanaka: Tanaka {BACK}, standing with his arms crossed at the meeting table, head tilted.",
    "S14e": f"Camera directly behind Mori: Mori {BACK}, standing by the lamp-lit desk at night, her shoulders trembling slightly, nodding.",
    "S17d": f"Camera directly behind Tanaka: Tanaka {BACK}, holding up a champagne glass toward the night city window in the dim gold lounge.",
    "S17bd": f"Camera directly behind Mori: Mori {BACK}, her hand resting flat on the grey breaker cabinet in the bare concrete room.",
    "S19c": f"Camera directly behind Yamamoto: Yamamoto {BACK} (bald crown), frozen with a telephone receiver at his ear, the dark meeting room beyond.",
})
# 고니감독님 요청(2026-10-11, B안): 정면 대사 CU → 「일하면서 옆에서 나누는 대화」 3/4 구도. OmniHuman은 정면~45°까지만 안정(규격 제8장 5)
# → 화자는 30~40° 3/4, 앞쪽에 상대의 흐린 어깨·뒤통수(어깨 너머), 손은 작업 중. 입은 화면에 또렷이(립싱크 대상).
CONVO = {
    "S09d": ("Over-the-shoulder conversation shot in the bright design office: in the soft out-of-focus foreground left, the back of Tanaka's "
             "light-brown hair and navy suit shoulder; Sato sits at his drafting desk, body angled toward the drawings, his left hand flat on "
             "a large blank technical drawing and his right index finger pointing at it, his head turned about 35 degrees toward Tanaka, "
             "speaking firmly with restrained anger behind silver-rimmed glasses. Medium close-up from mid-chest up, face sharp, 50mm lens."),
    "S12c": ("Over-the-shoulder conversation shot in the meeting room: in the dark soft foreground right, the back of Sato's head and navy work "
             "jacket shoulder (seated); Tanaka stands beside the long black table, one hand resting on the back of a chair, leaning slightly "
             "forward, his face turned about 35 degrees toward Sato with a slow cruel sneer, eyes narrowed. Medium close-up from mid-chest up, face sharp, 50mm lens."),
    "S24c": ("Over-the-shoulder conversation shot in the blacked-out control room: in the dark soft foreground left, the bald crown and black "
             "suit shoulder of Yamamoto seen from behind; Takahashi stands facing him at about 35 degrees, black overcoat open, one hand holding a "
             "plain folder at his side, condemning glare, lit by the red emergency lamp and the white doorway backlight. Medium close-up from mid-chest up, face sharp."),
}
# 시범 교훈 ⑱: 「Medium close-up」만으로는 서 있는 인물이 전신 원경으로 나옴(S12c r5) → 얼굴 크기를 명시
CONVO["S12c"] = ("Over-the-shoulder conversation shot in the meeting room, TIGHT on Tanaka: in the dark soft foreground right edge, the back "
                 "of Sato's grey-streaked head and navy work-jacket shoulder; Tanaka stands beside the long black table leaning forward with "
                 "both hands on the table edge, his face turned about 35 degrees toward Sato with a slow cruel sneer, eyes narrowed. "
                 "Framing from mid-chest up: Tanaka's head and shoulders fill the left-center of the frame, his face about one third of the "
                 "frame height, sharp; 85mm lens.")
# 고니감독님 지적(7:35): S22c 인서트가 원경으로 나오고 몸 없는 팔이 빈 의자 뒤에서 나옴 + 「START」 글자를 흐린 자국이 빨간 얼룩으로 보임
# → 진짜 인서트(손가락·버튼만 화면 가득), 버튼은 무지 빨간 버섯형 버튼(글자 없음). 일본어 「試運転」 라벨은 필요하면 합성.
COMPOSITION["S22c"] = ("EXTREME CLOSE-UP INSERT filling the whole frame: a man's index finger, the cuff of a navy suit sleeve and a chunky gold "
                       "wristwatch, the finger hovering one centimetre above a large round red mushroom-shaped emergency start button set in a "
                       "grey steel control panel; the button top is completely plain glossy red with NO letters; shallow depth of field, the "
                       "control room softly blurred behind; NO face, NO chair, NO monitors in focus. " + FULL)
CONVO_REFS = {"S09d": ["assets/portraits/ashita-cast-2/cells/tanaka-full-back.png"],
              "S12c": ["assets/portraits/ashita-cast-2/cells/sato-full-back.png"],
              "S24c": ["assets/portraits/ashita-cast-2/cells/yamamoto-full-back.png"]}
# B안 전체(고니감독님 승인 2026-10-12): 나머지 대사 10컷 — 어깨 너머 3/4, 일하는 손, 톤연출표 감정에 맞춘 표정·동작(제10장 7)
FACE13 = ("Framing from mid-chest up: the speaker's head and shoulders fill the frame, the face about one third of the frame height and "
          "sharp, turned about 35 degrees toward the other person; 85mm lens, f/2.0, shallow depth of field.")
EXTRA_REFS["S24b"] = ["assets/portraits/ashita-faces/takahashi.png"]   # 실루엣 컷이던 S24b를 립싱크 대화 컷으로 — 얼굴 기준 추가
CONVO.update({
    "S05d": ("Over-the-shoulder conversation shot in the bright design office: in the soft foreground left, the back of Sato's grey-streaked "
             "head and navy work-jacket shoulder (seated). Tanaka perches on the corner of the desk holding a white paper coffee cup loosely, "
             "head tilted, one eyebrow raised in a mocking smirk (L08 mocking laugh). " + FACE13),
    "S09e": ("Over-the-shoulder conversation shot in the design office: in the soft foreground right, the back of Sato's grey-streaked head "
             "and navy jacket shoulder. Tanaka leans back in his office chair, one arm over the backrest, the other hand gesturing lazily "
             "with an open palm, a condescending smirk (L15 looking-down laugh). " + FACE13),
    "S11d": ("Over-the-shoulder conversation shot across the long black meeting table: in the dark soft foreground left, the bald crown "
             "and gold-rimmed glasses temple of Yamamoto seen from behind. Sato sits upright, both hands flat on a closed plain folder on "
             "the table, jaw set, eyes unwavering, resolute (L18 determined). Chiaroscuro top light. " + FACE13),
    "S12b": ("Over-the-shoulder conversation shot in the meeting room: in the dark soft foreground right, the back of Sato's grey-streaked "
             "head (seated). Tanaka has just stood up, one fist pressed on the black table, leaning forward over it, furious, brow knotted, "
             "lips pressed tight between words (L21 shouting rage — mouth closed in the still). " + FACE13),
    "S13a": ("Over-the-shoulder conversation shot in the meeting room: in the soft foreground left, the navy suit shoulder and light-brown "
             "hair of Tanaka from behind, standing. Sato is slowly rising from his chair, one hand on the table edge, the other holding his "
             "folder, eyes lowered then looking up, quiet cold restraint after a long silence (L24 low and quiet). " + FACE13),
    "S14d": ("Over-the-shoulder conversation shot in the night office lit by one warm desk lamp: in the soft foreground right, the back of "
             "Mori's black bob and light-blue uniform shoulder. Sato stands beside the open cardboard box, one hand resting on its edge, "
             "leaning slightly toward Mori, earnest and grave, asking a final favor (L27 entrusting, word by word). " + FACE13),
    "S24b": ("Over-the-shoulder conversation shot in the blacked-out control room: in the dark soft foreground left, the bald crown and black "
             "suit shoulder of Yamamoto seen from behind. Takahashi stands facing him, black overcoat open, holding up a plain closed folder "
             "at chest height, calm and cold, delivering a notice (L43 cold announcement). His face is lit by the red emergency lamp from one "
             "side and the white doorway backlight from behind — face clearly visible. " + FACE13),
    "S25a": ("Over-the-shoulder shot from behind Sato standing (soft charcoal suit shoulder and grey hair in the dark foreground right): "
             "Tanaka kneels on the control room floor looking up, both hands clasped in front of his chest begging, face crumpled, real tears "
             "streaming and sweat glistening, red emergency light (L47 sobbing plea). Seen from slightly above. " + FACE13),
    "S26a": ("Over-the-shoulder shot from low behind the kneeling Tanaka (soft light-brown hair and navy shoulder in the dark foreground "
             "left): Sato in a charcoal suit stands looking down at him, hands at his sides, cold calm eyes behind silver glasses, backlit by "
             "the open doorway (L48 cold). Low angle. " + FACE13),
    "S26c": ("Over-the-shoulder shot from low behind the kneeling Tanaka (soft light-brown hair in the dark foreground left): Sato in a "
             "charcoal suit, slightly closer, adjusts his cuff with one hand, an icy faint smile at one corner of the mouth, backlit by the "
             "doorway (L49 chilling). Low angle. " + FACE13),
})
CONVO_REFS.update({
    "S05d": ["assets/portraits/ashita-cast-2/cells/sato-full-back.png"], "S09e": ["assets/portraits/ashita-cast-2/cells/sato-full-back.png"],
    "S11d": ["assets/portraits/ashita-cast-2/cells/yamamoto-full-back.png"], "S12b": ["assets/portraits/ashita-cast-2/cells/sato-full-back.png"],
    "S13a": ["assets/portraits/ashita-cast-2/cells/tanaka-full-back.png"], "S14d": ["assets/portraits/ashita-cast-2/cells/mori-full-back.png"],
    "S24b": ["assets/portraits/ashita-cast-2/cells/yamamoto-full-back.png"], "S25a": ["assets/portraits/ashita-cast-2/cells/sato-b-full-back.png"],
    "S26a": ["assets/portraits/ashita-cast-2/cells/tanaka-full-back.png"], "S26c": ["assets/portraits/ashita-cast-2/cells/tanaka-full-back.png"],
})
for _k, _v in MOUTH_HIDE.items():
    COMPOSITION[_k] = _v + " " + NO_MOUTH + " " + FULL
EXTRA_REFS = {"S17be": ["assets/portraits/ashita-cast/cells/loc-misc-key2.png"]}
COMPOSITION["S17be"] = ("Extreme close-up of the large black lever on the front of the old grey mechanical breaker cabinet, mounted on the "
                        "bare concrete wall of the small substation room lit by one bare bulb; NO desks, NO office. " + FULL)


def who_of(name):
    return next(((k, v) for k, v in PEOPLE if name.startswith(k + "-")), (None, None))


def describe(path, i):
    name = os.path.basename(path)
    if path in LIGHT_REF.values():
        return (f"Reference image {i} is the LIGHTING and LOCATION reference for this scene: match its blackout darkness, red emergency "
                "lamp and white doorway backlight exactly; ignore the person in it.")
    if path.startswith(FACE_DIR):
        who = dict(PEOPLE).get(name[:-4], "the character")
        return (f"Reference image {i} is a tight face crop of {who}: reproduce exactly this face, age, hairstyle and glasses (or no glasses); "
                "it is for identity ONLY — do NOT copy its camera angle, background or lighting.")
    if "/ashita-kf-" in path:
        k = next((k for k, s in FACE_KF.items() if name.startswith(s + "-")), None)
        who = dict(PEOPLE).get(k, "the character")
        return (f"Reference image {i} is the APPROVED face of {who}: reproduce exactly this face, age and hairstyle "
                "(glasses exactly as there); ignore its background, framing and pose.")
    k, v = who_of(name)
    if k:
        return (f"Reference image {i} is the character sheet cell of {v}: copy this exact face, hairstyle, glasses (or no glasses), "
                "wardrobe and age; ignore its background, framing and any sheet layout.")
    if name.startswith("props-"):
        return f"Reference image {i} is the prop reference: copy the object's exact shape, size and material; ignore any background or labels."
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing and light direction; "
            "ignore any borders, labels or wall papers.")


def notes(refs):
    out = []
    for r in refs:
        b = os.path.basename(r)
        for k, v in LOC_NOTE.items():
            if b.startswith(k) and v not in out:
                out.append(v)
    return out


def build(sc, face_refs):
    refs = list(face_refs) + list(sc["refs"]) + EXTRA_REFS.get(sc["id"], [])
    convo = (STAGE.startswith("r5") or STAGE.startswith("r7")) and sc["id"] in CONVO
    if convo:
        refs += CONVO_REFS[sc["id"]]
    if sc["id"] in BACK_ONLY:  # 뒷모습 전용: 얼굴 크롭 제거, 화자 셀 → <화자>-full-back
        out = []
        for r in refs:
            if r.startswith(FACE_DIR):
                continue
            k, _ = who_of(os.path.basename(r))
            if k == BACK_ONLY[sc["id"]]:
                r = os.path.join(os.path.dirname(r), f"{k}-full-back.png")
            if r not in out:
                out.append(r)
        refs = out
    lr = LIGHT_REF.get(sc["scene"])
    if lr and sc["id"] != "S24d" and sc.get("lighting") in ("red_door", "backlit"):
        # 낮 로케이션·낮 배경 승인 얼굴(高橋 S24c-1) 참조를 빼고 같은 장면 조명 참조로 교체
        refs = [r for r in refs if not os.path.basename(r).startswith(DAY_LOCS) and "/ashita-kf-a/" not in r] + [lr]
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, "
             "no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    parts.append(sc["keyframe_prompt"])
    parts += notes(sc["refs"])
    if sc.get("lighting") in LIGHT_NOTE:
        parts.append(LIGHT_NOTE[sc["lighting"]])
    people = [r for r in refs if who_of(os.path.basename(r))[0] or r.startswith(FACE_DIR)]
    if sc["kind"] == "ins" and people:
        parts.append(INSERT)
    if sc.get("angle") in ANGLE and (sc["angle"] != "SIDE" or people) and not (sc["angle"] == "SIDE" and sc["id"] in MOUTH_HIDE):
        parts.append(ANGLE[sc["angle"]])
    if sc.get("ja_overlay") or sc["id"] in ("S21e", "S21g"):
        parts.append(BLANK)
    if convo:
        parts.append(CONVO[sc["id"]] + " Full-frame 16:9 image, no black bars, no letterbox.")
    elif sc["id"] in COMPOSITION:
        parts.append(COMPOSITION[sc["id"]])
    elif sc["kind"] == "d":
        parts.append(TIGHT)
    else:
        parts.append(FULL)
    if sc["kind"] == "d":
        parts.append("Mouth gently closed or barely parted (speech is added later); natural skin texture, both eyes sharp and symmetrical.")
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": " ".join(parts)}


STAGE = ""


def main():
    global STAGE
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    STAGE = arg
    stage, _, only = arg.partition(":")
    stage = stage.lower()
    only = set(only.split(",")) if only else None
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    chars, missing = [], []
    for sc in sb["scenes"]:
        if not sc.get("keyframe"):
            continue
        if stage == "p" or stage.startswith("r"):
            if sc["id"] not in only:
                continue
        else:
            is_a = sc["kind"] == "d"
            if (stage == "a") != is_a or (only and sc["id"] not in only):
                continue
            if stage == "b" and not only and sc["id"] in PILOT_DONE:
                continue
        face = []
        if stage.startswith("r") and sc["kind"] in FACE_KINDS:  # 재생성: 배경 없는 얼굴 크롭 참조
            for r in sc["refs"]:
                k, _ = who_of(os.path.basename(r))
                if k in FACE_KF:
                    f = f"{FACE_DIR}/{k}.png"
                    if f not in face:
                        face.append(f)
        if (stage == "b" or (stage == "a" and only)) and sc["kind"] in FACE_KINDS:  # 재생성분도 승인 얼굴 참조
            for r in sc["refs"]:
                k, _ = who_of(os.path.basename(r))
                if k in FACE_KF:
                    f = f"{KF_A}/{FACE_KF[k]}-1.png"
                    if f not in face:
                        face.append(f)
        c = build(sc, face)
        missing += [f for f in c["refs"] if not os.path.exists(os.path.join(ROOT, f))]
        if only and stage != "p":
            c["count"] = 2
        chars.append(c)
    if (stage == "p" or stage.startswith("r")) and len(chars) != len(only):
        raise SystemExit(f"시범 컷 일부 없음: {sorted(only - {c['id'] for c in chars})}")
    if missing:
        raise SystemExit("참조 파일 없음: " + ", ".join(sorted(set(missing))))
    name = "pilot" if stage == "p" else stage if stage.startswith("r") else stage + ("-r" if only else "")
    head = {"_설명": f"ashita-kara PHASE 4 키프레임 {name} (build_ashita_keyframes.py 생성, 직접 수정 금지).", "_style_preset": sb["preset"]}
    path = OUT.format(name)
    json.dump({**head, "characters": chars}, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(c["count"] for c in chars)
    print(f"{name} 키프레임 {len(chars)}컷 {n}장 → {path} (약 {n * 0.04:.2f}달러)")


if __name__ == "__main__":
    main()
