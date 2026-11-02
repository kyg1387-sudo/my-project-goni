#!/usr/bin/env python3
"""「みすぼらしい老人は、財閥会長だった」 제작 자산 생성기 (일본 제작 기준 첫 작품).

대본(skits/beggar-chairman.md)과 줄별 톤 연출표(docs/톤연출표-거지노인회장.md)를
세그먼트 목록으로 정의하고, 일본어 발화 길이 추정으로 타이밍을 계산해 다음을 생성한다:

    scripts/scenes/beggar-chairman.json   장면 프롬프트 (규칙집 5블록, 장면별 5/10초, 재사용 장면)
    subs/beggar-chairman.ass              일본어 자막 (화면에 굽는 자막 + 자막 카드)
    subs/beggar-chairman.ko-review.srt    사용자 검수용 한국어 임시 자막 (업로드 안 함)
    scripts/audio/beggar-chairman.json    목소리·감정·속도·연기 태그·현장음·BGM·정적·효과음 설정

세그먼트 = 연속된 장면(샷) 묶음 + 그 구간에 순서대로 놓이는 줄. 대사 세그먼트는 화자 1명이
보이는 장면 1개(화자-화면 일치), 내레이션 세그먼트는 무언 장면 여러 개 위에 놓는다.
장면 길이가 "auto"면 대사가 들어가는 최소 길이(5 또는 10초)를 고른다. 대사가 장면을
넘치면 오류로 멈춘다 — 생성 전에 무료로 잡는다(비용 원칙 1).

사용법: python3 scripts/build_beggar_chairman.py   (생성 후 정렬 검증 결과를 출력)
"""

import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
WORK = "beggar-chairman"

# ---------- 고정 외형·장소 문구 (모든 장면에서 동일 반복 — 인물 일관성 규칙 5) ----------
# 인물마다 물리적 고정 식별자 2~3개(규칙집 2장 — 미묘한 인상보다 물리적 표식이 일관성에 강함)를 반복한다.
GENZO = ("78세 일본인 노인 남성(마르고 각진 얼굴, 짧게 깎은 흰머리와 짧은 흰 턱수염, 왼쪽 눈썹 위 작은 점, "
         "깊은 이마 주름, 소매가 닳은 낡은 회색 무지 점퍼, 무릎이 해진 회색 면바지, 해진 흰 운동화)")
GENZO_FACE = ("78세 일본인 노인 남성(마르고 각진 얼굴, 짧게 깎은 흰머리와 짧은 흰 턱수염, 왼쪽 눈썹 위 작은 점, "
              "깊은 이마 주름, 소매가 닳은 낡은 회색 무지 점퍼)")
KURODA = ("45세 일본인 남성 레스토랑 지배인(갸름한 얼굴, 포마드로 넘긴 검은 올백 머리, 얇은 콧수염, "
          "검은 쓰리피스 정장, 은색 넥타이, 가슴에 아무 글자 없는 무지 금속 명찰)")
MAMIYA = ("32세 일본인 남성 사업가(둥근 얼굴, 옆을 짧게 친 갈색 투블럭 머리, 왼쪽 귀에 작은 은색 귀걸이, "
          "로고 없는 크림색 무지 니트와 베이지 코트, 손목에 굵은 은시계)")
YUI = ("21세 일본인 여성 아르바이트 홀 직원(계란형 얼굴, 일자 앞머리와 낮게 묶은 검은 머리, 왼쪽 눈 밑 작은 점, "
       "흰 셔츠에 남색 무지 앞치마)")
SAKAKI = ("64세 일본인 남성 비서실장(단정히 빗어 넘긴 백발 올백, 은테 안경, 짧은 회색 콧수염, "
          "검은 쓰리피스 정장)")
HOST = "50대 일본인 남성 진행자(단정한 회색 머리, 검은 뿔테 안경, 남색 무지 정장, 흰 셔츠, 온화한 미소)"

HALL = ("도쿄 고급 호텔 1층 일식 레스토랑 홀(따뜻한 간접 조명, 흰 식탁보, 짙은 원목 벽과 "
        "장지문풍 칸막이, 큰 통유리창, 간판·메뉴판·노렌은 아무 글자 없는 무지)")
CORNER = f"{HALL}의 안쪽 화장실 옆 구석 자리"
ENTRANCE = "같은 일식 레스토랑의 입구(짙은 원목 문, 아무 글자 없는 무지 노렌, 따뜻한 간접 조명)"
KITCHEN = "같은 일식 레스토랑의 주방(스테인리스 조리대, 직원 식사용 큰 냄비, 따뜻한 조명)"
STREET = "도쿄 도심의 오후, 고층 유리 호텔 정문 앞 돌계단(간판·글자 없는 매끈한 석재 외벽)"
CAR = "밤, 검은 고급 세단 뒷좌석 안(창밖으로 흐르는 도쿄의 불빛)"
STUDIO = "따뜻한 조명의 단정한 서재 세트(책장, 은은한 배경 흐림, 글자 없는 무지 소품)"

UDON = "흰 식탁보 위 김이 오르는 가케우동 한 그릇(맑은 국물의 일본식 우동, 파 몇 조각, 무지 도자기 그릇)"
UDON_COLD = "흰 식탁보 위 김이 나지 않는 식어 버린 가케우동 한 그릇(무지 도자기 그릇)"

PALETTE = "warm amber and deep brown palette"
STYLE = ""  # 규칙집: 스타일 블록은 각 프롬프트 안에 전부 포함 — 공통 블록 분리 금지

# ---------- 자막 스타일 / 목소리 ----------
G, K, M, Y, S, N, C, H = "Genzo", "Kuroda", "Mamiya", "Yui", "Sakaki", "Naration", "Caption", "Host"
NAMES = {G: "源蔵", K: "黒田", M: "間宮", Y: "ゆい", S: "榊", H: "司会者"}
# 프롬프트용 로마자 이름 — 프롬프트 속 한자·가나는 화면에 가짜 글자로 번질 수 있어 쓰지 않는다
ROMAJI = {G: "Genzo", K: "Kuroda", M: "Mamiya", Y: "Yui", S: "Sakaki", H: "Host"}
RJ = {NAMES[k]: v for k, v in ROMAJI.items()}
VOICES = {G: "Japanese_SeriousCommander", K: "el:Daniel", M: "Japanese_DominantMan",
          Y: "Japanese_DecisivePrincess", S: "Japanese_GentleButler", N: "el:Brian", H: "el:Brian"}

CHAR_RATE = 6.5   # 일본어 낭독 초당 글자 수(문장부호 제외, 속도 1.0 기준) — 시험 TTS 후 재측정
LINE_PAD = 0.3
MIN_DUR = 1.0
SHOT_TAIL = 0.8   # 대사 뒤 여운(규칙 8-1 ①)
NARR_SPEED = 0.9


def speech_len(text, speed):
    chars = len(re.sub(r"[\s、。！？!?…「」『』（）・―─]", "", text))
    return max(MIN_DUR, chars / (CHAR_RATE * speed) + LINE_PAD)


# 실측 TTS 길이(대사 음성 미리 생성 후 커밋되는 파일) — 있으면 추정 대신 사용하고 대사 장면을 실측 길이로 다듬는다(규칙 6)
MEASURED_PATH = os.path.join(ROOT, "scripts", "audio", f"{WORK}.tts-durations.json")
MEASURED = {}
if os.path.exists(MEASURED_PATH):
    with open(MEASURED_PATH, encoding="utf-8") as _f:
        MEASURED = {int(k): float(v) for k, v in json.load(_f).items()}
MIN_TRIM = 2.5

