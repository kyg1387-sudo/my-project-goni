#!/usr/bin/env python3
"""EP3. 김씨와 폐지 할머니 — 제작 자산 생성기.

김씨 시리즈(docs/기획안-김씨시리즈.md) 세 번째 편. 대사 최소(김씨 2줄/할머니 2줄/
최사장 2줄)의 "가장 무언에 가까운 실험편" — 내레이션과 무언 몽타주 비중이 크다.

전체 대본을 섹션별 대사/내레이션/자막카드와 숏 리스트로 정의해 두고, 발화 길이와
줄 앞 침묵(pause)·말 속도(speed) 기반으로 자막 타이밍을 계산한 뒤 다섯 파일을 만든다:

    scripts/scenes/kim-cart-grandma.json   (16:9 장면 프롬프트 + scene_speakers)
    subs/kim-cart-grandma.ass              (자막: 화자별 색상 + Naration + Caption)
    scripts/audio/kim-cart-grandma.json    (목소리·감정·현장음 설정)
    docs/대본-EP3-김씨와폐지할머니.md         (막별 대본, 자산과 동일 소스에서 자동 생성)
    docs/톤연출표-EP3-김씨와폐지할머니.md      (규칙 8-2: 줄별 감정·속도·침묵·연기 지시)

문서와 자산을 같은 SECTIONS에서 생성해 대본-자산 불일치(검증 규칙)를 원천 차단한다.

주의(비용 원칙): 이 스크립트는 프롬프트/자막/설정 파일만 만든다 — API 호출이 없어
무료다. 콜드오픈 훈 장면과 4막 클라이맥스 장면은 동일 프롬프트로 설계했으니(같은
순간의 재배치), 영상 생성 후 out/sceneNN.mp4를 콜드오픈 자리에 복사해 재사용하면
중복 과금을 피할 수 있다 — COLD_OPEN_DUPES 목록 참고.

목소리(오디오 설정)는 현재 파이프라인이 지원하는 fal.ai MiniMax 프리셋으로 채워
두었다. 시리즈 목소리 대장(CLAUDE.md EP2 실증 교훈 ⑨: 김씨=ElevenLabs
8vwSOQHQApfVx993mKf9, 내레이터=5n5gqmaQi9Ewevrz7bOS)을 쓰려면 generate_audio.py에
엔진별 라우팅을 추가해야 한다(현재 코드는 fal.ai 단일 tts_model만 지원) — 실제
생성 전에 이 부분을 먼저 확인할 것.

사용법: python3 scripts/build_ep3_assets.py
"""

import json
import math
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SLUG = "kim-cart-grandma"

SCENE_SEC = 10          # 장면당 길이(초) — 시리즈 기존 두 작품과 동일하게 통일
CHAR_RATE = 5.5         # 초당 글자 수(한국어 낭독, 공백 제외)
LINE_PAD = 0.4          # 대사 뒤 호흡
MIN_DUR = 1.2
SECTION_TAIL = 1.5
DEFAULT_PAUSE = {"Kim": 1.2, "Grandma": 1.3, "Choi": 1.0, "Naration": 0.5, "Caption": 0.6}

# ---------- 등장인물·장소 고정 문구 (모든 장면 프롬프트에서 동일하게 반복) ----------

KIM = ("60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, "
       "무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 "
       "명찰표, 허리에 낡은 무전기)")
GRANDMA = ("70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 "
           "꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 "
           "남색 누빔 점퍼, 해진 목장갑)")
CHOI = ("50대 한국 남성 고물상 주인(다부진 체격, 짧게 깎은 희끗한 머리, 기름때 묻은 "
        "무늬 없는 회색 작업 조끼와 검은 목장갑, 허리에 낡은 무전기)")
CART = "손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카"

GUARD_BOOTH = ("작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 "
               "놓인 좁은 책상, 창밖은 어두운 단지 화단, 벽에는 아무 글자도 없는 매끈한 "
               "근무표 칠판")
APT_GATE = "아파트 단지 정문 앞 인도, 화단과 낮은 담장, 저녁 어스름"
DEMOLITION = ("재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 "
              "아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 늦은 오후")
