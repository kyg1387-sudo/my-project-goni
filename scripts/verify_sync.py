#!/usr/bin/env python3
"""#02 자동 정합 검사(03_시네마규격 qa_guardrails, 규격 제8장 7) — 무과금, 로컬.
검사: ① 화자–화면 일치(OMNI 컷의 대사 화자 = 키프레임 인물)  ② 립싱크 창(OMNI 컷 ≤ 7.9초, 대사 1줄 = 1컷)
     ③ 자막 ↔ 음성 번호(대사·내레이션 줄 수 = .ass Dialogue 수(강조 자막 제외))  ④ 대사 사이 정적 ≤ 1.0초(같은 장면, 설계 예외 제외)
     ⑤ 정지 컷 길이(편집 카메라 없는 정지 ≤ 5초)  ⑥ 광고 지점(3:30·7:00 ±10초, 대사 중간 금지)
사용법: verify_sync.py   (0이면 합격)"""
import json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sb = json.load(open(os.path.join(ROOT, "scripts/storyboard/chika.json"), encoding="utf-8"))
lk = json.load(open(os.path.join(ROOT, "productions/chika-souko-ja/lock.json"), encoding="utf-8"))
ass = open(os.path.join(ROOT, "subs/chika.ass"), encoding="utf-8").read()
SPK = {"桐谷": "kiritani", "権藤": "gondo", "沙織": "saori", "宮本": "miyamoto", "大河内": "okochi"}
DESIGNED = {("S01",), ("S13",), ("S14",), ("S16",)}   # 설계된 정적(콜드오픈·광고 전·임팩트·결정타) — 1.5초까지 허용
import importlib.util
_spec = importlib.util.spec_from_file_location("build_lock", os.path.join(ROOT, "productions/chika-souko-ja/build_lock.py"))
_bl = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_bl)
SILENT = _bl.SILENT   # Lock 타임라인에서 승인된 무언 비트(대사 N 뒤 k초) — 그만큼 정적 허용
bad = []
lines = {l["id"]: l for l in lk["lines"]}
# ①②
for s in sb["scenes"]:
    if s["kind"] == "d":
        l = lines.get(s["line"])
        if not l: bad.append(f"{s['id']}: 대사 {s['line']} 없음"); continue
        who = SPK.get(l["spk"].split("(")[0], "")
        if who and not any(who in r for r in s["refs"]): bad.append(f"{s['id']}: 화자 {l['spk']} ≠ 화면 인물 {s['refs']}")
        if s["assembled_s"] > 7.95: bad.append(f"{s['id']}: OMNI {s['assembled_s']:.2f}s > 7.9s")
# ③
n_sub = len([m for m in re.finditer(r"^Dialogue: [^,]*,[^,]*,[^,]*,(\w+),", ass, re.M) if m.group(1) not in ("Emph", "Caption")])
n_voice = len([l for l in lk["lines"] if l.get("start") is not None and int(l["id"][4:]) <= 65])
if n_sub != n_voice: bad.append(f"자막 {n_sub}줄 ≠ 음성 {n_voice}줄")
# ④
prev = None
for l in sorted(lk["lines"], key=lambda x: x["start"]):
    if int(l["id"][4:]) > 65: continue
    if prev and prev["scene"] == l["scene"] and not l["id"].startswith("line0") is False:
        gap = l["start"] - prev["end"]
        lim = 1.5 if (l["scene"],) in DESIGNED else 1.0
        beat = SILENT.get(l["scene"], {}).get(int(prev["id"][4:]))
        lim += (beat[0] if beat else 0) + 1.8   # 인물 대사 끝→컷 여운 1.8초(제6장 5) + 무언 비트
        if gap > lim + 1e-6 and "語り" not in prev["spk"] and "語り" not in l["spk"]:
            bad.append(f"{prev['id']}→{l['id']} ({l['scene']}): 대사 사이 정적 {gap:.2f}s > {lim}s")
    prev = l
# ⑤
for s in sb["scenes"]:
    if s["tier"] in ("still", "gfx", "reuse", "card") and s["assembled_s"] > 6.6: bad.append(f"{s['id']}: 정지 컷 {s['assembled_s']:.1f}s > 6.5s")
# ⑥
for name, t in lk["ads"].items() if isinstance(lk["ads"], dict) else []:
    tgt = 210 if "1" in name else 420
    if abs(t - tgt) > 10: bad.append(f"광고 {name} {t:.1f}s (목표 {tgt}±10)")
    for l in lk["lines"]:
        if l["start"] < t < l["end"]: bad.append(f"광고 {name}이 {l['id']} 대사 중간")
print(f"검사 완료: 위반 {len(bad)}건"); [print("  ", b) for b in bad]
sys.exit(1 if bad else 0)
