# -*- coding: utf-8 -*-
"""블랙카드 1화: source/manifest.json → 00_script_ja.md(대본 4절)·05_톤연출표.md 생성.
가상 회사명 치환, 한 줄 2문장 분할, 30자 초과 검사(수동 OVERRIDE로 교정)."""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
M = json.load(open(HERE / "source/manifest.json", encoding="utf-8"))

SUBS = [("東都商事", "蓮見商事"), ("六本木グランドタワー", "六本木ルクスタワー"), ("ラ・ルミエール", "最上階のレストラン"),
        ("도토상사", "하스미상사"), ("롯폰기 그랜드타워", "롯폰기 룩스타워"), ("라 루미에르", "최상층 레스토랑")]
# 30자 초과·문장 분할 수동 교정 (line_id → [문장 조각…] 각 조각 = 새 줄)
OVERRIDE = {
 "L001": ["十五年、魂を削って尽くした会社。今朝、俺はゴミのように切り捨てられた。"],
 "L002": ["鼻で笑った上司。冷たく背を向けた妻。", "虫を見るような目で俺を見た、同期の連中。"],
 "L004": ["雨のアスファルトで拾ったのは、残高ゼロの通帳じゃなかった。"],
 "L005": ["日本の上位0.01%だけに許される。\"限度額なし\"のブラックカード。"],
 "L013": ["同期の柴田は、俺より三年早く部長になった。そして今日、俺に判子を押させる側に立っていた。"],
 "L021": ["金がないということは、こういうことだ。合法的に殺されても、文句を言えない。"],
 "L025": ["だが――その夜。あのビルの裏口、追い出された、まさにその場所で。"],
 "L026": ["つま先に当たった\"あるもの\"が、すべてを、ひっくり返した。"],
 "L029": ["だが、社員証をハサミで二つに切った、あの警備室に――。俺は、背を向けた。"],
 "L038": ["口座に一円もない男の手に、転がり込んだ。日本経済を動かす側の、\"力\"が。"],
 "L048": ["翌日。俺を切り捨てた男の前に立ったとき――", "あいつが浮かべた表情を、俺は、一生、忘れない。"],
 "L056": ["本日より、こちらはオーナー様のお席となっております。"],
 "L063": ["昨日まで俺を、犬のように使っていた男。俺の前で膝を折るまでにかかった時間は――二十四時間。"],
 "L069": ["胸がすく――という言葉の意味を、四十三年目に初めて知った。"],
 "L071": ["俺を捨てた妻が――オフィスのドアを叩き壊すように開けたのだ。"],
 "L082": ["泣きながら縋る彼女に、俺が渡したのは――離婚届じゃなかった。"],
 "L098": ["それは、十五年間、毎朝くぐってきたあのビルの――", "正面玄関に刻まれた紋章と、同じだった。"],
 "L106": ["次回――十五年前、俺を\"候補者\"に選んだのは誰か。No.1からNo.6は、どこへ消えたのか。"],
 "L107": ["そして期限の日。ビルと株と時計の請求書は、誰の手に渡るのか。"],
 "L108": ["見逃したくない方は、チャンネル登録と通知ベルをお願いします。"],
}
def sub(s):
    for a, b in SUBS: s = s.replace(a, b)
    return s
def sents(ja): return [x for x in re.split(r"(?<=[。！？])", ja) if x.strip()]
def nchars(s): return len(re.sub(r"[\s「」『』\"（）()―…]", "", s))

SPK_JA = {k: v["ja"] for k, v in M["characters"].items()}
SPK_STYLE = {"Kenji": "Kenji", "Shibata": "Shibata", "Misaki": "Misaki", "Concierge": "Koe", "Guard": "Staff", "Driver": "Staff", "Clerk": "Staff", "Manager": "Staff", "President": "President"}
SEG_JA = {"HOOK": "① 도입 후크", "ACT1": "② 발단·갈등", "ACT2": "② 발단·갈등(계속)", "ACT3": "③ 전개·위기", "CLIMAX": "④ 절정", "EPILOGUE": "④ 결말·다음 화 예고"}

