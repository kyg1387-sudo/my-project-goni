#!/usr/bin/env python3
"""EP3. 김씨와 폐지 할머니 — 제작 자산 생성기.

김씨 시리즈(docs/기획안-김씨시리즈.md) 세 번째 편. 대사 최소(김씨 2줄/할머니 2줄/
최사장 2줄)의 "가장 무언에 가까운 실험편" — 내레이션과 무언 몽타주 비중이 크다.

docs/영화제작규칙집.md 5장(컷 프롬프트 5블록: LOCK/SCENE/CAMERA/DURATION/DIALOGUE/
SOUND)·6장(컷 길이 규칙)·7장(카메라 문법 3축) 규격을 따른다. 섹션(=씬)마다 컷을
직접 저작(길이 5|10초, Movement/Angle/Size 지정)하고, 대사·내레이션은 별도로
타이밍을 계산해 두 결과를 합친 뒤 화자-화면 일치를 자동 검증한다.

생성 파일:
    scripts/scenes/kim-cart-grandma.json   (컷별 5블록 프롬프트 + durations + scene_speakers)
    subs/kim-cart-grandma.ass              (자막: 화자별 색상 + Naration + Caption)
    scripts/audio/kim-cart-grandma.json    (목소리·감정·현장음 설정)
    docs/대본-EP3-김씨와폐지할머니.md         (막별 대본, 자산과 동일 소스에서 자동 생성)
    docs/톤연출표-EP3-김씨와폐지할머니.md      (규칙 8-2: 줄별 감정·속도·침묵·연기 지시)
    docs/EP3-컷프롬프트.md                  (컷별 5블록 프롬프트 검수용 문서)

문서와 자산을 같은 SECTIONS에서 생성해 대본-자산 불일치(검증 규칙)를 원천 차단한다.
빌드 마지막에 화자-화면 정렬을 자동 재검증한다(0건이어야 커밋 가능).

주의(비용 원칙): 이 스크립트는 프롬프트/자막/설정 파일만 만든다 — API 호출이 없어
무료다. 콜드오픈 훅 장면과 4막 클라이맥스 장면은 같은 고물상 구도를 재사용하도록
설계했으니, 영상 생성 후 out/sceneNN.mp4를 콜드오픈 자리에 복사해 재사용하면
중복 과금을 피할 수 있다 — COLD_OPEN_DUPES 참고.

주의(컷 길이 규칙, §6): 실제 fal.ai Seedance 모델은 5초 또는 10초만 지원한다
(scripts/generate_video.py 확인). 규칙집의 이상적 길이표(인서트 3~4초 등)는 이
두 값 중 가까운 쪽으로 반올림해 배정했다 — 정밀한 3~4초 인서트는 불가능하다.

목소리(오디오 설정)는 현재 파이프라인이 지원하는 fal.ai MiniMax 프리셋으로 채워
두었다. 시리즈 목소리 대장(CLAUDE.md EP2 실증 교훈 ⑨: 김씨=ElevenLabs
8vwSOQHQApfVx993mKf9, 내레이터=5n5gqmaQi9Ewevrz7bOS)을 쓰려면 generate_audio.py에
엔진별 라우팅을 추가해야 한다(현재 코드는 fal.ai 단일 tts_model만 지원) — 실제
생성 전에 이 부분을 먼저 확인할 것.

사용법: python3 scripts/build_ep3_assets.py
"""

import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SLUG = "kim-cart-grandma"

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
               "놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 "
               "근무표 칠판")  # 시간대는 각 컷에서 명시(고정 문구 금지 — 시간대 충돌 방지)
APT_GATE = "아파트 단지 정문 앞 인도, 화단과 낮은 담장"
DEMOLITION = ("재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 "
              "아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터")
ALLEY_NIGHT = "가로등 하나만 켜진 어두운 동네 골목, 쌓여 있는 폐지 더미들과 낡은 셔터문들, 옅은 밤안개"
JUNKYARD = ("고물상 마당, 압축된 폐지 더미와 녹슨 저울, 머리 위로 매달린 알전구 조명, "
            "낡은 트럭 한 대, 벽에는 아무 글자도 없는 매끈한 함석판")

PALETTE_MAIN = "muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones"
PALETTE_FLASHBACK = "desaturated sepia-toned palette, soft grain, memory-like"

LIPSYNC_SUFFIX = "한국어로 말하는 입 모양, 영어 없음"  # 파이프라인 고유 규칙 — 규칙집보다 우선

# 캐릭터 시트 참조명 (assets/character-sheets/*.txt 의 헤더와 일치)
SHEET_REF = {
    "김씨": "the \"GUARD KIM\" reference character sheet",
    "할머니": "the \"GRANDMOTHER\" reference character sheet",
    "최사장": "the \"CHOI - SCRAPYARD OWNER\" reference character sheet",
}
EN_NAME = {"김씨": "the guard (Kim)", "할머니": "the grandmother", "최사장": "Choi (the scrapyard owner)"}


