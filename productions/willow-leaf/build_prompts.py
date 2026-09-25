#!/usr/bin/env python3
"""버들잎 한 장 — 컷 데이터 → 스토리보드 시트 / 컷 프롬프트 / 편집 타임라인 생성.

AI 영화 제작 규칙집(Seedance 2.0 기준)을 그대로 따른다.
  - 컷 프롬프트는 LOCK / SCENE / CAMERA / DURATION / DIALOGUE / SOUND 블록 고정
  - 스타일 블록은 매 프롬프트·매 시트에 전부 포함 (공통 블록 참조 금지)
  - VO·자막·타이틀은 프롬프트에 넣지 않고 편집 타임라인으로만 뺀다

사용법:
    python3 productions/willow-leaf/build_prompts.py

출력 (같은 폴더):
    03_storyboards.md   씬 스토리보드 콘택트시트 프롬프트 (시트당 패널 5개 이하)
    04_cut_prompts.md   컷당 1개 영상 생성 프롬프트
    05_edit_timeline.md 타임코드 · VO · 자막 · 편집 지시
    cuts.json           위 내용의 기계 판독용 데이터
"""

import json
import os

PROJECT = "WILLOW LEAF"
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 캐릭터 — 고정 식별자(2~3개)를 매 프롬프트에 반복한다
# ---------------------------------------------------------------------------
CHAR = {
    "YUNA": ("Oh Yuna", "OH YUNA",
             "23-year-old Korean woman, low ponytail tied with a faded mint-green scrunchie, "
             "small beauty mark under her left eye, beige adhesive bandage on her right index finger; "
             "green-and-white striped convenience-store vest over a white T-shirt, black slacks, "
             "worn white canvas sneakers"),
    "YUNA_CHILD": ("young Yuna", "YOUNG YUNA",
                   "8-year-old Korean girl, two low pigtails with mint-green hair ties, "
                   "small beauty mark under her left eye; yellow T-shirt, denim overalls, pink rubber sandals"),
    "WANG_A": ("Wang Dohyun", "WANG DOHYUN - A",
               "78-year-old Korean man, cropped snow-white hair, thick white eyebrows, round tortoiseshell "
               "glasses, small pale scar on the right side of his chin; faded gray linen jacket over a "
               "wrinkled beige shirt, worn brown leather shoes"),
    "WANG_B": ("Wang Dohyun", "WANG DOHYUN - B",
               "78-year-old Korean man, cropped snow-white hair, thick white eyebrows, round tortoiseshell "
               "glasses, small pale scar on the right side of his chin; charcoal-navy three-piece suit, "
               "white shirt with no tie, small silver willow-leaf lapel pin, polished black shoes"),
    "KANG": ("Kang Taesik", "KANG TAESIK",
             "38-year-old Korean man, gel-slicked-back black hair, rectangular black-rimmed glasses, "
             "thick gold wristwatch on his left wrist; white short-sleeve dress shirt, navy tie, "
             "green-and-white striped convenience-store vest, gray slacks, black loafers"),
    "MALSUN_A": ("Grandma Malsun", "LEE MALSUN - A",
                 "65-year-old Korean woman, silver-streaked bob with a small pink hairpin on the right side, "
                 "deep smile lines, green jade ring on her left hand; faded floral cotton blouse, "
                 "dark baggy work pants"),
    "MALSUN_B": ("Grandma Malsun", "LEE MALSUN - B",
                 "80-year-old Korean woman, silver bob with a small pink hairpin on the right side, "
                 "deep smile lines, green jade ring on her left hand; light-blue hospital gown under a "
                 "cream knitted cardigan"),
    "KIM": ("Secretary Kim", "SECRETARY KIM",
            "52-year-old Korean man, neat side-parted black hair with silver temples, clear coiled "
            "earpiece in his right ear; black suit, white shirt, black tie, black leather folder"),
    "HAN": ("Director Han", "DIRECTOR HAN JIWON",
            "46-year-old Korean woman, sharp chin-length black bob, small pearl stud earrings; "
            "light-gray pantsuit, white blouse, black tablet in hand"),
}

LOC = {
    "L1": "LOCATION 01 - STORE EXTERIOR",
    "L2": "LOCATION 02 - STORE INTERIOR",
    "L3": "LOCATION 03 - WANSACHEON SPRING",
    "L4": "LOCATION 04 - HOSPITAL WARD",
    None: None,
}

NUM = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}

# ---------------------------------------------------------------------------
# 씬 — 스토리보드 시트의 스타일 블록 (조명 · 팔레트 · 장소)
# ---------------------------------------------------------------------------
SCENES = {
    "01": dict(title="COLD OPEN", act="콜드오픈", loc="L1",
               lighting="harsh 2 p.m. midsummer sunlight, bleached highlights, visible heat haze",
               palette="sun-bleached yellow-green and pale concrete, cool fluorescent spill from inside the store",
               setting="a small unbranded convenience store with a green-and-white facade on a quiet street in "
                       "Naju, South Korea, present day, August, 2 p.m.; a large weeping willow and a wooden bench "
                       "stand beside the glass entrance door"),
    "02": dict(title="FLASH FORWARD", act="콜드오픈", loc="L1",
               lighting="crisp bright morning daylight, high contrast, glossy reflections",
               palette="clean whites, glossy blacks, cold steel-blue shadows",
               setting="the same Naju convenience store three days later, 10 a.m., inspection day"),
    "03": dict(title="NIGHT SHIFT", act="1막 사연", loc=None,
               lighting="flat greenish kitchen fluorescent light, rising steam",
               palette="stainless steel gray, sickly green, one red accent from a rubber apron",
               setting="a cramped Korean restaurant kitchen at 11 p.m., a stainless sink piled with dishes"),
    "04": dict(title="WANSACHEON MEMORY", act="1막 사연", loc="L3",
               lighting="low summer dusk sun through willow leaves, soft halation, gentle film fade",
               palette="faded warm amber and honey-green, lifted blacks like an old family photo",
               setting="Wansacheon, a small stone-walled village spring shaded by old willows in Naju, "
                       "fifteen years ago, summer dusk"),
    "05": dict(title="THE BENCH", act="1막 사연", loc="L1",
               lighting="hot afternoon sunlight with dappled willow shade",
               palette="sun-bleached yellow-green with deep cool shade under the willow",
               setting="the wooden bench under the willow in front of the Naju convenience store, "
                       "the same August day, 2:20 p.m."),
    "06": dict(title="THE BACK OFFICE", act="2막 분노", loc="L2",
               lighting="cold overhead fluorescent tube light, harsh top-down shadows, a faint flicker",
               palette="sickly teal-green, dull gray, monitor-blue glow",
               setting="the cramped back office of the convenience store, the next morning, a CCTV monitor "
                       "on a cluttered desk"),
    "07": dict(title="THE BOTTLE", act="2막 분노", loc="L1",
               lighting="blue-hour dusk with warm sodium streetlight pools",
               palette="deep dusk blue against warm orange streetlight",
               setting="in front of the Naju convenience store at dusk the same day; a black sedan parked "
                       "across the street under a streetlight"),
    "08": dict(title="INSPECTION DAY", act="3막 반전", loc="L2",
               lighting="crisp bright morning daylight flooding through the glass front, high contrast",
               palette="clean whites, glossy blacks, a burgundy entrance mat as the only warm color",
               setting="the Naju convenience store three days later, 10 a.m., head-office inspection day"),
    "09": dict(title="THE LEAF", act="4막 눈물", loc="L2",
               lighting="soft diffused daylight through the shop windows, gentle falloff",
               palette="warm neutrals, soft cream and muted green",
               setting="inside the Naju convenience store, continuous from the inspection"),
    "10": dict(title="JUSTICE", act="5막 사이다", loc="L2",
               lighting="cool daylight that turns warmer and brighter as the scene resolves",
               palette="cool steel-blue shifting to warm clean daylight",
               setting="inside the Naju convenience store, continuous from the inspection"),
    "11": dict(title="THE WARD", act="6막 눈물", loc="L4",
               lighting="late-afternoon golden window light, soft warm backlight",
               palette="warm gold and soft white, pale mint hospital accents",
               setting="a six-bed hospital ward in Naju at late afternoon; the other beds hidden behind "
                       "drawn curtains; Grandma Malsun's bed is by the window"),
    "12": dict(title="WANSACHEON MORNING", act="6막 눈물", loc="L3",
               lighting="misty early-morning light, low sun breaking through willow branches",
               palette="soft green and pale gold, silver mist",
               setting="Wansacheon stone spring in Naju at dawn, the next morning"),
}

SEPIA = "desaturated sepia, soft vignette, dust in the air, 1960s poverty"


