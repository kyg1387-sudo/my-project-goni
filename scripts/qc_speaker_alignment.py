#!/usr/bin/env python3
"""화자-장면 정렬 검증 (검증 섹션 필수 항목 — 생성 실행 전 무과금 검사).

자막(.ass)의 각 대사 줄이, 그 시간대에 재생되는 장면(scripts/scenes/<skit>.json)의
프롬프트에 실제로 그 화자가 등장하는지 초 단위로 검사한다. 내레이션·녹음/영상 속
목소리(narration_styles로 지정된 스타일)는 화면에 화자가 없어도 되므로 검사에서 제외.

화자 판별은 대본 생성 스크립트(scripts/build_<skit>_assets.py)에 정의된 인물 고정
외형 문구가 장면 프롬프트에 그대로 포함돼 있는지로 확인한다 — 그 스크립트의
MARKERS를 그대로 재사용해야 정확하다. 이 파일은 참교육사이다 전용으로, 다른
작품에 쓰려면 MARKERS를 그 작품의 인물 고정 문구로 바꿔야 한다.

사용법: python3 scripts/qc_speaker_alignment.py [--skit 참교육사이다]
"""

import argparse
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# 참교육사이다 인물 고정 외형 (build_참교육사이다_assets.py와 반드시 동일해야 함)
MARKERS = {
    "한도희": "20대 후반 한국 여성 요양보호사(둥근 얼굴, 단정하게 묶은 짧은 검은 생머리, "
              "베이지색 요양보호사 유니폼 조끼와 흰 셔츠, 단단하고 절제된 눈빛)",
    "서회장": "70대 한국 남성 재벌 회장(마르고 깊은 주름이 팬 얼굴, 짧게 다듬은 백발, "
             "짙은 남색 실크 환자용 가운, 형형하고 맑은 눈빛)",
    "엄마": "50대 후반 한국 여성(둥글고 지친 얼굴, 희끗희끗한 짧은 파마머리, 낡은 꽃무늬 카디건)",
    "서미령": "30대 한국 여성 상무(날렵한 얼굴형, 어깨 길이 스트레이트 검은 머리, "
             "짙은 남색 정장 재킷, 차갑고 표독스러운 표정)",
    "서준혁": "30대 한국 남성 전무(각진 턱선, 깔끔하게 넘긴 검은 머리, 회색 슬림핏 수트, 오만한 표정)",
    "사내": "건장한 한국 남성 사내 여러 명(어두운 색 작업 점퍼, 짧게 깎은 머리, 거친 인상, "
           "동일한 복장 유지)",
    "목포해경": "50대 한국 남성 해양경찰 수사관(짧은 반백머리, 각진 얼굴, 감청색 해양경찰 정복, "
              "무거운 표정)",
}
NO_ONSCREEN_REQUIRED = {"Naration", "JunhyukRec", "ChairmanVideo"}


def parse_time(t):
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_ass(path):
    lines = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw.startswith("Dialogue:"):
                continue
            fields = raw[len("Dialogue:"):].strip().split(",", 9)
            start, end, style, name = fields[1], fields[2], fields[3], fields[4]
            lines.append((parse_time(start), parse_time(end), style, name, fields[9]))
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skit", default="참교육사이다")
    args = ap.parse_args()

    events = parse_ass(os.path.join(ROOT, "subs", f"{args.skit}.ass"))
    scenes = json.load(open(os.path.join(ROOT, "scripts", "scenes", f"{args.skit}.json"), encoding="utf-8"))
    scene_sec, shots = scenes["duration"], scenes["scenes"]

    print(f"대사 {len(events)}줄, 장면 {len(shots)}개 (장면당 {scene_sec}초)\n")

    mismatches = []
    for i, (start, end, style, name, text) in enumerate(events, 1):
        if style in NO_ONSCREEN_REQUIRED:
            continue
        scene_idx = int(start // scene_sec)
        if scene_idx >= len(shots):
            mismatches.append((i, start, name, text, scene_idx, "장면 범위 초과"))
            continue
        marker = MARKERS.get(name)
        if marker is None:
            mismatches.append((i, start, name, text, scene_idx, f"화자 '{name}'에 대한 마커 정의 없음"))
        elif marker not in shots[scene_idx]:
            mismatches.append((i, start, name, text, scene_idx, "장면에 화자 마커 없음"))

    print(f"불일치 {len(mismatches)}건\n")
    for i, start, name, text, scene_idx, reason in mismatches:
        m, s = divmod(start, 60)
        print(f"  [{i:02d}] {int(m)}:{s:05.2f} 화자={name} 장면#{scene_idx + 1} — {reason}")
        print(f"       대사: {text[:50]}")
        if 0 <= scene_idx < len(shots):
            print(f"       장면: {shots[scene_idx][:80]}")

    if mismatches:
        raise SystemExit(1)
    print("통과 — 생성 실행 전 검증 완료.")


if __name__ == "__main__":
    main()
