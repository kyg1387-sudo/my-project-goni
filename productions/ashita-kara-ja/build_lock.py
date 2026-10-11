#!/usr/bin/env python3
"""『明日から来なくていい』 PHASE 1 Lock 타임라인 — 실측 음성 길이로 줄별 타임코드·장면 경계·광고 지점을 고정한다.

규칙(버들잎 Lock에서 승인된 규칙 준수 조정안 + 이 작품 결정):
  같은 장면 안 대사 사이 0.6초(같은 화자)/0.8초(화자 바뀜), 대사 끝→컷 1.8초, 내레이션 끝→컷 1.0초,
  독립 무언 컷 2.5초, 인서트는 진행 중인 대사·내레이션 위로(한 줄이 3.5초마다 컷 1개를 덮음),
  후크 20초, 아웃트로 50초, 광고 지점은 NA11·NA16 끝 + 1.0초 여운(v1.1 결정 ④) 뒤 장면 경계(3:30·7:00 ±10초).
입력: assets/auditions/ashita-tts/lineNNN.mp3(실측), 00_script_ja.md(동결 대본), 02_카메라앵글설계.md(컷 수)
출력: 06_Lock타임라인.md, lock.json
"""
import collections, json, math, os, re, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIO = os.path.join(REPO, "assets", "auditions", "ashita-tts")
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, INSERT, PER_CUT, AD_TAIL = 0.6, 0.8, 1.8, 1.0, 2.5, 3.5, 1.0
HOOK, OUTRO = 20.0, 50.0
AD_AFTER = {"NA11": ("1차 광고", 210.0), "NA16": ("2차 광고", 420.0)}
SECTION_START = {"S01": "② 발단·갈등"}
MIN_TOTAL = 9 * 60 + 40


