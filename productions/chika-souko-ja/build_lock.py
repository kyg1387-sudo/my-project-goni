#!/usr/bin/env python3
"""#02 『地下倉庫の伝票』 PHASE 1 Lock 타임라인 — 실측 음성 길이로 줄별 타임코드·장면 경계·광고 지점·전체 길이를 고정한다.

규칙(CLAUDE.md 제0장·제6장 5, #01 build_lock.py 계승):
  같은 장면 대사 사이 0.6초(같은 화자)/0.8초(화자 바뀜) — 톤 연출표의 앞·뒤 쉼이 더 길면 그 값,
  장면 끝: 인물 대사 끝→컷 1.8초 / 내레이션 끝→컷 1.0초,
  무언 비트(SILENT)는 대사가 덮지 않는 화면 시간, 광고 지점 = 전환 문장 끝 + 0.9초 여운 = 장면 경계.
입력: assets/auditions/chika-tts/lineNNN.mp3(실측, 교정 채택본), 00_script_ja.md, build_tts.T(톤 연출표)
출력: 06_Lock타임라인.md, lock.json
"""
import json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from build_tts import T, load_lines, SAME_AS

AUDIO = os.path.join(REPO, "assets", "auditions", "chika-tts")
LAUGH_MIX = os.path.join(REPO, "assets", "auditions", "chika-gondo-laugh", "mix_B_bellow+happy.mp3")  # #36 = 폭소 SFX + 대사(확정 B안)
GAP_SAME, GAP_CHANGE, TAIL_D, TAIL_N, AD_TAIL = 0.6, 0.8, 1.8, 1.0, 0.9
AD_AFTER = {19: ("1차 광고", 210.0), 38: ("2차 광고", 420.0)}  # NA9 「…すべて――権藤。」 뒤 / 桐谷 「そこまでにしてください」 뒤
MIN_TOTAL = 580.0  # 9:40 (아웃트로 포함, 엔드카드 제외)
OMNI_WARN = 7.4    # OmniHuman 8초 상한(앞뒤 0.3초 여백 포함) → 초과분은 컷어웨이 분할

