#!/usr/bin/env python3
"""타워맨션 PHASE 1 Lock 타임라인 — 실측 음성 길이로 줄별 타임코드·장면 경계·광고 지점·전체 길이를 고정한다.

규칙(버들잎 Lock 규칙 계승 + CLAUDE.md 제0장·제6장 5):
  같은 장면 대사 사이 0.6초(같은 화자)/0.8초(화자 바뀜) — 톤 연출표의 앞·뒤 쉼이 더 길면 그 값,
  장면 끝: 인물 대사 끝→컷 1.8초 / 내레이션 끝→컷 1.0초,
  무언 비트(장면별 SILENT 표)는 대사가 덮지 않는 화면 시간, 광고 지점 = 전환 문장 끝 + 0.9초 여운 뒤 장면 경계.
입력: assets/auditions/tower-tts/lineNNN.mp3(실측), 00_script_ja.md, build_tts.T(톤 연출표)
출력: 06_Lock타임라인.md, lock.json
"""
import json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from parse_script import load_lines
from build_tts import T, SPLIT

GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, AD_TAIL, SPLIT_GAP = 0.6, 0.8, 1.8, 1.0, 0.9, 0.35
AD_AFTER = {25: ("1차 광고", 210.0), 47: ("2차 광고", 420.0)}  # NA14 「…言い方だ。」 뒤 / 레이카 「訴えてやるわ!」 뒤
MIN_TOTAL = 580.0  # 9:40 (아웃트로 포함, 엔드카드 제외)

