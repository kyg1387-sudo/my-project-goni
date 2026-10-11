#!/usr/bin/env python3
"""『明日から来なくていい』 PHASE 1 본녹음 스펙 + 줄별 톤 연출표 생성기 (무료).

입력: 00_script_ja.md (🔒 동결 대본), 04_목소리추천.md의 확정 캐스트(아래 VOICE).
출력: scripts/auditions/ashita-tts.json (Typecast ssfm-v30 jpn, line### = 시간 순서),
      05_톤연출표.md (줄 번호 ↔ 대본 태그 ↔ 목소리 ↔ 감정·강도·템포).
가나 변형은 음성 입력에만 적용하고 자막은 한자를 유지한다.
OUT3(다음 작품 예고)은 문안 보류라 녹음 대상에서 뺀다. 후크 H1은 L22 녹음을 재사용한다.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

VOICE = {  # 04_목소리추천.md 확정 캐스트
    "NA": ("Lloyd", "tc_65681f21097fc4326ceb5e21"),
    "佐藤": ("Rex", "tc_6322940059d649937b97f326"),
    "田中": ("Takuya Murakami", "tc_63478295af3bab65523c3237"),
    "山本": ("Dean", "tc_673eb45cdc1073aef51e6b90"),
    "高橋": ("Poseidon", "tc_6a8f9d53322676d2f0934a21"),
    "森": ("Nanami Ichikawa", "tc_64a66e30679f68b9bf301edb"),
    "OUT": ("Yui Sato", "tc_629fe972013e90b4db213fd8"),
}

# 태그: (감정 프리셋, 강도, 템포, 연기 메모). 지정 없는 줄 0개(규칙 8-2) — 아래에서 검사한다.
TONE = {
    "NA0": ("tonedown", 1.0, 0.95, "미스터리, 「……の、はずだった」 앞 반 박자"),
    "NA1": ("normal", 1.0, 1.0, "차분한 도입"), "NA2": ("normal", 1.0, 1.0, "규모를 또렷하게"),
    "NA3": ("normal", 1.0, 1.0, "인물 소개, 존중"), "NA4": ("normal", 1.0, 0.95, "「平社員」에 무게"),
    "L01": ("happy", 0.7, 1.0, "걱정 섞인 밝음"), "L02": ("normal", 1.0, 0.95, "담담한 지론"),
    "L03": ("normal", 1.0, 0.95, "낮게 다짐"), "L04": ("normal", 1.0, 0.95, "존경, 작게"),
    "NA5": ("tonedown", 1.0, 1.0, "불길한 전환"), "NA6": ("normal", 1.0, 1.0, "「落下傘」에 경멸 한 방울"),
    "L05": ("toneup", 1.0, 1.05, "건성 인사, 이름을 일부러 헷갈림"), "L06": ("toneup", 1.0, 1.05, "가볍게 깔봄"),
    "L07": ("tonedown", 1.0, 0.9, "낮게 경고, 「人が死ぬぞ」에 힘"), "L08": ("happy", 0.8, 1.0, "비웃음 [Omni]"),
    "NA7": ("normal", 1.0, 1.0, "탐욕을 나열"), "L09": ("normal", 1.0, 1.05, "아무렇지 않게 지시"),
    "L10": ("sad", 0.8, 0.95, "망설임, 말끝 흐림"), "L11": ("tonedown", 1.0, 0.95, "낮게 압박, 「わかるよな？」 천천히"),
    "NA8": ("normal", 1.0, 1.0, "장치 이름 또박또박"), "NA9": ("tonedown", 1.0, 0.95, "「森の判子」에서 멈칫"),
    "L12": ("normal", 1.0, 0.95, "사실을 짚음"), "L13": ("toneup", 1.0, 1.05, "건성 반박"),
    "L14": ("angry", 0.8, 0.95, "억누른 분노 [Omni]"), "L15": ("happy", 0.8, 1.0, "깔보는 웃음 [Omni]"),
    "NA10": ("normal", 1.0, 1.0, "담담하게"), "NA11": ("tonedown", 1.0, 0.9, "저음 완급, 광고 직전 여운"),
    "NA12": ("tonedown", 1.0, 0.95, "카운트다운"), "L16": ("tonedown", 1.0, 0.95, "느긋한 위압"),
    "L17": ("normal", 1.0, 1.0, "보고하듯 단호"), "L18": ("angry", 0.7, 0.9, "결연, 「絶対に」에 힘 [Omni]"),
    "L19": ("tonedown", 1.0, 0.95, "차갑게 비꼼"), "L20": ("angry", 1.2, 1.1, "폭발"),
    "L21": ("angry", 1.2, 1.1, "고함 [Omni]"), "L22": ("angry", 1.0, 0.95, "천천히 즐기며 내리꽂음 [Omni·후크]"),
    "L23": ("tonedown", 1.0, 0.95, "사무적으로 잔인"), "L24": ("tonedown", 1.0, 0.85, "긴 침묵 뒤 낮게 [Omni]"),
    "L25": ("sad", 1.2, 0.9, "울먹임"), "L26": ("normal", 1.0, 0.9, "다정하게"),
    "L27": ("tonedown", 1.0, 0.9, "당부, 한 마디씩 [Omni]"), "L28": ("sad", 0.9, 0.9, "눈물 참고 약속"),
    "NA13": ("sad", 1.0, 0.95, "쓸쓸하게"), "NA14": ("normal", 1.0, 0.95, "시청자에게 직접 질문"),
    "L29": ("normal", 1.0, 0.95, "남 일처럼 담담"), "L30": ("tonedown", 1.0, 0.9, "조용한 신호"),
    "L31": ("happy", 1.0, 1.05, "들뜬 축배"), "L32": ("happy", 0.8, 0.95, "흡족"),
    "L33": ("normal", 1.0, 1.05, "귀찮다는 듯"), "L34": ("normal", 1.0, 1.0, "떨리지만 단호"),
    "L35": ("tonedown", 1.0, 1.0, "혀 차듯 포기"), "NA15": ("normal", 1.0, 1.0, "사실 전달"),
    "L36": ("toneup", 1.0, 1.1, "당황"), "L37": ("angry", 1.0, 1.1, "짜증"),
    "L38": ("toneup", 1.0, 1.1, "공포 섞인 보고"), "L39": ("sad", 1.0, 0.9, "얼어붙어 더듬음"),
    "NA16": ("tonedown", 1.0, 0.9, "저음 완급, 광고 직전 여운"),
    "NA17": ("normal", 1.0, 1.0, "진실 공개 시작"), "NA18": ("normal", 1.0, 1.0, "조건을 또박또박"),
    "NA19": ("normal", 1.0, 0.95, "「一秒たりとも」에 힘"), "L40": ("angry", 0.8, 1.05, "다급한 경고"),
    "L41": ("tonedown", 1.0, 0.9, "억지 허세"), "NA20": ("toneup", 1.0, 1.05, "폭발 순간"),
    "NA21": ("normal", 1.0, 0.95, "안도, 따뜻하게"), "L42": ("normal", 1.0, 0.95, "공식 선언"),
    "L43": ("normal", 1.0, 0.95, "냉정하게 통보"), "L44": ("angry", 0.8, 0.95, "단죄 [Omni]"),
    "L45": ("sad", 1.0, 0.9, "더듬는 변명"), "L46": ("angry", 0.9, 0.95, "일갈"),
    "L47": ("sad", 1.1, 0.9, "울며 애원 [Omni] — 1.3은 발음이 뭉개져 1.1"), "L48": ("tonedown", 1.0, 0.9, "차갑게 [Omni]"),
    "L49": ("tonedown", 1.0, 0.85, "서늘하게 [Omni]"), "NA22": ("normal", 1.0, 1.0, "결과 통보"),
    "NA23": ("normal", 1.0, 1.0, "단호하게"), "NA24": ("normal", 1.0, 1.0, "개인 타격, 마지막 한 방"),
    "L50": ("normal", 1.0, 0.95, "간절하게"), "L51": ("happy", 0.7, 0.9, "무뚝뚝한 따뜻함"),
    "NA25": ("normal", 1.0, 0.95, "여운"), "NA26": ("normal", 1.0, 0.9, "가장 느리게, 마무리"),
    "OUT1": ("happy", 1.0, 1.0, "밝게 감사"), "OUT2": ("happy", 1.0, 1.0, "질문은 또렷이"),
    "OUT4": ("happy", 1.0, 1.0, "손 흔들며 인사"),
}

KANA = [("大東", "だいとう"), ("佐藤誠", "佐藤まこと"), ("田中翔", "たなかしょう"), ("翔", "しょう"),
        ("森", "もり"), ("百億円", "ひゃくおくえん"), ("三億円", "さんおくえん"), ("第一種", "だいいっしゅ"),
        ("一秒", "いちびょう"), ("三度", "さんど"), ("七日", "なのか"), ("本部長", "ほんぶちょう"),
        ("“", ""), ("”", ""), ("『", ""), ("』", "")]


# 본녹음 언어 검사(run 509)에서 발음이 실제로 흔들린 줄만 줄 단위 가나 보정 후 재녹음(동음이의어 오인은 제외)
TAG_KANA = {
    "NA6": [("専務", "せんむ"), ("甥", "おい")],        # 「山本千鶴の愛知」로 들림
    "NA23": [("専務", "せんむ"), ("告訴", "こくそ")],    # 「千鶴」「ごそこ」로 들림
    "L06": [("二か月", "にかげつ")],                    # 「多か月」로 들림
    "L07": [("二か月", "にかげつ")],                    # 「二月」로 들림
    "NA9": [("判子", "はんこ")],                       # 「ハンチ」로 들림
    "L47": [("悪かった", "わるかった")],                 # 「おるかった」로 들림(울음 강도 1.3 → 1.1)
}


def kana(s):
    for a, b in KANA:
        s = s.replace(a, b)
    return s


def kana_tag(tag, s):
    for a, b in TAG_KANA.get(tag, []):
        s = s.replace(a, b)
    return kana(s)


def load():
    t = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 4-1.")[0]
    out = []
    for m in re.finditer(r"^\s+((?:NA|L|OUT)\d+)\s*([^\s:「(]*)[^「\n]*「(.+?)」", body, re.M):
        tag, spk, text = m.group(1), m.group(2), m.group(3)
        if tag == "OUT3":
            continue  # 다음 작품 예고 — 문안 보류
        role = "NA" if tag.startswith("NA") else "OUT" if tag.startswith("OUT") else spk
        out.append((tag, role, text))
    return out


def main():
    lines = load()
    missing = [tag for tag, _, _ in lines if tag not in TONE]
    if missing:
        raise SystemExit(f"톤 지정 없는 줄: {missing}")
    tests, rows = [], []
    for n, (tag, role, text) in enumerate(lines, 1):
        emo, inten, tempo, note = TONE[tag]
        name, vid = VOICE[role]
        tests.append({"id": f"line{n:03d}", "model": "typecast-direct", "voice": vid, "language": "jpn",
                      "text": kana_tag(tag, text), "emotion_preset": emo, "emotion_intensity": inten, "tempo": tempo})
        rows.append(f"| line{n:03d} | {tag} | {'내레이터' if role == 'NA' else '진행자' if role == 'OUT' else role} | {name} | "
                    f"{text} | {emo} | {inten} | {tempo} | {note} |")
    spec = {"_설명": f"『明日から来なくていい』 PHASE 1 본녹음 {len(tests)}줄 (확정 캐스트, Typecast ssfm-v30 jpn). "
                    "음성 입력만 가나 변형, 자막은 한자 유지. line### = 시간 순서. OUT3(예고)은 보류, 후크 H1은 L22 재사용. "
                    "TTS 구독 크레딧만 사용. 생성: productions/ashita-kara-ja/build_tts_spec.py",
            "tc_model": "ssfm-v30", "language": "jpn", "tests": tests}
    with open(os.path.join(REPO, "scripts", "auditions", "ashita-tts.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    md = ["# 『明日から来なくていい』 줄별 톤 연출표 (규칙 8-2)", "",
          f"> 🔒 동결 대본 기준 본녹음 {len(tests)}줄. 지정 없는 줄 0개. 생성기: `build_tts_spec.py` (대본·캐스트가 바뀌면 다시 실행).",
          "> 감정 프리셋은 Typecast ssfm-v30(normal·happy·sad·angry·tonedown·toneup·whisper). 장면 키프레임 표정도 같은 감정으로 맞춘다(규칙 7).",
          "> 가나 변형(음성 입력만): " + " · ".join(f"{a}→{b}" for a, b in KANA if b and a not in "“”『』"), "",
          "| 녹음 | 대본 | 화자 | 목소리 | 일본어 | 감정 | 강도 | 템포 | 연기 메모 |", "|---|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(HERE, "05_톤연출표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"본녹음 {len(tests)}줄 → scripts/auditions/ashita-tts.json, 05_톤연출표.md")


if __name__ == "__main__":
    main()
