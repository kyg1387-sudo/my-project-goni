#!/usr/bin/env python3
"""『運転手のくせに』 PHASE 1 본녹음 스펙 + 줄별 톤 연출표 생성기 (무료). ashita build_tts_spec.py 복사·수정.

입력: 00_script_ja.md (🔒 v1.0 동결), 04_목소리추천.md의 확정 캐스트(아래 VOICE, 2026-10-13 고니감독님 확정).
출력: scripts/auditions/untenshu-tts.json (Typecast ssfm-v30 jpn, line### = 시간 순서), 05_톤연출표.md.
가나 변형은 음성 입력에만 적용하고 자막은 한자를 유지한다.
재사용(녹음 안 함): OUT1·OUT3·OUT4 = 『明日から』 진행자 녹음·립싱크(assets/auditions/ashita-outro-omni),
후크 H1 = L11, 드라이브 레코더 S18 = L11·L14(스피커 필터).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

VOICE = {  # 04_목소리추천.md 확정 캐스트 (2026-10-13 고니감독님 추천안 그대로 확정)
    "NA": ("Lloyd", "tc_65681f21097fc4326ceb5e21"),
    "黒田": ("Zeus", "tc_6a5882fe54564e2a06a218bb"), "大塚": ("Simon", "tc_65b34b05b3fb844f3d6b7aab"),
    "小川": ("Tomoko Nomura", "tc_63be4f467ac1708d9ccd75d4"), "石井": ("Sindarin", "tc_61095ebc03c0e5b98f8ba69c"),
    "三浦": ("Miki Yamamoto", "tc_63b6650135703800462c1eb0"), "千代子": ("Emma", "tc_61d55a84b8c48f42d69b2399"),
    "老婦人": ("Lucille", "tc_674808a7602c751359c7b280"),
    "OUT": ("Yui Sato", "tc_629fe972013e90b4db213fd8"),
}
REUSED = {"OUT1", "OUT3", "OUT4"}
DELETED = {"NA5", "NA7"}  # v1.1 삭제 — 녹음 번호(line008·line015)를 지키려고 번호는 세고 사용만 안 함
RETAKE = {"NA12", "L32", "L33", "L37"}  # 본녹음 언어 검사 발음 보정 → untenshu-tts-add에 같은 line 번호로 재녹음

# 태그: (감정 프리셋, 강도, 템포, 연기 메모 — 표정·동작까지 한 줄에서 결정, 제10장 7). 지정 없는 줄 0개.
TONE = {
    "NA0": ("tonedown", 1.0, 0.95, "미스터리, 「開けたのは」 뒤 끊김"),
    "NA1": ("normal", 1.0, 1.0, "비 오는 밤, 차분한 도입"),
    "NA2": ("normal", 1.0, 0.95, "인물 소개, 존중"),
    "NA3": ("sad", 0.6, 0.95, "「妻の写真だった」 부드럽게 내려앉음"),
    "L01": ("happy", 0.5, 0.9, "미안함 섞인 고마움, 느릿하게 — 지팡이에 기대 고개 숙임"),
    "L02": ("happy", 0.6, 0.95, "온화한 미소 — 문을 잡아 주는 흰 장갑"),
    "NA4": ("normal", 1.0, 0.95, "「彼の流儀」에 무게"),
    "NA5": ("normal", 1.0, 1.0, "시간·장소 전환"),
    "NA6": ("normal", 1.0, 1.0, "인물 소개, 「部長」 또렷"),
    "L03": ("angry", 0.7, 1.05, "술 취한 짜증 — 넥타이를 잡아당기며 털썩 앉음"),
    "L04": ("normal", 1.0, 0.95, "정중한 응대 — 백미러로 손님 확인"),
    "L05": ("toneup", 1.0, 1.05, "거만한 명령, 「こっちは」 강조 — 다리를 꼬고 기댐"),
    "L06": ("normal", 1.0, 1.0, "성실, 조심스럽게 — 무릎 위 서류를 넘김"),
    "L07": ("happy", 0.9, 1.0, "히죽 웃는 자랑 — 창밖을 보며 턱을 쓰다듬음"),
    "NA7": ("normal", 1.0, 1.0, "「大一番」에 힘"),
    "L08": ("normal", 1.0, 0.95, "정중한 설명, 미안한 기색 — 깜빡이를 켜는 손"),
    "L09": ("angry", 0.8, 1.05, "의심·비꼼 — 몸을 앞으로 숙임"),
    "L10": ("sad", 0.6, 0.95, "당황하지만 차분, 말끝 흐림 — 핸들을 쥔 손에 힘"),
    "L11": ("angry", 1.2, 1.1, "폭발 고함 — 등받이를 걷어차고 손가락질 [Omni·후크·레코더]"),
    "NA8": ("tonedown", 1.0, 0.95, "충격의 순간, 느리게"),
    "L12": ("toneup", 1.0, 1.1, "다급한 제지 — 大塚의 팔을 잡음, 떨림"),
    "L13": ("tonedown", 1.0, 0.95, "낮게 깔보는 위협, 「神様なんだよ」 천천히 — 小川의 손을 뿌리침"),
    "L14": ("happy", 0.8, 0.95, "비웃음 — 뒤로 기대며 느린 고갯짓 [Omni·레코더]"),
    "L15": ("tonedown", 1.0, 0.9, "감정을 누르고 담담 — 백미러 속 눈, 미동 없음"),
    "NA9": ("tonedown", 1.0, 0.95, "조용한 무게"),
    "L16": ("angry", 0.8, 1.05, "경멸, 던지듯 — 구겨진 지폐를 던짐"),
    "L17": ("normal", 1.0, 0.9, "담담, 「会社は、ございません」 반 박자 쉼(복선) — 앞만 봄"),
    "L18": ("angry", 0.6, 1.0, "혀 차며 비아냥 — 문을 쾅 닫음"),
    "L19": ("sad", 0.8, 0.95, "진심 어린 사과 — 고개 숙여 지갑을 꺼냄"),
    "L20": ("sad", 0.6, 0.95, "다정, 조심스럽게 — 닦은 액자를 두 손으로 내밂 [Omni]"),
    "L21": ("normal", 1.0, 0.9, "놀람 섞인 감사, 따뜻하게 — 액자를 받아 듦"),
    "L22": ("happy", 0.5, 1.0, "수줍은 따뜻한 인사 — 꾸벅 인사 후 내림"),
    "NA10": ("tonedown", 1.0, 0.9, "저음 완급, 1차 광고 직전 여운"),
    "NA11": ("normal", 1.0, 1.0, "들뜬 사무실 분위기"),
    "L23": ("normal", 1.0, 1.0, "조심스러운 보고 — 서류를 안고 다가감"),
    "L24": ("angry", 0.8, 1.0, "짜증·깔봄 — 서류를 책상에 내던짐 [Omni]"),
    "L25": ("tonedown", 1.0, 1.0, "낮게 못박음 — 손가락으로 책상을 두드림"),
    "L26": ("sad", 0.8, 0.9, "억누른 서운함, 작게 — 서류를 꼭 쥠"),
    "L27": ("normal", 1.0, 0.95, "진지한 당부 — 서류철을 든 채 大塚를 봄 [Omni]"),
    "L28": ("happy", 1.0, 1.05, "아첨 섞인 자신만만 — 벌떡 일어나 웃음"),
    "NA12": ("normal", 1.0, 0.95, "조용한 아침"),
    "NA13": ("sad", 0.6, 0.95, "회상, 아련하게"),
    "NA14": ("normal", 1.0, 0.95, "인용 부분 살짝 낮게"),
    "NA15": ("happy", 0.5, 0.95, "시작의 따뜻함"),
    "L29": ("sad", 0.6, 0.85, "약하지만 따뜻한 미소 — 남편의 손을 잡음 [Omni]"),
    "L30": ("sad", 0.8, 0.85, "목이 메어 짧게 — 아내의 손을 감쌈(뒷모습)"),
    "NA16": ("normal", 1.0, 0.95, "약속의 무게"),
    "NA17": ("tonedown", 1.0, 0.9, "주제 문장, 천천히"),
    "L31": ("normal", 1.0, 1.0, "단정한 안내 — 걸으며 손으로 방향 안내"),
    "L32": ("tonedown", 0.8, 1.0, "우쭐한 작은 목소리(귓속말 톤) — 小川 쪽으로 몸을 기울임 (whisper는 「ほらな」가 뭉개져 교체)"),
    "L33": ("normal", 1.0, 0.95, "정중하고 위엄 있게 — 문 앞에서 가볍게 목례"),
    "L34": ("tonedown", 1.0, 0.85, "조용한 압박 — 大塚를 똑바로 봄, 미동 없이 [Omni]"),
    "NA18": ("tonedown", 1.0, 0.95, "충격, 핏기가 가심"),
    "L35": ("sad", 1.0, 1.05, "공포로 더듬음 — 명함 쥔 손이 떨림 [Omni]"),
    "NA19": ("tonedown", 1.0, 0.9, "저음 완급, 2차 광고 직전 여운"),
    "NA20": ("normal", 1.0, 0.95, "증거 제시, 또박또박"),
    "L36": ("sad", 0.7, 0.9, "창백한 실망 — 안경을 벗음"),
    "L37": ("toneup", 1.0, 1.1, "패닉 변명 — 땀, 양손을 내젓음 [Omni]"),
    "L38": ("normal", 1.0, 0.9, "차분하고 단호 — 태블릿 위에 두 손을 포갬"),
    "L39": ("tonedown", 1.0, 0.9, "단호, 「金額では」 강조 [Omni]"),
    "L40": ("tonedown", 1.0, 0.9, "짧은 통보 — 태블릿을 거둠"),
    "L41": ("sad", 1.1, 0.9, "울며 애원 — 무릎 꿇고 올려다봄, 눈물 [Omni]"),
    "L42": ("tonedown", 1.0, 0.9, "조용히 되짚음 — 내려다봄"),
    "L43": ("normal", 1.0, 0.9, "신념, 한 마디씩 — 흰 장갑을 쥐었던 손을 펼침"),
    "L44": ("tonedown", 1.0, 0.85, "차가운 결론 [Omni]"),
    "L45": ("sad", 0.5, 0.9, "부드럽게 전환 — 小川 쪽으로 몸을 돌림"),
    "L46": ("happy", 0.6, 0.9, "따뜻한 제안 — 小川에게 미소 [Omni]"),
    "L47": ("sad", 1.0, 0.9, "눈물이 맺힌 떨림 — 서류를 안은 손이 떨림"),
    "L48": ("tonedown", 1.0, 0.95, "엄중한 결정 — 깊이 고개 숙인 뒤"),
    "NA21": ("normal", 1.0, 1.0, "결과 전달"),
    "NA22": ("tonedown", 1.0, 0.95, "몰락 통보"),
    "NA23": ("normal", 1.0, 0.95, "교훈, 「思い知らされた」 무게"),
    "L49": ("happy", 0.7, 0.9, "다정한 농담 — 백미러 속 웃는 눈"),
    "L50": ("happy", 0.8, 1.0, "웃으며 거절 — 우산을 접으며 탐"),
    "NA24": ("normal", 1.0, 0.85, "가장 느리게, 마무리"),
    # v1.1 Lock 보강(13_Lock보강안.md, 4-3절 증폭 설계) — 별도 스펙 untenshu-tts-add(P01~P11)
    "P1": ("sad", 0.6, 0.95, "억눌린 小川의 마음, 「静かな目」에서 반 박자"),
    "P2": ("happy", 0.9, 1.05, "반성 없는 자랑, 「しつけてやったよ」 비웃듯 — 의자에 기대 통화 [Omni] · 분노 정점"),
    "P3": ("sad", 0.5, 0.85, "액자에 건네는 혼잣말, 쓸쓸한 미소 — 손·뒷모습"),
    "P4": ("tonedown", 1.0, 0.95, "「小さな傷」에서 멈칫"),
    "P5": ("sad", 0.8, 0.9, "감정의 바닥, 가장 조용히"),
    "P6": ("toneup", 0.8, 1.0, "멈칫한 의문 — 사진 앞에서 발을 멈춤"),
    "P7": ("angry", 0.6, 1.05, "코웃음, 귀찮다는 듯 — 걸으며 넥타이"),
    "P8": ("normal", 1.0, 1.0, "자신만만한 훈계(아이러니) — 창에 비친 자기 모습"),
    "P9": ("toneup", 1.0, 1.1, "다급한 수습 — 반쯤 일어나 손을 뻗음"),
    "P10": ("tonedown", 1.0, 0.9, "조용히 탈출구를 막음 — 미동 없이"),
    "P11": ("tonedown", 1.0, 0.95, "응징의 여운, 「一台もなかった」 천천히"),
    "OUT2": ("happy", 1.0, 0.92, "질문은 또렷이(진행자 립싱크 입력 tempo 0.92 표준)"),
}

KANA = [("黒田宗一郎", "くろだそういちろう"), ("大塚浩二", "おおつかこうじ"), ("小川結衣", "おがわゆい"),
        ("黒田", "くろだ"), ("大塚", "おおつか"), ("小川", "おがわ"), ("千代子", "ちよこ"),
        ("白鷺精機", "しらさぎせいき"), ("東雲物産", "しののめぶっさん"), ("三十億", "さんじゅうおく"),
        ("港区", "みなとく"), ("旋盤", "せんばん"), ("昨夜", "ゆうべ"), ("直々", "じきじき"),
        ("本日付", "ほんじつづけ"), ("制帽", "せいぼう"), ("千円", "せんえん"), ("四十年前", "よんじゅうねんまえ"),
        ("六十七歳", "ろくじゅうななさい"), ("四十五歳", "よんじゅうごさい"), ("二十六歳", "にじゅうろくさい"),
        ("七年前", "ななねんまえ"), ("午後十一時", "ごごじゅういちじ"), ("週に一度", "しゅうにいちど"),
        ("一言", "ひとこと"), ("取締役", "とりしまりやく"), ("専務", "せんむ"), ("負け組", "まけぐみ"),
        ("指図", "さしず"), ("――", "……"), ("“", ""), ("”", "")]

TAG_KANA = {  # 본녹음 언어 검사(run 38399414508)에서 발음이 흔들린 줄만 줄 단위 보정(ashita R6 방식)
    "NA12": [("脱いだ", "ぬいだ")],                       # 「正母を向いた」로 들림
    "L33": [("黒田です", "クロダです")],                    # 「クローダ」로 들림
    "L37": [("違うんです専務", "違うんです、せんむ")],         # 「さテム」로 들림
    "P9": [("大塚の処分", "おおつかの、しょぶん")],            # 예방
    "P10": [("処分", "しょぶん")],                          # 예방
}


def kana(tag, s):
    for a, b in TAG_KANA.get(tag, []) + KANA:
        s = s.replace(a, b)
    return s


def load():
    t = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 4-1.")[0]
    out = []
    for m in re.finditer(r"^\s+((?:NA|L|OUT|P)\d+)\s*([^\s:「(]*)[^「\n]*「(.+?)」", body, re.M):
        tag, spk, text = m.groups()
        role = "NA" if tag.startswith("NA") or (tag.startswith("P") and not spk) else "OUT" if tag.startswith("OUT") else spk
        out.append((tag, role, text))
    return out


def main():
    allx = [x for x in load() if x[0] not in REUSED]
    lines = [x for x in allx if not x[0].startswith("P")]
    adds = [x for x in allx if x[0].startswith("P")]
    missing = [tag for tag, _, _ in allx if tag not in TONE and tag not in DELETED]
    if missing:
        sys.exit(f"톤 지정 없는 줄: {missing}")
    tests, rows, add_tests, add_rows = [], [], [], []

    def entry(fid, tag, role, text):
        emo, inten, tempo, note = TONE[tag]
        name, vid = VOICE[role]
        who = "내레이터" if role == "NA" else "진행자" if role == "OUT" else role
        test = {"id": fid, "model": "typecast-direct", "voice": vid, "language": "jpn", "text": kana(tag, text),
                "emotion_preset": emo, "emotion_intensity": inten, "tempo": tempo}
        return test, f"| {fid} | {tag} | {who} | {name} | {text} | {emo} | {inten} | {tempo} | {note} |"

    for n, (tag, role, text) in enumerate(lines, 1):
        fid = f"line{n:03d}"
        if tag in DELETED:
            rows.append(f"| {fid} | {tag} | 내레이터 | Lloyd | ~~{text}~~ | — | — | — | v1.1 삭제(녹음 보관·미사용) |")
            continue
        test, row = entry(fid, tag, role, text)
        tests.append(test)
        if tag in RETAKE:
            row += " **재녹음(보정)**"
            add_tests.append(test)
        rows.append(row)
    for tag, role, text in adds:
        test, row = entry(f"P{int(tag[1:]):02d}", tag, role, text)
        add_tests.append(test)
        add_rows.append(row)
    head = "| 녹음 | 대본 | 화자 | 목소리 | 일본어 | 감정 | 강도 | 템포 | 연기 메모(음성·표정·동작) |"
    md = ["# 『運転手のくせに』 줄별 톤 연출표 (규칙 8-2·제10장 7)", "",
          f"> 🔒 v1.1 동결 대본 기준 본녹음 {len(tests)}줄(+삭제 2줄 번호 유지) · 보강 {len(add_rows)}줄 · 재사용 3줄(OUT1·OUT3·OUT4 『明日から』 진행자). 지정 없는 줄 0개. 생성기: `build_tts_spec.py`.",
          "> 감정 프리셋 Typecast ssfm-v30(normal·happy·sad·angry·tonedown·toneup·whisper). **연기 메모의 표정·동작이 키프레임·i2v 동작 문장·립싱크 연기 지시의 원본이다**(감정 일치표가 대조).",
          "> 재사용: 후크 H1 = L11 · S18 드라이브 레코더 = L11·L14(스피커 필터).",
          "> 가나 변형(음성 입력만): " + " · ".join(f"{a}→{b}" for a, b in KANA if a not in "“”"), "",
          head, "|---|---|---|---|---|---|---|---|---|"] + rows + ["", "## v1.1 Lock 보강 녹음 (P01~P11, `untenshu-tts-add` — 재녹음 4줄과 같은 실행)", "",
          head, "|---|---|---|---|---|---|---|---|---|"] + add_rows
    open(os.path.join(HERE, "05_톤연출표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    spec = {"_설명": f"『運転手のくせに』 PHASE 1 본녹음 {len(tests)}줄(확정 캐스트, Typecast ssfm-v30 jpn). 음성 입력만 가나 변형, 자막은 한자. "
                    "line### = 시간 순서(v1.1 삭제 NA5·NA7 번호 유지). OUT1·OUT3·OUT4는 『明日から』 재사용. TTS 구독 크레딧만 사용. 생성: productions/untenshu-ja/build_tts_spec.py",
            "tc_model": "ssfm-v30", "language": "jpn", "tests": tests}
    json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "untenshu-tts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    add = {"_설명": f"『運転手のくせに』 v1.1 Lock 보강 {len(add_rows)}줄(P01~) + 발음 보정 재녹음 {len(add_tests) - len(add_rows)}줄(같은 line 번호). "
                   "build_lock.py는 이 폴더의 line###을 원본보다 우선한다. TTS 구독 크레딧만 사용. 생성: productions/untenshu-ja/build_tts_spec.py",
           "tc_model": "ssfm-v30", "language": "jpn", "tests": add_tests}
    json.dump(add, open(os.path.join(REPO, "scripts", "auditions", "untenshu-tts-add.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"본녹음 {len(tests)}줄 · 보강+재녹음 {len(add_tests)}줄 → scripts/auditions/untenshu-tts-add.json")


if __name__ == "__main__":
    main()
