#!/usr/bin/env python3
"""엄마는 기억을 배달한다 — 제작 자산 생성기 (기준 초상 참조 방식).

전작(build_full_assets.py)의 beat 정렬 방식을 따르되, 모든 인물 장면에
확정된 기준 초상 이미지(refs)를 붙여 image(reference)-to-video로 생성한다.
→ 인물 일관성 고정 + 재생성 비용 절감 (CLAUDE.md 다음 작품 규칙).

생성 파일:
    scripts/scenes/mom-memory-delivery.json   (16:9 장면 프롬프트 + refs)
    subs/mom-memory-delivery.ass              (1920x1080 자막)
    scripts/audio/mom-memory-delivery.json    (목소리·감정·현장음 설정)

사용자 확정 사항: 배우 4명(정례2/혜정1보정/경비원카메오/민호1),
목소리(정례=Abbess, 혜정=Calm_Woman, 민호=Decent_Boy, 경비원=Deep_Voice_Man),
전 대사 감정 지정, 명찰 "김영곤", 학교 명판은 글자 없이(장흥초등학교는 인서트).

사용법: python3 scripts/build_mom_assets.py
"""

import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# 확정 배우 기준 초상 (refs — 장면 생성 참조 이미지, 저장소 경로)
REF_JR = "assets/portraits/mom-memory-delivery/jeongrye-2.png"
REF_JR_Y = "assets/portraits/mom-memory-delivery-views/jeongrye-young-1.png"  # 회상(40대)
REF_HJ = "assets/portraits/mom-memory-delivery-views/hyejeong-fix-1.png"
REF_MH = "assets/portraits/mom-memory-delivery/minho-1.png"
REF_GD = "assets/portraits/mom-memory-delivery-guard/guard-final.png"

# 인물 고정 문구 (기준 초상과 함께 프롬프트에도 반복 — 이중 고정)
JR = "72세 한국 할머니 정례(흰머리 섞인 회색 짧은 파마머리, 갸름한 얼굴, 연보라색 무지 카디건)"
JR_Y = "40대 초반의 정례(검은 짧은 파마머리, 갸름한 얼굴, 소박한 꽃무늬 없는 무지 앞치마)"
HJ = "45세 한국 여성 혜정(어깨길이 갈색 단발, 남색 무지 재킷과 흰 블라우스)"
MH = "10살 한국 남자아이 민호(짧은 검은 머리, 하늘색 무지 티셔츠, 노란 책가방)"
GD = "60대 한국 남성 초등학교 경비원(은테 안경, 회색 경비 제복과 정모, 가슴에 명찰표)"

# 장소 고정 문구 (클로즈업에도 반드시 포함)
HOUSE = "오래된 한국 다세대주택의 소박한 거실"
DOOR = "다세대주택 현관"
KITCHEN = "소박한 옛날식 부엌"
ALLEY = "주택가 골목길, 흐린 하늘"
BUS = "낡은 시내버스 안 창가"
HILL = "학교로 오르는 언덕길, 흐린 하늘"
GATE = "초등학교 정문 앞(아무 글자 없는 매끈한 교문 기둥과 무지 명판), 흐린 하늘"
GATE_RAIN = "비 내리는 초등학교 정문 앞(아무 글자 없는 매끈한 교문 기둥)"
OLD_GATE = "30년 전 초등학교 앞 등굣길, 비 내리는 아침, 아련한 세피아빛 회상 톤"
OLD_KITCHEN = "30년 전 소박한 옛날 부엌, 아련한 세피아빛 회상 톤"

TALK = ("카메라를 향해 대사에 맞춰 입을 자연스럽게 움직이며 한국어로 말하는 "
        "정면 상반신 샷, 화면에는 말하는 사람 한 명만 등장")
MUTE = "아무도 입을 움직이거나 말하지 않는 장면"

STYLE = ("시네마틱 한국 가족 드라마, 실사 영화 화질, 첨부된 기준 인물 사진과 똑같은 "
         "얼굴·머리·의상을 유지, 자연스러운 피부 질감, 16:9 와이드 가로 구도, "
         "말하는 입 모양은 한국어(영어 없음), 화면 속 옷·간판·명판·소품·배경에는 "
         "글자나 로고가 전혀 보이지 않게")

