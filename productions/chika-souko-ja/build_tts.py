#!/usr/bin/env python3
"""#02 『地下倉庫の伝票』 — 줄별 톤 연출표(05) + 본녹음 TTS 스펙(scripts/auditions/chika-tts.json) 생성기.

입력: 00_script_ja.md(대본 v2), 확정 캐스트(04_목소리오디션계획.md §9~12)
출력: 05_톤연출표.md, scripts/auditions/chika-tts.json, assets/auditions/chika-tts/ 에 오디션 재사용 파일 복사
규칙: CLAUDE.md 8-2(빈 줄 0개) · Typecast language=jpn 필수 · 음성 입력만 가나 변형(자막은 한자 유지)
"""
import json, os, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUD = os.path.join(REPO, "assets", "auditions")

CAST = {  # 확정 2026-10-08
    "NA": ("사오리(내레이션)", "tc_62b17ef6695ad26f7fb8e7f3"),
    "沙織": ("사오리", "tc_62b17ef6695ad26f7fb8e7f3"),
    "権藤": ("곤도", "tc_6465b87a4ee2060b333caf80"),
    "桐谷": ("기리타니", "tc_6620d223b5347631a920ba83"),
    "大河内": ("오코치", "tc_673eb45cdc1073aef51e6b90"),
    "宮本": ("미야모토", "tc_6a8f9d53322676d2f0934a21"),
    "진행자": ("진행자(#01 동일)", "tc_629fe972013e90b4db213fd8"),
}

# 가나 변형(음성 입력 전용). 긴 표기부터.
KANA = [
    ("権藤", "ごんどう"), ("桐谷", "きりたに"), ("大河内", "おおこうち"), ("沙織", "さおり"),
    ("吹き溜まり", "ふきだまり"), ("溶解処分", "ようかいしょぶん"), ("弔慰金", "ちょういきん"),
    ("登記簿", "とうきぼ"), ("印影", "いんえい"), ("空車率", "くうしゃりつ"),
    ("業務上横領", "ぎょうむじょうおうりょう"), ("懲戒解雇", "ちょうかいかいこ"),
    ("常務取締役", "じょうむとりしまりやく"), ("二十五万円", "にじゅうごまんえん"),
    ("三千万円", "さんぜんまんえん"), ("十億円", "じゅうおくえん"), ("百二十か月", "ひゃくにじゅっかげつ"),
    ("百二十枚", "ひゃくにじゅうまい"), ("午後十一時四十八分", "ごご、じゅういちじ、よんじゅうはっぷん"),
    ("簿記一級", "ぼきいっきゅう"), ("四十二ページ", "よんじゅうにページ"), ("手柄泥棒", "てがらどろぼう"),
    ("三十四歳", "さんじゅうよんさい"), ("八年", "はちねん"), ("七年前", "ななねんまえ"),
    ("七か所", "ななかしょ"), ("過去三年", "かこさんねん"), ("三か月", "さんかげつ"), ("三日後", "みっかご"),
    ("十年分", "じゅうねんぶん"), ("十年前", "じゅうねんまえ"), ("十年間", "じゅうねんかん"), ("十年", "じゅうねん"),
    ("地下二階", "ちかにかい"), ("三週間目", "さんしゅうかんめ"), ("半年間", "はんとしかん"), ("半年", "はんとし"),
    ("義理の父", "ぎりのちち"), ("ID", "アイディー"), ("毎月", "まいつき"),
]


def kana(text):
    s = text
    for a, b in KANA:
        s = s.replace(a, b)
    return s.replace("『", "").replace("』", "").replace("“", "").replace("”", "")


