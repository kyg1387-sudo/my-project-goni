#!/usr/bin/env python3
"""김씨의 쪽지 (EP2) — 제작 자산 생성기 (기준 초상 image-to-video 판).

대본: docs/대본-김씨의쪽지.md (v2 확정) + docs/스토리보드-김씨의쪽지.md
     + docs/톤연출표-김씨의쪽지.md (규칙 8-2)
build_guard_kim_assets.py 의 beat 정렬 + refs 방식에 다음을 추가했다:
  * 대사 줄에 (감정, 앞침묵, 속도)를 내장 — emotion/speed_overrides와 앞침묵이
    줄 번호 어긋남 없이 자동 산출된다 (빈 줄 0개, 규칙 8-2).
  * 내레이션(N) 줄 지원 — narration_styles 등록(립싱크 제외), el2 목소리는
    assets/audio-overrides/kim-note/ 의 사전 생성 mp3가 덮어쓴다.
  * 대사 MCU 장면 번호를 자동 수집해 omnihuman_scenes 로 기록.
  * 쪽지·수첩 필체 인서트는 NOTE(무지 쪽지 클로즈업) 자리 장면으로 두고,
    생성 전에 assets/video-overrides/kim-note/sceneNN.mp4 (PIL 필체 합성,
    무과금 로컬 렌더)로 교체한다 — 생성 모델에 글자를 맡기지 않는다.

생성 파일:
    scripts/scenes/kim-note.json  (16:9, 장면별 5/10초, refs=기준 초상)
    subs/kim-note.ass
    scripts/audio/kim-note.json

사용법: python3 scripts/build_kim_note_assets.py
"""

import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = "assets/portraits"

# 확정 기준 초상 (사용자 선택: 준호 얼굴 1번 → 파생 세트)
REF_KIM = f"{P}/guard-kim-secret-cap2/kim-gold-1.png"          # EP1 재사용 (제복·명찰)
REF_KIM_BACK = f"{P}/guard-kim-secret-views3/kim-back-new-1.png"  # EP1 뒷모습 재사용
REF_JUNHO = f"{P}/ep2-cast/junho-hood-1.png"                   # 복도·밝은 곳
REF_JUNHO_ROOM = f"{P}/ep2-cast/junho-room-1.png"              # 어두운 방
REF_JUNHO_SUIT = f"{P}/ep2-cast/junho-suit-2.png"              # 면접 정장
REF_JUNHO_BACK = f"{P}/ep2-cast/junho-back-1.png"              # 후드 뒷모습 (신규 생성)
REF_JUNHO_SUIT_BACK = f"{P}/ep2-cast/junho-suit-back-1.png"    # 정장 뒷모습 (신규 생성)
REF_JIWOO = f"{P}/ep2-cast/jiwoo-spring-2.png"
REF_PARK = f"{P}/ep2-cast/park-spring-2.png"
REF_WIFE = f"{P}/ep2-cast/wife-photo-1.png"             # 아내 사진 기준(scene08에서 추출)

# 인물 고정 문구 (모든 장면 동일 반복 — 규칙 5)
KIM = ("68세 한국 남성 아파트 경비원 김씨(흰머리 섞인 짧은 머리, 온화하지만 무뚝뚝한 표정, "
       "짙은 회색 무지 경비원 제복, 금색 장식 문양이 있는 남색 경비원 정모, 가슴 왼쪽에 금색 명찰)")
JUNHO = ("27살 한국 남성 준호(부스스한 검은 곱슬 앞머리, 창백한 피부와 눈 밑 다크서클, 마른 체형, "
         "로고 없는 베이지색 무지 후드티(후드 내림), 짙은 회색 무지 바지)")
JUNHO_SUIT = ("27살 한국 남성 준호(검은 곱슬머리를 단정히 빗어 넘김, 혈색이 돌아온 얼굴에 옅은 미소, "
              "마른 체형, 남색 무지 정장과 흰 무지 셔츠, 넥타이 없음)")