ALLEY_NIGHT = "가로등 하나만 켜진 어두운 동네 골목, 쌓여 있는 폐지 더미들과 낡은 셔터문들, 옅은 밤안개"
JUNKYARD = ("고물상 마당, 압축된 폐지 더미와 녹슨 저울, 머리 위로 매달린 알전구 조명, "
            "낡은 트럭 한 대, 벽에는 아무 글자도 없는 매끈한 함석판")

STYLE = ("시네마틱 한국 드라마, 실사 영화 화질, 동일한 인물과 의상과 장소를 모든 "
         "장면에서 유지, 자연스러운 피부 질감, 16:9 와이드 가로 구도, 한국어로 말하는 "
         "입 모양, 영어 없음")

FACE = "정면 상반신, 입을 자연스럽게 움직이며"

# (style, name, text, emotion, speed, pause_before, direction_tag)
def line(style, name, text, emotion=None, speed=1.0, pause=None, tag=""):
    return dict(style=style, name=name, text=text, emotion=emotion, speed=speed,
                pause=DEFAULT_PAUSE[style] if pause is None else pause, tag=tag)


def N(text, tone=""):
    return line("Naration", "", text, tag=tone)


def C(text):
    return line("Caption", "", text)


# 콜드오픈과 4막 클라이맥스는 같은 순간 — 셋을 그대로 재사용한다 (COLD_OPEN_DUPES 주석 참고).
JUNKYARD_SHOTS = [
    (f"{JUNKYARD}, {KIM}이 굳은 표정으로 {CHOI} 앞을 가로막고 서 있고 그 옆에 {CART}가 "
     f"놓여 있는 장면, 팽팽한 긴장감, {FACE}", ["김씨", "최사장"]),
    (f"{JUNKYARD}, {KIM}의 손이 {CART} 손잡이에 감긴 낡은 가죽끈을 천천히 짚는 클로즈업, "
     f"손끝 클로즈업, 결연한 표정", ["김씨"]),
    (f"{JUNKYARD}, {CHOI}가 팔짱을 낀 채 미심쩍은 표정으로 {KIM}을 바라보는 장면, {FACE}",
     ["최사장"]),
]

