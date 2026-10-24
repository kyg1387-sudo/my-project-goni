#!/usr/bin/env python3
"""『時給5万円の罠』 PHASE 4 최종 키프레임 모으기 — Kill Gate 합격본(assets/portraits/yamibaito-kf-ok/<id>-1.png)을 스토리보드 경로
assets/portraits/yamibaito-keyframes/<id>-1.png(PHASE 5 i2v·정지 푸시인·OmniHuman 입력)로 복사하고 레터박스를 검사한다(제7장 5).
사용법: python3 scripts/assemble_yamibaito_keyframes.py [--check]"""
import json, os, shutil, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = os.path.join(ROOT, "scripts", "storyboard", "yamibaito.json")
OK = "assets/portraits/yamibaito-kf-ok"


def main():
    check = "--check" in sys.argv
    scenes = [s for s in json.load(open(SB, encoding="utf-8"))["scenes"] if s.get("keyframe")]
    missing, plan = [], []
    for s in scenes:
        src = f"{OK}/{s['id']}-1.png"
        if not os.path.exists(os.path.join(ROOT, src)):
            missing.append(s["id"]); continue
        plan.append((src, s["keyframe"]))
    print(f"합격 {len(plan)} / 필요 {len(scenes)}" + (f" — 없음 {len(missing)}: {', '.join(missing)}" if missing else ""))
    if missing and not check:
        sys.exit(1)
    if not check:
        for src, dst in plan:
            os.makedirs(os.path.dirname(os.path.join(ROOT, dst)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, src), os.path.join(ROOT, dst))
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "kf_letterbox_fix.py")] + [os.path.join(ROOT, d) for _, d in plan], check=True)
        print(f"키프레임 {len(plan)}컷 복사 + 레터박스 검사 완료")


if __name__ == "__main__":
    main()
