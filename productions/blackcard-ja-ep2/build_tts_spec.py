#!/usr/bin/env python3
"""『ブラックカード』第2話 PHASE 1 본녹음 스펙 생성기(무료).
단일 출처 05_톤연출표.md(v1.4, 143줄 + OUT 4) → scripts/auditions/blackcard2-tts.json
- 목소리: 04_목소리추천.md 확정 캐스트(2026-11-05 고니감독님 「추천대로」). OUT = Typecast Yui Sato.
- 음성 입력만 가나 치환(자막은 한자 `_subtitle`). 표 머리말의 가나 목록 + 1화 공통 목록, 긴 낱말 먼저.
- v3 태그: whisper→[whispers], sad→[sad], angry→[angry], 표의 [태그] 메모는 그대로 앞에. 줄당 태그 최대 2개.
- 검사: 목소리 없는 화자 0, 2자 이하 줄 0, 치환 후 남은 한자 숫자 보고(읽기 위험).
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(HERE, "05_톤연출표.md")

VOICE = {  # 2026-11-05 확정(04_목소리추천.md)
    "健二": ("Taniguchi", "AzXhp77fg6sHrgy2EtLn"), "高橋 健二(N)": ("Taniguchi", "AzXhp77fg6sHrgy2EtLn"),
    "声": ("Mio", "jDIcRgSETu4QTbxPgjmn"), "美咲": ("Jun", "cijnU1nZEPfVNWVa4qoW"),
    "柴田": ("Jiro", "qrxCoXetZMROJh88P461"), "警備員": ("Jiro", "qrxCoXetZMROJh88P461"), "運転手": ("Jiro", "qrxCoXetZMROJh88P461"),
    "三好": ("Atsuji", "Ncfr0DOB9MiCWyPewqcL"), "鷺沼": ("Akio", "eRD4wLHoHH7P30TZIexm"),
    "No.1": ("Fumi", "jFC0UIEzTxa9AlmUpvLs"), "永瀬": ("Kaguya - Natural", "5sgRUBXTwmRGmFqEzLBa"),
    "案内音": ("Aiko", "qtZU80V9mb7jMTtOMfcs"),
}
KANA_EXTRA = [("高橋健二", "たかはしけんじ"), ("高橋", "たかはし"), ("健二", "けんじ"), ("柴田", "しばた"), ("美咲", "みさき"), ("判子", "はんこ"),
              ("希望退職", "きぼうたいしょく"), ("十五年前", "じゅうごねんまえ"), ("十五年", "じゅうごねん"), ("十二年", "じゅうにねん"), ("十年前", "じゅうねんまえ"),
              ("七番目", "ななばんめ"), ("七人目", "しちにんめ"), ("七枚目", "ななまいめ"), ("八枚目", "はちまいめ"), ("六つ目", "むっつめ"), ("七つ目", "ななつめ"),
              ("六人", "ろくにん"), ("六名様", "ろくめいさま"), ("七人", "しちにん"), ("三十人", "さんじゅうにん"), ("六枚", "ろくまい"), ("二年前", "にねんまえ"),
              ("一か月前", "いっかげつまえ"), ("先月", "せんげつ"), ("午前零時", "ごぜんれいじ"), ("六時間後", "ろくじかんご"), ("一人", "ひとり"), ("一日", "いちにち"),
              ("一点", "いってん"), ("一枚", "いちまい"), ("精算", "せいさん"), ("紋章", "もんしょう"), ("住民票", "じゅうみんひょう"), ("地下書庫", "ちかしょこ"),
              ("地下二階", "ちかにかい"), ("書庫", "しょこ"), ("常務", "じょうむ"), ("人事部長", "じんじぶちょう"), ("今朝", "けさ"), ("横浜", "よこはま"), ("三好", "みよし"), ("No.6", "ナンバーシックス"), ("をCに", "をシーに")]

lines = open(SRC, encoding="utf-8").read().splitlines()
head = next(l for l in lines if l.startswith("> 가나 변형"))
pairs = []
for item in head.split(":", 1)[1].split("·"):
    if "→" in item:
        a, b = item.strip().split("→", 1); pairs.append((a.strip(), b.strip()))
KANA = sorted(pairs + KANA_EXTRA, key=lambda p: -len(p[0]))
def kana(t):
    for a, b in KANA: t = t.replace(a, b)
    return t

TAG = {"whisper": "[whispers]", "sad": "[sad]", "angry": "[angry]"}
tests, err = [], []
for l in lines:
    if not l.startswith("| line"): continue
    c = [x.strip() for x in l.strip("|").split("|")]
    rec, src, spk, _v, ja, e, inten, tempo, memo = c[:9]
    if spk not in VOICE: err.append(f"{rec} 목소리 없음: {spk}"); continue
    name, vid = VOICE[spk]
    tags = []
    if TAG.get(e): tags.append(TAG[e])
    tags += [m for m in re.findall(r"\[[a-z ]+\]", memo) if m not in tags]
    body = kana(ja).replace("――", "、").replace('"', "")
    if len(re.sub(r"[、。！？…\s]", "", body)) <= 2: err.append(f"{rec} 2자 이하")
    if spk == "No.1" or "전화" in memo: pass  # 전화 EQ는 마스터링에서
    tests.append({"id": rec, "src": src, "speaker": spk, "model": "elevenlabs-direct", "voice": vid, "voice_name": name, "el_model": "eleven_v3",
                  "text": (" ".join(tags[:2]) + " " if tags else "") + body, "_tone": f"{e}/{inten}/{tempo}", "_memo": memo, "_subtitle": ja})

OUT = [("OUT1", "最後までご覧いただき、ありがとうございます。"), ("OUT2", "皆様なら、\"次の名前\"の欄に、誰の名前を書きますか。"),
       ("OUT3", "コメントで、教えてください。チャンネル登録も、よろしくお願いします。"), ("OUT4", "次回、横浜の港で、消えたはずの男が待っています。それでは、また。")]
n = len(tests)
for j, (oid, t) in enumerate(OUT, 1):
    tests.append({"id": f"line{200+n+j:03d}", "src": oid, "speaker": "진행자", "model": "typecast-direct", "voice": "tc_629fe972013e90b4db213fd8", "language": "jpn",
                  "text": kana(t).replace('"', ""), "emotion_preset": "normal", "emotion_intensity": 1.0, "tempo": 0.95, "_subtitle": t})

risk = sorted({m for t in tests for m in re.findall(r"[一二三四五六七八九十百千]+[^\s、。]?", t["text"])})
print("오류", len(err)); [print(" ", e) for e in err]
print("남은 한자 숫자(눈으로 확인):", " ".join(risk))
if err: sys.exit(1)
spec = {"_설명": f"『ブラックカード』第2話 PHASE 1 본녹음 {len(tests)}줄(본편 {n} + OUT {len(OUT)}). 확정 캐스트 04_목소리추천.md — "
                 "켄지 Taniguchi·声 Mio·美咲 Jun·柴田/경비원/운전사 Jiro·三好 Atsuji·鷺沼 Akio·No.1 Fumi·永瀬 Kaguya-Natural·안내음 Aiko(eleven_v3), 진행자 Yui Sato(Typecast). "
                 "음성 입력만 가나 치환, 자막은 한자(_subtitle). fal 지출 0. 생성: productions/blackcard-ja-ep2/build_tts_spec.py",
        "tc_model": "ssfm-v30", "language": "jpn", "tests": tests}
json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "blackcard2-tts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"tests {len(tests)} | EL chars {sum(len(t['text']) for t in tests if t['model']=='elevenlabs-direct')} | TC chars {sum(len(t['text']) for t in tests if t['model']!='elevenlabs-direct')}")