# ---------- 참조 이미지 (기준 초상 = 캐릭터 시트, 로케이션 시트 — 규칙 5·교훈 ⑫) ----------
REF_DIR = f"assets/refs/{WORK}"
CHAR_MARKERS = {"genzo": "78세 일본인 노인", "kuroda": "45세 일본인 남성 레스토랑 지배인",
                "mamiya": "32세 일본인 남성 사업가", "yui": "21세 일본인 여성", "sakaki": "64세 일본인 남성 비서실장",
                "host": "50대 일본인 남성 진행자"}
LOC_MARKERS = [("loc-street", ("호텔 정문 앞 돌계단", "호텔 외관")), ("loc-entrance", ("레스토랑의 입구",)),
               ("loc-kitchen", ("레스토랑의 주방",)), ("loc-car", ("세단 뒷좌석",)), ("loc-studio", ("서재 세트",)),
               ("loc-hall", ("일식 레스토랑 홀", "식탁 위 정물"))]


def refs_for(text):
    """프롬프트에 등장하는 인물·장소의 참조 시트 경로 목록 (Seedance reference-to-video 최대 4장)."""
    refs = [f"{REF_DIR}/char-{k}.png" for k, m in CHAR_MARKERS.items() if m in text]
    loc = next((k for k, ms in LOC_MARKERS if any(m in text for m in ms)), None)
    if loc:
        refs.append(f"{REF_DIR}/{loc}.png")
    return refs[:4]


# ---------- 프롬프트 (규칙집 5블록) ----------
def lock(people):
    if not people:
        return ("[LOCK] Exactly zero people in frame — 사람이 한 명도 없는, 인물 없음. "
                f"Photorealistic live-action Japanese drama, Kodak 35mm film grain, 24fps, 16:9, {PALETTE}. "
                "화면에 글자·간판 문자·자막 없음. No blood.")
    n = len(people)
    count = "Exactly one person" if n == 1 else f"Exactly {n} people"
    return (f"[LOCK] {count} in frame: {', '.join(RJ.get(p, p) for p in people)}. 모든 인물은 일본인. "
            f"Photorealistic live-action Japanese drama, Kodak 35mm film grain, 24fps, 16:9, {PALETTE}. "
            "화면에 글자·간판 문자·자막 없음. No blood.")


def prompt(people, scene, movement, speed, framing, end, dur, dialogue="none", sound=""):
    return (f"{lock(people)} [SCENE] {scene} [CAMERA] Movement: {movement}. Speed: {speed}. "
            f"Framing: {framing}. End: {end}. [DURATION] {dur} seconds. "
            f"[DIALOGUE] {dialogue} [SOUND] {sound or 'none'}")


def talk(style, place, look, expression, tone, line_jp, sound):
    """대사 장면: 화자 혼자, 가슴 위 정면(손 미포함 — 교훈 ⑪), 일본어 입 모양."""
    who = {G: GENZO_FACE, K: KURODA, M: MAMIYA, Y: YUI, S: SAKAKI, H: HOST}[style]
    scene = (f"{place}, {who} 혼자 단독 인물 샷, {look}. 정면 상반신, 가슴 위 클로즈업(손은 프레임 밖), "
             f"입을 자연스럽게 움직이며 일본어로 말하는 입 모양(한국어·영어 없음), {expression}")
    # 대사 원문은 넣지 않는다 — 따옴표 속 문장을 화면 자막처럼 그려 넣는 오생성 방지(글자 금지 규칙)
    return lambda d: prompt([NAMES[style]], scene, "slow push-in", "very slow",
                            "medium close-up, face centered, chest-up, hands out of frame",
                            "stops at close-up, hold the last 1 second", d,
                            f"{ROMAJI[style]} speaks one line in Japanese ({tone}), lips moving naturally, "
                            "no on-screen text", sound)


def silent(people, scene, movement, speed, framing, end, sound=""):
    return lambda d: prompt(people, scene, movement, speed, framing, end, d, "none", sound)


# ---------- 줄 정의: (스타일, 일본어, 한국어 검수, 감정, 속도, EL 태그, 앞침묵) ----------
def line(style, jp, ko, emotion="neutral", speed=1.0, tag="", lead=0.6):
    return dict(style=style, jp=jp, ko=ko, emotion=emotion, speed=speed, tag=tag, lead=lead)


def narr(jp, ko, speed=NARR_SPEED, tag="[warm, storytelling]", lead=0.4):
    return line(N, jp, ko, "neutral", speed, tag, lead)


def card(jp, ko, at, dur):
    """자막 카드(무음, 화면 전용) — 세그먼트 시작 기준 at초에 dur초 표시."""
    return dict(style=C, jp=jp, ko=ko, at=at, dur=dur)


# 세그먼트: name, section(전환 페이드 기준), shots=[(길이|"auto", 프롬프트 함수, 보이는 화자, 현장음, reuse_of)],
#          lines=[...], cards=[...], silence_before(정적 초), sfx=[(세그먼트 기준 초, 파일, dB)]
SEGMENTS = []


def seg(name, section, shots, lines=(), cards=(), **kw):
    SEGMENTS.append(dict(name=name, section=section, shots=list(shots), lines=list(lines),
                         cards=list(cards), **kw))


# ===== S#0 콜드 오픈 =====
L1 = line(K, "物乞いは裏口から出てってくださいって！何度言わせるんですか！",
          "거지는 뒷문으로 나가시라고요! 몇 번을 말해요?", "angry", 1.10, "[shouting, irritated]", 0.3)
seg("S0 콜드오픈 — 지배인 고함", 0, [("auto", talk(
    K, HALL, "노인 쪽으로 몸을 숙이고 낡은 점퍼 소매를 거칠게 잡아당기는 순간(손은 프레임 밖)",
    "경멸로 일그러진 화난 얼굴", "shouting, irritated", L1["jp"], "fabric yank, chair scrape"),
    [NAMES[K]], "fabric yank, chair scraping on wooden floor", None)], [L1])
L2 = line(M, "うわ、これマジで撮ってアップしよ。", "와, 이거 진짜 찍어서 올려야겠다.",
          "happy", 1.05, "[mocking laugh]", 0.4)
seg("S0 콜드오픈 — 間宮 촬영", 0, [("auto", talk(
    M, HALL, "옆 테이블에 앉아 휴대폰을 얼굴 높이로 들고 촬영하는 자세(휴대폰은 프레임 아래쪽)",
    "비웃는 입꼬리, 즐거워하는 얼굴", "mocking laugh", L2["jp"], "phone camera shutter click"),
    [NAMES[M]], "", None)], [L2])
seg("S0 콜드오픈 — 노인 정적 + 내레이션 훅", 0, [
    (5, silent([NAMES[G]], f"{HALL}, {GENZO_FACE} 혼자, 화내지 않고 담담하게 위를 올려다보는 얼굴, 김이 오르는 우동 그릇이 앞에 흐릿하게",
               "static", "locked off", "close-up, face centered", "hold the whole shot like a freeze frame"),
     [], "", None),
    (10, silent([], f"{UDON}, 사람이 한 명도 없는, 인물 없음. 레스토랑 흰 식탁 위 정물, 배경은 따뜻한 조명의 흐림",
                "slow push-in", "very slow", "insert close-up of the bowl", "hold the last 1 second"),
     [], "", None),
], [
    narr("このレストランで、彼に気づいた者は、一人もいませんでした。",
         "이 레스토랑에서 그를 알아본 사람은, 단 한 명도 없었습니다.", 0.9, "[low, secretive]", 0.5),
    narr("この老人こそが、天城グループを一代で築いた男だということに。",
         "이 노인이, 天城그룹을 혼자 힘으로 일군 사람이라는 것을.", 0.9, "[slow, weighty]", 0.6),
])
seg("S0 궁금증 카드 + 타이틀", 0, [(5, silent([],
    "해 질 녘 도쿄 도심의 고층 유리 호텔 외관, 사람이 한 명도 없는, 인물 없음. 간판·글자 없는 매끈한 외벽, 따뜻한 노을빛",
    "slow push-in", "very slow", "wide establishing shot of the hotel tower", "hold the last 1 second"),
    [], "", None)], [], [
    card("三十分後、この支配人は土下座することになる", "삼십 분 뒤, 이 지배인은 무릎 꿇고 엎드리게 됩니다", 0.2, 2.3),
    card("みすぼらしい老人は、財閥会長だった", "타이틀: 거지 노인은 재벌 회장님이었다", 2.7, 2.2)])