def C(scene, title, shot, people, scene_txt, move, speed, framing, end, dur,
      dlg="none", sound="", vo="", sub="", post="", panel="", caption="",
      hands=(), extra=None, palette=None, loc="default", wardrobe="", setting=None):
    """컷 하나. people = CHAR 키 목록, hands = 손/실루엣만 보이는 인물 키."""
    return dict(scene=scene, title=title, shot=shot, people=list(people), hands=list(hands),
                extra=extra, scene_txt=scene_txt, move=move, speed=speed, framing=framing, end=end,
                dur=dur, dlg=dlg, sound=sound, vo=vo, sub=sub, post=post, panel=panel,
                caption=caption, palette=palette, loc=loc, wardrobe=wardrobe, setting=setting)


HOLD = "hold the last 1 second completely still."

CUTS = [
    # ===================== 콜드오픈 =====================
    C("01", "폭염의 거리", "Long shot, establishing", [],
      "The empty street in front of the convenience store at 2 p.m. Heat shimmers above the asphalt. "
      "The willow's long branches hang motionless beside the glass door. Nothing moves.",
      "Static, locked off", "none",
      "Long shot; store front on the right third, willow on the left third, heat haze across the lower frame",
      "Holds the full composition for the entire shot; " + HOLD, 4,
      sound="Loud cicadas, a distant scooter, the drone of the store's outdoor AC unit",
      panel="Long shot of the heat-hazed street, willow beside the store", caption="2 p.m. heat"),
    C("01", "물 한 모금만", "Medium, low floor-level angle", ["WANG_A", "KANG"],
      "Just inside the glass entrance door. Wang Dohyun sits collapsed on the tile floor, sweat on his face, "
      "glasses askew, lifting one trembling hand upward. Kang Taesik stands over him, seen only from behind "
      "at the edge of frame, arms crossed.",
      "Handheld, fine natural tremor", "subtle, slow drift toward the reaching hand",
      "Floor-level eye line; Wang in medium shot, centered; Kang's back and crossed arm fill the left edge",
      "Settles on Wang's reaching hand and face; " + HOLD, 6,
      dlg='Wang Dohyun (Korean, cracked dry whisper): "물… 물 한 모금만…"',
      sound="Door chime stuttering as the automatic door half-opens, muffled cicadas, fridge hum",
      panel="Old man collapsed by the glass door, trembling hand raised; manager's back at frame edge",
      caption="Water... please", loc="L2"),
    C("01", "나가시라고요", "Medium, low angle", ["KANG", "WANG_A"],
      "Kang Taesik looks down at the old man with disgust and jabs his finger toward the door. Bright shelves "
      "of snacks and drinks behind him. Only Wang's white hair and shoulder are visible, blurred in the "
      "lower foreground.",
      "Static, locked off, low angle", "none",
      "Low angle, Kang in medium shot from the waist up; Wang's white hair out of focus in the lower-left "
      "foreground; keep Kang no closer than medium",
      "Kang's pointing arm fully extended toward the door; " + HOLD, 5,
      dlg='Kang Taesik (Korean, irritated, loud): "아, 진짜! 영감님, 돈 없으면 나가시라고요. 손님들 다 도망가잖아!"',
      sound="Fridge hum, door chime, a customer bell ringing somewhere",
      panel="Low angle: manager points at the door, old man's white hair in foreground", caption="Get out", loc="L2"),
    C("01", "쿵", "Insert, close-up", [],
      "Outside the glass door, an elderly man's wrinkled hand and faded gray linen sleeve slide down the "
      "sunlit glass after his shoulder bumps against it. The street is reflected in the glass.",
      "Static, locked off", "none",
      "Insert close-up of the hand pressed against the glass, reflections of the street across it",
      "The hand comes to rest at the bottom edge of frame; " + HOLD, 3,
      sound="A dull thud against glass, the door chime, cicadas swell",
      post="3막 CUT 41(돌리줌) 직후 0.5초 플래시컷으로 재사용",
      panel="Insert: wrinkled hand sliding down the sunlit glass door", caption="Thud",
      hands=["WANG_A"]),
    C("01", "종이컵", "Insert, macro close-up", [],
      "At the water dispenser beside the counter, a white paper cup fills with cold water. A young woman's "
      "hand holds it; a beige bandage wraps her right index finger. Her hand is shaking slightly with urgency.",
      "Static, locked off", "none",
      "Macro close-up, the cup and the bandaged finger centered, the dispenser spout at top of frame",
      "The cup is full and the water stops; " + HOLD, 3,
      sound="Dispenser gurgle, quick footsteps, the door chime behind",
      panel="Insert: paper cup filling at the dispenser, bandaged finger", caption="Cold water",
      hands=["YUNA"], loc="L2"),
    C("01", "버들가지", "Full shot, following", ["YUNA"],
      "Oh Yuna pushes out through the glass door into the blazing sun holding the paper cup, and without "
      "breaking stride reaches up to pluck a single leaf from a low willow branch.",
      "Follow shot, camera behind Yuna at shoulder height", "brisk walking pace",
      "Keep Yuna's back and ponytail with the mint-green scrunchie centered; willow branches enter from the top",
      "Stops as her fingers close on the leaf; " + HOLD, 5,
      sound="Door chime, cicadas loud outside, rustle of willow leaves",
      panel="Follow shot: Yuna rushes outside with the cup, plucks a willow leaf", caption="A willow leaf"),
    C("01", "버들잎 한 장", "Insert, macro close-up", [],
      "A single fresh willow leaf drops from a young woman's fingers onto the water in the paper cup and "
      "slowly spins on the surface. The bandaged index finger is visible.",
      "Static, locked off", "none",
      "Macro, looking slightly down into the cup; the leaf lands dead center",
      "The leaf stops spinning and floats still; " + HOLD, 4,
      sound="A tiny water tap, cicadas dip, a soft wind chime tone",
      panel="Macro: a willow leaf lands and spins on the water in the paper cup", caption="The leaf",
      hands=["YUNA"]),
    C("01", "천천히 드세요", "Medium two-shot", ["YUNA", "WANG_A"],
      "In the willow's shade, Oh Yuna kneels beside Wang Dohyun, who sits slumped against the wall. She holds "
      "the paper cup in both hands and guides it to his lips, the willow leaf floating on top.",
      "Slow dolly in toward the two of them", "very slow",
      "Two-shot, both faces visible in profile-three-quarter, the cup between them at the center",
      "Stops at a medium close two-shot as he takes the first sip; " + HOLD, 8,
      dlg='Oh Yuna (Korean, gentle, slightly breathless): "할아버지, 천천히 드세요. 급하게 드시다 체하시면 안 돼요."',
      sound="Cicadas, willow leaves rustling, a soft sip",
      panel="Yuna kneels in the willow shade, offering the cup to the old man", caption="Drink slowly"),
    C("01", "그 눈빛", "Close-up", ["WANG_A"],
      "Wang Dohyun holds the cup and looks down at the willow leaf floating in it. His eyes widen slightly "
      "behind his tortoiseshell glasses; something ancient stirs in his face.",
      "Rack focus from the leaf in the cup (foreground) to Wang's eyes, camera locked", "slow focus pull",
      "Close-up; the cup rim and leaf in the lower foreground, Wang's face behind",
      "Focus lands sharp on his eyes; " + HOLD, 5,
      sound="Cicadas fade down, a low sustained tone",
      panel="Rack focus from the leaf to the old man's widening eyes", caption="He knows this leaf"),
    C("02", "검은 차 세 대", "Wide, low angle", [],
      "Three glossy black sedans pull up one after another in front of the convenience store, their tinted "
      "windows reflecting the sky. No people are visible.",
      "Static, locked off, low angle near the asphalt", "none",
      "Low angle, wide; the cars fill the frame left to right, the store facade behind them",
      "The third car stops in frame; " + HOLD, 4,
      sound="Tires on asphalt, engines cutting off one by one, cicadas stop abruptly",
      post="자막 '사흘 뒤' 좌하단",
      panel="Low angle: three black sedans stopping in a row", caption="Three days later"),
    C("02", "굳어버린 얼굴", "Medium to medium close-up", ["KANG"],
      "Kang Taesik, tie tightened, rises from a deep 90-degree bow on a burgundy entrance mat. As his eyes land "
      "on someone off-screen, his eager smile collapses and the color drains from his face.",
      "Slow zoom in, camera locked", "slow",
      "Starts medium, ends medium close-up on Kang; the bright doorway behind him",
      "Stops on his frozen face; " + HOLD, 5,
      dlg='Kang Taesik (Korean, eager, then trailing off): "회, 회장님! 저희 점포는—"',
      sound="A high thin ringing tone swells and cuts out",
      post="마지막 프레임 흑백 정지 → 타이틀 '버들잎 한 장'",
      panel="Manager straightens from a bow, his smile freezing", caption="He recognizes him", loc="L2"),

    # ===================== 1막 · 사연 =====================
    C("03", "밤의 설거지", "Medium, profile", ["YUNA"],
      "A cramped restaurant kitchen at night. Oh Yuna scrubs a large pot at a stainless sink piled with dishes, "
      "sleeves rolled up, yellow rubber gloves on, steam rising. Exhausted but steady.",
      "Side tracking, camera moves parallel to the sink", "slow",
      "Medium; keep Yuna in profile and the dish pile between her and camera",
      "Stops on Yuna in clean profile; " + HOLD, 6,
      sound="Running water, clanking dishes, an extractor fan roaring",
      vo="스물세 살 오유나. 낮에는 편의점, 밤에는 식당 설거지를 한다.",
      panel="Yuna scrubbing pots at a steaming stainless sink at night", caption="Night shift",
      wardrobe="Wardrobe override for this cut: red rubber apron over her white T-shirt, no store vest."),
    C("03", "미납 안내", "Insert", [],
      "A smartphone lies on a wet shelf above the sink. The screen lights up with a notification bubble whose "
      "text is soft and unreadable. A yellow-gloved hand pauses in the blurred foreground.",
      "Rack focus from the gloved hand (foreground) to the phone screen, camera locked", "slow focus pull",
      "Insert; phone in the right half, gloved hand soft in the left foreground",
      "Focus settles on the glowing screen; " + HOLD, 4,
      sound="A short notification buzz under the running water",
      vo="병원에 계신 할머니의 입원비 때문이다.",
      sub="휴대폰 화면 합성: [나주OO병원] 입원비 미납 안내",
      panel="Insert: phone lights up with a notification beside the sink", caption="A hospital bill",
      hands=["YUNA"]),
    C("04", "할머니 손", "Full shot, rear follow", ["MALSUN_A", "YUNA_CHILD"],
      "Fifteen years ago. Grandma Malsun leads young Yuna by the hand along a stone path toward a small "
      "stone-walled spring shaded by old willows. Their long shadows stretch ahead.",
      "Follow shot, camera behind them at waist height", "slow walking pace",
      "Both backs centered, holding hands; the spring and willows ahead of them",
      "They stop at the spring's edge and the camera stops with them; " + HOLD, 6,
      sound="Evening cicadas, trickling spring water, a distant dog barking",
      vo="어릴 적 할머니는 유나의 손을 잡고 동네 샘터 '완사천'에 자주 갔다.",
      post="1막 회상 톤: 화면비 유지, 가장자리 비네팅",
      panel="Rear follow: grandma and little Yuna walk hand in hand to the spring", caption="Fifteen years ago"),
    C("04", "완사천 이야기", "Medium two-shot", ["MALSUN_A", "YUNA_CHILD"],
      "Grandma Malsun crouches at the spring and scoops water with a dried gourd dipper, then floats a willow "
      "leaf on it and turns to young Yuna, who crouches beside her listening wide-eyed.",
      "Slow dolly in toward the two of them", "very slow",
      "Two-shot at their crouched height, the spring water glinting between them",
      "Stops on a close two-shot as grandma speaks to Yuna; " + HOLD, 10,
      dlg='Grandma Malsun (Korean, warm storytelling, soft Jeolla dialect): "유나야, 옛날에 여기서 한 처녀가 목마른 장수한테 물을 떠 줬단다. 급하게 마시다 체할까 봐, 버들잎을 띄워서."',
      sound="Spring water trickling, willow leaves rustling, cicadas",
      panel="Grandma floats a willow leaf in a gourd dipper, telling the legend", caption="The legend"),
    C("04", "사람 도리", "Close-up", ["MALSUN_A"],
      "Grandma Malsun, close, smiling with deep smile lines, looking down at young Yuna who is just off-screen. "
      "Dusk light glows through the willow behind her.",
      "Static, locked off", "none",
      "Close-up, head and shoulders, willow leaves glowing in the soft background",
      "Holds on her gentle smile after the last word; " + HOLD, 9,
      dlg='Grandma Malsun (Korean, tender, firm on the last line): "그 장수가 나중에 고려를 세운 왕건이었어. 남 목마를 때 건네는 물 한 바가지, 그게 사람 도리다."',
      sound="Spring water, soft wind in the leaves",
      panel="Close-up: grandma's warm smile, glowing willows behind", caption="A person's duty"),
    C("04", "작은 손", "Insert", [],
      "A little girl's small hands hold the gourd dipper; a willow leaf floats on the water. She sips carefully, "
      "slowly, then lowers the dipper.",
      "Static, locked off", "none",
      "Insert; the dipper centered, the leaf visible on the water",
      "The dipper lowers out through the bottom of frame; " + HOLD, 4,
      sound="A soft sip, water dripping back into the spring",
      vo="그날 유나가 버들잎을 띄운 건, 할머니한테서 배운 습관이었다.",
      post="매치컷 → 다음 컷(노인의 손 + 종이컵) 같은 구도",
      panel="Insert: little hands holding a gourd dipper with a floating leaf", caption="A habit",
      hands=["YUNA_CHILD"]),
    C("05", "주름진 손", "Insert", [],
      "An old man's wrinkled, trembling hands hold the white paper cup; the willow leaf floats on the "
      "remaining water. Dappled willow shade moves across his fingers and gray linen cuffs.",
      "Static, locked off", "none",
      "Insert with the cup centered exactly like a match cut; hands filling the lower two-thirds",
      "The trembling slows; " + HOLD, 4,
      sound="Cicadas, the faint rustle of willow leaves",
      panel="Insert: wrinkled hands holding the paper cup with the leaf", caption="Match cut",
      hands=["WANG_A"]),
    C("05", "60년 만이구나", "Medium close-up", ["WANG_A"],
      "Wang Dohyun sits alone on the wooden bench under the willow, staring into the paper cup. His lips "
      "tremble. He whispers to himself.",
      "Slow dolly in toward Wang", "very slow",
      "Starts medium, ends medium close-up; willow branches frame the top edge",
      "Stops on his wet eyes behind the glasses; " + HOLD, 8,
      dlg='Wang Dohyun (Korean, whisper to himself, trembling): "…60년 만이구나."',
      sound="Cicadas recede, a low piano note",
      panel="Old man alone on the bench, whispering to the cup", caption="Sixty years"),
    C("05", "60년 전의 물", "Overhead insert", [],
      "Sixty years ago at the same stone spring, dusty and poor. A teenage girl's hands in a faded white cotton "
      "sleeve offer a gourd dipper of water with a willow leaf floating in it to a thin boy's dirt-streaked, "
      "trembling hands. Only hands and forearms are visible.",
      "Static overhead, straight down 90 degrees", "none",
      "Overhead; the dipper passing between the two pairs of hands at the center, stone edge of the spring below",
      "The boy's hands close around the dipper; " + HOLD, 6,
      sound="Muffled, distant cicadas, water dripping, wind",
      vo="왕도현 회장은 60년 전 나주에서 끼니를 굶던 소년이었다. 완사천에서 버들잎 띄운 물을 건넨 소녀가 있었는데, 그 소녀가 훗날 그의 아내가 됐다.",
      panel="Sepia overhead: a girl's hands give a boy's hands a dipper with a leaf", caption="Sixty years ago",
      extra=["a teenage girl seen only as hands and forearms", "a thin teenage boy seen only as hands and forearms"],
      palette=SEPIA, loc="L3",
      setting="Wansacheon, the stone-walled village spring in Naju, sixty years ago, a dusty summer afternoon"),
    C("05", "꺼진 휴대폰", "Insert", [],
      "An old man's thumb presses the power button of a black smartphone again and again. The screen stays "
      "completely dark, reflecting only the willow branches above.",
      "Static, locked off", "none",
      "Insert; the dark phone screen centered in his wrinkled hand, gray linen cuff at the edge",
      "The thumb stops pressing; " + HOLD, 4,
      sound="Dry clicks of the button, cicadas",
      vo="올해 아내를 떠나보낸 회장은 비서도 없이 혼자 고향 샘터를 찾았다가, 휴대폰이 꺼진 채 더위를 먹고 쓰러질 뻔했던 것이다.",
      panel="Insert: thumb pressing the button of a dead phone", caption="Dead phone",
      hands=["WANG_A"]),
    C("05", "홀로 벤치에", "Long shot, rising", ["WANG_A"],
      "Wang Dohyun sits alone on the bench under the great willow, the paper cup in his hands, the convenience "
      "store's sun-glared glass front behind him.",
      "Crane up, lens level", "slow",
      "Wang stays centered as he shrinks in frame; the willow canopy grows around him",
      "Stops high with Wang small under the willow; " + HOLD, 6,
      sound="Cicadas swell back up, a sustained string note",
      panel="Crane up: the old man small beneath the willow", caption="Alone"),

    # ===================== 2막 · 분노 =====================
    C("06", "CCTV", "Insert", [],
      "A CCTV monitor on a cluttered desk shows grainy black-and-white security footage of a young woman "
      "kneeling to give a cup to an old man outside. A man's finger with a thick gold wristwatch taps the "
      "screen twice.",
      "Static, locked off", "none",
      "Insert; the monitor fills the frame, the tapping finger enters from the right",
      "The finger rests on the screen; " + HOLD, 4,
      sound="Two hard taps on glass, the monitor's electrical hum",
      post="모니터 영상 속 인물은 화면 이미지일 뿐, 인원수 미포함",
      panel="Insert: gold-watch finger taps CCTV footage of the water scene", caption="Next morning",
      hands=["KANG"]),
    C("06", "이거 절도야", "Medium two-shot", ["KANG", "YUNA"],
      "Kang Taesik swivels in his office chair to face Oh Yuna, who stands stiffly by the office door holding "
      "her vest hem. He smirks.",
      "Static, locked off", "none",
      "Medium two-shot; Kang seated on the left, Yuna standing on the right, the monitor glow between them",
      "Holds on Kang's smirk and Yuna's stiff posture; " + HOLD, 7,
      dlg='Kang Taesik (Korean, smug, accusatory): "오유나 씨. 어제 생수 계산 안 하고 줬지? 이거 절도야, 절도."',
      sound="Fluorescent buzz, chair creak",
      panel="Manager in his chair accuses Yuna standing by the door", caption="It's theft"),
    C("06", "제 컵이고요", "Close-up", ["YUNA"],
      "Oh Yuna, bewildered, eyes darting, her voice small.",
      "Static, locked off", "none",
      "Close-up, head and shoulders, the office door frame behind her",
      "Holds on her lowered eyes; " + HOLD, 6,
      dlg='Oh Yuna (Korean, small, bewildered): "정수기 물이었어요. 제 컵이고요…"',
      sound="Fluorescent buzz",
      panel="Close-up: Yuna, bewildered", caption="It was my cup"),
    C("06", "책임질 거야?", "Medium, over-the-shoulder", ["KANG", "YUNA"],
      "Kang Taesik gets up and steps into Oh Yuna's space, jabbing his finger in the air. Camera sits behind "
      "Yuna's shoulder; only her ponytail with the mint-green scrunchie and shoulder are visible.",
      "Handheld, fine natural tremor", "restless",
      "Over Yuna's shoulder; Kang in a medium shot, never closer than medium",
      "Settles on Kang mid-gesture; " + HOLD, 10,
      dlg='Kang Taesik (Korean, rising anger): "컵은 공짜야? 이번 주에 본사 점검 나와. 나 이번에 직영점장 되는 거 걸려 있는데, 거지 영감 들락거리는 가게로 찍히면 책임질 거야?"',
      sound="Fluorescent buzz, his loafers scuffing the floor",
      panel="Over Yuna's shoulder: the manager leans in, jabbing his finger", caption="Will you take the blame?"),
    C("06", "시말서", "Insert", [],
      "A blank A4 form is slapped onto the desk; loose papers scatter. A man's hand with a thick gold "
      "wristwatch pulls away.",
      "Static, locked off", "none",
      "Insert, top-down angle on the desk surface",
      "Papers settle; " + HOLD, 3,
      sound="A sharp paper slap, papers sliding",
      sub="서류 합성: '시말서'",
      panel="Insert: a form slapped onto the desk", caption="Written apology",
      hands=["KANG"]),
    C("06", "10만 원", "Medium", ["KANG"],
      "Kang Taesik stands by the desk, pointing at the office door, looking down at someone off-screen.",
      "Static, locked off", "none",
      "Medium shot at eye level; the door in the background",
      "Holds as he lowers his arm; " + HOLD, 8,
      dlg='Kang Taesik (Korean, cold, final): "시말서 쓰고 이번 달 급여에서 10만 원 깎아. 싫으면 내일부터 나오지 말든가."',
      sound="Fluorescent buzz, a distant customer bell",
      panel="The manager points at the door", caption="100,000 won"),
    C("06", "병원비", "Insert", [],
      "A young woman's hand with a beige bandage on the right index finger holds a phone; the screen glows "
      "with a notification whose text is soft and unreadable.",
      "Static, locked off", "none",
      "Insert; the phone slightly below center, her vest's green stripes behind",
      "Her thumb tightens on the phone; " + HOLD, 4,
      sound="A muted vibration",
      sub="휴대폰 화면 합성: [나주OO병원] 입원비 미납 안내 (2회차)",
      panel="Insert: bandaged hand gripping a glowing phone", caption="The bill",
      hands=["YUNA"]),
    C("06", "쓰겠습니다", "Choker close-up", ["YUNA"],
      "Oh Yuna bites her lip, eyes glistening, refusing to cry. After a long breath she answers.",
      "Slow zoom in, camera locked", "very slow",
      "From close-up to choker: forehead cropped, eyes and mouth filling the frame",
      "Stops on her eyes as a tear almost falls; " + HOLD, 8,
      dlg='Oh Yuna (Korean, barely audible, swallowing tears): "…쓰겠습니다."',
      sound="Fluorescent buzz drops away to silence",
      panel="Choker: Yuna biting her lip, holding back tears", caption="I'll write it"),
    C("06", "혼자 쓰는 시말서", "Rear shot", ["YUNA"],
      "Oh Yuna sits hunched over the desk, writing on the form alone. The fluorescent tube above flickers.",
      "Static rear shot", "none",
      "Her back and mint-green scrunchie fill the center; the desk lamp and form beyond her",
      "Holds as the fluorescent light flickers once; " + HOLD, 6,
      sound="Pen scratching, fluorescent flicker tick",
      vo="물 한 잔 값으로, 10만 원이 깎였다.",
      panel="Rear shot: Yuna alone, writing at the desk", caption="Alone"),
    C("07", "생수 한 병", "Medium full", ["YUNA"],
      "Dusk. Oh Yuna crouches under the willow and places an unopened bottle of water on the wooden bench, "
      "then tapes a small folded paper note to it with handwriting too small to read.",
      "Side tracking, camera moves parallel to the bench", "slow",
      "Medium full; Yuna and the bench in profile, the glowing store behind",
      "Stops as she stands up and looks at the bottle; " + HOLD, 6,
      sound="Evening crickets, a passing car, willow leaves",
      vo="그래도 유나는 그날 저녁, 편의점 앞 버드나무 아래에 생수 한 병을 몰래 놓아두었다.",
      panel="Dusk: Yuna places a water bottle with a note on the bench", caption="For the thirsty"),
    C("07", "목마른 분 드세요", "Insert", [],
      "The water bottle on the bench with a small paper note taped to it, the note fluttering in the breeze. "
      "Willow branches sway above in the dusk.",
      "Static, locked off", "none",
      "Insert; bottle centered, the streetlight flare in the background",
      "The note settles; " + HOLD, 3,
      sound="Soft breeze, crickets",
      sub="쪽지 글씨 합성: '목마른 분 드세요.'",
      panel="Insert: bottle and fluttering note on the bench", caption="The note"),
    C("07", "검은 세단", "Wide", [],
      "Across the street, a black sedan is parked under a streetlight. Its rear window slowly slides down, "
      "revealing only the dark silhouette of an elderly man inside.",
      "Slow zoom in, camera locked", "slow",
      "Wide to medium-wide on the rear window of the car, the streetlight halo above",
      "Stops once the window is fully down; " + HOLD, 6,
      sound="The electric window motor, crickets",
      panel="A black sedan across the street, its rear window lowering", caption="Watching",
      hands=["WANG_B"]),
    C("07", "내가 직접 가지", "Medium two-shot, car interior", ["WANG_B", "KIM"],
      "Inside the dark sedan. Wang Dohyun in the back seat, now in his suit, looks out at the bench. Secretary "
      "Kim in the front passenger seat turns back toward him. Streetlight falls across their faces.",
      "Static, locked off", "none",
      "Two-shot; Wang in the right rear, Kim turned in the left front, the lit bench visible through the window",
      "Holds on Wang's resolved face after Kim answers; " + HOLD, 8,
      dlg='Wang Dohyun (Korean, low, resolute): "김 비서. 이 점포, 사흘 뒤 점검 일정에 넣게. 내가 직접 가지." / Secretary Kim (Korean, crisp): "알겠습니다, 회장님."',
      sound="Car interior hush, faint crickets outside",
      panel="Car interior: the chairman gives an order to Secretary Kim", caption="I'll go myself",
      loc=None),

    # ===================== 3막 · 반전 =====================
    C("08", "레드카펫", "Medium full", ["KANG"],
      "Kang Taesik unrolls a long burgundy mat at the entrance, then straightens his navy tie in the glass door's "
      "reflection with a satisfied grin.",
      "Side tracking, camera moves parallel to Kang", "steady",
      "Medium full; Kang and the mat in profile, the bright glass door beyond",
      "Stops on him adjusting his tie in the reflection; " + HOLD, 5,
      sound="The mat thumping flat, a pop song on the store radio",
      panel="Kang lays a burgundy mat and fixes his tie in the glass", caption="Inspection day"),
    C("08", "창고에만 있어", "Medium two-shot", ["KANG", "YUNA"],
      "Kang Taesik points Oh Yuna toward the stockroom door. She stands in the doorway, head bowed.",
      "Static, locked off", "none",
      "Medium two-shot; Kang on the left, Yuna in the stockroom doorway on the right",
      "Holds on Yuna lowering her head; " + HOLD, 6,
      dlg='Kang Taesik (Korean, curt, dismissive): "오유나, 오늘은 창고에만 있어. 얼굴 비치지 마."',
      sound="Store radio, fridge hum",
      panel="Kang orders Yuna into the stockroom", caption="Stay out of sight"),
    C("08", "닫히는 문", "Insert", [],
      "The stockroom door swings shut; a young woman's hand with a beige bandage on the index finger lets go "
      "of the handle.",
      "Static, locked off", "none",
      "Insert on the door handle and the narrowing gap",
      "The door clicks shut; " + HOLD, 3,
      sound="A soft latch click",
      panel="Insert: the stockroom door closes", caption="Click",
      hands=["YUNA"]),
    C("08", "구두", "Insert, low angle", [],
      "A car door opens and a polished black shoe with a charcoal-navy trouser hem steps down onto sunlit asphalt.",
      "Static, locked off, low angle near the ground", "none",
      "Insert at ground level; the shoe lands center frame, the black car door edge above",
      "The second foot joins the first; " + HOLD, 3,
      sound="A car door opening, a firm footstep",
      panel="Insert: polished shoe steps onto the asphalt", caption="He arrives",
      hands=["WANG_B"], loc="L1",
      setting="the sunlit asphalt in front of the Naju convenience store, inspection day, 10 a.m."),
    C("08", "회장님!", "Wide", ["KANG", "HAN", "KIM", "WANG_B"],
      "The automatic glass door slides open. Director Han and Secretary Kim enter first, then Wang Dohyun, "
      "backlit so his face is in silhouette against the sun. Kang Taesik bows a deep 90 degrees on the "
      "burgundy mat.",
      "Static, locked off", "none",
      "Wide from behind the counter; the entrance centered, Kang bowing in the foreground right",
      "Holds with Kang still bowed and the three standing before him; " + HOLD, 8,
      dlg='Kang Taesik (Korean, over-eager, loud): "회, 회장님! 나주점 매니저 강태식입니다! 저희 점포는 고객 응대 만족도가—"',
      sound="Door slide, door chime, the store radio clicks off",
      panel="Wide: executives enter, the chairman backlit; Kang bows deeply", caption="Chairman!"),
    C("08", "그 얼굴", "Medium", ["KANG"],
      "Kang Taesik lifts his head from the bow and recognizes the face in front of him. He goes rigid; "
      "his glasses slide slightly down his nose.",
      "Dolly zoom: camera pulls back while the lens zooms in, subject size constant, background stretches",
      "slow and steady",
      "Medium; Kang stays the same size while the store shelves behind him stretch away",
      "Stops at maximum background stretch; " + HOLD, 5,
      sound="A high ringing tone, the world muffles",
      post="이 영화의 돌리줌은 이 컷 1회만. 직후 CUT 04 0.5초 플래시컷",
      panel="Dolly zoom: Kang recognizes the old man", caption="That face"),
    C("08", "응대를 참 잘하시더군", "Close-up, low angle", ["WANG_B"],
      "Wang Dohyun looks at Kang with calm, unreadable eyes, the willow-leaf lapel pin catching the light.",
      "Slow dolly in toward Wang, low angle", "very slow",
      "Low angle close-up; the bright shop ceiling behind his white hair",
      "Stops tight on his calm eyes; " + HOLD, 8,
      dlg='Wang Dohyun (Korean, quiet, dry): "고객 응대라… 사흘 전에도 응대를 참 잘하시더군."',
      sound="Silence under the fridge hum",
      panel="Low angle close-up: the chairman, calm and cold", caption="Great service"),
    C("08", "…네?", "Medium", ["KANG"],
      "Kang Taesik, a bead of sweat running down his temple, swallows hard.",
      "Static, locked off", "none",
      "Medium; Kang slightly left of center, the burgundy mat under his feet",
      "Holds on his frozen mouth; " + HOLD, 4,
      dlg='Kang Taesik (Korean, a dry croak): "…네?"',
      sound="A hard swallow, fridge hum",
      panel="Kang sweating, speechless", caption="...Sorry?"),
    C("08", "그 아가씨 어디 있소", "Medium", ["WANG_B", "HAN", "KIM"],
      "Wang Dohyun turns away from Kang and scans the store, Director Han and Secretary Kim flanking him a step "
      "behind.",
      "Arc shot, camera circles Wang 30 degrees", "slow",
      "Medium; Wang centered, Han and Kim soft behind his shoulders",
      "Stops with Wang looking toward the stockroom door; " + HOLD, 8,
      dlg='Wang Dohyun (Korean, clear, carrying): "여기 버들잎 띄워서 물 주던 아가씨, 어디 있소?"',
      sound="Footsteps on tile, fridge hum",
      panel="Arc: the chairman scans the store for the girl", caption="Where is she?"),
    C("08", "정적", "Wide, high angle", ["KANG", "WANG_B", "HAN", "KIM"],
      "Nobody moves. Kang stands frozen on the burgundy mat; Wang, Han and Kim stand in the aisle.",
      "Static, locked off, high angle from a ceiling corner like a security camera", "none",
      "High angle wide of the whole shop floor, all four small in frame",
      "Holds the stillness for the entire shot; " + HOLD, 5,
      sound="Only the refrigerator motor humming",
      panel="High angle: four figures frozen in silence", caption="Silence"),

    # ===================== 4막 · 눈물 =====================
    C("09", "창고 문", "Medium", ["WANG_B", "YUNA"],
      "The stockroom door opens and Oh Yuna steps out, wiping her hands on her vest. Wang Dohyun's shoulder "
      "and white hair are soft in the foreground.",
      "Rack focus from Wang's shoulder in the foreground to Yuna in the doorway, camera locked", "slow focus pull",
      "Wang's shoulder in the left foreground, Yuna medium in the doorway on the right",
      "Focus lands on Yuna's surprised face; " + HOLD, 6,
      sound="Door creak, fridge hum",
      panel="Rack focus: Yuna steps out of the stockroom", caption="She appears"),
    C("09", "괜찮으세요?", "Medium close-up, walking", ["YUNA"],
      "Oh Yuna walks toward him, eyes widening in recognition, worry — not awe — on her face.",
      "Reverse tracking, camera retreats ahead of Yuna", "slow walking pace",
      "Medium close-up; Yuna centered, the aisle shelves sliding past behind her",
      "Stops as she stops; " + HOLD, 8,
      dlg='Oh Yuna (Korean, worried, gentle): "할아버지…? 괜찮으세요? 그날 많이 어지러워 보이셨는데…"',
      sound="Soft footsteps, a first low piano note",
      panel="Reverse tracking: Yuna walks up, worried", caption="Are you okay?"),
    C("09", "미소", "Close-up", ["WANG_B"],
      "Wang Dohyun's eyes soften behind his tortoiseshell glasses. The faintest smile.",
      "Static, locked off", "none",
      "Close-up, head and shoulders",
      "Holds on the smile; " + HOLD, 5,
      sound="Piano sustain",
      vo="회장님이냐고 묻지 않았다. 몸이 괜찮냐고 물었다.",
      panel="Close-up: the chairman's eyes soften", caption="A smile"),
    C("09", "누구한테 배웠소", "Over-the-shoulder", ["YUNA", "WANG_B"],
      "Over Oh Yuna's shoulder toward Wang Dohyun, who studies her face.",
      "Static, locked off", "none",
      "Over Yuna's shoulder (ponytail and mint-green scrunchie visible), Wang in medium close-up",
      "Holds after his question; " + HOLD, 6,
      dlg='Wang Dohyun (Korean, gentle, searching): "아가씨. 그 버들잎, 누구한테 배웠소?"',
      sound="Fridge hum, piano",
      panel="OTS: the chairman asks who taught her", caption="Who taught you?"),
    C("09", "할머니가요", "Over-the-shoulder", ["WANG_B", "YUNA"],
      "Reverse angle over Wang Dohyun's shoulder onto Oh Yuna, who smiles shyly as she remembers.",
      "Static, locked off", "none",
      "Over Wang's shoulder (white hair visible), Yuna in medium close-up",
      "Holds on her small smile; " + HOLD, 9,
      dlg='Oh Yuna (Korean, soft, remembering): "할머니가요. 완사천 이야기 해주시면서… 목마른 사람한테 물을 줄 땐, 체하지 않게 천천히 주라고요."',
      sound="Piano",
      panel="OTS: Yuna answers, remembering her grandmother", caption="My grandmother"),
    C("09", "낡은 수첩", "Insert", [],
      "An old man's hand draws a worn brown leather notebook from his suit's inner pocket and opens it: "
      "a yellowed, pressed willow leaf lies between the pages.",
      "Slow dolly in toward the notebook", "very slow",
      "Insert; the notebook in his hands, the pressed leaf ending dead center",
      "Stops on the pressed leaf; " + HOLD, 5,
      sound="Leather creak, a page turning",
      panel="Insert: an old notebook with a pressed willow leaf", caption="Sixty-year-old leaf",
      hands=["WANG_B"]),
    C("09", "평생 그 사람 덕에", "Close-up", ["WANG_B"],
      "Wang Dohyun looks down at the pressed leaf, then up at Yuna, his voice thickening.",
      "Slow dolly in toward Wang", "very slow",
      "Close-up to tighter close-up",
      "Stops on his wet eyes; " + HOLD, 10,
      dlg='Wang Dohyun (Korean, voice thickening): "60년 전, 굶어 쓰러진 나한테 똑같이 물을 준 소녀가 있었소. 평생 그 사람 덕에 살았지."',
      sound="Piano, strings enter softly",
      panel="Close-up: the chairman remembers the girl", caption="She saved me"),
    C("09", "먼저 갔소", "Choker close-up", ["WANG_B"],
      "Wang Dohyun, tears welling behind his glasses, trying to keep his voice steady.",
      "Static, locked off", "none",
      "Choker: forehead cropped, eyes and mouth fill the frame",
      "Holds as a tear falls; " + HOLD, 9,
      dlg='Wang Dohyun (Korean, breaking): "올봄에 먼저 갔소. 그래서 샘터에 인사하러 왔다가… 그날, 다시 그 사람을 만난 줄 알았다오."',
      sound="Piano and strings",
      post="BGM: 잔잔한 피아노 메인 테마 여기서 풀버전",
      panel="Choker: tears behind the glasses", caption="She's gone"),
    C("09", "눈물 한 방울", "Insert, macro", [],
      "A single tear drops onto the pressed willow leaf in the open notebook.",
      "Static, locked off", "none",
      "Macro on the leaf",
      "The tear soaks into the page; " + HOLD, 3,
      sound="A tiny drop, piano",
      panel="Macro: a tear falls on the pressed leaf", caption="A tear",
      hands=["WANG_B"]),
    C("09", "꼭 해드릴게요", "Close-up", ["YUNA"],
      "Oh Yuna, eyes brimming, holds back her tears and nods.",
      "Slow zoom in, camera locked", "very slow",
      "Close-up, ends slightly tighter",
      "Stops on her nod; " + HOLD, 9,
      dlg='Oh Yuna (Korean, holding back tears): "…할머니도 지금 병원에 계세요. 그 얘기, 할머니한테 꼭 해드릴게요."',
      sound="Piano",
      panel="Close-up: Yuna, holding back tears", caption="I'll tell her"),
    C("09", "지켜보는 등", "Rear shot", ["KANG", "YUNA", "WANG_B"],
      "Kang Taesik stands by the counter watching, his back to the camera, shoulders sinking. Beyond him, "
      "out of focus, Yuna and Wang face each other.",
      "Static rear shot", "none",
      "Kang's back and slicked hair fill the left half; Yuna and Wang soft in the right background",
      "Holds as his shoulders drop; " + HOLD, 5,
      sound="Piano fades out",
      panel="Rear shot: Kang watches from behind, shoulders sinking", caption="He watches"),

    # ===================== 5막 · 사이다 =====================
    C("10", "김 비서, CCTV", "Medium", ["WANG_B", "KIM", "HAN"],
      "Without turning around, Wang Dohyun speaks. Secretary Kim steps forward and Director Han raises her tablet.",
      "Static, locked off", "none",
      "Medium; Wang centered, Kim and Han entering from behind his shoulders",
      "Holds as Han turns the tablet screen outward; " + HOLD, 4,
      dlg='Wang Dohyun (Korean, flat, commanding): "김 비서, CCTV."',
      sound="Fridge hum, footsteps",
      panel="The chairman calls for the CCTV", caption="Show the CCTV"),
    C("10", "재생", "Insert", [],
      "A black tablet in a woman's hands plays grainy security footage: a manager shoving an old man out through "
      "a glass door.",
      "Static, locked off", "none",
      "Insert; the tablet screen fills the frame, her pearl earring barely visible at the top edge",
      "The footage reaches the push; " + HOLD, 5,
      sound="Tinny playback audio: the shove, a thud",
      post="태블릿 속 인물은 화면 이미지일 뿐, 인원수 미포함",
      panel="Insert: tablet replaying the shove", caption="The footage",
      hands=["HAN"]),
    C("10", "핏기", "Medium", ["KANG"],
      "Kang Taesik watches the footage; the color drains from his face.",
      "Slow zoom in, camera locked", "slow",
      "Medium to medium close-up (no closer)",
      "Stops as he takes a half-step back; " + HOLD, 4,
      sound="The playback's thud echoing",
      panel="Kang watches, blood draining from his face", caption="Caught"),
    C("10", "허위보고?", "Medium, low angle", ["WANG_B"],
      "Wang Dohyun faces Kang, standing very still, lapel pin gleaming.",
      "Static, locked off, low angle", "none",
      "Low angle medium; the bright ceiling behind him",
      "Holds after the last word; " + HOLD, 10,
      dlg='Wang Dohyun (Korean, measured, cutting): "물 한 잔을 절도라고 했다지. 그럼 자네가 본사에 올린 \'고객 불만 제로\' 보고서는 뭐라고 불러야 하나? 허위보고?"',
      sound="Fridge hum",
      panel="Low angle: the chairman confronts the manager", caption="A false report?"),
    C("10", "오해입니다", "Medium", ["KANG"],
      "Kang Taesik steps forward with pleading hands, glasses crooked.",
      "Handheld, fine natural tremor", "agitated",
      "Medium; Kang centered, never closer than medium",
      "Freezes as he is cut off mid-word; " + HOLD, 7,
      dlg='Kang Taesik (Korean, panicked, pleading): "회장님, 그건 오해입니다! 제가 그 노인이 회장님인 줄 알았으면—"',
      sound="Scuffing loafers",
      panel="Kang pleads with open hands", caption="If I'd known—"),
    C("10", "옷으로 재는 사람", "Close-up", ["WANG_B"],
      "Wang Dohyun cuts him off, calm and steady, every word landing.",
      "Slow dolly in toward Wang", "very slow",
      "Medium close-up to close-up",
      "Stops tight on his steady eyes; " + HOLD, 10,
      dlg='Wang Dohyun (Korean, calm, steely): "그게 문제라는 거요. 알았으면 무릎 꿇고, 몰랐으면 문밖으로 밀어내고. 사람을 옷으로 재는 사람한테 가게를 맡길 순 없소."',
      sound="A low drum hit under the last line",
      panel="Close-up: the chairman delivers the verdict", caption="Judged by clothes"),
    C("10", "감사팀 조사", "Over-the-shoulder", ["KANG", "HAN"],
      "Director Han steps forward and addresses Kang Taesik, tablet held against her chest. Kang's back and "
      "slicked hair are in the foreground.",
      "Static, locked off", "none",
      "Over Kang's shoulder; Han in medium close-up",
      "Holds after her last word; " + HOLD, 9,
      dlg='Director Han (Korean, crisp, official): "강태식 씨. 직영점장 승진 취소, 부당 급여 공제 건으로 감사팀 조사 들어갑니다. 오늘부로 업무에서 빠지세요."',
      sound="Fridge hum",
      panel="OTS: Director Han announces the audit", caption="Audit"),
    C("10", "돌려드리겠습니다", "Medium two-shot", ["HAN", "YUNA"],
      "Director Han turns to Oh Yuna with a slight bow of respect. Yuna, startled, bows back deeply.",
      "Static, locked off", "none",
      "Medium two-shot; Han on the left, Yuna on the right",
      "Holds on Yuna's deep bow; " + HOLD, 6,
      dlg='Director Han (Korean, warm, respectful): "오유나 씨. 공제된 급여는 오늘 바로 돌려드리겠습니다."',
      sound="Fridge hum, a soft rising string",
      panel="Director Han bows to Yuna; Yuna bows back", caption="Refunded"),
    C("10", "명찰", "Insert", [],
      "A man's trembling fingers unclip a name badge from a green-and-white striped vest; a thick gold wristwatch "
      "on the wrist.",
      "Static, locked off", "none",
      "Insert on the badge and the trembling fingers",
      "The badge comes free; " + HOLD, 4,
      sound="A small plastic clip snapping",
      panel="Insert: trembling fingers remove the name badge", caption="Badge off",
      hands=["KANG"]),
    C("10", "레드카펫 위로", "Rear shot", ["KANG"],
      "Kang Taesik walks away from camera across the burgundy mat he laid himself and out through the glass door "
      "into the glaring sun.",
      "Static rear shot", "none",
      "Kang's back centered, shrinking as he walks toward the bright doorway",
      "Holds after he disappears into the glare; " + HOLD, 7,
      sound="Door chime, cicadas rushing in, then fading",
      panel="Rear shot: Kang walks out over his own mat", caption="Exit"),
    C("10", "반짝이는 생수병", "Insert", [],
      "Outside under the willow, the water bottle Yuna left on the bench glints in the sunlight, the paper note "
      "stirring in the breeze.",
      "Static, locked off", "none",
      "Insert; the bottle centered, sun flare through the willow leaves",
      "A glint of sunlight on the bottle; " + HOLD, 4,
      sound="Cicadas, willow leaves, a clear chime",
      panel="Insert: the water bottle glinting under the willow", caption="Still there",
      loc="L1", setting="the wooden bench under the willow outside the Naju convenience store, late morning"),

    # ===================== 6막 · 눈물 =====================
    C("11", "6인실", "Wide, establishing", ["MALSUN_B", "WANG_B", "YUNA"],
      "Late afternoon. Grandma Malsun sits up in her bed by the window. Wang Dohyun sits in a chair beside her "
      "with a fruit basket on the side table; Oh Yuna stands at the foot of the bed. The other beds are hidden "
      "behind drawn curtains.",
      "Static, locked off", "none",
      "Wide; the window on the right glowing gold, the three figures in a triangle",
      "Holds the composition; " + HOLD, 5,
      sound="A distant hospital PA chime, a monitor beep, soft traffic outside",
      panel="Wide: hospital ward, chairman at grandma's bedside, Yuna at the foot", caption="That evening"),
    C("11", "빚 갚는 겁니다", "Medium two-shot", ["WANG_B", "MALSUN_B"],
      "Wang Dohyun leans toward Grandma Malsun and speaks with deep respect.",
      "Slow dolly in toward the two of them", "very slow",
      "Two-shot, Wang on the left, Malsun on the right, window glow between them",
      "Stops on a close two-shot; " + HOLD, 9,
      dlg='Wang Dohyun (Korean, humble, sincere): "손녀를 참 잘 키우셨습니다. 병원비는 나래복지재단에서 맡겠습니다. 이건 보답이 아니라, 빚 갚는 겁니다."',
      sound="Monitor beep, soft piano",
      panel="Two-shot: the chairman speaks to grandma with respect", caption="Repaying a debt"),
    C("11", "무슨", "Medium close-up", ["MALSUN_B", "WANG_B"],
      "Grandma Malsun takes his hand in both of hers and smiles faintly, embarrassed. Only Wang's hand and suit "
      "sleeve are visible.",
      "Static, locked off", "none",
      "Medium close-up on Malsun; Wang's hand held in hers in the lower frame",
      "Holds on her faint smile; " + HOLD, 6,
      dlg='Grandma Malsun (Korean, soft Jeolla dialect, bashful): "물 한 잔 준 걸 가지고… 무슨."',
      sound="Monitor beep",
      panel="Grandma holds the chairman's hand, smiling", caption="Just a cup of water"),
    C("11", "빛바랜 사진", "Insert", [],
      "The old leather notebook lies open on the blanket: the pressed willow leaf and a small faded black-and-white "
      "photo of a teenage girl standing by a stone spring. An old woman's finger with a green jade ring touches "
      "the photo.",
      "Static, locked off", "none",
      "Insert, slightly top-down; the photo and leaf centered on the blanket",
      "The finger stops on the girl's face in the photo; " + HOLD, 4,
      sound="Piano pauses",
      panel="Insert: pressed leaf and an old photo; grandma's jade-ringed finger", caption="The photo",
      hands=["MALSUN_B"]),
    C("11", "순임이 아니오?", "Close-up", ["MALSUN_B"],
      "Grandma Malsun stares at the photo, her voice trembling with recognition.",
      "Slow zoom in, camera locked", "very slow",
      "Close-up to tighter close-up",
      "Stops on her trembling lips; " + HOLD, 8,
      dlg='Grandma Malsun (Korean, trembling, Jeolla dialect): "…이 사람, 순임이 아니오? 버들잎 띄우는 거, 내가 어릴 적에 순임이한테 배웠는디…"',
      sound="Silence, a single high piano note",
      panel="Close-up: grandma recognizes the girl in the photo", caption="Sunim?"),
    C("11", "제 집사람입니다", "Choker close-up", ["WANG_B"],
      "Wang Dohyun freezes, stunned, then his face breaks and tears run behind his glasses.",
      "Static, locked off", "none",
      "Choker: forehead cropped, eyes and mouth fill the frame",
      "Holds on his tears; " + HOLD, 7,
      dlg='Wang Dohyun (Korean, a whisper that breaks): "…제 집사람입니다."',
      sound="Strings swell",
      panel="Choker: the chairman breaks into tears", caption="My wife"),
    C("11", "입을 막는 손", "Close-up", ["YUNA"],
      "Oh Yuna covers her mouth with her bandaged hand, tears spilling over.",
      "Static, locked off", "none",
      "Close-up, window glow rim-lighting her hair",
      "Holds on her tears; " + HOLD, 4,
      sound="Strings",
      panel="Close-up: Yuna covers her mouth, crying", caption="It came full circle"),
    C("11", "세 사람의 물", "Medium two-shot", ["WANG_B", "MALSUN_B"],
      "Wang Dohyun holds Grandma Malsun's hand in both of his, head bowed, then looks up at her.",
      "Static, locked off", "none",
      "Medium two-shot; their joined hands in the center of the frame",
      "Holds on their joined hands; " + HOLD, 8,
      dlg='Wang Dohyun (Korean, gentle, through tears): "물 한 잔이 사람을 살립니다. 저는 그걸… 두 번이나 겪었고요."',
      sound="Piano theme returns",
      panel="Two-shot: joined hands, the chairman through tears", caption="Water saves people"),
    C("11", "창가의 버들잎", "Medium, profile", ["YUNA"],
      "Oh Yuna places a fresh willow leaf on the windowsill; golden light rims her profile.",
      "Static, locked off", "none",
      "Medium in profile, the window filling the background with gold",
      "Holds as she takes her hand away from the leaf; " + HOLD, 5,
      sound="Soft wind outside, piano",
      panel="Yuna sets a willow leaf on the golden windowsill", caption="A leaf on the sill"),
    C("11", "버들잎 장학금", "Over-the-shoulder", ["YUNA", "WANG_B"],
      "Over Oh Yuna's shoulder, Wang Dohyun turns to her from his chair with a warm, hopeful look.",
      "Static, locked off", "none",
      "Over Yuna's shoulder (mint-green scrunchie visible), Wang in medium close-up",
      "Holds after his question; " + HOLD, 9,
      dlg='Wang Dohyun (Korean, warm, hopeful): "유나 양. 우리 재단에 \'버들잎 장학금\'이라는 걸 만들 생각이오. 첫 번째 수혜자가 돼 주겠소?"',
      sound="Piano",
      panel="OTS: the chairman offers Yuna the scholarship", caption="Willow Leaf Scholarship"),
    C("11", "…네", "Choker close-up", ["YUNA"],
      "Oh Yuna bursts into tears and nods, laughing and crying at once.",
      "Handheld, fine natural tremor", "subtle",
      "Choker, golden backlight flaring at the edge",
      "Holds on her tear-streaked smile; " + HOLD, 6,
      dlg='Oh Yuna (Korean, crying): "…네."',
      sound="Piano and strings peak",
      panel="Choker: Yuna cries and nods", caption="Yes"),
    C("12", "두 장의 버들잎", "Overhead", [],
      "Two willow leaves float side by side on the clear surface of the stone spring and drift slowly together "
      "through thin morning mist.",
      "Static overhead, straight down 90 degrees", "none",
      "Overhead; the two leaves enter from the top and drift to the center",
      "The leaves drift to the center; " + HOLD, 6,
      sound="Trickling spring water, early birds",
      vo="천 년 전 한 처녀가 버들잎 하나로 왕을 얻었다고 한다. 하지만 이 이야기에서 버들잎이 알려주는 건 다른 거다.",
      panel="Overhead: two willow leaves drifting side by side on the spring", caption="Next morning"),
    C("12", "완사천", "Extreme long shot, rising", ["YUNA", "WANG_B"],
      "Oh Yuna and Wang Dohyun stand side by side at the edge of the stone spring, seen from behind, under the "
      "old willows in the morning mist.",
      "Drone pullback, up and back", "slow and smooth",
      "The two backs stay centered as the spring, the willows and the town of Naju open up around them",
      "Stops high with the spring and willows filling the frame and the two figures tiny; " + HOLD, 10,
      sound="Birdsong, spring water, the piano theme's final chord",
      vo="누군가 목말라 보이면, 이름도 옷차림도 묻지 말고 물 한 잔 건넬 것. 급하게 마시다 체하지 않도록, 천천히.",
      post="끝 → 블랙 + 고지 자막",
      panel="Drone pullback: Yuna and the chairman at the spring, the town opening up", caption="Slowly"),
]


