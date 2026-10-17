#!/usr/bin/env python3
"""『みすぼらしい老人は、財閥会長だった』 PHASE 1 Lock 타임라인 — 실측 음성 길이로 줄별 타임코드·장면 경계·광고 지점을 고정한다(무료).

규칙(『月に帰った』 build_lock.py와 같은 값): 같은 화자 0.6초 / 화자 바뀜 0.8초, 대사 끝→컷 1.8초, 내레이션 끝→컷 1.0초,
장면 첫 대사 앞 무언 컷은 컷당 2.5초(LEAD), 후크 20초(대본 H0~H3, 줄은 S10·S06 재사용), 아웃트로 30초(host-library 재사용 3컷 + 신규 1컷),
광고 지점 = NA11·NA14a 끝 + 1.0초 여운 뒤 장면 경계(3:30·7:00 ±10초). 극적 멈춤(PAUSE)은 그 줄 앞 간격을 대신한다.
입력: assets/auditions/beggar-tts/lineNNN.mp3, 00_script_ja.md(🔒 v1.0)
출력: 06_Lock타임라인.md, lock.json
"""
import collections, json, os, re, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIO = os.path.join(REPO, "assets", "auditions", "beggar-tts")
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, INSERT, AD_TAIL = 0.6, 0.8, 1.8, 1.0, 2.5, 1.0
HOOK, OUTRO = 20.0, 30.0
AD_AFTER = {"NA11": ("1차 광고", 210.0), "NA14a": ("2차 광고", 420.0)}
PAUSE = {"L38": 2.0, "L31": 1.0 + 3 * 0.5, "L48": 1.5}  # その子が 앞 2초 정적 / 榊 등장 정적 1초+구두 3걸음 / 한 입 먹고
# 장면별 첫 대사 앞 무언 컷 수(설정 컷·인서트·리액션) — 02_카메라앵글설계에서 확정 전 대본 지문 기준 값
LEAD = {"S01": 2, "S02": 2, "S03": 1, "S04": 2, "S05": 2, "S06": 2, "S07": 2, "S08": 1, "S09": 2, "S10": 2,
        "S11": 1, "S12": 2, "S13": 1, "S14": 2, "S15": 2, "S16": 2, "S17": 2}
# 장면 안 대사 사이에 끼는 무언 컷(지문: 間宮 휴대폰 내림, 영상 삭제 인서트, 눈물 등) — 그 줄 앞에 INSERT초씩
MID = {"L12b": 1, "L27b": 1, "L30a": 1, "L30b": 1, "L34": 1, "L45": 1, "L47": 0, "L48": 1, "L52": 1, "NA9": 0, "NA10": 1, "L22": 1, "L28": 1, "L40": 1}
MIN_TOTAL, MAX_TOTAL = 9 * 60 + 40, 11 * 60