# ===== S#1 一時間前 — 호텔 앞 =====
seg("S1 한 시간 전 — 호텔 앞", 1, [
    (5, silent([NAMES[G]], f"{STREET}, {GENZO}가 해진 운동화로 돌계단 위에 멈춰 서는 발걸음, 발과 계단 위주",
               "static", "locked off", "low angle insert on worn sneakers on stone steps", "hold the last 1 second"),
     [], "city street traffic hum, distant footsteps, no voices", None),
    (10, silent([NAMES[G]], f"{STREET}, {GENZO} 혼자 고개를 들어 높은 유리 호텔 건물을 올려다보는 뒷모습",
                "tilt up", "slow", "from his back to the top of the glass tower, full shot to wide",
                "stops on the tower top, hold the last 1 second"),
     [], "city street traffic hum, wind, no voices", None),
    (10, silent([NAMES[G]], f"{STREET}, {GENZO} 혼자 호텔 외벽의 매끈한 돌을 손바닥으로 천천히 쓸어 보는 모습, 그리운 표정",
                "slow push-in", "slow", "medium shot to close-up on his hand and profile",
                "hold the last 1 second"),
     [], "city street traffic hum, no voices", None),
    (5, silent([NAMES[G]], f"{STREET}, {GENZO_FACE} 혼자 눈을 감고 옛일을 떠올리는 얼굴, 오후 햇살",
               "static", "locked off", "close-up, face centered", "hold the last 1 second"),
     [], "city street traffic hum, no voices", None),
], [
    narr("天城源蔵、七十八歳。天城グループの創業者。", "아마기 겐조, 일흔여덟. 天城그룹 창업자.", 0.9, "[calm, introducing]", 1.9),
    narr("医者は彼に、残された時間は一年だと告げました。", "의사는 그에게, 남은 시간이 일 년이라고 했습니다.", 0.9, "[quiet]", 0.8),
    narr("会社を譲る前に、彼にはどうしても、自分の目で確かめたいことがありました。",
         "회사를 물려주기 전에, 그는 꼭 자기 눈으로 확인하고 싶은 것이 있었습니다.", 0.9, "[curious]", 0.8),
    narr("自分の会社が今もまだ、腹を空かせた人にご飯を出せる場所なのかどうか。",
         "자기 회사가 아직도, 배고픈 사람에게 밥을 내어 주는 곳인지.", 0.9, "[warm]", 0.6),
    narr("七十年前、この場所には、小さなうどん屋がありました。",
         "칠십 년 전, 이 자리에는 작은 우동집이 있었습니다.", 0.85, "[slow, nostalgic]", 0.8),
], [card("一時間前", "한 시간 전", 0.2, 1.5)], lowpass_note="거리 소음은 로우패스 처리(ambience_lowpass)")

# ===== S#2 입구 =====
L3 = line(K, "ちょっと、お客さん。ここ、入られちゃ困るんですけど。", "저기요, 어르신. 여기 들어오시면 곤란한데요.",
          "disgusted", 1.0, "[cold, condescending]", 0.8)
L4 = line(G, "飯を一杯、食べに来たんじゃ。かけうどんはあるかね？", "밥 한 그릇 먹으러 왔소. 가케우동 되겠소?",
          "neutral", 0.85, lead=1.0)
L5 = line(K, "かけうどん？うちのコースは、一番安くても三万円ですよ。", "가케우동이요? 여기 코스는 제일 싼 게 삼만 엔이에요.",
          "happy", 1.05, "[scoffing]", 0.6)
L6 = line(G, "金なら、ある。", "돈은 있소.", "neutral", 0.80, lead=1.0)
L7 = line(K, "…はぁ。じゃあ、あっちの隅の席にどうぞ。トイレの横です。", "…하. 그럼 저쪽 구석 자리로 가세요. 화장실 옆이요.",
          "disgusted", 1.0, "[annoyed sigh]", 0.8)
seg("S2 입구 — 지배인 훑어봄", 2, [(5, silent([NAMES[K], NAMES[G]],
    f"{ENTRANCE}, {KURODA}가 입구에 들어선 {GENZO}의 옷차림을 위아래로 훑어보는 투샷, 지배인의 경멸하는 눈빛",
    "static", "locked off", "two-shot, full body, both faces visible", "hold the last 1 second"), [], "", None)])
seg("S2 L3", 2, [("auto", talk(K, ENTRANCE, "입구에 서서 노인을 내려다봄", "차갑고 거만한 무표정, 위아래로 훑는 눈",
                                "cold, condescending", L3["jp"], ""), [NAMES[K]], "", None)], [L3])
seg("S2 L4", 2, [("auto", talk(G, ENTRANCE, "입구에 서서 지배인을 바라봄", "온화한 무표정, 차분한 눈빛",
                                "calm, gentle", L4["jp"], ""), [NAMES[G]], "", None)], [L4])
seg("S2 L5", 2, [("auto", talk(K, ENTRANCE, "입구에 서서 노인을 내려다봄", "코웃음 치며 비웃는 얼굴",
                                "scoffing", L5["jp"], ""), [NAMES[K]], "", None)], [L5])
seg("S2 L6", 2, [("auto", talk(G, ENTRANCE, "입구에 서서 지배인을 똑바로 바라봄", "조용하고 단단한 눈빛, 눈을 피하지 않음",
                                "quiet, firm", L6["jp"], ""), [NAMES[G]], "", None)], [L6])
seg("S2 L7", 2, [("auto", talk(K, ENTRANCE, "턱으로 홀 안쪽을 가리키는 동작(손은 프레임 밖)", "귀찮다는 듯 한숨 쉬는 얼굴",
                                "annoyed sigh", L7["jp"], ""), [NAMES[K]], "", None)], [L7])

# ===== S#3 구석 자리 =====
L8 = line(M, "支配人さん、あっち臭くて飯が食えないんですけど？", "지배인님, 저쪽 냄새 나서 밥을 못 먹겠는데요?",
          "disgusted", 1.05, lead=0.8)
L9 = line(K, "これは大変失礼いたしました、間宮社長。すぐに片付けますので。", "이거 대단히 실례했습니다, 마미야 사장님. 금방 정리하겠습니다.",
          "neutral", 1.10, "[fawning]", 0.5)
L10 = line(K, "お客さん、水だけ飲んだら帰ってください。他のお客様のご迷惑なんで。",
           "어르신, 물만 드시고 가세요. 다른 손님들께 폐가 되니까요.", "angry", 0.95, "[low, threatening]", 0.8)
seg("S3 구석 자리 착석", 3, [(5, silent([NAMES[G]],
    f"{CORNER}, {GENZO} 혼자 구석 자리에 조용히 앉는 모습, 주변은 흐릿한 빈 테이블들",
    "static", "locked off", "medium wide shot, he sits alone at a small table", "hold the last 1 second"), [], "", None)])
seg("S3 L8", 3, [("auto", talk(M, HALL, "자기 테이블에 앉아 구석 쪽을 흘끗 봄", "코를 찡그린 불쾌한 얼굴",
                                "whiny, loud", L8["jp"], ""), [NAMES[M]], "", None)], [L8])
