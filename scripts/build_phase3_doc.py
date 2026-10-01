#!/usr/bin/env python3
"""PHASE 3 산출물 생성: scripts/storyboard/<skit>.json + subs/<skit>.ass + scripts/scenes/<skit>.json
→ docs/EP3-PHASE3-샷리스트.md (규격서 PHASE 3 표 + 제5장 씬 프롬프트 템플릿).
사용법: python3 scripts/build_phase3_doc.py kim-cart-grandma docs/EP3-PHASE3-샷리스트.md
"""
import json
import re
import sys

skit, out_path = sys.argv[1], sys.argv[2]
sb = json.load(open(f"scripts/storyboard/{skit}.json", encoding="utf-8"))
scenes = json.load(open(f"scripts/scenes/{skit}.json", encoding="utf-8"))
durs = [int(d) for d in scenes["durations"]]
cum = [0]
for d in durs:
    cum.append(cum[-1] + d)


def parse_t(s):
    h, m, sec = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(sec)


def tc(x):
    m = int(x // 60); s = x - m * 60; f = int(round((s - int(s)) * 24))
    if f == 24:
        f = 0; s += 1
    return f"{m:02d}:{int(s):02d}.{f:02d}"


rows = []
tts_i = 0
for ln in open(f"subs/{skit}.ass", encoding="utf-8"):
    if not ln.startswith("Dialogue:"):
        continue
    p = ln.strip().split(",", 9)
    text = re.sub(r"\{[^}]*\}", "", p[9]).replace("\\N", " ").strip()
    style = p[3]
    if style != "Caption":
        tts_i += 1
    rows.append(dict(start=parse_t(p[1]), end=parse_t(p[2]), style=style, text=text,
                     line=(f"line{tts_i:03d}" if style != "Caption" else "자막카드")))
names = {"Kim": "김씨", "Grandma": "할머니", "Choi": "최사장", "Naration": "내레이터", "Caption": ""}

def audio_for(k):
    s0, s1 = cum[k], cum[k + 1]
    hits = [r for r in rows if r["start"] < s1 and r["end"] > s0]
    parts = []
    for r in hits:
        kind = "대사" if r["style"] in ("Kim", "Grandma", "Choi") else ("자막" if r["style"] == "Caption" else "내레")
        kw = r["text"][:18] + ("…" if len(r["text"]) > 18 else "")
        parts.append(f"{r['line']} {names.get(r['style'], r['style'])}".strip() + f" Attack {tc(r['start'])}–{tc(r['end'])} ({kind}: {kw})")
    return "<br>".join(parts) if parts else "무음 (앰비언스만)"

L = []
L.append("# EP3 「김씨와 폐지 할머니」 — PHASE 3 정밀 샷 리스트 & 프롬프트 설계 (Storyboard Lock)\n")
L.append("규격서 PHASE 3 산출물. 작성 2026-10-01. 상태: **Storyboard Lock — 사용자 PASS 2026-10-01** (이후 변경은 사용자 재승인 필요)\n")
L.append("원본 데이터: `scripts/storyboard/kim-cart-grandma.json` (이 문서는 `scripts/build_phase3_doc.py`로 생성). "
         "타임코드는 PHASE 1 Lock 타임라인(24fps)과 PHASE 2 Lock 에셋을 그대로 참조한다.\n")
L.append("## 3-0. 공통 규칙 (모든 컷에 동일 주입)\n")
L.append(f"- 스타일 프리셋: `{sb['preset']}`")
L.append(f"- 네거티브: `{sb['negative']}`")
L.append("- 참조 호출: `KIM@<셀>` = 김씨 시트, `GMA@<셀>` = 할머니 시트, `CHOI@<셀>` = 최사장 시트, `LOC@<장소>-<day|night|key1|key2>` = 로케이션 셀. "
         "셀 이름: front/45/side(상단), fullbody-front/back/side(중단), front-neutral/smile/tense·wary(하단), hands(중단 전신에서 손 크롭).")
L.append("- 카메라 무빙은 규격 승인 목록만 사용: Static / Slow cinematic push-in(1.05~1.08) / Subtle handheld sway / Very slow lateral drift(보행 속도 동기). "
         "인수인계본의 Dolly zoom(S15)·Side tracking·Follow shot은 위 승인 동작으로 치환했다.")
L.append("- 컷 길이: fal Seedance 제약으로 5/10초 단위 생성 후, 편집에서 3~5초 시각적 환기 규칙(제4장)에 맞춰 분할·인서트한다.")
L.append("- 말하는 씬 4초 초과(S02, S28, S30)는 **Talking face → B-roll → 리액션** 치팅을 필수 적용(아래 Edit Strategy).")
L.append("- 헤드 턴 15~20° 이내, 표정은 키프레임에 50% 선반영, 비디오 단계에서는 미세 모션만 지시.\n")
L.append("## 3-1. 샷 리스트 (규격 표)\n")
L.append("| Scene | 타임코드 & 듀레이션 | 오디오 파형 & 대사 | 샷 사이즈 & 렌즈 | 조명 설계 | 카메라 무빙 | 전환(Out) | 참조 에셋 |")
L.append("|---|---|---|---|---|---|---|---|")
for k, sc in enumerate(sb["scenes"]):
    lens_short = sc["lens"].split(",")[0]
    light_short = sc["lighting"].split(",")[0]
    L.append(f"| {sc['id']} | {tc(cum[k])} ~ {tc(cum[k+1])} ({durs[k]}s) | {audio_for(k)} | {sc['shot']} / {lens_short} | {light_short} | {sc['camera']} | {sc['transition_out']} | {', '.join(sc['refs'])} |")
L.append("\n## 3-2. 씬별 키프레임 & 모션 프롬프트 (제5장 템플릿)\n")
for k, sc in enumerate(sb["scenes"]):
    L.append(f"### {sc['id']} ({durs[k]}s) — {sc['shot']}\n")
    L.append("```")
    L.append("[SCENE SPECIFICATION]")
    L.append(f"- Scene ID: {sc['id']}")
    L.append(f"- Timecode: {tc(cum[k])} - {tc(cum[k+1])} (Duration: {durs[k]}s)")
    L.append(f"- Audio Anchor: {audio_for(k).replace('<br>', ' / ')}")
    L.append(f"- Transition Out: {sc['transition_out']}")
    L.append(f"- References: {', '.join(sc['refs'])}")
    L.append("")
    L.append("[KEYFRAME GENERATION PROMPT]")
    L.append(f"(Subject): {sc['subject']}")
    L.append(f"(Expression, pre-baked 50%): {sc['expression']}")
    L.append(f"(Environment): {sc['environment']}")
    L.append(f"(Cinematography): {sc['lens']}; {sb['preset']}")
    L.append(f"(Lighting): {sc['lighting']}")
    L.append(f"(Negative Prompt): {sb['negative']}")
    L.append("")
    L.append("[MOTION & LIP-SYNC PROMPT]")
    L.append("- Engine: Image-to-Video (approved keyframe only)")
    L.append(f"- Camera Motion: {sc['camera']}")
    L.append(f"- Character Motion: {sc['motion']}")
    if sc.get("edit"):
        L.append(f"- Edit Strategy: {sc['edit']}")
    L.append("```\n")
L.append("## 3-3. PHASE 4·5 실행 계획 (PASS 후)\n")
L.append("- PHASE 4 키프레임: 장면당 1장, `fal-ai/nano-banana/edit`에 캐릭터 시트+로케이션 셀을 멀티 참조로 넣어 생성. 스펙은 `scripts/build_ep3_keyframes.py`가 이 Lock 데이터에서 자동 생성(`scripts/portraits/ep3-keyframes.json` 44장, 파일럿 `ep3-keyframes-pilot.json` 3장). 실행은 `generate-video.yml portraits_spec=…` → `assets/portraits/<spec>/sNN-1.png`. Kill Gate(외계어·손가락·눈동자·그리드 출력) 통과분만 Lock, 불합격은 `portraits_regen_ids`로 부분 재생성.")
L.append("- PHASE 5 모션: `generate_video.py`에 키프레임 입력(Image-to-Video, Seedance image-to-video) 모드를 추가해 승인 키프레임만 변환. Text-to-Video 사용 금지.")
L.append("- 비용 보고: PHASE 4·5 각각 실행 전에 장면 수·예상 비용을 보고하고 승인을 받는다.")
open(out_path, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("생성:", out_path, f"({len(L)}줄)")
