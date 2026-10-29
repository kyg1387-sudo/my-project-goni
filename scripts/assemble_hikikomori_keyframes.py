#!/usr/bin/env python3
"""『引きこもりの息子』 PHASE 4 최종 키프레임 모으기 — 단계별 합격본을 스토리보드 경로
assets/portraits/hikikomori-keyframes/<id>-1.png(PHASE 5 i2v·정지 푸시인·OmniHuman 입력)로 복사하고,
레터박스를 자르고(kf_letterbox_fix), 얼굴이 작은 립싱크 컷은 얼굴 1/3로 크롭한다(kf_face_frame, 제17장 2).
우선순위: productions/hikikomori-ja/kf_select.json(검수에서 고른 후보) > r3 > r2 > r1 > a·b1·b2.
사용법: python3 scripts/assemble_hikikomori_keyframes.py [--check]"""
import json, os, shutil, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = os.path.join(ROOT, "scripts", "storyboard", "hikikomori.json")
SEL = os.path.join(ROOT, "productions", "hikikomori-ja", "kf_select.json")
STAGES = ["assets/portraits/hikikomori-kf-r3", "assets/portraits/hikikomori-kf-r2", "assets/portraits/hikikomori-kf-r1",
          "assets/portraits/hikikomori-kf-a", "assets/portraits/hikikomori-kf-b1", "assets/portraits/hikikomori-kf-b2"]


def main():
    check = "--check" in sys.argv
    sel = json.load(open(SEL, encoding="utf-8")) if os.path.exists(SEL) else {}
    picks = {k: v for k, v in sel.get("pick", {}).items()}
    frame = sel.get("face_frame", {})  # id: [target, hint_x, fg]
    crops = sel.get("crop", {})  # id: [x0, y0, w] 비율
    scenes = [s for s in json.load(open(SB, encoding="utf-8"))["scenes"] if s.get("keyframe")]
    missing, plan = [], []
    for s in scenes:
        src = picks.get(s["id"]) or next((f"{d}/{s['id']}-1.png" for d in STAGES if os.path.exists(os.path.join(ROOT, d, f"{s['id']}-1.png"))), None)
        if not src or not os.path.exists(os.path.join(ROOT, src)):
            missing.append(s["id"]); continue
        plan.append((s["id"], src, s["keyframe"]))
    if missing:
        sys.exit(f"키프레임 없음 {len(missing)}컷: {', '.join(missing)}")
    if check:
        print(f"키프레임 {len(plan)}컷 확인"); return
    for sid, src, dst in plan:
        d = os.path.join(ROOT, dst); os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(os.path.join(ROOT, src), d)
        if sid in crops:  # 앞 인물 잘라내기(안경 유입 등) — [x0, y0, 폭] 비율, 16:9 유지
            from PIL import Image
            im = Image.open(d).convert("RGB"); W, H = im.size; x0, y0, wf = crops[sid]
            cw = int(W * wf); ch = int(cw * 9 / 16)
            im.crop((int(W * x0), int(H * y0), int(W * x0) + cw, int(H * y0) + ch)).resize((W, H), Image.LANCZOS).save(d)
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "kf_letterbox_fix.py"), d], check=True, capture_output=True)
        if sid in frame:
            t, hx, fg = frame[sid]
            subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "kf_face_frame.py"), d, d, str(t), str(hx), fg], check=True)
    vdir = os.path.join(ROOT, "assets", "portraits", "hikikomori-keyframes", "_v1")
    if os.path.isdir(vdir):
        shutil.rmtree(vdir)  # letterbox 원본 백업은 단계 폴더에 이미 있음
    print(f"키프레임 {len(plan)}컷 복사·레터박스 크롭 완료 (선택 지정 {len(picks)}컷, 얼굴 크롭 {len(frame)}컷)")


if __name__ == "__main__":
    main()
