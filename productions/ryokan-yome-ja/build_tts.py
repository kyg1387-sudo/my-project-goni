#!/usr/bin/env python3
"""#03 『老舗旅館の嫁』 — 줄별 톤 연출표(05) + 본녹음 TTS 스펙(scripts/auditions/ryokan-tts.json) 생성기.

입력: 00_script_ja.md(대본 v2), 확정 캐스트(scripts/audio/ryokan-cast-voices.json, 고니감독님 청취 2026-10-18)
출력: 05_톤연출표.md, scripts/auditions/ryokan-tts.json
규칙: CLAUDE.md 8-2(빈 줄 0개) · 제10장 8(가나 치환본, ≤30자/문장, ≤2문장/줄 검사) · 제11장 23(감정 강도 A/B)
엔진: ElevenLabs eleven_v3 직접 호출(연기 태그 2~4단어, 대사 앞에만) · 진행자 = Typecast Yui Sato(#02 공통)
사용법: python3 productions/ryokan-yome-ja/build_tts.py
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CAST_JSON = json.load(open(os.path.join(REPO, "scripts", "audio", "ryokan-cast-voices.json"), encoding="utf-8"))

# 대본 화자 표기 → (표시명, 배역 키)
CAST = {
    "NA": ("와카나(내레이션)", "narr"), "若菜": ("와카나", "wakana"), "富子": ("도미코", "tomiko"),
    "麻衣": ("마이", "mai"), "隆之": ("다카유키", "takayuki"), "桜井": ("사쿠라이", "sakurai"),
    "陳": ("천", "chen"), "常連客": ("단골 노인", "regular"), "진행자": ("진행자(#02 공통)", "host"),
}
HOST_TC = "tc_629fe972013e90b4db213fd8"  # Yui Sato — #01·#02 진행자

KANA = [(k, v) for k, v in CAST_JSON["kana"].items()]
KANA += [("三十三歳", "さんじゅうさんさい"), ("五十ページ", "ごじゅっページ"), ("三ページ目", "さんページめ"),
         ("二組", "ふたくみ"), ("五日", "いつか"), ("三日前", "みっかまえ"), ("三日", "みっか"), ("四時", "よじ"),
         ("十一時", "じゅういちじ"), ("三か月", "さんかげつ"), ("一円", "いちえん"), ("一度も", "いちども"),
         ("外資系", "がいしけい"), ("在庫設定", "ざいこせってい"), ("無給労働", "むきゅうろうどう"),
         ("弁護士", "べんごし"), ("請求", "せいきゅう"), ("同窓会", "どうそうかい"), ("面接室", "めんせつしつ"), ("財産分与", "ざいさんぶんよ"), ("信頼", "しんらい")]
KANA.sort(key=lambda kv: -len(kv[0]))  # 긴 표기부터


def kana(text):
    s = text
    for a, b in KANA:
        s = s.replace(a, b)
    return s.replace("「", "").replace("」", "")


# 줄별 톤: 번호 → (EL 연기 태그, 감정 메모, 속도, 앞 쉼, 뒤 쉼, 연기·표정 지시)  — 빈 줄 0개
# 속도는 Lock 배치·OmniHuman 템포 참고값(EL v3는 태그로 표현, 속도는 후처리 95~105%).
T = {
    1: ('[desperate, voice breaking, pleading through tears]', 'sad 애원(강)', 0.80, 0.3, 0.4, '감독님 지적(2026-10-20): 절실함 부족 → 숨 섞인 떨림, 「お願い」에서 갈라지고 「戻ってきて」는 매달리듯 / 손 인서트'),
    2: ('[calm, quietly firm]', '결정타', 0.85, 0.8, 1.0, '분노 0, 낮고 또렷하게, 「でしょう？」 아주 살짝 올림 / 차분한 눈 — 썸네일·제목 대사'),
    3: ('[soft, reflective]', '회상', 0.88, 0.6, 0.5, '「下働き。」 한 단어로 끊고 반 박자'),
    4: ('[low, suspenseful]', '훅', 0.88, 0.3, 1.0, '「……百年の暖簾に」 앞 정적, 끝을 낮게 → 타이틀'),
    5: ('[neutral, gentle]', '자기소개', 0.95, 0.5, 0.3, '밝지도 어둡지도 않게'),
    6: ('[neutral, gentle]', '자기소개', 0.95, 0.3, 0.4, '「嫁いだ」 담담'),
    7: ('[steady, brisk]', '몽타주', 1.0, 0.4, 0.4, '리듬감, 사실 보고'),
    8: ('[steady]', '사실', 0.95, 0.4, 0.3, '「私だけ」 살짝 눌러'),
    9: ('[steady, proud]', '사실', 0.95, 0.3, 0.5, '자랑이 아닌 기록'),
    10: ('[warm, elderly]', 'happy 푸근', 0.85, 0.6, 0.4, '노인의 느린 말투 / 와이드, 입 안 보임 — 카메오'),
    11: ('[warm, polite]', 'happy 접객', 0.95, 0.5, 0.8, '진심 어린 접객 미소 / OMNI'),
    12: ('[cold, dismissive]', 'angry 0.7 냉담', 1.0, 0.8, 0.3, '「お給料？」 어이없다는 듯 올리고 뒤는 평탄 / 눈썹 한 번 올림'),
    13: ('[flat, indifferent]', '냉담', 1.0, 0.3, 1.0, '당연한 사실을 읊듯 / 등 돌림'),
    14: ('[low, hurt]', 'sad 0.6', 0.85, 0.8, 0.8, '가장 느리게, 「一円も」 뒤 반 박자 / 식칼 「톡」 뒤'),
    15: ('[hesitant, quiet]', 'sad 조심', 0.88, 1.2, 0.3, '「隆之さん」 뒤 1초 쉼, 끝을 흐림 / 무릎 위 손'),
    16: ('[bored, annoyed]', '귀찮음', 1.05, 0.5, 0.3, '게임 화면 보며 건성 / 시선은 휴대폰'),
    17: ('[dismissive, tired]', '귀찮음', 1.05, 0.2, 1.0, '「いいんだって」 끝을 늘어뜨림, 한숨 / 어깨 너머'),
    18: ('[low, weary]', '피로', 0.85, 0.8, 0.5, '피로가 묻은 낮은 톤 / 스탠드 꺼짐'),
    19: ('[bright, hospitable]', 'happy 접객', 0.95, 0.5, 0.2, '손님용 상냥한 접객 톤 / 입은 웃고'),
    20: ('[cold, quiet]', 'angry 0.7 냉담', 0.92, 0.2, 1.0, '반 박자 낮추고 차갑게, 「お気になさらず」 가볍게 / 시선만 복도 끝'),
    21: ('[flat, hurt]', '굴욕', 0.85, 0.7, 0.8, '「下働き」를 따옴표처럼 띄워서, 뒤 정적 — 걸레질 소리가 멈춘 뒤'),
    22: ('[firm, formal]', '통보', 0.95, 1.0, 0.3, '결정 사항 읽듯 또박또박 / 찻잔 내려놓음'),
    23: ('[flat, dismissive]', '통보', 0.95, 0.2, 0.8, '「だけでいいわ」 가볍게 / 와카나를 보지 않음'),
    24: ('[softly, uncertain]', 'fearful 절제', 0.9, 1.0, 0.2, '「でも」 뒤 1초, 말끝 끊김(마이가 자름) / 입술을 깨묾'),
    25: ('[sneering, mocking]', 'angry 0.8 비웃음', 1.08, 0.2, 0.3, '「はあ？」 높고 짧게, 부채 「촤악」 직후 / 입꼬리 한쪽'),
    26: ('[mocking, slow]', 'angry 0.8 비웃음', 1.05, 0.3, 1.0, '「よそ者」 강세, 마지막 문장은 느긋하게 내려다보듯 — 썸네일 상단 / 뒤 리액션 4초'),
    27: ('[cold, decisive]', 'angry 0.7 단호', 0.92, 0.8, 0.3, '「嫌なら」 뒤 반 박자 / 턱 들고 정면'),
    28: ('[proud, cold]', 'angry 0.7 단호', 0.92, 0.2, 1.0, '「百年」 힘주어 — 엔딩에서 그대로 되돌아오는 문장 / 어깨 너머'),
    29: ('[soft, relieved]', '해방', 0.85, 0.8, 0.5, '미소 컷과 동기화, 「不思議と」 뒤 반 박자'),
    30: ('[calm, clear]', '해방', 0.85, 1.5, 1.0, '앞 1.5초 침묵 후 또렷하게, 떨림 없음 / 깊이 절, 평온한 얼굴'),
    31: ('[low, ominous]', '전환', 0.85, 0.8, 0.9, '낮게, 「すべての始まり」 눌러 — 1차 광고 전환 문장'),
    32: ('[steady, calm]', '사실', 0.92, 1.0, 0.3, '성실함이 들리게'),
    33: ('[steady, listing]', '사실', 0.95, 0.3, 0.4, '목록은 또박또박'),
    34: ('[low, measured]', '복선', 0.85, 0.4, 0.8, '「……それをどう使うかは」 앞 1초, 뒤는 낮게'),
    35: ('[smug, airy]', 'happy 오만', 1.08, 0.5, 0.2, '콧노래 섞인 듯 가볍게 / 파일을 보지도 않고'),
    36: ('[smug, dismissive]', 'happy 오만', 1.08, 0.2, 1.0, '「ずっと」 강세 / 휴지통 「쿵」 뒤'),
    37: ('[tense, counting]', '카운트다운', 0.9, 1.0, 0.3, '「五日。」 끊어서, 긴장'),
    38: ('[steady, reporting]', '사실', 0.95, 0.3, 0.5, '사실 보고'),
    39: ('[flustered, stammering]', 'fearful 변명', 1.12, 0.3, 0.8, '「で、ですから」 더듬고 높게 / 손님 등 뒤'),
    40: ('[low, fading]', '불안', 0.9, 0.4, 0.6, '「次々と消えていった」 낮게 사라지듯 / 메일 화면 인서트 위'),
    41: ('[steady, grave]', '사실', 0.9, 0.8, 0.3, '「そば茶が出された」 무겁게'),
    42: ('[low, bitter]', '회수', 0.85, 0.3, 0.8, '「幸い」 안도 → 「三ページ目」 가장 낮게, 한 마디씩'),
    43: ('[shouting, furious]', 'angry 0.9', 1.1, 0.3, 0.3, '「麻衣！」 고함, 뒤는 숨 가쁘게 / 장부 내던짐'),
    44: ('[panicked, tearful]', 'fearful 변명', 1.15, 0.3, 1.0, '「わ、私」 더듬고 울먹이며 높게 / 손사래, 시선 피함'),
    45: ('[anguished, sharp]', 'angry→불안', 1.05, 0.3, 0.8, '안경 밀어 올리며, 「二十年」에 비명 섞임 / 어깨 너머'),
    46: ('[warm, calm]', '온기', 0.92, 1.0, 0.3, '처음으로 온기'),
    47: ('[warm, playful]', 'happy 여유', 1.0, 0.6, 0.3, '눈웃음, 찻잔 건네며'),
    48: ('[amused, teasing]', 'happy 여유', 1.0, 0.3, 0.8, '「あら」에서 장난기, 「あなたが決めて」 따뜻하게 — 쇼츠 명대사'),
    49: ('[soft, grateful]', '온기', 0.9, 0.8, 0.8, '「ずっと」 살짝, 눈가 젖은 리액션 위'),
    50: ('[tense, low]', '긴장', 0.88, 0.8, 0.4, '「初日。」 뒤 반 박자'),
    51: ('[polite, formal]', '사무적', 0.92, 0.5, 0.2, '정중한 비즈니스 일본어 / 뒷모습'),
    52: ('[polite, firm]', '사무적', 0.92, 0.2, 0.5, '「すべて」 또렷하게 / 뒷모습'),
    53: ('[shocked, stammering]', 'surprised', 1.1, 0.3, 0.5, '「キャ、」 더듬고 「キャンセル」 높게, 「どうして」 앞 뚝 / 눈 크게'),
    54: ('[calm, firm]', '단호·정중', 0.88, 0.8, 0.2, '「若菜さんです」 앞 반 박자, 또렷하게 / 창밖으로 고개'),
    55: ('[calm, final]', '단호·정중', 0.85, 0.2, 1.0, '가장 느리게, 마지막 문장 — 뒤 수화기 낙하·BGM 절단'),
    56: ('[low, matter-of-fact]', '사실', 0.9, 2.0, 0.4, '2초 무음 뒤 저음 드론 위에서, 숫자 또렷이'),
    57: ('[low, pointed]', '회수', 0.9, 0.3, 0.8, '「下働きの嫁」 따옴표 느낌으로 띄우고 눌러'),
    58: ('[hushed, revealing]', '도파민', 0.85, 0.8, 0.8, '「……三ページ目は」 앞 쉼, 낮게 — 휴지통 인서트 위'),
    59: ('[suspended, soft]', '전환', 0.85, 0.5, 0.9, '끝을 열어 둠 — 2차 광고 전환 문장'),
    60: ('[clear, honest]', '오해 차단', 0.9, 0.8, 0.3, '또렷하게 — 빼가기 오해 차단'),
    61: ('[calm, clear]', '오해 차단', 0.9, 0.3, 0.8, '「ご自分で」 강세'),
    62: ('[warm, elderly]', 'happy 푸근', 0.85, 0.8, 0.3, '느리게, 「ねえ」 늘어뜨림 / 와이드, 입 안 보임 — 카메오'),
    63: ('[warm, heartfelt]', 'happy 푸근', 0.85, 0.3, 1.5, '「人に」 강세, 뒤여운 1.5초 — 눈물 포인트'),
    64: ('[calm, level]', '조용한 통쾌', 0.85, 1.5, 0.3, '「ですか」 올리지 않고 내림 / 차분'),
    65: ('[calm, slightly cold]', '조용한 통쾌', 0.85, 0.3, 0.3, '마이 #26과 같은 리듬으로 되돌려줌, 화내지 않음'),
    66: ('[gentle, final]', '조용한 통쾌', 0.85, 0.3, 1.0, '「どうぞ」 뒤 반 박자, 입가만 옅게 — 썸네일 하단 프레임'),
    67: ('[steady, reporting]', '사후 보고', 0.92, 0.8, 0.3, '담담한 보고'),
    68: ('[steady, reporting]', '사후 보고', 0.92, 0.3, 0.3, '「正式に成立した」 또렷'),
    69: ('[low, closing]', '사후 보고', 0.88, 0.3, 1.0, '마지막 문장만 반 박자 느리게 — 남편의 결말'),
    70: ('[quiet, desolate]', '여운', 0.85, 0.6, 1.0, '쓸쓸하게, 가장 작게 / 부감 롱샷 위'),
    71: ('[desperate, voice breaking, pleading through tears]', 'sad 애원(강)', 0.80, 1.0, 0.3, '#1과 같은 녹음 — 수화기 두 손, 안경 벗음, 어깨 떨림 / OMNI'),
    72: ('[sobbing, broken]', 'sad 애원', 0.82, 0.3, 0.5, '말줄임마다 울음 삼킴, 「間違ってたわ」 갈라짐 — 컷 2·19의 꼿꼿함과 정반대'),
    73: ('[desperate, urgent]', 'fearful 다급', 1.15, 0.2, 0.5, '수화기 빼앗듯 급하게, 끝 끊김 / 핸드헬드 — 끝까지 「엄마 말대로」'),
    74: ('[gentle, steady]', '온화·결정적', 0.85, 1.5, 0.3, '분노 0. 도미코 #28을 같은 단어·다른 온도로 / 눈은 차분'),
    75: ('[calm, quietly firm]', '결정타', 0.85, 0.4, 1.0, '#2와 같은 녹음·같은 컷 — 「でしょう？」 아주 살짝 올림'),
    76: ('[warm, sincere]', '주제', 0.85, 1.0, 0.5, '교훈은 설교가 아닌 고백 톤 / 복도 팔로우'),
    77: ('[warm, bright]', '주제', 0.9, 0.3, 1.0, '「毎日」 밝게 — 가장 느리게 끝'),
    78: ('', 'normal', 1.0, 0.5, 0.4, '아웃트로 인사, 정중하게 (#02 재사용)'),
    79: ('', 'happy', 1.0, 0.4, 0.4, '구독 요청, 밝게 (#02 재사용) / 버튼 오버레이'),
    80: ('', 'happy', 1.0, 0.5, 0.4, '시청자 질문, 친근하게 / 허리 위 — 신규(Typecast)'),
    81: ('', 'normal', 1.0, 0.4, 0.4, '예고, 끝을 살짝 올려 — 신규(Typecast)'),
    82: ('', 'happy', 1.0, 0.4, 0.0, '작별 인사 (#02 재사용) → 손 흔들기'),
}
SAME_AS = {1: 71, 2: 75}                      # 같은 녹음을 두 장면에서 재사용(플래시포워드)
REUSE_EXT = {78: "chika line066", 79: "chika line067", 82: "chika line069"}  # #02 진행자 녹음 재사용(assets/auditions/chika-tts/)
MAX_SENT, MAX_SENT_PER_LINE = 30, 2


def load_lines():
    s = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read()
    body = s[s.index("## 4. 대본"):s.index("## 5. 대사별")]
    sc, out = None, []
    for ln in body.split("\n"):
        m = re.match(r"^(S\d\d|OUT) \(", ln)
        if m:
            sc = m.group(1)
        m = re.match(r"^\s+(\S+?):((?:【OMNI】)?(?:\([^)]*\))?)「(.+)」\s*(\[.*\])?$", ln)
        if m:
            spk = "NA" if re.match(r"NA\d", m.group(1)) else m.group(1)
            out.append((len(out) + 1, sc, m.group(1), spk, "OMNI" in m.group(2), m.group(3)))
    return out


def check_length(n, text):
    """제10장 8: 한 문장 ≤30자, 한 줄 ≤2문장. 「……」·「、」는 문장 경계가 아님."""
    sents = [t for t in re.split(r"[。！？]", text.replace("……", "…")) if t.strip()]
    warn = []
    if len(sents) > MAX_SENT_PER_LINE:
        warn.append(f"#{n} 문장 {len(sents)}개")
    for t in sents:
        if len(t) > MAX_SENT:
            warn.append(f"#{n} {len(t)}자: {t[:18]}…")
    return warn


def main():
    lines = load_lines()
    assert len(lines) == len(T), f"대본 {len(lines)}줄 ↔ 톤표 {len(T)}줄 불일치"
    warns, tests, rows, chars_el, chars_tc = [], [], [], 0, 0
    for n, sc, tag, spk, omni, text in lines:
        warns += check_length(n, text)
        eltag, emo, tempo, pre, post, note = T[n]
        name, role = CAST[spk]
        lid = f"line{n:03d}"
        if n in SAME_AS:
            src = f"#{SAME_AS[n]} 재사용"
        elif n in REUSE_EXT:
            src = f"#02 {REUSE_EXT[n]} 재사용"
        elif role == "host":
            tests.append({"id": lid, "model": "typecast-direct", "voice": HOST_TC, "language": "jpn",
                          "text": kana(text), "subtitle": text, "emotion_preset": "happy" if "happy" in emo else "normal",
                          "emotion_intensity": 1.0, "tempo": tempo})
            chars_tc += len(text); src = "신규(Typecast)"
        elif role == "regular":
            r = CAST_JSON["roles"]["regular"]
            tests.append({"id": lid, "model": "typecast-direct", "voice": r["voice_id"], "language": "jpn",
                          "text": kana(text), "subtitle": text, "emotion_preset": "happy", "emotion_intensity": 0.8, "tempo": tempo})
            chars_tc += len(text); src = "신규(Typecast)"
        else:
            r = CAST_JSON["roles"][role]
            tests.append({"id": lid, "model": "elevenlabs-direct", "voice": r["voice_id"], "voice_name": r["name"],
                          "el_model": "eleven_v3", "text": (eltag + " " if eltag else "") + kana(text), "subtitle": text})
            chars_el += len(text) + len(eltag); src = "신규(EL)"
        rows.append(f"| {n} | {sc} | {name} | {'OMNI' if omni else '-'} | {text} | {eltag or '-'} {emo} | {tempo} | {pre} | {post} | {note} | {src} |")
    spec = {"_설명": "#03 본녹음(PHASE 1). build_tts.py 생성물 — 직접 고치지 말 것. 대본 동결 승인 후 실행.",
            "tests": tests}
    os.makedirs(os.path.join(REPO, "scripts", "auditions"), exist_ok=True)
    json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "ryokan-tts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    md = ["# #03 『老舗旅館の嫁』 줄별 톤 연출표 (규칙 8-2 — 빈 줄 0개)", "",
          f"> 생성: `build_tts.py` · 캐스트 확정 2026-10-18 · 전체 {len(lines)}줄(신규 {len(tests)}개 / EL 약 {chars_el}자 + Typecast 약 {chars_tc}자, 동일 녹음 재사용 {len(SAME_AS)}줄, #02 진행자 재사용 {len(REUSE_EXT)}줄)",
          "> EL 태그 = eleven_v3 오디오 태그(2~4단어, 대사 앞). 속도 = Lock 배치·후처리 참고값. 쉼(초) = Lock 타임라인 배치값. 음성 입력은 가나 변형(§6), 자막은 대본 원문.",
          "> 감정 축: 와카나는 한 번도 소리를 높이지 않는다(통쾌함은 낮은 목소리) · 도미코 3단(접객 미소 → 통보 → 애원) · 마이는 늘 빠르다(반성 없음) · 되돌려주는 세 문장(#26→#62, #28→#70, #20→#2/#71)은 같은 단어·같은 끊김.", "",
          "| # | 장면 | 화자 | 립싱크 | 대사(자막) | 태그·감정 | 속도 | 앞 쉼 | 뒤 쉼 | 연기·표정 지시 | 음성 |",
          "|---|---|---|---|---|---|---|---|---|---|---|", *rows, ""]
    if warns:
        md += ["## 길이 검사(제10장 8) 경고", *[f"- {w}" for w in warns], ""]
    open(os.path.join(HERE, "05_톤연출표.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"{len(lines)}줄 / 신규 {len(tests)}개 / EL {chars_el}자 + TC {chars_tc}자 / 재사용 {len(SAME_AS) + len(REUSE_EXT)}줄")
    for w in warns:
        print("경고:", w)


if __name__ == "__main__":
    main()
