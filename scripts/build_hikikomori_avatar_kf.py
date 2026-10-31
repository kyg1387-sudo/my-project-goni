#!/usr/bin/env python3
"""3D 아바타 시험 쇼츠(쇼츠 ③ 구간 S18c~S20d, 16컷) 키프레임 변환 스펙 생성 — 본편 키프레임(화면 합성본)을 구도 베이스로,
컷에 나오는 인물의 아바타 기준(hikikomori-avatar/av-<인물>-N.png)을 참조로 붙인다. 손·소품·화면 글자 규칙은 본편과 같다(제19장 25·13).
사용법: python3 scripts/build_hikikomori_avatar_kf.py daiki=1 kentaro=2 ...   → scripts/portraits/hikikomori-avatar-kf.json
"""
import json, os, re, sys
sys.argv += [] ; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CUTS = ["S18c", "S18d", "S18e", "S18f", "S18g", "S19a", "S19b", "S19c", "S19d", "S19e", "S19f", "S19g", "S20a", "S20b", "S20c", "S20d"]
NAMES = {"daiki": r"Daiki", "kentaro": r"Kentaro|father", "makabe": r"Makabe", "ryosuke": r"Ryosuke", "seiji": r"Seiji|uncle", "yumiko": r"Yumiko|mother"}
STYLE = ("Re-render this exact frame in a stylized 3D animated feature-film style: soft rounded forms, slightly larger expressive eyes, smooth subsurface skin, "
         "clean stylized hair, soft global illumination, the same cinematic lighting and colour mood (NOT photorealistic, NOT 2D anime). ")


def main():
    picks = dict(a.split("=") for a in sys.argv[1:] if "=" in a)
    sb = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "scripts/storyboard/hikikomori.json"), encoding="utf-8"))["scenes"]}
    chars = []
    for cid in CUTS:
        s = sb[cid]; text = (s.get("subject") or "") + " " + (s.get("keyframe_prompt") or "")[:600]
        scr = os.path.join("assets/preview/hikikomori-screens", f"{cid}.png")
        base = scr if os.path.exists(os.path.join(ROOT, scr)) else f"assets/portraits/hikikomori-keyframes/{cid}-1.png"
        who = [k for k, pat in NAMES.items() if re.search(pat, text)]
        refs = [base] + [f"assets/portraits/hikikomori-avatar/av-{k}-{picks.get(k, '1')}.png" for k in who][:5]
        idmap = " ".join(f"Reference image {i + 2} is the 3D character design of {k.capitalize()} — use exactly this design for him/her." for i, k in enumerate(who[:5]))
        p = (f"EDIT reference image 1 — keep EXACTLY its composition, camera angle, framing, every person's position, pose, hands, gaze and expression, the props and the room. "
             + STYLE + idmap + " Hands: natural five fingers, the same number of hands as in reference image 1. Screens and papers stay plain or keep their existing content; "
             "no new text, no letters, no logo, no watermark.")
        chars.append({"id": cid, "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": p})
    json.dump({"_설명": "3D 아바타 시험 쇼츠 16컷 키프레임 변환(고니감독님 제안 2026-10-31).", "characters": chars},
              open(os.path.join(ROOT, "scripts/portraits/hikikomori-avatar-kf.json"), "w"), ensure_ascii=False, indent=1)
    for c in chars:
        print(c["id"], [os.path.basename(r) for r in c["refs"]])


if __name__ == "__main__":
    main()