def speech_span(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    return idx[0] / 16000, idx[-1] / 16000


def load_lines():
    t = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 5.")[0]
    scene, out = "H", []
    for l in body.split("\n"):
        m = re.match(r"^(H\d|S\d+|OUT\d)\b", l)
        if m:
            scene = "OUT" if m.group(1).startswith("OUT") else m.group(1)
            if m.group(1) == "OUT3":
                out.append({"tag": "OUT3", "spk": "OUT", "scene": "OUT"})
            continue
        m = re.match(r"^\s+((?:NA|L)\d+[a-z]?)\s*([^\s:「(\[]*)[^「\n]*「", l)
        if m:
            tag = m.group(1)
            out.append({"tag": tag, "spk": "NA" if tag.startswith("NA") else m.group(2), "scene": scene})
    return out


def tc(x):
    return f"{int(x // 60)}:{x % 60:05.2f}"


def build():
    lines = load_lines()
    for n, x in enumerate(lines, 1):
        x["id"] = f"line{n:03d}"
        a, b = speech_span(os.path.join(AUDIO, x["id"] + ".mp3"))
        x["lead"], x["dur"] = round(a, 3), round(b - a, 3)
    body = [x for x in lines if x["scene"].startswith("S")]
    scenes = collections.OrderedDict()
    for x in body:
        scenes.setdefault(x["scene"], []).append(x)
    t, srows, ads = HOOK, [], []
    for sid in sorted(LEAD, key=lambda s: int(s[1:])):
        ls = scenes.get(sid, [])
        start = t
        t += LEAD[sid] * INSERT
        prev = None
        for x in ls:
            if prev:
                t += PAUSE.get(x["tag"], GAP_SAME if prev["spk"] == x["spk"] else GAP_CHANGE)
            elif x["tag"] in PAUSE:
                t += PAUSE[x["tag"]]
            t += MID.get(x["tag"], 0) * INSERT
            x["start"], x["end"] = round(t, 3), round(t + x["dur"], 3)
            t = x["end"]
            if x["tag"] in AD_AFTER:
                t += AD_TAIL
                ads.append((AD_AFTER[x["tag"]][0], t, AD_AFTER[x["tag"]][1], x["tag"]))
            prev = x
        if ls:
            t += TAIL_N if ls[-1]["spk"] == "NA" else TAIL_D
        srows.append((sid, start, t, len(ls)))
    main_end = t
    total = main_end + OUTRO
    # 수모 구간 비율(제15장 24): 첫 모멸 S04 시작 → 단서 S06 시작
    s4 = next(r[1] for r in srows if r[0] == "S04")
    s6 = next(r[1] for r in srows if r[0] == "S06")
    ratio = (s6 - HOOK) / (main_end - HOOK)
    return lines, srows, ads, main_end, total, ratio, s4, s6


def main():
    lines, srows, ads, main_end, total, ratio, s4, s6 = build()
    ok = MIN_TOTAL <= total <= MAX_TOTAL
    md = ["# 『みすぼらしい老人は、財閥会長だった』 PHASE 1 Lock 타임라인 (실측)", "",
          f"> 본녹음 실측(무음 제외 발화 길이) 기준. 후크 {HOOK:.0f}초 + 본편 + 아웃트로 {OUTRO:.0f}초. 생성기 `build_lock.py`.", "",
          f"- **전체 길이: {tc(total)}** ({'✅ 9:40~11:00 안' if ok else '❌ 기준 밖'}) · 본편 끝 {tc(main_end)}",
          f"- 수모 구간 단서 지점: S06 {tc(s6)} = 본편의 {ratio * 100:.0f}% ({'✅ 35~40% 전' if ratio < 0.40 else '❌'})"]
    for name, at, target, tag in ads:
        d = at - target
        md.append(f"- **{name}**: {tc(at)} ({tag} 끝 + 1.0초) · 목표 {tc(target)} 대비 {d:+.1f}초 {'✅' if abs(d) <= 10 else '⚠️ ±10초 초과'}")
    md += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 | 줄 수 |", "|---|---|---|---|---|"]
    md += [f"| {s} | {tc(a)} | {tc(b)} | {b - a:.1f}초 | {n} |" for s, a, b, n in srows]
    md += ["", "## 줄별 타임코드", "", "| 녹음 | 대본 | 화자 | 장면 | 시작 | 끝 | 발화 |", "|---|---|---|---|---|---|---|"]
    md += [f"| {x['id']} | {x['tag']} | {x['spk']} | {x['scene']} | {tc(x['start']) if 'start' in x else '-'} | "
           f"{tc(x['end']) if 'end' in x else '-'} | {x['dur']:.2f}초 |" for x in lines]
    open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump({"total": total, "main_end": main_end, "ads": ads, "scenes": srows, "lines": lines},
              open(os.path.join(HERE, "lock.json"), "w"), ensure_ascii=False, indent=1)
    print("\n".join(md[:8]))


if __name__ == "__main__":
    main()
