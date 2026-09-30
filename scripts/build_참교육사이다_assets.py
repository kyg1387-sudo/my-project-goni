#!/usr/bin/env python3
"""[참교육 사이다] 요양보호사가 알고 보니 3천억 수산그룹 상속자 — 제작 자산 생성기.

docs/대본-참교육사이다-사투리버전.md(완결 대본) + 사용자가 확정한 타입캐스트
배역 캐스팅을 기반으로, build_full_assets.py와 같은 방식(섹션별 대사/내레이션 +
숏 리스트, 발화 길이 기반 자막 타이밍)으로 세 파일을 생성한다:

    scripts/scenes/참교육사이다.json  (16:9 장면 프롬프트)
    subs/참교육사이다.ass             (1920x1080 자막)
    scripts/audio/참교육사이다.json   (목소리·감정·현장음 설정 — 전 배역 Typecast)

타이밍 규칙: 줄 길이(공백 제외 글자 수)/5.5 + 0.4초, 최소 1.2초. 섹션별 발화
구간을 5초 장면 경계에 맞춰 올림하고, 남는 시간은 섹션 끝의 연출 호흡으로 둔다.
장면은 카메라 구도를 순환시키며 확장해(expand_shots) 정면 고정 반복을 피한다.

사용법: python3 scripts/build_참교육사이다_assets.py
"""

import json
import math
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# 등장인물 고정 외형 (모든 장면 프롬프트에서 동일 문구 반복 — 일관성 유지, 규칙 5)
DOHEE = ("20대 후반 한국 여성 요양보호사(둥근 얼굴, 단정하게 묶은 짧은 검은 생머리, "
         "베이지색 요양보호사 유니폼 조끼와 흰 셔츠, 가슴에 아무 글자도 없는 매끈한 흰색 "
         "명찰을 달고 있음, 단단하고 절제된 눈빛)")
CHAIRMAN = ("70대 한국 남성 재벌 회장(마르고 깊은 주름이 팬 얼굴, 짧게 다듬은 백발, "
            "짙은 남색 실크 환자용 가운, 형형하고 맑은 눈빛)")
EOMMA = ("50대 중반 한국 여성, 중년이지 노인이 아님(둥글고 지친 얼굴, 짧은 파마머리로 "
         "대부분 검은 머리에 흰머리는 약간만 섞임, 낡은 꽃무늬 카디건)")
MIRYEONG = ("30대 한국 여성 상무(날렵한 얼굴형, 어깨 길이 스트레이트 검은 머리, "
            "짙은 남색 정장 재킷, 차갑고 표독스러운 표정)")
JUNHYUK = "30대 한국 남성 전무(각진 턱선, 깔끔하게 넘긴 검은 머리, 회색 슬림핏 수트, 오만한 표정)"
SANAE = "건장한 한국인 남성 사내 여러 명(전형적인 한국인 얼굴 특징, 어두운 색 작업 점퍼, 짧게 깎은 머리, 거친 인상, 동일한 복장 유지)"
HAEGYEONG = "50대 한국 남성 해양경찰 수사관(짧은 반백머리, 각진 얼굴, 감청색 해양경찰 정복, 무거운 표정)"

FUNERAL = "목포 대형 장례식장 빈소, 흰 국화 화환이 늘어선 엄숙한 실내, 차분하고 서늘한 조명"
SICKROOM = "고급스럽지만 차분한 목포 해안가 저택 병실, 큰 창밖으로 바다가 보임, 은은한 오후 햇살"
DOHEE_HOME = "낡은 서민 아파트의 좁은 부엌 겸 거실, 형광등 조명, 생활감 있는 살림살이"
WAREHOUSE = "목포항 버려진 냉동창고 내부, 녹슨 선반과 어두운 조명, 서늘하고 음산한 분위기"
BOARDROOM = "해진수산 대형 이사회 회의실, 긴 원목 테이블과 통유리창, 차갑고 딱딱한 조명"
HARBOR = "목포 앞바다가 보이는 항구 부두, 새로 진수한 구조선이 정박, 맑은 아침 햇살"

STYLE = ("시네마틱 한국 드라마, 실사 영화 화질, 동일한 인물과 의상과 장소를 "
         "모든 장면에서 유지, 자연스러운 피부 질감, 16:9 와이드 가로 구도, "
         "지시된 인물 외 임의 등장 인물 없음, 화면 속에 새겨지거나 쓰인 글자 없음, "
         "소품이나 서류는 항상 인물의 손에 쥐어진 채로만 등장하고 허공에 떠 있지 않음")

