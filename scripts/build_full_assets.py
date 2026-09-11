#!/usr/bin/env python3
"""회장님의 마지막 배달 — 풀버전(약 11~12분) 제작 자산 생성기.

전체 대본을 섹션별 대사/내레이션과 숏 리스트로 정의해 두고, 발화 길이 기반으로
자막 타이밍을 계산한 뒤 세 파일을 생성한다:

    scripts/scenes/chairman-last-delivery-full.json  (16:9 장면 프롬프트)
    subs/chairman-last-delivery-full.ass             (1920x1080 자막)
    scripts/audio/chairman-last-delivery-full.json   (목소리·감정·현장음 설정)

타이밍 규칙: 줄 길이(공백 제외 글자 수)/5.5 + 0.4초, 최소 1.2초. 섹션별 발화
구간을 10초 장면 경계에 맞춰 올림하고, 남는 시간은 섹션 끝의 연출 호흡으로 둔다.
장면 수 = ceil(섹션 구간/10), 섹션 숏 리스트를 순환하며 채운다.

사용법: python3 scripts/build_full_assets.py
"""

import json
import math
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# 등장인물 고정 외형 (모든 장면 프롬프트에서 동일 문구 반복 — 일관성 유지)
DOYUN = "20대 후반 한국 남성 배달 기사(짧은 검은 머리, 파란색 배달 점퍼, 검은 바지, 짜장 소스 묻은 흰 운동화)"
MIRAN = "50대 한국 여성(베이지색 트위드 명품 정장, 진주 목걸이, 단정한 올림머리)"
TAESEOK = "20대 후반 한국 남성(흰색 명품 후드티, 금목걸이, 갈색 염색머리)"
JUNG = "60대 한국 남성 비서실장(백발, 은테 안경, 검은 스리피스 정장)"
LOBBY = "대리석 바닥과 크리스탈 샹들리에가 있는 최고급 아파트 로비, 차가운 백색 조명"

STYLE = ("시네마틱 한국 드라마, 실사 영화 화질, 동일한 인물과 의상과 장소를 "
         "모든 장면에서 유지, 자연스러운 피부 질감, 16:9 와이드 가로 구도")

# (스타일, 화자이름, 대사, 감정|None)  — 스타일: N(내레이션)/D(도윤)/V(빌런)/J(정실장)
N, D, V, J = "Naration", "Doyun", "Vil", "Jung"

