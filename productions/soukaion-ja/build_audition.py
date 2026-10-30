#!/usr/bin/env python3
"""『63ヘルツ』(soukaion) PHASE 1 — ElevenLabs 오디션 스펙 생성기(무과금, EL 크레딧만).
입력: productions/soukaion-ja/audition_candidates.json  {"misaki": [{"name":..,"voice_id":..}, ...], ...}
출력: scripts/auditions/soukaion-el-audition.json  (eleven_v3 + 영어 연기 태그 2~4단어, 음성 입력은 가나 치환본, subtitle은 원문 — 제19장 2 ③)
규칙: 배역별 3명 × 대비 감정 2줄(美咲는 내레이션+대사 겸임이라 3줄). 읽기 위험 어휘(六十三ヘルツ·環境計量士·四〇二号室·内容証明)를 오디션 줄에 포함(제20장 1).
사용법: python3 productions/soukaion-ja/build_audition.py
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CAST = json.load(open(os.path.join(REPO, "scripts", "audio", "soukaion-cast-voices.json"), encoding="utf-8"))
KANA = sorted(CAST["kana"].items(), key=lambda kv: -len(kv[0]))
def kana(s):
    for a, b in KANA: s = s.replace(a, b)
    return s
LINES = {
 "misaki": [("NA24", "[calm, measured]", "三十八年間、工場や道路の音を測り続けた、元・環境計量士だった。"),
            ("NA28_35", "[low, slow, chilling]", "六十三ヘルツ。……私が、玄関の鍵を閉めた、十五分後だった。"),
            ("L12", "[choked, pleading whisper]", "……やめてください……お願いだから……")],
 "yui": [("L03", "[bright, childlike]", "ママ、これ。赤いの"),
         ("L32", "[sleepy, soft, hopeful]", "……ママ。上の人、もう怒ってない？")],
 "kuroki": [("L02", "[low, sneering, bored]", "うるせえな。気に入らないなら、お前らが出ていけよ"),
            ("L09", "[flat, dismissive]", "は？　俺、普通に生活してるだけだけど")],
 "ohno": [("L14_15", "[calm, slow, teaching]", "警察が聞いているのは、音の大きさです。私が見るのは、音の、形です"),
          ("L37", "[slow, tender, firm]", "妻には、間に合わなかった。……次は、あなたが、誰かの耳になりなさい")],
 "bengoshi": [("L27", "[calm, professional, intrigued]", "……これは、騒音の相談ではありませんね"),
              ("L30", "[calm, grave, low]", "騒音で有罪になった判例があります。……懲役です")],
 "keisatsu": [("L06", "[flat, official]", "上の方にはお伝えしました。ただ、個人間の問題ですので")],
 "kanri": [("L38", "[flat, clerical]", "四〇二号室は、解約となりました。内容証明は、確認しております")],
}
def main():
    cand = json.load(open(os.path.join(HERE, "audition_candidates.json"), encoding="utf-8"))
    tests, chars = [], 0
    for role, voices in cand.items():
        if role.startswith("_"): continue
        for v in voices:
            for lid, tag, text in LINES[role]:
                tests.append({"id": f"{role}_el_{v['name'].split(' ')[0]}_{lid}", "model": "elevenlabs-direct",
                              "voice": v["voice_id"], "voice_name": v["name"], "el_model": "eleven_v3",
                              "text": f"{tag} {kana(text)}", "subtitle": text})
                chars += len(text) + len(tag) + 1
    spec = {"_설명": f"『63ヘルツ』(soukaion) ElevenLabs 오디션 — build_audition.py 생성물. 배역 {len(cand)}개, 샘플 {len(tests)}개, EL 약 {chars}자 크레딧(fal 0). 직전 작품 확정 목소리·외국 억양 제외.", "tests": tests}
    json.dump(spec, open(os.path.join(REPO, "scripts", "auditions", "soukaion-el-audition.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"샘플 {len(tests)}개 · EL 약 {chars}자")
if __name__ == "__main__": main()