# 줄별 톤: 번호 → (감정, 강도, 속도, 앞 쉼, 뒤 쉼, 연기·표정 지시)  — 빈 줄 0개(규칙 8-2)
T = {
    1: ("tonedown", 1.0, 0.95, 0.3, 0.9, "냉정한 제지, 한 단어씩 / 표정: 무표정"),
    2: ("tonedown", 1.0, 0.95, 0.5, 0.4, "억눌린 회상, 담담하게"),
    3: ("tonedown", 1.1, 0.95, 0.3, 0.7, "모욕을 그대로 옮기는 차가움 — 뒤 0.7초 완전 정적"),
    4: ("tonedown", 1.3, 0.9, 0, 1.0, "콜드오픈 결정타, 낮게 눌러서 → 타이틀"),
    5: ("toneup", 1.0, 1.0, 0.3, 0.4, "단상의 과장된 자신감 / 표정: 턱 든 득의"),
    6: ("tonedown", 1.1, 0.95, 0.5, 0.5, "「私だ」에 힘, 억눌린 분노"),
    7: ("normal", 1.0, 1.0, 0.5, 0.4, "자기소개는 건조하게, 곤도 소개에 냉소"),
    8: ("sad", 0.8, 1.0, 0.3, 0, "억누른 분노, 끝을 삼킴 / 표정: 떨리는 입술"),
    9: ("normal", 1.0, 0.95, 0.3, 0.3, "비웃음, 가르치듯 / 표정: 입꼬리 비웃음 (오디션 재사용)"),
    10: ("normal", 1.0, 1.0, 0.3, 0.3, "무심한 명령조 / 어깨 너머"),
    11: ("normal", 1.0, 0.95, 0.4, 0.3, "당혹, 「え……？」 뒤 반 박자 / 표정: 당황"),
    12: ("tonedown", 1.2, 0.95, 0.3, 0.6, "낮게 협박, 「……次やったら」 앞 쉼 / 표정: 차가운 눈"),
    13: ("tonedown", 1.0, 0.95, 0.5, 0.5, "체념 → 「一つだけ」에서 결의"),
    14: ("happy", 1.0, 1.0, 0.3, 0.8, "조롱, 웃음 섞어 / 표정: 비웃음 — 썸네일 대사"),
    15: ("normal", 1.0, 0.9, 0.5, 0.4, "온화한 노인, 서민 말투 / 표정: 인자한 미소 (오디션 재사용)"),
    16: ("tonedown", 1.0, 1.0, 0.5, 0.4, "건조한 업무 설명"),
    17: ("tonedown", 1.1, 0.95, 0.3, 0.5, "「だが」에서 반격의 예고"),
    18: ("tonedown", 1.0, 0.9, 0.5, 0.6, "무심하게 던지는 폭탄 — 「権藤くん」에 무게"),
    19: ("tonedown", 1.3, 0.9, 0.5, 0.9, "발견의 전율, 「すべて――権藤」 앞 정적 — 1차 광고"),
    20: ("tonedown", 1.0, 0.9, 0.4, 0.3, "오래 참아 온 고백, 낮게"),
    21: ("sad", 0.8, 0.9, 0.3, 0.5, "쓴웃음 섞인 회한"),
    22: ("tonedown", 1.2, 0.95, 0.5, 0.6, "조용하지만 단단한 결의 / 표정: 굳은 눈"),
    23: ("normal", 1.0, 0.95, 0.4, 0.6, "숫자를 또렷이 — 「三千万円」 앞 반 박자"),
    24: ("tonedown", 1.0, 0.95, 0.5, 0.3, "의심 → 기억이 떠오르는 전환"),
    25: ("tonedown", 1.3, 0.9, 0.3, 0.7, "「……妻の、実家だった」 낮게 떨어뜨림"),
    26: ("normal", 1.0, 0.95, 0.5, 0.3, "시각을 또박또박"),
    27: ("tonedown", 1.2, 0.95, 0.3, 0.6, "「同じ夜、同じ時刻」 한 마디씩, 확신"),
    28: ("sad", 0.8, 0.9, 0.8, 0.8, "불안, 작고 낮게"),
    29: ("tonedown", 1.3, 0.9, 0.3, 0.4, "어둠 속 위협, 낮고 느리게 / 역광 실루엣"),
    30: ("sad", 0.8, 0.95, 0.4, 0.4, "떨림을 누르는 대답 / 표정: 굳은 얼굴, 눈만 흔들림"),
    31: ("tonedown", 1.3, 0.9, 0.3, 0.6, "협박, 「……お前の居場所も」 앞 쉼"),
    32: ("whisper", 1.0, 0.9, 0.8, 0.6, "다정한 속삭임, 안심시키듯"),
    33: ("happy", 1.3, 1.05, 0.2, 0.3, "들뜬 고함, 축배 / 표정: 득의만면"),
    34: ("happy", 1.0, 1.0, 0.3, 0.3, "탐욕스러운 웃음, 「年収は倍だ」에 힘"),
    35: ("happy", 0.8, 1.0, 0.3, 0.5, "비웃는 명령 / 부하 어깨 너머"),
    36: ("happy", 1.0, 1.0, 0.12, 0.3, "폭소 효과음(B) 꼬리에 이어서 — 확정 소스 재사용"),
    37: ("normal", 1.0, 0.95, 0.3, 0.7, "모욕, 느물거리며 / 어깨 너머 — 뒤 0.7초 정적"),
    38: ("tonedown", 1.0, 0.95, 0.3, 0.9, "#1 재사용(같은 대사) — 2차 광고"),
    39: ("angry", 1.2, 1.05, 0.2, 0.3, "당황한 허세, 목소리 높임 / 표정: 눈 커진 당황"),
    40: ("tonedown", 1.0, 0.95, 0.3, 0.4, "냉정한 선고, 한 마디씩 (오디션 재사용)"),
    41: ("normal", 1.0, 0.95, 0.3, 0.4, "혐의 낭독, 숫자 또렷이 (오디션 재사용, 「…不正送金。」에서 컷 분할)"),
    42: ("tonedown", 1.0, 0.95, 0.4, 0.4, "증거 나열, 건조하게 / 보고서 인서트 위"),
    43: ("normal", 1.0, 0.95, 0.4, 0.5, "누명 해소 선언, 담담하게 / 사오리 리액션 위"),
    44: ("angry", 1.4, 1.1, 0.2, 0.2, "핏대 선 절규 / 표정: 일그러진 분노"),
    45: ("angry", 1.5, 1.0, 0.1, 0.4, "목이 쉬도록 — 무너지는 절규 (오디션 재사용)"),
    46: ("tonedown", 1.0, 0.95, 0.5, 0.6, "짧은 의심 — 마지막 불안 (오디션 재사용)"),
    47: ("normal", 1.0, 0.95, 0.3, 0.3, "흔들림 없이 또렷하게 / 표정: 정면 응시"),
    48: ("tonedown", 1.0, 0.95, 0.3, 0.5, "사실만 담담하게"),
    49: ("tonedown", 1.0, 0.9, 0.4, 0.4, "조용히 꾸짖듯 / 표정: 엄한 눈"),
    50: ("tonedown", 1.2, 0.95, 0.3, 0.4, "콜백①, 「……証拠なら」 앞 쉼"),
    51: ("tonedown", 1.2, 0.9, 0.4, 0.8, "낮게 최후통첩 — 썸네일 B (「紙」 억양 재녹음 + 대안)"),
    52: ("tonedown", 1.0, 0.95, 0.5, 0.3, "차분한 위압 (오디션 재사용)"),
    53: ("normal", 1.0, 0.95, 0.3, 0.6, "추궁 (오디션 재사용)"),
    54: ("sad", 1.0, 1.0, 0.3, 0.4, "더듬으며 무너짐, 말끝 흐림 / 무릎 꿇은 정수리"),
    55: ("normal", 1.0, 0.95, 0.4, 0.3, "현장의 자부심, 또렷하게"),
    56: ("tonedown", 1.1, 0.95, 0.3, 0.5, "콜백②, 「でしたよね」에 냉소"),
    57: ("happy", 0.7, 0.95, 0.5, 0.5, "처음으로 미소, 여유 (오디션 재사용)"),
    58: ("tonedown", 1.4, 0.9, 0.5, 1.0, "최종 결정타, 한 단어씩 눌러서 / 내려다보는 시선 — 뒤 1초 정적"),
    59: ("tonedown", 1.0, 0.95, 0.4, 0.5, "처분 통보, 사무적으로 / 연행 롱샷 위"),
    60: ("normal", 1.0, 0.95, 0.5, 1.0, "결과 보고, 통쾌함은 절제 → 「一か月後」"),
    61: ("happy", 0.8, 0.9, 0.5, 0.3, "장난스러운 인사"),
    62: ("happy", 0.8, 0.95, 0.3, 0.5, "웃으며, 그리움 섞어"),
    63: ("sad", 0.8, 0.9, 0.6, 0.8, "먼 곳을 보는 여운 (오디션 재사용)"),
    64: ("tonedown", 1.0, 0.9, 0.5, 0.5, "회상, 담담하게"),
    65: ("normal", 1.0, 0.9, 0.4, 1.0, "주제, 따뜻하고 단단하게 — 가장 느리게"),
    66: ("normal", 1.0, 1.0, 0.5, 0.4, "아웃트로 인사, 정중하게 (#01 재사용)"),
    67: ("happy", 1.0, 1.0, 0.4, 0.4, "구독 요청, 밝게 (#01 재사용) / 버튼 오버레이"),
    68: ("happy", 1.0, 1.0, 0.5, 0.4, "시청자 질문, 친근하게 / 허리 위"),
    69: ("happy", 1.0, 1.0, 0.4, 0, "작별 인사 (#01 재사용) → 손 흔들기"),
}

