#!/usr/bin/env python3
"""회장님의 마지막 배달 — 풀버전 제작 자산 생성기 (드라마 대사 중심판).

실제 배우 드라마처럼 등장인물의 연기와 대화로만 이야기를 끌어가고,
내레이션은 쓰지 않는다. 시간 경과·장소는 화면 자막 카드(Caption)로,
설명이 필요한 배경은 인물 대사(주로 정 실장과의 대화)로 풀어낸다.
할아버지의 유언만 회상 보이스오버(입 모양 없음)로 들려준다.

생성 파일:
    scripts/scenes/chairman-last-delivery-full.json  (16:9 장면 프롬프트, 장면별 5/10초)
    subs/chairman-last-delivery-full.ass             (1920x1080 자막)
    scripts/audio/chairman-last-delivery-full.json   (목소리·감정·현장음 설정)

핵심 규칙 — 화면과 대사의 일치:
  * 같은 화자의 연속 대사(beat)마다 그 화자가 정면을 보고 말하는 전용 장면을 배정한다.
    한 장면에는 한 화자의 대사만 들어가므로, 장면 단위 립싱크에서 화면 속 인물이
    남의 대사로 입을 움직이는 일이 없다.
  * Caption(자막 카드)과 보이스오버 beat, Action(무언 연기) 장면에는
    "아무도 말하지 않는" 지시를 붙여 대사 장면과 분리한다.
  * 대사 장면 프롬프트에는 한국어 발화·입 모양 지시를 명시한다.

사용법: python3 scripts/build_full_assets.py
"""

import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# 등장인물 고정 외형 (모든 장면 프롬프트에서 동일 문구 반복 — 일관성 유지)
DOYUN = "20대 후반 한국 남성 배달 기사(짧은 검은 머리, 파란색 배달 점퍼, 검은 바지, 짜장 소스 묻은 흰 운동화)"
MIRAN = "50대 한국 여성(베이지색 트위드 명품 정장, 진주 목걸이, 단정한 올림머리)"
TAESEOK = "20대 후반 한국 남성(흰색 명품 후드티, 금목걸이, 갈색 염색머리)"
JUNG = "60대 한국 남성 비서실장(백발, 은테 안경, 검은 스리피스 정장)"
GUARD = "60대 한국 남성 경비원(회색 경비 제복, 경비 모자)"
MANAGER = "50대 한국 남성 관리소장(감색 양복, 가슴에 명찰)"
LOBBY = "대리석 바닥과 크리스탈 샹들리에가 있는 최고급 아파트 로비, 차가운 백색 조명"
HALLWAY = "고급 펜트하우스 현관"
GARAGE = "어두운 지하 주차장, 검은 고급 세단과 배달 오토바이"

# 대사 장면: 말하는 사람 한 명만, 한국어 입 모양 (립싱크 품질을 위해 정면 상반신)
TALK = ("카메라를 향해 대사에 맞춰 입을 자연스럽게 움직이며 한국어로 말하는 "
        "정면 상반신 샷, 화면에는 말하는 사람 한 명만 등장")
# 무언 장면: 인물이 있어도 입을 움직이지 않게
MUTE = "아무도 입을 움직이거나 말하지 않는 장면"

STYLE = ("시네마틱 한국 드라마, 실사 영화 화질, 동일한 인물과 의상과 장소를 "
         "모든 장면에서 유지, 자연스러운 피부 질감, 16:9 와이드 가로 구도, "
         "모든 대사와 화면 속 글자는 한국어, 영어 없음")

# 스타일: D(도윤)/V(빌런)/J(정실장)
#   N  = 보이스오버(회상 음성, 립싱크 없음, 화면은 무언 연출)
#   C  = Caption(화면 자막 카드, 소리 없음)
#   A  = Action(무언 연기 장면, name 자리에 길이 초, text 자리에 장면 프롬프트)
N, D, V, J = "Naration", "Doyun", "Vil", "Jung"
C, A = "Caption", "Action"

