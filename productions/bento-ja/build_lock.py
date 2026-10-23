#!/usr/bin/env python3
"""『閉店間際の弁当屋』(bento-ja) PHASE 1 Lock 타임라인 — 실측 음성 길이로 줄별 타임코드·장면 경계·광고 지점을 고정한다(무료).

규칙(『みすぼらしい老人』 build_lock.py와 같은 값): 같은 화자 0.6초 / 화자 바뀜 0.8초, 대사 끝→컷 1.8초, 내레이션 끝→컷 1.0초,
무언 동작 컷 2.5초(INSERT). 제18장 2에 따라 대본 지문의 동작 컷을 Lock 계산에 넣는다:
장면 머리(설정 컷) 1컷 + 첫 줄 앞 지문 줄 수 = LEAD, 줄 사이 지문 줄 수 = 그 줄 앞 MID.
후크 20초(H0 4 · H1 5 · H2 6 · H3 5), 아웃트로 30초, 광고 지점 = NA14·NA24 끝 + 1.0초 여운(3:30·7:00 ±10초).
L01(후크 H1)은 편지 낭독 L29 녹음을 재사용한다(build_tts.py SAME_AS).
입력: assets/auditions/bento-tts/lineNNN.mp3, 00_script_ja.md(🔒 v1.0)
출력: 06_Lock타임라인.md, lock.json
"""
import json, os, re, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIO = os.path.join(REPO, "assets", "auditions", "bento-tts")
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, INSERT, AD_TAIL = 0.6, 0.8, 1.8, 1.0, 2.5, 1.0
HOOK, OUTRO = 20.0, 30.0
AD_AFTER = {"NA14": ("1차 광고", 210.0), "NA24": ("2차 광고", 420.0)}
PAUSE = {"L35": 1.0 + 0.8}  # 9시 정각 문 종소리 → 정적 1초(룸톤) 뒤 첫마디
HOOK_AT = {"L01": 4.3, "NA0": 9.3}
SAME_AS = {"L01": "L29"}
CARDS = {"S12": 2.0}  # 무언 질문 카드(장면 머리, 2026-10-20 승인) — 2차 광고 지점 뒤라 광고 시각은 그대로
CLUE_SCENE = "S06"  # 단서(소년이 오지 않은 밤) + BGM 전환(제15장 24)
MIN_TOTAL, MAX_TOTAL = 9 * 60 + 40, 11 * 60
# 길이 보정(무료, 2026-10-20 실측 13:11 → 보정): ① 느린 목소리 배속(≤1.15, 제11장 4 상한, 피치 유지 atempo — 후처리에서 실제 적용)
# ② 내레이션·VO 줄(편지 낭독·짧은 대사) 앞 지문 컷은 그 목소리 아래에 깐다(B롤 위 VO — 컷이 첫마디보다 VO_LEAD초만 먼저 시작)
STRETCH = {}  # Shino 1.15·Chiemi 1.12 배속을 파일에 적용함(원본 assets/auditions/bento-tts-orig/, 제11장 4) — 이중 적용 금지
VO_UNDER, VO_LEAD = True, 0.8
VOICE_OF = {}
SKIP_ACTION = re.compile(r"^\s*(시점 자막|질문 카드|【|\(사운드|\(BGM|\(편지 낭독)")