def line(style, name, text, emotion=None, speed=1.0, pause=None, tag=""):
    return dict(style=style, name=name, text=text, emotion=emotion, speed=speed,
                pause=DEFAULT_PAUSE[style] if pause is None else pause, tag=tag)


def N(text, tone=""):
    return line("Naration", "", text, tag=tone)


def C(text):
    return line("Caption", "", text)


def cut(desc, speakers, duration, size, movement, angle="Eye-level",
        end="hold on the final frame for the last second", sound="", palette=None,
        dialogue=None):
    """컷 1개 = 규칙집 §5의 5블록 하나. dialogue: (화자, 감정톤, 텍스트) 또는 None."""
    return dict(desc=desc, speakers=speakers, duration=duration, size=size,
                movement=movement, angle=angle, end=end, sound=sound,
                palette=palette or PALETTE_MAIN, dialogue=dialogue)


# 콜드오픈과 4막 클라이맥스가 공유하는 고물상 구도 — 문구를 최대한 맞춰 두면
# 영상 생성 후 클립을 복사해 재사용하기 쉽다 (COLD_OPEN_DUPES 참고).
JUNKYARD_BLOCK = f"{JUNKYARD}, {KIM}이 굳은 표정으로 {CHOI} 앞을 가로막고 서 있고 그 옆에 {CART}가 놓여 있는 장면"
JUNKYARD_STRAP = f"{JUNKYARD}, {KIM}의 손이 {CART} 손잡이에 감긴 낡은 가죽끈을 천천히 짚는 모습, 결연한 표정"
JUNKYARD_CHOI = f"{JUNKYARD}, {CHOI}가 팔짱을 낀 채 {KIM}을 바라보는 장면"