# ---- 줄 전개
rows = []  # dict(id, src, seg, scene, spk, type, ja, ko, chars)
for t in M["timeline"]:
    if t["type"] not in ("narration", "dialogue"): continue
    ja = sub(t["text_ja"]); ko = sub(t["text_ko"])
    parts = OVERRIDE.get(t["line_id"]) or ([ja] if len(sents(ja)) <= 2 else None)
    if parts is None:
        ss = sents(ja); parts = ["".join(ss[i:i+2]) for i in range(0, len(ss), 2)]
    for i, p in enumerate(parts):
        lid = t["line_id"] + ("" if len(parts) == 1 else "abcdef"[i])
        rows.append(dict(id=lid, src=t["line_id"], seg=t["segment"], scene=t["scene"], spk=t["speaker"], type=t["type"],
                         ja=sub(p), ko=ko if i == 0 else "(앞 줄 분할)", chars=nchars(p)))
viol = []
for r in rows:
    for s in sents(r["ja"]):
        if len(s.strip()) > 30: viol.append((r["id"], len(s.strip()), s.strip()[:24]))
    if len(sents(r["ja"])) > 2: viol.append((r["id"], "2문장 초과", r["ja"][:24]))

# ---- 감정 맵 (Typecast ssfm-v30 프리셋)
def emo(r):
    s, seg, ja = r["spk"], r["seg"], r["ja"]
    if s == "Concierge": return ("normal", 0.9, 0.88, "감정 0, 콜센터보다 느리게. 금액·정산의 무게를 전혀 싣지 않음")
    if s == "Kenji" and r["type"] == "narration":
        if seg == "HOOK": return ("tonedown", 1.0, 1.06, "낮고 빠른 속삭임. 분노를 눌러서 표현, 문장 끝 내림")
        if seg == "EPILOGUE" and ("そう、思っていた" in ja or "七日。七人目" in ja): return ("whisper", 0.9, 0.9, "처음으로 흔들리는 톤. 세 단어를 끊어 읽음")
        if seg == "EPILOGUE" and ja.startswith("次回") or "チャンネル登録" in ja or "コメントで" in ja or "そして期限の日" in ja: return ("tonedown", 1.0, 0.98, "CTA도 켄지의 낮은 톤 유지, 유튜버 톤 금지")
        if seg == "ACT3" and ("静かだった" in ja or "雑音が" in ja or "胸がすく" in ja): return ("whisper", 0.8, 0.9, "숨만으로. BGM·환경음 0 구간")
        if seg == "CLIMAX": return ("tonedown", 1.0, 0.95, "차갑고 일정. 「柴田」 한 단어만 반 박자 쉼")
        return ("tonedown", 1.0, 1.0, "1인칭 회고 だ・である, 억제된 분노")
    if s == "Kenji":
        if "判子は" in ja: return ("tonedown", 0.8, 0.9, "柴田·美咲의 억양을 그대로 모방, 음량 절반. 세 번째는 거의 속삭임")
        if "座れ" in ja: return ("angry", 0.6, 1.0, "유일하게 힘을 주는 한 단어. 나머지는 경어로 평탄")
        if seg in ("ACT1", "ACT2") and ("十五年だぞ" in ja or "話を" in ja): return ("sad", 0.6, 0.9, "목이 메어 억누름(제19장 6). 큰 오열 금지")
        if seg == "ACT2" and ("あれを" in ja or "カードで" in ja or "銀座まで" in ja or "何でも" in ja): return ("tonedown", 0.9, 0.95, "짧게, 떨림은 손에만")
        if seg == "ACT2" and "オーナーになりたい" in ja: return ("tonedown", 1.0, 0.9, "망설임 없이, 「全部」는 끊어서")
        return ("tonedown", 1.0, 0.95, "대사는 나레이션보다 반 박자 느리고 작게")
    if s == "Shibata":
        if seg == "ACT1": return ("toneup", 0.9, 1.05, "동기를 깔보는 가벼운 투. 「だろ」「だよ」를 던지듯")
        return ("sad", 0.6, 0.95, "목소리가 갈라지기 직전의 긴장, 소리 지르지 않음")
    if s == "Misaki":
        if seg == "ACT1": return ("tonedown", 1.0, 1.0, "온도 없는 사무적 목소리. 「判子は――ここ」는 柴田과 같은 억양")
        return ("sad", 0.6, 0.9, "문장을 끝내지 못하고 끊김(――에서 반드시 정지). 눈물 목소리 과장 금지")
    if s == "President": return ("normal", 0.8, 1.0, "휴대폰을 보며 창백해짐, 말끝이 올라감")
    return ("normal", 0.9, 1.0, "접객 경어, 개성 없이")