seg("S3 L9", 3, [("auto", talk(K, HALL, "손님 테이블 앞에서 허리를 살짝 굽힘", "과장된 굽신 미소",
                                "fawning", L9["jp"], ""), [NAMES[K]], "", None)], [L9])
seg("S3 L10", 3, [("auto", talk(K, CORNER, "노인 쪽으로 몸을 숙여 목소리를 낮춤", "낮고 위협적인 화난 얼굴",
                                 "low, threatening", L10["jp"], ""), [NAMES[K]], "", None)], [L10])
seg("S3 노인 창밖", 3, [(5, silent([NAMES[G]],
    f"{CORNER}, {GENZO_FACE} 혼자 말없이 창밖을 바라보는 옆얼굴, 쓸쓸하지만 담담한 표정",
    "static", "locked off", "close-up profile", "hold the last 1 second"), [], "", None)])

# ===== S#4 ゆい =====
L11 = line(Y, "おじいさん、温かいお茶です。ゆっくり飲んでくださいね。", "할아버지, 따뜻한 차예요. 천천히 드세요.",
           "happy", 0.95, lead=0.8)
L12 = line(G, "ありがとう。お嬢さんは、ここで働いて長いのかね？", "고맙구먼. 아가씨는 여기서 일한 지 오래됐소?",
           "happy", 0.85, lead=0.8)
L13 = line(Y, "三ヶ月です。学費を稼いでるんです。", "석 달이요. 학비를 벌고 있어요.", "happy", 1.0, lead=0.6)
L14 = line(Y, "かけうどんはメニューにないんですけど…厨房に聞いてみますね。",
           "가케우동은 메뉴에 없는데요… 주방에 한번 물어볼게요.", "neutral", 0.95, lead=0.8)
seg("S4 찻잔 내려놓음", 4, [(5, silent([NAMES[Y], NAMES[G]],
    f"{CORNER}, {YUI}가 {GENZO} 앞 식탁에 김이 오르는 무지 찻잔을 조용히 내려놓는 장면, 찻잔과 손 위주",
    "static", "locked off", "insert close-up on the teacup being set down", "hold the last 1 second"),
    [], "ceramic teacup set gently on a table", None)])
seg("S4 L11", 4, [("auto", talk(Y, CORNER, "식탁 옆에 서서 노인을 내려다봄", "다정한 미소",
                                 "soft, kind", L11["jp"], ""), [NAMES[Y]], "", None)], [L11])
seg("S4 L12", 4, [("auto", talk(G, CORNER, "자리에 앉아 아가씨를 올려다봄, 앞에 찻잔", "처음으로 옅은 미소",
                                 "warm", L12["jp"], ""), [NAMES[G]], "", None)], [L12])
seg("S4 L13", 4, [("auto", talk(Y, CORNER, "식탁 옆에 서 있음", "수줍게 웃는 얼굴",
                                 "shy", L13["jp"], ""), [NAMES[Y]], "", None)], [L13])
seg("S4 L14", 4, [("auto", talk(Y, CORNER, "주위를 살피며 몸을 살짝 숙임", "결심한 듯 작게 속삭이는 얼굴",
                                 "whisper", L14["jp"], ""), [NAMES[Y]], "", None)], [L14])
seg("S4 주방 몽타주", 4, [(10, silent([NAMES[Y]],
    f"{KITCHEN}, {YUI} 혼자 직원 식사용 큰 냄비에서 국자로 우동 국물을 무지 도자기 그릇에 붓는 장면",
    "slow push-in", "slow", "medium shot to close-up on the bowl", "hold the last 1 second"),
    [], "ladle pouring broth into a ceramic bowl, kitchen simmer, no voices", None)], [
    narr("メニューにないかけうどん。まかないの一杯を、彼女はこっそり用意しました。",
         "메뉴에 없는 가케우동. 직원 식사 한 그릇을, 그녀는 몰래 준비했습니다.", 0.9, "[warm]", 1.2)])

# ===== S#5 갈등 고조 =====
L15 = line(K, "春川さん！まかないを客に出すなんて、何考えてるんですか！",
           "하루카와 씨! 직원 밥을 손님한테 내다니, 무슨 생각이에요!", "angry", 1.10, "[shouting]", 0.5)
L16 = line(Y, "おじいさんが、かけうどんを食べたいっておっしゃったので…",
           "할아버지가 가케우동을 드시고 싶다고 하셔서…", "fearful", 0.90, lead=0.6)
L17 = line(K, "バイトのくせに出しゃばらないでください。今日で辞めてもらいます。",
           "알바 주제에 나서지 마세요. 오늘부로 그만두세요.", "angry", 1.0, "[cold]", 0.5)
L18 = line(M, "ははっ、物乞いとバイト、セットでクビかよ。", "하하, 거지랑 알바, 세트로 잘리네.", "happy", 1.05, lead=0.6)
seg("S5 우동 앞 노인", 5, [(5, silent([NAMES[G]],
    f"{CORNER}, {GENZO_FACE} 혼자 앞에 놓인 김이 오르는 가케우동 그릇을 한참 내려다보는 얼굴, 눈가가 촉촉함",
    "slow push-in", "very slow", "close-up, the steaming bowl soft in the foreground", "hold the last 1 second"),
    [], "", None)])
seg("S5 L15", 5, [("auto", talk(K, CORNER, "성큼 다가와 아르바이트생을 노려봄", "화난 얼굴",
                                 "shouting", L15["jp"], ""), [NAMES[K]], "", None)], [L15])
seg("S5 L16", 5, [("auto", talk(Y, CORNER, "몸을 움츠림", "겁먹은 눈, 떨리는 입술",
                                 "timid, shaky", L16["jp"], ""), [NAMES[Y]], "", None)], [L16])
seg("S5 L17", 5, [("auto", talk(K, CORNER, "차갑게 내려다봄", "차갑고 화난 얼굴",
                                 "cold", L17["jp"], ""), [NAMES[K]], "", None)], [L17])
seg("S5 L18 + 예고 카드", 5, [(10, talk(M, HALL, "휴대폰을 든 채 웃음(휴대폰은 프레임 아래쪽)", "비웃으며 웃는 얼굴",
                                         "laughing", L18["jp"], ""), [NAMES[M]], "", None)], [L18],
    [card("この後──支配人の顔が真っ青に", "잠시 후 — 지배인의 얼굴이 새파랗게 질립니다", "after", 3.0)])

# ===== S#6 콜드 오픈 합류 =====
L19 = line(Y, "支配人、うどん代は私が払います。おじいさんに食べさせてあげてください。",
           "지배인님, 우동 값은 제가 낼게요. 할아버지 드시게 해 주세요.", "sad", 0.95, lead=1.0)
L20 = line(K, "お前も一緒に出ていけ！二人とも、今すぐだ！", "너도 같이 나가! 둘 다, 당장!", "angry", 1.15, "[yelling]", 0.3)
L21 = line(G, "そのうどん代は、わしが払おう。", "그 우동 값은, 내가 내겠소.", "neutral", 0.80, lead=1.5)
seg("S6 L1 재사용", 6, [("auto", None, [NAMES[K]], "fabric yank, chair scraping on wooden floor", 1)], [dict(L1)])
seg("S6 L19", 6, [("auto", talk(Y, CORNER, "지배인 앞을 막아섬", "눈물 고인 간절한 눈",
                                 "pleading", L19["jp"], ""), [NAMES[Y]], "", None)], [L19])
seg("S6 L20", 6, [("auto", talk(K, CORNER, "삿대질 직전처럼 몸을 앞으로 내밈(손은 프레임 밖)", "핏대 선 분노한 얼굴",
                                 "yelling", L20["jp"], ""), [NAMES[K]], "", None)], [L20])
