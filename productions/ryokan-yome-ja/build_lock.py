#!/usr/bin/env python3
"""#03 『老舗旅館の嫁』 PHASE 1 Lock 타임라인 — 실측 음성 길이로 줄별 타임코드·장면 경계·광고 지점·전체 길이를 고정한다.

규칙(CLAUDE.md 제0장·제6장 5, #02 build_lock.py 계승):
  같은 장면 대사 사이 0.6초(같은 화자)/0.8초(화자 바뀜) — 톤 연출표의 앞·뒤 쉼이 더 길면 그 값,
  장면 끝: 인물 대사 끝→컷 1.8초 / 내레이션 끝→컷 1.0초,
  무언 비트(SILENT)는 대사가 덮지 않는 화면 시간, 광고 지점 = 전환 문장 끝 + 0.9초 여운 = 장면 경계.
입력: assets/auditions/ryokan-tts/lineNNN.mp3(실측, 교정 채택본), 00_script_ja.md, build_tts.T(톤 연출표)
출력: 06_Lock타임라인.md, lock.json
사용법: python3 productions/ryokan-yome-ja/build_lock.py
"""
import json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from build_tts import T, load_lines, SAME_AS

AUDIO = os.path.join(REPO, "assets", "auditions", "ryokan-tts")
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, AD_TAIL = 0.6, 0.8, 1.8, 1.0, 0.9
AD_AFTER = {31: ("1차 광고", 210.0), 59: ("2차 광고", 420.0)}  # NA12 「すべての始まりだった」 뒤 / NA27 「その頃――私は」 뒤
MIN_TOTAL = 580.0  # 9:40
OMNI_WARN = 7.4

