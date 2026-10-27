#!/usr/bin/env python3
"""『引きこもりの息子』 PHASE 1 Lock 타임라인 — 실측 음성 길이로 줄별 타임코드·장면 경계·광고 지점을 고정한다(무료).

규칙(『月に帰った』 build_lock.py와 같은 값): 같은 화자 0.6초 / 화자 바뀜 0.8초, 대사 끝→컷 1.8초, 내레이션 끝→컷 1.0초,
장면 첫 대사 앞 무언 컷은 컷당 2.5초(LEAD), 후크 20초(대본 H0~H3, L01은 S05에서 재생), 아웃트로 30초(재사용 립싱크 + OUT3 신규),
광고 지점 = NA12 끝 + 1.0초 / NA21 끝 + 예고 카드 2.5초 + 1.0초 뒤 장면 경계(3:30·7:00 ±10초). 카운트다운 카드는 장면 꼬리(TRAIL). 극적 멈춤(PAUSE)은 그 줄 앞 간격을 대신한다.
입력: assets/auditions/hikikomori-tts/lineNNN.mp3, 00_script_ja.md(🔒 v1.0)
출력: 06_Lock타임라인.md, lock.json
"""
import collections, json, os, re, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIO = os.path.join(REPO, "assets", "auditions", "hikikomori-tts")
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, INSERT, AD_TAIL = 0.6, 0.8, 1.8, 1.0, 2.5, 1.0
HOOK, OUTRO = 20.0, 30.0
AD_AFTER = {"NA12": ("1차 광고", 210.0), "NA21": ("2차 광고", 420.0)}
AD_EXTRA = {"NA21": 2.5}  # 예고 카드 「この後――会議室の扉が開く」
PAUSE = {"L11": 1.5, "L45": 0.8 + 1.5, "L58": 1.0, "L56": 0.8}  # でも 앞 침묵 / 문 열림 정적+걸어 들어옴 / 되받아치기 앞 / 고개 숙이기 전
# 장면별 첫 대사 앞 무언 컷 수(설정 컷·인서트·리액션) — 02_카메라앵글설계에서 확정 전 대본 지문 기준 값
LEAD = {"S01": 2, "S02": 1, "S03": 1, "S04": 1, "S05": 1, "S06": 1, "S07": 1, "S08": 1, "S09": 2, "S10": 1, "S11": 1, "S12": 2,
        "S13": 0, "S14": 1, "S15": 1, "S16": 2, "S17": 2, "S18": 2, "S19": 0, "S20": 0, "S21": 1, "S22": 1, "S23": 1, "S24": 1}
TRAIL = {"S13": 1, "S14": 1, "S20": 1, "S22": 1, "S24": 2}  # 카운트다운 카드·버즈아이·리액션·엔딩 풀백
REPLAY_BEFORE = {"L10": "L01"}  # S05 「出ていけ！」 = L01 녹음 재생
# 장면 안 대사 사이에 끼는 무언 컷(지문: 間宮 휴대폰 내림, 영상 삭제 인서트, 눈물 등) — 그 줄 앞에 INSERT초씩
MID = {"L06": 1, "L10": 1, "L11": 1, "NA6": 1, "L13": 1, "L20": 1, "NA12": 1, "L23": 1, "L24": 1, "L26": 2, "NA18": 1,
       "L39": 1, "NA19a": 1, "NA21": 1, "L42": 1, "L43": 1, "L50": 1, "L51": 1, "L61": 1, "L64": 1, "NA22": 1}
