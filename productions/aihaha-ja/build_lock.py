#!/usr/bin/env python3
"""『母が遺したビデオレター』 PHASE 1→3 Lock 타임라인 — 확정 본녹음(B안 템포 적용본)으로 줄별 타임코드·장면 경계·광고 지점을 고정(무료).
build_lock.py(hikikomori)를 옮김. 규칙: 같은 화자 0.6 / 화자 바뀜 0.8, 대사 끝→컷 1.8, 내레이션 끝→컷 1.0, 무언 컷 2.5초(INSERT).
후크는 줄을 순서대로 놓고(H0 L01·L02 → H1 NA0 → H2 NA1) 질문 카드 2.0초 + 타이틀 3.0초. 아웃트로 30초(OUT1~5 진행자).
광고 = NA13 끝 + 1.0초(3:30) / NA28 끝 + 예고 카드 2.5초 + 1.0초(7:00), ±10초.
입력: assets/auditions/aihaha-tts-b/lineNNN.mp3(pace_variant.py 결과 = lock_tempo·쉼 압축 적용), 00_script_ja.md(🔒 v1.1)
출력: 06_Lock타임라인.md, lock.json
"""
import collections, json, os, re, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIO = os.path.join(REPO, "assets", "auditions", "aihaha-tts-b")
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, INSERT, AD_TAIL = 0.6, 0.8, 1.8, 1.0, 2.5, 1.0
HOOK_LEAD, HOOK_CARD, HOOK_TITLE, OUTRO = 0.4, 2.0, 2.5, 28.0
AD_AFTER = {"NA13": ("1차 광고", 210.0), "NA28": ("2차 광고", 420.0)}
AD_EXTRA = {"NA28": 2.5}  # 예고 카드 「この後――母の動画が、もう一度流れる」
PAUSE = {"L35": 1.5, "L46": 1.5, "L56": 1.5, "L57a": 3.0}  # AI 실언 앞 정적 / 결정타 한 박자 / LINE 재생 탭 / 3초 정적
# 장면 첫 대사 앞 무언 컷 수(대본 지문)
LEAD = {"S01": 1, "S02": 1, "S03": 0, "S04": 1, "S05": 0, "S06": 0, "S07": 1, "S08": 1, "S09": 1, "S10": 0, "S11": 1, "S12": 0, "S13": 0}
# 내레이션 아래에 겹쳐 보여 주는 인서트(시간 추가 없음 — 화면이 그 문장의 그림, 제0장 4 「이야기 비트로 채우고 여운으로 끌지 않는다」)
UNDER = {"S01": "약통·산책 몽타주 → NA2·NA3", "S03": "CCTV → NA8", "S05": "태블릿 창 확대 → NA14", "S06": "차용증 넘기는 손 → NA18",
         "S12": "빈 집 앞 뒷모습 → NA32", "S13": "LINE 화면·재생 탭 → NA34",
         "NA5": "손목시계 차는 손", "NA8a": "열린 빈 서랍", "NA18b": "인지 자리 짚는 검지", "NA20": "개시 결과 「該当なし」 3장", "NA22": "돌봄 카메라 영상",
         "NA24a": "LINE 동영상 쌓임", "NA25": "손목시계 초침 ECU", "NA28": "달력 10月3日", "NA15": "실제 창(완공) 정지", "L52": "핸드백 쥔 손(L51 위)"}
TRAIL = {"S11": 1, "S13": 1}  # 버즈아이 / 엔딩 여운
# 대사 사이 무언 컷(지문) — 그 줄 앞에 INSERT초씩
MID = {"NA24b": 1, "L26": 1, "L37": 1}  # 펜 끝 인서트(BGM 0) / 형광등 스위치 / 翔太 핏기 가심(무언) — 정적이 연출인 곳만
MID_EXTRA = {"NA25": 3.0}  # 펜이 멈추는 무언 3초(NA24c 뒤, 시계 초침만)
MIN_TOTAL, MAX_TOTAL = 9 * 60 + 40, 11 * 60 + 15  # 제0장 「10~11분 내외」


