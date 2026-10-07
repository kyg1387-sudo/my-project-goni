#!/usr/bin/env python3
"""『タワマンのボスママ』 PHASE 4 키프레임 스펙 생성기 (build_yanagi_keyframes.py 구조, 규격 제7장 1·7).

scripts/storyboard/tower.json(PHASE 3)을 읽어 generate_portraits.py 스펙을 만든다. 스펙을 손으로 고치지 않는다.
단계:
  pilot  scripts/portraits/tower-kf-pilot.json  파일럿 3장(S01b 레이카 엘리베이터 OMNI · S13d 유미 총회 OMNI · S17b 레이카 바닥 부감)
  a      scripts/portraits/tower-kf-a.json      OMNI 대사 CU 13장 — 참조 = PHASE 2 셀(표정 셀 + 로케이션)
  b      scripts/portraits/tower-kf-b.json      나머지 — 얼굴이 보이는 컷은 A에서 승인한 인물별 기준 얼굴을 1번 참조로 추가
generate-video.yml portraits_spec=<스펙> → assets/portraits/<스펙>/<id>-1.png
사용법: python3 scripts/build_tower_keyframes.py pilot|a|b[:ID,ID]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "tower.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "tower-kf-{}.json")
KF_A = "assets/portraits/tower-kf-a"
PILOT = ["S01b", "S13d", "S17b"]

PEOPLE = {
    "yumi": "Yumi (42, chin-length black bob with side-swept fringe, thin silver-rimmed glasses, navy cardigan)",
    "reika": "Reika (40, long wavy chestnut hair, red lips, pearl earrings, cream tweed jacket, NO glasses)",
    "riko": "Riko (7-year-old girl, two low pigtails, mustard-yellow dress)",
    "odagiri": "Mr. Odagiri (mid-70s gentleman, combed-back white hair, white moustache, charcoal three-piece suit)",
    "tanto": "the property-management clerk (early 30s, short black hair, grey suit, NO glasses)",
    "mamaA": "Mama A (honey-brown curly bob, pink sweater)", "mamaB": "Mama B (sleek black high ponytail, white blouse, NO glasses)",
    "mamaC": "Mama C (long light-brown hair, beige dress)", "jumin": "the middle-aged resident (salt-and-pepper hair, navy polo shirt)",
}
FACE_KF = {"reika": "S13b", "yumi": "S13d", "odagiri": "S16b", "tanto": "S14m"}  # 인물별 기준 얼굴(A단계 승인 후 B에 1번 참조)
FACE_KINDS = ("face", "react", "d")
# 구도 참조(사용자 승인 시험 장면 CU): 가슴 위 CU 프레이밍이 넓게 빠지는 컷에 추가(파일럿 S13d 실증: 미디엄으로 생성됨)
FRAMING_REF = "assets/portraits/tower-ja-kf-test/S5-yumi-cu-1.png"
EXTRA_REFS = {"S13d": [FRAMING_REF], "S05e": [FRAMING_REF], "S19c": [FRAMING_REF]}

TIGHT = ("Tight chest-up close-up: head and shoulders fill the frame, the top of the head near the top edge, the frame cut at mid-chest; "
         "the face occupies about one third of the frame height; hands NOT visible. Full-frame 16:9 image, no black bars.")
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
LOC_NOTE = {
    "loc-lobby": "The lobby walls and elevator surrounds are bare polished stone and brushed steel: NO paper notices, NO signs, NO floor-number displays with digits.",
    "loc-hall": "The assembly-hall walls are plain white with nothing hanging on them; the projector screen is completely blank white.",
    "loc-kidsroom": "The kids-room walls have NO posters or papers with writing; the plaque beside the door is plain blank white.",
    "loc-office": "Binder spines and labels are completely blank; no papers with readable writing.",
    "prop-bag": "The burgundy quilted bag has NO logo, NO monogram, NO metal emblem — only plain quilting and a gold chain.",
}
COMPOSITION = {
    "S01b": TIGHT + (" Setting: inside the open mirrored passenger elevator of the luxury tower lobby, brushed steel and mirror soft behind her. "
                     "Expression at about 60 percent: a condescending, polite-but-cruel smirk, chin raised, eyes looking down; NOT a friendly smile."),
    "S13d": TIGHT + (" CAMERA DISTANCE: about one metre from her face with an 85mm lens — her head and shoulders fill the frame; "
                     "NOT a medium shot, NOT a full-body shot, her hands and waist are NOT visible. Setting: standing in the middle rows of the packed residents' assembly hall; behind her many seated residents are "
                     "soft, out-of-focus shapes with unrecognizable faces, the tall windows on the left. Expression: calm, resolute, "
                     "about 50 percent firmness; NOT smiling."),
    "S17b": (FULL + " Extreme bird's-eye view from directly above the stage floor: Reika is ALREADY sitting collapsed on the pale wood floor "
             "beside the lectern, legs folded to one side, shoulders slumped, her long chestnut hair falling forward, the open burgundy "
             "bag lying on the floor next to her with a few items spilled (a lipstick, a compact, a plain white envelope). She is small in "
             "the frame; her face is mostly hidden by her hair. Image upright."),
}


def describe(path, i):
    name = os.path.basename(path)
    if path == FRAMING_REF:
        return (f"Reference image {i} is a FRAMING reference only: copy its tight chest-up close-up framing, camera distance and shallow "
                "depth of field exactly (head and shoulders filling the frame); ignore its background, hair fringe and the empty room.")
    if "/tower-kf-a/" in path:
        who = next((v for k, v in PEOPLE.items() if FACE_KF.get(k) == name.split("-")[0]), "the character")
        return f"Reference image {i} is the APPROVED face of {who}: reproduce exactly this face, age and hairstyle; ignore its background, framing and pose."
    for k, v in PEOPLE.items():
        if name.startswith(k + "-"):
            return (f"Reference image {i} is the character sheet cell of {v}: copy this exact face, hairstyle, wardrobe and age; "
                    "ignore its background, framing and any sheet layout.")
    if name.startswith("prop-"):
        return f"Reference image {i} is the prop reference: copy the object's exact shape, colour and material; ignore the white background."
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing and light direction; "
            "ignore any borders or labels.")


def notes(refs):
    out = []
    for r in refs:
        b = os.path.basename(r)
        for k, v in LOC_NOTE.items():
            if b.startswith(k) and v not in out:
                out.append(v)
    return out


def build(sc, face_refs):
    refs = list(face_refs) + sc["refs"] + EXTRA_REFS.get(sc["id"], [])
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    parts.append(sc["keyframe_prompt"])
    parts += notes(refs)
    if sc["id"] in COMPOSITION:
        parts.append(COMPOSITION[sc["id"]])
    elif sc["kind"] == "d":
        parts.append(TIGHT)
    else:
        parts.append(FULL)
    if sc["kind"] == "d":
        parts.append("Mouth gently closed or barely parted (speech is added later); natural skin texture, both eyes sharp and symmetrical.")
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": " ".join(parts)}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    stage, _, only = arg.partition(":")
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    shots = [s for s in sb["scenes"] if s["keyframe"]]
    if stage == "pilot":
        pick = [s for s in shots if s["id"] in PILOT]
        items = [build(s, []) for s in pick]
    elif stage == "a":
        pick = [s for s in shots if s["kind"] == "d"]
        items = [build(s, []) for s in pick]
    elif stage == "b":
        pick = [s for s in shots if s["kind"] != "d"]
        items = []
        for s in pick:
            face = []
            if s["kind"] in FACE_KINDS:
                for r in s["refs"]:
                    k = os.path.basename(r).split("-")[0]
                    if k in FACE_KF:
                        p = f"{KF_A}/{FACE_KF[k]}-1.png"
                        if not os.path.exists(os.path.join(ROOT, p)):
                            raise SystemExit(f"{s['id']}: 기준 얼굴 {p} 없음 — A단계 먼저")
                        face.append(p)
            items.append(build(s, face))
    else:
        raise SystemExit("단계: pilot|a|b")
    if only:
        ids = set(only.split(","))
        items = [x for x in items if x["id"] in ids]
        stage += "-r"
    spec = {"_설명": f"tower PHASE 4 키프레임 {stage}(build_tower_keyframes.py 생성, 직접 수정 금지). {len(items)}장 약 {len(items) * 0.04:.2f}달러.",
            "_style_preset": sb["preset"], "characters": items}
    path = OUT.format(stage)
    json.dump(spec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(items)}장")


if __name__ == "__main__":
    main()