SECTIONS = [
    dict(
        name="콜드오픈",
        lead_in=1.0,
        lines=[
            line("Kim", "김씨", "이 손잡이, 가죽끈 감긴 거 보이시죠.", "serious", 0.85, 1.0,
                 "[firm, low]"),
            line("Kim", "김씨", "이거 임자 되시는 분이 직접 감으신 겁니다. 함부로 못 없애는 물건입니다.",
                 "determined", 0.8, 0.6, "[steady, resolute]"),
        ],
        cuts=[
            cut(JUNKYARD_BLOCK + ", 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임",
                ["김씨", "최사장"], 10, "Medium close-up", "Slow dolly in toward Kim",
                end="hold on Kim's resolute expression",
                sound="rusty cart wheel creak, distant scrap metal clinking, tense quiet, no crowd murmur"),
            # Kim의 두 줄 대사가 10초를 넘어가므로(약 12초), 이 컷도 김씨를 화면에 유지한 채
            # 이어간다 — Choi 단독 리액션으로 끊으면 뒷부분 대사와 화자-화면이 어긋난다.
            cut(JUNKYARD_BLOCK + ", 정면 상반신 구도, 한국어로 대사를 마무리하며 입을 자연스럽게 "
                "움직이고, 최사장은 미심쩍은 표정으로 침묵",
                ["김씨", "최사장"], 10, "Medium close-up", "Static, locked off",
                end="hold on Choi's wary silent stare after Kim finishes speaking",
                sound="rusty cart wheel creak, tense quiet, no crowd murmur"),
        ],
    ),
    dict(
        name="궁금증 캡션", lead_in=0.3,
        lines=[C("며칠째, 그는 왜 여기 있는 걸까")],
        cuts=[cut(f"{JUNKYARD}, {CART} 손잡이의 가죽끈만 어둡게 보이는 정지된 듯한 구도, 인물 없음",
                  [], 5, "Extreme close-up", "Static, locked off",
                  sound="")],
    ),
    dict(
        name="타이틀", lead_in=0.3,
        lines=[C("김씨와 폐지 할머니")],
        cuts=[cut(f"{APT_GATE}, 저녁 어스름이 내려앉은 텅 빈 인도, 사람이 한 명도 없는, 인물 없음",
                  [], 5, "Long shot", "Static, locked off", sound="")],
    ),
    dict(
        name="사흘 전 캡션", lead_in=0.3,
        lines=[C("사흘 전")],
        cuts=[cut(f"{APT_GATE}, 오후 햇살이 비치는 인도, 사람이 한 명도 없는, 인물 없음",
                  [], 5, "Long shot", "Static, locked off", sound="")],
    ),
    dict(
        name="1막 — 할머니의 하루",
        lead_in=1.0,
        lines=[
            N("이 골목의 리어카는, 유독 손잡이가 반질반질했습니다.", "차분한 도입"),
            N("그 리어카는 이십 년 전, 할머니의 남편이 마지막으로 손봐준 물건이었습니다.",
              "따뜻한 회상"),
            N("손잡이에 감긴 가죽끈도, 삐걱이는 그 소리도, 전부 그 사람이 남기고 간 "
              "것이었습니다.", "잔잔하게"),
            N("할머니에게 이 리어카는, 벌이가 아니라 남편이었습니다.", "여운, 느리게"),
            N("다른 건 아무리 험하게 다뤄도, 이 손잡이만은 늘 헝겊으로 닦아냈습니다.",
              "잔잔하게, 의미심장"),
            N("경비 김씨는 매일 아침, 재활용 종이상자를 따로 접어 화단 옆에 놓아두었습니다.",
              "잔잔한 도입"),
            N("말 한마디 없이, 그저 그렇게.", "여운"),
        ],
        cuts=[
            cut(f"{APT_GATE}, 오후 햇살 속 {GRANDMA}가 {CART}를 끌고 걸어오는 모습",
                ["할머니"], 10, "Long shot", "Side tracking, camera moves parallel to the grandmother",
                sound="cart wheel creaking softly, quiet afternoon street"),
            cut(f"{APT_GATE} 인근 골목, 오후, {GRANDMA}가 허리를 굽혀 상자를 주워 {CART}에 싣는 모습",
                ["할머니"], 10, "Medium", "Static, locked off",
                sound="cardboard rustling, quiet afternoon street"),
            cut(f"{CART} 손잡이에 감긴 낡은 갈색 가죽끈, {APT_GATE} 배경, 오후 햇살",
                [], 5, "Close-up", "Static, locked off", sound=""),
            cut(f"{APT_GATE} 인근 골목, 오후, {GRANDMA}가 다른 곳은 험하게 다뤄도 손잡이의 가죽끈만은 "
                f"헝겊으로 정성스레 닦아내는 손", ["할머니"], 5, "Close-up",
                "Slow dolly in toward her hands", sound="soft cloth wiping, quiet street"),
            cut(f"{GUARD_BOOTH}, 오후, {KIM}이 창문 너머로 {GRANDMA}가 지나가는 모습을 무표정하게 "
                f"지켜보는 장면", ["김씨"], 5, "Medium close-up", "Static, locked off", sound=""),
            cut(f"{GUARD_BOOTH} 앞 화단, 이른 아침, {KIM}이 납작하게 접은 종이상자 더미를 조용히 "
                f"내려놓고 돌아서는 모습", ["김씨"], 5, "Full shot",
                "Static rear shot, back of Kim fills frame",
                sound="quiet early morning ambience, birds distant"),
            cut(f"{APT_GATE}, 이른 아침, {GRANDMA}가 그 상자 더미를 발견하고 살짝 고개를 끄덕이며 "
                f"{CART}에 싣는 모습", ["할머니"], 5, "Long shot", "Static, locked off",
                sound="quiet early morning ambience"),
        ],
    ),
    dict(
        name="2막 — 리어카 분실",
        lead_in=1.0,
        lines=[
            N("그날 오후, 철거 트럭이 골목의 폐자재를 실어 갔습니다.", "담담하게"),
            N("리어카도 함께, 고철더미인 줄 알고.", "반 박자 느리게"),
            line("Grandma", "할머니", "…내 리어카…", "sad(절제)", 0.7, 1.5, "[breathless, quiet]"),
            N("말은 짧았지만, 그 말 안에 이십 년이 들어 있었습니다.", "여운"),
            N("할머니는 그날 밤, 늦도록 혼자 골목을 헤맸습니다.", "지치고 무겁게"),
            N("아무도, 리어카가 어디로 갔는지 알지 못했습니다.", "무겁게"),
        ],
        cuts=[
            cut(f"{DEMOLITION}, 늦은 오후, {GRANDMA}가 {CART}를 담벼락 옆에 세워두고 폐지를 "
                f"주우러 자리를 비우는 모습", ["할머니"], 5, "Long shot", "Static, locked off",
                sound="demolition site rubble settling, distant truck engine idling, no crowd voices"),
            cut(f"{DEMOLITION}, 늦은 오후, 철거 인부들이 잔해를 트럭에 싣는 장면, 배경에 놓인 "
                f"{CART}가 함께 실려가는 모습", [], 5, "Long shot",
                "Slow dolly in toward the departing truck",
                sound="truck engine, rubble loading, distant"),
            cut(f"{DEMOLITION}, 늦은 오후, {GRANDMA}가 폐지를 안고 돌아와 텅 빈 자리를 발견하고 "
                f"얼어붙은 표정으로 서 있는 장면, 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임",
                ["할머니"], 10, "Medium close-up",
                "Dolly zoom: camera pulls back while lens zooms in, subject size constant, "
                "background stretches",
                end="hold on her frozen face for the last second",
                sound="sudden silence, wind"),
            cut(f"{DEMOLITION}, 늦은 오후, {GRANDMA}가 주저앉아 빈손으로 바닥을 짚는 모습",
                ["할머니"], 5, "Full shot", "Static, locked off", angle="Low angle",
                sound="quiet, distant city hum"),
            cut(f"{DEMOLITION} 인근, 늦은 밤, {GRANDMA}가 홀로 주변을 헤매며 찾는 모습, 지친 모습",
                ["할머니"], 5, "Long shot", "Handheld, fine natural tremor",
                sound="quiet night street ambience, footsteps"),
        ],
    ),
    dict(
        name="3막 — 김씨의 사흘 밤",
        lead_in=1.0,
        # 정보 공개를 늦춘다: '왜 저렇게까지 하는가'라는 궁금증을 수첩을 펼치는 순간까지
        # 미뤄야 폭발력이 생긴다(리뷰 피드백 반영).
        lines=[
            N("그에게도, 아무도 모르는 이유가 있었습니다.", "담담하지만 의미심장하게"),
            N("그래서 그는, 아무도 시키지 않은 일을, 사흘 밤 계속했습니다.", "결연하게"),
            N("첫째 날 밤, 샅샅이 뒤진 골목엔 흔적조차 없었습니다.", "담담하게"),
            N("비가 쏟아지던 둘째 날 밤, 우산도 없이 고물상 거리를 헤맸지만 역시 헛걸음이었습니다.",
              "빗소리 배경, 지쳐가는 톤"),
            N("쉬어가던 밤, 그는 아내의 꽃무늬 수첩을 다시 펼쳤습니다.", "잔잔하게, 그리움"),
            N("거기엔 이렇게 적혀 있었습니다 — '폐지 줍는 할머니, 옛날에 옥수수 나눠주시던 분'.",
              "천천히, 낭독하듯"),
            N("십 년 전, 아무도 그에게 말을 걸지 않던 겨울, 할머니가 말없이 건넨 삶은 옥수수 "
              "하나였습니다.", "따뜻하게, 뭉클함"),
            N("김씨는 그날을, 십 년이 지나도록 잊지 않고 있었습니다.", "담담하게, 여운"),
            N("다리가 저려올 때쯤에야, 셋째 날 실마리를 얻었습니다.", "지쳐가는 톤"),
            N("철거 업체가 고철을 넘긴 곳 — 마침내 방향을 찾았습니다.", "긴장, 조금 빠르게"),
        ],
        cuts=[
            cut(f"{GUARD_BOOTH}, 밤, {KIM}이 퇴근 준비를 하다 창밖 {GRANDMA}의 빈 자리를 보고 "
                f"잠시 멈춰서는 장면", ["김씨"], 10, "Medium close-up", "Static, locked off",
                sound="quiet night office hum, clock ticking"),
            cut(f"{GUARD_BOOTH}, 밤, {KIM}이 결심한 듯 문을 열고 나서는 모습", ["김씨"], 5,
                "Full shot", "Follow shot, camera behind Kim at shoulder height",
                sound="door, footsteps into the night"),
            cut(f"{ALLEY_NIGHT}, {KIM}이 손전등을 들고 골목 구석구석을 살피며 걷는 모습",
                ["김씨"], 10, "Long shot", "Side tracking, camera moves parallel to Kim",
                sound="footsteps, flashlight click, distant night ambience"),
            cut(f"{ALLEY_NIGHT}, 비가 내리는 가운데 {KIM}이 우산도 없이 젖은 채 골목을 헤매는 모습",
                ["김씨"], 10, "Full shot", "Handheld, fine natural tremor",
                sound="heavy rain, footsteps splashing"),
            cut(f"{GUARD_BOOTH}, 밤, {KIM}이 서랍에서 아내의 낡은 꽃무늬 수첩을 꺼내 펼쳐보는 모습",
                ["김씨"], 10, "Medium close-up", "Slow dolly in toward Kim",
                sound="quiet night office hum, paper rustling"),
            cut("아내의 낡은 꽃무늬 수첩 페이지 클로즈업, 손글씨가 적힌 모습이나 글자는 흐릿하게 "
                "표현, 인물 없음", [], 5, "Extreme close-up", "Rack focus from the page edge to the writing, camera locked",
                sound="paper rustling"),
            cut(f"{GUARD_BOOTH} 창가, 밤, 지친 {KIM}이 보온병 뚜껑을 열어 마시며 먼 곳을 응시하는 "
                f"장면", ["김씨"], 5, "Medium close-up", "Static, locked off",
                sound="quiet night office hum"),
            cut(f"{ALLEY_NIGHT}, {KIM}의 지친 발걸음 클로즈업, 다리를 절며 걷는 모습",
                ["김씨"], 5, "Close-up", "Static, locked off", sound="tired footsteps, night ambience"),
        ],
    ),
    dict(
        name="4막 도입 — 고물상을 찾아가다",
        lead_in=1.0,
        lines=[
            N("김씨는 그길로, 소문난 고물상들을 하나씩 찾아갔습니다.", "결연하게"),
            N("세 번째 집, 마당 안쪽에 낯익은 손잡이가 보였습니다.", "긴장, 발견"),
        ],
        cuts=[
            cut(f"고물상 거리 초입, 리어카들이 줄지어 서 있는 낮의 골목, {KIM}이 두리번거리며 "
                f"걸어가는 모습", ["김씨"], 10, "Full shot",
                "Side tracking, camera moves parallel to Kim",
                sound="daytime street ambience, distant traffic"),
            cut(f"고물상 마당 입구, {KIM}이 걸음을 멈추고 안쪽의 낯익은 손잡이를 발견하는 모습",
                ["김씨"], 5, "Medium close-up", "Slow zoom in, camera locked",
                end="hold on Kim's focused gaze",
                sound="daytime scrapyard ambience"),
        ],
    ),
    dict(
        name="4막 — 고물상 대치",
        lead_in=1.0,
        lines=[
            line("Choi", "최사장", "이미 계근까지 끝난 물건입니다. 값도 다 쳐드렸고요.",
                 "neutral(단호)", 0.9, 1.0, "[brisk, businesslike]"),
            N("김씨는, 물러서지 않았습니다.", "단호하게, 짧게"),
            line("Kim", "김씨", "이 손잡이, 가죽끈 감긴 거 보이시죠.", "serious", 0.85, 1.2,
                 "[firm, low]"),
            line("Kim", "김씨", "이거 임자 되시는 분이 직접 감으신 겁니다. 함부로 못 없애는 물건입니다.",
                 "determined", 0.8, 0.6, "[steady, resolute]"),
            N("최사장은 잠시, 자신의 어머니를 떠올렸습니다.", "느리게, 여운"),
            N("돌아가시기 전까지, 낡은 유모차를 놓지 못하시던 어머니를.", "느리게"),
            line("Choi", "최사장", "…가져가십쇼. 값은 됐습니다.", "warm(무뚝뚝)",
                 0.85, 1.2, "[gruff, softened]"),
        ],
        cuts=[
            # 콜드오픈 컷 1과 완전히 동일 — 실제로는 같은 클립(재사용, COLD_OPEN_DUPES 참고).
            cut(JUNKYARD_BLOCK + ", 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임",
                ["김씨", "최사장"], 10, "Medium close-up", "Slow dolly in toward Kim",
                end="hold on Kim's resolute expression",
                sound="rusty cart wheel creak, tense quiet, no crowd murmur"),
            cut(JUNKYARD_STRAP + ", 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임",
                ["김씨"], 10, "Medium close-up", "Slow dolly in toward Kim",
                sound="tense quiet"),
            # Kim의 두 줄 대사가 10초를 넘어가므로(약 12초), 이 컷에도 김씨를 포함시켜 둔다
            # (Choi 단독 클로즈업으로 끊으면 뒷부분 대사와 화자-화면이 어긋난다).
            cut(JUNKYARD_CHOI + ", 김씨가 대사를 마무리하는 목소리를 들으며 표정이 서서히 "
                "흔들리는 모습", ["최사장", "김씨"], 10, "Close-up", "Slow zoom in, camera locked",
                end="hold on Choi's softening expression",
                sound="tense quiet fading into a softer stillness"),
            cut(JUNKYARD_BLOCK.replace("굳은 표정으로", "누그러진 표정으로 손짓하며") +
                ", 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임",
                ["최사장"], 10, "Medium close-up", "Static, locked off",
                sound="quiet resolution, distant scrapyard ambience"),
        ],
    ),
    dict(
        # 시간순: ①밤 — 바퀴 교체 ②밤 — 장갑 덧감기 ③새벽 — 밀고 이동·배치
        name="5막 — 새벽 배달",
        lead_in=1.0,
        lines=[
            N("그는 밤늦도록, 자신의 몫으로 새 바퀴를 구해 맞추었습니다.", "느리게, 정성스럽게"),
            N("거친 쇠손잡이에 시릴 손을 위해, 장갑 한 짝도 덧대어 감았습니다.", "느리게, 다정하게"),
            N("그날 새벽, 아무도 없는 골목에 리어카 하나가 돌아와 있었습니다.", "잔잔하게"),
        ],
        cuts=[
            cut(f"{GUARD_BOOTH} 앞, 밤늦게, {KIM}이 손전등을 입에 물고 {CART} 바퀴를 직접 갈아 "
                f"끼우는 모습", ["김씨"], 5, "Medium close-up", "Static, locked off",
                sound="metal clinking, tools, quiet night"),
            cut(f"{CART} 손잡이 클로즈업, 밤, {KIM}의 거친 손이 해진 갈색 가죽끈 위에 낡은 남색 "
                f"작업 장갑 한 짝을 조심스레 덧대어 감는 모습", ["김씨"], 5, "Close-up",
                "Static, locked off", sound="quiet night, soft fabric handling"),
            cut(f"{ALLEY_NIGHT}, {KIM}이 고쳐진 {CART}를 새벽 어스름 속에 혼자 밀고 걸어가 "
                f"할머니의 평소 자리에 조용히 세워두는 모습", ["김씨"], 10, "Long shot",
                "Follow shot, camera behind Kim at shoulder height",
                end="ends as he sets the cart down and walks away, hold for the last second",
                sound="pre-dawn quiet street ambience, single cart wheel creak, distant rooster"),
        ],
    ),
    dict(
        name="다음날 아침 캡션", lead_in=0.3,
        lines=[C("다음날 아침")],
        cuts=[cut(f"{DEMOLITION} 인근 골목, 이른 아침 옅은 안개, 사람이 한 명도 없는, 인물 없음",
                  [], 5, "Long shot", "Static, locked off", sound="")],
    ),
    dict(
        name="6막 — 결말",
        lead_in=1.0,
        lines=[
            line("Grandma", "할머니", "…영감이 감아준 건데…", "sad(그리움, 울먹)", 0.7, 2.0,
                 "[trembling, tender]"),
            N("말 한마디 건네지 않았지만, 두 사람은 십 년 동안 온기를 주고받고 있었습니다.",
              "따뜻하게, 뭉클하게"),
            N("빚을 갚는 데, 꼬박 십 년이 걸렸습니다.", "느리게, 여운"),
            N("고마움은 몰라도 된다고, 그는 그저 덤덤히 웃을 뿐이었습니다.", "느리게, 잔잔하게"),
            N("그날 이후, 할머니의 리어카는 다시 골목길을 지켰습니다.", "따뜻하게, 여운"),
        ],
        cuts=[
            cut(f"{DEMOLITION} 인근 골목, 이른 아침, {GRANDMA}가 {CART}를 발견하고 놀라 다가가는 "
                f"장면", ["할머니"], 5, "Medium", "Static, locked off",
                sound="quiet morning ambience, birds"),
            cut(f"{CART} 손잡이의 가죽끈을 두 손으로 감싸 쓰다듬는 {GRANDMA}의 손, {DEMOLITION} "
                f"배경, 이른 아침, 한국어로 대사하며", ["할머니"], 10, "Close-up",
                "Slow zoom in, camera locked", end="hold on her trembling hands",
                sound="quiet morning ambience"),
            cut(f"{GRANDMA}의 얼굴, 눈물이 고인 채 옅은 미소, {DEMOLITION} 배경, 이른 아침",
                ["할머니"], 5, "Choker", "Static, locked off",
                end="hold on her tearful smile", sound="quiet morning ambience"),
            cut("십 년 전 겨울 회상 장면, 눈 내리는 어두운 골목에서 " + GRANDMA + "가 " + KIM +
                "에게 김이 모락모락 나는 삶은 옥수수를 말없이 건네는 모습, 세피아 톤, 짧은 인서트",
                ["할머니", "김씨"], 5, "Medium", "Static, locked off",
                palette=PALETTE_FLASHBACK, sound="soft snowfall silence, distant winter wind"),
            cut(f"{GUARD_BOOTH} 앞 창턱, 이른 아침 햇살, 김이 모락모락 나는 삶은 옥수수가 담긴 "
                f"작은 봉지 하나가 놓여 있는 모습, 사람이 한 명도 없는, 인물 없음", [], 5,
                "Close-up", "Static, locked off", sound="quiet morning ambience"),
            cut(f"{GUARD_BOOTH}, 이른 아침, {KIM}이 창턱의 옥수수 봉지를 발견하고 손에 들어보며 "
                f"옅은 미소를 짓는 장면", ["김씨"], 5, "Medium close-up", "Static, locked off",
                sound="quiet morning office ambience"),
            cut(f"{APT_GATE}, 아침 햇살 속 {GRANDMA}가 다시 {CART}를 끌고 걸어가는 모습, 힘찬 걸음",
                ["할머니"], 5, "Long shot", "Side tracking, camera moves parallel to the grandmother",
                sound="cart wheel rolling smoothly, quiet morning street"),
        ],
    ),
    dict(
        name="엔딩 카드", lead_in=0.3,
        lines=[C("고마움은 몰라도 된다. 그 사람은 원래 그런 사람이니까")],
        cuts=[cut(f"{GUARD_BOOTH} 앞, {KIM}이 뒷모습으로 서서 조용히 단지를 바라보는 모습, "
                  f"저녁 어스름", ["김씨"], 10, "Long shot",
                  "Static rear shot, back of Kim fills frame",
                  sound="quiet evening ambience")],
    ),
    dict(
        name="다음 편 예고", lead_in=0.3,
        lines=[C("다음 이야기 — 김씨의 크리스마스")],
        cuts=[cut(f"{GUARD_BOOTH} 창가, 작은 트리 장식이 살짝 보이는 겨울 예고 컷, 사람이 한 명도 "
                  f"없는, 인물 없음", [], 5, "Medium", "Static, locked off", sound="")],
    ),
]