SECTIONS = [
    dict(
        name="콜드 오픈",
        ambience="porcelain bowl clattering, liquid splashing on marble floor, wordless shocked crowd murmur, lobby reverb",
        narration_shots=[
            f"{LOBBY}, {DOYUN}가 입주민들이 지켜보는 가운데 천천히 무릎을 꿇는 슬로우 모션, {MUTE}",
            f"{DOYUN}의 은색 손목시계 클로즈업, 8시 32분을 가리키는 시계 바늘, 긴장감 있는 연출, {MUTE}",
        ],
        speaker_shots={
            "미란": [f"{LOBBY}, {MIRAN}이 분노한 표정으로 아래를 손가락질하며 {TALK}"],
            "태석": [f"{LOBBY}, {TAESEOK}이 휴대폰을 든 채 낄낄대며 {TALK}"],
        },
        lines=[
            (A, "5", f"{LOBBY}, {MIRAN}이 {DOYUN} 앞에서 짜장면 그릇을 쏟아 검은 소스가 흰 운동화 위로 흐르는 장면, "
                     f"뒤에서 {TAESEOK}이 휴대폰으로 촬영하며 비웃는 표정, {MUTE}", None),
            (V, "미란", "무릎 꿇어. 다들 보는 데서.", "angry"),
            (V, "태석", "야 이거 봐, 진짜 꿇네.", "happy"),
            (C, "", "오후 8시 32분 — 한성그룹 이사회 발표까지 28분", None),
        ],
    ),
    dict(
        name="회상 — 유언",
        ambience="quiet traditional study room tone, fountain pen scratching on paper, distant wind chime",
        narration_shots=[
            f"고급 한옥 서재에서 백발 노인의 손이 만년필로 유언장에 서명하는 회상 장면, 세피아 톤, {MUTE}",
            f"{DOYUN}가 배달 오토바이를 타고 밤거리를 달리는 몽타주, 회상 톤, {MUTE}",
            f"야간 도시 스카이라인과 대기업 본사 빌딩 외관, 웅장한 야경, {MUTE}",
        ],
        speaker_shots={},
        lines=[
            (N, "할아버지", "밑바닥에서 90일을 버텨라. 하루라도 정체를 밝히면, 그룹 전체를 재단에 기부한다.", None),
            (C, "", "석 달 전, 한성그룹 강 회장 별세.\\N유일한 손자 강도윤, 유언에 따라 신분을 숨긴 채 90일째.", None),
        ],
    ),
    dict(
        name="8시간 전 — 도착",
        ambience="night city street ambience, motorcycle engine idling, guard booth, freight elevator hum",
        narration_shots=[
            f"밤의 강남 최고급 아파트 외관과 정문, {DOYUN}가 배달 오토바이 옆에서 헬멧을 벗는 장면, 드라마틱 야경, {MUTE}",
            f"어두운 지하 화물 엘리베이터에 배달 봉지를 들고 타는 {DOYUN}, 차가운 형광등 조명, 계급 대비 연출, {MUTE}",
        ],
        speaker_shots={
            "경비원": [f"경비실 앞에 선 {GUARD}이 근엄한 얼굴로 지하 주차장 쪽을 손으로 가리키며 {TALK}"],
            D: [f"밤의 아파트 정문 앞, 헬멧을 벗은 {DOYUN}가 담담한 표정으로 {TALK}"],
        },
        lines=[
            (C, "", "8시간 전 — 강남 한성 팰리스", None),
            (V, "경비원", "어이, 배달. 정문 아니야. 지하 화물 엘리베이터로 돌아가. 여기 사는 분들 눈에 띄면 안 돼.", "angry"),
            (D, "", "네. 알겠습니다.", None),
            (A, "5", f"어두운 지하 화물 엘리베이터에 배달 봉지를 들고 타는 {DOYUN}, 차가운 형광등 조명, 계급 대비 연출, {MUTE}", None),
        ],
    ),
    dict(
        name="4801호 첫 배달",
        ambience="apartment hallway room tone, porcelain bowl spill and splash, phone camera shutter clicks, wordless mocking snicker",
        narration_shots=[
            f"{DOYUN}의 무표정한 얼굴 클로즈업, 감정을 누르는 눈빛, {MUTE}",
        ],
        speaker_shots={
            "미란": [
                f"{HALLWAY}, {MIRAN}이 짜증난 표정으로 팔짱을 낀 채 {TALK}",
                f"{HALLWAY}, {MIRAN}이 짜장면 그릇을 든 채 단무지를 가리키며 화난 표정으로 {TALK}",
            ],
            "태석": [
                f"{HALLWAY}, 슬리퍼 차림의 {TAESEOK}이 비웃는 표정으로 {TALK}",
                f"{HALLWAY}, {TAESEOK}이 휴대폰 카메라를 들이대고 낄낄대며 {TALK}",
            ],
            D: [f"{HALLWAY}, 배달 봉지를 든 {DOYUN}가 공손하게 고개를 살짝 숙였다 들며 {TALK}"],
        },
        lines=[
            (V, "미란", "아 진짜, 왜 이렇게 늦어? 면 다 불었겠네.", "angry"),
            (D, "", "죄송합니다. 엘리베이터가 화물용밖에 안 돼서요.", None),
            (V, "미란", "그건 니 사정이고. 아니, 배달하는 애가 뭐 이렇게 말이 많아? 봉지 내려놓고 가.", "angry"),
            (V, "태석", "엄마, 이거 누구야? 짜장면 냄새 진짜. 야, 너 이 아파트 들어올 때 냄새 좀 빼고 와라. 여기 사는 사람들 격이 있어.", "happy"),
            (V, "미란", "잠깐. 너 이리 와봐. 이거 봐. 단무지가 두 개밖에 없어. 내가 세 개 시켰는데.", "angry"),
            (D, "", "확인해보겠습니다.", None),
            (V, "미란", "확인은 무슨. 너 지금 내가 거짓말한다는 거야?", "angry"),
            (A, "5", f"{HALLWAY}, {MIRAN}이 짜장면 그릇을 {DOYUN}의 발 앞에 쏟아붓는 장면, 검은 소스가 바닥에 퍼지는 클로즈업, {MUTE}", None),
            (V, "미란", "이거 치우고 가. 다시 갖고 와. 너네 사장한테 내가 누군지 말해. 한성건설 유 상무 와이프라고.", "angry"),
            (A, "5", f"{HALLWAY}, {DOYUN}가 무릎을 꿇고 손으로 짜장 소스를 닦고, {TAESEOK}이 옆에서 휴대폰으로 찍으며 웃는 장면, {MUTE}", None),
            (V, "태석", "야 이거 스토리 올려야지. 배달 거지 무릎 꿇은 거.", "happy"),
            (D, "", "다시 갖다 드리겠습니다.", None),
            (V, "미란", "당연하지. 이번엔 정문으로 올라와. 관리소장한테 내가 말해둘 테니까. 네가 무릎 꿇고 사과하는 거, 내 눈으로 제대로 보게.", "angry"),
        ],
    ),
    dict(
        name="지하 주차장 — 정 실장",
        ambience="underground parking garage ambience, low ventilation hum, car window motor, echoing footsteps",
        narration_shots=[
            f"{GARAGE}, {JUNG}이 세단 옆에서 {DOYUN}를 향해 허리 숙여 정중히 인사하는 장면, {MUTE}",
            f"{GARAGE} 와이드 샷, 오토바이와 세단 사이에 마주 선 {DOYUN}와 {JUNG}, 미스터리한 분위기, {MUTE}",
        ],
        speaker_shots={
            "정 실장": [f"{GARAGE}, 세단 옆에 반듯하게 선 {JUNG}이 고개를 들고 정중한 표정으로 {TALK}"],
            D: [f"{GARAGE}, {DOYUN}가 짜장 소스 묻은 손을 내렸다 들며 차분한 눈빛으로 {TALK}"],
        },
        lines=[
            (A, "5", f"{GARAGE}, {JUNG}이 세단 옆에서 {DOYUN}를 향해 허리 숙여 정중히 인사하는 장면, {MUTE}", None),
            (J, "정 실장", "도련님. 여덟 시간 남았습니다. 오늘 밤 아홉 시, 이사회가 새 회장을 발표합니다.", None),
            (D, "", "90일. 생각보다 길었어요.", None),
            (J, "정 실장", "회장님 유언 그대로 정체를 밝히지 않고 버티셨습니다. 이 아파트를 지은 한성건설도, 관리하는 한성자산도, 오늘 밤부터 도련님 것입니다.", None),
            (D, "", "정 실장님. 4801호.", None),
            (J, "정 실장", "유민호 상무 자택입니다. 한성건설 주택사업본부.", None),
            (D, "", "그 사람 지난 3년 실적 자료, 이사회 전에 제 책상에 올려주세요.", None),
            (J, "정 실장", "이미 준비돼 있습니다. 회장님께서 생전에 유 상무를 눈여겨보고 계셨습니다. 좋은 쪽은 아니었습니다.", None),
            (D, "", "그리고 하나 더. 이 단지 관리소장. 배달 기사 정문 출입 금지, 그거 규정에 있는 건지 아니면 누가 제멋대로 만든 건지 확인해 주세요.", None),
            (J, "정 실장", "알겠습니다.", None),
            (D, "", "이사회는 여기서 열죠. 아홉 시, 이 아파트 로비에서.", None),
            (J, "정 실장", "회장님과 똑 같으십니다.", None),
        ],
    ),
    dict(
        name="로비 재배달",
        ambience="marble lobby wordless crowd murmur, echoing footsteps, tense atmosphere, no music",
        narration_shots=[
            f"{LOBBY}, {DOYUN}가 새 짜장면 봉지를 들고 정문으로 들어서고 관리소장과 경비원 두 명이 막아서는 장면, {MUTE}",
            f"{LOBBY}, 입주민 십여 명이 무릎 꿇은 {DOYUN}를 둘러싸고 지켜보는 와이드 샷, {MUTE}",
        ],
        speaker_shots={
            "관리소장": [f"{LOBBY}, {MANAGER}이 단호한 표정으로 서류판을 든 채 {TALK}"],
            "미란": [
                f"{LOBBY}, {MIRAN}이 손가락질하며 분노한 표정으로 {TALK}",
                f"{LOBBY}, {MIRAN}의 붉어진 얼굴, 당황과 분노가 섞인 표정으로 {TALK}",
            ],
            "태석": [f"{LOBBY}, {TAESEOK}이 휴대폰을 든 채 비웃는 표정으로 {TALK}"],
            D: [f"{LOBBY}, 무릎 꿇은 {DOYUN}가 고개를 들어 차분한 표정으로 {TALK}"],
        },
        lines=[
            (C, "", "오후 8시 30분", None),
            (V, "관리소장", "4801호에서 신고가 들어왔어. 배달 기사가 입주민한테 불손했다고. 여기서 사과하고 가.", "angry"),
            (V, "미란", "무릎 꿇어. 다들 보는 데서.", "angry"),
            (D, "", "죄송합니다.", None),
            (V, "태석", "야 이거 봐, 진짜 꿇네. 엄마, 이런 애들은 이렇게 해야 돼. 지 분수를 알아야지.", "happy"),
            (V, "미란", "니 사장한테 전화해. 너 오늘부로 잘라달라고. 내 남편이 한성건설 상무야. 이 동네 배달 업체 전부 우리 쪽에서 계약 관리해. 알아?", "angry"),
            (D, "", "네. 압니다. 한성자산 계약입니다.", None),
            (V, "미란", "뭐?", "surprised"),
            (D, "", "이 단지 협력업체 계약, 한성건설이 아니라 한성자산에서 관리합니다. 상무님 소관이 아닙니다.", None),
            (A, "5", f"{LOBBY}, 입주민 십여 명이 웅성거림을 멈추고 조용해진 가운데 무릎 꿇은 {DOYUN}를 바라보는 와이드 샷, {MUTE}", None),
            (V, "미란", "이 새끼가 어디서 아는 척을.", "angry"),
        ],
    ),
    dict(
        name="아홉 시 — 신분 공개",
        ambience="automatic glass doors sliding open, many synchronized footsteps, camera flashes clicking, wordless gasps",
        narration_shots=[
            "최고급 아파트 로비의 자동문이 열리며 검은 정장의 남자들 열두 명이 줄지어 들어오는 장면, 뒤로 카메라 플래시 세례, 슬로우 모션, " + MUTE,
        ],
        speaker_shots={
            "정 실장": [f"{LOBBY}, {JUNG}이 반듯하게 서서 존경을 담은 표정으로 {TALK}"],
            "미란": [f"{LOBBY}, {MIRAN}의 창백해진 얼굴, 경악한 표정으로 더듬거리며 {TALK}"],
        },
        lines=[
            (C, "", "오후 9시 정각", None),
            (A, "5", f"{JUNG}이 무릎 꿇은 {DOYUN} 앞에서 허리를 90도로 숙여 인사하고 입주민들이 경악하는 장면, {MUTE}", None),
            (J, "정 실장", "회장님. 유언 조건 90일, 완료됐습니다. 이사회 소집 준비가 끝났습니다.", None),
            (V, "미란", "회, 회장님이라니. 무슨.", "surprised"),
            (J, "정 실장", "한성그룹 제3대 회장, 강도윤 회장님이십니다. 사모님 남편분, 유민호 상무의 최종 결재권자이십니다.", None),
            (A, "5", f"{MIRAN}이 입을 벌린 채 뒤로 물러나고 {TAESEOK}의 휴대폰이 바닥에 떨어지는 장면, {MUTE}", None),
            (A, "5", f"{DOYUN}가 일어서서 무릎의 먼지를 터는 장면, 위엄 있는 분위기 전환, {MUTE}", None),
        ],
    ),
    dict(
        name="심판",
        ambience="stunned lobby silence, wordless gasps and murmurs, paper envelope rustle, quiet sobbing",
        narration_shots=[
            f"{TAESEOK}이 몸을 떨며 고개를 숙이는 장면, {MUTE}",
        ],
        speaker_shots={
            D: [
                f"{LOBBY}, {DOYUN}가 서류 봉투를 든 채 위엄 있는 표정으로 {TALK}",
                f"{DOYUN}의 얼굴 클로즈업, 차갑고 단호한 눈빛으로 {TALK}",
            ],
            "미란": [
                f"{LOBBY}, {MIRAN}의 창백해진 얼굴, 두려움에 떨리는 표정으로 {TALK}",
                f"{LOBBY}, {MIRAN}이 무릎을 꿇고 두 손을 모아 애원하는 표정으로 {TALK}",
                f"{LOBBY}, {MIRAN}의 창백해진 얼굴, 두려움에 떨리는 표정으로 {TALK}",
            ],
            "태석": [f"{LOBBY}, {TAESEOK}이 몸을 떨며 사색이 된 얼굴로 더듬거리며 {TALK}"],
            "관리소장": [f"{LOBBY}, {MANAGER}이 진땀을 흘리며 어쩔 줄 몰라 하는 표정으로 {TALK}"],
        },
        lines=[
            (D, "", "유민호 상무. 주택사업본부. 지난 3년 협력업체 선정 과정에서 리베이트 수수 정황 열한 건. 그중 여섯 건이 이 단지 공사입니다.", None),
            (D, "", "사모님. 남편분이 이 아파트 어떻게 샀는지 아세요?", None),
            (V, "미란", "그, 그건.", "fearful"),
            (D, "", "모르셨으면 오늘 아시게 될 겁니다. 감사실이 지금 4801호로 올라가고 있습니다.", None),
            (D, "", "그리고 오태석 대리. 오늘 아버지 회사 배달 기사 무릎 꿇린 영상 두 개 찍으셨죠. 그거 이미 회사 윤리위원회에 제출됐습니다. 본인 계정에서 올린 걸 캡처했으니까 부인은 안 될 겁니다.", None),
            (V, "태석", "저, 저는 몰랐습니다. 회장님인 줄 알았으면.", "fearful"),
            (D, "", "그게 문제예요. 회장인 줄 알았으면 안 그랬을 거라는 거. 그러니까 회장 아닌 사람한테는 그래도 된다는 거잖아요.", None),
            (D, "", "관리소장님. 배달 기사 정문 출입 금지 규정. 한성자산 관리규정에 그런 조항 없습니다. 누가 만든 겁니까?", None),
            (V, "관리소장", "4801호 사모님이 입주민 대표라서, 요청하셔서.", "fearful"),
            (D, "", "오늘부로 폐지합니다. 그리고 소장님은 내일 아침 한성자산 인사팀으로 출근하세요. 이 단지, 오늘부터 한성자산이 직접 관리합니다. 입주민 대표 선출 다시 합니다.", None),
            (V, "미란", "회장님, 제발. 저희 남편은 잘못 없어요. 제가 잘못했어요. 저는 그냥, 배달하는 애가.", "sad"),
            (D, "", "배달하는 애. 맞아요. 저 지난 90일 동안 배달하는 애였습니다. 그 90일 동안 저한테 짜장면 부은 사람, 사모님이 처음은 아니었어요.", None),
            (V, "미란", "그, 그럼.", "fearful"),
            (D, "", "근데 무릎 꿇으라고 한 건 사모님이 처음이었습니다.", None),
            (D, "", "이사회 시작하죠. 첫 안건, 유민호 상무 직위해제.", None),
        ],
    ),
    dict(
        name="에필로그 — 마지막 배달",
        ambience="night street ambience, motorcycle starting and riding away, wind, dawn birds at quiet hillside",
        narration_shots=[
            f"밤거리, {DOYUN}가 배달 오토바이를 타고 떠나는 뒷모습, 도시 야경 보케, {MUTE}",
            f"새벽 산 중턱의 산소 앞, 배달 기사 복장의 {DOYUN}가 짜장면을 내려놓고 고개 숙이는 장면, 일출, 감성적인 엔딩, {MUTE}",
        ],
        speaker_shots={
            D: [f"{LOBBY}, {DOYUN}가 헬멧을 손에 든 채 잔잔한 미소로 {TALK}"],
            "정 실장": [f"{LOBBY}, {JUNG}이 존경 어린 표정으로 {TALK}"],
        },
        lines=[
            (C, "", "한 시간 뒤", None),
            (A, "10", f"{LOBBY}, 정장 차림의 중년 남성 임원이 감사실 직원들과 함께 걸어 나오다 무릎 꿇은 아내와 아들을 보고 멈춰 서고, "
                      f"그 앞에 짜장 소스 묻은 운동화를 신은 {DOYUN}가 서 있는 장면, {MUTE}", None),
            (D, "", "정 실장님. 오토바이는 제가 몰고 갈게요. 마지막 배달 하나 남았어요.", None),
            (J, "정 실장", "어디로 가십니까?", None),
            (D, "", "할아버지 산소요. 짜장면 좋아하셨거든요.", None),
            (N, "할아버지", "밑바닥에서 무릎 꿇어본 사람만이, 남을 무릎 꿇리지 않는다.", None),
            (C, "", "— 다음 편에 계속 —", None),
        ],
    ),
]