# 스타일 이름: 화자별 자막 색 + Caption(무음 카드) + Action(무언 장면)
S_JR, S_HJ, S_MH, S_GD = "Jeongrye", "Hyejeong", "Minho", "Guard"
C, A = "Caption", "Action"


def shot(prompt, refs):
    return {"p": prompt, "r": refs}


SECTIONS = [
    dict(
        name="1막 — 자꾸 사라지는 엄마",
        ambience="",
        narration_shots=[
            shot(f"{HOUSE}, 아무도 없는 거실과 활짝 열린 현관문, 바닥에 놓인 낡은 노란 우산 한 자루, 불안한 정적, {MUTE}", []),
        ],
        speaker_shots={
            S_HJ: [
                shot(f"{DOOR}, {HJ}이 놀란 얼굴로 집안을 두리번거리다 다급히 휴대폰을 귀에 대고 {TALK}", [REF_HJ]),
                shot(f"{ALLEY}, {HJ}이 화가 나 언성을 높이며 {TALK}", [REF_HJ]),
                shot(f"{ALLEY}, {HJ}이 기가 막힌 표정으로 하늘을 가리키며 {TALK}", [REF_HJ]),
                shot(f"밤의 {KITCHEN}, {HJ}이 식탁에 혼자 앉아 지친 얼굴로 휴대폰을 들고 눈물을 참으며 {TALK}", [REF_HJ]),
            ],
            S_JR: [
                shot(f"{ALLEY}, 낡은 노란 우산을 품에 안은 {JR}이 태연하게 웃으며 {TALK}", [REF_JR]),
                shot(f"{ALLEY}, {JR}이 노란 우산을 꼭 끌어안고 시무룩하지만 고집스러운 표정으로 {TALK}", [REF_JR]),
                shot(f"{ALLEY}, {JR}이 눈물이 살짝 맺힌 채 우산을 더 꼭 끌어안고 고집스럽게 {TALK}", [REF_JR]),
            ],
        },
        lines=[
            (A, "10", f"이른 아침의 오래된 다세대주택 골목 전경, 전깃줄과 낮은 지붕들, 잔잔하고 "
                      f"쓸쓸한 분위기, 사람 없음, {MUTE}", None, []),
            (C, "", "어느 오래된 다세대주택", None),
            (S_HJ, "", "엄마? …엄마 어디 갔어?!", "surprised"),
            (S_HJ, "", "네, 저희 엄마가 또 없어졌어요. 연보라색 가디건 입으셨고요…!", "fearful"),
            (A, "5", f"{ALLEY}, 낡은 노란 우산을 품에 안은 {JR}이 젊은 경찰관과 함께 걸어오고, "
                     f"맞은편에서 {HJ}이 달려오는 장면, {MUTE}", None, [REF_JR, REF_HJ]),
            (S_JR, "", "왜 이렇게 야단이야. 잠깐 나갔다 온 건데.", "happy"),
            (S_HJ, "", "잠깐이 아니잖아! 이번 달만 벌써 세 번째야, 세 번째!", "angry"),
            (S_JR, "", "…비가 온다고 했단 말이야.", "sad"),
            (S_HJ, "", "비? 오늘 하늘 좀 봐, 엄마. 구름 한 점 없잖아!", "angry"),
            (S_JR, "", "아니야… 온댔어. 오늘은 꼭 온댔단 말이야.", "sad"),
            (A, "5", f"밤의 다세대주택 안방 문틈 사이로 보이는 {JR}, 낡은 노란 우산을 수건으로 "
                     f"정성껏 닦아 머리맡에 눕혀 두는 장면, 따뜻하지만 쓸쓸한 조명, {MUTE}", None, [REF_JR]),
            (A, "10", f"저녁의 {HOUSE}, {JR}과 {HJ}이 작은 밥상에 마주 앉아 말없이 저녁을 먹고, "
                      f"{JR}이 {HJ}의 밥그릇 위에 반찬을 조용히 올려 주는 장면, 어색하지만 애틋한 침묵, "
                      f"화면에는 정확히 두 명만 등장, {MUTE}", None, [REF_JR, REF_HJ]),
            (S_HJ, "", "고모… 나 진짜 힘들어. 회사 다니면서 혼자서는 도저히…", "sad"),
            (S_HJ, "", "…요양원 상담, 다음 주에 가보기로 했어.", "sad"),
        ],
    ),
    dict(
        name="2막 — 몰래 따라간 길",
        ambience="",
        narration_shots=[
            shot(f"{HOUSE}, 창밖 흐린 하늘, {MUTE}", []),
        ],
        speaker_shots={
            S_JR: [
                shot(f"{HOUSE} 창가, {JR}이 설레는 표정으로 흐린 하늘을 올려다보며 혼잣말로 {TALK}", [REF_JR]),
                shot(f"{GATE}, {JR}이 노란 우산을 두 손으로 꼭 쥐고 공손하고 간절한 표정으로 {TALK}", [REF_JR]),
            ],
            S_HJ: [
                shot(f"{DOOR}, {HJ}이 몰래 뒤따라 나서며 낮은 목소리로 혼잣말하는 {TALK}", [REF_HJ]),
                shot(f"{GATE} 건너편, {HJ}이 어리둥절한 표정으로 학교를 올려다보며 혼잣말로 {TALK}", [REF_HJ]),
                shot(f"{GATE} 옆, {HJ}이 조심스럽게 묻는 표정으로 {TALK}", [REF_HJ]),
                shot(f"{GATE} 옆, {HJ}이 놀라 눈이 커진 채 {TALK}", [REF_HJ]),
                shot(f"{GATE} 옆, {HJ}이 얼어붙은 듯 창백해진 얼굴로 떨리며 {TALK}", [REF_HJ]),
            ],
            S_GD: [
                shot(f"{GATE} 경비실 옆, {GD}이 반갑게 웃으며 {TALK}", [REF_GD]),
                shot(f"{GATE} 경비실 옆, {GD}이 따뜻한 미소로 고개를 끄덕이며 {TALK}", [REF_GD]),
                shot(f"{GATE} 옆, {GD}이 차분하게 설명하는 {TALK}", [REF_GD]),
                shot(f"{GATE} 옆, {GD}이 조심스럽고 안타까운 표정으로 목소리를 낮춰 {TALK}", [REF_GD]),
            ],
        },
        lines=[
            (C, "", "사흘 뒤, 흐린 날 아침", None),
            (S_JR, "", "오늘은 진짜 비가 오겠네. …가야지, 늦으면 안 되지.", "happy"),
            (S_HJ, "", "어디를 가는 거야, 대체…", "neutral"),
            (A, "5", f"{BUS}, {JR}이 창가에 앉아 노란 우산을 꼭 끌어안고 창밖을 바라보는 장면, {MUTE}", None, [REF_JR]),
            (A, "5", f"{HILL}, 앞서 걸어가는 {JR}과 멀찍이 뒤따르는 {HJ}, 화면에는 정확히 두 명만 등장, {MUTE}", None, [REF_JR, REF_HJ]),
            (A, "10", f"{GATE}, {JR}이 교문 옆 늘 서던 자리에 멈춰 서서 노란 우산을 두 손으로 쥐고 "
                      f"운동장 쪽을 하염없이 바라보는 옆모습, 잔잔하고 아련한 연출, {MUTE}", None, [REF_JR]),
            (S_HJ, "", "…초등학교? 여기가 어디라고…", "surprised"),
            (S_GD, "", "아이고, 어르신. 오늘도 오셨네요.", "happy"),
            (S_JR, "", "우리 아이가 우산을 안 가져갔어요. 비 맞으면 감기 걸리는데…", "neutral"),
            (S_GD, "", "걱정 마세요. 이따 아이들 나올 때까지 여기서 같이 기다립시다.", "happy"),
            (A, "5", f"{GATE}, 멀리서 지켜보던 {HJ}이 조심스럽게 {GD} 쪽으로 걸어가는 장면, "
                     f"화면에는 정확히 두 명만 등장, {MUTE}", None, [REF_HJ, REF_GD]),
            (S_HJ, "", "저기… 저희 엄마세요. 여기 자주 오셨나요?", "neutral"),
            (S_GD, "", "따님이시구나. …비 예보만 있으면 오세요. 벌써 몇 달째예요.", "neutral"),
            (S_HJ, "", "몇 달째라고요…?", "surprised"),
            (A, "5", f"{GATE}, 하교 종이 울린 뒤 우르르 쏟아져 나오는 아이들, 그 사이에서 {JR}이 "
                     f"노란 우산을 쥔 채 아이들 얼굴을 하나하나 애타게 살피는 장면, {MUTE}", None, [REF_JR]),
            (S_GD, "", "늘 저 자리에서, 우산 들고 아이들 나오는 것만 보다 가십니다.", "sad"),
            (S_GD, "", "처음엔 손주 마중인 줄 알았는데… 한번은 그러시더라고요. 우리 민호 나올 시간이라고.", "sad"),
            (S_GD, "", "그 얘길 듣고는… 저도 그냥 모른 척, 같이 기다려 드립니다.", "sad"),
            (S_HJ, "", "…민호… 오빠?", "surprised"),
        ],
    ),
    dict(
        name="3막 — 30년 전, 그 비 오는 날",
        ambience="steady rain falling on pavement, rain drops on umbrella, distant thunder rumble",
        narration_shots=[
            shot(f"{OLD_GATE}, 빗줄기 사이 텅 빈 등굣길, {MUTE}", []),
        ],
        speaker_shots={
            S_MH: [
                shot(f"{OLD_GATE}, {MH}가 비를 맞으며 해맑게 웃는 얼굴로 뒤돌아보고 {TALK}", [REF_MH]),
                shot(f"{OLD_GATE}, {MH}가 밝게 웃으며 손을 흔들고 {TALK}", [REF_MH]),
            ],
            S_JR: [
                shot(f"{OLD_KITCHEN} 현관 앞, {JR_Y}이 웃음 섞인 걱정스러운 표정으로 {TALK}", [REF_JR_Y]),
                shot(f"{OLD_KITCHEN}, {JR_Y}이 창밖 폭우를 보고 놀라 걱정스럽게 {TALK}", [REF_JR_Y]),
            ],
        },
        lines=[
            (C, "", "30년 전, 같은 학교 앞", None),
            (A, "5", f"{OLD_KITCHEN} 현관, {MH}가 노란 책가방을 둘러메고 신발을 구겨 신으며 "
                     f"뛰어나갈 준비를 하는 장면, {MUTE}", None, [REF_MH]),
            (S_MH, "", "엄마! 나 우산 없어도 돼! 금방 뛰어가면 되는데, 뭐!", "happy"),
            (S_JR, "", "감기 걸린다니까! 이따 엄마가 우산 갖고 갈게!", "happy"),
            (S_MH, "", "응! 약속이야, 엄마!", "happy"),
            (A, "10", f"30년 전 빗속 골목길, {MH}가 책가방을 머리에 얹고 물웅덩이를 첨벙이며 "
                      f"신나게 뛰어가는 몽타주, 아련한 세피아빛 회상 톤, {MUTE}", None, [REF_MH]),
            (A, "5", f"{OLD_KITCHEN}, {JR_Y}이 설거지하던 손을 멈추고 창밖에 쏟아지는 폭우를 "
                     f"바라보는 장면, {MUTE}", None, [REF_JR_Y]),
            (S_JR, "", "어머, 비가 이렇게 쏟아지네. 가야겠다.", "surprised"),
            (A, "5", f"30년 전 빗속 골목길, {JR_Y}이 노란 우산을 들고 빗속을 달려가는 장면, "
                     f"아련한 세피아빛 회상 톤, {MUTE}", None, [REF_JR_Y]),
            (A, "5", f"30년 전 빗속 길바닥, 펴지지 못한 노란 우산이 젖은 아스팔트 위에 떨어져 "
                     f"천천히 구르는 클로즈업, 사람 없음, {MUTE}", None, []),
            (A, "5", f"{OLD_GATE}, 빗속에 번쩍이는 구급차의 붉은 불빛, 길바닥에 떨어진 젖은 노란 책가방 "
                     f"클로즈업, 사람 얼굴은 보이지 않음, {MUTE}", None, []),
            (C, "", "민호는 그날, 엄마를 기다리다 길을 건너던 중이었다", None),
        ],
    ),
    dict(
        name="4막 — 우산을 함께 들다",
        ambience="",
        narration_shots=[
            shot(f"{GATE_RAIN}, 젖은 골목길과 빗줄기, 잔잔한 전환 연출, 사람 없음, {MUTE}", []),
            shot(f"{GATE_RAIN}, 활짝 펴진 낡은 노란 우산 위로 빗방울이 맺혀 흐르는 클로즈업, "
                 f"따뜻하고 아련한 여운, {MUTE}", []),
        ],
        speaker_shots={
            S_HJ: [
                shot(f"{GATE}, {HJ}이 눈물을 참으며 떨리는 목소리로 {TALK}", [REF_HJ]),
                shot(f"{GATE}, {HJ}이 울음이 터진 채 {TALK}", [REF_HJ]),
                shot(f"{GATE}, {HJ}이 눈물이 흐르는 채 놀란 얼굴로 {TALK}", [REF_HJ]),
                shot(f"{GATE}, {HJ}이 오열하며 {TALK}", [REF_HJ]),
                shot(f"{GATE_RAIN}, {HJ}이 눈물 속에 옅은 미소를 지으며 {TALK}", [REF_HJ]),
                shot(f"{GATE_RAIN} 노란 우산 아래, {HJ}이 다정하게 웃으며 {TALK}", [REF_HJ]),
            ],
            S_JR: [
                shot(f"{GATE}, {JR}이 해맑게 웃으며 노란 우산을 들어 보이고 {TALK}", [REF_JR]),
                shot(f"{GATE}, {JR}이 처음으로 흔들리는 눈빛으로 조용히 {TALK}", [REF_JR]),
                shot(f"{GATE}, {JR}이 눈물이 고인 채 가슴을 누르며 천천히 오열하는 {TALK}", [REF_JR]),
                shot(f"{GATE_RAIN} 노란 우산 아래, {JR}이 평온한 눈물의 미소로 하교하는 아이들 쪽을 바라보다 {TALK}", [REF_JR]),
                shot(f"{GATE_RAIN} 노란 우산 아래, {JR}이 딸을 바라보며 눈물의 미소로 {TALK}", [REF_JR]),
            ],
        },
        lines=[
            (A, "5", f"{GATE} 건너편, {HJ}이 눈물을 닦고 심호흡을 한 뒤 엄마 쪽으로 "
                     f"천천히 걸어가는 장면, {MUTE}", None, [REF_HJ]),
            (S_HJ, "", "엄마… 여기서 뭐 해…", "sad"),
            (S_JR, "", "어, 혜정 왔니? 오빠 우산 갖다주러 왔지. 오늘 비 온다잖아.", "happy"),
            (S_HJ, "", "엄마… 오빠는… 오빠는 이제 여기 없잖아…", "sad"),
            (S_JR, "", "…알아.", "sad"),
            (S_HJ, "", "…뭐라고?", "surprised"),
            (S_JR, "", "아는데… 아는데도, 비만 오면 여기가 이렇게 아파서… 그날 조금만 빨리 왔으면, 우리 민호…", "sad"),
            (S_JR, "", "엄마가 미안해서… 삼십 년을 미안해서, 혜정아…", "sad"),
            (S_HJ, "", "엄마 잘못 아니야… 엄마 잘못 아니야, 엄마…", "sad"),
            (A, "5", f"{GATE}, {JR}과 {HJ}이 서로 끌어안고 있는 위로 빗방울이 하나둘 떨어지기 시작하는 장면, "
                     f"화면에는 정확히 두 명만 등장, {MUTE}", None, [REF_JR, REF_HJ]),
            (A, "5", f"{GATE_RAIN}, 서로 끌어안은 {JR}과 {HJ} 위로 빗줄기가 점점 굵어지고, 두 사람이 "
                     f"떨어질 줄 모르는 장면, 화면에는 정확히 두 명만 등장, {MUTE}", None, [REF_JR, REF_HJ]),
            (S_HJ, "", "엄마… 비 온다. 우산 펴자.", "sad"),
            (A, "5", f"{GATE_RAIN}, {JR}과 {HJ}이 낡은 노란 우산을 함께 펴 들고, 그 옆으로 우산을 쓴 "
                     f"아이들이 웃으며 하교하는 장면, {MUTE}", None, [REF_JR, REF_HJ]),
            (S_JR, "", "…우리 민호도, 저렇게 웃었는데.", "sad"),
            (S_HJ, "", "응. …엄마, 이제 나랑 같이 오자. 비 오는 날마다, 같이.", "sad"),
            (S_JR, "", "…그럴까, 우리 딸.", "happy"),
            (A, "10", f"{GATE_RAIN}, 낡은 노란 우산을 함께 쓴 {JR}과 {HJ}의 뒷모습이 빗속에 서 있고, "
                      f"멀리 경비실 앞에서 {GD}이 조용히 목례하는 와이드 샷, 잔잔한 여운, {MUTE}", None,
             [REF_JR, REF_HJ, REF_GD]),
            (C, "", "그 뒤로, 비가 오는 날이면", None),
            (A, "10", f"다른 비 오는 날의 {HILL}, 노란 우산을 함께 쓴 {JR}과 {HJ}이 팔짱을 끼고 "
                      f"나란히 언덕길을 오르는 뒷모습, 따뜻한 연출, 화면에는 정확히 두 명만 등장, {MUTE}",
             None, [REF_JR, REF_HJ]),
            (A, "10", f"{GATE_RAIN}, 노란 우산을 쓴 {JR}과 {HJ}이 경비실 앞의 {GD}과 서로 웃으며 "
                      f"목례를 나누는 장면, 따뜻한 여운, 화면에는 정확히 세 명만 등장, {MUTE}", None,
             [REF_JR, REF_HJ, REF_GD]),
            (A, "10", f"저녁의 {HOUSE}, {JR}이 낡은 사진 액자를 수건으로 정성껏 닦고, 뒤에서 {HJ}이 "
                      f"엄마의 어깨를 살며시 감싸 안는 장면, 액자 속 사진은 흐릿하게 보이지 않게, "
                      f"따뜻한 저녁 조명, 화면에는 정확히 두 명만 등장, {MUTE}", None, [REF_JR, REF_HJ]),
            (C, "", "기억은 흐려져도, 사랑은 길을 잊지 않는다", None),
        ],
    ),
]