SECTIONS = [
    dict(
        name="콜드 오픈",
        lead_in=3.0,
        ambience="porcelain bowl clattering, liquid splashing on marble floor, shocked crowd murmur, lobby reverb",
        shots=[
            f"{LOBBY}, {MIRAN}이 {DOYUN}에게 호통치며 짜장면 그릇을 쏟아 검은 소스가 흰 운동화 위로 흐르는 장면, 뒤에서 {TAESEOK}이 휴대폰으로 촬영하며 비웃음",
            f"{LOBBY}, {DOYUN}가 입주민들이 지켜보는 가운데 천천히 무릎을 꿇는 장면, 슬로우 모션",
            f"{DOYUN}의 은색 손목시계 클로즈업, 8시 32분을 가리키는 시계 바늘, 긴장감 있는 연출",
        ],
        lines=[
            (V, "미란", "무릎 꿇어. 다들 보는 데서.", "angry"),
            (V, "태석", "야 이거 봐, 진짜 꿇네.", "happy"),
            (N, "", "배달 기사가 천천히 무릎을 꿇습니다. 그리고 손목시계를 봅니다.", None),
            (N, "", "여덟 시 삼십이 분.", None),
        ],
    ),
    dict(
        name="내레이션 훅",
        lead_in=1.0,
        ambience="low cinematic room tone, clock ticking, distant city hum, no music",
        shots=[
            f"{DOYUN}의 얼굴 클로즈업, 무표정하지만 깊은 눈빛, 화면 정지 같은 정적인 연출",
            "고급 한옥 서재에서 백발 노인의 손이 만년필로 유언장에 서명하는 회상 장면, 세피아 톤",
            "야간 도시 스카이라인과 대기업 본사 빌딩 외관, 웅장한 야경",
            f"{DOYUN}가 배달 오토바이를 타고 밤거리를 달리는 몽타주, 회상 톤",
        ],
        lines=[
            (N, "", "이 남자 이름은 강도윤. 스물아홉. 한성그룹 창업주의 유일한 손자입니다.", None),
            (N, "", "석 달 전, 할아버지는 유언장에 단 한 줄을 남기고 세상을 떠났습니다.", None),
            (N, "", "\"밑바닥에서 90일을 버텨라. 하루라도 정체를 밝히면 그룹 전체를 재단에 기부한다.\"", None),
            (N, "", "오늘이 90일째. 그리고 28분 뒤, 아홉 시. 한성그룹 이사회가 새 회장을 발표합니다.", None),
            (N, "", "지금 이 남자를 무릎 꿇린 사람들은 아무것도 모릅니다. 이 아파트가 누구 건지. 자기 남편 월급이 누구 결재로 나가는지.", None),
            (N, "", "28분 뒤에 어떻게 되는지, 끝까지 보세요.", None),
        ],
    ),
    dict(
        name="8시간 전 — 도착",
        lead_in=2.0,
        ambience="night city street ambience, motorcycle engine idling, guard booth, freight elevator hum",
        shots=[
            f"밤의 강남 최고급 아파트 외관과 정문, {DOYUN}가 배달 오토바이 옆에서 헬멧을 벗는 장면, 드라마틱 야경",
            f"경비실 앞, 제복 입은 경비원이 손사래 치며 지하 주차장을 가리키고 {DOYUN}가 말없이 듣는 장면",
            f"어두운 지하 화물 엘리베이터에 배달 봉지를 들고 타는 {DOYUN}, 차가운 형광등 조명, 계급 대비 연출",
        ],
        lines=[
            (N, "", "자막, 8시간 전. 강남 한복판, 한 채에 백억이 넘는다는 최고급 아파트, 한성 팰리스.", None),
            (V, "경비원", "배달은 지하 화물 엘리베이터. 정문으로 들어오지 마. 여기 사는 분들 눈에 띄면 안 돼.", "angry"),
            (N, "", "여러분, 이 아파트 이름 잘 기억하세요. 한성 팰리스. 한성건설이 지었고, 한성자산이 관리하고, 그 두 회사 모두 도윤이 오늘 밤 물려받을 그룹의 계열사입니다.", None),
            (N, "", "이 단지 전체가, 이 경비실까지도, 몇 시간 뒤 이 남자 겁니다.", None),
        ],
    ),
    dict(
        name="4801호 첫 배달",
        lead_in=2.0,
        ambience="apartment hallway room tone, porcelain bowl spill and splash, phone camera shutter clicks, mocking snicker",
        shots=[
            f"고급 펜트하우스 현관, 문이 열리고 {MIRAN}이 짜증난 표정으로 {DOYUN}를 맞는 장면",
            f"펜트하우스 현관, {TAESEOK}이 슬리퍼를 끌고 나와 배달 봉지를 발로 툭 차며 비웃는 장면",
            f"{DOYUN}의 무표정한 얼굴 클로즈업, 감정을 누르는 눈빛",
            f"{MIRAN}이 짜장면 그릇을 들고 단무지를 가리키며 따지는 클로즈업",
            f"{MIRAN}이 짜장면 그릇을 {DOYUN}의 발 앞에 쏟아붓는 장면, 검은 소스가 바닥에 퍼지는 클로즈업",
            f"{DOYUN}가 무릎을 꿇고 손으로 짜장 소스를 닦고, {TAESEOK}이 옆에서 휴대폰으로 찍으며 웃는 장면",
        ],
        lines=[
            (V, "미란", "아 진짜, 왜 이렇게 늦어? 면 다 불었겠네.", "angry"),
            (D, "", "죄송합니다. 엘리베이터가 화물용밖에 안 돼서요.", None),
            (V, "미란", "그건 니 사정이고. 아니, 배달하는 애가 뭐 이렇게 말이 많아? 봉지 내려놓고 가.", "angry"),
            (V, "태석", "엄마, 이거 누구야?", None),
            (V, "태석", "짜장면 냄새 진짜. 야, 너 이 아파트 들어올 때 냄새 좀 빼고 와라. 여기 사는 사람들 격이 있어.", "happy"),
            (N, "", "여러분은 아시죠. 도윤이 왜 참는지. 오늘이 90일째. 한 마디만 잘못하면 그룹 전체가 재단으로 넘어갑니다.", None),
            (N, "", "이 남자는 지금 참는 게 아닙니다. 기다리고 있는 겁니다.", None),
            (V, "미란", "잠깐. 너 이리 와봐.", "angry"),
            (V, "미란", "이거 봐. 단무지가 두 개밖에 없어. 내가 세 개 시켰는데.", "angry"),
            (D, "", "확인해보겠습니다.", None),
            (V, "미란", "확인은 무슨. 너 지금 내가 거짓말한다는 거야?", "angry"),
            (V, "미란", "이거 치우고 가. 다시 갖고 와. 너네 사장한테 내가 누군지 말해. 한성건설 유 상무 와이프라고.", "angry"),
            (V, "태석", "야 이거 스토리 올려야지. 배달 거지 무릎 꿇은 거.", "happy"),
            (N, "", "여러분, 태석이 지금 찍고 있는 이 영상. 오늘 밤 이 영상이 어디에 올라가는지 끝까지 보시면 압니다.", None),
            (D, "", "다시 갖다 드리겠습니다.", None),
            (V, "미란", "당연하지. 그리고 이번엔 정문으로 올라와. 관리소장한테 내가 말해둘 테니까. 무릎 꿇고 사과하는 거 제대로 보게.", "angry"),
        ],
    ),
    dict(
        name="지하 주차장 — 정 실장",
        lead_in=2.0,
        ambience="underground parking garage ambience, low ventilation hum, car window motor, echoing footsteps",
        shots=[
            f"어두운 지하 주차장, 배달 오토바이 옆에 세워진 검은 고급 세단, {JUNG}이 차창 너머로 정중히 고개 숙이는 장면",
            f"{JUNG}의 진지한 얼굴 클로즈업, 어둠 속 대비 조명",
            f"{DOYUN}가 짜장 소스 묻은 손을 내려다보며 차분히 말하는 클로즈업",
            f"지하 주차장 와이드 샷, 오토바이와 세단 사이에 마주 선 {DOYUN}와 {JUNG}, 미스터리한 분위기",
        ],
        lines=[
            (J, "정 실장", "도련님. 여덟 시간 남았습니다.", None),
            (N, "", "한성그룹 비서실장, 정 실장. 지난 90일 동안 매일 이 시간에 이렇게 나타나 딱 한 마디만 하고 사라졌습니다. 유언장의 조건, 정체를 밝히지 말 것을 지키기 위해서입니다.", None),
            (D, "", "정 실장님. 4801호.", None),
            (J, "정 실장", "유민호 상무 자택입니다. 한성건설 주택사업본부.", None),
            (D, "", "그 사람 지난 3년 실적 자료, 오늘 밤 이사회 전에 제 책상에 올려주세요.", None),
            (J, "정 실장", "이미 준비돼 있습니다. 회장님께서 생전에 유 상무를 눈여겨보고 계셨습니다. 좋은 쪽은 아니었습니다.", None),
            (D, "", "그리고 하나 더. 이 단지 관리소장. 경비 인력 배치 규정 확인해 주세요. 배달 기사 정문 출입 금지, 그거 규정에 있는 건지 아니면 누가 제멋대로 만든 건지.", None),
            (J, "정 실장", "알겠습니다.", None),
            (D, "", "저 오늘 밤 아홉 시까지 여기 있을 겁니다. 이사회, 여기서 열죠.", None),
            (J, "정 실장", "회장님과 똑 같으십니다.", None),
            (N, "", "여러분, 지금 도윤이 뭘 하는지 보이시죠. 이 남자는 화를 내지 않습니다. 준비를 합니다. 그리고 오늘 밤 이사회를 이 아파트에서 엽니다. 4801호 사람들이 무릎 꿇는 걸 제대로 보기 위해서.", None),
        ],
    ),
    dict(
        name="로비 재배달",
        lead_in=2.0,
        ambience="marble lobby crowd murmur, echoing footsteps, tense atmosphere, no music",
        shots=[
            f"{LOBBY}, {DOYUN}가 새 짜장면 봉지를 들고 정문으로 들어서고 관리소장과 경비원 두 명이 막아서는 장면",
            f"{LOBBY}, 입주민 십여 명이 둘러선 가운데 {MIRAN}이 손가락질하며 호통치는 장면",
            f"{LOBBY}, 무릎 꿇은 {DOYUN}가 고개를 들어 차분하게 말하는 클로즈업",
            f"{MIRAN}의 붉어진 얼굴 클로즈업, 당황과 분노가 섞인 표정",
        ],
        lines=[
            (N, "", "저녁 여덟 시 반. 도윤이 새 짜장면을 들고 정문으로 들어섰습니다.", None),
            (V, "관리소장", "4801호에서 신고가 들어왔어. 배달 기사가 입주민한테 불손했다고. 여기서 사과하고 가.", "angry"),
            (V, "미란", "무릎 꿇어. 다들 보는 데서.", "angry"),
            (N, "", "여덟 시 삼십이 분. 여러분, 이제 아시죠. 28분 남았습니다.", None),
            (D, "", "죄송합니다.", None),
            (V, "태석", "야 이거 봐, 진짜 꿇네. 엄마, 이런 애들은 이렇게 해야 돼. 지 분수를 알아야지.", "happy"),
            (V, "미란", "니 사장한테 전화해. 너 오늘부로 잘라달라고. 내 남편이 한성건설 상무야. 이 동네 배달 업체 전부 우리 쪽에서 계약 관리해. 알아?", "angry"),
            (D, "", "네. 압니다. 한성자산 계약입니다.", None),
            (V, "미란", "뭐?", "surprised"),
            (D, "", "이 단지 협력업체 계약, 한성건설이 아니라 한성자산에서 관리합니다. 상무님 소관이 아닙니다.", None),
            (N, "", "로비가 조용해졌습니다.", None),
            (V, "미란", "이 새끼가 어디서 아는 척을.", "angry"),
        ],
    ),
    dict(
        name="아홉 시 — 신분 공개",
        lead_in=3.0,
        ambience="automatic glass doors sliding open, many synchronized footsteps, camera flashes clicking, gasps",
        shots=[
            "최고급 아파트 로비의 자동문이 열리며 검은 정장의 남자들 열두 명이 줄지어 들어오는 장면, 뒤로 카메라 플래시 세례, 슬로우 모션",
            f"{JUNG}이 무릎 꿇은 {DOYUN} 앞에서 허리를 90도로 숙여 인사하고 입주민들이 경악하는 장면",
            f"{MIRAN}이 입을 벌린 채 뒤로 물러나고 {TAESEOK}의 휴대폰이 바닥에 떨어지는 장면",
            f"{DOYUN}가 일어서서 무릎의 먼지를 터는 장면, 위엄 있는 분위기 전환",
        ],
        lines=[
            (N, "", "로비 자동문이 열렸습니다. 검은 정장의 남자들이 줄지어 들어왔습니다. 열두 명. 그 뒤로 정 실장. 그 뒤로 취재진. 로비 시계가 아홉 시를 가리켰습니다.", None),
            (J, "정 실장", "회장님. 유언 조건 90일, 완료됐습니다. 이사회 소집 준비 끝났습니다.", None),
            (N, "", "로비의 모든 소리가 사라졌습니다.", None),
            (V, "미란", "회, 회장님이라니. 무슨.", "surprised"),
            (J, "정 실장", "한성그룹 제3대 회장, 강도윤 회장님이십니다. 사모님 남편분, 유민호 상무의 최종 결재권자이십니다.", None),
            (N, "", "태석의 휴대폰이 바닥에 떨어졌습니다.", None),
        ],
    ),
    dict(
        name="심판",
        lead_in=2.0,
        ambience="stunned lobby silence, gasps and murmurs, paper envelope rustle, quiet sobbing",
        shots=[
            f"{LOBBY}, {DOYUN}가 서류 봉투를 들고 차분하게 말하고 {JUNG}이 뒤에 시립한 장면",
            f"{MIRAN}의 창백해진 얼굴 클로즈업, 두려움에 떨리는 표정",
            f"{TAESEOK}이 몸을 떨며 고개를 숙이는 장면",
            f"{DOYUN}가 {TAESEOK} 앞에 서서 조용히 말하는 투샷, 팽팽한 긴장감",
            f"중년 관리소장이 진땀을 흘리며 {MIRAN}을 슬쩍 쳐다보는 장면",
            f"{MIRAN}이 무릎을 꿇고 애원하고 {DOYUN}가 내려다보는 권력 역전 구도",
        ],
        lines=[
            (D, "", "유민호 상무. 주택사업본부. 지난 3년 협력업체 선정 과정에서 리베이트 수수 정황 열한 건. 그중 여섯 건이 이 단지 공사입니다.", None),
            (D, "", "사모님. 남편분이 이 아파트 어떻게 샀는지 아세요?", None),
            (V, "미란", "그, 그건.", "fearful"),
            (D, "", "모르셨으면 오늘 아시게 될 겁니다. 감사실이 지금 4801호로 올라가고 있습니다.", None),
            (D, "", "그리고 오태석 대리.", None),
            (D, "", "오늘 아버지 회사 배달 기사 무릎 꿇린 영상 두 개 찍으셨죠. 그거 이미 회사 윤리위원회에 제출됐습니다. 본인 계정에서 올린 걸 캡처했으니까 부인은 안 될 겁니다.", None),
            (V, "태석", "저, 저는 몰랐습니다. 회장님인 줄 알았으면.", "fearful"),
            (D, "", "그게 문제예요. 회장인 줄 알았으면 안 그랬을 거라는 거. 그러니까 회장 아닌 사람한테는 그래도 된다는 거잖아요.", None),
            (D, "", "관리소장님. 배달 기사 정문 출입 금지 규정. 한성자산 관리규정에 그런 조항 없습니다. 누가 만든 겁니까?", None),
            (V, "관리소장", "4801호 사모님이 입주민 대표라서, 요청하셔서.", "fearful"),
            (D, "", "오늘부로 폐지합니다. 그리고 소장님은 내일 아침 한성자산 인사팀으로 출근하세요.", None),
            (D, "", "이 단지, 오늘부터 한성자산이 직접 관리합니다. 입주민 대표 선출 다시 합니다.", None),
            (V, "미란", "회장님, 제발. 저희 남편은 잘못 없어요. 제가 잘못했어요. 저는 그냥, 배달하는 애가.", "sad"),
            (D, "", "배달하는 애. 맞아요. 저 지난 90일 동안 배달하는 애였습니다. 그 90일 동안 저한테 짜장면 부은 사람, 사모님이 처음은 아니었어요.", None),
            (V, "미란", "그, 그럼.", "fearful"),
            (D, "", "근데 무릎 꿇으라고 한 건 사모님이 처음이었습니다.", None),
            (D, "", "이사회 시작하죠. 첫 안건, 유민호 상무 직위해제.", None),
        ],
    ),
    dict(
        name="에필로그 — 마지막 배달",
        lead_in=3.0,
        ambience="night street ambience, motorcycle starting and riding away, wind, dawn birds at quiet hillside",
        shots=[
            f"{LOBBY}, 정장 차림의 중년 남성 임원이 감사실 직원들과 함께 걸어 나오다 무릎 꿇은 아내와 아들을 보고 멈춰 서는 장면",
            f"{DOYUN}가 헬멧을 집어 들고 {JUNG}과 대화하는 장면, 여운 있는 조명",
            f"밤거리, {DOYUN}가 배달 오토바이를 타고 떠나는 뒷모습, 도시 야경 보케",
            f"새벽 산 중턱의 산소 앞, 배달 기사 복장의 {DOYUN}가 짜장면을 내려놓고 고개 숙이는 장면, 일출, 감성적인 엔딩",
        ],
        lines=[
            (N, "", "한 시간 뒤. 유민호 상무가 감사실 직원들과 함께 내려왔습니다. 로비에서 아내와 아들이 무릎을 꿇고 있는 걸 봤습니다. 그리고 그 앞에, 짜장 소스가 묻은 운동화를 신은 채 서 있는 새 회장을 봤습니다.", None),
            (D, "", "정 실장님. 오토바이는 제가 몰고 갈게요. 마지막 배달 하나 남았어요.", None),
            (J, "정 실장", "어디로 가십니까?", None),
            (D, "", "할아버지 산소요. 짜장면 좋아하셨거든요.", None),
            (N, "", "강 회장의 유언장에는 사실 한 줄이 더 있었습니다. 도윤이 오늘 밤 처음 본 문장입니다.", None),
            (N, "", "\"밑바닥에서 무릎 꿇어본 사람만이, 남을 무릎 꿇리지 않는다.\"", None),
            (N, "", "다음 편, 더 좋은 이야기로 다시 찾아옵니다. 구독하고 기다려 주세요.", None),
        ],
    ),
]

