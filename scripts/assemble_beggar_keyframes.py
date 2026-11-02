#!/usr/bin/env python3
"""『みすぼらしい老人は、財閥会長だった』 PHASE 4 최종 키프레임 모으기 — 단계별 합격본을 스토리보드 경로
assets/portraits/beggar-chairman-keyframes/<id>-1.png(PHASE 5 i2v·정지 푸시인·OmniHuman 입력)로 복사한다.
우선순위: productions/beggar-chairman-ja/kf_select.json(검수에서 고른 후보) > a단계 > b단계.
사용법: python3 scripts/assemble_beggar_keyframes.py [--check]  (--check: 복사 없이 누락만 확인)"""
import json, os, shutil, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = os.path.join(ROOT, "scripts", "storyboard", "beggar-chairman.json")
SEL = os.path.join(ROOT, "productions", "beggar-chairman-ja", "kf_select.json")
STAGES = ["assets/portraits/beggar-kf-a", "assets/portraits/beggar-kf-b"]
# 시범·재생성 합격본(얼굴 1/3 재구도 -fixed 우선)
PILOT = {"S13i": "assets/portraits/beggar-kf-pilot/S13i-fixed.png", "S12f": "assets/portraits/beggar-kf-pilot/S12f-fixed.png",
         "S11i": "assets/portraits/beggar-kf-pilot/S11i-fixed.png"}


def main():
    check = "--check" in sys.argv
    sel = {k: v for k, v in json.load(open(SEL, encoding="utf-8")).items() if not k.startswith("_")} if os.path.exists(SEL) else {}
    sel = {**PILOT, **sel}
    scenes = [s for s in json.load(open(SB, encoding="utf-8"))["scenes"] if s.get("keyframe")]
    missing, plan = [], []
    for s in scenes:
        src = sel.get(s["id"]) or next((f"{d}/{s['id']}-1.png" for d in STAGES
                                         if os.path.exists(os.path.join(ROOT, d, f"{s['id']}-1.png"))), None)
        if not src or not os.path.exists(os.path.join(ROOT, src)):
            missing.append(s["id"]); continue
        plan.append((src, s["keyframe"]))
    if missing:
        sys.exit(f"키프레임 없음 {len(missing)}컷: {', '.join(missing)}")
    if not check:
        for src, dst in plan:
            os.makedirs(os.path.dirname(os.path.join(ROOT, dst)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, src), os.path.join(ROOT, dst))
    print(f"키프레임 {len(plan)}컷 {'확인' if check else '복사'} 완료 (선택 지정 {sum(1 for s in scenes if s['id'] in sel)}컷)")


if __name__ == "__main__":
    main()
