#!/usr/bin/env python3
"""경비원 김씨의 비밀 (EP1) — 제작 자산 생성기 (기준 초상 image-to-video 판).

대본: docs/대본-경비원김씨의비밀.md (콜드 오픈 A안 + 감동 강화 2고, 사용자 확정)
build_full_assets.py 의 beat 정렬 방식에 기준 초상 refs 연결을 추가했다.

생성 파일:
    scripts/scenes/guard-kim-secret.json  (16:9, 장면별 5/10초, refs=기준 초상)
    subs/guard-kim-secret.ass
    scripts/audio/guard-kim-secret.json

사용법: python3 scripts/build_guard_kim_assets.py
"""

import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = "assets/portraits"

# 확정 기준 초상 (사용자 선택)
REF_KIM = f"{P}/guard-kim-secret-cap2/kim-gold-1.png"
REF_KIM_BACK_WALK = f"{P}/guard-kim-secret-views3/kim-back-new-1.png"
REF_KIM_BACK_NEAR = f"{P}/guard-kim-secret-views3/kim-back-new-2.png"
REF_PARK = f"{P}/guard-kim-secret-views/parkyeosa-2.png"
REF_PARK_BACK = f"{P}/guard-kim-secret-views2/parkyeosa-back-1.png"
REF_JIWOO = f"{P}/guard-kim-secret/jiwoo-1.png"
REF_JIWOO_BACK = f"{P}/guard-kim-secret-views/jiwoo-back-1.png"
REF_MOM = f"{P}/guard-kim-secret/jiwoo-mom-1.png"
REF_MOM_BACK = f"{P}/guard-kim-secret-views2/jiwoo-mom-back-2.png"

# 인물 고정 문구 (모든 장면 동일 반복)
KIM = ("68세 한국 남성 아파트 경비원 김씨(흰머리 섞인 짧은 머리, 온화하지만 무뚝뚝한 표정, "
       "짙은 회색 무지 경비원 제복, 금색 장식 문양이 있는 남색 경비원 정모, 가슴 왼쪽에 금색 명찰)")
PARK = "55세 한국 여성 입주민 대표 박여사(짧은 갈색 파마머리, 민트색 무지 니트 카디건, 진주 목걸이)"
JIWOO = ("10살 한국 초등학생 여자아이 지우(어깨까지 오는 검은 생머리, 노란 머리핀, "
         "분홍색 무지 패딩 점퍼, 하늘색 무지 책가방)")
MOM = "38세 한국 여성 지우 엄마(하나로 묶은 검은 머리, 갈색 무지 코트, 어깨에 검은 가방)"

APT = "아무 글자도 없는 깨끗한 한국 아파트 단지"
GATE = f"{APT}의 경비실 앞"
BOARD = f"{APT}의 게시판 앞(게시물 글자는 보이지 않게 흐릿하게)"
ALLEY = "밤의 어두운 아파트 단지 골목길, 가로등 불빛, 간판이나 글자 없음"
ROOM = "아파트 관리동 회의실(아무 글자 없는 벽), 긴 테이블과 접이식 의자"
SNOWGATE = f"눈이 펑펑 내리는 {APT} 학원 건물 앞(간판 글자 없음)"

TALK = ("카메라를 향해 대사에 맞춰 입을 자연스럽게 움직이며 한국어로 말하는 "
        "정면 상반신 샷, 화면에는 말하는 사람 한 명만 등장")
MUTE = "아무도 입을 움직이거나 말하지 않는 장면"

STYLE = ("시네마틱 한국 드라마, 실사 영화 화질, 동일한 인물과 의상과 장소를 모든 장면에서 유지, "
         "자연스러운 피부 질감, 16:9 와이드 가로 구도, 말하는 입 모양은 한국어(영어 없음), "
         "화면 속 옷·간판·소품·배경에는 글자나 로고가 보이지 않게(김씨의 금색 명찰만 예외)")

N, C, A = "Naration", "Caption", "Action"
K, PY, JW, MM = "Kim", "Park", "Jiwoo", "Mom"