SCENE_SEC = 10          # 장면당 길이(초)
CHAR_RATE = 5.5         # 초당 글자 수(한국어 낭독)
LINE_PAD = 0.4          # 줄 사이 호흡
MIN_DUR = 1.2
SECTION_TAIL = 1.5


def line_duration(text):
    chars = len(re.sub(r"\s", "", text))
    return max(MIN_DUR, chars / CHAR_RATE + LINE_PAD)


def fmt_time(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ASS_HEADER = """[Script Info]
Title: 회장님의 마지막 배달 (풀버전) 자막
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Naration,Noto Sans CJK KR,52,&H00DDDDDD,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Doyun,Noto Sans CJK KR,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Vil,Noto Sans CJK KR,60,&H0000E5FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Jung,Noto Sans CJK KR,60,&H00FFC896,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    events, scenes, ambience_prompts, emotions = [], [], [], {}
    t_video, line_no = 0.0, 0

    for sec in SECTIONS:
        # 발화 배치 (섹션 시작 + lead_in부터 순차)
        t = t_video + sec["lead_in"]
        for style, name, text, emotion in sec["lines"]:
            line_no += 1
            dur = line_duration(text)
            events.append((t, t + dur - 0.1, style, name, text))
            if emotion:
                emotions[str(line_no)] = emotion
            t += dur
        raw_span = (t - t_video) + SECTION_TAIL

        # 장면 경계에 맞춰 올림, 숏 리스트 순환
        n = max(1, math.ceil(raw_span / SCENE_SEC))
        for k in range(n):
            scenes.append(sec["shots"][k % len(sec["shots"])])
            ambience_prompts.append(sec["ambience"])
        t_video += n * SCENE_SEC
        print(f"{sec['name']}: 발화 {len(sec['lines'])}줄, {raw_span:.1f}s → 장면 {n}개")

    total = t_video
    print(f"\n합계: 자막 {line_no}줄, 장면 {len(scenes)}개, 영상 {total:.0f}초 ({total / 60:.1f}분)")

    # 1) 자막
    with open(os.path.join(ROOT, "subs", "chairman-last-delivery-full.ass"), "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, style, name, text in events:
            f.write(f"Dialogue: 0,{fmt_time(s)},{fmt_time(e)},{style},{name},0,0,0,,{text}\n")

    # 2) 장면 프롬프트
    with open(os.path.join(ROOT, "scripts", "scenes", "chairman-last-delivery-full.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": SCENE_SEC, "ratio": "16:9", "style": STYLE, "scenes": scenes},
                  f, ensure_ascii=False, indent=2)

    # 3) 오디오 설정
    audio = {
        "tts_model": "fal-ai/minimax/speech-02-hd",
        "language_boost": "Korean",
        "speed": 1.05,
        "default_voice": "Deep_Voice_Man",
        "style_voices": {"Naration": "Deep_Voice_Man", "Doyun": "Determined_Man",
                         "Vil": "Wise_Woman", "Jung": "Patient_Man"},
        "name_voices": {"미란": "Wise_Woman", "태석": "Casual_Guy",
                        "경비원": "Imposing_Manner", "관리소장": "Imposing_Manner",
                        "정 실장": "Patient_Man"},
        "style_emotions": {"Vil": "angry", "Naration": "neutral",
                           "Doyun": "neutral", "Jung": "neutral"},
        "emotion_overrides": emotions,
        "narration_styles": ["Naration"],
        "lipsync_models": ["fal-ai/sync-lipsync", "fal-ai/latentsync"],
        "ambience_model": "fal-ai/mmaudio-v2",
        "ambience_volume": 0.4,
        "ambience_prompts": ambience_prompts,
        "bgm_model": "fal-ai/lyria2",
        "bgm_prompt": "tense cinematic Korean drama orchestral score, suspenseful strings and piano, "
                      "slow build to a triumphant reveal, dramatic, instrumental only, no vocals",
        "bgm_volume": 0.22,
    }
    with open(os.path.join(ROOT, "scripts", "audio", "chairman-last-delivery-full.json"), "w", encoding="utf-8") as f:
        json.dump(audio, f, ensure_ascii=False, indent=2)

    print("생성 완료: subs/chairman-last-delivery-full.ass, "
          "scripts/scenes/chairman-last-delivery-full.json, "
          "scripts/audio/chairman-last-delivery-full.json")


if __name__ == "__main__":
    main()
