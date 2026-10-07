#!/usr/bin/env python3
"""타워맨션 PHASE 1 — 줄별 톤 연출표(05) + 본녹음 TTS 스펙(scripts/auditions/tower-tts.json) 생성기.

입력: 00_script_ja.md(동결 대본), 04_목소리추천.md의 확정 캐스트(아래 CAST 상수)
출력: 05_톤연출표.md, scripts/auditions/tower-tts.json
규칙: CLAUDE.md 8-2(빈 줄 0개) · 제9장 5(Typecast language 필수) · 음성 입력만 가나 변형(자막은 한자 유지)
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from parse_script import load_lines

# 확정 캐스트 (2026-10-07 사용자: 유미 ②Haruna · 레이카 ①Sakura · 오다기리 ①Hideo · 나머지 원어민 추천)
CAST = {
    "NA": ("유미(내레이션)", "tc_62b17ef6695ad26f7fb8e7f3"),
    "由美": ("유미", "tc_62b17ef6695ad26f7fb8e7f3"),
    "麗華": ("레이카", "tc_6412c4162bafc5127fa16ffa"),
    "小田切": ("오다기리", "tc_640997d2c535f40558c0722c"),
    "ママA": ("측근 엄마 A", "tc_68d49c1e02c83f1fd4cdeaae"),
    "担当者": ("관리회사 담당자", "tc_62baac31e1c614d37b9160e3"),
    "住民": ("주민", "tc_63f7167e54b37fb5326409d1"),
    "莉子": ("리코", "tc_63edf3ccd8e2eb7338999376"),
    "진행자": ("진행자", "tc_629fe972013e90b4db213fd8"),
}

# 가나 변형(음성 입력 전용). 긴 표기부터 바꾼다.
KANA = [
    ("西園寺ビルメンテナンス", "さいおんじビルメンテナンス"), ("西園寺", "さいおんじ"), ("麗華", "れいか"),
    ("小田切", "おだぎり"), ("莉子", "りこ"), ("高橋由美", "たかはしゆみ"), ("高橋", "たかはし"),
    ("修繕積立金", "しゅうぜんつみたてきん"), ("積立金", "つみたてきん"), ("区分所有者", "くぶんしょゆうしゃ"),
    ("賃借人", "ちんしゃくにん"), ("一・八倍", "いってんはちばい"), ("四十二階", "よんじゅうにかい"),
    ("四十二歳", "よんじゅうにさい"), ("五階", "ごかい"), ("二千四百万円", "にせんよんひゃくまんえん"),
    ("築六年", "ちくろくねん"), ("業務上横領", "ぎょうむじょうおうりょう"), ("経理一筋二十年", "けいり、ひとすじ、にじゅうねん"),
    ("二十年", "にじゅうねん"), ("三か月後", "さんかげつご"), ("一か月後", "いっかげつご"), ("三か月", "さんかげつ"), ("一か月", "いっかげつ"), ("三件", "さんけん"),
    ("三日前", "みっかまえ"), ("三週間", "さんしゅうかん"), ("二年分", "にねんぶん"), ("二十七件", "にじゅうななけん"), ("百人", "ひゃくにん"), ("過去二年間", "かこにねんかん"), ("SNS", "エスエヌエス"),
    ("名誉毀損", "めいよきそん"), ("捏造", "ねつぞう"), ("滞納", "たいのう"), ("閲覧請求", "えつらんせいきゅう"),
]
KANA_BY_SPK = {"ママA": [("りこちゃん", "リコちゃん"), ("れいかさん", "レイカさん")]}  # 원어민 Miu가 영어처럼 읽은 이름 → 가타카나


# 줄별 입력 교정(1차 녹음 large-v3 검사 오독 → 가나 변형). 자막은 대본 원문 유지.
LINE_TEXT = {
    3: "さんかげつご、この女が段ボール箱を抱えて、あの、にもつようエレベーターに乗ることになるとは知らずに。",
    10: "ごめんね、りこちゃん。ここ、上の子専用になったの。れいかさんが決めたのよ",
    16: "理由は、外壁の緊急工事。だが、このマンションは、ちく、ろくねん。外壁はどこも傷んでいない。",
    32: "代表者の名前は、さいおんじ。れいかの、じつの弟だった。",
    46: "理事長の解任決議は、賛成多数で即座に可決された。管理組合は、ぎょうむじょうおうりょうで、けいじこくそすることを決めた。",
    50: "私が海外にいる間、あなたはオーナーの、めい、だと名乗っていたそうだね。だが、あなたは私の部屋を借りているだけの、ただのちんしゃくにんだ",
}
# 대안 녹음(검사 후 더 나은 쪽 채택): 줄 번호 → (접미사, 입력문, 속도)
ALT = {10: ("v2", "ごめんね、りこ、ちゃん。ここ、上の子専用になったの。れいか、さんが決めたのよ", 1.0)}


def kana(text, spk):
    s = text
    for a, b in KANA:
        s = s.replace(a, b)
    for a, b in KANA_BY_SPK.get(spk, []):
        s = s.replace(a, b)
    s = s.replace("〜", "").replace("』『", "、").replace("『", "").replace("』", "")
    return s


# 줄별 톤: 번호(대본 순서) → (감정, 강도, 속도, 앞 쉼, 뒤 쉼, 연기·표정 지시)
# 쉼(초)은 Lock 타임라인 배치값. 0 = 장면 규칙(대사 끝→컷 1.8 / 내레이션 끝→컷 1.0)을 따른다.
T = {
    1: ("toneup", 1.0, 1.0, 0.3, 0, "내려다보는 비웃음, 공손한 척하는 악의 / 표정: 입꼬리만 올린 냉소"),
    2: ("tonedown", 1.0, 0.95, 0.5, 0.5, "담담한 회상, 감정 억제"),
    3: ("tonedown", 1.0, 0.95, 0.5, 0.5, "낮게, 예고하듯"),
    4: ("tonedown", 1.2, 0.9, 0.5, 0.7, "숨 들이쉬고 멈칫 — 뒤 0.7초 완전 정적(BGM도 끊음)"),
    5: ("tonedown", 1.4, 0.9, 0, 1.0, "차갑고 확신에 찬 고백 — 후크 결정타"),
    6: ("normal", 1.0, 1.0, 0.5, 0.5, "자기소개, 건조하고 담백하게"),
    7: ("normal", 1.0, 1.0, 0.5, 0.5, "관찰자 톤, 「タワマンカースト」에 살짝 냉소"),
    8: ("tonedown", 1.0, 1.0, 0.5, 0.5, "규칙 나열, 담담한 냉소"),
    9: ("tonedown", 1.0, 1.0, 0.5, 0, "정점의 인물 소개, 이름에 무게"),
    10: ("happy", 1.0, 1.05, 0.3, 0, "들뜬 하이톤, 미안한 척 아첨 / 리코에게 몸 숙인 뒷모습"),
    11: ("tonedown", 1.0, 1.0, 0.5, 0.5, "부당함을 사실로만 짚는다"),
    12: ("sad", 0.8, 0.95, 0.5, 0, "억눌린 분노, 「奥歯を噛みしめた」에 힘"),
    13: ("sad", 1.2, 0.95, 0.3, 0.8, "울먹임 직전의 작은 목소리 / 엄마 품에 얼굴 묻음"),
    14: ("whisper", 1.0, 0.9, 0.8, 0, "속삭이듯 다독임, 끝에 결심 / 머리 쓰다듬는 손"),
    15: ("normal", 1.0, 1.0, 0.5, 0.5, "통지 내용 낭독, 숫자 또렷이"),
    16: ("tonedown", 1.0, 1.0, 0.5, 0, "「だが」에서 의심으로 전환"),
    17: ("toneup", 0.9, 1.0, 0.3, 0.6, "명분을 내세운 거만한 안건 설명 / 단상 원경, 입 비노출"),
    18: ("normal", 1.0, 0.95, 0.3, 0, "정중하고 차분하게, 떨림 없음 / 표정: 담담한 정면 시선"),
    19: ("toneup", 0.8, 1.0, 0.5, 0.4, "귀찮다는 듯 느물거리는 하이톤 / 측면, 마이크로 입 가림"),
    20: ("happy", 0.7, 1.0, 0.4, 0.3, "비웃으며 내려다보는 모욕 — 「バッグ三つ分」에 웃음기 / 표정: 비웃음"),
    21: ("happy", 1.2, 1.05, 0.3, 0, "맞장구치는 아첨, 웃음 섞어"),
    22: ("sad", 0.8, 0.95, 0.5, 0.5, "체념한 주민들에 대한 쓸쓸한 관찰"),
    23: ("tonedown", 1.0, 0.95, 0.5, 0.5, "고개 숙인 채 낮게"),
    24: ("tonedown", 1.0, 0.95, 0.5, 0.5, "인용 부분을 또박또박"),
    25: ("tonedown", 1.3, 0.9, 0.5, 0, "「……これは」 앞 반 박자 쉼, 확신의 결론 — 1차 광고 클리프행어"),
    26: ("normal", 1.0, 1.0, 0.5, 0.5, "법적 권리를 차분히, 단호하게"),
    27: ("tonedown", 1.0, 0.95, 0.5, 0, "경리의 신조, 한 구절씩 끊어"),
    28: ("sad", 0.8, 1.0, 0.3, 0, "소심하게 털어놓음, 말끝 흐림 / 담당자 뒷모습"),
    29: ("normal", 1.0, 0.95, 0.5, 0, "망설이다 결심, 「……でも」에서 톤이 곧아짐 / 파일 내미는 손"),
    30: ("tonedown", 1.2, 0.95, 0.5, 0.8, "금액 앞에서 숨 고르고 또렷이(뒤 ドン 효과음)"),
    31: ("normal", 1.0, 1.0, 0.5, 0.5, "건조한 사실 나열"),
    32: ("tonedown", 1.3, 0.9, 0.5, 0, "「西園寺」 뒤 반 박자, 폭로"),
    33: ("tonedown", 1.0, 1.0, 0.5, 0, "냉소 섞인 발견"),
    34: ("tonedown", 1.1, 0.95, 0.5, 0.5, "집요한 대조 작업의 결론, 「一件残らず」에 힘"),
    35: ("tonedown", 1.2, 0.95, 0.5, 1.0, "「……西園寺ではなかった」 낮게 떨어뜨림 — 디졸브"),
    36: ("normal", 1.0, 1.0, 0.5, 0.5, "긴장 고조, 담담하게"),
    37: ("toneup", 0.7, 0.95, 0.5, 0, "귓가에 대고 깔보는 속삭임 / 등 돌린 실루엣"),
    38: ("toneup", 1.0, 1.0, 0.3, 0.4, "단상의 거만한 선고, 「……発言禁止処分」에 승리감 / 표정: 턱 든 미소"),
    39: ("tonedown", 1.2, 0.95, 0.5, 0.3, "조용하지만 단호, 떨림 없음 / 표정: 흔들림 없는 시선"),
    40: ("normal", 1.0, 1.0, 0.3, 0.5, "자료를 제시하는 경리의 정확한 톤"),
    41: ("tonedown", 1.0, 0.9, 1.0, 0.4, "BGM 끊김+심장 박동 뒤, 인용을 차갑게 — 뒤 0.4초"),
    42: ("tonedown", 1.4, 0.9, 0, 0.8, "킬링 멘트, 한 단어씩 눌러서"),
    43: ("angry", 1.2, 1.05, 0.3, 0, "흥분한 고함 / 일어선 뒷모습"),
    44: ("angry", 1.3, 1.1, 0.2, 0, "말 더듬는 당황, 목소리 갈라짐 / 표정: 눈 커진 당황·땀"),
    45: ("tonedown", 1.3, 0.95, 0.4, 0, "처음으로 단호하게, 소심함이 사라진 톤 / 표정: 결심한 정면"),
    46: ("normal", 1.0, 1.0, 0.5, 0.5, "결과 보고, 통쾌함은 절제"),
    47: ("angry", 1.5, 1.1, 0.3, 0.9, "이성을 잃은 절규, 마이크 스탠드 움켜쥠 / 표정: 분노 일그러짐 — 2차 광고"),
    48: ("tonedown", 1.2, 0.85, 0.8, 0.8, "느리고 낮게 깔리는 한 마디, 권위 / 표정: 담담한 노신사"),
    49: ("tonedown", 1.0, 0.95, 0.5, 0.5, "작은 반전의 고백, 차분하게"),
    50: ("tonedown", 1.0, 0.85, 0.4, 0, "한 마디씩 끊어 권위 유지 / 표정: 냉정"),
    51: ("tonedown", 1.0, 0.85, 0.4, 0, "규약을 읽듯 또박또박"),
    52: ("normal", 1.0, 0.85, 0.6, 0, "「……家賃も」 앞 쉼, 마지막 통보는 담담하게"),
    53: ("sad", 1.5, 1.1, 0.5, 0, "3분할: ①「お、小田切様……!」 떨림 ②「待ってください、それだけは……!」 숨 가쁘게 ③「私、ここを…行く場所が……!」 말끝 흐림 / 바닥에 주저앉은 CU"),
    54: ("tonedown", 1.0, 0.85, 0.6, 0, "로우앵글, 「下の階」에 힘"),
    55: ("tonedown", 1.1, 0.85, 0.5, 0, "돌아서며 마지막 일침, 살짝 웃음기"),
    56: ("tonedown", 1.0, 0.95, 0.5, 0.5, "정체 정리, 냉정하게"),
    57: ("normal", 1.0, 1.0, 0.5, 0.5, "후일담, 안도"),
    58: ("normal", 1.0, 1.0, 0.5, 0.5, "시간 경과 카드(밝게)"),
    59: ("happy", 1.5, 1.05, 0.3, 0, "신나서 외침 / 유리문 안 원경"),
    60: ("happy", 0.6, 0.95, 0.5, 0.5, "정중한 미소 뒤의 반격, 「……住人の皆さんが」 앞 쉼 / 표정: 우아한 미소"),
    61: ("tonedown", 1.0, 0.9, 0.5, 1.0, "엔딩 메시지, 따뜻하지만 단단하게"),
    62: ("normal", 1.0, 1.0, 0.3, 0.5, "진행자, 밝고 따뜻하게"),
    63: ("happy", 0.8, 1.0, 0.3, 0.5, "구독 요청, 미소"),
    64: ("happy", 0.8, 1.0, 0.3, 0.5, "시청자 질문, 친근하게"),
    65: ("happy", 0.8, 1.0, 0.3, 0, "작별 인사"),
}
SPLIT = {53: [("a", "お、おだぎり様……!", "sad", 1.2, 1.05), ("b", "待ってください、それだけは……!", "sad", 1.5, 1.15),
              ("c", "私、ここを追い出されたら、行く場所が……!", "sad", 1.5, 1.0)]}


def remap_existing(tests):
    """대본 보강으로 줄 번호가 밀려도 같은 녹음(목소리·문장·감정·속도 동일)은 새 번호로 옮겨 재사용한다(크레딧 절약)."""
    spec_path = os.path.join(REPO, "scripts", "auditions", "tower-tts.json")
    adir = os.path.join(REPO, "assets", "auditions", "tower-tts")
    if not (os.path.exists(spec_path) and os.path.isdir(adir)):
        return
    sig = lambda t: (t["voice"], t["text"], t.get("emotion_preset"), t.get("emotion_intensity"), t.get("tempo"))
    old = {sig(t): t["id"] for t in json.load(open(spec_path, encoding="utf-8"))["tests"]}
    tmp = os.path.join(adir, "_remap")
    os.makedirs(tmp, exist_ok=True)
    moved = {}
    for t in tests:
        oid = old.get(sig(t))
        src = os.path.join(adir, f"{oid}.mp3") if oid else None
        if src and os.path.exists(src):
            os.replace(src, os.path.join(tmp, f"{t['id']}.mp3"))
            moved[oid] = t["id"]
    for f in os.listdir(adir):  # 재사용되지 않은 옛 녹음(문장이 바뀐 줄)은 지운다 → 새로 녹음
        if f.endswith(".mp3"):
            os.remove(os.path.join(adir, f))
    for f in os.listdir(tmp):
        os.replace(os.path.join(tmp, f), os.path.join(adir, f))
    os.rmdir(tmp)
    json.dump(moved, open(os.path.join(HERE, "tts_remap.json"), "w"), indent=1)
    print(f"재사용 {len(moved)}개, 새 녹음 {len(tests) - len(moved)}개")


def main():
    lines = load_lines()
    assert len(lines) == len(T), (len(lines), len(T))
    tests, rows = [], []
    for n, x in enumerate(lines, 1):
        spk = "NA" if x["spk"].startswith("NA") else x["spk"]
        role, voice = CAST[spk]
        emo, inten, tempo, pre, post, note = T[n]
        lid = f"line{n:03d}"
        if n in SPLIT:
            for suf, txt, e, i, tp in SPLIT[n]:
                tests.append({"id": lid + suf, "model": "typecast-direct", "voice": voice, "language": "jpn",
                              "text": kana(txt, spk), "emotion_preset": e, "emotion_intensity": i, "tempo": tp})
        else:
            tests.append({"id": lid, "model": "typecast-direct", "voice": voice, "language": "jpn",
                          "text": LINE_TEXT.get(n) or kana(x["text"], spk), "emotion_preset": emo, "emotion_intensity": inten, "tempo": tempo})
            if n in ALT:
                suf, txt, tp = ALT[n]
                tests.append({"id": lid + suf, "model": "typecast-direct", "voice": voice, "language": "jpn",
                              "text": txt, "emotion_preset": emo, "emotion_intensity": inten, "tempo": tp})
        rows.append(f"| {lid} | {x['scene']} | {role} | {'OMNI' if x['omni'] else ''} | {x['text']} | {emo} {inten} | {tempo} | {pre or '규칙'} / {post or '규칙'} | {note} |")
    remap_existing(tests)
    spec = {"_설명": "타워맨션 PHASE 1 본녹음(확정 원어민 캐스트, Typecast ssfm-v30 jpn). build_tts.py 생성 — 직접 수정 금지. 음성 입력만 가나 변형, 자막은 한자 유지. 줄 번호 = 대본 순서.",
            "tc_model": "ssfm-v30", "language": "jpn", "tests": tests}
    json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "tower-tts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = ["# 『タワマンのボスママ』 줄별 톤 연출표 (CLAUDE.md 8-2 — 빈 줄 0개)", "",
          "생성: `build_tts.py` · 감정 = Typecast emotion_preset(강도) · 속도 = tempo · 쉼 = 앞/뒤 초(「규칙」= 대사 끝→컷 1.8, 내레이션 끝→컷 1.0) · 표정은 키프레임에 50% 반영",
          "", "| 줄 | 장면 | 배역 | 립싱크 | 대사 | 감정 | 속도 | 쉼(앞/뒤) | 연기·표정 지시 |", "|---|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(HERE, "05_톤연출표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(len(lines), "줄 →", len(tests), "녹음,", sum(len(t["text"]) for t in tests), "자")


if __name__ == "__main__":
    main()