VOICE = {"Kenji": "오디션(남성 40대 저음·속삭임 가능)", "Shibata": "오디션(남성 40대, 약간 높음)", "Misaki": "오디션(여성 40대, 차가움)",
         "Concierge": "오디션(여성, 사무적 — 전 화 고정)", "Guard": "Rex 후보", "Driver": "Rex 후보", "Clerk": "Rex 후보", "Manager": "Rex 후보", "President": "Poseidon 후보"}

# ---- 05_톤연출표.md
out = ["# 『ブラックカード』(第1話) 줄별 톤 연출표 (규칙 8-2 · 제10장 7 — 음성·표정·동작의 단일 출처)", "",
       f"> 검토판 v0.9 기준 {len(rows)}줄(원본 109줄을 한 줄 2문장 규칙으로 분할). 지정 없는 줄 0개. 생성기: `build_script_docs.py`(source/manifest.json).",
       "> 감정 프리셋은 Typecast ssfm-v30(normal·happy·sad·angry·tonedown·toneup·whisper). 켄지 나레이션은 전편 tonedown 기본, 정점만 whisper. 큰 오열(sad 1.0) 없음(제19장 6).",
       "> 가나 변형(음성 입력만): 蓮見商事→はすみしょうじ · 六本木ルクスタワー→ろっぽんぎルクスタワー · 高橋健二→たかはしけんじ · 柴田→しばた · 美咲→みさき · 判子→はんこ · 希望退職→きぼうたいしょく · 追い出し部屋→おいだしべや · 退職金→たいしょくきん · 三千二百十八円→さんぜんにひゃくじゅうはちえん · 二千三百四十円→にせんさんびゃくよんじゅうえん · 三千八百万円→さんぜんはっぴゃくまんえん · 三千八百万→さんぜんはっぴゃくまん · 午前十時四十五分→ごぜんじゅうじよんじゅうごふん · 上位0.01%→じょういれいてんれいいちパーセント · 二十四時間→にじゅうよじかん · 四十三歳→よんじゅうさんさい · 四十三年目→よんじゅうさんねんめ · 十五年→じゅうごねん · 七日→なのか · 六日→むいか · 候補者No.7→こうほしゃナンバーセブン · No.1→ナンバーワン · No.6→ナンバーシックス · 筆頭株主→ひっとうかぶぬし · 所有権移転→しょゆうけんいてん · 慰謝料→いしゃりょう · 財産分与→ざいさんぶんよ · 協議書→きょうぎしょ · 家族カード→かぞくカード · 精算→せいさん · 有効期限→ゆうこうきげん · 紋章→もんしょう · 正面玄関→しょうめんげんかん · 辞令→じれい · 個室→こしつ · 本日十二時→ほんじつじゅうにじ · 午前零時→ごぜんれいじ",
       "", "| 녹음 | 대본 | 화자 | 목소리 | 일본어 | 감정 | 강도 | 템포 | 연기 메모(표정·동작) |", "|---|---|---|---|---|---|---|---|---|"]
for i, r in enumerate(rows, 1):
    e = emo(r)
    out.append(f"| line{i:03d} | {r['id']} | {SPK_JA[r['spk']]} | {VOICE[r['spk']]} | {r['ja']} | {e[0]} | {e[1]} | {e[2]} | {e[3]} |")
(HERE / "05_톤연출표.md").write_text("\n".join(out), encoding="utf-8")

# ---- 대본 4절 블록 (장면별)
SCENE_HDR = {}
for s in M["scenes"]: SCENE_HDR[s["scene"]] = s["title"]
TAG = {"narration": "", "dialogue": " [Omni]"}
def tag(r):
    if r["type"] == "narration": return ""
    if r["chars"] <= 11: return " [VO]"
    return " [Omni]"
blocks = []; cur = None
for r in rows:
    if r["scene"] != cur:
        cur = r["scene"]; blocks.append(f"\nS{cur} — {sub(SCENE_HDR[cur])}")
    who = "" if r["type"] == "narration" else f" {SPK_JA[r['spk']]}"
    blocks.append(f"   {r['id']}{who}{tag(r)}:「{r['ja']}」\n   → {r['ko']}")
(HERE / "_script_body.md").write_text("\n".join(blocks), encoding="utf-8")
total = sum(r["chars"] for r in rows)
print("rows", len(rows), "chars", total, "| violations:", viol)
