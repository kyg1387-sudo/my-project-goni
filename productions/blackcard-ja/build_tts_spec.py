#!/usr/bin/env python3
"""『ブラックカード』 PHASE 1 본녹음 스펙 생성기(무료). 00_script_ja.md(🔒 v1.0) → scripts/auditions/blackcard-tts.json
- 켄지·柴田·美咲·声 = ElevenLabs eleven_v3(elevenlabs-direct, 2026-11-01 정밀 분석 확정 캐스트), 진행자 OUT = Typecast Yui Sato.
- 음성 입력만 가나 치환(자막은 한자 유지). EL v3 연기 태그는 줄당 1개·짧게(제15장 ⑩): whisper→[whispers], sad→[sad], angry→[angry].
- 검사: 한 문장 30자·한 줄 2문장, 목소리 없는 화자 0, 톤 미지정 0.
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from build_script_docs import rows, emo, SPK_JA   # 대본 줄·감정 맵(단일 출처)

VOICE = {  # 2026-11-01 정밀 분석(F0·다이내믹·발화 속도·Whisper 전사) 확정
    "Kenji": ("Taniguchi", "AzXhp77fg6sHrgy2EtLn"),
    "Shibata": ("Jiro", "qrxCoXetZMROJh88P461"),
    "Misaki": ("Jun", "cijnU1nZEPfVNWVa4qoW"),
    "Concierge": ("Mio", "jDIcRgSETu4QTbxPgjmn"),
    "Guard": ("Jiro", "qrxCoXetZMROJh88P461"), "Driver": ("Jiro", "qrxCoXetZMROJh88P461"),
    "Clerk": ("Jiro", "qrxCoXetZMROJh88P461"), "Manager": ("Jiro", "qrxCoXetZMROJh88P461"), "President": ("Jiro", "qrxCoXetZMROJh88P461"),
}
KANA = [("蓮見商事", "はすみしょうじ"), ("六本木ルクスタワー", "ろっぽんぎルクスタワー"), ("高橋健二", "たかはしけんじ"), ("高橋", "たかはし"), ("健二", "けんじ"),
        ("柴田", "しばた"), ("美咲", "みさき"), ("判子", "はんこ"), ("希望退職", "きぼうたいしょく"), ("追い出し部屋", "おいだしべや"), ("退職金", "たいしょくきん"),
        ("三千二百十八円", "さんぜんにひゃくじゅうはちえん"), ("二千三百四十円", "にせんさんびゃくよんじゅうえん"), ("三千八百万円", "さんぜんはっぴゃくまんえん"),
        ("三千八百万", "さんぜんはっぴゃくまん"), ("午前十時四十五分", "ごぜんじゅうじよんじゅうごふん"), ("0.01%", "れいてんれいいちパーセント"),
        ("二十四時間", "にじゅうよじかん"), ("四十三歳", "よんじゅうさんさい"), ("四十三年目", "よんじゅうさんねんめ"), ("四十三", "よんじゅうさん"), ("十五年間", "じゅうごねんかん"),
        ("十五年", "じゅうごねん"), ("七日", "なのか"), ("六日", "むいか"), ("No.7", "ナンバーセブン"), ("No.1", "ナンバーワン"), ("No.6", "ナンバーシックス"),
        ("候補者", "こうほしゃ"), ("筆頭株主", "ひっとうかぶぬし"), ("所有権移転", "しょゆうけんいてん"), ("慰謝料", "いしゃりょう"), ("財産分与", "ざいさんぶんよ"),
        ("協議書", "きょうぎしょ"), ("家族カード", "かぞくカード"), ("精算", "せいさん"), ("有効期限", "ゆうこうきげん"), ("紋章", "もんしょう"), ("正面玄関", "しょうめんげんかん"),
        ("辞令", "じれい"), ("個室", "こしつ"), ("本日十二時", "ほんじつじゅうにじ"), ("午前零時", "ごぜんれいじ"), ("三十年", "さんじゅうねん"), ("三年", "さんねん"), ("一円", "いちえん"),
        ("一生", "いっしょう"), ("一点", "いってん"), ("一枚", "いちまい"), ("七人目", "しちにんめ"), ("十二時", "じゅうにじ"), ("十八時", "じゅうはちじ"), ("今朝", "けさ")]
TAG = {"whisper": "[whispers] ", "sad": "[sad] ", "angry": "[angry] "}
def kana(t):
    for a, b in KANA: t = t.replace(a, b)
    return t
OUT = [("OUT1", "最後までご覧いただき、ありがとうございます。"), ("OUT2", "皆様なら、残り六日で、誰に、最初に復讐しますか。"),
       ("OUT3", "コメントで、教えてください。チャンネル登録も、よろしくお願いします。"), ("OUT4", "次回、カードを落とした本当の持ち主が、明らかになります。それでは、また。")]
tests = []
for i, r in enumerate(rows, 1):
    e = emo(r); name, vid = VOICE[r["spk"]]
    text = TAG.get(e[0], "") + kana(r["ja"]).replace("――", "、").replace('"', "")
    tests.append({"id": f"line{i:03d}", "src": r["id"], "speaker": SPK_JA[r["spk"]], "model": "elevenlabs-direct", "voice": vid, "voice_name": name,
                  "el_model": "eleven_v3", "text": text, "_tone": f"{e[0]}/{e[1]}/{e[2]}", "_subtitle": r["ja"]})
n = len(tests)
for j, (oid, t) in enumerate(OUT, 1):
    tests.append({"id": f"line{n+j:03d}", "src": oid, "speaker": "진행자", "model": "typecast-direct", "voice": "tc_629fe972013e90b4db213fd8", "language": "jpn",
                  "text": kana(t), "emotion_preset": "normal", "emotion_intensity": 1.0, "tempo": 0.95, "_subtitle": t})
spec = {"_설명": "『ブラックカード』 PHASE 1 본녹음 131줄(본편 127 + OUT 4). 켄지 Taniguchi·柴田/보조 Jiro·美咲 Jun·声 Mio = ElevenLabs eleven_v3, 진행자 Yui Sato = Typecast. 음성 입력만 가나 치환, 자막은 한자(_subtitle). fal 지출 0. 생성: productions/blackcard-ja/build_tts_spec.py",
        "tc_model": "ssfm-v30", "language": "jpn", "tests": tests}
json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "blackcard-tts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
chars = sum(len(t["text"]) for t in tests)
print(f"tests {len(tests)} | EL chars {sum(len(t['text']) for t in tests if t['model']=='elevenlabs-direct')} | TC chars {sum(len(t['text']) for t in tests if t['model']!='elevenlabs-direct')}")