def speech_span(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    return idx[0] / 16000, idx[-1] / 16000


def load():
    body = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read().split("## 4. 대본")[1].split("## 5.")[0]
    scenes, lines, scene, pend = [], [], None, 0
    for l in body.split("\n"):
        m = re.match(r"^(H\d|S\d+[a-z]?|OUT\d)\b", l)
        if m:
            scene = "OUT" if m.group(1).startswith("OUT") else m.group(1)
            if scene.startswith("S"):
                scenes.append({"id": scene, "lead": 1, "lines": []})  # 장면 머리 = 설정 컷 1개
            pend = 0
            if not scene.startswith("OUT"):
                continue
        m = re.match(r"^\s*((?:NA|L|OUT)\d+[a-z]?)\s*([^\s:「\[]*)[^\n]*?:「", l)
        if m:
            tag = m.group(1)
            if tag == "OUT0":
                continue
            x = {"tag": tag, "spk": "NA" if tag.startswith("NA") else m.group(2), "scene": scene, "mid": 0,
                 "vo": tag.startswith("NA") or "[VO]" in l}
            lines.append(x)
            if scene.startswith("S"):
                sc = scenes[-1]
                if sc["lines"]:
                    x["mid"] = pend
                else:
                    sc["lead"] += pend
                sc["lines"].append(x)
            pend = 0
            continue
        if scene and scene.startswith("S") and re.match(r"^\s*\(", l) and not SKIP_ACTION.match(l):
            pend += 1
    for sc in scenes:  # 마지막 줄 뒤 지문(여운 동작 컷)
        sc["tail_cuts"] = 0
    return scenes, lines


def tc(x):
    return f"{int(x // 60)}:{x % 60:05.2f}"


def build():
    scenes, lines = load()
    spec = json.load(open(os.path.join(REPO, "scripts", "auditions", "bento-tts.json"), encoding="utf-8"))
    VOICE_OF.update({t["id"]: t.get("voice_name", "") for t in spec["tests"]})
    tags = {x["tag"]: x for x in lines}
    for n, x in enumerate(lines, 1):
        x["id"] = f"line{n:03d}"
    for x in lines:
        src = tags[SAME_AS[x["tag"]]]["id"] if x["tag"] in SAME_AS else x["id"]
        a, b = speech_span(os.path.join(AUDIO, src + ".mp3"))
        f = STRETCH.get(VOICE_OF.get(src, ""), 1.0)
        x["lead"], x["dur"], x["audio"], x["stretch"] = round(a / f, 3), round((b - a) / f, 3), src, f
    t, srows, ads = HOOK, [], []
    for sc in scenes:
        start = t
        t += CARDS.get(sc["id"], 0.0)
        first_na = sc["lines"] and sc["lines"][0]["vo"]
        t += (VO_LEAD if (VO_UNDER and first_na and sc["lead"]) else sc["lead"] * INSERT)
        prev = None
        for x in sc["lines"]:
            if prev:
                t += PAUSE.get(x["tag"], GAP_SAME if prev["spk"] == x["spk"] else GAP_CHANGE)
            elif x["tag"] in PAUSE:
                t += PAUSE[x["tag"]]
            t += (VO_LEAD if x["mid"] else 0) if (VO_UNDER and x["vo"]) else x["mid"] * INSERT
            x["start"], x["end"] = round(t, 3), round(t + x["dur"], 3)
            t = x["end"]
            if x["tag"] in AD_AFTER:
                t += AD_TAIL
                ads.append((AD_AFTER[x["tag"]][0], t, AD_AFTER[x["tag"]][1], x["tag"]))
            prev = x
        if sc["lines"]:
            t += TAIL_N if sc["lines"][-1]["spk"] == "NA" else TAIL_D
        else:
            t += INSERT  # 대사 없는 장면(S15 액자 ECU)
        srows.append((sc["id"], start, t, len(sc["lines"]), sc["lead"], sum(x["mid"] for x in sc["lines"])))
    main_end = t
    total = main_end + OUTRO
    clue = next(r[1] for r in srows if r[0] == CLUE_SCENE)
    ratio = (clue - HOOK) / (main_end - HOOK)
    return lines, srows, ads, main_end, total, ratio, clue


def main():
    lines, srows, ads, main_end, total, ratio, clue = build()
    ok = MIN_TOTAL <= total <= MAX_TOTAL
    spoken = sum(x["dur"] for x in lines if x["scene"].startswith("S"))
    md = ["# 『閉店間際の弁当屋』 PHASE 1 Lock 타임라인 (실측) — 🔒 2026-10-20 고니감독님 확정", "",
          f"> 본녹음 실측(무음 제외 발화 길이) 기준. 후크 {HOOK:.0f}초 + 본편 + 아웃트로 {OUTRO:.0f}초. 지문 동작 컷 {INSERT}초씩 포함(제18장 2). 생성기 `build_lock.py`.", "",
          f"- **전체 길이: {tc(total)}** ({'✅ 9:40~11:00 안' if ok else '❌ 기준 밖'}) · 본편 끝 {tc(main_end)} · 본편 발화 합계 {spoken:.0f}초",
          f"- 단서 지점(소년이 오지 않은 밤 + BGM 전환): {CLUE_SCENE} {tc(clue)} = 본편의 {ratio * 100:.0f}% ({'✅ 40% 전' if ratio < 0.40 else '❌'})"]
    for name, at, target, tag in ads:
        d = at - target
        md.append(f"- **{name}**: {tc(at)} ({tag} 끝 + 1.0초) · 목표 {tc(target)} 대비 {d:+.1f}초 {'✅' if abs(d) <= 10 else '⚠️ ±10초 초과'}")
    md += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 | 줄 수 | 머리 컷 | 중간 컷 |", "|---|---|---|---|---|---|---|"]
    md += [f"| {s} | {tc(a)} | {tc(b)} | {b - a:.1f}초 | {n} | {ld} | {md_} |" for s, a, b, n, ld, md_ in srows]
    md += ["", "## 줄별 타임코드", "", "| 녹음 | 대본 | 화자 | 장면 | 시작 | 끝 | 발화 |", "|---|---|---|---|---|---|---|"]
    for x in lines:
        if x["tag"] in HOOK_AT:
            x["start"] = HOOK_AT[x["tag"]]; x["end"] = round(x["start"] + x["dur"], 3)
    md += [f"| {x['audio']} | {x['tag']} | {x['spk']} | {x['scene']} | {tc(x['start']) if 'start' in x else '-'} | "
           f"{tc(x['end']) if 'end' in x else '-'} | {x['dur']:.2f}초 |" for x in lines]
    open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump({"hook": HOOK, "outro": OUTRO, "total": round(total, 3), "body_end": round(main_end, 3),
               "ads": [{"name": n, "at": round(a, 3), "target": tg, "after": tag} for n, a, tg, tag in ads],
               "scenes": [{"id": s, "start": round(a, 3), "end": round(b, 3), "lines": n} for s, a, b, n, _, _ in srows],
               "lines": lines}, open(os.path.join(HERE, "lock.json"), "w"), ensure_ascii=False, indent=1)
    print("\n".join(md[:9]))


if __name__ == "__main__":
    main()