# ---------------------------------------------------------------------------
# 빌더
# ---------------------------------------------------------------------------
def palette_of(cut):
    return cut["palette"] or SCENES[cut["scene"]]["palette"]


def loc_of(cut):
    return SCENES[cut["scene"]]["loc"] if cut["loc"] == "default" else cut["loc"]


def people_in_frame(cut):
    names, sheets = [], []
    for k in cut["people"] + cut["hands"]:
        name = CHAR[k][0]
        if k in cut["hands"]:
            name += " (seen only as hands/silhouette, no face)"
        names.append(name)
        if CHAR[k][1] not in sheets:
            sheets.append(CHAR[k][1])
    for e in cut["extra"] or []:
        names.append(e)
    return names, sheets


def lock_block(cut):
    names, sheets = people_in_frame(cut)
    n = len(names)
    parts = []
    if sheets:
        parts.append(f"Use the reference character sheet(s) for face and wardrobe only: {', '.join(sheets)}.")
    loc = LOC[loc_of(cut)]
    if loc:
        parts.append(f"Use the reference location sheet {loc} for the space only.")
    parts.append("Do not remove the background.")
    if n == 0:
        parts.append("Exactly zero people in frame: no humans, no faces, no silhouettes.")
    else:
        word = "person" if n == 1 else "people"
        parts.append(f"Exactly {NUM[n]} {word} in frame: {'; '.join(names)}. No other people, no duplicates, "
                     f"no background extras.")
    parts.append(f"Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, {palette_of(cut)}.")
    parts.append("No blood, no gore.")
    return " ".join(parts)