# 장면별 무언 비트(초): "pre" = 첫 줄 앞, 숫자 n = n번 줄 뒤, "post" = 마지막 줄 뒤. 비트 하나당 2~4초(제0장 4: 여운으로 끌지 않는다).
SILENT = {
    "S01": {"pre": (2.5, "★ 떨리는 수화기 손 인서트(얼굴 없음), 하나이카다 사무실 밤"), 2: (2.0, "전화를 내려놓는 손, 꺼지는 화면"),
            "post": (3.5, "타이틀 『老舗旅館の嫁』 직전 컷 블러 위(암전 0) → 「三か月前」 소자막 디졸브")},
    "S02": {"pre": (2.5, "어둠 속 주방, 형광등 점등 → 가마솥 김"), 6: (2.0, "몽타주 디졸브 3컷: 가마솥 뚜껑 / 도마·식칼 / 밝아 오는 창"), 7: (1.0, "노트북 앞 와카나, 전화를 어깨에")},
    "S03": {"pre": (1.5, "현관, 서양인 가족에게 영어 응대(무언)"), 9: (2.5, "★ 단골 노부부가 신을 벗으며 와카나를 보고 웃음(와이드 투샷, 카메오)"), "post": (1.0, "와카나의 접객 미소 여운")},
    "S04": {"pre": (1.5, "주방 뒷문, 도미코의 빈손"), 13: (2.0, "와카나 고개 숙임 → 식칼을 도마에 「톡」(손 인서트)")},
    "S05": {"pre": (1.5, "부부의 방, 휴대폰 불빛 아래 다카유키"), 17: (2.0, "와카나 옆얼굴, 눈만 흔들림(정지 푸시인)"), "post": (1.5, "밤 11시 사무실, 장부 덮고 스탠드 「딸깍」 → 디졸브")},
    "S06": {"pre": (3.0, "★ 현관 설정샷 — 전경 도미코·마이, 후경 복도 끝 걸레질 와카나(랙 포커스)"), 20: (2.0, "걸레를 쥔 손이 멈춤 → 걸레질 소리 끊김, 0.7초 정적")},
    "S07": {"pre": (2.0, "좌시키 설정샷(하이앵글 4인)"), 23: (1.0, "찻잔 내려놓는 인서트"), 26: (3.0, "다카유키 리액션 — 고개 숙이고 찻잔만(무언)"),
            28: (2.5, "★ 와카나가 천천히 고개를 든다, 해방의 옅은 미소(슬로 푸시인 → 초커)"), 30: (1.5, "깊이 절하는 와카나, 평온한 얼굴")},
    "S08": {"pre": (3.5, "★ 아침 빈 방, 문틀을 통과해 책상으로(푸시 패스트), 새소리"), 33: (2.0, "파일 표지에서 떨어지는 손, 이혼 신고서 봉투(오버헤드)")},
    "S09": {36: (1.5, "휴지통 속 파일 인서트(완충) → 디졸브")},
    "S10": {"pre": (2.0, "「あと三日」 소자막 → 번역 앱 휴대폰을 내미는 마이"), 38: (3.0, "★ 열쇠를 두고 다투는 두 가족, 뒤에서 쩔쩔매는 마이(핸드헬드)"), 40: (1.5, "노트북 화면에 쌓이는 영어 메일(lcd, 글자 흐림)")},
    "S11": {"pre": (2.0, "객실 상에 놓이는 찻잔 → 노부인의 손이 멈춤"), 42: (3.0, "리뷰 화면 4.8→3.1 그래픽(lcd) 하드컷, 알림음 3연타"), "post": (2.0, "비 내리는 쓰키미소 노렌(무인 완충) → 디졸브")},
    "S12": {"pre": (2.0, "하나이카다 사무실 낮, 찻잔을 건네는 사쿠라이"), 48: (2.0, "와카나 리액션 — 입을 가리고 웃을 듯, 눈가 젖음(정지 푸시인)")},
    "S13": {"pre": (2.5, "「繁忙期、初日」 소자막 → 쉴 새 없이 울리는 프런트 전화, 수화기 드는 도미코"), 50: (2.0, "★ 타이베이 사무실, 블라인드 빛, 책상 앞 남자의 뒷모습"),
            55: (3.0, "★ 도미코 손에서 미끄러진 수화기가 줄에 매달려 흔들림(하이앵글) — BGM 절단, 2초 무음(룸톤)"), 57: (2.0, "장부 위 「−２，０００万円」 카운트업(저음 드론)"),
            58: (3.0, "★ 밤, 휴지통에서 파일을 꺼내는 도미코의 손, 펼쳐진 3페이지 빨간 띠 → 텅 빈 현관 노렌(크레인 업)")},
    "S14": {"pre": (4.5, "★ 하나이카다 현관, 대만 버스 도착, 에어브레이크 → 중국어로 맞으며 절하는 와카나(사이드 트래킹)"), 61: (2.0, "손님들에게 둘러싸인 와카나 와이드")},
    "S15": {"pre": (2.5, "로비 소파의 노부부, 다가가는 와카나"), "post": (2.0, "와카나가 깊이 고개 숙임, 아내가 끄덕임 — 눈물 포인트 여운")},
    "S16": {"pre": (3.0, "밤 사무실, 휴대폰 진동 2회 「麻衣」(lcd) → 받는 와카나"), "post": (2.5, "★ 전화를 내려놓는 손, 미소 홀드(자막 없는 구간 = 썸네일 프레임)")},
    "S17": {"pre": (5.0, "★ 뒷문 골목 밤, 캐리어를 끄는 마이 → 택시 → 뛰어나오는 다카유키, 멀어지는 미등(하이앵글 롱샷)"), 69: (3.0, "★ 텅 빈 프런트, 홀로 장부 앞에 앉은 도미코(부감 롱샷)")},
    "S18": {"pre": (3.5, "휴대폰 「義母」 진동 3회(lcd) → 숨을 고르고 받는 와카나"), 73: (1.5, "와카나 CU, 숨 한 번"),
            75: (4.0, "★ 전화를 끊고 휴대폰을 엎는 손 → 창밖 손님 웃음소리 → 미소 홀드"), 76: (3.0, "복도를 지나 밝은 프런트로 걸어가는 뒷모습(팔로우)"), "post": (2.0, "프런트에서 카메라를 향해 정중히 절")},
    "OUT": {"pre": (16.0, "하이라이트 몽타주(본편 목소리 5줄 재사용) → 진행자"), "post": (4.5, "손 흔들기 → 엔드카드(별도)")},
}