# 중앙 타이틀/엔딩 카드용 인라인 태그
TITLE_TAG = r"{\an5\pos(960,470)\fnNoto Serif CJK KR\fs84\b1\fsp9\c&HD8F0FA&\3c&H120A05&\bord2\shad2\4c&H96000000&\blur0.4\fad(600,600)}"
END_TAG = r"{\an5\pos(960,470)\fnNoto Serif CJK KR\fs64\b1\fsp7\c&HD8F0FA&\3c&H120A05&\bord2\shad2\4c&H96000000&\blur0.4\fad(1200,1500)}"

SECTIONS = [
    dict(
        name="콜드 오픈",
        ambience="night wind, distant city hum, single footsteps on pavement",
        narration_shots=[
            (f"{BOARD}, 종이 한 장을 게시판에 붙이는 여성의 손 클로즈업(종이는 백지, 글자 없음), "
             f"차가운 아침 조명, {MUTE}", []),
            (f"밤의 {APT} 전경, 가로등만 켜진 어두운 단지, 서늘한 분위기, {MUTE}", []),
        ],
        speaker_shots={
            MM: [(f"{APT} 관리동 복도, {MOM}이 겁에 질린 떨리는 표정으로 두 손을 모으고 {TALK}", [REF_MOM])],
        },
        lines=[
            (A, "10", f"CCTV 화질의 어두운 밤 골목, {JIWOO}가 혼자 걷고 열 걸음 뒤에서 짙은 제복의 남자 "
                      f"실루엣이 따라 걷는 장면, 서늘한 푸른 조명, 화면에는 정확히 두 명만 등장, {MUTE}",
             [REF_JIWOO_BACK]),
            (MM, "", "밤마다… 어떤 남자가 우리 애 뒤를 따라다녀요. 어제도 봤어요. 경비 아저씨 같던데…!", "fearful"),
            (C, "", "그 남자는, 경비원 김씨였다", None),
            (C, "", TITLE_TAG + "경비원 김씨의 비밀", None),
        ],
    ),
    dict(
        name="1막 — 사흘 전",
        ambience="quiet morning birds, distant door closing",
        narration_shots=[
            (f"아침의 {APT} 전경, 평화로운 등굣길 풍경, 사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
            (f"{BOARD}, 게시판을 물끄러미 바라보다 눈을 내리깔고 지나가는 {KIM}의 옆모습, {MUTE}", [REF_KIM]),
        ],
        speaker_shots={
            PY: [(f"{APT} 놀이터 앞, {PARK}이 짜증난 표정으로 팔짱을 낀 채 {TALK}", [REF_PARK]),
                 (f"{APT} 놀이터 앞, {PARK}이 굳은 얼굴로 종이(백지)를 꺼내 들며 {TALK}", [REF_PARK])],
            K: [(f"{GATE}, {KIM}가 무표정하게 택배 상자(무지)를 내밀며 {TALK}", [REF_KIM]),
                (f"{GATE}, {KIM}가 무뚝뚝한 얼굴로 짧게 {TALK}", [REF_KIM])],
            JW: [(f"아침 등굣길 {GATE}, {JIWOO}가 씩씩하게 손을 흔들며 {TALK}", [REF_JIWOO])],
        },
        lines=[
            (C, "", "사흘 전", None),
            (A, "5", f"아침 햇살의 {APT} 전경, 사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
            (A, "10", f"아침의 {GATE}, 주민이 인사해도 고개만 살짝 까딱하는 {KIM}, 무표정, {MUTE}", [REF_KIM]),
            (PY, "", "아니, 좀 웃으면서 주시면 어디 덧나요?", "angry"),
            (K, "", "…택배요, 1502호.", None),
            (JW, "", "아저씨! 학교 다녀오겠습니다!", "happy"),
            (K, "", "…차 조심해라.", None),
            (A, "5", f"아침 등굣길, 뛰어가는 {JIWOO}의 뒷모습을 잠시 바라보다 고개를 돌리는 {KIM}, "
                     f"화면에는 정확히 두 명만 등장, {MUTE}", [REF_KIM, REF_JIWOO_BACK]),
            (PY, "", "세상에… 애들 다니는 단지에서…! 이건 그냥 넘어갈 일이 아니에요! 서명 받겠습니다!", "angry"),
            (C, "", "'경비원 교체' 서명, 사흘 만에 서른두 세대", None),
        ],
    ),
    dict(
        name="2막 — 김씨의 밤",
        ambience="night wind, snow crunch footsteps, distant dog bark",
        narration_shots=[
            (f"{ALLEY}, {KIM}가 경비실 책상에서 낡은 꽃무늬 수첩을 덮고 갈피의 오래된 사진을 "
             f"손끝으로 쓸어보는 클로즈업(수첩과 사진에 글자 없음), 따뜻한 스탠드 조명, {MUTE}", [REF_KIM]),
            (f"밤의 경비실 창가, {KIM}가 창밖으로 내리기 시작하는 눈을 말없이 올려다보는 옆모습, "
             f"혼자 단독 인물 샷, {MUTE}", [REF_KIM]),
        ],
        speaker_shots={},
        lines=[
            (C, "", "같은 날, 밤 10시", None),
            (A, "10", f"{ALLEY}, {JIWOO}가 혼자 걷고 열 걸음 뒤에서 {KIM}가 말없이 따라 걷는 장면, "
                      f"콜드 오픈과 같은 구도지만 따뜻한 주황빛 가로등 조명, 화면에는 정확히 두 명만 등장, {MUTE}",
             [REF_JIWOO_BACK, REF_KIM_BACK_WALK]),
            (A, "10", f"{ALLEY}, 아파트 현관에 불이 켜질 때까지 화단 옆에 서서 지켜보는 {KIM}, "
                      f"하얀 입김, 안도한 듯 돌아서는 걸음, 혼자 단독 인물 샷, {MUTE}", [REF_KIM]),
            (A, "10", f"새벽의 {APT} 빙판길, {KIM}가 굽은 허리로 길에 소금을 뿌리는 장면, "
                      f"혼자 단독 인물 샷, {MUTE}", [REF_KIM]),
            (A, "5", f"밤의 {APT}, 사다리에 올라 깜빡이는 가로등 전구를 갈아 끼우는 {KIM}, "
                     f"혼자 단독 인물 샷, {MUTE}", [REF_KIM]),
            (A, "10", f"{ALLEY}, 폐지 리어카를 미는 백발 할머니 뒤를 {KIM}가 말없이 밀어주는 장면, "
                      f"할머니가 돌아보면 이미 저만치 걸어가는 {KIM}, 화면에는 정확히 두 명만 등장, {MUTE}",
             [REF_KIM_BACK_WALK]),
            (C, "", "그는 7년째, 매일 밤 이 길을 걸었다", None),
            (A, "10", f"눈이 내리기 시작하는 다른 날 밤의 {ALLEY}, {JIWOO}가 혼자 걷고 열 걸음 뒤에서 "
                      f"{KIM}가 우산을 든 채 말없이 따라 걷는 장면, 화면에는 정확히 두 명만 등장, {MUTE}",
             [REF_JIWOO_BACK, REF_KIM_BACK_WALK]),
        ],
    ),
    dict(
        name="3막 — 폭설의 밤",
        ambience="heavy snowfall wind, muffled snow footsteps",
        narration_shots=[
            (f"경비실 책상 위, 금색 명찰을 풀어 천천히 내려놓는 {KIM}의 주름진 손 클로즈업, "
             f"명찰의 금색이 스탠드 불빛에 반짝인다, {MUTE}", [REF_KIM]),
        ],
        speaker_shots={
            MM: [(f"퇴근길 거리(간판 글자 없음), {MOM}이 휴대폰을 귀에 대고 다급한 표정으로 {TALK}", [REF_MOM]),
                 (f"{APT} 현관 앞, 눈을 맞으며 달려온 {MOM}이 놀란 얼굴로 {TALK}", [REF_MOM])],
            K: [(f"{SNOWGATE}, 눈이 쌓인 검은 우산을 든 {KIM}가 온화한 표정으로 {TALK}", [REF_KIM]),
                (f"{APT} 현관 앞, 어깨에 눈이 쌓인 {KIM}가 담담한 표정으로 {TALK}", [REF_KIM])],
            JW: [(f"{SNOWGATE}, {JIWOO}가 반가움에 울 것 같은 표정으로 {TALK}", [REF_JIWOO])],
        },
        lines=[
            (C, "", "해고 통보를 받은 날, 폭설", None),
            (A, "10", f"경비실 책상 위, 금색 명찰을 풀어 천천히 내려놓는 {KIM}의 주름진 손 클로즈업, "
                      f"떨리는 손끝, {MUTE}", [REF_KIM]),
            (A, "5", f"경비실 창가, 짐 가방을 옆에 둔 {KIM}가 창밖의 폭설을 말없이 바라보는 옆모습, "
                     f"혼자 단독 인물 샷, {MUTE}", [REF_KIM]),
            (MM, "", "지우야, 엄마가 눈 때문에 차가 막혀서… 학원 앞에서 꼼짝 말고 있어! 알았지?!", "fearful"),
            (A, "10", f"{SNOWGATE}, {JIWOO}가 혼자 발을 동동거리며 눈 속에 서 있는 장면, "
                      f"점점 굵어지는 눈발, 혼자 단독 인물 샷, {MUTE}", [REF_JIWOO]),
            (A, "10", f"{SNOWGATE}, 눈보라 속에서 검은 우산을 쓰고 천천히 걸어오는 {KIM}의 모습, "
                      f"혼자 단독 인물 샷, {MUTE}", [REF_KIM]),
            (JW, "", "…아저씨!", "happy"),
            (K, "", "…춥다. 가자.", None),
            (A, "10", f"눈보라 치는 {APT} 길, {KIM}가 자신의 외투를 벗어 {JIWOO}에게 씌워주고 "
                      f"나란히 걷는 장면, 화면에는 정확히 두 명만 등장, {MUTE}", [REF_KIM, REF_JIWOO]),
            (A, "5", f"눈보라 속 클로즈업, {KIM}가 우산을 {JIWOO} 쪽으로 기울여 자신의 어깨에는 "
                     f"눈이 쌓이는 장면, 화면에는 정확히 두 명만 등장, {MUTE}", [REF_KIM, REF_JIWOO]),
            (MM, "", "…아저씨가, 왜…", "surprised"),
            (K, "", "…별거 아닙니다. 들어가십시오.", None),
            (A, "5", f"{APT} 현관 앞, {MOM}이 지우를 끌어안은 채 멀어지는 방향을 흔들리는 눈으로 "
                     f"바라보는 장면, 화면에는 정확히 두 명만 등장, {MUTE}", [REF_MOM, REF_JIWOO]),
            (A, "10", f"눈 내리는 {APT} 길을 혼자 돌아가는 {KIM}의 뒷모습, 어깨에 쌓인 눈, "
                      f"멀어지는 걸음, 혼자 단독 인물 샷, {MUTE}", [REF_KIM_BACK_WALK]),
            (A, "5", f"불이 꺼진 빈 경비실, 책상 위 금색 명찰만 남아 있는 클로즈업, "
                     f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
        ],
    ),
    dict(
        name="4막 — 진실",
        ambience="",
        narration_shots=[
            (f"{ROOM}, 낡은 꽃무늬 수첩이 긴 테이블 위에 조용히 놓이는 클로즈업(수첩에 글자 없음), {MUTE}", []),
        ],
        speaker_shots={
            JW: [(f"{ROOM}, {JIWOO}가 숨을 헐떡이며 눈물이 그렁그렁한 채 소리치는 {TALK}", [REF_JIWOO]),
                 (f"{ROOM}, {JIWOO}가 울면서 주먹을 꼭 쥐고 {TALK}", [REF_JIWOO])],
            MM: [(f"{ROOM}, {MOM}이 자리에서 일어나지 못한 채 떨리는 손으로 입을 가리고 {TALK}", [REF_MOM]),
                 (f"{ROOM}, {MOM}이 눈물을 쏟으며 무너지는 목소리로 {TALK}", [REF_MOM])],
            PY: [(f"{ROOM}, {PARK}이 수첩을 넘기다 멈추고 떨리는 목소리로 {TALK}", [REF_PARK]),
                 (f"{ROOM}, {PARK}이 눈시울이 붉어진 채 결심한 표정으로 {TALK}", [REF_PARK])],
            K: [(f"{ROOM} 뒤편, {KIM}가 모자를 벗어 손에 들고 낮고 떨리는 목소리로 {TALK}", [REF_KIM]),
                (f"{ROOM}, {KIM}가 눈물을 참으며 먼 곳을 바라보다 카메라를 향해 {TALK}", [REF_KIM])],
        },
        lines=[
            (C, "", "다음 날, 주민 회의", None),
            (A, "5", f"{ROOM}의 문이 벌컥 열리고 {JIWOO}가 숨을 헐떡이며 뛰어 들어오는 장면, "
                     f"혼자 단독 인물 샷, {MUTE}", [REF_JIWOO]),
            (JW, "", "아저씨 자르지 마세요!! 그 수상한 사람… 저 지켜준 거란 말이에요!!", "sad"),
            (JW, "", "무서워서 뛰어가면 같이 빨리 걸어주고… 넘어진 데는 다음 날 미끄럽지 않게 돼 있고… "
                     "제가 다 봤단 말이에요…!", "sad"),
            (MM, "", "…그럼 그 밤마다 봤다는 남자가… 내가… 내가 신고한 그 사람이…", "sad"),
            (MM, "", "우리 애를 지켜준 사람을… 내 손으로 쫓아낸 거예요…?", "sad"),
            (A, "5", f"{ROOM}, 낡은 꽃무늬 수첩이 긴 테이블 위에 조용히 놓이는 클로즈업, {MUTE}", []),
            (PY, "", "이 앞장은… 글씨가 다르네요. 302호 할머니 무릎이 안 좋음, 언덕길 조심… 이건 여자 글씨인데…", "sad"),
            (K, "", "…집사람 겁니다. 7년 전에 먼저 갔습니다.", None),
            (PY, "", "…이걸, 7년을 혼자 하신 거예요? 왜, 왜 말을 안 하셨어요…!", "sad"),
            (K, "", "…별거 아닙니다.", None),
            (K, "", "평생 온 동네 애들 챙기던 사람인데… 마지막에 그럽디다. 여보, 나 없어도… 밤길에 애들 좀 봐줘요.", "sad"),
            (K, "", "세상이 그래도 따뜻하다는 걸… 애들이 알아야 하잖아요. …그 사람이, 그랬습니다.", "sad"),
            (A, "10", f"아련한 세피아빛 회상, 비 오는 옛 골목에서 꽃무늬 카디건을 입은 여성이 "
                      f"아이들에게 우산을 씌워주는 뒷모습(얼굴은 보이지 않음), 따뜻한 역광, {MUTE}", []),
            (PY, "", "이 서명, 없던 걸로 하겠습니다. 대신 제가 새 서명을 받겠어요. 김영곤 님, 계속 계셔 주세요로요…!", "sad"),
            (A, "5", f"{ROOM}, {PARK}이 서명지(백지)를 천천히 반으로 접는 손 클로즈업, {MUTE}", [REF_PARK]),
            (MM, "", "죄송해요… 정말 죄송해요…", "sad"),
            (K, "", "…애 지키려고 하신 일인데요. 잘하신 겁니다.", None),
            (A, "10", f"{ROOM}, {JIWOO}가 {KIM}에게 달려가 허리를 끌어안고, {KIM}가 놀란 손을 "
                      f"허공에 들었다가 천천히 아이의 머리를 쓰다듬는 장면, 화면에는 정확히 두 명만 등장, "
                      f"{MUTE}", [REF_KIM, REF_JIWOO]),
        ],
    ),
    dict(
        name="5막 — 결말",
        ambience="bright winter morning birds, gentle breeze",
        narration_shots=[
            (f"{BOARD}, 색색의 종이 쪽지가 빼곡히 붙은 게시판(쪽지는 원경으로 흐릿, 글자 안 보임), "
             f"따뜻한 아침 햇살, {MUTE}", []),
            (f"아침 햇살이 퍼지는 {APT} 위의 맑은 겨울 하늘, 지붕의 눈이 녹아 반짝이는 풍경, "
             f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
        ],
        speaker_shots={
            JW: [(f"아침 등굣길 {APT} 정문 앞, {JIWOO}가 환하게 웃으며 손을 내밀고 {TALK}", [REF_JIWOO])],
            K: [(f"아침 등굣길 {APT} 정문 앞, {KIM}가 처음으로 옅은 미소를 지으며 {TALK}", [REF_KIM]),
                (f"{GATE}, {KIM}가 보온병을 두 손으로 받으며 고개를 살짝 숙이고 {TALK}", [REF_KIM])],
            PY: [(f"{GATE}, {PARK}이 보온병을 내밀며 처음으로 환하게 웃는 얼굴로 {TALK}", [REF_PARK])],
        },
        lines=[
            (C, "", "일주일 뒤", None),
            (A, "10", f"{BOARD}, 색색의 종이 쪽지가 빼곡히 붙은 게시판, 따뜻한 아침 햇살, "
                      f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
            (PY, "", "…유자차예요. 앞으로도, 잘 부탁드립니다.", None),
            (K, "", "…고맙습니다.", None),
            (A, "10", f"경비실 책상 위, 제자리에 돌아온 금색 명찰과 낡은 꽃무늬 수첩과 새 수첩 한 권이 "
                      f"나란히 놓인 클로즈업, 아침 햇살, {MUTE}", []),
            (JW, "", "아저씨! 오늘은 제가 데려다줄게요! 같이 가요!", "happy"),
            (K, "", "…허허. 그래, 가자.", "happy"),
            (A, "10", f"아침 햇살의 {APT} 길, {KIM}와 {JIWOO}가 손을 잡고 나란히 걸어가는 뒷모습, "
                      f"녹기 시작한 눈, 화면에는 정확히 두 명만 등장, {MUTE}",
             [REF_KIM_BACK_WALK, REF_JIWOO_BACK]),
            (C, "", END_TAG + r"말이 없던 그 사람은,\N매일 밤 사랑을 지키고 있었다", None),
        ],
    ),
]

CHAR_RATE = 5.5
LINE_PAD = 0.4
MIN_DUR = 1.2
CAPTION_MIN = 2.4
BEAT_LEAD = 0.4
BEAT_TAIL = 0.6


def line_duration(style, text):
    plain = re.sub(r"\{[^}]*\}", "", text)
    chars = len(re.sub(r"\s", "", plain.replace("\\N", " ")))
    dur = max(MIN_DUR, chars / CHAR_RATE + LINE_PAD)
    return max(dur, CAPTION_MIN) if style == C else dur


def beat_scene_sizes(need):
    sizes = [10] * int(need // 10)
    rem = need - 10 * len(sizes)
    if rem > 5:
        sizes.append(10)
    elif rem > 0.01 or not sizes:
        sizes.append(5)
    return sizes


def build_beats(lines):
    beats = []
    for style, name, text, *rest in lines:
        if style == A:
            beats.append({"key": "ACT", "size": int(name), "prompt": text,
                          "refs": rest[0] if rest else []})
            continue
        emotion = rest[0] if rest else None
        key = "N" if style in (N, C) else style
        if beats and beats[-1].get("key") == key and "lines" in beats[-1]:
            beats[-1]["lines"].append((style, name, text, emotion))
        else:
            beats.append({"key": key, "lines": [(style, name, text, emotion)]})
    return beats


def fmt_time(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ASS_HEADER = """[Script Info]
Title: 경비원 김씨의 비밀 자막
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Naration,Noto Sans CJK KR,52,&H00D2EEF5,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,4,2,2,200,200,85,1
Style: Caption,Noto Sans CJK KR,46,&H00E8E8E8,&H000000FF,&H00000000,&H96000000,-1,-1,0,0,100,100,0,0,1,4,2,8,200,200,70,1
Style: Kim,Noto Sans CJK KR,60,&H00B8E8FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Park,Noto Sans CJK KR,60,&H00C8B8F0,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Jiwoo,Noto Sans CJK KR,60,&H0090EE90,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Mom,Noto Sans CJK KR,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    events, scene_items, ambience_prompts, emotions = [], [], [], {}
    t_video, tts_no = 0.0, 0

    for sec in SECTIONS:
        sec_start = t_video
        narr_idx = 0
        spk_idx = {}
        n_lines = sum(1 for l in sec["lines"] if l[0] != A)

        for beat in build_beats(sec["lines"]):
            if beat["key"] == "ACT":
                item = {"prompt": beat["prompt"], "duration": beat["size"]}
                if beat["refs"]:
                    item["refs"] = beat["refs"]
                scene_items.append(item)
                ambience_prompts.append(sec["ambience"])
                t_video += beat["size"]
                continue

            t = t_video + BEAT_LEAD
            for style, name, text, emotion in beat["lines"]:
                if style != C:
                    tts_no += 1
                    if emotion:
                        emotions[str(tts_no)] = emotion
                dur = line_duration(style, text)
                events.append((t, t + dur - 0.1, style, name, text))
                t += dur
            need = (t - t_video) + BEAT_TAIL

            key = beat["key"]
            shots = sec["narration_shots"] if key == "N" else sec["speaker_shots"][key]
            for size in beat_scene_sizes(need):
                if key == "N":
                    prompt, refs = shots[narr_idx % len(shots)]
                    narr_idx += 1
                else:
                    k = spk_idx.get(key, 0)
                    prompt, refs = shots[k % len(shots)]
                    spk_idx[key] = k + 1
                item = {"prompt": prompt, "duration": size}
                if refs:
                    item["refs"] = refs
                scene_items.append(item)
                ambience_prompts.append(sec["ambience"])
                t_video += size

        print(f"{sec['name']}: 발화 {n_lines}줄 → {t_video - sec_start:.0f}초")

    total = t_video
    n5 = sum(1 for s in scene_items if s["duration"] == 5)
    n10 = len(scene_items) - n5
    print(f"\n합계: 자막 {len(events)}줄(TTS {tts_no}줄), 장면 {len(scene_items)}개 "
          f"(5초 {n5} + 10초 {n10}), 영상 {total:.0f}초 ({total / 60:.1f}분)")

    with open(os.path.join(ROOT, "subs", "guard-kim-secret.ass"), "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, style, name, text in events:
            f.write(f"Dialogue: 0,{fmt_time(s)},{fmt_time(e)},{style},{name},0,0,0,,{text}\n")

    with open(os.path.join(ROOT, "scripts", "scenes", "guard-kim-secret.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": 10, "ratio": "16:9", "style": STYLE, "scenes": scene_items},
                  f, ensure_ascii=False, indent=2)

    audio = {
        "tts_model": "fal-ai/minimax/speech-02-hd",
        "language_boost": "Korean",
        "speed": 1.0,
        "default_voice": "Imposing_Manner",
        "style_voices": {"Kim": "Imposing_Manner", "Park": "Wise_Woman",
                         "Jiwoo": "Lively_Girl", "Mom": "Calm_Woman"},
        "style_emotions": {"Kim": "neutral", "Park": "neutral",
                           "Jiwoo": "neutral", "Mom": "neutral"},
        "emotion_overrides": emotions,
        "scene_durations": [s["duration"] for s in scene_items],
        "narration_styles": [],
        "silent_styles": ["Caption"],
        "lipsync_models": ["fal-ai/latentsync", "fal-ai/sync-lipsync"],
        "ambience_model": "fal-ai/mmaudio-v2",
        "ambience_volume": 0.35,
        "ambience_prompts": ambience_prompts,
        "bgm_model": "fal-ai/lyria2",
        "bgm_prompt": "warm emotional Korean drama score, gentle piano and strings, quiet winter "
                      "atmosphere building to a tearful heartfelt resolution, instrumental only, no vocals",
        "bgm_volume": 0.22,
    }
    with open(os.path.join(ROOT, "scripts", "audio", "guard-kim-secret.json"), "w", encoding="utf-8") as f:
        json.dump(audio, f, ensure_ascii=False, indent=2)

    print("생성 완료: subs/guard-kim-secret.ass, scripts/scenes/guard-kim-secret.json, "
          "scripts/audio/guard-kim-secret.json")


if __name__ == "__main__":
    main()