seg("S6 L21", 6, [("auto", talk(G, CORNER, "자리에 앉은 채 지배인을 올려다봄", "처음으로 단단해진 눈빛, 낮고 위엄 있는 얼굴",
                                 "low, commanding", L21["jp"], ""), [NAMES[G]], "", None)], [L21],
    sfx_at_line_start=("assets/sfx/heartbeat.wav", -14, 1.4))

# ===== S#7 신분 공개 (정적 → 문 열림 → 인사 → 임팩트) =====
L22 = line(S, "会長、お車の用意ができております。", "회장님, 차 준비됐습니다.", "neutral", 0.90, lead=0.6)
L23 = line(K, "か、会長…ですって…？", "회, 회장님…이라고요…?", "fearful", 0.85, "[stammering, shocked]", 1.0)
L24 = line(S, "天城グループ創業者、天城源蔵会長でいらっしゃいます。このホテルのオーナーです。",
           "天城그룹 창업자, 아마기 겐조 회장님이십니다. 이 호텔의 주인이시죠.", "neutral", 0.90, lead=0.8)
seg("S7 문 열림", 7, [(5, silent([NAMES[S]],
    f"{ENTRANCE}, 활짝 열린 원목 문으로 {SAKAKI}가 홀로 걸어 들어오는 장면, 위엄 있는 걸음",
    "static", "locked off", "full shot from inside the hall toward the door", "hold the last 1 second"),
    [], "heavy wooden door opening, three leather shoe footsteps on wooden floor", None)],
    silence_before=1.0)
seg("S7 깊은 인사", 7, [(5, silent([NAMES[S], NAMES[G]],
    f"{CORNER}, {SAKAKI}가 자리에 앉은 {GENZO} 앞에 서서 허리를 깊이 숙여 인사하는 장면",
    "static", "locked off", "two-shot, side angle, full body", "hold the last 1 second"), [], "", None)])
seg("S7 L22", 7, [("auto", talk(S, CORNER, "인사 후 고개를 든 자세", "정중하고 깊은 무표정",
                                 "respectful, deep", L22["jp"], ""), [NAMES[S]], "", None)], [L22],
    sfx_after_line=("assets/sfx/impact-low.wav", -6, 0.2), bgm_change_after_line=True)
seg("S7 지배인 리액션 + L23", 7, [("auto", talk(K, CORNER, "얼어붙은 채 서 있음", "새파랗게 질린 얼굴, 떨리는 입술",
                                              "stammering, shocked", L23["jp"], ""), [NAMES[K]], "", None)], [L23])
seg("S7 L24", 7, [("auto", talk(S, CORNER, "회장 옆에 곧게 서 있음", "단호한 무표정",
                                 "firm", L24["jp"], ""), [NAMES[S]], "", None)], [L24])
seg("S7 間宮 휴대폰 내림", 7, [(5, silent([NAMES[M]],
    f"{HALL}, {MAMIYA} 혼자 들고 있던 휴대폰을 천천히 내리는 모습, 당황해 굳은 얼굴",
    "static", "locked off", "medium shot", "hold the last 1 second"), [], "", None)])

# ===== S#8 참교육 =====
L25 = line(G, "黒田支配人。この場所に、もともと何があったか知っとるかね？", "구로다 지배인. 이 자리에 원래 뭐가 있었는지 아시오?",
           "neutral", 0.80, lead=1.2)
L26 = line(G, "七十年前、ここは小さなうどん屋じゃった。", "칠십 년 전, 여기는 작은 우동집이었소.", "sad", 0.80, lead=1.0)
L26b = line(G, "家も親もない八つの子に、タダでかけうどんを出してくれた店じゃ。",
            "집도 부모도 없는 여덟 살 아이에게, 공짜로 가케우동을 내준 가게였지.", "sad", 0.80, lead=0.4)
L27 = line(G, "その子が、わしじゃよ。", "그 아이가, 나요.", "sad", 0.75, lead=2.0)
L28 = line(G, "腹を空かせた人を裏口から追い出す店なら…天城の名を掲げる資格はない。",
           "배고픈 사람을 뒷문으로 내쫓는 가게라면… 天城의 이름을 걸 자격이 없소.", "neutral", 0.85, lead=1.0)
L29 = line(K, "会長…存じ上げず、本当に申し訳ございません…！", "회장님… 몰라뵙고, 정말 죄송합니다…!",
           "fearful", 0.90, "[trembling, desperate]", 1.0)
L30 = line(G, "知らなかったから申し訳ない、か…知っておったら、しなかったということじゃな。",
           "몰라봐서 죄송하다라… 알았더라면, 안 그랬다는 말이구먼.", "sad", 0.80, lead=1.5)
L31 = line(G, "明日からは、もう来なくて結構です。", "내일부터는, 더 나오지 않으셔도 됩니다.", "neutral", 0.80, lead=1.5)
L32 = line(M, "会長、あの…うちの父が、天城さんの取引先をやってまして…", "회장님, 저기… 저희 아버지가, 天城 거래처를 하고 있어서…",
           "fearful", 1.0, lead=0.8)
L33 = line(S, "間宮社長のお父様には、今夜、会長が直接お電話なさいます。", "마미야 사장님 아버님께는, 오늘 밤 회장님께서 직접 전화하실 겁니다.",
           "neutral", 0.90, lead=0.6)
GENZO_STAND = "자리에서 일어나 지배인을 마주 봄"
seg("S8 L25", 8, [("auto", talk(G, CORNER, GENZO_STAND, "차분하고 조용한 정면 얼굴", "calm, quiet", L25["jp"], ""),
                   [NAMES[G]], "", None)], [L25])
seg("S8 지배인 고개 저음", 8, [(5, silent([NAMES[K]], f"{CORNER}, {KURODA} 혼자 겁에 질려 천천히 고개를 젓는 얼굴",
                                      "static", "locked off", "close-up", "hold the last 1 second"), [], "", None)])
seg("S8 L26", 8, [("auto", talk(G, CORNER, GENZO_STAND, "먼 곳을 보는 그리운 눈빛", "nostalgic, soft", L26["jp"], ""),
                   [NAMES[G]], "", None)], [L26])
seg("S8 L26b", 8, [("auto", talk(G, CORNER, GENZO_STAND, "그리움에 젖은 눈빛, 옅게 떨리는 입가", "nostalgic, soft", L26b["jp"], ""),
                    [NAMES[G]], "", None)], [L26b])
seg("S8 L27", 8, [("auto", talk(G, CORNER, GENZO_STAND, "긴 침묵 끝에 눈가가 젖은 얼굴", "low, sad", L27["jp"], ""),
                   [NAMES[G]], "", None)], [L27])
seg("S8 L28", 8, [("auto", talk(G, CORNER, GENZO_STAND, "단단한 정면 얼굴", "firm, steady", L28["jp"], ""),
                   [NAMES[G]], "", None)], [L28])
seg("S8 土下座", 8, [(5, silent([NAMES[K]], f"{CORNER}, {KURODA} 혼자 나무 바닥에 무릎을 꿇고 이마를 숙여 엎드리는 도게자(일본식 엎드려 사죄) 동작",
                               "static", "locked off", "full shot, side angle", "hold the last 1 second"),
                      [], "knees hitting a wooden floor, fabric rustle", None)])
seg("S8 L29", 8, [("auto", talk(K, CORNER, "바닥에 엎드렸다가 고개만 든 자세", "떨며 절박하게 올려다보는 얼굴",
                                 "trembling, desperate", L29["jp"], ""), [NAMES[K]], "", None)], [L29])
seg("S8 L30", 8, [("auto", talk(G, CORNER, GENZO_STAND, "씁쓸한 눈빛", "bitter, quiet", L30["jp"], ""),
                   [NAMES[G]], "", None)], [L30])