COLD_OPEN_DUPES = ("콜드오픈 컷 1과 4막 대치 컷 1은 프롬프트가 완전히 동일함(JUNKYARD_BLOCK "
                    "구도) — 4막 대치를 먼저 생성한 뒤 그 out/sceneNN.mp4를 콜드오픈 컷 1 "
                    "자리에 복사하면 그 컷은 중복 과금 없이 재사용 가능. 나머지 컷들은 같은 "
                    "장소를 재사용하지만 구도가 달라 각각 생성해야 함")

STYLE_META = {"Kim": "김씨", "Grandma": "할머니", "Choi": "최사장", "Naration": "", "Caption": ""}
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


def lock_block(speakers, palette):
    n = len(speakers)
    if n == 0:
        return ("[LOCK] Use the reference character sheets for face and wardrobe only. Do not "
                f"remove the background. Exactly zero people in frame — an empty shot, no one "
                f"present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, "
                f"{palette}. No blood.")
    names = ", ".join(SHEET_REF[s] for s in speakers)
    count = {1: "one person", 2: "two people", 3: "three people"}[n]
    who = ", ".join(EN_NAME[s] for s in speakers)
    return (f"[LOCK] Use {names} for face and wardrobe only. Do not remove the background. "
            f"Exactly {count} in frame: {who}. Photorealistic live-action, Kodak 35mm film "
            f"grain, 24fps, 16:9, {palette}. No blood.")


