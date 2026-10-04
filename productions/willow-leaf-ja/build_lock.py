#!/usr/bin/env python3
"""버들잎 PHASE 1 Lock 타임라인 — 실측 음성 길이로 줄별 타임코드·장면 경계·광고 지점을 고정한다.

규칙(사용자 승인 2026-10-04 「규칙 준수 조정안」):
  같은 장면 안 대사 사이 0.6초(같은 화자)/0.8초(화자 바뀜), 대사 끝→컷 1.8초, 내레이션 끝→컷 1.0초,
  독립 무언 컷 2.5초, 인서트는 진행 중인 대사·내레이션 위로(한 줄이 3.5초마다 컷 1개를 덮음),
  후크 20초, 아웃트로 50초, 광고 지점은 전환 문장 끝 + 0.9초 여운 뒤 장면 경계(3:30·7:00 ±10초).
입력: assets/auditions/yanagi-tts/lineNNN.mp3 (실측), 00_script_ja.md(동결 대본), 02_카메라앵글설계.md(컷 수)
출력: 06_Lock타임라인.md, lock.json
"""
import json, math, os, re, subprocess, collections
import numpy as np, imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FF = imageio_ffmpeg.get_ffmpeg_exe()
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, INSERT, PER_CUT, AD_TAIL = 0.6, 0.8, 1.8, 1.0, 2.5, 3.5, 0.9
HOOK, OUTRO = 20.0, 50.0
SECTION = {"S01": "② 발단·갈등"}
AD_AFTER = {"line024": ("1차 광고", 210.0), "line054": ("2차 광고", 420.0)}  # NA8 「水一杯の代償は…」 뒤 / 유나 「祖母です…」 뒤(수첩 인서트가 장면 경계)
INSERT_BY_SCENE = {f"S{i:02d}": 1.75 for i in range(2, 9)}  # 1차 광고를 3:40 안에 두기 위해 S02~S08 인서트(종이컵·버들잎·유리문)를 1.75초로