def scene_block(cut):
    s = SCENES[cut["scene"]]
    setting = (cut["setting"] or s["setting"]).rstrip(".")
    txt = f"{setting[0].upper()}{setting[1:]}. {cut['scene_txt']}"
    ids = [f"{CHAR[k][0]}: {CHAR[k][2]}" for k in cut["people"] + cut["hands"]]
    if ids:
        txt += " Fixed identifiers — " + " | ".join(ids) + "."
    if cut["wardrobe"]:
        txt += " " + cut["wardrobe"]
    if cut["palette"] == SEPIA:
        txt += " This is a sepia flashback set sixty years in the past."
    return txt


def cut_prompt(cut):
    lines = [
        f"[LOCK] {lock_block(cut)}",
        f"[SCENE] {scene_block(cut)}",
        "[CAMERA]",
        f"Movement: {cut['move']}",
        f"Speed: {cut['speed']}",
        f"Framing: {cut['framing']}",
        f"End: {cut['end']}",
        f"[DURATION] {cut['dur']} seconds",
        f"[DIALOGUE] {cut['dlg']}",
        f"[SOUND] {cut['sound']}",
    ]
    if cut["post"]:
        lines.append(f"Post note: {cut['post']}")
    return "\n".join(lines)


def tc(sec):
    return f"{sec // 60}:{sec % 60:02d}"