seg("S8 L31", 8, [("auto", talk(G, CORNER, GENZO_STAND, "소리치지 않는 차분하고 냉정한 얼굴", "calm, final", L31["jp"], ""),
                   [NAMES[G]], "", None)], [L31])
seg("S8 L32", 8, [("auto", talk(M, HALL, "자리에서 엉거주춤 일어남", "식은땀 흘리며 억지로 웃는 얼굴",
                                 "nervous", L32["jp"], ""), [NAMES[M]], "", None)], [L32])
seg("S8 L33", 8, [("auto", talk(S, CORNER, "곧게 서서 마미야를 바라봄", "차갑고 정중한 얼굴",
                                 "polite, cold", L33["jp"], ""), [NAMES[S]], "", None)], [L33])

# ===== S#9 かけうどん 한 그릇 =====
L34 = line(G, "お嬢さん、うどんを…もう一杯、温めてくれるかね？", "아가씨, 우동을… 한 그릇 더 데워 주겠소?",
           "happy", 0.85, lead=1.0)
L35 = line(Y, "はい、おじいさん！すぐ温めてきます！", "네, 할아버지! 금방 데워 올게요!", "happy", 1.0, lead=0.6)
L36 = line(G, "七十年ぶりじゃ…同じ味がする。", "칠십 년 만이구먼… 같은 맛이 나.", "sad", 0.75, lead=1.5)
L37 = line(G, "お嬢さんは来年度から、天城の奨学生じゃ。学費の心配はいらんよ。",
           "아가씨는 내년부터, 天城 장학생이오. 학비 걱정은 하지 마시오.", "happy", 0.85, lead=1.0)
L38 = line(G, "榊。今日からこの店のメニューに、かけうどんを載せなさい。", "사카키. 오늘부터 이 가게 메뉴에 가케우동을 올리게.",
           "happy", 0.85, lead=1.0)
L38b = line(G, "腹を空かせた人からは、お代はもらわんように。", "배고픈 사람한테는, 값을 받지 말고.", "happy", 0.85, lead=0.4)
seg("S9 완충 — 식은 우동", 9, [(5, silent([], f"{UDON_COLD}, 사람이 한 명도 없는, 인물 없음. 레스토랑 구석 식탁 위 정물",
                                     "static", "locked off", "insert close-up of the cold bowl", "hold the whole shot"),
                              [], "", None)])
seg("S9 L34", 9, [("auto", talk(G, CORNER, "다시 자리에 앉아 아가씨를 올려다봄", "따뜻하고 다정한 미소", "warm, gentle", L34["jp"], ""),
                   [NAMES[G]], "", None)], [L34])
seg("S9 L35", 9, [("auto", talk(Y, CORNER, "식탁 옆에 서 있음", "젖은 눈으로 밝게 웃는 얼굴", "teary, bright", L35["jp"], ""),
                   [NAMES[Y]], "", None)], [L35])
seg("S9 우동 한 입", 9, [(5, silent([NAMES[G]], f"{CORNER}, {GENZO} 혼자 김이 오르는 가케우동을 젓가락으로 한 입 드는 모습, 눈가가 젖음",
                                 "static", "locked off", "medium close-up, bowl and face", "hold the last 1 second"),
                          [], "chopsticks touching a ceramic bowl, soft slurp", None)])
seg("S9 L36", 9, [("auto", talk(G, CORNER, "식탁 앞에 앉아 있음(그릇은 프레임 밖)", "눈물이 고인 채 떨리는 얼굴", "tearful, trembling", L36["jp"], ""),
                   [NAMES[G]], "", None)], [L36])
seg("S9 L37", 9, [("auto", talk(G, CORNER, "아가씨를 올려다봄", "인자한 미소", "warm, kind", L37["jp"], ""),
                   [NAMES[G]], "", None)], [L37])
seg("S9 ゆい 눈물", 9, [(5, silent([NAMES[Y]], f"{CORNER}, {YUI} 혼자 두 손으로 입을 막고 눈물을 흘리는 얼굴",
                                "static", "locked off", "close-up", "hold the last 1 second"), [], "", None)])
seg("S9 L38", 9, [("auto", talk(G, CORNER, "옆에 선 비서실장 쪽을 바라봄", "단단하고 따뜻한 얼굴", "warm but firm", L38["jp"], ""),
                   [NAMES[G]], "", None)], [L38])
seg("S9 L38b", 9, [("auto", talk(G, CORNER, "비서실장을 바라본 채", "따뜻하게 미소 짓는 얼굴", "warm but firm", L38b["jp"], ""),
                    [NAMES[G]], "", None)], [L38b])

# ===== S#10 에필로그 =====
seg("S10 세단 뒷좌석", 10, [
    (10, silent([NAMES[G]], f"{CAR}, {GENZO_FACE} 혼자 창밖 도시 불빛을 말없이 바라보는 옆얼굴, 평온한 표정",
                "slow push-in", "very slow", "medium close-up profile", "hold the last 1 second"),
     [], "quiet luxury car interior, low engine hum, no voices", None),
    (10, silent([], "밤 도쿄 도심의 고층 빌딩 야경, 사람이 한 명도 없는, 인물 없음. 간판·글자 없는 건물들",
                "slow pan right", "slow", "wide establishing shot of the night skyline", "hold the last 1 second"),
     [], "distant city night ambience, no voices", None),
], [
    narr("その夜、天城会長は、遺言書に一行を書き加えました。", "그날 밤, 아마기 회장은 유언장에 한 줄을 덧붙였습니다.", 0.9, "[quiet]", 1.0),
    narr("「どん底でひざまずいたことのある者だけが、人をひざまずかせない。」",
         "밑바닥에서 무릎 꿇어본 사람만이, 남을 무릎 꿇리지 않는다.", 0.8, "[slow, gentle]", 0.8),
    narr("そして一年後。この一行が、彼の孫を配達員にするのです。",
         "그리고 일 년 뒤. 이 한 줄이, 그의 손자를 배달원으로 만듭니다.", 0.9, "[teasing, curious]", 0.8),
], [card("次回──会長の最後の配達", "다음 이야기 — 회장님의 마지막 배달", "after", 3.0)])

# ===== S#11 아웃트로 =====
HOST_LINE = line(H, "皆さんの周りにも、こんな人はいますか？ぜひコメントで教えてください。",
                 "여러분 곁에도 이런 분이 계신가요? 댓글로 들려주세요.", "happy", 1.0, "[warm, friendly]", 0.5)
HOST_LINE2 = line(H, "チャンネル登録も、よろしくお願いします。", "구독도 잘 부탁드립니다.", "happy", 1.0, "[warm, bright]", 0.3)
seg("S11 아웃트로", 11, [("auto", talk(H, STUDIO, "카메라를 향해 앉아 있음", "온화한 미소", "warm, friendly",
                                     HOST_LINE["jp"], ""), [NAMES[H]], "", None)], [HOST_LINE, HOST_LINE2])


# ---------- 참조 이미지 프롬프트 (규칙집 2·3장. 시트 안 글자는 넣지 않음 — 글자 금지 규칙이 우선) ----------
SHEET_STYLE = ("photorealistic, soft studio lighting, minimal style, Kodak 35mm film grain, "
               "absolutely no text, no letters, no labels, no logos anywhere in the image")
