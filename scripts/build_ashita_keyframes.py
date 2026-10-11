#!/usr/bin/env python3
"""『明日から来なくていい』 PHASE 4 키프레임 스펙 생성기 (build_yanagi_keyframes.py 구조, 규격 제7장 1·7).

scripts/storyboard/ashita-kara.json(PHASE 3, build_ashita_phase3.py 생성)을 읽어 generate_portraits.py 스펙을 만든다.
스토리보드를 고치면 이 스크립트를 다시 돌릴 뿐, 스펙을 손으로 고치지 않는다.

단계:
  p:<id,id,…>  시범(파일럿) — scripts/portraits/ashita-kf-pilot.json
  a            OMNI 대사 CU 12장 — 참조 = PHASE 2 셀(표정 셀 + 로케이션)
  b            나머지 — 얼굴이 보이는 컷은 A에서 승인한 인물별 기준 얼굴 키프레임을 1번 참조로 추가(FACE_KF, A 검수 후 확정)
generate-video.yml portraits_spec=<스펙> → assets/portraits/<스펙>/<id>-1.png
사용법: python3 scripts/build_ashita_keyframes.py p:S25a,S24d,S14a | a | b | a:S12c,S25a(재생성분만 -r)
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "ashita-kara.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "ashita-kf-{}.json")
KF_A = "assets/portraits/ashita-kf-a"

PEOPLE = [  # (셀 파일 접두어, 설명) — 더 긴 접두어를 먼저(sato-b가 sato보다 먼저)
    ("sato-b", "Sato (48, engineer, thin silver-rimmed glasses, charcoal suit)"),
    ("sato", "Sato (48, engineer, thin silver-rimmed glasses, navy work jacket)"),
    ("tanaka", "Tanaka (28, arrogant manager, light-brown swept-up hair, NO glasses)"),
    ("yamamoto", "Yamamoto (63, executive, bald crown, thin gold-rimmed glasses)"),
    ("takahashi", "Takahashi (55, client division head, very short grey hair, NO glasses, black overcoat)"),
    ("mori", "Mori (24, young female engineer, black bob with bangs, NO glasses)"),
]
# B단계 인물별 기준 얼굴 = A단계 대사 키프레임 (A 검수 후 확정)
FACE_KF = {"sato": "S14d", "sato-b": "S26a", "tanaka": "S12c", "takahashi": "S24c"}
FACE_KINDS = ("face", "react", "d")

LOC_NOTE = {  # 로케이션별 고정 문장(PHASE 2 Kill Gate 잔여 결함 대응)
    "loc-control": ("All control-room walls are completely bare: NO papers, notices, charts or signs on the walls; consoles have plain "
                    "unlabeled buttons; monitors show only abstract shapes or are dark."),
    "loc-meeting": "The meeting room walls are completely bare: no posters, no signs, no plaques; the table is long glossy black lacquer.",
    "loc-office": "Office walls are bare: no posters, no exit signs, no notices; drawings and screens show only lines with no lettering.",
    "loc-misc": "No shop signs, posters or labels with writing anywhere; any awning or sign surface is plain.",
    "props-breaker": "The breaker unit has NO stickers or labels at all, only scuffed grey metal.",
}
TIGHT = ("Tight chest-up close-up: head and shoulders fill the frame, the top of the head near the top edge, the frame cut at mid-chest; "
         "the face occupies about one third of the frame height; hands NOT visible. Full-frame 16:9 image, no black bars.")
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
COMPOSITION = {
    "S25a": TIGHT + " Tanaka is on his knees, face crumpled in sobbing despair, looking up toward someone just off camera.",
    "S24d": ("Medium shot from the side: Yamamoto stands frozen in terror in the dark control room, face drenched with fine realistic "
             "perspiration, gold-rimmed glasses slightly fogged at the edges, a trembling hand half raised. " + FULL),
    "S14a": ("Wide night shot of the open-plan office: Sato in the navy work jacket and silver-rimmed glasses stands at his lamp-lit desk "
             "placing a folder into a cardboard box, seen in three-quarter view; Mori in the light-blue uniform stands two steps behind him, "
             "seen from behind. Only one warm desk lamp lights the scene. " + FULL),
}
EXTRA_REFS = {}


def who_of(name):
    return next(((k, v) for k, v in PEOPLE if name.startswith(k + "-")), (None, None))


def describe(path, i):
    name = os.path.basename(path)
    if "/ashita-kf-" in path:
        k = next((k for k, s in FACE_KF.items() if name.startswith(s + "-")), None)
        who = dict(PEOPLE).get(k, "the character")
        return (f"Reference image {i} is the APPROVED face of {who}: reproduce exactly this face, age and hairstyle "
                "(glasses exactly as there); ignore its background, framing and pose.")
    k, v = who_of(name)
    if k:
        return (f"Reference image {i} is the character sheet cell of {v}: copy this exact face, hairstyle, glasses (or no glasses), "
                "wardrobe and age; ignore its background, framing and any sheet layout.")
    if name.startswith("props-"):
        return f"Reference image {i} is the prop reference: copy the object's exact shape, size and material; ignore any background or labels."
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing and light direction; "
            "ignore any borders, labels or wall papers.")


def notes(refs):
    out = []
    for r in refs:
        b = os.path.basename(r)
        for k, v in LOC_NOTE.items():
            if b.startswith(k) and v not in out:
                out.append(v)
    return out


def build(sc, face_refs):
    refs = list(face_refs) + list(sc["refs"]) + EXTRA_REFS.get(sc["id"], [])
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, "
             "no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    parts.append(sc["keyframe_prompt"])
    parts += notes(sc["refs"])
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
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    stage, _, only = arg.partition(":")
    stage = stage.lower()
    only = set(only.split(",")) if only else None
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    chars, missing = [], []
    for sc in sb["scenes"]:
        if not sc.get("keyframe"):
            continue
        if stage == "p":
            if sc["id"] not in only:
                continue
        else:
            is_a = sc["kind"] == "d"
            if (stage == "a") != is_a or (only and sc["id"] not in only):
                continue
        face = []
        if stage == "b" and sc["kind"] in FACE_KINDS:
            for r in sc["refs"]:
                k, _ = who_of(os.path.basename(r))
                if k in FACE_KF:
                    f = f"{KF_A}/{FACE_KF[k]}-1.png"
                    if f not in face:
                        face.append(f)
        c = build(sc, face)
        missing += [f for f in c["refs"] if not os.path.exists(os.path.join(ROOT, f))]
        if only and stage != "p":
            c["count"] = 2
        chars.append(c)
    if stage == "p" and len(chars) != len(only):
        raise SystemExit(f"시범 컷 일부 없음: {sorted(only - {c['id'] for c in chars})}")
    if missing:
        raise SystemExit("참조 파일 없음: " + ", ".join(sorted(set(missing))))
    name = "pilot" if stage == "p" else stage + ("-r" if only else "")
    head = {"_설명": f"ashita-kara PHASE 4 키프레임 {name} (build_ashita_keyframes.py 생성, 직접 수정 금지).", "_style_preset": sb["preset"]}
    path = OUT.format(name)
    json.dump({**head, "characters": chars}, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{name} 키프레임 {len(chars)}장 → {path} (약 {len(chars) * 0.04:.2f}달러)")


if __name__ == "__main__":
    main()