SECTIONS = [
    dict(
        name="콜드오픈",
        lead_in=1.0,
        ambience="rusty cart wheel creak, distant scrap metal clinking, tense quiet, no crowd murmur",
        shots=JUNKYARD_SHOTS,
        lines=[
            line("Kim", "김씨", "이 손잡이, 가죽끈 감긴 거 보이시죠.", "serious", 0.85, 1.0,
                 "[firm, low]"),
            line("Kim", "김씨", "이거 임자 되시는 분이 직접 감으신 겁니다. 함부로 못 없애는 물건입니다.",
                 "determined", 0.8, 0.6, "[steady, resolute]"),
        ],
    ),
    dict(
        name="궁금증 캡션",
        lead_in=0.3,
        ambience="",
        shots=[(f"{JUNKYARD}, {CART} 손잡이의 가죽끈만 어둡게 클로즈업된 정지 화면", [])],
        lines=[C("며칠째, 그는 왜 여기 있는 걸까")],
    ),
    dict(
        name="타이틀",
        lead_in=0.3,
        ambience="",
        shots=[(f"{APT_GATE}, 저녁 어스름 속 텅 빈 인도, 사람이 한 명도 없는, 인물 없음", [])],
        lines=[C("김씨와 폐지 할머니")],
    ),
    dict(
        name="사흘 전 캡션",
        lead_in=0.3,
        ambience="",
        shots=[(f"{APT_GATE}, 오후 햇살이 비치는 인도, 사람이 한 명도 없는, 인물 없음", [])],
        lines=[C("사흘 전")],
    ),
    dict(
        name="1막 — 할머니의 하루",
        lead_in=1.0,
        ambience="",
        shots=[
            (f"{APT_GATE}, {GRANDMA}가 {CART}를 끌고 천천히 걸어오는 뒷모습, 원거리 풀샷",
             ["할머니"]),
            (f"{APT_GATE} 인근 골목, {GRANDMA}가 허리를 굽혀 상자를 주워 {CART}에 싣는 모습, "
             f"무릎 높이 앵글", ["할머니"]),
            (f"{GUARD_BOOTH}, {KIM}이 창문 너머로 {GRANDMA}가 지나가는 모습을 무표정하게 "
             f"지켜보는 장면, {FACE}", ["김씨"]),
            (f"{CART} 손잡이에 감긴 낡은 갈색 가죽끈 클로즈업, {APT_GATE} 배경, 오후 햇살", []),
            (f"{GUARD_BOOTH} 앞 화단, {KIM}이 납작하게 접은 종이상자 더미를 조용히 내려놓고 "
             f"돌아서는 뒷모습, 이른 아침", ["김씨"]),
            (f"{APT_GATE}, {GRANDMA}가 그 상자 더미를 발견하고 살짝 고개를 끄덕이며 "
             f"{CART}에 싣는 모습, 원거리", ["할머니"]),
        ],
        lines=[
            N("이 골목의 리어카는, 유독 손잡이가 반질반질했습니다.", "차분한 도입"),
            N("그 리어카는 이십 년 전, 할머니의 남편이 마지막으로 손봐준 물건이었습니다.",
              "따뜻한 회상"),
            N("손잡이에 감긴 가죽끈도, 삐걱이는 그 소리도, 전부 그 사람이 남기고 간 "
              "것이었습니다.", "잔잔하게"),
            N("할머니에게 이 리어카는, 벌이가 아니라 남편이었습니다.", "여운, 느리게"),
            N("경비 김씨는 매일 아침, 재활용 종이상자를 따로 접어 화단 옆에 놓아두었습니다.",
              "잔잔한 도입"),
            N("말 한마디 없이, 그저 그렇게.", "여운"),
        ],
    ),
    dict(
        name="2막 — 리어카 분실",
        lead_in=1.0,
        ambience="demolition site rubble settling, distant truck engine idling, no crowd voices",
        shots=[
            (f"{DEMOLITION}, {GRANDMA}가 {CART}를 담벼락 옆에 세워두고 폐지를 주우러 자리를 "
             f"비우는 뒷모습", ["할머니"]),
            (f"{DEMOLITION}, 철거 인부들이 잔해를 트럭에 싣는 장면, 배경에 놓인 {CART}가 "
             f"함께 실려가는 모습, 원거리 앵글", []),
            (f"{DEMOLITION}, {GRANDMA}가 폐지를 안고 돌아와 텅 빈 자리를 발견하고 얼어붙은 "
             f"표정으로 서 있는 장면, {FACE}", ["할머니"]),
            (f"{DEMOLITION}, {GRANDMA}가 주저앉아 빈손으로 바닥을 짚는 모습, 낮은 앵글",
             ["할머니"]),
            (f"{DEMOLITION} 인근, {GRANDMA}가 늦은 밤까지 홀로 주변을 헤매며 찾는 모습, "
             f"지친 뒷모습", ["할머니"]),
        ],
        lines=[
            N("그날 오후, 철거 트럭이 골목의 폐자재를 실어 갔습니다.", "담담하게"),
            N("리어카도 함께, 고철더미인 줄 알고.", "반 박자 느리게", ),
            line("Grandma", "할머니", "…내 리어카…", "sad(절제)", 0.7, 1.5, "[breathless, quiet]"),
            N("말은 짧았지만, 그 말 안에 이십 년이 들어 있었습니다.", "여운"),
            N("할머니는 그날 밤, 늦도록 혼자 골목을 헤맸습니다.", "지치고 무겁게"),
            N("아무도, 리어카가 어디로 갔는지 알지 못했습니다.", "무겁게"),
        ],
    ),
    dict(
        name="3막 — 김씨의 사흘 밤",
        lead_in=1.0,
        ambience="",
        shots=[
            (f"{GUARD_BOOTH}, {KIM}이 퇴근 준비를 하다 창밖 {GRANDMA}의 빈 자리를 보고 잠시 "
             f"멈춰서는 장면, {FACE}", ["김씨"]),
            (f"{ALLEY_NIGHT}, {KIM}이 손전등을 들고 골목 구석구석을 살피며 걷는 뒷모습, "
             f"인물 한 명, 무언 수색", ["김씨"]),
            (f"{ALLEY_NIGHT}, {KIM}이 쌓인 폐지 더미 사이를 손전등으로 비추며 하나씩 "
             f"확인하는 모습, 옆모습", ["김씨"]),
            (f"{GUARD_BOOTH} 창가, 지친 {KIM}이 보온병 뚜껑을 열어 마시며 시계를 보는 장면, "
             f"{FACE}", ["김씨"]),
            (f"{ALLEY_NIGHT}, 비가 내리는 가운데 {KIM}이 우산도 없이 젖은 채 골목을 걷는 "
             f"모습, 뒷모습", ["김씨"]),
            (f"{GUARD_BOOTH}, {KIM}이 서랍에서 아내의 낡은 꽃무늬 수첩을 꺼내 펼쳐보는 "
             f"모습, 클로즈업, 인물 한 명", ["김씨"]),
        ],
        lines=[
            N("십 년 전, 이 일을 처음 시작한 날이 있었습니다.", "회상 도입"),
            N("아무도 그에게 말을 걸지 않던 겨울이었습니다.", "쓸쓸하게"),
            N("그런 그에게, 할머니가 말없이 건넨 삶은 옥수수 하나가 있었습니다.", "따뜻하게"),
            N("김씨는 그날을 잊지 않고 있었습니다.", "담담하게"),
            N("그래서 그는, 아무도 시키지 않은 일을, 사흘 밤 계속했습니다.", "결연하게"),
            N("첫째 날 밤, 골목을 뒤졌지만 리어카는 없었습니다.", "담담하게"),
            N("비가 오는 둘째 날 밤에도, 그는 우산 없이 걸었습니다.", "빗소리 배경, 담담하게"),
            N("둘째 날 밤, 고물상 거리까지 갔지만 역시 허탕이었습니다.", "지쳐가는 톤"),
            N("쉬어가던 밤, 그는 아내의 꽃무늬 수첩을 다시 펼쳤습니다.", "잔잔하게, 그리움"),
            N("거기엔 이렇게 적혀 있었습니다 — '폐지 줍는 할머니, 옛날에 옥수수 나눠주시던 분'.",
              "천천히, 낭독하듯"),
            N("다리가 저려올 때쯤에야, 셋째 날 실마리를 얻었습니다.", "지쳐가는 톤"),
            N("철거 업체가 고철을 넘긴 곳 — 마침내 방향을 찾았습니다.", "긴장, 조금 빠르게"),
        ],
    ),
    dict(
        name="4막 도입 — 고물상을 찾아가다",
        lead_in=1.0,
        ambience="",
        shots=[
            (f"고물상 거리 초입, 리어카들이 줄지어 서 있는 낮의 골목, {KIM}이 두리번거리며 "
             f"걸어가는 뒷모습", ["김씨"]),
        ],
        lines=[
            N("김씨는 그길로, 소문난 고물상들을 하나씩 찾아갔습니다.", "결연하게"),
            N("세 번째 집, 마당 안쪽에 낯익은 손잡이가 보였습니다.", "긴장, 발견"),
        ],
    ),
    dict(
        name="4막 — 고물상 대치",
        lead_in=1.0,
        ambience="rusty cart wheel creak, distant scrap metal clinking, tense quiet, no crowd murmur",
        shots=JUNKYARD_SHOTS,
        lines=[
            line("Choi", "최사장", "이미 계근까지 끝난 물건입니다. 값도 다 쳐드렸고요.",
                 "neutral(단호)", 0.9, 1.0, "[brisk, businesslike]"),
            line("Kim", "김씨", "이 손잡이, 가죽끈 감긴 거 보이시죠.", "serious", 0.85, 1.2,
                 "[firm, low]"),
            line("Kim", "김씨", "이거 임자 되시는 분이 직접 감으신 겁니다. 함부로 못 없애는 물건입니다.",
                 "determined", 0.8, 0.6, "[steady, resolute]"),
            N("최사장은 잠시, 자신의 어머니를 떠올렸습니다.", "느리게, 여운"),
            N("돌아가시기 전까지, 낡은 유모차를 놓지 못하시던 어머니를.", "느리게"),
            line("Choi", "최사장", "…가져가십쇼. 바퀴는 제가 손봐 드리겠습니다.", "warm(무뚝뚝)",
                 0.85, 1.2, "[gruff, softened]"),
        ],
    ),
    dict(
        name="5막 — 새벽 배달",
        lead_in=1.0,
        ambience="pre-dawn quiet street ambience, single cart wheel creak, distant rooster, no voices",
        shots=[
            (f"{ALLEY_NIGHT}, {KIM}이 고쳐진 {CART}를 새벽 어스름 속에 혼자 밀고 걸어가는 "
             f"뒷모습, 인물 한 명, 원거리", ["김씨"]),
            (f"{DEMOLITION} 인근 골목 모퉁이, {KIM}이 {CART}를 할머니의 평소 자리에 조용히 "
             f"세워두는 모습, 뒷모습", ["김씨"]),
            (f"{CART} 손잡이 클로즈업, 해진 갈색 가죽끈 위에 낡은 남색 작업 장갑 한 짝이 "
             f"감겨 있는 모습, 새벽 어스름", []),
            (f"{GUARD_BOOTH} 앞, 밤늦게 {KIM}이 손전등을 입에 물고 {CART} 바퀴를 직접 갈아 "
             f"끼우는 모습, 클로즈업", ["김씨"]),
        ],
        lines=[
            N("그는 밤늦도록, 자신의 돈으로 새 바퀴를 갈아 끼웠습니다.", "느리게, 정성스럽게"),
            N("그날 새벽, 아무도 없는 골목에 리어카 하나가 돌아와 있었습니다.", "잔잔하게"),
            N("손잡이에는, 낯선 장갑 한 짝이 감겨 있었습니다.", "여운, 느리게"),
        ],
    ),
    dict(
        name="다음날 아침 캡션",
        lead_in=0.3,
        ambience="",
        shots=[(f"{DEMOLITION} 인근 골목, 이른 아침 옅은 안개, 사람이 한 명도 없는, 인물 없음", [])],
        lines=[C("다음날 아침")],
    ),
    dict(
        name="6막 — 결말",
        lead_in=1.0,
        ambience="",
        shots=[
            (f"{DEMOLITION} 인근 골목, {GRANDMA}가 {CART}를 발견하고 놀라 다가가는 장면, "
             f"{FACE}", ["할머니"]),
            (f"{CART} 손잡이의 가죽끈을 두 손으로 감싸 쓰다듬는 {GRANDMA}의 손 클로즈업, "
             f"{DEMOLITION} 배경", ["할머니"]),
            (f"{GRANDMA}의 얼굴 클로즈업, 눈물이 고인 채 옅은 미소, {DEMOLITION} 배경",
             ["할머니"]),
            (f"{GUARD_BOOTH} 앞 창턱, 삶은 옥수수가 담긴 작은 봉지 하나가 놓여 있는 모습, "
             f"사람이 한 명도 없는, 인물 없음, 이른 아침 햇살", []),
            (f"{GUARD_BOOTH}, {KIM}이 창턱의 옥수수 봉지를 발견하고 손에 들어보며 옅은 "
             f"미소를 짓는 장면, {FACE}", ["김씨"]),
            (f"{APT_GATE}, 아침 햇살 속 {GRANDMA}가 다시 {CART}를 끌고 걸어가는 뒷모습, "
             f"힘찬 걸음, 원거리", ["할머니"]),
        ],
        lines=[
            line("Grandma", "할머니", "…영감이 감아준 건데…", "sad(그리움, 울먹)", 0.7, 2.0,
                 "[trembling, tender]"),
            N("고마움은 몰라도 된다고, 김씨는 생각했습니다.", "느리게"),
            N("그 사람은, 원래 그런 사람이니까요.", "가장 느리게, 여운"),
            N("그날 이후, 할머니의 리어카는 다시 골목길을 지켰습니다.", "따뜻하게, 여운"),
        ],
    ),
    dict(
        name="엔딩 카드",
        lead_in=0.3,
        ambience="",
        shots=[(f"{GUARD_BOOTH} 앞, {KIM}이 뒷모습으로 서서 조용히 단지를 바라보는 모습, "
                f"저녁 어스름, 인물 한 명", ["김씨"])],
        lines=[C("고마움은 몰라도 된다. 그 사람은 원래 그런 사람이니까")],
    ),
    dict(
        name="다음 편 예고",
        lead_in=0.3,
        ambience="",
        shots=[(f"{GUARD_BOOTH} 창가, 작은 트리 장식이 살짝 보이는 겨울 예고 컷, 사람이 "
                f"한 명도 없는, 인물 없음", [])],
        lines=[C("다음 이야기 — 김씨의 크리스마스")],
    ),
]