# 3막(회상)에만 빗소리 현장음, 나머지는 생략(사람 말소리 오염 방지)
RAIN_AMB = "steady rain falling on pavement, rain drops on umbrella, distant thunder rumble"

CHAR_RATE = 5.5
LINE_PAD = 0.4
MIN_DUR = 1.2
CAPTION_MIN = 2.4
BEAT_LEAD = 0.6
BEAT_TAIL = 1.2


def line_duration(style, text):
    chars = len(re.sub(r"\s", "", text.replace("\\N", " ")))
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
    for item in lines:
        style, name, text, emotion = item[0], item[1], item[2], item[3]
        if style == A:
            refs = item[4] if len(item) > 4 else []
            beats.append({"key": "ACT", "size": int(name), "prompt": text, "refs": refs})
            continue
        key = "N" if style == C else style
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
Title: 엄마는 기억을 배달한다 자막
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Noto Sans CJK KR,46,&H00E8E8E8,&H000000FF,&H00000000,&H96000000,-1,-1,0,0,100,100,0,0,1,4,2,8,200,200,70,1
Style: Jeongrye,Noto Sans CJK KR,60,&H00B8E8FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Hyejeong,Noto Sans CJK KR,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Minho,Noto Sans CJK KR,60,&H0090EE90,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Guard,Noto Sans CJK KR,60,&H00A0C8F0,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1

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
                scene_items.append({"prompt": beat["prompt"], "duration": beat["size"],
                                    "refs": beat["refs"]})
                ambience_prompts.append(sec["ambience"])
                t_video += beat["size"]
                continue

            t = t_video + BEAT_LEAD
            for style, name, text, emotion in beat["lines"]:
                if style != C:
                    tts_no += 1
                    emotions[str(tts_no)] = emotion or "neutral"
                dur = line_duration(style, text)
                events.append((t, t + dur - 0.1, style, name, text))
                t += dur
            need = (t - t_video) + BEAT_TAIL

            key = beat["key"]
            shots = sec["narration_shots"] if key == "N" else sec["speaker_shots"][key]
            for size in beat_scene_sizes(need):
                if key == "N":
                    sh = shots[narr_idx % len(shots)]
                    narr_idx += 1
                else:
                    k = spk_idx.get(key, 0)
                    sh = shots[k % len(shots)]
                    spk_idx[key] = k + 1
                scene_items.append({"prompt": sh["p"], "duration": size, "refs": sh["r"]})
                ambience_prompts.append(sec["ambience"])
                t_video += size

        print(f"{sec['name']}: 발화 {n_lines}줄 → {t_video - sec_start:.0f}초")

    total = t_video
    n5 = sum(1 for s in scene_items if s["duration"] == 5)
    n10 = len(scene_items) - n5
    n_ref = sum(1 for s in scene_items if s["refs"])
    print(f"\n합계: 자막 {len(events)}줄(TTS {tts_no}줄), 장면 {len(scene_items)}개 "
          f"(5초 {n5} + 10초 {n10}, 초상 참조 {n_ref}개), 영상 {total:.0f}초 ({total / 60:.1f}분)")

    with open(os.path.join(ROOT, "subs", "mom-memory-delivery.ass"), "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, style, name, text in events:
            f.write(f"Dialogue: 0,{fmt_time(s)},{fmt_time(e)},{style},{name},0,0,0,,{text}\n")

    with open(os.path.join(ROOT, "scripts", "scenes", "mom-memory-delivery.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": 10, "ratio": "16:9", "style": STYLE, "scenes": scene_items},
                  f, ensure_ascii=False, indent=2)

    audio = {
        "tts_model": "fal-ai/minimax/speech-02-hd",
        "language_boost": "Korean",
        "speed": 1.0,
        "default_voice": "Calm_Woman",
        "style_voices": {"Jeongrye": "Abbess", "Hyejeong": "Calm_Woman",
                         "Minho": "Decent_Boy", "Guard": "Deep_Voice_Man"},
        "style_emotions": {},
        "emotion_overrides": emotions,
        "scene_durations": [s["duration"] for s in scene_items],
        "narration_styles": [],
        "silent_styles": ["Caption"],
        "lipsync_models": ["fal-ai/sync-lipsync", "fal-ai/latentsync"],
        "ambience_model": "fal-ai/mmaudio-v2",
        "ambience_volume": 0.4,
        "ambience_prompts": ambience_prompts,
        "bgm_model": "fal-ai/lyria2",
        "bgm_prompt": "emotional Korean family drama score, gentle piano and warm strings, "
                      "tender and sorrowful, building to a tearful embrace and quiet hope, "
                      "instrumental only, no vocals",
        "bgm_volume": 0.22,
    }
    with open(os.path.join(ROOT, "scripts", "audio", "mom-memory-delivery.json"), "w", encoding="utf-8") as f:
        json.dump(audio, f, ensure_ascii=False, indent=2)

    print("생성 완료: subs/mom-memory-delivery.ass, scripts/scenes/mom-memory-delivery.json, "
          "scripts/audio/mom-memory-delivery.json")


if __name__ == "__main__":
    main()