def sheet_groups():
    """씬별 컷을 5패널 이하 시트로 나눈다 (01-A, 01-B …)."""
    groups = []
    for key in SCENES:
        cuts = [c for c in CUTS if c["scene"] == key]
        chunks = [cuts[i:i + 5] for i in range(0, len(cuts), 5)]
        for i, chunk in enumerate(chunks):
            suffix = f"-{chr(65 + i)}" if len(chunks) > 1 else ""
            groups.append((f"{key}{suffix}", key, chunk))
    return groups


def storyboard_prompt(sheet_id, key, chunk):
    s = SCENES[key]
    n = len(chunk)
    grid = (f"exactly {NUM[n]} numbered panels in a 3x2 grid"
            + (("; cell 5 is plain black and empty" if n == 4 else f"; cells {n + 1} to 5 are plain black and empty")
               if n < 5 else ""))
    chars = []
    for c in chunk:
        for k in c["people"] + c["hands"]:
            if k not in chars:
                chars.append(k)
    char_txt = " ".join(f"{CHAR[k][0][0].upper()}{CHAR[k][0][1:]} is {'an' if CHAR[k][2][0] in '8aeiou' else 'a'} {CHAR[k][2]}." for k in chars)
    out = [
        f"Cinematic storyboard contact sheet, one single image containing {grid}; the 6th cell is a black card "
        f"with the white title text \"{PROJECT} - SCENE {sheet_id} {s['title']}\". Each panel has a small white "
        f"label in its top-left corner showing the cut number and duration (e.g. \"CUT 1 - 5s\") and a one-line "
        f"caption below it. Photorealistic live-action, Kodak 35mm film grain, {s['lighting']}, {s['palette']}, "
        f"16:9 panels. Setting: {s['setting']}. {char_txt} Use the reference character sheets for faces and "
        f"wardrobe only. No blood, no gore.",
    ]
    for i, c in enumerate(chunk, 1):
        extra = " (sepia flashback panel)" if c["palette"] == SEPIA else ""
        out.append(f"Panel {i} — CUT {c['n']} - {c['dur']}s — {c['shot']}: {c['panel']}{extra}. "
                   f"Caption: {c['caption']}.")
    return "\n".join(out)