HOOK_AT = {"L01": 0.4, "NA0": 8.6}
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
            if x["tag"] in REPLAY_BEFORE:  # 재사용 녹음 재생(앞 간격 + 발화)
                r = next(y for y in lines if y["tag"] == REPLAY_BEFORE[x["tag"]])
                t += GAP_SAME + r["dur"]
                x["replay_end"] = round(t, 3)
            if prev:
                t += PAUSE.get(x["tag"], GAP_SAME if prev["spk"] == x["spk"] else GAP_CHANGE)
            elif x["tag"] in PAUSE:
                t += PAUSE[x["tag"]]
            t += MID.get(x["tag"], 0) * INSERT
            x["start"], x["end"] = round(t, 3), round(t + x["dur"], 3)
            t = x["end"]
            if x["tag"] in AD_AFTER:
                t += AD_EXTRA.get(x["tag"], 0) + AD_TAIL
                ads.append((AD_AFTER[x["tag"]][0], t, AD_AFTER[x["tag"]][1], x["tag"]))
            prev = x
        if ls:
            t += TAIL_N if ls[-1]["spk"] == "NA" else TAIL_D
        t += TRAIL.get(sid, 0) * INSERT
        srows.append((sid, start, t, len(ls)))
    main_end = t
    total = main_end + OUTRO
    # 수모 구간 비율(제15장 24): 첫 모멸 S05 시작 → 단서 S09 시작
    s4 = next(r[1] for r in srows if r[0] == "S05")
    s6 = next(r[1] for r in srows if r[0] == "S09")
    ratio = (s6 - HOOK) / (main_end - HOOK)
    return lines, srows, ads, main_end, total, ratio, s4, s6


def main():
    lines, srows, ads, main_end, total, ratio, s4, s6 = build()
    ok = MIN_TOTAL <= total <= MAX_TOTAL
    md = ["# 『引きこもりの息子』 PHASE 1 Lock 타임라인 (실측)", "",
          f"> 본녹음 실측(무음 제외 발화 길이) 기준. 후크 {HOOK:.0f}초 + 본편 + 아웃트로 {OUTRO:.0f}초. 생성기 `build_lock.py`.", "",
          f"- **전체 길이: {tc(total)}** ({'✅ 9:40~11:00 안' if ok else '❌ 기준 밖'}) · 본편 끝 {tc(main_end)}",
          f"- 수모 구간 단서 지점: S09 {tc(s6)} = 본편의 {ratio * 100:.0f}% ({'✅ 35~40% 전' if ratio < 0.40 else '❌'})"]
    for name, at, target, tag in ads:
        d = at - target
        md.append(f"- **{name}**: {tc(at)} ({tag} 끝 + 1.0초) · 목표 {tc(target)} 대비 {d:+.1f}초 {'✅' if abs(d) <= 10 else '⚠️ ±10초 초과'}")
    md += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 | 줄 수 |", "|---|---|---|---|---|"]
    md += [f"| {s} | {tc(a)} | {tc(b)} | {b - a:.1f}초 | {n} |" for s, a, b, n in srows]
    md += ["", "## 줄별 타임코드", "", "| 녹음 | 대본 | 화자 | 장면 | 시작 | 끝 | 발화 |", "|---|---|---|---|---|---|---|"]
    md += [f"| {x['id']} | {x['tag']} | {x['spk']} | {x['scene']} | {tc(x['start']) if 'start' in x else '-'} | "
           f"{tc(x['end']) if 'end' in x else '-'} | {x['dur']:.2f}초 |" for x in lines]
    open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    for x in lines:  # 후크 줄(H0 L01 · H2 NA0) 고정 시각 — 후크 컷 길이 H0 3.0 / H1 5.0 / H2 7.0 / H3 5.0
        if x["tag"] in HOOK_AT:
            x["start"] = HOOK_AT[x["tag"]]; x["end"] = round(x["start"] + x["dur"], 3)
    replay = next(x for x in lines if x["tag"] == "L10")["replay_end"] - next(x for x in lines if x["tag"] == "L01")["dur"]
    json.dump({"hook": HOOK, "outro": OUTRO, "total": total, "body_end": main_end,
               "ads": [{"name": n, "at": round(a, 3), "target": tg, "after": tag} for n, a, tg, tag in ads],
               "scenes": [{"id": s, "start": round(a, 3), "end": round(b, 3), "lines": n} for s, a, b, n in srows],
               "replay": [{"tag": "L01", "start": round(replay, 3)}], "lines": lines},
              open(os.path.join(HERE, "lock.json"), "w"), ensure_ascii=False, indent=1)
    print("\n".join(md[:8]))


if __name__ == "__main__":
    main()