# 카메라 문법(영화제작규칙집.md 7장) — 정면 고정 샷만 반복되지 않도록 장면마다 순환 적용
CAMERA_VARIANTS = [
    "로우 앵글에서 인물을 향해 천천히 달리 인 하며",
    "인물 주위를 곡선으로 도는 아크 샷으로",
    "인물 어깨 높이에서 뒤따르는 팔로우 샷으로",
    "핸드헬드로 미세하게 흔들리는 구도로",
    "하이 앵글로 인물을 내려다보며",
    "인물 옆에서 나란히 움직이는 사이드 트래킹으로",
    "정지된 카메라로 고정된 채",
    "인물에게 슬로우 줌인 하며",
    "더치 앵글로 살짝 기울어진 구도로",
    "인물 뒤에서 고정된 리어 샷으로",
    "인물에게서 서서히 물러나는 리버스 트래킹으로",
    "카메라가 천천히 올라가는 크레인 업으로",
]


def expand_shots(shots, n):
    """섹션의 원래 shots(내용 순서 보장)를 카메라 구도를 바꿔가며 정확히 n개로
    확장한다. 시간 비율에 맞춰 내용을 매핑하므로 화자 정렬은 그대로 유지되고,
    같은 내용이 이어져도 매 컷 카메라가 달라 정면 고정 반복을 피한다."""
    out = []
    for i in range(n):
        content = shots[min(int(i * len(shots) / n), len(shots) - 1)]
        cam = CAMERA_VARIANTS[i % len(CAMERA_VARIANTS)]
        out.append(f"{cam}, {content}")
    return out

# 화자 이름 → 고정 외형 문구 (qc_speaker_alignment.py가 그대로 import해서 재사용 —
# 두 파일에 같은 문구를 따로 옮겨 적으면 한쪽만 고쳤을 때 어긋난다, EP3 교훈: DOHEE
# 상수/QC 마커 desync 실증)
MARKERS = {
    "한도희": DOHEE, "서회장": CHAIRMAN, "엄마": EOMMA, "서미령": MIRYEONG,
    "서준혁": JUNHYUK, "사내": SANAE, "목포해경": HAEGYEONG,
}
# 내레이션·녹음/영상 속 목소리 스타일: 화면에 실제 화자가 안 보여도 됨(규칙 4)
NO_ONSCREEN_REQUIRED = {"Naration", "JunhyukRec", "ChairmanVideo"}