COLD_OPEN_DUPES = "콜드오픈(섹션 1)과 4막(섹션 8)은 동일 프롬프트 3개를 공유 — 생성 후 클립 복사로 중복 과금 회피 가능"

STYLE_META = {  # style -> (ass 색상 등은 ASS_STYLE_BLOCK에서), 화면 표시용 화자 한글명
    "Kim": "김씨", "Grandma": "할머니", "Choi": "최사장", "Naration": "", "Caption": "",
}

SILENT_STYLES = ["Caption"]
NARRATION_STYLES = ["Naration"]


def line_duration(entry):
    if entry["style"] == "Caption":
        return max(2.2, len(entry["text"]) / 8 + 1.0)
    chars = len(entry["text"].replace(" ", ""))
    base = max(MIN_DUR, chars / CHAR_RATE + LINE_PAD)
    return base / entry["speed"]


def fmt_time(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ASS_HEADER = """[Script Info]
Title: 김씨와 폐지 할머니 (EP3) 자막
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Naration,Noto Sans CJK KR,52,&H00DDDDDD,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Caption,Noto Serif CJK KR,56,&H00FFF3C4,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,5,200,200,80,1
Style: Kim,Noto Sans CJK KR,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Grandma,Noto Sans CJK KR,60,&H0096C8FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1
Style: Choi,Noto Sans CJK KR,60,&H0064C8FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build():
    events, scenes, scene_speakers, ambience_prompts = [], [], [], []
    emotions, speed_overrides = {}, {}
    t_video, tts_line_no = 0.0, 0
    section_ends = []
    tone_rows_dialogue, tone_rows_narration = [], []

    for sec in SECTIONS:
        t = t_video + sec["lead_in"]
        sec_dialogue = []  # (start, end, name) — 화자-화면 일치 배정에 사용
        for entry in sec["lines"]:
            t += entry["pause"]
            dur = line_duration(entry)
            start, end = t, t + dur - (0.1 if entry["style"] != "Caption" else 0.0)
            events.append((start, end, entry["style"], entry["name"], entry["text"]))
            if entry["style"] not in SILENT_STYLES:
                tts_line_no += 1
                if entry["emotion"]:
                    emotions[str(tts_line_no)] = entry["emotion"]
                if entry["speed"] != 1.0:
                    speed_overrides[str(tts_line_no)] = entry["speed"]
            if entry["style"] in ("Kim", "Grandma", "Choi"):
                tone_rows_dialogue.append((tts_line_no, entry))
                sec_dialogue.append((start, end, entry["name"]))
            elif entry["style"] == "Naration":
                tone_rows_narration.append((tts_line_no, entry))
            t += dur
        raw_span = (t - t_video) + SECTION_TAIL

        # 장면 배정: 대사가 걸치는 10초 블록에는 반드시 그 화자가 등장하는 샷을 배정한다
        # (화자-화면 일치 규칙) — 순수 순환(k % len(shots))이 아니라 시간 기반으로 고른다.
        n = max(1, math.ceil(raw_span / SCENE_SEC))
        shots = sec["shots"]
        empty_shots = [s for s in shots if not s[1]]
        rotation = {}

        def pick_shot(needed_names):
            if needed_names:
                key = tuple(needed_names)
                candidates = [s for s in shots if set(needed_names) <= set(s[1])]
                if not candidates:
                    candidates = [s for s in shots if set(s[1]) & set(needed_names)]
                if not candidates:
                    print(f"  경고: '{sec['name']}'에 화자 {needed_names} 등장 샷이 없음 — "
                          f"첫 샷으로 대체(대본 보강 필요)")
                    candidates = shots
            else:
                key = ("__neutral__",)
                candidates = empty_shots or shots
            i = rotation.get(key, 0)
            rotation[key] = i + 1
            return candidates[i % len(candidates)]

        for k in range(n):
            w0, w1 = t_video + k * SCENE_SEC, t_video + (k + 1) * SCENE_SEC
            needed = sorted({name for (s0, s1, name) in sec_dialogue if s0 < w1 and s1 > w0})
            prompt, speakers = pick_shot(needed)
            scenes.append(prompt)
            scene_speakers.append(speakers)
            ambience_prompts.append(sec["ambience"])
        t_video += n * SCENE_SEC
        section_ends.append(len(scenes))
        print(f"{sec['name']}: 대사/내레이션 {len(sec['lines'])}줄, {raw_span:.1f}s → 장면 {n}개")

    total = t_video
    print(f"\n합계: TTS {tts_line_no}줄(자막카드 별도), 장면 {len(scenes)}개, "
          f"영상 {total:.0f}초 ({total / 60:.1f}분)")

    return dict(events=events, scenes=scenes, scene_speakers=scene_speakers,
                ambience_prompts=ambience_prompts, emotions=emotions,
                speed_overrides=speed_overrides, total=total,
                section_ends=section_ends[:-1], tts_line_count=tts_line_no,
                tone_dialogue=tone_rows_dialogue, tone_narration=tone_rows_narration)


def write_ass(data):
    path = os.path.join(ROOT, "subs", f"{SLUG}.ass")
    with open(path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, style, name, text in data["events"]:
            f.write(f"Dialogue: 0,{fmt_time(s)},{fmt_time(e)},{style},{name},0,0,0,,{text}\n")
    print(f"자막 저장: {path}")


def write_scenes(data):
    path = os.path.join(ROOT, "scripts", "scenes", f"{SLUG}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"duration": SCENE_SEC, "ratio": "16:9", "style": STYLE,
                   "scenes": data["scenes"]}, f, ensure_ascii=False, indent=2)
    print(f"장면 프롬프트 저장: {path} ({len(data['scenes'])}개)")


def write_audio_config(data):
    audio = {
        "tts_model": "fal-ai/minimax/speech-02-hd",
        "language_boost": "Korean",
        "speed": 1.0,
        "default_voice": "Deep_Voice_Man",
        "style_voices": {"Naration": "Deep_Voice_Man", "Kim": "Imposing_Manner",
                         "Grandma": "Wise_Woman", "Choi": "Determined_Man"},
        "name_voices": {"김씨": "Imposing_Manner", "할머니": "Wise_Woman",
                        "최사장": "Determined_Man"},
        "style_names": {"Kim": "김씨", "Grandma": "할머니", "Choi": "최사장",
                        "Naration": "내레이터"},
        "style_emotions": {"Kim": "neutral", "Grandma": "sad", "Choi": "neutral",
                           "Naration": "neutral"},
        "emotion_overrides": data["emotions"],
        "speed_overrides": data["speed_overrides"],
        "narration_styles": NARRATION_STYLES,
        "silent_styles": SILENT_STYLES,
        "scene_speakers": data["scene_speakers"],
        "section_ends": data["section_ends"],
        "lipsync_models": ["fal-ai/sync-lipsync", "fal-ai/latentsync"],
        "ambience_model": "fal-ai/mmaudio-v2",
        "ambience_volume": 0.35,
        "ambience_prompts": data["ambience_prompts"],
        "bgm_model": "fal-ai/lyria2",
        "bgm_prompt": "warm gentle Korean drama piano and strings, understated, bittersweet, "
                      "slow tempo, instrumental only, no vocals, no lyrics",
        "bgm_volume": 0.18,
        "_주의": ("김씨=EL 8vwSOQHQApfVx993mKf9, 내레이터=EL 5n5gqmaQi9Ewevrz7bOS 로 교체 "
                "예정(시리즈 목소리 대장) — generate_audio.py에 엔진별 라우팅 추가 후 적용. "
                "그 전까지는 위 MiniMax 프리셋이 폴백."),
    }
    path = os.path.join(ROOT, "scripts", "audio", f"{SLUG}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(audio, f, ensure_ascii=False, indent=2)
    print(f"오디오 설정 저장: {path}")


def write_script_doc(data):
    lines = ["# EP3 「김씨와 폐지 할머니」 대본 (강화판 — 유품 리어카 + 옥수수 수미상관)", ""]
    lines.append(f"자산 슬러그: `{SLUG}` · 예상 길이 {data['total']/60:.1f}분 · "
                 f"장면 {len(data['scenes'])}개 · TTS {data['tts_line_count']}줄(자막카드 별도)")
    lines.append("")
    lines.append("**로그라인**: 재개발 철거장 앞에서 사라진 할머니의 리어카는, 이십 년 전 "
                 "돌아가신 남편이 마지막으로 손봐준 유일한 유품이다. 말 없는 경비원 김씨는 "
                 "십 년 전 이 일을 처음 시작한 날 할머니에게 받은 옥수수 한 개의 온정을 "
                 "갚기 위해, 아무도 시키지 않은 일을 사흘 밤 계속한다.")
    lines.append("")
    lines.append(f"**편집 메모**: {COLD_OPEN_DUPES}.")
    lines.append("")
    for sec in SECTIONS:
        lines.append(f"## {sec['name']}")
        lines.append("")
        for prompt, speakers in sec["shots"]:
            who = f" _(등장: {', '.join(speakers)})_" if speakers else " _(인물 없음)_"
            lines.append(f"- {prompt}{who}")
        lines.append("")
        if sec["lines"]:
            for entry in sec["lines"]:
                if entry["style"] == "Caption":
                    lines.append(f"> 【자막카드】 {entry['text']}")
                elif entry["style"] == "Naration":
                    lines.append(f"> (내레이션) {entry['text']}")
                else:
                    speaker = STYLE_META[entry["style"]]
                    lines.append(f"**{speaker}**: {entry['text']}")
            lines.append("")
    with open(os.path.join(ROOT, "docs", "대본-EP3-김씨와폐지할머니.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("대본 문서 저장: docs/대본-EP3-김씨와폐지할머니.md")


def write_tone_doc(data):
    lines = ["# EP3 「김씨와 폐지 할머니」 줄별 톤 연출표 (규칙 8-2)", ""]
    lines.append("엔진: MM=MiniMax(현재 폴백), EL=ElevenLabs(시리즈 목소리 대장 적용 예정, "
                 "generate_audio.py 엔진 라우팅 추가 후)")
    lines.append("표기: 속도(1.0=보통), 앞침묵=대사 시작 전 여백(초), 지시=연기·표정(장면 "
                 "프롬프트에도 동일 반영)")
    lines.append("")
    lines.append(f"## 대사 ({len(data['tone_dialogue'])}줄)")
    lines.append("| # | 화자 | 대사 | 엔진 | 감정 | 속도 | 앞침묵 | 연기 지시 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for i, e in data["tone_dialogue"]:
        speaker = STYLE_META[e["style"]]
        engine = "EL(예정)" if speaker == "김씨" else "MM"
        lines.append(f"| {i} | {speaker} | {e['text']} | {engine} | {e['emotion']} | "
                     f"{e['speed']:.2f} | {e['pause']:.1f} | {e['tag']} |")
    lines.append("")
    lines.append(f"## 내레이션 ({len(data['tone_narration'])}줄, 내레이터=EL 예정 — 전 줄 speed 0.9 기준)")
    lines.append("| # | 문안 | 톤 |")
    lines.append("|---|---|---|")
    for i, e in data["tone_narration"]:
        lines.append(f"| N{i} | {e['text']} | {e['tag']} |")
    lines.append("")
    lines.append("## 전환 연출 메모 (규칙 8-1)")
    lines.append("- 콜드오픈→궁금증 캡션: 하드 컷 (긴장 유지, 디졸브 없이)")
    lines.append("- 사흘 전 캡션→1막: 디졸브 0.5초 (시간 역행 표시)")
    lines.append("- 2막 '…내 리어카…' 뒤: 완충 무언 컷(주저앉는 손) 여운 0.8초 → 디졸브")
    lines.append("- 3막 몽타주 내부(사흘 밤): 전환 전부 디졸브 0.4~0.6초, 현장음(밤안개·손전등) 브리지")
    lines.append("- 4막 '…가져가십쇼' 뒤: 여운 1초 → 디졸브 → 5막 새벽")
    lines.append("- 6막 가죽끈 클로즈업→얼굴 클로즈업: 디졸브 0.4초 (같은 정서 유지)")
    lines.append("- 옥수수 봉지(무인 컷)→김씨 발견 컷: 하드 컷 (수미상관 대비, 임팩트 유지)")
    with open(os.path.join(ROOT, "docs", "톤연출표-EP3-김씨와폐지할머니.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("톤 연출표 저장: docs/톤연출표-EP3-김씨와폐지할머니.md")


def main():
    data = build()
    write_ass(data)
    write_scenes(data)
    write_audio_config(data)
    write_script_doc(data)
    write_tone_doc(data)
    print("\n생성 완료.")


if __name__ == "__main__":
    main()
