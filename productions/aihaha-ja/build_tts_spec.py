#!/usr/bin/env python3
"""『母が遺したビデオレター』(aihaha-ja) PHASE 1 본녹음 스펙 + 줄별 톤 연출표 생성기 (무료).

입력: 00_script_ja.md (🔒 v1.0 동결 대본), 고니감독님 청취 확정 캐스트(2026-11-03, 아래 VOICE).
출력: scripts/auditions/aihaha-tts.json  (ElevenLabs eleven_v3 elevenlabs-direct + 아웃트로 Typecast Yui Sato, line### = 시간 순서)
      scripts/audio/aihaha-cast-voices.json (배역별 목소리·설정값 기록 — 제20장 1)
      05_톤연출표.md (줄 번호 ↔ 대본 태그 ↔ 목소리 ↔ 연기 태그·안정도·속도·연기 메모 = 음성·표정·동작의 단일 출처, 제10장 7)
규칙: 음성 입력 = 「[짧은 영어 톤 태그] + 가나 치환본」, 자막은 원문 한자 유지(제20장 1·제14장 8).
      ElevenLabs v3 stability: 0.0 Creative(감정 폭 큼) / 0.5 Natural(기본) / 1.0 Robust(평탄·일정 — 가짜 어머니 전용, 제20장 4).
검사: 한 문장 30자·한 줄 2문장(제17장 4②) · 톤 지정 없는 줄 0 · 목소리 없는 화자 0 · 태그 4단어 이하(제20장 1·EP2 ⑩).
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# 2026-11-03 고니감독님 청취 확정(aihaha-el-cast·aihaha-el-haha)
VOICE = {
    "NA":   {"name": "Chiemi", "voice": "CAz2VQzFEVyGujit7Iof", "role": "由紀子(내레이션)", "settings": {"stability": 0.5}},
    "由紀子": {"name": "Chiemi", "voice": "CAz2VQzFEVyGujit7Iof", "role": "由紀子(대사)", "settings": {"stability": 0.5}},
    "母":   {"name": "Chieko - Warm, Witty Grandma", "voice": "xE6NbKmUvY3BhBzNAYsV", "role": "어머니 佐和子(진짜)", "settings": {"stability": 0.5}},
    "AI母": {"name": "Chieko - Warm, Witty Grandma", "voice": "xE6NbKmUvY3BhBzNAYsV", "role": "가짜 비디오레터 어머니", "settings": {"stability": 1.0}},
    "叔父": {"name": "Jun - Calm, Clear and Husky", "voice": "JOcmGzB8OFjY8MhjHHEf", "role": "숙부 剛", "settings": {"stability": 0.5}},
    "叔母": {"name": "Chidori", "voice": "RG23A8s6ehr3kui0iBz6", "role": "숙모 頼子", "settings": {"stability": 0.5}},
    "翔太": {"name": "Samurai", "voice": "TlxVR97quVHvTxE8Qkcm", "role": "사촌 翔太", "settings": {"stability": 0.5}},
    "宮下": {"name": "MacLight", "voice": "C4mQ5g9WaCYNQ3mMeJZR", "role": "형사 宮下", "settings": {"stability": 0.5}},
    "OUT":  {"name": "Yui Sato", "voice": "tc_629fe972013e90b4db213fd8", "role": "아웃트로 진행자(Typecast, 채널 공식)", "typecast": True},
}

# 줄별 연기: (영어 톤 태그 2~4단어, stability 덮어쓰기 또는 None, speed, 연기 메모 = 표정·동작)
# 숙부 Jun은 오디션에서 음량·분노 폭이 작았음 → 분노 정점(L38·L39)은 stability 0.0(Creative)로 폭을 키우고 믹스에서 음량 맞춤.
TONE = {
    "L01": ("flat, emotionless", None, 0.95, "태블릿 속 가짜 어머니 — 눈 깜빡임 없음·대칭 얼굴, 입모양 12프레임 지연(편집)"),
    "L02": ("flat, emotionless", None, 0.95, "같은 화면, 억양 없이 일정하게"),
    "NA0": ("quiet, uneasy", None, 0.92, "태블릿 빛 속 옆얼굴, 숨을 멈춘 채"),
    "NA1": ("quiet, certain", None, 0.88, "「一度も」 앞 반 박자, 끝을 낮게 단정"),
    "NA2": ("calm, reflective", None, 0.95, "회상의 시작, 담담하게"),
    "NA3": ("warm, gentle", None, 0.95, "간병의 일상, 리듬감 있게"),
    "L03": ("warm, gentle", None, 0.9, "창가 의자에서 딸을 올려다보며 웃음 — 눈가 주름"),
    "L03a": ("warm, chatty", None, 0.92, "창밖 비계 맨션을 손끝으로 가리키며"),
    "L03b": ("soft, warm", None, 0.95, "담요를 덮어 주며 다정하게 — 어머니 i2v 위 목소리"),
    "NA4": ("warm, nostalgic", None, 0.92, "「ゆっこ」를 부드럽게"),
    "NA5": ("quiet, sad", None, 0.88, "「旅立った」 끝을 사라지게"),
    "NA5a": ("quiet, sad", None, 0.85, "빈 의자 위, 가장 낮게"),
    "NA6": ("calm, bitter", None, 0.95, "「柱ばかり」에 씁쓸함"),
    "L04": ("condescending", None, 1.0, "맥주를 따르며 위에서 내려다봄 — 거만한 턱"),
    "L05": ("sneering", None, 1.05, "초밥 접시를 밀며 비웃음 — 입꼬리"),
    "L06": ("mocking, casual", None, 1.05, "스마트폰을 보며 코웃음 — 눈은 화면에"),
    "L07": ("restrained, trembling", None, 0.9, "무릎 위 손을 꽉 쥐고 억누름 — 젖었지만 흐르지 않는 눈, NOT smiling"),
    "NA7": ("quiet, bitter", None, 0.92, "「三年間」에 무게"),
    "NA8": ("ominous, quiet", None, 0.88, "CCTV 화면 위, 「消えた」 끊어서"),
    "L08": ("serious, persuasive", None, 0.95, "목소리를 낮춰 다가앉으며 — 진지한 척"),
    "NA9": ("tense, quiet", None, 0.92, "숫자는 또박또박"),
    "NA10": ("tense, quiet", None, 0.92, "「母の実印」 강조"),
    "L09a": ("shocked, quiet", None, 0.92, "차용증을 내려다보며 굳음 — 커진 눈"),
    "L09b": ("fake gentle", None, 0.95, "다정한 척 목소리를 누그러뜨림 — 눈은 차갑게"),
    "L09": ("pressuring, firm", None, 1.0, "차용증을 손끝으로 두드리며 — 압박"),
    "L10": ("casual, smug", None, 1.0, "태블릿을 내밀며 — 우쭐한 미소"),
    "L11": ("flat, emotionless", None, 0.95, "태블릿 속 가짜 어머니 — 무깜빡임"),
    "L12": ("fake sad", None, 1.0, "손수건을 꺼내며 우는 척 — 마른 눈"),
    "NA11": ("cold, quiet", None, 0.92, "「一滴も」에 냉소"),
    "L13": ("quiet, hesitant", None, 0.9, "시선을 내린 채 작게 — 하이 앵글"),
    "L14": ("sneering, mocking", None, 1.05, "비웃음 섞어 — 제목 인용구, 가장 날카롭게"),
    "L15": ("smug, relaxed", None, 0.98, "잔을 내려놓으며 여유 — 「十一月」 가볍게"),
    "NA12": ("quiet, defeated", None, 0.9, "고개를 숙인 무력감"),
    "NA13": ("tense, whispery", None, 0.88, "1차 광고 직전 — 「息をのんだ」 끝 숨"),
    "NA14": ("tense, slow", None, 0.85, "태블릿 화면 확대와 함께 천천히"),
    "NA15": ("whispering, stunned", None, 0.8, "속삭이듯 — 앞 1초 침묵"),
    "NA16": ("firm, quiet", None, 0.92, "날짜를 또박또박"),
    "NA17": ("quiet, certain", None, 0.92, "「分かる」 단정"),
    "L16": ("whispering, trembling", None, 0.85, "혼잣말 속삭임 — 떨리는 입술"),
    "NA17a": ("tense, low", None, 0.88, "질문으로 열어 둠"),
    "NA18": ("confident, calm", None, 0.95, "전문가의 자신감이 처음 비침"),
    "NA18a": ("calm, firm", None, 0.95, "「一円単位で」 강조"),
    "NA19": ("calm, explaining", None, 0.95, "설명이지만 짧게"),
    "NA20": ("crisp, certain", None, 0.95, "세 기관 이름 또박또박, 「該当なし」 단정"),
    "NA21": ("cold, certain", None, 0.95, "「すら」에 냉소"),
    "NA22": ("tense, quiet", None, 0.9, "시각을 또박또박"),
    "NA23": ("cold, quiet", None, 0.9, "「実印のケース」 강조"),
    "L17": ("polite, determined", None, 0.95, "태블릿과 서류 봉투를 내밀며"),
    "L17a": ("impressed, calm", None, 0.95, "태블릿 영상을 멈추고 由紀子를 봄"),
    "L17b": ("soft, sad", None, 0.9, "손목시계를 감싸며 — 젖은 눈"),
    "L17c": ("calm, serious", None, 0.95, "차용증을 들어 보이며 — 단호"),
    "L18": ("calm, professional", None, 0.98, "서류를 넘기며"),
    "L19": ("serious, low", None, 0.95, "눈을 들어 똑바로 — 무게"),
    "L20": ("small smile, firm", None, 0.95, "작게 웃으며 — 이 작품 유일한 미소"),
    "NA20a": ("quiet, mysterious", None, 0.9, "열린 고리 — 「もう一つ」 강조"),
    "L21": ("irritated, pushy", None, 1.02, "거실 기둥을 손바닥으로 두드리며"),
    "L21a": ("threatening, low", None, 0.98, "기둥에서 손을 떼며 위협"),
    "L22": ("greedy, casual", None, 1.05, "스마트폰으로 집 안을 찍으며 — 탐욕스러운 눈"),
    "L23": ("spiteful, smug", None, 1.02, "핸드백을 고쳐 들며 — 험담의 쾌감"),
    "NA24": ("quiet, restrained", None, 0.9, "굴욕을 삼킴"),
    "NA24a": ("cold, quiet", None, 0.92, "「毎晩」에 무게"),
    "L24a": ("whispering, tearful", None, 0.85, "영정 앞 속삭임 — 젖었지만 흐르지 않는 눈, NOT smiling"),
    "NA25": ("quiet, slow", None, 0.85, "시계 초침 소리 위, 천천히"),
    "NA26": ("quiet, knowing", None, 0.9, "「勘違い」 강조 — 반격의 예고"),
    "NA27": ("quiet, knowing", None, 0.88, "「数字」 뒤 반 박자"),
    "NA28": ("firm, resolute", None, 0.9, "2차 광고 직전 — 날짜 단정"),
    "L24": ("smug, satisfied", None, 0.98, "펜을 내밀며 — 승리한 얼굴"),
    "L25": ("calm, polite", None, 0.95, "리모컨을 들며 — 담담"),
    "L26": ("flat, emotionless", None, 0.95, "TV 속 가짜 어머니"),
    "L27": ("calm, firm", None, 0.95, "TV를 가리키며 — 차분한 확신"),
    "L30": ("calm, firm", None, 0.95, "날짜를 또박또박"),
    "L31": ("calm, firm", None, 0.95, "개시 결과를 차용증 위에 놓으며 — 「ゼロ円」 단정"),
    "L32": ("shrill, angry", None, 1.05, "언성을 높이며 — 몸을 앞으로"),
    "L33": ("calm, dignified", None, 0.92, "안경을 고쳐 쓰며 담담히 — 소리치지 않음"),
    "L34": ("flustered, stammering", 0.0, 1.05, "벌떡 일어나며 — 땀, 흔들리는 눈"),
    "L35": ("quiet, sharp", None, 0.9, "천천히 고개를 돌려 翔太를 봄 — 앞 1.5초 정적"),
    "L36": ("quiet, firm", None, 0.92, "또박또박"),
    "L37": ("quiet, emotional", None, 0.9, "영정 쪽을 보며 — 젖은 눈"),
    "L38": ("furious, shouting", 0.0, 1.05, "테이블을 짚고 몸을 숙이며 고함 — 붉어진 얼굴"),
    "L39": ("furious, shouting", 0.0, 1.08, "테이블을 내리치며"),
    "L40": ("calm, quiet", None, 0.92, "흔들리지 않는 목소리"),
    "L41": ("calm, quiet", None, 0.9, "왼손목 시계를 봄"),
    "L42": ("confused, irritated", None, 0.98, "팔짱 낀 채 — 짜증"),
    "L43": ("calm, firm", None, 0.88, "「九十三日」 한 글자씩"),
    "L44": ("calm, explaining", None, 0.92, "짧게 끊어서"),
    "L45": ("calm, firm", None, 0.9, "단정"),
    "L46": ("quiet, decisive", None, 0.85, "한 박자 쉬고 — 킬링 멘트"),
    "NA30": ("cold, satisfied", None, 0.9, "「時計に」 강조"),
    "L47": ("shocked, trembling", 0.0, 0.92, "의자에 주저앉으며 떨림 — 핏기 없는 얼굴"),
    "L48": ("panicked, shrill", 0.0, 1.08, "남편 팔을 끝까지 붙잡은 채"),
    "NA31": ("cold, quiet", None, 0.92, "사실 전달"),
    "L49": ("formal, firm", None, 0.95, "현관에서 거실로 들어서며"),
    "L51": ("formal, cold", None, 0.95, "숙모를 똑바로 봄"),
    "L52": ("formal, firm", None, 0.92, "정중하지만 거부할 수 없게"),
    "L53": ("pleading, weak", 0.0, 0.88, "처음으로 애원 — 하이 앵글, 작게 떨림"),
    "L54": ("quiet, calm", None, 0.9, "조용히 — 콜백 준비"),
    "L55": ("quiet, final", None, 0.88, "끝을 낮게 — 콜백, 소리치지 않음"),
    "NA32": ("calm, matter-of-fact", None, 0.95, "결말 정리, 담담"),
    "NA33": ("calm, quiet", None, 0.92, "짧게"),
    "NA34": ("soft, emotional", None, 0.88, "휴대폰을 든 손, 「聞けずにいた」 떨림"),
    "L56": ("tender, slightly tired", None, 0.88, "LINE 음성 메시지 — 휴대폰 스피커 질감(믹스), 숨 섞임"),
    "L57": ("tender, smiling", None, 0.88, "「……」에서 웃음 섞인 숨"),
    "L57a": ("whispering, tearful", None, 0.82, "속삭이며 대답 — 한 줄기 눈물(i2v), NOT smiling"),
    "NA35": ("quiet, emotional", None, 0.88, "마지막 주제문 1"),
    "NA36": ("quiet, emotional", None, 0.82, "마지막 주제문 2 — 가장 느리게, 끝 2초 여운"),
    # 아웃트로: Typecast(프리셋, 강도, 템포)
    "OUT1": ("happy", 0.6, 0.95, "CU 스타일 C, 감사 인사"),
    "OUT2": ("normal", 1.0, 0.95, "35° MCU, 질문을 던지듯"),
    "OUT3": ("happy", 1.0, 0.92, "댓글 유도, 밝고 또렷이"),
    "OUT4": ("happy", 0.8, 0.95, "구독 버튼 오버레이"),
    "OUT5": ("happy", 1.0, 0.95, "손 흔들기"),
}

# 음성 입력 전용 가나 치환(긴 것 먼저) — 자막은 원문 유지
KANA = [("大野頼子さん", "おおのよりこさん"), ("由紀子", "ゆきこ"), ("伯母さん", "おばさん"), ("叔父さん", "おじさん"),
        ("お姉さん", "おねえさん"), ("姉さん", "ねえさん"), ("叔父一家", "おじいっか"), ("叔父", "おじ"), ("叔母", "おば"),
        ("通夜", "つや"), ("四十九日", "しじゅうくにち"), ("四十六", "よんじゅうろく"), ("四千七百万円", "よんせんななひゃくまんえん"),
        ("二千六百万", "にせんろっぴゃくまん"), ("一億", "いちおく"), ("七月二十五日", "しちがつにじゅうごにち"), ("七月二日", "しちがつふつか"),
        ("十月三日", "じゅうがつみっか"), ("九十三日", "きゅうじゅうさんにち"), ("十一時四十一分", "じゅういちじよんじゅういっぷん"),
        ("十一月", "じゅういちがつ"), ("三週間", "さんしゅうかん"), ("三か月", "さんかげつ"), ("三年間", "さんねんかん"), ("三年前", "さんねんまえ"),
        ("二十年", "にじゅうねん"), ("三枚", "さんまい"), ("三社", "さんしゃ"), ("三人", "さんにん"), ("一円単位", "いちえんたんい"),
        ("一通", "いっつう"), ("一滴", "いってき"), ("一言", "ひとこと"), ("一度も", "いちども"), ("一度", "いちど"), ("一緒", "いっしょ"),
        ("一つ", "ひとつ"), ("信用金庫", "しんようきんこ"), ("信用情報", "しんようじょうほう"), ("貸金業", "かしきんぎょう"),
        ("CIC、JICC、KSC", "シーアイシー、ジェイアイシーシー、ケーエスシー"), ("AI", "エーアイ"), ("千葉県警", "ちばけんけい"),
        ("鑑定", "かんてい"), ("署まで", "しょまで"), ("ご同行", "ごどうこう"), ("更地", "さらち"), ("競売", "けいばい"),
        ("腕時計", "うでどけい"), ("何日", "なんにち"), ("何と", "なんと"), ("何の", "なんの"), ("実印", "じついん"),
        ("借用書", "しゃくようしょ"), ("相続人", "そうぞくにん"), ("開示", "かいじ"), ("該当", "がいとう"), ("融資", "ゆうし"),
        ("担保", "たんぽ"), ("判子", "はんこ"), ("見守り", "みまもり"), ("合成", "ごうせい"), ("解雇", "かいこ"),
        ("『", ""), ("』", "")]
TAG_KANA = {}  # 언어 검사에서 흔들린 줄만 줄 단위로 덧붙인다(제19장 2)


def kana(tag, s):
    for a, b in TAG_KANA.get(tag, []):
        s = s.replace(a, b)
    for a, b in KANA:
        s = s.replace(a, b)
    return s


LINE_RE = re.compile(r'^\s*((?:NA|L|OUT)\d+\w*)\s*([^:「]*?)\s*[:：]\s*「(.+)」\s*$')


def load():
    t = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read()
    assert "🔒 v1.0" in t.splitlines()[0], "동결 대본(🔒 v1.0)이 아닙니다"
    body = t.split("## 4. 대본")[1].split("## 5.")[0]
    out = []
    for ln in body.splitlines():
        m = LINE_RE.match(ln)
        if not m:
            continue
        tag, meta, text = m.groups()
        spk = "NA" if tag.startswith("NA") else "OUT" if tag.startswith("OUT") else meta.split()[0] if meta.split() else ""
        out.append((tag, spk, text))
    return out


def sentences(text):
    parts = re.split(r"(?<=[。！？])\s*", text.replace("――", "。"))
    return [p for p in (x.strip(" 　") for x in parts) if re.sub(r"[……、。！？\s　]", "", p)]


def main():
    lines = load()
    tags = [t for t, _, _ in lines]
    dup = sorted({t for t in tags if tags.count(t) > 1})
    assert not dup, f"중복 태그: {dup}"
    missing = [t for t in tags if t not in TONE]
    assert not missing, f"톤 지정 없는 줄: {missing}"
    unused = [k for k in TONE if k not in tags]
    assert not unused, f"대본에 없는 톤 키: {unused}"
    nov = [t for t, s, _ in lines if s not in VOICE]
    assert not nov, f"목소리 없는 화자: {nov}"
    bad = []
    for tag, spk, text in lines:
        ss = sentences(text)
        if len(ss) > 2:
            bad.append(f"{tag}: {len(ss)}문장")
        bad += [f"{tag}: {len(s)}자" for s in ss if len(re.sub(r"[、。！？…\s　\"『』]", "", s)) > 30]
        if not VOICE[spk].get("typecast") and len(TONE[tag][0].replace(",", " ").split()) > 4:
            bad.append(f"{tag}: 태그 4단어 초과")
    assert not bad, "규칙 위반:\n  " + "\n  ".join(bad)

    tests, rows, chars = [], [], 0
    for n, (tag, spk, text) in enumerate(lines, 1):
        v, (t0, stab, speed, note) = VOICE[spk], TONE[tag]
        fid = f"line{n:03d}"
        if v.get("typecast"):
            tests.append({"id": fid, "model": "typecast-direct", "voice": v["voice"], "language": "jpn",
                          "text": kana(tag, text), "emotion_preset": t0, "emotion_intensity": stab, "tempo": speed})
            rows.append(f"| {fid} | {tag} | 진행자 | {v['name']}(Typecast) | {text} | {t0} {stab} | — | {speed} | {note} |")
            continue
        # eleven_v3 API에는 확실히 지원되는 stability만 보낸다(speed 등 미지원 값으로 실행 전체가 실패하는 위험 차단).
        # 속도는 PHASE 1 Lock에서 줄별 배속(atempo, 0.85~1.15)으로 맞춘다 — lock_tempo(제11장 4).
        vs = {"stability": stab if stab is not None else v["settings"]["stability"]}
        inp = f"[{t0}] {kana(tag, text)}"
        chars += len(inp)
        tests.append({"id": fid, "model": "elevenlabs-direct", "voice": v["voice"], "voice_name": v["name"],
                      "el_model": "eleven_v3", "voice_settings": vs, "lock_tempo": speed, "text": inp})
        rows.append(f"| {fid} | {tag} | {v['role']} | {v['name']} | {text} | [{t0}] | {vs['stability']} | {speed} | {note} |")

    spec = {"_설명": f"『母が遺したビデオレター』 PHASE 1 본녹음 {len(tests)}줄(본편 ElevenLabs eleven_v3 + 아웃트로 Typecast Yui Sato). "
                    "음성 입력 = [영어 톤 태그] + 가나 치환본, 자막은 원문. line### = 시간 순서. 생성: productions/aihaha-ja/build_tts_spec.py. "
                    "실행: generate-video.yml audition_spec=aihaha-tts (브랜치 claude/aihaha-ja).",
            "language": "jpn", "tc_model": "ssfm-v30", "tests": tests}
    json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "aihaha-tts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cast = {k: {kk: vv for kk, vv in v.items()} for k, v in VOICE.items()}
    json.dump({"_설명": "『母が遺したビデオレター』 확정 캐스트·ElevenLabs 설정값(제20장 1 — 재현성). 2026-11-03 고니감독님 청취 확정. 줄별 덮어쓰기(stability·speed)는 05_톤연출표.md.",
               "model": "eleven_v3", "cast": cast}, open(os.path.join(REPO, "scripts", "audio", "aihaha-cast-voices.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = ["# 『母が遺したビデオレター』 줄별 톤 연출표 (규칙 8-2 · 제10장 7 — 음성·표정·동작의 단일 출처)", "",
          f"> 🔒 동결 대본 v1.0 기준 본녹음 {len(tests)}줄(본편 {len(tests)-5} + 아웃트로 5). 지정 없는 줄 0개. 생성기: `build_tts_spec.py`. ElevenLabs 입력 약 {chars}자(태그 포함).",
          "> 안정도(stability): 0.0 감정 폭 큼(분노·당황 정점) / 0.5 기본 / 1.0 평탄(가짜 어머니 전용 — 진짜 어머니와 같은 목소리에서 숨·떨림을 지워 대비, 제20장 4).",
          "> 연기 메모의 표정·동작은 키프레임(50% 반영)·i2v 동작 문장·OmniHuman 연기 지시에 그대로 쓴다. 가나 치환은 음성 입력에만.", "",
          "| 녹음 | 대본 | 배역 | 목소리 | 일본어 | 연기 태그 | 안정도 | Lock 템포 | 연기 메모(표정·동작) |", "|---|---|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(HERE, "05_톤연출표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    from collections import Counter
    print(f"본녹음 {len(tests)}줄 → scripts/auditions/aihaha-tts.json · scripts/audio/aihaha-cast-voices.json · 05_톤연출표.md / ElevenLabs 약 {chars}자")
    print(Counter(s for _, s, _ in lines))


if __name__ == "__main__":
    main()