def speech_span(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    return idx[0] / 16000, idx[-1] / 16000


def load_lines():
    t = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read()
    assert "🔒 v1.1" in t.splitlines()[0]
    body = t.split("## 4. 대본")[1].split("## 5.")[0]
    scene, out = "H0", []
    for l in body.split("\n"):
        m = re.match(r"^(H\d|S\d+|OUT\d)\b", l)
        if m:
            scene = "OUT" if m.group(1).startswith("OUT") else m.group(1)
        m2 = re.match(r'^\s*((?:NA|L|OUT)\d+\w*)\s*([^:「]*?)\s*[:：]\s*「(.+)」\s*$', l)  # build_tts_spec.py LINE_RE와 같음
        if m2:
            tag = m2.group(1)
            spk = "NA" if tag.startswith("NA") else "OUT" if tag.startswith("OUT") else (m2.group(2).split() or [""])[0]
            out.append({"tag": tag, "spk": spk, "scene": "OUT" if tag.startswith("OUT") else scene})
    return out


def tc(x):
    return f"{int(x // 60)}:{x % 60:05.2f}"


def build():
    lines = load_lines()
    assert len(lines) == 118, len(lines)
    for n, x in enumerate(lines, 1):
        x["id"] = f"line{n:03d}"
        a, b = speech_span(os.path.join(AUDIO, x["id"] + ".mp3"))
        x["lead"], x["dur"] = round(a, 3), round(b - a, 3)
    # 후크: 줄을 순서대로
    t, prev = HOOK_LEAD, None
    for x in [y for y in lines if y["scene"].startswith("H")]:
        if prev:
            t += GAP_SAME if prev["spk"] == x["spk"] else GAP_CHANGE
        x["start"], x["end"] = round(t, 3), round(t + x["dur"], 3); t = x["end"]; prev = x
    hook = round(t + 0.6 + HOOK_CARD + HOOK_TITLE, 3)
    scenes = collections.OrderedDict()
    for x in lines:
        if x["scene"].startswith("S"):
            scenes.setdefault(x["scene"], []).append(x)
    t, srows, ads = hook, [], []
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
            t += MID.get(x["tag"], 0) * INSERT + MID_EXTRA.get(x["tag"], 0)
            x["start"], x["end"] = round(t, 3), round(t + x["dur"], 3)
            t = x["end"]
            if x["tag"] in AD_AFTER:
                t += AD_EXTRA.get(x["tag"], 0) + AD_TAIL
                ads.append((AD_AFTER[x["tag"]][0], t, AD_AFTER[x["tag"]][1], x["tag"]))
            prev = x
        if ls and ls[-1]["tag"] not in AD_AFTER:
            t += TAIL_N if ls[-1]["spk"] == "NA" else TAIL_D
        t += TRAIL.get(sid, 0) * INSERT
        srows.append((sid, start, t, len(ls)))
    main_end = t
    total = main_end + OUTRO
    s2 = next(r[1] for r in srows if r[0] == "S02"); s5 = next(r[1] for r in srows if r[0] == "S05")
    ratio = (s5 - hook) / (main_end - hook)
    return lines, srows, ads, hook, main_end, total, ratio, s5


def main():
    lines, srows, ads, hook, main_end, total, ratio, s5 = build()
    ok = MIN_TOTAL <= total <= MAX_TOTAL
    md = ["# 『母が遺したビデオレター』 PHASE 1 Lock 타임라인 (실측 · B안 템포 · 대본 v1.1)", "",
          f"> 확정 본녹음(`aihaha-tts-b`, 템포·쉼 압축 적용) 발화 길이 기준. 후크 {hook:.1f}초 + 본편 + 아웃트로 {OUTRO:.0f}초. 생성기 `build_lock.py`.", "",
          f"- **전체 길이: {tc(total)}** ({'✅ 9:40~11:00 안' if ok else '❌ 기준 밖'}) · 본편 끝 {tc(main_end)} · 후크 {hook:.1f}초",
          f"- 수모 구간(첫 모멸 S02 → 단서 S05 비계): 본편의 {ratio * 100:.0f}% ({'✅ 40% 전' if ratio < 0.40 else '⚠️'})"]
    for name, at, target, tag in ads:
        d = at - target
        md.append(f"- **{name}**: {tc(at)} ({tag} 끝 + 여운) · 목표 {tc(target)} 대비 {d:+.1f}초 {'✅' if abs(d) <= 10 else '⚠️ ±10초 초과'}")
    md += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 | 줄 수 |", "|---|---|---|---|---|"]
    md += [f"| {s} | {tc(a)} | {tc(b)} | {b - a:.1f}초 | {n} |" for s, a, b, n in srows]
    md += ["", "## 줄별 타임코드", "", "| 녹음 | 대본 | 화자 | 장면 | 시작 | 끝 | 발화 |", "|---|---|---|---|---|---|---|"]
    md += [f"| {x['id']} | {x['tag']} | {x['spk']} | {x['scene']} | {tc(x['start']) if 'start' in x else '-'} | "
           f"{tc(x['end']) if 'end' in x else '-'} | {x['dur']:.2f}초 |" for x in lines]
    open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump({"hook": hook, "outro": OUTRO, "total": total, "body_end": main_end,
               "ads": [{"name": n, "at": round(a, 3), "target": tg, "after": tag} for n, a, tg, tag in ads],
               "scenes": [{"id": s, "start": round(a, 3), "end": round(b, 3), "lines": n} for s, a, b, n in srows],
               "under": UNDER, "lines": lines}, open(os.path.join(HERE, "lock.json"), "w"), ensure_ascii=False, indent=1)
    print("\n".join(md[:9]))
    for s, a, b, n in srows: print(s, tc(a), tc(b), f"{b-a:.1f}s", n)


if __name__ == "__main__":
    main()
