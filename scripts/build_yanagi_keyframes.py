#!/usr/bin/env python3
"""『柳の葉と一杯の水』 PHASE 4 키프레임 스펙 생성기 (build_ep4_keyframes.py 구조, 규격 제7장 1·7).

scripts/storyboard/yanagi.json(PHASE 3, build_yanagi_phase3.py 생성)을 읽어 generate_portraits.py 스펙을 만든다.
스토리보드를 고치면 이 스크립트를 다시 돌릴 뿐, 스펙을 손으로 고치지 않는다.

2단계 (규격 제7장 7: 기준 얼굴은 대사 키프레임):
  A  scripts/portraits/yanagi-kf-a.json  OMNI 대사 CU 14장 — 참조 = PHASE 2 셀(표정 셀 + 로케이션)
  B  scripts/portraits/yanagi-kf-b.json  나머지 — 얼굴이 보이는 컷은 A에서 승인한 인물별 기준 얼굴 키프레임을 1번 참조로 추가
generate-video.yml portraits_spec=<스펙> → assets/portraits/<스펙>/<id>-1.png
사용법: python3 scripts/build_yanagi_keyframes.py [a|b]   (b는 A 결과가 있어야 함)
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "yanagi.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "yanagi-kf-{}.json")
KF_A = "assets/portraits/yanagi-kf-a"

PEOPLE = {  # 셀 파일 접두어 → 이름
    "ogata-a": "Ogata (old man, casual faded grey linen jacket)", "ogata-b": "Ogata (old man, charcoal-navy three-piece suit)",
    "sakamoto": "Sakamoto (store manager, gel-slicked hair, black-rimmed glasses)", "yuna": "Yuna (young female clerk)",
    "haruko": "Haruko (80-year-old grandmother)", "sato": "Sato (chairman's secretary)", "murase": "Murase (head of audit)",
}
# B단계 인물별 기준 얼굴 = A단계 대사 키프레임 (A 검수 후 확정)
FACE_KF = {"ogata-a": "S02b", "ogata-b": "S23d", "yuna": "S26b", "haruko": "S12b", "sakamoto": "S22b"}
FACE_KINDS = ("face", "react", "d")

LOC_NOTE = {  # 로케이션별 고정 문장(PHASE 2 Kill Gate 잔여 결함 + 가상 표기 합성 면)
    "loc-store-ext": ("The long fascia sign band above the glass storefront is a plain uniform deep-green panel with a thin white edge, "
                      "completely blank. The glass doors and windows are clean with NO posters, stickers or notices; beside the door one "
                      "small plain white rectangular plate, blank. Vending machine fronts show only plain coloured bottles, no labels."),
    "loc-misc-sedan": ("The black sedan has NO emblem or badge anywhere (no hood ornament, no grille badge, no trunk badge). Its licence "
                       "plate is a plain blank white rectangle with a thin green border, no characters."),
    "props-notebook": ("The pressed leaf is ONE long narrow WILLOW leaf (lanceolate, about 9 cm long and 1 cm wide, pointed tip, faded "
                       "olive-brown), flat under clear film; NOT a maple, ginkgo or broad leaf."),
    "props-photo": ("The small black-and-white photo shows a teenage girl in a 1960s blouse standing beside an old round stone well with a "
                    "wooden bucket and a weeping willow; NO faucet, NO tap, NO modern objects."),
    "props-cup": "The cup is a plain white paper cup with no print; one long narrow willow leaf floats on the water.",
    "loc-store-int": ("Store interior walls are plain white with NO coloured stripes or bands along the top of the walls or shelves, "
                      "no brand trade dress, no logos, no numerals, no posters with writing."),
}
WILLOW = ("The leaf is a WEEPING-WILLOW leaf: very long and slender like a narrow blade (about 9 cm long, under 1.2 cm wide), "
          "smooth untoothed edges, tapering to a long pointed tip, a thin pale midrib; NOT round, NOT oval, NOT serrated, NOT a birch, "
          "elm, beech or cherry leaf.")
NO_PROP_REF = {"S07a", "S09a", "S09a2", "S26f", "S26h", "S29b"}  # 시트 소품 셀의 잎 모양이 틀려 참조에서 뺌(문장으로 고정)


TIGHT = ("Tight chest-up close-up: head and shoulders fill the frame, the top of the head near the top edge, the frame cut at mid-chest; "
         "the face occupies about one third of the frame height; hands NOT visible. Full-frame 16:9 image, no black bars.")
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
COMPOSITION = {  # 키프레임 Kill Gate 보강 (A단계 1차 검수 2026-10-05)
    # B단계 1차 검수
    "S07a": WILLOW, "S09a2": WILLOW, "S29b": WILLOW + " Two such leaves float side by side.",
    "S09a": WILLOW + (" Setting: the wooden bench in the willow shade right beside the small convenience store (as in the location "
                      "reference), NOT a park, no stone lantern. Close-up: the paper cup sharp in the lower foreground, Ogata's face "
                      "soft behind it."),
    "S26f": WILLOW + " The worn brown leather notebook lies open, the dry faded olive-brown willow leaf pressed flat under clear film.",
    "S26h": WILLOW + " The worn brown leather notebook lies open, the dry faded olive-brown willow leaf pressed flat under clear film.",
    "S26i": FULL + " No logos, no brand names, no numerals anywhere on the glass or walls.",
    "S27e": ("Sakamoto kneels in a full dogeza on the polished floor: knees on the floor, forehead pressed to the floor, both palms "
             "flat on the floor in front of his head; NOT a push-up, legs folded under him."),
    "S27l": ("Bird's-eye view straight down from the ceiling: Sakamoto kneels in dogeza on the mirror-polished floor, seen from "
             "directly above as a small figure — his back, slicked hair and flat palms; his face is NOT visible. Image upright."),
    "S27i2": ("Macro insert: the lower half of a man's jaw in profile at the very top edge of the frame, one bead of sweat falling "
              "toward the mirror-polished floor below, reflections; a normal human scale, no giant face."),
    "S27f": "Macro insert, no people: one tiny drop of water on the mirror-polished floor, soft reflections; plain floor, no white squares or patches.",
    "S25a": ("High-angle security-camera view from a ceiling corner of the store: small figures of Ogata, Sato, Murase and Sakamoto "
             "standing near the counter, wide fisheye-like perspective, slightly cool flat video look."),
    "S28g": "Haruko looks down at a small faded black-and-white paper photograph held in her fingers; NOT a phone, NOT a tablet.",
    "S20d": FULL, "S13a2": FULL, "S13c2": FULL, "S26h2": FULL + " " + WILLOW, "S29c": FULL,
    "S13a3": FULL + " The older woman is seen from behind and the side so that her face is NOT visible; only her floral sleeve and hands.",
    "S27b": "The black tablet screen shows only a plain dark grey video frame with soft blurred shapes (picture composited later).",
    "S12b": TIGHT + " Haruko sits propped on pillows by the window, looking at the camera with warm worry.",
    "S14g": TIGHT + " Expression: a thin cold smirk with hard narrowed eyes behind the glasses, NOT a broad friendly smile.",
    "S22b": TIGHT + " Expression: an eager over-polite fawning smile, eyebrows raised, shoulders slightly hunched forward.",
}


def describe(path, i):
    name = os.path.basename(path)
    if name.startswith(("S", "H")) and "/yanagi-kf-" in path:
        who = next((v for k, v in PEOPLE.items() if FACE_KF.get(k) == name.split("-")[0]), "the character")
        return f"Reference image {i} is the APPROVED face of {who}: reproduce exactly this face, age and hairstyle (glasses only if worn there); ignore its background, framing and pose."
    for k, v in PEOPLE.items():
        if name.startswith(k):
            return (f"Reference image {i} is the character sheet cell of {v}: copy this exact face, hairstyle, wardrobe and age; "
                    "ignore its background, framing and any sheet layout.")
    if name.startswith("props-"):
        return f"Reference image {i} is the prop reference: copy the object's exact shape, size and material; ignore any background or labels."
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
    src = [r for r in sc["refs"] if not (sc["id"] in NO_PROP_REF and os.path.basename(r).startswith("props-"))]
    refs = list(face_refs) + src
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, "
             "no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    parts.append(sc["keyframe_prompt"])
    parts += [n for n in notes(src)]
    if sc["id"] in COMPOSITION:
        parts.append(COMPOSITION[sc["id"]])
    if sc["kind"] == "d":
        parts.append("Mouth gently closed or barely parted (speech is added later); natural skin texture, both eyes sharp and symmetrical.")
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": " ".join(parts)}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "a"
    stage, _, only = arg.partition(":")  # 예: a:S12b,S14g → 재생성분만 yanagi-kf-a-r.json
    stage = stage.lower()
    only = set(only.split(",")) if only else None
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    chars, missing = [], []
    for sc in sb["scenes"]:
        if not sc.get("keyframe"):
            continue
        is_a = sc["kind"] == "d"
        if (stage == "a") != is_a or (only and sc["id"] not in only):
            continue
        face = []
        if stage == "b" and sc["kind"] in FACE_KINDS:
            for r in sc["refs"]:
                b = os.path.basename(r)
                k = next((k for k in FACE_KF if b.startswith(k)), None)
                if k:
                    f = f"{KF_A}/{FACE_KF[k]}-1.png"
                    if f not in face:
                        face.append(f)
        c = build(sc, face)
        missing += [f for f in c["refs"] if not os.path.exists(os.path.join(ROOT, f))]
        if only:
            c["count"] = 2  # 재생성은 2후보 중 선택
        chars.append(c)
    if missing:
        raise SystemExit("참조 파일 없음: " + ", ".join(sorted(set(missing))))
    head = {"_설명": f"yanagi PHASE 4 키프레임 {stage.upper()}단계 (build_yanagi_keyframes.py 생성, 직접 수정 금지).",
            "_style_preset": sb["preset"]}
    path = OUT.format(stage + ("-r" if only else ""))
    json.dump({**head, "characters": chars}, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{stage.upper()}단계 키프레임 {len(chars)}장 → {path} (약 {len(chars) * 0.04:.2f}달러)")


if __name__ == "__main__":
    main()