JIWOO = ("10살 한국 초등학생 여자아이 지우(어깨까지 오는 검은 생머리, 노란 머리핀, "
         "연분홍색 무지 가디건, 하늘색 무지 책가방)")
PARK = "55세 한국 여성 입주민 대표 박여사(짧은 갈색 파마머리, 밝은 무지 봄 카디건, 진주 목걸이)"

# 장소 고정 문구 (클로즈업 포함 전 장면에 장소 명시 — 규칙 5)
APT = "아무 글자도 없는 깨끗한 한국 아파트 단지, 초봄 아침, 나뭇가지에 벚꽃 봉오리, 눈 없음"
CORR = ("낡은 한국 복도식 아파트의 외부 복도, 무지 베이지색 벽, 글자·번호·문패·표지가 전혀 없는 "
        "매끈한 무지 문, 은색 금속 문고리")
CORR_DAWN = f"새벽 어스름의 {CORR}, 푸르스름한 여명"
CORR_NIGHT = f"밤의 {CORR}, 어둑한 푸른빛 형광등 불빛"
ROOM = ("커튼이 쳐진 어두운 원룸 방 안(무지 벽, 포스터나 글자 없음), 커튼 틈으로 스며드는 "
        "가는 빛줄기, 구석에 라벨 없는 무지 흰 일회용 용기들이 쌓여 있음")
KITCH = "어두운 원룸 구석의 작은 부엌, 낡은 휴대용 가스레인지, 라벨 없는 무지 흰 일회용 용기들, 글자 없음"
GUARD_IN = "아무 글자 없는 아파트 경비실 안, 작은 책상과 창문, 따뜻한 스탠드 조명"
RECYC = "밤의 아파트 단지 분리수거장, 종이 상자와 무지 재활용 수거함(글자·라벨 없음), 가로등 불빛"
NOTE_BG = "나무 책상 위에 놓인 아무 글자도 없는 무지 쪽지 한 장의 클로즈업, 따뜻한 조명, 사람이 한 명도 없는 무인 장면"

TALK = ("카메라를 향해 대사에 맞춰 입을 자연스럽게 움직이며 한국어로 말하는 "
        "정면 상반신 샷, 화면에는 말하는 사람 한 명만 등장")
MUTE = "아무도 입을 움직이거나 말하지 않는 장면"

STYLE = ("시네마틱 한국 드라마, 실사 영화 화질, 동일한 인물과 의상과 장소를 모든 장면에서 유지, "
         "자연스러운 피부 질감, 16:9 와이드 가로 구도, 말하는 입 모양은 한국어(영어 없음), "
         "화면 속 옷·간판·소품·배경에는 글자나 로고가 보이지 않게(김씨의 금색 명찰만 예외), 초봄, 눈 없음")

N, C, A = "Naration", "Caption", "Action"
K, JH = "Kim", "Junho"

TITLE_TAG = r"{\an5\pos(960,470)\fnNoto Serif CJK KR\fs84\b1\fsp9\c&HD8F0FA&\3c&H120A05&\bord2\shad2\4c&H96000000&\blur0.4\fad(600,600)}"
END_TAG = r"{\an5\pos(960,470)\fnNoto Serif CJK KR\fs64\b1\fsp7\c&HD8F0FA&\3c&H120A05&\bord2\shad2\4c&H96000000&\blur0.4\fad(1200,1500)}"

