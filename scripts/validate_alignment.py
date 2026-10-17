#!/usr/bin/env python3
"""생성 전 무료 검증 — 화자-장면 정렬과 오디오 설정·대본 규칙을 검사한다 (불일치 0건이어야 생성 가능).

검사 항목:
  1. 대사 줄이 장면 하나 안에 완전히 들어가고, 그 장면의 scene_speakers에 화자가 있는지 (화자-화면 일치)
  2. 한 장면에 두 화자의 대사가 섞이지 않았는지
  3. 내레이션이 대사와 시간상 겹치지 않는지 (내레이션은 무언 구간 전용)
  4. 줄별 연출 지정 누락 — MiniMax 줄은 speed_overrides, ElevenLabs 줄은 tag_overrides (빈 줄 0개)
  5. TTS 문장에 아라비아 숫자·영문자가 없는지 (해당 언어 문자로 표기)
  6. 장면 프롬프트 5블록·인원수·No blood·End 지정 여부
  7. 장면 수와 scene_speakers / ambience_prompts 길이 일치

사용법: python3 scripts/validate_alignment.py <작품>
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import parse_ass  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def main():
    if len(sys.argv) != 2:
        sys.exit("사용법: python3 scripts/validate_alignment.py <작품>")
    work = sys.argv[1]
    with open(os.path.join(ROOT, "scripts", "scenes", f"{work}.json"), encoding="utf-8") as f:
        sc = json.load(f)
    with open(os.path.join(ROOT, "scripts", "audio", f"{work}.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    lines = parse_ass(os.path.join(ROOT, "subs", f"{work}.ass"))

    default = int(sc.get("duration", 5))
    durs = [int(s.get("duration", default)) if isinstance(s, dict) else default for s in sc["scenes"]]
    bounds, t = [], 0.0
    for d in durs:
        bounds.append((t, t + d))
        t += d
    errors, warns = [], []

    speakers = cfg.get("scene_speakers", [])
    if len(speakers) != len(durs):
        errors.append(f"scene_speakers {len(speakers)}개 ≠ 장면 {len(durs)}개")
    if len(cfg.get("ambience_prompts", [])) not in (0, len(durs)):
        errors.append(f"ambience_prompts {len(cfg['ambience_prompts'])}개 ≠ 장면 {len(durs)}개")

    silent = set(cfg.get("silent_styles", []))
    narration = set(cfg.get("narration_styles", ["Naration"]))
    names = cfg.get("style_names", {})
    tts = [l for l in lines if l[2] not in silent]
    dialogue, narr = [], []
    scene_talkers = {}
    for i, (s, e, style, name, text) in enumerate(tts, start=1):
        who = name or names.get(style, style)
        if style in narration:
            narr.append((s, e, i, text))
            continue
        dialogue.append((s, e, i, who))
        k = next((k for k, (a, b) in enumerate(bounds) if a <= s < b), None)
        if k is None:
            errors.append(f"[{i:03d}] {who} {s:.2f}s — 장면 범위 밖")
            continue
        a, b = bounds[k]
        if e > b + 0.05:
            errors.append(f"[{i:03d}] {who} {s:.2f}~{e:.2f}s — 장면 {k + 1}({a:.0f}~{b:.0f}s) 경계를 넘음")
        if k < len(speakers) and who not in speakers[k]:
            errors.append(f"[{i:03d}] {who} — 장면 {k + 1}에 보이는 인물 {speakers[k]}에 없음")
        scene_talkers.setdefault(k, set()).add(who)
    for k, who in scene_talkers.items():
        if len(who) > 1:
            errors.append(f"장면 {k + 1}에 두 화자 이상의 대사: {sorted(who)}")
    for s, e, i, _ in narr:
        for ds, de, j, who in dialogue:
            if s < de and ds < e:
                errors.append(f"내레이션 [{i:03d}] {s:.2f}~{e:.2f}s 이 대사 [{j:03d}] {who}와 겹침")

    voices = cfg.get("style_voices", {})
    speeds, tags = cfg.get("speed_overrides", {}), cfg.get("tag_overrides", {})
    for i, (s, e, style, name, text) in enumerate(tts, start=1):
        voice = cfg.get("name_voices", {}).get(name) or voices.get(style) or cfg.get("default_voice", "")
        if voice.startswith("el:"):
            if str(i) not in tags:
                errors.append(f"[{i:03d}] ElevenLabs 줄에 연기 태그(tag_overrides) 없음")
            elif len(tags[str(i)].strip("[]").replace(",", " ").split()) > 4:
                warns.append(f"[{i:03d}] 연기 태그가 4단어 초과 — 낭독 누출 위험: {tags[str(i)]}")
        elif str(i) not in speeds:
            errors.append(f"[{i:03d}] MiniMax 줄에 속도(speed_overrides) 지정 없음")
        if re.search(r"[0-9A-Za-z０-９Ａ-Ｚａ-ｚ]", text):
            errors.append(f"[{i:03d}] TTS 문장에 숫자·영문자: {text}")

    for k, s in enumerate(sc["scenes"], start=1):
        p = s["prompt"] if isinstance(s, dict) else s
        for blk in ("[LOCK]", "[SCENE]", "[CAMERA]", "[DURATION]", "[DIALOGUE]", "[SOUND]"):
            if blk not in p:
                errors.append(f"장면 {k}: 프롬프트에 {blk} 블록 없음")
        if "No blood" not in p:
            errors.append(f"장면 {k}: No blood 없음")
        if not re.search(r"Exactly (zero|one|\d+) (person|people)", p):
            errors.append(f"장면 {k}: LOCK에 인원수 숫자 없음")
        if "End:" not in p:
            errors.append(f"장면 {k}: CAMERA End 없음")
        if "Exactly zero" in p and "인물 없음" not in p:
            errors.append(f"장면 {k}: 무인 장면에 '인물 없음' 이중 명시 없음")

    print(f"장면 {len(durs)}개 / {t:.0f}초, TTS 줄 {len(tts)}개 (대사 {len(dialogue)}, 내레이션 {len(narr)})")
    for w in warns:
        print("  경고:", w)
    if errors:
        print(f"불일치 {len(errors)}건:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("불일치 0건 — 생성 가능")


if __name__ == "__main__":
    main()