def validate_speaker_alignment(events, scenes, scene_sec):
    """자막의 각 대사 시간대에, 그 시각 장면 프롬프트에 실제 화자 마커가 있는지 검사한다.

    EP3 교훈 ⑰: shots 순환/시간비율 확장 방식은 대사가 컷 경계를 넘어가며 화자
    없는 컷에 얹히는 사고가 실제로 여러 번 났다 — 빌드 자체를 SystemExit로 막아
    화자-화면 불일치 자산이 커밋되는 일을 원천 차단한다(경고만 남기고 넘어가지 않음).
    """
    mismatches = []
    for i, (start, _end, style, name, text) in enumerate(events, 1):
        if style in NO_ONSCREEN_REQUIRED:
            continue
        scene_idx = int(start // scene_sec)
        if scene_idx >= len(scenes):
            mismatches.append((i, start, name, text, scene_idx, "장면 범위 초과"))
            continue
        marker = MARKERS.get(name)
        if marker is None:
            mismatches.append((i, start, name, text, scene_idx, f"화자 '{name}' 마커 정의 없음"))
        elif marker not in scenes[scene_idx]:
            mismatches.append((i, start, name, text, scene_idx, "장면에 화자 마커 없음"))

    if mismatches:
        print(f"\n화자-장면 정렬 실패: 불일치 {len(mismatches)}건")
        for i, start, name, text, scene_idx, reason in mismatches:
            m, s = divmod(start, 60)
            print(f"  [{i:02d}] {int(m)}:{s:05.2f} 화자={name} 장면#{scene_idx + 1} — {reason}")
            print(f"       대사: {text[:50]}")
        raise SystemExit(
            "빌드 중단 — 화자-장면 불일치가 있는 자산은 저장하지 않습니다. "
            "SECTIONS의 shots 배정을 고친 뒤 다시 실행하세요."
        )
    print(f"화자-장면 정렬 검증 통과 (대사 {len(events)}줄 중 불일치 0건)")


# (스타일, 화자이름, 대사, 감정|None)
# N=내레이션 H=한도희 C=서해진회장 M=엄마 R=서미령 J=서준혁 S=사내 P=목포해경
# JR/CV=녹음·영상 속 목소리(화면에 실제 인물이 안 보여도 되는 구간 — narration_styles에
# 포함시켜 립싱크 대상에서 제외. 규칙 4: 립싱크는 화면에 나온 인물 대사에만 적용)
N, H, C, M, R, J, S, P = "Naration", "Dohee", "Chairman", "Eomma", "Miryeong", "Junhyuk", "Sanae", "Haegyeong"
JR, CV = "JunhyukRec", "ChairmanVideo"

SECTIONS = [
    dict(
        name="콜드 오픈",
        lead_in=1.5,
        ambience="quiet funeral hall murmur, hushed whispers, distant weeping, incense smoke undertone, no music",
        shots=[
            f"{FUNERAL}, {MIRYEONG}가 {DOHEE}의 뺨을 세게 올려붙이는 순간, 조문객들이 놀라 술렁이는 장면",
            f"{FUNERAL}, 바닥에 쓰러질 듯 휘청이다 다시 꼿꼿이 서는 {DOHEE}의 클로즈업, 입술에서 피가 살짝 비침",
            f"{FUNERAL}, 영정 사진 속 {CHAIRMAN}을 올려다보는 {DOHEE}의 옆모습, 슬픔을 억누른 표정",
            f"{FUNERAL}, 피 묻은 입술을 손등으로 닦으며 담담히 말하는 {DOHEE}의 클로즈업",
            f"{FUNERAL}, 조문객들 사이에서 흔들림 없이 서 있는 {DOHEE}의 단단한 눈빛, 여운 있는 홀드",
        ],
        lines=[
            (R, "서미령", "요양보호사 주제에 어디서 상주 완장을 차고 설쳐? 당장 꺼져!", "angry"),
            (N, "", "목포 최대 재벌, 삼천억 자산의 해진수산 서해진 회장의 장례식장. 조문객들이 수군거리는 가운데 뺨을 맞은 스물아홉 살 요양보호사 한도희.", None),
            (N, "", "하지만 이 자리에 있는 사람 중 아무도 모릅니다. 사흘 전, 회장이 이 여자를 법적인 딸로 입양했다는 사실을. 그리고 육십일 뒤 이사회에서, 이 여자가 회장을 죽인 진짜 범인을 끌어내릴 거라는 사실을요.", None),
            (H, "한도희", "상무님. 지금 누구 얼굴에 손을 올리신 건지, 딱 두 달 뒤에 똑똑히 알게 될 겁니다.", "neutral"),
        ],
    ),
    dict(
        name="분노 — 바닥의 삶",
        lead_in=1.5,
        ambience="small apartment kitchen room tone, refrigerator hum, distant early morning street, no music",
        shots=[
            f"{DOHEE_HOME}, 지친 얼굴로 새벽에 귀가한 {DOHEE}가 식탁 위 빈 봉투를 발견하고 멈춰 서는 장면",
            f"{DOHEE_HOME}, 빈 봉투를 사이에 두고 마주 선 {DOHEE}와 {EOMMA}의 투샷, 무거운 침묵",
            f"{DOHEE_HOME}, 눈을 피하며 딴청 부리듯 설거지하는 {EOMMA}의 뒷모습, 목소리만 날카로움",
            "칠흑같이 어두운 밤바다에 몰아치는 거센 파도, 인물 없음, 회상 톤",
            "낡은 구인 공고지 클로즈업, 손글씨로 급히 적은 채용 조건, 인물 없음",
            f"면접실 책상 앞, {MIRYEONG}가 이력서를 손끝으로 툭 밀어내며 냉담하게 바라보는 장면",
            f"면접실, {MIRYEONG}가 이력서를 바닥에 던지고 {DOHEE}가 무표정하게 듣는 투샷",
            f"면접실 바닥에 떨어진 이력서를 말없이 주워드는 {DOHEE}의 손 클로즈업",
        ],
        lines=[
            (N, "", "두 달 전. 도희는 새벽 네 시에 요양원 야간 근무를 마치고 집에 돌아옵니다. 식탁 위엔 빈 봉투 하나.", None),
            (H, "한도희", "엄마… 이번 달 월급 또 가져갔어?", "sad"),
            (M, "엄마", "워매… 딸년 돈이 엄니 돈이제, 누구 돈이다냐? 니가 해경서 짤리지만 안 했어도, 우리가 요로코롬 궁상떨고 살겄냐?", "angry"),
            (N, "", "도희는 한때 해양경찰 특공대 최연소 여성 대원이었습니다. 하지만 십 년 전 어느 폭풍우 치던 밤, 구조에 실패했다는 이유로 모든 책임을 뒤집어쓰고 옷을 벗었죠. 그날 이후 도희의 인생은 바다 밑바닥에 가라앉았습니다.", None),
            (N, "", "그러던 어느 날, 파격적인 조건의 채용 공고. 해진수산 회장의 전담 요양보호사, 월급 팔백만 원. 면접장에서 도희를 맞은 건 회장의 의붓딸 서미령이었습니다.", None),
            (R, "서미령", "해경 출신? 잘린 거잖아. 우리 엄마는 치매야. 기저귀 갈고 밥 떠먹이면 돼. 아, 그리고 그 촌스러운 사투리 우리 집에선 쓰지 마. 엄마 치매 더 심해지니까.", "angry"),
            (N, "", "평생 목포에서 살아온 회장의 딸이, 목포 말을 촌스럽다고 합니다. 미령은 도희의 이력서를 바닥에 던졌고, 도희는 말없이 그걸 주웠습니다. 돈이 필요했으니까요.", None),
        ],
    ),
    dict(
        name="반전 — 치매가 아니었다",
        lead_in=1.5,
        ambience="quiet sickroom room tone, distant ocean waves through window, soft medical equipment hum, no music",
        shots=[
            f"{SICKROOM}, 창밖 바다만 하루 종일 바라보는 {CHAIRMAN}의 옆모습, 무표정",
            f"{SICKROOM}, 약통을 정리하던 {DOHEE}가 알약 색이 처방전과 다른 것을 발견하고 눈을 가늘게 뜨는 클로즈업",
            f"{SICKROOM}, 등 뒤에서 또렷한 목소리로 말을 거는 {CHAIRMAN}과 놀라 돌아보는 {DOHEE}의 투샷",
            f"{SICKROOM}, 침대에 걸터앉아 담담히 말하는 {CHAIRMAN}의 클로즈업, 형형한 눈빛",
            f"{SICKROOM}, {CHAIRMAN}과 그 앞에 선 {DOHEE}가 마주보고 대화하는 투샷",
            f"{SICKROOM}, 회상하는 눈빛으로 창밖을 보며 말하는 {CHAIRMAN}의 클로즈업",
            f"{SICKROOM}, {CHAIRMAN}의 말을 듣고 놀란 표정으로 굳는 {DOHEE}의 클로즈업",
        ],
        lines=[
            (N, "", "출근 첫날부터 이상했습니다. 회장은 하루 종일 창밖 바다만 바라보며 한마디도 하지 않았죠. 그런데 사흘째 밤, 약을 챙기던 도희의 눈에 들어온 것. 알약의 색이 처방전과 미묘하게 달랐습니다.", None),
            (N, "", "도희는 약 한 알을 몰래 주머니에 넣었습니다. 그 순간, 등 뒤에서 들려온 또렷한 목소리.", None),
            (C, "서회장", "아가, 고것을 챙겨가꼬… 뭣에 쓸라고 그라냐? 석 달째 그 약을, 먹는 척허고 혓바닥 밑에 숨겨서 뱉어부렀어야… 그란디도 손발이 덜덜 떨리는 거 봉께, 먹는 국물에다가도 뭘 탄갑소. 근디 니는, 들어온 지 사흘 만에 딱 알아채부렀네. 내가 사람 하나는, 기가 맥히게 잘 골랐당깨.", "surprised"),
            (H, "한도희", "…처음부터 저를 알고 부르신 거예요?", "surprised"),
            (C, "서회장", "십 년 전 그 칠흑 같은 비바람 몰아치던 밤… 뒤집힌 요트 밑창으로 기어들어가서 내 외손주 끝까지 건져낼라고 발버둥 치던 해경. 고것이 바로, 니 아니었냐?", "sad"),
        ],
    ),
    dict(
        name="눈물 — 여섯 번의 잠수",
        lead_in=1.0,
        ambience="quiet sickroom room tone, muffled crying, soft ocean waves, no music",
        shots=[
            f"{SICKROOM}, 손을 떨기 시작하는 {DOHEE}의 클로즈업, 눈에 눈물이 고임",
            f"{SICKROOM}, {DOHEE}가 무너지듯 고개를 숙이고 흐느끼는 장면",
            f"{SICKROOM}, 흐느끼는 {DOHEE}를 {CHAIRMAN}이 안타깝게 바라보는 투샷",
            f"{SICKROOM}, {CHAIRMAN}이 진지한 눈빛으로 위로하듯 말하는 클로즈업",
            f"{SICKROOM}, {CHAIRMAN}과 {DOHEE}가 나란히 앉아 말없이 서로를 바라보는 투샷",
            f"{SICKROOM}, {CHAIRMAN}이 서랍에서 서류 봉투를 꺼내는 클로즈업",
            f"{SICKROOM}, {CHAIRMAN}이 서류 봉투를 {DOHEE}에게 내밀며 담담히 말하는 투샷",
            f"입양 서류를 떨리는 손으로 받아드는 {DOHEE}의 클로즈업, {CHAIRMAN}의 손이 살짝 함께 보임",
        ],
        lines=[
            (N, "", "도희의 손이 떨리기 시작합니다. 그날 밤, 뒤집힌 요트 안에 갇혀 있던 열여섯 살 소년. 도희는 목숨을 걸고 여섯 번이나 차가운 바다에 뛰어들었지만, 끝내 아이를 살리지 못했습니다.", None),
            (H, "한도희", "회장님… 지가요… 지가 쪼끔만 더 빨랐으믄… 그 어린것을 살렸을 것인디…", "sad"),
            (N, "", "십 년 동안 숨겨왔던 고향 말이, 울음과 함께 터져 나옵니다.", None),
            (C, "서회장", "울지 마라, 아가. 해경 수색일지 내가 진작에 싹 다 훑어봤어야. 아무도 그 거친 물에 안 들어갈라고 배 위에서 구경만 헐 때, 니 혼자 갈비뼈가 부러져감서 여섯 번을 들어갔어. 우리 민우가 눈 감기 전에 마지막으로 맞잡은 따뜻한 온기가… 니 손이었당깨.", "sad"),
            (N, "", "십 년 동안 한 번도 울지 못했던 도희가, 처음으로 소리 내어 울었습니다. 그리고 회장이 내민 서류 한 장.", None),
            (C, "서회장", "고 요트, 사고가 아니여. 누가 연료관을 싹 잘라놨드라. 내 핏줄이 없어지믄 누가 젤로 이득 보겄냐? 의붓자식 준혁이허고 미령이여. 도희야. 내 딸 해라잉. 입양 서류여. 내가 죽고 육십일 뒤 이사회에서, 니가 고것들 끝장내부러라.", "neutral"),
        ],
    ),
    dict(
        name="사이다 — 협박",
        lead_in=1.5,
        ambience="corporate hallway tense murmur, camera flashes, distant funeral hall echo, no music",
        shots=[
            f"장례식장 복도, 하얗게 질린 얼굴로 마주 선 {JUNHYUK}과 {MIRYEONG}, 무거운 분위기",
            f"장례식장 복도, {JUNHYUK}이 {DOHEE} 앞을 가로막고 차갑게 위협하는 장면",
            f"{JUNHYUK}의 오만한 표정 클로즈업, 뒤로 {MIRYEONG}가 팔짱 끼고 서 있음",
            "밤길, 도로를 달리는 자동차 헤드라이트, 뒤로 검은 승합차가 바짝 따라붙는 장면, 미스터리한 긴장감",
        ],
        lines=[
            (N, "", "그리고 일주일 뒤, 회장은 조용히 눈을 감았습니다. 장례식장에서 입양 사실이 공개되자, 미령과 준혁의 얼굴이 하얗게 질렸죠.", None),
            (J, "서준혁", "치매 노인 구워삶아 호적에 오른 꽃뱀 년이 어딜 까불어? 너 이사회 날까지 살아서 걸어갈 수 있을 것 같아?", "angry"),
            (N, "", "그 말은 협박이 아니라 예고였습니다. 발인 다음 날 밤, 도희의 차를 덩치 큰 사내 다섯이 둘러쌉니다. 목포항 버려진 냉동 창고로 끌려간 도희.", None),
        ],
    ),
    dict(
        name="사이다 — 냉동창고",
        lead_in=1.0,
        ambience="abandoned cold storage warehouse ambience, metal door creaking, distant foghorn, tense silence then scuffle",
        shots=[
            f"{WAREHOUSE}, {DOHEE}가 두 손으로 각서 한 장을 쥐고 내려다보는 가운데, "
            f"{SANAE}이 주위를 둘러싼 장면, 서류는 도희 손에서 떨어지지 않고 고정",
            f"{WAREHOUSE}, {DOHEE}가 순식간에 몸을 돌려 {SANAE} 중 한 명을 제압하는 액션 컷, 모션 블러",
            f"{WAREHOUSE}, 바닥에 쓰러진 {SANAE}과 그 사이에 태연히 선 {DOHEE}",
            f"{WAREHOUSE}, {DOHEE}가 쓰러진 사내의 휴대폰을 주워 화면을 확인하며 전화를 거는 클로즈업",
            f"{WAREHOUSE} 출입구, {DOHEE}가 유유히 걸어 나가는 뒷모습, 여운 있는 조명",
        ],
        lines=[
            (S, "사내", "아따 아가씨, 상속 포기 각서에 지장 딱 찍어부러. 안 그라믄 오늘 밤 산 채로 저 시커먼 앞바다 물고기 밥 되는 것이여.", "angry"),
            (H, "한도희", "바다요? 아재. 나가 저 바다서 십 년 묵고 산 사람이요.", "happy"),
            (N, "", "해경 특공대 제압술. 삼십 초 만에 다섯 명이 바닥을 구릅니다.", None),
            (S, "사내", "워매… 요것이 뭔 요양보호사여… 사람 때려잡는 인간 병기제…", "fearful"),
            (N, "", "도희는 쓰러진 사내의 휴대폰을 집어 듭니다. 마지막 통화 기록, '서준혁 전무님'.", None),
            (H, "한도희", "전무님. 보내신 분들, 지금 다 누워 계세요. 다음엔 좀 튼튼한 분들로 보내주세요.", "happy"),
        ],
    ),
    dict(
        name="눈물 — 엄마의 선택",
        lead_in=1.5,
        ambience="tense boardroom silence, papers shuffling, distant sob, no music",
        shots=[
            f"{BOARDROOM} 앞 복도, {MIRYEONG}가 {EOMMA}에게 봉투를 내밀며 회유하는 장면",
            f"{BOARDROOM} 앞 복도, 봉투를 받아든 {EOMMA}의 놀란 얼굴 클로즈업, {MIRYEONG}와 투샷",
            f"{BOARDROOM}, 증인석에 선 {EOMMA}의 굳은 얼굴, 긴 테이블에 둘러앉은 임원들",
            f"{BOARDROOM}, 차마 엄마를 쳐다보지 못하는 {DOHEE}의 옆모습, {EOMMA}가 멀리 증인석에 보임",
            f"{BOARDROOM}, 일그러지는 {MIRYEONG}의 얼굴과 말을 잇는 {EOMMA}의 투샷",
            f"{BOARDROOM}, {EOMMA}가 눈물을 흘리며 절규하듯 말하는 클로즈업",
            f"{BOARDROOM}, {EOMMA}와 {DOHEE}의 투샷, {DOHEE}의 눈에 눈물이 고이기 시작",
            f"{BOARDROOM}, 눈물을 쏟는 {DOHEE}의 클로즈업, {EOMMA}가 함께 프레임에 보임",
        ],
        lines=[
            (N, "", "힘으로 안 되자, 미령은 가장 잔인한 카드를 꺼냅니다. 바로 도희의 엄마였죠.", None),
            (R, "서미령", "어머니, 이사회에서 딱 한마디만 하시면 돼요. 딸이 처음부터 재산 노리고 회장님 속였다고. 그럼 오억 드릴게요.", "neutral"),
            (M, "엄마", "오억이요? 오메… 고것이 참말이요?", "surprised"),
            (N, "", "이사회 당일. 증인석에 선 도희의 엄마. 도희는 차마 엄마를 쳐다보지 못합니다. 평생 딸의 돈을 가져갔던 사람. 이번에도 딸을 팔 거라고, 도희는 생각했습니다.", None),
            (M, "엄마", "지가요… 저 서울 사모님헌티 돈 오억 받기로 약조를 했었어라. 우리 딸이 사기 쳐서 노인네 홀렸다고 거짓말 쳐주믄, 돈방석 앉혀준다고 꼬드기드만요.", "neutral"),
            (N, "", "회의장이 술렁입니다. 미령의 얼굴이 일그러지죠.", None),
            (M, "엄마", "근디요…! 나가 평생 이 불쌍한 딸년 등골을 파먹고 살았는디… 이번엔 도저히 못 팔아먹겄소! 이 아그가 어떤 아그인디! 남의 집 귀한 새끼 살리겄다고 얼어 죽을 바다에 제 목숨 던졌다가 버려진, 불쌍한 내 딸이여라! 도희야… 애미가 잘못했다… 참말로 죽을죈디, 용서해라 도희야…!", "sad"),
            (H, "한도희", "엄마…", "sad"),
            (N, "", "스물아홉 해 만에 처음 들어보는, 엄마의 사과였습니다.", None),
        ],
    ),
    dict(
        name="권선징악 — 마지막 녹음",
        lead_in=1.0,
        ambience="tense boardroom silence, recording playback static, gasps, door opening, handcuffs clinking",
        shots=[
            f"{BOARDROOM}, {JUNHYUK}이 테이블을 내리치며 소리치고 {DOHEE}가 침착하게 마주보는 투샷",
            f"{BOARDROOM} 테이블 위, 낡은 블랙박스에서 재생 표시등이 켜지는 클로즈업, 인물 없음",
            f"{BOARDROOM} 대형 스크린에 재생되는 영상 전경, 임원들이 경악하는 반응 샷",
            f"스크린 속 재현 장면, {MIRYEONG}가 {CHAIRMAN}의 약통에 다른 알약을 넣는 장면",
            f"스크린 속 클로즈업, {CHAIRMAN}이 카메라를 정면으로 응시하며 말하는 장면",
            f"{BOARDROOM}, 스크린을 끄고 담담히 말하는 {DOHEE}와 일그러지는 {MIRYEONG}의 투샷",
            f"{BOARDROOM} 문이 열리며 {HAEGYEONG}이 수사관들과 함께 들어서는 장면",
            f"{BOARDROOM}, {HAEGYEONG}이 {JUNHYUK}과 {MIRYEONG}을 향해 체포를 선언하는 클로즈업",
            f"{BOARDROOM}, {HAEGYEONG}과 {JUNHYUK}·{MIRYEONG}이 마주선 투샷, 무거운 정적",
            f"수갑이 채워지는 {JUNHYUK}과 {MIRYEONG}, {DOHEE}와 마주하는 장면",
            f"{BOARDROOM}, 끌려나가는 {JUNHYUK}·{MIRYEONG}을 정면으로 바라보는 {DOHEE}의 단호한 클로즈업",
            f"{BOARDROOM}, {DOHEE}가 끌려나가는 {MIRYEONG}·{JUNHYUK}을 등지고 당당히 서 있는 투샷",
            f"{BOARDROOM}, {DOHEE}가 회의실 창밖 바다를 바라보며 서 있는 와이드 샷, 승리의 여운",
        ],
        lines=[
            (J, "서준혁", "신파 그만하고! 증거 있어? 우리가 뭘 했다는 증거 있냐고!", "angry"),
            (H, "한도희", "있습니다.", "neutral"),
            (N, "", "도희가 꺼낸 건 낡은 블랙박스 하나. 회장이 십 년 동안 숨겨온, 사고 요트 선장실의 녹음 장치였습니다.", None),
            (JR, "서준혁", "연료관만 자르면 돼. 폭풍 오는 날 나가면 아무도 사고라고 의심 안 해.", "neutral"),
            (N, "", "회의장이 얼어붙습니다. 도희가 몰래 챙겼던 그 알약은, 국립과학수사연구원 감정 결과 처방전에 없는 성분으로 이미 확인된 뒤였습니다. 도희는 이어서 영상 하나를 띄웁니다. 미령이 회장의 약통에 다른 알약을 넣는 장면. 회장이 직접 설치한 카메라였죠. 그리고 영상 마지막, 카메라를 바라보며 말하는 회장의 모습.", None),
            (CV, "서회장", "미령아, 준혁아. 고것이 느그들 마지막 기회였어야. 내가 다 보고 있었당께.", "neutral"),
            (H, "한도희", "회장님은 치매가 아니었습니다. 당신들이 약을 바꾸는 걸, 석 달 동안 전부 지켜보고 계셨어요.", "neutral"),
            (R, "서미령", "이거, 조작이야!", "angry"),
            (N, "", "그 순간 들어서는 목포해양경찰서 수사관들. 선두에 선 사람은 십 년 전 도희에게 책임을 떠넘겼던 바로 그 상관이었습니다.", None),
            (P, "목포해경", "서준혁, 서미령. 십 년 전 요트 살인교사 및 서해진 회장 살인미수 혐의로 긴급 체포허요. 그리고 한도희 경장… 십 년 전엔 내가 비겁해서 진실을 덮었는디, 오늘은 내 경찰 뱃지를 걸고 요 잡것들 죗값 치르게 헐라고 직접 영장 쳐왔네. 면목 없네, 정말로.", "sad"),
            (N, "", "수갑이 채워지는 준혁과 미령. 끌려나가며 미령이 소리칩니다.", None),
            (R, "서미령", "너 따위가 해진수산을 가질 수 있을 것 같아?!", "angry"),
            (H, "한도희", "내가 왜 못 가집니까? 서해진 회장님의 법적 유언에 따라 삼천억 지분 전액 상속받아 즉시 민우 해양구조재단으로 귀속시킵니다. 그리고 내가 그 재단의 종신 이사장이자 해진수산 총괄 경영인으로 취임할 겁니다. 당신들 감방에서 썩는 동안 피눈물 흘리며 참회나 하쇼.", "neutral"),
        ],
    ),
    dict(
        name="엔딩 — 도파민 여운",
        lead_in=1.5,
        ambience="calm harbor morning ambience, seagulls, gentle waves, ship horn, uplifting",
        shots=[
            f"{HARBOR}, 새로 진수한 흰색 구조선이 정박해 있는 장면, 선체 옆면은 매끈하고 글자 없음",
            f"{HARBOR}, 부두에서 손을 흔드는 {EOMMA}와 구조대장 제복을 입고 배 위에서 돌아보는 {DOHEE}를 함께 담은 와이드 투샷",
            f"{HARBOR}, 구조대장 제복을 입은 {DOHEE}가 배 위에서 바다를 바라보며 말하는 클로즈업",
            f"{DOHEE}의 손에 들린 편지 봉투 클로즈업, 여운 있는 조명",
        ],
        lines=[
            (N, "", "한 달 뒤. 목포 앞바다에 새 구조선이 띄워집니다. 선체에 새겨진 이름, '민우호'. 그리고 그 배의 초대 구조대장은, 명예 복직한 한도희였습니다.", None),
            (M, "엄마", "도희야! 조심해서 댕겨와라잉!", "happy"),
            (H, "한도희", "회장님. 이번엔 한 명도 안 놓칠라요. 걱정 말으씨요.", "neutral"),
            (N, "", "바닥에 가라앉았던 한 여자의 인생이, 마침내 수면 위로 떠올랐습니다. 그런데 그날 밤, 도희에게 도착한 한 통의 편지. 발신인은… 죽은 서해진 회장이었습니다.", None),
            (N, "", "다음 이야기에서 계속됩니다.", None),
        ],
    ),
]

SCENE_SEC = 5           # 장면당 길이(초) — 5|10 중 짧은 쪽으로 빠른 컷 전환(사용자 피드백)
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
Title: 참교육 사이다 (전라도 사투리 버전) 자막
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Naration,Noto Sans CJK KR,52,&H00DDDDDD,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Dohee,Noto Sans CJK KR,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Chairman,Noto Sans CJK KR,60,&H0000E5FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Eomma,Noto Sans CJK KR,60,&H00FFC896,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Miryeong,Noto Sans CJK KR,60,&H00C896FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Junhyuk,Noto Sans CJK KR,60,&H00FF8080,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Sanae,Noto Sans CJK KR,60,&H0096FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Haegyeong,Noto Sans CJK KR,60,&H00AAFFAA,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: JunhyukRec,Noto Sans CJK KR,52,&H00FF8080,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: ChairmanVideo,Noto Sans CJK KR,52,&H0000E5FF,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,5,2,2,200,200,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    events, scenes, ambience_prompts, emotions = [], [], [], {}
    t_video, line_no = 0.0, 0

    for sec in SECTIONS:
        t = t_video + sec["lead_in"]
        for style, name, text, emotion in sec["lines"]:
            line_no += 1
            dur = line_duration(text)
            events.append((t, t + dur - 0.1, style, name, text))
            if emotion:
                emotions[str(line_no)] = emotion
            t += dur
        raw_span = (t - t_video) + SECTION_TAIL

        n = max(1, math.ceil(raw_span / SCENE_SEC))
        for shot in expand_shots(sec["shots"], n):
            scenes.append(shot)
            ambience_prompts.append(sec["ambience"])
        t_video += n * SCENE_SEC
        print(f"{sec['name']}: 발화 {len(sec['lines'])}줄, {raw_span:.1f}s → 장면 {n}개")

    total = t_video
    print(f"\n합계: 자막 {line_no}줄, 장면 {len(scenes)}개, 영상 {total:.0f}초 ({total / 60:.1f}분)")

    validate_speaker_alignment(events, scenes, SCENE_SEC)

    # 1) 자막
    with open(os.path.join(ROOT, "subs", "참교육사이다.ass"), "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, style, name, text in events:
            f.write(f"Dialogue: 0,{fmt_time(s)},{fmt_time(e)},{style},{name},0,0,0,,{text}\n")

    # 2) 장면 프롬프트
    with open(os.path.join(ROOT, "scripts", "scenes", "참교육사이다.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": SCENE_SEC, "ratio": "16:9", "style": STYLE, "scenes": scenes},
                  f, ensure_ascii=False, indent=2)

    # 3) 오디오 설정 — 전 배역 확정 Typecast 캐스팅 (docs/대본-참교육사이다-사투리버전.md 참고)
    audio = {
        "tts_engine": "typecast",
        "typecast_model": "ssfm-v30",
        "typecast_language": "kor",
        "default_voice": "tc_66e26710ac44cf7c7ebfdb71",   # 나레이션
        "style_voices": {"Naration": "tc_66e26710ac44cf7c7ebfdb71"},
        "name_voices": {
            "한도희": "tc_67b68ff3ba5438793103bfab",
            "서회장": "tc_61945d9c2c11c2c9fd934340",
            "엄마": "tc_5ebea266728f5b00075e6215",
            "서미령": "tc_66d91c60da8dd20be59cd40b",
            "서준혁": "tc_676cda634571635588f87804",
            "사내": "tc_63da42a2dbbf266ceb0b0fb2",
            "목포해경": "tc_67e38d8c771b5511659c4534",
        },
        "emotion_overrides": emotions,
        # JunhyukRec/ChairmanVideo: 녹음·영상 속 목소리라 화면에 실제 입모양이 없어도 됨 →
        # 립싱크 제외 대상에 함께 포함 (규칙 4)
        "narration_styles": ["Naration", "JunhyukRec", "ChairmanVideo"],
        "lipsync_models": ["fal-ai/sync-lipsync", "fal-ai/latentsync"],
        "ambience_model": "fal-ai/mmaudio-v2",
        "ambience_volume": 0.4,
        "ambience_prompts": ambience_prompts,
        "bgm_model": "fal-ai/lyria2",
        # 단곡 반복은 루프가 티남(EP2 교훈 ⑭) — 도입/중반/결말 3곡을 페이드로 이어붙임
        "bgm_segments": [
            "slow tense cinematic Korean drama orchestral intro, subtle traditional Korean "
            "instrumental accents, quiet strings and piano, mournful and restrained, "
            "instrumental only, no vocals",
            "building suspenseful Korean drama orchestral score, strings and piano tension "
            "rising, dramatic accents, instrumental only, no vocals",
            "triumphant cinematic Korean drama orchestral finale, strings and piano resolving "
            "to a vindicated uplifting theme, dramatic, instrumental only, no vocals",
        ],
        "bgm_fade": 1.5,
        "bgm_gap": 2.0,
        "bgm_volume": 0.22,
    }
    with open(os.path.join(ROOT, "scripts", "audio", "참교육사이다.json"), "w", encoding="utf-8") as f:
        json.dump(audio, f, ensure_ascii=False, indent=2)

    print("생성 완료: subs/참교육사이다.ass, "
          "scripts/scenes/참교육사이다.json, "
          "scripts/audio/참교육사이다.json")


if __name__ == "__main__":
    main()
