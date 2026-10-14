#!/usr/bin/env python3
"""『運転手のくせに』 PHASE 4 키프레임 스펙 생성기 (build_ashita_keyframes.py의 교훈 ①~⑱을 일반 규칙으로 옮김).

scripts/storyboard/untenshu.json(PHASE 3)을 읽어 generate_portraits.py 스펙을 만든다. 스펙을 손으로 고치지 않는다.
사용법: python3 scripts/build_untenshu_keyframes.py <스펙 접미사> <컷,컷,…|all-d|all> [후보 수=1]
  예) pilot S06e,S17c,S21b 2  → scripts/portraits/untenshu-kf-pilot.json
generate-video.yml portraits_spec=untenshu-kf-<접미사> → assets/portraits/untenshu-kf-<접미사>/<컷>-<n>.png
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "untenshu.json"), encoding="utf-8"))

FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
# ashita 교훈 ①⑤⑦: 립싱크 컷이 미디엄으로 넓어지고 고함치는 입 → 얼굴 크기 수치 + 감정은 눈·이마·턱 + 입은 닫힘(말은 나중에 입힘)
CONVO = ("Over-the-shoulder conversation framing: the speaker's face fills at least one quarter of the frame height and is in razor-sharp focus; "
         "the listener's shoulder and back of the head are a soft blurred shape at the frame edge; the speaker's mouth is gently CLOSED in this frame "
         "(speech is added later), emotion shown in the eyes, brows and jaw. Natural five-fingered hands only where described.")
# ⑩ 인서트에 얼굴이 나옴 → 인서트 고정 문장
INSERT = ("EXTREME CLOSE-UP INSERT: only the hands / object described fill the frame; NO face, NO head and NO shoulders anywhere in the frame.")
# ⑪ 같은 로케이션 연속 컷 같은 구도 → 앵글 고정 문장
ANGLE = {
    "HA": "CAMERA: steep high angle, looking down from above.",
    "OH": "CAMERA: directly overhead, looking straight down.",
    "BE": "CAMERA: bird's-eye view straight down from high above.",
    "LA": "CAMERA: low angle, looking up.",
    "SIDE": "CAMERA: from the side or behind — NOT facing the camera.",
}
# ⑫ 글자 합성 면에 가짜 글자 → 무지 면
BLANK = ("Every paper, document, card, screen, meter display, license plate and roof lamp surface is completely blank and clean: NO characters, "
         "NO numbers (Japanese text is composited later).")
# ⑰ 뒷모습 지시에도 얼굴이 돌아봄 → 뒷모습 칸 참조(생성기 refs) + 문장
BACK = "The person marked 'seen only from behind' shows only the back of the head and shoulders; the face is NOT visible at all."


def spec_for(shot, n):
    p = shot["keyframe_prompt"]
    extra = []
    if shot["kind"] == "d":
        extra.append(CONVO)
    if shot["kind"] == "ins" or (shot["kind"] in ("live",) and "Insert" in shot["subject"][:20]):
        extra.append(INSERT)
    if shot["angle"] in ANGLE:
        extra.append(ANGLE[shot["angle"]])
    if "seen only from behind" in p:
        extra.append(BACK)
    extra += [BLANK, FULL]
    refs = [r for r in shot["refs"] if r]
    return {"id": shot["id"], "count": n, "aspect_ratio": "16:9", "refs": refs,
            "prompt": "Create ONE single photorealistic cinematic film still — one frame only, NOT a grid. " +
                      ("Reference images: the people's faces, hair and clothes must match their reference images exactly (same person); "
                       "the last reference is the location — keep its space and lighting. " if refs else "") + p + " " + " ".join(extra)}


def main():
    name, sel = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    shots = [s for s in SB["scenes"] if s.get("keyframe")]
    if sel == "all-d":
        pick = [s for s in shots if s["kind"] == "d"]
    elif sel == "all":
        pick = shots
    else:
        ids = sel.split(",")
        pick = [s for s in shots if s["id"] in ids]
        missing = set(ids) - {s["id"] for s in pick}
        if missing:
            sys.exit(f"없는 컷: {sorted(missing)}")
    spec = {"_설명": f"『運転手のくせに』 PHASE 4 키프레임 {name}: {len(pick)}컷 x 후보 {n}장 = {len(pick) * n}장, 약 {len(pick) * n * 0.04:.2f}달러. "
                    "생성: scripts/build_untenshu_keyframes.py (스토리보드 keyframe_prompt + 시트 칸 참조).",
            "characters": [spec_for(s, n) for s in pick]}
    out = os.path.join(ROOT, "scripts", "portraits", f"untenshu-kf-{name}.json")
    json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{out}: {len(pick)}컷 x {n} = {len(pick) * n}장 약 {len(pick) * n * 0.04:.2f}달러")


if __name__ == "__main__":
    main()