# 대사 줄: (스타일, 이름, 대사, 감정, 앞침묵초, 속도) — 톤 연출표 v1 그대로
# 내레이션 줄: (N, "", 문안, None, 앞침묵초, 0.9)
# Action:     (A, "길이", 프롬프트, refs)
SECTIONS = [
    dict(
        name="콜드 오픈",
        ambience="pre-dawn silence, plastic bag rustle, distant single bird",
        narration_shots=[
            (f"{CORR_DAWN}, 아직 해가 뜨지 않은 어둑한 푸른 새벽, 인물 없이 복도 전체를 비추는 정적인 "
             f"와이드 샷, 문고리에 걸린 흰 무지 봉지 하나, 문과 벽에 아무 종이도 붙어 있지 않음, "
             f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
        ],
        speaker_shots={},
        lines=[
            (A, "5", f"{CORR_DAWN}, {KIM}의 주름진 손이 흰 무지 비닐봉지를 문고리에 조심스럽게 거는 "
                     f"익스트림 클로즈업(손과 문고리만, 얼굴 안 보임), {MUTE}", [REF_KIM]),
            (A, "5", f"어두운 원룸의 현관 안쪽에서 본 샷, 문이 손가락 폭만큼 열려 그 좁은 틈으로 "
                     f"새벽 복도의 푸른 빛이 세로선으로 들어오고, {JUNHO}가 문틈에 얼굴을 가까이 대고 "
                     f"한쪽 눈으로 조심스럽게 밖을 내다보는 클로즈업, 어두운 실내에 눈가만 빛에 드러남, "
                     f"인물은 문 뒤에 실제로 서 있음, 이중 노출이나 반투명 유령 효과 없음, {MUTE}",
             [REF_JUNHO_ROOM]),
            (C, "", "매주 수요일 새벽, 그 문고리에는", None, 0.4, None),
            (C, "", TITLE_TAG + "김씨의 쪽지", None, 0.4, None),
            (C, "", "석 달 전", None, 0.4, None),
        ],
    ),
    dict(
        name="1장 — 닫힌 문",
        ambience="spring morning birds, distant children, light breeze",
        narration_shots=[
            (f"{CORR}, 아침 햇살, 닫힌 무지 문 앞에 쌓인 우편물과 무지 흰 봉지들을 천천히 비추다 "
             f"닫힌 문 전체로 빠지는 샷, 사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
        ],
        speaker_shots={
            K: [(f"{GUARD_IN}, 책상 위 갈색 나무 액자를 바라보며 꽃무늬 수첩을 쓰다듬는 {KIM}, "
                 f"액자 속 흑백 사진은 참조된 흑백 사진과 완전히 동일한 사진(같은 단발머리 중년 여성, "
                 f"짙은 카라 블라우스), 눈시울이 옅게 붉어진 그리움에 잠긴 표정으로 {TALK}", [REF_KIM, REF_WIFE])],
        },
        lines=[
            (A, "10", f"{APT} 경비실 앞, {JIWOO}가 등굣길에 환하게 웃으며 손을 흔들고 {KIM}가 "
                      f"고개만 살짝 까딱해 답하는 장면, 화면에는 정확히 두 명만 등장, {MUTE}",
             [REF_JIWOO, REF_KIM]),
            (N, "", "504호의 문은, 오래도록 낮에는 열리지 않았습니다.", None, 0.8, 0.9),
            (A, "10", f"{RECYC}, {JUNHO}의 뒷모습이 무지 봉지를 내려놓고 주위를 살피다 급히 "
                      f"돌아가는 장면, 혼자 단독 인물 샷, {MUTE}", [REF_JUNHO_BACK]),
            (A, "5", f"밤의 {APT} 순찰길, 손전등을 든 {KIM}가 멀리 분리수거장 쪽을 걱정스럽게 "
                     f"바라보는 장면, 혼자 단독 인물 샷, {MUTE}", [REF_KIM]),
            (A, "5", f"{GUARD_IN}, 책상 위 중년 여성의 흑백 사진 액자와 그 옆의 흰 국화 한 송이 "
                     f"클로즈업, 사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
            (A, "5", f"{GUARD_IN}, 책상 위 낡은 꽃무늬 수첩을 펴는 주름진 두 손만 보이는 탑다운 클로즈업"
                     f"(수첩 속은 백지, 글자 없음), 화면에 얼굴 없이 한 사람의 손만 등장, 다른 인물 없음, "
                     f"{MUTE}", [REF_KIM]),
            (A, "5", f"{GUARD_IN} 책상 위에 펼쳐진 꽃무늬 수첩의 백지 페이지 클로즈업, "
                     f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),  # ★쪽지① 수첩 아내 필체 (PIL 교체)
            (K, "", "…여보. 그 청년, 아직 그 방에 있소.", "sad", 2.0, 0.85),
        ],
    ),
    dict(
        name="2장 — 다시 걸린 봉지",
        ambience="pre-dawn room tone, container clink, plastic bag rustle",
        narration_shots=[
            (f"{CORR}, 오후의 빛이 기운 복도, 은색 문고리에 흰 무지 비닐봉지 하나가 그대로 걸려 있는 "
             f"클로즈업(봉지가 화면 중앙에 뚜렷이 보임), 문에 아무 종이·문패 없음, "
             f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
        ],
        speaker_shots={
            JH: [(f"{ROOM}, 낡아 누렇게 바랜 무지 쪽지와 새 무지 흰 쪽지 두 장을 나란히 든 {JUNHO}가 "
                  f"놀란 눈으로 낮게 혼잣말하는 {TALK}", [REF_JUNHO_ROOM]),
                 (f"{KITCH} 앞 작은 상, 국그릇을 앞에 두고 숟가락을 든 채 눈가가 붉어진 {JUNHO}가 "
                  f"목이 멘 표정으로 {TALK}", [REF_JUNHO_ROOM])],
        },
        lines=[
            (A, "10", f"새벽의 {GUARD_IN}, {KIM}가 반찬통들을 흰 무지 봉지에 담다가 주먹을 입에 대고 "
                      f"낮게 기침을 한 번 하는 장면, 혼자 단독 인물 샷, {MUTE}", [REF_KIM]),
            (A, "5", f"{CORR_DAWN}, {KIM}의 손이 반찬통이 담긴 흰 무지 봉지를 문고리에 거는 클로즈업, "
                     f"{MUTE}", [REF_KIM]),
            (A, "5", NOTE_BG + f", {MUTE}", []),  # ★쪽지② 「먹게.」 (PIL 교체)
            (JH, "", "…글씨가, 달라.", "surprised", 1.5, 0.85),
            (N, "", "칠 년 만에 다시 걸린 봉지를, 그는 사흘 동안 열지 못했습니다.", None, 1.0, 0.9),
            (A, "5", f"{CORR_DAWN}, {KIM}의 손이 낡은 봉지를 내리고 새 흰 무지 봉지로 바꿔 거는 "
                     f"클로즈업, {MUTE}", [REF_KIM]),
            (A, "5", NOTE_BG + f", {MUTE}", []),  # ★쪽지③ 「국은 데워 먹게.」 (PIL 교체)
            (A, "5", f"{KITCH}, 김이 모락모락 오르는 작은 냄비의 클로즈업, 사람이 한 명도 없는 "
                     f"무인 장면, 인물 없음, {MUTE}", []),
            (JH, "", "…따뜻하네.", "sad", 2.0, 0.80),
        ],
    ),
    dict(
        name="3장 — 쪽지가 쌓이다",
        ambience="early morning birds, soft plastic rustle, gentle spring breeze",
        narration_shots=[
            (f"{CORR_DAWN}, 주름진 손이 흰 무지 비닐봉지를 은색 문고리에 걸어 놓는 순간의 클로즈업"
             f"(봉지를 쥔 손과 문고리가 화면에 뚜렷이 보임), 매주 반복되는 수요일의 몽타주 느낌, "
             f"{MUTE}", [REF_KIM]),
        ],
        speaker_shots={
            K: [(f"{CORR_DAWN}, 문고리에 걸린 씻은 반찬통들을 발견한 {KIM}가 옅게 웃다 한 손으로 "
                 f"허리를 짚는 모습, 온화한 표정으로 {TALK}", [REF_KIM])],
        },
        lines=[
            (N, "", "봉지는 매주 걸렸고, 쪽지는 한 장씩 늘어 갔습니다.", None, 0.8, 0.9),
            (A, "5", f"{CORR}, 아침 햇살, 비워진 흰 무지 봉지가 가볍게 흔들리는 문고리 클로즈업, "
                     f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
            (A, "5", NOTE_BG + f", 쪽지 세 장이 나란히 놓임, {MUTE}", []),  # ★쪽지④ 모음 3장 (PIL 교체)
            (A, "5", f"문이 10센티미터만 살짝 열린 좁은 세로 틈 사이로 보이는 시점 샷, 틈의 양쪽은 "
                     f"어두운 문과 문틀이 크게 가리고, {CORR_DAWN} 저편으로 멀어지는 {KIM}의 제복 입은 "
                     f"뒷모습, 바닥은 마른 회색 콘크리트 복도(눈 없음), {MUTE}", [REF_KIM_BACK]),
            (A, "10", f"{ROOM}, 씻어서 엎어 말리는 반찬통들과 벽에 나란히 붙은 무지 쪽지들, "
                      f"{JUNHO}가 커튼을 조금 열어 빛줄기가 넓어지는 장면, {MUTE}", [REF_JUNHO_ROOM]),
            (A, "5", f"{CORR_NIGHT}, {JUNHO}의 손이 씻은 반찬통이 담긴 흰 무지 봉지를 문고리에 "
                     f"조심스럽게 되거는 클로즈업, {MUTE}", [REF_JUNHO]),
            (K, "", "…잘 먹었으면 됐네.", "happy", 1.5, 0.90),
        ],
    ),
    dict(
        name="4장 — 걸리지 않은 봉지",
        ambience="grey dawn wind, empty corridor room tone, faint heartbeat-like low pulse",
        narration_shots=[
            (f"{CORR_DAWN}, 아무것도 걸려 있지 않은 텅 빈 은색 문고리를 향해 천천히 다가가는 클로즈업, "
             f"문은 완전히 매끈한 무지이며 금색 문패·명패·표지·종이가 하나도 붙어 있지 않음, "
             f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
        ],
        speaker_shots={
            JH: [(f"{GUARD_IN} 문가에 어색하게 선 {JUNHO}가 조심스럽고 갈라지는 목소리로 걱정스럽게 "
                  f"{TALK}", [REF_JUNHO]),
                 (f"{GUARD_IN}, 죽이 담긴 흰 무지 봉지를 두 손으로 안은 {JUNHO}가 수줍게 시선을 "
                  f"내렸다 들며 담담하게 {TALK}", [REF_JUNHO])],
            K: [(f"{GUARD_IN}, 정모를 벗은 맨머리에 물수건을 한 손에 쥔 채 간이침대에서 몸을 일으킨 "
                 f"{KIM}가 눈을 크게 뜨고 믿기지 않는 놀란 표정으로 {TALK}", [REF_KIM])],
        },
        lines=[
            (N, "", "석 달 만에 처음으로, 수요일의 문고리는 비어 있었습니다.", None, 1.0, 0.9),
            (A, "5", f"{CORR_DAWN}, 손가락 하나 폭의 문틈 사이로 보이는 {JUNHO}의 불안하게 흔들리는 "
                     f"눈 익스트림 클로즈업, {MUTE}", [REF_JUNHO]),
            (A, "5", f"어두운 현관 안쪽({ROOM}의 문 앞), 문고리를 잡은 {JUNHO}의 떨리는 손 클로즈업, "
                     f"{MUTE}", [REF_JUNHO]),
            (A, "5", f"{CORR} 쪽으로 문이 활짝 열리며 눈부신 낮빛이 쏟아지고, 역광 속에서 {JUNHO}가 "
                     f"한 발을 내딛는 로우 앵글 미디엄 샷, {MUTE}", [REF_JUNHO]),
            (A, "5", f"{GUARD_IN}, 정모를 벗은 맨머리로 간이침대에 반듯이 누워 앓는 {KIM}, 접은 흰 "
                     f"물수건은 이마 위에만 얹혀 있고 두 눈은 감았지만 가려지지 않음, 제복 상의를 입은 채, "
                     f"책상 위는 깨끗함, 혼자 단독 인물 샷, {MUTE}", [REF_KIM]),
            (JH, "", "…아저씨. 괜찮으세요?", "fearful", 1.0, 0.85),
            (K, "", "…자네가, 여길 어떻게…", "surprised", 0.8, 0.85),
            (A, "5", f"{GUARD_IN}, {JUNHO}가 죽이 담긴 흰 무지 봉지를 두 손으로 조심스럽게 내미는 "
                     f"장면, {MUTE}", [REF_JUNHO]),
            (A, "5", NOTE_BG + f", 서툰 글씨 느낌의 무지 쪽지, {MUTE}", []),  # ★쪽지⑤ 「드세요.」 (PIL 교체)
            (JH, "", "…이번엔, 제 차례라서요.", "sad", 1.2, 0.80),
        ],
    ),
    dict(
        name="5장 — 쪽지의 비밀",
        ambience="quiet guard booth evening room tone, paper rustling softly",
        narration_shots=[
            (f"{GUARD_IN}, 낡은 종이 상자 안에 가득 쌓인 무지 쪽지들의 클로즈업, "
             f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),
        ],
        speaker_shots={
            JH: [(f"{GUARD_IN}, 낡은 종이 상자를 품에 안은 {JUNHO}가 시선을 내린 채 낮고 느리게 "
                  f"{TALK}", [REF_JUNHO]),
                 (f"{GUARD_IN}, 누렇게 바랜 무지 쪽지 한 장을 조심스럽게 꺼내 든 {JUNHO}가 "
                  f"그리움에 잠긴 표정으로 {TALK}", [REF_JUNHO]),
                 (f"낮의 {GUARD_IN} 실내(창밖은 밝은 오후), 눈물이 고인 채 웃으려 애쓰는 {JUNHO}가 "
                  f"떨리는 목소리로 {TALK}", [REF_JUNHO])],
            K: [(f"낮의 {GUARD_IN} 실내, 책상 앞 의자에 앉아 바랜 쪽지를 오래 바라보는 {KIM}, "
                 f"눈시울이 붉어진 채 낮은 목소리로 {TALK}", [REF_KIM]),
                (f"낮의 {GUARD_IN} 실내, 책상 앞 의자에 앉은 {KIM}가 시선을 들어 담담하지만 무겁게 "
                 f"{TALK}", [REF_KIM])],
        },
        lines=[
            (A, "5", f"낮의 {GUARD_IN}(창밖은 밝은 오후), {JUNHO}가 탁자 위에서 낡은 종이 상자를 여는 "
                     f"하이 앵글 클로즈업, 상자 안에 무지 쪽지들이 가득, {MUTE}", [REF_JUNHO]),
            (JH, "", "…하나도 못 버렸어요.", "sad", 1.5, 0.80),
            (JH, "", "그런데 이건… 칠 년 전 거예요. 그때도 누가, 걸어줬었거든요.", "sad", 1.2, 0.85),
            (A, "5", NOTE_BG + f", 누렇게 바랜 무지 쪽지, {MUTE}", []),  # ★쪽지⑥ 아내 필체 (PIL 교체)
            (A, "5", f"{GUARD_IN}, 바랜 무지 쪽지를 두 손으로 쥔 {KIM}의 주름진 손 클로즈업, "
                     f"{MUTE}", [REF_KIM]),  # 완충 컷 (톤표 — 10번 대사 앞)
            (K, "", "…집사람 겁니다.", "sad", 2.5, 0.75),
            (K, "", "칠 년 전에… 먼저 걸던 사람이오. 나는, 이어서 걸었을 뿐이고.", "sad", 1.0, 0.80),
            (JH, "", "…그럼 저는, 두 분께… 두 번 받은 거네요.", "sad", 1.8, 0.78),
            (A, "5", f"나무 책상 위에 나란히 놓인 두 장의 무지 쪽지(하나는 누렇게 바래고 하나는 흰색) "
                     f"탑다운 클로즈업, 따뜻한 스탠드 조명, 사람이 한 명도 없는 무인 장면, 인물 없음, "
                     f"{MUTE}", []),  # ★쪽지⑦ 나란히 (PIL 교체, 무음 여운)
        ],
    ),
    dict(
        name="6장 — 열린 문",
        ambience="bright spring morning birds, gentle breeze, light footsteps",
        narration_shots=[
            (f"경비실 창문 너머로 보이는 {APT}의 길, {JUNHO_SUIT}가 멀어져 걸어가는 뒷모습 롱샷, "
             f"봄 햇살, {MUTE}", [REF_JUNHO_SUIT_BACK]),
        ],
        speaker_shots={
            JH: [(f"{APT} 경비실 앞, 기준 사진과 완전히 동일한 얼굴의 {JUNHO_SUIT}가 처음으로 밝고 "
                  f"또렷한 표정과 옅은 미소로 {TALK}, 옷에 명찰·배지·핀 없음, 바닥은 눈이 전혀 없는 마른 보도블록",
                  [REF_JUNHO_SUIT])],
            K: [(f"{APT} 경비실 앞, {KIM}가 옅은 미소로 배웅하듯 손을 살짝 들며 {TALK}", [REF_KIM])],
        },
        lines=[
            (A, "5", f"초봄 아침의 {APT}, {JUNHO_SUIT}가 아파트 현관을 나서는 와이드 샷, "
                     f"혼자 단독 인물 샷, {MUTE}", [REF_JUNHO_SUIT]),
            (A, "10", f"{APT} 경비실 앞, 서로 마주 보고 선 두 사람의 옆모습 투샷: {JUNHO_SUIT}가 "
                      f"{KIM}를 향해 허리 숙여 꾸벅 인사하고, {KIM}는 몸과 얼굴을 준호 쪽으로 돌려 "
                      f"따뜻한 눈으로 그를 바라보며 어깨를 가볍게 툭 두드림, 두 사람의 시선이 서로를 "
                      f"향함(카메라를 보지 않음), 바닥은 눈이 전혀 없는 마른 보도블록, "
                      f"화면에는 정확히 두 명만 등장, {MUTE}",
             [REF_JUNHO_SUIT, REF_KIM]),
            (JH, "", "다녀오겠습니다.", "happy", 0.8, 0.95),
            (K, "", "…그래. 잘 다녀오게.", "happy", 1.0, 0.85),
            (A, "5", f"{APT} 길, {JIWOO}가 환하게 손을 흔들고 {PARK}이 반찬통 몇 개를 안고 걸어오는 "
                     f"장면, 지우는 환하게 웃고 박여사는 온화한 미소로 서로를 바라봄, 바닥은 눈이 전혀 없는 마른 봄 보도, "
                     f"화면에는 정확히 두 명만 등장, {MUTE}", [REF_JIWOO, REF_PARK]),
            (A, "5", f"{GUARD_IN}, 책상 위 꽃무늬 수첩에 펜으로 쓰는 주름진 한 손만 보이는 탑다운 "
                     f"클로즈업(페이지는 백지, 글자 없음), 화면에 얼굴이나 다른 인물 없이 손과 팔만 등장, "
                     f"{MUTE}", [REF_KIM]),
            (A, "5", f"{GUARD_IN} 책상 위에 펼쳐진 꽃무늬 수첩의 백지 페이지 클로즈업, "
                     f"사람이 한 명도 없는 무인 장면, 인물 없음, {MUTE}", []),  # ★쪽지⑧ 수첩 김씨 필체 (PIL 교체)
            (N, "", "닫힌 문을 연 것은, 수요일마다 걸린 두 사람의 글씨였습니다.", None, 1.0, 0.9),
            (C, "", END_TAG + r"당신의 문고리에도,\N누군가의 온기가 걸려 있을지 모릅니다", None, 0.4, None),
        ],
    ),
]

CHAR_RATE = 5.5
LINE_PAD = 0.4
MIN_DUR = 1.2
CAPTION_MIN = 2.4
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
    for entry in lines:
        style = entry[0]
        if style == A:
            _, size, prompt, refs = entry
            beats.append({"key": "ACT", "size": int(size), "prompt": prompt, "refs": refs})
            continue
        _, name, text, emotion, pre, speed = entry
        key = "N" if style in (N, C) else style
        rec = (style, name, text, emotion, pre, speed)
        if beats and beats[-1].get("key") == key and "lines" in beats[-1]:
            beats[-1]["lines"].append(rec)
        else:
            beats.append({"key": key, "lines": [rec]})
    return beats


def fmt_time(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ASS_HEADER = """[Script Info]
Title: 김씨의 쪽지 자막
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
Style: Junho,Noto Sans CJK KR,60,&H00A8E8C8,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,200,200,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    events, scene_items, ambience_prompts = [], [], []
    emotions, speeds = {}, {}
    omni_scenes, override_slots = [], []
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
                if (beat["prompt"].startswith(NOTE_BG) or "백지 페이지" in beat["prompt"]
                        or "나란히 놓인 두 장의 무지 쪽지" in beat["prompt"]):
                    override_slots.append(len(scene_items))
                ambience_prompts.append(sec["ambience"])
                t_video += beat["size"]
                continue

            t = t_video
            for style, name, text, emotion, pre, speed in beat["lines"]:
                t += pre
                if style != C:
                    tts_no += 1
                    emotions[str(tts_no)] = emotion or "neutral"
                    if speed:
                        speeds[str(tts_no)] = speed
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
                if key != "N":
                    omni_scenes.append(len(scene_items))  # 대사 MCU → omnihuman 대상
                ambience_prompts.append(sec["ambience"])
                t_video += size

        print(f"{sec['name']}: 발화 {n_lines}줄 → {t_video - sec_start:.0f}초")

    total = t_video
    n5 = sum(1 for s in scene_items if s["duration"] == 5)
    n10 = len(scene_items) - n5
    print(f"\n합계: 자막 {len(events)}줄(TTS {tts_no}줄), 장면 {len(scene_items)}개 "
          f"(5초 {n5} + 10초 {n10}), 영상 {total:.0f}초 ({total / 60:.1f}분)")
    print(f"omnihuman 대사 장면: {omni_scenes}")
    print(f"PIL 인서트 자리(video-overrides 교체 예정): {override_slots}")

    with open(os.path.join(ROOT, "subs", "kim-note.ass"), "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for s, e, style, name, text in events:
            f.write(f"Dialogue: 0,{fmt_time(s)},{fmt_time(e)},{style},{name},0,0,0,,{text}\n")

    with open(os.path.join(ROOT, "scripts", "scenes", "kim-note.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": 10, "ratio": "16:9", "style": STYLE, "scenes": scene_items},
                  f, ensure_ascii=False, indent=2)

    audio = {
        "tts_model": "fal-ai/minimax/speech-02-hd",
        "language_boost": "Korean",
        "speed": 1.0,
        "default_voice": "Imposing_Manner",
        "style_voices": {"Kim": "Imposing_Manner", "Junho": "Casual_Guy",
                         "Naration": "Calm_Woman"},
        "style_emotions": {"Kim": "neutral", "Junho": "neutral", "Naration": "neutral"},
        "emotion_overrides": emotions,
        "speed_overrides": speeds,
        "scene_durations": [s["duration"] for s in scene_items],
        "narration_styles": ["Naration"],
        "silent_styles": ["Caption"],
        "omnihuman_scenes": omni_scenes,
        "lipsync_models": ["fal-ai/latentsync", "fal-ai/sync-lipsync"],
        "ambience_model": "fal-ai/mmaudio-v2",
        "ambience_volume": 0.35,
        "ambience_prompts": ambience_prompts,
        "bgm_model": "fal-ai/lyria2",
        "bgm_prompt": "tender emotional Korean drama score, gentle piano and warm strings, "
                      "quiet early-spring atmosphere of loneliness slowly opening into warmth, "
                      "building to a hopeful heartfelt resolution, instrumental only, no vocals",
        "bgm_volume": 0.22,
    }
    with open(os.path.join(ROOT, "scripts", "audio", "kim-note.json"), "w", encoding="utf-8") as f:
        json.dump(audio, f, ensure_ascii=False, indent=2)

    print("생성 완료: subs/kim-note.ass, scripts/scenes/kim-note.json, scripts/audio/kim-note.json")


if __name__ == "__main__":
    main()