# 장면별 무언 비트(초): "pre" = 첫 줄 앞, 숫자 n = n번 줄 뒤, "post" = 마지막 줄 뒤(꼬리 규칙과 별개)
SILENT = {
    "S01": {"pre": (3.0, "레이카가 엘리베이터 문 앞을 막아섬"), 1: (3.0, "문 닫힘 → 치맛자락 쥔 리코 손(훌쩍임 효과음)"), "post": (3.0, "타이틀 카드")},
    "S02": {"pre": (2.5, "타워 외관 로우앵글 → 층별 피라미드 그래픽"), 8: (2.5, "라운지 예약판·비켜서는 저층 주민"), 9: (2.5, "로비를 가로지르는 레이카와 측근들")},
    "S03": {"pre": (2.5, "키즈룸 안내판 + 유리 너머를 보는 리코"), 10: (2.0, "유리문에 손바닥을 댄 리코 뒷모습")},
    "S03-2": {"pre": (2.0, "밤 거실, 소파의 모녀")},
    "S04": {"pre": (2.5, "우편함 통지서 클로즈업"), "post": (2.0, "매끈한 외벽 인서트")},
    "S05": {"pre": (2.5, "임시총회 와이드"), 17: (2.5, "측근 박수 → 머뭇거리는 주민 박수 → 손을 드는 유미"), "post": (2.5, "정적 + 다리를 꼬는 레이카")},
    "S06": {"post": (2.0, "웃음소리, 고개 숙이는 유미")},
    "S06-2": {"pre": (2.0, "시선을 피하는 주민들")},
    "S07": {"pre": (2.5, "수첩에 빠르게 적는 손 ECU"), "post": (1.5, "안경 너머 유미의 눈 ECU")},
    "S08": {"pre": (3.0, "밤 식탁, 잠든 리코에게 담요")},
    "S09": {"pre": (2.0, "관리사무소 카운터, 파일을 내미는 담당자")},
    "S10": {"pre": (2.0, "장부에 빨간 동그라미"), 30: (1.5, "「二千四百万円」 강조 자막 + ドン"), 31: (2.0, "법인 등기 화면 인서트")},
    "S11": {"pre": (1.5, "가상 SNS 화면 스크롤"), 33: (3.0, "쌓여 가는 출력물·형광펜(디졸브 3컷)")},
    "S12": {"pre": (1.5, "주민 명부, 42층 칸")},
    "S12-2": {"pre": (3.0, "하얀 봉투를 봉하는 손(복선)")},
    "S12-3": {"pre": (2.5, "회의실로 몰려드는 주민들"), 36: (2.5, "로비, 측근을 거느린 레이카"), "post": (2.0, "노트북 가방을 고쳐 메는 손")},
    "S13": {"pre": (3.0, "만석 대회의실 와이드"), 38: (3.0, "측근 박수 → 노트북을 연결하는 손")},
    "S14": {"pre": (13.0, "통장⇄SNS 1쌍(3.0)·2쌍(3.0)·BGM 차단+심장 박동(1.5)·3쌍(3.0)·「ざわ…」 3분할(2.5)"),
            45: (4.5, "통장 원본 인서트(2.0) → 측근들이 떨어져 앉음(2.5)")},
    "S15": {"pre": (2.0, "마이크 스탠드를 움켜쥐는 손(더치 5°)")},
    "S16": {"pre": (3.5, "지팡이 노신사가 일어섬(원경→미디엄)"), 48: (3.0, "모두 뒤돌아봄 → 하얗게 질린 레이카")},
    "S17": {"pre": (3.5, "무릎 → 바닥에 주저앉은 부감 → 쏟아진 가방·督促状"), 55: (3.0, "올려다보는 레이카 → 시선을 피하는 측근들")},
    "S17-2": {"pre": (2.5, "빈 단상 위 통장 원본 → 노을")},
    "S18": {"pre": (2.5, "바뀐 안내판, 아이들과 노는 리코"), "post": (2.0, "웃는 아이들 원경")},
    "S19": {"pre": (3.0, "종이상자를 안은 레이카, 화물 엘리베이터를 가리키는 유미 손"), 60: (4.0, "화물 엘리베이터에 타는 레이카, 문 닫힘(S01 매치컷)"),
            "post": (4.0, "1.0초 페이드아웃 → 엔딩 문구 카드")},
    "OUT-2": {"pre": (18.0, "하이라이트 몽타주(목소리만 5줄 재사용)")},
    "OUT-3": {"post": (4.5, "손 흔들기")},
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
    audio = os.path.join(REPO, "assets", "auditions", "tower-tts")
    lines = load_lines()
    for n, x in enumerate(lines, 1):
        x["n"], x["id"] = n, f"line{n:03d}"
        if n in SPLIT:
            parts = [speech_span(os.path.join(audio, f"{x['id']}{s}.mp3")) for s, *_ in SPLIT[n]]
            x["dur"] = sum(b - a for a, b in parts) + SPLIT_GAP * (len(parts) - 1)
        else:
            a, b = speech_span(os.path.join(audio, x["id"] + ".mp3"))
            x["dur"] = b - a
        x["kind"] = "N" if x["spk"].startswith("NA") else "D"
    scenes = []
    for x in lines:
        if not scenes or scenes[-1][0] != x["scene"]:
            scenes.append((x["scene"], []))
        scenes[-1][1].append(x)
    # 대사 없는 장면(S12-2)을 순서대로 끼운다
    order = [s for s, _ in scenes]
    scenes.insert(order.index("S12-3"), ("S12-2", []))  # 봉투 복선
    t, rows, srows, ads = 0.0, [], [], []
    for sid, ls in scenes:
        start = t
        sil = SILENT.get(sid, {})
        if "pre" in sil:
            t += sil["pre"][0]
        prev = None
        for x in ls:
            emo, inten, tempo, pre, post, note = T[x["n"]]
            if prev is not None:
                gap = GAP_SAME if prev["spk"] == x["spk"] else GAP_CHANGE
                gap = max(gap, pre, T[prev["n"]][4])
                t += gap
            x["start"], x["end"] = t, t + x["dur"]
            t = x["end"]
            rows.append(x)
            if x["n"] in sil:
                t += sil[x["n"]][0] + (T[x["n"]][4] or 0)
            prev = x
            if x["n"] in AD_AFTER:
                ads.append((AD_AFTER[x["n"]][0], x["end"] + AD_TAIL, AD_AFTER[x["n"]][1], x["id"]))
        if ls:
            last = ls[-1]
            if last["n"] not in sil:
                t += max(TAIL_N if last["kind"] == "N" else TAIL_D, T[last["n"]][4])
        if "post" in sil:
            t += sil["post"][0]
        srows.append((sid, start, t))
    return rows, srows, ads, t


def main():
    rows, srows, ads, total = build()
    main_end = next(s for s in srows if s[0] == "OUT-2")[1]
    out = ["# 『タワマンのボスママ』 PHASE 1 Lock 타임라인 (실측)", "",
           f"- **전체 길이: {tc(total)}** (아웃트로 포함, 엔드카드 제외) — 기준 9:40 이상 {'✅' if total >= MIN_TOTAL else '❌ 미달 → 대본 보강 필요'}",
           f"- 본편 끝(아웃트로 시작): {tc(main_end)}"]
    for name, at, target, lid in ads:
        ok = abs(at - target) <= 10
        out.append(f"- **{name}: {tc(at)}** ({lid} 끝 + 0.9초 여운) — 목표 {tc(target)} ±10초 {'✅' if ok else '❌'}")
    out += ["", "## 장면 경계", "", "| 장면 | 시작 | 끝 | 길이 |", "|---|---|---|---|"]
    out += [f"| {s} | {tc(a)} | {tc(b)} | {b - a:.1f}초 |" for s, a, b in srows]
    out += ["", "## 줄별 타임코드", "", "| 줄 | 장면 | 화자 | 립싱크 | 시작 | 끝 | 길이 | 대사 |", "|---|---|---|---|---|---|---|---|"]
    out += [f"| {x['id']} | {x['scene']} | {x['spk']} | {'OMNI' if x['omni'] else ''} | {tc(x['start'])} | {tc(x['end'])} | {x['dur']:.2f} | {x['text'][:30]} |" for x in rows]
    long_omni = [x for x in rows if x["omni"] and x["dur"] > 7.4]
    if long_omni:
        out += ["", "## OMNI 8초 상한 주의(앞뒤 여백 포함 시 초과 위험 → 컷어웨이 분할)", ""]
        out += [f"- {x['id']} {x['dur']:.2f}초: {x['text'][:30]}" for x in long_omni]
    open(os.path.join(HERE, "06_Lock타임라인.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    json.dump({"total": total, "ads": [{"name": a, "at": b, "target": c, "line": d} for a, b, c, d in ads],
               "scenes": [{"id": s, "start": a, "end": b} for s, a, b in srows],
               "lines": [{k: x[k] for k in ("id", "scene", "spk", "omni", "start", "end", "dur", "text")} for x in rows]},
              open(os.path.join(HERE, "lock.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(out[:6]))


if __name__ == "__main__":
    main()