def speech_span(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    env = np.convolve(np.abs(x), np.ones(160) / 160, "same")
    idx = np.where(env > 0.01)[0]
    return idx[0] / 16000, idx[-1] / 16000


def tc(x):
    return f"{int(x // 60)}:{x % 60:05.2f}"


def build():
    lines = []
    for n, sc, tag, spk, omni, text in load_lines():
        src = os.path.join(AUDIO, f"line{SAME_AS.get(n, n):03d}.mp3")
        a, b = speech_span(src)
        lines.append({"n": n, "id": f"line{n:03d}", "scene": sc, "spk": tag, "spk_key": spk, "omni": omni,
                      "text": text, "dur": b - a, "kind": "N" if spk == "NA" else "D"})
    scenes = []
    for x in lines:
        if not scenes or scenes[-1][0] != x["scene"]:
            scenes.append((x["scene"], []))
        scenes[-1][1].append(x)
    t, rows, srows, ads = 0.0, [], [], []
    for sid, ls in scenes:
        start = t
        sil = SILENT.get(sid, {})
        if "pre" in sil:
            t += sil["pre"][0]
        prev = None
        for x in ls:
            _tag, _emo, _tempo, pre, post, _note = T[x["n"]]
            if prev is not None:
                gap = GAP_SAME if prev["spk_key"] == x["spk_key"] else GAP_CHANGE
                gap = max(gap, pre, T[prev["n"]][4])
                t += gap
            x["start"], x["end"] = t, t + x["dur"]
            t = x["end"]
            rows.append(x)
            if x["n"] in sil and sil[x["n"]][0] > 0:
                t += sil[x["n"]][0] + (T[x["n"]][4] or 0)
            prev = x
        last = ls[-1]
        if last["n"] in AD_AFTER:
            assert "post" not in sil, f"{sid}: 광고 장면 뒤에 무언 비트 금지"
            t += AD_TAIL
            ads.append((AD_AFTER[last["n"]][0], t, AD_AFTER[last["n"]][1], last["id"]))
        elif not (last["n"] in sil and sil[last["n"]][0] > 0):
            t += max(TAIL_N if last["kind"] == "N" else TAIL_D, T[last["n"]][4])
        if "post" in sil:
            t += sil["post"][0]
        srows.append((sid, start, t))
    return rows, srows, ads, t


def main():
    rows, srows, ads, total = build()
    main_end = next(s for s in srows if s[0] == "OUT")[1]
    out = ["# 『老舗旅館の嫁』 PHASE 1 Lock 타임라인 (실측)", "",
           f"- **전체 길이: {tc(total)}** (아웃트로 포함, 엔드카드 제외) — 기준 9:40 이상 {'✅' if total >= MIN_TOTAL else '❌ 미달 → 대본 보강 필요'}",
           f"- 본편 끝(아웃트로 시작): {tc(main_end)}"]
    for name, at, target, lid in ads:
        ok = abs(at - target) <= 10
        out.append(f"- **{name}: {tc(at)}** ({lid} 끝 + 0.9초 여운 = 장면 경계) — 목표 {tc(target)} ±10초 {'✅' if ok else '❌'}")
    humil_end = next(s for s in srows if s[0] == "S07")[2]
    out.append(f"- 수모 구간(S02~S07 끝): {tc(humil_end)} = 본편의 {humil_end / main_end * 100:.0f}% (제11장 24: 35~40% 이내 {'✅' if humil_end / main_end <= 0.40 else '❌'})")
    out += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 | 무언 비트 |", "|---|---|---|---|---|"]
    for s, a, b in srows:
        beats = " / ".join(f"{'앞' if k == 'pre' else ('뒤' if k == 'post' else f'#{k} 뒤')} {v[0]}s {v[1]}" for k, v in SILENT.get(s, {}).items() if v[0] > 0)
        out.append(f"| {s} | {tc(a)} | {tc(b)} | {b - a:.1f}초 | {beats} |")
    out += ["", "## 줄별 타임코드", "", "| 줄 | 장면 | 화자 | 립싱크 | 시작 | 끝 | 길이 | 대사 |", "|---|---|---|---|---|---|---|---|"]
    out += [f"| {x['id']} | {x['scene']} | {x['spk']} | {'OMNI' if x['omni'] else ''} | {tc(x['start'])} | {tc(x['end'])} | {x['dur']:.2f} | {x['text'][:30]} |" for x in rows]
    long_omni = [x for x in rows if x["omni"] and x["dur"] > OMNI_WARN]
    if long_omni:
        out += ["", f"## OMNI 8초 상한 — {OMNI_WARN}초 초과 {len(long_omni)}줄(말하는 얼굴 → B롤/리액션 컷어웨이로 분할, 음성은 그대로)", ""]
        out += [f"- {x['id']} {x['spk']} {x['dur']:.2f}초: {x['text'][:30]}" for x in long_omni]
    open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    json.dump({"total": total, "main_end": main_end, "ads": [{"name": a, "at": b, "target": c, "line": d} for a, b, c, d in ads],
               "scenes": [{"id": s, "start": a, "end": b} for s, a, b in srows],
               "lines": [{k: x[k] for k in ("id", "scene", "spk", "omni", "start", "end", "dur", "text")} for x in rows]},
              open(os.path.join(HERE, "lock.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(out[:7]))


if __name__ == "__main__":
    main()
