#!/usr/bin/env python3
"""『63ヘルツ』(soukaion-ja) PHASE 1 — 줄별 톤 연출표(05) + 본녹음 TTS 스펙(scripts/auditions/soukaion-tts.json) 생성기 (무료).

입력: 00_script_ja.md(대본 v3 🔒), 배역 대장 scripts/audio/soukaion-cast-voices.json(고니감독님 청취 확정 2026-10-24)
출력: 05_톤연출표.md, scripts/auditions/soukaion-tts.json (line### = 대본 순서)
엔진: 전 배역·내레이터 = ElevenLabs eleven_v3(영어 연기 태그 2~4단어, 대사 앞) · 진행자 = Typecast ssfm-v30 jpn(제19장 2 ⑤)
규칙: 톤 지정 없는 줄 0개 · 한 문장 ≤30자 · 한 줄 ≤2문장(제14장 8) · 음성 입력은 가나 치환본, subtitle은 대본 원문
사용법: python3 productions/soukaion-ja/build_tts.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CAST_JSON = json.load(open(os.path.join(REPO, "scripts", "audio", "soukaion-cast-voices.json"), encoding="utf-8"))

CAST = {"NA": ("美咲(내레이션)", "misaki"), "美咲": ("美咲", "misaki"), "結衣": ("結衣", "yui"), "黒木": ("黒木", "kuroki"),
        "大野": ("大野", "ohno"), "弁護士": ("弁護士", "bengoshi"), "警察官": ("警察官", "keisatsu"), "管理会社": ("管理会社", "kanri"),
        "진행자": ("진행자", "host")}
SAME_AS = {"L11": "L02"}  # S03b 黒木 「お前らが出ていけよ」 = 후크 H2 L02 녹음 재사용
SKIP = {"OUT0", "OUT5"}   # 무언 몽타주·엔드카드
EXTRA_ID = {}

# 태그: (EL 연기 태그 또는 Typecast (감정, 강도, 템포), 연기 메모 = 표정·동작의 단일 출처, 제10장 7)
# 발성 디렉션 표준(제20장 7): 내레이션(美咲 1인칭 회고)은 감정 배제·낮고 담담, 다큐 호흡. 대사는 숨 삼킴·속삭임, 외침 0줄.
N = lambda tag, note: (tag, note)
T = {
    # ── 美咲 내레이션(1인칭 だ・である) — 낮고 침착, 세기는 속도·침묵으로
    "NA0": N("[low, flat, slow]", "후크. 「地獄」를 세게 말하지 않고 낮게"),
    "NA1": N("[low, quiet]", "후크 결말 선행 ①"), "NA2": N("[low, steady, slow]", "후크 결말 선행 ② 「一週間で」 또렷이"),
    "NA3": N("[calm, tired]", "아침 7시, 피로가 밴 담담함"), "NA4": N("[calm, matter-of-fact]", "자기소개, 숫자 또렷이"),
    "NA5": N("[calm, warm]", "딸 이야기, 아주 조금 온기"), "NA6": N("[quiet, heavy]", "「貯められていなかった」 무겁게"),
    "NA7": N("[calm, low]", "22:50, 하루의 유일한 휴식"), "NA8": N("[low, flat, precise]", "「十一時ちょうど」 또렷이"),
    "NA9": N("[quiet, heavy]", "딸의 해석, 느리게"), "NA10": N("[quiet, bitter]", "「否定できなかった」 씁쓸하게"),
    "NA11": N("[flat, clipped]", "「三回」 짧게"), "NA12": N("[low, cold]", "「大きくなった」 차갑게"),
    "NA13": N("[flat, dry]", "뜯긴 종이, 건조하게"), "NA14": N("[flat, clipped]", "숫자만"),
    "NA15": N("[quiet, heavy]", "「二度」 무겁게 — 직업 리스크"), "NA16": N("[low, firm]", "「仕事ではない」 단단히"),
    "NA16a": N("[flat, listing, tired]", "하루 루틴을 나열하듯, 끝에 피로"),
    "NA17": N("[quiet, slow]", "「一行」 뒤 반 박자"), "NA18": N("[low, resolved]", "「四階へ」 결심"),
    "NA19": N("[hushed, tense]", "402호 앞, 숨죽여"), "NA20": N("[low, heavy]", "새벽 2시까지, 무겁게"),
    "NA21": N("[quiet, trembling edge]", "「声を出した」 — 떨림의 가장자리만"),
    "NA22": N("[low, slow, turning]", "1차 광고 직전, 끝을 가장 느리게 → 0.8초 여운"),
    "NA23": N("[calm, low]", "大野 소개"), "NA24": N("[measured]", "「三十八年間」 또렷이"), "NA24a": N("[quiet, warm]", "「私の壁でもある」 — 온기"),
    "NA25a": N("[quiet, slow]", "「分かっていなかった」 복선, 느리게"), "NA25": N("[calm, matter-of-fact]", "측정기 설치"),
    "NA26": N("[hushed, precise]", "「ちょうど」 또렷이"), "NA26a": N("[quiet]", "측정기 앞, 숨죽임"),
    "NA27": N("[hushed, tense]", "막대 하나, 숨죽여"), "NA28": N("[low, slow, precise]", "「六十三ヘルツ」 — 가장 또렷이, 뒤 0.8초"),
    "NA29": N("[hushed, counting]", "「きっかり二秒」"), "NA30": N("[low, cold, precise]", "「一度も、ずれなかった」 차갑게"),
    "NA31": N("[low, slow, heavy]", "「足音ではなかった」 — 반전 ①, 느리게"), "NA31a": N("[quiet, realizing]", "이사 온 주 — 깨달음"),
    "NA31b": N("[quiet, bitter]", "「思おうとしていた」 자조"),
    "NA32": N("[calm, steady]", "기록 계속"), "NA33": N("[low, suspenseful]", "「ひとつの事実」 톤 낮춤"),
    "NA34": N("[low, precise]", "「十一時ではなかった」"), "NA35": N("[low, slow, chilling]", "「十五分後」 — 반전 ②, 가장 느리게, 뒤 0.8초"),
    "NA36": N("[hushed, cold]", "「待っていた」 속삭이듯 차갑게"),
    "NA36a": N("[quiet, tense]", "엘리베이터"), "NA36b": N("[hushed, chilling]", "「小さく、笑った」"), "NA36c": N("[low, firm]", "「五日分あった」 단단히"),
    "NA37a": N("[quiet, precise]", "빨간 동그라미"), "NA37": N("[calm, matter-of-fact]", "편지 두 통"),
    "NA38": N("[measured, reading out]", "한 통째 — 읽듯이"), "NA39": N("[measured, reading out]", "다른 한 통"),
    "NA40": N("[low, slow, suspenseful]", "2차 광고 직전, 「翌日の夜が来た」 가장 느리게 → 0.8초"),
    "NA41": N("[hushed, tense]", "다음 날 밤, 숨죽여"), "NA41a": N("[quiet]", "짧게"), "NA41b": N("[quiet, guarded]", "「もう嫌だった」 억눌러"),
    "NA42": N("[hushed, listening]", "끄는 소리 — 귀 기울이듯"), "NA42a": N("[hushed, slow]", "테이프 소리, 느리게"),
    "NA43": N("[quiet, steady]", "밤을 세었다"),
    "NA44": N("[low, precise]", "「七日目、午前四時」 또렷이"), "NA45": N("[low, slow]", "베란다 — 느리게"),
    "NA46": N("[hushed, recognizing]", "「あの段ボール」 알아봄"), "NA47": N("[low, flat, slow]", "스피커 — 감정 없이, 느리게"),
    "NA48": N("[low, steady]", "「消えた」 담담하게"), "NA49": N("[flat, precise]", "「六日目」 또렷이"),
    "NA50": N("[low, slow, final]", "「彼のほうだった」 — 카타르시스, 가장 느리게, 뒤 1.0초"),
    "NA50a": N("[calm, matter-of-fact]", "관리회사 전화"), "NA50b": N("[quiet, heavy, relieved]", "「誰も言ってくれなかった」 — 안도 섞인 무게"),
    "NA51": N("[warm, gentle]", "S10부터 반음 따뜻하게. 「九時まで」"), "NA52": N("[warm, quiet, slow]", "측정기, 조용한 채 — 여운"),
    "NA53": N("[calm, firm]", "교훈 ① 단단히"), "NA54": N("[calm, firm, slow]", "「記録だ」 — 느리게"),
    "NA55": N("[measured, listing]", "실용 정보 나열, 또박또박"), "NA56": N("[calm, warm, slow]", "「法律の言葉に変わる」"),
    "NA57": N("[gentle, direct, slow]", "시청자에게 1회 질문 — 가장 느리게"), "NA58": N("[gentle, quiet]", "댓글 유도, 짧게"),
    # ── 美咲 대사 — 절제, 외침 없음
    "L04": N("[soft, warm, smiling]", "딸에게, 웃으며 [VO]"), "L08": N("[polite, trembling slightly]", "402호 문 앞, 정중하지만 떨림 [VO]"),
    "L10": N("[quiet, hesitant]", "말을 잇지 못함 [VO]"), "L12": N("[choked, pleading whisper]", "목 멘 채, 외침 아님. NOT shouting [VO]"),
    "L16": N("[quiet, puzzled]", "「形？」 되묻기 [VO]"), "L20": N("[hushed, counting]", "스톱워치, 숨죽여 세기 [VO]"),
    "L22": N("[quiet, dreading]", "「じゃあ、これは」 [VO]"), "L24": N("[whispering, chilled]", "「見てる」 속삭임 [VO]"),
    "L28": N("[quiet, confused]", "변호사에게 되묻기 [VO]"), "L31": N("[whispering, disbelief]", "「来ない」 믿기지 않는 속삭임 [VO]"),
    "L33": N("[warm, smiling, soft]", "딸에게, 웃으며 [VO]"), "L34": N("[warm, polite]", "おはぎ를 내밀며 [VO]"), "L36": N("[hesitant, moved]", "받지 못하고 [VO]"),
    # ── 結衣 — 6세, 작게
    "L03": N("[bright, childlike]", "카탈로그를 가리키며, 어깨 너머 [Omni]"), "L05": N("[small, sleepy, worried]", "이불 속, 작게 [VO]"),
    "L32": N("[sleepy, soft, hopeful]", "잠에서 덜 깬 채, 이불을 쥔 손 [Omni]"),
    # ── 黒木 — 낮은 비웃음, 고함 없음
    "L02": N("[low, sneering, bored]", "문틈 얼굴 절반, 비웃음 [VO] — S03b L11에 재사용"),
    "L09": N("[flat, dismissive]", "「普通に生活してるだけ」 가볍게 [VO]"), "L11": N("[low, sneering, bored]", "L02 녹음 재사용 [VO]"),
    # ── 大野 — 느리고 짧게, 따뜻함은 밑에
    "L13": N("[low, slow, gentle]", "문가에서, 느리게 [VO]"), "L14": N("[calm, slow, teaching]", "측정기를 쥔 손, 어깨 너머 3/4 [Omni]"),
    "L15": N("[calm, slow, emphatic]", "「形です」 — 측정기를 내밀며 [Omni]"), "L17": N("[gentle, explaining]", "손가락으로 눈금 [VO]"),
    "L18": N("[low, firm]", "「嘘をつけない」 [VO]"), "L19": N("[low, steady, serious]", "「一晩も、休まずに」 어깨 너머 [Omni]"),
    "L21": N("[quiet, grave, slow]", "출력물을 보며, 조용히 [Omni]"), "L23": N("[low, certain]", "「床に直接」 확신 [Omni]"),
    "L25": N("[low, slow, sorrowful]", "창가 뒷모습, 아내 이야기 [VO]"), "L26": N("[low, resolved, slow]", "「測る人間になった」 [VO]"),
    "L35": N("[gruff, warm underneath]", "측정기를 내밀며 [Omni]"), "L37": N("[slow, tender, firm]", "「誰かの耳になりなさい」 — 가장 느리게 [Omni]"),
    # ── 弁護士 — 사무적이되 단호
    "L27": N("[calm, professional, intrigued]", "노트를 넘기며, 어깨 너머 [Omni]"), "L29": N("[firm, precise, professional]", "노트를 짚으며 [Omni]"),
    "L30": N("[calm, grave, low]", "판례집을 덮으며 「懲役です」 [VO]"),
    # ── 警察官 · 管理会社 — 사무적 VO
    "L00": N("[flat, official, apologetic]", "무전기 EQ [VO]"), "L06": N("[flat, official]", "현관 앞 [VO]"),
    "L01": N("[flat, clerical, hurried]", "전화 EQ [VO]"), "L07": N("[flat, clerical, hurried]", "전화 EQ [VO]"),
    "L38": N("[flat, clerical]", "「解約となりました」 사무적 [VO]"),
    # ── 진행자 Yui Sato (Typecast)
    "OUT1": (("normal", 1.0, 0.95), "가슴 위 CU, 정중하게 [Omni]"),
    "OUT2": (("normal", 1.0, 0.92), "요약, 진지하게 [Omni]"),
    "OUT3": (("normal", 0.9, 0.95), "다음 화 예고 [Omni]"),
    "OUT4": (("happy", 0.9, 1.0), "구독·댓글 요청, 밝게 [Omni]"),
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
    n = 0
    for (tag, spk, omni, text) in lines:
        warns += check_length(tag, text)
        tone, note = T[tag]
        name, role = CAST[spk]
        if tag in EXTRA_ID:
            lid = EXTRA_ID[tag]
        else:
            n += 1; lid = f"line{n:03d}"
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
            kt = kana(text)
            tests.append({"id": lid, "model": "elevenlabs-direct", "voice": r["voice_id"], "voice_name": r["name"],
                          "el_model": "eleven_v3", "text": f"{tone} {kt}", "subtitle": text})
            chars_el += len(text) + len(tone) + 1; src = f"EL {r['name']}"
        tone_s = tone if isinstance(tone, str) else f"{tone[0]} {tone[1]} · tempo {tone[2]}"
        rows.append(f"| {lid[4:]} | {tag} | {name} | {'Omni' if omni else '-'} | {text} | {tone_s} | {note} | {src} |")
    for tag, src_tag in SAME_AS.items():
        rows.append(f"| — | {tag} | 재사용 | | | | {src_tag}({idmap[src_tag]}) 음성을 S03b에 배치 | |")
    spec = {"_설명": f"『63ヘルツ』 본녹음(PHASE 1). build_tts.py 생성물 — 직접 고치지 말 것. EL {chars_el}자 · Typecast {chars_tc}자, fal 0.",
            "tts_model": "ssfm-v30", "language": "jpn", "tests": tests}
    json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "soukaion-tts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    md = ["# 『63ヘルツ』 줄별 톤 연출표 (PHASE 1 — 음성·표정·동작의 단일 출처, 제10장 7)", "",
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