def dialogue_block(entry):
    if entry is None:
        return "[DIALOGUE] none"
    name, tag, text = entry
    return f"[DIALOGUE] {EN_NAME[name]} (Korean, {tag}): \"{text}\""


def build_5block(c):
    parts = [
        lock_block(c["speakers"], c["palette"]),
        f"[SCENE] {c['desc']}",
        "[CAMERA]",
        f"Movement: {c['movement']}",
        "Speed: natural, unhurried",
        f"Framing: keep {'the full cast' if len(c['speakers']) > 1 else (EN_NAME[c['speakers'][0]] if c['speakers'] else 'the setting')} "
        f"in frame, {c['size']} throughout, {c['angle']}",
        f"End: {c['end']}",
        f"[DURATION] {c['duration']} seconds",
        dialogue_block(c["dialogue"]),
        f"[SOUND] {c['sound'] or 'none — quiet natural room tone only'}",
    ]
    return "\n".join(parts)


def build():
    events, scenes, scene_speakers, durations, ambience_prompts = [], [], [], [], []
    emotions, speed_overrides = {}, {}
    t_video, tts_line_no = 0.0, 0
    section_ends = []
    tone_rows_dialogue, tone_rows_narration = [], []
    cut_prompts = []
    mismatches = []

    for sec in SECTIONS:
        t = t_video + sec["lead_in"]
        sec_dialogue = []  # (start, end, name, tag, text) — 검증 및 [DIALOGUE] 매칭용
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
                sec_dialogue.append((start, end, entry["name"], entry["tag"] or "neutral",
                                     entry["text"]))
            elif entry["style"] == "Naration":
                tone_rows_narration.append((tts_line_no, entry))
            t += dur
        raw_span = (t - t_video) + SECTION_TAIL

        cuts = sec["cuts"]
        sec_total = sum(c["duration"] for c in cuts)
        if sec_total < raw_span:
            print(f"  경고: '{sec['name']}' 컷 합계 {sec_total}s < 오디오 길이 "
                  f"{raw_span:.1f}s — 컷 보강 필요")

        cursor = t_video
        for c in cuts:
            w0, w1 = cursor, cursor + c["duration"]
            # 이 컷의 시간창과 겹치는 대사가 있으면 5블록의 [DIALOGUE]에 채우고,
            # 화자가 c["speakers"]에 없으면 화자-화면 불일치로 기록한다(검증).
            overlapping = [d for d in sec_dialogue if d[0] < w1 and d[1] > w0]
            if overlapping and c["dialogue"] is None:
                c = dict(c, dialogue=(overlapping[0][2], overlapping[0][3], overlapping[0][4]))
            for (s0, s1, name, tag, text) in overlapping:
                if name not in c["speakers"]:
                    mismatches.append((sec["name"], name, s0, c["speakers"]))
            scenes.append(c["desc"])
            scene_speakers.append(c["speakers"])
            durations.append(c["duration"])
            ambience_prompts.append(c["sound"])
            cut_prompts.append(build_5block(c))
            cursor += c["duration"]

        t_video += sec_total
        section_ends.append(len(scenes))
        print(f"{sec['name']}: 대사/내레이션 {len(sec['lines'])}줄(오디오 {raw_span:.1f}s), "
              f"컷 {len(cuts)}개(합계 {sec_total}s)")

    if mismatches:
        print("\n화자-화면 불일치 발견:")
        for sec_name, name, s0, spk in mismatches:
            print(f"  [{sec_name}] {name} 대사(시작 {s0:.1f}s)가 걸린 컷의 speakers={spk}")
        raise SystemExit(f"화자-화면 불일치 {len(mismatches)}건 — 컷 재배치 후 다시 실행하세요.")

    total = t_video
    print(f"\n합계: TTS {tts_line_no}줄(자막카드 별도), 컷 {len(scenes)}개, "
          f"영상 {total:.0f}초 ({total / 60:.1f}분) — 화자-화면 불일치 0건")

    return dict(events=events, scenes=scenes, scene_speakers=scene_speakers,
                durations=durations, ambience_prompts=ambience_prompts, emotions=emotions,
                speed_overrides=speed_overrides, total=total,
                section_ends=section_ends[:-1], tts_line_count=tts_line_no,
                tone_dialogue=tone_rows_dialogue, tone_narration=tone_rows_narration,
                cut_prompts=cut_prompts)