def speech_span(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    return idx[0] / 16000, idx[-1] / 16000


def scene_key(s):
    m = re.match(r"S(\d+)(b?)", s)
    return (int(m.group(1)), m.group(2))


def load_lines():
    """대본 §4에서 (태그, 화자, 장면) 순서 목록. build_tts_spec.py와 같은 순서(OUT3 제외)."""
    t = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 4-1.")[0]
    scene, out = "H", []
    for l in body.split("\n"):
        m = re.match(r"^(H\d|S\d+b?|OUT-\d)\b", l)
        if m:
            scene = m.group(1)
        m = re.match(r"^\s+((?:NA|L|OUT)\d+)\s*([^\s:「(]*)[^「\n]*「", l)
        if m and m.group(1) != "OUT3":
            tag = m.group(1)
            spk = "NA" if tag.startswith("NA") else "OUT" if tag.startswith("OUT") else m.group(2)
            out.append({"tag": tag, "spk": spk, "scene": scene})
    return out


def load_cuts():
    t = open(os.path.join(HERE, "02_카메라앵글설계.md"), encoding="utf-8").read()
    return {r.split("|")[1].strip(): len(r.split("|")[2].split("→"))
            for r in t.split("\n") if re.match(r"^\| S\d+b? \|", r)}


def tc(x):
    return f"{int(x // 60)}:{x % 60:05.2f}"


def build():
    lines, cuts = load_lines(), load_cuts()
    for n, x in enumerate(lines, 1):
        x["id"] = f"line{n:03d}"
        a, b = speech_span(os.path.join(AUDIO, x["id"] + ".mp3"))
        x["lead"], x["dur"] = a, b - a
    body = [x for x in lines if x["scene"].startswith("S")]
    scenes = collections.OrderedDict()
    for x in body:
        scenes.setdefault(x["scene"], []).append(x)
    order = sorted(set(cuts) | set(scenes), key=scene_key)
    t, srows, ads = HOOK, [], []
    for sid in order:
        ls = scenes.get(sid, [])
        cover = sum(max(1, math.ceil(x["dur"] / PER_CUT)) for x in ls)
        silent = max(0, cuts.get(sid, 0) - cover)
        start = t
        t += silent * INSERT
        for k, x in enumerate(ls):
            x["start"], x["end"] = t, t + x["dur"]
            t = x["end"]
            nxt = ls[k + 1] if k < len(ls) - 1 else None
            if x["tag"] in AD_AFTER:
                t += AD_TAIL
                ads.append((AD_AFTER[x["tag"]][0], t, AD_AFTER[x["tag"]][1], x["tag"]))
            elif nxt:
                t += GAP_SAME if nxt["spk"] == x["spk"] else GAP_CHANGE
        if ls and ls[-1]["tag"] not in AD_AFTER:
            t += TAIL_N if ls[-1]["spk"] == "NA" else TAIL_D
        srows.append((sid, start, t, silent, len(ls)))
    hook = [x for x in lines if x["scene"].startswith("H")]
    outro = [x for x in lines if x["scene"].startswith("OUT")]
    return lines, hook, outro, srows, ads, t


def main():
    lines, hook, outro, srows, ads, body_end = build()
    total = body_end + OUTRO
    problems = [f"{n} {tc(a)} (목표 {tc(g)})" for n, a, g, _ in ads if abs(a - g) > 10.0]
    if total < MIN_TOTAL:
        problems.append(f"전체 {tc(total)} < 9:40 — PHASE 2로 넘어가지 말고 대본(이야기 비트) 보강")
    hook_speech = sum(x["dur"] for x in hook)
    outro_speech = sum(x["dur"] for x in outro)
    md = ["# 『明日から来なくていい』 PHASE 1 Lock 타임라인", "",
          f"> 실측 음성(Typecast {len(lines)}줄, 앞뒤 무음 제외 발화 구간) + 규칙: 대사 사이 {GAP_SAME}/{GAP_CHANGE}초 · 대사 끝→컷 {TAIL_D}초 · "
          f"내레이션 끝→컷 {TAIL_N}초 · 독립 무언 컷 {INSERT}초 · 광고 여운 {AD_TAIL}초 · 후크 {HOOK:.0f}초 · 아웃트로 {OUTRO:.0f}초.",
          "> 생성기: `build_lock.py` (무료). **PHASE 3 샷 리스트는 이 타임코드를 기준으로 한다.**", "",
          "## 요약", "", "| 항목 | 값 |", "|---|---|",
          f"| 본편 끝 | {tc(body_end)} |", f"| 아웃트로 | {tc(body_end)} ~ {tc(total)} ({OUTRO:.0f}초) |",
          f"| **전체 길이** | **{tc(total)}** (엔드카드 제외, 기준 10:00~11:00·최소 9:40) |"]
    for n, a, g, tag in ads:
        md.append(f"| {n} | **{tc(a)}** ({tag} 끝 + {AD_TAIL}초, 목표 {tc(g)}, 차이 {a - g:+.1f}초) |")
    md.append(f"| 후크 음성 | NA0 {hook_speech:.1f}초 (H1은 L22 재사용) |")
    md.append(f"| 아웃트로 음성 | {outro_speech:.1f}초 (OUT3 예고 보류) |")
    md.append(f"| 판정 | {'✅ 통과' if not problems else '❌ ' + ' / '.join(problems)} |")
    md += ["", "## 구간 경계", "", "| 구간 | 시작 |", "|---|---|", "| ① 도입 후크 | 0:00.00 |"]
    for sid, a, b, _, _ in srows:
        if sid in SECTION_START:
            md.append(f"| {SECTION_START[sid]} | {tc(a)} |")
    md.append(f"| ③ 전개·위기 (1차 광고 직후) | {tc(ads[0][1])} |")
    md.append(f"| ④ 절정·결말 (2차 광고 직후) | {tc(ads[1][1])} |")
    md.append(f"| ⑤ 아웃트로 | {tc(body_end)} |")
    md += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 | 대사·내레이션 | 독립 무언 컷 |", "|---|---|---|---|---|---|"]
    for sid, a, b, s, n in srows:
        md.append(f"| {sid} | {tc(a)} | {tc(b)} | {b - a:.2f}s | {n} | {s} |")
    md += ["", "## 줄별 타임코드", "", "| 녹음 | 대본 | 화자 | 장면 | 시작 | 끝 | 길이 |", "|---|---|---|---|---|---|---|"]
    for x in lines:
        if "start" in x:
            md.append(f"| {x['id']} | {x['tag']} | {x['spk']} | {x['scene']} | {tc(x['start'])} | {tc(x['end'])} | {x['dur']:.2f}s |")
        else:
            md.append(f"| {x['id']} | {x['tag']} | {x['spk']} | {x['scene']} | (고정 구간) | | {x['dur']:.2f}s |")
    open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump({"hook": HOOK, "outro": OUTRO, "body_end": body_end, "total": total,
               "ads": [{"name": n, "at": a, "target": g, "after": tag} for n, a, g, tag in ads],
               "scenes": [{"id": s, "start": a, "end": b, "silent_cuts": k} for s, a, b, k, _ in srows],
               "lines": [{k: x.get(k) for k in ("id", "tag", "spk", "scene", "lead", "dur", "start", "end")} for x in lines]},
              open(os.path.join(HERE, "lock.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"전체 {tc(total)} / 광고 " + ", ".join(f"{n} {tc(a)}" for n, a, _, _ in ads))
    if problems:
        print("문제: " + " / ".join(problems))


if __name__ == "__main__":
    main()
