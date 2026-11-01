#!/usr/bin/env python3
"""『ブラックカード』 PHASE 1 Lock 타임라인 — 실측 음성 길이로 줄별 타임코드·장면 경계·광고 지점을 고정한다(무료).
규칙(『引きこもり』 build_lock.py와 같은 값): 같은 화자 0.6초 / 화자 바뀜 0.8초, 대사 끝→컷 1.8초, 내레이션 끝→컷 1.0초,
장면 첫 줄 앞 무언 컷은 컷당 2.5초(LEAD), 아웃트로 30초. 후크는 S01(원안 그대로, 0:00부터 켄지 나레이션).
광고 지점 = L040 끝 + 1.0초(1차, 목표 3:30) / L071 끝 + 예고 카드 2.5초 + 1.0초(2차, 목표 7:00).
입력: assets/auditions/blackcard-tts/lineNNN.mp3(line001~line126 본편), build_script_docs.rows(🔒 v1.0 줄 순서)
출력: 06_Lock타임라인.md, lock.json
"""
import collections, json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from build_script_docs import rows, SPK_JA
AUDIO = os.path.join(REPO, "assets", "auditions", "blackcard-tts")
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, INSERT, AD_TAIL, OUTRO = 0.6, 0.8, 1.8, 1.0, 2.5, 1.0, 30.0
AD_AFTER = {"L040": ("1차 광고", 210.0), "L071": ("2차 광고", 420.0)}
AD_EXTRA = {"L071": 2.5}   # 예고 카드 「この後――妻が隠していたもの」
# 그 줄 앞 극적 멈춤(초) — 승인음 뒤 3초 무음, 「ただ、静かだった」 정적, 찢기 뒤, 암전 등(대본 6절 정점 효과음과 짝)
PAUSE = {"L031a": 3.0, "L037": 3.0, "L063": 1.5, "L068": 3.0, "L072": 0.5, "L079": 1.0, "L080a": 1.0, "L089": 1.0, "L103a": 1.0, "L105": 1.0}
LEAD = {"01": 1, "02": 1, "03": 1, "04": 1, "05": 1, "06": 1, "07": 4, "08": 1, "09": 1, "10": 1, "11": 1, "12": 1}
TRAIL = {"05": 1, "10": 1}
MID = {"L030": 1, "L032": 0, "L038": 1, "L046": 1, "L048a": 1, "L052": 1, "L054": 4, "L057": 1, "L059": 2, "L063": 2,
       "L070": 1, "L076": 1, "L081": 0, "L097": 0, "L098a": 1, "L100": 1, "L101": 1, "L105": 0, "L106": 0}
MIN_TOTAL, MAX_TOTAL = 9 * 60 + 40, 11 * 60
def speech_span(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    if len(idx) == 0: return 0.0, 0.0
    return idx[0] / 16000, idx[-1] / 16000
def tc(x): return f"{int(x // 60)}:{x % 60:05.2f}"
def build():
    lines = []
    for n, r in enumerate(rows, 1):
        x = {"id": f"line{n:03d}", "tag": r["id"], "spk": SPK_JA[r["spk"]], "scene": r["scene"], "type": r["type"], "ja": r["ja"]}
        p = os.path.join(AUDIO, x["id"] + ".mp3")
        if not os.path.exists(p): raise SystemExit(f"missing {p}")
        a, b = speech_span(p); x["lead"], x["dur"] = round(a, 3), round(b - a, 3)
        lines.append(x)
    scenes = collections.OrderedDict()
    for x in lines: scenes.setdefault(x["scene"], []).append(x)
    t, srows, ads = 0.0, [], []
    for sid in sorted(scenes):
        ls = scenes[sid]; start = t; t += LEAD.get(sid, 1) * INSERT; prev = None
        for x in ls:
            if prev: t += PAUSE.get(x["tag"], GAP_SAME if prev["spk"] == x["spk"] else GAP_CHANGE)
            elif x["tag"] in PAUSE: t += PAUSE[x["tag"]]
            t += MID.get(x["tag"], 0) * INSERT
            x["start"], x["end"] = round(t, 3), round(t + x["dur"], 3); t = x["end"]
            if x["tag"] in AD_AFTER:
                t += AD_EXTRA.get(x["tag"], 0) + AD_TAIL
                ads.append((AD_AFTER[x["tag"]][0], t, AD_AFTER[x["tag"]][1], x["tag"]))
            prev = x
        t += TAIL_N if ls[-1]["type"] == "narration" else TAIL_D
        t += TRAIL.get(sid, 0) * INSERT
        srows.append((sid, start, t, len(ls)))
    main_end = t; total = main_end + OUTRO
    s_hum = next(r[1] for r in srows if r[0] == "02"); s_clue = next(r[1] for r in srows if r[0] == "04")
    ratio = (s_clue - s_hum) / main_end
    return lines, srows, ads, main_end, total, ratio, s_clue
def main():
    lines, srows, ads, main_end, total, ratio, s_clue = build()
    ok = MIN_TOTAL <= total <= MAX_TOTAL
    md = ["# 『ブラックカード』 PHASE 1 Lock 타임라인 (실측)", "",
          "> 본녹음 실측(무음 제외 발화 길이) 기준. 후크 = S01 본편 안 + 본편 + 아웃트로 30초. 생성기 `build_lock.py`.", "",
          f"- **전체 길이: {tc(total)}** ({'✅ 9:40~11:00 안' if ok else '❌ 기준 밖'}) · 본편 끝 {tc(main_end)}",
          f"- 단서 지점(카드 발견 S04 시작): {tc(s_clue)} = 본편의 {s_clue / main_end * 100:.0f}% ({'✅ 35~40% 전' if s_clue / main_end < 0.40 else '❌'})",
          f"- 후크(S01) 끝: {tc(srows[0][2])} (목표 0:20~0:30)"]
    for name, at, target, tag in ads:
        d = at - target
        md.append(f"- **{name}**: {tc(at)} ({tag} 끝 뒤) · 목표 {tc(target)} 대비 {d:+.1f}초 {'✅' if abs(d) <= 10 else '⚠️ ±10초 초과'}")
    md += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 | 줄 수 |", "|---|---|---|---|---|"]
    md += [f"| S{s} | {tc(a)} | {tc(b)} | {b - a:.1f}초 | {n} |" for s, a, b, n in srows]
    md += ["", "## 줄별 타임코드", "", "| 녹음 | 대본 | 화자 | 장면 | 시작 | 끝 | 발화 |", "|---|---|---|---|---|---|---|"]
    md += [f"| {x['id']} | {x['tag']} | {x['spk']} | S{x['scene']} | {tc(x['start'])} | {tc(x['end'])} | {x['dur']:.2f}초 |" for x in lines]
    open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump({"hook": 0.0, "outro": OUTRO, "total": total, "body_end": main_end,
               "ads": [{"name": n, "at": round(a, 3), "target": tg, "after": tag} for n, a, tg, tag in ads],
               "scenes": [{"id": s, "start": round(a, 3), "end": round(b, 3), "lines": n} for s, a, b, n in srows], "lines": lines},
              open(os.path.join(HERE, "lock.json"), "w"), ensure_ascii=False, indent=1)
    print("\n".join(md[:9]))
if __name__ == "__main__":
    main()
