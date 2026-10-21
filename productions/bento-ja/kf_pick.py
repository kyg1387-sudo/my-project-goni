#!/usr/bin/env python3
"""bento PHASE 4 합격 키프레임 선택표 → assets/portraits/bento-keyframes/<컷>-1.png 로 복사(로컬 보정 전 원본).

선택 근거는 PHASE4_검수(Kill Gate) — 기본 = bento-kf-ab의 -1, 재생성 컷은 아래 PICK. PENDING은 재생성 대기(복사 안 함).
"""
import json, os, shutil

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = "assets/portraits/"
PICK = {  # 컷: 원본 파일
    "S08j": P + "bento-kf-pilot-ok/S08j.png", "S13d": P + "bento-kf-pilot-ok/S13d.png", "S13f": P + "bento-kf-pilot-ok/S13f.png",
    "H2": P + "bento-kf-r4/H2-2.png", "S02c": P + "bento-kf-r4/S02c-2.png", "S03a": P + "bento-kf-r4/S03a-1.png",
    "S03b": P + "bento-kf-r4/S03b-1.png", "S03be": P + "bento-kf-r4/S03be-2.png", "S03bf": P + "bento-kf-r4/S03bf-2.png",
    "S03bg": P + "bento-kf-r4/S03bg-1.png", "S03c": P + "bento-kf-r4/S03c-1.png", "S03d": P + "bento-kf-r4/S03d-2.png",
    "S04b": P + "bento-kf-r4/S04b-1.png", "S08c": P + "bento-kf-r4/S08c-2.png", "S08f": P + "bento-kf-r4/S08f-2.png",
    "S08n": P + "bento-kf-r4/S08n-2.png", "S10a": P + "bento-kf-r4/S10a-1.png", "S10bb": P + "bento-kf-r4/S10bb-1.png",
    "S10bd": P + "bento-kf-r4/S10bd-1.png", "S12f": P + "bento-kf-r4/S12f-1.png", "S12g": P + "bento-kf-r4/S12g-2.png",
    "S12k": P + "bento-kf-r4/S12k-2.png", "S12r": P + "bento-kf-r4/S12r-1.png", "S13j": P + "bento-kf-r4/S13j-1.png",
    "S13n": P + "bento-kf-r4/S13n-1.png", "S13u": P + "bento-kf-r4/S13u-2.png", "S14e": P + "bento-kf-r4/S14e-2.png",
    "S02d": P + "bento-kf-r6/S02d-1.png", "S02e": P + "bento-kf-r6/S02e-1.png", "S04e": P + "bento-kf-r6/S04e-2.png",
    "S04g": P + "bento-kf-r6/S04g-2.png", "S05f": P + "bento-kf-r6/S05f-1.png", "S06b": P + "bento-kf-r6/S06b-1.png",
    "S07d": P + "bento-kf-r6/S07d-2.png", "S08a": P + "bento-kf-r6/S08a-1.png", "S08b": P + "bento-kf-r6/S08b-1.png",
    "S08h": P + "bento-kf-r6/S08h-2.png", "S09b": P + "bento-kf-r6/S09b-1.png", "S09e": P + "bento-kf-r6/S09e-1.png",
    "S09g": P + "bento-kf-r6/S09g-2.png", "S09i": P + "bento-kf-r6/S09i-1.png", "S09n": P + "bento-kf-r6/S09n-1.png",
    "S12d": P + "bento-kf-r6/S12d-1.png", "S13l": P + "bento-kf-r6/S13l-1.png",
    "S06a": P + "bento-kf-r7/S06a-1.png", "S13b": P + "bento-kf-r7/S13b-1.png",
    "S07a": P + "bento-kf-r8/S07a-1c.png", "S13s": P + "bento-kf-r8/S13s-1.png", "S14b": P + "bento-kf-r8/S14b-1.png",  # r8(2026-10-21), S07a 메뉴 종이 가짜 글자 로컬 흐림
    "S04d": P + "bento-kf-r9/S04d-1.png", "S03ba": P + "bento-kf-r9/S03ba-2.png", "S03bb": P + "bento-kf-r9/S03bb-1.png", "S03bd": P + "bento-kf-r9/S03bd-1.png",  # r9
    "S09l": P + "bento-kf-r10/S09l-1.png", "S01d": P + "bento-kf-r10/S01d-2.png", "S09d": P + "bento-kf-r10/S09d-1.png", "S13g": P + "bento-kf-r10/S13g-1.png",
    "S03e": P + "bento-kf-r10/S03e-1.png", "S08g": P + "bento-kf-r10/S08g-1.png", "S10be": P + "bento-kf-r10/S10be-2.png",  # r10
    "S05e": P + "bento-kf-r5/S05e-1.png", "S09p": P + "bento-kf-r5/S09p-1.png", "S13t": P + "bento-kf-r5/S13t-1.png",
}
PENDING = set()


def main():
    sb = json.load(open(os.path.join(REPO, "scripts", "storyboard", "bento.json"), encoding="utf-8"))["scenes"]
    out = os.path.join(REPO, P, "bento-keyframes")
    os.makedirs(out, exist_ok=True)
    n, miss = 0, []
    for s in sb:
        if not s.get("keyframe") or s["id"] in PENDING:
            continue
        src = PICK.get(s["id"], P + f"bento-kf-ab/{s['id']}-1.png")
        if not os.path.exists(os.path.join(REPO, src)):
            miss.append(s["id"]); continue
        shutil.copy(os.path.join(REPO, src), os.path.join(out, f"{s['id']}-1.png")); n += 1
    print(f"복사 {n}컷 · 대기 {len(PENDING)} · 없음 {miss}")


if __name__ == "__main__":
    main()
