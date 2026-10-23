#!/usr/bin/env python3
"""『時給5万円の罠』(yamibaito-ja) PHASE 1 — 줄별 톤 연출표(05) + 본녹음 TTS 스펙(scripts/auditions/yamibaito-tts.json) 생성기 (무료).

입력: 00_script_ja.md(대본 v3 🔒), 배역 대장 scripts/audio/yamibaito-cast-voices.json(고니감독님 청취 확정 2026-10-24)
출력: 05_톤연출표.md, scripts/auditions/yamibaito-tts.json (line### = 대본 순서)
엔진: 전 배역·내레이터 = ElevenLabs eleven_v3(영어 연기 태그 2~4단어, 대사 앞) · 진행자 = Typecast ssfm-v30 jpn(제19장 2 ⑤)
규칙: 톤 지정 없는 줄 0개 · 한 문장 ≤30자 · 한 줄 ≤2문장(제14장 8) · 음성 입력은 가나 치환본, subtitle은 대본 원문
사용법: python3 productions/yamibaito-ja/build_tts.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CAST_JSON = json.load(open(os.path.join(REPO, "scripts", "audio", "yamibaito-cast-voices.json"), encoding="utf-8"))

CAST = {"NA": ("내레이터", "narr"), "健太": ("健太", "kenta"), "悠斗": ("悠斗", "yuto"), "男": ("男", "otoko"),
        "店長": ("店長", "tencho"), "母": ("母", "haha"), "警察官": ("警察官", "keisatsu"), "진행자": ("진행자", "host")}
SAME_AS = {"L00": "L08"}  # 후크의 「ここに、出口はない」 = S05 L08 녹음 재사용
SKIP = {"OUT0", "OUT5"}   # 무언 몽타주·예고 카드

# 태그: (EL 연기 태그 또는 Typecast (감정, 강도, 템포), 연기 메모 = 표정·동작의 단일 출처, 제10장 7)
N = lambda tag, note: (tag, note)
T = {
    # 내레이터 Hatake — 3인칭 です・ます, 차갑고 낮게·객관적. 세기는 속도·침묵으로
    "NA0": N("[low, cold, slow]", "후크. 숫자만 또렷이, 뒤에 심장 박동"),
    "NA1": N("[low, ominous, trailing off]", "후크. 「一週間後」에서 끊어 여운"),
    "NA2": N("[calm, detached]", "장소 제시, 담담"), "NA3": N("[calm, detached]", "인물 소개, 이름·나이 또렷이"),
    "NA4": N("[calm, matter-of-fact]", "일상 묘사"), "NA8": N("[quiet, foreboding]", "「普通の青年」 뒤에 반 박자"),
    "NA9": N("[low, suspenseful]", "DM 도착, 톤 한 단계 낮춤"), "NA10": N("[measured, reading out]", "DM 조건을 읽듯 또박또박"),
    "NA11": N("[measured, reading out]", "「現金」에 무게"), "NA12": N("[flat, skeptical]", "「おかしな話」 건조하게"),
    "NA13": N("[calm, matter-of-fact]", "켄타의 첫 반응"), "NA6": N("[flat, cold]", "잔고 숫자, 감정 없이"),
    "NA5": N("[quiet, heavy]", "「遅れていました」 무겁게"), "NA7a": N("[quiet, heavy]", "「借金」에 무게"),
    "NA7b": N("[flat, cold]", "「十五年」 건조하게"), "NA7": N("[quiet, bitter]", "SNS, 약간 씁쓸하게"),
    "NA14": N("[low, slow, knowing]", "주제문 ①, 느리게"), "NA16": N("[low, suspicious]", "조건 도입, 톤 낮춤"),
    "NA17": N("[clipped, counting]", "ひとつ — 끊어 읽기"), "NA18": N("[clipped, counting]", "ふたつ — 끊어 읽기"),
    "NA19": N("[clipped, colder]", "みっつ — 「家族にも」 가장 차갑게"), "NA20": N("[hushed, uneasy]", "「おかしい」 반복, 속삭이듯"),
    "NA21": N("[low, slow, knowing]", "주제문 ②, 「鈍らせます」 느리게"), "NA22": N("[flat, final]", "버튼, 단정적으로"),
    "NA15": N("[quiet, direct, slow]", "시청자에게 1회 질문 — 가장 느리게, 뒤 1.0초 여운"),
    "NA23": N("[low, uneasy]", "출발 전날 밤"), "NA24": N("[quiet, curious]", "번호 검색"), "NA24a": N("[quiet]", "「相談窓口」 짧게"),
    "NA24b": N("[low, regretful, slow]", "「かけませんでした」 — 복선, 여운 0.8초"),
    "NA25a": N("[quiet, heavy]", "「最後の普通の会話」 무겁게"), "NA25d": N("[calm, matter-of-fact]", "짐"),
    "NA25e": N("[quiet, foreboding]", "「戻るつもり」 — 복선"), "NA25b": N("[low, ominous]", "약속의 밤"),
    "NA25c": N("[low, slow, ominous]", "왕박스카, 「音もなく」 느리게"),
    "NA25": N("[low, slow, suspenseful]", "1차 광고 직전, 끝을 가장 느리게 → 0.8초 여운"),
    "NA26": N("[hushed, tense]", "차 안, 숨죽여"), "NA27": N("[hushed, tense]", "「一言も」 짧게"),
    "NA27a": N("[hushed, observing]", "떨리는 손"), "NA27b": N("[quiet]", "짧게"), "NA27c": N("[low, uneasy]", "「いけない気が」 여운"),
    "NA28": N("[low, slow]", "빛이 사라짐, 느리게"), "NA29": N("[flat, clipped]", "한 시간, 짧게"),
    "NA30": N("[low, cold, slow]", "「完全な闇」 가장 낮게"), "NA31": N("[low, observing]", "도착"),
    "NA32": N("[flat, clipped]", "간판 없음·쇠창살, 끊어 읽기"), "NA33": N("[hushed, sensory]", "쇠 냄새, 속삭이듯"),
    "NA34": N("[low, slow, final]", "철문, 「閉まっていました」 느리고 무겁게"),
    "NA35": N("[low, cold]", "「アルバイト先では」 차갑게"), "NA36": N("[low, grave]", "「収容所」 무겁게"),
    "NA37": N("[flat, reading out]", "통장 정리"), "NA38": N("[flat, reading out]", "짐 분류"),
    "NA39": N("[low, heavy]", "16시간, 「ほとんど」 무겁게"), "NA39a": N("[flat, clipped]", "식사·바닥, 끊어 읽기"),
    "NA39b": N("[low, slow]", "카메라, 「一瞬も」 느리게"), "NA40": N("[low, slow, grave]", "주제문 ③ — 「命の値段」 가장 느리게"),
    "NA41": N("[hushed, chilling]", "실종, 속삭이듯 차갑게"), "NA42": N("[hushed, chilling]", "「口にしません」 여운"),
    "NA43a": N("[low, sorrowful]", "무너지는 마음"), "NA43b": N("[quiet, turning]", "「気づいていました」 — 전환, 톤 살짝 올림"),
    "NA43c": N("[quiet, precise]", "3시·5분 또렷이"), "NA43d": N("[quiet, precise]", "비상계단, 복선"),
    "NA43": N("[low, slow, suspenseful]", "2차 광고 직전, 「ありませんでした」 가장 느리게 → 0.8초"),
    "NA44": N("[hushed, tense, precise]", "시각 또렷이, 숨죽여"), "NA45": N("[low, firm]", "「決めました」 단호하게"),
    "NA45a": N("[hushed, tense]", "감시자 외출"), "NA45b": N("[hushed, tense]", "열쇠"),
    "NA46": N("[tense, faster]", "추격 — 템포 올림"), "NA47": N("[firm, breathless]", "「振り返りませんでした」"),
    "NA48": N("[driving, breathless]", "달리고 달리고 — 리듬"), "NA48a": N("[breathless, fading]", "기억나지 않음"),
    "NA48b": N("[quiet, relief]", "편의점 불빛 — 안도"), "NA49": N("[low, slow, meaningful]", "복선 회수, 느리게"),
    "NA50": N("[firm, quiet]", "「迷いませんでした」 단단히"), "NA50a": N("[hushed, trembling]", "떨리는 손"),
    "NA50b": N("[quiet, relief]", "장소 특정"), "NA51": N("[low, building]", "「一時間後」 — 급습 예고"),
    "NA52": N("[firm, driving]", "급습, 힘 있게"), "NA53": N("[firm, cold justice]", "체포, 단정적"),
    "NA54": N("[measured]", "27명 또렷이"), "NA54b": N("[firm, warm]", "「被害者として」 단단히"),
    "NA54a": N("[quiet, heavy]", "18세 소년, 무겁게"), "NA55": N("[quiet, warm]", "悠斗 — 안도"),
    "NA56": N("[measured, resolving]", "뉴스, 해결"), "NA57": N("[quiet, warm]", "목숨을 되찾음"),
    "NA58": N("[quiet, heavy]", "상처, 「消えていません」 여운"), "NA58a": N("[calm, gentle]", "현재"),
    "NA58b": N("[quiet, tender]", "어머니에게 말하지 않음 — 여운"), "NA59": N("[low, slow]", "주제문 ④"),
    "NA60": N("[low, grave]", "「大きな悪意」 무겁게"), "NA61": N("[firm, plain]", "「ありません」 단정"),
    "NA62": N("[low, slow, warning]", "지금 이 순간에도 — 경고"), "NA63": N("[gentle, direct]", "행동 요청 ①"),
    "NA64": N("[gentle, sincere]", "행동 요청 ② 「どうか」 진심"), "NA65": N("[clear, measured]", "#9110 — 번호 또렷이"),
    "NA66": N("[warm, slow]", "평범한 일상"), "NA67": N("[warm, gentle ending]", "주제문, 가장 느리게"),
    # 健太 Hadou — 불안·궁핍, 절제. 외침 없음
    "L01": N("[whispering, stunned]", "폰을 보며 속삭임 [Omni]"),
    "L02": N("[low, convincing himself]", "자신에게 말하듯, 눈은 불안 [Omni]"),
    "L04": N("[forced cheerful, strained]", "억지로 밝게, 눈은 웃지 않음 [Omni]"),
    "L10": N("[muttering, hollow]", "고개 숙인 채 [VO]"),
    "L14": N("[trembling whisper, afraid]", "젖은 눈·흐르지 않음, NOT smiling [Omni]"),
    "L16": N("[breathless, pleading]", "수화기, 숨 가쁨 [VO]"), "L16a": N("[breathless, urgent]", "공장 설명 [VO]"),
    "L20": N("[quiet, choked, half laugh]", "悠斗 어깨 너머 뒷모습 [VO]"),
    "L22": N("[quiet, tender, holding back]", "젖은 눈, 웃지 않고 조용히 [Omni]"),
    # 悠斗 Mizu — 체념·자조 → 재회 오열
    "L09": N("[whispering, dry]", "입만 움직이는 속삭임, 어깨 너머 [Omni]"),
    "L11": N("[low, hollow, bitter]", "자조, 눈은 작업대 [Omni]"),
    "L12": N("[whispering, quick, nervous]", "눈만 빠르게 [Omni]"), "L13": N("[whispering, lower]", "더 낮게 [Omni]"),
    "L13a": N("[whispering, defeated]", "눈을 내리깔고 [Omni]"),
    "L19": N("[choked up, tearful]", "젖은 눈·흐르지 않음(흐름은 다음 i2v 컷), NOT smiling [Omni]"),
    # 男 Henry — 낮고 무표정, 고함 없음(외침은 L15만 VO)
    "L06": N("[cold, flat, low]", "조수석에서 돌아보지 않음 [VO]"), "L06a": N("[cold, clipped]", "짧게 [VO]"),
    "L07": N("[cold, flat, slow]", "무표정 가슴 위 CU [Omni]"), "L08": N("[quiet menace, slow]", "눈만 健太에게 [Omni] — 후크 L00에 재사용"),
    "L00": N("[quiet menace, slow]", "후크 재사용(L08 녹음) [VO]"),
    "L08a": N("[cold, bored]", "책상 사이 뒷모습 [VO]"), "L15": N("[shouting, distant]", "멀리서 고함 — 화면은 손 [VO]"),
    # 店長 Takumi — 짧고 묵직하게 따뜻
    "L17": N("[calm, warm, low]", "카운터 너머 3/4 [Omni]"), "L17a": N("[steady, protective]", "문 쪽을 한 번 보고 [Omni]"),
    "L17b": N("[grave, realizing]", "창밖 어둠 쪽 [Omni]"),
    # 母 Koharu — 전화 너머
    "L03": N("[warm, motherly]", "전화 너머 EQ [VO]"), "L05": N("[gentle, a little worried]", "[VO]"),
    "L21": N("[gentle, worried, soft]", "결말 전화 [VO]"),
    # 警察官 Anton
    "L18": N("[commanding shout]", "철문 너머 — 화면은 빛줄기 [VO]"),
    # 진행자 Yui Sato (Typecast)
    "OUT1": (("normal", 1.0, 0.95), "가슴 위 CU, 정중하게 [Omni]"),
    "OUT2": (("normal", 1.0, 0.92), "질문, 진지하게 [Omni]"),
    "OUT3": (("normal", 0.9, 0.95), "댓글 부탁 [Omni]"),
    "OUT4": (("happy", 0.9, 1.0), "구독 요청, 밝게 [Omni]"),
}

KANA = sorted(CAST_JSON["kana"].items(), key=lambda kv: -len(kv[0]))
KANA += [("「", ""), ("」", "")]
KANA.sort(key=lambda kv: -len(kv[0]))


def kana(s):
    for a, b in KANA:
        s = s.replace(a, b)
    return s


def load():
    body = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read().split("## 4. 대본")[1].split("## 5.")[0]
    out = []
    for m in re.finditer(r"^\s*((?:NA|L|OUT)\d+[a-z]?)\s*([^\s:「\[]*)\s*(\[[^\]]*\])?[^\n]*?:「(.*)」\s*$", body, re.M):
        tag, spk, mode, text = m.group(1), m.group(2), (m.group(3) or ""), m.group(4)
        if tag in SKIP:
            continue
        spk = "NA" if tag.startswith("NA") else spk
        out.append((tag, spk, "Omni" in mode, text))
    return out


def check_length(tag, text):
    w = []
    sents = [x for x in re.split(r"(?<=[。！？])", text) if x.strip()]
    if len(sents) > 2:
        w.append(f"{tag}: 한 줄 {len(sents)}문장")
    for x in sents:
        n = len(re.sub(r"[「」\s、。！？…]", "", x))
        if n > 30:
            w.append(f"{tag}: {n}자 문장")
    return w


def main():
    lines = load()
    warns = [f"{t}: 톤 지정 없음" for t, _, _, _ in lines if t not in T]
    warns += [f"{t}: 화자 표기 미등록 {s}" for t, s, _, _ in lines if s not in CAST]
    if warns:
        sys.exit("\n".join(warns))
    roles = CAST_JSON["roles"]
    tests, rows, chars_el, chars_tc, idmap = [], [], 0, 0, {}
    for n, (tag, spk, omni, text) in enumerate(lines, 1):
        warns += check_length(tag, text)
        tone, note = T[tag]
        name, role = CAST[spk]
        lid = f"line{n:03d}"
        idmap[tag] = lid
        r = roles[role]
        if tag in SAME_AS:
            src = f"{SAME_AS[tag]} 녹음 재사용"
        elif isinstance(tone, tuple):
            emo, inten, tempo = tone
            tests.append({"id": lid, "model": "typecast-direct", "voice": r["voice_id"], "language": "jpn",
                          "text": kana(text), "subtitle": text, "emotion_preset": emo,
                          "emotion_intensity": inten, "tempo": tempo})
            chars_tc += len(text); src = f"Typecast {r['name']}"
        else:
            tests.append({"id": lid, "model": "elevenlabs-direct", "voice": r["voice_id"], "voice_name": r["name"],
                          "el_model": "eleven_v3", "text": f"{tone} {kana(text)}", "subtitle": text})
            chars_el += len(text) + len(tone) + 1; src = f"EL {r['name']}"
        tone_s = tone if isinstance(tone, str) else f"{tone[0]} {tone[1]} · tempo {tone[2]}"
        rows.append(f"| {n} | {tag} | {name} | {'Omni' if omni else '-'} | {text} | {tone_s} | {note} | {src} |")
    for tag, src_tag in SAME_AS.items():
        rows.append(f"| — | {tag} | 재사용 | | | | {src_tag}({idmap[src_tag]}) 음성을 후크 H2에 배치 | |")
    spec = {"_설명": f"『時給5万円の罠』 본녹음(PHASE 1). build_tts.py 생성물 — 직접 고치지 말 것. EL {chars_el}자 · Typecast {chars_tc}자, fal 0.",
            "tts_model": "ssfm-v30", "language": "jpn", "tests": tests}
    json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "yamibaito-tts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    md = ["# 『時給5万円の罠』 줄별 톤 연출표 (PHASE 1 — 음성·표정·동작의 단일 출처, 제10장 7)", "",
          f"> build_tts.py 생성물. 녹음 {len(tests)}줄(EL {chars_el}자 · Typecast {chars_tc}자) + 재사용 {len(SAME_AS)}줄. "
          "EL 태그 = eleven_v3 연기 태그(영어 2~4단어, 대사 앞). 음성 입력은 가나 치환본, 자막은 대본 원문. 원칙: 세기는 속도·침묵·효과음으로, 목소리는 낮게(외침은 VO만).", "",
          "| # | 태그 | 화자 | 립싱크 | 대사 | 톤 | 연기 메모(표정·동작) | 목소리 |", "|---|---|---|---|---|---|---|---|"] + rows
    if warns:
        md += ["", "## 경고", ""] + [f"- {w}" for w in warns]
    open(os.path.join(HERE, "05_톤연출표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"녹음 {len(tests)}줄 · EL {chars_el}자 · Typecast {chars_tc}자 · 경고 {len(warns)}")
    for w in warns:
        print(" -", w)


if __name__ == "__main__":
    main()