CHAR_RATE = 5.5         # 초당 글자 수(한국어 낭독)
LINE_PAD = 0.4          # 줄 사이 호흡
MIN_DUR = 1.2
CAPTION_MIN = 2.4       # 자막 카드 최소 노출 시간
BEAT_LEAD = 0.4         # beat 시작 전 호흡
BEAT_TAIL = 0.6         # beat 끝 호흡


def line_duration(style, text):
    chars = len(re.sub(r"\s", "", text.replace("\\N", " ")))
    dur = max(MIN_DUR, chars / CHAR_RATE + LINE_PAD)
    return max(dur, CAPTION_MIN) if style == C else dur


def beat_scene_sizes(need):
    """beat 길이(need초)를 5/10초 장면 조합으로 덮는 최소 낭비 조합을 돌려준다."""
    sizes = [10] * int(need // 10)
    rem = need - 10 * len(sizes)
    if rem > 5:
        sizes.append(10)
    elif rem > 0.01 or not sizes:
        sizes.append(5)
    return sizes


def build_beats(lines):
    """연속된 같은 화자의 줄들을 beat로 묶는다. Action은 단독 beat가 된다.

    Caption과 보이스오버(Naration)는 무언 연출 장면을 쓰므로 'N' beat로 묶는다.
    """
    beats = []
    for style, name, text, emotion in lines:
        if style == A:
            beats.append({"key": "ACT", "size": int(name), "prompt": text})
            continue
        key = "N" if style in (N, C) else (name or style)
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
Title: 회장님의 마지막 배달 (풀버전) 자막
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Naration,Noto Sans CJK KR,52,&H00DDDDDD,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Caption,Noto Sans CJK KR,46,&H00E8E8E8,&H000000FF,&H00000000,&H96000000,-1,-1,0,0,100,100,0,0,1,4,2,8,200,200,70,1
Style: Doyun,Noto Sans CJK KR,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Vil,Noto Sans CJK KR,60,&H0000E5FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Jung,Noto Sans CJK KR,60,&H00FFC896,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1

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
                scene_items.append({"prompt": beat["prompt"], "duration": beat["size"]})
                ambience_prompts.append(sec["ambience"])
                t_video += beat["size"]
                continue

            t = t_video + BEAT_LEAD
            for style, name, text, emotion in beat["lines"]:
                if style != C:
                    tts_no += 1        # TTS는 Caption을 건너뛰므로 번호도 건너뛴다
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
                    prompt = shots[narr_idx % len(shots)]
                    narr_idx += 1
                else:
                    k = spk_idx.get(key, 0)
                    prompt = shots[k % len(shots)]
                    spk_idx[key] = k + 1
                scene_items.append({"prompt": prompt, "duration": size})
                ambience_prompts.append(sec["ambience"])
                t_video += size

        print(f"{sec['name']}: 발화 {n_lines}줄 → {t_video - sec_start:.0f}초")

    total = t_video
    n5 = sum(1 for s in scene_items if s["duration"] == 5)
    n10 = len(scene_items) - n5
    print(f"\n합계: 자막 {len(events)}줄(TTS {tts_no}줄), 장면 {len(scene_items)}개 "
          f"(5초 {n5} + 10초 {n10}), 영상 {total:.0f}초 ({total / 60:.1f}분)")

    # 1) 자막
    with open(os.path.join(ROOT, "subs", "chairman-last-delivery-full.ass"), "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, style, name, text in events:
            f.write(f"Dialogue: 0,{fmt_time(s)},{fmt_time(e)},{style},{name},0,0,0,,{text}\n")

    # 2) 장면 프롬프트 (장면별 5/10초)
    with open(os.path.join(ROOT, "scripts", "scenes", "chairman-last-delivery-full.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": 10, "ratio": "16:9", "style": STYLE, "scenes": scene_items},
                  f, ensure_ascii=False, indent=2)

    # 3) 오디오 설정
    audio = {
        "tts_model": "fal-ai/minimax/speech-02-hd",
        "language_boost": "Korean",
        "speed": 1.05,
        "default_voice": "Determined_Man",
        "style_voices": {"Naration": "Deep_Voice_Man", "Doyun": "Determined_Man",
                         "Vil": "Wise_Woman", "Jung": "Patient_Man"},
        "name_voices": {"미란": "Wise_Woman", "태석": "Casual_Guy",
                        "경비원": "Imposing_Manner", "관리소장": "Imposing_Manner",
                        "정 실장": "Patient_Man", "할아버지": "Deep_Voice_Man"},
        "style_emotions": {"Vil": "angry", "Naration": "neutral",
                           "Doyun": "neutral", "Jung": "neutral"},
        "emotion_overrides": emotions,
        "narration_styles": ["Naration"],
        "silent_styles": ["Caption"],
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