CHAR_SHEETS = {
    "genzo": ("78-year-old Japanese man, thin build, slightly stooped",
              "worn-out plain grey zip jacket with frayed cuffs, grey cotton trousers worn at the knees, "
              "old scuffed white sneakers, no logos",
              "calm gentle expression", "very short cropped white hair",
              "lean angular face, short white chin beard, small mole above the left eyebrow, deep forehead wrinkles"),
    "kuroda": ("45-year-old Japanese man, slim upright build",
               "black three-piece suit, silver tie, white shirt, plain blank metal name badge with no lettering, "
               "polished black shoes",
               "arrogant composed expression", "black hair slicked back with pomade",
               "narrow face, thin moustache, sharp eyes"),
    "mamiya": ("32-year-old Japanese man, medium build",
               "plain cream knit sweater without logo, beige long coat, dark slacks, brown loafers, "
               "thick silver wristwatch",
               "smug half-smile", "brown two-block haircut, sides cropped short",
               "round face, small silver stud earring in the left ear"),
    "yui": ("21-year-old Japanese woman, petite build",
            "white shirt, plain navy waist apron without logo, black trousers, black flat shoes",
            "kind warm smile", "straight black bangs, black hair tied in a low ponytail",
            "oval face, small mole under the left eye"),
    "sakaki": ("64-year-old Japanese man, tall dignified build",
               "black three-piece suit, dark tie, white shirt, polished black shoes",
               "composed respectful expression", "neatly combed-back white hair",
               "silver-rimmed glasses, short grey moustache"),
    "host": ("50-year-old Japanese man, medium build",
             "plain navy suit, white shirt, no tie, brown shoes",
             "warm friendly smile", "neat grey hair", "black horn-rimmed glasses, gentle eyes"),
}
LOC_SHEETS = {
    "loc-hall": ("the dining hall of an upscale Japanese restaurant on the ground floor of a Tokyo hotel: warm indirect "
                 "lighting, white tablecloths, dark wooden walls, shoji-style partitions, large floor-to-ceiling windows, "
                 "completely blank menus and noren curtains",
                 "a small corner table beside the restroom passage", "a central table by the window"),
    "loc-entrance": ("the entrance of the same upscale Japanese restaurant: heavy dark wooden door, blank plain noren "
                     "curtain with no lettering, warm indirect lighting",
                     "the doorway seen from inside the hall", "the reception podium area"),
    "loc-kitchen": ("the kitchen of the same Japanese restaurant: stainless steel counters, a large staff-meal stockpot "
                    "on the stove, warm practical lighting",
                    "the stove with the large pot", "a prep counter with ceramic bowls"),
    "loc-street": ("the front of a tall glass hotel tower in central Tokyo: wide stone entrance steps, smooth stone "
                   "facade with no signage or lettering",
                   "the stone steps seen from street level", "the smooth stone wall beside the entrance"),
    "loc-car": ("the back seat of a black luxury sedan at night, Tokyo city lights streaming past the window",
                "the rear seat by the window", "view through the side window"),
    "loc-studio": ("a tidy study set with bookshelves and warm lighting, softly blurred background, plain props",
                   "an armchair facing the camera", "the bookshelf background"),
}


def image_jobs():
    jobs = []
    for cid, (who, wardrobe, expr, hair, face) in CHAR_SHEETS.items():
        jobs.append({"id": f"char-{cid}", "out": f"{REF_DIR}/char-{cid}.png", "prompt": (
            f"Character reference sheet, one single 16:9 image on a pure white background, {SHEET_STYLE}, "
            f"fashion-lookbook layout. Left half: full-body front view and full-body back view of the same {who} "
            "standing side by side, feet visible, both figures cropped at the neck so the head is cut off by the top "
            f"edge of the frame — no face shown on the left side. Wardrobe: {wardrobe}. Right half: one large close-up "
            f"portrait from the shoulders up, straight to camera, {expr}, {hair}, {face}. Exactly one person depicted.")})
    for lid, (place, pos1, pos2) in LOC_SHEETS.items():
        jobs.append({"id": lid, "out": f"{REF_DIR}/{lid}.png", "prompt": (
            "Location reference sheet, one single 16:9 image divided into a 2x2 grid of four photographs of the same "
            f"place, no people at all, empty space, {SHEET_STYLE}, warm amber and deep brown palette. Place: {place}. "
            f"Top-left: daytime wide shot. Top-right: evening wide shot. Bottom-left: {pos1}. Bottom-right: {pos2}.")})
    return jobs


# ---------- 빌드 ----------
# 모바일 시청 기준: 1줄 최대 글자 수(일본어) — 넘으면 문장부호 근처에서 두 줄로 나눈다(최대 2줄)
MAX_LINE = 18


def _best_cut(text, marks, limit):
    mid = len(text) / 2
    cuts = [i + 1 for i, c in enumerate(text[:-1])
            if c in marks and max(i + 1, len(text) - i - 1) <= limit]
    return min(cuts, key=lambda i: abs(i - mid)) if cuts else None


def wrap_jp(text, limit=MAX_LINE):
    """두 줄로 나눈다 — 문장부호 → 조사 뒤 → 정가운데 순으로 자를 곳을 찾는다(단어 중간 자르기 최소화)."""
    if len(text) <= limit:
        return text
    cut = (_best_cut(text, "、。！？…」", limit + 4) or _best_cut(text, "はがをにでのもとへ", limit + 2)
           or round(len(text) / 2))
    return text[:cut] + "\\N" + text[cut:]


