#!/usr/bin/env python3
"""『ブラックカード』第2話 PHASE 1 Lock 타임라인 — 실측 음성으로 줄별 타임코드·장면 경계·광고 지점 고정(무료).
1화 build_lock.py와 같은 규칙: 같은 화자 0.6 / 화자 교체 0.8초, 대사 끝→컷 1.8, 내레이션 끝→컷 1.0초, 무언 컷 2.5초(INSERT),
아웃트로 30초, 전체(본편+아웃트로) 9:40~11:00, 광고 3:30·7:00 ±10초.
정점 정적(PAUSE)은 09_정점효과음설계.md T0~T10과 짝 — 길이 조정은 LEAD·MID(비주얼 비트)·삭제 줄·배속으로만(제20장 3).
사용법: python3 build_lock.py [--speed 1.05] [--cut L207,L218,...] [--add L286b] [--write]
"""
import argparse, collections, json, os, re, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIO = os.path.join(REPO, "assets", "auditions", "blackcard2-tts")
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, INSERT, AD_TAIL, OUTRO = 0.6, 0.8, 1.8, 1.0, 2.5, 1.0, 30.0
AD_AFTER = {"L252": ("1차 광고", 210.0), "L299": ("2차 광고", 420.0)}
AD_EXTRA = {"L299": 3.0}          # 예고 카드 『この後――十五年前、俺を"落とした"男の告白』
HOOK_LEAD = 0.5                   # 0~3.5초 BGM 없음 구간: 레코더 클릭 뒤 첫 마디
CARD = {"S14": 4.0}               # 후크 질문 카드 2.0 + 타이틀 2.0(직전 컷 블러 위, 암전 금지)
PAUSE = {"L222": 1.0, "L252": 2.0, "L266": 1.0, "L285": 1.5, "L315": 1.5, "L319": 2.0, "L322": 1.5, "L340a": 1.0, "L340c": 1.0, "L340i": 1.0}  # 2026-11-06 B안: 서명 직전·정산 취소 전화·마지막 대사
LEAD = {"S13": 0, "S14": 0, "S15": 0, "S16": 0, "S17": 0, "S18": 0, "S19": 0, "S20": 1, "S21": 1, "S22": 0, "S23": 1, "S24": 0}
MID = {"L203": 1, "L216": 1, "L234": 1, "L320": 1, "L323": 1}   # 2026-11-06 Lock: 핵심 발견 6곳만(제20장 3)
TRAIL = {"S24": 1.2}   # B안 마지막 컷: 대사 없는 창업자 초상 3.0초(얼굴 비노출)
MIN_TOTAL, MAX_TOTAL = 9 * 60 + 40, 11 * 60

def speech_span(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    return (idx[0] / 16000, idx[-1] / 16000) if len(idx) else (0.0, 0.0)

def script_rows():
    scene, rows = None, []
    for l in open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8"):
        m = re.match(r"\*\*(S\d+)", l)
        if m: scene = m.group(1)
        m = re.match(r"\s+(L\d{3}[a-z]?) ", l)
        if m and scene: rows.append((m.group(1), scene))
    sc = dict(rows)
    out = []
    for l in open(os.path.join(HERE, "05_톤연출표.md"), encoding="utf-8"):
        if not l.startswith("| line"): continue
        c = [x.strip() for x in l.strip("|").split("|")]
        out.append({"id": c[0], "tag": c[1], "spk": c[2], "scene": sc.get(c[1]), "type": "narration" if "(N)" in c[2] else "dialogue", "ja": c[4]})
    return out

def tc(x): return f"{int(x // 60)}:{x % 60:05.2f}"

def build(speed=1.0, cut=(), add=()):
    lines = []
    for x in script_rows():
        if x["tag"] in cut: continue
        p = os.path.join(AUDIO, x["id"] + ".mp3")
        a, b = speech_span(p); x["lead"], x["dur"] = round(a, 3), round((b - a) / speed, 3)
        lines.append(x)
    for a in add:   # (tag, after_tag, spk, scene, dur, ja)
        i = next(k for k, y in enumerate(lines) if y["tag"] == a[1])
        lines.insert(i + 1, {"id": a[0].lower().replace("l", "line", 1), "tag": a[0], "spk": a[2], "scene": a[3], "type": "dialogue", "ja": a[5], "lead": 0, "dur": round(a[4] / speed, 3)})
    scenes = collections.OrderedDict()
    for x in lines: scenes.setdefault(x["scene"], []).append(x)
    t, srows, ads = 0.0, [], []
    for sid, ls in scenes.items():
        start = t; t += LEAD.get(sid, 1) * INSERT + CARD.get(sid, 0) + (HOOK_LEAD if sid == "S13" else 0); prev = None
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
    return lines, srows, ads, t, t + OUTRO

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--cut", default="")
    ap.add_argument("--add-shacho", action="store_true", help="논리 검수표 ③-2 永瀬 1줄(L286b) 추정 3.0초 슬롯")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    cut = [c for c in a.cut.split(",") if c]
    add = [("L286b", "L286", "永瀬", "S18", 3.0, "社長は、何も知りません。封筒が来たら、判を押すだけです。")] if a.add_shacho else []
    lines, srows, ads, main_end, total = build(a.speed, cut, add)
    ok = MIN_TOTAL <= total <= MAX_TOTAL
    speech = sum(x["dur"] for x in lines)
    md = ["# 『ブラックカード』第2話 PHASE 1 Lock 타임라인 (실측)", "",
          f"> 본녹음 실측(무음 제외 발화) · 배속 {a.speed:.2f} · 삭제 {', '.join(cut) or '없음'} · 추가 {', '.join(x[0] for x in add) or '없음'}. 생성기 `build_lock.py`.", "",
          f"- **전체 길이: {tc(total)}** ({'✅ 9:40~11:00 안' if ok else '❌ 기준 밖'}) · 본편 끝 {tc(main_end)} · 발화 합계 {speech:.1f}초 · 비발화 {main_end - speech:.1f}초",
          f"- 후크(S13) 끝: {tc(srows[0][2])} (목표 0:20~0:30)"]
    for name, at, target, tag in ads:
        d = at - target
        md.append(f"- **{name}**: {tc(at)} ({tag} 끝 뒤) · 목표 {tc(target)} 대비 {d:+.1f}초 {'✅' if abs(d) <= 10 else '⚠️ ±10초 초과'}")
    md += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 | 줄 수 |", "|---|---|---|---|---|"]
    md += [f"| {s} | {tc(x)} | {tc(y)} | {y - x:.1f}초 | {n} |" for s, x, y, n in srows]
    md += ["", "## 줄별 타임코드", "", "| 녹음 | 대본 | 화자 | 장면 | 시작 | 끝 | 발화 |", "|---|---|---|---|---|---|---|"]
    md += [f"| {x['id']} | {x['tag']} | {x['spk']} | {x['scene']} | {tc(x['start'])} | {tc(x['end'])} | {x['dur']:.2f}초 |" for x in lines]
    print("\n".join(md[4:6] + [m for m in md if m.startswith("- **")][1:]))
    if a.write:
        open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
        json.dump({"speed": a.speed, "cut": cut, "add": [x[0] for x in add], "outro": OUTRO, "total": total, "body_end": main_end,
                   "ads": [{"name": n, "at": round(x, 3), "target": tg, "after": tag} for n, x, tg, tag in ads],
                   "scenes": [{"id": s, "start": round(x, 3), "end": round(y, 3), "lines": n} for s, x, y, n in srows], "lines": lines},
                  open(os.path.join(HERE, "lock.json"), "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