# 오디션 파일 재사용(대본 문장과 동일 + 같은 목소리) — 재생성 0
REUSE = {
    9: "chika-gondo-voice/gondo_Shinwook_1_sneer.mp3",
    15: "chika-okochi-miyamoto/miyamoto_Poseidon_1_greet.mp3",
    36: "chika-gondo-laugh/gondo_S13_line_happy.mp3",
    40: "chika-kiritani-voice/kiritani_ChunsikKang_1_dismiss.mp3",
    41: "chika-kiritani-voice/kiritani_ChunsikKang_2_charge.mp3",
    45: "chika-gondo-voice/gondo_Shinwook_3_scream.mp3",
    46: "chika-kiritani-voice/kiritani_ChunsikKang_3_doubt.mp3",
    52: "chika-okochi-miyamoto/okochi_Dean_1_question.mp3",
    53: "chika-okochi-miyamoto/okochi_Dean_2_basis.mp3",
    57: "chika-okochi-miyamoto/okochi_Dean_3_smile.mp3",
    63: "chika-okochi-miyamoto/miyamoto_Poseidon_3_keep.mp3",
}
SAME_AS = {38: 1}
REUSE_EXT = {66: "tower line062", 67: "tower line063", 69: "tower line065"}  # #01 채널 공통 진행자 녹음(assets/auditions/chika-tts/에 복사됨, 재생성 0)  # 같은 대사·같은 컷 재사용
# 대안 녹음: 줄 번호 → (접미사, 입력문, 감정, 강도)
ALT = {51: ("v2", "……その、かみが。あんたの破滅だよ、ごんどうくん", "tonedown", 1.0)}


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