# 장면별 무언 비트(초): "pre" = 첫 줄 앞, 숫자 n = n번 줄 뒤, "post" = 마지막 줄 뒤(꼬리 규칙과 별개)
# 컷 길이 기준(규칙집 6): 인서트 3~4 / 액션 5~7. 끌지 않도록 비트 하나당 2~4초.
SILENT = {
    "S01": {"pre": (3.0, "★ 양쪽 문 열림, 역광 감사팀 실루엣(로우앵글 슬로모)"), 1: (2.5, "★ 와인잔 낙하·파열(슬로모, 파편음)"),
            "post": (4.0, "타이틀 『地下倉庫の伝票』(딥 투 블랙 1.0) → 카드 「二か月前」")},
    "S02": {"pre": (2.5, "★ 대강당 와이드, 스크린 빛"), 5: (6.0, "작성자 태그 줌인 2.0 → P.42 1.5 → 박수 객석 → 사오리 차가운 눈 CU")},
    "S03": {"pre": (2.0, "기획부 사무실 설정, 동료들"), 7: (2.0, "금시계 손목 인서트"), 9: (4.0, "기획서 묶음 쓰레기통 낙하 → 시선 피하는 동료들"), 12: (2.0, "사오리 리액션 CU — 굳은 얼굴, 눈만 흔들림")},
    "S04": {"pre": (3.0, "인트라넷 인사 발령 그래픽"), "post": (3.0, "어두운 사무실, 건네지는 USB(손만)")},
    "S05": {"pre": (3.0, "상자 안은 사오리 뒷모습, 다가오는 곤도"), "post": (4.0, "★ 엘리베이터 문 닫힘 — 문틈 사오리 굳은 얼굴 → 하강음 브리지 → 형광등 지직")},
    "S06": {"pre": (4.0, "형광등 깜빡 점등 → ★ 랙 소실점 설정샷(돌리 인)"), 15: (2.0, "랙 사이를 둘러보는 사오리(와이드 속 작은 인물)"), 16: (2.5, "책상 위 스마트폰 삼각대 세우는 손(S15 셋업)")},
    "S07": {"pre": (7.0, "3주 스캔 몽타주(디졸브 3컷: 상자 더미·스캐너 불빛·날짜 넘김) → 손이 멈춤 → 지출결의서 인서트"), 19: (0.0, "NA9 아래 ★ 부채꼴 전표 오버헤드(도장음 ×3)")},
    "S08": {"pre": (1.5, "미야모토가 다가옴"), 20: (1.5, "사오리 리액션 — 전표를 쥔 손에 힘"), 21: (2.5, "형광등에 전표를 비춰 보는 사오리")},
    "S09": {"pre": (8.5, "카드 「あと二十日」 2.0 → 심야 DB 구축 몽타주(노트북 화면·형광펜·상자 번호) 4.0 → 커피잔 / 사다리 상자 2.5"),
            23: (2.5, "三千万円 카운트업 강조 자막(베이스 히트)"), 24: (3.5, "★ 弔慰金 申請書 ↔ 등기부 주소 빨간 선(심장박동 + 「띵」)")},
    "S10": {"pre": (3.5, "USB 꽂기 → 로그 화면 23:48"), 26: (3.0, "★ 클럽 영수증 23:41 ↔ 로그 일치 하이라이트(베이스 드롭)"),
            27: (6.0, "핫라인 첨부 → 클릭 → 送信完了(홀드) → 카드 「あと十四日」"), "post": (1.5, "어두운 지하 홀드")},
    "S11": {"pre": (10.0, "카드 「あと三日」 1.5 → ★ 빈 복도·다가오는 구두 소리 4.5 → 노트북 닫는 손 1.5 → ★ 문 열림, 역광 곤도 실루엣 2.5"),
            30: (2.5, "구두가 상자를 참, 종이 흩어짐(발+상자)"), 31: (3.0, "문 닫힘 → 떨리는 사오리 손")},
    "S12": {"pre": (3.5, "샴페인 코르크 「펑」(S10 送信完了 클릭음과 사운드 매치) → 환호하는 부하들(흐린 얼굴), 잔을 치켜든 곤도 실루엣")},
    "S13": {"pre": (8.5, "연회장 샹들리에 → 현수막 → 상석 오코치 CU → ★ 사오리 입장(개어 든 앞치마)"),
            37: (4.0, "발밑 카펫에 와인 → 사오리 CU 시선 내림(0.7초 정적은 톤표) → ★ 양쪽 문 열림")},
    "S14": {"pre": (4.5, "★ 감사팀 5명 로우앵글 슬로모 입장, 철제 보관함 든 미야모토"), 40: (3.0, "★ 곤도 MS 돌리줌(작품 내 1회)"),
            41: (3.5, "와인잔 파열(S01 재사용) → 1.5초 룸톤 정적"), 42: (2.0, "곤도 주변 부하들이 물러섬(흐린 얼굴)")},
    "S15": {45: (2.5, "★ 하객 시선이 사오리에게(랙 포커스)"), 47: (1.5, "삼각대 인서트(S06 재사용)"), 50: (2.0, "미야모토가 보관함 뚜껑을 염"),
            "post": (2.5, "★ 하이앵글 — 곤도 무릎 꿇음")},
    "S16": {"pre": (3.5, "잔을 내려놓는 손 → 일어서는 오코치(미디엄)")},
    "S17": {"pre": (4.0, "현수막 낙하 → 경비원 손, 사원증 회수"), 59: (0.0, "#59는 ★ 연행 롱샷 위 목소리"), 60: (0.0, ""),
            "post": (4.5, "빈 카펫 위 깨진 와인잔 2.0 → 카드 「一か月後」 2.5(디졸브 1.0)")},
    "S18": {"pre": (3.0, "오렌지빛 지하, 꽃다발 든 사오리가 계단을 내려옴"), 63: (4.0, "봉인 상자 라벨 → 표창장 → 두 사람 목례"),
            "post": (1.5, "★ 크레인 업 끝, 1.0초 페이드아웃")},
    "OUT": {"pre": (16.0, "하이라이트 몽타주(본편 목소리 5줄 재사용)"), "post": (4.5, "손 흔들기 → 엔드카드(별도)")},
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
        src = LAUGH_MIX if n == 36 else os.path.join(AUDIO, f"line{SAME_AS.get(n, n):03d}.mp3")
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
            emo, inten, tempo, pre, post, note = T[x["n"]]
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
        if last["n"] in AD_AFTER:  # 광고 지점 = 전환 문장 끝 + 0.9초 여운 = 장면 경계(제0장 3)
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
    out = ["# 『地下倉庫の伝票』 PHASE 1 Lock 타임라인 (실측)", "",
           f"- **전체 길이: {tc(total)}** (아웃트로 포함, 엔드카드 제외) — 기준 9:40 이상 {'✅' if total >= MIN_TOTAL else '❌ 미달 → 대본 보강 필요'}",
           f"- 본편 끝(아웃트로 시작): {tc(main_end)}"]
    for name, at, target, lid in ads:
        ok = abs(at - target) <= 10
        out.append(f"- **{name}: {tc(at)}** ({lid} 끝 + 0.9초 여운 = 장면 경계) — 목표 {tc(target)} ±10초 {'✅' if ok else '❌'}")
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
    print("\n".join(out[:6]))


if __name__ == "__main__":
    main()