def write_ass(data):
    path = os.path.join(ROOT, "subs", f"{SLUG}.ass")
    with open(path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, style, name, text in data["events"]:
            f.write(f"Dialogue: 0,{fmt_time(s)},{fmt_time(e)},{style},{name},0,0,0,,{text}\n")
    print(f"자막 저장: {path}")


def write_scenes(data):
    path = os.path.join(ROOT, "scripts", "scenes", f"{SLUG}.json")
    scenes_5block = [f"{p}\n\n{LIPSYNC_SUFFIX}" for p in data["cut_prompts"]]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ratio": "16:9", "durations": data["durations"], "scenes": scenes_5block},
                  f, ensure_ascii=False, indent=2)
    print(f"장면(컷) 5블록 프롬프트 저장: {path} ({len(data['scenes'])}개, "
          f"길이 {sorted(set(data['durations']))})")


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
                 f"컷 {len(data['scenes'])}개 · TTS {data['tts_line_count']}줄(자막카드 별도)")
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
        for c in sec["cuts"]:
            who = f" _(등장: {', '.join(c['speakers'])})_" if c["speakers"] else " _(인물 없음)_"
            lines.append(f"- [{c['duration']}s, {c['size']}, {c['movement'].split(',')[0]}] "
                         f"{c['desc']}{who}")
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
    lines.append("- 6막 회상 인서트(십 년 전 옥수수) 전후: 세피아 디졸브 0.5초로 확실히 구분")
    lines.append("- 옥수수 봉지(무인 컷)→김씨 발견 컷: 하드 컷 (수미상관 대비, 임팩트 유지)")
    with open(os.path.join(ROOT, "docs", "톤연출표-EP3-김씨와폐지할머니.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("톤 연출표 저장: docs/톤연출표-EP3-김씨와폐지할머니.md")


def write_cut_doc(data):
    lines = ["# EP3 컷 프롬프트 (규칙집 §5, 5블록 양식)", ""]
    lines.append(f"총 {len(data['cut_prompts'])}개 컷 · 각 프롬프트 끝에 파이프라인 고유 규칙 "
                 f"문구(`{LIPSYNC_SUFFIX}`)를 덧붙여 실제 생성에 사용한다.")
    lines.append("")
    lines.append(f"**컷 길이 제약**: {sorted(set(data['durations']))}초만 사용 — fal.ai Seedance가 "
                 "5·10초만 지원해서(scripts/generate_video.py), 규칙집 §6의 이상적 길이표(인서트 "
                 "3~4초 등)는 가까운 값으로 반올림했다.")
    lines.append("")
    idx = 0
    for sec in SECTIONS:
        lines.append(f"## {sec['name']}")
        lines.append("")
        for c in sec["cuts"]:
            idx += 1
            lines.append(f"### CUT {idx} ({c['duration']}s)")
            lines.append("```")
            lines.append(data["cut_prompts"][idx - 1])
            lines.append("```")
            lines.append("")
    with open(os.path.join(ROOT, "docs", "EP3-컷프롬프트.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"컷 프롬프트 문서 저장: docs/EP3-컷프롬프트.md ({idx}개 컷)")


def main():
    data = build()
    write_ass(data)
    write_scenes(data)
    write_audio_config(data)
    write_script_doc(data)
    write_tone_doc(data)
    write_cut_doc(data)
    print("\n생성 완료.")


if __name__ == "__main__":
    main()