def main():
    lines = load_lines()
    assert len(lines) == len(T), f"대본 {len(lines)}줄 ↔ 톤표 {len(T)}줄 불일치"
    assert all(spk != "진행자" or n in REUSE_EXT or n == 68 for n, sc, tag, spk, omni, text in lines)
    tests, rows, chars = [], [], 0
    out_dir = os.path.join(AUD, "chika-tts")
    os.makedirs(out_dir, exist_ok=True)
    for n, sc, tag, spk, omni, text in lines:
        emo, inten, tempo, pre, post, note = T[n]
        name, vid = CAST[spk]
        lid = f"line{n:03d}"
        src = "신규"
        if n in SAME_AS:
            src = f"#{SAME_AS[n]} 재사용"
        elif n in REUSE_EXT:
            src = f"#01 {REUSE_EXT[n]} 재사용"
        elif n in REUSE:
            src = "오디션 재사용"
            shutil.copyfile(os.path.join(AUD, REUSE[n]), os.path.join(out_dir, f"{lid}.mp3"))
        else:
            t = {"id": lid, "model": "typecast-direct", "voice": vid, "language": "jpn",
                 "text": kana(text), "subtitle": text, "emotion_preset": emo,
                 "emotion_intensity": inten, "tempo": tempo}
            tests.append(t); chars += len(t["text"])
            if n in ALT:
                suf, alt_text, aemo, aint = ALT[n]
                tests.append({**t, "id": f"{lid}_{suf}", "text": alt_text, "emotion_preset": aemo,
                              "emotion_intensity": aint})
                chars += len(alt_text)
        rows.append(f"| {n} | {sc} | {name} | {'OMNI' if omni else '-'} | {text} | {emo} {inten} | {tempo} | {pre} | {post} | {note} | {src} |")
    spec = {"_설명": "#02 본녹음(PHASE 1). build_tts.py 생성물 — 직접 고치지 말 것.",
            "tc_model": "ssfm-v30", "language": "jpn", "tests": tests}
    json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "chika-tts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    md = ["# #02 『地下倉庫の伝票』 줄별 톤 연출표 (규칙 8-2 — 빈 줄 0개)", "",
          f"> 생성: `build_tts.py` · 캐스트 확정 2026-10-08 · 전체 {len(lines)}줄(신규 녹음 {len(tests)}개 / 약 {chars}자, 오디션 재사용 {len(REUSE)}줄, 동일 컷 재사용 {len(SAME_AS)}줄)",
          "> 쉼(초) = Lock 타임라인 배치값. 음성 입력은 가나 변형(§6), 자막은 대본 원문.", "",
          "| # | 장면 | 화자 | 립싱크 | 대사(자막) | 감정 | 속도 | 앞 쉼 | 뒤 쉼 | 연기·표정 지시 | 음성 |",
          "|---|---|---|---|---|---|---|---|---|---|---|", *rows, ""]
    open(os.path.join(HERE, "05_톤연출표.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"{len(lines)}줄 / 신규 {len(tests)}개 / {chars}자 / 재사용 {len(REUSE) + len(SAME_AS)}줄")


if __name__ == "__main__":
    main()
