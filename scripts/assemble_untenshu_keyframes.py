#!/usr/bin/env python3
"""『運転手のくせに』 PHASE 4 최종 키프레임 모으기 — 단계별 합격본을 스토리보드 경로
assets/portraits/untenshu-keyframes/<id>-1.png(PHASE 5 i2v·정지 푸시인·OmniHuman 입력)로 복사한다.
우선순위: productions/ashita-kara-ja/kf_select.json(검수에서 고른 후보) > a단계 > b단계.
사용법: python3 scripts/assemble_untenshu_keyframes.py [--check]  (--check: 복사 없이 누락만 확인)"""
import json, os, shutil, subprocess, sys

# 대사 컷 얼굴 1/4 이상 크롭(제10장 1) — 복사 뒤 매번 다시 적용(복사가 크롭을 덮어쓰므로).
# 자동 검출이 엉뚱한 사람을 고르는 컷은 원본 좌표로 고정: id → (hint_x, fg, x, y, w, h)
FACE_MANUAL = {"S12a": ("0.7", "L", 868, 156, 157, 157), "S21c": ("0.25", "R", 242, 77, 156, 156)}
FACE_SKIP = {"S06e", "S17c"}
# R38: 조수석 쪽에서 본 운전 컷은 기사가 화면 왼쪽(앞유리)을 봐야 함(우핸들) — 반대로 나온 컷은 좌우 반전
MIRROR = {"S01b", "S08b", "S09d"}   # 시범에서 이미 크롭한 판을 선택(kf_select)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = os.path.join(ROOT, "scripts", "storyboard", "untenshu.json")
SEL = os.path.join(ROOT, "productions", "untenshu-ja", "kf_select.json")
STAGES = ["assets/portraits/untenshu-kf-a", "assets/portraits/untenshu-kf-b"]


def main():
    check = "--check" in sys.argv
    sel = {k: v for k, v in json.load(open(SEL, encoding="utf-8")).items() if not k.startswith("_")}
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
    if not check:
        from PIL import Image, ImageOps
        for sc in scenes:
            if sc["kind"] != "d" or sc["id"] in FACE_SKIP:
                continue
            k = os.path.join(ROOT, sc["keyframe"])
            m = FACE_MANUAL.get(sc["id"])
            args = [m[0], m[1]] + [str(v) for v in m[2:]] if m else ["0.5", sc.get("fg") or "-"]
            subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "kf_face_frame.py"), k, k, "0.27"] + args, check=True, capture_output=True)
        for sc in scenes:   # 반전은 얼굴 크롭 뒤에(검출기가 반전 얼굴을 못 찾음)
            if sc["id"] in MIRROR:
                k = os.path.join(ROOT, sc["keyframe"]); ImageOps.mirror(Image.open(k)).save(k)
    print(f"키프레임 {len(plan)}컷 {'확인' if check else '복사'} 완료 (선택 지정 {sum(1 for s in scenes if s['id'] in sel)}컷)")


if __name__ == "__main__":
    main()