def build():
    for i, c in enumerate(CUTS, 1):
        c["n"] = i

    # 03 storyboards
    sb = ["# 03 · 스토리보드 콘택트시트 — 버들잎 한 장", "",
          "> 한 장 = 한 씬, 패널 하나 = 컷 하나. 패널 5개 초과 씬은 -A/-B로 나눔.",
          "> 스타일 블록은 시트마다 전부 포함(공통 블록 분리 금지). 이 파일은 `build_prompts.py`가 생성.", ""]
    for sheet_id, key, chunk in sheet_groups():
        s = SCENES[key]
        cut_range = f"CUT {chunk[0]['n']:02d}–{chunk[-1]['n']:02d}"
        sb += [f"## SCENE {sheet_id} · {s['title']} ({s['act']} · {cut_range})", "", "```",
               storyboard_prompt(sheet_id, key, chunk), "```", ""]
    write("03_storyboards.md", sb)

    # 04 cut prompts
    cp = ["# 04 · 컷 프롬프트 — 버들잎 한 장 (Seedance 2.0)", "",
          f"> 총 {len(CUTS)}컷 · 컷당 1개 · 블록 고정: LOCK / SCENE / CAMERA / DURATION / DIALOGUE / SOUND.",
          "> 코드 블록 안만 그대로 붙여넣기. VO·자막은 블록 밖 '편집' 줄에만 있고 프롬프트에 들어가지 않음.",
          "> 이 파일은 `build_prompts.py`가 생성 — 수정은 스크립트의 CUTS 데이터에서.", ""]
    current = None
    for c in CUTS:
        s = SCENES[c["scene"]]
        if s["act"] != current:
            current = s["act"]
            cp += [f"## {current}", ""]
        cp += [f"### CUT {c['n']:02d} · {c['dur']}s · {c['title']} — {c['shot']}", "", "```", cut_prompt(c), "```"]
        edit = []
        if c["vo"]:
            edit.append(f"VO: {c['vo']}")
        if c["sub"]:
            edit.append(f"자막/합성: {c['sub']}")
        if edit:
            cp.append("편집 — " + " · ".join(edit))
        cp.append("")
    write("04_cut_prompts.md", cp)

    # 05 timeline
    tl = ["# 05 · 편집 타임라인 — 버들잎 한 장", "",
          "> 컷 길이 합산 타임코드. 타이틀·고지 카드는 편집 전용(생성 없음). VO·자막·BGM은 여기서만 얹는다.", "",
          "| 컷 | IN | OUT | 길이 | 막 | 내용 | VO / 자막 / 편집 |", "|---|---|---|---|---|---|---|"]
    t = 0
    act_ranges = {}
    for c in CUTS:
        act = SCENES[c["scene"]]["act"]
        start = t
        t += c["dur"]
        act_ranges.setdefault(act, [start, t])[1] = t
        notes = " / ".join(x for x in [f"VO: {c['vo']}" if c["vo"] else "",
                                       f"자막: {c['sub']}" if c["sub"] else "", c["post"]] if x)
        tl.append(f"| {c['n']:02d} | {tc(start)} | {tc(t)} | {c['dur']}s | {act} | {c['title']} | {notes} |")
        if c["n"] == 11:
            tl.append(f"| — | {tc(t)} | {tc(t + 3)} | 3s | 콜드오픈 | **타이틀 카드** | 블랙 + 타이틀 '버들잎 한 장' (1막은 콜드오픈과 같은 날 밤으로 복귀) |")
            t += 3
    tl.append(f"| — | {tc(t)} | {tc(t + 5)} | 5s | 엔딩 | **고지 카드** | 본 영상은 나주 완사천 설화를 모티브로 재구성한 "
              f"창작물이며, 등장하는 인물·기업은 실제와 무관합니다. |")
    t += 5
    tl += ["", f"**총 러닝타임: {tc(t)}** (생성 {sum(c['dur'] for c in CUTS)}초 + 카드 8초)", "",
           "## 막별 구간", "", "| 막 | 구간 |", "|---|---|"]
    for act, (a, b) in act_ranges.items():
        tl.append(f"| {act} | {tc(a)} ~ {tc(b)} |")
    write("05_edit_timeline.md", tl)

    with open(os.path.join(HERE, "cuts.json"), "w", encoding="utf-8") as f:
        json.dump([dict(n=c["n"], scene=c["scene"], act=SCENES[c["scene"]]["act"], title=c["title"],
                        duration=c["dur"], prompt=cut_prompt(c), vo=c["vo"], subtitle=c["sub"])
                   for c in CUTS], f, ensure_ascii=False, indent=2)
    print(f"{len(CUTS)} cuts, {len(sheet_groups())} storyboard sheets, runtime {tc(t)}")


def write(name, lines):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    build()