def speech_span(path):
    raw = subprocess.run([FF, "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    return idx[0] / 16000, idx[-1] / 16000  # 파일 안 발화 시작·끝(초)


def load_lines():
    t = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 4-1.")[0]
    scene, out, cur = "H", [], None
    for l in body.split("\n"):
        s = l.strip()
        m = re.match(r"^(H\d|S\d+(?:-\d)?)\b", s)
        if m:
            scene = m.group(1)
        m = re.match(r"^(NA\d+|[^\s:「→]{1,6}):(【OMNI】)?(\([^)]*\))?「(.*)$", s)
        if m:
            cur = {"scene": scene, "spk": m.group(1), "text": m.group(4)}
            out.append(cur)
            if s.endswith("」"):
                cur["text"] = cur["text"][:-1]; cur = None
        elif cur and s and not s.startswith("→"):
            cur["text"] += s
            if s.endswith("」"):
                cur["text"] = cur["text"][:-1]; cur = None
    return [x for x in out if x["spk"] != "진행자"][1:]  # H1은 line047 재사용


def load_cuts():
    t = open(os.path.join(HERE, "02_카메라앵글설계.md"), encoding="utf-8").read()
    body = t.split("## 3. 장면별 커버리지 표")[1].split("## 4.")[0]
    return {r.split("|")[1].strip(): len(r.split("|")[2].split("→")) for r in body.split("\n") if r.startswith("| S")}


def tc(x):
    return f"{int(x // 60)}:{x % 60:05.2f}"


def build(extra=None):
    extra = extra or {}
    lines, cuts = load_lines(), load_cuts()
    audio = os.path.join(REPO, "assets", "auditions", "yanagi-tts")
    for n, x in enumerate(lines, 1):
        x["id"] = f"line{n:03d}"
        a, b = speech_span(os.path.join(audio, x["id"] + ".mp3"))
        x["lead"], x["dur"] = a, b - a
    scenes = collections.OrderedDict()
    for x in lines:
        scenes.setdefault(re.match(r"S\d+", x["scene"]).group(0), []).append(x)
    order = sorted(set(list(cuts) + list(scenes)), key=lambda s: int(s[1:]))
    t, rows, srows, ads = HOOK, [], [], []
    for sid in order:
        ls = scenes.get(sid, [])
        cover = sum(max(1, math.ceil(x["dur"] / PER_CUT)) for x in ls)
        silent = max(0, cuts.get(sid, 0) - cover)
        start = t
        t += silent * INSERT_BY_SCENE.get(sid, INSERT) + extra.get(sid, 0.0)  # 장면 앞 설정·인서트 무언 컷
        for k, x in enumerate(ls):
            x["start"], x["end"] = t, t + x["dur"]
            t = x["end"]
            if k < len(ls) - 1:
                t += GAP_SAME if ls[k + 1]["spk"] == x["spk"] else GAP_CHANGE
            if x["id"] in AD_AFTER:
                # 광고 지점: 문장 끝 + 여운 0.9초 → 하드컷(장면 경계). 다음 줄 앞 간격은 컷 꼬리 규칙으로 대체
                if k < len(ls) - 1:
                    t -= GAP_SAME if ls[k + 1]["spk"] == x["spk"] else GAP_CHANGE
                t += AD_TAIL
                ads.append((AD_AFTER[x["id"]][0], t, AD_AFTER[x["id"]][1]))
            rows.append(x)
        if ls:
            last = ls[-1]
            if last["id"] not in AD_AFTER:
                t += TAIL_N if last["spk"].startswith("NA") else TAIL_D
        srows.append((sid, start, t, silent))
    return rows, srows, ads, t


def main():
    rows, srows, ads, end = build()
    # 광고 지점을 3:30·7:00에 맞추도록 앞 구간 무언 컷을 조정(±0.5~3초, 이야기 비트 안에서)
    extra = {}
    bad = [(n, a, g) for n, a, g in ads if abs(a - g) > 10.0]
    if bad:
        raise SystemExit("광고 지점이 ±10초를 벗어남: " + ", ".join(f"{n} {tc(a)}(목표 {tc(g)})" for n, a, g in bad))
    total = end + OUTRO
    sec_b = {}
    for sid, a, b, _ in srows:
        if sid in SECTION:
            sec_b[SECTION[sid]] = a
    sec_b["③ 전개·위기 (1차 광고 직후)"] = ads[0][1]
    sec_b["④ 절정·결말 (2차 광고 직후)"] = ads[1][1]
    md = ["# 『柳の葉と一杯の水』 PHASE 1 Lock 타임라인", "",
          "> 실측 음성(Typecast 78줄, 앞뒤 무음 제외 발화 구간) + 사용자 승인 규칙 준수 조정안(2026-10-04).",
          f"> 대사 사이 {GAP_SAME}/{GAP_CHANGE}초 · 대사 끝→컷 {TAIL_D}초 · 내레이션 끝→컷 {TAIL_N}초 · 독립 무언 컷 {INSERT}초 · 광고 여운 {AD_TAIL}초 · 후크 {HOOK:.0f}초 · 아웃트로 {OUTRO:.0f}초.",
          f"> 생성기: `productions/willow-leaf-ja/build_lock.py` (무료). **PHASE 3 샷 리스트는 이 타임코드를 기준으로 한다.**", "",
          "## 요약", "",
          f"| 항목 | 값 |", "|---|---|",
          f"| 본편 끝 | {tc(end)} |", f"| 아웃트로 | {tc(end)} ~ {tc(total)} ({OUTRO:.0f}초) |",
          f"| **전체 길이** | **{tc(total)}** (엔드카드 제외, 기준 10:00~11:00·최소 9:40) |"]
    for name, at, target in ads:
        md.append(f"| {name} | **{tc(at)}** (목표 {tc(target)}, 차이 {at - target:+.1f}초) |")
    md += ["", "## 구간 경계", "", "| 구간 | 시작 |", "|---|---|", f"| ① 도입 후크 | 0:00.00 |"]
    for k, v in sec_b.items():
        md.append(f"| {k} | {tc(v)} |")
    md.append(f"| ⑤ 아웃트로 | {tc(end)} |")
    md += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 | 독립 무언 컷 |", "|---|---|---|---|---|"]
    for sid, a, b, s in srows:
        md.append(f"| {sid} | {tc(a)} | {tc(b)} | {b - a:.2f}s | {s} |")
    md += ["", "## 줄별 타임코드", "", "| 줄 | 장면 | 화자 | 시작 | 끝 | 발화 | 대사 |", "|---|---|---|---|---|---|---|"]
    for x in rows:
        md.append(f"| {x['id']} | {x['scene']} | {x['spk']} | {tc(x['start'])} | {tc(x['end'])} | {x['dur']:.2f}s | {x['text'][:28]} |")
    md += ["", "- H1(0:02~0:09)은 line047 음성을 재사용한다. 아웃트로 진행자 4줄(line075~078)은 아웃트로 50초 안에 배치한다."]
    open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump({"rows": [{k: x[k] for k in ("id", "scene", "spk", "start", "end", "dur", "lead")} for x in rows],
               "scenes": srows, "ads": ads, "main_end": end, "total": total, "extra": extra},
              open(os.path.join(HERE, "lock.json"), "w"), ensure_ascii=False, indent=1)
    print(f"본편 {tc(end)} / 전체 {tc(total)} / 광고 " + ", ".join(f"{n} {tc(a)}" for n, a, _ in ads))


if __name__ == "__main__":
    main()
