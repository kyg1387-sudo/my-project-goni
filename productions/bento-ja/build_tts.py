#!/usr/bin/env python3
"""『閉店間際の弁当屋』(bento-ja) PHASE 1 — 줄별 톤 연출표(05) + 본녹음 TTS 스펙(scripts/auditions/bento-tts.json) 생성기 (무료).

입력: 00_script_ja.md(대본 v1.1 🔒), 배역 대장 scripts/audio/bento-cast-voices.json(고니감독님 청취 확정 2026-10-20)
출력: 05_톤연출표.md, scripts/auditions/bento-tts.json (line### = 대본 순서)
엔진: 어른 배역·내레이터 = ElevenLabs eleven_v3(영어 연기 태그 2~4단어, 대사 앞) · 아역·진행자 = Typecast ssfm-v30 jpn(제19장 2 ⑤)
규칙: 톤 지정 없는 줄 0개 · 한 문장 ≤30자 · 한 줄 ≤2문장(제14장 8) · 음성 입력은 가나 치환본, subtitle은 대본 원문
사용법: python3 productions/bento-ja/build_tts.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CAST_JSON = json.load(open(os.path.join(REPO, "scripts", "audio", "bento-cast-voices.json"), encoding="utf-8"))

# 대본 화자 표기 → (표시명, 배역 키)
CAST = {
    "NA": ("내레이터", "narr"), "修三": ("修三", "shuzo"), "澄江": ("澄江", "sumie"),
    "拓海(少年)": ("拓海 소년", "takumi_boy"), "拓海(大人)": ("拓海 어른", "takumi_adult"),
    "美緒": ("美緒", "mio"), "陽菜": ("陽菜", "hina"), "진행자": ("진행자", "host"),
}
SAME_AS = {"L01": "L29"}
# 내레이션 속도(2026-10-20 실측 3.5자/초로 느림 → 제19장 4 ③). 모든 NA 줄 앞에 붙인다
NA_PACE = "[steady, natural pace]"  # 후크 H1 = 편지 낭독 L29와 같은 문장 → 한 번만 녹음해 재사용

# 태그: (EL 연기 태그 또는 Typecast (감정, 강도, 템포), 연기 메모 = 표정·동작의 단일 출처, 제10장 7)
T = {
    # 내레이터 Shino — 3인칭 です・ます, 담담하고 따뜻하게
    "NA0": ("[hushed, gentle storyteller]", "후크, 비밀을 털어놓듯 낮게"),
    "NA1": ("[calm, warm narrator]", "가게 소개"), "NA2": ("[calm, warm narrator]", "인물 소개, 「七十三歳」 또렷이"),
    "NA3": ("[quiet, wistful]", "「閉じます」 조용히"), "NA3a": ("[soft, tender]", "지금도 남은 습관, 따뜻하게"),
    "NA4": ("[soft, drifting into memory]", "회상 진입"), "NA5": ("[warm, nostalgic]", "1996년, 「毎晩」에 무게"),
    "NA6": ("[gentle, a little sad]", "「一番安い」 천천히"), "NA6a": ("[warm, quietly moved]", "「一度も」 반 박자"),
    "NA7": ("[quiet]", "짧게"), "NA8": ("[quiet, lingering]", "「止まったまま」 여운"),
    "NA8a": ("[soft, heartfelt]", "「幼い妹と」 부드럽게"), "NA8b": ("[quiet, matter-of-fact]", "담담히"),
    "NA9": ("[warm, smiling softly]", "따뜻한 전환"), "NA10": ("[gentle reveal]", "반전 ① 예고"),
    "NA11": ("[gentle reveal, slower]", "반전 ①, 또박또박"), "NA11a": ("[soft]", "덧붙이듯"),
    "NA12": ("[warm, intimate]", "「ただ一人」 천천히"), "NA13": ("[quiet, ominous]", "톤 전환"),
    "NA14": ("[slow, suspenseful]", "1차 광고 직전, 끝을 가장 느리게"),
    "NA15": ("[quiet, worried]", "걱정"), "NA15a": ("[quiet]", "담담히"), "NA15b": ("[soft, uneasy]", "「明かりは」 여운"),
    "NA16": ("[quiet, wistful]", "식어 가는 도시락"), "NA16a": ("[matter-of-fact]", "현실"),
    "NA16b": ("[warm, firm]", "「やめませんでした」 단단히"), "NA17": ("[warm, gentle]", "겨울 정경"),
    "NA18": ("[soft, lingering]", "이별, 끝을 열어 둠"), "NA19": ("[calm, time passing]", "시간 몽타주"),
    "NA19a": ("[quiet, wistful]", "「一度も」 무게"), "NA20": ("[soft, sorrowful]", "아내의 죽음, 절제"),
    "NA21": ("[quiet, steadfast]", "「九時まで」 또렷이"), "NA21a": ("[warm, moved]", "약속 회수"),
    "NA22": ("[calm]", "현재로 복귀"), "NA23": ("[curious, gentle]", "봉투"),
    "NA24": ("[slow, suspenseful]", "2차 광고 직전, 「止まりました」 가장 느리게"),
    "NA25": ("[soft, moved]", "소리 없는 울음"), "NA26": ("[gentle, building]", "마지막 한 줄 예고"),
    "NA27": ("[warm, peaceful]", "결말"), "NA28": ("[warm, smiling]", "현재"), "NA28a": ("[warm, smiling]", "밝게"),
    "NA29": ("[slow, heartfelt]", "주제문"), "NA30": ("[warm, gentle ending]", "주제문, 가장 느리게"),
    # 修三 Tonatsu — 1996 43세: 무뚝뚝·짧게 / 현재 73세: 낮고 느리게, 목이 멤
    "L03": ("[gruff, curt]", "봉지를 꺼내며 소년을 보지 않음 [Omni]"),
    "L03b": ("[gruff, deadpan]", "계산대를 보며 시치미 [Omni]"), "L03d": ("[gruff, curt]", "봉지를 내밀며 [VO]"),
    "L05": ("[quiet, flat]", "쌀 씻는 손을 멈추지 않음 [VO]"),
    "L06d": ("[low, after a pause]", "칼을 내려놓고 결심 [VO]"),
    "L07": ("[gruff, curt]", "수건을 내밀며 퉁명 [Omni]"), "L09": ("[gruff, avoiding eye contact]", "봉지를 내밀며 눈을 피함 [Omni]"),
    "L10a": ("[gruff, offhand]", "행주질하며 무심한 척 [Omni]"), "L10c": ("[quiet, faint smile]", "입꼬리만 살짝 [VO]"),
    "L12": ("[gruff, embarrassed]", "서랍을 닫으며 등을 반쯤 돌림 [Omni]"),
    "L14": ("[gruff, covering feelings]", "셔터를 잡은 채 거리를 봄 [Omni]"),
    "L14b": ("[gruff, reassuring]", "쌀 포대를 내려놓으며 짧게 [Omni]"),
    "L16": ("[low, quick]", "셔터를 다시 올리며 [Omni]"), "L19": ("[firm, gentle]", "봉지 두 개, 소년 눈을 보고 [Omni]"),
    "L21": ("[gruff, warm underneath]", "카운터를 짚고 눈높이를 맞춤 [Omni]"),
    "L24": ("[quiet, holding back]", "뚜껑 닫던 손이 멈춤 [VO]"),
    "L26b": ("[choked up, short]", "종이 새를 손바닥에, 목이 멤 [Omni]"),
    "L26c": ("[gruff, tender]", "봉지를 쥐여 주며 눈을 봄 [Omni]"),
    "L26e": ("[quiet, promising]", "등을 살짝 밀며 [VO]"),
    "L26g": ("[gruff, pretending]", "문에서 눈을 떼지 않음 [VO]"),
    "L26j": ("[quiet, steady]", "사과 깎던 손을 멈춤(60대) [Omni]"),
    "L31d": ("[older man, laughing through tears]", "편지를 쥔 채 혼잣말(73세) [VO]"),
    "L36": ("[older man, choked up]", "마지막 도시락에 손을 얹고 목이 멤(73세) [Omni]"),
    "L37b": ("[older man, soft smile]", "두건 쪽을 보았다가 拓海를 봄 [Omni]"),
    "L39": ("[older man, voice breaking]", "사진을 들어 보이며 눈물 섞인 미소 [Omni]"),
    "L40": ("[older man, gruff but kind]", "陽菜에게 몸을 숙여 [Omni]"),
    "L42": ("[older man, quiet acceptance]", "빈 주방을 돌아봄 [Omni]"),
    "L44": ("[older man, wry chuckle]", "멍하니 보다가 코웃음 [Omni]"),
    # 澄江 Chiemi — 밝고 생활감 있게(내레이터 Shino와 구분), 병실은 약하게
    "L04": ("[bright, chatty]", "젖은 손을 앞치마에 닦으며 [Omni]"),
    "L06": ("[worried, lowering voice]", "걱정스럽게 [Omni]"),
    "L06c": ("[teary, hushed]", "젖은 눈, 목소리를 낮춤 [Omni]"),
    "L11": ("[teasing, fond]", "팔짱 끼고 작게 웃음 [Omni]"),
    "L13": ("[gentle, knowing]", "남편 옆에서 조용히 [Omni]"),
    "L14a": ("[forced cheer]", "장부를 덮고 애써 웃음 [Omni]"),
    "L22a": ("[warm, motherly]", "쪼그려 앉아 눈을 맞춤 [Omni]"),
    "L25": ("[laughing, teary]", "웃으며 눈가를 훔침 [Omni]"),
    "L26f": ("[soft, wistful]", "남편과 문을 봄 [Omni]"),
    "L26h": ("[teasing, teary laugh]", "남편 옆얼굴을 보며 웃음 [Omni]"),
    "L26i": ("[weak, gentle]", "병실, 약하게 웃음 [Omni]"),
    "L26k": ("[weak, tender]", "눈을 감으며, 젖었지만 흐르지 않음 [VO]"),
    # 拓海 어른 Masa — 진실하고 낮게, 편지 낭독은 절제
    "L01": ("[quiet, holding back tears]", "후크 H1 — L29 녹음 재사용 [VO]"),
    "L27": ("[soft, letter reading]", "편지 첫 줄 [VO]"), "L27a": ("[soft, letter reading]", "자기소개 [VO]"),
    "L28": ("[soft, apologetic]", "「本当に」 무게 [VO]"),
    "L29": ("[quiet, holding back tears]", "반전 ② 직전, 후크 재사용 [VO]"),
    "L30": ("[quiet, confessing]", "고백 [VO]"), "L30a": ("[quiet, confessing]", "이어서 [VO]"),
    "L31": ("[quiet, holding back tears]", "반전 ②, 끊어서 [VO]"),
    "L31a": ("[soft, sad]", "어머니의 죽음 [VO]"), "L31b": ("[soft, warm memory]", "죽 이야기 [VO]"),
    "L31c": ("[soft, a little proud]", "여동생 소식 [VO]"),
    "L32a": ("[soft, regretful]", "몇 번이나 [VO]"), "L32b": ("[soft, earnest]", "떳떳해지고 나서 [VO]"),
    "L32": ("[warm, quietly proud]", "子ども食堂 [VO]"), "L33": ("[warm, shy smile]", "가게 이름, 끝은 묻듯이 [VO]"),
    "L34": ("[soft, resolute]", "마지막 한 줄 [VO]"),
    "L35": ("[tearful smile]", "문간에서 젖은 눈으로 웃으며 [Omni]"),
    "L37a": ("[careful, gentle]", "두건을 보다가 조심스럽게 [Omni]"),
    "L38": ("[earnest, bowing]", "봉투를 두 손으로 밀며 [Omni]"),
    "L41": ("[soft, concerned]", "눈물을 닦고 셔터를 봄 [Omni]"),
    "L43": ("[earnest, hopeful]", "카운터를 짚고 진지하게 [Omni]"),
    # 아역 Typecast — (감정, 강도, 템포)
    "L02": (("normal", 0.8, 0.9), "쇼케이스 너머 수줍게 [Omni]"),
    "L03a": (("sad", 0.6, 0.9), "동전을 다시 세며 귀가 빨개짐 [Omni]"),
    "L03c": (("happy", 0.7, 1.0), "눈을 크게 뜸 [VO]"),
    "L06a": (("happy", 0.6, 0.95), "밝은 척, 동생에게 [VO·원경]"),
    "L06b": (("normal", 0.8, 0.9), "美緒 6세, 작게 [VO]"),
    "L08": (("sad", 0.6, 0.9), "수건을 받아 고개를 숙임 [VO]"),
    "L10": (("happy", 0.8, 1.0), "봉지를 안고 눈이 반짝 [Omni]"),
    "L10b": (("happy", 0.6, 1.0), "조금 자랑스럽게 [Omni]"),
    "L15": (("sad", 0.7, 0.9), "떨리는 목소리를 참음 [Omni]"),
    "L17": (("sad", 0.6, 0.9), "美緒, 작은 목소리 [VO]"),
    "L18": (("sad", 0.8, 0.88), "고개를 숙인 채 [VO]"),
    "L20": (("sad", 0.9, 0.9), "눈물을 참으며 고개를 저음 [VO]"),
    "L22": (("sad", 0.8, 0.88), "울음을 삼키고 [VO]"),
    "L22b": (("sad", 0.7, 0.9), "입술을 깨물고 [VO]"),
    "L23": (("sad", 0.6, 0.9), "아쉬운 얼굴 [Omni]"),
    "L26": (("happy", 0.6, 0.92), "젖은 눈으로 웃으며 [Omni]"),
    "L26a": (("happy", 0.6, 0.9), "美緒, 수줍게 [VO]"),
    "L26d": (("happy", 0.5, 0.92), "울음을 참으며 웃어 보임 [Omni]"),
    "L37": (("happy", 0.7, 1.05), "陽菜 8세, 美緒보다 빠르고 밝게 [VO]"),
    # 진행자 Yui Sato
    "OUT1": (("normal", 1.0, 0.95), "가슴 위 CU, 정중하게 [Omni]"),
    "OUT2": (("normal", 1.0, 0.92), "질문, 따뜻하게 [Omni]"),
    "OUT3": (("happy", 0.8, 0.95), "댓글 부탁 [Omni]"),
    "OUT4": (("happy", 1.0, 1.0), "구독 요청, 밝게 [Omni]"),
}

KANA = sorted(CAST_JSON["kana"].items(), key=lambda kv: -len(kv[0]))
KANA += [("三十年間", "さんじゅうねんかん"), ("二週間", "にしゅうかん"), ("五年前", "ごねんまえ"), ("十年前", "じゅうねんまえ"),
         ("一週間", "いっしゅうかん"), ("一度", "いちど"), ("二つ", "ふたつ"), ("一つ", "ひとつ"), ("一番", "いちばん"),
         ("一人", "ひとり"), ("三十年分", "さんじゅうねんぶん"), ("お代", "おだい"), ("お粥", "おかゆ"), ("看護師", "かんごし"),
         ("配膳", "はいぜん"), ("差出人", "さしだしにん"), ("便り", "たより"), ("坊主", "ぼうず"), ("給料", "きゅうりょう"), ("お母さん", "おかあさん"), ("病で", "やまいで"), ("妹", "いもうと"),
         ("「", ""), ("」", "")]
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
        if tag == "OUT0":
            continue  # 무언 몽타주
        spk = "NA" if tag.startswith("NA") else spk
        out.append((tag, spk, "Omni" in mode, text))
    return out


def check_length(tag, text):
    w = []
    sents = [x for x in re.split(r"(?<=[。！？])", text) if x.strip()]
    if len(sents) > 2:
        w.append(f"{tag}: 한 줄 {len(sents)}문장")
    for x in sents:
        n = len(re.sub(r"[「」\s]", "", x))
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
        r = roles["mio"] if role == "hina" else roles[role]  # 陽菜 = 美緒와 같은 목소리(고니감독님 선택), 연기로 구분
        if tag in SAME_AS:
            src = f"{SAME_AS[tag]} 녹음 재사용"
        elif isinstance(tone, tuple):
            emo, inten, tempo = tone
            tests.append({"id": lid, "model": "typecast-direct", "voice": r["voice_id"], "language": "jpn",
                          "text": kana(text), "subtitle": text, "emotion_preset": emo,
                          "emotion_intensity": inten, "tempo": tempo})
            chars_tc += len(text); src = f"Typecast {r['name']}"
        else:
            pace = NA_PACE + " " if role == "narr" else ""
            tests.append({"id": lid, "model": "elevenlabs-direct", "voice": r["voice_id"], "voice_name": r["name"],
                          "el_model": "eleven_v3", "text": f"{pace}{tone} {kana(text)}", "subtitle": text})
            chars_el += len(text) + len(tone) + 1; src = f"EL {r['name']}"
        tone_s = tone if isinstance(tone, str) else f"{tone[0]} {tone[1]} · tempo {tone[2]}"
        rows.append(f"| {n} | {tag} | {name} | {'Omni' if omni else '-'} | {text} | {tone_s} | {note} | {src} |")
    for tag, src_tag in SAME_AS.items():
        rows.append(f"| — | {tag} | 재사용 | | | | {src_tag}({idmap[src_tag]}) 음성을 후크 H1에 배치 | |")
    spec = {"_설명": f"『閉店間際の弁当屋』 본녹음(PHASE 1). build_tts.py 생성물 — 직접 고치지 말 것. EL {chars_el}자 · Typecast {chars_tc}자, fal 0.",
            "tts_model": "ssfm-v30", "language": "jpn", "tests": tests}
    json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "bento-tts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    md = ["# 『閉店間際の弁当屋』 줄별 톤 연출표 (PHASE 1 — 음성·표정·동작의 단일 출처, 제10장 7)", "",
          f"> build_tts.py 생성물. 녹음 {len(tests)}줄(EL {chars_el}자 · Typecast {chars_tc}자) + 재사용 {len(SAME_AS)}줄. "
          "EL 태그 = eleven_v3 연기 태그(영어 2~4단어, 대사 앞). 음성 입력은 가나 치환본, 자막은 대본 원문.", "",
          "| # | 태그 | 화자 | 립싱크 | 대사 | 톤 | 연기 메모(표정·동작) | 목소리 |", "|---|---|---|---|---|---|---|---|"] + rows
    if warns:
        md += ["", "## 경고", ""] + [f"- {w}" for w in warns]
    open(os.path.join(HERE, "05_톤연출표.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"녹음 {len(tests)}줄 · EL {chars_el}자 · Typecast {chars_tc}자 · 경고 {len(warns)}")
    for w in warns:
        print(" -", w)


if __name__ == "__main__":
    main()