def fmt_ass(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def fmt_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


ASS_HEADER = """[Script Info]
Title: みすぼらしい老人は、財閥会長だった
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Naration,Noto Sans CJK JP,62,&H00E6E6E6,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,6,2,2,140,140,110,1
Style: Genzo,Noto Sans CJK JP,68,&H00FFFFFF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,6,2,2,140,140,110,1
Style: Kuroda,Noto Sans CJK JP,68,&H0000E5FF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,6,2,2,140,140,110,1
Style: Mamiya,Noto Sans CJK JP,68,&H0080C0FF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,6,2,2,140,140,110,1
Style: Yui,Noto Sans CJK JP,68,&H00C8C8FF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,6,2,2,140,140,110,1
Style: Sakaki,Noto Sans CJK JP,68,&H00FFC896,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,6,2,2,140,140,110,1
Style: Host,Noto Sans CJK JP,64,&H00FFFFFF,&H000000FF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,6,2,2,140,140,110,1
Style: Caption,Noto Serif CJK JP,96,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,5,0,5,140,140,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    scenes, ambience, speakers, events, cards = [], [], [], [], []
    tts_meta = []          # TTS 줄(자막 카드 제외) 순서대로 메타
    section_ends, sfx_cues, silences, bgm_marks = [], [], [], []
    t = 0.0
    prev_section = None
    errors = []

    for sg in SEGMENTS:
        if prev_section is not None and sg["section"] != prev_section:
            section_ends.append(len(scenes))           # 직전 장면 = 섹션 마지막
        prev_section = sg["section"]
        if sg.get("silence_before"):
            silences.append([round(t - sg["silence_before"], 3), round(t, 3)])

        # 줄 길이 계산 → auto 장면 길이 결정
        cursor, placed = 0.0, []
        for ln in sg["lines"]:
            start = cursor + ln["lead"]
            idx = len(tts_meta) + len(placed) + 1
            dur = MEASURED.get(idx) or speech_len(ln["jp"], ln["speed"])
            placed.append((start, dur, ln))
            cursor = start + dur
        need = cursor + SHOT_TAIL
        shots = []
        fixed = sum(s[0] for s in sg["shots"] if s[0] != "auto")
        for length, fn, vis, amb, reuse in sg["shots"]:
            if length == "auto":
                length = 5 if need - fixed <= 5 else 10
            shots.append((length, fn, vis, amb, reuse))
        total = sum(s[0] for s in shots)
        if need > total + 0.01:
            errors.append(f"{sg['name']}: 줄 길이 {need:.1f}s > 장면 {total}s")

        # 실측 길이가 있으면 대사 장면(장면 1개짜리 세그먼트)을 "앞침묵+대사+여운"으로 다듬는다
        trim = None
        if MEASURED and sg["lines"] and len(shots) == 1:
            trim = round(max(MIN_TRIM, min(need, shots[0][0])) + 0.04, 1)
            total = trim
        seg_start = t
        for length, fn, vis, amb, reuse in shots:
            item = {"duration": length}
            if reuse:
                item["reuse_of"] = reuse
                item["prompt"] = scenes[reuse - 1]["prompt"]
                item["refs"] = scenes[reuse - 1].get("refs", [])
            else:
                item["prompt"] = fn(length)
                item["refs"] = refs_for(item["prompt"])
            if trim:
                item["trim_to"] = trim
            scenes.append(item)
            ambience.append(amb)
            speakers.append(vis)
            t += trim or length

        for start, dur, ln in placed:
            a = seg_start + start
            events.append((a, a + dur, ln["style"], NAMES.get(ln["style"], ""), ln["jp"], ln["ko"]))
            tts_meta.append(ln)
            if sg.get("sfx_at_line_start") and ln is sg["lines"][0]:
                f, db, before = sg["sfx_at_line_start"]
                sfx_cues.append({"time": round(a - before, 3), "file": f, "gain_db": db})
            if sg.get("sfx_after_line") and ln is sg["lines"][-1]:
                f, db, after = sg["sfx_after_line"]
                sfx_cues.append({"time": round(a + dur + after, 3), "file": f, "gain_db": db})
            if sg.get("bgm_change_after_line") and ln is sg["lines"][-1]:
                bgm_marks.append(("reveal", round(a + dur + 0.2, 3)))
        for cd in sg["cards"]:
            if cd["at"] == "after":  # 마지막 줄이 끝난 뒤 0.3초부터, 세그먼트 끝까지
                cd = dict(cd, at=round(cursor + 0.3, 2))
                cd["dur"] = min(cd["dur"], total - cd["at"])
            a = seg_start + cd["at"]
            cards.append((a, a + cd["dur"], cd["jp"], cd["ko"]))
            if cd["at"] + cd["dur"] > total + 0.01:
                errors.append(f"{sg['name']}: 자막 카드가 세그먼트 밖으로 나감")
        if sg["name"].startswith("S9 완충"):
            bgm_marks.append(("warm", round(seg_start, 3)))

    total = t
    if errors:
        raise SystemExit("타이밍 오류:\n  " + "\n  ".join(errors))

    # 1) 장면 프롬프트
    with open(os.path.join(ROOT, "scripts", "scenes", f"{WORK}.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": 5, "ratio": "16:9", "style": STYLE, "scenes": scenes},
                  f, ensure_ascii=False, indent=2)

    # 2) 일본어 자막(.ass) — 대사·내레이션 + 자막 카드(화면 중앙)
    rows = [(s, e, st, nm, jp) for s, e, st, nm, jp, _ in events]
    rows += [(s, e, C, "", jp) for s, e, jp, _ in cards]
    rows.sort(key=lambda r: r[0])
    with open(os.path.join(ROOT, "subs", f"{WORK}.ass"), "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, st, nm, text in rows:
            # 이벤트를 나누면 TTS 줄 번호가 밀리므로 나누지 않는다 — 긴 줄은 대본에서 두 줄로 쪼갤 것
            f.write(f"Dialogue: 0,{fmt_ass(s)},{fmt_ass(e)},{st},{nm},0,0,0,,{wrap_jp(text)}\n")

    # 3) 한국어 검수 자막(.srt)
    ko = [(s, e, (f"（{nm}）" if nm else "（내레이션）" if st == N else "") + k) for s, e, st, nm, _, k in events]
    ko += [(s, e, f"［자막 카드］{k}") for s, e, _, k in cards]
    ko.sort(key=lambda r: r[0])
    with open(os.path.join(ROOT, "subs", f"{WORK}.ko-review.srt"), "w", encoding="utf-8") as f:
        for n, (s, e, text) in enumerate(ko, start=1):
            f.write(f"{n}\n{fmt_srt(s)} --> {fmt_srt(e)}\n{text}\n\n")

    # 4) 오디오 설정 — 줄 번호는 자막 카드(silent_styles) 제외 후 기준
    emotions, speeds, tags = {}, {}, {}
    for i, ln in enumerate(tts_meta, start=1):
        if ln["emotion"] != "neutral":
            emotions[str(i)] = ln["emotion"]
        speeds[str(i)] = ln["speed"]
        if ln["tag"]:
            tags[str(i)] = ln["tag"]
    reveal = next(v for k, v in bgm_marks if k == "reveal")
    warm = next(v for k, v in bgm_marks if k == "warm")
    tension_end = silences[0][0]
    audio = {
        "tts_model": "fal-ai/minimax/speech-02-hd",
        "language_boost": "Japanese",
        "el_model": "fal-ai/elevenlabs/tts/eleven-v3",
        "el_language_code": "ja",
        "speed": 1.0,
        "default_voice": VOICES[N],
        "style_voices": {st: v for st, v in VOICES.items()},
        "style_names": {st: nm for st, nm in NAMES.items()},
        "narration_styles": [N],
        "silent_styles": [C],
        "emotion_overrides": emotions,
        "speed_overrides": speeds,
        "tag_overrides": tags,
        "scene_speakers": speakers,
        "section_ends": section_ends,
        "lipsync_models": ["fal-ai/sync-lipsync", "fal-ai/latentsync"],
        "ambience_model": "fal-ai/mmaudio-v2",
        "ambience_volume": 0.35,
        "ambience_prompts": ambience,
        "bgm_model": "fal-ai/lyria2",
        "bgm_segments": [
            {"start": 0, "end": tension_end, "volume": 0.22, "fade_in": 1.5, "fade_out": 1.5,
             "prompt": "tense Japanese drama underscore, low drone and sparse mysterious piano, slowly rising "
                       "strings, suspenseful, instrumental only, no vocals"},
            {"start": reveal, "end": warm - 2.0, "volume": 0.26, "fade_in": 0.3, "fade_out": 2.0,
             "prompt": "majestic cinematic orchestral swell, triumphant and dignified, Japanese drama climax, "
                       "instrumental only, no vocals"},
            {"start": warm, "end": total, "volume": 0.22, "fade_in": 2.0, "fade_out": 3.0,
             "prompt": "warm gentle solo piano, emotional and tender, Japanese human drama ending, "
                       "instrumental only, no vocals"},
        ],
        "silence_hits": silences,
        "sfx_cues": sfx_cues,
        "ducking": {"threshold": 0.03, "ratio": 8, "attack": 20, "release": 400},
        "master": {"lufs": -14, "tp": -1},
    }
    with open(os.path.join(ROOT, "scripts", "audio", f"{WORK}.json"), "w", encoding="utf-8") as f:
        json.dump(audio, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.join(ROOT, "scripts", "images"), exist_ok=True)
    with open(os.path.join(ROOT, "scripts", "images", f"{WORK}.json"), "w", encoding="utf-8") as f:
        json.dump({"work": WORK, "jobs": image_jobs()}, f, ensure_ascii=False, indent=2)

    n_new = sum(1 for s in scenes if "reuse_of" not in s)
    secs = sum(s["duration"] for s in scenes if "reuse_of" not in s)
    print(f"장면 {len(scenes)}개 (신규 생성 {n_new}개 = {secs}초, 재사용 {len(scenes) - n_new}개), "
          f"영상 {total:.0f}초 ({total / 60:.1f}분)")
    print(f"TTS 줄 {len(tts_meta)}개, 자막 카드 {len(cards)}개, 정적 {silences}, 효과음 {len(sfx_cues)}개")
    print(f"BGM 구간: 긴장 0~{tension_end:.1f}s / 사이다 {reveal:.1f}~{warm - 2:.1f}s / 감동 {warm:.1f}~{total:.1f}s")


if __name__ == "__main__":
    main()
